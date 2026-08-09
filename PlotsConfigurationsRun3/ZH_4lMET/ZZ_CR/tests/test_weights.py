def test_exact_weight_contract(load_state):
    state = load_state(category="flavor")
    metadata = state["CATEGORY_METADATA"]
    for name in ("DY_ALL", "DY_ZEE", "DY_ZMM"):
        assert metadata[name]["category_weight_factor"] == "SelectedLeptonSF_Z"
    for name, item in metadata.items():
        if name.startswith(("ZZCR_", "SR_")):
            assert item["category_weight_factor"] == "SelectedLeptonSF_ZX*BTagVetoSF"
        assert "TriggerSF_event" in item["full_nominal_mc_weight"]
        assert "no MC scale factors" in item["data_weight_rule"]


def test_runner_mapping_equals_registry(load_state):
    state = load_state()
    try:
        from zz_cr_runner import RunAnalysis
    except ModuleNotFoundError as exc:
        if exc.name == "ROOT":
            return
        raise
    resolved = RunAnalysis.resolve_cut_weight_factors({"cuts": state["cuts"]})
    assert resolved == {
        category_id: item["category_weight_factor"]
        for category_id, item in state["CATEGORY_METADATA"].items()
    }
