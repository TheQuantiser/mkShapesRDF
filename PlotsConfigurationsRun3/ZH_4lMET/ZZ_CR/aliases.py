import os

from mkShapesRDF.processor.data.LeptonSel_cfg import ElectronWP, MuonWP

aliases = {}


_L2TIGHT_ERA = "Full2024v15"

# Ordered pT thresholds for the four leptons in Z0+X (lead -> 4th).
FOUR_LEPTON_PT_MINS = (25.0, 15.0, 10.0, 10.0)

def _l2tight_leading2_expr(era):
    ele_wps = list(ElectronWP[era]["TightObjWP"].keys())
    mu_wps = list(MuonWP[era]["TightObjWP"].keys())

    lead0_terms = [f"Alt(Lepton_isTightElectron_{wp}, 0, 0) > 0.5" for wp in ele_wps]
    lead0_terms += [f"Alt(Lepton_isTightMuon_{wp}, 0, 0) > 0.5" for wp in mu_wps]

    lead1_terms = [f"Alt(Lepton_isTightElectron_{wp}, 1, 0) > 0.5" for wp in ele_wps]
    lead1_terms += [f"Alt(Lepton_isTightMuon_{wp}, 1, 0) > 0.5" for wp in mu_wps]

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

aliases["L2TightLeading2"] = {"expr": _l2tight_leading2_expr(_L2TIGHT_ERA)}

configurations = (
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) + "/"
)

aliases["Z0_idx"] = {
    "linesToAdd": [
        '#include "%s/PlotsConfigurationsRun3/ZH_4lMET/ZZ_CR/macros/zh4lmet_zzcr_helpers.cc"'
        % configurations
    ],
    "expr": (
        "ZH4lMETZZCR::bestZ0IdxWithID("
        "Lepton_pt, Lepton_eta, Lepton_phi, Lepton_pdgId, "
        f"Lepton_isTightElectron_{PAIR_ID_CONFIG['eleWP']}, "
        f"Lepton_isTightMuon_{PAIR_ID_CONFIG['muWP']}, "
        f"{PAIR_ID_CONFIG['Z0_minPass']}, "
        f"{PAIR_ID_CONFIG['Z0_ptMins'][0]}, "
        f"{PAIR_ID_CONFIG['Z0_ptMins'][1]})"
    ),
}

aliases["X_idx"] = {
    "expr": (
        "ZH4lMETZZCR::xPairIdxWithID("
        "Z0_idx, Lepton_pt, Lepton_pdgId, "
        f"Lepton_isTightElectron_{PAIR_ID_CONFIG['eleWP']}, "
        f"Lepton_isTightMuon_{PAIR_ID_CONFIG['muWP']}, "
        f"{PAIR_ID_CONFIG['X_minPass']}, "
        f"{PAIR_ID_CONFIG['X_ptMins'][0]}, "
        f"{PAIR_ID_CONFIG['X_ptMins'][1]})"
    ),
}


aliases["PassesZZCR4lOrderedPt"] = {
    "expr": (
        "ZH4lMETZZCR::passesOrderedPtThresholdsFromPairs("
        "Lepton_pt, Z0_idx, X_idx, "
        f"{FOUR_LEPTON_PT_MINS[0]}, "
        f"{FOUR_LEPTON_PT_MINS[1]}, "
        f"{FOUR_LEPTON_PT_MINS[2]}, "
        f"{FOUR_LEPTON_PT_MINS[3]})"
    )
}

aliases["PuppiMET_significance"] = {"expr": "PuppiMET_significance"}

aliases["PuppiMET_sumEt"] = {"expr": "PuppiMET_sumEt"}

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
                "ZH4lMETZZCR::"
                f"{helper_func}(Lepton_pt, Lepton_eta, Lepton_phi, Lepton_pdgId, {pair_name}_idx)"
            ),
        }

aliases["m4l"] = {
    "expr": "ZH4lMETZZCR::fourLeptonMassFromPairs(Lepton_pt, Lepton_eta, Lepton_phi, Lepton_pdgId, Z0_idx, X_idx)",
}

