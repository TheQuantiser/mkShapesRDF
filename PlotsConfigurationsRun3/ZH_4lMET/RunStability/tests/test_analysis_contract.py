from copy import deepcopy

from contract_validation import contract_digest, validate_analysis_contract


def _contract_from_state(state):
    contract = {
        "year": "2024",
        "analysis_pass": "RUN_STABILITY",
        "category_profile": "standard",
        "histogram_profile": "analysis",
        "sample_profile": "presentation",
        "preselection": state["preselections"],
        "categories": {},
        "variables": {},
    }
    for category_id, metadata in state["CATEGORY_METADATA"].items():
        contract["categories"][category_id] = {
            **deepcopy(metadata),
            "active_variables": list(state["CATEGORY_VARIABLES"][category_id]),
        }
    for name, definition in state["variables"].items():
        contract["variables"][name] = {
            "expression": definition["name"],
            "range": deepcopy(definition["range"]),
            "fold": definition.get("fold", 0),
            "categories": list(definition.get("categories", [])),
        }
    contract["contract_sha256"] = contract_digest(contract)
    return contract


def test_contract_matches_executable_runtime(load_state):
    state = load_state()
    contract = _contract_from_state(state)
    assert validate_analysis_contract(
        contract,
        cuts=state["cuts"],
        preselections=state["preselections"],
        variables=state["variables"],
        category_metadata=state["CATEGORY_METADATA"],
        category_variables=state["CATEGORY_VARIABLES"],
        expected_context={
            "year": "2024",
            "analysis_pass": "RUN_STABILITY",
            "category_profile": "standard",
            "histogram_profile": "analysis",
            "sample_profile": "presentation",
        },
    )


def test_contract_divergence_is_detected(load_state):
    state = load_state()
    contract = _contract_from_state(state)
    contract["variables"]["Z0_mass"]["fold"] = 99
    contract["contract_sha256"] = contract_digest(contract)
    try:
        validate_analysis_contract(
            contract,
            cuts=state["cuts"],
            preselections=state["preselections"],
            variables=state["variables"],
            category_metadata=state["CATEGORY_METADATA"],
            category_variables=state["CATEGORY_VARIABLES"],
        )
    except AssertionError as exc:
        assert "Z0_mass: fold diverges" in str(exc)
    else:
        raise AssertionError("divergent contract unexpectedly validated")


def test_category_view_metadata_flows_into_contract(load_state):
    state = load_state()
    contract = _contract_from_state(state)
    item = contract["categories"]["DY_HLT_ISOMU24_ZMM"]
    assert item["view_type"] == "trigger_path"
    assert item["partition_family"] == ("DY:concrete_hlt_path_x_selected_z_flavor")
    assert item["is_exclusive_within_family"] is False
    assert item["is_overlapping_projection"] is True
    assert item["run_stability_luminosity_source"] == "hlt_isomu24"
    assert item["active_variables"] == state["CATEGORY_VARIABLES"]["DY_HLT_ISOMU24_ZMM"]
