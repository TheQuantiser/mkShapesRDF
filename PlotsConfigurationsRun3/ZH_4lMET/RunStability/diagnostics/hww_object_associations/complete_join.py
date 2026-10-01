"""Exhaustively join two pinned DY central NanoAOD files to HWW part0.

Read only the complete event identities and MC Runs lineage.  This does not
run or emulate the HWW producer.  The mapping contains one row per central
entry; only a unique key on both sides receives an HWW entry.
"""

import argparse
import csv
import gzip
import hashlib
import io
import json
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import uproot


MANIFEST_SHA256 = "c47bc8fde91a4c06aeead3c488115585df85194331d5886024f6f74333d8ee98"
PAIR_SHA256 = "a49c3c2bddda0a0d006114933cdca43125cfaf24d05996944ea66997dcad7f6b"
HWW_UUID = {
    "dy_ee": "c183f92c-3747-11f1-be55-3cecef0de5e4",
    "dy_mumu": "d4c93ad6-37e9-11f1-98cc-3cecef0ddda8",
}
ROLES = ("dy_ee", "dy_mumu")
IDENTITY = ("run", "luminosityBlock", "event")
UINT64_MASK = (1 << 64) - 1


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def pinned_json(path, expected):
    actual = sha256(path)
    if actual != expected:
        raise ValueError(f"Pinned SHA-256 mismatch for {path}: {actual}")
    return json.loads(Path(path).read_bytes())


def one(items, role):
    found = [item for item in items if item["role"] == role]
    if len(found) != 1:
        raise ValueError(f"Expected one record for {role}; found {len(found)}")
    return found[0]


def check_pair(source, pair):
    required_equal = {
        "pfn": "central_pfn",
        "hww_part0_pfn": "hww_pfn",
        "source_id": "source_id",
        "lfn": "central_lfn",
        "verified_events_entries": "central_events_entries",
        "file_inventory_hash": "source_file_inventory_hash",
        "sample": "sample",
        "dataset": "source_dataset",
    }
    for left, right in required_equal.items():
        if source[left] != pair[right]:
            raise ValueError(f"Manifest/pair mismatch: {left} vs {right}")
    if (
        source["role"] != pair["role"]
        or source["frozen_file_entries"] != source["verified_events_entries"]
        or pair["hww_part_index"] != 0
        or source["is_data"]
    ):
        raise ValueError(f"Invalid pinned DY pair: {source['role']}")


def read_file(pfn, expected_uuid, expected_entries, hww):
    """Return all typed event keys and the complete scalar Runs sums."""
    with uproot.open(pfn, timeout=30) as root_file:
        uuid = str(root_file.file.uuid)
        if uuid != expected_uuid:
            raise ValueError(f"ROOT UUID mismatch for {pfn}: {uuid}")
        tree = root_file["Events"]
        if tree.num_entries != expected_entries:
            raise ValueError(f"Events entry-count mismatch for {pfn}: {tree.num_entries}")
        if not set(IDENTITY).issubset(tree.keys()):
            raise ValueError(f"Missing Events identity branch in {pfn}")
        columns = tree.arrays(list(IDENTITY), library="np")
        expected_event_dtype = "<i8" if hww else "<u8"
        if columns["event"].dtype.str != expected_event_dtype:
            raise ValueError(f"Unexpected event dtype in {pfn}: {columns['event'].dtype}")
        if any(len(columns[name]) != expected_entries for name in IDENTITY):
            raise ValueError(f"Incomplete Events identity read from {pfn}")
        keys = []
        for run, lumi, event in zip(*(columns[name] for name in IDENTITY)):
            run, lumi, event = int(run), int(lumi), int(event)
            if not (0 <= run < 1 << 32 and 0 <= lumi < 1 << 32):
                raise ValueError(f"Invalid run/luminosityBlock in {pfn}: {(run, lumi)}")
            event = event & UINT64_MASK if hww else event
            if not 0 <= event <= UINT64_MASK:
                raise ValueError(f"Invalid event in {pfn}: {event}")
            keys.append((run, lumi, event))
        runs = root_file["Runs"]
        if not {"genEventCount", "genEventSumw"}.issubset(runs.keys()):
            raise ValueError(f"Missing MC Runs lineage in {pfn}")
        counts = runs["genEventCount"].array(library="np")
        sumws = runs["genEventSumw"].array(library="np")
        if len(counts) != runs.num_entries or len(sumws) != runs.num_entries:
            raise ValueError(f"Incomplete Runs read from {pfn}")
        lineage = {
            "runs_entries": runs.num_entries,
            "genEventCount": int(sum(counts)),
            "genEventSumw": float(sum(sumws)),
        }
        return keys, {"uuid": uuid, "events_entries": tree.num_entries,
                      "event_dtype": str(columns["event"].dtype), "runs": lineage}


