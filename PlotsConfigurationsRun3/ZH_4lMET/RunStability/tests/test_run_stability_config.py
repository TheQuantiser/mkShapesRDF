import csv
import hashlib
import json
from pathlib import Path
import runpy
import shutil

import pytest


ROOT = pytest.importorskip("ROOT")


CONFIG_DIR = Path(__file__).resolve().parents[1]
LUMI_RESULTS = (
    CONFIG_DIR
    / "lumi"
    / "audits"
    / "ZZ_CR_RunStability_BCD_afa86d85_conjunction_20260818T200415Z"
    / "results"
)
EXPECTED_RUNS = {
    "2022": 170,
    "2022EE": 190,
    "2023": 126,
    "2023BPix": 43,
    "2024": 456,
}
EXPECTED_LUMI_FB = {
    "2022": 8.076828657919002,
    "2022EE": 26.671325997159986,
    "2023": 18.062658998219003,
    "2023BPix": 9.693130030386998,
    "2024": 109.72830897472497,
}


def _load(monkeypatch, era="2024", results_dir=LUMI_RESULTS, runtime_lumi=None):
    monkeypatch.setenv("YEAR", era)
    monkeypatch.setenv("ANALYSIS_PASS", "RUN_STABILITY")
    if results_dir is None:
        monkeypatch.delenv("RUN_STABILITY_LUMI_DIR", raising=False)
    else:
        monkeypatch.setenv("RUN_STABILITY_LUMI_DIR", str(results_dir))
    monkeypatch.setenv("RUN_STABILITY_REGION", "DY")
    monkeypatch.setenv("RUN_STABILITY_PRODUCTION_PROFILE", "dy")
    monkeypatch.setenv("SELECTION_PROFILE", "dy")
    monkeypatch.setenv("RUN_STABILITY_OBSERVABLES", "configured")
    monkeypatch.delenv("RUN_STABILITY_CATEGORIES", raising=False)
    year_state = runpy.run_path(str(CONFIG_DIR / "year_config.py"))
    _, selected, _ = year_state["load_selected_year"]()
    return runpy.run_path(
        str(CONFIG_DIR / "run_stability_config.py"),
        init_globals={
            **year_state,
            "CONFIG_DIR": str(CONFIG_DIR),
            "YEAR": era,
            "ANALYSIS_PASS": "RUN_STABILITY",
            "_selected_year": selected,
            "lumi": selected["lumi_fb"] if runtime_lumi is None else runtime_lumi,
        },
    )


def _sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _copy_inputs(tmp_path):
    root = tmp_path / "lumi"
    results = root / "results"
    inputs = root / "inputs"
    results.mkdir(parents=True)
    inputs.mkdir(parents=True)
    names = (
        "luminosity_by_run.csv",
        "luminosity_by_analysis_era.csv",
        "luminosity_by_year.csv",
        "trigger_combinations_by_run.csv",
        "trigger_combinations_by_era.csv",
        "trigger_combinations_by_year.csv",
        "trigger_paths_by_run.csv",
        "trigger_paths_by_era.csv",
        "trigger_paths_by_year.csv",
        "validation_report.json",
    )
    for name in names:
        shutil.copy2(LUMI_RESULTS / name, results / name)
    shutil.copy2(LUMI_RESULTS.parent / "provenance.json", root / "provenance.json")
    shutil.copy2(
        LUMI_RESULTS.parent / "inputs" / "manifest.json", inputs / "manifest.json"
    )
    shutil.copy2(
        LUMI_RESULTS.parent / "inputs" / "year_config.json",
        inputs / "year_config.json",
    )
    return results


def _rewrite_csv(path, transform):
    with path.open(newline="") as handle:
        reader = csv.DictReader(handle)
        fieldnames = reader.fieldnames
        rows = list(reader)
    rows = transform(rows)
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _refresh_receipt(results, name):
    provenance_path = results.parent / "provenance.json"
    provenance = json.loads(provenance_path.read_text())
    provenance["results_sha256"][f"results/{name}"] = _sha256(results / name)
    provenance_path.write_text(json.dumps(provenance, indent=2, sort_keys=True) + "\n")