aliases["pT4l"] = {
    "expr": "ZH4lMETZZCR::fourLeptonPtFromPairs(Lepton_pt, Lepton_eta, Lepton_phi, Lepton_pdgId, Z0_idx, X_idx)",
}


aliases["phi4l"] = {
    "expr": "ZH4lMETZZCR::fourLeptonPhiFromPairs(Lepton_pt, Lepton_eta, Lepton_phi, Lepton_pdgId, Z0_idx, X_idx)",
}

aliases["dPhi_MET_Z"] = {"expr": "ZH4lMETZZCR::deltaPhi(PuppiMET_phi, Z0_phi)"}
aliases["dPhi_MET_X"] = {"expr": "ZH4lMETZZCR::deltaPhi(PuppiMET_phi, X_phi)"}
for lep_name, lep_idx in LEPTON_PAIR_INDEX_EXPRESSIONS.items():
    aliases[f"dPhi_MET_{lep_name}"] = {
        "expr": f"ZH4lMETZZCR::deltaPhi(PuppiMET_phi, Alt(Lepton_phi, {lep_idx}, -999.f))"
    }
aliases["dPhi_MET_ZplusX"] = {"expr": "ZH4lMETZZCR::deltaPhi(PuppiMET_phi, phi4l)"}

PAIR_LEPTON_HELPER_COLUMNS = {}
for lep_name, lep_idx in LEPTON_PAIR_INDEX_EXPRESSIONS.items():
    eta_helper = f"zzcr_{lep_name}_eta"
    phi_helper = f"zzcr_{lep_name}_phi"
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
            "ZH4lMETZZCR::deltaPhi("
            f"{PAIR_LEPTON_HELPER_COLUMNS[lep_a]['phi']}, "
            f"{PAIR_LEPTON_HELPER_COLUMNS[lep_b]['phi']})"
        ),
    }
    aliases[f"dEta_{lep_a}_{lep_b}"] = {
        "expr": (
            "ZH4lMETZZCR::deltaEta("
            f"{PAIR_LEPTON_HELPER_COLUMNS[lep_a]['eta']}, "
            f"{PAIR_LEPTON_HELPER_COLUMNS[lep_b]['eta']})"
        ),
    }
    aliases[f"dR_{lep_a}_{lep_b}"] = {
        "expr": (
            "ZH4lMETZZCR::deltaR("
            f"{PAIR_LEPTON_HELPER_COLUMNS[lep_a]['eta']}, "
            f"{PAIR_LEPTON_HELPER_COLUMNS[lep_a]['phi']}, "
            f"{PAIR_LEPTON_HELPER_COLUMNS[lep_b]['eta']}, "
            f"{PAIR_LEPTON_HELPER_COLUMNS[lep_b]['phi']})"
        ),
    }

aliases["recoil_ux"] = {
    "expr": "ZH4lMETZZCR::recoilUx(pT4l, phi4l, PuppiMET_pt, PuppiMET_phi)"
}
aliases["recoil_uy"] = {
    "expr": "ZH4lMETZZCR::recoilUy(pT4l, phi4l, PuppiMET_pt, PuppiMET_phi)"
}
aliases["recoil_ut"] = {
    "expr": "ZH4lMETZZCR::recoilUt(pT4l, phi4l, PuppiMET_pt, PuppiMET_phi)"
}
aliases["recoil_upar"] = {
    "expr": "ZH4lMETZZCR::recoilUpar(pT4l, phi4l, PuppiMET_pt, PuppiMET_phi)"
}
aliases["recoil_uperp"] = {
    "expr": "ZH4lMETZZCR::recoilUperp(pT4l, phi4l, PuppiMET_pt, PuppiMET_phi)"
}

aliases["Z0_isEE"] = {"expr": "ZH4lMETZZCR::pairFlavor(Lepton_pdgId, Z0_idx) == 11"}
aliases["Z0_isMM"] = {"expr": "ZH4lMETZZCR::pairFlavor(Lepton_pdgId, Z0_idx) == 13"}
aliases["X_isEE"] = {"expr": "ZH4lMETZZCR::pairFlavor(Lepton_pdgId, X_idx) == 11"}
aliases["X_isMM"] = {"expr": "ZH4lMETZZCR::pairFlavor(Lepton_pdgId, X_idx) == 13"}
aliases["X_isSF"] = {"expr": "X_isEE || X_isMM"}
aliases["X_isDF"] = {"expr": "!X_isEE && !X_isMM"}

