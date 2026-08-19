import hashlib
import json
from pathlib import Path
import runpy
from copy import deepcopy

import pytest


CONFIG_DIR = Path(__file__).resolve().parents[1]
PROFILE_CONFIG = CONFIG_DIR / "run_stability_profiles.json"
YEAR_CONFIG = CONFIG_DIR / "year_config.json"

OBSERVABLES = (
    "Z0_mass",
    "Z0_pt",
    "lZ1_pt",
    "lZ2_pt",
    "lZ1_eta",
    "lZ2_eta",
)
AXES = {
    "Z0_mass": ("Z0_mass", "m_{Z_{0}} [GeV]", 60, 60.0, 120.0, 1.0, 0),
    "Z0_pt": ("Z0_pt", "p_{T}^{Z_{0}} [GeV]", 20, 0.0, 100.0, 5.0, 2),
    "lZ1_pt": (
        "Alt(Lepton_pt, Alt(Z0_idx, 0, -1), -999.f)",
        "p_{T}(#it{l}_{Z,1}) [GeV]",
        13,
        35.0,
        100.0,
        5.0,
        2,
    ),
    "lZ2_pt": (
        "Alt(Lepton_pt, Alt(Z0_idx, 1, -1), -999.f)",
        "p_{T}(#it{l}_{Z,2}) [GeV]",
        13,
        35.0,
        100.0,
        5.0,
        2,
    ),
    "lZ1_eta": (
        "Alt(Lepton_eta, Alt(Z0_idx, 0, -1), -999.f)",
        "#eta_{#it{l}_{Z,1}}",
        50,
        -2.5,
        2.5,
        0.1,
        0,
    ),
    "lZ2_eta": (
        "Alt(Lepton_eta, Alt(Z0_idx, 1, -1), -999.f)",
        "#eta_{#it{l}_{Z,2}}",
        50,
        -2.5,
        2.5,
        0.1,
        0,
    ),
}
CATEGORY_SELECTOR_SHA256 = (
    "be24d1ac1df9a8b1f91b05187031c1e83fee2825c10cee0c690e73121f3d03a5"
)


def _payload():
    return json.loads(PROFILE_CONFIG.read_text(encoding="utf-8"))


def test_json_has_one_public_dy_production_and_selection_profile():
    payload = _payload()
    year_payload = json.loads(YEAR_CONFIG.read_text(encoding="utf-8"))

    assert payload["schema_version"] == 1
    assert payload["default_production_profile"] == "dy"
    assert tuple(payload["production_profiles"]) == ("dy",)
    assert tuple(payload["selection_profiles"]) == ("dy",)
    assert "production_profiles" not in year_payload
    assert "selection_profiles" not in year_payload

    production = payload["production_profiles"]["dy"]
    selection = payload["selection_profiles"]["dy"]
    assert production["analysis_pass"] == "RUN_STABILITY"
    assert production["region"] == "DY"
    assert production["selection_profile"] == "dy"
    assert production["observable_selector"] == "configured"
    assert production["observables"] == list(OBSERVABLES)
    assert production["mass_window_gev"] == [60.0, 120.0]
    assert production["mass_window_strict"] is True
    assert selection["allowed_analysis_passes"] == ["RUN_STABILITY"]
    assert selection["target_region"] == "DY"
    assert selection["ordered_2l_pt_mins"] == [35.0, 35.0]


def test_json_owns_exact_compact_uniform_axes_and_loader_expands_them():
    payload = _payload()
    production = payload["production_profiles"]["dy"]
    assert tuple(production["axes"]) == OBSERVABLES

    state = runpy.run_path(str(CONFIG_DIR / "run_stability_production.py"))
    resolved = state["run_stability_production_profile"]("dy")
    for name, (expression, label, bins, low, high, width, fold) in AXES.items():
        raw = production["axes"][name]
        assert set(raw) == {"expression", "label", "uniform", "fold"}
        assert raw == {
            "expression": expression,
            "label": label,
            "uniform": [bins, low, high],
            "fold": fold,
        }
        edges = resolved["axes"][name]["edges"]
        assert len(edges) == bins + 1
        assert edges[0] == low
        assert edges[-1] == high
        assert all(
            abs((right - left) - width) < 1.0e-12
            for left, right in zip(edges, edges[1:])
        )


