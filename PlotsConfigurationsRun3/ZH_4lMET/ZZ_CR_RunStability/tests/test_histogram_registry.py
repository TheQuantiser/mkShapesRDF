def test_default_sparse_plan(load_state):
    state = load_state()
    assert len(state["VARIABLE_REGISTRY"]) == 510
    assert len(state["variables"]) == 54
    assert sum(map(len, state["CATEGORY_VARIABLES"].values())) == 150
    assert "X_mass" not in state["CATEGORY_VARIABLES"]["DY_ALL"]
    assert "TriggerSF_Z" in state["CATEGORY_VARIABLES"]["DY_ALL"]
    assert "TriggerSF_ZX" not in state["CATEGORY_VARIABLES"]["DY_ALL"]
    assert (
        state["CATEGORY_VARIABLES"]["DY_ENRICHED"]
        == state["CATEGORY_VARIABLES"]["DY_ALL"]
    )
    assert "X_mass" in state["CATEGORY_VARIABLES"]["ZZCR_ALL"]
    assert "TriggerSF_ZX" in state["CATEGORY_VARIABLES"]["ZZCR_ALL"]
    assert "TriggerSF_Z" not in state["CATEGORY_VARIABLES"]["ZZCR_ALL"]


def test_activation_does_not_change_definition_hashes(load_state):
    analysis = load_state(histogram="analysis")
    all_detail = load_state(histogram="all", ALLOW_LARGE_PLAN="1")
    assert (
        analysis["VARIABLE_REGISTRY_HASHES"] == all_detail["VARIABLE_REGISTRY_HASHES"]
    )
    assert (
        analysis["VARIABLE_REGISTRY"]["Z0_mass"]["range"]
        == all_detail["variables"]["Z0_mass"]["range"]
    )


def test_requested_presentation_binning_and_flow_folding(load_state):
    registry = load_state()["VARIABLE_REGISTRY"]

    expected_edges = {
        "Z0_mass": [30, 40, 60, 80, 85, 90, 95, 100, 120],
        "X_mass": [30, 40, 60, 80, 85, 90, 95, 100, 120],
        "PuppiMET_pt": [0, 10, 20, 30, 40, 50, 80, 100, 120],
        "Z0_pt": [0, 2, 4, 6, 8, 10, 15, 20, 25, 30, 35, 40, 50, 60, 70, 80, 100, 120],
        "X_pt": [0, 2, 4, 6, 8, 10, 15, 20, 25, 30, 35, 40, 50, 60, 70, 80, 100, 120],
        "lZ1_pt": [0, 5, 10, 15, 20, 25, 30, 40, 50, 80, 100, 120],
        "lZ2_pt": [0, 5, 10, 15, 20, 25, 30, 40, 50, 80, 100, 120],
        "lX1_pt": [0, 5, 10, 15, 20, 25, 30, 40, 50, 80, 100, 120],
        "lX2_pt": [0, 5, 10, 15, 20, 25, 30, 40, 50, 80, 100, 120],
        "CleanJet_pt_0": [0, 10, 20, 30, 40, 50, 70, 90, 100],
        "CleanJet_pt_1": [0, 10, 20, 30, 40, 50, 70, 90, 100],
        "nCleanJet": [-0.5, 0.5, 1.5, 2.5, 3.5, 4.5, 5.5, 6.5, 7.5],
        "nLepton": [1.5, 2.5, 3.5, 4.5, 5.5, 6.5, 7.5, 8.5],
    }
    for name, edges in expected_edges.items():
        assert registry[name]["range"] == ([float(edge) for edge in edges],)
        assert registry[name]["fold"] == 3

    for name in ("dPhi_MET_Z", "dPhi_MET_X", "dPhi_MET_ZplusX", "dPhi_lZ1_lZ2"):
        assert registry[name]["range"] == (8, 0.0, 3.2)
        assert registry[name]["fold"] == 3

    # Ordinary azimuths remain signed; only absolute delta-phi is zero-based.
    assert registry["Z0_phi"]["range"] == (16, -3.2, 3.2)


def test_exact_include_and_exclude(load_state):
    state = load_state(
        VARIABLE_INCLUDE="Z0_mass,X_mass,PuppiMET_pt",
        VARIABLE_EXCLUDE="PuppiMET_pt",
    )
    assert tuple(state["variables"]) == ("Z0_mass", "X_mass")
    assert state["CATEGORY_VARIABLES"]["DY_ALL"] == ["Z0_mass"]
    assert state["CATEGORY_VARIABLES"]["DY_ENRICHED"] == ["Z0_mass"]
    assert state["CATEGORY_VARIABLES"]["ZZCR_ALL"] == ["Z0_mass", "X_mass"]
    assert "PuppiMET_pt" in state["VARIABLE_REGISTRY"]


def test_action_budget_fails_closed(load_state):
    import pytest

    with pytest.raises(RuntimeError, match="MAX_HISTOGRAM_ACTIONS"):
        load_state(MAX_HISTOGRAM_ACTIONS="10")


