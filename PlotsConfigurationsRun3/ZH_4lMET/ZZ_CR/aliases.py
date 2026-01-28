import os

aliases = {}

configurations = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) + "/"

aliases["dileptonMass"] = {
    "linesToAdd": [
        "#include <ROOT/RVec.hxx>",
        "#include <Math/Vector4D.h>",
        "float lepMass(int pdgId) {"
        "  return (std::abs(pdgId) == 11) ? 0.000511f : 0.105658f;"
        "}",
        "int min4(int nlep) {"
        "  return (nlep > 4) ? 4 : nlep;"
        "}",
        "ROOT::VecOps::RVec<int> bestZ0Idx(const ROOT::VecOps::RVec<float>& pt, "
        "const ROOT::VecOps::RVec<float>& eta, const ROOT::VecOps::RVec<float>& phi, "
        "const ROOT::VecOps::RVec<int>& pdgId) {"
        "  ROOT::VecOps::RVec<int> out = {-1, -1};"
        "  const float mZ = 91.1876f;"
        "  float bestDiff = 1e9f;"
        "  int n = std::min<int>(pt.size(), 4);"
        "  for (int i = 0; i < n; ++i) {"
        "    for (int j = i + 1; j < n; ++j) {"
        "      if (pdgId[i] * pdgId[j] >= 0) continue;"
        "      if (std::abs(pdgId[i]) != std::abs(pdgId[j])) continue;"
        "      ROOT::Math::PtEtaPhiMVector v1(pt[i], eta[i], phi[i], lepMass(pdgId[i]));"
        "      ROOT::Math::PtEtaPhiMVector v2(pt[j], eta[j], phi[j], lepMass(pdgId[j]));"
        "      float mll = (v1 + v2).M();"
        "      float diff = std::abs(mll - mZ);"
        "      if (diff < bestDiff) {"
        "        bestDiff = diff;"
        "        out[0] = i;"
        "        out[1] = j;"
        "      }"
        "    }"
        "  }"
        "  return out;"
        "}",
        "ROOT::VecOps::RVec<int> xPairIdx(const ROOT::VecOps::RVec<int>& zidx, int nlep) {"
        "  ROOT::VecOps::RVec<int> out;"
        "  for (int i = 0; i < nlep; ++i) {"
        "    if (i != zidx[0] && i != zidx[1]) out.push_back(i);"
        "  }"
        "  if (out.size() < 2) return {-1, -1};"
        "  return {out[0], out[1]};"
        "}",
        "float pairMass(const ROOT::VecOps::RVec<float>& pt, const ROOT::VecOps::RVec<float>& eta, "
        "const ROOT::VecOps::RVec<float>& phi, const ROOT::VecOps::RVec<int>& pdgId, "
        "const ROOT::VecOps::RVec<int>& idx) {"
        "  if (idx.size() < 2 || idx[0] < 0 || idx[1] < 0) return -999.0f;"
        "  ROOT::Math::PtEtaPhiMVector v1(pt[idx[0]], eta[idx[0]], phi[idx[0]], lepMass(pdgId[idx[0]]));"
        "  ROOT::Math::PtEtaPhiMVector v2(pt[idx[1]], eta[idx[1]], phi[idx[1]], lepMass(pdgId[idx[1]]));"
        "  return (v1 + v2).M();"
        "}",
        "float pairPt(const ROOT::VecOps::RVec<float>& pt, const ROOT::VecOps::RVec<float>& eta, "
        "const ROOT::VecOps::RVec<float>& phi, const ROOT::VecOps::RVec<int>& pdgId, "
        "const ROOT::VecOps::RVec<int>& idx) {"
        "  if (idx.size() < 2 || idx[0] < 0 || idx[1] < 0) return -999.0f;"
        "  ROOT::Math::PtEtaPhiMVector v1(pt[idx[0]], eta[idx[0]], phi[idx[0]], lepMass(pdgId[idx[0]]));"
        "  ROOT::Math::PtEtaPhiMVector v2(pt[idx[1]], eta[idx[1]], phi[idx[1]], lepMass(pdgId[idx[1]]));"
        "  return (v1 + v2).Pt();"
        "}",
        "int pairFlavor(const ROOT::VecOps::RVec<int>& pdgId, const ROOT::VecOps::RVec<int>& idx) {"
        "  if (idx.size() < 2 || idx[0] < 0 || idx[1] < 0) return 0;"
        "  int flav = std::abs(pdgId[idx[0]]);"
        "  return (flav == std::abs(pdgId[idx[1]])) ? flav : 0;"
        "}",
        "float fourLeptonMass(const ROOT::VecOps::RVec<float>& pt, const ROOT::VecOps::RVec<float>& eta, "
        "const ROOT::VecOps::RVec<float>& phi, const ROOT::VecOps::RVec<int>& pdgId) {"
        "  int n = std::min<int>(pt.size(), 4);"
        "  if (n < 4) return -999.0f;"
        "  ROOT::Math::PtEtaPhiMVector v1(pt[0], eta[0], phi[0], lepMass(pdgId[0]));"
        "  ROOT::Math::PtEtaPhiMVector v2(pt[1], eta[1], phi[1], lepMass(pdgId[1]));"
        "  ROOT::Math::PtEtaPhiMVector v3(pt[2], eta[2], phi[2], lepMass(pdgId[2]));"
        "  ROOT::Math::PtEtaPhiMVector v4(pt[3], eta[3], phi[3], lepMass(pdgId[3]));"
        "  return (v1 + v2 + v3 + v4).M();"
        "}",
        "float fourLeptonPt(const ROOT::VecOps::RVec<float>& pt, const ROOT::VecOps::RVec<float>& eta, "
        "const ROOT::VecOps::RVec<float>& phi, const ROOT::VecOps::RVec<int>& pdgId) {"
        "  int n = std::min<int>(pt.size(), 4);"
        "  if (n < 4) return -999.0f;"
        "  ROOT::Math::PtEtaPhiMVector v1(pt[0], eta[0], phi[0], lepMass(pdgId[0]));"
        "  ROOT::Math::PtEtaPhiMVector v2(pt[1], eta[1], phi[1], lepMass(pdgId[1]));"
        "  ROOT::Math::PtEtaPhiMVector v3(pt[2], eta[2], phi[2], lepMass(pdgId[2]));"
        "  ROOT::Math::PtEtaPhiMVector v4(pt[3], eta[3], phi[3], lepMass(pdgId[3]));"
        "  return (v1 + v2 + v3 + v4).Pt();"
        "}",
    ],
    "expr": "1.0",
}

