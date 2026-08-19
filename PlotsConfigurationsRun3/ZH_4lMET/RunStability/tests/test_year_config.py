import json
from pathlib import Path
import runpy

import pytest


CONFIG_DIR = Path(__file__).resolve().parents[1]
YEAR_CONFIG = CONFIG_DIR / "year_config.json"
EXPECTED_LUMI_FB = {
    "2022": 8.076828657919002,
    "2022EE": 26.671325997159986,
    "2023": 18.062658998219003,
    "2023BPix": 9.693130030386998,
    "2024": 109.72830897472497,
}


def _helpers():
    return runpy.run_path(str(CONFIG_DIR / "year_config.py"))


def test_year_json_owns_only_era_sample_trigger_and_lumi_metadata():
    raw = json.loads(YEAR_CONFIG.read_text(encoding="utf-8"))
    assert raw["schema_version"] == 2
    assert raw["default_year"] == "2024"
    assert tuple(raw["years"]) == tuple(EXPECTED_LUMI_FB)
    assert "selection_profiles" not in raw
    assert "production_profiles" not in raw
    assert "btag" not in raw["year_defaults"]
    assert "lumi_nuisance" not in raw["year_defaults"]
    assert "trigobj_nanoaod_version" not in raw["year_defaults"]
    assert set(raw["year_defaults"]) == {
        "mc",
        "data",
        "trigger_paths",
        "lepton_ids",
    }
    assert {
        era: definition["lumi_fb"] for era, definition in raw["years"].items()
    } == EXPECTED_LUMI_FB


def test_all_eras_materialize_complete_unique_dy_inputs(monkeypatch):
    helpers = _helpers()
    full = helpers["load_full_config"]()
    for era, expected_lumi in EXPECTED_LUMI_FB.items():
        monkeypatch.setenv("YEAR", era)
        selected_era, definition, selected_full = helpers["load_selected_year"]()
        assert selected_era == era
        assert selected_full == full
        assert definition["lumi_fb"] == expected_lumi
        assert definition["l2tight_era"]
        assert definition["mc"]["production"]
        assert definition["mc"]["steps"]
        assert definition["mc"]["samples"]
        assert len(definition["mc"]["samples"]) == len(set(definition["mc"]["samples"]))
        assert definition["data"]["reco"]
        assert definition["data"]["steps"]
        runs = definition["data"]["runs"]
        assert runs and len(runs) == len(set(runs))
        datasets = [sample["dataset"] for sample in definition["data"]["samples"]]
        assert datasets and len(datasets) == len(set(datasets))
        for sample in definition["data"]["samples"]:
            assert sample["stream"] in full["data_stream_triggers"]
            assert sample["trigger"]
            assert set(sample.get("runs", runs)) <= set(runs)


def test_2022_bcd_primary_dataset_transition_matrix_is_exact(monkeypatch):
    monkeypatch.setenv("YEAR", "2022")
    _, year, _ = _helpers()["load_selected_year"]()
    components = {
        (sample["dataset"], run)
        for sample in year["data"]["samples"]
        for run in sample.get("runs", year["data"]["runs"])
    }
    assert year["data"]["runs"] == [
        "Run2022B-ReReco-v1",
        "Run2022C-ReReco-v1",
        "Run2022D-ReReco-v1",
    ]
    assert components == {
        ("MuonEG", "Run2022B-ReReco-v1"),
        ("MuonEG", "Run2022C-ReReco-v1"),
        ("MuonEG", "Run2022D-ReReco-v1"),
        ("SingleMuon", "Run2022B-ReReco-v1"),
        ("SingleMuon", "Run2022C-ReReco-v1"),
        ("Muon", "Run2022C-ReReco-v1"),
        ("Muon", "Run2022D-ReReco-v1"),
        ("EGamma", "Run2022B-ReReco-v1"),
        ("EGamma", "Run2022C-ReReco-v1"),
        ("EGamma", "Run2022D-ReReco-v1"),
    }


def test_year_json_owns_one_ordered_concrete_hlt_path_per_profile_join():
    full = _helpers()["load_full_config"]()
    paths = tuple(
        path
        for definition in full["year_defaults"]["trigger_paths"].values()
        for path in definition["paths"]
    )
    assert len(paths) == len(set(paths)) == 7
    assert all(path.startswith("HLT_") for path in paths)


def test_data_filters_are_exact_ordered_and_fail_closed():
    helpers = _helpers()
    configured = ["Run2022B-ReReco-v1", "Run2022C-ReReco-v1"]
    assert helpers["resolve_data_run_filter"](configured, ()) == configured
    assert helpers["resolve_data_run_filter"](configured, ("Run2022C-ReReco-v1",)) == [
        "Run2022C-ReReco-v1"
    ]
    with pytest.raises(ValueError, match="unknown run tags"):
        helpers["resolve_data_run_filter"](configured, ("Run2022Z-Missing",))


def test_materializer_rejects_unknown_stream_trigger_and_run():
    helpers = _helpers()
    raw = json.loads(YEAR_CONFIG.read_text(encoding="utf-8"))
    raw["years"]["2022"]["data"]["samples"][0]["stream"] = "Missing"
    with pytest.raises(ValueError, match="unknown stream"):
        helpers["_materialize_years"](raw)

    raw = json.loads(YEAR_CONFIG.read_text(encoding="utf-8"))
    raw["years"]["2022"]["data"]["samples"][0]["trigger"] = "Trigger_Missing"
    with pytest.raises(ValueError, match="unconfigured trigger flags"):
        helpers["_materialize_years"](raw)

    raw = json.loads(YEAR_CONFIG.read_text(encoding="utf-8"))
    raw["years"]["2022"]["data"]["samples"][0]["runs"] = ["Run2022Z-Missing"]
    with pytest.raises(ValueError, match="unknown run tags"):
        helpers["_materialize_years"](raw)
