"""Disjoint Run-3 selections aligned with AN2019_238 Tables 37--39."""

import os

if "analysis_pass" not in globals() or "PAIR_ID_CONFIG" not in globals():
    from selection_config import PAIR_ID_CONFIG, analysis_pass


_PASS = analysis_pass(globals().get("ANALYSIS_PASS") or os.environ.get("ANALYSIS_PASS"))
ANALYSIS_PASS = _PASS["name"]

cuts = {}

# Reusable atomic predicates keep the explicit stream-inclusive/per-stream
# entries readable.
_CAT_STR_MUONEG = "(streamPriority_MuonEG)"
_CAT_STR_MUON = "(streamPriority_Muon)"
_CAT_STR_EGAMMA = "(streamPriority_EGamma)"
_CAT_ZEE = "(Z0_isEE)"
_CAT_ZMM = "(Z0_isMM)"
_CAT_XSF = "(X_isSF)"
_CAT_XDF = "(X_isDF)"
_CAT_XEE = "(X_isEE)"
_CAT_XMM = "(X_isMM)"

_TRIGGER_OR = (
    "(Trigger_ElMu || Trigger_sngMu || Trigger_dblMu || "
    "Trigger_sngEl || Trigger_dblEl)"
)

# The technical l2tight production gate is shared by all passes.  The forward
# horn veto is the detector-quality requirement used by the external Run-III
# HWW and control-region configurations in every supported era.  Reuse the
# existing diagnostic alias: it counts 30 < pT < 50 GeV jets at
# 2.5 < |eta| < 3.0, exactly matching their ``noJetInHorn`` definition.
preselections = f"{_TRIGGER_OR} && nLepton >= 2 && L2TightLeading2 && nJetInHorn == 0"

_Z1_PT = "Alt(Lepton_pt, Alt(Z0_idx, 0, -1), -999.f)"
_Z2_PT = "Alt(Lepton_pt, Alt(Z0_idx, 1, -1), -999.f)"
_Z1_PT_MIN, _Z2_PT_MIN = PAIR_ID_CONFIG["Z0_ptMins"]
_Z_PARENT_KIN = (
    f"(Z0_mass > 30.) && ({_Z1_PT} > {_Z1_PT_MIN:g})"
    f" && ({_Z2_PT} > {_Z2_PT_MIN:g})"
)
_DY_PARENT = f"{_TRIGGER_OR} && nLepton >= 2 && hasValidZ0 && {_Z_PARENT_KIN}"

_X1_PT = "Alt(Lepton_pt, Alt(X_idx, 0, -1), -999.f)"
_X2_PT = "Alt(Lepton_pt, Alt(X_idx, 1, -1), -999.f)"
_X1_PT_MIN, _X2_PT_MIN = PAIR_ID_CONFIG["X_ptMins"]
_X_PARENT_KIN = (
    f"(X_mass > 4.) && ({_X1_PT} > {_X1_PT_MIN:g})"
    f" && ({_X2_PT} > {_X2_PT_MIN:g})"
)

# Every four-lepton selection is an explicit extension of the DY baseline.
# This broad parent has no ordered-pT profile, Z window, MET requirement, or
# b veto; those belong to its physical children.
_FOURL_PRE = (
    f"{_DY_PARENT} && nLepton >= 4 && hasValidX && selectedIndicesDistinct"
    f" && {_X_PARENT_KIN} && m4l > 0. && sumLeptonCharge == 0"
)

_PHYSICAL_COMMON = (
    f"{_FOURL_PRE} && fifthLeptonVeto && Z0_mass > 12."
    " && physicalBtagVeto && abs(Z0_mass - 91.1876) < 15."
    " && Passes4lOrderedPt"
)

_ZZ_CONTROL_REGION = (
    f"{_PHYSICAL_COMMON}"
    " && X_mass > 75. && X_mass < 105. && PuppiMET_pt < 35."
)

_SIGNAL_XSF = (
    "X_isSF && X_mass > 10. && X_mass < 65."
    " && PuppiMET_pt > 35. && m4l > 140."
)
_SIGNAL_XDF = "X_isDF && X_mass > 10. && X_mass < 70. && PuppiMET_pt > 20."
_SIGNAL_REGION = f"{_PHYSICAL_COMMON} && (({_SIGNAL_XSF}) || ({_SIGNAL_XDF}))"

