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
        ERA_CONFIG,
        FAMILY_DIR,
        globals().get("samples", {}),
        SELECTED_WPS,
        systematics=False,
    )
)

_trigger_args = "Trigger_ElMu,Trigger_sngMu,Trigger_dblMu,Trigger_sngEl,Trigger_dblEl"
aliases["event_trigger_priority"] = {
    "expr": f"FourLepton::triggerFamilyPriorityCategory({_trigger_args})"
}
aliases["event_stream_priority"] = {
    "expr": f"FourLepton::dataStreamPriorityCategory({_trigger_args})"
}
aliases["event_stream_is_muoneg"] = {"expr": "event_stream_priority == 1"}
aliases["event_stream_is_muon"] = {"expr": "event_stream_priority == 2"}
aliases["event_stream_is_egamma"] = {"expr": "event_stream_priority == 3"}

_closure_include = [f'#include "{CONFIG_DIR / "macros/closure.cc"}"']
_tight_ele = f"Lepton_isTightElectron_{SELECTED_WPS['electron_wp']}"
_tight_mu = f"Lepton_isTightMuon_{SELECTED_WPS['muon_wp']}"
aliases["event_pass_anchor_ordered_pt"] = {
    "linesToAdd": _closure_include,
    "expr": f"ClosureBridge::passesAnchor2lPt(Lepton_pt,Lepton_pdgId,{_tight_ele},{_tight_mu},25.f,15.f)",
}
aliases["extra_tight_lepton_count"] = {
    "expr": f"ClosureBridge::nExtraTight10(Lepton_pt,Lepton_pdgId,{_tight_ele},{_tight_mu},z_lepton_index)"
}
aliases["z_abs_rapidity"] = {
    "expr": "ClosureBridge::safeAbsRapidity(z_pt,z_eta,z_phi,z_mass)"
}
aliases["z_phi_eta_star"] = {
    "expr": (
        "ClosureBridge::phiEtaStar("
        "Alt(Lepton_eta,Alt(z_lepton_index,0,-1),-999.f),Alt(Lepton_phi,Alt(z_lepton_index,0,-1),-999.f),"
        "Alt(Lepton_eta,Alt(z_lepton_index,1,-1),-999.f),Alt(Lepton_phi,Alt(z_lepton_index,1,-1),-999.f))"
    )
}
aliases["z_lepton_lead_pt"] = {
    "expr": "max(Alt(Lepton_pt,Alt(z_lepton_index,0,-1),-999.f),Alt(Lepton_pt,Alt(z_lepton_index,1,-1),-999.f))"
}
aliases["z_lepton_sublead_pt"] = {
    "expr": "min(Alt(Lepton_pt,Alt(z_lepton_index,0,-1),-999.f),Alt(Lepton_pt,Alt(z_lepton_index,1,-1),-999.f))"
}
aliases["z_lepton_lead_abs_eta"] = {
    "expr": "ClosureBridge::selectedAbsEta(Lepton_pt,Lepton_eta,z_lepton_index,true)"
}
aliases["z_lepton_sublead_abs_eta"] = {
    "expr": "ClosureBridge::selectedAbsEta(Lepton_pt,Lepton_eta,z_lepton_index,false)"
}
aliases["selected_jet_count"] = {"expr": "Sum(CleanJet_pt > 30.)"}
_bcfg = ERA_CONFIG["btag"]
_bwp = resolve_btag_working_point(
    _bcfg["correction_file"], _bcfg["correction_prefix"], "L"
)
aliases["tagged_jet_count"] = {
    "expr": f"Sum(CleanJet_pt > 20. && abs(CleanJet_eta) < 2.5 && Take(Jet_{_bcfg['algo']},CleanJet_jetIdx) > {_bwp})"
}
