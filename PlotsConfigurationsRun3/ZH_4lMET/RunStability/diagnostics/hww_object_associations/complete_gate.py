"""One complete pinned DY producer traversal through the actual 2024 l2tight gate.

The second gate branch realigns the already computed tight vectors and
requires two retained leptons before the unchanged two-position predicate.
Historical HWW membership is joined afterward by source entry.
No ROOT output, snapshot, or source normalization is produced.
"""

import argparse
import csv
import gzip
import hashlib
import json
import math
import runpy
import subprocess
import time
from collections import defaultdict
from pathlib import Path

from full_mc import CHAIN, HERE, MANIFEST_SHA, NORMALIZATION_SHA, PRODUCTION, REPO


ROLES = tuple(NORMALIZATION_SHA)
WITNESSES = {"dy_ee": 174, "dy_mumu": 127}
PRODUCER_TREES = {
    "mkShapesRDF/processor": "9c86299cdd2a8419fd30f48ad73a4fc530a567aa",
    "mkShapesRDF/include": "311e5fd6311c74b58ba233258acb2018aabcdd7d",
}


def checked_producer_source():
    """Reject a changed producer tree while allowing demo-only commits."""
    status = subprocess.run(
        ["git", "status", "--porcelain", "--", *PRODUCER_TREES],
        cwd=REPO, check=True, text=True, capture_output=True,
    ).stdout.strip()
    if status:
        raise ValueError(f"Producer tree has local changes: {status}")
    observed = {}
    for path, expected in PRODUCER_TREES.items():
        actual = subprocess.run(
            ["git", "rev-parse", f"HEAD:{path}"], cwd=REPO,
            check=True, text=True, capture_output=True,
        ).stdout.strip()
        if actual != expected:
            raise ValueError(f"Producer tree changed since pinned demo: {path} {actual}")
        observed[path] = actual
    return observed


def checked_source(manifest_path, role):
    raw = Path(manifest_path).read_bytes()
    if hashlib.sha256(raw).hexdigest() != MANIFEST_SHA:
        raise ValueError("Pinned manifest bytes changed")
    matches = [row for row in json.loads(raw)["files"] if row["role"] == role]
    if len(matches) != 1 or matches[0]["is_data"]:
        raise ValueError(f"Expected one pinned MC source for {role}")
    source = matches[0]
    receipt_path = HERE / "inputs" / f"normalization-{role}.json"
    if hashlib.sha256(receipt_path.read_bytes()).hexdigest() != NORMALIZATION_SHA[role]:
        raise ValueError("Pinned historical baseW receipt changed")
    receipt = json.loads(receipt_path.read_text())
    if (receipt["status"] != "verified" or receipt["method"] != "retained_hww_baseW"
        or receipt["sample"] != source["sample"] or receipt["dataset"] != source["dataset"]
        or receipt["matched_input_lfn"] != source["lfn"]
        or receipt["historical_hww_part0_uri"] != source["hww_part0_pfn"]):
        raise ValueError("Pinned baseW receipt does not identify this input")
    return source, receipt


def mapping_for_role(join_dir, role, source):
    path = Path(join_dir) / f"{role}-source-entry-map.tsv.gz"
    report = json.loads((Path(join_dir) / f"{role}-join.json").read_text())
    if (report["role"] != role or report["source_pfn"] != source["pfn"]
        or report["source"]["uuid"] != source["verified_root_uuid"]
        or report["hww_part0_pfn"] != source["hww_part0_pfn"]
        or report["counts"]["ambiguous_keys"] or report["counts"]["output_only"]):
        raise ValueError("Historical join contains ambiguous or output-only identities")
    result = []
    actual_hash = hashlib.sha256(path.read_bytes()).hexdigest()
    if actual_hash != report["mapping"]["sha256"]:
        raise ValueError("Historical join map bytes differ from their receipt")
    with gzip.open(path, "rt", encoding="ascii", newline="") as stream:
        reader = csv.DictReader(stream, delimiter="\t")
        if reader.fieldnames != ["source_entry", "hww_entry", "status"]:
            raise ValueError("Unexpected join mapping schema")
        for expected, row in enumerate(reader):
            if int(row["source_entry"]) != expected:
                raise ValueError("Join mapping is incomplete or unordered")
            if row["status"] not in ("matched", "input_only"):
                raise ValueError("Ambiguous join row")
            result.append(int(row["hww_entry"]) if row["status"] == "matched" else None)
    matched_entries = [x for x in result if x is not None]
    if (len(result) != source["verified_events_entries"]
        or len(matched_entries) != report["counts"]["matched"]
        or len(set(matched_entries)) != len(matched_entries)
        or any(not 0 <= x < report["hww_part0"]["events_entries"] for x in matched_entries)):
        raise ValueError("Join mapping count mismatch")
    return result, {"path": str(path), "sha256": actual_hash,
                    "join_report": str(Path(join_dir) / f"{role}-join.json")}


