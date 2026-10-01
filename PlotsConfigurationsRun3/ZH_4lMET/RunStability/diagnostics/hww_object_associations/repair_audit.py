"""Independently reopen repaired/original nominal snapshots and saved ledgers.

No producer execution or central NanoAOD scan is performed. Historical HWW
reads are restricted to identity, multiplicity, and original-index branches.
WP expectations use their saved ORIGINAL defining-stage vectors, never a
working point reevaluated on corrected pT. NPZ object arrays are loaded only
from the explicitly supplied, trusted local diagnostic production directories.
"""

import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path

import awkward as ak
import numpy as np
import uproot

from complete_gate import mapping_for_role
from full_mc import HERE, MANIFEST_SHA


KEYS = ("run", "luminosityBlock", "event")
CORE = ("pt", "eta", "phi", "pdgId", "electronIdx", "muonIdx")
OUTCOMES = (
    "passes_both",
    "rejected_only_by_actual",
    "accepted_only_by_actual",
    "rejected_both",
)
EXPECTED = {"dy_ee": [42732, 606, 25689, 5911], "dy_mumu": [83368, 5914, 5324, 21697]}
RATIO_RTOL, RATIO_ATOL = 2e-6, 2e-7


def artifact(path):
    path = Path(path).resolve()
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return {
        "path": str(path),
        "bytes": path.stat().st_size,
        "sha256": digest.hexdigest(),
    }


def identities(columns, require_unsigned=False):
    words = [np.asarray(columns[name]) for name in KEYS]
    if any(word.ndim != 1 or word.dtype.kind not in "iu" for word in words):
        raise ValueError("Identity words must be scalar integers, never floats")
    if len({len(word) for word in words}) != 1:
        raise ValueError("Identity columns have inconsistent lengths")
    if words[2].dtype.itemsize != 8:
        raise ValueError("Event identity must retain all 64 bits")
    if require_unsigned and words[2].dtype.kind != "u":
        raise ValueError("Source NPZ event words must be uint64")
    # The historical/snapshot signed int64 bridge is inverted by its unsigned
    # two's-complement bit pattern. No conversion through float is permitted.
    events = words[2].astype(np.uint64, copy=False)
    if any(np.any(word < 0) or np.any(word >= 2**32) for word in words[:2]):
        raise ValueError("Run/lumisection outside uint32 domain")
    return [(int(r), int(l), int(e)) for r, l, e in zip(words[0], words[1], events)]


def entries(columns):
    values = np.asarray(columns["diagnostic_source_entry"])
    if values.ndim != 1 or values.dtype.kind not in "iu" or np.any(values < 0):
        raise ValueError("Source entries must be nonnegative scalar integers")
    return [int(value) for value in values]


def load(directory):
    directory = Path(directory).resolve()
    report_path = directory / "production.json"
    report = json.loads(report_path.read_text())
    source = next(
        row
        for row in json.loads((HERE / "inputs/inputs.json").read_text())["files"]
        if row["role"] == report["role"]
    )
    if report["source"] != source or report["manifest_sha256"] != MANIFEST_SHA:
        raise ValueError("Production source differs from the pinned manifest")
    output = directory / f'{report["role"]}-{report["kind"]}.root'
    if Path(report["output"]).resolve() != output:
        raise ValueError("Production output identity differs from its directory")
    with np.load(directory / "input-identity.npz", allow_pickle=False) as stored:
        raw = {name: stored[name] for name in stored.files}
    raw_keys, raw_entries = identities(raw, True), entries(raw)
    start, stop = report["range"]
    if raw_entries != list(range(start, stop)) or len(set(raw_keys)) != stop - start:
        raise ValueError(
            "Source identity ledger is incomplete, unordered, or duplicated"
        )
    if not source["is_data"] and (
        start != 0 or stop != source["verified_events_entries"]
    ):
        raise ValueError("MC audit requires the full pinned source identity ledger")
    if not source["is_data"] and (
        "genWeight" not in raw
        or raw["genWeight"].ndim != 1
        or len(raw["genWeight"]) != len(raw_entries)
    ):
        raise ValueError("MC source weight ledger has missing or inconsistent rows")
    gate = None
    gate_path = directory / "gate-ledger.npz"
    if gate_path.exists():
        with np.load(gate_path, allow_pickle=True) as stored:
            gate = {name: stored[name] for name in stored.files}
        gate_keys, gate_entries = identities(gate, True), entries(gate)
        if len(set(gate_entries)) != len(gate_entries) or len(set(gate_keys)) != len(
            gate_keys
        ):
            raise ValueError("Duplicate pregate identity")
        source_by_entry = dict(zip(raw_entries, raw_keys))
        if any(source_by_entry.get(e) != k for e, k in zip(gate_entries, gate_keys)):
            raise ValueError("Pregate keys do not round-trip to the full source ledger")
        for name in ("diag_original_gate", "diag_aligned_gate"):
            if not np.all(np.isin(gate[name], [False, True])):
                raise ValueError("Nonboolean pregate outcome")
    elif not source["is_data"]:
        raise ValueError("MC pregate ledger is missing")
    files = [report_path, output, directory / "input-identity.npz"]
    if gate is not None:
        files.append(gate_path)
    return {
        "metadata": report,
        "raw": raw,
        "raw_keys": raw_keys,
        "raw_entries": raw_entries,
        "gate": gate,
        "output": output,
        "artifacts": [artifact(path) for path in files],
    }


