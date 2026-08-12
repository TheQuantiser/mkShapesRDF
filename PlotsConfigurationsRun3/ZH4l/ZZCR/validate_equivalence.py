#!/usr/bin/env python3
"""Run protected legacy-vs-new ZZCR event-level equivalence checks.

The legacy source is copied to an ignored temporary directory below ``ZH4l``;
the authoritative ``ZH_4lMET`` tree is never edited or used as an output
location.  Both configurations use native RunAnalysis tree snapshots over the
same real files, after which this script compares selected objects, observables,
predicates, region membership, and nominal weights event by event.
"""

from __future__ import annotations

import argparse
from bisect import bisect_right
from collections import defaultdict
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time


HERE = Path(__file__).resolve().parent
FAMILY = HERE.parent
REPO = FAMILY.parents[1]
LEGACY_SOURCE = REPO / "PlotsConfigurationsRun3" / "ZH_4lMET" / "ZZ_CR"
NEW_SOURCE = HERE
LEGACY_WORK = FAMILY / ".equivalence_legacy"
NEW_WORK = FAMILY / ".equivalence_new"
RESULTS_WORK = FAMILY / ".equivalence_results"
SUPPORTED_ERAS = ("2022", "2022EE", "2023", "2023BPix", "2024")
DEFAULT_SAMPLES = ("ZZ", "ZH")
ZH_SIGNAL_BY_ERA = {
    "2022": "ZH_Hto2Wto2L2Nu_M125",
    "2022EE": "ZH_Hto2Wto2L2Nu_M125",
    "2023": "ZH_Hto2Wto2L2Nu_M125",
    "2023BPix": "ZH_Hto2Wto2L2Nu_M125",
    "2024": "ZH_Zto2L_Hto2Wto2L2Nu_M125",
}

IDENTITY_COLUMNS = ("run", "luminosityBlock", "event")
REGION_COLUMNS = (
    "inZZCR",
    "inZZCR_4e",
    "inZZCR_4mu",
    "inZZCR_2e2mu",
    "inSR_XSF",
    "inSR_XDF",
)
EXACT_COLUMNS = (
    "Z_idx0",
    "Z_idx1",
    "X_idx0",
    "X_idx1",
    "pass4lPt",
    "veto5l",
    "bVeto",
    "nLepton10",
) + REGION_COLUMNS
FLOAT_COLUMNS = (
    "mZ",
    "mX",
    "m4l",
    "ptZ",
    "ptX",
    "pt4l",
    "PuppiMET_pt",
    "minMll4l",
    "weight",
)
COMPARE_COLUMNS = IDENTITY_COLUMNS + EXACT_COLUMNS + FLOAT_COLUMNS
BRANCH_BY_COLUMN = {
    column: (
        column if column in IDENTITY_COLUMNS or column == "weight" else f"eq_{column}"
    )
    for column in COMPARE_COLUMNS
}

HISTOGRAM_AXES = {
    "mZ": ((30, 40, 60, 80, 85, 90, 95, 100, 120), 3),
    "mX": ((30, 40, 60, 80, 85, 90, 95, 100, 120), 3),
    "m4l": ((60, 80, 100, 120, 140, 160, 180, 200, 250, 300, 400, 600), 3),
    "ptZ": ((0, 2, 4, 6, 8, 10, 15, 20, 25, 30, 35, 40, 50, 60, 70, 80, 100, 120), 3),
    "ptX": ((0, 2, 4, 6, 8, 10, 15, 20, 25, 30, 35, 40, 50, 60, 70, 80, 100, 120), 3),
    "pt4l": ((0, 20, 40, 60, 80, 100, 150, 200, 300, 400), 2),
    "PuppiMET_pt": ((0, 10, 20, 30, 40, 50, 80, 100, 120), 3),
    "minMll4l": ((0, 4, 8, 12, 16, 20, 30, 40, 60, 80), 3),
    "nLepton10": ((-0.5, 0.5, 1.5, 2.5, 3.5, 4.5, 5.5, 6.5), 3),
}


