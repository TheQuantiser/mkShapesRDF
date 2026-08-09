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
        self.cut_weight_factors = self.resolve_cut_weight_factors(cuts)
        super().__init__(samples, aliases, variables, cuts, nuisances, lumi, *args, **kwargs)

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
        try:
            for cut_name, cut_definition in all_cuts.items():
                factor = self.cut_weight_factors.get(cut_name, "1.f")
                self.cuts = {cut_name: cut_definition}
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
