from pathlib import Path
import runpy

import pytest


def test_combined_output_trees_are_not_histogram_categories(tmp_path):
    ROOT = pytest.importorskip("ROOT")
    path = tmp_path / "combined.root"
    f = ROOT.TFile.Open(str(path), "RECREATE")
    f.mkdir("S8_Z_BRIDGE/yield", "", True).cd()
    ROOT.TH1D("histo_MC", "", 1, 0, 2).Write()
    f.mkdir("trees/S8_Z_BRIDGE/MC", "", True)
    f.Close()
    namespace = runpy.run_path(
        str(Path(__file__).resolve().parents[1] / "make_summary.py")
    )
    reader = namespace["Reader"]({"2024": str(path)})
    try:
        assert reader.categories("2024") == ("S8_Z_BRIDGE",)
        assert reader.samples("2024") == ("MC",)
    finally:
        reader.close()
