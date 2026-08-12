"""One-graph sparse nominal runner with stage and counter-specific weights."""

from array import array
import os

import ROOT
from mkShapesRDF.shapeAnalysis.runner import RunAnalysis as _CoreRunAnalysis


class RunAnalysis(_CoreRunAnalysis):
    def __init__(self, samples, aliases, variables, cuts, nuisances, lumi, *args, **kwargs):
        if any("tree" in cfg for cfg in variables.values()):
            raise RuntimeError("ZH4l Closure is histogram-only; trees are forbidden")
        self.stage_weight_factors = {
            name: definition.get("weights", {}).get("*", "1.f")
            for name, definition in cuts["cuts"].items()
        }
        normalized_cuts = {
            "preselections": cuts["preselections"],
            "cuts": {name: definition["expr"] for name, definition in cuts["cuts"].items()},
        }
        super().__init__(samples, aliases, variables, normalized_cuts, nuisances, lumi, *args, **kwargs)

    def _variables_for_cut(self, cut_name, source=None):
        return {
            name: cfg
            for name, cfg in (source or self.variables).items()
            if cut_name in cfg.get("cuts", ())
        }

    def createResults(self):
        self.results = {cut: {name: {} for name in self._variables_for_cut(cut)} for cut in self.cuts}

    def create_cuts_vars(self):
        for sample_name, sample_dfs in self.dfs.items():
            for index, metadata in sample_dfs.items():
                dataframe = metadata["df"]
                for cut_name, cut_definition in self.cuts.items():
                    cut_df = dataframe.Filter(cut_definition["expr"])
                    default_factor = self.stage_weight_factors.get(cut_name, "1.f")
                    for variable_name, definition in self._variables_for_cut(cut_name).items():
                        axes = definition["name"].split(":")
                        hist_range = []
                        configured_range = definition["range"]
                        if len(axes) == 1 and isinstance(configured_range, list):
                            hist_range.extend((len(configured_range) - 1, array("d", configured_range)))
                        elif len(configured_range) == len(axes) and all(
                            isinstance(edges, (list, tuple)) for edges in configured_range
                        ):
                            for edges in configured_range:
                                hist_range.extend((len(edges) - 1, array("d", edges)))
                        else:
                            hist_range = list(configured_range)
                        factor = definition.get("studyWeightFactor", default_factor)
                        weight_column = "weight"
                        weighted_df = cut_df
                        if factor not in ("1", "1.", "1.f", "1.0"):
                            weight_column = f"closureWeight_{cut_name}_{abs(hash((variable_name, factor))) & 0xffffffff:x}"
                            weighted_df = cut_df.Define(weight_column, f"weight * ({factor})")
                        columns = [f"{variable_name}_{axis}" for axis in range(len(axes))]
                        method = {1: weighted_df.Histo1D, 2: weighted_df.Histo2D, 3: weighted_df.Histo3D}[len(axes)]
                        result = method((f"{cut_name}_{variable_name}", "", *tuple(hist_range)), *columns, weight_column)
                        self.results[cut_name][variable_name].setdefault(sample_name, {})[index] = ROOT.RDF.Experimental.VariationsFor(result)

    def convertResults(self):
        all_cuts, all_variables = self.cuts, self.variables
        try:
            for cut_name in all_cuts:
                self.cuts = {cut_name: all_cuts[cut_name]}
                self.variables = self._variables_for_cut(cut_name, all_variables)
                super().convertResults()
        finally:
            self.cuts, self.variables = all_cuts, all_variables

    def _save_sparse(self):
        output = ROOT.TFile(self.outputFileMap, "recreate")
        try:
            for cut_name, cut_results in self.results.items():
                output.mkdir(cut_name)
                for variable_name, variable_results in cut_results.items():
                    public_name = self.variables[variable_name].get("outputName")
                    if not public_name:
                        public_name = variable_name[len(self.remappedVariables[variable_name]):] if variable_name in self.remappedVariables else variable_name
                    output.mkdir(f"{cut_name}/{public_name}")
                    output.cd(f"/{cut_name}/{public_name}")
                    for sample_name, indexed in variable_results.items():
                        merged = {}
                        for variations in indexed.values():
                            for variation_name, histogram in variations.items():
                                if variation_name not in merged:
                                    merged[variation_name] = histogram.Clone()
                                else:
                                    merged[variation_name].Add(histogram)
                        for variation_name, histogram in merged.items():
                            suffix = "" if variation_name == "nominal" else f"_{variation_name}"
                            histogram.SetName(f"histo_{sample_name}{suffix}")
                            histogram.SetTitle(histogram.GetName())
                            histogram.Write()
        finally:
            output.Close()

    saveResults = _save_sparse
    mergeSaveResults = _save_sparse
    mergeAndSaveResults = _save_sparse


if __name__ == "__main__":
    ROOT.gInterpreter.Declare('#include "headers.hh"')
    exec(open("script.py").read(), globals(), globals())
    runner = RunAnalysis(samples, aliases, variables, cuts, nuisances, lumi, limit=globals().get("limitEvents", -1), remote_io_settings=globals().get("remoteIO"))
    runner.run()
