import os
import sys

_this_dir = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else os.getcwd()
if _this_dir not in sys.path:
    sys.path.insert(0, _this_dir)

if "load_selected_year" not in globals():
    _candidates = [
        globals().get("CONFIG_DIR"),
        globals().get("folder"),
        os.getcwd(),
        os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else None,
    ]
    _config_dir = None
    for _cand in _candidates:
        if not _cand:
            continue
        _cand_abs = os.path.abspath(_cand)
        if os.path.exists(os.path.join(_cand_abs, "year_config.py")):
            _config_dir = _cand_abs
            break
    if _config_dir is None:
        _config_dir = os.path.abspath(os.getcwd())
    exec(
        open(os.path.join(_config_dir, "year_config.py")).read(),
        globals(),
        globals(),
    )

aliases = {}

if (
    "PAIR_ID_CONFIG" not in globals()
    or "LEPTON_PAIR_INDEX_EXPRESSIONS" not in globals()
    or "TRIGGER_PATH_PRIORITY" not in globals()
    or "selection_profile" not in globals()
    or "analysis_pass" not in globals()
):
    from selection_config import (
        EVENT_TRIGGER_DIAGNOSTIC_BRANCHES,
        LEPTON_PAIR_COMBINATIONS,
        LEPTON_PAIR_INDEX_EXPRESSIONS,
        PAIR_ID_CONFIG,
        selection_profile,
        TRIGGER_AGGREGATE_FLAGS,
        TRIGGER_PATH_PRIORITY,
        TRIGOBJ_DECODED_BIT_SUFFIXES,
        TRIGOBJ_DIAGNOSTIC_SUFFIXES,
        TRIGOBJ_FAMILY_SUFFIXES,
        TRIGOBJ_PATH_LEG_SUFFIXES,
        analysis_pass,
        trigobj_nanoaod_version,
    )
from mkShapesRDF.processor.data.LeptonSel_cfg import ElectronWP, MuonWP


YEAR, _selected_year, _ = load_selected_year()
_ALIAS_PASS = analysis_pass(
    globals().get("ANALYSIS_PASS") or os.environ.get("ANALYSIS_PASS")
)
_L2TIGHT_ERA = _selected_year["l2tight_era"]
TRIGOBJ_NANOAOD_VERSION = trigobj_nanoaod_version(_selected_year)

# Ordered pT thresholds for the selected Z0 pair and Z0+X quartet.
_SELECTION_PROFILE = selection_profile(_selected_year)
TWO_LEPTON_PT_MINS = _SELECTION_PROFILE["ordered_2l_pt_mins"]
FOUR_LEPTON_PT_MINS = _SELECTION_PROFILE["ordered_4l_pt_mins"]
TRIGOBJ_MATCH_DR = 0.1

configurations = os.environ.get("CONFIG_INCLUDE_BASE") or (
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) + "/"
)
configurations = configurations.rstrip("/") + "/"

AVAILABLE_BRANCHES = globals().get("AVAILABLE_BRANCHES")


def _filter_existing_tight_wps(kind, wps):
    if not AVAILABLE_BRANCHES:
        return list(wps)
    prefix = f"Lepton_isTight{kind}_"
    filtered = [wp for wp in wps if prefix + wp in AVAILABLE_BRANCHES]
    return filtered or list(wps)


def _select_existing_tight_wp(kind, preferred, candidates):
    if not AVAILABLE_BRANCHES:
        return preferred
    branch = f"Lepton_isTight{kind}_{preferred}"
    if branch in AVAILABLE_BRANCHES:
        return preferred
    for candidate in candidates:
        if f"Lepton_isTight{kind}_{candidate}" in AVAILABLE_BRANCHES:
            return candidate
    return preferred


def _l2tight_leading2_expr(era, use_production_order=False):
    # Mirror the production TightObjWP OR.  For the production-order form,
    # use the matched pre-scale pT and order so the technical gate remains
    # fixed under later lepton-scale variations.
    if era not in ElectronWP or era not in MuonWP:
        raise KeyError(f"Unknown l2tight era '{era}' in LeptonSel_cfg")

    ele_wps = _filter_existing_tight_wps(
        "Electron", list(ElectronWP[era]["TightObjWP"].keys())
    )
    mu_wps = _filter_existing_tight_wps(
        "Muon", list(MuonWP[era]["TightObjWP"].keys())
    )
    if not ele_wps and not mu_wps:
        raise ValueError(f"No TightObjWP entries configured for era '{era}'")

    if use_production_order:
        index0 = "FourLepton::productionGateIndex(ProductionLeptonPt, 0)"
        index1 = "FourLepton::productionGateIndex(ProductionLeptonPt, 1)"
    else:
        index0 = "0"
        index1 = "1"

    lead0_terms = [
        f"Alt(Lepton_isTightElectron_{wp}, {index0}, 0) > 0.5" for wp in ele_wps
    ]
    lead0_terms += [
        f"Alt(Lepton_isTightMuon_{wp}, {index0}, 0) > 0.5" for wp in mu_wps
    ]

    lead1_terms = [
        f"Alt(Lepton_isTightElectron_{wp}, {index1}, 0) > 0.5" for wp in ele_wps
    ]
    lead1_terms += [
        f"Alt(Lepton_isTightMuon_{wp}, {index1}, 0) > 0.5" for wp in mu_wps
    ]

    return (
        "(nLepton > 1)"
        + " && ("
        + " || ".join(lead0_terms)
        + ") && ("
        + " || ".join(lead1_terms)
        + ")"
    )

def _data_samples(samples_dict):
    return [sample for sample, cfg in samples_dict.items() if "isData" in cfg]

DATA_SAMPLES = _data_samples(globals().get("samples", {}))

# Run-III correction aliases are MC-only in the external
# PlotsConfigurationsRun3 convention.  Keep a typed DATA sentinel available
# before the common trigger aliases are defined so their public realization
# can be exactly unit-valued without maintaining a second DATA-only graph.
# A zero-generator-weight MC event is also harmlessly unit-valued here: its
# physics-template contribution is zero independently of the correction.
aliases["genWeight"] = {
    "expr": "0.f",
    "samples": DATA_SAMPLES,
}

_L2_GATE_INCLUDE = [
    '#include "%s/PlotsConfigurationsRun3/ZH_4lMET/ZZ_CR/macros/four_lepton_helpers.cc"'
    % configurations
]

aliases["ProductionLeptonPt"] = {
    "linesToAdd": _L2_GATE_INCLUDE,
    "expr": (
        "FourLepton::productionAlignedPt("
        "Lepton_eta, Lepton_phi, Lepton_pdgId, "
        "VetoLepton_pt, VetoLepton_eta, VetoLepton_phi, VetoLepton_pdgId)"
    ),
}
aliases["ProductionLeptonPdgId"] = {
    "expr": (
        "FourLepton::productionAlignedPdgId("
        "Lepton_eta, Lepton_phi, VetoLepton_eta, VetoLepton_phi, "
        "VetoLepton_pdgId)"
    ),
}
aliases["ProductionSourceIndices"] = {
    "expr": (
        "FourLepton::selectedProductionSourceIndices("
        "Lepton_eta, Lepton_phi, Lepton_pdgId, "
        "VetoLepton_eta, VetoLepton_phi, VetoLepton_pdgId)"
    )
}
for _source_quantity in ("pt", "eta", "phi", "pdgId"):
    aliases[f"ProductionSource{_source_quantity[0].upper()}{_source_quantity[1:]}"] = {
        "expr": f"Take(VetoLepton_{_source_quantity}, ProductionSourceIndices)"
    }

aliases["L2TightLeading2Naive"] = {
    "linesToAdd": _L2_GATE_INCLUDE,
    "expr": _l2tight_leading2_expr(_L2TIGHT_ERA, use_production_order=False),
}

aliases["L2TightLeading2"] = {
    "linesToAdd": _L2_GATE_INCLUDE,
    "expr": _l2tight_leading2_expr(_L2TIGHT_ERA, use_production_order=True),
}

