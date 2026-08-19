import json
from pathlib import Path
import zlib

import cloudpickle
import pytest


ROOT = pytest.importorskip("ROOT")

from plot_run_stability import (  # noqa: E402
    CHI2_EXPECTATION_LEGEND_LABEL,
    CHI2_Y_AXIS_LABEL,
    MAX_OUTPUT_STEM_LENGTH,
    PERIOD_PLOT_TYPOGRAPHY,
    _category_annotation,
    _era_spans,
    _matplotlib_axis_title,
    _OverlayLegendTuple,
    _period_mc_groups,
    _physical_period_spans,
    _render_chi2_vs_run,
    _selected_run_labels,
    _staggered_run_labels,
    chi2_bin_statistic,
    chi2_display_summary,
    chi2_output_stem,
    garwood_interval,
    main,
    make_chi2_vs_run,
    make_period_plot,
    make_ratio_vs_run,
    make_run_plot,
    mc_ratio_covariance,
    period_inventory,
    period_output_stem,
    period_ratio_autorange,
    physical_run_period,
    ratio_display_summary,
    ratio_vs_run_autorange,
    ratio_with_uncertainty,
    resolve_luminosity_source,
    stability_output_stem,
    validate_dataset,
)


@pytest.mark.parametrize(
    ("root_title", "visible_title"),
    (
        ("m_{Z_{0}} [GeV]", r"$m_{Z_{0}}$ [GeV]"),
        ("p_{T}^{Z_{0}} [GeV]", r"$p_{T}^{Z_{0}}$ [GeV]"),
        (
            "p_{T}(#it{l}_{Z,1}) [GeV]",
            r"$p_{T}(\mathit{l}_{Z,1})$ [GeV]",
        ),
        (
            "p_{T}(#it{l}_{Z,2}) [GeV]",
            r"$p_{T}(\mathit{l}_{Z,2})$ [GeV]",
        ),
        ("#eta_{#it{l}_{Z,1}}", r"$\eta_{\mathit{l}_{Z,1}}$"),
        ("#eta_{#it{l}_{Z,2}}", r"$\eta_{\mathit{l}_{Z,2}}$"),
    ),
)
def test_focused_observable_axis_titles_are_valid_matplotlib_mathtext(
    root_title, visible_title
):
    import matplotlib.mathtext

    translated = _matplotlib_axis_title(root_title)
    assert translated == visible_title
    matplotlib.mathtext.MathTextParser("path").parse(translated)


def _fixture(
    tmp_path,
    era="2024",
    runs=(101, 102),
    luminosities=(1.0, 2.0),
    run_periods=("2024I_v1", "2024I_v2"),
):
    config_path = tmp_path / f"{era}.pkl"
    root_path = tmp_path / f"{era}.root"
    contract = {
        "schema_version": 3,
        "enabled": True,
        "analysis_era": era,
        "target_region": "DY",
        "ordered_runs": list(runs),
        "run_to_bin": {run: index for index, run in enumerate(runs, 1)},
        "categories": ["DY_ALL"],
        "observables": ["Z0_mass"],
        "auxiliary_output_paths": ["run_stability/DY_ALL/Z0_mass/histo_DATA"],
        "nominal": [
            {
                "run": run,
                "run_period": period,
                "recorded_fb": lumi,
                "delivered_fb": lumi,
            }
            for run, period, lumi in zip(runs, run_periods, luminosities)
        ],
        "trigger_any": [
            {
                "run": run,
                "run_period": period,
                "recorded_fb": lumi,
                "delivered_fb": lumi,
            }
            for run, period, lumi in zip(runs, run_periods, luminosities)
        ],
        "category_luminosity_sources": {"DY_ALL": "trigger_any"},
        "mc_source_lumi_fb": 10.0,
        "inputs": {},
    }
    contract["luminosity_sources"] = {
        "nominal": {"rows": contract["nominal"]},
        "trigger_any": {"rows": contract["trigger_any"]},
    }
    config = {
        "tag": f"fixture_{era}",
        "RUN_STABILITY_CONTRACT": contract,
        "plot": {
            "plot": {
                "DY": {"isData": 0, "scale": 1.0, "color": 418},
                "OTHER": {"isData": 0, "scale": 1.0, "color": 600},
                "DATA": {"isData": 1, "color": 1},
            },
            "groupPlot": {
                "DY": {"samples": ["DY"], "nameHR": "DY", "color": 418},
                "Other": {
                    "samples": ["OTHER"],
                    "nameHR": "Other",
                    "color": 600,
                },
            },
            "legend": {},
        },
    }
    config_path.write_bytes(zlib.compress(cloudpickle.dumps(config)))

    output = ROOT.TFile.Open(str(root_path), "RECREATE")
    data = ROOT.TH2D(
        "histo_DATA", ";Run;Z mass", len(runs), 0.5, len(runs) + 0.5, 2, 0.0, 2.0
    )
    data.Sumw2()
    for index, run in enumerate(runs, 1):
        data.GetXaxis().SetBinLabel(index, str(run))
        for _ in range(index):
            data.Fill(index, 0.5)
    output.mkdir("run_stability/DY_ALL/Z0_mass")
    output.cd("run_stability/DY_ALL/Z0_mass")
    data.Write()
    output.mkdir("run_stability/metadata")
    output.cd("run_stability/metadata")
    for source in ("nominal", "trigger_any"):
        for quantity in ("delivered", "recorded"):
            hist = ROOT.TH1D(
                f"{source}_{quantity}_lumi_fb", "", len(runs), 0.5, len(runs) + 0.5
            )
            for index, (run, lumi) in enumerate(zip(runs, luminosities), 1):
                hist.GetXaxis().SetBinLabel(index, str(run))
                hist.SetBinContent(index, lumi)
            hist.Write()
    source = ROOT.TH1D("mc_source_lumi_fb", "", 1, 0.5, 1.5)
    source.SetBinContent(1, 10.0)
    source.Write()
    output.mkdir("DY_ALL/Z0_mass")
    output.cd("DY_ALL/Z0_mass")
    for name, contents in (("DY", (20.0, 10.0)), ("OTHER", (5.0, 5.0))):
        hist = ROOT.TH1D(f"histo_{name}", ";Z mass;Events", 2, 0.0, 2.0)
        hist.Sumw2()
        for index, value in enumerate(contents, 1):
            hist.SetBinContent(index, value)
            hist.SetBinError(index, value**0.5)
        hist.Write()
    output.Close()
    return config_path, root_path


def test_ratio_point_uncertainty_is_poisson_data_only():
    low, high = garwood_interval(0)
    assert low == 0.0
    assert high > 0.0
    result = ratio_with_uncertainty(4.0, 2.0)
    assert result["value"] == pytest.approx(2.0)
    assert result["error_low"] == pytest.approx((4.0 - result["data_low"]) / 2.0)
    assert result["error_high"] == pytest.approx((result["data_high"] - 4.0) / 2.0)
    with pytest.raises(RuntimeError, match="integer count"):
        ratio_with_uncertainty(1.5, 2.0)


