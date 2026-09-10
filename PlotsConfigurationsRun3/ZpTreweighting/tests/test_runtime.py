"""Offline checks of site selection and bounded input resolution, not physics."""

from pathlib import Path
import runpy
from unittest.mock import Mock

import pytest


FAMILY = Path(__file__).resolve().parents[1]


def load(monkeypatch, **settings):
    import os

    for name in os.environ:
        if name.startswith("ZPT_"):
            monkeypatch.delenv(name)
    for name, value in settings.items():
        monkeypatch.setenv("ZPT_" + name, str(value))
    return runpy.run_path(
        str(FAMILY / "runtime.py"),
        init_globals={
            "configDir": str(FAMILY / "2024_v15"),
            "filesToExec": [],
            "varsToKeep": [],
        },
    )


@pytest.mark.parametrize(
    "site,packaged,write",
    [("lpc", True, "cmseos.fnal.gov"), ("cern", False, "eoscms.cern.ch")],
)
def test_sites_keep_cern_inputs(monkeypatch, site, packaged, write):
    ns = load(monkeypatch, SITE=site)
    assert ns["condorRuntimePackage"] is packaged
    assert ns["remoteIO"]["xrdReadEndpoint"] == "root://eoscms.cern.ch"
    assert ns["remoteIO"]["xrdWriteEndpoint"] == "root://" + write
    assert ns["outputFolder"].startswith(str(FAMILY))


def test_selection_bounds_discovery_and_preserves_weights(monkeypatch):
    ns = load(monkeypatch, SAMPLE="DY", DATASET="muons", LIMIT_FILES=1, FILES_PER_JOB=1)
    catalog = {
        "DY": {
            "name": [("electrons", []), ("muons", [], "specialWeight")],
            "weight": "nominal",
            "FilesPerJob": 10,
        },
        "DATA": {"name": [("data", [])]},
    }
    search = Mock()
    search.searchFiles.return_value = [
        "root://host//first.root",
        "root://host//second.root",
    ]
    result = ns["resolve_samples"](catalog, {"muons": "/store/mc"}, search)
    search.searchFiles.assert_called_once_with(
        "/store/mc",
        "muons",
        redirector="root://eoscms.cern.ch",
        read_redirector="root://eoscms.cern.ch",
    )
    assert result == {
        "DY": {
            "name": [("muons", ["root://host//first.root"], "specialWeight")],
            "weight": "nominal",
            "FilesPerJob": 1,
        }
    }


def test_pinned_input_skips_discovery(monkeypatch):
    ns = load(
        monkeypatch, SAMPLE="DY", DATASET="muons", INPUT_FILE="root://host//fixed.root"
    )
    search = Mock()
    catalog = {"DY": {"name": [("muons", [])]}}
    result = ns["resolve_samples"](catalog, {"muons": "/store/mc"}, search)
    search.searchFiles.assert_not_called()
    assert result["DY"]["name"] == [("muons", ["root://host//fixed.root"])]


@pytest.mark.parametrize(
    "settings",
    [
        {"SITE": "typo"},
        {"LIMIT_FILES": 0},
        {"SYSTEMATICS": "yes"},
        {"DATASET": "muons"},
        {"SAMPLE": "DY", "INPUT_FILE": "file.root"},
        {"APPLY_REWEIGHT": 1},
    ],
)
def test_invalid_settings_fail_before_discovery(monkeypatch, settings):
    with pytest.raises(ValueError):
        load(monkeypatch, **settings)


def test_unknown_or_empty_inputs_fail(monkeypatch):
    ns = load(monkeypatch, SAMPLE="DY")
    search = Mock()
    with pytest.raises(ValueError, match="Unknown ZPT_SAMPLE"):
        ns["resolve_samples"]({"DATA": {}}, {}, search)
    search.searchFiles.return_value = []
    with pytest.raises(FileNotFoundError, match="DY/muons"):
        ns["resolve_samples"](
            {"DY": {"name": [("muons", [])]}}, {"muons": "/store/mc"}, search
        )


@pytest.mark.parametrize("variant", ["2022_v12", "2022_v12_incl"])
@pytest.mark.parametrize("apply", [0, 1])
def test_low_mass_dy_reweight_is_applied_exactly_once(monkeypatch, variant, apply):
    ns = load(
        monkeypatch,
        SAMPLE="DY",
        DATASET="DYto2L-2Jets_MLL-10to50",
        INPUT_FILE="root://host//fixed.root",
        APPLY_REWEIGHT=apply,
        REWEIGHT_JSON=FAMILY / variant / "dyZpTrw.json",
    )
    path = FAMILY / variant / "samples.py"
    exec(compile(path.read_text(), str(path), "exec"), ns)
    sample = ns["samples"]["DY"]
    weights = sample["weight"] + "*".join(
        item[2] for item in sample["name"] if len(item) > 2
    )
    assert weights.count("DY_NLO_ZpTrw") == apply
