"""Two-pass controller; state lives in native configs, receipts and outputs."""

import argparse
from collections import Counter
from copy import deepcopy
import fcntl
import json
import math
from pathlib import Path
import re
import subprocess
import time

import workflow as wf


def job_outputs(config):
    from mkShapesRDF.shapeAnalysis.runner import RunAnalysis

    output = wf.root_output(config)
    return [
        output.with_name(f"{output.stem}__ALL__{job[0]}_{job[3]}.root")
        for job in RunAnalysis.splitSamples(config["samples"])
    ]


def query_jobs(client, cluster, folder, count, target=()):
    attributes = "ClusterId,ProcId,JobStatus,ExitCode,ExitBySignal,Iwd,HoldReason"
    result = subprocess.run(
        wf.condor_command(
            [
                client,
                *target,
                str(cluster),
                "-json",
                "-attributes",
                attributes,
                "-limit",
                str(count + 1),
            ]
        ),
        cwd=folder,
        env=wf.condor_environment(),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=60,
        check=True,
    )
    # Native Condor clients may print nothing for an empty successful query.
    # Missing history still cannot establish completion in wait_for_jobs.
    ads = json.loads(result.stdout) if result.stdout.strip() else []
    if not isinstance(ads, list) or any(not isinstance(ad, dict) for ad in ads):
        raise ValueError(f"{client} did not return a JSON job list")
    return ads


def wait_for_jobs(config, hours):
    from mkShapesRDF.shapeAnalysis.BatchSubmission import _safe_terse_receipt

    folder = wf.batch_dir(config)
    receipt = _safe_terse_receipt((folder / "submit.receipt.txt").read_text())
    match = re.fullmatch(r"(\d+)\.(\d+)(?:\s+-\s+(\d+)\.(\d+))?", receipt or "")
    if not match:
        raise ValueError(
            f"Unknown submission state; inspect {folder}/submit.receipt.txt"
        )
    cluster, first = map(int, match.group(1, 2))
    if match.group(3) and int(match.group(3)) != cluster:
        raise ValueError("Submission receipt spans multiple clusters")
    last = int(match.group(4)) if match.group(4) else first
    outputs = job_outputs(config)
    expected = set(range(first, last + 1))
    if not outputs or len(expected) != len(outputs):
        raise ValueError(
            "Submission receipt job count differs from the saved configuration"
        )
    deadline = time.monotonic() + hours * 3600
    target = wf.scheduler_target(config)
    previous = None
    while True:
        queued = query_jobs("condor_q", cluster, folder, len(expected), target)
        ads = queued or query_jobs(
            "condor_history", cluster, folder, len(expected), target
        )
        seen = set()
        for ad in ads:
            proc = ad.get("ProcId")
            if ad.get("ClusterId") != cluster or proc not in expected or proc in seen:
                raise ValueError(
                    "Scheduler job identities differ from the submission receipt"
                )
            if ad.get("Iwd") != str(folder):
                raise ValueError(
                    "Scheduler job directory differs from the prepared run"
                )
            seen.add(proc)
            state = ad.get("JobStatus")
            if state in (3, 5):
                raise ValueError(
                    f"Job {cluster}.{proc} is removed/held: {ad.get('HoldReason', '')}"
                )
            if state not in (1, 2, 4, 6, 7):
                raise ValueError(f"Unsupported job state for {cluster}.{proc}: {state}")
            if state == 4 and (
                ad.get("ExitBySignal") is not False or ad.get("ExitCode") != 0
            ):
                raise ValueError(
                    f"Job {cluster}.{proc} lacks a successful exit; inspect its logs"
                )
        completed = (
            not queued and seen == expected and all(ad["JobStatus"] == 4 for ad in ads)
        )
        if completed:
            for output in outputs:
                wf.check_root(output)
            print(
                f"{config['zpt']['run_dir']}: {len(expected)} jobs completed; outputs readable."
            )
            return
        progress = (
            bool(queued),
            tuple(sorted(Counter(ad["JobStatus"] for ad in ads).items())),
            len(seen),
        )
        if progress != previous:
            print(
                f"Cluster {cluster}: states {dict(progress[1])}; records {len(seen)}/{len(expected)}. Waiting.",
                flush=True,
            )
            previous = progress
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError(
                "Waiting timed out; jobs were not cancelled. Resume the same auto name."
            )
        time.sleep(min(30, remaining))


def flattened(config):
    from mkShapesRDF.shapeAnalysis.latinos.LatinosUtils import (
        flatten_cuts,
        flatten_samples,
    )

    cuts = deepcopy(config["cuts"]["cuts"])
    samples = deepcopy(config["samples"])
    flatten_cuts(cuts)
    flatten_samples(samples)
    return cuts, samples


def check_histograms(config):
    """Reopen nominal histogram members before reusing a merged result."""
    import ROOT

    output = wf.root_output(config)
    wf.check_root(output)
    cuts, samples = flattened(config)
    with ROOT.TFile.Open(str(output)) as handle:
        for cut in cuts:
            for variable in config["variables"]:
                for sample in samples:
                    name = f"{cut}/{variable}/histo_{sample}"
                    histogram = handle.Get(name)
                    if not histogram or not histogram.InheritsFrom("TH1"):
                        raise ValueError(
                            f"Missing nominal histogram: {name} in {output}"
                        )


