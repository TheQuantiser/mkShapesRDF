"""Common ZH4l aliases plus quantities unique to the DY→ZZ bridge."""

from pathlib import Path

from common.corrections import build_correction_aliases
from common.eras import load_selected_era, resolve_btag_working_point
from common.objects import build_object_aliases
from common.observables import build_observable_aliases

FAMILY_DIR = Path(globals().get("FAMILY_DIR", Path(__file__).resolve().parent.parent))
CONFIG_DIR = FAMILY_DIR / "Closure"
_, ERA_CONFIG, _ = load_selected_era()
aliases, SELECTED_WPS = build_object_aliases(
    ERA_CONFIG, FAMILY_DIR, globals().get("AVAILABLE_BRANCHES")
)
aliases.update(build_observable_aliases())
aliases.update(
    build_correction_aliases(
        ERA_CONFIG, FAMILY_DIR, globals().get("samples", {}), SELECTED_WPS,
        systematics=False,
    )
)

_trigger_args = "Trigger_ElMu,Trigger_sngMu,Trigger_dblMu,Trigger_sngEl,Trigger_dblEl"
aliases["triggerPriority"] = {
    "expr": f"FourLepton::triggerFamilyPriorityCategory({_trigger_args})"
}
aliases["streamPriority"] = {
    "expr": f"FourLepton::dataStreamPriorityCategory({_trigger_args})"
}
aliases["streamPriority_MuonEG"] = {"expr": "streamPriority == 1"}
aliases["streamPriority_Muon"] = {"expr": "streamPriority == 2"}
aliases["streamPriority_EGamma"] = {"expr": "streamPriority == 3"}

_closure_include = [f'#include "{CONFIG_DIR / "macros/closure.cc"}"']
_tight_ele = f"Lepton_isTightElectron_{SELECTED_WPS['electron_wp']}"
_tight_mu = f"Lepton_isTightMuon_{SELECTED_WPS['muon_wp']}"
aliases["passAnchor2lPt"] = {
    "linesToAdd": _closure_include,
    "expr": f"ClosureBridge::passesAnchor2lPt(Lepton_pt,Lepton_pdgId,{_tight_ele},{_tight_mu},25.f,15.f)",
}
aliases["nExtraTight10"] = {
    "expr": f"ClosureBridge::nExtraTight10(Lepton_pt,Lepton_pdgId,{_tight_ele},{_tight_mu},Z_idx)"
}
aliases["Z0_absRapidity"] = {"expr": "ClosureBridge::safeAbsRapidity(ptZ,etaZ,phiZ,mZ)"}
aliases["phiEtaStar"] = {
    "expr": (
        "ClosureBridge::phiEtaStar("
        "Alt(Lepton_eta,Alt(Z_idx,0,-1),-999.f),Alt(Lepton_phi,Alt(Z_idx,0,-1),-999.f),"
        "Alt(Lepton_eta,Alt(Z_idx,1,-1),-999.f),Alt(Lepton_phi,Alt(Z_idx,1,-1),-999.f))"
    )
}
aliases["Z_lead_pt"] = {"expr": "max(Alt(Lepton_pt,Alt(Z_idx,0,-1),-999.f),Alt(Lepton_pt,Alt(Z_idx,1,-1),-999.f))"}
aliases["Z_sublead_pt"] = {"expr": "min(Alt(Lepton_pt,Alt(Z_idx,0,-1),-999.f),Alt(Lepton_pt,Alt(Z_idx,1,-1),-999.f))"}
aliases["Z_lead_absEta"] = {"expr": "ClosureBridge::selectedAbsEta(Lepton_pt,Lepton_eta,Z_idx,true)"}
aliases["Z_sublead_absEta"] = {"expr": "ClosureBridge::selectedAbsEta(Lepton_pt,Lepton_eta,Z_idx,false)"}
aliases["nJet30"] = {"expr": "Sum(CleanJet_pt > 30.)"}
_bcfg = ERA_CONFIG["btag"]
_bwp = resolve_btag_working_point(_bcfg["correction_file"], _bcfg["correction_prefix"], "L")
aliases["nBLoose"] = {
    "expr": f"Sum(CleanJet_pt > 20. && abs(CleanJet_eta) < 2.5 && Take(Jet_{_bcfg['algo']},CleanJet_jetIdx) > {_bwp})"
}
