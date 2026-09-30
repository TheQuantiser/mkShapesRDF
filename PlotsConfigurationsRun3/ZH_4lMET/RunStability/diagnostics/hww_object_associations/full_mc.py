"""Run the configured 2024 MC producer, on one entry, only through l2tight.

No snapshot, histogram, or HWWNano file is written. The source-normalization
receipt only supplies the configured baseW module's required denominator;
no yields or absolute weights are interpreted in this diagnostic.
"""

import argparse
import hashlib
import json
import math
import runpy
from pathlib import Path


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[4]
CHAIN = "MCl2loose2024v15__MCCorr2024v15__JERFrom23BPix__l2tight"
PRODUCTION = "Summer24_150x_nAODv15_Full2024v15"
MANIFEST_SHA = "c47bc8fde91a4c06aeead3c488115585df85194331d5886024f6f74333d8ee98"
NORMALIZATION_SHA = {
    "dy_ee": "557e7e75c054099e303e0e0258a1dd0170f601ba2752c13656aeb473e76efa4a",
    "dy_mumu": "366729024becd971f5205c511fb13325d3bb26823b86b02da0d0b6a3c7b77eba",
}


def run(manifest_path, role, entry, key):
    import ROOT
    import mkShapesRDF
    from mkShapesRDF.processor.framework.mRDF import mRDF
    from mkShapesRDF.processor.framework.Productions_cfg import Productions
    from mkShapesRDF.processor.framework.Steps_cfg import Steps

    ROOT.gROOT.SetBatch(True)
    if ROOT.IsImplicitMTEnabled():
        raise RuntimeError("RDataFrame Range requires implicit MT disabled")
    manifest_bytes = Path(manifest_path).read_bytes()
    if hashlib.sha256(manifest_bytes).hexdigest() != MANIFEST_SHA:
        raise ValueError("Pinned input manifest bytes changed")
    manifest = json.loads(manifest_bytes)
    source = next(item for item in manifest["files"] if item["role"] == role)
    if source["is_data"] or not source["entry_start"] <= entry < source["entry_stop"]:
        raise ValueError("Expected one pinned MC source entry")
    receipt_path = HERE / "inputs" / f"normalization-{role}.json"
    if hashlib.sha256(receipt_path.read_bytes()).hexdigest() != NORMALIZATION_SHA[role]:
        raise ValueError("Full-source normalization receipt bytes changed")
    receipt = json.loads(receipt_path.read_text())
    if (receipt["status"] != "verified" or receipt["method"] != "retained_hww_baseW"
        or receipt["sample"] != source["sample"] or receipt["dataset"] != source["dataset"]
        or receipt["matched_input_lfn"] != source["lfn"]
        or receipt["historical_hww_part0_uri"] != source["hww_part0_pfn"]):
        raise ValueError("Normalization receipt does not identify this pinned source")
    framework = Path(mkShapesRDF.__file__).resolve().parent
    if framework.parent != REPO:
        raise RuntimeError("Imported producer package is not from the demo worktree")
    source_file = ROOT.TFile.Open(source["pfn"], "READ")
    try:
        tree = source_file.Get("Events") if source_file else None
        if (not tree or tree.GetEntries() != source["verified_events_entries"]
            or str(source_file.GetUUID().AsString()).strip("{}").lower() != source["verified_root_uuid"]):
            raise ValueError("Pinned central Events count/UUID changed")
    finally:
        if source_file:
            source_file.Close()
    ROOT.gInterpreter.Declare(f'#include "{framework / "include/headers.hh"}"')
    xs_file = Productions[PRODUCTION]["xsFile"]
    xs_db = runpy.run_path(str((REPO / "mkShapesRDF/processor/framework" / xs_file).resolve()))["xs_db"]
    xs = float(xs_db[source["sample"]][0].split("=")[1])
    if (not math.isclose(xs, receipt["cross_section_pb"], rel_tol=1e-12)
        or not math.isclose(receipt["gen_event_sumw"], xs * 1000 / receipt["historical_hww_baseW"], rel_tol=1e-12)):
        raise ValueError("Historical baseW and current catalog cross section disagree")
    state = {"sampleName": source["sample"], "files": [source["pfn"]],
             "xs_db": xs_db, "values": []}
    replacements = {"RPLME_FW": str(framework), "RPLME_CMSSW": "Full2024v15",
                    "RPLME_LUMI": "", "RPLME_SAMPLENAME": source["sample"],
                    "RPLME_genEventSumw": repr(receipt["gen_event_sumw"])}
    df = mRDF().readRDF("Events", [source["pfn"]])
    df = df.Define("diagnostic_source_entry", "rdfentry_")
    df.df = df.df.Range(entry, entry + 1)
    identity = df.df.AsNumpy(["run", "luminosityBlock", "event"])
    observed_key = [int(identity[name][0]) for name in ("run", "luminosityBlock", "event")]
    if observed_key != key:
        raise ValueError(f"Pinned source entry/key mismatch: {observed_key} != {key}")
    actions = []
    df = df.Filter("((nElectron+nMuon)>1)")
    actions.append(("chain_selection", df.Count()))
    for name in Steps[CHAIN]["subTargets"]:
        if name.startswith("finalSnapshot_"):
            break
        spec = Steps[name]
        if spec["isChain"]:
            raise ValueError("Nested producer chain is not supported")
        exec("from " + spec["import"] + " import *", state)
        declaration = spec["declare"]
        for old, new in replacements.items():
            declaration = declaration.replace(old, new)
        exec(declaration, state)
        module = eval(spec["module"], state)
        df = module.run(df, state["values"])
        actions.append((name, df.Count()))
        if name == "l2tight":
            break
    stages = [{"step": name, "retained": bool(action.GetValue())}
              for name, action in actions]
    first_loss = next((item["step"] for item in stages if not item["retained"]), None)
    return {"role": role, "source_entry": entry, "key": key,
            "source_pfn": source["pfn"], "configured_chain": CHAIN,
            "normalization_receipt_sha256": NORMALIZATION_SHA[role],
            "stages": stages, "first_failing_step": first_loss,
            "scope": "One-entry current configured MC chain through l2tight; no correction or snapshot executed."}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", type=Path, required=True)
    ap.add_argument("--role", choices=tuple(NORMALIZATION_SHA), required=True)
    ap.add_argument("--entry", type=int, required=True)
    ap.add_argument("--key", nargs=3, type=int, required=True)
    args = ap.parse_args()
    print(json.dumps(run(args.manifest, args.role, args.entry, args.key), sort_keys=True))
