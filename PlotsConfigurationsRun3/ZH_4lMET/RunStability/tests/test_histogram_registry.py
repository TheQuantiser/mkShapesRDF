import pytest


OBSERVABLES = (
    "Z0_mass",
    "Z0_pt",
    "lZ1_pt",
    "lZ2_pt",
    "lZ1_eta",
    "lZ2_eta",
)


def test_default_public_histogram_matrix_is_exactly_six_by_48(load_state):
    state = load_state()
    categories = state["RUN_STABILITY_CATEGORIES"]

    assert state["RUN_STABILITY_OBSERVABLES"] == OBSERVABLES
    assert tuple(state["variables"]) == OBSERVABLES
    assert len(categories) == 48
    assert tuple(state["CATEGORY_VARIABLES"]) == categories
    assert all(
        tuple(state["CATEGORY_VARIABLES"][category]) == OBSERVABLES
        for category in categories
    )
    assert sum(map(len, state["CATEGORY_VARIABLES"].values())) == 288
    assert len(state["RUN_STABILITY_CONTRACT"]["auxiliary_output_paths"]) == 288
    assert state["RUN_STABILITY_CONTRACT"]["auxiliary_output_paths"] == [
        f"run_stability/{category}/{observable}/histo_DATA"
        for category in categories
        for observable in OBSERVABLES
    ]


def test_runtime_variables_are_exact_json_axis_materializations(load_state):
    state = load_state()
    expected = {
        "Z0_mass": ("Z0_mass", 60, 60.0, 120.0, 1.0, 0),
        "Z0_pt": ("Z0_pt", 20, 0.0, 100.0, 5.0, 2),
        "lZ1_pt": (
            "Alt(Lepton_pt, Alt(Z0_idx, 0, -1), -999.f)",
            13,
            35.0,
            100.0,
            5.0,
            2,
        ),
        "lZ2_pt": (
            "Alt(Lepton_pt, Alt(Z0_idx, 1, -1), -999.f)",
            13,
            35.0,
            100.0,
            5.0,
            2,
        ),
        "lZ1_eta": (
            "Alt(Lepton_eta, Alt(Z0_idx, 0, -1), -999.f)",
            50,
            -2.5,
            2.5,
            0.1,
            0,
        ),
        "lZ2_eta": (
            "Alt(Lepton_eta, Alt(Z0_idx, 1, -1), -999.f)",
            50,
            -2.5,
            2.5,
            0.1,
            0,
        ),
    }
    for name, (expression, bins, low, high, width, fold) in expected.items():
        definition = state["variables"][name]
        edges = definition["range"][0]
        assert definition["name"] == expression
        assert definition["fold"] == fold
        assert len(edges) == bins + 1
        assert edges[0] == low
        assert edges[-1] == high
        assert all(
            abs((right - left) - width) < 1.0e-12
            for left, right in zip(edges, edges[1:])
        )
        contract = state["HISTOGRAM_BINNING_CONTRACT"][name]
        assert contract["source"]["uniform"] == [bins, low, high]
        assert contract["resolved"] == edges
        assert contract["fold"] == fold
        assert contract["strategy"] == "declarative-uniform"


@pytest.mark.parametrize(
    ("setting", "value", "message"),
    (
        (
            "RUN_STABILITY_OBSERVABLES",
            "Z0_mass",
            "exact observable tuple",
        ),
        (
            "RUN_STABILITY_CATEGORIES",
            "DY_ALL",
            "exact category tuple",
        ),
    ),
)
def test_public_matrix_rejects_partial_overrides(load_state, setting, value, message):
    with pytest.raises((RuntimeError, ValueError), match=message):
        load_state(**{setting: value})


@pytest.mark.parametrize("region", ("ZZCR", "SR"))
def test_non_dy_regions_fail_closed(load_state, region):
    with pytest.raises(ValueError, match="RUN_STABILITY_REGION=DY"):
        load_state(RUN_STABILITY_REGION=region)


@pytest.mark.parametrize("analysis_pass", ("ALL", "ZZCR", "SR", "CONTROL"))
def test_non_run_stability_passes_fail_closed(load_state, analysis_pass):
    with pytest.raises(ValueError, match="ANALYSIS_PASS"):
        load_state(analysis_pass=analysis_pass)


def test_unknown_observable_and_category_fail_closed(load_state):
    with pytest.raises(ValueError, match="Invalid RUN_STABILITY_OBSERVABLES"):
        load_state(RUN_STABILITY_OBSERVABLES="not_an_observable")
    with pytest.raises(ValueError, match="Invalid RUN_STABILITY_CATEGORIES"):
        load_state(RUN_STABILITY_CATEGORIES="DY_NOT_A_CATEGORY")
