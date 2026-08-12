"""Physical ZH4l regions, written as intersections of named predicates."""

TRIGGER_OR = "(Trigger_ElMu || Trigger_sngMu || Trigger_dblMu || Trigger_sngEl || Trigger_dblEl)"
preselections = f"{TRIGGER_OR} && nLepton >= 2 && passLeading2Tight && noJetInHorn"

valid4l = "validZX && mZ > 30. && mX > 4. && m4l > 0. && q4l == 0"
base4l = (
    f"{valid4l} && pass4lPt && veto5l && minMll4l > 12. && bVeto "
    "&& abs(mZ - 91.1876) < 15."
)
zzcr = f"{base4l} && isXSF && mX > 75. && mX < 105. && PuppiMET_pt < 35."
sr_xsf = f"{base4l} && isXSF && mX > 10. && mX < 65. && PuppiMET_pt > 35. && m4l > 140."
sr_xdf = f"{base4l} && isXDF && mX > 10. && mX < 70. && PuppiMET_pt > 20."

cuts = {
    "ZZCR": zzcr,
    "ZZCR_4e": f"{zzcr} && isZee && isXee",
    "ZZCR_4mu": f"{zzcr} && isZmm && isXmm",
    "ZZCR_2e2mu": f"{zzcr} && ((isZee && isXmm) || (isZmm && isXee))",
    "SR_XSF": sr_xsf,
    "SR_XDF": sr_xdf,
}
