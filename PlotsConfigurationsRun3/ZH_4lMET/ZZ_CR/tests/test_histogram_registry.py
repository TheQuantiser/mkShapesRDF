def test_default_sparse_plan(load_state):
    state = load_state()
    assert len(state["VARIABLE_REGISTRY"]) == 509
    assert len(state["variables"]) == 53
    assert sum(map(len, state["CATEGORY_VARIABLES"].values())) == 125
    assert "X_mass" not in state["CATEGORY_VARIABLES"]["DY_ALL"]
    assert "X_mass" in state["CATEGORY_VARIABLES"]["ZZCR_ALL"]


def test_activation_does_not_change_definition_hashes(load_state):
    analysis = load_state(histogram="analysis")
    all_detail = load_state(histogram="all", ALLOW_LARGE_PLAN="1")
    assert analysis["VARIABLE_REGISTRY_HASHES"] == all_detail["VARIABLE_REGISTRY_HASHES"]
    assert analysis["VARIABLE_REGISTRY"]["Z0_mass"]["range"] == all_detail["variables"]["Z0_mass"]["range"]


def test_exact_include_and_exclude(load_state):
    state = load_state(
        VARIABLE_INCLUDE="Z0_mass,X_mass,PuppiMET_pt",
        VARIABLE_EXCLUDE="PuppiMET_pt",
    )
    assert tuple(state["variables"]) == ("Z0_mass", "X_mass")
    assert state["CATEGORY_VARIABLES"]["DY_ALL"] == ["Z0_mass"]
    assert state["CATEGORY_VARIABLES"]["ZZCR_ALL"] == ["Z0_mass", "X_mass"]
    assert "PuppiMET_pt" in state["VARIABLE_REGISTRY"]


def test_action_budget_fails_closed(load_state):
    import pytest
    with pytest.raises(RuntimeError, match="MAX_HISTOGRAM_ACTIONS"):
        load_state(MAX_HISTOGRAM_ACTIONS="10")