def test_all_eras_have_exact_audited_dy_run_and_output_inventories(
    monkeypatch, tmp_path
):
    results = _copy_inputs(tmp_path)
    for era, expected in EXPECTED_RUNS.items():
        state = _load(monkeypatch, era, results_dir=results)
        contract = state["RUN_STABILITY_CONTRACT"]
        assert contract["enabled"] is True
        assert len(contract["ordered_runs"]) == expected
        assert contract["ordered_runs"] == sorted(contract["ordered_runs"])
        assert len(contract["run_to_bin"]) == expected
        assert contract["target_region"] == "DY"
        assert len(contract["categories"]) == 48
        assert contract["observables"] == [
            "Z0_mass",
            "Z0_pt",
            "lZ1_pt",
            "lZ2_pt",
            "lZ1_eta",
            "lZ2_eta",
        ]
        assert len(contract["auxiliary_output_paths"]) == 288
        assert all(
            path.endswith("/histo_DATA") for path in contract["auxiliary_output_paths"]
        )
        assert contract["future_luminosity_source_default"] is None
        assert contract["mc_source_lumi_fb"] == EXPECTED_LUMI_FB[era]
        assert len(contract["luminosity_sources"]) == 14
        assert len(contract["metadata_output_paths"]) == 29
        assert contract["category_luminosity_sources"]["DY_STREAM_MUON"] == (
            "trigger_any"
        )
        assert contract["category_luminosity_sources"]["DY_TRGFAM_SINGLEMU"] == (
            "trigger_sngmu"
        )
        assert contract["category_luminosity_sources"]["DY_HLT_ISOMU24"] == (
            "hlt_isomu24"
        )
        assert contract["inputs"]["luminosity_by_run"]["sha256"] == _sha256(
            LUMI_RESULTS / "luminosity_by_run.csv"
        )
        projection = contract["inputs"]["luminosity_projection"]
        assert projection["status"] == "matched"
        assert projection["live_sha256"] == projection["audited_sha256"]


def test_nominal_and_trigger_any_rows_are_aligned(monkeypatch, tmp_path):
    results = _copy_inputs(tmp_path)
    contract = _load(monkeypatch, results_dir=results)["RUN_STABILITY_CONTRACT"]
    assert [row["run"] for row in contract["nominal"]] == contract["ordered_runs"]
    assert [row["run"] for row in contract["trigger_any"]] == contract["ordered_runs"]
    assert contract["aggregate_checks"]["nominal_era"]["recorded_fb"] == pytest.approx(
        sum(row["recorded_fb"] for row in contract["nominal"]), abs=5e-9
    )
    assert contract["aggregate_checks"]["trigger_any_era"][
        "recorded_fb"
    ] == pytest.approx(
        sum(row["recorded_fb"] for row in contract["trigger_any"]), abs=5e-9
    )


def test_all_family_and_path_sources_are_run_aligned(monkeypatch, tmp_path):
    results = _copy_inputs(tmp_path)
    contract = _load(monkeypatch, results_dir=results)["RUN_STABILITY_CONTRACT"]
    assert set(contract["luminosity_sources"]) == {
        "nominal",
        "trigger_any",
        "trigger_elmu",
        "trigger_sngmu",
        "trigger_dblmu",
        "trigger_sngel",
        "trigger_dblel",
        "hlt_mu23_ele12",
        "hlt_mu12_ele23",
        "hlt_mu8_ele23",
        "hlt_mu17_mu8",
        "hlt_isomu24",
        "hlt_ele23_ele12",
        "hlt_ele30",
    }
    for definition in contract["luminosity_sources"].values():
        assert [row["run"] for row in definition["rows"]] == contract["ordered_runs"]


def test_missing_luminosity_input_fails_closed(monkeypatch, tmp_path):
    results = _copy_inputs(tmp_path)
    (results / "luminosity_by_run.csv").unlink()
    with pytest.raises(FileNotFoundError, match="inputs are incomplete"):
        _load(monkeypatch, results_dir=results)


