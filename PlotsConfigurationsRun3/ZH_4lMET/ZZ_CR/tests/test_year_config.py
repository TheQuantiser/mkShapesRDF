import json
from pathlib import Path
import runpy

import pytest


CONFIG_DIR = Path(__file__).resolve().parents[1]
YEAR_CONFIG = CONFIG_DIR / "year_config.json"
EXPECTED_CORRECTION_FILES = {
    "2022": "/cvmfs/cms-griddata.cern.ch/cat/metadata/BTV/Run3-22CDSep23-Summer22-NanoAODv12/latest/btagging.json.gz",
    "2022EE": "/cvmfs/cms-griddata.cern.ch/cat/metadata/BTV/Run3-22EFGSep23-Summer22EE-NanoAODv12/latest/btagging.json.gz",
    "2023": "/cvmfs/cms-griddata.cern.ch/cat/metadata/BTV/Run3-23CSep23-Summer23-NanoAODv12/latest/btagging.json.gz",
    "2023BPix": "/cvmfs/cms-griddata.cern.ch/cat/metadata/BTV/Run3-23DSep23-Summer23BPix-NanoAODv12/latest/btagging.json.gz",
    "2024": "/cvmfs/cms-griddata.cern.ch/cat/metadata/BTV/Run3-24CDEReprocessingFGHIPrompt-Summer24-NanoAODv15/latest/btagging.json.gz",
}
EXPECTED_EFFICIENCY_MAPS = {
    year: "root://cmseos.fnal.gov//store/user/mwadud/ZH4lMET/btag/" + filename
    for year, filename in {
        "2022": "bTagEff_2022_ttbar_PNetB_loose.root",
        "2022EE": "bTagEff_2022EE_ttbar_PNetB_loose.root",
        "2023": "bTagEff_2023_ttbar_PNetB_loose.root",
        "2023BPix": "bTagEff_2023BPix_ttbar_PNetB_loose.root",
        "2024": "bTagEff_2024_ttbar_UParTAK4B_loose.root",
    }.items()
}


def _helpers():
    return runpy.run_path(str(CONFIG_DIR / "year_config.py"))


def test_official_cvmfs_btag_payloads_and_loose_working_points():
    helpers = _helpers()
    raw = json.loads(YEAR_CONFIG.read_text())
    for year, definition in raw["years"].items():
        btag = definition["btag"]
        assert btag["correction_file"] == EXPECTED_CORRECTION_FILES[year]
        payload = Path(helpers["resolve_btag_sf_payload"](btag["correction_file"]))
        assert payload.is_absolute(), year
        assert payload.is_file(), year
        assert payload.parent.name == "latest"
        assert payload.name == "btagging.json.gz"
        resolved = helpers["resolve_btag_working_point"](
            btag["correction_file"], btag["correction_prefix"], "L"
        )
        assert resolved == pytest.approx(btag["veto_wp"], abs=5e-5), year


def test_btv_payload_does_not_claim_to_supply_mc_efficiency_maps():
    correctionlib = pytest.importorskip("correctionlib")
    helpers = _helpers()
    raw = json.loads(YEAR_CONFIG.read_text())
    for year, definition in raw["years"].items():
        btag = definition["btag"]
        payload = helpers["resolve_btag_sf_payload"](btag["correction_file"])
        correction_set = correctionlib.CorrectionSet.from_file(payload)
        assert btag["correction_prefix"] + "_wp_values" in correction_set, year
        assert btag["correction_prefix"] + "_comb" in correction_set, year
        assert btag["correction_prefix"] + "_light" in correction_set, year
        assert not any("eff" in name.lower() for name in correction_set.keys()), year


def test_remote_efficiency_map_urls_are_explicit_and_resolve_unchanged():
    helpers = _helpers()
    raw = json.loads(YEAR_CONFIG.read_text())
    for year, definition in raw["years"].items():
        configured = definition["btag"]["efficiency_map"]
        assert configured == EXPECTED_EFFICIENCY_MAPS[year]
        assert helpers["is_xrootd_url"](configured)
        assert helpers["resolve_btag_efficiency_map"](configured) == configured


