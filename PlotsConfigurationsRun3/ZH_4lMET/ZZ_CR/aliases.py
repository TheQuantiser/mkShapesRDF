import os
import sys

_this_dir = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else os.getcwd()
if _this_dir not in sys.path:
    sys.path.insert(0, _this_dir)

if "load_selected_year" not in globals():
    _candidates = [
        globals().get("ZZCR_CONFIG_DIR"),
        globals().get("folder"),
        os.getcwd(),
        os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else None,
    ]
    _zzcr_config_dir = None
    for _cand in _candidates:
        if not _cand:
            continue
        _cand_abs = os.path.abspath(_cand)
        if os.path.exists(os.path.join(_cand_abs, "zzcr_year.py")):
            _zzcr_config_dir = _cand_abs
            break
    if _zzcr_config_dir is None:
        _zzcr_config_dir = os.path.abspath(os.getcwd())
    exec(
        open(os.path.join(_zzcr_config_dir, "zzcr_year.py")).read(),
        globals(),
        globals(),
    )

aliases = {}

if "PAIR_ID_CONFIG" not in globals() or "LEPTON_PAIR_INDEX_EXPRESSIONS" not in globals():
    from zzcr_selection_config import LEPTON_PAIR_COMBINATIONS, LEPTON_PAIR_INDEX_EXPRESSIONS, PAIR_ID_CONFIG
from mkShapesRDF.processor.data.LeptonSel_cfg import ElectronWP, MuonWP


ZZCR_YEAR, _selected_year, _ = load_selected_year()
_L2TIGHT_ERA = _selected_year["l2tight_era"]

# Ordered pT thresholds for the four leptons in Z0+X (lead -> 4th).
FOUR_LEPTON_PT_MINS = (25.0, 15.0, 10.0, 10.0)

def _pinned_event_branches():
    pinned = [
        item.strip()
        for item in os.environ.get("ZZCR_PINNED_FILES", "").replace("\n", ",").split(",")
        if item.strip()
    ]
    if not pinned:
        return None
    try:
        import ROOT
    except ImportError:
        return None
    first = pinned[0]
    if first.startswith("/store/"):
        endpoint = os.environ.get("ZZCR_XRD_READ_ENDPOINT", "root://eoscms.cern.ch").rstrip("/")
        first = f"{endpoint}/{first}"
    elif first.startswith("/eos/cms/store/") and os.environ.get("ZZCR_INPUT_ACCESS_MODE") in ("xrootd", "stage-in"):
        endpoint = os.environ.get("ZZCR_XRD_READ_ENDPOINT", "root://eoscms.cern.ch").rstrip("/")
        first = f"{endpoint}/{first[len('/eos/cms'):]}"
    try:
        fobj = ROOT.TFile.Open(first)
    except OSError:
        return None
    if not fobj or fobj.IsZombie():
        return None
    tree = fobj.Get("Events")
    if not tree:
        fobj.Close()
        return None
    branches = {branch.GetName() for branch in tree.GetListOfBranches()}
    fobj.Close()
    return branches


ZZCR_AVAILABLE_BRANCHES = globals().get("ZZCR_AVAILABLE_BRANCHES") or _pinned_event_branches()


def _filter_existing_tight_wps(kind, wps):
    if not ZZCR_AVAILABLE_BRANCHES:
        return list(wps)
    prefix = f"Lepton_isTight{kind}_"
    filtered = [wp for wp in wps if prefix + wp in ZZCR_AVAILABLE_BRANCHES]
    return filtered or list(wps)


def _select_existing_tight_wp(kind, preferred, candidates):
    if not ZZCR_AVAILABLE_BRANCHES:
        return preferred
    branch = f"Lepton_isTight{kind}_{preferred}"
    if branch in ZZCR_AVAILABLE_BRANCHES:
        return preferred
    for candidate in candidates:
        if f"Lepton_isTight{kind}_{candidate}" in ZZCR_AVAILABLE_BRANCHES:
            return candidate
    return preferred


def _l2tight_leading2_expr(era):
    # Mirror mkShapesRDF.processor.modules.L2TightSelection logic exactly:
    # each of the leading two leptons must pass at least one TightObjWP
    # among all electron and muon TightObjWP definitions for the chosen era.
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

aliases["L2TightLeading2"] = {
    "expr": _l2tight_leading2_expr(_L2TIGHT_ERA)
}

