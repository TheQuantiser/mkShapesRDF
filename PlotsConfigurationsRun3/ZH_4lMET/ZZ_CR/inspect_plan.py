#!/usr/bin/env python3
"""Inspect the compact category-variable plan without discovering input files."""

import argparse
import json
import os
from pathlib import Path
import runpy


def build_plan(args):
    here = Path(__file__).resolve().parent
    os.environ.update(
        YEAR=args.year,
        ANALYSIS_PASS=args.analysis_pass,
        CATEGORY_PROFILE=args.category_profile,
        HISTOGRAM_PROFILE=args.histogram_profile,
        HISTOGRAMS="1",
        ENABLE_SYSTEMATICS="1" if args.systematics else "0",
    )
    state = {"CONFIG_DIR": str(here), "HISTOGRAMS": True}
    for filename in (
        "year_config.py", "selection_config.py", "cuts.py", "variables.py"
    ):
        state.update(runpy.run_path(str(here / filename), init_globals=state))
    _, year_cfg, full_cfg = state["load_selected_year"]()
    overlap = state["resolve_overlap_model"](year_cfg, full_cfg)
    category_variables = state["CATEGORY_VARIABLES"]
    input_files = int(os.environ.get("INPUT_FILE_COUNT", "0"))
    files_per_job = int(os.environ.get("FILES_PER_JOB", "10"))
    actions = sum(len(names) for names in category_variables.values())
    nuisance_multiplier = int(os.environ.get("SYSTEMATIC_ACTION_MULTIPLIER", "1"))
    return {
        "year": args.year,
        "analysis_pass": args.analysis_pass,
        "category_profile": args.category_profile,
        "histogram_profile": args.histogram_profile,
        "physics_regions": sorted(
            {item["physics_region"] for item in state["CATEGORY_METADATA"].values()}
        ),
        "physics_region_count": len(
            {item["physics_region"] for item in state["CATEGORY_METADATA"].values()}
        ),
        "final_categories": list(state["CATEGORY_METADATA"]),
        "final_category_count": len(state["CATEGORY_METADATA"]),
        "registry_variable_count": len(state["VARIABLE_REGISTRY"]),
        "active_variable_count": len(state["variables"]),
        "variables_per_category": category_variables,
        "category_variable_histogram_actions": actions,
        "nominal_action_estimate": actions,
        "systematic_action_estimate": actions * nuisance_multiplier if args.systematics else 0,
        "configured_process_count": len(overlap["output_names"]) + 1,
        "input_file_count": input_files,
        "estimated_jobs": (input_files + files_per_job - 1) // files_per_job if input_files else None,
        "files_per_job": files_per_job,
        "pre_refactor_category_count": 46,
        "pre_refactor_variable_count": 509,
        "pre_refactor_action_count": 23414,
        "action_reduction_factor": 23414 / actions,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--year", default=os.environ.get("YEAR", "2024"))
    parser.add_argument("--analysis-pass", default=os.environ.get("ANALYSIS_PASS", "ALL"))
    parser.add_argument("--category-profile", default=os.environ.get("CATEGORY_PROFILE", "minimal"))
    parser.add_argument("--histogram-profile", default=os.environ.get("HISTOGRAM_PROFILE", "analysis"))
    parser.add_argument("--systematics", action="store_true")
    parser.add_argument(
        "--output", default=str(Path(__file__).resolve().parent / "development" / "booking_plan.json")
    )
    args = parser.parse_args()
    plan = build_plan(args)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(plan, indent=2, sort_keys=True) + "\n")
    print(json.dumps(plan, indent=2, sort_keys=True))
    print(f"Wrote {output}")


if __name__ == "__main__":
    main()