ASSOCIATION_CPP = r"""
#include <stdexcept>
#include <cstdlib>
#include <vector>
#include <set>
#include <utility>
ROOT::RVecI hwwAssociationPositions(const ROOT::RVecI &ve, const ROOT::RVecI &vm,
                                    const ROOT::RVecI &vp, const ROOT::RVecI &re,
                                    const ROOT::RVecI &rm, const ROOT::RVecI &rp) {
  if (ve.size()!=vm.size() || ve.size()!=vp.size() || re.size()!=rm.size() || re.size()!=rp.size())
    throw std::runtime_error("inconsistent prefilter or retained lepton vector lengths");
  auto valid = [](int e, int m, int pdg) {
    return (e>=0 && m==-1 && std::abs(pdg)==11) ||
           (e==-1 && m>=0 && std::abs(pdg)==13);
  };
  std::set<std::pair<int,int>> seen_pre, seen_retained;
  for (size_t k=0; k<ve.size(); ++k) {
    if (!valid(ve[k],vm[k],vp[k]) || !seen_pre.insert({ve[k],vm[k]}).second)
      throw std::runtime_error("invalid or duplicated prefilter raw lepton identity");
  }
  ROOT::RVecI positions;
  for (size_t j=0; j<re.size(); ++j) {
    if (!valid(re[j],rm[j],rp[j]) || !seen_retained.insert({re[j],rm[j]}).second)
      throw std::runtime_error("invalid or duplicated retained raw lepton identity");
    int found=-1;
    for (size_t k=0; k<ve.size(); ++k)
      if (ve[k]==re[j] && vm[k]==rm[j]) {
        if (found>=0 || vp[k]!=rp[j]) throw std::runtime_error("ambiguous/inconsistent lepton identity");
        found=(int)k;
      }
    if (found<0) throw std::runtime_error("retained lepton absent from prefilter collection");
    positions.push_back(found);
  }
  return positions;
}
template<class Bits> Bits hwwAlignedBits(const Bits &bits, const ROOT::RVecI &positions,
                                        size_t prefilter_size) {
  if (bits.size()!=prefilter_size) throw std::runtime_error("tight vector has wrong prefilter length");
  Bits aligned;
  for (auto k: positions) {
    if (k<0 || (size_t)k>=bits.size()) throw std::runtime_error("tight-vector index out of bounds");
    aligned.push_back(bits[k]);
  }
  if (aligned.size()!=positions.size()) throw std::runtime_error("aligned tight vector has wrong length");
  return aligned;
}
"""


def vector(value):
    return [ord(x) if isinstance(x, str) else int(x) for x in value]


def cell():
    return {"events": 0, "gen_sumw": 0.0, "gen_sumw2": 0.0}


def add(count, weight):
    count["events"] += 1
    count["gen_sumw"] += weight
    count["gen_sumw2"] += weight * weight