def test_reduced_chi2_bin_statistic_uses_garwood_and_scaled_mc_variance():
    result = chi2_bin_statistic(4.0, 3.0, 1.25)
    low, high = garwood_interval(4)
    expected_data_variance = (0.5 * (high - low)) ** 2
    assert result["data_variance"] == pytest.approx(expected_data_variance)
    assert result["total_variance"] == pytest.approx(expected_data_variance + 1.25)
    assert result["chi2_contribution"] == pytest.approx(
        1.0 / (expected_data_variance + 1.25)
    )

    zero = chi2_bin_statistic(0.0, 0.0, 0.0)
    assert zero["valid"]
    assert zero["data_variance"] > 0.0
    assert zero["chi2_contribution"] == 0.0
    high_statistics = chi2_bin_statistic(10000.0, 10000.0, 25.0)
    assert high_statistics["valid"]
    assert high_statistics["chi2_contribution"] == 0.0
    with pytest.raises(RuntimeError, match="integer count"):
        chi2_bin_statistic(1.5, 1.0, 1.0)


def test_reduced_chi2_autorange_preserves_core_and_marks_one_outlier():
    rows = [
        {
            "era": "2024",
            "run": index,
            "valid": True,
            "invalid_reason": None,
            "reduced_chi2": 20.0 if index == 10 else 0.95 + 0.01 * index,
            "ndf": 50,
        }
        for index in range(1, 11)
    ]
    display = chi2_display_summary(rows)
    assert display["range"][0] < 1.0 < display["range"][1]
    assert display["range"][1] < 3.0
    assert [point["run"] for point in display["above"]] == [10]
    assert display["policy"]["expected_band"].startswith("1 +/- sqrt")


def test_reduced_chi2_autorange_focuses_dense_core_and_audits_broad_tail():
    rows = [
        {
            "era": "2024",
            "run": index,
            "valid": True,
            "invalid_reason": None,
            "reduced_chi2": 0.82 + 0.015 * (index % 20),
            "ndf": 50,
        }
        for index in range(1, 61)
    ]
    rows.extend(
        {
            "era": "2024",
            "run": index,
            "valid": True,
            "invalid_reason": None,
            "reduced_chi2": 10.0 + index,
            "ndf": 50,
        }
        for index in range(61, 81)
    )
    display = chi2_display_summary(rows)
    assert display["policy"]["range_mode"] == "informative_median_mad_core"
    assert display["range"][0] == 0.0
    assert 1.0 < display["range"][1] < 3.0
    assert len(display["above"]) == 20
    assert display["clipped"]["central_above"] == display["above"]
    excluded = {
        point["run"]: point["reason_codes"]
        for point in display["policy"]["excluded_points"]
    }
    assert all("above_diagnostic_focus_cap" in excluded[run] for run in range(61, 81))


def test_reduced_chi2_autorange_sparse_fallback_and_hard_cap_are_explicit():
    sparse = [
        {
            "era": "2024",
            "run": 1,
            "valid": True,
            "invalid_reason": None,
            "reduced_chi2": 0.02,
            "ndf": 50,
        },
        {
            "era": "2024",
            "run": 2,
            "valid": True,
            "invalid_reason": None,
            "reduced_chi2": 0.05,
            "ndf": 50,
        },
        {
            "era": "2024",
            "run": 3,
            "valid": False,
            "invalid_reason": "zero_luminosity",
            "reduced_chi2": None,
            "ndf": 0,
        },
    ]
    display = chi2_display_summary(sparse)
    assert display["policy"]["range_mode"] == "unity_sparse_fallback"
    assert display["policy"]["sparse_fallback"] == [0.0, 1.6]
    assert display["range"] == pytest.approx([0.0, 1.728])
    assert [point["run"] for point in display["invalid"]] == [3]

    coherent_high = [
        {
            "era": "2024",
            "run": index,
            "valid": True,
            "invalid_reason": None,
            "reduced_chi2": 4.80 + 0.01 * index,
            "ndf": 50,
        }
        for index in range(1, 9)
    ]
    capped = chi2_display_summary(coherent_high)
    assert capped["range"] == [0.0, 5.0]
    assert capped["policy"]["hard_cap_applied"] is True
    assert capped["policy"]["diagnostic_hard_bounds"] == [0.0, 5.0]


def test_reduced_chi2_hard_cap_tick_has_required_canvas_clearance(tmp_path):
    rows = [
        {
            "era": "2024",
            "run": 380000 + index,
            "run_period": "2024I",
            "physical_run_period": "2024I",
            "recorded_lumi_fb": 0.01,
            "valid": True,
            "invalid_reason": None,
            "reduced_chi2": 4.80 + 0.01 * index,
            "ndf": 50,
        }
        for index in range(1, 9)
    ]
    presentation = _render_chi2_vs_run(
        rows,
        tmp_path,
        "hard_cap_layout",
        "DY_ALL",
        "Z0_mass",
    )
    assert presentation["display_range"] == [0.0, 5.0]
    assert presentation["visible_semantics"]["dynamic_y_ticks"][-1] == 5.0
    layout = presentation["visible_semantics"]["layout_audit"]
    assert layout["clipped_required_artists"] == []
    assert layout["minimum_edge_clearance_pixels"]["top"] >= (
        layout["canvas_inset_requirement_pixels"]
    )


def test_physical_period_inventory_collapses_configured_variants(tmp_path):
    assert physical_run_period("2023C_v4") == "2023C"
    assert physical_run_period("2024I_v2") == "2024I"
    with pytest.raises(RuntimeError, match="Unsupported or empty"):
        physical_run_period("2023B-extra")
    config_path, root_path = _fixture(tmp_path)
    dataset = validate_dataset(config_path, root_path)
    inventory = period_inventory(dataset, "trigger_any")
    assert inventory == [
        {
            "period": "2024I",
            "analysis_era": "2024",
            "run_indices": [0, 1],
            "runs": [101, 102],
            "configured_run_periods": ["2024I_v1", "2024I_v2"],
        }
    ]


def test_shared_mc_covariance_is_block_diagonal_by_era():
    covariance = mc_ratio_covariance(
        [1.0, 2.0, 3.0],
        ["2022", "2022", "2023"],
        {"2022": 10.0, "2023": 20.0},
        {"2022": 4.0, "2023": 9.0},
    )
    assert covariance[0][1] == pytest.approx(0.08)
    assert covariance[0][2] == 0.0
    assert covariance[2][2] == pytest.approx(9.0 * 9.0 / 400.0)


def _autorange_row(run, ratio, *, era="2024", data=100.0, error=0.03, mc_rel=0.04):
    return {
        "era": era,
        "run": run,
        "ratio": ratio,
        "ratio_error_low": error,
        "ratio_error_high": 1.05 * error,
        "data_yield": data,
        "mc_yield": data / ratio if ratio and ratio > 0.0 else 100.0,
        "mc_relative_uncertainty": mc_rel,
        "valid": ratio is not None,
        "invalid_reason": None if ratio is not None else "zero_luminosity",
    }


