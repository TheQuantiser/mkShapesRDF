"""Physical ZH4l regions, written as intersections of named predicates."""

TRIGGER_OR = (
    "(Trigger_ElMu || Trigger_sngMu || Trigger_dblMu || Trigger_sngEl || Trigger_dblEl)"
)
preselections = f"{TRIGGER_OR} && nLepton >= 2 && event_pass_leading_lepton_tight && event_pass_jet_horn_veto"

valid4l = "zx_is_valid && z_mass > 30. && x_mass > 4. && zx_mass > 0. && zx_charge == 0"
base4l = (
    f"{valid4l} && zx_pass_ordered_pt && event_pass_extra_lepton_veto && zx_min_pair_mass > 12. && event_pass_b_veto "
    "&& abs(z_mass - 91.1876) < 15."
)
zzcr = f"{base4l} && x_is_same_flavor && x_mass > 75. && x_mass < 105. && PuppiMET_pt < 35."
sr_xsf = f"{base4l} && x_is_same_flavor && x_mass > 10. && x_mass < 65. && PuppiMET_pt > 35. && zx_mass > 140."
sr_xdf = f"{base4l} && x_is_different_flavor && x_mass > 10. && x_mass < 70. && PuppiMET_pt > 20."

cuts = {
    "ZZCR": zzcr,
    "ZZCR_4e": f"{zzcr} && z_is_ee && x_is_ee",
    "ZZCR_4mu": f"{zzcr} && z_is_mumu && x_is_mumu",
    "ZZCR_2e2mu": f"{zzcr} && ((z_is_ee && x_is_mumu) || (z_is_mumu && x_is_ee))",
    "SR_XSF": sr_xsf,
    "SR_XDF": sr_xdf,
}