def test_lumi_binding_is_self_contained_and_semantic(monkeypatch):
    results = LUMI_RESULTS
    live = CONFIG_DIR / "year_config.json"
    audited = results.parent / "inputs" / "year_config.json"
    assert _sha256(live) != _sha256(audited)
    contract = _load(monkeypatch, results_dir=results)["RUN_STABILITY_CONTRACT"]
    projection = contract["inputs"]["luminosity_projection"]
    assert projection["status"] == "matched"
    assert projection["live_sha256"] == projection["audited_sha256"]
    assert Path(contract["input_results_dir"]).is_relative_to(CONFIG_DIR)


def test_default_active_lumi_binding_names_and_hashes_live_leaf(monkeypatch):
    state = _load(monkeypatch, "2024", results_dir=None)
    binding = state["RUN_STABILITY_CONTRACT"]["inputs"]["active_luminosity_binding"]
    assert binding["mode"] == "profile_default"
    assert binding["status"] == "matched"
    assert (
        Path(binding["path"]).resolve()
        == (CONFIG_DIR / "lumi" / "run_stability_luminosity_binding.json").resolve()
    )


def test_relative_lumi_override_fails_closed(monkeypatch):
    with pytest.raises(ValueError, match="must be an absolute path"):
        _load(monkeypatch, "2024", results_dir=Path("relative/results"))


def test_runtime_mc_lumi_must_equal_selected_configured_audited_value(monkeypatch):
    with pytest.raises(RuntimeError, match="runtime lumi must equal"):
        _load(monkeypatch, "2024", runtime_lumi=1.0)


def test_lumi_manifest_bytes_must_match_provenance(monkeypatch, tmp_path):
    results = _copy_inputs(tmp_path)
    manifest_path = results.parent / "inputs" / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["analysis_revision"] = "mutated-after-receipt"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    with pytest.raises(RuntimeError, match="inputs/manifest.json"):
        _load(monkeypatch, results_dir=results)


def test_lumi_semantic_projection_drift_fails_closed(monkeypatch, tmp_path):
    results = _copy_inputs(tmp_path)
    audited_path = results.parent / "inputs" / "year_config.json"
    audited = json.loads(audited_path.read_text())
    audited["years"]["2024"]["l2tight_era"] += "_mutated"
    audited_path.write_text(json.dumps(audited, indent=2, sort_keys=True) + "\n")

    manifest_path = results.parent / "inputs" / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["year_config"]["sha256"] = _sha256(audited_path)
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    provenance_path = results.parent / "provenance.json"
    provenance = json.loads(provenance_path.read_text())
    provenance["inputs"]["manifest_sha256"] = _sha256(manifest_path)
    provenance_path.write_text(json.dumps(provenance, indent=2, sort_keys=True) + "\n")
    with pytest.raises(
        RuntimeError, match="luminosity-relevant year configuration differs"
    ):
        _load(monkeypatch, results_dir=results)


def test_malformed_validation_json_fails_closed(monkeypatch, tmp_path):
    results = _copy_inputs(tmp_path)
    (results / "validation_report.json").write_text("{not-json\n")
    with pytest.raises(RuntimeError, match="Invalid run-stability JSON"):
        _load(monkeypatch, results_dir=results)


def test_failed_validation_receipt_fails_closed(monkeypatch, tmp_path):
    results = _copy_inputs(tmp_path)
    path = results / "validation_report.json"
    receipt = json.loads(path.read_text())
    receipt["status"] = "failed"
    path.write_text(json.dumps(receipt, sort_keys=True) + "\n")
    _refresh_receipt(results, path.name)
    with pytest.raises(RuntimeError, match="passed luminosity validation receipt"):
        _load(monkeypatch, results_dir=results)


def test_duplicate_run_fails_closed(monkeypatch, tmp_path):
    results = _copy_inputs(tmp_path)
    path = results / "luminosity_by_run.csv"

    def duplicate(rows):
        row = next(item for item in rows if item["analysis_era"] == "2024")
        return rows + [dict(row)]

    _rewrite_csv(path, duplicate)
    _refresh_receipt(results, path.name)
    with pytest.raises(RuntimeError, match="duplicate run"):
        _load(monkeypatch, results_dir=results)


