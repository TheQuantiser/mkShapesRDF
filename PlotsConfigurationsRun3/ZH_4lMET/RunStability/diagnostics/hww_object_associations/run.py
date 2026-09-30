"""One bounded current-producer and historical-HWW object-association demo."""

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

from historical import inspect


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[4]
WITNESSES = (
    ("muon_c", 234, (379416, 147, 131724611), 65),
    ("egamma_c", 20774, (379729, 907, 1396820419), 991),
    ("egamma_i", 27025, (386509, 159, 333332716), 1936),
    ("egamma_i", 46209, (386509, 735, 1539152813), 3325),
    ("dy_ee", 174, (1, 384532, 2060318616), None),
    ("dy_mumu", 127, (1, 260002, 1443526502), None),
)
HISTORICAL_INVARIANTS = {
    ("muon_c", 234): (False, True, True),
    ("egamma_c", 20774): (False, True, True),
    ("egamma_i", 27025): (True, False, True),
    ("egamma_i", 46209): (False, False, True),
}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def git(*args):
    return subprocess.check_output(["git", *args], cwd=REPO, text=True).strip()


def check_witness(role, entry, historical, live):
    """Fail if a pinned event no longer exhibits its documented mechanism."""
    if (role, entry) in HISTORICAL_INVARIANTS:
        expected = HISTORICAL_INVARIANTS[(role, entry)]
        actual = tuple(historical["invariant"][name] for name in ("tight", "eta", "phi"))
        if not historical["hww_present"] or actual != expected:
            raise AssertionError(f"Historical association pattern changed: {(role, entry)} {actual}")
    elif historical["hww_present"] or live.get("isolated_l2tight_pass") is not False:
        raise AssertionError(f"MC absence/gate pattern changed: {(role, entry)}")
    positions = live["retained_position_checks"]
    mismatched_tight = any(pos["expected_tight"] != pos["stored_position_tight"] for pos in positions)
    if (role, entry) in (("muon_c", 234), ("egamma_c", 20774), ("egamma_i", 46209), ("dy_ee", 174)) and not mismatched_tight:
        raise AssertionError(f"Current prefilter tight-vector mechanism not reproduced: {(role, entry)}")
    if (role, entry) == ("dy_mumu", 127) and (len(positions) != 1 or positions[0]["expected_tight"]):
        raise AssertionError("Legitimate one-retained-muon l2tight control changed")
    if (role, entry) == ("egamma_i", 27025):
        if live["correction_original_permutation"]["Lepton_sorting"] != [1, 0]:
            raise AssertionError("Corrected-pT order did not flip on the pinned witness")
        if all(p["eta_associated"] and p["phi_associated"] for p in live["corrected_position_checks"]):
            raise AssertionError("Current correction association hazard was not observed")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--manifest", type=Path, required=True)
    ap.add_argument("--pair-evidence", type=Path, required=True)
    ap.add_argument("--output-dir", type=Path, required=True)
    args = ap.parse_args()
    manifest = json.loads(args.manifest.read_text())
    if manifest.get("kind") != "paired_2024_lowpt_nanoaod_inputs":
        raise ValueError("Unexpected input manifest kind")
    if git("rev-parse", "HEAD:mkShapesRDF") != git("rev-parse", manifest["mkshapes_head"] + ":mkShapesRDF"):
        raise ValueError("Current producer package differs from pinned historical clean tree")
    if args.output_dir.exists():
        raise FileExistsError("Use a fresh output directory")
    args.output_dir.mkdir(parents=True)
    files = {f["role"]: f for f in manifest["files"]}
    if len(files) != len(manifest["files"]):
        raise ValueError("Duplicate role in input manifest")
    rows = []
    for role, entry, key, hww_entry in WITNESSES:
        f = files[role]
        historical = inspect(args.manifest, args.pair_evidence, role, entry, key, hww_entry)
        cmd = [sys.executable, str(HERE / "live.py"), "--pfn", f["pfn"], "--entry", str(entry), "--key", *map(str, key)]
        if not f["is_data"]:
            cmd.append("--mc")
        if role == "egamma_i" and entry == 27025:
            cmd.append("--correct")
        completed = subprocess.run(cmd, text=True, capture_output=True, check=True)
        # ROOT warnings go to stderr; preserve them for provenance.
        live = json.loads(completed.stdout.strip().splitlines()[-1])
        if Path(live["producer_package"]).resolve().parents[0] != REPO / "mkShapesRDF":
            raise RuntimeError("Imported producer package is not from this demo worktree")
        check_witness(role, entry, historical, live)
        rows.append({"role": role, "source_entry": entry, "key": key,
                     "source_pfn": f["pfn"], "historical_hww_pfn": f["hww_part0_pfn"],
                     "historical": historical, "live_current_code": live,
                     "live_stdout_before_json": completed.stdout.strip().splitlines()[:-1],
                     "live_stderr": completed.stderr.strip()})
        print(f"{role} {entry}: HWW {'present' if historical['hww_present'] else 'absent'}, "
              f"live retained {len(live['lepton_sel']['Lepton_pt'])}, "
              f"isolated l2tight {live.get('isolated_l2tight_pass', 'DATA')}", flush=True)
    result = {"kind": "bounded_2024_hww_object_association_demo", "schema_version": 1,
              "producer_revision": git("rev-parse", "HEAD"),
              "producer_package_tree": git("rev-parse", "HEAD:mkShapesRDF"),
              "python_hash_seed": os.environ.get("PYTHONHASHSEED", "random"),
              "pinned_manifest_sha256": sha(args.manifest),
              "parent_pair_evidence_sha256": sha(args.pair_evidence),
              "witnesses": rows,
              "scope": "Few exact events, actual historical HWW part0, current isolated lepton modules; not full-year prevalence or full DATA producer success."}
    (args.output_dir / "events.json").write_text(json.dumps(result, indent=2) + "\n")
    print(args.output_dir / "events.json")


if __name__ == "__main__":
    main()
