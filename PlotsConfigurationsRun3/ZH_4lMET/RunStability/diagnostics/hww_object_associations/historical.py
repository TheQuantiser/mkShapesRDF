"""Read-only checks of pinned central NanoAOD and historical HWW part0 events.

The HWW records are products of an unavailable dirty producer worktree.  This
module observes those records; it does not attribute them to current code.
"""

import hashlib
import json
import math
from pathlib import Path

import uproot

from mkShapesRDF.processor.data.LeptonSel_cfg import ElectronWP, MuonWP


MANIFEST_SHA256 = "c47bc8fde91a4c06aeead3c488115585df85194331d5886024f6f74333d8ee98"
PAIR_SHA256 = "a49c3c2bddda0a0d006114933cdca43125cfaf24d05996944ea66997dcad7f6b"
ELECTRON_WP = "mvaWinter22V2Iso_WP90_tthMVA_Run3"
MUON_WP = "cut_TightID_pfIsoTight_HWW_tthmva_67"
ELECTRON_TIGHT = "Lepton_isTightElectron_" + ELECTRON_WP
MUON_TIGHT = "Lepton_isTightMuon_" + MUON_WP
UINT64_MASK = (1 << 64) - 1

# Source entry, complete event key, and HWW part0 entry.  None means that the
# pinned HWW part0 must contain no matching key.  The MC entries are controls
# from the retained local producer stage ledger, not historical stage proofs.
WITNESSES = {
    ("muon_c", 234): ((379416, 147, 131724611), 65),
    ("egamma_c", 20774): ((379729, 907, 1396820419), 991),
    ("egamma_i", 27025): ((386509, 159, 333332716), 1936),
    ("egamma_i", 46209): ((386509, 735, 1539152813), 3325),
    ("dy_ee", 174): ((1, 384532, 2060318616), None),
    ("dy_mumu", 127): ((1, 260002, 1443526502), None),
}

# Independently reopened on the LPC, 2026-09-30.  The manifest pins central
# UUIDs; these pin the actual historical HWW files used by this diagnostic.
HWW_UUID = {
    "muon_c": "bcc9d2f0-3579-11f1-a0a2-a4bf01606976",
    "egamma_c": "ebce4a80-358e-11f1-aade-3cecef951668",
    "egamma_i": "904011a4-359c-11f1-9867-7cc2559e8508",
    "dy_ee": "c183f92c-3747-11f1-be55-3cecef0de5e4",
    "dy_mumu": "d4c93ad6-37e9-11f1-98cc-3cecef0ddda8",
}

ELECTRON_CUTS = {
    "ROOT::RVecB (Electron_pt.size(), true)": [
        "ROOT::VecOps::abs(Electron_eta) < 2.5",
        "Electron_mvaIso_WP90",
        "Electron_convVeto",
        "Electron_pfRelIso03_all < 0.06",
        "Electron_promptMVA > 0.90",
    ],
    "ROOT::VecOps::abs(Electron_eta) <= 1.479": [
        "ROOT::VecOps::abs(Electron_dxy) < 0.05",
        "ROOT::VecOps::abs(Electron_dz)  < 0.1",
    ],
    "ROOT::VecOps::abs(Electron_eta) > 1.479": [
        "ROOT::VecOps::abs(Electron_dxy) < 0.1",
        "ROOT::VecOps::abs(Electron_dz) <  0.2",
    ],
}
MUON_CUTS = {
    "ROOT::RVecB (Muon_pt.size(), true)": [
        "ROOT::VecOps::abs(Muon_eta) < 2.4",
        "Muon_tightId",
        "ROOT::VecOps::abs(Muon_dz) < 0.1",
        "Muon_pfIsoId >= 4",
        "Muon_promptMVA > 0.67",
    ],
    "Muon_pt <= 20.0": ["ROOT::VecOps::abs(Muon_dxy) < 0.01"],
    "Muon_pt > 20.0": ["ROOT::VecOps::abs(Muon_dxy) < 0.02"],
}
RAW_FIELDS = {
    "Electron": (
        "pt", "eta", "phi", "mvaIso_WP90", "convVeto",
        "pfRelIso03_all", "promptMVA", "dxy", "dz",
    ),
    "Muon": (
        "pt", "eta", "phi", "tightId", "pfIsoId", "promptMVA",
        "dxy", "dz",
    ),
}
HWW_FIELDS = (
    "Lepton_pt", "Lepton_eta", "Lepton_phi", "Lepton_electronIdx",
    "Lepton_muonIdx", ELECTRON_TIGHT, MUON_TIGHT,
    "VetoLepton_pt", "VetoLepton_eta", "VetoLepton_phi",
    "VetoLepton_electronIdx", "VetoLepton_muonIdx",
)


def _load_pinned(path, expected_hash):
    contents = Path(path).read_bytes()
    actual_hash = hashlib.sha256(contents).hexdigest()
    if actual_hash != expected_hash:
        raise ValueError(f"Pinned input hash mismatch: {path}: {actual_hash}")
    return json.loads(contents)