aliases["L2TightProductionGate"] = {
    "linesToAdd": _L2_GATE_INCLUDE,
    "expr": _l2tight_leading2_expr(_L2TIGHT_ERA, use_production_order=True),
}

aliases["L2TightGateIndex0"] = {
    "linesToAdd": _L2_GATE_INCLUDE,
    "expr": "FourLepton::productionGateIndex(ProductionLeptonPt, 0)",
}

aliases["L2TightGateIndex1"] = {
    "linesToAdd": _L2_GATE_INCLUDE,
    "expr": "FourLepton::productionGateIndex(ProductionLeptonPt, 1)",
}

ELECTRON_TIGHT_WPS = _filter_existing_tight_wps(
    "Electron", list(ElectronWP[_L2TIGHT_ERA]["TightObjWP"].keys())
)
MUON_TIGHT_WPS = _filter_existing_tight_wps(
    "Muon", list(MuonWP[_L2TIGHT_ERA]["TightObjWP"].keys())
)
PAIR_ELE_WP = _select_existing_tight_wp(
    "Electron", PAIR_ID_CONFIG["eleWP"], ELECTRON_TIGHT_WPS
)
PAIR_MU_WP = _select_existing_tight_wp(
    "Muon", PAIR_ID_CONFIG["muWP"], MUON_TIGHT_WPS
)

aliases["Z0_idx"] = {
    "linesToAdd": [
        '#include "%s/PlotsConfigurationsRun3/ZH_4lMET/ZZ_CR/macros/four_lepton_helpers.cc"'
        % configurations
    ],
    "expr": (
        "FourLepton::bestZ0IdxWithID("
        "Lepton_pt, Lepton_eta, Lepton_phi, Lepton_pdgId, "
        f"Lepton_isTightElectron_{PAIR_ELE_WP}, "
        f"Lepton_isTightMuon_{PAIR_MU_WP}, "
        f"{PAIR_ID_CONFIG['Z0_minPass']}, "
        f"{PAIR_ID_CONFIG['Z0_ptMins'][0]}, "
        f"{PAIR_ID_CONFIG['Z0_ptMins'][1]})"
    ),
}

aliases["X_idx"] = {
    "expr": (
        "FourLepton::xPairIdxWithID("
        "Z0_idx, Lepton_pt, Lepton_pdgId, "
        f"Lepton_isTightElectron_{PAIR_ELE_WP}, "
        f"Lepton_isTightMuon_{PAIR_MU_WP}, "
        f"{PAIR_ID_CONFIG['X_minPass']}, "
        f"{PAIR_ID_CONFIG['X_ptMins'][0]}, "
        f"{PAIR_ID_CONFIG['X_ptMins'][1]})"
    ),
}

aliases["Lepton_trigIdx_tnp"] = {
    "linesToAdd": [
        '#include "%s/PlotsConfigurationsRun3/ZH_4lMET/ZZ_CR/macros/four_lepton_helpers.cc"'
        % configurations
    ],
    "expr": (
        # Keep matching identical to addTnPTree (same-PDG, nearest dR<0.1),
        # so trigger studies and TnP are numerically aligned.
        "FourLepton::createTrigIndexTnP("
        "Lepton_eta, Lepton_phi, Lepton_pdgId, "
        f"TrigObj_eta, TrigObj_phi, TrigObj_id, {TRIGOBJ_MATCH_DR})"
    ),
}

aliases["Lepton_trigDR_tnp"] = {
    "expr": (
        "FourLepton::createTrigMatchDRTnP("
        "Lepton_eta, Lepton_phi, Lepton_pdgId, "
        f"TrigObj_eta, TrigObj_phi, TrigObj_id, {TRIGOBJ_MATCH_DR})"
    ),
}

aliases["Lepton_trigMatchCount_tnp"] = {
    "expr": (
        "FourLepton::countTrigMatchesTnP("
        "Lepton_eta, Lepton_phi, Lepton_pdgId, "
        f"TrigObj_eta, TrigObj_phi, TrigObj_id, {TRIGOBJ_MATCH_DR})"
    ),
}

aliases["Lepton_trigMatchState_tnp"] = {
    "expr": (
        "FourLepton::createTrigMatchStateTnP("
        "Lepton_pdgId, Lepton_trigIdx_tnp, Lepton_trigMatchCount_tnp)"
    ),
}


aliases["Passes2lOrderedPt"] = {
    "expr": (
        "FourLepton::passesOrdered2lPtThresholdsFromPair("
        "Lepton_pt, Z0_idx, "
        f"{TWO_LEPTON_PT_MINS[0]}, "
        f"{TWO_LEPTON_PT_MINS[1]})"
    )
}


aliases["Passes4lOrderedPt"] = {
    "expr": (
        "FourLepton::passesOrdered4lPtThresholdsFromPairs("
        "Lepton_pt, Z0_idx, X_idx, "
        f"{FOUR_LEPTON_PT_MINS[0]}, "
        f"{FOUR_LEPTON_PT_MINS[1]}, "
        f"{FOUR_LEPTON_PT_MINS[2]}, "
        f"{FOUR_LEPTON_PT_MINS[3]})"
    )
}

# Compatibility names all resolve to the configured AN2019/238 four-lepton
# threshold profile.  Keeping one expression prevents the control and signal
# regions from silently drifting apart.
for _ordered_pt_alias in (
    "Passes4lOrderedPtRun2",
    "Passes4lOrderedPtRun3",
):
    aliases[_ordered_pt_alias] = dict(aliases["Passes4lOrderedPt"])

def _branch_or_default(branch, default):
    if not AVAILABLE_BRANCHES or branch in AVAILABLE_BRANCHES:
        return branch
    return default


aliases["PuppiMET_significance"] = {
    # NanoAODv12 does not persist this v15 diagnostic.  Do not invent a proxy
    # with different physics meaning; the histogram mask removes this
    # negative applicability sentinel from the four v12 eras.
    "expr": (
        _branch_or_default("PuppiMET_significance", "-999.f")
        if TRIGOBJ_NANOAOD_VERSION >= 15
        else "-999.f"
    )
}

aliases["PuppiMET_sumEt"] = {"expr": _branch_or_default("PuppiMET_sumEt", "-999.f")}

PAIR_KINEMATICS_FUNCTIONS = {
    "mass": "pairMass",
    "pt": "pairPt",
    "eta": "pairEta",
    "phi": "pairPhi",
}

for pair_name in ("Z0", "X"):
    for observable_name, helper_func in PAIR_KINEMATICS_FUNCTIONS.items():
        aliases[f"{pair_name}_{observable_name}"] = {
            "expr": (
                "FourLepton::"
                f"{helper_func}(Lepton_pt, Lepton_eta, Lepton_phi, Lepton_pdgId, {pair_name}_idx)"
            ),
        }

aliases["m4l"] = {
    "expr": "FourLepton::fourLeptonMassFromPairs(Lepton_pt, Lepton_eta, Lepton_phi, Lepton_pdgId, Z0_idx, X_idx)",
}

aliases["minSelectedPairMass"] = {
    "expr": (
        "FourLepton::minimumSelectedPairMass("
        "Lepton_pt, Lepton_eta, Lepton_phi, Lepton_pdgId, Z0_idx, X_idx)"
    ),
}

aliases["pT4l"] = {
    "expr": "FourLepton::fourLeptonPtFromPairs(Lepton_pt, Lepton_eta, Lepton_phi, Lepton_pdgId, Z0_idx, X_idx)",
}


aliases["phi4l"] = {
    "expr": "FourLepton::fourLeptonPhiFromPairs(Lepton_pt, Lepton_eta, Lepton_phi, Lepton_pdgId, Z0_idx, X_idx)",
}

aliases["dPhi_MET_Z"] = {"expr": "FourLepton::deltaPhi(PuppiMET_phi, Z0_phi)"}
aliases["dPhi_MET_X"] = {"expr": "FourLepton::deltaPhi(PuppiMET_phi, X_phi)"}
for lep_name, lep_idx in LEPTON_PAIR_INDEX_EXPRESSIONS.items():
    aliases[f"dPhi_MET_{lep_name}"] = {
        "expr": f"FourLepton::deltaPhi(PuppiMET_phi, Alt(Lepton_phi, {lep_idx}, -999.f))"
    }