def check_plots(config):
    from matplotlib.image import imread

    cuts, _ = flattened(config)
    for cut in cuts:
        for prefix in ("cratio_", "log_cratio_"):
            path = Path(config["plotPath"]) / f"{prefix}{cut}_ptll.png"
            if not path.is_file() or not imread(path).size:
                raise ValueError(f"Missing or unreadable plot: {path}")


def check_application(baseline, corrected):
    """Only the intended DY factor may change between the two compiled passes."""
    samples = deepcopy(baseline["samples"])
    samples["DY"]["weight"] += "*DY_NLO_ZpTrw"
    if samples != corrected["samples"]:
        raise ValueError(
            "Samples, inputs or base weights changed between passes; inspect both configs"
        )
    for key in ("cuts", "variables", "nuisances", "lumi"):
        if baseline[key] != corrected[key]:
            raise ValueError(
                f"{key} changed between passes; keep analysis source stable"
            )
    unchanged_aliases = [
        {k: v for k, v in config["aliases"].items() if k != "DY_NLO_ZpTrw"}
        for config in (baseline, corrected)
    ]
    if unchanged_aliases[0] != unchanged_aliases[1]:
        raise ValueError("Aliases other than DY_NLO_ZpTrw changed between passes")


def prepare_or_load(folder, options, weights=None):
    if not folder.exists():
        wf.create_run(
            argparse.Namespace(action="prepare", weights=weights, **options), folder
        )
    pickle_path, config = wf.load_run(folder)
    settings = config["zpt"]
    expected = {
        "variant": wf.ERAS[options["era"]],
        "site": options["site"],
        "systematics": not options["nominal_only"],
        "run_mode": "production",
        "apply_reweight": weights is not None,
        "limit_files": -1,
        "sample": "",
    }
    if any(settings.get(key) != value for key, value in expected.items()):
        raise ValueError(
            f"Options differ from saved {folder}; resume with its original options"
        )
    if weights and settings["reweight_json"] != str(weights):
        raise ValueError(
            "Corrected run already uses a different weights JSON; use a new auto name"
        )
    return pickle_path, config


def finish_pass(folder, pickle_path, config, hours):
    receipt = wf.batch_dir(config) / "submit.receipt.txt"
    if not receipt.exists():
        wf.submit(config)
    wait_for_jobs(config, hours)
    if not wf.root_output(config).exists():
        wf.merge(config, pickle_path, folder)
    check_histograms(config)
    if not Path(config["plotPath"]).exists():
        wf.plot(config, folder)
    check_plots(config)


def run(args, run_dir):
    if not math.isfinite(args.wait_hours) or args.wait_hours <= 0:
        raise ValueError("--wait-hours must be finite and positive")
    weights = args.weights.resolve(strict=True) if args.weights else None
    if (run_dir / "configs").exists():
        raise ValueError(
            "This name belongs to a manual run; choose a separate auto name"
        )
    run_dir.mkdir(parents=True, exist_ok=True)
    with (run_dir / ".controller.lock").open("a") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise ValueError(
                "Another controller is already running for this campaign"
            ) from None
        baseline_dir, corrected_dir = run_dir / "baseline", run_dir / "corrected"
        saved = wf.load_run(baseline_dir)[1]["zpt"] if baseline_dir.exists() else {}
        eras = {value: key for key, value in wf.ERAS.items()}
        options = {
            "era": args.era or eras.get(saved.get("variant"), "2024"),
            "site": args.site or saved.get("site", "lpc"),
            "nominal_only": (
                args.nominal_only
                if args.nominal_only is not None
                else not saved.get("systematics", True)
            ),
        }
        if weights:
            wf.check_weights(weights, wf.ERAS[options["era"]])
        pickle_path, baseline = prepare_or_load(baseline_dir, options)
        finish_pass(baseline_dir, pickle_path, baseline, args.wait_hours)
        fitted = baseline_dir / "weights" / "dyZpTrw.json"
        if weights is None and corrected_dir.exists() and not args.apply_fitted:
            weights = Path(wf.load_run(corrected_dir)[1]["zpt"]["reweight_json"])
        if weights is None:
            if not fitted.parent.exists():
                wf.extract(baseline, baseline_dir)
            wf.check_weights(fitted, baseline["zpt"]["variant"])
            if args.apply_fitted:
                weights = fitted
            else:
                print(
                    f"Paused for formula review: {fitted}\nResume auto {run_dir.name} with --weights PATH, or --apply-fitted."
                )
                return
        wf.check_weights(weights, baseline["zpt"]["variant"])
        pickle_path, corrected = prepare_or_load(corrected_dir, options, weights)
        check_application(baseline, corrected)
        finish_pass(corrected_dir, pickle_path, corrected, args.wait_hours)
        print(f"Both histogram passes completed. Results: {run_dir}")
