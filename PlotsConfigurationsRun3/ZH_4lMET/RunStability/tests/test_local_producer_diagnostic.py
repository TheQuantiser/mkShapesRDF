"""Bounded input and identity checks for the local producer diagnostic."""

import hashlib
import json
import runpy
import subprocess

import pytest

from local_producer_diagnostic import (
    PRODUCER,
    REPO,
    _book_entries,
    _book_keys,
    _result_keys,
    build_ledger,
    load_manifest,
    load_mc_sumw,
    step_names,
)
from mkShapesRDF.processor.framework.Productions_cfg import Productions


DATASET = "/MuonEG/Run2024C-MINIv6NANOv15-v1/NANOAOD"
DATA_LFN = "/store/data/Run2024C/MuonEG/NANOAOD/mini/source.root"
MC_DATASET = (
    "/DYto2E-2Jets_Bin-MLL-50_TuneCP5_13p6TeV_amcatnloFXFX-pythia8/"
    "RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v4/NANOAODSIM"
)
MC_LFN = "/store/mc/RunIII2024Summer24NanoAODv15/DYto2E/NANOAODSIM/source.root"


def _file(role, sample, dataset, lfn, is_data, stop):
    return {
        "role": role,
        "sample": sample,
        "dataset": dataset,
        "lfn": lfn,
        "pfn": "root://cmsxrootd.fnal.gov/" + lfn,
        "era": "2024",
        "is_data": is_data,
        "entry_start": 0,
        "entry_stop": stop,
        "frozen_file_entries": stop + 1,
        "verified_events_entries": stop + 1,
        "verified_root_uuid": "00000000-0000-0000-0000-000000000000",
        "source_id": "a" * 64,
        "file_inventory_hash": "b" * 64,
    }


def _manifest(tmp_path, *, change=None):
    data = _file("muon_c", "MuonEG_Run2024C-ReReco-v1", DATASET, DATA_LFN, True, 200000)
    mc = _file("dy_ee", "DYto2E-2Jets_MLL-50", MC_DATASET, MC_LFN, False, 80000)
    if change:
        data.update(change)
    path = tmp_path / "inputs.json"
    path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "kind": "paired_2024_lowpt_nanoaod_inputs",
                "mkshapes_head": subprocess.check_output(
                    ["git", "rev-parse", "HEAD"], cwd=REPO, text=True
                ).strip(),
                "files": [data, mc],
            }
        )
    )
    return path


def _load(path, role, tmp_path):
    return load_manifest(
        path, role, tmp_path / "fresh", hashlib.sha256(path.read_bytes()).hexdigest()
    )


def test_selects_exact_manifest_role_dataset_pfn_and_original_entry_window(tmp_path):
    manifest = _load(_manifest(tmp_path), "muon_c", tmp_path)
    assert manifest["pfn"] == "root://cmsxrootd.fnal.gov/" + DATA_LFN
    assert (manifest["entry_start"], manifest["entry_stop"]) == (0, 200000)
    assert step_names(manifest)[-2:] == ("formulasDATA", "finalSnapshot_DATA")


def test_manifest_hash_and_catalog_identity_fail_closed(tmp_path):
    path = _manifest(tmp_path)
    with pytest.raises(ValueError, match="manifest SHA"):
        load_manifest(path, "muon_c", tmp_path / "fresh", "0" * 64)
    path = _manifest(tmp_path, change={"dataset": "/Wrong/Dataset/NANOAOD"})
    with pytest.raises(ValueError, match="catalog"):
        _load(path, "muon_c", tmp_path)
    path = _manifest(tmp_path, change={"is_data": False})
    with pytest.raises(ValueError, match="role"):
        _load(path, "muon_c", tmp_path)


def test_pinned_base_revision_checks_producer_tree_across_diagnostic_commits(tmp_path):
    path = _manifest(tmp_path)
    cohort = json.loads(path.read_text())
    cohort["mkshapes_head"] = "8cd688101e5f0ac833f476d5b4bcfe1822c0d77f"
    path.write_text(json.dumps(cohort))
    manifest = _load(path, "muon_c", tmp_path)
    assert manifest["pinned_mkshapes_head"] == cohort["mkshapes_head"]
    assert manifest["producer_package_tree"] == subprocess.check_output(
        ["git", "rev-parse", "HEAD:mkShapesRDF"], cwd=REPO, text=True
    ).strip()
    cohort["mkshapes_head"] = "0" * 40
    path.write_text(json.dumps(cohort))
    with pytest.raises(ValueError, match="unavailable"):
        _load(path, "muon_c", tmp_path)


@pytest.mark.parametrize(
    "change",
    [
        {"pfn": "root://other.example//store/data/source.root"},
        {"entry_start": 200000, "entry_stop": 200000},
        {"entry_stop": 200002},
        {"entry_stop": 200001, "frozen_file_entries": 200002},
    ],
)
def test_rejects_pfn_mismatch_and_invalid_or_oversized_range(tmp_path, change):
    with pytest.raises(ValueError):
        _load(_manifest(tmp_path, change=change), "muon_c", tmp_path)


def test_rejects_existing_output_and_unknown_role(tmp_path):
    path = _manifest(tmp_path)
    (tmp_path / "fresh").mkdir()
    with pytest.raises(ValueError, match="already exists"):
        _load(path, "muon_c", tmp_path)
    with pytest.raises(ValueError, match="role"):
        _load(path, "missing", tmp_path)


