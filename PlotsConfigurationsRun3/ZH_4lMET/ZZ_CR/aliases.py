import os

aliases = {}

configurations = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) + "/"

aliases["Z0_idx"] = {
    "linesToAdd": ['#include "%s/PlotsConfigurationsRun3/ZH_4lMET/ZZ_CR/macros/zh4lmet_zzcr_helpers.cc"' % configurations],
    "expr": "ZH4lMETZZCR::bestZ0Idx(Lepton_pt, Lepton_eta, Lepton_phi, Lepton_pdgId)"
}

aliases["X_idx"] = {
    "expr": "ZH4lMETZZCR::xPairIdx(Z0_idx, Lepton_pt)"
}


aliases["PuppiMET_significance"] = {
    "expr": "PuppiMET_significance"
}

aliases["PuppiMET_sumPtUnclustered"] = {
    "expr": "PuppiMET_sumEt"
}

aliases["Z0_mass"] = {
    "expr": "ZH4lMETZZCR::pairMass(Lepton_pt, Lepton_eta, Lepton_phi, Lepton_pdgId, Z0_idx)",
}

aliases["X_mass"] = {
    "expr": "ZH4lMETZZCR::pairMass(Lepton_pt, Lepton_eta, Lepton_phi, Lepton_pdgId, X_idx)",
}

aliases["Z0_pt"] = {
    "expr": "ZH4lMETZZCR::pairPt(Lepton_pt, Lepton_eta, Lepton_phi, Lepton_pdgId, Z0_idx)",
}

aliases["X_pt"] = {
    "expr": "ZH4lMETZZCR::pairPt(Lepton_pt, Lepton_eta, Lepton_phi, Lepton_pdgId, X_idx)",
}

aliases["m4l"] = {
    "expr": "ZH4lMETZZCR::fourLeptonMassFromPairs(Lepton_pt, Lepton_eta, Lepton_phi, Lepton_pdgId, Z0_idx, X_idx)",
}

aliases["pT4l"] = {
    "expr": "ZH4lMETZZCR::fourLeptonPtFromPairs(Lepton_pt, Lepton_eta, Lepton_phi, Lepton_pdgId, Z0_idx, X_idx)",
}


aliases["Z0_phi"] = {
    "expr": "ZH4lMETZZCR::pairPhi(Lepton_pt, Lepton_eta, Lepton_phi, Lepton_pdgId, Z0_idx)",
}

aliases["X_phi"] = {
    "expr": "ZH4lMETZZCR::pairPhi(Lepton_pt, Lepton_eta, Lepton_phi, Lepton_pdgId, X_idx)",
}

aliases["phi4l"] = {
    "expr": "ZH4lMETZZCR::fourLeptonPhiFromPairs(Lepton_pt, Lepton_eta, Lepton_phi, Lepton_pdgId, Z0_idx, X_idx)",
}

aliases["lZ1_phi"] = {
    "expr": "ZH4lMETZZCR::leptonPhiAtIdx(Lepton_phi, Alt(Z0_idx, 0, -1))"
}
aliases["lZ2_phi"] = {
    "expr": "ZH4lMETZZCR::leptonPhiAtIdx(Lepton_phi, Alt(Z0_idx, 1, -1))"
}
aliases["lX1_phi"] = {
    "expr": "ZH4lMETZZCR::leptonPhiAtIdx(Lepton_phi, Alt(X_idx, 0, -1))"
}
aliases["lX2_phi"] = {
    "expr": "ZH4lMETZZCR::leptonPhiAtIdx(Lepton_phi, Alt(X_idx, 1, -1))"
}

aliases["dPhi_MET_Z"] = {"expr": "ZH4lMETZZCR::deltaPhi(PuppiMET_phi, Z0_phi)"}
aliases["dPhi_MET_X"] = {"expr": "ZH4lMETZZCR::deltaPhi(PuppiMET_phi, X_phi)"}
aliases["dPhi_MET_lZ1"] = {"expr": "ZH4lMETZZCR::deltaPhi(PuppiMET_phi, lZ1_phi)"}
aliases["dPhi_MET_lZ2"] = {"expr": "ZH4lMETZZCR::deltaPhi(PuppiMET_phi, lZ2_phi)"}
aliases["dPhi_MET_lX1"] = {"expr": "ZH4lMETZZCR::deltaPhi(PuppiMET_phi, lX1_phi)"}
aliases["dPhi_MET_lX2"] = {"expr": "ZH4lMETZZCR::deltaPhi(PuppiMET_phi, lX2_phi)"}
aliases["dPhi_MET_ZplusX"] = {"expr": "ZH4lMETZZCR::deltaPhi(PuppiMET_phi, phi4l)"}

