from pathlib import Path
import re
import runpy

import pytest


CONFIG_DIR = Path(__file__).resolve().parents[1]


def _load_configuration(monkeypatch, tmp_path, **overrides):
    for name in (
        "ANALYSIS_PASS",
        "CATEGORY_PROFILE",
        "HISTOGRAM_PROFILE",
        "SAMPLE_PROFILE",
        "ENABLE_SYSTEMATICS",
        "RUN_STABILITY_REGION",
        "RUN_STABILITY_OBSERVABLES",
        "RUN_STABILITY_CATEGORIES",
        "SELECTION_PROFILE",
        "RUN_STABILITY_PRODUCTION_PROFILE",
        "EXECUTION_PROFILE",
        "INPUT_ACCESS_MODE",
        "OUTPUT_MODE",
        "JOB_CAMPAIGN",
        "PRODUCTION_CAMPAIGN",
    ):
        monkeypatch.delenv(name, raising=False)
    values = {
        "YEAR": "2024",
        "ANALYSIS_PASS": "RUN_STABILITY",
        "CATEGORY_PROFILE": "standard",
        "HISTOGRAM_PROFILE": "analysis",
        "SAMPLE_PROFILE": "presentation",
        "ENABLE_SYSTEMATICS": "0",
        "RUN_STABILITY_REGION": "DY",
        "RUN_STABILITY_PRODUCTION_PROFILE": "dy",
        "EXECUTION_PROFILE": "local",
        "OUTPUT_MODE": "local",
    }
    values.update({name: str(value) for name, value in overrides.items()})
    for name, value in values.items():
        monkeypatch.setenv(name, value)
    tmp_path.mkdir(parents=True, exist_ok=True)
    monkeypatch.chdir(tmp_path)
    return runpy.run_path(
        str(CONFIG_DIR / "configuration.py"),
        init_globals={"CONFIG_DIR": str(CONFIG_DIR)},
    )


def _focused_state(monkeypatch, tmp_path):
    probe = _load_configuration(monkeypatch, tmp_path / "probe")
    focused = probe["_CANONICAL_RUN_STABILITY_IDENTITY"]
    return _load_configuration(
        monkeypatch,
        tmp_path / "focused",
        RUN_STABILITY_OBSERVABLES=focused["observable_selector"],
        RUN_STABILITY_CATEGORIES=focused["category_selector"],
        SELECTION_PROFILE=focused["selection_profile"],
        JOB_CAMPAIGN="focused_tag_test",
        PRODUCTION_CAMPAIGN="focused_tag_test_remote",
    )


def test_focused_tag_is_concise_semantic_and_utc(monkeypatch, tmp_path):
    state = _focused_state(monkeypatch, tmp_path)
    tag = state["tag"]
    contract = state["RUN_STABILITY_TAG_CONTRACT"]

    assert re.fullmatch(
        r"DYRS_2024_pt35_m60to120_obs6_cat48-be24d1ac_" r"[0-9]{8}T[0-9]{12}Z",
        tag,
    )
    assert contract["tag"] == tag
    assert contract["timestamp_utc_compact"] == tag.rsplit("_", 1)[1]
    assert contract["observables"] == [
        "Z0_mass",
        "Z0_pt",
        "lZ1_pt",
        "lZ2_pt",
        "lZ1_eta",
        "lZ2_eta",
    ]
    assert len(contract["categories"]) == 48
    assert contract["category_selector_sha256"].startswith("be24d1ac")
    assert contract["ordered_2l_pt_mins_gev"] == [35.0, 35.0]
    assert contract["mass_window_gev"] == [60.0, 120.0]
    assert "RUN_STABILITY_TAG_CONTRACT" in state["varsToKeep"]
    assert "write_contract.py" in state["filesToExec"]
    assert "worker_payload.py" in state["filesToExec"]


def test_focused_tags_do_not_collide_with_microsecond_timestamp(monkeypatch, tmp_path):
    first = _focused_state(monkeypatch, tmp_path / "first")["tag"]
    second = _focused_state(monkeypatch, tmp_path / "second")["tag"]
    assert first != second


def test_focused_tag_and_generated_paths_remain_bounded(monkeypatch, tmp_path):
    state = _focused_state(monkeypatch, tmp_path)
    assert len(state["tag"]) <= 96
    assert len(Path(state["jobControlDir"]).as_posix()) <= 180
    assert len(state["outputFile"]) <= 128


def test_focused_identity_wires_pickle_contract_and_worker_payload(
    monkeypatch, tmp_path
):
    state = _focused_state(monkeypatch, tmp_path)
    assert "RUN_STABILITY_TAG_CONTRACT" in state["varsToKeep"]
    assert state["filesToExec"].index("write_contract.py") < state["filesToExec"].index(
        "worker_payload.py"
    )

    contract_source = (CONFIG_DIR / "write_contract.py").read_text()
    worker_source = (CONFIG_DIR / "worker_payload.py").read_text()
    assert 'contract["tag_identity"] = tag_identity' in contract_source
    assert '"runStabilityTagIdentity": RUN_STABILITY_TAG_CONTRACT' in worker_source
    assert '"analysisContract": analysisContract' in worker_source


def test_semantic_category_drift_fails_closed(monkeypatch, tmp_path):
    probe = _load_configuration(monkeypatch, tmp_path / "probe_drift")
    focused = probe["_CANONICAL_RUN_STABILITY_IDENTITY"]
    categories = list(focused["categories"])
    categories[0], categories[1] = categories[1], categories[0]
    with pytest.raises(ValueError, match="exact category tuple"):
        _load_configuration(
            monkeypatch,
            tmp_path / "drift",
            RUN_STABILITY_OBSERVABLES=focused["observable_selector"],
            RUN_STABILITY_CATEGORIES=",".join(categories),
            SELECTION_PROFILE=focused["selection_profile"],
        )
