import re

import pytest


def test_public_cut_tree_is_dy_only_with_strict_mass_and_pair_pt(load_state):
    state = load_state()
    assert tuple(state["cuts"]) == ("DY",)
    assert tuple(state["CATEGORY_METADATA"]) == state["RUN_STABILITY_CATEGORIES"]
    assert len(state["CATEGORY_METADATA"]) == 48

    parent = state["cuts"]["DY"]["expr"]
    assert re.search(r"Z0_mass\s*>\s*60\.", parent)
    assert re.search(r"Z0_mass\s*<\s*120\.", parent)
    assert "Z0_mass >=" not in parent
    assert "Z0_mass <=" not in parent
    assert "Passes2lOrderedPt" in parent
    assert "Trigger_" not in parent
    assert "nLepton" not in parent
    assert "Trigger_ElMu" in state["preselections"]
    assert "nLepton >= 2" in state["preselections"]
    assert tuple(state["cuts"]["DY"]["categories"]) == tuple(
        category.removeprefix("DY_") for category in state["RUN_STABILITY_CATEGORIES"]
    )


def test_all_category_metadata_is_dy_and_uses_one_nominal_weight(load_state):
    state = load_state()
    for category, metadata in state["CATEGORY_METADATA"].items():
        assert category.startswith("DY_")
        assert metadata["physics_region"] == "DY"
        assert metadata["parent_expression"] == state["cuts"]["DY"]["expr"]
        assert metadata["weight_policy"] == "1.f"
        assert metadata["category_weight_factor"] == "1.f"
        assert metadata["run_stability_luminosity_source"]


def test_derived_category_families_have_exact_counts_and_lumi_routes(load_state):
    metadata = load_state()["CATEGORY_METADATA"]
    assert sum(name in {"DY_ALL", "DY_ZEE", "DY_ZMM"} for name in metadata) == 3
    assert sum(name.startswith("DY_STREAM_") for name in metadata) == 9
    assert sum(name.startswith("DY_TRGFAM_") for name in metadata) == 15
    assert sum(name.startswith("DY_HLT_") for name in metadata) == 21

    assert metadata["DY_ALL"]["run_stability_luminosity_source"] == "trigger_any"
    assert (
        metadata["DY_STREAM_MUON"]["run_stability_luminosity_source"] == "trigger_any"
    )
    assert (
        metadata["DY_TRGFAM_SINGLEMU"]["run_stability_luminosity_source"]
        == "trigger_sngmu"
    )
    assert (
        metadata["DY_TRGFAM_SINGLEMU_ZMM"]["run_stability_luminosity_source"]
        == "trigger_sngmu"
    )
    assert (
        metadata["DY_HLT_ISOMU24"]["run_stability_luminosity_source"] == "hlt_isomu24"
    )
    assert (
        metadata["DY_HLT_ISOMU24_ZMM"]["run_stability_luminosity_source"]
        == "hlt_isomu24"
    )


@pytest.mark.parametrize("profile", ("minimal", "flavor", "stream", "trigger", "debug"))
def test_non_public_category_profiles_fail_closed(load_state, profile):
    with pytest.raises(ValueError, match="CATEGORY_PROFILE=standard"):
        load_state(category=profile)