def join(source_keys, hww_keys, mapping_path):
    source_by_key = defaultdict(list)
    hww_by_key = defaultdict(list)
    for entry, key in enumerate(source_keys):
        source_by_key[key].append(entry)
    for entry, key in enumerate(hww_keys):
        hww_by_key[key].append(entry)

    duplicates = []
    for key in source_by_key.keys() | hww_by_key.keys():
        src, dst = source_by_key.get(key, ()), hww_by_key.get(key, ())
        if len(src) > 1 or len(dst) > 1:
            duplicates.append({"key": list(key), "source_entries": list(src),
                               "hww_entries": list(dst)})
    duplicates.sort(key=lambda item: item["key"])

    counts = {"matched": 0, "input_only": 0, "output_only": 0,
              "ambiguous_source_rows": 0, "ambiguous_hww_rows": 0,
              "ambiguous_keys": len(duplicates)}
    with gzip.GzipFile(filename=str(mapping_path), mode="wb", mtime=0) as zipped:
        with io.TextIOWrapper(zipped, encoding="ascii", newline="") as stream:
            writer = csv.writer(stream, delimiter="\t", lineterminator="\n")
            writer.writerow(("source_entry", "hww_entry", "status"))
            for source_entry, key in enumerate(source_keys):
                n_source = len(source_by_key[key])
                hww_entries = hww_by_key.get(key, ())
                if n_source > 1 or len(hww_entries) > 1:
                    status, hww_entry = "ambiguous", ""
                    counts["ambiguous_source_rows"] += 1
                elif not hww_entries:
                    status, hww_entry = "input_only", ""
                    counts["input_only"] += 1
                else:
                    status, hww_entry = "matched", hww_entries[0]
                    counts["matched"] += 1
                writer.writerow((source_entry, hww_entry, status))
    for key, entries in hww_by_key.items():
        if len(entries) > 1 or len(source_by_key.get(key, ())) > 1:
            counts["ambiguous_hww_rows"] += len(entries)
        elif key not in source_by_key:
            counts["output_only"] += 1
    if (counts["matched"] + counts["input_only"] + counts["ambiguous_source_rows"] != len(source_keys)
            or counts["matched"] + counts["output_only"] + counts["ambiguous_hww_rows"] != len(hww_keys)):
        raise AssertionError("Join accounting did not close")
    return counts, duplicates


def run(manifest_path, pair_path, output_dir):
    started = time.monotonic()
    manifest = pinned_json(manifest_path, MANIFEST_SHA256)
    evidence = pinned_json(pair_path, PAIR_SHA256)
    if evidence["kind"] != "paired_2024_lowpt_parent_pair_evidence":
        raise ValueError("Unexpected parent-pair evidence kind")
    upstream = {}
    for path_field, hash_field in (("frozen_fileset_path", "frozen_fileset_sha256"),
                                   ("hww_exact_compiled_pickle_path", "hww_exact_compiled_pickle_sha256")):
        path = Path(evidence[path_field])
        actual = sha256(path) if path.is_file() else None
        if actual is not None and actual != evidence[hash_field]:
            raise ValueError(f"Upstream SHA-256 mismatch for {path}")
        upstream[path_field] = {"path": str(path), "sha256_verified": actual == evidence[hash_field]
                                if actual is not None else None}
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=False)
    results = {}
    for role in ROLES:
        role_started = time.monotonic()
        source = one(manifest["files"], role)
        pair = one(evidence["pairs"], role)
        check_pair(source, pair)
        source_keys, source_file = read_file(source["pfn"], source["verified_root_uuid"],
                                             source["verified_events_entries"], False)
        hww_keys, hww_file = read_file(pair["hww_pfn"], HWW_UUID[role],
                                       pair["hww_events_entries"], True)
        expected_runs = pair["mc_runs_match"]
        for key in ("genEventCount", "genEventSumw"):
            if (source_file["runs"][key] != hww_file["runs"][key]
                    or source_file["runs"][key] != expected_runs[f"{key}_central"]
                    or hww_file["runs"][key] != expected_runs[f"{key}_hww"]):
                raise ValueError(f"MC Runs lineage mismatch for {role}: {key}")
        mapping_path = output_dir / f"{role}-source-entry-map.tsv.gz"
        counts, duplicates = join(source_keys, hww_keys, mapping_path)
        result = {
            "role": role, "source_pfn": source["pfn"], "hww_part0_pfn": pair["hww_pfn"],
            "source_id": source["source_id"], "source_file_inventory_hash": source["file_inventory_hash"],
            "source_lfn": source["lfn"], "source": source_file, "hww_part0": hww_file,
            "counts": counts, "duplicate_keys": duplicates,
            "mapping": {"path": str(mapping_path.resolve()), "sha256": sha256(mapping_path),
                        "format": "gzip TSV, one row per central entry in ascending order; columns source_entry, hww_entry, status; blank hww_entry for input_only or ambiguous"},
            "runtime_seconds": round(time.monotonic() - role_started, 3),
            "historical_producer_source": "unavailable dirty worktree",
        }
        result_path = output_dir / f"{role}-join.json"
        result_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
        results[role] = {"counts": counts, "result": str(result_path.resolve()),
                         "result_sha256": sha256(result_path), "mapping": str(mapping_path.resolve())}
        print(json.dumps({"role": role, **results[role]}, sort_keys=True), flush=True)
    receipt = {
        "kind": "pinned_dy_part0_complete_identity_join", "created_utc": datetime.now(timezone.utc).isoformat(),
        "manifest": {"path": str(Path(manifest_path).resolve()), "sha256": MANIFEST_SHA256},
        "parent_pair_evidence": {"path": str(Path(pair_path).resolve()), "sha256": PAIR_SHA256},
        "upstream": upstream, "roles": results,
        "runtime_seconds": round(time.monotonic() - started, 3),
        "scope": "Two exact central files and their paired historical HWW part0 only; no producer replay or other samples",
    }
    (output_dir / "join-receipt.json").write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    if any(results[role]["counts"]["ambiguous_keys"] for role in ROLES):
        raise ValueError("Ambiguous event keys found; see per-role join reports; no ambiguous mapping assigned")
    return receipt


if __name__ == "__main__":
    here = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=here / "inputs" / "inputs.json")
    parser.add_argument("--pair-evidence", type=Path, default=here / "inputs" / "parent-pair-evidence.json")
    parser.add_argument("--output-dir", type=Path, required=True, help="Fresh local output directory")
    args = parser.parse_args()
    run(args.manifest, args.pair_evidence, args.output_dir)
