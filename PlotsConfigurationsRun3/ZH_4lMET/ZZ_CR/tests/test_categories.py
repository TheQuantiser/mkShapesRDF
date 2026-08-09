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
        "SR_ALL", "SR_XSF", "SR_XDF",
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


def test_full_cut_is_mechanical(load_state):
    state = load_state(category="flavor")
    item = state["CATEGORY_METADATA"]["ZZCR_4E"]
    assert item["full_cut_expression"] == (
        f"({state['preselections']}) && ({item['parent_expression']})"
        f" && ({item['split_expression']})"
    )


def test_category_budget_fails_closed(load_state):
    with pytest.raises(RuntimeError, match="MAX_CATEGORIES"):
        load_state(category="trigger", MAX_CATEGORIES="3")