def test_mc_requires_hashed_verified_full_source_sumw(tmp_path):
    manifest = _load(_manifest(tmp_path), "dy_ee", tmp_path)
    receipt = {
        "schema_version": 1,
        "status": "verified",
        "sample": manifest["sample"],
        "dataset": manifest["dataset"],
        "method": "Runs.genEventSumw",
        "source_lfns": [MC_LFN, "/store/mc/other.root"],
        "per_file_gen_event_sumw": [11.5, -1.5],
        "source_file_inventory_hash": manifest["file_inventory_hash"],
        "gen_event_sumw": 10.0,
    }
    path = tmp_path / "sumw.json"
    path.write_text(json.dumps(receipt))
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    assert load_mc_sumw(manifest, path, digest) == 10.0
    assert "l2tight" in step_names(manifest)
    receipt["gen_event_sumw"] = 9.0
    path.write_text(json.dumps(receipt))
    with pytest.raises(ValueError, match="sum"):
        load_mc_sumw(manifest, path, hashlib.sha256(path.read_bytes()).hexdigest())
    receipt.update(
        source_lfns=[MC_LFN], per_file_gen_event_sumw=[11.5], gen_event_sumw=11.5
    )
    path.write_text(json.dumps(receipt))
    with pytest.raises(ValueError, match="sum"):
        load_mc_sumw(manifest, path, hashlib.sha256(path.read_bytes()).hexdigest())
    with pytest.raises(ValueError, match="receipt"):
        load_mc_sumw(manifest, None, None)


def test_ledger_links_step_outputs_to_original_typed_event_keys():
    keys = [
        {
            "diagnostic_source_entry": 2,
            "run": 380000,
            "luminosityBlock": 4,
            "event": 2**63 + 9,
        },
        {
            "diagnostic_source_entry": 3,
            "run": 380000,
            "luminosityBlock": 4,
            "event": 17,
        },
        {
            "diagnostic_source_entry": 4,
            "run": 380001,
            "luminosityBlock": 1,
            "event": 18,
        },
    ]
    ledger = build_ledger(keys, [("chain_selection", [2, 4]), ("lumiMask", [4])])
    assert ledger["input_events"][0]["event"] == 2**63 + 9
    assert ledger["stages"] == [
        {
            "step": "chain_selection",
            "input_count": 3,
            "output_count": 2,
            "output_source_entries": [2, 4],
        },
        {
            "step": "lumiMask",
            "input_count": 2,
            "output_count": 1,
            "output_source_entries": [4],
        },
    ]
    with pytest.raises(ValueError, match="source entry"):
        build_ledger(keys, [("bad", [2, 5])])


def test_retained_hww_basew_requires_catalog_xs_and_matched_central_parent(tmp_path):
    manifest = _load(_manifest(tmp_path), "dy_ee", tmp_path)
    xs_file = Productions[PRODUCER["mc"][0]]["xsFile"]
    xs_db = runpy.run_path(str(REPO / "mkShapesRDF/processor/framework" / xs_file))[
        "xs_db"
    ]
    xs = float(xs_db[manifest["sample"]][0].split("=")[1])
    receipt = {
        "schema_version": 1,
        "status": "verified",
        "sample": manifest["sample"],
        "dataset": manifest["dataset"],
        "method": "retained_hww_baseW",
        "matched_input_lfn": MC_LFN,
        "historical_hww_part0_uri": "root://example//store/user/HWW_part0.root",
        "historical_compiled_pickle_sha256": "c" * 64,
        "parent_pair_evidence_sha256": "d" * 64,
        "historical_hww_baseW": 2.0,
        "cross_section_pb": xs,
        "gen_event_sumw": xs * 500,
    }
    path = tmp_path / "retained_basew.json"
    path.write_text(json.dumps(receipt))
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    assert load_mc_sumw(manifest, path, digest) == xs * 500
    receipt["cross_section_pb"] = "invalid"
    path.write_text(json.dumps(receipt))
    with pytest.raises(ValueError, match="provenance/algebra"):
        load_mc_sumw(manifest, path, hashlib.sha256(path.read_bytes()).hexdigest())


def test_root_entry_range_preserves_original_entry_and_unsigned_event_identity(
    tmp_path,
):
    import ROOT
    from mkShapesRDF.processor.framework.mRDF import mRDF

    df = mRDF()
    df.df = (
        ROOT.RDataFrame(6)
        .Define("run", "380000U")
        .Define("luminosityBlock", "4U")
        .Define("event", "(ULong64_t(1) << 63) + rdfentry_")
        .Define("CUT", "true")
    )
    df.cols = list(map(str, df.df.GetColumnNames()))
    df = df.Define("diagnostic_source_entry", "rdfentry_").Copy()
    df.df = df.df.Range(2, 5)
    keys_action = _book_keys(df)
    filtered = df.Filter("diagnostic_source_entry != 3")
    final_action = _book_entries(filtered)
    output = tmp_path / "synthetic.root"
    opts = ROOT.RDF.RSnapshotOptions()
    opts.fLazy = True
    opts.fMode = "RECREATE"
    filtered.df.Snapshot(
        "Events", str(output), sorted(filtered.GetColumnNames()), opts
    ).GetValue()
    ledger = build_ledger(
        _result_keys(keys_action), [("filter", final_action.GetValue())]
    )
    assert [row["diagnostic_source_entry"] for row in ledger["input_events"]] == [
        2,
        3,
        4,
    ]
    assert [row["event"] for row in ledger["input_events"]] == [
        2**63 + n for n in (2, 3, 4)
    ]
    assert ledger["stages"][0]["output_source_entries"] == [2, 4]
    written = ROOT.RDataFrame("Events", str(output))
    assert [int(value) for value in written.Take["ULong64_t"]("event").GetValue()] == [
        2**63 + 2,
        2**63 + 4,
    ]
