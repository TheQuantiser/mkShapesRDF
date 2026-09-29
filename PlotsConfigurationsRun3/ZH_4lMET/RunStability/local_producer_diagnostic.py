"""Run one bounded 2024 NanoAOD producer chain into a local diagnostic tree.

This tool deliberately bypasses mkPostProc's Condor generation and stage-out.
Its input manifest is an exact file and original-entry identity, not discovery.
"""

import argparse
import gzip
import hashlib
import json
import math
from pathlib import Path
import runpy
import subprocess
import sys


LEAF = Path(__file__).resolve().parent
REPO = LEAF.parents[2]
sys.path.insert(0, str(REPO))

from mkShapesRDF.processor.framework.Productions_cfg import Productions  # noqa: E402
from mkShapesRDF.processor.framework.Steps_cfg import Steps  # noqa: E402


PRODUCER = {
    "data": (
        "Run2024_ReRecoCDE_PromptFGHI_nAODv15_Full2024v15",
        "DATAl2loose2024v15__l2loose",
    ),
    "mc": (
        "Summer24_150x_nAODv15_Full2024v15",
        "MCl2loose2024v15__MCCorr2024v15__JERFrom23BPix__l2tight",
    ),
}
MAX_ENTRIES = 200000
IDENTITY = ("diagnostic_source_entry", "run", "luminosityBlock", "event")
ROLE_IS_DATA = {
    "dy_ee": False,
    "dy_mumu": False,
    "muon_c": True,
    "muon_i": True,
    "egamma_c": True,
    "egamma_i": True,
}


def _sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def step_names(manifest):
    """Return the exact configured chain, including the skipped final snapshot."""
    return tuple(Steps[PRODUCER[manifest["producer_role"]][1]]["subTargets"])


def load_manifest(path, role, output_dir, expected_sha256):
    """Select one fixed cohort role and reject altered or ambiguous input."""
    path = Path(path).resolve(strict=True)
    digest = _sha256(path)
    if digest != expected_sha256:
        raise ValueError("Pinned input manifest SHA-256 mismatch")
    cohort = json.loads(path.read_text())
    if (
        cohort.get("schema_version") != 1
        or cohort.get("kind") != "paired_2024_lowpt_nanoaod_inputs"
    ):
        raise ValueError("Expected pinned paired_2024_lowpt_nanoaod_inputs manifest")
    pinned_head = cohort.get("mkshapes_head")
    if (
        not isinstance(pinned_head, str)
        or len(pinned_head) != 40
        or any(char not in "0123456789abcdef" for char in pinned_head)
    ):
        raise ValueError("Pinned mkShapesRDF revision is invalid")
    try:
        pinned_tree = subprocess.check_output(
            ["git", "rev-parse", f"{pinned_head}:mkShapesRDF"],
            cwd=REPO,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
        current_tree = subprocess.check_output(
            ["git", "rev-parse", "HEAD:mkShapesRDF"], cwd=REPO, text=True
        ).strip()
    except subprocess.CalledProcessError as exc:
        raise ValueError("Pinned mkShapesRDF revision is unavailable") from exc
    if pinned_tree != current_tree:
        raise ValueError("Producer package differs from pinned mkShapesRDF revision")
    matches = [item for item in cohort.get("files", ()) if item.get("role") == role]
    if len(matches) != 1:
        raise ValueError(f"Expected one exact manifest role {role!r}")
    manifest = dict(matches[0])
    if manifest.get("era") != "2024" or type(manifest.get("is_data")) is not bool:
        raise ValueError("Expected one 2024 DATA or MC source")
    if (
        manifest["role"] not in ROLE_IS_DATA
        or manifest["is_data"] != ROLE_IS_DATA[manifest["role"]]
    ):
        raise ValueError("Manifest role and DATA/MC type disagree")
    producer_role = "data" if manifest["is_data"] else "mc"
    production, _ = PRODUCER[producer_role]
    sample_file = (
        REPO / "mkShapesRDF/processor/framework" / Productions[production]["samples"]
    ).resolve()
    samples = runpy.run_path(str(sample_file))["Samples"]
    sample = manifest.get("sample")
    if sample not in samples or samples[sample].get("nanoAOD") != manifest.get(
        "dataset"
    ):
        raise ValueError("Sample/dataset does not match the 2024 processor catalog")
    lfn = manifest.get("lfn")
    if (
        not isinstance(lfn, str)
        or not lfn.startswith(f"/store/{'data' if producer_role == 'data' else 'mc'}/")
        or not lfn.endswith(".root")
        or any(part in ("", ".", "..") for part in lfn[1:].split("/"))
        or manifest.get("pfn") != "root://cmsxrootd.fnal.gov/" + lfn
    ):
        raise ValueError("LFN/PFN must name the exact manifest /store ROOT file")
    start, stop = manifest.get("entry_start"), manifest.get("entry_stop")
    if (
        type(start) is not int
        or type(stop) is not int
        or start < 0
        or stop <= start
        or stop - start > MAX_ENTRIES
        or type(manifest.get("frozen_file_entries")) is not int
        or manifest.get("verified_events_entries") != manifest["frozen_file_entries"]
        or not isinstance(manifest.get("verified_root_uuid"), str)
        or not manifest["verified_root_uuid"]
        or stop > manifest["frozen_file_entries"]
    ):
        raise ValueError(f"Entry range must be half-open and at most {MAX_ENTRIES}")
    if not Path(output_dir).is_absolute():
        raise ValueError("output_dir must be an absolute local path")
    output = Path(output_dir)
    if output.exists():
        raise ValueError(f"output_dir already exists: {output}")
    if not output.parent.is_dir():
        raise ValueError("output_dir parent must already exist")
    manifest["producer_role"] = producer_role
    manifest["output_dir"] = str(output)
    manifest["manifest_path"] = str(path)
    manifest["manifest_sha256"] = digest
    manifest["pinned_mkshapes_head"] = pinned_head
    manifest["mkshapes_head"] = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=REPO, text=True
    ).strip()
    manifest["producer_package_tree"] = current_tree
    return manifest


