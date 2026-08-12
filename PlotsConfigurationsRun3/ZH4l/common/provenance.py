"""Compact reproducibility record; generated records belong in output dirs."""

import subprocess


def build_provenance(era, samples, cuts, variables, weights, runtime):
    try:
        sha = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], text=True, stderr=subprocess.DEVNULL
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        sha = "unknown"
    return {
        "git_sha": sha,
        "era": era,
        "samples": sorted(samples),
        "cuts": sorted(cuts),
        "variables": sorted(variables),
        "weights": weights,
        "runtime_endpoint": runtime.get("xrdReadEndpoint"),
    }