LEGACY_TREE_OVERRIDE = r"""

# Event-level migration validation override. Generated in a temporary copy.
from category_config import PHYSICAL_COMMON, SR_XDF, SR_XSF, ZZCR_PARENT

cuts = {"VALIDATION": "1"}
variables = {
    "equivalence": {
        "tree": {
            "run": "run",
            "luminosityBlock": "luminosityBlock",
            "event": "event",
            "eq_Z_idx0": "int(Alt(Z0_idx,0,-1))",
            "eq_Z_idx1": "int(Alt(Z0_idx,1,-1))",
            "eq_X_idx0": "int(Alt(X_idx,0,-1))",
            "eq_X_idx1": "int(Alt(X_idx,1,-1))",
            "eq_mZ": "double(Z0_mass)",
            "eq_mX": "double(X_mass)",
            "eq_m4l": "double(m4l)",
            "eq_ptZ": "double(Z0_pt)",
            "eq_ptX": "double(X_pt)",
            "eq_pt4l": "double(pT4l)",
            "eq_PuppiMET_pt": "double(PuppiMET_pt)",
            "eq_pass4lPt": "bool(Passes4lOrderedPt)",
            "eq_veto5l": "bool(fifthLeptonVeto)",
            "eq_minMll4l": "double(minSelectedPairMass)",
            "eq_bVeto": "bool(physicalBtagVeto)",
            "eq_nLepton10": "int(Sum(Lepton_pt >= 10.f))",
            "eq_inZZCR": "bool(" + ZZCR_PARENT + ")",
            "eq_inZZCR_4e": "bool((" + ZZCR_PARENT + ") && Z0_isEE && X_isEE)",
            "eq_inZZCR_4mu": "bool((" + ZZCR_PARENT + ") && Z0_isMM && X_isMM)",
            "eq_inZZCR_2e2mu": "bool((" + ZZCR_PARENT + ") && ((Z0_isEE && X_isMM) || (Z0_isMM && X_isEE)))",
            "eq_inSR_XSF": "bool((" + PHYSICAL_COMMON + ") && (" + SR_XSF + "))",
            "eq_inSR_XDF": "bool((" + PHYSICAL_COMMON + ") && (" + SR_XDF + "))",
        },
        "cuts": ["VALIDATION"],
    }
}
"""


NEW_TREE_OVERRIDE = r"""

# Event-level migration validation override. Generated in a temporary copy.
cuts = {"VALIDATION": "1"}
variables = {
    "equivalence": {
        "tree": {
            "run": "run",
            "luminosityBlock": "luminosityBlock",
            "event": "event",
            "eq_Z_idx0": "int(Alt(Z_idx,0,-1))",
            "eq_Z_idx1": "int(Alt(Z_idx,1,-1))",
            "eq_X_idx0": "int(Alt(X_idx,0,-1))",
            "eq_X_idx1": "int(Alt(X_idx,1,-1))",
            "eq_mZ": "double(mZ)",
            "eq_mX": "double(mX)",
            "eq_m4l": "double(m4l)",
            "eq_ptZ": "double(ptZ)",
            "eq_ptX": "double(ptX)",
            "eq_pt4l": "double(pt4l)",
            "eq_PuppiMET_pt": "double(PuppiMET_pt)",
            "eq_pass4lPt": "bool(pass4lPt)",
            "eq_veto5l": "bool(veto5l)",
            "eq_minMll4l": "double(minMll4l)",
            "eq_bVeto": "bool(bVeto)",
            "eq_nLepton10": "int(nLepton10)",
            "eq_inZZCR": "bool(" + zzcr + ")",
            "eq_inZZCR_4e": "bool((" + zzcr + ") && isZee && isXee)",
            "eq_inZZCR_4mu": "bool((" + zzcr + ") && isZmm && isXmm)",
            "eq_inZZCR_2e2mu": "bool((" + zzcr + ") && ((isZee && isXmm) || (isZmm && isXee)))",
            "eq_inSR_XSF": "bool(" + sr_xsf + ")",
            "eq_inSR_XDF": "bool(" + sr_xdf + ")",
        },
        "cuts": ["VALIDATION"],
    }
}
"""


def _validated_work_path(path: Path) -> Path:
    resolved = path.resolve()
    if resolved.parent != FAMILY.resolve() or not resolved.name.startswith(
        ".equivalence_"
    ):
        raise RuntimeError(f"Refusing unsafe validation work path: {resolved}")
    return resolved


def _remove_work(path: Path) -> None:
    path = _validated_work_path(path)
    if path.exists():
        shutil.rmtree(path)


