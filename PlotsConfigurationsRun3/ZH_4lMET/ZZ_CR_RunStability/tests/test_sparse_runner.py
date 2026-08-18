import pytest


ROOT = pytest.importorskip("ROOT")

from mkShapesRDF.shapeAnalysis.runner import RunAnalysis as CoreRunAnalysis
from zz_cr_runner import RunAnalysis


def _bare(cls, variables, cuts, factors=None, dataframe=None):
    runner = object.__new__(cls)
    runner.variables = variables
    runner.cuts = cuts
    runner.dfs = {
        "MC": {
            0: {
                "df": dataframe
                or (
                    ROOT.RDataFrame(1)
                    .Define("weight", "2.f")
                    .Define("x_0", "1.f")
                    .Define("y_0", "2.f")
                )
            }
        }
    }
    runner.remappedVariables = {}
    if factors is not None:
        runner.cut_weight_factors = factors
    runner.createResults()
    return runner


def _integral(result_map):
    return result_map["nominal"].Integral()


def test_overlapping_categories_have_independent_event_weights():
    variables = {"x": {"name": "x", "range": (1, 0.5, 1.5), "categories": ["DY_ALL", "ZZCR_ALL"]}}
    cuts = {
        "DY_ALL": {"expr": "true", "parent": "DY"},
        "ZZCR_ALL": {"expr": "true", "parent": "ZZCR"},
    }
    runner = _bare(RunAnalysis, variables, cuts, {"DY_ALL": "3.f", "ZZCR_ALL": "5.f"})
    runner.create_cuts_vars()
    assert _integral(runner.results["DY_ALL"]["x"]["MC"][0]) == pytest.approx(6.0)
    assert _integral(runner.results["ZZCR_ALL"]["x"]["MC"][0]) == pytest.approx(10.0)


def test_sparse_filtering_and_unrestricted_core_compatibility():
    cuts = {
        "DY_ALL": {"expr": "true", "parent": "DY"},
        "ZZCR_ALL": {"expr": "true", "parent": "ZZCR"},
    }
    sparse_variables = {
        "x": {"name": "x", "range": (1, 0.5, 1.5), "categories": ["DY_ALL", "ZZCR_ALL"]},
        "y": {"name": "y", "range": (1, 1.5, 2.5), "categories": ["ZZCR_ALL"]},
    }
    sparse = _bare(RunAnalysis, sparse_variables, cuts, {"DY_ALL": "1.f", "ZZCR_ALL": "1.f"})
    sparse.create_cuts_vars()
    assert "y" not in sparse.results["DY_ALL"]
    assert _integral(sparse.results["ZZCR_ALL"]["y"]["MC"][0]) == pytest.approx(2.0)

    unrestricted = {name: {key: value for key, value in definition.items() if key != "categories"} for name, definition in sparse_variables.items()}
    local = _bare(RunAnalysis, unrestricted, cuts, {name: "1.f" for name in cuts})
    core = _bare(CoreRunAnalysis, unrestricted, cuts)
    local.create_cuts_vars()
    core.create_cuts_vars()
    for cut in cuts:
        for variable in unrestricted:
            assert _integral(local.results[cut][variable]["MC"][0]) == pytest.approx(
                _integral(core.results[cut][variable]["MC"][0])
            )


def test_tree_variables_fail_closed():
    with pytest.raises(RuntimeError, match="histogram-only"):
        RunAnalysis([], {}, {"tree": {"tree": {"x": "x"}}}, {"cuts": {}, "preselections": "1"}, {}, 1.0)


def test_sparse_variations_survive_conversion_and_save(tmp_path):
    dataframe = (
        ROOT.RDataFrame(1)
        .Define("weight", "2.f")
        .Define("x_0", "1.f")
        .Define("y_0", "2.f")
        .Vary(
            "weight",
            "ROOT::RVecF{weight * 1.1f, weight * 0.9f}",
            ["up", "down"],
            "weight_test",
        )
    )
    variables = {
        "x": {
            "name": "x",
            "range": (1, 0.5, 1.5),
            "fold": 0,
            "categories": ["DY_ALL", "ZZCR_ALL"],
        },
        "y": {
            "name": "y",
            "range": (1, 1.5, 2.5),
            "fold": 0,
            "categories": ["ZZCR_ALL"],
        },
    }
    cuts = {
        "DY_ALL": {"expr": "true", "parent": "DY"},
        "ZZCR_ALL": {"expr": "true", "parent": "ZZCR"},
    }
    runner = _bare(
        RunAnalysis,
        variables,
        cuts,
        {"DY_ALL": "1.f", "ZZCR_ALL": "1.f"},
        dataframe=dataframe,
    )
    runner.outputFileMap = str(tmp_path / "sparse.root")
    runner.create_cuts_vars()
    runner.convertResults()

    dy_variations = runner.results["DY_ALL"]["x"]["MC"][0]
    zz_variations = runner.results["ZZCR_ALL"]["x"]["MC"][0]
    assert set(dy_variations) == {"nominal", "weight_testup", "weight_testdown"}
    assert dy_variations["nominal"].Integral() == pytest.approx(2.0)
    assert dy_variations["weight_testup"].Integral() == pytest.approx(2.2)
    assert dy_variations["weight_testdown"].Integral() == pytest.approx(1.8)
    assert zz_variations["nominal"].Integral() == pytest.approx(2.0)
    assert zz_variations["weight_testup"].Integral() == pytest.approx(2.2)
    assert zz_variations["weight_testdown"].Integral() == pytest.approx(1.8)

    # Exercise all three framework spelling variants used by local/batch paths.
    runner.saveResults()
    runner.mergeSaveResults()
    runner.mergeAndSaveResults()
    output = ROOT.TFile.Open(runner.outputFileMap, "READ")
    assert output and not output.IsZombie()
    try:
        assert not output.GetDirectory("DY_ALL/y")
        for path in (
            "DY_ALL/x/histo_MC",
            "DY_ALL/x/histo_MC_weight_testup",
            "DY_ALL/x/histo_MC_weight_testdown",
            "ZZCR_ALL/y/histo_MC",
        ):
            assert output.Get(path), path
    finally:
        output.Close()
