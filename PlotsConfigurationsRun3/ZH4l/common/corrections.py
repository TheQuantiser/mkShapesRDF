"""Selected-object lepton/trigger corrections and fixed-WP b-veto weight."""

import json
import os
from pathlib import Path
from .runtime import common_import_statement

from .eras import (
    resolve_btag_efficiency_map,
    resolve_btag_sf_payload,
    resolve_btag_working_point,
)


PUBLIC_CORRECTION_ALIASES = frozenset(
    {
        "sf_lepton_z",
        "sf_lepton_zx",
        "sf_trigger_z",
        "sf_trigger_zx",
        "event_pass_b_veto",
        "sf_b_veto",
    }
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


def build_correction_aliases(
    era_cfg, family_dir, samples, selected_wps, *, systematics=True
):
    family_dir = Path(family_dir).resolve()
    data_samples = [
        name for name, cfg in samples.items() if bool(cfg.get("isData", False))
    ]
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
            "sf_lepton_z": {
                "expr": f"FourLepton::selectedLeptonSFProduct(Lepton_pdgId,z_lepton_index,{ele},{mu},0)"
            },
            "sf_lepton_z_up": {
                "expr": f"FourLepton::selectedLeptonSFProduct(Lepton_pdgId,z_lepton_index,{ele}_Up,{mu},0)"
            },
            "sf_lepton_z_down": {
                "expr": f"FourLepton::selectedLeptonSFProduct(Lepton_pdgId,z_lepton_index,{ele}_Down,{mu},0)"
            },
            "sf_lepton_zx": {
                "expr": f"FourLepton::selectedLeptonSFProduct4(Lepton_pdgId,z_lepton_index,x_lepton_index,{ele},{mu})"
            },
            "sf_lepton_zx_up": {
                "expr": f"FourLepton::selectedLeptonSFProduct4(Lepton_pdgId,z_lepton_index,x_lepton_index,{ele}_Up,{mu})"
            },
            "sf_lepton_zx_down": {
                "expr": f"FourLepton::selectedLeptonSFProduct4(Lepton_pdgId,z_lepton_index,x_lepton_index,{ele}_Down,{mu})"
            },
            "sf_lepton_zx_electron_up": {
                "expr": f"FourLepton::selectedLeptonSFProduct4(Lepton_pdgId,z_lepton_index,x_lepton_index,{ele}_Up,{mu})"
            },
            "sf_lepton_zx_electron_down": {
                "expr": f"FourLepton::selectedLeptonSFProduct4(Lepton_pdgId,z_lepton_index,x_lepton_index,{ele}_Down,{mu})"
            },
            "sf_lepton_zx_muon_up": {
                "expr": f"FourLepton::selectedLeptonSFProduct4(Lepton_pdgId,z_lepton_index,x_lepton_index,{ele},{mu}_Up)"
            },
            "sf_lepton_zx_muon_down": {
                "expr": f"FourLepton::selectedLeptonSFProduct4(Lepton_pdgId,z_lepton_index,x_lepton_index,{ele},{mu}_Down)"
            },
        }
    )

    trigger_era = era_cfg["l2tight_era"]
    common_dir = family_dir / "common"
    declare = (
        common_import_statement(common_dir)
        + "from common.selected_trigger_adapter import declare_canonical_trigger; "
        f"declare_canonical_trigger({trigger_era!r})"
    )
    aliases["zh4l_internal_trigger_declared"] = {
        "linesToProcess": [declare],
        "expr": "1.f",
    }
    trigger_include = [f'#include "{family_dir / "common/macros/trigger.cc"}"']
    args = "zh4l_internal_production_lepton_pt,Lepton_eta,Lepton_phi,zh4l_internal_production_lepton_pdg_id"
    aliases["zh4l_internal_trigger_z_result"] = {
        "linesToAdd": trigger_include,
        "expr": f"SelectedTrigger::selectedPairResult({args},z_lepton_index,PV_npvsGood,static_cast<int>(run_period))",
    }
    aliases["zh4l_internal_trigger_zx_result"] = {
        "expr": f"SelectedTrigger::selectedFourResult({args},z_lepton_index,x_lepton_index,PV_npvsGood,static_cast<int>(run_period))"
    }
    for domain, result in (
        ("z", "zh4l_internal_trigger_z_result"),
        ("zx", "zh4l_internal_trigger_zx_result"),
    ):
        aliases[f"sf_trigger_{domain}"] = {
            "expr": f"genWeight == 0.f ? 1.f : SelectedTrigger::at({result},4)"
        }
        aliases[f"sf_trigger_{domain}_down"] = {
            "expr": f"genWeight == 0.f ? 1.f : SelectedTrigger::at({result},5)"
        }
        aliases[f"sf_trigger_{domain}_up"] = {
            "expr": f"genWeight == 0.f ? 1.f : SelectedTrigger::at({result},6)"
        }

    bcfg = era_cfg["btag"]
    wp = resolve_btag_working_point(
        bcfg["correction_file"], bcfg["correction_prefix"], "L"
    )
    if abs(wp - float(bcfg["veto_wp"])) > 5.0e-5:
        raise RuntimeError("Configured and official BTV loose working points disagree")
    binclude = [f'#include "{family_dir / "common/macros/btag.cc"}"']
    jet_tag = f"Jet_{bcfg['algo']}"
    aliases["event_pass_b_veto"] = {
        "linesToAdd": binclude,
        "expr": f"FixedWPBTag::veto(CleanJet_pt,CleanJet_eta,CleanJet_jetIdx,{jet_tag},{wp},20.f)",
    }
    aliases["event_pass_b_veto_pt30"] = {
        "expr": f"FixedWPBTag::veto(CleanJet_pt,CleanJet_eta,CleanJet_jetIdx,{jet_tag},{wp},30.f)"
    }
    aliases["Jet_hadronFlavour"] = {
        "expr": "ROOT::VecOps::RVec<int>(Jet_pt.size(),0)",
        "samples": data_samples,
    }
    efficiency = resolve_btag_efficiency_map(bcfg["efficiency_map"])
    payload = resolve_btag_sf_payload(bcfg["correction_file"])
    shifts = ["central"]
    if systematics and _bool_env("ENABLE_SYSTEMATICS", True):
        shifts += [
            "up_correlated",
            "down_correlated",
            "up_uncorrelated",
            "down_uncorrelated",
        ]
    for flavor, group in (("bc", 1), ("light", 0)):
        for shift in shifts:
            name = f"zh4l_internal_sf_btag_{flavor}" + (
                "" if shift == "central" else f"_{shift}"
            )
            expr = (
                "FixedWPBTag::eventSF(CleanJet_pt,CleanJet_eta,CleanJet_jetIdx,"
                f"Jet_hadronFlavour,{jet_tag},{json.dumps(efficiency)},{json.dumps(payload)},"
                f"{json.dumps(bcfg['correction_prefix'])},{json.dumps(shift)},{group},{wp})"
            )
            aliases[name] = {"expr": f"genWeight == 0.f ? 1.f : {expr}"}
            if shift != "central":
                aliases[name]["samples"] = mc_samples
    aliases["sf_b_veto"] = {
        "expr": "zh4l_internal_sf_btag_bc*zh4l_internal_sf_btag_light"
    }
    if not systematics:
        for definition in aliases.values():
            prefix = "genWeight == 0.f ? 1.f : "
            if definition.get("expr", "").startswith(prefix):
                definition["expr"] = definition["expr"][len(prefix) :]
                definition["dataExpr"] = "1.f"
        aliases = {
            name: definition
            for name, definition in aliases.items()
            if not name.endswith(("_Up", "_Down", "_up", "_down"))
        }
    return aliases