def load_mc_sumw(manifest, receipt_path, receipt_sha256):
    """Use a hashed, externally verified full-source normalization receipt."""
    if not receipt_path or not receipt_sha256:
        raise ValueError(
            "MC requires a hashed, verified full-source normalization receipt"
        )
    path = Path(receipt_path)
    if not path.is_absolute() or _sha256(path) != receipt_sha256:
        raise ValueError("MC normalization receipt path/hash mismatch")
    receipt = json.loads(path.read_text())
    if any(
        (
            receipt.get("schema_version") != 1,
            receipt.get("status") != "verified",
            receipt.get("sample") != manifest["sample"],
            receipt.get("dataset") != manifest["dataset"],
        )
    ):
        raise ValueError("MC normalization receipt identity/status mismatch")
    method = receipt.get("method")
    total = receipt.get("gen_event_sumw")
    if type(total) not in (int, float) or not math.isfinite(total) or total == 0:
        raise ValueError("MC full-source genEventSumw is invalid")
    if method == "Runs.genEventSumw":
        lfns = receipt.get("source_lfns")
        sums = receipt.get("per_file_gen_event_sumw")
        if (
            not isinstance(lfns, list)
            or not isinstance(sums, list)
            or len(lfns) < 2
            or len(lfns) != len(sums)
            or any(not isinstance(lfn, str) for lfn in lfns)
            or len(set(lfns)) != len(lfns)
            or manifest["lfn"] not in lfns
            or receipt.get("source_file_inventory_hash")
            != manifest.get("file_inventory_hash")
            or any(
                type(value) not in (int, float) or not math.isfinite(value)
                for value in sums
            )
            or not math.isclose(total, math.fsum(sums), rel_tol=1e-12, abs_tol=1e-9)
        ):
            raise ValueError("MC full-source genEventSumw does not equal per-file sum")
    elif method == "retained_hww_baseW":
        xs_file = Productions[PRODUCER["mc"][0]]["xsFile"]
        xs_db = runpy.run_path(
            str((REPO / "mkShapesRDF/processor/framework" / xs_file).resolve())
        )["xs_db"]
        xs = float(xs_db[manifest["sample"]][0].split("=")[1])
        basew = receipt.get("historical_hww_baseW")
        receipt_xs = receipt.get("cross_section_pb")
        if (
            receipt.get("matched_input_lfn") != manifest["lfn"]
            or not str(receipt.get("historical_hww_part0_uri", "")).startswith(
                "root://"
            )
            or not isinstance(receipt.get("historical_compiled_pickle_sha256"), str)
            or len(receipt["historical_compiled_pickle_sha256"]) != 64
            or not isinstance(receipt.get("parent_pair_evidence_sha256"), str)
            or len(receipt["parent_pair_evidence_sha256"]) != 64
            or type(basew) not in (int, float)
            or not math.isfinite(basew)
            or basew == 0
            or type(receipt_xs) not in (int, float)
            or not math.isfinite(receipt_xs)
            or not math.isclose(receipt_xs, xs, rel_tol=1e-12)
            or not math.isclose(total, xs * 1000 / basew, rel_tol=1e-12)
        ):
            raise ValueError("MC retained HWW baseW provenance/algebra mismatch")
    else:
        raise ValueError("MC normalization receipt method is unsupported")
    return float(total)


