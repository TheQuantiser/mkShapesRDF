from pathlib import Path
import runpy

import pytest


CONFIG_DIR = Path(__file__).resolve().parents[1]


def _load(monkeypatch, tmp_path, **overrides):
    defaults = {
        "YEAR": "2024",
        "ANALYSIS_PASS": "RUN_STABILITY",
        "RUN_STABILITY_PRODUCTION_PROFILE": "dy",
        "SELECTION_PROFILE": "dy",
        "RUN_STABILITY_REGION": "DY",
        "RUN_STABILITY_OBSERVABLES": "configured",
        "CATEGORY_PROFILE": "standard",
        "HISTOGRAM_PROFILE": "analysis",
        "SAMPLE_PROFILE": "presentation",
        "ENABLE_SYSTEMATICS": "0",
        "EXECUTION_PROFILE": "local",
        "OUTPUT_MODE": "local",
    }
    defaults.update({key: str(value) for key, value in overrides.items()})
    for key, value in defaults.items():
        monkeypatch.setenv(key, value)
    monkeypatch.chdir(tmp_path)
    return runpy.run_path(
        str(CONFIG_DIR / "configuration.py"),
        init_globals={"CONFIG_DIR": str(CONFIG_DIR)},
    )


def test_configuration_defaults_to_single_public_contract(monkeypatch, tmp_path):
    state = _load(monkeypatch, tmp_path)
    profile = state["SELECTED_RUN_STABILITY_PRODUCTION_PROFILE"]
    assert state["RUN_STABILITY_PRODUCTION_PROFILE"] == "dy"
    assert state["ANALYSIS_PASS"] == "RUN_STABILITY"
    assert state["RUN_STABILITY_REGION"] == "DY"
    assert state["SELECTION_PROFILE"] == "dy"
    assert state["RUN_STABILITY_OBSERVABLE_SELECTOR"] == "configured"
    assert tuple(profile["observables"]) == (
        "Z0_mass",
        "Z0_pt",
        "lZ1_pt",
        "lZ2_pt",
        "lZ1_eta",
        "lZ2_eta",
    )
    assert len(profile["categories"]) == 48
    assert state["filesToExec"] == [
        "year_config.py",
        "selection_config.py",
        "category_config.py",
        "samples.py",
        "run_stability_config.py",
        "aliases.py",
        "cuts.py",
        "variables.py",
        "plot.py",
        "nuisances_nominal.py",
        "structure.py",
        "write_contract.py",
        "worker_payload.py",
    ]


@pytest.mark.parametrize("analysis_pass", ("ALL", "ZZCR", "SR", "CONTROL"))
def test_configuration_rejects_clone_era_analysis_passes(
    monkeypatch, tmp_path, analysis_pass
):
    with pytest.raises(ValueError, match="requires ANALYSIS_PASS=RUN_STABILITY"):
        _load(monkeypatch, tmp_path, ANALYSIS_PASS=analysis_pass)