class Checks:
    def __init__(self):
        self.issues = {}
        self.failed_entries = set()
        self.source_entries = []
        self.keys = []

    def reject(self, name, mask):
        bad = np.flatnonzero(np.asarray(mask, dtype=bool))
        if not len(bad):
            return
        record = self.issues.setdefault(name, {"events": 0, "examples": []})
        record["events"] += int(len(bad))
        self.failed_entries.update(self.source_entries[i] for i in bad)
        for i in bad[: max(0, 8 - len(record["examples"]))]:
            record["examples"].append(
                {"source_entry": self.source_entries[i], "key": list(self.keys[i])}
            )

    def equal(self, name, actual, expected):
        same = np.asarray(ak.num(actual) == ak.num(expected))
        good = np.zeros(len(same), dtype=bool)
        if np.any(same):
            good[same] = np.asarray(ak.all(actual[same] == expected[same], axis=1))
        self.reject(name, ~good)


def object_ids(arrays, prefix, checks):
    for prop in ("electronIdx", "muonIdx", "pdgId"):
        dtype = ak.to_numpy(ak.flatten(arrays[prefix + "Lepton_" + prop])).dtype
        if dtype.kind not in "iu":
            raise ValueError(f"Lepton identity field is not integer: {prefix}{prop}")
    fields = [
        ak.to_list(arrays[prefix + "Lepton_" + p])
        for p in ("electronIdx", "muonIdx", "pdgId")
    ]
    lengths = np.asarray(ak.num(arrays[prefix + "Lepton_pt"]))
    result, bad = [], []
    for i, (es, ms, ps) in enumerate(zip(*fields)):
        row = list(zip(es, ms, ps))
        valid = len(es) == len(ms) == len(ps) == lengths[i]
        valid &= len({(e, m) for e, m, _ in row}) == len(row)
        valid &= all(
            (e >= 0 and m == -1 and abs(p) == 11)
            or (e == -1 and m >= 0 and abs(p) == 13)
            for e, m, p in row
        )
        result.append(row if valid else None)
        bad.append(not valid)
    checks.reject(prefix + "raw_identity_invalid", bad)
    return result


def positions(before, after, checks, label):
    result, bad = [], []
    for old, new in zip(before, after):
        lookup = {key: i for i, key in enumerate(old)} if old is not None else {}
        valid = new is not None and all(key in lookup for key in new)
        result.append([lookup[key] for key in new] if valid else [])
        bad.append(not valid)
    checks.reject(label, bad)
    return ak.Array(result), np.asarray(bad)