def _book_keys(df):
    return {name: df.df.Take[df.df.GetColumnType(name)](name) for name in IDENTITY}


def _book_entries(df):
    name = IDENTITY[0]
    return df.df.Take[df.df.GetColumnType(name)](name)


def _result_keys(actions):
    values = {name: list(action.GetValue()) for name, action in actions.items()}
    return [
        dict(zip(IDENTITY, (int(values[name][i]) for name in IDENTITY)))
        for i in range(len(values[IDENTITY[0]]))
    ]


def build_ledger(input_events, stages):
    """Map every surviving original entry to one retained typed event key."""
    previous = [row[IDENTITY[0]] for row in input_events]
    if len(set(previous)) != len(previous):
        raise ValueError("Duplicate input source entry")
    result = []
    for name, entries in stages:
        entries = [int(entry) for entry in entries]
        surviving = iter(previous)
        if any(not any(parent == entry for parent in surviving) for entry in entries):
            raise ValueError(f"Step {name} introduced/reordered a source entry")
        result.append(
            {
                "step": name,
                "input_count": len(previous),
                "output_count": len(entries),
                "output_source_entries": entries,
            }
        )
        previous = entries
    return {"input_events": input_events, "stages": result}


def run(
    manifest_path,
    role,
    output_dir,
    manifest_sha256,
    normalization_receipt=None,
    normalization_sha256=None,
):
    """Execute the exact configured modules once on a bounded original-entry range."""
    manifest = load_manifest(manifest_path, role, output_dir, manifest_sha256)
    producer_role = manifest["producer_role"]
    sumw = (
        load_mc_sumw(manifest, normalization_receipt, normalization_sha256)
        if producer_role == "mc"
        else None
    )

    import ROOT
    import mkShapesRDF
    from mkShapesRDF.processor.framework.mRDF import mRDF

    if ROOT.IsImplicitMTEnabled():
        raise RuntimeError("Entry Range requires ROOT implicit multithreading off")
    ROOT.gROOT.SetBatch(True)
    framework = Path(mkShapesRDF.__file__).resolve().parent
    if framework.parent != REPO:
        raise RuntimeError(
            "Imported mkShapesRDF package is not from diagnostic worktree"
        )
    golden_sha256 = None
    if producer_role == "data":
        golden_path = framework / Productions[PRODUCER["data"][0]]["jsonFile"].lstrip(
            "/"
        )
        golden_sha256 = _sha256(golden_path)
        if golden_sha256 != manifest.get("golden_sha256"):
            raise ValueError("DATA Golden JSON hash differs from pinned manifest")
    source_file = ROOT.TFile.Open(manifest["pfn"], "READ")
    try:
        source_tree = source_file.Get("Events") if source_file else None
        if not source_tree:
            raise RuntimeError("Pinned source Events tree is unreadable")
        observed_entries = source_tree.GetEntries()
        if observed_entries != manifest["frozen_file_entries"]:
            raise RuntimeError("Pinned source Events entries differ from manifest")
        uuid = str(source_file.GetUUID().AsString()).strip("{}").lower()
        if uuid != str(manifest.get("verified_root_uuid", "")).strip("{}").lower():
            raise RuntimeError("Pinned source ROOT UUID differs from manifest")
    finally:
        if source_file:
            source_file.Close()
    ROOT.gInterpreter.Declare(f'#include "{framework / "include/headers.hh"}"')
    replacements = {
        "RPLME_FW": str(framework),
        "RPLME_CMSSW": "Full2024v15",
        "RPLME_LUMI": Productions[PRODUCER[producer_role][0]].get("jsonFile", ""),
        "RPLME_SAMPLENAME": manifest["sample"],
        "RPLME_genEventSumw": repr(sumw),
    }
    state = {
        "sampleName": manifest["sample"],
        "files": [manifest["pfn"]],
        "values": [],
    }
    if producer_role == "mc":
        xs_file = Productions[PRODUCER["mc"][0]]["xsFile"]
        state["xs_db"] = runpy.run_path(
            str((REPO / "mkShapesRDF/processor/framework" / xs_file).resolve())
        )["xs_db"]
    df = mRDF().readRDF("Events", [manifest["pfn"]])
    if any(name not in df.GetColumnNames() for name in IDENTITY[1:]):
        raise ValueError("Input Events tree lacks run/luminosityBlock/event identity")
    if IDENTITY[0] in df.GetColumnNames():
        raise ValueError("Input already contains reserved diagnostic_source_entry")
    df = df.Define(IDENTITY[0], "rdfentry_")
    df = df.Copy()
    df.df = df.df.Range(manifest["entry_start"], manifest["entry_stop"])
    input_keys = _book_keys(df)
    stages = []
    df = df.Filter("((nElectron+nMuon)>1)")
    stages.append(("chain_selection", _book_entries(df)))
    for name in step_names(manifest):
        if name.startswith("finalSnapshot_"):
            break
        spec = Steps[name]
        if spec["isChain"]:
            raise ValueError(f"Nested chain not supported: {name}")
        exec("from " + spec["import"] + " import *", state)
        declaration = spec["declare"]
        for old, new in replacements.items():
            declaration = declaration.replace(old, new)
        exec(declaration, state)
        module = eval(spec["module"], state)
        df = module.run(df, state["values"])
        stages.append((name, _book_entries(df)))

    output_dir = Path(manifest["output_dir"])
    output_dir.mkdir(mode=0o700)
    output_root = output_dir / "events.root"
    columns = sorted(df.GetColumnNames())
    opts = ROOT.RDF.RSnapshotOptions()
    opts.fLazy = True
    opts.fMode = "RECREATE"
    snapshot = df.df.Snapshot("Events", str(output_root), columns, opts)
    snapshot.GetValue()
    ledger = build_ledger(
        _result_keys(input_keys),
        [(name, actions.GetValue()) for name, actions in stages],
    )
    ledger_path = output_dir / "entry_ledger.json.gz"
    with gzip.open(ledger_path, "wt", encoding="utf-8") as stream:
        json.dump(ledger, stream, separators=(",", ":"))
    final_file = ROOT.TFile.Open(str(output_root), "READ")
    try:
        tree = final_file.Get("Events") if final_file else None
        if not tree or tree.GetEntries() != ledger["stages"][-1]["output_count"]:
            raise RuntimeError(
                "Diagnostic ROOT output failed Events/count verification"
            )
        branches = sorted(branch.GetName() for branch in tree.GetListOfBranches())
        if not set(columns).issubset(branches):
            raise RuntimeError("Diagnostic ROOT output is missing nominal columns")
    finally:
        if final_file:
            final_file.Close()
    receipt = {
        "kind": "run_stability_local_producer_diagnostic",
        "schema_version": 1,
        "source_manifest": manifest["manifest_path"],
        "source_manifest_sha256": manifest["manifest_sha256"],
        "mkshapes_head": manifest["mkshapes_head"],
        "pinned_mkshapes_head": manifest["pinned_mkshapes_head"],
        "producer_package_tree": manifest["producer_package_tree"],
        "role": manifest["role"],
        "production": PRODUCER[producer_role][0],
        "chain": PRODUCER[producer_role][1],
        "sample": manifest["sample"],
        "dataset": manifest["dataset"],
        "lfn": manifest["lfn"],
        "pfn": manifest["pfn"],
        "entry_range": [manifest["entry_start"], manifest["entry_stop"]],
        "mc_full_source_gen_event_sumw": sumw,
        "normalization_receipt": (
            str(normalization_receipt) if normalization_receipt else None
        ),
        "normalization_receipt_sha256": normalization_sha256,
        "source_id": manifest.get("source_id"),
        "file_inventory_hash": manifest.get("file_inventory_hash"),
        "verified_root_uuid": manifest.get("verified_root_uuid"),
        "observed_root_uuid": uuid,
        "observed_events_entries": observed_entries,
        "golden_sha256": golden_sha256,
        "diagnostic_source_sha256": _sha256(__file__),
        "stage_counts": [
            {
                key: value
                for key, value in stage.items()
                if key != "output_source_entries"
            }
            for stage in ledger["stages"]
        ],
        "entry_ledger": str(ledger_path),
        "entry_ledger_sha256": _sha256(ledger_path),
        "root_file": str(output_root),
        "root_sha256": _sha256(output_root),
        "branches": branches,
    }
    (output_dir / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", help="Exact local JSON manifest")
    parser.add_argument("--manifest-sha256", required=True)
    parser.add_argument(
        "--role", required=True, help="One unique manifest files[].role"
    )
    parser.add_argument(
        "--output-dir", required=True, help="Fresh absolute local directory"
    )
    parser.add_argument("--normalization-receipt", help="Required for MC")
    parser.add_argument("--normalization-sha256", help="Required for MC")
    args = parser.parse_args()
    result = run(
        args.manifest,
        args.role,
        args.output_dir,
        args.manifest_sha256,
        args.normalization_receipt,
        args.normalization_sha256,
    )
    print(result["root_file"])
    print(Path(result["root_file"]).with_name("receipt.json"))


if __name__ == "__main__":
    main()
