#!/usr/bin/env python3
"""Count declared category projections on bounded NanoAOD inputs.

This tool constructs only filters and Count actions.  It dependency-slices the
normal alias dictionary from the category expressions, so no histogram or
correction-weight graph is booked.
"""

import argparse
from copy import deepcopy
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import runpy
import sys

import ROOT

from mkShapesRDF.lib.parse_cpp import ParseCpp
from mkShapesRDF.shapeAnalysis.runner import RunAnalysis


HERE = Path(__file__).resolve().parent


def _alias_dependencies(expression):
    return set(ParseCpp.listOfVariables(ParseCpp.parse(expression)))


def _needed_aliases(aliases, expressions):
    needed = set()
    required = set()
    for expression in expressions:
        required.update(_alias_dependencies(expression))
    changed = True
    while changed:
        changed = False
        for name, definition in aliases.items():
            if name not in required or name in needed:
                continue
            needed.add(name)
            changed = True
            if "expr" in definition:
                required.update(_alias_dependencies(definition["expr"]))
            if "exprSlot" in definition:
                required.update(_alias_dependencies(definition["exprSlot"][1]))
            if "args" in definition:
                required.update(_alias_dependencies(definition["args"]))
    return {name: deepcopy(value) for name, value in aliases.items() if name in needed}


def _load_state(year, is_data, available_branches):
    os.environ.update(
        YEAR=year,
        ANALYSIS_PASS="RUN_STABILITY",
        RUN_STABILITY_PRODUCTION_PROFILE="dy",
        RUN_STABILITY_REGION="DY",
        SELECTION_PROFILE="dy",
        CATEGORY_PROFILE="standard",
        HISTOGRAM_PROFILE="analysis",
        SAMPLE_PROFILE="presentation",
        HISTOGRAMS="1",
        ENABLE_SYSTEMATICS="0",
        CONFIG_INCLUDE_BASE=str(HERE.parents[2]),
    )
    sample_name = "DATA" if is_data else "MC"
    sample_cfg = {"isData": True} if is_data else {}
    state = {
        "CONFIG_DIR": str(HERE),
        "CONFIG_INCLUDE_BASE": str(HERE.parents[2]),
        "HISTOGRAMS": True,
        "AVAILABLE_BRANCHES": set(available_branches),
        "samples": {sample_name: sample_cfg},
        "YEAR": year,
        "ANALYSIS_PASS": "RUN_STABILITY",
        "RUN_STABILITY_REGION": "DY",
        "CATEGORY_PROFILE": "standard",
        "HISTOGRAM_PROFILE": "analysis",
        "SAMPLE_PROFILE": "presentation",
    }
    state.update(runpy.run_path(str(HERE / "year_config.py"), init_globals=state))
    _, year_cfg, _ = state["load_selected_year"]()
    state["lumi"] = float(year_cfg["lumi_fb"])
    for filename in (
        "selection_config.py",
        "run_stability_config.py",
        "aliases.py",
        "cuts.py",
    ):
        state.update(runpy.run_path(str(HERE / filename), init_globals=state))
    return state, sample_name


def count_input(args):
    ROOT.gInterpreter.Declare(
        f'#include "{HERE.parents[2] / "mkShapesRDF" / "include" / "headers.hh"}"'
    )
    remote_io = {
        "inputAccessMode": "stage-in",
        "xrdReadEndpoint": args.read_endpoint,
        "stageInCleanup": "always",
        "preserveStageInOnFailure": False,
        "remoteTransferRetries": args.transfer_retries,
    }
    prepared, _, stage_manager = RunAnalysis.prepareInputFiles(
        args.input, [], remote_io
    )
    try:
        chain = RunAnalysis.getTTreeNomAndFriends(prepared, [])
        available = [branch.GetName() for branch in chain.GetListOfBranches()]
        state, sample_name = _load_state(args.year, args.kind == "DATA", available)
        metadata = state["CATEGORY_METADATA"]
        declared_lines = set()
        for definition in state["aliases"].values():
            for line in definition.get("linesToAdd", []):
                if line in declared_lines:
                    continue
                ROOT.gInterpreter.Declare(line.replace("RPLME_nThreads", "1"))
                declared_lines.add(line)
        expressions = [state["preselections"]]
        expressions.extend(item["parent_expression"] for item in metadata.values())
        expressions.extend(item["split_expression"] for item in metadata.values())
        aliases = _needed_aliases(state["aliases"], expressions)
        sample = (sample_name, prepared, "1.f", 0, args.kind == "DATA", {})
        runner = RunAnalysis(
            [sample],
            aliases,
            {},
            {"cuts": state["cuts"], "preselections": state["preselections"]},
            {},
            1.0,
            limit=args.events,
            remote_io_settings={"inputAccessMode": "as-configured"},
        )
        runner.loadAliases()
        df = runner.dfs[sample_name][0]["df"]
        parent_actions = {}
        for region in dict.fromkeys(
            item["physics_region"] for item in metadata.values()
        ):
            parent = next(
                item["parent_expression"]
                for item in metadata.values()
                if item["physics_region"] == region
            )
            parent_actions[region] = df.Filter(
                f"({state['preselections']}) && ({parent})"
            ).Count()
        category_actions = {
            category_id: df.Filter(item["full_cut_expression"]).Count()
            for category_id, item in metadata.items()
        }
        parent_counts = {
            name: int(action.GetValue()) for name, action in parent_actions.items()
        }
        category_counts = {
            name: int(action.GetValue()) for name, action in category_actions.items()
        }
        entries = int(chain.GetEntries())
        examined = min(entries, args.events) if args.events >= 0 else entries
        categories = {}
        for category_id, count in category_counts.items():
            item = metadata[category_id]
            parent_count = parent_counts[item["physics_region"]]
            categories[category_id] = {
                "count": count,
                "fraction_of_parent": count / parent_count if parent_count else None,
                "physics_region": item["physics_region"],
                "view_type": item["view_type"],
                "partition_family": item["partition_family"],
            }
        return {
            "year": args.year,
            "kind": args.kind,
            "label": args.label,
            "inputs": list(args.input),
            "tree_entries": entries,
            "events_examined": examined,
            "dependency_sliced_alias_count": len(aliases),
            "parent_counts": parent_counts,
            "categories": categories,
        }
    finally:
        stage_manager.cleanup(success=sys.exc_info()[0] is None)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--year", required=True)
    parser.add_argument("--kind", choices=("DATA", "MC"), required=True)
    parser.add_argument("--label", required=True)
    parser.add_argument("--input", action="append", required=True)
    parser.add_argument("--events", type=int, default=100000)
    parser.add_argument("--read-endpoint", default="root://eoscms.cern.ch")
    parser.add_argument("--transfer-retries", type=int, default=2)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    result = {
        "schema_version": 1,
        "recorded_utc": datetime.now(timezone.utc).isoformat(),
        "counting_model": "dependency-sliced aliases plus Filter/Count actions; no histograms or correction weights",
        "sample": count_input(args),
    }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
