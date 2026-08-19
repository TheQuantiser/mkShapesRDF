#!/usr/bin/env python3
"""Validate pinned plot inputs and print or execute supported plot commands."""

import argparse
import hashlib
import json
from pathlib import Path
import shlex
import subprocess
import sys


LEAF = Path(__file__).resolve().parent
DEFAULT_MANIFEST = LEAF / "plot_reproduction.json"
PLOTTER = LEAF / "plot_run_stability.py"


def _sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _load_manifest(path):
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema_version") != 1:
        raise ValueError("plot_reproduction.json schema_version must be 1")
    datasets = payload.get("datasets")
    if not isinstance(datasets, list) or not datasets:
        raise ValueError("plot_reproduction.json requires a nonempty datasets list")
    eras = [item.get("era") for item in datasets]
    if any(not isinstance(era, str) or not era for era in eras):
        raise ValueError("Every reproduction dataset needs a nonempty era")
    if len(eras) != len(set(eras)):
        raise ValueError("Reproduction dataset eras must be unique")
    return payload


def _resolve_dataset(item):
    resolved = {"era": item["era"]}
    for role in ("config", "input"):
        path = (LEAF / item[role]).resolve()
        try:
            path.relative_to(LEAF)
        except ValueError as exc:
            raise ValueError(f"{role} escapes the RunStability leaf: {path}") from exc
        if not path.is_file():
            raise FileNotFoundError(f"Missing {role} for {item['era']}: {path}")
        expected = item.get(f"{role}_sha256")
        actual = _sha256(path)
        if actual != expected:
            raise RuntimeError(
                f"{item['era']} {role} hash mismatch: expected={expected}, actual={actual}"
            )
        resolved[role] = path
        resolved[f"{role}_sha256"] = actual
    return resolved


def _datasets(manifest):
    return [_resolve_dataset(item) for item in manifest["datasets"]]


def _multi_era_command(kind, datasets, args):
    command = [sys.executable, str(PLOTTER), kind]
    for item in datasets:
        command.extend(
            ["--dataset", item["era"], str(item["config"]), str(item["input"])]
        )
    command.extend(
        [
            "--category",
            args.category,
            "--observable",
            args.observable,
            "--luminosity-source",
            "auto",
            "--output-dir",
            str(Path(args.output_dir).resolve()),
        ]
    )
    return command


def _period_command(datasets, args):
    matching = [item for item in datasets if item["era"] == args.era]
    if len(matching) != 1:
        raise ValueError(f"Manifest has no unique dataset for era {args.era!r}")
    item = matching[0]
    return [
        sys.executable,
        str(PLOTTER),
        "period-plot",
        "--config",
        str(item["config"]),
        "--input",
        str(item["input"]),
        "--category",
        args.category,
        "--observable",
        args.observable,
        "--period",
        args.period,
        "--luminosity-source",
        "auto",
        "--output-dir",
        str(Path(args.output_dir).resolve()),
    ]


def _parser():
    parser = argparse.ArgumentParser(
        description="Reproduce plots from the exact retained RunStability campaign"
    )
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    subparsers = parser.add_subparsers(dest="action", required=True)
    subparsers.add_parser("validate", help="verify all pinned input hashes")
    for action in ("ratio-vs-run", "chi2-vs-run"):
        command = subparsers.add_parser(action)
        command.add_argument("--category", default="DY_ALL")
        command.add_argument("--observable", default="Z0_mass")
        command.add_argument("--output-dir", required=True)
        command.add_argument("--execute", action="store_true")
    period = subparsers.add_parser("period-plot")
    period.add_argument("--era", required=True)
    period.add_argument("--period", required=True)
    period.add_argument("--category", default="DY_ALL")
    period.add_argument("--observable", default="Z0_mass")
    period.add_argument("--output-dir", required=True)
    period.add_argument("--execute", action="store_true")
    return parser


def main(argv=None):
    args = _parser().parse_args(argv)
    manifest_path = args.manifest.expanduser().resolve()
    manifest = _load_manifest(manifest_path)
    datasets = _datasets(manifest)
    if args.action == "validate":
        print(
            json.dumps(
                {
                    "status": "passed",
                    "campaign": manifest.get("campaign"),
                    "datasets": datasets,
                },
                default=str,
                indent=2,
                sort_keys=True,
            )
        )
        return 0
    if args.action == "period-plot":
        command = _period_command(datasets, args)
    else:
        command = _multi_era_command(args.action, datasets, args)
    print(shlex.join(command))
    if args.execute:
        subprocess.run(command, check=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