# DeepFlavB veto WP for Summer24.

btag_veto_algo = "btagDeepFlavB"
btag_veto_WP = 0.0485
aliases[f"bVeto"] = {
    "expr": f"ZH4lMETZZCR::bVetoDeepFlavB(CleanJet_pt, CleanJet_eta, CleanJet_jetIdx, Jet_{btag_veto_algo}, {btag_veto_WP})",
}

aliases["sumLeptonCharge"] = {
    "expr": "ZH4lMETZZCR::sumLeptonChargeFromPairs(Lepton_pdgId, Z0_idx, X_idx)"
}

aliases["HT"] = {"expr": "Sum(CleanJet_pt)"}
aliases["nJetInHorn"] = {
    "expr": "Sum(CleanJet_pt > 30 && CleanJet_pt < 50 && abs(CleanJet_eta) > 2.5 && abs(CleanJet_eta) < 3.0)"
}

# Data-only fallbacks for MC-only NanoAOD branches.
DATA_FALLBACK_BLOCKS = {
    # Generator-level branches unavailable in data.
    "gen": {
        "GenMET_pt": "ZH4lMETZZCR::zeroFloat()",
        "GenMET_phi": "ZH4lMETZZCR::zeroFloat()",
        "GenPart_pdgId": "ZH4lMETZZCR::emptyIntVec()",
        "GenPart_pt": "ZH4lMETZZCR::emptyFloatVec()",
        "GenPart_eta": "ZH4lMETZZCR::emptyFloatVec()",
        "GenPart_phi": "ZH4lMETZZCR::emptyFloatVec()",
        "Electron_genPartIdx": "ZH4lMETZZCR::emptyIntVec()",
        "Muon_genPartIdx": "ZH4lMETZZCR::emptyIntVec()",
        "Jet_genJetIdx": "ZH4lMETZZCR::emptyIntVec()",
        "GenJet_pt": "ZH4lMETZZCR::emptyFloatVec()",
        "GenJet_eta": "ZH4lMETZZCR::emptyFloatVec()",
        "GenJet_phi": "ZH4lMETZZCR::emptyFloatVec()",
    },
    # Lepton WP SF vectors are MC-only.
    "lepton_sf": {
        f"Lepton_tightElectron_{PAIR_ID_CONFIG['eleWP']}_TotSF": "ZH4lMETZZCR::emptyFloatVec()",
        f"Lepton_tightMuon_{PAIR_ID_CONFIG['muWP']}_TotSF": "ZH4lMETZZCR::emptyFloatVec()",
    },
}

for fallback_group in DATA_FALLBACK_BLOCKS.values():
    for branch_name, fallback_expr in fallback_group.items():
        aliases[branch_name] = {
            "expr": fallback_expr,
            "samples": DATA_SAMPLES,
        }

aliases["Lepton_genPartIdx"] = {
    "expr": "ZH4lMETZZCR::leptonGenPartIdx(Lepton_pdgId, Lepton_electronIdx, Lepton_muonIdx, Electron_genPartIdx, Muon_genPartIdx)"
}

aliases["Lepton_genPdgId"] = {
    "expr": "ZH4lMETZZCR::genPdgIdFromIdx(Lepton_genPartIdx, GenPart_pdgId)"
}

aliases["Lepton_genPt"] = {
    "expr": "ZH4lMETZZCR::genFloatFromIdx(Lepton_genPartIdx, GenPart_pt)"
}

aliases["Lepton_genEta"] = {
    "expr": "ZH4lMETZZCR::genFloatFromIdx(Lepton_genPartIdx, GenPart_eta)"
}

aliases["Lepton_genPhi"] = {
    "expr": "ZH4lMETZZCR::genFloatFromIdx(Lepton_genPartIdx, GenPart_phi)"
}
