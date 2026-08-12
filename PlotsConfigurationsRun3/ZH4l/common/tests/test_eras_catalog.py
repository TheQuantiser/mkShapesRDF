import json
from pathlib import Path

import pytest

from common.eras import load_full_config, load_selected_era, resolve_era


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