def test_trigger_schema_joins_year_inventory_without_repeating_physical_paths():
    payload = _payload()
    year_payload = json.loads(YEAR_CONFIG.read_text(encoding="utf-8"))
    definitions = payload["production_profiles"]["dy"]["category_definitions"]
    trigger_paths = year_payload["year_defaults"]["trigger_paths"]

    families = definitions["trigger_families"]
    assert tuple(record["aggregate"] for record in families) == (
        "Trigger_ElMu",
        "Trigger_sngMu",
        "Trigger_dblMu",
        "Trigger_sngEl",
        "Trigger_dblEl",
    )
    assert set(record["aggregate"] for record in families) == set(trigger_paths)
    assert all("expression" not in record for record in families)
    assert all("scope_name" not in record for record in families)

    concrete = definitions["concrete_paths"]
    assert all("path" not in record for record in concrete)
    assert len({(record["aggregate"], record["ordinal"]) for record in concrete}) == 7
    assert sum(len(value["paths"]) for value in trigger_paths.values()) == 7


@pytest.mark.parametrize(
    ("mutation", "message"),
    (
        (
            lambda profile: profile["axes"]["Z0_mass"].update(
                {"uniform": [60, 59.0, 120.0]}
            ),
            "Z0_mass bounds must equal mass_window_gev",
        ),
        (
            lambda profile: profile["axes"]["lZ1_pt"].update(
                {"uniform": [13, 30.0, 100.0]}
            ),
            "lZ1_pt lower bound must equal",
        ),
        (
            lambda profile: profile["category_definitions"]["concrete_paths"][1].update(
                {"ordinal": 0}
            ),
            "duplicate aggregate/ordinal joins",
        ),
    ),
)
def test_profile_loader_rejects_cross_contract_drift(mutation, message):
    payload = _payload()
    state = runpy.run_path(str(CONFIG_DIR / "run_stability_production.py"))
    profile = deepcopy(payload["production_profiles"]["dy"])
    mutation(profile)
    with pytest.raises(ValueError, match=message):
        state["_validate_production_profile"](
            "dy", profile, payload["selection_profiles"]
        )


def test_public_category_order_is_derived_and_has_frozen_identity(
    monkeypatch,
):
    monkeypatch.setenv("YEAR", "2024")
    monkeypatch.setenv("ANALYSIS_PASS", "RUN_STABILITY")
    monkeypatch.setenv("SELECTION_PROFILE", "dy")
    monkeypatch.setenv("RUN_STABILITY_REGION", "DY")
    state = runpy.run_path(str(CONFIG_DIR / "category_config.py"))
    categories = state["configured_category_names"]()

    assert len(categories) == 48
    assert len(categories) == len(set(categories))
    assert categories[:12] == (
        "DY_ALL",
        "DY_ZEE",
        "DY_ZMM",
        "DY_STREAM_MUONEG",
        "DY_STREAM_MUON",
        "DY_STREAM_EGAMMA",
        "DY_STREAM_MUONEG_ZEE",
        "DY_STREAM_MUONEG_ZMM",
        "DY_STREAM_MUON_ZEE",
        "DY_STREAM_MUON_ZMM",
        "DY_STREAM_EGAMMA_ZEE",
        "DY_STREAM_EGAMMA_ZMM",
    )
    assert categories[-4:] == (
        "DY_HLT_ELE23_ELE12_ZEE",
        "DY_HLT_ELE23_ELE12_ZMM",
        "DY_HLT_ELE30_ZEE",
        "DY_HLT_ELE30_ZMM",
    )
    digest = hashlib.sha256(",".join(categories).encode()).hexdigest()
    assert digest == CATEGORY_SELECTOR_SHA256
