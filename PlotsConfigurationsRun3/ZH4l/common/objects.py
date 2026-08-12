"""Selected Z/X objects and common ZH4l predicates.

This is the only Python owner of the nominal Z/X definition.  The C++ helper
contains mechanics; the returned dictionary is the analyst-facing RDF API.
"""

from pathlib import Path

from mkShapesRDF.processor.data.LeptonSel_cfg import ElectronWP, MuonWP


PUBLIC_OBJECT_ALIASES = frozenset(
    {
        "Z_idx", "X_idx", "validZ", "validX", "validZX",
        "passLeading2Tight", "passZPt", "pass4lPt", "veto5l",
        "nLepton10", "isZee", "isZmm", "isXee", "isXmm", "isXSF",
        "isXDF", "mZ", "ptZ", "etaZ", "phiZ", "mX", "ptX",
        "etaX", "phiX", "m4l", "pt4l", "phi4l", "minMll4l", "q4l",
        "noJetInHorn",
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
    if not available_branches or f"Lepton_isTight{kind}_{preferred}" in available_branches:
        return preferred
    return next(
        (wp for wp in candidates if f"Lepton_isTight{kind}_{wp}" in available_branches),
        preferred,
    )


def _leading_tight_expr(era, ele_wps, mu_wps):
    def terms(index):
        return [
            *(f"Alt(Lepton_isTightElectron_{wp}, {index}, 0) > 0.5" for wp in ele_wps),
            *(f"Alt(Lepton_isTightMuon_{wp}, {index}, 0) > 0.5" for wp in mu_wps),
        ]

    i0 = "FourLepton::productionGateIndex(ZH4l_prodPt, 0)"
    i1 = "FourLepton::productionGateIndex(ZH4l_prodPt, 1)"
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
        "ZH4l_prodPt": {
            "linesToAdd": include,
            "expr": (
                "FourLepton::productionAlignedPt(Lepton_eta, Lepton_phi, "
                "Lepton_pdgId, VetoLepton_pt, VetoLepton_eta, VetoLepton_phi, "
                "VetoLepton_pdgId)"
            ),
        },
        "ZH4l_prodPdgId": {
            "expr": (
                "FourLepton::productionAlignedPdgId(Lepton_eta, Lepton_phi, "
                "VetoLepton_eta, VetoLepton_phi, VetoLepton_pdgId)"
            )
        },
        "passLeading2Tight": {
            "expr": _leading_tight_expr(l2_era, ele_wps, mu_wps)
        },
        "Z_idx": {
            "expr": (
                "FourLepton::bestZ0IdxWithID(Lepton_pt, Lepton_eta, Lepton_phi, "
                f"Lepton_pdgId, Lepton_isTightElectron_{ele_wp}, "
                f"Lepton_isTightMuon_{mu_wp}, {int(lep['z0_min_pass'])}, "
                f"{zpt[0]:g}, {zpt[1]:g})"
            )
        },
        "X_idx": {
            "expr": (
                "FourLepton::xPairIdxWithID(Z_idx, Lepton_pt, Lepton_pdgId, "
                f"Lepton_isTightElectron_{ele_wp}, Lepton_isTightMuon_{mu_wp}, "
                f"{int(lep['x_min_pass'])}, {xpt[0]:g}, {xpt[1]:g})"
            )
        },
        "validZ": {"expr": "Alt(Z_idx,0,-1) >= 0 && Alt(Z_idx,1,-1) >= 0"},
        "validX": {"expr": "Alt(X_idx,0,-1) >= 0 && Alt(X_idx,1,-1) >= 0"},
        "validZX": {
            "expr": "validZ && validX && FourLepton::fourSelectedIndicesDistinct(Z_idx, X_idx, Lepton_pt.size())"
        },
        "passZPt": {
            "expr": f"FourLepton::passesOrdered2lPtThresholdsFromPair(Lepton_pt, Z_idx, {ordered2[0]:g}, {ordered2[1]:g})"
        },
        "pass4lPt": {
            "expr": (
                "FourLepton::passesOrdered4lPtThresholdsFromPairs(Lepton_pt, "
                f"Z_idx, X_idx, {ordered4[0]:g}, {ordered4[1]:g}, "
                f"{ordered4[2]:g}, {ordered4[3]:g})"
            )
        },
        "nLepton10": {"expr": "Sum(Lepton_pt >= 10.f)"},
        "veto5l": {"expr": "FourLepton::fifthLeptonVeto(Lepton_pt, 10.f)"},
        "isZee": {"expr": "FourLepton::pairFlavor(Lepton_pdgId, Z_idx) == 11"},
        "isZmm": {"expr": "FourLepton::pairFlavor(Lepton_pdgId, Z_idx) == 13"},
        "isXee": {"expr": "FourLepton::pairFlavor(Lepton_pdgId, X_idx) == 11"},
        "isXmm": {"expr": "FourLepton::pairFlavor(Lepton_pdgId, X_idx) == 13"},
        "isXSF": {"expr": "isXee || isXmm"},
        "isXDF": {"expr": "!isXee && !isXmm"},
        "noJetInHorn": {
            "expr": "Sum(CleanJet_pt > 30 && CleanJet_pt < 50 && abs(CleanJet_eta) > 2.5 && abs(CleanJet_eta) < 3.0) == 0"
        },
    }
    aliases["mZ"] = {"expr": "FourLepton::pairMass(Lepton_pt,Lepton_eta,Lepton_phi,Lepton_pdgId,Z_idx)"}
    aliases["ptZ"] = {"expr": "FourLepton::pairPt(Lepton_pt,Lepton_eta,Lepton_phi,Lepton_pdgId,Z_idx)"}
    aliases["etaZ"] = {"expr": "FourLepton::pairEta(Lepton_pt,Lepton_eta,Lepton_phi,Lepton_pdgId,Z_idx)"}
    aliases["phiZ"] = {"expr": "FourLepton::pairPhi(Lepton_pt,Lepton_eta,Lepton_phi,Lepton_pdgId,Z_idx)"}
    aliases["mX"] = {"expr": "FourLepton::pairMass(Lepton_pt,Lepton_eta,Lepton_phi,Lepton_pdgId,X_idx)"}
    aliases["ptX"] = {"expr": "FourLepton::pairPt(Lepton_pt,Lepton_eta,Lepton_phi,Lepton_pdgId,X_idx)"}
    aliases["etaX"] = {"expr": "FourLepton::pairEta(Lepton_pt,Lepton_eta,Lepton_phi,Lepton_pdgId,X_idx)"}
    aliases["phiX"] = {"expr": "FourLepton::pairPhi(Lepton_pt,Lepton_eta,Lepton_phi,Lepton_pdgId,X_idx)"}
    aliases["m4l"] = {"expr": "FourLepton::fourLeptonMassFromPairs(Lepton_pt,Lepton_eta,Lepton_phi,Lepton_pdgId,Z_idx,X_idx)"}
    aliases["pt4l"] = {"expr": "FourLepton::fourLeptonPtFromPairs(Lepton_pt,Lepton_eta,Lepton_phi,Lepton_pdgId,Z_idx,X_idx)"}
    aliases["phi4l"] = {"expr": "FourLepton::fourLeptonPhiFromPairs(Lepton_pt,Lepton_eta,Lepton_phi,Lepton_pdgId,Z_idx,X_idx)"}
    aliases["minMll4l"] = {"expr": "FourLepton::minimumSelectedPairMass(Lepton_pt,Lepton_eta,Lepton_phi,Lepton_pdgId,Z_idx,X_idx)"}
    aliases["q4l"] = {"expr": "FourLepton::sumLeptonChargeFromPairs(Lepton_pdgId,Z_idx,X_idx)"}
    return aliases, {"electron_wp": ele_wp, "muon_wp": mu_wp}