def _one(items, predicate, label):
    found = [item for item in items if predicate(item)]
    if len(found) != 1:
        raise ValueError(f"Expected exactly one {label}; found {len(found)}")
    return found[0]


def _check_working_points():
    electron = ElectronWP["Full2024v15"]["TightObjWP"][ELECTRON_WP]["cuts"]
    muon = MuonWP["Full2024v15"]["TightObjWP"][MUON_WP]["cuts"]
    if electron != ELECTRON_CUTS or muon != MUON_CUTS:
        raise ValueError("Current Full2024v15 named tight-WP expressions changed")


def _key(row, hww=False):
    values = tuple(int(row[field]) for field in ("run", "luminosityBlock", "event"))
    if not (0 <= values[0] < 1 << 32 and 0 <= values[1] < 1 << 32):
        raise ValueError(f"Invalid run/luminosityBlock identity: {values}")
    event = values[2] & UINT64_MASK if hww else values[2]
    if not 0 <= event < 1 << 64:
        raise ValueError(f"Invalid event identity: {values}")
    return values[:2] + (event,)


def _rows(tree, fields, start, stop):
    missing = set(fields) - set(tree.keys())
    if missing:
        raise ValueError(f"Missing required branches: {sorted(missing)}")
    return tree.arrays(list(fields), entry_start=start, entry_stop=stop, library="np")


def _record(arrays, index=0):
    return {name: values[index].tolist() for name, values in arrays.items()}


def _key_count(tree, wanted, stop, hww):
    arrays = _rows(tree, ("run", "luminosityBlock", "event"), 0, stop)
    if arrays["event"].dtype.str != ("<i8" if hww else "<u8"):
        raise ValueError(f"Unexpected {'HWW' if hww else 'central'} event dtype: {arrays['event'].dtype}")
    return sum(
        _key({field: arrays[field][i] for field in arrays}, hww) == wanted
        for i in range(len(arrays["event"]))
    )


def _raw_objects(row, flavor):
    fields = RAW_FIELDS[flavor]
    vectors = {field: row[f"{flavor}_{field}"] for field in fields}
    if len({len(vector) for vector in vectors.values()}) != 1:
        raise ValueError(f"Inconsistent raw {flavor} vector lengths")
    objects = []
    for i in range(len(vectors["pt"])):
        obj = {field: vector[i] for field, vector in vectors.items()}
        eta = abs(obj["eta"])
        dxy = abs(obj["dxy"])
        dz = abs(obj["dz"])
        if flavor == "Electron":
            impact = dxy < (0.05 if eta <= 1.479 else 0.1) and dz < (0.1 if eta <= 1.479 else 0.2)
            tight = (
                eta < 2.5 and obj["mvaIso_WP90"] and obj["convVeto"]
                and obj["pfRelIso03_all"] < 0.06
                and obj["promptMVA"] > 0.90 and impact
            )
        else:
            tight = (
                eta < 2.4 and obj["tightId"] and dz < 0.1
                and obj["pfIsoId"] >= 4 and obj["promptMVA"] > 0.67
                and dxy < (0.01 if obj["pt"] <= 20.0 else 0.02)
            )
        objects.append({"index": i, **obj, "named_tight": bool(tight)})
    return objects


def _association(row, raw):
    n = len(row["Lepton_pt"])
    core = ("Lepton_eta", "Lepton_phi", "Lepton_electronIdx", "Lepton_muonIdx")
    if any(len(row[name]) != n for name in core):
        raise ValueError("Retained core Lepton vectors have unequal lengths")
    comparisons = []
    for i in range(n):
        electron, muon = row["Lepton_electronIdx"][i], row["Lepton_muonIdx"][i]
        if (electron >= 0) == (muon >= 0):
            raise ValueError(f"Ambiguous retained flavor at position {i}")
        flavor, raw_index, branch = (
            ("Electron", electron, ELECTRON_TIGHT) if electron >= 0
            else ("Muon", muon, MUON_TIGHT)
        )
        if raw_index >= len(raw[flavor]):
            raise ValueError(f"Out-of-range raw {flavor} index at retained position {i}")
        obj = raw[flavor][raw_index]
        bit = row[branch][i] if i < len(row[branch]) else None
        comparisons.append({
            "position": i, "flavor": flavor, "raw_index": raw_index,
            "stored_tight": bit, "raw_named_tight": obj["named_tight"],
            "tight_match": bit is not None and bool(bit) == obj["named_tight"],
            "stored_eta": row["Lepton_eta"][i], "raw_eta": obj["eta"],
            "eta_match": math.isclose(row["Lepton_eta"][i], obj["eta"], abs_tol=1e-6),
            "stored_phi": row["Lepton_phi"][i], "raw_phi": obj["phi"],
            "phi_match": math.isclose(row["Lepton_phi"][i], obj["phi"], abs_tol=1e-6),
        })
    return comparisons


