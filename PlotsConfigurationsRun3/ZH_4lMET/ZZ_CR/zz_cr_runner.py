"""ZZ_CR runner with compact split jobs and one shared configuration payload."""

from copy import deepcopy
import pickle
import os
import subprocess
import sys
import zlib

import ROOT

from mkShapesRDF.shapeAnalysis.runner import RunAnalysis as _CoreRunAnalysis


def prepare_remote_output_directory():
    """Create the configured remote parent from the authenticated worker."""
    if globals().get("OUTPUT_MODE") not in ("test-remote", "production-remote"):
        return
    if os.environ.get("MKSHAPESRDF_SKIP_REMOTE_OUTPUT_PREPARE") == "1":
        return
    endpoint = globals().get("xrdWriteEndpoint")
    output_lfn = globals().get("analysisRemoteOutputLFN")
    if not endpoint or not output_lfn:
        raise RuntimeError("Remote output requires xrdWriteEndpoint and analysisRemoteOutputLFN")
    subprocess.run(
        ["xrdfs", endpoint, "mkdir", "-p", output_lfn],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=int(globals().get("remoteCommandTimeout", 120)),
    )


class RunAnalysis(_CoreRunAnalysis):
    """Use stock analysis with compact jobs and optional per-cut weights."""

    def __init__(self, samples, aliases, variables, cuts, nuisances, lumi, *args, **kwargs):
        tree_variables = [name for name, cfg in variables.items() if "tree" in cfg]
        if tree_variables:
            raise RuntimeError(
                "ZZ_CR is histogram-only; tree variables are disabled: "
                + ", ".join(tree_variables)
            )
        self.cut_weight_factors = self.resolve_cut_weight_factors(cuts)
        super().__init__(samples, aliases, variables, cuts, nuisances, lumi, *args, **kwargs)

    def _variables_for_cut(self, cut_name, source=None):
        return {
            name: definition
            for name, definition in (source or self.variables).items()
            if not definition.get("categories")
            or cut_name in definition["categories"]
        }

    def createResults(self):
        """Create only resolved sparse category-variable result slots."""
        self.results = {
            cut_name: {
                variable_name: {}
                for variable_name in self._variables_for_cut(cut_name)
            }
            for cut_name in self.cuts
        }

    @staticmethod
    def resolve_cut_weight_factors(cuts):
        """Flatten declarative cut/category weight policies for booking."""
        resolved = {}
        for parent, definition in cuts["cuts"].items():
            if isinstance(definition, dict):
                weight_policy = definition.get("weights", {})
                default_factor = weight_policy.get(
                    "*", definition.get("weight", "1.f")
                )
                for category in definition.get("categories", {}):
                    resolved[f"{parent}_{category}"] = weight_policy.get(
                        category, default_factor
                    )
            else:
                resolved[parent] = "1.f"
        return resolved

    @staticmethod
    def splitSamples(samples, useFilesPerJob=True):
        split_samples = _CoreRunAnalysis.splitSamples(samples, useFilesPerJob)
        compact_samples = []
        for sample in split_samples:
            compact = list(sample)
            original = compact[5]
            compact[5] = {
                key: deepcopy(original[key])
                for key in ("flatten_samples_map",)
                if key in original
            }
            compact_samples.append(tuple(compact))
        return compact_samples

    def create_cuts_vars(self):
        """Book each cut with its configured correction on the weight branch.

        The core runner intentionally has one nominal ``weight`` column.  For
        the unified nominal pass, invoke its unchanged booking implementation
        one cut at a time on lightweight RDataFrame branch nodes whose weight
        has been redefined.  Parent regions may overlap without contaminating
        one another's correction contract.
        """
        all_cuts = self.cuts
        all_dfs = self.dfs
        all_variables = self.variables
        try:
            for cut_name, cut_definition in all_cuts.items():
                selected_variables = self._variables_for_cut(cut_name, all_variables)
                if not selected_variables:
                    raise RuntimeError(f"No variables resolved for {cut_name}")
                factor = self.cut_weight_factors.get(cut_name, "1.f")
                self.cuts = {cut_name: cut_definition}
                self.variables = selected_variables
                if factor in ("1", "1.", "1.f", "1.0"):
                    self.dfs = all_dfs
                else:
                    self.dfs = {
                        sample_name: {
                            index: {
                                **metadata,
                                "df": metadata["df"].Redefine(
                                    "weight", f"weight * ({factor})"
                                ),
                            }
                            for index, metadata in sample_dfs.items()
                        }
                        for sample_name, sample_dfs in all_dfs.items()
                    }
                super().create_cuts_vars()
        finally:
            self.cuts = all_cuts
            self.dfs = all_dfs
            self.variables = all_variables

    def convertResults(self):
        """Convert only booked sparse results, retaining every variation."""
        all_cuts = self.cuts
        all_variables = self.variables
        try:
            for cut_name, cut_definition in all_cuts.items():
                self.cuts = {cut_name: cut_definition}
                self.variables = self._variables_for_cut(cut_name, all_variables)
                super().convertResults()
        finally:
            self.cuts = all_cuts
            self.variables = all_variables

    def _save_sparse_results(self):
        """Write the non-rectangular result dictionary without empty folders."""
        output = ROOT.TFile(self.outputFileMap, "recreate")
        try:
            for cut_name, cut_results in self.results.items():
                output.mkdir(cut_name)
                for variable_name, variable_results in cut_results.items():
                    public_name = (
                        variable_name[len(self.remappedVariables[variable_name]):]
                        if variable_name in self.remappedVariables
                        else variable_name
                    )
                    output.mkdir(f"{cut_name}/{public_name}")
                    output.cd(f"/{cut_name}/{public_name}")
                    for sample_name, indexed_results in variable_results.items():
                        merged = {}
                        for variations in indexed_results.values():
                            for variation_name, histogram in variations.items():
                                if variation_name not in merged:
                                    merged[variation_name] = histogram.Clone()
                                else:
                                    merged[variation_name].Add(histogram)
                        for variation_name, histogram in merged.items():
                            suffix = "" if variation_name == "nominal" else f"_{variation_name}"
                            name = f"histo_{sample_name}{suffix}"
                            histogram.SetName(name)
                            histogram.SetTitle(name)
                            histogram.Write()
        finally:
            output.Close()

    def saveResults(self):
        self._save_sparse_results()

    def mergeSaveResults(self):
        self._save_sparse_results()

    def mergeAndSaveResults(self):
        self._save_sparse_results()


if __name__ == "__main__":
    ROOT.gInterpreter.Declare('#include "headers.hh"')
    exec(open("script.py").read(), globals(), globals())

    with open(sharedBatchPayload, "rb") as payload_handle:
        worker_payload = pickle.loads(zlib.decompress(payload_handle.read()))
    if "_expand_runtime_paths" in globals():
        worker_payload = _expand_runtime_paths(worker_payload)
    globals().update(worker_payload)
    prepare_remote_output_directory()

    runner = RunAnalysis(
        samples,
        aliases,
        variables,
        cuts,
        nuisances,
        lumi,
        limit=globals().get("limitEvents", -1),
        remote_io_settings=globals().get("remoteIO"),
    )
    runner.run()