aliases["dPhi_MET_ZplusX"] = {"expr": "FourLepton::deltaPhi(PuppiMET_phi, phi4l)"}

PAIR_LEPTON_HELPER_COLUMNS = {}
for lep_name, lep_idx in LEPTON_PAIR_INDEX_EXPRESSIONS.items():
    eta_helper = f"pair_{lep_name}_eta"
    phi_helper = f"pair_{lep_name}_phi"
    aliases[eta_helper] = {
        "expr": f"Alt(Lepton_eta, {lep_idx}, -999.f)",
    }
    aliases[phi_helper] = {
        "expr": f"Alt(Lepton_phi, {lep_idx}, -999.f)",
    }
    PAIR_LEPTON_HELPER_COLUMNS[lep_name] = {"eta": eta_helper, "phi": phi_helper}

for lep_a, lep_b in LEPTON_PAIR_COMBINATIONS:
    aliases[f"dPhi_{lep_a}_{lep_b}"] = {
        "expr": (
            "FourLepton::deltaPhi("
            f"{PAIR_LEPTON_HELPER_COLUMNS[lep_a]['phi']}, "
            f"{PAIR_LEPTON_HELPER_COLUMNS[lep_b]['phi']})"
        ),
    }
    aliases[f"dEta_{lep_a}_{lep_b}"] = {
        "expr": (
            "FourLepton::deltaEta("
            f"{PAIR_LEPTON_HELPER_COLUMNS[lep_a]['eta']}, "
            f"{PAIR_LEPTON_HELPER_COLUMNS[lep_b]['eta']})"
        ),
    }
    aliases[f"dR_{lep_a}_{lep_b}"] = {
        "expr": (
            "FourLepton::deltaR("
            f"{PAIR_LEPTON_HELPER_COLUMNS[lep_a]['eta']}, "
            f"{PAIR_LEPTON_HELPER_COLUMNS[lep_a]['phi']}, "
            f"{PAIR_LEPTON_HELPER_COLUMNS[lep_b]['eta']}, "
            f"{PAIR_LEPTON_HELPER_COLUMNS[lep_b]['phi']})"
        ),
    }

TRIGOBJ_FILTER_BITS_DEFAULT = "0ULL"


def _has_filter_bit_expr(filter_bits_expr, bit_index):
    if bit_index is None:
        return "false"
    return f"FourLepton::trigObjHasFilterBit({filter_bits_expr}, {bit_index})"


def _flavor_bit_expr(abs_pdg_expr, filter_bits_expr, flavor_pdg_id, bit_index):
    return f"(({abs_pdg_expr}) == {flavor_pdg_id}) && ({_has_filter_bit_expr(filter_bits_expr, bit_index)})"


def _trigger_or_false(branch):
    return _branch_or_default(branch, "false")


_hlt_expr_by_label = {
    label: _trigger_or_false(path) for path, label in TRIGGER_PATH_PRIORITY
}

