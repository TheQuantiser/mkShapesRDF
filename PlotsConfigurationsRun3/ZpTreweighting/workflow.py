"""Named runs using the framework's configuration, batch and plotting tools."""

import argparse
from datetime import datetime
import json
import os
from pathlib import Path
import re
import subprocess
import sys


FAMILY = Path(__file__).resolve().parent
ERAS = {
    "2022": "2022_v12",
    "2022-inclusive": "2022_v12_incl",
    "2023": "2023_v12",
    "2024": "2024_v15",
    "2024-inclusive": "2024_v15_incl",
}
# One fixed, previously read file; no directory listing is needed for a smoke run.
SMOKE_INPUT = (
    "root://eoscms.cern.ch//store/group/phys_higgs/cmshww/amassiro/HWWNano/"
    "Summer24_150x_nAODv15_Full2024v15/"
    "MCl2loose2024v15__MCCorr2024v15__JERFrom23BPix__l2tight/"
    "nanoLatino_DYto2Mu-2Jets_MLL-50__part0.root"
)


def parser():
    cli = argparse.ArgumentParser(prog="./run.sh", description=__doc__)
    cli.add_argument(
        "--runs-dir",
        type=Path,
        default=FAMILY / "runs",
        help="run storage (default: runs/ beside this script)",
    )
    actions = cli.add_subparsers(dest="action", required=True)
    smoke = actions.add_parser(
        "smoke", help="run 100 events from one fixed 2024 DY file"
    )
    smoke.add_argument("name", nargs="?", default=None)
    smoke.add_argument(
        "--batch", action="store_true", help="prepare one Condor job instead"
    )
    smoke.add_argument("--events", type=int, default=100)
    prepare = actions.add_parser(
        "prepare", help="compile all samples and prepare Condor files"
    )
    prepare.add_argument("name")
    prepare.add_argument("--era", choices=ERAS, default="2024")
    prepare.add_argument("--nominal-only", action="store_true")
    prepare.add_argument("--weights", type=Path, help="explicit reviewed DY fit JSON")
    for command in (smoke, prepare):
        command.add_argument("--site", choices=("lpc", "cern"), default="lpc")
    for name, help_text in (
        ("submit", "submit the prepared JDL once"),
        ("status", "show live Condor queue and history for this run"),
        ("merge", "merge the expected returned ROOT files"),
        ("plot", "plot ptll from the run's saved configuration"),
        ("extract", "fit mm-channel DY weights from a full unweighted run"),
    ):
        actions.add_parser(name, help=help_text).add_argument("name")
    return cli


def execute(command, run_dir, env=None, timeout=None):
    subprocess.run(
        [str(item) for item in command],
        cwd=run_dir,
        env=env,
        check=True,
        timeout=timeout,
    )


def fit_keys(variant):
    year, kind = (
        ("2023", "NLO")
        if variant == "2023_v12"
        else (variant.removesuffix("_incl"), "LO")
    )
    jets = (0,) if variant.endswith("_incl") else (0, 1, 2)
    return year, kind, jets


def check_weights(path, variant):
    year, kind, jets = fit_keys(variant)
    data = json.loads(path.read_text())
    values = data.get(year, {}) if isinstance(data, dict) else {}
    if not isinstance(values, dict) or any(
        not isinstance(values.get(f"{kind}_{jet}j"), str)
        or not values[f"{kind}_{jet}j"].strip()
        for jet in jets
    ):
        raise ValueError(
            f"{path} needs nonempty {year}/{kind}_<jet>j formulas for {jets}"
        )


def load_run(run_dir):
    from mkShapesRDF.shapeAnalysis.ConfigLib import ConfigLib

    pickles = list((run_dir / "configs").glob("*.pkl"))
    if len(pickles) != 1:
        raise ValueError(
            f"Expected exactly one saved configuration in {run_dir / 'configs'}; found {len(pickles)}"
        )
    config = ConfigLib.loadPickle(str(pickles[0]), {})
    settings = config["zpt"]
    if settings["run_dir"] != str(run_dir) or settings["campaign"] != run_dir.name:
        raise ValueError(
            "Saved configuration belongs to a different run directory; use its original location"
        )
    if settings["variant"] not in ERAS.values():
        raise ValueError("Saved configuration has an unsupported variant")
    return pickles[0], config


