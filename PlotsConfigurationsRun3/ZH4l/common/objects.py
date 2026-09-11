"""Selected Z/X objects and common ZH4l predicates.

This builds the established complete Z/X alias preset. Flexible studies use
common.presets with explicit definition graphs and the same C++ mechanics.
"""

from pathlib import Path

from mkShapesRDF.processor.data.LeptonSel_cfg import ElectronWP, MuonWP


PUBLIC_OBJECT_ALIASES = frozenset(
    {
        "z_lepton_index",
        "x_lepton_index",
        "z_is_valid",
        "x_is_valid",
        "zx_is_valid",
        "event_pass_leading_lepton_tight",
        "z_pass_ordered_pt",
        "zx_pass_ordered_pt",
        "event_pass_extra_lepton_veto",
        "veto_lepton_count",
        "z_is_ee",
        "z_is_mumu",
        "x_is_ee",
        "x_is_mumu",
        "x_is_same_flavor",
        "x_is_different_flavor",
        "z_mass",
        "z_pt",
        "z_eta",
        "z_phi",
        "x_mass",
        "x_pt",
        "x_eta",
        "x_phi",
        "zx_mass",
        "zx_pt",
        "zx_phi",
        "zx_min_pair_mass",
        "zx_charge",
        "event_pass_jet_horn_veto",
    }
)


def _available_wps(kind, era, available_branches):
    source = ElectronWP if kind == "Electron" else MuonWP
    configured = tuple(source[era]["TightObjWP"])
    if not available_branches:
        return configured
    prefix = f"Lepton_isTight{kind}_"
    present = tuple(wp for wp in configured if prefix + wp in available_branches)
    return present or configured


def _selected_wp(kind, preferred, candidates, available_branches):
    if (
        not available_branches
        or f"Lepton_isTight{kind}_{preferred}" in available_branches
    ):
        return preferred
    raise ValueError(
        f"Requested Lepton_isTight{kind}_{preferred} is absent; select a supported WP explicitly"
    )


def _leading_tight_expr(era, ele_wps, mu_wps):
    def terms(index):
        return [
            *(f"Alt(Lepton_isTightElectron_{wp}, {index}, 0) > 0.5" for wp in ele_wps),
            *(f"Alt(Lepton_isTightMuon_{wp}, {index}, 0) > 0.5" for wp in mu_wps),
        ]

    i0 = "FourLepton::productionGateIndex(zh4l_internal_production_lepton_pt, 0)"
    i1 = "FourLepton::productionGateIndex(zh4l_internal_production_lepton_pt, 1)"
    return f"nLepton > 1 && ({' || '.join(terms(i0))}) && ({' || '.join(terms(i1))})"