def test_ratio_vs_run_autorange_focuses_precise_core_and_records_outliers():
    rows = [_autorange_row(index, 0.97 + 0.005 * index) for index in range(1, 13)]
    rows.extend((_autorange_row(13, 0.10), _autorange_row(14, 4.0)))
    display = ratio_vs_run_autorange(rows)
    low, high = display["range"]
    assert 0.30 <= high - low <= 0.40
    assert low < 1.0 < high
    assert [point["run"] for point in display["below"]] == [13]
    assert [point["run"] for point in display["above"]] == [14]
    assert {13, 14} == {
        point["run"] for point in display["policy"]["central_outlier_points"]
    }
    assert len(display["policy"]["selection_inputs"]) == len(rows)
    assert display["clipped"]["data_central_below"] == display["below"]
    assert display["clipped"]["data_central_above"] == display["above"]
    assert ratio_display_summary(rows) == display


def test_ratio_vs_run_autorange_preserves_shifted_coherent_population():
    rows = [_autorange_row(index, 1.30 + 0.01 * index) for index in range(1, 9)]
    display = ratio_vs_run_autorange(rows)
    assert display["policy"]["range_mode"] == "informative_median_mad_core"
    assert display["range"][0] < 1.0 < 1.38 < display["range"][1]
    assert display["above"] == []
    assert display["below"] == []


def test_ratio_vs_run_autorange_sparse_fallback_records_exclusions_and_invalid():
    rows = [_autorange_row(1, 0.98), _autorange_row(2, 1.02)]
    rows.extend(
        _autorange_row(index, ratio, data=1.0, error=3.0)
        for index, ratio in ((3, 0.2), (4, 1.0), (5, 3.0))
    )
    rows.append(_autorange_row(6, None))
    display = ratio_vs_run_autorange(rows)
    assert display["policy"]["range_mode"] == "unity_baseline_sparse_fallback"
    assert display["policy"]["fallback_range"] == [0.70, 1.30]
    assert display["range"] == pytest.approx([0.652, 1.348])
    assert [point["run"] for point in display["policy"]["informative_points"]] == [
        1,
        2,
    ]
    assert {
        point["run"] for point in display["policy"]["excluded_uninformative_points"]
    } == {3, 4, 5}
    assert [point["run"] for point in display["invalid"]] == [6]
    assert display["clipped"]["invalid"] == display["invalid"]


def test_ratio_vs_run_autorange_includes_every_era_mc_band():
    rows = [
        _autorange_row(index, 0.98 + 0.005 * index, era="2023", mc_rel=0.08)
        for index in range(1, 4)
    ] + [
        _autorange_row(index, 0.99 + 0.004 * index, era="2024", mc_rel=0.22)
        for index in range(4, 8)
    ]
    display = ratio_vs_run_autorange(rows)
    assert display["range"][0] <= 0.78
    assert display["range"][1] >= 1.22
    assert display["policy"]["era_mc_bands"] == [
        {"era": "2023", "relative_uncertainty": 0.08, "low": 0.92, "high": 1.08},
        {"era": "2024", "relative_uncertainty": 0.22, "low": 0.78, "high": 1.22},
    ]
    assert display["clipped"]["mc_band_below"] == []
    assert display["clipped"]["mc_band_above"] == []


def test_ratio_vs_run_autorange_enforces_minimum_span_and_hard_bounds():
    narrow = ratio_vs_run_autorange(
        [_autorange_row(index, 1.0 + 0.001 * index) for index in range(1, 7)]
    )
    assert narrow["range"][1] - narrow["range"][0] >= 0.30
    extreme = ratio_vs_run_autorange(
        [_autorange_row(index, 1.0, era="extreme", mc_rel=2.0) for index in range(1, 7)]
    )
    assert extreme["range"] == [0.5, 1.5]
    assert extreme["policy"]["hard_bounds_applied"] == {"low": True, "high": True}
    assert [item["era"] for item in extreme["clipped"]["mc_band_below"]] == ["extreme"]
    assert [item["era"] for item in extreme["clipped"]["mc_band_above"]] == ["extreme"]


def test_run_labels_stagger_adjacent_era_boundaries():
    rows = [
        {"era": "2022", "run": 101, "recorded_lumi_fb": 1.0},
        {"era": "2022", "run": 102, "recorded_lumi_fb": 1.0},
        {"era": "2022EE", "run": 201, "recorded_lumi_fb": 1.0},
        {"era": "2022EE", "run": 202, "recorded_lumi_fb": 1.0},
    ]
    spans = _era_spans(rows)
    selected = _selected_run_labels(rows, spans)
    displayed, staggered_bins = _staggered_run_labels(selected, spans)
    assert selected == [(1, "101"), (2, "102"), (3, "201"), (4, "202")]
    assert displayed == [(1, "101"), (2, "102"), (3, "\n201"), (4, "202")]
    assert staggered_bins == [3]


def test_physical_period_spans_are_short_labelled_contiguous_lanes():
    rows = [
        {"era": "2022", "run": 1, "physical_run_period": "2022B"},
        {"era": "2022", "run": 2, "physical_run_period": "2022B"},
        {"era": "2022", "run": 3, "physical_run_period": "2022C"},
        {"era": "2023", "run": 4, "physical_run_period": "2023C"},
    ]
    assert _physical_period_spans(rows) == [
        {
            "period": "2022B",
            "label": "B",
            "era": "2022",
            "first_bin": 1,
            "last_bin": 2,
            "first_run": 1,
            "last_run": 2,
            "run_count": 2,
        },
        {
            "period": "2022C",
            "label": "C",
            "era": "2022",
            "first_bin": 3,
            "last_bin": 3,
            "first_run": 3,
            "last_run": 3,
            "run_count": 1,
        },
        {
            "period": "2023C",
            "label": "C",
            "era": "2023",
            "first_bin": 4,
            "last_bin": 4,
            "first_run": 4,
            "last_run": 4,
            "run_count": 1,
        },
    ]
    with pytest.raises(RuntimeError, match="noncontiguous"):
        _physical_period_spans(rows + [rows[0]])


def test_category_annotation_separates_selection_and_flavor():
    assert _category_annotation("DY_ALL") == (
        "Trigger: inclusive OR\n" "Inclusive $Z\\rightarrow\\ell\\ell$"
    )
    assert _category_annotation("DY_STREAM_MUONEG_ZMM") == (
        "Stream: MuonEG\n" "$Z\\rightarrow\\mu\\mu$"
    )
    assert "HLT path:" in _category_annotation("DY_HLT_MU23_ELE12_ZEE")


