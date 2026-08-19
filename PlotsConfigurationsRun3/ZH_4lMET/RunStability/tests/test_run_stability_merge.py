from pathlib import Path
import subprocess

import pytest


ROOT = pytest.importorskip("ROOT")

CONFIG_DIR = Path(__file__).resolve().parents[1]
HADD2 = CONFIG_DIR.parents[2] / "utils" / "bin" / "hadd2"


def _directory(output, path):
    current = output
    for component in path.split("/"):
        child = current.GetDirectory(component)
        if not child:
            child = current.mkdir(component)
        current = child
    current.cd()


def _ordinary(output, sample, values):
    _directory(output, "DY_ALL/Z0_mass")
    histogram = ROOT.TH1D(f"histo_{sample}", f"histo_{sample}", 2, 0.0, 2.0)
    histogram.Sumw2()
    for index, value in enumerate(values, 1):
        histogram.SetBinContent(index, value)
        histogram.SetBinError(index, value**0.5)
    histogram.Write()


def _data_auxiliary(output, values):
    _directory(output, "run_stability/DY_ALL/Z0_mass")
    histogram = ROOT.TH2D("histo_DATA", "histo_DATA", 2, 0.5, 2.5, 2, 0.0, 2.0)
    histogram.Sumw2()
    for index, value in enumerate(values, 1):
        histogram.SetBinContent(index, index, value)
        histogram.SetBinError(index, index, value**0.5)
        histogram.GetXaxis().SetBinLabel(index, str(355100 + index))
    histogram.Write()


def _metadata(output):
    _directory(output, "run_stability/metadata")
    values = {
        "nominal_delivered_lumi_fb": (0.10, 0.20),
        "nominal_recorded_lumi_fb": (0.09, 0.18),
        "trigger_any_delivered_lumi_fb": (0.08, 0.16),
        "trigger_any_recorded_lumi_fb": (0.07, 0.14),
    }
    for name, contents in values.items():
        histogram = ROOT.TH1D(name, name, 2, 0.5, 2.5)
        for index, value in enumerate(contents, 1):
            histogram.SetBinContent(index, value)
            histogram.SetBinError(index, 0.0)
            histogram.GetXaxis().SetBinLabel(index, str(355100 + index))
        histogram.Write()
    source = ROOT.TH1D("mc_source_lumi_fb", "mc_source_lumi_fb", 1, 0.5, 1.5)
    source.SetBinContent(1, 8.0)
    source.SetBinError(1, 0.0)
    source.Write()


def _write_worker(path, sample, values):
    output = ROOT.TFile(str(path), "RECREATE")
    try:
        _ordinary(output, sample, values)
        if sample == "DATA":
            _data_auxiliary(output, values)
            _metadata(output)
    finally:
        output.Close()


def test_unchanged_hadd2_merges_data_and_mc_without_multiplying_metadata(tmp_path):
    assert HADD2.is_file(), HADD2
    data_file = tmp_path / "data_worker.root"
    mc_file = tmp_path / "mc_worker.root"
    merged_file = tmp_path / "merged.root"
    _write_worker(data_file, "DATA", (2.0, 3.0))
    _write_worker(mc_file, "DY", (4.0, 5.0))

    subprocess.run(
        [str(HADD2), str(merged_file), str(data_file), str(mc_file)],
        check=True,
        text=True,
        capture_output=True,
    )

    merged = ROOT.TFile.Open(str(merged_file), "READ")
    assert merged and not merged.IsZombie()
    try:
        data = merged.Get("DY_ALL/Z0_mass/histo_DATA")
        mc = merged.Get("DY_ALL/Z0_mass/histo_DY")
        auxiliary = merged.Get("run_stability/DY_ALL/Z0_mass/histo_DATA")
        assert isinstance(data, ROOT.TH1) and not isinstance(data, ROOT.TH2)
        assert isinstance(mc, ROOT.TH1) and not isinstance(mc, ROOT.TH2)
        assert isinstance(auxiliary, ROOT.TH2)
        assert data.Integral(0, data.GetNbinsX() + 1) == pytest.approx(5.0)
        assert mc.Integral(0, mc.GetNbinsX() + 1) == pytest.approx(9.0)
        assert auxiliary.Integral(0, 3, 0, 3) == pytest.approx(5.0)
        assert not merged.Get("run_stability/DY_ALL/Z0_mass/histo_DY")

        expected = {
            "nominal_delivered_lumi_fb": (0.10, 0.20),
            "nominal_recorded_lumi_fb": (0.09, 0.18),
            "trigger_any_delivered_lumi_fb": (0.08, 0.16),
            "trigger_any_recorded_lumi_fb": (0.07, 0.14),
        }
        for name, values in expected.items():
            histogram = merged.Get(f"run_stability/metadata/{name}")
            assert isinstance(histogram, ROOT.TH1D)
            assert tuple(
                histogram.GetBinContent(index) for index in (1, 2)
            ) == pytest.approx(values)
            assert tuple(histogram.GetBinError(index) for index in (1, 2)) == (0.0, 0.0)
        source = merged.Get("run_stability/metadata/mc_source_lumi_fb")
        assert isinstance(source, ROOT.TH1D)
        assert source.GetBinContent(1) == pytest.approx(8.0)
    finally:
        merged.Close()


def test_mkplot_configuration_does_not_enumerate_auxiliary_hierarchy(load_state):
    state = load_state()
    assert "run_stability" not in state["cuts"]
    assert "run_stability" not in state["variables"]
    assert all(
        len(definition["name"].split(":")) == 1
        for definition in state["variables"].values()
    )