ALL_CUT_DEFINITIONS = {
    "inclusive_z_dy": {
        "expr": _DY_PARENT,
        "categories": {
            "STR_Inclusive__Z_ZEE__X_NA": _CAT_ZEE,
            "STR_Inclusive__Z_ZMM__X_NA": _CAT_ZMM,
            "STR_MuonEG__Z_ZEE__X_NA": f"{_CAT_STR_MUONEG} && {_CAT_ZEE}",
            "STR_MuonEG__Z_ZMM__X_NA": f"{_CAT_STR_MUONEG} && {_CAT_ZMM}",
            "STR_Muon__Z_ZEE__X_NA": f"{_CAT_STR_MUON} && {_CAT_ZEE}",
            "STR_Muon__Z_ZMM__X_NA": f"{_CAT_STR_MUON} && {_CAT_ZMM}",
            "STR_EGamma__Z_ZEE__X_NA": f"{_CAT_STR_EGAMMA} && {_CAT_ZEE}",
            "STR_EGamma__Z_ZMM__X_NA": f"{_CAT_STR_EGAMMA} && {_CAT_ZMM}",
        },
    },
    "four_lepton_base": {
        "expr": _FOURL_PRE,
        "categories": {
            "STR_Inclusive__Z_ZEE__X_XSF": f"{_CAT_ZEE} && {_CAT_XSF}",
            "STR_Inclusive__Z_ZEE__X_XDF": f"{_CAT_ZEE} && {_CAT_XDF}",
            "STR_Inclusive__Z_ZMM__X_XSF": f"{_CAT_ZMM} && {_CAT_XSF}",
            "STR_Inclusive__Z_ZMM__X_XDF": f"{_CAT_ZMM} && {_CAT_XDF}",
            "STR_MuonEG__Z_ZEE__X_XSF": f"{_CAT_STR_MUONEG} && {_CAT_ZEE} && {_CAT_XSF}",
            "STR_MuonEG__Z_ZEE__X_XDF": f"{_CAT_STR_MUONEG} && {_CAT_ZEE} && {_CAT_XDF}",
            "STR_MuonEG__Z_ZMM__X_XSF": f"{_CAT_STR_MUONEG} && {_CAT_ZMM} && {_CAT_XSF}",
            "STR_MuonEG__Z_ZMM__X_XDF": f"{_CAT_STR_MUONEG} && {_CAT_ZMM} && {_CAT_XDF}",
            "STR_Muon__Z_ZEE__X_XSF": f"{_CAT_STR_MUON} && {_CAT_ZEE} && {_CAT_XSF}",
            "STR_Muon__Z_ZEE__X_XDF": f"{_CAT_STR_MUON} && {_CAT_ZEE} && {_CAT_XDF}",
            "STR_Muon__Z_ZMM__X_XSF": f"{_CAT_STR_MUON} && {_CAT_ZMM} && {_CAT_XSF}",
            "STR_Muon__Z_ZMM__X_XDF": f"{_CAT_STR_MUON} && {_CAT_ZMM} && {_CAT_XDF}",
            "STR_EGamma__Z_ZEE__X_XSF": f"{_CAT_STR_EGAMMA} && {_CAT_ZEE} && {_CAT_XSF}",
            "STR_EGamma__Z_ZEE__X_XDF": f"{_CAT_STR_EGAMMA} && {_CAT_ZEE} && {_CAT_XDF}",
            "STR_EGamma__Z_ZMM__X_XSF": f"{_CAT_STR_EGAMMA} && {_CAT_ZMM} && {_CAT_XSF}",
            "STR_EGamma__Z_ZMM__X_XDF": f"{_CAT_STR_EGAMMA} && {_CAT_ZMM} && {_CAT_XDF}",
        },
    },
    "zz_control_region": {
        "expr": _ZZ_CONTROL_REGION,
        "categories": {
            "STR_Inclusive__Z_ZEE__X_XSF": f"{_CAT_ZEE} && {_CAT_XSF}",
            "STR_Inclusive__Z_ZEE__X_XDF": f"{_CAT_ZEE} && {_CAT_XDF}",
            "STR_Inclusive__Z_ZMM__X_XSF": f"{_CAT_ZMM} && {_CAT_XSF}",
            "STR_Inclusive__Z_ZMM__X_XDF": f"{_CAT_ZMM} && {_CAT_XDF}",
            "STR_MuonEG__Z_ZEE__X_XSF": f"{_CAT_STR_MUONEG} && {_CAT_ZEE} && {_CAT_XSF}",
            "STR_MuonEG__Z_ZEE__X_XDF": f"{_CAT_STR_MUONEG} && {_CAT_ZEE} && {_CAT_XDF}",
            "STR_MuonEG__Z_ZMM__X_XSF": f"{_CAT_STR_MUONEG} && {_CAT_ZMM} && {_CAT_XSF}",
            "STR_MuonEG__Z_ZMM__X_XDF": f"{_CAT_STR_MUONEG} && {_CAT_ZMM} && {_CAT_XDF}",
            "STR_Muon__Z_ZEE__X_XSF": f"{_CAT_STR_MUON} && {_CAT_ZEE} && {_CAT_XSF}",
            "STR_Muon__Z_ZEE__X_XDF": f"{_CAT_STR_MUON} && {_CAT_ZEE} && {_CAT_XDF}",
            "STR_Muon__Z_ZMM__X_XSF": f"{_CAT_STR_MUON} && {_CAT_ZMM} && {_CAT_XSF}",
            "STR_Muon__Z_ZMM__X_XDF": f"{_CAT_STR_MUON} && {_CAT_ZMM} && {_CAT_XDF}",
            "STR_EGamma__Z_ZEE__X_XSF": f"{_CAT_STR_EGAMMA} && {_CAT_ZEE} && {_CAT_XSF}",
            "STR_EGamma__Z_ZEE__X_XDF": f"{_CAT_STR_EGAMMA} && {_CAT_ZEE} && {_CAT_XDF}",
            "STR_EGamma__Z_ZMM__X_XSF": f"{_CAT_STR_EGAMMA} && {_CAT_ZMM} && {_CAT_XSF}",
            "STR_EGamma__Z_ZMM__X_XDF": f"{_CAT_STR_EGAMMA} && {_CAT_ZMM} && {_CAT_XDF}",
        },
    },
    "signal_region": {
        "expr": _SIGNAL_REGION,
        "categories": {
            "STR_Inclusive__Z_ZEE__X_XEE": f"{_CAT_ZEE} && {_CAT_XEE}",
            "STR_Inclusive__Z_ZEE__X_XMM": f"{_CAT_ZEE} && {_CAT_XMM}",
            "STR_Inclusive__Z_ZEE__X_XDF": f"{_CAT_ZEE} && {_CAT_XDF}",
            "STR_Inclusive__Z_ZMM__X_XEE": f"{_CAT_ZMM} && {_CAT_XEE}",
            "STR_Inclusive__Z_ZMM__X_XMM": f"{_CAT_ZMM} && {_CAT_XMM}",
            "STR_Inclusive__Z_ZMM__X_XDF": f"{_CAT_ZMM} && {_CAT_XDF}",
        },
    },
}