def _copy_source(source: Path, destination: Path) -> None:
    _remove_work(destination)
    ignored = shutil.ignore_patterns(
        "__pycache__",
        ".pytest_cache",
        "configs",
        "condor",
        "jobs",
        "rootFiles",
        "plots",
        "*.pyc",
        "*.root",
        "*.pdf",
        "*.tex",
    )
    shutil.copytree(source, destination, ignore=ignored)


def _prepare_workdirs() -> None:
    if not LEGACY_SOURCE.is_dir() or not NEW_SOURCE.is_dir():
        raise RuntimeError("Legacy or new ZZCR source directory is missing")
    _copy_source(LEGACY_SOURCE, LEGACY_WORK)
    _copy_source(NEW_SOURCE, NEW_WORK)
    _remove_work(RESULTS_WORK)
    RESULTS_WORK.mkdir()

    legacy_config = LEGACY_WORK / "configuration.py"
    source = legacy_config.read_text()
    old = 'runnerFile = "zz_cr_runner.py"'
    if source.count(old) != 1:
        raise RuntimeError("Could not identify the legacy runner declaration")
    legacy_config.write_text(source.replace(old, 'runnerFile = "default"'))
    # The legacy provenance/payload writers describe histogram-only sparse
    # production.  Validation uses a native temporary tree snapshot, so keep
    # their serialized names available without invoking those unrelated
    # generated-artifact contracts.
    (LEGACY_WORK / "write_contract.py").write_text(
        'analysisContract = {"purpose": "temporary event equivalence"}\n'
        'analysisContractPath = ""\n'
    )
    (LEGACY_WORK / "worker_payload.py").write_text('sharedBatchPayload = ""\n')

    for work, override in (
        (LEGACY_WORK, LEGACY_TREE_OVERRIDE),
        (NEW_WORK, NEW_TREE_OVERRIDE),
    ):
        cuts = work / "cuts.py"
        variables = work / "variables.py"
        cuts.write_text(
            cuts.read_text()
            + '\n# Validation uses one preselection-level tree.\ncuts = {"VALIDATION": "1"}\n'
        )
        variables.write_text(variables.read_text() + override)


def _run_configuration(kind: str, config: Path, era: str, samples, events: int):
    output = RESULTS_WORK / era / kind
    configs = RESULTS_WORK / era / f"{kind}_configs"
    output.mkdir(parents=True, exist_ok=True)
    configs.mkdir(parents=True, exist_ok=True)
    log = RESULTS_WORK / era / f"{kind}.log"

    env = os.environ.copy()
    env.update(
        {
            "ERA": era,
            "YEAR": era,
            "ANALYSIS_PASS": "CONTROL",
            "CATEGORY_PROFILE": "flavor",
            "HISTOGRAM_PROFILE": "analysis",
            "SAMPLE_PROFILE": "commissioning" if kind == "legacy" else "quick",
            "SAMPLE_FILTER": ",".join(samples),
            "LIMIT_FILES_PER_SAMPLE": "1",
            "ENABLE_SYSTEMATICS": "0",
            "ZH4L_CAMPAIGN": f"equivalence_{era}",
            "EXECUTION_PROFILE": "local_xrootd",
            "INPUT_ACCESS_MODE": "xrootd",
            "OUTPUT_MODE": "local",
            "XRD_READ_ENDPOINT": "root://eoscms.cern.ch",
            "XRD_DISCOVERY_ENDPOINT": "root://eoscms.cern.ch",
        }
    )
    command = [
        "mkShapesRDF",
        "-c",
        "1",
        "-o",
        "0",
        "-b",
        "0",
        "-f",
        str(config),
        "-configs",
        str(configs),
        "--output-folder",
        str(output),
        "-l",
        str(events),
    ]
    print(
        f"[equivalence] ERA={era} kind={kind} samples={','.join(samples)} "
        f"events={events}",
        flush=True,
    )
    started = time.monotonic()
    with log.open("w") as stream:
        result = subprocess.run(
            command,
            cwd=REPO,
            env=env,
            stdout=stream,
            stderr=subprocess.STDOUT,
            text=True,
        )
    elapsed = time.monotonic() - started
    if result.returncode:
        tail = "\n".join(log.read_text(errors="replace").splitlines()[-120:])
        raise RuntimeError(
            f"{kind} ERA={era} failed with exit {result.returncode}; "
            f"log={log}\n{tail}"
        )
    roots = sorted(output.rglob("*.root"))
    if len(roots) != 1:
        raise RuntimeError(
            f"Expected one {kind} ROOT output for ERA={era}, found {roots}"
        )
    print(
        f"[equivalence] ERA={era} kind={kind} complete in {elapsed:.2f}s",
        flush=True,
    )
    return roots[0], elapsed, log