def test_on_demand_plot_and_ratio_artifacts(tmp_path):
    config_path, root_path = _fixture(tmp_path)
    dataset = validate_dataset(config_path, root_path, "trigger_any")
    plot_dir = tmp_path / "plot"
    plot_receipt = make_run_plot(
        dataset, "DY_ALL", "Z0_mass", 101, "trigger_any", plot_dir
    )
    assert plot_receipt["mc_scale"] == pytest.approx(0.1)
    assert len(list(plot_dir.glob("*.png"))) == 1
    assert len(list(plot_dir.glob("*.pdf"))) == 1
    assert len(list(plot_dir.glob("*.json"))) == 1
    assert all(plot_receipt["output_sha256"].values())

    ratio_dir = tmp_path / "ratio"
    ratio_receipt = make_ratio_vs_run(
        [dataset], "DY_ALL", "Z0_mass", "trigger_any", ratio_dir
    )
    assert ratio_receipt["invalid_zero_luminosity_runs"] == []
    assert Path(ratio_receipt["outputs"]["root"]).is_file()
    assert Path(ratio_receipt["outputs"]["csv"]).is_file()
    assert all(ratio_receipt["output_sha256"].values())
    assert ratio_receipt["schema_version"] == 4
    assert ratio_receipt["output_stem"] == ("stability_Zmass_DY_ALL_trigger_any_2024")
    ratio_display = ratio_receipt["presentation"]["ratio_autorange"]
    assert ratio_display["policy"]["name"] == "uncertainty_aware_ratio_vs_run_v1"
    assert (
        ratio_receipt["presentation"]["ratio_display_range"] == ratio_display["range"]
    )
    assert ratio_display["range"][0] < 1.0 < ratio_display["range"][1]
    assert 1.0 in ratio_receipt["presentation"]["dynamic_y_ticks"]
    assert ratio_receipt["presentation"]["y_axis_label"] == "Data/MC"
    assert ratio_receipt["presentation"]["canvas_pixels"] == [3000, 1560]
    assert ratio_receipt["presentation"]["legend_entries"] == [
        "Data",
        "MC",
        "Out of range",
    ]
    assert ratio_receipt["presentation"]["visible_semantics"]["legend_mc_entry"] == "MC"
    assert ratio_receipt["presentation"]["visible_semantics"]["top_ticks"] is False
    assert ratio_receipt["presentation"]["visible_semantics"]["right_ticks"] is False
    layout = ratio_receipt["presentation"]["visible_semantics"]["layout_audit"]
    assert layout["legend_annotation_overlap"] is False
    assert layout["clipped_required_artists"] == []
    assert all(
        clearance >= layout["canvas_inset_requirement_pixels"]
        for clearance in layout["minimum_edge_clearance_pixels"].values()
    )
    assert ratio_receipt["presentation"]["category_annotation"].startswith(
        "Trigger: inclusive OR"
    )
    assert ratio_receipt["presentation"]["era_spans"][0][
        "mc_relative_uncertainty"
    ] == pytest.approx(40.0**0.5 / 40.0)
    assert ratio_receipt["presentation"]["physical_period_spans"][0] == {
        "period": "2024I",
        "label": "I",
        "era": "2024",
        "first_bin": 1,
        "last_bin": 2,
        "first_run": 101,
        "last_run": 102,
        "run_count": 2,
    }
    assert ratio_receipt["presentation"]["physical_period_lane"] == {
        "membership_source": "compiled nominal run_period rows",
        "label_policy": (
            "single period letter; year/analysis era supplied by the era lane"
        ),
        "separator_extent_axes_fraction": [0.0, 0.06],
        "transparent_label_background": True,
    }
    assert [
        point["run"] for point in ratio_receipt["presentation"]["out_of_range"]["below"]
    ] == [101, 102]
    assert ratio_receipt["presentation"]["selected_run_labels"] == [
        {"bin": 1, "run": 101},
        {"bin": 2, "run": 102},
    ]
    assert ratio_receipt["presentation"]["staggered_run_label_bins"] == []
    receipt_path = next(ratio_dir.glob("*.json"))
    assert json.loads(receipt_path.read_text())["kind"] == "data_mc_ratio_vs_run"
    output = ROOT.TFile.Open(ratio_receipt["outputs"]["root"], "READ")
    try:
        graph = output.Get("ratio_graph_garwood_data")
        assert graph
        assert graph.GetErrorYlow(0) == pytest.approx(
            ratio_with_uncertainty(1.0, 4.0)["error_low"]
        )
        ratio_hist = output.Get("ratio_by_run")
        assert ratio_hist.TestBit(ROOT.TH1.kNoStats)
        assert ratio_hist.GetBinError(1) == pytest.approx(0.25)
        covariance = output.Get("ratio_covariance_mcstat")
        assert covariance and covariance.GetBinContent(1, 2) > 0.0
        assert covariance.GetXaxis().GetBinLabel(1) == "101"
    finally:
        output.Close()


def test_reduced_chi2_vs_run_scales_each_era_and_emits_exact_components(
    tmp_path, monkeypatch
):
    import matplotlib.axes

    legend_calls = []
    reference_lines = []
    original_legend = matplotlib.axes.Axes.legend
    original_axhline = matplotlib.axes.Axes.axhline

    def reject_errorbar(*args, **kwargs):
        raise AssertionError("reduced-chi2 run points must be scatter-only")

    def record_legend(self, *args, **kwargs):
        legend_calls.append(dict(kwargs))
        return original_legend(self, *args, **kwargs)

    def record_axhline(self, *args, **kwargs):
        reference_lines.append((args, dict(kwargs)))
        return original_axhline(self, *args, **kwargs)

    monkeypatch.setattr(matplotlib.axes.Axes, "errorbar", reject_errorbar)
    monkeypatch.setattr(matplotlib.axes.Axes, "legend", record_legend)
    monkeypatch.setattr(matplotlib.axes.Axes, "axhline", record_axhline)
    config_path, root_path = _fixture(tmp_path)
    dataset = validate_dataset(config_path, root_path, "trigger_any")
    output_dir = tmp_path / "chi2"
    receipt = make_chi2_vs_run(
        [dataset], "DY_ALL", "Z0_mass", "trigger_any", output_dir
    )
    assert receipt["kind"] == "reduced_chi2_vs_run"
    assert receipt["output_stem"] == "chi2_Zmass_DY_ALL_trigger_any_2024"
    assert receipt["covariance"]["status"] == "not_computed"
    assert "not an exact" in receipt["statistic_definition"]["interpretation"]
    assert receipt["runs"][0]["mc_scale"] == pytest.approx(0.1)
    assert receipt["runs"][1]["mc_scale"] == pytest.approx(0.2)
    assert receipt["runs"][0]["mc_variance_scale"] == pytest.approx(0.01)
    assert receipt["runs"][0]["ndf"] == 2
    assert receipt["runs"][0]["n_fitted_parameters"] == 0
    assert receipt["runs"][0]["approx_expected_std"] == pytest.approx(1.0)
    first_bins = receipt["run_bin_statistics"][0]["bins"]
    assert first_bins[0]["mc"] == pytest.approx(2.5)
    assert first_bins[0]["mc_variance"] == pytest.approx(0.25)
    assert first_bins[1]["mc"] == pytest.approx(1.5)
    assert first_bins[1]["mc_variance"] == pytest.approx(0.15)
    assert receipt["runs"][0]["chi2"] == pytest.approx(
        sum(item["chi2_contribution"] for item in first_bins)
    )
    assert receipt["presentation"]["physical_period_spans"][0]["period"] == ("2024I")
    visible = receipt["presentation"]["visible_semantics"]
    assert visible["y_axis_label"] == CHI2_Y_AXIS_LABEL
    assert visible["run_point_artist"] == "scatter_without_errorbars"
    assert visible["reference_line_y"] == 1.0
    assert visible["expectation_legend_label"] == CHI2_EXPECTATION_LEGEND_LABEL
    assert visible["legend_frame_alpha"] == 1.0
    assert visible["top_ticks"] is False and visible["right_ticks"] is False
    assert 1.0 in visible["dynamic_y_ticks"]
    assert visible["layout_audit"]["legend_annotation_overlap"] is False
    assert visible["layout_audit"]["clipped_required_artists"] == []
    assert legend_calls[-1]["framealpha"] == 1.0
    assert any(args and args[0] == 1.0 for args, _ in reference_lines)
    assert CHI2_Y_AXIS_LABEL == r"$\chi^2_{\mathrm{red}}$"
    assert CHI2_EXPECTATION_LEGEND_LABEL == (r"Approx. $1 \pm \sqrt{2/\mathrm{ndf}}$")
    assert receipt["presentation"]["display_range"][0] <= 1.0
    assert receipt["presentation"]["display_range"][1] >= 1.0
    assert receipt["presentation"]["out_of_range"]["below"] == []
    assert [
        point["run"] for point in receipt["presentation"]["out_of_range"]["above"]
    ] == [102]
    assert receipt["presentation"]["invalid"] == []
    assert receipt["presentation"]["autorange"]["policy"]["name"] == (
        "focused_reduced_chi2_informative_core_v2"
    )
    assert set(receipt["outputs"]) == {"csv", "root", "png", "pdf"}
    assert all(receipt["output_sha256"].values())

    output = ROOT.TFile.Open(receipt["outputs"]["root"], "READ")
    try:
        reduced = output.Get("reduced_chi2_by_run")
        contributions = output.Get("chi2_contribution_by_run_bin")
        definition = output.Get("statistic_definition_json")
        covariance = output.Get("covariance_status_json")
        expected_band = output.Get("approx_expected_reduced_chi2_band")
        assert reduced and contributions and definition and covariance and expected_band
        assert reduced.GetXaxis().GetBinLabel(1) == "101"
        assert contributions.GetBinContent(1, 1) == pytest.approx(
            first_bins[0]["chi2_contribution"]
        )
        assert json.loads(covariance.GetTitle())["status"] == "not_computed"
    finally:
        output.Close()

    assert (
        "config_sha256" in Path(receipt["outputs"]["csv"]).read_text().splitlines()[0]
    )
    with pytest.raises(FileExistsError, match="Refusing to overwrite"):
        make_chi2_vs_run([dataset], "DY_ALL", "Z0_mass", "trigger_any", output_dir)


