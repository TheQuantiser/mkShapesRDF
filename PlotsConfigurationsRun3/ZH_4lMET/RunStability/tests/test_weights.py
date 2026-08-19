from pathlib import Path
import runpy


CONFIG_DIR = Path(__file__).resolve().parents[1]


def test_exact_weight_contract(load_state):
    state = load_state()
    metadata = state["CATEGORY_METADATA"]
    assert metadata
    selected_pass = state["analysis_pass"]()
    correction = state["selected_correction_weight"](selected_pass)
    _, selected_year, _ = state["load_selected_year"]()
    mc_weight = selected_year["mc"]["common_weight"] + "*" + correction

    assert correction == "puWeight*SelectedLeptonSF_Z*TriggerSF_Z"
    assert mc_weight == (
        "XSWeight*METFilter_Common*puWeight*SelectedLeptonSF_Z*TriggerSF_Z"
    )
    assert selected_year["data"]["common_weight"] == "METFilter_DATA"
    for name, item in metadata.items():
        assert name.startswith("DY_")
        assert item["category_weight_factor"] == "1.f"
        assert "sample_base_mc_weight" not in item
        assert "full_nominal_mc_weight" not in item
        assert "no MC scale factors" in item["data_weight_rule"]


def test_dy_trigger_sf_alias_uses_exact_selected_z_pair(load_state):
    compiled = load_state()
    state = runpy.run_path(
        str(CONFIG_DIR / "aliases.py"),
        init_globals={**compiled, "samples": {}},
    )
    expression = state["aliases"]["TriggerResult_Z"]["expr"]
    assert "SelectedTrigger::selectedPairResult(" in expression
    assert (
        "ProductionLeptonPt, Lepton_eta, Lepton_phi, ProductionLeptonPdgId"
        in expression
    )
    assert ", Z0_idx, PV_npvsGood," in expression

    wrapper = (CONFIG_DIR / "macros" / "selected_trigger_wrappers.cc").read_text()
    assert "{idx[0], idx[1]}" in wrapper
    assert "sortByPt(cpt, ceta, cphi, cid);\n  return exactTwo(" in wrapper


def test_runner_mapping_equals_registry(load_state):
    state = load_state()
    try:
        from run_stability_runner import RunAnalysis
    except ModuleNotFoundError as exc:
        if exc.name == "ROOT":
            return
        raise
    resolved = RunAnalysis.resolve_cut_weight_factors({"cuts": state["cuts"]})
    assert resolved == {
        category_id: item["category_weight_factor"]
        for category_id, item in state["CATEGORY_METADATA"].items()
    }
