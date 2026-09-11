"""Nominal sparse histograms and event trees on the native mkShapesRDF graph.

Native input preparation, normalization, subsamples, folding and cleanup remain
authoritative. This adapter owns output booking and preserves zero-weight rows.
"""

from array import array
import ast
from copy import deepcopy
from pathlib import Path
import json
import re
import shutil
import tempfile

import ROOT

from mkShapesRDF.shapeAnalysis.runner import RunAnalysis as CoreRunAnalysis


def flatten_regions(cuts):
    """Flatten native categories while inheriting declared correction factors."""
    regions, factors = {}, {}
    for name, definition in cuts.items():
        if isinstance(definition, str):
            regions[name], factors[name] = definition, "1.f"
            continue
        default = definition.get("weights", {}).get(
            "*", definition.get("weight", "1.f")
        )
        categories = definition.get("categories")
        if categories is None:
            regions[name], factors[name] = definition["expr"], default
        else:
            for category, expression in categories.items():
                key = f"{name}_{category}"
                regions[key] = f"({definition['expr']}) && ({expression})"
                factors[key] = definition.get("weights", {}).get(category, default)
    return regions, factors


class RunAnalysis(CoreRunAnalysis):
    """Use ``weight`` for a total, ``weightFactor`` for a relative factor.

    ``studyWeight`` / ``studyWeightFactor`` remain compatibility spellings.
    Trees declare ``tree``, ``cuts``, optional ``treeName`` and ``treeWeight``.
    All expressions use the same aliases as the histograms.
    """

    def __init__(
        self, samples, aliases, variables, cuts, nuisances, lumi, *args, **kwargs
    ):
        # Automatic finite-MC statistics are a downstream datacard directive,
        # not a varied event graph. Keep that native placeholder admissible.
        if any(cfg.get("type") != "auto" for cfg in nuisances.values()):
            raise ValueError(
                "The ZH4l common adapter is nominal-only; use the native ZZCR runner for nuisances"
            )
        header = Path(__file__).resolve().parent / "macros/outputs.h"
        if not ROOT.gInterpreter.Declare(f'#include "{header}"'):
            raise RuntimeError("Cannot declare ZH4l output weight checks")
        flat, self.region_factors = flatten_regions(cuts["cuts"])
        self._parents = {
            key: name
            for name, definition in cuts["cuts"].items()
            for key in (
                [f"{name}_{cat}" for cat in definition["categories"]]
                if isinstance(definition, dict) and "categories" in definition
                else [name]
            )
        }
        variables = deepcopy(variables)
        self._tree_files = []
        self._tree_scratch = None
        self._tree_paths = set()
        for name, definition in variables.items():
            total_keys = {"weight", "studyWeight", "regionWeights"} & definition.keys()
            factor_keys = {"weightFactor", "studyWeightFactor"} & definition.keys()
            if (
                len(total_keys) > 1
                or len(factor_keys) > 1
                or (total_keys and factor_keys)
            ):
                raise ValueError(
                    f"{name}: specify one total weight or one relative factor"
                )
            if "regionWeights" in definition:
                weights = definition["regionWeights"]
                if not isinstance(weights, dict) or any(
                    not isinstance(value, str) or not value.strip()
                    for value in weights.values()
                ):
                    raise ValueError(
                        f"{name}: regionWeights requires total-weight expressions"
                    )
                selected = {
                    cut
                    for cut in flat
                    if all(
                        key not in definition
                        or cut in definition[key]
                        or self._parents[cut] in definition[key]
                        for key in ("cuts", "categories")
                    )
                }
                if "tree" in definition or set(definition["regionWeights"]) != selected:
                    raise ValueError(
                        f"{name}: regionWeights must cover exactly its flat histogram regions"
                    )
            if "tree" in definition:
                if (
                    definition.get("variations")
                    or definition.get("variationPolicy", "nominal") != "nominal"
                ):
                    raise ValueError(
                        "Tree variations are reserved; only nominal export is supported"
                    )
                if definition.get("rowUnit", "event") != "event":
                    raise ValueError(
                        "Event snapshots require rowUnit='event'; keep candidate collections as vectors"
                    )
                if not definition.get("cuts"):
                    raise ValueError(f"Tree {name} requires explicit cuts")
                tree_name = definition.get("treeName", "Events")
                if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", tree_name):
                    raise ValueError(f"Invalid tree name {tree_name!r}")
            for key in ("cuts", "categories"):
                if key in definition:
                    unknown = set(definition[key]) - set(flat) - set(cuts["cuts"])
                    if unknown:
                        raise ValueError(f"{name}: unknown {key}: {sorted(unknown)}")
        super().__init__(
            samples,
            deepcopy(aliases),
            variables,
            {"preselections": cuts["preselections"], "cuts": flat},
            {},
            lumi,
            *args,
            **kwargs,
        )
        if any("tree" in definition for definition in variables.values()):
            for sample in samples:
                chunk = self.dfs[sample[0]][sample[3]]
                chain = chunk["ttree"]
                chain.GetEntries()
                offsets = [int(chain.GetTreeOffset()[i]) for i in range(len(sample[1]))]
                file_expr, entry_expr = 'std::string("")', "ULong64_t(0)"
                for path, offset in zip(sample[1], offsets):
                    file_expr = f"rdfentry_ >= {offset}ULL ? std::string({json.dumps(path)}) : ({file_expr})"
                    entry_expr = f"rdfentry_ >= {offset}ULL ? ULong64_t(rdfentry_-{offset}ULL) : ({entry_expr})"
                chunk["df"] = (
                    chunk["df"]
                    .Define("zh4l_internal_source_file", file_expr)
                    .Define("zh4l_internal_source_entry", entry_expr)
                )
                chunk["columnNames"] = list(map(str, chunk["df"].GetColumnNames()))

    def _variables_for_cut(self, cut):
        return {
            name: cfg
            for name, cfg in self.variables.items()
            if all(
                key not in cfg or cut in cfg[key] or self._parents[cut] in cfg[key]
                for key in ("cuts", "categories")
            )
        }

    def loadAliases(self, afterNuis=False):
        # Resolve explicit sample roles before asking the native alias loader to
        # evaluate either branch; DATA need not carry any MC input columns.
        for sample, chunks in self.dfs.items():
            parent = next(iter(chunks.values())).get("parent", sample)
            is_data = bool(next(s[4] for s in self.samples if s[0] == parent))
            for chunk in chunks.values():
                frame = chunk["df"]
                for name, definition in self.aliases.items():
                    if afterNuis != definition.get("afterNuis", False):
                        continue
                    if "samples" in definition and parent not in definition["samples"]:
                        continue
                    data_override = is_data and "dataExpr" in definition
                    expression = (
                        definition.get("dataExpr")
                        if data_override
                        else definition.get("expr")
                    )
                    if frame.HasColumn(name):
                        if expression == name:
                            continue
                        raise ValueError(
                            f"Alias {name} collides with a retained column"
                        )
                    if not data_override:
                        for line in definition.get("linesToProcess", ()):
                            exec(
                                line.replace("RPLME_nThreads", str(frame.GetNSlots())),
                                globals(),
                            )
                        for line in definition.get("linesToAdd", ()):
                            if not ROOT.gInterpreter.Declare(
                                line.replace("RPLME_nThreads", str(frame.GetNSlots()))
                            ):
                                raise RuntimeError(f"C++ declaration failed for {name}")
                    if expression is not None:
                        frame = frame.Define(name, expression)
                    elif "class" in definition:
                        frame = frame.Define(
                            name, f"{definition['class']}({definition.get('args', '')})"
                        )
                    elif "exprSlot" in definition:
                        func, args = definition["exprSlot"]
                        if isinstance(args, str):
                            args = ast.literal_eval(f"[{args}]")
                        if not isinstance(args, (list, tuple)) or not all(
                            isinstance(arg, str) for arg in args
                        ):
                            raise ValueError(
                                f"{name}: exprSlot columns must be a list of names"
                            )
                        frame = frame.DefineSlot(
                            name,
                            func.replace("RPLME_nThreads", str(frame.GetNSlots())),
                            args,
                        )
                    else:
                        if not (
                            definition.get("linesToAdd")
                            or definition.get("linesToProcess")
                        ):
                            raise ValueError(f"Unsupported alias definition {name}")
                chunk["df"] = frame
                chunk["columnNames"] = list(map(str, frame.GetColumnNames()))
        if afterNuis:
            # The core applies abs(weight)>0 between loadAliases and
            # loadVariables. Keep that gate neutral, then restore the exact
            # normalized (possibly zero or signed) weight before any booking.
            for chunks in self.dfs.values():
                for chunk in chunks.values():
                    chunk["df"] = (
                        chunk["df"]
                        .Define("zh4l_internal_saved_weight", "weight")
                        .Redefine("weight", "1.0")
                    )

    def loadVariables(self):
        for chunks in self.dfs.values():
            for chunk in chunks.values():
                chunk["df"] = chunk["df"].Redefine(
                    "weight", "zh4l_internal_saved_weight"
                )
        super().loadVariables()

    def loadBranches(self):
        # Define projections separately per tree. The native implementation
        # mutates colliding public names globally and cannot represent two
        # different schemas with the same field name.
        return

    def createResults(self):
        self.results = {
            cut: {name: {} for name in self._variables_for_cut(cut)}
            for cut in self.cuts
        }

    def _snapshot(self, dataframe, definition, sample, index, cut):
        tree_name = definition.get("treeName", "Events")
        identity = (cut, sample, index, tree_name)
        if identity in self._tree_paths:
            raise ValueError(
                f"Multiple tree definitions target {identity}; choose distinct treeName values"
            )
        self._tree_paths.add(identity)
        branches = dict(definition["tree"])
        if "weight" in branches and "treeWeight" in definition:
            raise ValueError("Specify the tree's weight once")
        branches.setdefault(
            "weight",
            definition.get("treeWeight", f"weight * ({self.region_factors[cut]})"),
        )
        branches["weight"] = f"ZH4lOutputs::checkedWeight({branches['weight']})"
        # Capture every expression before renaming any public column. This
        # avoids order-dependent swaps such as {a: b, b: a}.
        columns = set(map(str, dataframe.GetColumnNames()))
        projected = []
        for ordinal, (name, expr) in enumerate(branches.items()):
            if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name):
                raise ValueError(f"Invalid tree branch {name!r}")
            temporary = f"zh4l_internal_projection_{ordinal}"
            if temporary in columns:
                raise ValueError(f"Reserved output column {temporary} exists")
            dataframe = dataframe.Define(temporary, expr)
            projected.append((name, temporary))
        for name, temporary in projected:
            dataframe = (
                dataframe.Redefine(name, temporary)
                if name in columns
                else dataframe.Define(name, temporary)
            )
        if self._tree_scratch is None:
            self._tree_scratch = Path(
                tempfile.mkdtemp(
                    prefix=".zh4l-trees-", dir=Path(self.outputFileMap).resolve().parent
                )
            )
        filename = str(self._tree_scratch / f"{len(self._tree_files)}.root")
        options = ROOT.RDF.RSnapshotOptions()
        options.fLazy = True
        result = dataframe.Snapshot(tree_name, filename, list(branches), options)
        self._tree_files.append((cut, sample, tree_name, filename))
        return result

    def create_cuts_vars(self):
        for sample, chunks in self.dfs.items():
            for index, chunk in chunks.items():
                for cut, region in self.cuts.items():
                    dataframe = chunk["df"].Filter(region["expr"])
                    for ordinal, (name, definition) in enumerate(
                        self._variables_for_cut(cut).items()
                    ):
                        frame = dataframe
                        if "tree" in definition:
                            result = self._snapshot(
                                frame, definition, sample, index, cut
                            )
                        else:
                            if "valid" in definition:
                                frame = frame.Filter(definition["valid"])
                            if "weight" in definition and "studyWeight" in definition:
                                raise ValueError(f"{name}: ambiguous total weight")
                            total = definition.get(
                                "weight", definition.get("studyWeight")
                            )
                            if "regionWeights" in definition:
                                total = definition["regionWeights"][cut]
                            factor = definition.get(
                                "weightFactor",
                                definition.get(
                                    "studyWeightFactor", self.region_factors[cut]
                                ),
                            )
                            expression = (
                                total if total is not None else f"weight * ({factor})"
                            )
                            weight = f"zh4l_internal_booking_weight_{ordinal}"
                            frame = frame.Define(
                                weight, f"ZH4lOutputs::checkedWeight({expression})"
                            )
                            dimensions = len(definition["name"].split(":"))
                            axes = definition["range"]
                            hist_range = []
                            if len(axes) == dimensions and all(
                                isinstance(axis, (tuple, list)) for axis in axes
                            ):
                                for axis in axes:
                                    hist_range.extend((len(axis) - 1, array("d", axis)))
                            else:
                                hist_range = list(axes)
                            if dimensions not in (1, 2, 3):
                                raise ValueError(
                                    f"{name}: unsupported histogram dimension {dimensions}"
                                )
                            result = getattr(frame, f"Histo{dimensions}D")(
                                (f"{cut}_{name}", "", *hist_range),
                                *(f"{name}_{i}" for i in range(dimensions)),
                                weight,
                            )
                            result = ROOT.RDF.Experimental.VariationsFor(result)
                        self.results[cut][name].setdefault(sample, {})[index] = result

    def convertResults(self):
        cuts, variables = self.cuts, self.variables
        try:
            for cut in cuts:
                self.cuts = {cut: cuts[cut]}
                self.variables = self._variables_for_cut(cut)
                super().convertResults()
                self.variables = variables
        finally:
            self.cuts, self.variables = cuts, variables

    def saveResults(self):
        output = ROOT.TFile.Open(self.outputFileMap, "RECREATE")
        if not output or output.IsZombie():
            raise OSError(f"Cannot create {self.outputFileMap}")
        try:
            for cut, variables in self.results.items():
                public_names = set()
                for name, samples in variables.items():
                    definition = self.variables[name]
                    if "tree" in definition:
                        continue
                    public = definition.get("outputName", name)
                    if (
                        name in self.remappedVariables
                        and "outputName" not in definition
                    ):
                        public = name[len(self.remappedVariables[name]) :]
                    if public in public_names:
                        raise ValueError(f"Duplicate histogram path {cut}/{public}")
                    public_names.add(public)
                    directory = output.mkdir(f"{cut}/{public}", "", True)
                    directory.cd()
                    for sample, chunks in samples.items():
                        merged = None
                        for variations in chunks.values():
                            histogram = variations["nominal"]
                            if merged is None:
                                merged = histogram.Clone(f"histo_{sample}")
                                merged.SetDirectory(0)
                            else:
                                merged.Add(histogram)
                        merged.Write(f"histo_{sample}")
            groups = {}
            for cut, sample, name, filename in self._tree_files:
                groups.setdefault((cut, sample, name), []).append(filename)
            for (cut, sample, name), files in groups.items():
                directory = output.GetDirectory(
                    f"trees/{cut}/{sample}"
                ) or output.mkdir(f"trees/{cut}/{sample}", "", True)
                directory.cd()
                chain = ROOT.TChain(name)
                count = 0
                template = None
                schema = None
                for filename in files:
                    source = ROOT.TFile.Open(filename)
                    if not source or source.IsZombie() or not source.Get(name):
                        raise OSError(f"Missing snapshot {filename}:{name}")
                    count += source.Get(name).GetEntries()
                    current_schema = tuple(
                        (branch.GetName(), branch.GetClassName(), branch.GetTitle())
                        for branch in source.Get(name).GetListOfBranches()
                    )
                    if schema is not None and current_schema != schema:
                        source.Close()
                        raise ValueError(
                            f"Incompatible tree schemas in {cut}/{sample}/{name}"
                        )
                    schema = current_schema
                    if template is None:
                        template = source.Get(name).CloneTree(0)
                        template.SetDirectory(0)
                    source.Close()
                    chain.Add(filename)
                directory.cd()
                tree = chain.CloneTree(-1, "fast") if count else template
                if not tree or tree.GetEntries() != count:
                    raise RuntimeError(
                        f"Incomplete tree assembly: {cut}/{sample}/{name}"
                    )
                tree.Write(name)
                chain.Reset()
        finally:
            output.Close()

    mergeSaveResults = saveResults
    mergeAndSaveResults = saveResults

    def run(self):
        # Core run() keeps lazy Snapshot results alive until its finally block.
        # Deleting snapshots sooner leaves open .nfs files on shared storage.
        # Failed runs retain their task-owned scratch for diagnosis.
        super().run()
        if self._tree_scratch is not None:
            shutil.rmtree(self._tree_scratch)
            self._tree_scratch = None


def main(namespace):
    """Worker entry point shared by the small leaf runner shims."""
    ROOT.gInterpreter.Declare('#include "headers.hh"')
    runner = RunAnalysis(
        *(
            namespace[key]
            for key in ("samples", "aliases", "variables", "cuts", "nuisances", "lumi")
        ),
        limit=namespace.get("limitEvents", -1),
        remote_io_settings=namespace.get("remoteIO"),
    )
    runner.run()
