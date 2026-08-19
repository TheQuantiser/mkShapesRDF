import pytest


ROOT = pytest.importorskip("ROOT")

from mkShapesRDF.shapeAnalysis.histo_utils import postPlot  # noqa: E402
from run_stability_runner import RunAnalysis  # noqa: E402


def _contract():
    return {
        "enabled": True,
        "ordered_runs": [101, 102],
        "categories": ["DY_ALL"],
        "observables": ["obs"],
        "metadata_writer": {"sample": "DATA", "split_index": 0},
        "nominal": [
            {"run": 101, "delivered_fb": 1.1, "recorded_fb": 1.0},
            {"run": 102, "delivered_fb": 2.2, "recorded_fb": 2.0},
        ],
        "trigger_any": [
            {"run": 101, "delivered_fb": 1.0, "recorded_fb": 0.9},
            {"run": 102, "delivered_fb": 2.0, "recorded_fb": 1.8},
        ],
        "mc_source_lumi_fb": 3.5,
    }


def _frame():
    return (
        ROOT.RDataFrame(4)
        .Define("weight", "1.f")
        .Define("runStabilityIndex", "static_cast<int>(rdfentry_ % 2) + 1")
        .Define(
            "obs_0",
            "rdfentry_ == 0 ? -1.f : (rdfentry_ == 3 ? 3.f : "
            "static_cast<float>(rdfentry_) - 0.5f)",
        )
    )


def _runner(data_index=0):
    runner = object.__new__(RunAnalysis)
    runner.run_stability_enabled = True
    runner.run_stability_contract = _contract()
    runner.variables = {
        "obs": {
            "name": "obs",
            "range": ([0.0, 1.0, 2.0],),
            "fold": 3,
            "xaxis": "Observable",
        }
    }
    runner.cuts = {"DY_ALL": {"expr": "true", "parent": "DY"}}
    runner.dfs = {"DATA": {data_index: {"df": _frame()}}}
    runner.run_stability_results = {"DY_ALL": {"obs": {}}}
    runner.results = {}
    runner.remappedVariables = {}
    return runner


def test_data_th2_matches_folded_ordinary_th1_and_preserves_axes(tmp_path):
    runner = _runner()
    runner._book_run_stability_for_cut("DY_ALL")
    runner._convert_run_stability_results()
    histogram = runner.run_stability_results["DY_ALL"]["obs"][0]

    ordinary = _frame().Histo1D(("ordinary", "", 2, 0.0, 2.0), "obs_0", "weight")
    ordinary_histogram = ordinary.GetValue().Clone()
    ordinary_histogram.SetDirectory(0)
    ordinary_histogram = postPlot(ordinary_histogram, doFold=3, unroll=False)

    assert isinstance(histogram, ROOT.TH2)
    assert histogram.GetNbinsX() == 2
    assert histogram.GetXaxis().GetBinLabel(1) == "101"
    assert histogram.GetXaxis().GetBinLabel(2) == "102"
    assert histogram.GetYaxis().GetTitle() == "Observable"
    assert histogram.GetSumw2N() > 0
    assert histogram.Integral(1, 2, 1, 2) == pytest.approx(
        ordinary_histogram.Integral(1, 2)
    )
    for xbin in range(0, 4):
        assert histogram.GetBinContent(xbin, 0) == 0.0
        assert histogram.GetBinContent(xbin, 3) == 0.0

    runner.outputFileMap = str(tmp_path / "data.root")
    runner.saveResults()
    output = ROOT.TFile.Open(runner.outputFileMap, "READ")
    assert output and not output.IsZombie()
    try:
        stored = output.Get("run_stability/DY_ALL/obs/histo_DATA")
        assert stored and isinstance(stored, ROOT.TH2)
        assert stored.Integral(1, 2, 1, 2) == pytest.approx(4.0)
        for name, expected in (
            ("nominal_recorded_lumi_fb", (1.0, 2.0)),
            ("trigger_any_recorded_lumi_fb", (0.9, 1.8)),
        ):
            metadata = output.Get(f"run_stability/metadata/{name}")
            assert metadata and isinstance(metadata, ROOT.TH1)
            assert tuple(metadata.GetBinContent(index) for index in (1, 2)) == expected
            assert tuple(metadata.GetBinError(index) for index in (1, 2)) == (0.0, 0.0)
            assert metadata.GetXaxis().GetBinLabel(1) == "101"
        source = output.Get("run_stability/metadata/mc_source_lumi_fb")
        assert source.GetBinContent(1) == pytest.approx(3.5)
    finally:
        output.Close()


def test_overflow_only_fold_matches_ordinary_th1_and_preserves_underflow_sumw2():
    auxiliary = ROOT.TH2D("aux_fold2", "", 1, 0.5, 1.5, 2, 35.0, 45.0)
    ordinary = ROOT.TH1D("ordinary_fold2", "", 2, 35.0, 45.0)
    auxiliary.Sumw2()
    ordinary.Sumw2()
    for value, weight in ((30.0, 2.0), (37.0, 3.0), (42.0, 5.0), (50.0, 4.0)):
        auxiliary.Fill(1.0, value, weight)
        ordinary.Fill(value, weight)

    RunAnalysis.fold_observable_axis(auxiliary, 2)
    ordinary = postPlot(ordinary, doFold=2, unroll=False)

    assert auxiliary.GetSumw2N() > 0
    assert ordinary.GetSumw2N() > 0
    for ybin in range(0, auxiliary.GetNbinsY() + 2):
        assert auxiliary.GetBinContent(1, ybin) == pytest.approx(
            ordinary.GetBinContent(ybin)
        )
        assert auxiliary.GetBinError(1, ybin) == pytest.approx(
            ordinary.GetBinError(ybin)
        )
    assert auxiliary.GetBinContent(1, 0) == pytest.approx(2.0)
    assert auxiliary.GetBinError(1, 0) == pytest.approx(2.0)
    assert auxiliary.GetBinContent(1, 2) == pytest.approx(9.0)
    assert auxiliary.GetBinError(1, 2) == pytest.approx((5.0**2 + 4.0**2) ** 0.5)
    assert auxiliary.GetBinContent(1, 3) == 0.0
    assert auxiliary.GetBinError(1, 3) == 0.0


