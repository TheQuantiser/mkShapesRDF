#!/usr/bin/env python3
"""Direct, read-only ROOT displays of fixed central/HWWNano event pairs."""

import argparse
import hashlib
import json
import math
from pathlib import Path
import sys
import time

MANIFEST_SHA256 = "c47bc8fde91a4c06aeead3c488115585df85194331d5886024f6f74333d8ee98"
WPS = {
    "Electron": "mvaWinter22V2Iso_WP90_tthMVA_Run3",
    "Muon": "cut_TightID_pfIsoTight_HWW_tthmva_67",
}
FIELDS = {
    "Electron": ("pt", "eta", "phi", "charge", "mvaIso_WP90", "convVeto",
                 "pfRelIso03_all", "promptMVA", "dxy", "dz"),
    "Muon": ("pt", "eta", "phi", "charge", "tightId", "pfIsoId",
             "promptMVA", "dxy", "dz"),
}
HWW_ID = {
    "muon_c": ("bcc9d2f0-3579-11f1-a0a2-a4bf01606976", 316341),
    "egamma_c": ("ebce4a80-358e-11f1-aade-3cecef951668", 49200),
    "egamma_i": ("904011a4-359c-11f1-9867-7cc2559e8508", 44596),
    "dy_ee": ("c183f92c-3747-11f1-be55-3cecef0de5e4", 68421),
    "dy_mumu": ("d4c93ad6-37e9-11f1-98cc-3cecef0ddda8", 88692),
}
# Zero-based source/HWW entries, full key, required observed mismatch fields.
CASES = {
    "muon_c": ("muon_c", 234, 65, (379416, 147, 131724611), {"tight"}),
    "egamma_c": ("egamma_c", 20774, 991, (379729, 907, 1396820419), {"tight"}),
    "egamma_i_eta": ("egamma_i", 27025, 1936, (386509, 159, 333332716), {"eta"}),
    "egamma_i_both": ("egamma_i", 46209, 3325, (386509, 735, 1539152813), {"tight", "eta"}),
    "dy_ee_singleton": ("dy_ee", 8, 2, (1, 384532, 2060317109), set()),
    "dy_mumu_singleton": ("dy_mumu", 102, 39, (1, 260002, 1443526295), set()),
    "dy_ee_association": ("dy_ee", 1480, 632, (1, 404199, 2165694222), {"tight"}),
}
TOLERANCE = 1e-6  # Coordinates are the same raw float values, not smeared pT.
UINT64_MASK = (1 << 64) - 1


def require(condition, message):
    if not condition:
        raise ValueError(message)


def table(headers, rows):
    rows = [[format(value, ".12g") if isinstance(value, float) else str(value)
             for value in row] for row in rows]
    widths = [max([len(header), *(len(row[i]) for row in rows)])
              for i, header in enumerate(headers)]
    print(" | ".join(h.ljust(w) for h, w in zip(headers, widths)))
    print("-+-".join("-" * w for w in widths))
    for row in rows:
        print(" | ".join(value.ljust(w) for value, w in zip(row, widths)))


def vector(tree, name):
    branch = tree.GetBranch(name)
    require(bool(branch), f"Missing required branch: {name}")
    values = getattr(tree, name)
    if branch.GetClassName():
        return list(values)
    leaf = tree.GetLeaf(name)
    require(bool(leaf), f"Missing leaf: {name}")
    return [values[i] for i in range(leaf.GetLen())]


def key(tree):
    return (int(tree.run), int(tree.luminosityBlock), int(tree.event) & UINT64_MASK)


def cuts(flavor, obj):
    eta, dxy, dz = abs(obj["eta"]), abs(obj["dxy"]), abs(obj["dz"])
    if flavor == "Electron":
        xy_limit, z_limit = (0.05, 0.1) if eta <= 1.479 else (0.1, 0.2)
        return {
            "abs(eta)<2.5": eta < 2.5,
            "mvaIso_WP90": bool(obj["mvaIso_WP90"]),
            "convVeto": bool(obj["convVeto"]),
            "pfRelIso03_all<0.06": obj["pfRelIso03_all"] < 0.06,
            "promptMVA>0.90": obj["promptMVA"] > 0.90,
            f"abs(dxy)<{xy_limit}": dxy < xy_limit,
            f"abs(dz)<{z_limit}": dz < z_limit,
        }
    xy_limit = 0.01 if obj["pt"] <= 20.0 else 0.02
    return {
        "abs(eta)<2.4": eta < 2.4,
        "tightId": bool(obj["tightId"]),
        "abs(dz)<0.1": dz < 0.1,
        "pfIsoId>=4": obj["pfIsoId"] >= 4,
        "promptMVA>0.67": obj["promptMVA"] > 0.67,
        f"abs(dxy)<{xy_limit}": dxy < xy_limit,
    }


