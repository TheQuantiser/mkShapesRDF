import pytest


def test_minimal_category_ids_exact(load_state):
    state = load_state()
    assert tuple(state["CATEGORY_METADATA"]) == ("DY_ALL", "ZZCR_ALL", "SR_ALL")
    assert len(state["CATEGORY_METADATA"]) == len(set(state["CATEGORY_METADATA"]))


def test_flavor_profile_is_physical(load_state):
    state = load_state(category="flavor")
    assert tuple(state["CATEGORY_METADATA"]) == (
        "DY_ALL", "DY_ZEE", "DY_ZMM",
        "ZZCR_ALL", "ZZCR_4E", "ZZCR_4MU", "ZZCR_2E2MU",
        "SR_ALL", "SR_XSF", "SR_XDF", "SR_4E", "SR_4MU",
        "SR_2E2MU", "SR_3E1MU", "SR_1E3MU",
    )
    assert not any("XDF" in name for name in state["CATEGORY_METADATA"] if name.startswith("ZZCR"))
    assert "X_isSF" in state["cuts"]["ZZCR"]["expr"]


def test_stream_is_not_flavor_cartesian(load_state):
    state = load_state(category="stream")
    names = tuple(state["CATEGORY_METADATA"])
    assert len(names) == 12
    assert not any("ZEE" in name or "ZMM" in name or "XSF" in name for name in names)


def test_trigger_profile_is_bounded(load_state):
    state = load_state(category="trigger")
    assert len(state["CATEGORY_METADATA"]) == 18
    assert all(item["display_label"] for item in state["CATEGORY_METADATA"].values())
    assert all(
        "triggerFamilyPriority ==" in item["split_expression"]
        for name, item in state["CATEGORY_METADATA"].items()
        if "TRGPRIO" in name
    )
    assert not any(
        item["split_expression"] in ("Trigger_ElMu", "Trigger_sngMu")
        for item in state["CATEGORY_METADATA"].values()
    )


def test_standard_projection_inventory_and_metadata(load_state):
    state = load_state(category="standard")
    metadata = state["CATEGORY_METADATA"]
    assert len(metadata) == 35
    assert sum(name.startswith("DY_") for name in metadata) == 12
    assert sum(name.startswith("ZZCR_") for name in metadata) == 12
    assert sum(name.startswith("SR_") for name in metadata) == 11
    for item in metadata.values():
        assert item["view_type"] in {
            "inclusive", "flavor", "stream", "stream_flavor", "trigger", "debug"
        }
        assert item["partition_family"]
        assert isinstance(item["is_exclusive_within_family"], bool)
        assert isinstance(item["is_overlapping_projection"], bool)
        assert item["diagnostic_purpose"]


def test_detailed_adds_only_curated_sr_stream_x_flavor(load_state):
    standard = load_state(category="standard")
    detailed = load_state(category="detailed")
    added = set(detailed["CATEGORY_METADATA"]) - set(standard["CATEGORY_METADATA"])
    assert added == {
        f"SR_STREAM_{stream}_{flavor}"
        for stream in ("MUONEG", "MUON", "EGAMMA")
        for flavor in ("XSF", "XDF")
    }


def test_debug_requires_explicit_large_plan(load_state):
    with pytest.raises(RuntimeError, match="ALLOW_LARGE_PLAN"):
        load_state(category="debug")
    state = load_state(category="debug", ALLOW_LARGE_PLAN="1")
    assert len(state["CATEGORY_METADATA"]) == 56


def test_full_cut_is_mechanical(load_state):
    state = load_state(category="flavor")
    item = state["CATEGORY_METADATA"]["ZZCR_4E"]
    assert item["full_cut_expression"] == (
        f"({state['preselections']}) && ({item['parent_expression']})"
        f" && ({item['split_expression']})"
    )


def test_selected_pair_low_mass_veto_is_physical_four_lepton_only(load_state):
    state = load_state(category="minimal")
    dy = state["cuts"]["DY"]["expr"]
    zzcr = state["cuts"]["ZZCR"]["expr"]
    sr = state["cuts"]["SR"]["expr"]
    assert "minSelectedPairMass > 12." not in dy
    assert "minSelectedPairMass > 12." in zzcr
    assert "minSelectedPairMass > 12." in sr
    assert "Z0_mass > 12." not in zzcr
    assert "Z0_mass > 12." not in sr
    assert "abs(Z0_mass - 91.1876) < 15." in zzcr
    assert "abs(Z0_mass - 91.1876) < 15." in sr


def test_an2019_238_region_edges_remain_exact(load_state):
    state = load_state(category="minimal")
    zzcr = state["cuts"]["ZZCR"]["expr"]
    sr = state["cuts"]["SR"]["expr"]
    assert "X_isSF && X_mass > 75. && X_mass < 105. && PuppiMET_pt < 35." in zzcr
    assert (
        "X_isSF && X_mass > 10. && X_mass < 65."
        " && PuppiMET_pt > 35. && m4l > 140." in sr
    )
    assert "X_isDF && X_mass > 10. && X_mass < 70. && PuppiMET_pt > 20." in sr


def test_category_budget_fails_closed(load_state):
    with pytest.raises(RuntimeError, match="MAX_CATEGORIES"):
        load_state(category="trigger", MAX_CATEGORIES="3")
