cuts = {}

# https://github.com/TheQuantiser/mkShapesRDF/blob/4004a246f19a3001746b5f874aacbfe3f38c4368/mkShapesRDF/processor/data/TrigMaker_cfg.py#L1334
# https://github.com/cms-sw/cmssw/blob/master/PhysicsTools/NanoAOD/python/triggerObjects_cff.py

# 'EleMu'     : [ 'HLT_Mu23_TrkIsoVVL_Ele12_CaloIdL_TrackIdL_IsoVL', 'HLT_Mu12_TrkIsoVVL_Ele23_CaloIdL_TrackIdL_IsoVL_DZ', 'HLT_Mu8_TrkIsoVVL_Ele23_CaloIdL_TrackIdL_IsoVL_DZ'] ,
# 'DoubleMu'  : [ 'HLT_Mu17_TrkIsoVVL_Mu8_TrkIsoVVL_DZ_Mass3p8'] ,
# 'SingleMu'  : [ 'HLT_IsoMu24'] ,
# 'DoubleEle' : [ 'HLT_Ele23_Ele12_CaloIdL_TrackIdL_IsoVL'] ,
# 'SingleEle' : [ 'HLT_Ele30_WPTight_Gsf'] ,

preselections = ""
# preselections += "(Trigger_ElMu || (!Trigger_ElMu && (Trigger_sngMu || Trigger_dblMu)) || (!Trigger_ElMu && !Trigger_sngMu && !Trigger_dblMu && (Trigger_sngEl || Trigger_dblEl)))"
preselections += "!Trigger_ElMu && !Trigger_sngMu && !Trigger_dblMu && (Trigger_sngEl || Trigger_dblEl)"
preselections += " && nLepton >= 2"
# Keep Data/MC aligned at the same leading-lepton tightness; remove this line to disable.
preselections += " && L2TightLeading2"
preselections += " && PassesZZCR4lOrderedPt"
# preselections += " && Alt(Lepton_pt, 0, 0) > 25"
# preselections += " && Alt(Lepton_pt, 1, 0) > 15"
# preselections += " && Alt(Lepton_pt, 2, 0) > 10"
# preselections += " && Alt(Lepton_pt, 3, 0) > 10"
# preselections += " && Alt(Lepton_pt, 4, 0) < 10"
# preselections += " && Z0_mass > 12"
# preselections += " && bVeto"
# preselections += " && sumLeptonCharge == 0"

cuts["zz_cr"] = {
    "expr": "abs(Z0_mass - 91.1876) < 30",
    # "expr": "abs(Z0_mass - 91.1876) < 15 && X_mass > 75 && X_mass < 105 && PuppiMET_pt < 35",
    "categories": {
        # "XSF_ZEE": "X_isSF && Z0_isEE",
        # "XSF_ZMM": "X_isSF && Z0_isMM",
        # "XDF_ZEE": "X_isDF && Z0_isEE",
        # "XDF_ZMM": "X_isDF && Z0_isMM",
        "ZMM": "Z0_isMM",
        "ZEE": "Z0_isEE",
    },
}