def raw(tree, label):
    objects = {}
    for flavor, fields in FIELDS.items():
        columns = {field: vector(tree, f"{flavor}_{field}") for field in fields}
        count = len(columns["pt"])
        require(count == int(getattr(tree, "n" + flavor)),
                f"Stored n{flavor} disagrees with raw array length")
        require(all(len(v) == count for v in columns.values()),
                f"Unequal {label} raw {flavor} vector lengths")
        objects[flavor] = [{field: columns[field][i] for field in fields}
                           for i in range(count)]
        require(all(math.isfinite(value) for obj in objects[flavor] for value in obj.values()),
                f"Nonfinite {label} raw {flavor} input")
        print(f"\n{label} raw {flavor}: {count} objects")
        if not count:
            continue
        pdg = 11 if flavor == "Electron" else 13
        table(["index", *fields, "pdgId", "named tight"],
              [[i, *obj.values(), -pdg * int(obj["charge"]), all(cuts(flavor, obj).values())]
               for i, obj in enumerate(objects[flavor])])
        print("Named-WP cuts (evaluated at raw HWW/NanoAOD pT, before correction):")
        table(["index", "cut", "decision"],
              [[i, cut, "PASS" if passed else "FAIL"]
               for i, obj in enumerate(objects[flavor]) for cut, passed in cuts(flavor, obj).items()])
    return objects


