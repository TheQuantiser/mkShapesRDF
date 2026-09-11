"""Compile the real example without reading or discovering event files."""

from pathlib import Path
import sys

import pytest

from mkShapesRDF.shapeAnalysis.ConfigLib import ConfigLib
from mkShapesRDF.lib.search_files import SearchFiles

FAMILY = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(FAMILY))
from common.naming import public_name  # noqa: E402


@pytest.mark.parametrize("mode", ["histograms", "trees", "both"])
def test_example_compiles_plain_config_with_bounded_inputs(monkeypatch, tmp_path, mode):
    monkeypatch.setenv("ERA", "2024")
    monkeypatch.delenv("YEAR", raising=False)
    monkeypatch.setenv("ENABLE_SYSTEMATICS", "0")
    monkeypatch.setenv("ZH4L_OUTPUT_MODE", mode)
    monkeypatch.setenv("SAMPLE_FILTER", "ZZ,ZH_Zto2L_Hto2Wto2L2Nu_M125")
    monkeypatch.setenv("LIMIT_FILES_PER_SAMPLE", "1")

    def forbid_discovery(*args, **kwargs):
        raise AssertionError("The example must use its pinned input list")

    monkeypatch.setattr(SearchFiles, "searchFiles", forbid_discovery)
    namespace = {}
    leaf = FAMILY / "Example"
    ConfigLib.loadConfig([str(leaf / "configuration.py")], namespace)
    ConfigLib.loadConfig(
        [str(leaf / name) for name in namespace["filesToExec"]],
        namespace,
        namespace["imports"],
    )
    config = ConfigLib.createConfigDict(namespace["varsToKeep"], namespace)
    path = str(tmp_path / "config")
    ConfigLib.dumpConfigDict(config, path)
    reopened = ConfigLib.loadPickle(path + ".pkl", {})
    assert reopened["samples"] == config["samples"]
    assert set(config["samples"]) == {"ZZ", "ZH_Zto2L_Hto2Wto2L2Nu_M125"}
    assert all(
        len(sample["name"]) == 1 and len(sample["name"][0][1]) == 1
        for sample in config["samples"].values()
    )
    assert config["nuisances"] == {}
    assert (
        set(config["plot"]["plot"])
        == set(config["samples"])
        == set(config["structure"])
    )
    assert len(config["cuts"]["cuts"]) == 5
    assert len(config["variables"]) == {"histograms": 9, "trees": 2, "both": 11}[mode]
    for name in config["aliases"]:
        assert public_name(name) == name
    if mode != "trees":
        weights = config["variables"]["x_mass"]["regionWeights"]
        assert weights["four_lepton"] == "weight_lepton_trigger"
        assert weights["b_veto"] == weights["zz_control"] == "weight_nominal"
    if mode == "histograms":
        assert "accepted_jet_tag" not in config["aliases"]
    assert "GenPart" not in repr(config["aliases"])


def test_example_rejects_an_era_without_pinned_inputs(monkeypatch):
    monkeypatch.setenv("ERA", "2023")
    monkeypatch.delenv("YEAR", raising=False)
    with pytest.raises(ValueError, match="pins 2024"):
        ConfigLib.loadConfig([str(FAMILY / "Example/configuration.py")], {})