for lep_name, lep_idx in LEPTON_PAIR_INDEX_EXPRESSIONS.items():
    lep_idx_expr = f"static_cast<int>({lep_idx})"
    trig_idx_expr = f"FourLepton::valueAtInt(Lepton_trigIdx_tnp, {lep_idx_expr}, -1)"
    trig_bits_expr = (
        f"FourLepton::valueAtULL(TrigObj_filterBits, {lep_name}_trigObj_idx, "
        f"{TRIGOBJ_FILTER_BITS_DEFAULT})"
    )
    lep_pdgid_expr = f"FourLepton::valueAtInt(Lepton_pdgId, {lep_idx_expr}, 0)"
    abs_pdg_expr = f"abs({lep_pdgid_expr})"

    aliases[f"{lep_name}_trigObj_idx"] = {"expr": trig_idx_expr}
    aliases[f"{lep_name}_trigObj_dR"] = {
        "expr": f"Alt(Lepton_trigDR_tnp, {lep_idx}, -999.f)",
    }
    aliases[f"{lep_name}_trigObj_nMatches"] = {
        "expr": f"FourLepton::valueAtInt(Lepton_trigMatchCount_tnp, {lep_idx_expr}, 0)",
    }
    aliases[f"{lep_name}_trigObj_matchState"] = {
        "expr": f"FourLepton::valueAtInt(Lepton_trigMatchState_tnp, {lep_idx_expr}, -1)",
    }

    trigobj_sources = {
        "pt": f"FourLepton::valueAtFloat(TrigObj_pt, {lep_name}_trigObj_idx, -999.f)",
        "eta": f"FourLepton::valueAtFloat(TrigObj_eta, {lep_name}_trigObj_idx, -999.f)",
        "phi": f"FourLepton::valueAtFloat(TrigObj_phi, {lep_name}_trigObj_idx, -999.f)",
        "pdgId": f"FourLepton::valueAtInt(TrigObj_id, {lep_name}_trigObj_idx, -999)",
        "id": f"FourLepton::valueAtInt(TrigObj_id, {lep_name}_trigObj_idx, -999)",
        "filterBits": trig_bits_expr,
    }
    for suffix, expr in trigobj_sources.items():
        aliases[f"{lep_name}_trigObj_{suffix}"] = {"expr": expr}
        if suffix in ("pt", "eta", "phi", "pdgId", "id"):
            aliases[f"{lep_name}_trigObj_{suffix}_values"] = {
                "expr": (
                    "ROOT::VecOps::RVec<float>{static_cast<float>("
                    f"{lep_name}_trigObj_{suffix})}}[ROOT::VecOps::RVec<int>{{"
                    f"static_cast<int>({lep_name}_trigObj_idx >= 0)}}]"
                )
            }
    aliases[f"{lep_name}_trigObj_dR_values"] = {
        "expr": (
            "ROOT::VecOps::RVec<float>{static_cast<float>("
            f"{lep_name}_trigObj_dR)}}[ROOT::VecOps::RVec<int>{{"
            f"static_cast<int>({lep_name}_trigObj_idx >= 0)}}]"
        )
    }

    aliases[f"{lep_name}_trigObj_bit_ele_CaloIdLTrackIdLIsoVL"] = {
        "expr": _flavor_bit_expr(abs_pdg_expr, trig_bits_expr, 11, 0),
    }
    aliases[f"{lep_name}_trigObj_bit_ele_1eWPTight"] = {
        "expr": _flavor_bit_expr(abs_pdg_expr, trig_bits_expr, 11, 1),
    }
    aliases[f"{lep_name}_trigObj_bit_ele_1eWPLoose"] = {
        "expr": _flavor_bit_expr(abs_pdg_expr, trig_bits_expr, 11, 2),
    }

    _double_ele_leg1_bit = 4
    _double_ele_leg2_bit = 5 if TRIGOBJ_NANOAOD_VERSION >= 15 else None
    _ele_mu_bit = 6 if TRIGOBJ_NANOAOD_VERSION >= 15 else 5
    _single_ele_bit = 18 if TRIGOBJ_NANOAOD_VERSION >= 15 else 1
    aliases[f"{lep_name}_trigObj_bit_ele_DoubleEleLeg1"] = {
        "expr": _flavor_bit_expr(
            abs_pdg_expr, trig_bits_expr, 11, _double_ele_leg1_bit
        ),
    }
    aliases[f"{lep_name}_trigObj_bit_ele_DoubleEleLeg2"] = {
        "expr": _flavor_bit_expr(
            abs_pdg_expr, trig_bits_expr, 11, _double_ele_leg2_bit
        ),
    }
    aliases[f"{lep_name}_trigObj_bit_ele_DoubleEle"] = {
        "expr": (
            f"{lep_name}_trigObj_bit_ele_DoubleEleLeg1 || "
            f"{lep_name}_trigObj_bit_ele_DoubleEleLeg2"
        ),
    }
    aliases[f"{lep_name}_trigObj_bit_ele_EleMu"] = {
        "expr": _flavor_bit_expr(abs_pdg_expr, trig_bits_expr, 11, _ele_mu_bit),
    }
    aliases[f"{lep_name}_trigObj_bit_ele_Ele30WPTight"] = {
        "expr": _flavor_bit_expr(abs_pdg_expr, trig_bits_expr, 11, _single_ele_bit),
    }
    single_ele_match_expr = f"{lep_name}_trigObj_bit_ele_Ele30WPTight"

    aliases[f"{lep_name}_trigObj_bit_mu_TrkIsoVVL"] = {
        "expr": _flavor_bit_expr(abs_pdg_expr, trig_bits_expr, 13, 0),
    }
    aliases[f"{lep_name}_trigObj_bit_mu_Iso"] = {
        "expr": _flavor_bit_expr(abs_pdg_expr, trig_bits_expr, 13, 1),
    }
    aliases[f"{lep_name}_trigObj_bit_mu_SingleMu"] = {
        "expr": _flavor_bit_expr(abs_pdg_expr, trig_bits_expr, 13, 3),
    }
    aliases[f"{lep_name}_trigObj_bit_mu_DoubleMu"] = {
        "expr": _flavor_bit_expr(abs_pdg_expr, trig_bits_expr, 13, 4),
    }
    aliases[f"{lep_name}_trigObj_bit_mu_EleMu"] = {
        "expr": _flavor_bit_expr(abs_pdg_expr, trig_bits_expr, 13, 5),
    }

    family_match_exprs = {
        "SingleMu": f"{lep_name}_trigObj_bit_mu_SingleMu",
        "DoubleMu": f"{lep_name}_trigObj_bit_mu_DoubleMu",
        "SingleEle": single_ele_match_expr,
        "DoubleEle": f"{lep_name}_trigObj_bit_ele_DoubleEle",
        "EleMu": (
            f"({lep_name}_trigObj_bit_ele_EleMu || "
            f"{lep_name}_trigObj_bit_mu_EleMu)"
        ),
    }
    family_trigger_flags = {
        "SingleMu": "Trigger_sngMu",
        "DoubleMu": "Trigger_dblMu",
        "SingleEle": "Trigger_sngEl",
        "DoubleEle": "Trigger_dblEl",
        "EleMu": "Trigger_ElMu",
    }

    for family, match_expr in family_match_exprs.items():
        aliases[f"{lep_name}_trigObj_match_{family}"] = {"expr": match_expr}
        aliases[f"{lep_name}_trigObj_fired_{family}"] = {
            "expr": f"({_trigger_or_false(family_trigger_flags[family])}) && ({match_expr})"
        }

    aliases[f"{lep_name}_trigObj_leg_IsoMu24"] = {
        "expr": f"({_hlt_expr_by_label['IsoMu24']}) && {lep_name}_trigObj_match_SingleMu",
    }
    aliases[f"{lep_name}_trigObj_leg_Mu17_Mu8"] = {
        "expr": f"({_hlt_expr_by_label['Mu17_Mu8']}) && {lep_name}_trigObj_match_DoubleMu",
    }
    aliases[f"{lep_name}_trigObj_leg_Ele23_Ele12"] = {
        "expr": f"({_hlt_expr_by_label['Ele23_Ele12']}) && {lep_name}_trigObj_match_DoubleEle",
    }
    aliases[f"{lep_name}_trigObj_leg_Ele23_Ele12_leg1"] = {
        "expr": f"({_hlt_expr_by_label['Ele23_Ele12']}) && {lep_name}_trigObj_bit_ele_DoubleEleLeg1",
    }
    aliases[f"{lep_name}_trigObj_leg_Ele23_Ele12_leg2"] = {
        "expr": f"({_hlt_expr_by_label['Ele23_Ele12']}) && {lep_name}_trigObj_bit_ele_DoubleEleLeg2",
    }
    aliases[f"{lep_name}_trigObj_leg_Ele30"] = {
        "expr": f"({_hlt_expr_by_label['Ele30']}) && {lep_name}_trigObj_match_SingleEle",
    }
    aliases[f"{lep_name}_trigObj_leg_Mu23_Ele12"] = {
        "expr": f"({_hlt_expr_by_label['Mu23_Ele12']}) && {lep_name}_trigObj_match_EleMu",
    }
    aliases[f"{lep_name}_trigObj_leg_Mu12_Ele23"] = {
        "expr": f"({_hlt_expr_by_label['Mu12_Ele23']}) && {lep_name}_trigObj_match_EleMu",
    }
    aliases[f"{lep_name}_trigObj_leg_Mu8_Ele23"] = {
        "expr": f"({_hlt_expr_by_label['Mu8_Ele23']}) && {lep_name}_trigObj_match_EleMu",
    }

    aliases[f"{lep_name}_trigObj_bits4l"] = {
        "expr": (
            "FourLepton::pack4lTrigObjBits("
            f"{lep_pdgid_expr}, "
            f"{trig_bits_expr}, {TRIGOBJ_NANOAOD_VERSION})"
        ),
    }

_trigger_exprs = {flag: _trigger_or_false(flag) for flag in TRIGGER_AGGREGATE_FLAGS}
_hlt_priority_exprs = [
    _trigger_or_false(path) for path, _label in TRIGGER_PATH_PRIORITY
]

aliases["dataStreamPriority"] = {
    "expr": (
        "FourLepton::dataStreamPriorityCategory("
        f"{_trigger_exprs['Trigger_ElMu']}, "
        f"{_trigger_exprs['Trigger_sngMu']}, "
        f"{_trigger_exprs['Trigger_dblMu']}, "
        f"{_trigger_exprs['Trigger_sngEl']}, "
        f"{_trigger_exprs['Trigger_dblEl']})"
    ),
}

aliases["triggerFamilyPriority"] = {
    "expr": (
        "FourLepton::triggerFamilyPriorityCategory("
        f"{_trigger_exprs['Trigger_ElMu']}, "
        f"{_trigger_exprs['Trigger_sngMu']}, "
        f"{_trigger_exprs['Trigger_dblMu']}, "
        f"{_trigger_exprs['Trigger_sngEl']}, "
        f"{_trigger_exprs['Trigger_dblEl']})"
    ),
}

aliases["nFiredTriggerFamilies"] = {
    "expr": (
        "FourLepton::countFiredTriggerFamilies("
        f"{_trigger_exprs['Trigger_ElMu']}, "
        f"{_trigger_exprs['Trigger_sngMu']}, "
        f"{_trigger_exprs['Trigger_dblMu']}, "
        f"{_trigger_exprs['Trigger_sngEl']}, "
        f"{_trigger_exprs['Trigger_dblEl']})"
    ),
}

aliases["hltPathPriority"] = {
    "expr": "FourLepton::hltPathPriorityCategory(" + ", ".join(_hlt_priority_exprs) + ")",
}

aliases["nFiredHLTPaths"] = {
    "expr": "FourLepton::countFiredHLTPaths(" + ", ".join(_hlt_priority_exprs) + ")",
}

