"""Minimal alias graph for the selected-Z/DY RunStability workflow."""

import os
import sys

from mkShapesRDF.processor.data.LeptonSel_cfg import ElectronWP, MuonWP


_this_dir = os.path.dirname(os.path.abspath(__file__))
if _this_dir not in sys.path:
    sys.path.insert(0, _this_dir)

if "load_selected_year" not in globals():
    exec(
        open(os.path.join(_this_dir, "year_config.py")).read(),
        globals(),
        globals(),
    )
if "PAIR_ID_CONFIG" not in globals():
    from selection_config import (
        PAIR_ID_CONFIG,
        SELECTED_SELECTION_PROFILE,
        TRIGGER_AGGREGATE_FLAGS,
        analysis_pass,
    )

YEAR, _selected_year, _ = load_selected_year()
_ALIAS_PASS = analysis_pass()
_L2TIGHT_ERA = _selected_year["l2tight_era"]
_SELECTION_PROFILE = dict(SELECTED_SELECTION_PROFILE)
TWO_LEPTON_PT_MINS = tuple(_SELECTION_PROFILE["ordered_2l_pt_mins"])
AVAILABLE_BRANCHES = globals().get("AVAILABLE_BRANCHES")

configurations = os.environ.get("CONFIG_INCLUDE_BASE") or (
    os.path.dirname(os.path.dirname(os.path.dirname(_this_dir))) + "/"
)
configurations = configurations.rstrip("/") + "/"

aliases = {}
DATA_SAMPLES = [
    sample for sample, cfg in globals().get("samples", {}).items() if "isData" in cfg
]

if globals().get("RUN_STABILITY_CONTRACT", {}).get("enabled"):
    if DATA_SAMPLES not in ([], ["DATA"]):
        raise RuntimeError(
            "RunStability permits zero DATA outputs or one logical DATA output "
            f"named DATA; received {DATA_SAMPLES}"
        )
    if DATA_SAMPLES:
        aliases["runStabilityIndex"] = {
            "expr": (
                f"{RUN_STABILITY_CPP_NAMESPACE}::index("
                "static_cast<unsigned int>(run))"
            ),
            "linesToAdd": [RUN_STABILITY_CPP],
            "samples": DATA_SAMPLES,
        }
    aliases["__run_stability_contract__"] = {
        "run_stability_contract": RUN_STABILITY_CONTRACT,
    }

# DATA lacks generator and correction branches. These unit/sentinel columns
# keep one shared graph compilable without ever applying MC weights to DATA.
aliases["genWeight"] = {"expr": "0.f", "samples": DATA_SAMPLES}
aliases["puWeight"] = {"expr": "1.f", "samples": DATA_SAMPLES}

_HELPER_INCLUDE = [
    '#include "%s/PlotsConfigurationsRun3/ZH_4lMET/RunStability/macros/run_stability_helpers.cc"'
    % configurations
]


def _filter_existing_tight_wps(kind, values):
    if not AVAILABLE_BRANCHES:
        return list(values)
    prefix = f"Lepton_isTight{kind}_"
    selected = [value for value in values if prefix + value in AVAILABLE_BRANCHES]
    return selected or list(values)


def _select_existing_tight_wp(kind, preferred, candidates):
    if (
        not AVAILABLE_BRANCHES
        or f"Lepton_isTight{kind}_{preferred}" in AVAILABLE_BRANCHES
    ):
        return preferred
    for candidate in candidates:
        if f"Lepton_isTight{kind}_{candidate}" in AVAILABLE_BRANCHES:
            return candidate
    return preferred


def _l2tight_leading2_expr(era):
    if era not in ElectronWP or era not in MuonWP:
        raise KeyError(f"Unknown l2tight era {era!r}")
    electron_wps = _filter_existing_tight_wps("Electron", ElectronWP[era]["TightObjWP"])
    muon_wps = _filter_existing_tight_wps("Muon", MuonWP[era]["TightObjWP"])
    terms = []
    for ordinal in (0, 1):
        index = f"RunStability::productionGateIndex(ProductionLeptonPt, {ordinal})"
        choices = [
            f"Alt(Lepton_isTightElectron_{wp}, {index}, 0) > 0.5" for wp in electron_wps
        ] + [f"Alt(Lepton_isTightMuon_{wp}, {index}, 0) > 0.5" for wp in muon_wps]
        if not choices:
            raise ValueError(f"No TightObjWP entries configured for era {era!r}")
        terms.append("(" + " || ".join(choices) + ")")
    return "(nLepton > 1) && " + " && ".join(terms)


aliases["ProductionLeptonPt"] = {
    "linesToAdd": _HELPER_INCLUDE,
    "expr": (
        "RunStability::productionAlignedPt("
        "Lepton_eta, Lepton_phi, Lepton_pdgId, "
        "VetoLepton_pt, VetoLepton_eta, VetoLepton_phi, VetoLepton_pdgId)"
    ),
}
aliases["ProductionLeptonPdgId"] = {
    "expr": (
        "RunStability::productionAlignedPdgId("
        "Lepton_eta, Lepton_phi, VetoLepton_eta, VetoLepton_phi, VetoLepton_pdgId)"
    )
}
aliases["L2TightLeading2"] = {"expr": _l2tight_leading2_expr(_L2TIGHT_ERA)}