for _cut_name in _PASS["cuts"]:
    if _cut_name not in ALL_CUT_DEFINITIONS:
        raise RuntimeError(
            f"ANALYSIS_PASS={ANALYSIS_PASS} references unknown cut {_cut_name!r}"
        )
    cuts[_cut_name] = dict(ALL_CUT_DEFINITIONS[_cut_name])
    if _cut_name in _PASS.get("cut_weights", {}):
        _weight_policy = dict(_PASS["cut_weights"][_cut_name])
        _unknown_weight_categories = set(_weight_policy) - {
            "*",
            *cuts[_cut_name]["categories"],
        }
        if _unknown_weight_categories:
            raise RuntimeError(
                f"ANALYSIS_PASS={ANALYSIS_PASS} defines weights for unknown "
                f"{_cut_name} categories: {sorted(_unknown_weight_categories)}"
            )
        if not all(isinstance(_expr, str) and _expr.strip() for _expr in _weight_policy.values()):
            raise RuntimeError(f"{_cut_name} category weights must be non-empty expressions")
        cuts[_cut_name]["weights"] = _weight_policy

_expected_cuts = tuple(_PASS["cuts"])

if tuple(cuts) != _expected_cuts:
    raise RuntimeError(
        f"Cut/pass mismatch for {ANALYSIS_PASS}: "
        f"loaded={tuple(cuts)}, expected={_expected_cuts}"
    )
