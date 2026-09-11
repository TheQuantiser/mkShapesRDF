"""Check the executable alias/output vocabulary, including generated names."""

from pathlib import Path
import re

import pytest

from mkShapesRDF.shapeAnalysis.ConfigLib import ConfigLib
from common.naming import LEGACY_COLUMN_NAMES, public_name


FAMILY = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize(
    "leaf,systematics",
    [("ZZCR", "0"), ("ZZCR", "1"), ("Pairing", "0"), ("Closure", "0")],
)
def test_all_leaf_columns_and_expressions_use_one_vocabulary(
    monkeypatch, leaf, systematics
):
    monkeypatch.setenv("ERA", "2024")
    monkeypatch.delenv("YEAR", raising=False)
    monkeypatch.setenv("ENABLE_SYSTEMATICS", systematics)
    monkeypatch.setenv(
        "ZH4L_OUTPUT_MODE", "histograms" if systematics == "1" else "both"
    )
    namespace = {}
    directory = FAMILY / leaf
    ConfigLib.loadConfig([str(directory / "configuration.py")], namespace)
    namespace.update(
        samples={"MC": {"name": [], "weight": "1"}},
        makeMCFriendDirectory=lambda suffix: "root://eoscms.cern.ch//store/" + suffix,
    )
    ConfigLib.loadConfig(
        [
            str(directory / name)
            for name in ("aliases.py", "cuts.py", "variables.py", "nuisances.py")
        ],
        namespace,
        namespace["imports"],
    )
    for name in namespace["aliases"]:
        if name in {"genWeight", "Jet_hadronFlavour"} or name.startswith("Lepton_"):
            continue  # Explicit upstream DATA branch substitutes.
        assert public_name(name) == name
    expressions = [cfg.get("expr", "") for cfg in namespace["aliases"].values()]
    for cfg in namespace["variables"].values():
        expressions.extend(
            cfg.get(key, "")
            for key in ("name", "weight", "studyWeight", "studyWeightFactor")
        )
        expressions.extend(cfg.get("tree", {}).values())
        for field, expression in cfg.get("tree", {}).items():
            if field != expression:  # Retained native branch spelling is authoritative.
                public_name(field)
    for old in LEGACY_COLUMN_NAMES:
        pattern = re.compile(r"(?<![\w.:])" + re.escape(old) + r"(?!\w)")
        # A colon between histogram axes is a separator; C++ scope/member names
        # are protected while individual axes are checked independently.
        for expression in expressions:
            for axis in re.split(r"(?<!:):(?!:)", expression):
                assert not pattern.search(axis), (leaf, old, expression)


def test_explicit_region_inheritance_preserves_s0_veto_correction():
    import runpy

    namespace = runpy.run_path(str(FAMILY / "Closure/study_config.py"))
    factor = namespace["nominal_factor"]
    assert "sf_b_veto" in factor("S0_ZZCR")
    for child in ("S0_ZZCR_4E", "S0_ZZCR_4MU", "S0_ZZCR_2E2MU"):
        assert factor(child) == factor("S0_ZZCR")
    assert "sf_b_veto" not in factor("N1_NO_BVETO")


def test_s0_child_yield_inherits_parent_factor_in_execution(ROOT, tmp_path):
    import runpy
    from common.runner import RunAnalysis

    factor = runpy.run_path(str(FAMILY / "Closure/study_config.py"))["nominal_factor"]
    source = tmp_path / "input.root"
    frame = ROOT.RDataFrame(1)
    for name, value in {
        "x": "0.5",
        "sf_lepton_zx": "1.1",
        "sf_trigger_zx": "1.2",
        "sf_b_veto": "0.8",
    }.items():
        frame = frame.Define(name, value)
    frame.Snapshot("Events", str(source))
    cuts = {
        name: {"expr": "true", "weight": factor(name)}
        for name in ("S0_ZZCR", "S0_ZZCR_4E")
    }
    cuts["former_child"] = {"expr": "true", "weight": "sf_lepton_zx*sf_trigger_zx"}
    variables = {"yield": {"name": "x", "range": (1, 0.0, 1.0)}}
    sample = {"MC": {"name": [("mc", [str(source)])], "weight": "2.0"}}
    output = tmp_path / "out.root"
    RunAnalysis(
        RunAnalysis.splitSamples(sample),
        {},
        variables,
        {"cuts": cuts, "preselections": "1"},
        {},
        3.0,
        outputFileMap=str(output),
    ).run()
    f = ROOT.TFile.Open(str(output))
    parent = f.Get("S0_ZZCR/yield/histo_MC").Integral()
    child = f.Get("S0_ZZCR_4E/yield/histo_MC").Integral()
    former = f.Get("former_child/yield/histo_MC").Integral()
    assert child == parent
    assert child == pytest.approx(3.0 * 2.0 * 1.1 * 1.2 * 0.8)
    assert child / former == pytest.approx(0.8)
    f.Close()
