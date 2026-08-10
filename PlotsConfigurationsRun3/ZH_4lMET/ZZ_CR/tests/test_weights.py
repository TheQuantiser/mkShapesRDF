from pathlib import Path
import runpy


CONFIG_DIR = Path(__file__).resolve().parents[1]


def test_exact_weight_contract(load_state):
    state = load_state(category="flavor")
    metadata = state["CATEGORY_METADATA"]
    for name, item in metadata.items():
        if name.startswith("DY_"):
            assert item["category_weight_factor"] == (
                "SelectedLeptonSF_Z*TriggerSF_Z"
            )
            assert "TriggerSF_ZX" not in item["full_nominal_mc_weight"]
            assert item["full_nominal_mc_weight"].count("BTagVetoSF") == 0
    for name, item in metadata.items():
        if name.startswith(("ZZCR_", "SR_")):
            assert item["category_weight_factor"] == (
                "SelectedLeptonSF_ZX*TriggerSF_ZX*BTagVetoSF"
            )
            assert item["full_nominal_mc_weight"].count("BTagVetoSF") == 1
        assert "TriggerSF_event" not in item["full_nominal_mc_weight"]
        assert "no MC scale factors" in item["data_weight_rule"]


def test_dy_trigger_sf_alias_uses_exact_selected_z_pair(monkeypatch):
    monkeypatch.setenv("YEAR", "2024")
    monkeypatch.setenv("ANALYSIS_PASS", "ALL")
    state = runpy.run_path(
        str(CONFIG_DIR / "aliases.py"),
        init_globals={"CONFIG_DIR": str(CONFIG_DIR), "samples": {}},
    )
    expression = state["aliases"]["TriggerResult_Z"]["expr"]
    assert "SelectedTrigger::selectedPairResult(" in expression
    assert "ProductionLeptonPt, Lepton_eta, Lepton_phi, ProductionLeptonPdgId" in expression
    assert ", Z0_idx, PV_npvsGood," in expression

    wrapper = (CONFIG_DIR / "macros" / "selected_trigger_wrappers.cc").read_text()
    assert "{idx[0], idx[1]}" in wrapper
    assert "sortByPt(cpt, ceta, cphi, cid);\n  return exactTwo(" in wrapper


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
