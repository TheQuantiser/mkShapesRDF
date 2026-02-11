cuts = {}

preselections = ""
preselections += "(Trigger_ElMu || (!Trigger_ElMu && (Trigger_sngMu || Trigger_dblMu)) || (!Trigger_ElMu && !Trigger_sngMu && !Trigger_dblMu && (Trigger_sngEl || Trigger_dblEl)))"
preselections += " && nLepton >= 4"
# preselections += " && Alt(Lepton_pt, 0, 0) > 25"
# preselections += " && Alt(Lepton_pt, 1, 0) > 15"
# preselections += " && Alt(Lepton_pt, 2, 0) > 10"
# preselections += " && Alt(Lepton_pt, 3, 0) > 10"
# preselections += " && Alt(Lepton_pt, 4, 0) < 10"
# preselections += " && Z0_mass > 12"
preselections += " && bVeto"
# preselections += " && sumLeptonCharge == 0"

cuts["zz_cr"] = {
    # "expr": "abs(Z0_mass - 91.1876) < 15 && X_mass > 75 && X_mass < 105 && PuppiMET_pt < 35",
    expr": "abs(Z0_mass - 91.1876) < 15 && X_mass > 75 && X_mass < 105 && PuppiMET_pt < 35",
    "categories": {
        "XSF_ZEE": "X_isSF && Z0_isEE",
        "XSF_ZMM": "X_isSF && Z0_isMM",
        "XDF_ZEE": "X_isDF && Z0_isEE",
        "XDF_ZMM": "X_isDF && Z0_isMM",
    },
}
