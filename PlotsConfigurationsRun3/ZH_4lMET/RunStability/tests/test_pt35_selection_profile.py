import hashlib
from pathlib import Path
import runpy

import pytest


CONFIG_DIR = Path(__file__).resolve().parents[1]
YEAR_CONFIG = CONFIG_DIR / "year_config.json"
AUDITED_YEAR_CONFIG = (
    CONFIG_DIR
    / "lumi"
    / "audits"
    / "ZZ_CR_RunStability_BCD_afa86d85_conjunction_20260818T200415Z"
    / "inputs"
    / "year_config.json"
)
FROZEN_YEAR_CONFIG_SHA256 = (
    "afa86d851cd46c01b57598c9b865e7d9a8e6cbbb1dd2db7e1aa894e8d6ba3ba2"
)


@pytest.fixture(scope="module")
def ROOT():
    return pytest.importorskip("ROOT")


def _selection_state(monkeypatch, *, profile, analysis_pass="RUN_STABILITY"):
    monkeypatch.setenv("YEAR", "2022")
    monkeypatch.setenv("ANALYSIS_PASS", analysis_pass)
    monkeypatch.setenv("RUN_STABILITY_REGION", "DY")
    monkeypatch.setenv("SELECTION_PROFILE", profile)
    state = runpy.run_path(
        str(CONFIG_DIR / "year_config.py"),
        init_globals={"CONFIG_DIR": str(CONFIG_DIR)},
    )
    return runpy.run_path(
        str(CONFIG_DIR / "selection_config.py"),
        init_globals=state,
    )


def test_dy_selection_profile_preserves_frozen_luminosity_evidence(monkeypatch):
    assert hashlib.sha256(AUDITED_YEAR_CONFIG.read_bytes()).hexdigest() == (
        FROZEN_YEAR_CONFIG_SHA256
    )
    assert (
        hashlib.sha256(YEAR_CONFIG.read_bytes()).hexdigest()
        != FROZEN_YEAR_CONFIG_SHA256
    )
    state = _selection_state(monkeypatch, profile="dy")
    profile = state["SELECTED_SELECTION_PROFILE"]
    assert profile["name"] == "dy"
    assert profile["source"] == "run_stability_profiles.json"
    assert profile["target_region"] == "DY"
    assert tuple(profile["ordered_2l_pt_mins"]) == (35.0, 35.0)


def test_dy_profile_is_run_stability_only(monkeypatch):
    with pytest.raises(ValueError, match="ANALYSIS_PASS"):
        _selection_state(
            monkeypatch,
            profile="dy",
            analysis_pass="ALL",
        )


def test_dy_alias_consumes_exact_strict_35_35_thresholds(load_state):
    compiled = load_state(year="2022")
    assert compiled["cuts"]["DY"]["expr"].count("Passes2lOrderedPt") == 1
    alias_state = runpy.run_path(str(CONFIG_DIR / "aliases.py"), init_globals=compiled)
    alias_expression = alias_state["aliases"]["Passes2lOrderedPt"]["expr"]
    assert alias_expression.endswith("Lepton_pt, Z0_idx, 35.0, 35.0)")
    assert alias_state["TWO_LEPTON_PT_MINS"] == (35.0, 35.0)


def test_ordered_pt_helper_uses_strict_thresholds(ROOT):
    helper_macro = CONFIG_DIR / "macros" / "run_stability_helpers.cc"
    ROOT.gInterpreter.Declare(f'#include "{helper_macro}"')
    frame = ROOT.RDataFrame(1)
    frame = frame.Define("zidx", "ROOT::RVecI{1,0}")
    frame = frame.Define("at", "ROOT::RVecF{35.f,35.f}")
    frame = frame.Define("above", "ROOT::RVecF{35.001f,35.001f}")
    frame = frame.Define(
        "passesAt",
        "RunStability::passesOrdered2lPtThresholdsFromPair(at,zidx,35.f,35.f)",
    )
    frame = frame.Define(
        "passesAbove",
        "RunStability::passesOrdered2lPtThresholdsFromPair(above,zidx,35.f,35.f)",
    )
    assert bool(frame.Take["bool"]("passesAt").GetValue()[0]) is False
    assert bool(frame.Take["bool"]("passesAbove").GetValue()[0]) is True