aliases["streamPriority_MuonEG"] = {"expr": "dataStreamPriority == 1"}
aliases["streamPriority_Muon"] = {"expr": "dataStreamPriority == 2"}
aliases["streamPriority_EGamma"] = {"expr": "dataStreamPriority == 3"}
aliases["hasValidZ0"] = {
    "expr": "(Alt(Z0_idx, 0, -1) >= 0) && (Alt(Z0_idx, 1, -1) >= 0)",
}
aliases["hasValidX"] = {
    "expr": "(Alt(X_idx, 0, -1) >= 0) && (Alt(X_idx, 1, -1) >= 0)",
}
aliases["selectedIndicesDistinct"] = {
    "expr": (
        "FourLepton::fourSelectedIndicesDistinct("
        "Z0_idx, X_idx, Lepton_pt.size())"
    )
}
aliases["selectedIndicesAreLeading2"] = {
    "expr": "FourLepton::selectedPairIsLeading(Z0_idx)"
}
aliases["selectedIndicesAreLeading4"] = {
    "expr": "FourLepton::selectedPairsAreLeading(Z0_idx, X_idx)"
}
aliases["dyLike2lBaseline"] = {
    "expr": (
        "("
        + " || ".join(f"({_trigger_exprs[flag]})" for flag in TRIGGER_AGGREGATE_FLAGS)
        + ") && nLepton >= 2 && hasValidZ0 && "
        "Z0_mass > 30. && "
        f"Alt(Lepton_pt, Alt(Z0_idx, 0, -1), -999.f) > {PAIR_ID_CONFIG['Z0_ptMins'][0]:g} && "
        f"Alt(Lepton_pt, Alt(Z0_idx, 1, -1), -999.f) > {PAIR_ID_CONFIG['Z0_ptMins'][1]:g}"
    ),
}
aliases["fourLeptonIncremental"] = {
    "expr": (
        "dyLike2lBaseline && hasValidX && "
        "Passes4lOrderedPt && m4l > 0. && "
        "FourLepton::sumLeptonChargeFromPairs(Lepton_pdgId, Z0_idx, X_idx) == 0"
    ),
}
aliases["Z0_trigMatchState"] = {
    "expr": (
        "FourLepton::combineTrigMatchState2("
        "Alt(Z0_idx, 0, -1), Alt(Z0_idx, 1, -1), "
        "lZ1_trigObj_matchState, lZ2_trigObj_matchState)"
    ),
}
aliases["X_trigMatchState"] = {
    "expr": (
        "FourLepton::combineTrigMatchState2("
        "Alt(X_idx, 0, -1), Alt(X_idx, 1, -1), "
        "lX1_trigObj_matchState, lX2_trigObj_matchState)"
    ),
}
aliases["trigMatchState_4l"] = {
    "expr": (
        "FourLepton::combineTrigMatchState4("
        "Alt(Z0_idx, 0, -1), Alt(Z0_idx, 1, -1), "
        "Alt(X_idx, 0, -1), Alt(X_idx, 1, -1), "
        "lZ1_trigObj_matchState, lZ2_trigObj_matchState, "
        "lX1_trigObj_matchState, lX2_trigObj_matchState)"
    ),
}

# Selected-index lepton efficiencies.  LeptonSF writes these vectors aligned
# with the merged Lepton collection, so the actual Z0_idx/X_idx values—not a
# generic leading-N convention—are dereferenced here.  DATA receives unit
# fallback vectors below because these are MC corrections.
_ele_sf_base = f"Lepton_tightElectron_{PAIR_ID_CONFIG['eleWP']}_TotSF"
_mu_sf_base = f"Lepton_tightMuon_{PAIR_ID_CONFIG['muWP']}_TotSF"
_ele_sf_up = f"{_ele_sf_base}_Up"
_ele_sf_down = f"{_ele_sf_base}_Down"
_mu_sf_up = f"{_mu_sf_base}_Up"
_mu_sf_down = f"{_mu_sf_base}_Down"

for _branch in (_ele_sf_base, _ele_sf_up, _ele_sf_down, _mu_sf_base, _mu_sf_up, _mu_sf_down):
    aliases[_branch] = {
        "expr": "FourLepton::unitFloatVec(Lepton_pt.size())",
        "samples": DATA_SAMPLES,
    }

def _sf_branch_expr(branch):
    return branch if (not AVAILABLE_BRANCHES or branch in AVAILABLE_BRANCHES) else "FourLepton::unitFloatVec(Lepton_pt.size())"

_ele_nom_expr = _sf_branch_expr(_ele_sf_base)
_ele_up_expr = _sf_branch_expr(_ele_sf_up)
_ele_down_expr = _sf_branch_expr(_ele_sf_down)
_mu_nom_expr = _sf_branch_expr(_mu_sf_base)
_mu_up_expr = _sf_branch_expr(_mu_sf_up)
_mu_down_expr = _sf_branch_expr(_mu_sf_down)

for _lep_label, _lep_idx in LEPTON_PAIR_INDEX_EXPRESSIONS.items():
    aliases[f"{_lep_label}_LeptonSF"] = {
        "expr": f"FourLepton::sfValue({_ele_nom_expr}, {_mu_nom_expr}, Lepton_pdgId, {_lep_idx})"
    }

aliases["SelectedLeptonSF_Z"] = {
    "expr": f"FourLepton::selectedLeptonSFProduct(Lepton_pdgId, Z0_idx, {_ele_nom_expr}, {_mu_nom_expr}, 0)"
}
aliases["SelectedLeptonSF_Z_Up"] = {
    "expr": f"FourLepton::selectedLeptonSFProduct(Lepton_pdgId, Z0_idx, {_ele_up_expr}, {_mu_nom_expr}, 0)"
}
aliases["SelectedLeptonSF_Z_Down"] = {
    "expr": f"FourLepton::selectedLeptonSFProduct(Lepton_pdgId, Z0_idx, {_ele_down_expr}, {_mu_nom_expr}, 0)"
}
aliases["SelectedLeptonSF_ZX"] = {
    "expr": f"FourLepton::selectedLeptonSFProduct4(Lepton_pdgId, Z0_idx, X_idx, {_ele_nom_expr}, {_mu_nom_expr})"
}
aliases["SelectedLeptonSF_ZX_Up"] = {
    "expr": f"FourLepton::selectedLeptonSFProduct4(Lepton_pdgId, Z0_idx, X_idx, {_ele_up_expr}, {_mu_nom_expr})"
}
aliases["SelectedLeptonSF_ZX_Down"] = {
    "expr": f"FourLepton::selectedLeptonSFProduct4(Lepton_pdgId, Z0_idx, X_idx, {_ele_down_expr}, {_mu_nom_expr})"
}

aliases["SelectedElectronSF_Z_Up"] = {
    "expr": f"FourLepton::selectedLeptonSFProductFlavor(Lepton_pdgId, Z0_idx, {_ele_up_expr}, {_mu_nom_expr}, 11)"
}
aliases["SelectedElectronSF_Z_Down"] = {
    "expr": f"FourLepton::selectedLeptonSFProductFlavor(Lepton_pdgId, Z0_idx, {_ele_down_expr}, {_mu_nom_expr}, 11)"
}
aliases["SelectedMuonSF_Z_Up"] = {
    "expr": f"FourLepton::selectedLeptonSFProductFlavor(Lepton_pdgId, Z0_idx, {_ele_nom_expr}, {_mu_up_expr}, 13)"
}
aliases["SelectedMuonSF_Z_Down"] = {
    "expr": f"FourLepton::selectedLeptonSFProductFlavor(Lepton_pdgId, Z0_idx, {_ele_nom_expr}, {_mu_down_expr}, 13)"
}
aliases["SelectedElectronSF_ZX_Up"] = {
    "expr": f"FourLepton::selectedLeptonSFProductFlavor4(Lepton_pdgId, Z0_idx, X_idx, {_ele_up_expr}, {_mu_nom_expr}, 11)"
}
aliases["SelectedElectronSF_ZX_Down"] = {
    "expr": f"FourLepton::selectedLeptonSFProductFlavor4(Lepton_pdgId, Z0_idx, X_idx, {_ele_down_expr}, {_mu_nom_expr}, 11)"
}
aliases["SelectedMuonSF_ZX_Up"] = {
    "expr": f"FourLepton::selectedLeptonSFProductFlavor4(Lepton_pdgId, Z0_idx, X_idx, {_ele_nom_expr}, {_mu_up_expr}, 13)"
}
aliases["SelectedMuonSF_ZX_Down"] = {
    "expr": f"FourLepton::selectedLeptonSFProductFlavor4(Lepton_pdgId, Z0_idx, X_idx, {_ele_nom_expr}, {_mu_down_expr}, 13)"
}