def build_object_aliases(era_cfg, family_dir, available_branches=None):
    """Build the validated selected-object graph for one materialized era."""
    family_dir = Path(family_dir).resolve()
    helper = family_dir / "common" / "macros" / "objects.cc"
    include = [f'#include "{helper}"']
    lep = era_cfg["lepton_ids"]
    profile = lep["selection_profiles"]["run3_lowpt"]
    l2_era = era_cfg["l2tight_era"]
    if l2_era not in ElectronWP or l2_era not in MuonWP:
        raise KeyError(f"Unknown LeptonSel era {l2_era!r}")
    available = set(available_branches or ())
    ele_wps = _available_wps("Electron", l2_era, available)
    mu_wps = _available_wps("Muon", l2_era, available)
    ele_wp = _selected_wp("Electron", lep["electron_wp"], ele_wps, available)
    mu_wp = _selected_wp("Muon", lep["muon_wp"], mu_wps, available)
    zpt = tuple(float(x) for x in lep["z0_pt_mins"])
    xpt = tuple(float(x) for x in lep["x_pt_mins"])
    ordered2 = tuple(float(x) for x in profile["ordered_2l_pt_mins"])
    ordered4 = tuple(float(x) for x in profile["ordered_4l_pt_mins"])

    aliases = {
        "zh4l_internal_production_lepton_pt": {
            "linesToAdd": include,
            "expr": (
                "FourLepton::productionAlignedPt(Lepton_eta, Lepton_phi, "
                "Lepton_pdgId, VetoLepton_pt, VetoLepton_eta, VetoLepton_phi, "
                "VetoLepton_pdgId)"
            ),
        },
        "zh4l_internal_production_lepton_pdg_id": {
            "expr": (
                "FourLepton::productionAlignedPdgId(Lepton_eta, Lepton_phi, "
                "VetoLepton_eta, VetoLepton_phi, VetoLepton_pdgId)"
            )
        },
        "event_pass_leading_lepton_tight": {
            "expr": _leading_tight_expr(l2_era, ele_wps, mu_wps)
        },
        "z_lepton_index": {
            "expr": (
                "FourLepton::bestZ0IdxWithID(Lepton_pt, Lepton_eta, Lepton_phi, "
                f"Lepton_pdgId, Lepton_isTightElectron_{ele_wp}, "
                f"Lepton_isTightMuon_{mu_wp}, {int(lep['z0_min_pass'])}, "
                f"{zpt[0]:g}, {zpt[1]:g})"
            )
        },
        "x_lepton_index": {
            "expr": (
                "FourLepton::xPairIdxWithID(z_lepton_index, Lepton_pt, Lepton_pdgId, "
                f"Lepton_isTightElectron_{ele_wp}, Lepton_isTightMuon_{mu_wp}, "
                f"{int(lep['x_min_pass'])}, {xpt[0]:g}, {xpt[1]:g})"
            )
        },
        "z_is_valid": {
            "expr": "Alt(z_lepton_index,0,-1) >= 0 && Alt(z_lepton_index,1,-1) >= 0"
        },
        "x_is_valid": {
            "expr": "Alt(x_lepton_index,0,-1) >= 0 && Alt(x_lepton_index,1,-1) >= 0"
        },
        "zx_is_valid": {
            "expr": "z_is_valid && x_is_valid && FourLepton::fourSelectedIndicesDistinct(z_lepton_index, x_lepton_index, Lepton_pt.size())"
        },
        "z_pass_ordered_pt": {
            "expr": f"FourLepton::passesOrdered2lPtThresholdsFromPair(Lepton_pt, z_lepton_index, {ordered2[0]:g}, {ordered2[1]:g})"
        },
        "zx_pass_ordered_pt": {
            "expr": (
                "FourLepton::passesOrdered4lPtThresholdsFromPairs(Lepton_pt, "
                f"z_lepton_index, x_lepton_index, {ordered4[0]:g}, {ordered4[1]:g}, "
                f"{ordered4[2]:g}, {ordered4[3]:g})"
            )
        },
        "veto_lepton_count": {"expr": "Sum(Lepton_pt >= 10.f)"},
        "event_pass_extra_lepton_veto": {
            "expr": "FourLepton::fifthLeptonVeto(Lepton_pt, 10.f)"
        },
        "z_is_ee": {
            "expr": "FourLepton::pairFlavor(Lepton_pdgId, z_lepton_index) == 11"
        },
        "z_is_mumu": {
            "expr": "FourLepton::pairFlavor(Lepton_pdgId, z_lepton_index) == 13"
        },
        "x_is_ee": {
            "expr": "FourLepton::pairFlavor(Lepton_pdgId, x_lepton_index) == 11"
        },
        "x_is_mumu": {
            "expr": "FourLepton::pairFlavor(Lepton_pdgId, x_lepton_index) == 13"
        },
        "x_is_same_flavor": {"expr": "x_is_ee || x_is_mumu"},
        "x_is_different_flavor": {"expr": "!x_is_ee && !x_is_mumu"},
        "event_pass_jet_horn_veto": {
            "expr": "Sum(CleanJet_pt > 30 && CleanJet_pt < 50 && abs(CleanJet_eta) > 2.5 && abs(CleanJet_eta) < 3.0) == 0"
        },
    }
    aliases["z_mass"] = {
        "expr": "FourLepton::pairMass(Lepton_pt,Lepton_eta,Lepton_phi,Lepton_pdgId,z_lepton_index)"
    }
    aliases["z_pt"] = {
        "expr": "FourLepton::pairPt(Lepton_pt,Lepton_eta,Lepton_phi,Lepton_pdgId,z_lepton_index)"
    }
    aliases["z_eta"] = {
        "expr": "FourLepton::pairEta(Lepton_pt,Lepton_eta,Lepton_phi,Lepton_pdgId,z_lepton_index)"
    }
    aliases["z_phi"] = {
        "expr": "FourLepton::pairPhi(Lepton_pt,Lepton_eta,Lepton_phi,Lepton_pdgId,z_lepton_index)"
    }
    aliases["x_mass"] = {
        "expr": "FourLepton::pairMass(Lepton_pt,Lepton_eta,Lepton_phi,Lepton_pdgId,x_lepton_index)"
    }
    aliases["x_pt"] = {
        "expr": "FourLepton::pairPt(Lepton_pt,Lepton_eta,Lepton_phi,Lepton_pdgId,x_lepton_index)"
    }
    aliases["x_eta"] = {
        "expr": "FourLepton::pairEta(Lepton_pt,Lepton_eta,Lepton_phi,Lepton_pdgId,x_lepton_index)"
    }
    aliases["x_phi"] = {
        "expr": "FourLepton::pairPhi(Lepton_pt,Lepton_eta,Lepton_phi,Lepton_pdgId,x_lepton_index)"
    }
    aliases["zx_mass"] = {
        "expr": "FourLepton::fourLeptonMassFromPairs(Lepton_pt,Lepton_eta,Lepton_phi,Lepton_pdgId,z_lepton_index,x_lepton_index)"
    }
    aliases["zx_pt"] = {
        "expr": "FourLepton::fourLeptonPtFromPairs(Lepton_pt,Lepton_eta,Lepton_phi,Lepton_pdgId,z_lepton_index,x_lepton_index)"
    }
    aliases["zx_phi"] = {
        "expr": "FourLepton::fourLeptonPhiFromPairs(Lepton_pt,Lepton_eta,Lepton_phi,Lepton_pdgId,z_lepton_index,x_lepton_index)"
    }
    aliases["zx_min_pair_mass"] = {
        "expr": "FourLepton::minimumSelectedPairMass(Lepton_pt,Lepton_eta,Lepton_phi,Lepton_pdgId,z_lepton_index,x_lepton_index)"
    }
    aliases["zx_charge"] = {
        "expr": "FourLepton::sumLeptonChargeFromPairs(Lepton_pdgId,z_lepton_index,x_lepton_index)"
    }
    return aliases, {"electron_wp": ele_wp, "muon_wp": mu_wp}