aliases["Z0_idx"] = {
    "expr": "bestZ0Idx(Lepton_pt, Lepton_eta, Lepton_phi, Lepton_pdgId)"
}

aliases["X_idx"] = {
    "expr": "xPairIdx(Z0_idx, min4(nLepton))"
}

aliases["Z0_mass"] = {
    "expr": "pairMass(Lepton_pt, Lepton_eta, Lepton_phi, Lepton_pdgId, Z0_idx)",
}

aliases["X_mass"] = {
    "expr": "pairMass(Lepton_pt, Lepton_eta, Lepton_phi, Lepton_pdgId, X_idx)",
}

aliases["Z0_pt"] = {
    "expr": "pairPt(Lepton_pt, Lepton_eta, Lepton_phi, Lepton_pdgId, Z0_idx)",
}

aliases["X_pt"] = {
    "expr": "pairPt(Lepton_pt, Lepton_eta, Lepton_phi, Lepton_pdgId, X_idx)",
}

aliases["m4l"] = {
    "expr": "fourLeptonMass(Lepton_pt, Lepton_eta, Lepton_phi, Lepton_pdgId)",
}

aliases["pT4l"] = {
    "expr": "fourLeptonPt(Lepton_pt, Lepton_eta, Lepton_phi, Lepton_pdgId)",
}

aliases["X_isSF"] = {
    "expr": "pairFlavor(Lepton_pdgId, X_idx) != 0"
}
aliases["X_isDF"] = {
    "expr": "pairFlavor(Lepton_pdgId, X_idx) == 0 && X_idx[0] >= 0"
}
aliases["Z0_isEE"] = {
    "expr": "pairFlavor(Lepton_pdgId, Z0_idx) == 11"
}
aliases["Z0_isMM"] = {
    "expr": "pairFlavor(Lepton_pdgId, Z0_idx) == 13"
}
aliases["X_isEE"] = {
    "expr": "pairFlavor(Lepton_pdgId, X_idx) == 11"
}
aliases["X_isMM"] = {
    "expr": "pairFlavor(Lepton_pdgId, X_idx) == 13"
}

btag_WP_loose = 0.049
aliases["bVeto"] = {
    "expr": "Sum(CleanJet_pt > 20. && abs(CleanJet_eta) < 2.5 && "
    f"Take(Jet_btagDeepFlavB, CleanJet_jetIdx) > {btag_WP_loose}) == 0",
}

aliases["sumLeptonCharge"] = {"expr": "Sum(Lepton_charge)"}

aliases["HT"] = {"expr": "Sum(CleanJet_pt)"}