# Preserve the stored canonical branches as regression oracles.  The nominal
# analysis weights below are recomputed from the requested indices/event and
# never forward these leading-N scalars.
for _trigger_branch in (
    "TriggerSFWeight_2l",
    "TriggerSFWeight_2l_u",
    "TriggerSFWeight_2l_d",
    "TriggerSFWeight_4l",
    "TriggerSFWeight_4l_u",
    "TriggerSFWeight_4l_d",
    "TriggerEffWeight_2l",
    "TriggerEffWeight_4l",
):
    aliases[_trigger_branch] = {"expr": "1.f", "samples": DATA_SAMPLES}

_trigger_adapter_dir = (
    configurations + "PlotsConfigurationsRun3/ZH_4lMET/ZZ_CR"
)
_declare_trigger_line = (
    "import sys; "
    f"sys.path.insert(0, {_trigger_adapter_dir!r}) "
    f"if {_trigger_adapter_dir!r} not in sys.path else None; "
    "from selected_trigger_adapter import declare_canonical_trigger; "
    f"declare_canonical_trigger({_L2TIGHT_ERA!r})"
)
aliases["CanonicalTriggerDeclarations"] = {
    "linesToProcess": [_declare_trigger_line],
    "expr": "1.f",
}

_SELECTED_TRIGGER_INCLUDE = [
    '#include "%s/PlotsConfigurationsRun3/ZH_4lMET/ZZ_CR/macros/selected_trigger_wrappers.cc"'
    % configurations
]
aliases["TriggerProductionLeading2Idx"] = {
    "expr": "FourLepton::descendingPtIndices(ProductionLeptonPt, 2)"
}
aliases["TriggerProductionLeading4Idx"] = {
    "expr": "FourLepton::descendingPtIndices(ProductionLeptonPt, 4)"
}
_trigger_common_args = (
    "ProductionLeptonPt, Lepton_eta, Lepton_phi, ProductionLeptonPdgId"
)
_trigger_source_args = (
    "ProductionSourcePt, ProductionSourceEta, ProductionSourcePhi, "
    "ProductionSourcePdgId"
)
aliases["TriggerResult_Z"] = {
    "linesToAdd": _SELECTED_TRIGGER_INCLUDE,
    "expr": (
        "SelectedTrigger::selectedPairResult("
        f"{_trigger_common_args}, Z0_idx, PV_npvsGood, "
        "static_cast<int>(run_period))"
    ),
}
aliases["TriggerResult_ZX"] = {
    "expr": (
        "SelectedTrigger::selectedFourResult("
        f"{_trigger_common_args}, Z0_idx, X_idx, PV_npvsGood, "
        "static_cast<int>(run_period))"
    ),
}
aliases["TriggerResult_event"] = {
    "expr": (
        "SelectedTrigger::eventResult("
        f"{_trigger_source_args}, PV_npvsGood, static_cast<int>(run_period))"
    ),
}
aliases["TriggerResult_storedLeading2Oracle"] = {
    "expr": (
        "SelectedTrigger::selectedPairResult("
        f"{_trigger_source_args}, FourLepton::descendingPtIndices(ProductionSourcePt, 2), PV_npvsGood, "
        "static_cast<int>(run_period))"
    ),
}
aliases["TriggerResult_storedLeading4Oracle"] = {
    "expr": (
        "SelectedTrigger::eventResult("
        f"{_trigger_source_args}, PV_npvsGood, static_cast<int>(run_period))"
    ),
}

for _contract_name in ("Z", "ZX", "event"):
    _result = f"TriggerResult_{_contract_name}"
    for _alias_name, _index in (
        (f"TriggerEffData_{_contract_name}", 0),
        (f"TriggerEffData_{_contract_name}_Down", 1),
        (f"TriggerEffData_{_contract_name}_Up", 2),
        (f"TriggerEffMC_{_contract_name}", 3),
        (f"TriggerSF_{_contract_name}", 4),
        (f"TriggerSF_{_contract_name}_Down", 5),
        (f"TriggerSF_{_contract_name}_Up", 6),
        (f"TriggerSF_{_contract_name}_Valid", 7),
    ):
        _public_expr = f"SelectedTrigger::at({_result}, {_index})"
        if _alias_name.startswith("TriggerSF_"):
            # DATA has no trigger-SF correction or nuisance.  Efficiencies
            # remain available as diagnostics, but every public SF and
            # validity value is exactly one on DATA, matching the external
            # Run-III MC-only correction convention.
            _public_expr = f"(genWeight == 0.f ? 1.f : {_public_expr})"
        aliases[_alias_name] = {
            "expr": _public_expr
        }

# Backward-compatible efficiency names now explicitly mean DATA efficiency.
aliases["TriggerEff_Z"] = {"expr": "TriggerEffData_Z"}
aliases["TriggerEff_ZX"] = {"expr": "TriggerEffData_ZX"}

_selected_trigger_contract = (
    "Z" if str(globals().get("ANALYSIS_PASS", os.environ.get("ANALYSIS_PASS", "CONTROL"))).upper() == "ZPARENT" else "ZX"
)
for _public_name, _source_suffix in (
    ("TriggerEffData_selected", f"TriggerEffData_{_selected_trigger_contract}"),
    ("TriggerEffMC_selected", f"TriggerEffMC_{_selected_trigger_contract}"),
    ("TriggerSF_selected", f"TriggerSF_{_selected_trigger_contract}"),
    ("TriggerSF_selected_Down", f"TriggerSF_{_selected_trigger_contract}_Down"),
    ("TriggerSF_selected_Up", f"TriggerSF_{_selected_trigger_contract}_Up"),
    ("TriggerSF_selected_Valid", f"TriggerSF_{_selected_trigger_contract}_Valid"),
):
    aliases[_public_name] = {"expr": _source_suffix}

aliases["recoil_ux"] = {
    "expr": "FourLepton::recoilUx(pT4l, phi4l, PuppiMET_pt, PuppiMET_phi)"
}
aliases["recoil_uy"] = {
    "expr": "FourLepton::recoilUy(pT4l, phi4l, PuppiMET_pt, PuppiMET_phi)"
}
aliases["recoil_ut"] = {
    "expr": "FourLepton::recoilUt(pT4l, phi4l, PuppiMET_pt, PuppiMET_phi)"
}
aliases["recoil_upar"] = {
    "expr": "FourLepton::recoilUpar(pT4l, phi4l, PuppiMET_pt, PuppiMET_phi)"
}
aliases["recoil_uperp"] = {
    "expr": "FourLepton::recoilUperp(pT4l, phi4l, PuppiMET_pt, PuppiMET_phi)"
}

aliases["Z0_isEE"] = {"expr": "FourLepton::pairFlavor(Lepton_pdgId, Z0_idx) == 11"}
aliases["Z0_isMM"] = {"expr": "FourLepton::pairFlavor(Lepton_pdgId, Z0_idx) == 13"}
aliases["X_isEE"] = {"expr": "FourLepton::pairFlavor(Lepton_pdgId, X_idx) == 11"}
aliases["X_isMM"] = {"expr": "FourLepton::pairFlavor(Lepton_pdgId, X_idx) == 13"}
aliases["X_isSF"] = {"expr": "X_isEE || X_isMM"}
aliases["X_isDF"] = {"expr": "!X_isEE && !X_isMM"}


_quality_nanoaod_v15 = TRIGOBJ_NANOAOD_VERSION >= 15

