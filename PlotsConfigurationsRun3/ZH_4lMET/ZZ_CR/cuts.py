cuts = {}

# https://github.com/TheQuantiser/mkShapesRDF/blob/682e4abbb2cb14e9d42482d0b90723ec64520b81/mkShapesRDF/processor/data/TrigMaker_cfg.py#L1082

preselections = ""
preselections += "(Trigger_ElMu || Trigger_sngMu || Trigger_dblMu || Trigger_sngEl || Trigger_dblEl)"
preselections += " && nLepton >= 2"
preselections += " && L2TightLeading2"

cuts["zz_cr"] = {
    # "expr": "abs(Z0_mass - 91.1876) < 30",
    "expr": "(Z0_mass > 30.) && (lZ1_pt > 10.) && (lZ2_pt > 10.)",
    "categories": {
        # "XSF_ZEE": "X_isSF && Z0_isEE",
        # "XSF_ZMM": "X_isSF && Z0_isMM",
        # "XDF_ZEE": "X_isDF && Z0_isEE",
        # "XDF_ZMM": "X_isDF && Z0_isMM",
        # "XMM_ZEE": "X_isMM && Z0_isEE",
        # "XEE_ZEE": "X_isEE && Z0_isEE",
        # "XMM_ZMM": "X_isMM && Z0_isMM",
        # "XEE_ZMM": "X_isEE && Z0_isMM",
        # "ZMM": "Z0_isMM",
        # "ZEE": "Z0_isEE",
        "ALL": "(Z0_mass > 30.) && (lZ1_pt > 10.) && (lZ2_pt > 10.)",
    },
}

# DY-like trigger audit template:
# cuts["dy_like_2l_trigger_audit"] = {
#     "expr": (
#         "(Trigger_ElMu || Trigger_sngMu || Trigger_dblMu || Trigger_sngEl || Trigger_dblEl)"
#         " && nLepton >= 2"
#         " && ZZCR_hasValidZ0"
#         " && Z0_mass > 30."
#         " && lZ1_pt > 10."
#         " && lZ2_pt > 10."
#     ),
#     "categories": {
#         "MuonEG": "ZZCR_streamPriority_MuonEG",
#         "Muon": "ZZCR_streamPriority_Muon",
#         "EGamma": "ZZCR_streamPriority_EGamma",
#     },
# }
#
# Incremental ZZ-like trigger audit template:
# cuts["zz_like_4l_trigger_audit"] = {
#     "expr": (
#         "ZZCR_dyLike2lBaseline"
#         " && ZZCR_hasValidX"
#         " && (X_isSF || X_isDF)"
#         " && PassesZZCR4lOrderedPt"
#         " && m4l > 0."
#         " && sumLeptonCharge == 0"
#         " && bVeto"
#     ),
#     "categories": {
#         "X_SF": "X_isSF",
#         "X_DF": "X_isDF",
#         "MET_0_50": "PuppiMET_pt < 50.",
#         "MET_50_plus": "PuppiMET_pt >= 50.",
#     },
# }
