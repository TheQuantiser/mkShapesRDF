cuts = {}

preselections = ""
preselections += "(Trigger_ElMu || Trigger_sngMu || Trigger_dblMu || Trigger_sngEl || Trigger_dblEl)"
preselections += " && nLepton >= 2"
preselections += " && L2TightLeading2"

cuts["zz_cr"] = {
    # "expr": "abs(Z0_mass - 91.1876) < 30",
    "expr": "(Z0_mass > 30.) && (lZ1_pt > 10.) && (lZ1_pt > 10.)",
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
        "ALL": "(Z0_mass > 30.) && (lZ1_pt > 10.) && (lZ1_pt > 10.)",
    },
}
