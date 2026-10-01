"""Synthetic ROOT checks of the actual scale module's association boundary.

The test-only correction result forces a three-cycle pT permutation. It does
not test calibration payloads, correction formulas, or production random draws.
Each case uses a fresh process so its C++ helper cannot replace a real helper in
another test. Run after activating the supported framework runtime.
"""

import json
from pathlib import Path
import subprocess
import sys

import pytest


@pytest.mark.parametrize("is_data", [True, False])
@pytest.mark.parametrize("reverse_columns", [False, True])
def test_corrected_pt_keeps_each_object_array_associated(is_data, reverse_columns):
    command = [
        sys.executable,
        str(Path(__file__).resolve()),
        str(int(is_data)),
        str(int(reverse_columns)),
    ]
    result = subprocess.run(command, capture_output=True, text=True, timeout=90)
    assert result.returncode == 0, result.stdout + result.stderr
    observed = json.loads(result.stdout.splitlines()[-1])
    expected = {
        "Lepton_pt": [120.0, 100.0, 80.0],
        "Lepton_eta": [0.2, 1.3, -0.1],
        "Lepton_phi": [0.5, -0.5, 0.0],
        "Lepton_pdgId": [13, -13, 11],
        "Lepton_electronIdx": [-1, -1, 0],
        "Lepton_muonIdx": [0, 1, -1],
        "Lepton_isTightElectron_Test": [0, 0, 1],
        "Lepton_isTightMuon_Test": [1, 1, 0],
        "isLoose": [0, 1, 1],
        "Lepton_RecoSF": [1.0, 1.1, 0.9],
        "Lepton_RecoSF_leptonSFup": [1.1, 1.2, 1.0],
        "Lepton_RecoSF_leptonSFdo": [0.9, 1.0, 0.8],
        "Lepton_tightMuon_Test_IdIsoSF": [0.9, 1.0, 0.8],
        "Lepton_tightElectron_Test_TotSF_Up": [1.2, 1.3, 1.1],
        "Lepton_rochesterSF": [120.0 / 90.0, 100.0 / 80.0, 80.0 / 100.0],
        # Independently evaluated from MET + sum((newPt-oldPt)*(cos,sin)).
        "PuppiMET_pt": 123.9718648007069,
        "PuppiMET_phi": 0.03868177020148027,
        "PFMET_pt": 223.93045545675218,
        "PFMET_phi": 0.021411208711274197,
        "Lepton_diagnostic_count": 3,
    }
    if not is_data:
        expected.update(
            {
                "Lepton_pt_ScaleUp": [130.0, 110.0, 90.0],
                "Lepton_pt_ScaleDo": [110.0, 90.0, 70.0],
                "Lepton_pt_ResUp": [122.0, 104.0, 81.0],
                "Lepton_pt_ResDo": [118.0, 96.0, 79.0],
                "Lepton_pt_leptonScaleup": [130.0, 110.0, 90.0],
                "Lepton_pt_leptonScaledo": [110.0, 90.0, 70.0],
                "Lepton_pt_leptonResolutionup": [122.0, 104.0, 81.0],
                "Lepton_pt_leptonResolutiondo": [118.0, 96.0, 79.0],
                "Lepton_rochesterSF_leptonScaleup": [
                    120.0 / 130.0,
                    100.0 / 110.0,
                    80.0 / 90.0,
                ],
                "Lepton_rochesterSF_leptonScaledo": [
                    120.0 / 110.0,
                    100.0 / 90.0,
                    80.0 / 70.0,
                ],
                "Lepton_rochesterSF_leptonResolutionup": [
                    120.0 / 122.0,
                    100.0 / 104.0,
                    80.0 / 81.0,
                ],
                "Lepton_rochesterSF_leptonResolutiondo": [
                    120.0 / 118.0,
                    100.0 / 96.0,
                    80.0 / 79.0,
                ],
            }
        )
        # Preserve the existing pre-sort MET response to each pT variation.
        for tag, puppi_pt, puppi_phi, pf_pt, pf_phi in (
            ("leptonScaleup", 72.44834876219255, 0.0, 172.44834876219255, 0.0),
            ("leptonScaledo", 127.55165123780745, 0.0, 227.55165123780745, 0.0),
            (
                "leptonResolutionup",
                93.7394087530326,
                0.010229078800264274,
                193.7368774371562,
                0.004949264200227882,
            ),
            (
                "leptonResolutiondo",
                106.26982121893789,
                -0.009022919930018669,
                206.26772402916913,
                -0.004648592188126758,
            ),
        ):
            expected[f"PuppiMET_pt_{tag}"] = puppi_pt
            expected[f"PuppiMET_phi_{tag}"] = puppi_phi
            expected[f"PFMET_pt_{tag}"] = pf_pt
            expected[f"PFMET_phi_{tag}"] = pf_phi
    for name, values in expected.items():
        assert observed["values"][name] == pytest.approx(values), name
    assert observed["values"]["Lepton_diagnostic_matrix"] == [[1, 2], [3, 4, 5]]
    assert observed["temporary_columns"] == []