def test_remote_efficiency_maps_open_with_expected_histograms():
    ROOT = pytest.importorskip("ROOT")
    raw = json.loads(YEAR_CONFIG.read_text())
    for year, definition in raw["years"].items():
        url = definition["btag"]["efficiency_map"]
        handle = ROOT.TFile.Open(url, "READ")
        assert handle and not handle.IsZombie(), year
        try:
            assert all(handle.Get(name) for name in ("bjet_eff", "cjet_eff", "ljet_eff")), year
        finally:
            handle.Close()


def test_all_eras_have_disjoint_complete_overlap_and_normalization_models():
    helpers = _helpers()
    full = helpers["load_full_config"]()
    assert set(full["years"]) == {"2022", "2022EE", "2023", "2023BPix", "2024"}
    for year, definition in full["years"].items():
        helpers["_validate_year_cfg"](year, definition)
        overlap = helpers["resolve_overlap_model"](definition, full)
        normalizations = helpers["resolve_production_normalizations"](definition, full)
        physical = tuple(definition["mc"]["samples"])
        consumed = set(overlap["consumed_sources"])
        passthrough = set(overlap["passthrough_sources"])
        assert consumed.isdisjoint(passthrough), year
        assert consumed | passthrough == set(physical), year
        assert len(overlap["output_names"]) == len(set(overlap["output_names"])), year
        assert set(normalizations).issubset(physical), year


def test_sample_profiles_cover_exact_logical_outputs_for_every_year():
    helpers = _helpers()
    full = helpers["load_full_config"]()
    for year, definition in full["years"].items():
        overlap = helpers["resolve_overlap_model"](definition, full)
        commissioning = helpers["resolve_sample_profile"](
            definition, full, "commissioning"
        )
        presentation = helpers["resolve_sample_profile"](
            definition, full, "presentation"
        )

        expected_commissioning_mc = {
            sample_name
            for group_name in ("DY", "ZZ")
            for sample_name in full["plot_groups"][group_name]["samples"]
            if sample_name in overlap["output_names"]
        }
        assert set(commissioning["mc_output_names"]) == expected_commissioning_mc, year
        assert set(commissioning["output_names"]) == expected_commissioning_mc | {"DATA"}, year
        assert set(presentation["mc_output_names"]) == set(overlap["output_names"]), year
        assert set(presentation["output_names"]) == set(overlap["output_names"]) | {"DATA"}, year
        assert len(presentation["output_names"]) == len(set(presentation["output_names"])), year
        assert presentation["nonprompt_background_included"] is False

        target_signal = {
            sample_name
            for sample_name in full["plot_groups"]["HWW_signal"]["samples"]
            if sample_name in overlap["output_names"]
        }
        assert target_signal, year
        assert target_signal.issubset(presentation["mc_output_names"]), year


def test_sample_filter_is_stronger_than_profile_and_fails_closed():
    helpers = _helpers()
    full = helpers["load_full_config"]()
    year = full["years"]["2024"]
    selected = helpers["resolve_sample_selection"](
        year, full, "presentation", "ZZ,DATA"
    )
    assert selected["selection_source"] == "filter"
    assert selected["active_output_names"] == ("ZZ", "DATA")
    with pytest.raises(ValueError, match="absent from the selected year"):
        helpers["resolve_sample_selection"](
            year, full, "commissioning", "DOES_NOT_EXIST"
        )
    with pytest.raises(ValueError, match="selected no logical outputs"):
        helpers["resolve_sample_selection"](year, full, "presentation", "")


def test_data_stream_filter_is_exact_and_fail_closed():
    helpers = _helpers()
    full = helpers["load_full_config"]()
    samples = helpers["resolve_data_samples"](full["years"]["2024"], ["MuonEG"])
    assert samples
    assert {item["stream"] for item in samples} == {"MuonEG"}
    assert {item["dataset"] for item in samples} == {"MuonEG"}
    with pytest.raises(ValueError, match="unknown streams"):
        helpers["resolve_data_samples"](full["years"]["2024"], ["NotAStream"])
