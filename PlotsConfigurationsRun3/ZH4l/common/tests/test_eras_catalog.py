import json
from pathlib import Path

import pytest

from common.eras import (
    load_full_config,
    load_selected_era,
    resolve_era,
    resolve_overlap_model,
    resolve_sample_profile,
    resolve_sample_selection,
)


HERE = Path(__file__).resolve().parents[1]
ERAS = ("2022", "2022EE", "2023", "2023BPix", "2024")


def test_all_supported_eras_materialize_without_changing_identifiers():
    raw = json.loads((HERE / "eras.json").read_text())
    full = load_full_config()
    assert tuple(full["years"]) == ERAS
    for era in ERAS:
        selected, cfg, _ = load_selected_era(era=era)
        assert selected == era
        assert cfg["lumi_fb"] == raw["years"][era]["lumi_fb"]
        assert cfg["mc"]["production"] == raw["years"][era]["mc"]["production"]


def test_era_is_preferred_and_year_is_a_checked_compatibility_alias():
    assert resolve_era(environ={"ERA": "2024"}) == "2024"
    assert resolve_era(environ={"YEAR": "2023BPix"}) == "2023BPix"
    assert resolve_era(environ={"ERA": "2023", "YEAR": "2023"}) == "2023"
    with pytest.raises(ValueError, match="Inconsistent"):
        resolve_era(environ={"ERA": "2023", "YEAR": "2024"})
    with pytest.raises(ValueError, match="disagrees"):
        resolve_era("2024", environ={"ERA": "2023"})


def test_catalog_has_unique_logical_processes_and_group_ownership():
    full = load_full_config()
    group_members = {}
    for group, cfg in full["plot_groups"].items():
        for sample in cfg["samples"]:
            assert sample not in group_members, (sample, group_members[sample], group)
            group_members[sample] = group
    for era in ERAS:
        outputs = full["years"][era]["mc"]["samples"]
        assert len(outputs) == len(set(outputs))


def test_full_is_the_complete_default_and_quick_is_explicitly_bounded():
    full = load_full_config()
    for era in ERAS:
        _, cfg, _ = load_selected_era(era=era)
        canonical = tuple(resolve_overlap_model(cfg, full)["output_names"])

        default = resolve_sample_profile(cfg, full)
        production = resolve_sample_profile(cfg, full, "full")
        quick = resolve_sample_profile(cfg, full, "quick")

        assert default["output_names"] == canonical + ("DATA",)
        assert production["output_names"] == canonical + ("DATA",)
        assert quick["plot_groups"] == ("DY", "ZZ")
        assert set(quick["sample_to_plot_group"].values()) <= {"DY", "ZZ"}
        assert "ZZ" in quick["output_names"] and "DATA" in quick["output_names"]


def test_legacy_sample_profile_names_are_compatible_aliases():
    full = load_full_config()
    _, cfg, _ = load_selected_era(era="2024")
    assert resolve_sample_profile(cfg, full, "commissioning")["output_names"] == (
        resolve_sample_profile(cfg, full, "quick")["output_names"]
    )
    assert resolve_sample_profile(cfg, full, "presentation")["output_names"] == (
        resolve_sample_profile(cfg, full, "full")["output_names"]
    )


def test_exact_filter_can_select_signal_independently_of_operational_profile():
    full = load_full_config()
    _, cfg, _ = load_selected_era(era="2024")
    signal = "ZH_Zto2L_Hto2Wto2L2Nu_M125"
    resolved = resolve_sample_selection(cfg, full, "quick", signal)
    assert resolved["selection_source"] == "filter"
    assert resolved["active_output_names"] == (signal,)