@pytest.mark.parametrize(
    ("observable", "bins", "low", "high", "width", "fold"),
    (
        ("Z0_mass", 60, 60.0, 120.0, 1.0, 0),
        ("Z0_pt", 20, 0.0, 100.0, 5.0, 2),
        ("lZ1_pt", 13, 35.0, 100.0, 5.0, 2),
        ("lZ2_pt", 13, 35.0, 100.0, 5.0, 2),
        ("lZ1_eta", 50, -2.5, 2.5, 0.1, 0),
        ("lZ2_eta", 50, -2.5, 2.5, 0.1, 0),
    ),
)
def test_focused_th1_definition_and_data_th2_axis_are_identical(
    load_state, observable, bins, low, high, width, fold
):
    state = load_state()
    definition = state["variables"][observable]
    axis_bins, axis_edges = RunAnalysis._axis_model(definition)
    th1_edges = tuple(definition["range"][0])
    assert axis_bins == bins
    assert tuple(axis_edges) == th1_edges
    assert th1_edges[0] == low
    assert th1_edges[-1] == high
    assert all(
        right - left == pytest.approx(width)
        for left, right in zip(th1_edges, th1_edges[1:])
    )
    assert definition["fold"] == fold


def test_non_writer_data_split_has_no_metadata(tmp_path):
    runner = _runner(data_index=1)
    runner._book_run_stability_for_cut("DY_ALL")
    runner._convert_run_stability_results()
    runner.outputFileMap = str(tmp_path / "data_split_1.root")
    runner.saveResults()
    output = ROOT.TFile.Open(runner.outputFileMap, "READ")
    try:
        assert output.Get("run_stability/DY_ALL/obs/histo_DATA")
        assert not output.GetDirectory("run_stability/metadata")
    finally:
        output.Close()


def test_schema_three_writes_every_compiled_luminosity_source(tmp_path):
    runner = _runner()
    runner.run_stability_contract["luminosity_sources"] = {
        "nominal": {"rows": runner.run_stability_contract["nominal"]},
        "trigger_any": {"rows": runner.run_stability_contract["trigger_any"]},
        "hlt_isomu24": {
            "rows": [
                {"run": 101, "delivered_fb": 0.8, "recorded_fb": 0.7},
                {"run": 102, "delivered_fb": 1.6, "recorded_fb": 1.4},
            ]
        },
    }
    runner.outputFileMap = str(tmp_path / "schema_three.root")
    runner.saveResults()
    output = ROOT.TFile.Open(runner.outputFileMap, "READ")
    assert output and not output.IsZombie()
    try:
        for quantity, expected in (
            ("delivered", (0.8, 1.6)),
            ("recorded", (0.7, 1.4)),
        ):
            metadata = output.Get(
                f"run_stability/metadata/hlt_isomu24_{quantity}_lumi_fb"
            )
            assert metadata and isinstance(metadata, ROOT.TH1)
            assert tuple(metadata.GetBinContent(index) for index in (1, 2)) == (
                expected
            )
            assert tuple(metadata.GetBinError(index) for index in (1, 2)) == (0.0, 0.0)
    finally:
        output.Close()


def test_schema_three_rejects_misaligned_luminosity_rows(tmp_path):
    runner = _runner()
    runner.run_stability_contract["luminosity_sources"] = {
        "nominal": {"rows": list(reversed(runner.run_stability_contract["nominal"]))}
    }
    runner.outputFileMap = str(tmp_path / "misaligned.root")
    with pytest.raises(RuntimeError, match="row 1 is for run 102; expected 101"):
        runner.saveResults()


def test_mc_never_books_auxiliary_th2():
    runner = _runner()
    runner.dfs = {"DY": {0: {"df": _frame()}}}
    runner._book_run_stability_for_cut("DY_ALL")
    assert runner.run_stability_results["DY_ALL"]["obs"] == {}


def test_public_observable_resolves_core_internal_variable_remap():
    runner = _runner()
    runner.variables = {"__obs": runner.variables.pop("obs")}
    runner.remappedVariables = {"__obs": "__"}
    runner.createResults()
    assert set(runner.run_stability_results["DY_ALL"]) == {"__obs"}
    assert runner._public_variable_name("__obs") == "obs"


def test_nonempty_run_flow_fails_closed():
    histogram = ROOT.TH2D("flow", "", 2, 0.5, 2.5, 2, 0.0, 2.0)
    histogram.Fill(0.0, 1.0)
    with pytest.raises(RuntimeError, match="run-axis underflow"):
        RunAnalysis._assert_empty_run_flows(histogram)