def test_standard_view_aware_sparse_policy(load_state):
    state = load_state(category="standard")
    variables = state["CATEGORY_VARIABLES"]
    assert sum(map(len, variables.values())) == 1043
    assert len(variables["DY_ALL"]) == 25
    assert variables["DY_ENRICHED"] == variables["DY_ALL"]
    assert len(variables["ZZCR_ALL"]) == 50
    assert len(variables["SR_ALL"]) == 50
    assert len(variables["DY_ZEE"]) == 19
    assert len(variables["DY_STREAM_MUON"]) == 17
    assert len(variables["DY_STREAM_MUON_ZEE"]) == 15
    for name in tuple(variables):
        if (
            name.startswith("DY_")
            and name not in ("DY_ALL", "DY_ENRICHED")
            and not name.startswith("DY_ENRICHED_")
        ):
            enriched_name = name.replace("DY_", "DY_ENRICHED_", 1)
            assert variables[enriched_name] == variables[name]
    assert len(variables["ZZCR_4E"]) == 31
    assert len(variables["ZZCR_STREAM_MUON"]) == 25
    assert len(variables["ZZCR_STREAM_EGAMMA_4E"]) == 15
    assert "recoil_upar" in variables["ZZCR_ALL"]
    assert "recoil_upar" not in variables["ZZCR_4E"]
    assert "CleanJet_pt_0" in variables["SR_3E1MU"]
    assert "CleanJet_pt_0" not in variables["SR_STREAM_MUON"]


def test_profile_action_counts(load_state):
    expected = {
        "minimal": 150,
        "standard": 1043,
        "flavor": 536,
        "stream": 402,
        "trigger": 570,
        "detailed": 1133,
    }
    for profile, actions in expected.items():
        state = load_state(category=profile)
        assert sum(map(len, state["CATEGORY_VARIABLES"].values())) == actions


def test_run_stability_books_every_requested_observable_in_every_category(load_state):
    state = load_state(category="standard", analysis_pass="RUN_STABILITY")
    expected = set(state["RUN_STABILITY_OBSERVABLES"])
    assert set(state["CATEGORY_VARIABLES"]) == set(state["RUN_STABILITY_CATEGORIES"])
    assert all(
        expected <= set(state["CATEGORY_VARIABLES"][category])
        for category in state["RUN_STABILITY_CATEGORIES"]
    )
    assert (
        sum(
            len(expected & set(state["CATEGORY_VARIABLES"][category]))
            for category in state["RUN_STABILITY_CATEGORIES"]
        )
        == 1200
    )


def test_dy_run_stability_books_complete_exact_matrix(load_state):
    state = load_state(
        category="standard",
        analysis_pass="RUN_STABILITY",
        RUN_STABILITY_REGION="DY",
        RUN_STABILITY_OBSERVABLES="all_dy",
        RUN_STABILITY_CATEGORIES="all_dy",
    )
    assert state["RUN_STABILITY_CONTRACT"]["target_region"] == "DY"
    assert len(state["RUN_STABILITY_CATEGORIES"]) == 48
    assert len(state["RUN_STABILITY_OBSERVABLES"]) == 25
    assert tuple(state["variables"]) == state["RUN_STABILITY_OBSERVABLES"]
    assert tuple(state["CATEGORY_VARIABLES"]) == state["RUN_STABILITY_CATEGORIES"]
    assert all(
        tuple(state["CATEGORY_VARIABLES"][category])
        == state["RUN_STABILITY_OBSERVABLES"]
        for category in state["RUN_STABILITY_CATEGORIES"]
    )
    assert sum(map(len, state["CATEGORY_VARIABLES"].values())) == 1200
    assert len(state["RUN_STABILITY_CONTRACT"]["auxiliary_output_paths"]) == 1200


def test_dy_run_stability_accepts_exact_observable_and_category_subsets(load_state):
    state = load_state(
        category="standard",
        analysis_pass="RUN_STABILITY",
        RUN_STABILITY_REGION="DY",
        RUN_STABILITY_OBSERVABLES="Z0_mass,lZ1_pt,Z0_eta",
        RUN_STABILITY_CATEGORIES="DY_ALL,DY_ZEE",
    )
    assert state["RUN_STABILITY_OBSERVABLES"] == ("Z0_mass", "lZ1_pt", "Z0_eta")
    assert state["RUN_STABILITY_CATEGORIES"] == ("DY_ALL", "DY_ZEE")
    assert tuple(state["variables"]) == state["RUN_STABILITY_OBSERVABLES"]
    assert tuple(state["CATEGORY_VARIABLES"]) == state["RUN_STABILITY_CATEGORIES"]
    assert all(len(names) == 3 for names in state["CATEGORY_VARIABLES"].values())


def test_dy_run_stability_rejects_non_dy_observable(load_state):
    import pytest

    with pytest.raises(ValueError, match="Invalid RUN_STABILITY_OBSERVABLES"):
        load_state(
            category="standard",
            analysis_pass="RUN_STABILITY",
            RUN_STABILITY_REGION="DY",
            RUN_STABILITY_OBSERVABLES="X_mass",
            RUN_STABILITY_CATEGORIES="DY_ALL",
        )


def test_dy_run_stability_rejects_duplicate_selectors(load_state):
    import pytest

    with pytest.raises(ValueError, match="Duplicate RUN_STABILITY_OBSERVABLES"):
        load_state(
            category="standard",
            analysis_pass="RUN_STABILITY",
            RUN_STABILITY_REGION="DY",
            RUN_STABILITY_OBSERVABLES="Z0_mass,Z0_mass",
            RUN_STABILITY_CATEGORIES="DY_ALL",
        )


def test_run_stability_rejects_non_dy_region(load_state):
    import pytest

    with pytest.raises(ValueError, match="only RUN_STABILITY_REGION=DY"):
        load_state(
            category="standard",
            analysis_pass="RUN_STABILITY",
            RUN_STABILITY_REGION="ZZCR",
        )
