#!/usr/bin/env python3
"""Inspect the compact category-variable plan without discovering input files."""

import argparse
from collections import Counter
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
        SAMPLE_PROFILE=args.sample_profile,
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
    sample_scope = state["resolve_sample_selection"](
        year_cfg,
        full_cfg,
        args.sample_profile,
        args.sample_filter,
    )
    category_variables = state["CATEGORY_VARIABLES"]
    input_files = int(os.environ.get("INPUT_FILE_COUNT", "0"))
    files_per_job = int(os.environ.get("FILES_PER_JOB", "10"))
    actions = sum(len(names) for names in category_variables.values())
    metadata = state["CATEGORY_METADATA"]
    categories_by_region = Counter(
        item["physics_region"] for item in metadata.values()
    )
    categories_by_view_type = Counter(
        item["view_type"] for item in metadata.values()
    )
    actions_by_region = Counter()
    actions_by_view_type = Counter()
    for category_id, names in category_variables.items():
        actions_by_region[metadata[category_id]["physics_region"]] += len(names)
        actions_by_view_type[metadata[category_id]["view_type"]] += len(names)
    nuisance_multiplier = int(os.environ.get("SYSTEMATIC_ACTION_MULTIPLIER", "1"))
    return {
        "year": args.year,
        "analysis_pass": args.analysis_pass,
        "category_profile": args.category_profile,
        "histogram_profile": args.histogram_profile,
        "sample_profile": sample_scope["name"],
        "sample_profile_groups": list(sample_scope["plot_groups"]),
        "sample_profile_outputs": list(sample_scope["output_names"]),
        "sample_selection_source": sample_scope["selection_source"],
        "active_sample_outputs": list(sample_scope["active_output_names"]),
        "nonprompt_background_included": False,
        "physics_regions": sorted(
            {item["physics_region"] for item in state["CATEGORY_METADATA"].values()}
        ),
        "physics_region_count": len(
            {item["physics_region"] for item in state["CATEGORY_METADATA"].values()}
        ),
        "final_categories": list(state["CATEGORY_METADATA"]),
        "final_category_count": len(state["CATEGORY_METADATA"]),
        "categories_by_region": dict(sorted(categories_by_region.items())),
        "categories_by_view_type": dict(sorted(categories_by_view_type.items())),
        "registry_variable_count": len(state["VARIABLE_REGISTRY"]),
        "active_variable_count": len(state["variables"]),
        "variables_per_category": category_variables,
        "category_variable_histogram_actions": actions,
        "actions_by_region": dict(sorted(actions_by_region.items())),
        "actions_by_view_type": dict(sorted(actions_by_view_type.items())),
        "nominal_action_estimate": actions,
        "systematic_action_estimate": actions * nuisance_multiplier if args.systematics else 0,
        "configured_process_count": len(sample_scope["active_output_names"]),
        "all_resolved_process_count": len(overlap["output_names"]) + 1,
        "input_file_count": input_files,
        "estimated_jobs": (input_files + files_per_job - 1) // files_per_job if input_files else None,
        "files_per_job": files_per_job,
        "pre_refactor_category_count": 46,
        "pre_refactor_variable_count": 509,
        "pre_refactor_action_count": 23414,
        "action_reduction_factor": 23414 / actions,
        "expected_linear_plot_count": actions,
        "expected_log_plot_count": actions,
        "expected_total_plot_count": 2 * actions,
    }


def build_profile_comparison(args):
    profiles = ("minimal", "standard", "flavor", "stream", "trigger", "detailed")
    comparison = {}
    for profile in profiles:
        profile_args = argparse.Namespace(**vars(args))
        profile_args.category_profile = profile
        plan = build_plan(profile_args)
        comparison[profile] = {
            key: plan[key]
            for key in (
                "final_category_count", "categories_by_region",
                "categories_by_view_type", "active_variable_count",
                "category_variable_histogram_actions", "actions_by_region",
                "actions_by_view_type", "expected_linear_plot_count",
                "expected_log_plot_count", "expected_total_plot_count",
                "action_reduction_factor",
            )
        }
    comparison["standard_to_minimal_action_ratio"] = (
        comparison["standard"]["category_variable_histogram_actions"]
        / comparison["minimal"]["category_variable_histogram_actions"]
    )
    comparison["old_to_standard_action_reduction_factor"] = (
        23414 / comparison["standard"]["category_variable_histogram_actions"]
    )
    return comparison


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--year", default=os.environ.get("YEAR", "2024"))
    parser.add_argument("--analysis-pass", default=os.environ.get("ANALYSIS_PASS", "ALL"))
    parser.add_argument("--category-profile", default=os.environ.get("CATEGORY_PROFILE", "standard"))
    parser.add_argument("--histogram-profile", default=os.environ.get("HISTOGRAM_PROFILE", "analysis"))
    parser.add_argument("--sample-profile", default=os.environ.get("SAMPLE_PROFILE", "commissioning"))
    parser.add_argument("--sample-filter", default=os.environ.get("SAMPLE_FILTER"))
    parser.add_argument("--systematics", action="store_true")
    parser.add_argument("--write-profile-comparison", action="store_true")
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
    if args.write_profile_comparison:
        comparison = build_profile_comparison(args)
        comparison_output = (
            Path(__file__).resolve().parent
            / "development" / "category_profile_comparison.json"
        )
        comparison_output.write_text(
            json.dumps(comparison, indent=2, sort_keys=True) + "\n"
        )
        print(f"Wrote {comparison_output}")


if __name__ == "__main__":
    main()