def inspect(manifest_path, pair_evidence_path, role, entry, key, hww_entry=None):
    """Inspect one of six pinned witnesses and return a JSON-compatible record.

    DATA witnesses reopen one exact HWW entry and check uniqueness in its
    part0.  MC witnesses check absence by reading only HWW identity columns.
    The central uniqueness check covers only the manifest's bounded prefix.
    """
    entry = int(entry)
    key = tuple(int(part) for part in key)
    expected_key, expected_hww_entry = WITNESSES[(role, entry)]
    if key != expected_key or (hww_entry is not None and hww_entry != expected_hww_entry):
        raise ValueError("Witness entry, full key, or HWW entry differs from the pin")
    _check_working_points()
    manifest = _load_pinned(manifest_path, MANIFEST_SHA256)
    evidence = _load_pinned(pair_evidence_path, PAIR_SHA256)
    if evidence["kind"] != "paired_2024_lowpt_parent_pair_evidence":
        raise ValueError("Unexpected parent-pair evidence type")
    source = _one(manifest["files"], lambda item: item["role"] == role, "manifest role")
    pair = _one(evidence["pairs"], lambda item: item["role"] == role, "parent pair role")
    if (
        source["pfn"] != pair["central_pfn"]
        or source["hww_part0_pfn"] != pair["hww_pfn"]
        or source["source_id"] != pair["source_id"]
        or source["lfn"] != pair["central_lfn"]
        or source["verified_events_entries"] != pair["central_events_entries"]
        or pair["hww_part_index"] != 0
        or not source["entry_start"] <= entry < source["entry_stop"]
    ):
        raise ValueError("Manifest and parent-pair evidence disagree")
    with uproot.open(source["pfn"], timeout=30) as central:
        tree = central["Events"]
        if str(central.file.uuid) != source["verified_root_uuid"] or tree.num_entries != source["verified_events_entries"]:
            raise ValueError("Central ROOT UUID or Events count differs from pin")
        direct = _record(_rows(tree, ("run", "luminosityBlock", "event"), entry, entry + 1))
        if _key(direct) != key or _key_count(tree, key, source["entry_stop"], False) != 1:
            raise ValueError("Central witness key missing or ambiguous in pinned prefix")
        central_uuid = str(central.file.uuid)
    result = {
        "role": role, "source_entry": entry, "event_key": list(key),
        "source_pfn": source["pfn"], "source_uuid": central_uuid,
        "source_events_entries": source["verified_events_entries"],
        "source_prefix": [source["entry_start"], source["entry_stop"]],
        "hww_pfn": pair["hww_pfn"], "hww_part_index": 0,
        "manifest_sha256": MANIFEST_SHA256, "parent_pair_sha256": PAIR_SHA256,
        "historical_producer_source": "unavailable dirty worktree",
    }
    with uproot.open(pair["hww_pfn"], timeout=30) as historical:
        tree = historical["Events"]
        if str(historical.file.uuid) != HWW_UUID[role] or tree.num_entries != pair["hww_events_entries"]:
            raise ValueError("Historical HWW ROOT UUID or Events count differs from pin")
        result.update(hww_uuid=str(historical.file.uuid), hww_events_entries=tree.num_entries)
        matches = _key_count(tree, key, tree.num_entries, True)
        if expected_hww_entry is None:
            if matches:
                raise ValueError(f"MC witness unexpectedly found {matches} times in HWW part0")
            result.update(hww_entry=None, hww_present=False, historical_status="absent_from_pinned_part0")
            return result
        if matches != 1:
            raise ValueError(f"Historical HWW witness has {matches} part0 key matches")
        fields = HWW_FIELDS + tuple(f"{flavor}_{field}" for flavor in RAW_FIELDS for field in RAW_FIELDS[flavor])
        row = _record(_rows(tree, ("run", "luminosityBlock", "event") + fields, expected_hww_entry, expected_hww_entry + 1))
        if _key(row, True) != key:
            raise ValueError("Exact historical HWW entry does not have the pinned full key")
        raw = {flavor: _raw_objects(row, flavor) for flavor in RAW_FIELDS}
        comparisons = _association(row, raw)
        veto = {name: row[name] for name in HWW_FIELDS if name.startswith("VetoLepton_")}
        retained = {name: row[name] for name in HWW_FIELDS if name.startswith("Lepton_")}
        result.update(
            hww_entry=expected_hww_entry, hww_present=True, historical_status="retained",
            raw=raw, veto=veto, retained=retained,
            associations=comparisons,
            invariant={
                "tight": all(item["tight_match"] for item in comparisons),
                "eta": all(item["eta_match"] for item in comparisons),
                "phi": all(item["phi_match"] for item in comparisons),
                "tight_vector_lengths": all(len(row[name]) == len(row["Lepton_pt"]) for name in (ELECTRON_TIGHT, MUON_TIGHT)),
            },
        )
        return result