def audit_snapshot(production):
    meta, raw = production["metadata"], production["raw"]
    checks = Checks()
    final_by_entry, multiplicity, permutations = {}, Counter(), 0
    permutation_examples = []
    max_ratio_error = 0.0
    wp_names = meta["wp_columns"] + ["isLoose"]
    with uproot.open(production["output"]) as root_file:
        tree = root_file["Events"]
        names = set(tree.keys())
        required = set(KEYS) | {"diagnostic_source_entry", "Lepton_rochesterSF"}
        for prefix in ("", "diag_maker_", "diag_sel_", "diag_precorr_"):
            required.update(prefix + "Lepton_" + p for p in CORE)
        required.update(
            prefix + name
            for prefix in ("", "diag_pre_", "diag_sel_")
            for name in wp_names
        )
        required.update(
            flavor + "_" + prop
            for flavor in ("Electron", "Muon")
            for prop in ("pt", "eta", "phi", "pdgId")
        )
        sf_names = sorted(name for name in names if name.startswith("diag_sf_"))
        required.update(sf_names)
        required.update(name[len("diag_sf_") :] for name in sf_names)
        if required - names:
            raise ValueError(
                f"Snapshot association columns missing: {sorted(required - names)}"
            )
        if not meta["source"]["is_data"] and not sf_names:
            raise ValueError("MC snapshot lacks the frozen scale-factor columns")
        candidates = sorted(
            name for name in names if name.startswith("Lepton_") or name == "isLoose"
        )
        read_names = sorted(required | set(candidates) | ({"nLepton"} & names))
        flat_names, excluded = set(), set()
        source_by_entry = dict(zip(production["raw_entries"], production["raw_keys"]))
        for arrays in tree.iterate(read_names, step_size=5000, library="ak"):
            checks.source_entries = entries(arrays)
            checks.keys = identities(arrays)
            n = np.asarray(ak.num(arrays["Lepton_pt"]))
            multiplicity.update(map(int, n))
            for i, (entry, key) in enumerate(zip(checks.source_entries, checks.keys)):
                if entry in final_by_entry or source_by_entry.get(entry) != key:
                    raise ValueError(
                        "Snapshot identity duplicate or source round-trip failure"
                    )
                final_by_entry[entry] = {"key": key, "nLepton": int(n[i])}
            for name in candidates:
                if ak.to_layout(arrays[name]).minmax_depth == (2, 2):
                    flat_names.add(name)
                    checks.reject(
                        "length:" + name, np.asarray(ak.num(arrays[name])) != n
                    )
                else:
                    excluded.add(name)
            if "nLepton" in names:
                checks.reject("length:nLepton", np.asarray(arrays["nLepton"]) != n)
            stages = {}
            for prefix in ("diag_maker_", "diag_sel_", "diag_precorr_", ""):
                stages[prefix] = object_ids(arrays, prefix, checks)
                for prop in CORE:
                    checks.reject(
                        "length:" + prefix + "Lepton_" + prop,
                        np.asarray(ak.num(arrays[prefix + "Lepton_" + prop]))
                        != np.asarray(ak.num(arrays[prefix + "Lepton_pt"])),
                    )
                for prop in ("eta", "phi", "pdgId") + (() if prefix == "" else ("pt",)):
                    raw_vectors = {
                        flavor: ak.to_list(arrays[flavor + "_" + prop])
                        for flavor in ("Electron", "Muon")
                    }
                    expected = []
                    for i, row in enumerate(stages[prefix]):
                        values = []
                        if row is not None:
                            for e, m, _ in row:
                                flavor, index = (
                                    ("Electron", e) if e >= 0 else ("Muon", m)
                                )
                                vector = raw_vectors[flavor][i]
                                if index >= len(vector):
                                    values = []
                                    break
                                values.append(vector[index])
                        expected.append(values)
                    checks.equal(
                        prefix + "raw_mapping:" + prop,
                        arrays[prefix + "Lepton_" + prop],
                        ak.Array(expected),
                    )
            maker, sel, precorr, final = (
                stages[prefix]
                for prefix in ("diag_maker_", "diag_sel_", "diag_precorr_", "")
            )
            sel_pos, _ = positions(maker, sel, checks, "selection_absent_from_maker")
            final_pos, _ = positions(maker, final, checks, "final_absent_from_maker")
            corr_pos, invalid = positions(
                precorr, final, checks, "final_absent_from_precorr"
            )
            checks.reject(
                "precorr_identity_differs_from_selection",
                [a != b for a, b in zip(sel, precorr)],
            )
            checks.reject(
                "final_identity_set_differs_from_precorr",
                [
                    a is None or b is None or set(a) != set(b)
                    for a, b in zip(precorr, final)
                ],
            )
            for i, (bad, pos) in enumerate(zip(invalid, ak.to_list(corr_pos))):
                if not bad and pos != list(range(len(pos))):
                    permutations += 1
                    if len(permutation_examples) < 8:
                        permutation_examples.append(
                            {
                                "source_entry": checks.source_entries[i],
                                "key": list(checks.keys[i]),
                                "precorr_raw_identities": precorr[i],
                                "final_raw_identities": final[i],
                                "precorr_pt": ak.to_list(
                                    arrays["diag_precorr_Lepton_pt"][i]
                                ),
                                "final_pt": ak.to_list(arrays["Lepton_pt"][i]),
                                "rochesterSF": ak.to_list(
                                    arrays["Lepton_rochesterSF"][i]
                                ),
                            }
                        )
            for name in wp_names:
                pre = arrays["diag_pre_" + name]
                checks.reject(
                    "defining_stage_length:" + name,
                    np.asarray(ak.num(pre))
                    != np.asarray(ak.num(arrays["diag_maker_Lepton_pt"])),
                )
                # Index only sound reference rows; a missing original binding
                # is a persisted audit failure, never silently reinterpreted.
                pre_lengths = np.asarray(ak.num(pre))
                valid_sel = [
                    all(p < pre_lengths[i] for p in row)
                    for i, row in enumerate(ak.to_list(sel_pos))
                ]
                valid_final = [
                    all(p < pre_lengths[i] for p in row)
                    for i, row in enumerate(ak.to_list(final_pos))
                ]
                safe_sel = ak.Array(
                    [
                        row if valid else []
                        for row, valid in zip(ak.to_list(sel_pos), valid_sel)
                    ]
                )
                safe_final = ak.Array(
                    [
                        row if valid else []
                        for row, valid in zip(ak.to_list(final_pos), valid_final)
                    ]
                )
                checks.equal(
                    "selection_wp:" + name, arrays["diag_sel_" + name], pre[safe_sel]
                )
                checks.equal("final_wp:" + name, arrays[name], pre[safe_final])
            for name in sf_names:
                source = arrays[name]
                source_lengths = np.asarray(ak.num(source))
                checks.reject(
                    "sf_defining_stage_length:" + name,
                    source_lengths
                    != np.asarray(ak.num(arrays["diag_precorr_Lepton_pt"])),
                )
                safe = ak.Array(
                    [
                        row if all(p < source_lengths[i] for p in row) else []
                        for i, row in enumerate(ak.to_list(corr_pos))
                    ]
                )
                checks.equal(
                    "final_sf:" + name[len("diag_sf_") :],
                    arrays[name[len("diag_sf_") :]],
                    source[safe],
                )
            checks.reject(
                "final_pt_not_descending",
                np.asarray(
                    ak.any(
                        arrays["Lepton_pt"][:, 1:] > arrays["Lepton_pt"][:, :-1], axis=1
                    )
                ),
            )
            old_pt = arrays["diag_precorr_Lepton_pt"][corr_pos]
            same = np.asarray(ak.num(old_pt) == n)
            ratio = arrays["Lepton_rochesterSF"]
            same &= np.asarray(ak.num(ratio) == n)
            correct = np.zeros(len(n), dtype=bool)
            if np.any(same):
                expected = arrays["Lepton_pt"][same] / old_pt[same]
                observed = ratio[same]
                close = np.isclose(observed, expected, rtol=RATIO_RTOL, atol=RATIO_ATOL)
                correct[same] = np.asarray(
                    ak.all(
                        close & np.isfinite(expected) & np.isfinite(observed), axis=1
                    )
                )
                errors = ak.to_numpy(ak.flatten(abs(observed - expected)))
                if len(errors) and np.all(np.isfinite(errors)):
                    max_ratio_error = max(max_ratio_error, float(np.max(errors)))
            checks.reject("rochester_ratio_association", ~correct)
            if not meta["source"]["is_data"]:
                checks.reject("l2tight_fewer_than_two", n < 2)
        result = {
            "status": "failed" if checks.issues else "passed",
            "entries": tree.num_entries,
            "root_uuid": str(root_file.file.uuid),
            "branch_count": len(names),
            "flat_lepton_columns": sorted(flat_names),
            "excluded_nonflat_lepton_columns": sorted(excluded),
            "sf_columns": [name[len("diag_sf_") :] for name in sf_names],
            "multiplicity": dict(sorted(multiplicity.items())),
            "nonidentity_precorr_to_final_permutations": int(permutations),
            "nonidentity_permutation_examples": permutation_examples,
            "rochester_ratio_max_absolute_error": max_ratio_error,
            "unique_anomalous_events": len(checks.failed_entries),
            "anomaly_counts_may_overlap": True,
            "anomalies": checks.issues,
        }
    final_weights = (
        [float(raw["genWeight"][e]) for e in final_by_entry]
        if "genWeight" in raw
        else [1.0] * len(final_by_entry)
    )
    result["final_raw_weight_sums"] = sums(final_weights)
    production["snapshot_entries"] = final_by_entry
    return result


