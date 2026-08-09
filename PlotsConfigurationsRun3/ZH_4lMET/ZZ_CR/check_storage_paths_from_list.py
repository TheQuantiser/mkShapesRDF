#!/usr/bin/env python3
"""Verify materialized ZZ_CR storage paths against an all-parts text inventory.

The inventory is streamed exactly once.  A successful completeness decision
requires at least one nonzero ``__partN.root`` entry in the non-OLD inventory;
this prevents a traditional part0-only crawl from being mistaken for an
all-parts catalogue.  Individual configured samples may legitimately begin at
part1 (notably ``MuonEG_Run2022F-Prompt-v1``).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import posixpath
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Set, Tuple

from year_config import load_full_config, resolve_data_run_tags, resolve_tree_base_dir


ROOT = Path(__file__).resolve().parent
DEFAULT_CONFIG = ROOT / "year_config.json"
DEFAULT_INVENTORY = ROOT / os.environ.get(
    "STORAGE_FILE_LIST",
    "cmshww_HWWNano_file_list_22to25.txt",
)
FILE_NAME_RE = re.compile(r"^nanoLatino_(?P<sample>.+)__part(?P<part>[0-9]+)[.]root$")


class VerificationError(RuntimeError):
    """Raised when an inventory cannot support a trustworthy decision."""


@dataclass
class ExpectedSample:
    """One configured physical sample/run-tag check."""

    check_id: str
    era: str
    kind: str
    sample: str
    directories: Tuple[str, ...]
    dataset: Optional[str] = None
    stream: Optional[str] = None
    run_tag: Optional[str] = None
    match_count: int = 0
    matched_parts: Set[int] = field(default_factory=set)
    matched_directories: Set[str] = field(default_factory=set)

    @property
    def found(self) -> bool:
        return self.match_count > 0


@dataclass(frozen=True)
class InventoryStatistics:
    """Deterministic statistics collected while streaming the inventory."""

    sha256: str
    bytes_read: int
    lines_total: int
    lines_nonempty: int
    lines_old_excluded: int
    files_valid_nonold: int
    files_part0: int
    files_nonzero_part: int
    maximum_part: int


def _normalize_directory(path: str) -> str:
    """Normalize and validate an absolute POSIX directory."""

    if not isinstance(path, str) or not path.startswith("/"):
        raise VerificationError(f"Expected an absolute POSIX directory, got {path!r}")
    normalized = posixpath.normpath(path)
    if normalized == "/" or normalized != path.rstrip("/"):
        raise VerificationError(f"Non-canonical configured directory: {path!r}")
    return normalized


def _build_expectations(config: Mapping[str, Any]) -> Tuple[List[ExpectedSample], Dict[Tuple[str, str], List[int]]]:
    """Build exact directory/sample keys from the materialized configuration."""

    years = config.get("years")
    if not isinstance(years, Mapping) or not years:
        raise VerificationError("Materialized year configuration has no years mapping")

    checks: List[ExpectedSample] = []
    key_to_checks: Dict[Tuple[str, str], List[int]] = {}

    def add_check(check: ExpectedSample) -> None:
        index = len(checks)
        checks.append(check)
        for directory in check.directories:
            key_to_checks.setdefault((directory, check.sample), []).append(index)

    for era, year_cfg_any in years.items():
        if not isinstance(year_cfg_any, Mapping):
            raise VerificationError(f"Era {era!r} is not a mapping")
        year_cfg = year_cfg_any

        mc = year_cfg.get("mc")
        if not isinstance(mc, Mapping):
            raise VerificationError(f"Era {era!r} has no materialized MC configuration")
        production = mc.get("production")
        steps = mc.get("steps")
        samples = mc.get("samples")
        if not isinstance(production, str) or not isinstance(steps, str):
            raise VerificationError(f"Era {era!r} has invalid MC production/steps")
        if not isinstance(samples, list) or not all(isinstance(item, str) for item in samples):
            raise VerificationError(f"Era {era!r} has invalid MC sample aliases")

        for sample in samples:
            tree_base = resolve_tree_base_dir(year_cfg, "mc", sample_name=sample)
            directory = _normalize_directory(posixpath.join(tree_base, production, steps))
            add_check(
                ExpectedSample(
                    check_id=f"{era}/MC/{sample}",
                    era=str(era),
                    kind="mc",
                    sample=sample,
                    directories=(directory,),
                )
            )

        data = year_cfg.get("data")
        if not isinstance(data, Mapping):
            raise VerificationError(f"Era {era!r} has no materialized DATA configuration")
        reco = data.get("reco")
        data_steps = data.get("steps")
        data_samples = data.get("samples")
        if not isinstance(reco, str) or not isinstance(data_steps, str):
            raise VerificationError(f"Era {era!r} has invalid DATA reco/steps")
        if not isinstance(data_samples, list):
            raise VerificationError(f"Era {era!r} has invalid DATA samples")
        default_runs = resolve_data_run_tags(year_cfg)

        for sample_cfg_any in data_samples:
            if not isinstance(sample_cfg_any, Mapping):
                raise VerificationError(f"Era {era!r} has a non-mapping DATA sample")
            sample_cfg = sample_cfg_any
            dataset = sample_cfg.get("dataset")
            stream = sample_cfg.get("stream")
            if not isinstance(dataset, str) or not isinstance(stream, str):
                raise VerificationError(f"Era {era!r} has invalid DATA dataset/stream")
            tree_base = resolve_tree_base_dir(
                year_cfg,
                "data",
                sample_name=dataset,
                stream_name=stream,
            )
            directories = tuple(
                dict.fromkeys(
                    (
                        _normalize_directory(
                            posixpath.join(tree_base, f"{reco}_{stream}", data_steps)
                        ),
                        _normalize_directory(posixpath.join(tree_base, reco, data_steps)),
                    )
                )
            )
            run_tags = sample_cfg.get("runs", default_runs)
            if not isinstance(run_tags, (list, tuple)) or not all(
                isinstance(run_tag, str) for run_tag in run_tags
            ):
                raise VerificationError(
                    f"Era {era!r} DATA sample {dataset!r} has invalid run tags"
                )
            for run_tag in run_tags:
                physical_sample = f"{dataset}_{run_tag}"
                add_check(
                    ExpectedSample(
                        check_id=f"{era}/DATA/{physical_sample}",
                        era=str(era),
                        kind="data",
                        sample=physical_sample,
                        directories=directories,
                        dataset=dataset,
                        stream=stream,
                        run_tag=run_tag,
                    )
                )

    return checks, key_to_checks


def _stream_inventory(
    inventory_path: Path,
    checks: List[ExpectedSample],
    key_to_checks: Mapping[Tuple[str, str], Sequence[int]],
) -> InventoryStatistics:
    """Stream an inventory, validating syntax and updating matching checks."""

    digest = hashlib.sha256()
    bytes_read = 0
    lines_total = 0
    lines_nonempty = 0
    lines_old_excluded = 0
    files_valid_nonold = 0
    files_part0 = 0
    files_nonzero_part = 0
    maximum_part = 0

    try:
        handle = inventory_path.open("rb")
    except OSError as exc:
        raise VerificationError(f"Cannot open inventory {inventory_path}: {exc}") from exc

    with handle:
        for line_number, raw_line in enumerate(handle, start=1):
            lines_total += 1
            bytes_read += len(raw_line)
            digest.update(raw_line)
            try:
                line = raw_line.decode("utf-8").strip()
            except UnicodeDecodeError as exc:
                raise VerificationError(
                    f"Inventory is not UTF-8 at line {line_number}: {exc}"
                ) from exc
            if not line:
                continue
            lines_nonempty += 1
            if "_OLD" in line:
                lines_old_excluded += 1
                continue
            if not line.startswith("/"):
                raise VerificationError(
                    f"Inventory line {line_number} is not an absolute POSIX path: {line!r}"
                )

            normalized = posixpath.normpath(line)
            if normalized != line:
                raise VerificationError(
                    f"Inventory line {line_number} is not canonical: {line!r}"
                )
            directory, filename = posixpath.split(line)
            if "/HWWNano/" not in directory:
                raise VerificationError(
                    f"Inventory line {line_number} is outside an HWWNano tree: {line!r}"
                )
            match = FILE_NAME_RE.fullmatch(filename)
            if match is None:
                raise VerificationError(
                    f"Inventory line {line_number} has an invalid HWWNano filename: {filename!r}"
                )

            files_valid_nonold += 1
            part = int(match.group("part"))
            maximum_part = max(maximum_part, part)
            if part == 0:
                files_part0 += 1
            else:
                files_nonzero_part += 1

            key = (directory, match.group("sample"))
            for check_index in key_to_checks.get(key, ()):
                check = checks[check_index]
                check.match_count += 1
                check.matched_parts.add(part)
                check.matched_directories.add(directory)

    if files_valid_nonold == 0:
        raise VerificationError("Inventory has no valid non-OLD HWWNano files")
    if files_nonzero_part == 0:
        raise VerificationError(
            "Inventory contains only part0 files; an all-parts text inventory with "
            "at least one nonzero __partN.root entry is required for completeness"
        )

    return InventoryStatistics(
        sha256=digest.hexdigest(),
        bytes_read=bytes_read,
        lines_total=lines_total,
        lines_nonempty=lines_nonempty,
        lines_old_excluded=lines_old_excluded,
        files_valid_nonold=files_valid_nonold,
        files_part0=files_part0,
        files_nonzero_part=files_nonzero_part,
        maximum_part=maximum_part,
    )


def audit_configuration(config: Mapping[str, Any], inventory_path: Path) -> Dict[str, Any]:
    """Return a compact deterministic audit of all configured MC and DATA inputs."""

    checks, key_to_checks = _build_expectations(config)
    statistics = _stream_inventory(inventory_path, checks, key_to_checks)

    era_receipts: Dict[str, Dict[str, List[Dict[str, Any]]]] = {}
    for check in checks:
        era = era_receipts.setdefault(check.era, {"mc": [], "data": []})
        record: Dict[str, Any] = {
            "id": check.check_id,
            "sample": check.sample,
            "status": "found" if check.found else "missing",
            "expected_directories": list(check.directories),
            "match_count": check.match_count,
            "matched_part_summary": {
                "unique_count": len(check.matched_parts),
                "minimum": min(check.matched_parts) if check.matched_parts else None,
                "maximum": max(check.matched_parts) if check.matched_parts else None,
                "contains_part0": 0 in check.matched_parts,
            },
            "matched_directories": sorted(check.matched_directories),
        }
        if check.kind == "data":
            record.update(
                {
                    "dataset": check.dataset,
                    "stream": check.stream,
                    "run_tag": check.run_tag,
                }
            )
        era[check.kind].append(record)

    for era in era_receipts.values():
        era["mc"].sort(key=lambda item: item["id"])
        era["data"].sort(key=lambda item: item["id"])

    missing = [check.check_id for check in checks if not check.found]
    found = len(checks) - len(missing)
    return {
        "schema_version": 1,
        "kind": "zz_cr_all_parts_storage_audit",
        "complete": not missing,
        "inventory": {
            "path": str(inventory_path.resolve()),
            "format": "all_parts_text",
            "sha256": statistics.sha256,
            "bytes_read": statistics.bytes_read,
            "lines_total": statistics.lines_total,
            "lines_nonempty": statistics.lines_nonempty,
            "lines_old_excluded": statistics.lines_old_excluded,
            "files_valid_nonold": statistics.files_valid_nonold,
            "files_part0": statistics.files_part0,
            "files_nonzero_part": statistics.files_nonzero_part,
            "maximum_part": statistics.maximum_part,
            "all_parts_evidence": "nonzero_part_number_observed",
        },
        "summary": {
            "checks_total": len(checks),
            "checks_found": found,
            "checks_missing": len(missing),
            "missing_ids": sorted(missing),
        },
        "eras": dict(sorted(era_receipts.items())),
    }


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _write_receipt(path: Path, receipt: Mapping[str, Any]) -> None:
    """Write stable JSON bytes; no timestamp or runtime-dependent field is added."""

    content = json.dumps(receipt, indent=2, sort_keys=True) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _print_human(receipt: Mapping[str, Any]) -> None:
    inventory = receipt["inventory"]
    summary = receipt["summary"]
    print(f"Inventory: {inventory['path']}")
    print(
        "All-parts evidence: "
        f"{inventory['files_nonzero_part']} nonzero-part files; "
        f"maximum part={inventory['maximum_part']}"
    )
    for era, era_result in receipt["eras"].items():
        print(f"[{era}]")
        for kind in ("mc", "data"):
            missing = [item["sample"] for item in era_result[kind] if item["status"] == "missing"]
            print(
                f"  {kind.upper()}: {len(era_result[kind]) - len(missing)}/"
                f"{len(era_result[kind])} found"
            )
            for sample in missing:
                print(f"    - NOT FOUND: {sample}")
    print(
        f"Result: {'COMPLETE' if receipt['complete'] else 'INCOMPLETE'} "
        f"({summary['checks_found']}/{summary['checks_total']} checks found)."
    )


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "inventory",
        nargs="?",
        type=Path,
        default=DEFAULT_INVENTORY,
        help=(
            "all-parts HWWNano text inventory (default: STORAGE_FILE_LIST or "
            "cmshww_HWWNano_file_list_22to25.txt)"
        ),
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_CONFIG,
        help="schema-v2 year_config.json loaded through year_config.load_full_config",
    )
    parser.add_argument(
        "--receipt",
        type=Path,
        help="optional compact deterministic JSON audit receipt",
    )
    parser.add_argument("--quiet", action="store_true", help="suppress human-readable output")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_argument_parser().parse_args(argv)
    config_path = args.config.resolve()
    inventory_path = args.inventory.resolve()
    try:
        config = load_full_config(str(config_path))
        receipt = audit_configuration(config, inventory_path)
        receipt["config"] = {
            "path": str(config_path),
            "sha256": _sha256_file(config_path),
            "schema_version": config.get("schema_version"),
            "loader": "year_config.load_full_config",
        }
    except (OSError, ValueError, VerificationError) as exc:
        failure = {
            "schema_version": 1,
            "kind": "zz_cr_all_parts_storage_audit",
            "complete": False,
            "error": {"type": type(exc).__name__, "message": str(exc)},
            "config_path": str(config_path),
            "inventory_path": str(inventory_path),
        }
        if args.receipt is not None:
            _write_receipt(args.receipt, failure)
        print(f"ERROR: {exc}", file=sys.stderr)
        return 3

    if args.receipt is not None:
        _write_receipt(args.receipt, receipt)
    if not args.quiet:
        _print_human(receipt)
    return 0 if receipt["complete"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