def test_reduced_chi2_vs_run_records_zero_luminosity_invalid_run(tmp_path):
    config_path, root_path = _fixture(tmp_path, luminosities=(0.0, 2.0))
    dataset = validate_dataset(config_path, root_path)
    receipt = make_chi2_vs_run(
        [dataset], "DY_ALL", "Z0_mass", "trigger_any", tmp_path / "chi2_zero"
    )
    assert receipt["invalid_runs"] == [
        {"era": "2024", "run": 101, "reason": "zero_luminosity"}
    ]
    assert not receipt["runs"][0]["valid"]
    assert receipt["runs"][1]["valid"]


def test_physical_period_plot_scales_mc_once_and_emits_complete_receipt(tmp_path):
    config_path, root_path = _fixture(tmp_path)
    dataset = validate_dataset(config_path, root_path)
    luminosity_source = resolve_luminosity_source([dataset], "DY_ALL", "auto")
    output_dir = tmp_path / "period"
    receipt = make_period_plot(
        dataset,
        "DY_ALL",
        "Z0_mass",
        "2024I",
        luminosity_source,
        output_dir,
    )
    assert receipt["kind"] == "physical_run_period_data_mc"
    assert receipt["configured_run_periods"] == ["2024I_v1", "2024I_v2"]
    assert receipt["runs"] == [101, 102]
    assert receipt["recorded_lumi_fb"] == pytest.approx(3.0)
    assert receipt["mc_source_lumi_fb"] == pytest.approx(10.0)
    assert receipt["mc_scale"] == pytest.approx(0.3)
    assert receipt["mc_variance_scale"] == pytest.approx(0.09)
    assert receipt["data_yield"] == pytest.approx(3.0)
    assert receipt["mc_yield"] == pytest.approx(12.0)
    assert receipt["mc_variance"] == pytest.approx(3.6)
    assert receipt["schema_version"] == 2
    assert receipt["output_stem"] == "datamc_2024I_Zmass_DY_ALL_trigger_any"
    assert set(receipt["mc_grouping"]["groups"]) == {"DY", "Others"}
    assert receipt["mc_grouping"]["groups"]["DY"] == ["DY"]
    assert receipt["mc_grouping"]["groups"]["Others"] == ["OTHER"]
    assert receipt["mc_grouping"]["group_totals_after_period_scale"]["DY"] == {
        "yield": pytest.approx(9.0),
        "variance": pytest.approx(2.7),
    }
    assert receipt["mc_grouping"]["group_totals_after_period_scale"]["Others"] == {
        "yield": pytest.approx(3.0),
        "variance": pytest.approx(0.9),
    }
    assert receipt["presentation"]["ratio_autorange"]["policy"]["name"] == (
        "uncertainty_aware_period_ratio_intervals_v2"
    )
    visible = receipt["presentation"]["visible_semantics"]
    assert visible["stack_groups"] == ["DY", "Others"]
    assert visible["upper_data_zero_count_limits_rendered"] is False
    assert visible["upper_data_positive_bin_count"] == 1
    assert visible["upper_data_suppressed_zero_bin_count"] == 1
    assert visible["stack_artist"] == "filled_stairs"
    assert visible["stack_artist_class"] == "StepPatch"
    assert visible["stack_fill"] == "solid"
    assert visible["stack_facecolor_alpha"] == 1.0
    assert visible["stack_edgecolor"] == "none"
    assert visible["stack_linewidth"] == 0.0
    assert visible["stack_hatch"] is None
    assert visible["stack_per_bin_rectangles"] is False
    assert visible["stack_vertical_bin_boundaries"] is False
    assert [
        item["artist_class"] for item in visible["stack_group_artist_semantics"]
    ] == [
        "StepPatch",
        "StepPatch",
    ]
    assert all(
        item["facecolor_alpha"] == 1.0
        and item["edgecolor_rgba"][3] == 0.0
        and item["linewidth"] == 0.0
        and item["hatch"] is None
        and item["per_bin_rectangles"] is False
        and item["vertical_bin_boundaries"] is False
        for item in visible["stack_group_artist_semantics"]
    )
    assert visible["mc_stat_band"] == {
        "fill": "translucent_hatched",
        "alpha": 0.18,
        "hatch": "////",
        "facecolor": "#1F5F8B",
        "edgecolor": "#1F5F8B",
    }
    assert visible["mc_total_line"] == {
        "artist": "stairs",
        "color": "#1F5F8B",
        "linewidth": 1.6,
    }
    assert visible["legend"]["inside_axes"] is True
    assert visible["legend"]["entry_names"] == [
        "Data",
        "DY",
        "Others",
        "Total MC",
    ]
    assert "MC" not in visible["legend"]["entry_names"]
    assert all("\n$" in label for label in visible["legend"]["labels"])
    assert all("N=" not in label for label in visible["legend"]["labels"])
    assert all("MC stat. unc." not in label for label in visible["legend"]["labels"])
    assert visible["legend"]["mc_handle"] == "overlay_line_and_band"
    assert visible["category_annotation"]["inside_axes"] is True
    assert visible["category_annotation"]["luminosity_mathtext"] == (
        r"$3.000\,\mathrm{fb}^{-1}$"
    )
    assert r"3.000\,\mathrm{fb}^{-1}" in visible["category_annotation"]["visible_text"]
    assert visible["category_annotation"]["luminosity_unit_spacing"] == (
        r"LaTeX thin space \,"
    )
    assert visible["observable_axis_title"] == "Z mass"
    assert visible["ratio_y_axis_label"] == "Data/MC"
    assert visible["typography_points"] == PERIOD_PLOT_TYPOGRAPHY
    assert visible["typography_points"]["legend_fontsize"] >= 13.0
    assert visible["typography_points"]["axis_labelsize"] == 21.0
    assert visible["typography_points"]["tick_labelsize"] >= 13.0
    assert visible["typography_points"]["annotation_fontsize"] >= 14.0
    assert visible["scientific_notation"] == "mathtext"
    assert visible["layout_audit"]["canvas_inset_requirement_pixels"] == 6.0
    assert visible["layout_audit"]["visible_text_artist_count"] > 0
    assert all(
        clearance >= 6.0
        for clearance in visible["layout_audit"][
            "minimum_edge_clearance_pixels"
        ].values()
    )
    assert visible["ticks"] == {
        "top": False,
        "right": False,
        "applies_to": ["upper", "lower"],
        "which": "both",
        "x_endpoint_label_alignment": ["left", "right"],
    }
    yield_entries = {
        entry["name"]: entry for entry in visible["yield_legend"]["entries"]
    }
    assert yield_entries["Data"]["yield"] == pytest.approx(3.0)
    assert yield_entries["Data"]["variance"] == pytest.approx(3.0)
    assert yield_entries["Data"]["uncertainty_kind"].startswith("Garwood")
    assert yield_entries["DY"]["yield"] == pytest.approx(9.0)
    assert yield_entries["DY"]["variance"] == pytest.approx(2.7)
    assert yield_entries["Others"]["yield"] == pytest.approx(3.0)
    assert yield_entries["Others"]["variance"] == pytest.approx(0.9)
    assert yield_entries["Total MC"]["yield"] == pytest.approx(12.0)
    assert yield_entries["Total MC"]["variance"] == pytest.approx(3.6)
    assert yield_entries["DY"]["yield"] + yield_entries["Others"][
        "yield"
    ] == pytest.approx(yield_entries["Total MC"]["yield"])
    assert yield_entries["DY"]["variance"] + yield_entries["Others"][
        "variance"
    ] == pytest.approx(yield_entries["Total MC"]["variance"])
    assert visible["yield_legend"]["closure"] == {
        "group_yield_minus_mc": pytest.approx(0.0),
        "group_variance_minus_mc": pytest.approx(0.0),
    }
    style_provenance = receipt["presentation"]["ratio_autorange"]["policy"][
        "style_provenance"
    ]
    assert style_provenance["runtime_dependency"] is False
    assert style_provenance["robust_visibility_principle"]["function"] == (
        "audit_plot_visibility"
    )
    assert style_provenance["clipped_marker_principle"]["function"] == (
        "_panel_outlier_indicators"
    )
    assert set(receipt["outputs"]) == {"csv", "root", "png", "pdf"}
    assert all(receipt["output_sha256"].values())
    assert len(list(output_dir.glob("*.json"))) == 1

    output = ROOT.TFile.Open(receipt["outputs"]["root"], "READ")
    try:
        data = output.Get("data_period")
        mc = output.Get("mc_total_scaled")
        ratio = output.Get("ratio_graph_garwood_data")
        band = output.Get("ratio_mc_stat_band")
        dy = output.Get("mc_group_DY")
        others = output.Get("mc_group_Others")
        classification = output.Get("mc_group_classification_json")
        assert data and mc and ratio and band and dy and others and classification
        assert data.Integral(1, data.GetNbinsX()) == pytest.approx(3.0)
        assert mc.GetBinContent(1) == pytest.approx(7.5)
        assert mc.GetBinError(1) ** 2 == pytest.approx(2.25)
        assert dy.GetBinContent(1) == pytest.approx(6.0)
        assert dy.GetBinError(1) ** 2 == pytest.approx(1.8)
        assert others.GetBinContent(1) == pytest.approx(1.5)
        assert others.GetBinError(1) ** 2 == pytest.approx(0.45)
        assert json.loads(classification.GetTitle())["groups"] == {
            "DY": ["DY"],
            "Others": ["OTHER"],
        }
        assert ratio.GetPointY(0) == pytest.approx(3.0 / 7.5)
        assert band.GetErrorYhigh(0) == pytest.approx(1.5 / 7.5)
    finally:
        output.Close()

    csv_text = Path(receipt["outputs"]["csv"]).read_text()
    assert "mc_group_classification_source" in csv_text.splitlines()[0]
    assert "mc_dy_yield" in csv_text.splitlines()[0]
    assert "mc_dy_variance" in csv_text.splitlines()[0]
    assert "mc_others_yield" in csv_text.splitlines()[0]
    assert "mc_others_variance" in csv_text.splitlines()[0]
    before = dict(receipt["output_sha256"])
    with pytest.raises(FileExistsError, match="Refusing to overwrite"):
        make_period_plot(
            dataset,
            "DY_ALL",
            "Z0_mass",
            "2024I",
            luminosity_source,
            output_dir,
        )
    assert receipt["output_sha256"] == before