def sums(weights):
    values = [float(weight) for weight in weights]
    if not all(math.isfinite(value) for value in values):
        raise ValueError("Nonfinite raw event weight")
    return {
        "events": len(values),
        "sumw": math.fsum(values),
        "sumw2": math.fsum(value * value for value in values),
    }


def historical(production, join_dir):
    meta = production["metadata"]
    mapping, info = mapping_for_role(join_dir, meta["role"], meta["source"])
    join_path = Path(join_dir) / f'{meta["role"]}-join.json'
    join = json.loads(join_path.read_text())
    with uproot.open(meta["source"]["hww_part0_pfn"], timeout=60) as root_file:
        tree = root_file["Events"]
        if (
            str(root_file.file.uuid) != join["hww_part0"]["uuid"]
            or tree.num_entries != join["hww_part0"]["events_entries"]
        ):
            raise ValueError("Historical HWW UUID/count differs from pinned join")
        columns = list(KEYS) + ["nLepton", "Lepton_electronIdx", "Lepton_muonIdx"]
        arrays = tree.arrays(columns, library="ak")
        keys = identities(arrays)
        n = ak.to_numpy(arrays["nLepton"])
        if n.dtype.kind not in "iu":
            raise ValueError("Historical nLepton must be integer")
        if any(
            production["raw_keys"][entry] != keys[hww]
            for entry, hww in enumerate(mapping)
            if hww is not None
        ):
            raise ValueError("Historical keys fail the pinned source-entry join")
        if not np.all(
            ak.to_numpy(ak.num(arrays["Lepton_electronIdx"])) == n
        ) or not np.all(ak.to_numpy(ak.num(arrays["Lepton_muonIdx"])) == n):
            raise ValueError("Historical raw-index lengths differ from nLepton")
    return (
        mapping,
        n,
        {
            "mapping": artifact(info["path"]),
            "join_report": artifact(join_path),
            "read_columns": columns,
            "uuid": join["hww_part0"]["uuid"],
            "entries": len(keys),
            "historical_one_lepton_rows": int(np.count_nonzero(n == 1)),
        },
    )