def display(central, hww, case_name, case):
    role, source_entry, hww_entry, wanted, expected = case
    ctree, htree = central.Get("Events"), hww.Get("Events")
    for tree, entry in [(ctree, source_entry), (htree, hww_entry)]:
        require(0 <= entry < tree.GetEntries() and tree.GetEntry(entry) > 0,
                f"Cannot read Events entry {entry}")
        require(key(tree) == wanted, f"Wrong key at entry {entry}: {key(tree)} != {wanted}")
    print(f"\n=== CASE {case_name}: key={wanted}, zero-based entries {source_entry} / {hww_entry} ===")
    for label, file, entry in [("CENTRAL", central, source_entry), ("HISTORICAL HWW part0", hww, hww_entry)]:
        print(f"{label}: {file.GetName()}\n  UUID={file.GetUUID().AsString()}, tree=Events, entry={entry}")
    craw, hraw = raw(ctree, "CENTRAL"), raw(htree, "HWW")
    differences = []
    for flavor in FIELDS:
        require(len(craw[flavor]) == len(hraw[flavor]), f"Raw {flavor} counts differ")
        for i, (cobj, hobj) in enumerate(zip(craw[flavor], hraw[flavor])):
            for field in FIELDS[flavor]:
                if cobj[field] != hobj[field]:
                    differences.append([flavor, i, field, cobj[field], hobj[field]])
    print("\nCentral versus HWW raw cut inputs: " + ("EXACTLY EQUAL" if not differences else "DIFFERENCES"))
    if differences:
        table(["flavor", "raw index", "field", "central", "HWW raw"], differences)
    core_fields = ("pt", "eta", "phi", "pdgId", "electronIdx", "muonIdx")
    core = {}
    for collection in ["VetoLepton", "Lepton"]:
        core[collection] = {field: vector(htree, f"{collection}_{field}") for field in core_fields}
        n = len(core[collection]["pt"])
        require(all(len(v) == n for v in core[collection].values()), f"Unequal {collection} core lengths")
        print(f"\nHistorical {collection} collection ({n} slots):")
        table(["slot", *core_fields], [[i, *(core[collection][f][i] for f in core_fields)] for i in range(n)])
    bits = {flavor: vector(htree, "Lepton_isTight" + flavor + "_" + wp) for flavor, wp in WPS.items()}
    print("\nALL stored tight-decision vector lengths (no truncation or repair):")
    bit_names = sorted(b.GetName() for b in htree.GetListOfBranches() if b.GetName().startswith("Lepton_isTight"))
    table(["branch", "length", "stored values"], [[b, len(vector(htree, b)), vector(htree, b)] for b in bit_names])
    leptons = core["Lepton"]
    n = len(leptons["pt"])
    require(int(htree.nLepton) == n, "Stored nLepton disagrees with core arrays")
    observed, rows = set(), []
    for i in range(n):
        e, m = int(leptons["electronIdx"][i]), int(leptons["muonIdx"][i])
        require((e >= 0) != (m >= 0), f"Ambiguous flavor at retained slot {i}")
        flavor, index = ("Electron", e) if e >= 0 else ("Muon", m)
        require(index < len(hraw[flavor]), f"Invalid raw index at slot {i}")
        obj = hraw[flavor][index]
        require(int(leptons["pdgId"][i]) == -(11 if e >= 0 else 13) * int(obj["charge"]),
                f"Flavor/charge/index mismatch at slot {i}")
        require(i < len(bits[flavor]), f"Missing tight bit at slot {i}")
        require(all(math.isfinite(leptons[field][i]) for field in ["pt", "eta", "phi"]),
                f"Nonfinite stored kinematics at retained slot {i}")
        expected_bit, stored_bit = all(cuts(flavor, obj).values()), bool(bits[flavor][i])
        eta_delta = leptons["eta"][i] - obj["eta"]
        phi_delta = math.remainder(leptons["phi"][i] - obj["phi"], 2 * math.pi)
        failures = [f for f, bad in [("tight", expected_bit != stored_bit),
                                    ("eta", abs(eta_delta) > TOLERANCE),
                                    ("phi", abs(phi_delta) > TOLERANCE)] if bad]
        observed.update(failures)
        ratio = leptons["pt"][i] / obj["pt"] if obj["pt"] else "undefined"
        rows.append([i, flavor, index, obj["pt"], leptons["pt"][i], ratio,
                     obj["eta"], leptons["eta"][i], obj["phi"], leptons["phi"][i],
                     expected_bit, stored_bit, "MISMATCH: " + ",".join(failures) if failures else "OK"])
        if expected_bit != stored_bit:
            print(f"MISMATCH slot {i}: stored tight={stored_bit}, indexed raw tight={expected_bit}")
    print("\nRetained slot versus the RAW HWW object named by its raw index:")
    table(["slot", "flavor", "raw index", "raw pT", "stored pT", "pT ratio",
           "raw eta", "stored eta", "raw phi", "stored phi", "expected tight", "stored tight", "result"], rows)
    require(expected <= observed, f"Expected discrepancy did not reproduce: {expected} versus {observed}")
    if case_name.endswith("singleton"):
        require(n == 1, f"Expected historical singleton, found {n} retained leptons")
        print("FACT: this MC __l2tight part0 stores nLepton=1. This read does not identify its historical rejection/acceptance operation.")
    if case_name == "dy_ee_association":
        require(n >= 2 and observed, "Main MC association witness must show a real retained-object mismatch")
    if case_name == "egamma_i_eta":
        require(observed == {"eta"}, f"Expected eta-only observation, found {observed}")
    print(f"OBSERVATION REPRODUCED: {case_name}; mismatching fields={sorted(observed)}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", choices=CASES, action="append", help="Show one fixed case (repeatable); default: all")
    args = parser.parse_args()
    import ROOT
    ROOT.PyConfig.IgnoreCommandLineOptions = True
    ROOT.gROOT.SetBatch(True)
    ROOT.TFile.SetOpenTimeout(30000)
    # One ordinary TTree/GetEntry loop scans only integer identity branches.
    # It checks uniqueness of the displayed keys, not full-population deduplication.
    ROOT.gInterpreter.Declare(r'''
    #include <TTree.h>
    #include <TLeaf.h>
    #include <vector>
    #include <stdexcept>
    std::vector<std::vector<Long64_t>> root_inspection_matches(
        TTree* tree, const std::vector<ULong64_t>& keys) {
      std::vector<std::vector<Long64_t>> found(keys.size()/3);
      tree->SetBranchStatus("*", false);
      for (auto name : {"run", "luminosityBlock", "event"}) tree->SetBranchStatus(name, true);
      auto runLeaf = tree->GetLeaf("run");
      auto lumiLeaf = tree->GetLeaf("luminosityBlock");
      auto eventLeaf = tree->GetLeaf("event");
      for (Long64_t entry=0; entry<tree->GetEntries(); ++entry) {
        if (tree->GetEntry(entry)<=0) throw std::runtime_error("Identity GetEntry failed");
        const auto run = static_cast<ULong64_t>(runLeaf->GetValueLong64());
        const auto lumi = static_cast<ULong64_t>(lumiLeaf->GetValueLong64());
        const auto event = static_cast<ULong64_t>(eventLeaf->GetValueLong64());
        for (size_t i=0; i<found.size(); ++i)
          if (run==keys[3*i] && lumi==keys[3*i+1] && event==keys[3*i+2]) found[i].push_back(entry);
      }
      return found;
    }
    ''')
    manifest = Path(__file__).with_name("inputs") / "inputs.json"
    data = manifest.read_bytes()
    require(hashlib.sha256(data).hexdigest() == MANIFEST_SHA256, "Pinned manifest hash changed")
    sources = {item["role"]: item for item in json.loads(data)["files"]}
    selected = args.case or list(CASES)
    print(f"Direct ROOT inspection; ROOT {ROOT.gROOT.GetVersion()}, Python {sys.version.split()[0]}")
    print(f"Script SHA-256={hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}")
    print(f"Manifest SHA-256={MANIFEST_SHA256}; eta/wrapped-phi tolerance={TOLERANCE}")
    print("Named WP source: mkShapesRDF 69ff2dad, Full2024v15 LeptonSel_cfg.py; definitions are frozen locally, no framework imports.")
    start = time.monotonic()
    for role in dict.fromkeys(CASES[name][0] for name in selected):
        source = sources[role]
        cases = [(name, CASES[name]) for name in selected if CASES[name][0] == role]
        files = []
        try:
            for kind, pfn, uuid, entries in [
                ("central", source["pfn"], source["verified_root_uuid"], source["verified_events_entries"]),
                ("HWW", source["hww_part0_pfn"], *HWW_ID[role]),
            ]:
                file = ROOT.TFile.Open(pfn, "READ")
                require(bool(file) and not file.IsZombie(), f"Cannot open {pfn}")
                files.append(file)
                tree = file.Get("Events")
                require(bool(tree) and tree.InheritsFrom("TTree"), f"Missing Events tree: {pfn}")
                require(file.GetUUID().AsString() == uuid and tree.GetEntries() == entries,
                        f"UUID or entry count changed: {pfn}")
                for branch in ["run", "luminosityBlock", "event"]:
                    leaf = tree.GetLeaf(branch)
                    require(bool(leaf) and leaf.GetTypeName() in ["UInt_t", "ULong64_t", "Long64_t"],
                            f"Noninteger/missing identity branch {branch}")
                targets = ROOT.std.vector("ULong64_t")([word for _, c in cases for word in c[3]])
                print(f"\nChecking {role} {kind}: complete {entries:,}-entry identity-only scan for {len(cases)} fixed keys", flush=True)
                matches = ROOT.root_inspection_matches(tree, targets)
                for (_, case), found in zip(cases, matches):
                    expected_entry = case[1] if kind == "central" else case[2]
                    require(list(found) == [expected_entry], f"Missing/duplicate/wrong entry for {case[3]}: {list(found)}")
                needed = {"run", "luminosityBlock", "event", "nElectron", "nMuon"}
                needed.update(f"{flavor}_{field}" for flavor, fields in FIELDS.items() for field in fields)
                if kind == "HWW":
                    needed.add("nLepton")
                    needed.update(f"{c}_{f}" for c in ["Lepton", "VetoLepton"]
                                  for f in ["pt", "eta", "phi", "pdgId", "electronIdx", "muonIdx"])
                    needed.update(b.GetName() for b in tree.GetListOfBranches() if b.GetName().startswith("Lepton_isTight"))
                    needed.update("Lepton_isTight" + f + "_" + wp for f, wp in WPS.items())
                for branch in needed:
                    require(bool(tree.GetBranch(branch)), f"Missing required branch: {kind} {branch}")
                    tree.SetBranchStatus(branch, True)
            for name, case in cases:
                display(*files, name, case)
        finally:
            for file in files:
                file.Close()
    print(f"\nPASS: all {len(selected)} fixed observations reproduced; elapsed={time.monotonic()-start:.2f}s")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr, flush=True)
        sys.exit(1)
