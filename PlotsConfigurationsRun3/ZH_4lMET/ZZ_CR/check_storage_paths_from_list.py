#!/usr/bin/env python3
"""
Validate ZZ_CR storage paths against cmshww_HWWNano_file_list_22to25.txt.

Matching rule (MC):
  1) ignore any line containing "_OLD"
  2) require ".../<mc.production>/<mc.steps>/..."
  3) require filename token "nanoLatino_<sample>__part"

Matching rule (DATA):
  1) ignore any line containing "_OLD"
  2) require filename token "nanoLatino_<dataset>_<runTag>__part"
  3) accept either directory layout:
       - .../<data.reco>_<stream>/<data.steps>/...
       - .../<data.reco>/<data.steps>/...

This script reports FOUND/NOT FOUND for:
  - MC samples (non-2024, as originally requested)
  - DATA samples per run-tag/era (all configured years)
"""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
CFG = ROOT / "zzcr_year_config.json"
FILE_LIST = ROOT / "cmshww_HWWNano_file_list_22to25.txt"


def _load_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def _load_file_list(path: Path) -> list[str]:
    lines = [line.strip() for line in path.read_text(encoding="utf-8").splitlines()]
    return [line for line in lines if line and "_OLD" not in line]


def _tree_base(path: str) -> str:
    # /eos/cms/store/group/phys_higgs/cmshww/<user>/HWWNano/<prod>/<steps>/file.root
    #                                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ = first 9 segments
    return "/".join(path.split("/")[:9])


def _resolve_data_run_tags(year_cfg: dict) -> list[str]:
    tags = []
    for run_item in year_cfg["data"]["runs"]:
        if isinstance(run_item, str):
            tags.append(run_item)
        elif isinstance(run_item, (list, tuple)) and len(run_item) >= 2:
            tags.append(run_item[1])
        else:
            raise ValueError(f"Unsupported data.runs entry: {run_item!r}")
    return tags


def _match_any(paths: list[str], token: str) -> bool:
    return any(token in path for path in paths)


def main() -> int:
    cfg = _load_json(CFG)
    files = _load_file_list(FILE_LIST)
    years = cfg["years"]

    print(f"Config: {CFG}")
    print(f"File list: {FILE_LIST}")
    print("Excluded lines containing '_OLD'.\n")

    any_missing = False

    for year, year_cfg in years.items():
        if year == "2024":
            continue

        mc = year_cfg["mc"]
        production = mc["production"]
        steps = mc["steps"]
        sample_names = mc["samples"]

        print(f"[{year}]")
        print(f"  production = {production}")
        print(f"  steps      = {steps}")

        for sample_name in sample_names:
            token_prod_step = f"/{production}/{steps}/"
            token_sample = f"nanoLatino_{sample_name}__part"
            matches = [
                path
                for path in files
                if token_prod_step in path and token_sample in path
            ]
            bases = sorted({_tree_base(path) for path in matches})
            if matches:
                print(
                    f"  - {sample_name}: FOUND ({len(matches)} line(s)); tree_base_dir candidates = {bases}"
                )
            else:
                any_missing = True
                print(f"  - {sample_name}: NOT FOUND")
        print()

    if any_missing:
        print("Result: one or more samples are NOT FOUND.")
        return 2

    print("Result (MC): all non-2024 configured MC samples are FOUND in the file list.\n")

    # DATA validation for all configured years and run tags (eras).
    for year, year_cfg in years.items():
        data = year_cfg["data"]
        reco = data["reco"]
        steps = data["steps"]
        year_run_tags = _resolve_data_run_tags(year_cfg)

        print(f"[{year}] DATA")
        print(f"  reco  = {reco}")
        print(f"  steps = {steps}")

        for sample in data["samples"]:
            dataset = sample["dataset"]
            stream = sample["stream"]
            sample_run_tags = sample.get("runs", year_run_tags)
            missing_run_tags = []

            for run_tag in sample_run_tags:
                filename_token = f"nanoLatino_{dataset}_{run_tag}__part"
                by_stream_token = f"/{reco}_{stream}/{steps}/"
                legacy_token = f"/{reco}/{steps}/"

                found = False
                if _match_any(
                    files, by_stream_token + filename_token
                ) or _match_any(files, legacy_token + filename_token):
                    found = True

                if not found:
                    missing_run_tags.append(run_tag)

            if missing_run_tags:
                any_missing = True
                print(
                    f"  - {dataset} (stream={stream}): NOT FOUND for run tags {missing_run_tags}"
                )
            else:
                print(
                    f"  - {dataset} (stream={stream}): FOUND for all run tags ({len(sample_run_tags)})"
                )
        print()

    if any_missing:
        print("Result (DATA): one or more dataset run tags are NOT FOUND.")
        return 2

    print("Result (DATA): all configured dataset run tags are FOUND in the file list.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