def load_reference(directory, repaired):
    directory = Path(directory).resolve()
    role = repaired["metadata"]["role"]
    reports = [
        path
        for path in (
            directory / f"{role}-complete-gate.json",
            directory / "complete-gate.json",
        )
        if path.exists()
    ]
    if len(reports) != 1:
        raise ValueError(
            "Reference directory must have one canonical complete-gate report"
        )
    report = json.loads(reports[0].read_text())
    source = repaired["metadata"]["source"]
    if (
        report["role"] != role
        or report["source_pfn"] != source["pfn"]
        or report["source_uuid"] != source["verified_root_uuid"]
        or report["historical_hww_part0_pfn"] != source["hww_part0_pfn"]
        or report["all_wp_columns"] != repaired["metadata"]["wp_columns"]
        or report["input_entries"] != source["verified_events_entries"]
    ):
        raise ValueError(
            "Reference gate report differs from the pinned input or WP contract"
        )
    if report["producer_source_tree_sha1"] != {
        "mkShapesRDF/processor": "9c86299cdd2a8419fd30f48ad73a4fc530a567aa",
        "mkShapesRDF/include": "311e5fd6311c74b58ba233258acb2018aabcdd7d",
    }:
        raise ValueError(
            "Reference gate producer trees differ from the reviewed original"
        )
    if report["producer_revision"] != "69ff2dad8ac45c052e0f3364c35317c8ee7c6fa0":
        raise ValueError("Reference gate revision differs from the reviewed original")
    path = directory / "reference-gate-entries.npz"
    if artifact(path)["sha256"] != report["reference_entries_sha256"]:
        raise ValueError("Reference NPZ bytes differ from the complete-gate report")
    with np.load(path, allow_pickle=False) as stored:
        values = {name: stored[name] for name in stored.files}
    gate = {
        "diagnostic_source_entry": values["pregate_entries"],
        "genWeight": values["genWeight"],
    }
    if all(name in values for name in KEYS):
        gate.update({name: values[name] for name in KEYS})
    elif "keys" in values and values["keys"].ndim == 2 and values["keys"].shape[1] == 3:
        gate.update({name: values["keys"][:, i] for i, name in enumerate(KEYS)})
    else:
        raise ValueError(
            "Reference NPZ requires typed key columns or an integer keys[N,3] array"
        )
    reference_entries, reference_keys = entries(gate), identities(gate, True)
    if len(reference_entries) != len(reference_keys) or len(gate["genWeight"]) != len(
        reference_entries
    ):
        raise ValueError("Reference pregate columns have inconsistent lengths")
    if len(set(reference_entries)) != len(reference_entries) or len(
        set(reference_keys)
    ) != len(reference_keys):
        raise ValueError("Reference pregate identities are duplicated")
    if len(reference_entries) != report["stage_counts_before_gate"]["formulasMC"]:
        raise ValueError(
            "Reference pregate entry count differs from its complete-gate report"
        )
    for target, source_name, report_name in (
        ("diag_original_gate", "original_pass_entries", "original_gate_pass"),
        ("diag_aligned_gate", "aligned_pass_entries", "aligned_gate_pass"),
    ):
        accepted_values = values[source_name]
        if accepted_values.ndim != 1 or accepted_values.dtype.kind not in "iu":
            raise ValueError("Reference pass entries must be typed integers")
        accepted = {int(value) for value in accepted_values}
        if (
            len(accepted) != len(accepted_values)
            or not accepted.issubset(reference_entries)
            or len(accepted) != report[report_name]
        ):
            raise ValueError("Reference pass entry set fails complete-gate accounting")
        gate[target] = np.array(
            [entry in accepted for entry in reference_entries], dtype=bool
        )
    return {
        "gate": gate,
        "report": report,
        "artifacts": [artifact(reports[0]), artifact(path)],
    }