LEPTON_QUALITY_BRANCH_MAP = {
    "convVeto": {"ele": "Electron_convVeto", "mu": None, "default": "0"},
    "dxy": {"ele": "Electron_dxy", "mu": "Muon_dxy", "default": "-999.f"},
    "dz": {"ele": "Electron_dz", "mu": "Muon_dz", "default": "-999.f"},
    "eInvMinusPInv": {"ele": "Electron_eInvMinusPInv", "mu": None, "default": "-999.f"},
    "hoe": {"ele": "Electron_hoe", "mu": None, "default": "-999.f"},
    "jetPtRelv2": {"ele": "Electron_jetPtRelv2", "mu": "Muon_jetPtRelv2", "default": "-999.f"},
    "jetRelIso": {"ele": "Electron_jetRelIso", "mu": "Muon_jetRelIso", "default": "-999.f"},
    "lostHits": {"ele": "Electron_lostHits", "mu": None, "default": "-999"},
    "mvaIso_WP90": {"ele": "Electron_mvaIso_WP90", "mu": None, "default": "0"},
    "pfIsoId": {"ele": None, "mu": "Muon_pfIsoId", "default": "0"},
    "pfRelIso03_all": {"ele": "Electron_pfRelIso03_all", "mu": "Muon_pfRelIso03_all", "default": "-999.f"},
    # promptMVA is absent for both NanoAODv12 flavors.  Keep it as an explicit
    # version-applicability choice so the *_values aliases below are empty in
    # v12 instead of dereferencing a v15-only branch.
    "promptMVA": {
        "ele": "Electron_promptMVA" if _quality_nanoaod_v15 else None,
        "mu": "Muon_promptMVA" if _quality_nanoaod_v15 else None,
        "default": "-999.f",
    },
    "sieie": {"ele": "Electron_sieie", "mu": None, "default": "-999.f"},
    "sip3d": {"ele": "Electron_sip3d", "mu": "Muon_sip3d", "default": "-999.f"},
    "tightId": {"ele": None, "mu": "Muon_tightId", "default": "0"},
}

for lep_name, lep_idx in LEPTON_PAIR_INDEX_EXPRESSIONS.items():
    abs_pdg_expr = f"abs(Alt(Lepton_pdgId, {lep_idx}, 0))"
    ele_idx_expr = f"Alt(Lepton_electronIdx, {lep_idx}, -1)"
    mu_idx_expr = f"Alt(Lepton_muonIdx, {lep_idx}, -1)"
    for suffix, cfg in LEPTON_QUALITY_BRANCH_MAP.items():
        ele_src = cfg["ele"]
        mu_src = cfg["mu"]
        default = cfg["default"]
        ele_expr = (
            f"Alt({ele_src}, {ele_idx_expr}, {default})"
            if ele_src and _branch_or_default(ele_src, None)
            else default
        )
        mu_expr = (
            f"Alt({mu_src}, {mu_idx_expr}, {default})"
            if mu_src and _branch_or_default(mu_src, None)
            else default
        )
        aliases[f"{lep_name}_{suffix}"] = {
            "expr": (
                f"({abs_pdg_expr} == 11) ? ({ele_expr}) : "
                f"(({abs_pdg_expr} == 13) ? ({mu_expr}) : {default})"
            )
        }
        _ele_available = bool(ele_src and _branch_or_default(ele_src, None))
        _mu_available = bool(mu_src and _branch_or_default(mu_src, None))
        _applicability_terms = []
        if _ele_available:
            _applicability_terms.append(f"({abs_pdg_expr} == 11)")
        if _mu_available:
            _applicability_terms.append(f"({abs_pdg_expr} == 13)")
        _applicable = " || ".join(_applicability_terms) or "false"
        _hist_applicable = _applicable
        if suffix == "jetRelIso":
            # CMSSW NanoAOD defines exactly -1 for no matched jet, while
            # physical (1/ptRatio)-1 values extend down to -1/3 because
            # ptRatio is capped at 1.5.  Remove only the documented sentinel.
            _hist_applicable = (
                f"({_applicable}) && "
                f"({lep_name}_{suffix} != -1.f)"
            )
        aliases[f"{lep_name}_{suffix}_values"] = {
            "expr": (
                "ROOT::VecOps::RVec<float>{static_cast<float>("
                f"{lep_name}_{suffix})}}[ROOT::VecOps::RVec<int>{{"
                f"static_cast<int>({_hist_applicable})}}]"
            )
        }

# Current Run-III fixed-WP veto and event-SF contract.  Selection and SF read
# the identical tagger, loose WP, CleanJet pT, and eta acceptance.
_btag_cfg = _selected_year["btag"]
btag_veto_algo = _btag_cfg["algo"]
btag_veto_WP = resolve_btag_working_point(
    _btag_cfg["correction_file"], _btag_cfg["correction_prefix"], "L"
)
_configured_btag_veto_WP = float(_btag_cfg["veto_wp"])
if abs(btag_veto_WP - _configured_btag_veto_WP) > 5.e-5:
    raise RuntimeError(
        "Configured and official BTV loose working points disagree: "
        f"year_config.json={_configured_btag_veto_WP}, correctionlib={btag_veto_WP}"
    )
_BTAG_INCLUDE = [
    '#include "%s/PlotsConfigurationsRun3/ZH_4lMET/ZZ_CR/macros/fixed_wp_btag_sf.cc"'
    % configurations
]
aliases["bVeto"] = {
    "linesToAdd": _BTAG_INCLUDE,
    "expr": (
        "FixedWPBTag::veto(CleanJet_pt, CleanJet_eta, CleanJet_jetIdx, "
        f"Jet_{btag_veto_algo}, {btag_veto_WP}, 30.f)"
    ),
}
aliases["fifthLeptonVeto"] = {
    "expr": "FourLepton::fifthLeptonVeto(Lepton_pt, 10.f)"
}
aliases["physicalBtagVeto"] = {
    "expr": (
        "FixedWPBTag::veto(CleanJet_pt, CleanJet_eta, CleanJet_jetIdx, "
        f"Jet_{btag_veto_algo}, {btag_veto_WP}, 20.f)"
    )
}
aliases["BTagMapOverflowJetCount"] = {
    "expr": (
        "FixedWPBTag::mapOverflowJetCount("
        "CleanJet_pt, CleanJet_eta, CleanJet_jetIdx)"
    )
}

# This NanoAOD input is MC-only.  Define a typed DATA sentinel before the
# common central aliases below so the shared histogram graph compiles.
aliases["Jet_hadronFlavour"] = {
    "expr": "ROOT::VecOps::RVec<int>(Jet_pt.size(), 0)",
    "samples": DATA_SAMPLES,
}

_btagsf_samples = [
    _sample_name for _sample_name in globals().get("samples", {}) if _sample_name != "DATA"
]
# The fixed-WP event-SF evaluator is part of the CONTROL correction contract
# only.  ZPARENT/FOURL_BASE neither multiply this correction nor book its
# diagnostics, so they must not instantiate an evaluator that can fail on a
# physically irrelevant efficiency-map bin.
if _ALIAS_PASS["btag_sf"] and (_btagsf_samples or DATA_SAMPLES):
    _btag_map = resolve_btag_efficiency_map(_btag_cfg["efficiency_map"])
    _btag_sf_payload = resolve_btag_sf_payload(_btag_cfg["correction_file"])
    _systematics_enabled = globals().get("ENABLE_SYSTEMATICS")
    if _systematics_enabled is None:
        _systematics_value = os.environ.get("ENABLE_SYSTEMATICS", "1").strip().lower()
        if _systematics_value not in (
            "1", "true", "yes", "on", "0", "false", "no", "off"
        ):
            raise RuntimeError(
                "ENABLE_SYSTEMATICS must be a boolean 0/1 value; "
                f"received {_systematics_value!r}"
            )
        _systematics_enabled = _systematics_value in ("1", "true", "yes", "on")
    _btag_shifts = ["central"]
    if _systematics_enabled:
        _btag_shifts += [
            "up_correlated",
            "down_correlated",
            "up_uncorrelated",
            "down_uncorrelated",
        ]
    for _flavor, _group in (("bc", 1), ("light", 0)):
        for _shift in _btag_shifts:
            _alias_name = f"btagSF{_flavor}"
            if _shift != "central":
                _alias_name += f"_{_shift}"
            _event_sf_expr = (
                    "FixedWPBTag::eventSF("
                    "CleanJet_pt, CleanJet_eta, CleanJet_jetIdx, "
                    f"Jet_hadronFlavour, Jet_{btag_veto_algo}, "
                    f'"{_btag_map}", "{_btag_sf_payload}", '
                    f'"{_btag_cfg["correction_prefix"]}", "{_shift}", '
                    f"{_group}, {btag_veto_WP})"
                )
            aliases[_alias_name] = {"expr": _event_sf_expr}
            if _shift == "central":
                # Keep the conventional central alias available to the
                # shared DATA/MC diagnostic histogram graph.  DATA is
                # explicitly unit-valued and never enters a nuisance target.
                aliases[_alias_name]["expr"] = (
                    f"(genWeight == 0.f ? 1.f : {_event_sf_expr})"
                )
            else:
                aliases[_alias_name]["samples"] = _btagsf_samples
    aliases["BTagVetoSF"] = {
        "expr": "btagSFbc*btagSFlight",
    }
    aliases["BTagVetoSF_Valid"] = {
        "expr": "1.f",
    }

