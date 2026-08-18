from copy import deepcopy

from contract_validation import contract_digest, validate_analysis_contract


def _contract_from_state(state):
    contract = {
        "year": "2024",
        "analysis_pass": "ALL",
        "category_profile": "minimal",
        "histogram_profile": "analysis",
        "sample_profile": "commissioning",
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
            "year": "2024", "analysis_pass": "ALL",
            "category_profile": "minimal", "histogram_profile": "analysis",
            "sample_profile": "commissioning",
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
            cuts=state["cuts"], preselections=state["preselections"],
            variables=state["variables"], category_metadata=state["CATEGORY_METADATA"],
            category_variables=state["CATEGORY_VARIABLES"],
        )
    except AssertionError as exc:
        assert "Z0_mass: fold diverges" in str(exc)
    else:
        raise AssertionError("divergent contract unexpectedly validated")


def test_category_view_metadata_flows_into_contract(load_state):
    state = load_state(category="standard")
    contract = _contract_from_state(state)
    item = contract["categories"]["ZZCR_STREAM_EGAMMA_4E"]
    assert item["view_type"] == "stream_flavor"
    assert item["partition_family"] == "ZZCR:curated_stream_x_topology"
    assert item["is_exclusive_within_family"] is True
    assert item["is_overlapping_projection"] is True
    assert item["diagnostic_purpose"]
    assert item["active_variables"] == state["CATEGORY_VARIABLES"][
        "ZZCR_STREAM_EGAMMA_4E"
    ]