def compare_gates(original, repaired, join_dir, reference=None):
    a = reference["gate"] if reference else original["gate"]
    b = repaired["gate"]
    ae, be = entries(a), entries(b)
    ai, bi = {entry: i for i, entry in enumerate(ae)}, {
        entry: i for i, entry in enumerate(be)
    }
    if set(ai) != set(bi):
        raise ValueError("Original/repaired pregate source-entry sets differ")
    ak_keys, bk_keys = identities(a, True), identities(b, True)
    for entry in ae:
        i, j = ai[entry], bi[entry]
        for name in ("diag_original_gate", "diag_aligned_gate", "genWeight"):
            if a[name][i] != b[name][j]:
                raise ValueError(
                    f"Original/repaired pregate values differ: {name}, entry {entry}"
                )
        if ak_keys[i] != bk_keys[j]:
            raise ValueError("Original/repaired pregate event-key sets differ")
        for name in (
            "Lepton_pt",
            "Lepton_electronIdx",
            "Lepton_muonIdx",
            "VetoLepton_electronIdx",
            "VetoLepton_muonIdx",
        ):
            if name in a and not np.array_equal(a[name][i], b[name][j]):
                raise ValueError(
                    f"Original/repaired pregate collection differs: {name}, entry {entry}"
                )
    mapping, hist_n, provenance = historical(repaired, join_dir)
    cells, outcomes = defaultdict(list), defaultdict(list)
    labels, pre_n = {}, {}
    for entry in ae:
        i = ai[entry]
        old, aligned = bool(a["diag_original_gate"][i]), bool(a["diag_aligned_gate"][i])
        label = OUTCOMES[0 if old and aligned else 1 if aligned else 2 if old else 3]
        labels[entry] = label
        pre_n[entry] = len(b["Lepton_pt"][bi[entry]])
        h = mapping[entry]
        cell = (label, pre_n[entry], "absent" if h is None else int(hist_n[h]))
        weight = float(a["genWeight"][i])
        cells[cell].append(weight)
        outcomes[label].append(weight)
    counts = [len(outcomes[label]) for label in OUTCOMES]
    if counts != EXPECTED[repaired["metadata"]["role"]]:
        raise ValueError(
            f"Full pregate outcome counts differ from pinned observation: {counts}"
        )
    expected_old = {e for e in ae if a["diag_original_gate"][ai[e]]}
    expected_new = {e for e in ae if a["diag_aligned_gate"][ai[e]]}
    if repaired["metadata"]["stages"]["l2tight"] != len(expected_new) or (
        original and original["metadata"]["stages"]["l2tight"] != len(expected_old)
    ):
        raise ValueError(
            "Actual producer L2 stage counts differ from saved gate decisions"
        )
    if expected_old != {e for e, h in enumerate(mapping) if h is not None}:
        raise ValueError("Original gate membership differs from pinned historical HWW")
    if set(repaired["snapshot_entries"]) != expected_new:
        raise ValueError(
            "Repaired final entry set differs from the independent aligned gate"
        )
    if original and not set(original["snapshot_entries"]).issubset(expected_old):
        raise ValueError(
            "Original final snapshot contains an event rejected by its gate"
        )
    return {
        "status": "passed",
        "pregate_entry_and_key_sets_exactly_equal": True,
        "pregate_outcomes_exactly_equal": True,
        "pregate_collection_comparison": (
            "passed" if "Lepton_pt" in a else "not assessed"
        ),
        "repaired_final_aligned_gate_entry_and_key_sets_exactly_equal": True,
        "reference_gate_artifacts": reference["artifacts"] if reference else None,
        "outcome_order": list(OUTCOMES),
        "observed_counts": counts,
        "expected_counts": EXPECTED[repaired["metadata"]["role"]],
        "outcomes": {label: sums(outcomes[label]) for label in OUTCOMES},
        "cross_tab_by_current_and_historical_nLepton": [
            {
                "outcome": label,
                "current_pre_gate_nLepton": n,
                "historical_nLepton": h,
                **sums(weights),
            }
            for (label, n, h), weights in sorted(
                cells.items(), key=lambda item: str(item[0])
            )
        ],
        "original_gate_pass": len(expected_old),
        "aligned_gate_pass": len(expected_new),
        "original_final_after_gate_losses": (
            len(expected_old - set(original["snapshot_entries"])) if original else None
        ),
        "repaired_final_after_gate_losses": len(
            expected_new - set(repaired["snapshot_entries"])
        ),
        "historical": provenance,
        "labels": labels,
        "pre_n": pre_n,
        "historical_mapping": mapping,
        "historical_n": hist_n.tolist(),
    }


def run(args):
    if args.output_dir.exists():
        raise FileExistsError("Audit output directory must be fresh")
    if artifact(HERE / "inputs/inputs.json")["sha256"] != MANIFEST_SHA:
        raise ValueError("Pinned manifest bytes changed")
    repaired = load(args.repaired_dir)
    if repaired["metadata"]["kind"] != "repaired":
        raise ValueError("--repaired-dir does not identify a repaired production")
    original = load(args.original_dir) if args.original_dir else None
    reference = (
        load_reference(args.reference_gate_dir, repaired)
        if args.reference_gate_dir
        else None
    )
    if original:
        if original["metadata"]["kind"] != "original":
            raise ValueError("--original-dir does not identify original production")
        for name in ("role", "source", "range", "wp_columns"):
            if original["metadata"][name] != repaired["metadata"][name]:
                raise ValueError(f"Original/repaired metadata mismatch: {name}")
        if (
            original["raw_keys"] != repaired["raw_keys"]
            or original["raw_entries"] != repaired["raw_entries"]
        ):
            raise ValueError("Original/repaired full input ledgers differ")
        if not np.array_equal(
            original["raw"]["genWeight"], repaired["raw"]["genWeight"]
        ):
            raise ValueError("Original/repaired full input genWeight arrays differ")
    if not repaired["metadata"]["source"]["is_data"] and (
        not (original or reference) or not args.join_dir
    ):
        raise ValueError(
            "MC audit requires independent original gate evidence and the pinned historical join"
        )
    result = {
        "schema_version": 1,
        "kind": "hww_repair_durable_snapshot_audit",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "role": repaired["metadata"]["role"],
        "scope": "Final nominal snapshot association; MC pregate counterfactual and historical membership. No full-year or final-analysis yields.",
        "ratio_tolerance": {"rtol": RATIO_RTOL, "atol": RATIO_ATOL},
        "integer_identity": "Source uint64 preserved; signed int64 snapshot/historical event words inverted modulo 2^64 without floats.",
        "auditor": artifact(__file__),
        "manifest": artifact(HERE / "inputs/inputs.json"),
        "known_witness_input": artifact(HERE / "observed-summary.json"),
        "productions": {},
    }
    for production in ([original] if original else []) + [repaired]:
        kind = production["metadata"]["kind"]
        result["productions"][kind] = {
            "metadata": production["metadata"],
            "artifacts": production["artifacts"],
            "snapshot": audit_snapshot(production),
            "input_raw_weight_sums": sums(
                production["raw"].get("genWeight", np.ones(len(production["raw_keys"])))
            ),
        }
    gate = (
        compare_gates(original, repaired, args.join_dir, reference)
        if (original or reference)
        else None
    )
    witnesses = [
        row
        for row in json.loads((HERE / "observed-summary.json").read_text())["witnesses"]
        if row["role"] == result["role"]
    ]
    result["known_witnesses"] = []
    for witness in witnesses:
        entry = witness["source_entry"]
        row = {
            "source_entry": entry,
            "known_key": witness["key"],
            "source_ledger_key": (
                list(repaired["raw_keys"][entry])
                if entry < len(repaired["raw_keys"])
                else None
            ),
        }
        if (
            row["source_ledger_key"] is not None
            and row["source_ledger_key"] != row["known_key"]
        ):
            raise ValueError("Known witness identity changed")
        for production in ([original] if original else []) + [repaired]:
            record = production["snapshot_entries"].get(entry)
            row[production["metadata"]["kind"]] = {
                "present": record is not None,
                "nLepton": record["nLepton"] if record else None,
            }
        if gate:
            row["gate_outcome"] = gate["labels"].get(entry, "absent_before_gate")
            row["current_pre_gate_nLepton"] = gate["pre_n"].get(entry)
            h = gate["historical_mapping"][entry]
            row["historical_entry"] = h
            row["historical_nLepton"] = (
                gate["historical_n"][h] if h is not None else None
            )
        result["known_witnesses"].append(row)
    if gate:
        for name in ("labels", "pre_n", "historical_mapping", "historical_n"):
            gate.pop(name)
        result["gate_comparison"] = gate
    result["status"] = result["productions"]["repaired"]["snapshot"]["status"]
    args.output_dir.mkdir(parents=True)
    destination = args.output_dir / "audit.json"
    destination.write_text(
        json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n"
    )
    print(
        json.dumps(
            {
                "status": result["status"],
                "audit": str(destination.resolve()),
                "audit_sha256": artifact(destination)["sha256"],
            }
        )
    )
    return 0 if result["status"] == "passed" else 1