def test_nonfinite_luminosity_fails_closed(monkeypatch, tmp_path):
    results = _copy_inputs(tmp_path)
    path = results / "luminosity_by_run.csv"

    def poison(rows):
        row = next(item for item in rows if item["analysis_era"] == "2024")
        row["recorded_fb"] = "nan"
        return rows

    _rewrite_csv(path, poison)
    _refresh_receipt(results, path.name)
    with pytest.raises(RuntimeError, match="finite and nonnegative"):
        _load(monkeypatch, results_dir=results)


def test_inconsistent_era_aggregate_fails_closed(monkeypatch, tmp_path):
    results = _copy_inputs(tmp_path)
    path = results / "luminosity_by_analysis_era.csv"

    def shift(rows):
        row = next(item for item in rows if item["analysis_era"] == "2024")
        row["recorded_fb"] = str(float(row["recorded_fb"]) + 1.0)
        return rows

    _rewrite_csv(path, shift)
    _refresh_receipt(results, path.name)
    with pytest.raises(
        RuntimeError,
        match="must equal the exact validated nominal recorded luminosity",
    ):
        _load(monkeypatch, results_dir=results)


def test_nominal_trigger_run_set_mismatch_fails_closed(monkeypatch, tmp_path):
    results = _copy_inputs(tmp_path)
    path = results / "trigger_combinations_by_run.csv"

    def remove_one(rows):
        removed = False
        kept = []
        for row in rows:
            if (
                not removed
                and row["analysis_era"] == "2024"
                and row["scope_name"] == "Trigger_Any"
            ):
                removed = True
                continue
            kept.append(row)
        return kept

    _rewrite_csv(path, remove_one)
    _refresh_receipt(results, path.name)
    with pytest.raises(RuntimeError, match="run sets differ"):
        _load(monkeypatch, results_dir=results)


def test_nominal_hlt_path_run_set_mismatch_fails_closed(monkeypatch, tmp_path):
    results = _copy_inputs(tmp_path)
    path = results / "trigger_paths_by_run.csv"
    year_state = runpy.run_path(str(CONFIG_DIR / "year_config.py"))
    full = year_state["load_full_config"]()
    configured_paths = tuple(
        physical_path
        for definition in full["year_defaults"]["trigger_paths"].values()
        for physical_path in definition["paths"]
    )
    target_scope = configured_paths[len(configured_paths) // 2]

    def remove_one(rows):
        removed = False
        kept = []
        for row in rows:
            if (
                not removed
                and row["analysis_era"] == "2024"
                and row["scope_name"] == target_scope
            ):
                removed = True
                continue
            kept.append(row)
        return kept

    _rewrite_csv(path, remove_one)
    _refresh_receipt(results, path.name)
    with pytest.raises(RuntimeError, match="run sets differ"):
        _load(monkeypatch, results_dir=results)


def test_generated_index_is_exact_and_unknown_runs_fail(monkeypatch, tmp_path):
    results = _copy_inputs(tmp_path)
    state = _load(monkeypatch, "2022", results_dir=results)
    contract = state["RUN_STABILITY_CONTRACT"]
    assert ROOT.gInterpreter.Declare(state["RUN_STABILITY_CPP"])
    namespace = state["RUN_STABILITY_CPP_NAMESPACE"]
    known = contract["ordered_runs"][0]
    frame = ROOT.RDataFrame(1).Define("idx", f"{namespace}::index({known}u)")
    assert frame.Max("idx").GetValue() == 1
    unknown = ROOT.RDataFrame(1).Define("idx", f"{namespace}::index(1u)")
    # PyROOT exposes the thrown std::runtime_error as a cppyy exception type,
    # not necessarily Python's built-in RuntimeError.
    with pytest.raises(Exception, match="no audited bin for run"):
        unknown.Max("idx").GetValue()