def _load_tree(root_path: Path, sample: str):
    try:
        import ROOT
    except ImportError as exc:
        raise RuntimeError("PyROOT is required; source repository start.sh") from exc

    source = ROOT.TFile.Open(str(root_path))
    if not source or source.IsZombie():
        raise RuntimeError(f"Cannot open validation output {root_path}")
    tree_path = f"trees/VALIDATION/{sample}/Events"
    tree = source.Get(tree_path)
    if tree is None:
        available = []
        directory = source.Get("trees/VALIDATION")
        if directory:
            available = [key.GetName() for key in directory.GetListOfKeys()]
        source.Close()
        raise RuntimeError(
            f"Missing {tree_path} in {root_path}; available samples={available}"
        )
    arrays = ROOT.RDataFrame(tree).AsNumpy(list(BRANCH_BY_COLUMN.values()))
    source.Close()
    return {column: arrays[branch] for column, branch in BRANCH_BY_COLUMN.items()}


def _event_map(arrays, label):
    count = len(arrays["event"])
    events = {}
    for index in range(count):
        key = tuple(int(arrays[column][index]) for column in IDENTITY_COLUMNS)
        if key in events:
            raise RuntimeError(f"Duplicate event key {key} in {label}")
        events[key] = {
            column: arrays[column][index] for column in EXACT_COLUMNS + FLOAT_COLUMNS
        }
    return events


def _histogram(events, region, variable):
    edges, fold = HISTOGRAM_AXES[variable]
    visible = len(edges) - 1
    bins = [0.0] * (visible + 2)  # explicit underflow and overflow
    entries = 0
    for row in events.values():
        if not bool(row[region]):
            continue
        entries += 1
        value = float(row[variable])
        weight = float(row["weight"])
        if value < edges[0]:
            index = 0
        elif value >= edges[-1]:
            index = visible + 1
        else:
            index = bisect_right(edges, value)
        bins[index] += weight
    if fold & 1:
        bins[1] += bins[0]
        bins[0] = 0.0
    if fold & 2:
        bins[-2] += bins[-1]
        bins[-1] = 0.0
    return entries, bins