def run_witnesses(args):
    """Extract exact local rows after a successful aggregate snapshot audit."""
    if args.output_dir.exists():
        raise FileExistsError("Witness output directory must be fresh")
    audited = json.loads(args.audit_json.read_text())
    production = load(args.repaired_dir)
    meta = production["metadata"]
    recorded = audited["productions"]["repaired"]
    if (
        audited["status"] != "passed"
        or audited["role"] != meta["role"]
        or recorded["metadata"] != meta
        or recorded["artifacts"] != production["artifacts"]
    ):
        raise ValueError("Witness inputs differ from the successful aggregate audit")
    reference = (
        load_reference(args.reference_gate_dir, production)
        if args.reference_gate_dir
        else None
    )
    wanted = {}
    for row in json.loads((HERE / "observed-summary.json").read_text())["witnesses"]:
        if row["role"] == meta["role"]:
            wanted[row["source_entry"]] = {
                "key": row["key"],
                "origins": ["pinned_observed_summary"],
            }
    if reference:
        for row in reference["report"]["witnesses"]:
            entry = row["source_entry"]
            target = wanted.setdefault(entry, {"key": row["key"], "origins": []})
            if target["key"] != row["key"]:
                raise ValueError("Original witness key differs from the pinned witness")
            target["origins"].append("independent_original_gate_reference")
            target["original_gate_reference"] = row
    for row in recorded["snapshot"]["nonidentity_permutation_examples"][:1]:
        target = wanted.setdefault(
            row["source_entry"], {"key": row["key"], "origins": []}
        )
        target["origins"].append("audited_nonidentity_permutation")
    # Include the separately requested diagnostic entry without assigning it
    # the outcome of the pinned source-127 witness.
    if meta["role"] == "dy_mumu":
        wanted.setdefault(
            137,
            {
                "key": list(production["raw_keys"][137]),
                "origins": ["requested_diagnostic_entry"],
            },
        )
    gate = production["gate"]
    gate_rows = {e: i for i, e in enumerate(entries(gate))} if gate else {}
    rows = []
    with uproot.open(production["output"]) as root_file:
        tree = root_file["Events"]
        if (
            str(root_file.file.uuid) != recorded["snapshot"]["root_uuid"]
            or tree.num_entries != recorded["snapshot"]["entries"]
        ):
            raise ValueError("Witness snapshot UUID/count changed")
        source_entries = entries(tree.arrays(["diagnostic_source_entry"], library="np"))
        lookup = {entry: i for i, entry in enumerate(source_entries)}
        if len(lookup) != len(source_entries):
            raise ValueError("Witness snapshot contains duplicate source entries")
        sf_names = [
            name
            for name in (
                "Lepton_RecoSF",
                "Lepton_tightElectron_testrecipes_IdIsoSF",
                "Lepton_tightMuon_cut_Tight_HWW_IdIsoSF",
            )
            if name in recorded["snapshot"]["sf_columns"]
        ]
        wp_names = meta["wp_columns"] + ["isLoose"]
        columns = set(KEYS) | {"diagnostic_source_entry", "Lepton_rochesterSF"}
        columns.update(
            flavor + "_" + prop
            for flavor in ("Electron", "Muon")
            for prop in ("pt", "eta", "phi", "pdgId")
        )
        for prefix in ("", "diag_maker_", "diag_sel_", "diag_precorr_"):
            columns.update(prefix + "Lepton_" + prop for prop in CORE)
        columns.update(
            prefix + name
            for prefix in ("", "diag_pre_", "diag_sel_")
            for name in wp_names
        )
        columns.update(
            prefix + name for prefix in ("", "diag_sf_") for name in sf_names
        )
        for entry, provenance in sorted(wanted.items()):
            key = production["raw_keys"][entry]
            if list(key) != provenance["key"]:
                raise ValueError("Witness key fails the full uint64 source ledger")
            row = {
                "source_entry": entry,
                **provenance,
                "present_after_repaired_chain": entry in lookup,
                "snapshot_entry": lookup.get(entry),
                "raw_genWeight": (
                    float(production["raw"]["genWeight"][entry])
                    if "genWeight" in production["raw"]
                    else 1.0
                ),
            }
            if gate and entry in gate_rows:
                i = gate_rows[entry]
                row["saved_repaired_pregate"] = {
                    "original_pass": bool(gate["diag_original_gate"][i]),
                    "aligned_pass": bool(gate["diag_aligned_gate"][i]),
                    **{
                        name: np.asarray(gate[name][i]).tolist()
                        for name in (
                            "Lepton_pt",
                            "Lepton_electronIdx",
                            "Lepton_muonIdx",
                            "VetoLepton_electronIdx",
                            "VetoLepton_muonIdx",
                        )
                    },
                }
                if (entry in lookup) != bool(gate["diag_aligned_gate"][i]):
                    raise ValueError(
                        "Witness final presence differs from its aligned gate"
                    )
            if entry in lookup:
                arrays = tree.arrays(
                    sorted(columns),
                    entry_start=lookup[entry],
                    entry_stop=lookup[entry] + 1,
                    library="ak",
                )
                if identities(arrays) != [key] or entries(arrays) != [entry]:
                    raise ValueError(
                        "Exact local witness lookup failed identity round-trip"
                    )

                def values(prefix, names, row_arrays=arrays):
                    return {
                        name: ak.to_list(row_arrays[prefix + name][0]) for name in names
                    }

                core_names = ["Lepton_" + prop for prop in CORE]
                row["snapshot_stages"] = {
                    "raw_nanoaod_fields": values(
                        "",
                        [
                            flavor + "_" + prop
                            for flavor in ("Electron", "Muon")
                            for prop in ("pt", "eta", "phi", "pdgId")
                        ],
                    ),
                    "maker": values("diag_maker_", core_names),
                    "original_defining_stage_wp": values("diag_pre_", wp_names),
                    "post_selection": values("diag_sel_", core_names + wp_names),
                    "precorrection": values("diag_precorr_", core_names),
                    "precorrection_sf_examples": values("diag_sf_", sf_names),
                    "final": values(
                        "", core_names + wp_names + ["Lepton_rochesterSF"] + sf_names
                    ),
                }
                if "original_gate_reference" in provenance:
                    for name, expectation in provenance["original_gate_reference"][
                        "wp_vectors"
                    ].items():
                        if (
                            row["snapshot_stages"]["original_defining_stage_wp"][name]
                            != expectation["actual_prefilter"]
                        ):
                            raise ValueError(
                                "Original defining-stage witness flags changed"
                            )
            else:
                row["snapshot_stages"] = None
                row["absent_snapshot_stage_reason"] = (
                    "No repaired final row exists; original reference indices and flags "
                    "and saved repaired pregate arrays are retained without inventing "
                    "unavailable original corrected kinematics."
                )
            rows.append(row)
    result = {
        "schema_version": 1,
        "kind": "hww_repair_exact_local_witness_rows",
        "role": meta["role"],
        "status": "passed",
        "auditor": artifact(__file__),
        "aggregate_audit": artifact(args.audit_json),
        "production_artifacts": production["artifacts"],
        "reference_artifacts": reference["artifacts"] if reference else [],
        "scope": (
            "Local snapshot source-entry lookup and exact selected row reads only. "
            "No producer execution, source NanoAOD scan, or original final snapshot. "
            "All SF associations are covered by the aggregate audit; three named "
            "nominal SF vectors are included here for compact examples."
        ),
        "witnesses": rows,
    }
    args.output_dir.mkdir(parents=True)
    destination = args.output_dir / "witnesses.json"
    destination.write_text(
        json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n"
    )
    print(
        json.dumps(
            {
                "status": "passed",
                "witnesses": str(destination.resolve()),
                "sha256": artifact(destination)["sha256"],
            }
        )
    )
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repaired-dir", type=Path, required=True)
    parser.add_argument("--original-dir", type=Path)
    parser.add_argument("--reference-gate-dir", type=Path)
    parser.add_argument("--join-dir", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--witness-only", action="store_true")
    parser.add_argument("--audit-json", type=Path)
    args = parser.parse_args()
    if args.witness_only and args.audit_json is None:
        parser.error("--witness-only requires --audit-json")
    raise SystemExit(run_witnesses(args) if args.witness_only else run(args))