aliases["sumLeptonCharge"] = {
    "expr": "FourLepton::sumLeptonChargeFromPairs(Lepton_pdgId, Z0_idx, X_idx)"
}

aliases["HT"] = {"expr": "Sum(CleanJet_pt)"}
aliases["nJetInHorn"] = {
    "expr": "Sum(CleanJet_pt > 30 && CleanJet_pt < 50 && abs(CleanJet_eta) > 2.5 && abs(CleanJet_eta) < 3.0)"
}

# Data-only fallbacks for MC-only NanoAOD branches.
DATA_FALLBACK_BLOCKS = {
    # Generator-level branches unavailable in data.
    "gen": {
        # Keep generator-only values out of DATA physics bins.  The visible
        # axis starts above this sentinel and source production uses fold=0.
        "GenMET_pt": "-999.f",
        "GenMET_phi": "-999.f",
        "GenPart_pdgId": "FourLepton::emptyIntVec()",
        "GenPart_pt": "FourLepton::emptyFloatVec()",
        "GenPart_eta": "FourLepton::emptyFloatVec()",
        "GenPart_phi": "FourLepton::emptyFloatVec()",
        "Electron_genPartIdx": "FourLepton::emptyIntVec()",
        "Muon_genPartIdx": "FourLepton::emptyIntVec()",
        "Jet_genJetIdx": "FourLepton::emptyIntVec()",
        "GenJet_pt": "FourLepton::emptyFloatVec()",
        "GenJet_eta": "FourLepton::emptyFloatVec()",
        "GenJet_phi": "FourLepton::emptyFloatVec()",
    },
    # Lepton WP SF vectors are MC-only.
    "lepton_sf": {
        f"Lepton_tightElectron_{PAIR_ID_CONFIG['eleWP']}_TotSF": "FourLepton::emptyFloatVec()",
        f"Lepton_tightMuon_{PAIR_ID_CONFIG['muWP']}_TotSF": "FourLepton::emptyFloatVec()",
    },
    # A unit DATA column keeps shared correction-diagnostic histograms
    # compilable.  DATA remains absent from every nuisance target and its
    # event weight does not use this column.
    "pileup": {
        "puWeight": "1.f",
        "puWeightUp": "1.f",
        "puWeightDown": "1.f",
    },
    # TrigMaker payloads are MC-only scalar event weights.  Keep the
    # correction aliases available to the shared DATA plot/variable graph,
    # but make their DATA realization an explicit unit rather than asking
    # ROOT to resolve a non-existent NanoAOD branch.
    "trigger_sf": {
        "TriggerSFWeight_2l": "1.f",
        "TriggerSFWeight_2l_u": "1.f",
        "TriggerSFWeight_2l_d": "1.f",
        "TriggerSFWeight_4l": "1.f",
        "TriggerSFWeight_4l_u": "1.f",
        "TriggerSFWeight_4l_d": "1.f",
        "TriggerEffWeight_2l": "1.f",
        "TriggerEffWeight_4l": "1.f",
    },
}

for fallback_group in DATA_FALLBACK_BLOCKS.values():
    for branch_name, fallback_expr in fallback_group.items():
        aliases[branch_name] = {
            "expr": fallback_expr,
            "samples": DATA_SAMPLES,
        }

aliases["Lepton_genPartIdx"] = {
    "expr": "FourLepton::leptonGenPartIdx(Lepton_pdgId, Lepton_electronIdx, Lepton_muonIdx, Electron_genPartIdx, Muon_genPartIdx)"
}

aliases["Lepton_genPdgId"] = {
    "expr": "FourLepton::genPdgIdFromIdx(Lepton_genPartIdx, GenPart_pdgId)"
}

aliases["Lepton_genPt"] = {
    "expr": "FourLepton::genFloatFromIdx(Lepton_genPartIdx, GenPart_pt)"
}

aliases["Lepton_genEta"] = {
    "expr": "FourLepton::genFloatFromIdx(Lepton_genPartIdx, GenPart_eta)"
}

aliases["Lepton_genPhi"] = {
    "expr": "FourLepton::genFloatFromIdx(Lepton_genPartIdx, GenPart_phi)"
}

# Histogram projections exclude missing generator matches and absent
# reco/trigger objects.  Scalar diagnostic expressions keep their conventional
# sentinel values, while these zero-or-one-element vectors make
# source-axis underflow/overflow a statement about physics rather than about
# object applicability.
for _lep_name, _lep_idx in LEPTON_PAIR_INDEX_EXPRESSIONS.items():
    _gen_valid = f"Alt(Lepton_genPartIdx, {_lep_idx}, -1) >= 0"
    for _suffix, _source in (
        ("genPdgId", "Lepton_genPdgId"),
        ("genPt", "Lepton_genPt"),
        ("genEta", "Lepton_genEta"),
        ("genPhi", "Lepton_genPhi"),
    ):
        aliases[f"{_lep_name}_{_suffix}_values"] = {
            "expr": (
                "ROOT::VecOps::RVec<float>{static_cast<float>(Alt("
                f"{_source}, {_lep_idx}, -999.f))}}[ROOT::VecOps::RVec<int>{{"
                f"static_cast<int>({_gen_valid})}}]"
            )
        }

    _abs_pdg = f"abs(Alt(Lepton_pdgId, {_lep_idx}, 0))"
    for _kind, _pdg_id, _wps in (
        ("Electron", 11, ElectronWP[_L2TIGHT_ERA]["TightObjWP"].keys()),
        ("Muon", 13, MuonWP[_L2TIGHT_ERA]["TightObjWP"].keys()),
    ):
        for _wp in _wps:
            _name = f"{_lep_name}_isTight{_kind}_{_wp}"
            aliases[f"{_name}_values"] = {
                "expr": (
                    "ROOT::VecOps::RVec<float>{static_cast<float>(Alt("
                    f"Lepton_isTight{_kind}_{_wp}, {_lep_idx}, 0.f))}}"
                    "[ROOT::VecOps::RVec<int>{"
                    f"static_cast<int>({_abs_pdg} == {_pdg_id})}}]"
                )
            }

for _jet_index in range(2):
    _clean_valid = f"nCleanJet > {_jet_index}"
    _raw_jet_index = f"Alt(CleanJet_jetIdx, {_jet_index}, -1)"
    _gen_jet_index = f"Alt(Jet_genJetIdx, {_raw_jet_index}, -1)"
    for _suffix, _source in (
        ("pt", "CleanJet_pt"),
        ("eta", "CleanJet_eta"),
        ("phi", "CleanJet_phi"),
    ):
        aliases[f"CleanJet_{_suffix}_{_jet_index}_values"] = {
            "expr": (
                "ROOT::VecOps::RVec<float>{static_cast<float>(Alt("
                f"{_source}, {_jet_index}, -999.f))}}[ROOT::VecOps::RVec<int>{{"
                f"static_cast<int>({_clean_valid})}}]"
            )
        }
    for _suffix, _source in (
        ("genPt", "GenJet_pt"),
        ("genEta", "GenJet_eta"),
        ("genPhi", "GenJet_phi"),
    ):
        aliases[f"CleanJet_{_suffix}_{_jet_index}_values"] = {
            "expr": (
                "ROOT::VecOps::RVec<float>{static_cast<float>(Alt("
                f"{_source}, {_gen_jet_index}, -999.f))}}"
                "[ROOT::VecOps::RVec<int>{"
                f"static_cast<int>(({_clean_valid}) && ({_gen_jet_index} >= 0))}}]"
            )
        }