ZZCR_ELECTRON_TIGHT_WPS = _filter_existing_tight_wps(
    "Electron", list(ElectronWP[_L2TIGHT_ERA]["TightObjWP"].keys())
)
ZZCR_MUON_TIGHT_WPS = _filter_existing_tight_wps(
    "Muon", list(MuonWP[_L2TIGHT_ERA]["TightObjWP"].keys())
)
ZZCR_PAIR_ELE_WP = _select_existing_tight_wp(
    "Electron", PAIR_ID_CONFIG["eleWP"], ZZCR_ELECTRON_TIGHT_WPS
)
ZZCR_PAIR_MU_WP = _select_existing_tight_wp(
    "Muon", PAIR_ID_CONFIG["muWP"], ZZCR_MUON_TIGHT_WPS
)

configurations = os.environ.get("ZZCR_CONFIG_INCLUDE_BASE") or (
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) + "/"
)
configurations = configurations.rstrip("/") + "/"

aliases["Z0_idx"] = {
    "linesToAdd": [
        '#include "%s/PlotsConfigurationsRun3/ZH_4lMET/ZZ_CR/macros/zh4lmet_zzcr_helpers.cc"'
        % configurations
    ],
    "expr": (
        "ZH4lMETZZCR::bestZ0IdxWithID("
        "Lepton_pt, Lepton_eta, Lepton_phi, Lepton_pdgId, "
        f"Lepton_isTightElectron_{ZZCR_PAIR_ELE_WP}, "
        f"Lepton_isTightMuon_{ZZCR_PAIR_MU_WP}, "
        f"{PAIR_ID_CONFIG['Z0_minPass']}, "
        f"{PAIR_ID_CONFIG['Z0_ptMins'][0]}, "
        f"{PAIR_ID_CONFIG['Z0_ptMins'][1]})"
    ),
}

aliases["X_idx"] = {
    "expr": (
        "ZH4lMETZZCR::xPairIdxWithID("
        "Z0_idx, Lepton_pt, Lepton_pdgId, "
        f"Lepton_isTightElectron_{ZZCR_PAIR_ELE_WP}, "
        f"Lepton_isTightMuon_{ZZCR_PAIR_MU_WP}, "
        f"{PAIR_ID_CONFIG['X_minPass']}, "
        f"{PAIR_ID_CONFIG['X_ptMins'][0]}, "
        f"{PAIR_ID_CONFIG['X_ptMins'][1]})"
    ),
}

aliases["Lepton_trigIdx_tnp"] = {
    "linesToAdd": [
        '#include "%s/PlotsConfigurationsRun3/ZH_4lMET/ZZ_CR/macros/zh4lmet_zzcr_helpers.cc"'
        % configurations
    ],
    "expr": (
        # Keep matching identical to addTnPTree (same-PDG, nearest dR<0.1),
        # so trigger studies and TnP are numerically aligned.
        "ZH4lMETZZCR::createTrigIndexTnP("
        "Lepton_eta, Lepton_phi, Lepton_pdgId, "
        "TrigObj_eta, TrigObj_phi, TrigObj_id, 0.1)"
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

def _branch_or_default(branch, default):
    if not ZZCR_AVAILABLE_BRANCHES or branch in ZZCR_AVAILABLE_BRANCHES:
        return branch
    return default


aliases["PuppiMET_significance"] = {
    "expr": _branch_or_default("PuppiMET_significance", "-999.f")
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

for lep_name, lep_idx in LEPTON_PAIR_INDEX_EXPRESSIONS.items():
    trig_idx_expr = f"Alt(Lepton_trigIdx_tnp, {lep_idx}, -1)"
    trigobj_sources = {
        "pt": ("TrigObj_pt", "-999.f"),
        "eta": ("TrigObj_eta", "-999.f"),
        "phi": ("TrigObj_phi", "-999.f"),
        "pdgId": ("TrigObj_id", "-999"),
        "filterBits": ("TrigObj_filterBits", "0"),
    }
    for suffix, (source, default) in trigobj_sources.items():
        aliases[f"{lep_name}_trigObj_{suffix}"] = {
            "expr": f"Alt({source}, {trig_idx_expr}, {default})",
        }

    aliases[f"{lep_name}_trigObj_bits4l"] = {
        "expr": (
            "ZH4lMETZZCR::pack4lTrigObjBits("
            f"Alt(Lepton_pdgId, {lep_idx}, 0), "
            f"Alt(TrigObj_filterBits, {trig_idx_expr}, 0))"
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
    "pfRelIso04_all": {"ele": "Electron_pfRelIso04_all", "mu": "Muon_pfRelIso04_all", "default": "-999.f"},
    "promptMVA": {"ele": "Electron_promptMVA", "mu": "Muon_promptMVA", "default": "-999.f"},
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

# DeepFlavB veto WP configurable by ZZCR_YEAR.
btag_veto_algo = _selected_year["btag"]["algo"]
btag_veto_WP = _selected_year["btag"]["veto_wp"]
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