def _compare_sample(era, sample, legacy_path, new_path):
    legacy = _event_map(_load_tree(legacy_path, sample), f"legacy {era} {sample}")
    new = _event_map(_load_tree(new_path, sample), f"new {era} {sample}")
    if set(legacy) != set(new):
        missing_new = sorted(set(legacy) - set(new))[:10]
        missing_old = sorted(set(new) - set(legacy))[:10]
        raise AssertionError(
            f"ERA={era} sample={sample} preselection event sets differ: "
            f"legacy={len(legacy)} new={len(new)} "
            f"missing_new={missing_new} missing_legacy={missing_old}"
        )

    maximum = {column: {"absolute": 0.0, "relative": 0.0} for column in FLOAT_COLUMNS}
    region_counts = {side: defaultdict(int) for side in ("legacy", "new")}
    region_sumw = {side: defaultdict(float) for side in ("legacy", "new")}
    for key in sorted(legacy):
        left, right = legacy[key], new[key]
        for column in EXACT_COLUMNS:
            if int(left[column]) != int(right[column]):
                raise AssertionError(
                    f"ERA={era} sample={sample} event={key} {column} differs: "
                    f"legacy={left[column]} new={right[column]}"
                )
        for column in FLOAT_COLUMNS:
            old_value, new_value = float(left[column]), float(right[column])
            absolute = abs(old_value - new_value)
            scale = max(abs(old_value), abs(new_value), 1.0e-30)
            relative = absolute / scale
            maximum[column]["absolute"] = max(maximum[column]["absolute"], absolute)
            maximum[column]["relative"] = max(maximum[column]["relative"], relative)
            if not math.isclose(old_value, new_value, rel_tol=1.0e-10, abs_tol=1.0e-9):
                raise AssertionError(
                    f"ERA={era} sample={sample} event={key} {column} differs: "
                    f"legacy={old_value:.17g} new={new_value:.17g} "
                    f"absolute={absolute:.3g} relative={relative:.3g}"
                )
        for side, row in (("legacy", left), ("new", right)):
            weight = float(row["weight"])
            for region in REGION_COLUMNS:
                if bool(row[region]):
                    region_counts[side][region] += 1
                    region_sumw[side][region] += weight

    histogram_comparison = {}
    for region in REGION_COLUMNS:
        histogram_comparison[region] = {}
        for variable in HISTOGRAM_AXES:
            old_entries, old_bins = _histogram(legacy, region, variable)
            new_entries, new_bins = _histogram(new, region, variable)
            if old_entries != new_entries:
                raise AssertionError(
                    f"ERA={era} sample={sample} {region}/{variable} entries differ: "
                    f"legacy={old_entries} new={new_entries}"
                )
            deltas = [abs(left - right) for left, right in zip(old_bins, new_bins)]
            maximum_bin_delta = max(deltas, default=0.0)
            if maximum_bin_delta > 1.0e-9:
                raise AssertionError(
                    f"ERA={era} sample={sample} {region}/{variable} distribution "
                    f"differs: maximum bin delta={maximum_bin_delta:.3g}"
                )
            histogram_comparison[region][variable] = {
                "entries": new_entries,
                "sumw": sum(new_bins),
                "maximum_bin_delta": maximum_bin_delta,
            }

    return {
        "preselection_events": len(legacy),
        "region_entries": {
            region: int(region_counts["new"][region]) for region in REGION_COLUMNS
        },
        "region_sumw": {
            region: region_sumw["new"][region] for region in REGION_COLUMNS
        },
        "maximum_float_difference": maximum,
        "histogram_comparison": histogram_comparison,
    }


def _parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--eras", nargs="+", default=list(SUPPORTED_ERAS))
    parser.add_argument("--samples", nargs="+", default=list(DEFAULT_SAMPLES))
    parser.add_argument("--events", type=int, default=10_000)
    parser.add_argument("--report", type=Path)
    parser.add_argument("--keep-work", action="store_true")
    args = parser.parse_args()
    unknown = sorted(set(args.eras) - set(SUPPORTED_ERAS))
    if unknown:
        parser.error(f"unsupported eras: {unknown}")
    if args.events < 1:
        parser.error("--events must be positive")
    return args


def _resolve_samples(era, selectors):
    return [ZH_SIGNAL_BY_ERA[era] if sample == "ZH" else sample for sample in selectors]


def main():
    args = _parse_args()
    if shutil.which("mkShapesRDF") is None:
        raise RuntimeError("mkShapesRDF is not on PATH; source repository start.sh")
    _prepare_workdirs()
    report = {
        "event_limit": args.events,
        "sample_selectors": args.samples,
        "columns": list(COMPARE_COLUMNS),
        "eras": {},
    }
    try:
        for era in args.eras:
            era_samples = _resolve_samples(era, args.samples)
            legacy_root, legacy_time, legacy_log = _run_configuration(
                "legacy", LEGACY_WORK, era, era_samples, args.events
            )
            new_root, new_time, new_log = _run_configuration(
                "new", NEW_WORK, era, era_samples, args.events
            )
            era_result = {
                "samples_resolved": era_samples,
                "runtime_seconds": {"legacy": legacy_time, "new": new_time},
                "logs": {"legacy": str(legacy_log), "new": str(new_log)},
                "samples": {},
            }
            for sample in era_samples:
                era_result["samples"][sample] = _compare_sample(
                    era, sample, legacy_root, new_root
                )
            report["eras"][era] = era_result
            print(f"[equivalence] ERA={era} event-level comparison PASSED", flush=True)

        report["status"] = "passed"
        report["completed_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        destination = args.report or (RESULTS_WORK / "equivalence.json")
        destination = destination.resolve()
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
        print(f"[equivalence] all eras PASSED; report={destination}", flush=True)
    finally:
        if not args.keep_work:
            _remove_work(LEGACY_WORK)
            _remove_work(NEW_WORK)
    return 0


if __name__ == "__main__":
    sys.exit(main())
