"""Selected-object lepton/trigger corrections and fixed-WP b-veto weight."""

import json
import os
from pathlib import Path

from .eras import (
    resolve_btag_efficiency_map,
    resolve_btag_sf_payload,
    resolve_btag_working_point,
)


PUBLIC_CORRECTION_ALIASES = frozenset(
    {"LepSF_Z", "LepSF_ZX", "TriggerSF_Z", "TriggerSF_ZX", "bVeto", "bVetoSF"}
)


def _bool_env(name, default=True):
    value = os.environ.get(name)
    if value is None:
        return default
    normalized = value.strip().lower()
    if normalized in ("1", "true", "yes", "on"):
        return True
    if normalized in ("0", "false", "no", "off"):
        return False
    raise ValueError(f"{name} must be boolean, received {value!r}")


def build_correction_aliases(era_cfg, family_dir, samples, selected_wps, *, systematics=True):
    family_dir = Path(family_dir).resolve()
    data_samples = [name for name, cfg in samples.items() if "isData" in cfg]
    mc_samples = [name for name in samples if name not in data_samples]
    objects_include = [f'#include "{family_dir / "common/macros/objects.cc"}"']
    aliases = {"genWeight": {"expr": "0.f", "samples": data_samples}}

    ele = f"Lepton_tightElectron_{selected_wps['electron_wp']}_TotSF"
    mu = f"Lepton_tightMuon_{selected_wps['muon_wp']}_TotSF"
    for branch in (ele, ele + "_Up", ele + "_Down", mu, mu + "_Up", mu + "_Down"):
        aliases[branch] = {
            "linesToAdd": objects_include,
            "expr": "FourLepton::unitFloatVec(Lepton_pt.size())",
            "samples": data_samples,
        }

    aliases.update(
        {
            "LepSF_Z": {"expr": f"FourLepton::selectedLeptonSFProduct(Lepton_pdgId,Z_idx,{ele},{mu},0)"},
            "LepSF_Z_Up": {"expr": f"FourLepton::selectedLeptonSFProduct(Lepton_pdgId,Z_idx,{ele}_Up,{mu},0)"},
            "LepSF_Z_Down": {"expr": f"FourLepton::selectedLeptonSFProduct(Lepton_pdgId,Z_idx,{ele}_Down,{mu},0)"},
            "LepSF_ZX": {"expr": f"FourLepton::selectedLeptonSFProduct4(Lepton_pdgId,Z_idx,X_idx,{ele},{mu})"},
            "LepSF_ZX_Up": {"expr": f"FourLepton::selectedLeptonSFProduct4(Lepton_pdgId,Z_idx,X_idx,{ele}_Up,{mu})"},
            "LepSF_ZX_Down": {"expr": f"FourLepton::selectedLeptonSFProduct4(Lepton_pdgId,Z_idx,X_idx,{ele}_Down,{mu})"},
            "LepSF_ZX_EleUp": {"expr": f"FourLepton::selectedLeptonSFProduct4(Lepton_pdgId,Z_idx,X_idx,{ele}_Up,{mu})"},
            "LepSF_ZX_EleDown": {"expr": f"FourLepton::selectedLeptonSFProduct4(Lepton_pdgId,Z_idx,X_idx,{ele}_Down,{mu})"},
            "LepSF_ZX_MuUp": {"expr": f"FourLepton::selectedLeptonSFProduct4(Lepton_pdgId,Z_idx,X_idx,{ele},{mu}_Up)"},
            "LepSF_ZX_MuDown": {"expr": f"FourLepton::selectedLeptonSFProduct4(Lepton_pdgId,Z_idx,X_idx,{ele},{mu}_Down)"},
        }
    )

    trigger_era = era_cfg["l2tight_era"]
    common_dir = family_dir / "common"
    declare = (
        "import sys; "
        f"sys.path.insert(0, {str(family_dir)!r}) if {str(family_dir)!r} not in sys.path else None; "
        "from common.selected_trigger_adapter import declare_canonical_trigger; "
        f"declare_canonical_trigger({trigger_era!r})"
    )
    aliases["ZH4l_triggerDeclared"] = {"linesToProcess": [declare], "expr": "1.f"}
    trigger_include = [f'#include "{family_dir / "common/macros/trigger.cc"}"']
    args = "ZH4l_prodPt,Lepton_eta,Lepton_phi,ZH4l_prodPdgId"
    aliases["ZH4l_triggerResultZ"] = {
        "linesToAdd": trigger_include,
        "expr": f"SelectedTrigger::selectedPairResult({args},Z_idx,PV_npvsGood,static_cast<int>(run_period))",
    }
    aliases["ZH4l_triggerResultZX"] = {
        "expr": f"SelectedTrigger::selectedFourResult({args},Z_idx,X_idx,PV_npvsGood,static_cast<int>(run_period))"
    }
    for domain, result in (("Z", "ZH4l_triggerResultZ"), ("ZX", "ZH4l_triggerResultZX")):
        aliases[f"TriggerSF_{domain}"] = {"expr": f"genWeight == 0.f ? 1.f : SelectedTrigger::at({result},4)"}
        aliases[f"TriggerSF_{domain}_Down"] = {"expr": f"genWeight == 0.f ? 1.f : SelectedTrigger::at({result},5)"}
        aliases[f"TriggerSF_{domain}_Up"] = {"expr": f"genWeight == 0.f ? 1.f : SelectedTrigger::at({result},6)"}

    bcfg = era_cfg["btag"]
    wp = resolve_btag_working_point(bcfg["correction_file"], bcfg["correction_prefix"], "L")
    if abs(wp - float(bcfg["veto_wp"])) > 5.0e-5:
        raise RuntimeError("Configured and official BTV loose working points disagree")
    binclude = [f'#include "{family_dir / "common/macros/btag.cc"}"']
    jet_tag = f"Jet_{bcfg['algo']}"
    aliases["bVeto"] = {
        "linesToAdd": binclude,
        "expr": f"FixedWPBTag::veto(CleanJet_pt,CleanJet_eta,CleanJet_jetIdx,{jet_tag},{wp},20.f)",
    }
    aliases["bVeto30"] = {
        "expr": f"FixedWPBTag::veto(CleanJet_pt,CleanJet_eta,CleanJet_jetIdx,{jet_tag},{wp},30.f)"
    }
    aliases["Jet_hadronFlavour"] = {
        "expr": "ROOT::VecOps::RVec<int>(Jet_pt.size(),0)", "samples": data_samples
    }
    efficiency = resolve_btag_efficiency_map(bcfg["efficiency_map"])
    payload = resolve_btag_sf_payload(bcfg["correction_file"])
    shifts = ["central"]
    if systematics and _bool_env("ENABLE_SYSTEMATICS", True):
        shifts += ["up_correlated", "down_correlated", "up_uncorrelated", "down_uncorrelated"]
    for flavor, group in (("bc", 1), ("light", 0)):
        for shift in shifts:
            name = f"ZH4l_btagSF{flavor}" + ("" if shift == "central" else f"_{shift}")
            expr = (
                "FixedWPBTag::eventSF(CleanJet_pt,CleanJet_eta,CleanJet_jetIdx,"
                f"Jet_hadronFlavour,{jet_tag},{json.dumps(efficiency)},{json.dumps(payload)},"
                f"{json.dumps(bcfg['correction_prefix'])},{json.dumps(shift)},{group},{wp})"
            )
            aliases[name] = {"expr": f"genWeight == 0.f ? 1.f : {expr}"}
            if shift != "central":
                aliases[name]["samples"] = mc_samples
    aliases["bVetoSF"] = {"expr": "ZH4l_btagSFbc*ZH4l_btagSFlight"}
    return aliases