def run(manifest_path, join_dir, output_dir, role):
    import ROOT
    import mkShapesRDF
    from mkShapesRDF.processor.framework.mRDF import mRDF
    from mkShapesRDF.processor.framework.Productions_cfg import Productions
    from mkShapesRDF.processor.framework.Steps_cfg import Steps
    from mkShapesRDF.processor.data.LeptonSel_cfg import ElectronWP, MuonWP
    from mkShapesRDF.processor.modules.L2TightSelection import L2TightSelection

    started = time.monotonic()
    if Path(output_dir).exists():
        raise FileExistsError(f"Output directory already exists: {output_dir}")
    producer_trees = checked_producer_source()
    ROOT.gROOT.SetBatch(True)
    if ROOT.IsImplicitMTEnabled():
        raise RuntimeError("This diagnostic requires one deterministic RDataFrame event loop")
    source, receipt = checked_source(manifest_path, role)
    framework = Path(mkShapesRDF.__file__).resolve().parent
    if framework.parent != REPO:
        raise RuntimeError("Imported mkShapesRDF is not the demo worktree")
    root_file = ROOT.TFile.Open(source["pfn"], "READ")
    try:
        tree = root_file.Get("Events") if root_file else None
        if (not tree or tree.GetEntries()!=source["verified_events_entries"]
            or str(root_file.GetUUID().AsString()).strip("{}").lower()!=source["verified_root_uuid"]):
            raise ValueError("Pinned source ROOT UUID or complete entry count changed")
    finally:
        if root_file:
            root_file.Close()
    membership, join_meta = mapping_for_role(join_dir, role, source)
    ROOT.gInterpreter.Declare(f'#include "{framework / "include/headers.hh"}"')
    ROOT.gInterpreter.Declare(ASSOCIATION_CPP)
    xs_file = Productions[PRODUCTION]["xsFile"]
    xs_db = runpy.run_path(str((REPO / "mkShapesRDF/processor/framework" / xs_file).resolve()))["xs_db"]
    xs = float(xs_db[source["sample"]][0].split("=")[1])
    if (not math.isclose(xs, receipt["cross_section_pb"], rel_tol=1e-12)
        or not math.isclose(receipt["gen_event_sumw"], xs*1000/receipt["historical_hww_baseW"], rel_tol=1e-12)):
        raise ValueError("Pinned historical baseW/catalog cross section mismatch")
    state = {"sampleName": source["sample"], "files": [source["pfn"]],
             "xs_db": xs_db, "values": []}
    replacements = {"RPLME_FW": str(framework), "RPLME_CMSSW": "Full2024v15",
                    "RPLME_LUMI": "", "RPLME_SAMPLENAME": source["sample"],
                    "RPLME_genEventSumw": repr(receipt["gen_event_sumw"])}
    df = mRDF().readRDF("Events", [source["pfn"]])
    df = df.Define("diagnostic_source_entry", "rdfentry_")
    actions = [("input_entries", df.Count()), ("input_gen_sumw", df.Sum("genWeight"))]
    df = df.Define("diagnostic_gen_weight2", "(double)genWeight*(double)genWeight")
    actions.append(("input_gen_sumw2", df.Sum("diagnostic_gen_weight2")))
    df = df.Filter("((nElectron+nMuon)>1)")
    actions.append(("chain_selection", df.Count()))
    for name in Steps[CHAIN]["subTargets"]:
        if name in ("l2tight", "leptonScale_mc") or name.startswith("finalSnapshot_"):
            break
        spec = Steps[name]
        if spec["isChain"]:
            raise ValueError("Unexpected nested producer chain")
        exec("from " + spec["import"] + " import *", state)
        declaration = spec["declare"]
        for old, new in replacements.items():
            declaration = declaration.replace(old, new)
        exec(declaration, state)
        df = eval(spec["module"], state).run(df, state["values"])
        actions.append((name, df.Count()))
    pre = df
    ele_wp = [f"Lepton_isTightElectron_{wp}" for wp in ElectronWP["Full2024v15"]["TightObjWP"]]
    mu_wp = [f"Lepton_isTightMuon_{wp}" for wp in MuonWP["Full2024v15"]["TightObjWP"]]
    wp_names = ele_wp + mu_wp
    pre = pre.Define("diagnostic_positions",
        "hwwAssociationPositions(VetoLepton_electronIdx,VetoLepton_muonIdx,VetoLepton_pdgId,"
        "Lepton_electronIdx,Lepton_muonIdx,Lepton_pdgId)")
    columns = ["diagnostic_source_entry", "run", "luminosityBlock", "event", "genWeight",
               "VetoLepton_electronIdx", "VetoLepton_muonIdx", "Lepton_electronIdx",
               "Lepton_muonIdx", "diagnostic_positions"] + wp_names
    taken = {name: pre.df.Take[pre.df.GetColumnType(name)](name) for name in columns}
    actions.extend((f"take:{name}", action) for name, action in taken.items())
    original = L2TightSelection("Full2024v15").runModule(pre.Copy(), state["values"])
    actual_entries = original.df.Take[original.df.GetColumnType("diagnostic_source_entry")]("diagnostic_source_entry")
    actions.append(("actual_pass_entries", actual_entries))
    aligned = pre.Copy()
    for name in wp_names:
        aligned = aligned.Redefine(name,
            f"hwwAlignedBits({name},diagnostic_positions,VetoLepton_electronIdx.size())")
    # The unchanged gate reads [0] and [1]. A one-lepton event cannot pass a
    # correctly associated two-lepton predicate; keep it out of this branch.
    aligned = aligned.Filter("Lepton_pt.size()>=2")
    aligned = L2TightSelection("Full2024v15").runModule(aligned, state["values"])
    aligned_entries = aligned.df.Take[aligned.df.GetColumnType("diagnostic_source_entry")]("diagnostic_source_entry")
    actions.append(("aligned_pass_entries", aligned_entries))
    ROOT.RDF.RunGraphs([action for _, action in actions])
    values = {name: action.GetValue() for name, action in actions}
    stage_counts = {name: int(values[name]) for name, _ in actions if name == "chain_selection" or name in Steps[CHAIN]["subTargets"]}
    actual_set = set(map(int, values["actual_pass_entries"]))
    aligned_set = set(map(int, values["aligned_pass_entries"]))
    entries = list(map(int, values["take:diagnostic_source_entry"]))
    if len(entries)!=len(set(entries)) or len(entries)!=stage_counts["formulasMC"]:
        raise ValueError("Incomplete or duplicated pre-gate source entries")
    if any(not 0<=x<len(membership) for x in entries):
        raise ValueError("Out-of-range pre-gate source entry")
    if not actual_set.issubset(entries) or not aligned_set.issubset(entries):
        raise ValueError("Gate output is not a subset of pre-gate events")
    historical_set = {entry for entry, hww_entry in enumerate(membership) if hww_entry is not None}
    historical_gate_symmetric_difference = len(actual_set ^ historical_set)
    if historical_gate_symmetric_difference:
        raise ValueError(f"Current original gate differs from paired historical part0 in "
                         f"{historical_gate_symmetric_difference} source entries")
    totals = defaultdict(cell)
    cells = defaultdict(cell)
    witnesses = []
    examples = defaultdict(list)
    for i, entry in enumerate(entries):
        weight = float(values["take:genWeight"][i])
        if not math.isfinite(weight):
            raise ValueError(f"Nonfinite genWeight at source entry {entry}")
        retained = vector(values["take:Lepton_electronIdx"][i])
        outcome = ("passes_both" if entry in actual_set and entry in aligned_set else
                   "rejected_only_by_actual" if entry not in actual_set and entry in aligned_set else
                   "accepted_only_by_actual" if entry in actual_set else "rejected_both")
        status = "historical_part0" if membership[entry] is not None else "absent_from_part0"
        add(cells[(outcome,status)], weight)
        add(totals[outcome], weight)
        if len(retained)<2:
            add(totals["fewer_than_two_retained_leptons"], weight)
        pre_e = vector(values["take:VetoLepton_electronIdx"][i])
        pre_m = vector(values["take:VetoLepton_muonIdx"][i])
        ret_m = vector(values["take:Lepton_muonIdx"][i])
        positions = vector(values["take:diagnostic_positions"][i])
        if len(retained)!=len(positions) or len(pre_e)!=len(pre_m):
            raise ValueError("Association vector length mismatch")
        # The live gate may short-circuit its OR. Validate every configured
        # vector, including those whose value was not needed for that event.
        all_bits = {}
        for name in wp_names:
            bits = vector(values[f"take:{name}"][i])
            if len(bits) != len(pre_e) or any(bit not in (0, 1) for bit in bits):
                raise ValueError(f"Invalid prefilter WP vector: {name}, source entry {entry}")
            all_bits[name] = bits
        if entry == WITNESSES[role] or len(examples[(outcome,status)]) < 2:
            wp = {}
            for name in wp_names:
                original_bits = all_bits[name]
                wp[name] = {"actual_prefilter": original_bits,
                            "aligned_retained": [original_bits[k] for k in positions]}
            item = {"source_entry": entry, "historical_hww_entry": membership[entry],
                    "key": [int(values[f"take:{key}"][i]) for key in ("run","luminosityBlock","event")],
                    "genWeight": weight, "outcome": outcome,
                    "prefilter_electronIdx": pre_e, "prefilter_muonIdx": pre_m,
                    "retained_electronIdx": retained, "retained_muonIdx": ret_m,
                    "prefilter_positions_for_retained": positions, "wp_vectors": wp}
            if entry == WITNESSES[role]:
                witnesses.append(item)
            else:
                examples[(outcome,status)].append(item)
    if len(witnesses)!=1:
        raise ValueError("Pinned witness did not reach pre-gate stage")
    outcomes = ("passes_both", "rejected_only_by_actual", "accepted_only_by_actual", "rejected_both")
    if sum(totals[outcome]["events"] for outcome in outcomes) != len(entries):
        raise ValueError("Outcome partition does not cover pre-gate events")
    report = {"schema_version": 1, "role": role, "sample": source["sample"],
              "dataset": source["dataset"], "source_pfn": source["pfn"],
              "source_uuid": source["verified_root_uuid"], "historical_hww_part0_pfn": source["hww_part0_pfn"],
              "input_entries": int(values["input_entries"]),
              "input_gen_sumw": float(values["input_gen_sumw"]),
              "input_gen_sumw2": float(values["input_gen_sumw2"]),
              "stage_counts_before_gate": stage_counts,
              "original_gate_pass": len(actual_set), "aligned_gate_pass": len(aligned_set),
              "outcome_totals": dict(totals),
              "outcome_by_historical_membership": [
                  {"outcome": outcome, "historical_membership": status, **counts}
                  for (outcome,status), counts in sorted(cells.items())],
              "witnesses": witnesses + [item for group in examples.values() for item in group],
              "configured_chain": CHAIN, "all_wp_columns": wp_names,
              "normalization_receipt_sha256": NORMALIZATION_SHA[role],
              "producer_source_tree_sha1": producer_trees,
              "normalization_receipt_use": "Supplies the existing producer baseW module only; no partial-file normalization or yield is reported.",
              "membership": join_meta, "elapsed_seconds": time.monotonic()-started,
              "interpretation_limit": "Current clean-source gate counterfactual versus membership in one historical paired part0; historical dirty producer stage is unavailable."}
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=False)
    path = output_dir / f"{role}-complete-gate.json"
    path.write_text(json.dumps(report, indent=2, sort_keys=True)+"\n")
    return path, report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--join-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--role", choices=ROLES, required=True)
    args = parser.parse_args()
    path, report = run(args.manifest, args.join_dir, args.output_dir, args.role)
    print(json.dumps({"result": str(path), "role": args.role,
                      "pre_gate": report["stage_counts_before_gate"]["formulasMC"],
                      "original_gate_pass": report["original_gate_pass"],
                      "aligned_gate_pass": report["aligned_gate_pass"],
                      "elapsed_seconds": report["elapsed_seconds"]}, sort_keys=True))