def test_period_renderer_uses_solid_stepfilled_stack_and_larger_legend(
    tmp_path, monkeypatch
):
    import matplotlib.axes

    stairs_calls = []
    band_calls = []
    errorbar_calls = []
    legend_calls = []
    tick_params_calls = []
    original_stairs = matplotlib.axes.Axes.stairs
    original_fill_between = matplotlib.axes.Axes.fill_between
    original_errorbar = matplotlib.axes.Axes.errorbar
    original_tick_params = matplotlib.axes.Axes.tick_params
    original_legend = matplotlib.axes.Axes.legend

    def reject_bar(*args, **kwargs):
        raise AssertionError("period MC groups must not use per-bin bar rectangles")

    def record_stairs(self, *args, **kwargs):
        stairs_calls.append(dict(kwargs))
        return original_stairs(self, *args, **kwargs)

    def record_fill_between(self, *args, **kwargs):
        band_calls.append(dict(kwargs))
        return original_fill_between(self, *args, **kwargs)

    def record_errorbar(self, *args, **kwargs):
        errorbar_calls.append((args, dict(kwargs)))
        return original_errorbar(self, *args, **kwargs)

    def record_legend(self, *args, **kwargs):
        legend_calls.append(dict(kwargs))
        return original_legend(self, *args, **kwargs)

    def record_tick_params(self, *args, **kwargs):
        tick_params_calls.append(dict(kwargs))
        return original_tick_params(self, *args, **kwargs)

    monkeypatch.setattr(matplotlib.axes.Axes, "bar", reject_bar)
    monkeypatch.setattr(matplotlib.axes.Axes, "stairs", record_stairs)
    monkeypatch.setattr(matplotlib.axes.Axes, "fill_between", record_fill_between)
    monkeypatch.setattr(matplotlib.axes.Axes, "errorbar", record_errorbar)
    monkeypatch.setattr(matplotlib.axes.Axes, "legend", record_legend)
    monkeypatch.setattr(matplotlib.axes.Axes, "tick_params", record_tick_params)
    config_path, root_path = _fixture(tmp_path)
    dataset = validate_dataset(config_path, root_path)
    make_period_plot(
        dataset,
        "DY_ALL",
        "Z0_mass",
        "2024I",
        "trigger_any",
        tmp_path / "solid_stack",
    )

    assert len(stairs_calls) == 3
    assert len(errorbar_calls) >= 1
    assert list(errorbar_calls[0][0][1]) == [3.0]
    assert len(errorbar_calls[0][0][0]) == 1
    group_calls = [call for call in stairs_calls if call["fill"] is True]
    line_calls = [call for call in stairs_calls if call["fill"] is False]
    assert len(group_calls) == 2
    assert all(call["edgecolor"] == "none" for call in group_calls)
    assert all(call["linewidth"] == 0.0 for call in group_calls)
    assert line_calls == [
        {
            "fill": False,
            "color": "#1F5F8B",
            "linewidth": 1.6,
            "label": "_nolegend_",
            "zorder": 7,
        }
    ]
    assert any(
        call.get("facecolor") == "#1F5F8B"
        and call.get("edgecolor") == "#1F5F8B"
        and call.get("alpha") == 0.18
        and call.get("hatch") == "////"
        for call in band_calls
    )
    assert len(legend_calls) == 1
    assert legend_calls[0]["fontsize"] >= 13.0
    assert legend_calls[0]["handlelength"] >= 1.9
    assert [label.split("\n", 1)[0] for label in legend_calls[0]["labels"]] == [
        "Data",
        "DY",
        "Others",
        "Total MC",
    ]
    assert all("MC stat. unc." not in label for label in legend_calls[0]["labels"])
    assert all("N=" not in label for label in legend_calls[0]["labels"])
    assert isinstance(legend_calls[0]["handles"][-1], _OverlayLegendTuple)
    assert _OverlayLegendTuple in legend_calls[0]["handler_map"]
    explicit_tick_calls = [
        call
        for call in tick_params_calls
        if call.get("which") == "both"
        and call.get("top") is False
        and call.get("right") is False
    ]
    assert len(explicit_tick_calls) == 2