def _synthetic_run(is_data, reverse_columns):
    import ROOT
    from mkShapesRDF.processor.framework.mRDF import mRDF
    from mkShapesRDF.processor.modules.LeptonScaleSmearing import LeptonScaleSmearing

    ROOT.gROOT.SetBatch(True)
    assert ROOT.gInterpreter.Declare(
        """
        #include <TLorentzVector.h>
        using ROOT::RVecF;
        using ROOT::RVecI;
        using ROOT::RVecD;
        using namespace ROOT::VecOps;
        using namespace std;
        std::vector<RVecF> doLeptonScale(RVecF, RVecF, RVecF, RVecI,
            RVecI, RVecI, RVecI, RVecF, RVecF, RVecI, RVecF, float, bool) {
            return {{80.f,120.f,100.f}, {90.f,130.f,110.f},
                    {70.f,110.f,90.f}, {81.f,122.f,104.f}, {79.f,118.f,96.f}};
        }
    """
    )
    # Calibration setup is outside this structural test; the actual module,
    # mRDF propagation, ROOT Take, sortedIndices, and CorrectMET run unchanged.
    ROOT.gROOT.ProcessLine = lambda _line: 0
    mRDF.GetColumnNames = lambda self: sorted(self.cols, reverse=reverse_columns)
    frame = mRDF().readRDF(1)
    columns = {
        "Lepton_pt": "ROOT::RVecF{100.f,90.f,80.f}",
        "Lepton_eta": "ROOT::RVecF{-.1f,.2f,1.3f}",
        "Lepton_phi": "ROOT::RVecF{0.f,.5f,-.5f}",
        "Lepton_pdgId": "ROOT::RVecI{11,13,-13}",
        "Lepton_electronIdx": "ROOT::RVecI{0,-1,-1}",
        "Lepton_muonIdx": "ROOT::RVecI{-1,0,1}",
        "Lepton_isTightElectron_Test": "ROOT::RVecI{1,0,0}",
        "Lepton_isTightMuon_Test": "ROOT::RVecI{0,1,1}",
        "isLoose": "ROOT::RVecI{1,0,1}",
        "Lepton_RecoSF": "ROOT::RVecF{.9f,1.f,1.1f}",
        "Lepton_tightMuon_Test_IdIsoSF": "ROOT::RVecF{.8f,.9f,1.f}",
        "Lepton_tightElectron_Test_TotSF_Up": "ROOT::RVecF{1.1f,1.2f,1.3f}",
        "Lepton_rochesterSF": "ROOT::RVecF{9.f,8.f,7.f}",
        "Lepton_diagnostic_count": "3",
        "Lepton_diagnostic_matrix": "std::vector<ROOT::RVecF>{ROOT::RVecF{1.f,2.f}, ROOT::RVecF{3.f,4.f,5.f}}",
        "Muon_charge": "ROOT::RVecI{-1,1}",
        "Muon_nTrackerLayers": "ROOT::RVecI{10,12}",
        "Electron_seedGain": "ROOT::RVecF{12.f}",
        "Electron_r9": "ROOT::RVecF{.9f}",
        "Electron_deltaEtaSC": "ROOT::RVecF{0.f}",
        "run": "1u",
        "PuppiMET_pt": "100.f",
        "PuppiMET_phi": "0.f",
        "PFMET_pt": "200.f",
        "PFMET_phi": "0.f",
    }
    for name, expression in columns.items():
        frame = frame.Define(name, expression)
    frame = frame.Vary(
        "Lepton_RecoSF",
        "ROOT::RVec<ROOT::RVecF>{"
        "ROOT::RVecF{1.f,1.1f,1.2f}, ROOT::RVecF{.8f,.9f,1.f}}",
        ["up", "do"],
        "leptonSF",
    )
    module = LeptonScaleSmearing.__new__(LeptonScaleSmearing)
    module.isData = is_data
    module.era = "Full2024v15"
    module.year_key = "2024"
    module.columnsToDrop = []
    module.muoncorrection_file = module.elecorrection_file = "not-used-in-test"
    module.muonscale_path = module.macroele_path = "not-used-in-test"
    corrected = module.runModule(frame, [])
    names = [
        name
        for name in corrected.GetColumnNames()
        if name.startswith("Lepton_")
        or name == "isLoose"
        or name.startswith(("PuppiMET_", "PFMET_"))
    ]
    arrays = corrected.df.AsNumpy(names)
    values = {}
    for name in names:
        value = arrays[name][0]
        if name == "Lepton_diagnostic_matrix":
            values[name] = [list(row) for row in value]
        else:
            values[name] = value.tolist() if hasattr(value, "tolist") else float(value)
    return {
        "values": values,
        "temporary_columns": sorted(
            name
            for name in corrected.GetColumnNames()
            if name
            in {
                "Lepton_sorting",
                "Lepton_newPt",
                "Lepton_ScaleSmearing",
                "PuppiMET_LeptonScale",
                "PFMET_LeptonScale",
            }
        ),
    }


if __name__ == "__main__":
    print(json.dumps(_synthetic_run(bool(int(sys.argv[1])), bool(int(sys.argv[2])))))
