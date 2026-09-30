"""Bounded, read-only observations of the actual 2024 lepton producer modules.

Run one witness per process: the modules declare C++ helpers with fixed names.
This module does not alter the shared producer or write a HWWNano file.
"""

import argparse
import json
from pathlib import Path


MU_TIGHT = "Lepton_isTightMuon_cut_TightID_pfIsoTight_HWW_tthmva_67"
EL_TIGHT = "Lepton_isTightElectron_mvaWinter22V2Iso_WP90_tthMVA_Run3"


def _one(frame, columns):
    values = frame.df.AsNumpy(columns)
    if len(values[columns[0]]) != 1:
        raise RuntimeError("The witness did not survive this module stage")
    result = {}
    for name in columns:
        value = values[name][0]
        result[name] = value.tolist() if hasattr(value, "tolist") else int(value)
    return result


def run(pfn, entry, expected_key, is_mc, correct):
    import ROOT
    import mkShapesRDF
    from mkShapesRDF.processor.framework.mRDF import mRDF
    from mkShapesRDF.processor.modules.LeptonMaker import LeptonMaker
    from mkShapesRDF.processor.modules.LeptonSel import LeptonSel
    from mkShapesRDF.processor.modules.L2TightSelection import L2TightSelection

    ROOT.gROOT.SetBatch(True)
    if ROOT.IsImplicitMTEnabled():
        raise RuntimeError("RDataFrame Range requires implicit MT disabled")
    frame = mRDF().readRDF("Events", [pfn])
    frame.df = frame.df.Range(entry, entry + 1)
    frame = frame.Filter("((nElectron+nMuon)>1)")
    raw = _one(frame, ["run", "luminosityBlock", "event", "Electron_pt", "Electron_eta", "Electron_phi", "Muon_pt", "Muon_eta", "Muon_phi"])
    key = [int(raw[k]) for k in ("run", "luminosityBlock", "event")]
    if key != expected_key:
        raise ValueError(f"source entry/key mismatch: {key} != {expected_key}")
    values = []
    made = LeptonMaker().runModule(frame, values)
    before = _one(made, ["VetoLepton_pt", "VetoLepton_eta", "VetoLepton_phi", "VetoLepton_electronIdx", "VetoLepton_muonIdx"])
    selected = LeptonSel("Loose", 1, "Full2024v15").runModule(made, values)
    after = _one(selected, ["Lepton_pt", "Lepton_eta", "Lepton_phi", "Lepton_electronIdx", "Lepton_muonIdx", MU_TIGHT, EL_TIGHT, "isLoose"])
    # The definition is the actual producer expression. Map its prefilter
    # decisions by the original raw-object indices retained after filtering.
    positions = []
    for i, (ele, mu) in enumerate(zip(after["Lepton_electronIdx"], after["Lepton_muonIdx"])):
        source = before["VetoLepton_electronIdx"] if ele >= 0 else before["VetoLepton_muonIdx"]
        original = ele if ele >= 0 else mu
        hits = [j for j, idx in enumerate(source) if idx == original]
        if len(hits) != 1:
            raise ValueError("Ambiguous original lepton index")
        j = hits[0]
        flavor = "electron" if ele >= 0 else "muon"
        tight = EL_TIGHT if ele >= 0 else MU_TIGHT
        positions.append({"position": i, "flavor": flavor, "raw_index": original,
                          "prefilter_position": j,
                          "expected_tight": bool(after[tight][j]),
                          "stored_position_tight": bool(after[tight][i]),
                          "eta_associated": abs(after["Lepton_eta"][i] - (raw["Electron_eta"] if ele >= 0 else raw["Muon_eta"])[original]) < 1e-5,
                          "phi_associated": abs(after["Lepton_phi"][i] - (raw["Electron_phi"] if ele >= 0 else raw["Muon_phi"])[original]) < 1e-5})
    result = {"producer_package": str(Path(mkShapesRDF.__file__).resolve()),
              "stages_executed": ["chain_selection", "leptonMaker", "lepSel"],
              "raw": raw, "lepton_maker": before, "lepton_sel": after,
              "lepton_columns_after_lepton_sel": sorted(name for name in selected.GetColumnNames() if name.startswith(("Lepton_", "VetoLepton_"))),
              "retained_position_checks": positions,
              "tight_vector_lengths": {"electron": len(after[EL_TIGHT]), "muon": len(after[MU_TIGHT]), "retained": len(after["Lepton_pt"])}}
    if is_mc:
        gate = L2TightSelection("Full2024v15").runModule(selected, values)
        result["isolated_l2tight_pass"] = bool(gate.df.Count().GetValue())
        result["stages_executed"].append("isolated_l2tight")
        result["stage_limit"] = "Jet/JME, generator, weight, and formula modules were not run here; see separately verified prior full-chain ledger."
    else:
        result["stage_limit"] = "DATA trace stops after LeptonSel; the known Regrouped_* JME failure is not bypassed or described as full-chain success."
    if correct:
        if is_mc:
            raise ValueError("Correction witness is DATA only in this bounded demo")
        from mkShapesRDF.processor.modules.LeptonScaleSmearing import LeptonScaleSmearing
        # Observe the exact source expressions without changing their return
        # values, sequence, or the producer's dataframe. This records the
        # original permutation before the generic loop can redefine it.
        observed = {"loop_orders": [], "original_sorting_node": None}
        original_define = mRDF.Define
        original_names = mRDF.GetColumnNames

        def observed_define(frame, name, expression, *args, **kwargs):
            next_frame = original_define(frame, name, expression, *args, **kwargs)
            if name == "Lepton_sorting" and expression == "sortedIndices(Lepton_newPt)":
                observed["original_sorting_node"] = next_frame
            return next_frame

        def observed_names(frame):
            names = original_names(frame)
            if "Lepton_sorting" in names and "Lepton_rochesterSF" in names:
                observed["loop_orders"].append([name for name in names if name.startswith("Lepton_")])
            return names

        mRDF.Define = observed_define
        mRDF.GetColumnNames = observed_names
        try:
            corrected = LeptonScaleSmearing("Full2024v15", True).runModule(selected, values)
        finally:
            mRDF.Define = original_define
            mRDF.GetColumnNames = original_names
        if observed["original_sorting_node"] is None or not observed["loop_orders"]:
            raise RuntimeError("Correction permutation/loop instrumentation was not reached")
        result["correction_original_permutation"] = _one(observed["original_sorting_node"], ["Lepton_newPt", "Lepton_sorting"])
        result["correction_loop_column_order"] = observed["loop_orders"][-1]
        result["isolated_lepton_scale_data"] = _one(corrected, ["Lepton_pt", "Lepton_eta", "Lepton_phi", "Lepton_electronIdx", "Lepton_muonIdx", MU_TIGHT, EL_TIGHT])
        result["lepton_columns_after_isolated_correction"] = sorted(name for name in corrected.GetColumnNames() if name.startswith(("Lepton_", "VetoLepton_")))
        post = result["isolated_lepton_scale_data"]
        result["corrected_position_checks"] = [
            {"position": i, "raw_electron_index": idx,
             "eta_associated": abs(post["Lepton_eta"][i] - raw["Electron_eta"][idx]) < 1e-5,
             "phi_associated": abs(post["Lepton_phi"][i] - raw["Electron_phi"][idx]) < 1e-5}
            for i, idx in enumerate(post["Lepton_electronIdx"])
        ]
        result["correction_limit"] = "Actual leptonScale_data module ran directly after LeptonSel, without preceding JME. This is not a full DATA chain or snapshot; interpretation depends on the recorded permutation and loop order."
    else:
        result["correction_limit"] = "LeptonScaleSmearing not run for this witness; no naturally corrected-pT reorder is claimed."
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--pfn", required=True)
    parser.add_argument("--entry", type=int, required=True)
    parser.add_argument("--key", type=int, nargs=3, required=True)
    parser.add_argument("--mc", action="store_true")
    parser.add_argument("--correct", action="store_true")
    args = parser.parse_args()
    print(json.dumps(run(args.pfn, args.entry, args.key, args.mc, args.correct), sort_keys=True))