def test_concise_output_stems_are_unique_and_path_bounded():
    from category_config import build_categories

    categories = tuple(
        name
        for name in build_categories("RUN_STABILITY", "standard")[1]
        if not name.startswith("DY_ENRICHED")
    )
    assert len(categories) == 48
    observables = (
        "Z0_mass",
        "Z0_pt",
        "lZ1_pt",
        "lZ2_pt",
        "lZ1_eta",
        "lZ2_eta",
    )
    periods = ("2022B", "2022C", "2022D", "2022E", "2022F", "2022G")
    period_stems = {
        period_output_stem(period, observable, category, "trigger_any")
        for category in categories
        for observable in observables
        for period in periods
    }
    assert len(period_stems) == 48 * 6 * 6
    assert all(len(stem) <= MAX_OUTPUT_STEM_LENGTH for stem in period_stems)
    assert all(
        len(f"{stem}.json") <= MAX_OUTPUT_STEM_LENGTH + 5 for stem in period_stems
    )

    datasets = [
        {"contract": {"analysis_era": era}}
        for era in ("2022", "2022EE", "2023", "2023BPix", "2024")
    ]
    stability_stems = {
        stability_output_stem(datasets, observable, category, "trigger_any")
        for category in categories
        for observable in observables
    }
    assert len(stability_stems) == 48 * 6
    assert "stability_Zmass_DY_ALL_trigger_any_2022-2024" in stability_stems
    assert all(len(stem) <= MAX_OUTPUT_STEM_LENGTH for stem in stability_stems)
    chi2_stems = {
        chi2_output_stem(datasets, observable, category, "trigger_any")
        for category in categories
        for observable in observables
    }
    assert len(chi2_stems) == 48 * 6
    assert "chi2_Zpt_DY_ALL_trigger_any_2022-2024" in chi2_stems
    assert all(len(stem) <= MAX_OUTPUT_STEM_LENGTH for stem in chi2_stems)
    assert period_output_stem("2022B", "Z0_mass", "DY/A", "trigger_any") != (
        period_output_stem("2022B", "Z0_mass", "DY-A", "trigger_any")
    )


def test_period_two_group_aggregation_applies_process_scales_before_sumw2(tmp_path):
    config_path, root_path = _fixture(tmp_path)
    dataset = validate_dataset(config_path, root_path)
    dataset["config"]["plot"]["plot"]["DY"]["scale"] = 2.0
    dataset["config"]["plot"]["plot"]["OTHER"]["scale"] = 0.5
    receipt = make_period_plot(
        dataset,
        "DY_ALL",
        "Z0_mass",
        "2024I",
        "trigger_any",
        tmp_path / "scaled_groups",
    )
    assert receipt["mc_yield"] == pytest.approx(19.5)
    assert receipt["mc_variance"] == pytest.approx(11.025)
    assert receipt["mc_grouping"]["process_scales_before_aggregation"] == {
        "DY": 2.0,
        "OTHER": 0.5,
    }
    assert receipt["mc_grouping"]["group_totals_after_period_scale"]["DY"] == {
        "yield": pytest.approx(18.0),
        "variance": pytest.approx(10.8),
    }
    assert receipt["mc_grouping"]["group_totals_after_period_scale"]["Others"] == {
        "yield": pytest.approx(1.5),
        "variance": pytest.approx(0.225),
    }


def test_period_grouping_fails_closed_on_ambiguous_compiled_membership(tmp_path):
    config_path, root_path = _fixture(tmp_path)
    dataset = validate_dataset(config_path, root_path)
    dataset["config"]["plot"]["groupPlot"]["Other"]["samples"].append("DY")
    handle = ROOT.TFile.Open(str(root_path), "READ")
    try:
        process_hists = {}
        for process in dataset["processes"]:
            hist = handle.Get(f"DY_ALL/Z0_mass/histo_{process}").Clone()
            hist.SetDirectory(0)
            process_hists[process] = hist
    finally:
        handle.Close()
    with pytest.raises(RuntimeError, match="classification is ambiguous"):
        _period_mc_groups(dataset, process_hists)


def test_period_ratio_autorange_is_robust_and_records_clipped_features():
    rows = []
    for index in range(1, 11):
        rows.append(
            {
                "bin": index,
                "valid": True,
                "ratio": 8.0 if index == 10 else 0.96 + 0.01 * index,
                "ratio_error_low": 0.08,
                "ratio_error_high": 5.0 if index == 9 else 0.09,
                "data_yield": 100.0,
                "data_error_low": 10.0,
                "data_error_high": 11.0,
                "mc_yield": 10.0,
                "mc_stat_uncertainty": 50.0 if index == 8 else 1.0,
            }
        )
    display = period_ratio_autorange(rows)
    low, high = display["range"]
    assert high - low >= 0.4
    assert low < 1.0 < high
    assert high < 2.0
    assert display["clipped_bins"]["data_central_above"] == [10]
    assert display["clipped_bins"]["data_interval_above"] == [9, 10]
    assert display["clipped_bins"]["mc_band_below"] == [8]
    assert display["clipped_bins"]["mc_band_above"] == [8]
    assert display["policy"]["style_provenance"]["runtime_dependency"] is False