def batch_dir(config):
    return Path(config["batchFolder"]) / config["tag"]


def root_output(config):
    return Path(config["outputFolder"]) / config["outputFile"]


def check_root(path):
    import ROOT

    if not path.is_file():
        raise FileNotFoundError(f"Missing ROOT output: {path}")
    handle = ROOT.TFile.Open(str(path))
    if not handle or handle.IsZombie():
        raise ValueError(f"Unreadable ROOT output: {path}")
    try:
        if handle.TestBit(ROOT.TFile.kRecovered) or not handle.GetNkeys():
            raise ValueError(f"Recovered or empty ROOT output: {path}")
    finally:
        handle.Close()


def create_run(args, run_dir):
    smoke = args.action == "smoke"
    if smoke and args.events < 1:
        raise ValueError("--events must be positive")
    variant = "2024_v15" if smoke else ERAS[args.era]
    weights = (
        None if smoke or args.weights is None else args.weights.resolve(strict=True)
    )
    if weights:
        check_weights(weights, variant)
    # A stale interactive export must not silently narrow a full campaign.
    env = {
        key: value for key, value in os.environ.items() if not key.startswith("ZPT_")
    }
    settings = {
        "SITE": args.site,
        "CAMPAIGN": run_dir.name,
        "RUN_DIR": run_dir,
        "RUN_MODE": (
            "smoke-batch"
            if smoke and args.batch
            else "smoke" if smoke else "production"
        ),
        "LIMIT_FILES": 1 if smoke else -1,
        "FILES_PER_JOB": 1 if smoke else 0,
        "SYSTEMATICS": int(not smoke and not args.nominal_only),
        "APPLY_REWEIGHT": int(weights is not None),
    }
    if smoke:
        settings.update(
            SAMPLE="DY", DATASET="DYto2Mu-2Jets_MLL-50", INPUT_FILE=SMOKE_INPUT
        )
    if weights:
        settings["REWEIGHT_JSON"] = weights
    env.update({"ZPT_" + key: str(value) for key, value in settings.items()})
    run_dir.mkdir(parents=True, exist_ok=False)
    command = [
        "mkShapesRDF",
        "-c",
        "1",
        "-o",
        "0",
        "-f",
        FAMILY / variant,
        "-configs",
        run_dir / "configs",
    ]
    if smoke and not args.batch:
        command += ["-b", "0", "-l", str(args.events)]
    else:
        command += ["-b", "1", "-dR", "1"]
        if smoke:
            command += ["-l", str(args.events)]
    execute(command, run_dir, env)
    pickle_path, config = load_run(run_dir)
    print(f"Saved configuration: {pickle_path}")
    if smoke and not args.batch:
        check_root(root_output(config))
        print(f"Smoke output: {root_output(config)}")
    else:
        jdl = batch_dir(config) / "submit.jdl"
        if not jdl.is_file():
            raise FileNotFoundError(f"Preparation did not produce {jdl}")
        print(f"Prepared only; review {jdl} before ./run.sh submit {run_dir.name}")


