"""Tests for fail-closed, dual-domain inventory resolution."""

from __future__ import annotations

import copy
import importlib.util
from pathlib import Path

import pytest


PAIRING_DIR = Path(__file__).resolve().parents[1]
PAIRING_CONFIG_PATH = PAIRING_DIR / "pairing_config.py"


def _load_pairing_config():
    spec = importlib.util.spec_from_file_location(
        "_pairing_study_config_under_test", PAIRING_CONFIG_PATH
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def pairing_config():
    return _load_pairing_config()


EXPECTED_ZH = {
    "2022": (
        "ZH_Hto2Wto2L2Nu_M125",
        "GluGluZH_Hto2Wto2L2Nu_M125",
    ),
    "2022EE": (
        "ZH_Hto2Wto2L2Nu_M125",
        "GluGluZH_Hto2Wto2L2Nu_M125",
    ),
    "2023": (
        "ZH_Hto2Wto2L2Nu_M125",
        "GluGluZH_Hto2Wto2L2Nu_M125",
    ),
    "2023BPix": (
        "ZH_Hto2Wto2L2Nu_M125",
        "GluGluZH_Hto2Wto2L2Nu_M125",
    ),
    "2024": (
        "ZH_Zto2L_Hto2Wto2L2Nu_M125",
        "GluGluZH_Zto2L_Hto2Wto2L2Nu_M125",
    ),
}


def test_all_eras_resolve_disjoint_zh_and_zz_domains(pairing_config):
    assert pairing_config.SUPPORTED_YEARS == (
        "2022",
        "2022EE",
        "2023",
        "2023BPix",
        "2024",
    )
    for year in pairing_config.SUPPORTED_YEARS:
        inventory = pairing_config.resolve_study_inventory(year)
        assert inventory == {"ZH": EXPECTED_ZH[year], "ZZ": ("ZZ",)}
        assert set(inventory["ZH"]).isdisjoint(inventory["ZZ"])
        for sample in inventory["ZH"]:
            assert pairing_config.process_family(sample, year) == "ZH"
        assert pairing_config.process_family("ZZ", year) == "ZZ"


def test_inventory_is_derived_as_an_ordered_intersection(pairing_config):
    source = {
        "years": {
            "2022": {
                "mc": {
                    "samples": ["unused", "zh_second", "zz_only", "zh_first"]
                }
            }
        },
        "plot_groups": {
            "HWW_signal": {
                "samples": ["missing", "zh_first", "zh_second"]
            },
            "ZZ": {"samples": ["zz_only", "also_missing"]},
        },
    }
    assert pairing_config.resolve_inventory_from_config(source, "2022") == {
        "ZH": ("zh_first", "zh_second"),
        "ZZ": ("zz_only",),
    }


@pytest.mark.parametrize("empty_family", ("ZH", "ZZ"))
def test_inventory_fails_closed_when_either_domain_is_empty(
    pairing_config, empty_family
):
    config = copy.deepcopy(pairing_config.load_reference_json())
    group = pairing_config.STUDY_PLOT_GROUPS[empty_family]
    config["plot_groups"][group]["samples"] = ["not_in_the_year"]
    with pytest.raises(RuntimeError, match=f"empty {empty_family} inventory"):
        pairing_config.resolve_inventory_from_config(config, "2024")


def test_inventory_fails_closed_on_cross_domain_overlap(pairing_config):
    config = {
        "years": {"2022": {"mc": {"samples": ["shared"]}}},
        "plot_groups": {
            "HWW_signal": {"samples": ["shared"]},
            "ZZ": {"samples": ["shared"]},
        },
    }
    with pytest.raises(RuntimeError, match="both truth domains"):
        pairing_config.resolve_inventory_from_config(config, "2022")


def test_materialized_year_metadata_tracks_the_reference_catalog(pairing_config):
    reference = pairing_config.load_reference_json()
    default_lepton_ids = reference["year_defaults"]["lepton_ids"]
    for year in pairing_config.SUPPORTED_YEARS:
        resolved = pairing_config.load_pairing_year(year)
        raw = reference["years"][year]
        assert resolved["year"] == year
        assert resolved["inventory"] == {
            "ZH": EXPECTED_ZH[year],
            "ZZ": ("ZZ",),
        }
        assert resolved["production"] == raw["mc"]["production"]
        assert resolved["steps"] == raw["mc"]["steps"]
        assert resolved["electron_wp"] == default_lepton_ids["electron_wp"]
        assert resolved["muon_wp"] == default_lepton_ids["muon_wp"]
        assert resolved["candidate_z_pt_mins"] == (10.0, 10.0)
        assert resolved["ordered_4l_pt_mins"] == (25.0, 15.0, 10.0, 10.0)
        assert set(resolved["logical_components"]) == set(EXPECTED_ZH[year]) | {
            "ZZ"
        }
        for components in resolved["logical_components"].values():
            assert components
            for component in components:
                assert component["source_alias"]
                assert component["tree_base_dir"]
                assert isinstance(component["source_normalization"], float)


def test_unknown_year_and_sample_fail_closed(pairing_config):
    with pytest.raises(ValueError, match="Unsupported YEAR"):
        pairing_config.resolve_study_inventory("2018")
    with pytest.raises(KeyError, match="outside the pairing-study inventory"):
        pairing_config.process_family("DY", "2024")
