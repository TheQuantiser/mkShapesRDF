"""Minimal PairingStudy runner with per-variable diagnostic weights."""

from array import array

import ROOT

from mkShapesRDF.shapeAnalysis.runner import RunAnalysis as _CoreRunAnalysis


class RunAnalysis(_CoreRunAnalysis):
    """Retain the core graph while allowing a studyWeight at booking time."""

    def __init__(self, samples, aliases, variables, cuts, nuisances, lumi, *args, **kwargs):
        tree_variables = [name for name, cfg in variables.items() if "tree" in cfg]
        if tree_variables:
            raise RuntimeError(
                "PairingStudy is histogram-only; tree variables are disabled: "
                + ", ".join(tree_variables)
            )
        super().__init__(
            samples, aliases, variables, cuts, nuisances, lumi, *args, **kwargs
        )

    def create_cuts_vars(self):
        for sample_name in self.dfs:
            for index in self.dfs[sample_name]:
                dataframe = self.dfs[sample_name][index]["df"]
                for cut_name, cut_definition in self.cuts.items():
                    cut_df = dataframe.Filter(cut_definition["expr"])
                    for variable_name, definition in self.variables.items():
                        axes = definition["name"].split(":")
                        if len(axes) > 3:
                            raise RuntimeError(
                                f"{variable_name} has unsupported dimension {len(axes)}"
                            )
                        if len(definition["range"]) == len(axes):
                            hist_range = []
                            for edges in definition["range"]:
                                hist_range.extend([len(edges) - 1, array("d", edges)])
                        else:
                            hist_range = list(definition["range"])
                        columns = [
                            f"{variable_name}_{axis}" for axis in range(len(axes))
                        ]
                        histogram_method = {
                            1: cut_df.Histo1D,
                            2: cut_df.Histo2D,
                            3: cut_df.Histo3D,
                        }[len(axes)]
                        weight_column = definition.get("studyWeight", "weight")
                        histogram = histogram_method(
                            (f"{cut_name}_{variable_name}", "", *tuple(hist_range)),
                            *columns,
                            weight_column,
                        )
                        self.results[cut_name][variable_name].setdefault(
                            sample_name, {}
                        )[index] = histogram
        for cut_name in self.cuts:
            for variable_name in self.variables:
                for sample_name in self.dfs:
                    for index in self.dfs[sample_name]:
                        result = self.results[cut_name][variable_name][sample_name][
                            index
                        ]
                        self.results[cut_name][variable_name][sample_name][
                            index
                        ] = ROOT.RDF.Experimental.VariationsFor(result)


if __name__ == "__main__":
    ROOT.gInterpreter.Declare('#include "headers.hh"')
    exec(open("script.py").read(), globals(), globals())
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