aliases["dPhi_lZ1_lZ2"] = {"expr": "ZH4lMETZZCR::deltaPhi(lZ1_phi, lZ2_phi)"}
aliases["dPhi_lZ1_lX1"] = {"expr": "ZH4lMETZZCR::deltaPhi(lZ1_phi, lX1_phi)"}
aliases["dPhi_lZ1_lX2"] = {"expr": "ZH4lMETZZCR::deltaPhi(lZ1_phi, lX2_phi)"}
aliases["dPhi_lZ2_lX1"] = {"expr": "ZH4lMETZZCR::deltaPhi(lZ2_phi, lX1_phi)"}
aliases["dPhi_lZ2_lX2"] = {"expr": "ZH4lMETZZCR::deltaPhi(lZ2_phi, lX2_phi)"}
aliases["dPhi_lX1_lX2"] = {"expr": "ZH4lMETZZCR::deltaPhi(lX1_phi, lX2_phi)"}

aliases["recoil_ux"] = {"expr": "ZH4lMETZZCR::recoilUx(pT4l, phi4l, PuppiMET_pt, PuppiMET_phi)"}
aliases["recoil_uy"] = {"expr": "ZH4lMETZZCR::recoilUy(pT4l, phi4l, PuppiMET_pt, PuppiMET_phi)"}
aliases["recoil_ut"] = {"expr": "ZH4lMETZZCR::recoilUt(pT4l, phi4l, PuppiMET_pt, PuppiMET_phi)"}
aliases["recoil_upar"] = {"expr": "ZH4lMETZZCR::recoilUpar(pT4l, phi4l, PuppiMET_pt, PuppiMET_phi)"}
aliases["recoil_uperp"] = {"expr": "ZH4lMETZZCR::recoilUperp(pT4l, phi4l, PuppiMET_pt, PuppiMET_phi)"}
aliases["recoil_upar_bal"] = {"expr": "-recoil_upar"}

aliases["X_isSF"] = {
    "expr": "ZH4lMETZZCR::pairFlavor(Lepton_pdgId, X_idx) != 0"
}
aliases["X_isDF"] = {
    "expr": "ZH4lMETZZCR::pairFlavor(Lepton_pdgId, X_idx) == 0 && X_idx[0] >= 0"
}
aliases["Z0_isEE"] = {
    "expr": "ZH4lMETZZCR::pairFlavor(Lepton_pdgId, Z0_idx) == 11"
}
aliases["Z0_isMM"] = {
    "expr": "ZH4lMETZZCR::pairFlavor(Lepton_pdgId, Z0_idx) == 13"
}
aliases["X_isEE"] = {
    "expr": "ZH4lMETZZCR::pairFlavor(Lepton_pdgId, X_idx) == 11"
}
aliases["X_isMM"] = {
    "expr": "ZH4lMETZZCR::pairFlavor(Lepton_pdgId, X_idx) == 13"
}

# use UParT
# https://indico.cern.ch/event/1556659/contributions/6559758/attachments/3083466/5458488/BTag_250610_Summer24WPs.pdf
# https://cms-talk.web.cern.ch/t/ak4-b-tagging-and-c-tagging-working-points-for-runiiisummer24-now-available/126466
# https://github.com/cms-btv-pog/BTVNanoCommissioning/blob/master/src/BTVNanoCommissioning/utils/selection.py#L394-L412
# https://github.com/cms-btv-pog/BTVNanoCommissioning/blob/master/src/BTVNanoCommissioning/utils/selection.py#L45-L74
# https://gitlab.cern.ch/cms-btv/btv-scale-factors
# https://gitlab.cern.ch/cms-btv/btv-scale-factors/-/blob/master/2024_Summer24/wp/wp_database_btagging.yml?ref_type=heads

btag_veto_algo = "btagDeepFlavB"
btag_veto_WP = 0.0485
aliases[f"bVeto"] = {
    "expr": f"ZH4lMETZZCR::bVetoDeepFlavB(CleanJet_pt, CleanJet_eta, CleanJet_jetIdx, Jet_{btag_veto_algo}, {btag_veto_WP})",
}

aliases["sumLeptonCharge"] = {
    "expr": "ZH4lMETZZCR::sumLeptonChargeFromPairs(Lepton_pdgId, Z0_idx, X_idx)"
}

aliases["HT"] = {"expr": "Sum(CleanJet_pt)"}

aliases["GenMET_pt"] = {
    "expr": "ZH4lMETZZCR::zeroFloat()",
    "samples": ["DATA"],
}

aliases["GenMET_phi"] = {
    "expr": "ZH4lMETZZCR::zeroFloat()",
    "samples": ["DATA"],
}

aliases["GenPart_pdgId"] = {
    "expr": "ZH4lMETZZCR::emptyIntVec()",
    "samples": ["DATA"],
}

aliases["GenPart_pt"] = {
    "expr": "ZH4lMETZZCR::emptyFloatVec()",
    "samples": ["DATA"],
}

aliases["GenPart_eta"] = {
    "expr": "ZH4lMETZZCR::emptyFloatVec()",
    "samples": ["DATA"],
}

aliases["GenPart_phi"] = {
    "expr": "ZH4lMETZZCR::emptyFloatVec()",
    "samples": ["DATA"],
}

aliases["Electron_genPartIdx"] = {
    "expr": "ZH4lMETZZCR::emptyIntVec()",
    "samples": ["DATA"],
}

aliases["Muon_genPartIdx"] = {
    "expr": "ZH4lMETZZCR::emptyIntVec()",
    "samples": ["DATA"],
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