def test_period_ratio_autorange_keeps_small_samples_and_minimum_span():
    rows = [
        {
            "bin": index,
            "valid": True,
            "ratio": ratio,
            "ratio_error_low": 0.02,
            "ratio_error_high": 0.03,
            "data_yield": 100.0,
            "data_error_low": 10.0,
            "data_error_high": 11.0,
            "mc_yield": 100.0,
            "mc_stat_uncertainty": 1.0,
        }
        for index, ratio in enumerate((0.98, 1.0, 1.02), 1)
    ]
    display = period_ratio_autorange(rows)
    assert 0.4 <= display["range"][1] - display["range"][0] <= 0.5
    assert all(not bins for bins in display["clipped_bins"].values())


def test_period_ratio_autorange_sparse_precision_falls_back_and_marks_outliers():
    values = (
        (1, 0.0, 0.0, 1.8410, 0.0, 0.0, 15.887, 0.1159, 0.0468),
        (2, 2.0, 1.2918, 2.6379, 4.9031, 3.1663, 6.4650, 0.4079, 0.0899),
        (3, 3.0, 1.6327, 2.9182, 77.3758, 42.101, 75.259, 0.0388, 0.7703),
        (4, 4.0, 1.9143, 3.1628, 4.1688, 1.9954, 3.2964, 0.9595, 0.2505),
        (5, 5.0, 2.1597, 3.3825, 0.6552, 0.2830, 0.4433, 7.6311, 0.9544),
        (6, 17.0, 4.0822, 5.2037, 1.3926, 0.3344, 0.4263, 12.2073, 1.7071),
        (8, 6.0, 2.3799, 3.5836, 1.8102, 0.7180, 1.0812, 3.3145, 0.3660),
    )
    rows = [
        {
            "bin": bin_index,
            "valid": True,
            "data_yield": data_yield,
            "data_error_low": data_low,
            "data_error_high": data_high,
            "ratio": ratio,
            "ratio_error_low": ratio_low,
            "ratio_error_high": ratio_high,
            "mc_yield": mc_yield,
            "mc_stat_uncertainty": mc_error,
        }
        for (
            bin_index,
            data_yield,
            data_low,
            data_high,
            ratio,
            ratio_low,
            ratio_high,
            mc_yield,
            mc_error,
        ) in values
    ]
    display = period_ratio_autorange(rows)
    assert display["policy"]["range_mode"] == "unity_baseline_sparse_fallback"
    assert display["policy"]["informative_bins"] == [6]
    assert display["range"][1] < 2.0
    assert {2, 3, 4, 8} <= set(display["clipped_bins"]["data_central_above"])
    assert display["policy"]["excluded_insufficient_population_bins"] == [6]


def test_period_ratio_autorange_preserves_coherent_precise_shift():
    rows = [
        {
            "bin": index,
            "valid": True,
            "data_yield": 100.0,
            "data_error_low": 9.5,
            "data_error_high": 10.5,
            "ratio": 1.52 + 0.01 * index,
            "ratio_error_low": 0.06,
            "ratio_error_high": 0.07,
            "mc_yield": 65.0,
            "mc_stat_uncertainty": 2.0,
        }
        for index in range(1, 7)
    ]
    display = period_ratio_autorange(rows)
    assert display["policy"]["range_mode"] == "informative_median_mad_core"
    assert display["policy"]["range_central_input_bins"] == [1, 2, 3, 4, 5, 6]
    assert display["range"][0] <= 1.0 < 1.58 <= display["range"][1]
    assert not display["clipped_bins"]["data_central_above"]
    assert not display["clipped_bins"]["data_central_below"]


def test_physical_period_plot_fails_before_outputs_for_zero_luminosity(tmp_path):
    config_path, root_path = _fixture(tmp_path, luminosities=(0.0, 0.0))
    dataset = validate_dataset(config_path, root_path)
    output_dir = tmp_path / "guarded"
    with pytest.raises(RuntimeError, match="nonpositive trigger_any recorded"):
        make_period_plot(
            dataset,
            "DY_ALL",
            "Z0_mass",
            "2024I",
            "trigger_any",
            output_dir,
        )
    assert not output_dir.exists()


def test_list_and_validate_cli_do_not_require_luminosity_source(tmp_path, capsys):
    config_path, root_path = _fixture(tmp_path)
    common = ["--config", str(config_path), "--input", str(root_path)]

    assert main(["list", *common, "--json"]) == 0
    inventory = json.loads(capsys.readouterr().out)
    assert inventory["analysis_era"] == "2024"
    assert inventory["physical_run_periods"] == [
        {
            "configured_run_periods": ["2024I_v1", "2024I_v2"],
            "first_run": 101,
            "last_run": 102,
            "period": "2024I",
            "run_count": 2,
        }
    ]

    assert main(["validate", *common]) == 0
    assert "era: 2024" in capsys.readouterr().out

    chi2_dir = tmp_path / "chi2_cli"
    assert (
        main(
            [
                "chi2-vs-run",
                "--dataset",
                "2024",
                str(config_path),
                str(root_path),
                "--category",
                "DY_ALL",
                "--observable",
                "Z0_mass",
                "--luminosity-source",
                "auto",
                "--output-dir",
                str(chi2_dir),
            ]
        )
        == 0
    )
    cli_receipt = json.loads(capsys.readouterr().out)
    assert cli_receipt["kind"] == "reduced_chi2_vs_run"


def test_auto_luminosity_source_uses_compiled_category_mapping(tmp_path):
    config_path, root_path = _fixture(tmp_path)
    dataset = validate_dataset(config_path, root_path)
    dataset["contract"]["category_luminosity_sources"] = {"DY_ALL": "trigger_any"}
    assert resolve_luminosity_source([dataset], "DY_ALL", "auto") == "trigger_any"


def test_schema_three_auto_luminosity_source_fails_without_mapping(tmp_path):
    config_path, root_path = _fixture(tmp_path)
    dataset = validate_dataset(config_path, root_path)
    dataset["contract"]["category_luminosity_sources"] = {}
    with pytest.raises(RuntimeError, match="no compiled luminosity source mapping"):
        resolve_luminosity_source([dataset], "DY_ALL", "auto")


def test_validation_requires_delivered_luminosity_metadata(tmp_path):
    config_path, root_path = _fixture(tmp_path)
    output = ROOT.TFile.Open(str(root_path), "UPDATE")
    metadata = output.GetDirectory("run_stability/metadata")
    metadata.Delete("nominal_delivered_lumi_fb;*")
    output.Close()
    with pytest.raises(RuntimeError, match="nominal_delivered_lumi_fb"):
        validate_dataset(config_path, root_path)
