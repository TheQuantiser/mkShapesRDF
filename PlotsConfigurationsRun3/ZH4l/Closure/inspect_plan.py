#!/usr/bin/env python3
"""Inspect the closure graph without event reads; fail closed on plan budgets."""

from __future__ import annotations

import argparse
import json
import math
import os
import runpy
import sys
from types import SimpleNamespace
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
FAMILY_DIR = HERE.parent
for _path in (HERE, FAMILY_DIR):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

from common.eras import resolve_sample_selection  # noqa: E402
from study_config import SUPPORTED_ERAS, build_categories, load_live_json  # noqa: E402


def _inventory(year, profile):
    full = load_live_json()
    cfg = full["years"][year]
    resolved = resolve_sample_selection(cfg, full, "presentation")
    outputs = list(resolved["active_output_names"])
    if profile == "major":
        owners = {}
        for group, definition in full["plot_groups"].items():
            for sample in definition.get("samples", ()):
                owners[sample] = group
        keep = {"DY", "ZZ", "WZ", "Vg", "VgS", "top", "ttV_tZ"}
        outputs = [sample for sample in outputs if sample == "DATA" or owners.get(sample) in keep]
    return outputs


def inspect(year, profile="full", closure_profile="default", files_per_job=10, config_json=None):
    if year not in SUPPORTED_ERAS:
        raise ValueError(f"Unsupported era {year}")
    if profile not in ("major", "full"):
        raise ValueError("profile must be major or full")
    os.environ["CLOSURE_PROFILE"] = closure_profile
    # Load by absolute path.  Several ordinary PlotsConfigurations leaves use
    # the generic module names ``cuts`` and ``variables``; importing by name
    # can otherwise pick a sibling leaf in a combined test/session.
    cuts = SimpleNamespace(**runpy.run_path(str(HERE / "cuts.py")))
    variables = SimpleNamespace(**runpy.run_path(str(HERE / "variables.py")))

    inputs = None
    if config_json:
        payload = json.loads(Path(config_json).read_text())
        samples = payload.get("samples", {})
        inputs = sum(len(item.get("name", ())) for item in samples.values())
    categories = len(cuts.cuts)
    actions = variables.HISTOGRAM_ACTION_COUNT
    if categories > 60 and os.environ.get("ALLOW_LARGE_PLAN") != "1":
        raise RuntimeError(f"category budget exceeded: {categories} > 60")
    if actions > 300 and os.environ.get("ALLOW_LARGE_PLAN") != "1":
        raise RuntimeError(f"histogram action budget exceeded: {actions} > 300")
    families = Counter()
    for category, names in variables.CATEGORY_VARIABLES.items():
        if category in variables.PRIMARY_STAGES:
            family = "primary"
        elif category.startswith("N1_"):
            family = "nminus1"
        elif "EXTRA" in category:
            family = "extra_lepton"
        elif category.endswith(("_ZEE", "_ZMM")):
            family = "flavor"
        elif category.endswith(("_4E", "_4MU", "_2E2MU")):
            family = "topology"
        elif category.startswith("PT_"):
            family = "pt_contract"
        elif "_TRGPRIO_" in category:
            family = "trigger"
        elif "_STREAM_" in category:
            family = "stream"
        else:
            family = "focused_cross"
        families[family] += len(names)
    sample_inventory = _inventory(year, profile)
    return {
        "year": year,
        "sample_profile": profile,
        "sample_count": len(sample_inventory),
        "samples": sample_inventory,
        "input_file_count": inputs,
        "category_count": categories,
        "histogram_action_count": actions,
        "actions_by_study_family": dict(sorted(families.items())),
        "files_per_job": files_per_job,
        "estimated_jobs": None if inputs is None else math.ceil(inputs / files_per_job),
        "no_trees": not any("tree" in definition for definition in variables.variables.values()),
        "nonprompt_fake_background_included": False,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--year", choices=SUPPORTED_ERAS, default="2024")
    parser.add_argument("--sample-profile", choices=("major", "full"), default="full")
    parser.add_argument("--closure-profile", choices=("default", "focused_cross"), default="default")
    parser.add_argument("--files-per-job", type=int, default=10)
    parser.add_argument("--config-json")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    result = inspect(args.year, args.sample_profile, args.closure_profile, args.files_per_job, args.config_json)
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        for key, value in result.items():
            print(f"{key}: {value}")
        print("limitation: Nonprompt/fake background is not included.")


if __name__ == "__main__":
    main()
