import json
from pathlib import Path
import zlib

import cloudpickle
import pytest


ROOT = pytest.importorskip("ROOT")

from plot_run_stability import (  # noqa: E402
    garwood_interval,
    main,
    make_ratio_vs_run,
    make_run_plot,
    mc_ratio_covariance,
    ratio_display_summary,
    ratio_with_uncertainty,
    resolve_luminosity_source,
    validate_dataset,
)


def _fixture(tmp_path, era="2024", runs=(101, 102), luminosities=(1.0, 2.0)):
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
            {"run": run, "recorded_fb": lumi, "delivered_fb": lumi}
            for run, lumi in zip(runs, luminosities)
        ],
        "trigger_any": [
            {"run": run, "recorded_fb": lumi, "delivered_fb": lumi}
            for run, lumi in zip(runs, luminosities)
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


def test_poisson_and_mc_uncertainty_propagation():
    low, high = garwood_interval(0)
    assert low == 0.0
    assert high > 0.0
    result = ratio_with_uncertainty(4.0, 2.0, 0.25)
    assert result["value"] == pytest.approx(2.0)
    assert result["error_low"] > (4.0 - result["data_low"]) / 2.0
    with pytest.raises(RuntimeError, match="integer count"):
        ratio_with_uncertainty(1.5, 2.0, 0.25)


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


def test_ratio_display_uses_semantic_limits_and_preserves_outliers():
    rows = [
        {"era": "2022", "run": 1, "ratio": 0.49, "valid": True, "invalid_reason": None},
        {"era": "2022", "run": 2, "ratio": 1.00, "valid": True, "invalid_reason": None},
        {"era": "2022", "run": 3, "ratio": 1.51, "valid": True, "invalid_reason": None},
        {
            "era": "2022",
            "run": 4,
            "ratio": None,
            "valid": False,
            "invalid_reason": "zero_luminosity",
        },
    ]
    display = ratio_display_summary(rows)
    assert [point["run"] for point in display["below"]] == [1]
    assert [point["run"] for point in display["in_range"]] == [2]
    assert [point["run"] for point in display["above"]] == [3]
    assert [point["run"] for point in display["invalid"]] == [4]


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
    assert ratio_receipt["schema_version"] == 2
    assert ratio_receipt["presentation"]["ratio_display_range"] == [0.5, 1.5]
    assert ratio_receipt["presentation"]["canvas_pixels"] == [1500, 840]
    assert [
        point["run"] for point in ratio_receipt["presentation"]["out_of_range"]["below"]
    ] == [101, 102]
    assert ratio_receipt["presentation"]["selected_run_labels"] == [
        {"bin": 1, "run": 101},
        {"bin": 2, "run": 102},
    ]
    receipt_path = next(ratio_dir.glob("*.json"))
    assert json.loads(receipt_path.read_text())["kind"] == "data_mc_ratio_vs_run"
    output = ROOT.TFile.Open(ratio_receipt["outputs"]["root"], "READ")
    try:
        assert output.Get("ratio_graph_garwood_plus_mcstat")
        assert output.Get("ratio_by_run").TestBit(ROOT.TH1.kNoStats)
        covariance = output.Get("ratio_covariance_mcstat")
        assert covariance and covariance.GetBinContent(1, 2) > 0.0
        assert covariance.GetXaxis().GetBinLabel(1) == "101"
    finally:
        output.Close()


def test_list_and_validate_cli_do_not_require_luminosity_source(tmp_path, capsys):
    config_path, root_path = _fixture(tmp_path)
    common = ["--config", str(config_path), "--input", str(root_path)]

    assert main(["list", *common, "--json"]) == 0
    inventory = json.loads(capsys.readouterr().out)
    assert inventory["analysis_era"] == "2024"

    assert main(["validate", *common]) == 0
    assert "era: 2024" in capsys.readouterr().out


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
