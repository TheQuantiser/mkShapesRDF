#!/usr/bin/env python3
"""
Validate ZZ_CR non-2024 MC storage paths against cmshww_HWWNano_file_list_22to25.txt.

Matching rule (for each year/sample):
  1) ignore any line containing "_OLD"
  2) require ".../<mc.production>/<mc.steps>/..."
  3) require filename token "nanoLatino_<sample>__part"

This script reports whether each configured sample is found and which tree-base
directory(ies) contain matching lines.
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

    print("Result: all non-2024 configured MC samples are FOUND in the file list.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