electron_wps = _filter_existing_tight_wps(
    "Electron", ElectronWP[_L2TIGHT_ERA]["TightObjWP"]
)
muon_wps = _filter_existing_tight_wps("Muon", MuonWP[_L2TIGHT_ERA]["TightObjWP"])
pair_ele_wp = _select_existing_tight_wp(
    "Electron", PAIR_ID_CONFIG["eleWP"], electron_wps
)
pair_mu_wp = _select_existing_tight_wp("Muon", PAIR_ID_CONFIG["muWP"], muon_wps)

aliases["Z0_idx"] = {
    "expr": (
        "RunStability::bestZ0IdxWithID("
        "Lepton_pt, Lepton_eta, Lepton_phi, Lepton_pdgId, "
        f"Lepton_isTightElectron_{pair_ele_wp}, "
        f"Lepton_isTightMuon_{pair_mu_wp}, "
        f"{PAIR_ID_CONFIG['Z0_minPass']}, "
        f"{PAIR_ID_CONFIG['Z0_ptMins'][0]}, "
        f"{PAIR_ID_CONFIG['Z0_ptMins'][1]})"
    )
}
aliases["Z0_mass"] = {
    "expr": (
        "RunStability::pairMass("
        "Lepton_pt, Lepton_eta, Lepton_phi, Lepton_pdgId, Z0_idx)"
    )
}
aliases["Z0_pt"] = {
    "expr": (
        "RunStability::pairPt("
        "Lepton_pt, Lepton_eta, Lepton_phi, Lepton_pdgId, Z0_idx)"
    )
}
aliases["hasValidZ0"] = {"expr": "Z0_idx.size() == 2"}
aliases["Passes2lOrderedPt"] = {
    "expr": (
        "RunStability::passesOrdered2lPtThresholdsFromPair("
        "Lepton_pt, Z0_idx, "
        f"{TWO_LEPTON_PT_MINS[0]}, {TWO_LEPTON_PT_MINS[1]})"
    )
}
aliases["Z0_isEE"] = {"expr": "RunStability::pairFlavor(Lepton_pdgId, Z0_idx) == 11"}
aliases["Z0_isMM"] = {"expr": "RunStability::pairFlavor(Lepton_pdgId, Z0_idx) == 13"}

_trigger_exprs = {flag: flag for flag in TRIGGER_AGGREGATE_FLAGS}
aliases["dataStreamPriority"] = {
    "expr": (
        "RunStability::dataStreamPriorityCategory("
        f"{_trigger_exprs['Trigger_ElMu']}, "
        f"{_trigger_exprs['Trigger_sngMu']}, "
        f"{_trigger_exprs['Trigger_dblMu']}, "
        f"{_trigger_exprs['Trigger_sngEl']}, "
        f"{_trigger_exprs['Trigger_dblEl']})"
    )
}
aliases["streamPriority_MuonEG"] = {"expr": "dataStreamPriority == 1"}
aliases["streamPriority_Muon"] = {"expr": "dataStreamPriority == 2"}
aliases["streamPriority_EGamma"] = {"expr": "dataStreamPriority == 3"}
aliases["nJetInHorn"] = {
    "expr": (
        "Sum(CleanJet_pt > 30 && CleanJet_pt < 50 && "
        "abs(CleanJet_eta) > 2.5 && abs(CleanJet_eta) < 3.0)"
    )
}

# Nominal selected-Z lepton efficiency.
_ele_sf = f"Lepton_tightElectron_{PAIR_ID_CONFIG['eleWP']}_TotSF"
_mu_sf = f"Lepton_tightMuon_{PAIR_ID_CONFIG['muWP']}_TotSF"
for branch in (_ele_sf, _mu_sf):
    aliases[branch] = {
        "expr": "RunStability::unitFloatVec(Lepton_pt.size())",
        "samples": DATA_SAMPLES,
    }


def _sf_source(branch):
    if not AVAILABLE_BRANCHES or branch in AVAILABLE_BRANCHES:
        return branch
    return "RunStability::unitFloatVec(Lepton_pt.size())"


aliases["SelectedLeptonSF_Z"] = {
    "expr": (
        "RunStability::selectedLeptonSFProduct("
        f"Lepton_pdgId, Z0_idx, {_sf_source(_ele_sf)}, {_sf_source(_mu_sf)}, 0)"
    )
}

# The trigger correction is recomputed for the actual selected Z pair.
_trigger_adapter_dir = configurations + "PlotsConfigurationsRun3/ZH_4lMET/RunStability"
aliases["CanonicalTriggerDeclarations"] = {
    "linesToProcess": [
        "import sys; "
        f"sys.path.insert(0, {_trigger_adapter_dir!r}) "
        f"if {_trigger_adapter_dir!r} not in sys.path else None; "
        "from selected_trigger_adapter import declare_canonical_trigger; "
        f"declare_canonical_trigger({_L2TIGHT_ERA!r})"
    ],
    "expr": "1.f",
}
aliases["TriggerResult_Z"] = {
    "linesToAdd": [
        '#include "%s/PlotsConfigurationsRun3/ZH_4lMET/RunStability/macros/selected_trigger_wrappers.cc"'
        % configurations
    ],
    "expr": (
        "SelectedTrigger::selectedPairResult("
        "ProductionLeptonPt, Lepton_eta, Lepton_phi, ProductionLeptonPdgId, "
        "Z0_idx, PV_npvsGood, static_cast<int>(run_period))"
    ),
}
aliases["TriggerSF_Z"] = {
    "expr": "(genWeight == 0.f ? 1.f : SelectedTrigger::at(TriggerResult_Z, 4))"
}
