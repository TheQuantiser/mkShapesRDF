"""RunStability runner with DATA run-resolved auxiliary histograms."""

from copy import deepcopy
from array import array
import pickle
import os
import subprocess
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
        raise RuntimeError(
            "Remote output requires xrdWriteEndpoint and analysisRemoteOutputLFN"
        )
    subprocess.run(
        ["xrdfs", endpoint, "mkdir", "-p", output_lfn],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=int(globals().get("remoteCommandTimeout", 120)),
    )


class RunAnalysis(_CoreRunAnalysis):
    """Keep stock TH1 production and add DATA-only run-resolved TH2 output."""

    def __init__(
        self, samples, aliases, variables, cuts, nuisances, lumi, *args, **kwargs
    ):
        aliases = dict(aliases)
        marker = aliases.pop("__run_stability_contract__", None)
        self.run_stability_contract = deepcopy(
            (marker or {}).get("run_stability_contract", {"enabled": False})
        )
        self.run_stability_enabled = bool(
            self.run_stability_contract.get("enabled", False)
        )
        if self.run_stability_enabled:
            data_outputs = {sample[0] for sample in samples if sample[4]}
            if data_outputs and data_outputs != {"DATA"}:
                raise RuntimeError(
                    "RUN_STABILITY supports exactly one logical DATA output named "
                    f"DATA; received {sorted(data_outputs)}"
                )
            expected_paths = len(
                self.run_stability_contract.get("categories", ())
            ) * len(self.run_stability_contract.get("observables", ()))
            actual_paths = len(
                self.run_stability_contract.get("auxiliary_output_paths", ())
            )
            if expected_paths <= 0 or actual_paths != expected_paths:
                raise RuntimeError(
                    "RUN_STABILITY auxiliary path inventory diverges from its "
                    f"category/observable matrix: expected={expected_paths}, "
                    f"actual={actual_paths}"
                )
        tree_variables = [name for name, cfg in variables.items() if "tree" in cfg]
        if tree_variables:
            raise RuntimeError(
                "RunStability is histogram-only; tree variables are disabled: "
                + ", ".join(tree_variables)
            )
        self.cut_weight_factors = self.resolve_cut_weight_factors(cuts)
        super().__init__(
            samples, aliases, variables, cuts, nuisances, lumi, *args, **kwargs
        )

    def _variables_for_cut(self, cut_name, source=None):
        return {
            name: definition
            for name, definition in (source or self.variables).items()
            if not definition.get("categories") or cut_name in definition["categories"]
        }

    def _public_variable_name(self, variable_name):
        prefix = self.remappedVariables.get(variable_name, "")
        return variable_name[len(prefix) :] if prefix else variable_name

    def _internal_variable_name(self, public_name):
        matches = [
            variable_name
            for variable_name in self.variables
            if self._public_variable_name(variable_name) == public_name
        ]
        if len(matches) != 1:
            raise RuntimeError(
                "RUN_STABILITY could not resolve exactly one internal variable "
                f"for {public_name!r}; found {matches}"
            )
        return matches[0]

    def createResults(self):
        """Create only resolved sparse category-variable result slots."""
        run_stability_contract = getattr(
            self, "run_stability_contract", {"enabled": False}
        )
        run_stability_enabled = getattr(self, "run_stability_enabled", False)
        self.results = {
            cut_name: {
                variable_name: {} for variable_name in self._variables_for_cut(cut_name)
            }
            for cut_name in self.cuts
        }
        self.run_stability_results = {
            cut_name: {
                internal_name: {}
                for public_name in run_stability_contract.get("observables", ())
                for internal_name in (self._internal_variable_name(public_name),)
                if internal_name in self._variables_for_cut(cut_name)
            }
            for cut_name in self.cuts
            if run_stability_enabled
            and cut_name in run_stability_contract.get("categories", ())
        }

    @staticmethod
    def resolve_cut_weight_factors(cuts):
        """Flatten declarative cut/category weight policies for booking."""
        resolved = {}
        for parent, definition in cuts["cuts"].items():
            if isinstance(definition, dict):
                weight_policy = definition.get("weights", {})
                default_factor = weight_policy.get("*", definition.get("weight", "1.f"))
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
                self._book_run_stability_for_cut(cut_name)
        finally:
            self.cuts = all_cuts
            self.dfs = all_dfs
            self.variables = all_variables

    @staticmethod
    def _axis_model(variable):
        """Return the ROOT TH2 y-axis model for one public TH1 variable."""
        expression = variable["name"].split(":")
        if len(expression) != 1:
            raise RuntimeError("RUN_STABILITY observables must remain one-dimensional")
        axis = variable["range"]
        if len(axis) == 1:
            edges = tuple(float(value) for value in axis[0])
            if len(edges) < 2:
                raise RuntimeError("RUN_STABILITY variable edges are empty")
            return (len(edges) - 1, array("d", edges))
        if len(axis) == 3:
            return (int(axis[0]), float(axis[1]), float(axis[2]))
        raise RuntimeError(f"Unsupported RUN_STABILITY axis specification: {axis!r}")

    def _book_run_stability_for_cut(self, cut_name):
        if cut_name not in getattr(self, "run_stability_results", {}):
            return
        n_runs = len(self.run_stability_contract["ordered_runs"])
        for sample_name, sample_dfs in self.dfs.items():
            if sample_name != "DATA":
                continue
            for index, metadata in sample_dfs.items():
                df_cat = metadata["df"].Filter(self.cuts[cut_name]["expr"])
                for variable_name in self.run_stability_results[cut_name]:
                    variable = self.variables[variable_name]
                    y_model = self._axis_model(variable)
                    model = (
                        f"run_stability_{cut_name}_{variable_name}_{index}",
                        "",
                        n_runs,
                        0.5,
                        n_runs + 0.5,
                        *y_model,
                    )
                    result = df_cat.Histo2D(
                        model,
                        "runStabilityIndex",
                        f"{variable_name}_0",
                        "weight",
                    )
                    self.run_stability_results[cut_name][variable_name][index] = result

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
        self._convert_run_stability_results()

    @staticmethod
    def _merge_y_bin(histogram, source, destination):
        for xbin in range(0, histogram.GetNbinsX() + 2):
            content = histogram.GetBinContent(xbin, destination)
            error = histogram.GetBinError(xbin, destination)
            source_content = histogram.GetBinContent(xbin, source)
            source_error = histogram.GetBinError(xbin, source)
            histogram.SetBinContent(xbin, destination, content + source_content)
            histogram.SetBinError(
                xbin,
                destination,
                (error * error + source_error * source_error) ** 0.5,
            )
            histogram.SetBinContent(xbin, source, 0.0)
            histogram.SetBinError(xbin, source, 0.0)

    @classmethod
    def fold_observable_axis(cls, histogram, fold):
        """Apply mkShapesRDF fold codes to y only, preserving the run axis."""
        if fold in (1, 3):
            cls._merge_y_bin(histogram, 0, 1)
        if fold in (2, 3):
            cls._merge_y_bin(
                histogram,
                histogram.GetNbinsY() + 1,
                histogram.GetNbinsY(),
            )
        return histogram

    @staticmethod
    def _assert_empty_run_flows(histogram):
        nx = histogram.GetNbinsX()
        ny = histogram.GetNbinsY()
        for xbin, label in ((0, "underflow"), (nx + 1, "overflow")):
            content = sum(
                abs(histogram.GetBinContent(xbin, ybin)) for ybin in range(0, ny + 2)
            )
            uncertainty = sum(
                abs(histogram.GetBinError(xbin, ybin)) for ybin in range(0, ny + 2)
            )
            if content != 0.0 or uncertainty != 0.0:
                raise RuntimeError(
                    f"RUN_STABILITY run-axis {label} is nonempty in "
                    f"{histogram.GetName()}: content={content}, error={uncertainty}"
                )

    def _label_run_axis(self, histogram):
        runs = self.run_stability_contract["ordered_runs"]
        if histogram.GetNbinsX() != len(runs):
            raise RuntimeError("RUN_STABILITY histogram run-axis size diverges")
        histogram.GetXaxis().SetTitle("Run number")
        for index, run in enumerate(runs, 1):
            histogram.GetXaxis().SetBinLabel(index, str(run))

    def _convert_run_stability_results(self):
        if not getattr(self, "run_stability_enabled", False):
            return
        for cut_name, cut_results in self.run_stability_results.items():
            for variable_name, indexed_results in cut_results.items():
                for index, result in list(indexed_results.items()):
                    histogram = result.GetValue().Clone(
                        f"run_stability_{cut_name}_{variable_name}_DATA_{index}"
                    )
                    histogram.SetDirectory(0)
                    self._label_run_axis(histogram)
                    histogram.GetYaxis().SetTitle(
                        self.variables[variable_name].get("xaxis", "")
                    )
                    self._assert_empty_run_flows(histogram)
                    self.fold_observable_axis(
                        histogram, self.variables[variable_name].get("fold", 0)
                    )
                    self._assert_empty_run_flows(histogram)
                    indexed_results[index] = histogram

    def _save_sparse_results(self):
        """Write the non-rectangular result dictionary without empty folders."""
        output = ROOT.TFile(self.outputFileMap, "recreate")
        try:
            for cut_name, cut_results in self.results.items():
                output.mkdir(cut_name)
                for variable_name, variable_results in cut_results.items():
                    public_name = (
                        variable_name[len(self.remappedVariables[variable_name]) :]
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
                            suffix = (
                                ""
                                if variation_name == "nominal"
                                else f"_{variation_name}"
                            )
                            name = f"histo_{sample_name}{suffix}"
                            histogram.SetName(name)
                            histogram.SetTitle(name)
                            histogram.Write()
            self._write_run_stability_results(output)
        finally:
            output.Close()

    def _write_run_stability_results(self, output):
        if not getattr(self, "run_stability_enabled", False):
            return
        output.mkdir("run_stability")
        for cut_name, cut_results in self.run_stability_results.items():
            output.mkdir(f"run_stability/{cut_name}")
            for variable_name, indexed_results in cut_results.items():
                if not indexed_results:
                    continue
                public_name = self._public_variable_name(variable_name)
                output.mkdir(f"run_stability/{cut_name}/{public_name}")
                output.cd(f"/run_stability/{cut_name}/{public_name}")
                merged = None
                for histogram in indexed_results.values():
                    if not isinstance(histogram, ROOT.TH2):
                        raise RuntimeError(
                            "RUN_STABILITY auxiliary result was not converted to TH2"
                        )
                    if merged is None:
                        merged = histogram.Clone("histo_DATA")
                        merged.SetDirectory(0)
                    else:
                        merged.Add(histogram)
                self._assert_empty_run_flows(merged)
                merged.SetName("histo_DATA")
                merged.SetTitle("histo_DATA")
                merged.Write()
        if self._is_metadata_writer():
            self._write_run_stability_metadata(output)

    def _is_metadata_writer(self):
        policy = self.run_stability_contract.get("metadata_writer", {})
        sample_name = policy.get("sample", "DATA")
        split_index = int(policy.get("split_index", 0))
        return split_index in self.dfs.get(sample_name, {})

    def _run_metadata_histogram(self, name, rows, field):
        runs = self.run_stability_contract["ordered_runs"]
        if len(rows) != len(runs):
            raise RuntimeError(
                f"Run-stability metadata {name} has {len(rows)} rows; "
                f"expected {len(runs)}"
            )
        histogram = ROOT.TH1D(name, name, len(runs), 0.5, len(runs) + 0.5)
        histogram.SetDirectory(0)
        histogram.GetXaxis().SetTitle("Run number")
        histogram.GetYaxis().SetTitle("Luminosity [fb^{-1}]")
        for index, (run, row) in enumerate(zip(runs, rows), 1):
            if int(row["run"]) != int(run):
                raise RuntimeError(
                    f"Run-stability metadata {name} row {index} is for run "
                    f"{row['run']}; expected {run}"
                )
            histogram.GetXaxis().SetBinLabel(index, str(run))
            histogram.SetBinContent(index, float(row[field]))
            histogram.SetBinError(index, 0.0)
        return histogram

    def _write_run_stability_metadata(self, output):
        output.mkdir("run_stability/metadata")
        output.cd("/run_stability/metadata")
        sources = self.run_stability_contract.get("luminosity_sources")
        if not sources:
            sources = {
                "nominal": {"rows": self.run_stability_contract["nominal"]},
                "trigger_any": {"rows": self.run_stability_contract["trigger_any"]},
            }
        for source_name, definition in sources.items():
            rows = definition["rows"]
            for quantity, field in (
                ("delivered", "delivered_fb"),
                ("recorded", "recorded_fb"),
            ):
                self._run_metadata_histogram(
                    f"{source_name}_{quantity}_lumi_fb",
                    rows,
                    field,
                ).Write()
        source = ROOT.TH1D("mc_source_lumi_fb", "mc_source_lumi_fb", 1, 0.5, 1.5)
        source.SetDirectory(0)
        source.GetXaxis().SetBinLabel(1, "configuration")
        source.GetYaxis().SetTitle("Luminosity [fb^{-1}]")
        source.SetBinContent(1, float(self.run_stability_contract["mc_source_lumi_fb"]))
        source.SetBinError(1, 0.0)
        source.Write()

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
