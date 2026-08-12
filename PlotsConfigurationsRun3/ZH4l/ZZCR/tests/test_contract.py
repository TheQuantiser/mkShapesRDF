import runpy
from pathlib import Path


HERE = Path(__file__).resolve().parents[1]


def test_regions_are_physical_and_compact():
    namespace = runpy.run_path(str(HERE / "cuts.py"))
    cuts = namespace["cuts"]
    assert tuple(cuts) == (
        "ZZCR", "ZZCR_4e", "ZZCR_4mu", "ZZCR_2e2mu", "SR_XSF", "SR_XDF"
    )
    assert all("bVeto" in expression for expression in cuts.values())
    assert all("LepSF" not in expression and "TriggerSF" not in expression for expression in cuts.values())


def test_compact_histogram_contract_and_native_runner():
    variables = runpy.run_path(str(HERE / "variables.py"))["variables"]
    source = (HERE / "configuration.py").read_text()
    assert len(variables) == 9
    assert len(variables) * 6 == 54
    assert 'runnerFile = "default"' in source


def test_nominal_weight_has_exact_selected_zx_domain():
    source = (HERE / "samples.py").read_text()
    assert "puWeight*LepSF_ZX*TriggerSF_ZX*bVetoSF" in source