def submit(config):
    from mkShapesRDF.shapeAnalysis.BatchSubmission import (
        _record_condor_submit_result,
        _run_condor_submit,
    )

    folder = batch_dir(config)
    if not (folder / "submit.jdl").is_file():
        raise FileNotFoundError(f"No prepared submit.jdl in {folder}")
    receipt = folder / "submit.receipt.txt"
    # Reserve the existing framework receipt before contacting the scheduler.
    # An interrupted/failed attempt is deliberately not retried automatically.
    try:
        receipt.touch(exist_ok=False)
    except FileExistsError:
        raise ValueError(
            f"Submission was already attempted; inspect {receipt} and Condor before any retry"
        ) from None
    result = _run_condor_submit(
        ["condor_submit", "-terse", "submit.jdl"],
        cwd=folder,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    _record_condor_submit_result(result, folder, "submission")


def status(config, run_dir):
    from mkShapesRDF.shapeAnalysis.BatchSubmission import _safe_terse_receipt

    receipt = batch_dir(config) / "submit.receipt.txt"
    if not receipt.exists():
        print(f"No submission recorded. Run directory: {run_dir}")
        return
    job_range = _safe_terse_receipt(receipt.read_text())
    if not job_range:
        raise ValueError(
            f"Submission state is unknown; inspect {receipt} and submit.stderr.txt"
        )
    cluster = job_range.split(".", 1)[0]
    execute(["condor_q", cluster], run_dir, timeout=60)
    execute(["condor_history", cluster], run_dir, timeout=60)
    print(
        "Queue/history describe scheduler state. Inspect job errors and returned ROOT files before merging."
    )


def merge(config, pickle_path, run_dir):
    from mkShapesRDF.shapeAnalysis.runner import RunAnalysis

    output = root_output(config)
    if output.exists():
        raise FileExistsError(f"Output already exists: {output}")
    jobs = RunAnalysis.splitSamples(config["samples"])
    if not jobs:
        raise ValueError("Saved configuration has no jobs to merge")
    for job in jobs:
        check_root(output.with_name(f"{output.stem}__ALL__{job[0]}_{job[3]}.root"))
    execute(["mkShapesRDF", "-c", "0", "-o", "2", "-config", pickle_path], run_dir)
    check_root(output)
    print(f"Merged {len(jobs)} returned files: {output}")


def plot(config, run_dir):
    output = root_output(config)
    check_root(output)
    if Path(config["plotPath"]).exists():
        raise FileExistsError(f"Plot directory already exists: {config['plotPath']}")
    # mkPlot reads ./configs; every named run contains exactly one pickle.
    kind = "cratio" if "DATA" in config["samples"] else "c"
    command = [
        "mkPlot",
        "--inputFile",
        output,
        "--onlyVariable",
        "ptll",
        "--onlyPlot",
        kind,
        "--fileFormats",
        "png",
    ]
    if config["zpt"]["run_mode"].startswith("smoke"):
        # The pinned input is dimuon DY; show its populated regions on a linear axis.
        command += ["--linearOnly", "--onlyCut", "Zmm_0j,Zmm_1j,Zmm_2j"]
    execute(command, run_dir)
    if not list(Path(config["plotPath"]).rglob("*.png")):
        raise ValueError("mkPlot did not produce any PNG files")
    print(f"Plots: {config['plotPath']}")


def extract(config, run_dir):
    settings = config["zpt"]
    if settings["run_mode"] != "production" or settings["apply_reweight"]:
        raise ValueError("Extraction requires a full unweighted production run")
    if not {"DY", "DATA"}.issubset(config["samples"]):
        raise ValueError("Extraction requires DY, DATA and the configured backgrounds")
    output = root_output(config)
    check_root(output)
    result = run_dir / "weights"
    result.mkdir(exist_ok=False)
    variant = settings["variant"]
    year, kind, jets = fit_keys(variant)
    destination = result / "dyZpTrw.json"
    for jet in jets:
        execute(
            [
                sys.executable,
                FAMILY / variant / "extract_Zptrw.py",
                "-f",
                "-n",
                "2",
                "-c",
                "mm",
                "-nj",
                str(jet),
                "--input",
                output,
                "--write-json",
                destination,
                "--year",
                year,
                "--sample-type",
                kind,
            ],
            result,
        )
        # Upstream may exit zero after a failed fit without writing a formula.
        data = json.loads(destination.read_text()) if destination.exists() else {}
        if not data.get(year, {}).get(f"{kind}_{jet}j"):
            raise ValueError(
                f"Fit did not write {year}/{kind}_{jet}j; inspect {result}"
            )
    check_weights(destination, variant)
    print(
        f"Fit formulas: {destination}. Review the fits and subtraction model before using --weights."
    )


def main(argv=None):
    cli = parser()
    args = cli.parse_args(argv)
    name = args.name or datetime.now().strftime("smoke_%Y%m%d_%H%M%S_%f")
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", name):
        cli.error(
            "run names must start with a letter/digit and contain only letters, digits, _, . or -"
        )
    run_dir = args.runs_dir.expanduser().resolve() / name
    try:
        if args.action in ("smoke", "prepare"):
            create_run(args, run_dir)
        else:
            pickle_path, config = load_run(run_dir)
            if args.action == "submit":
                submit(config)
            elif args.action == "status":
                status(config, run_dir)
            elif args.action == "merge":
                merge(config, pickle_path, run_dir)
            elif args.action == "plot":
                plot(config, run_dir)
            else:
                extract(config, run_dir)
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        print(
            f"{args.action} failed: {exc}\nRun directory (preserved): {run_dir}",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
