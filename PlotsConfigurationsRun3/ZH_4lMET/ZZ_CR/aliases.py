import os

aliases = {}

configurations = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) + "/"

aliases["dileptonMass"] = {
    "linesToAdd": [
        """
#ifndef ZH4LMET_ZZCR_HELPERS
#define ZH4LMET_ZZCR_HELPERS
#include <ROOT/RVec.hxx>
#include <Math/Vector4D.h>
namespace ZH4lMETZZCR {
  float lepMass(int pdgId) {
    return (std::abs(pdgId) == 11) ? 0.000511f : 0.105658f;
  }
  ROOT::VecOps::RVec<int> orderPairByPt(const ROOT::VecOps::RVec<int>& idx,
                                        const ROOT::VecOps::RVec<float>& pt) {
    if (idx.size() < 2 || idx[0] < 0 || idx[1] < 0) return {-1, -1};
    int i0 = idx[0];
    int i1 = idx[1];
    if (static_cast<size_t>(i0) >= pt.size() || static_cast<size_t>(i1) >= pt.size()) return {-1, -1};
    return (pt[i0] >= pt[i1]) ? ROOT::VecOps::RVec<int>{i0, i1} : ROOT::VecOps::RVec<int>{i1, i0};
  }
  ROOT::VecOps::RVec<int> bestZ0Idx(const ROOT::VecOps::RVec<float>& pt,
                                    const ROOT::VecOps::RVec<float>& eta,
                                    const ROOT::VecOps::RVec<float>& phi,
                                    const ROOT::VecOps::RVec<int>& pdgId) {
    ROOT::VecOps::RVec<int> out = {-1, -1};
    const float mZ = 91.1876f;
    float bestDiff = 1e9f;
    int n = std::min<int>(std::min<int>(pt.size(), eta.size()),
                          std::min<int>(phi.size(), pdgId.size()));
    for (int i = 0; i < n; ++i) {
      for (int j = i + 1; j < n; ++j) {
        if (pdgId[i] * pdgId[j] >= 0) continue;
        if (std::abs(pdgId[i]) != std::abs(pdgId[j])) continue;
        ROOT::Math::PtEtaPhiMVector v1(pt[i], eta[i], phi[i], lepMass(pdgId[i]));
        ROOT::Math::PtEtaPhiMVector v2(pt[j], eta[j], phi[j], lepMass(pdgId[j]));
        float mll = (v1 + v2).M();
        float diff = std::abs(mll - mZ);
        if (diff < bestDiff) {
          bestDiff = diff;
          out[0] = i;
          out[1] = j;
        }
      }
    }
    return orderPairByPt(out, pt);
  }
  ROOT::VecOps::RVec<int> xPairIdx(const ROOT::VecOps::RVec<int>& zidx,
                                   const ROOT::VecOps::RVec<float>& pt) {
    if (zidx.size() < 2 || zidx[0] < 0 || zidx[1] < 0 || zidx[0] == zidx[1]) return {-1, -1};
    if (static_cast<size_t>(zidx[0]) >= pt.size() || static_cast<size_t>(zidx[1]) >= pt.size()) return {-1, -1};

    int lead = -1;
    int sublead = -1;
    for (size_t i = 0; i < pt.size(); ++i) {
      int idx = static_cast<int>(i);
      if (idx == zidx[0] || idx == zidx[1]) continue;
      if (lead < 0 || pt[idx] > pt[lead]) {
        sublead = lead;
        lead = idx;
      } else if (sublead < 0 || pt[idx] > pt[sublead]) {
        sublead = idx;
      }
    }

    if (lead < 0 || sublead < 0) return {-1, -1};
    ROOT::VecOps::RVec<int> pair = {lead, sublead};
    return orderPairByPt(pair, pt);
  }
  bool validLeptonIndex(int idx,
                        const ROOT::VecOps::RVec<float>& pt,
                        const ROOT::VecOps::RVec<float>& eta,
                        const ROOT::VecOps::RVec<float>& phi,
                        const ROOT::VecOps::RVec<int>& pdgId) {
    if (idx < 0) return false;
    size_t i = static_cast<size_t>(idx);
    return i < pt.size() && i < eta.size() && i < phi.size() && i < pdgId.size();
  }
  bool validPairIndices(const ROOT::VecOps::RVec<int>& idx,
                        const ROOT::VecOps::RVec<float>& pt,
                        const ROOT::VecOps::RVec<float>& eta,
                        const ROOT::VecOps::RVec<float>& phi,
                        const ROOT::VecOps::RVec<int>& pdgId) {
    if (idx.size() < 2) return false;
    return validLeptonIndex(idx[0], pt, eta, phi, pdgId) &&
           validLeptonIndex(idx[1], pt, eta, phi, pdgId);
  }
  float pairMass(const ROOT::VecOps::RVec<float>& pt, const ROOT::VecOps::RVec<float>& eta,
                 const ROOT::VecOps::RVec<float>& phi, const ROOT::VecOps::RVec<int>& pdgId,
                 const ROOT::VecOps::RVec<int>& idx) {
    if (!validPairIndices(idx, pt, eta, phi, pdgId)) return -999.0f;
    ROOT::Math::PtEtaPhiMVector v1(pt[idx[0]], eta[idx[0]], phi[idx[0]], lepMass(pdgId[idx[0]]));
    ROOT::Math::PtEtaPhiMVector v2(pt[idx[1]], eta[idx[1]], phi[idx[1]], lepMass(pdgId[idx[1]]));
    return (v1 + v2).M();
  }
  float pairPt(const ROOT::VecOps::RVec<float>& pt, const ROOT::VecOps::RVec<float>& eta,
               const ROOT::VecOps::RVec<float>& phi, const ROOT::VecOps::RVec<int>& pdgId,
               const ROOT::VecOps::RVec<int>& idx) {
    if (!validPairIndices(idx, pt, eta, phi, pdgId)) return -999.0f;
    ROOT::Math::PtEtaPhiMVector v1(pt[idx[0]], eta[idx[0]], phi[idx[0]], lepMass(pdgId[idx[0]]));
    ROOT::Math::PtEtaPhiMVector v2(pt[idx[1]], eta[idx[1]], phi[idx[1]], lepMass(pdgId[idx[1]]));
    return (v1 + v2).Pt();
  }
  int pairFlavor(const ROOT::VecOps::RVec<int>& pdgId, const ROOT::VecOps::RVec<int>& idx) {
    if (idx.size() < 2 || idx[0] < 0 || idx[1] < 0) return 0;
    if (static_cast<size_t>(idx[0]) >= pdgId.size() || static_cast<size_t>(idx[1]) >= pdgId.size()) return 0;
    int flav = std::abs(pdgId[idx[0]]);
    return (flav == std::abs(pdgId[idx[1]])) ? flav : 0;
  }
  float fourLeptonMassFromPairs(const ROOT::VecOps::RVec<float>& pt,
                                const ROOT::VecOps::RVec<float>& eta,
                                const ROOT::VecOps::RVec<float>& phi,
                                const ROOT::VecOps::RVec<int>& pdgId,
                                const ROOT::VecOps::RVec<int>& zidx,
                                const ROOT::VecOps::RVec<int>& xidx) {
    if (!validPairIndices(zidx, pt, eta, phi, pdgId) || !validPairIndices(xidx, pt, eta, phi, pdgId)) return -999.0f;
    if (zidx[0] == xidx[0] || zidx[0] == xidx[1] || zidx[1] == xidx[0] || zidx[1] == xidx[1]) return -999.0f;
    ROOT::Math::PtEtaPhiMVector vz1(pt[zidx[0]], eta[zidx[0]], phi[zidx[0]], lepMass(pdgId[zidx[0]]));
    ROOT::Math::PtEtaPhiMVector vz2(pt[zidx[1]], eta[zidx[1]], phi[zidx[1]], lepMass(pdgId[zidx[1]]));
    ROOT::Math::PtEtaPhiMVector vx1(pt[xidx[0]], eta[xidx[0]], phi[xidx[0]], lepMass(pdgId[xidx[0]]));
    ROOT::Math::PtEtaPhiMVector vx2(pt[xidx[1]], eta[xidx[1]], phi[xidx[1]], lepMass(pdgId[xidx[1]]));
    return (vz1 + vz2 + vx1 + vx2).M();
  }
  float fourLeptonPtFromPairs(const ROOT::VecOps::RVec<float>& pt,
                              const ROOT::VecOps::RVec<float>& eta,
                              const ROOT::VecOps::RVec<float>& phi,
                              const ROOT::VecOps::RVec<int>& pdgId,
                              const ROOT::VecOps::RVec<int>& zidx,
                              const ROOT::VecOps::RVec<int>& xidx) {
    if (!validPairIndices(zidx, pt, eta, phi, pdgId) || !validPairIndices(xidx, pt, eta, phi, pdgId)) return -999.0f;
    if (zidx[0] == xidx[0] || zidx[0] == xidx[1] || zidx[1] == xidx[0] || zidx[1] == xidx[1]) return -999.0f;
    ROOT::Math::PtEtaPhiMVector vz1(pt[zidx[0]], eta[zidx[0]], phi[zidx[0]], lepMass(pdgId[zidx[0]]));
    ROOT::Math::PtEtaPhiMVector vz2(pt[zidx[1]], eta[zidx[1]], phi[zidx[1]], lepMass(pdgId[zidx[1]]));
    ROOT::Math::PtEtaPhiMVector vx1(pt[xidx[0]], eta[xidx[0]], phi[xidx[0]], lepMass(pdgId[xidx[0]]));
    ROOT::Math::PtEtaPhiMVector vx2(pt[xidx[1]], eta[xidx[1]], phi[xidx[1]], lepMass(pdgId[xidx[1]]));
    return (vz1 + vz2 + vx1 + vx2).Pt();
  }
  ROOT::VecOps::RVec<int> genPdgIdFromIdx(const ROOT::VecOps::RVec<int>& genIdx,
                                          const ROOT::VecOps::RVec<int>& genPdgId) {
    ROOT::VecOps::RVec<int> out(genIdx.size(), 0);
    for (size_t i = 0; i < genIdx.size(); ++i) {
      int idx = genIdx[i];
      if (idx >= 0 && static_cast<size_t>(idx) < genPdgId.size()) {
        out[i] = genPdgId[idx];
      }
    }
    return out;
  }
  ROOT::VecOps::RVec<float> genFloatFromIdx(const ROOT::VecOps::RVec<int>& genIdx,
                                            const ROOT::VecOps::RVec<float>& genValues) {
    ROOT::VecOps::RVec<float> out(genIdx.size(), 0.0f);
    for (size_t i = 0; i < genIdx.size(); ++i) {
      int idx = genIdx[i];
      if (idx >= 0 && static_cast<size_t>(idx) < genValues.size()) {
        out[i] = genValues[idx];
      }
    }
    return out;
  }
  ROOT::VecOps::RVec<int> leptonGenPartIdx(const ROOT::VecOps::RVec<int>& leptonPdgId,
                                           const ROOT::VecOps::RVec<int>& leptonElectronIdx,
                                           const ROOT::VecOps::RVec<int>& leptonMuonIdx,
                                           const ROOT::VecOps::RVec<int>& electronGenPartIdx,
                                           const ROOT::VecOps::RVec<int>& muonGenPartIdx) {
    ROOT::VecOps::RVec<int> out(leptonPdgId.size(), -1);
    for (size_t i = 0; i < leptonPdgId.size(); ++i) {
      int pdgId = leptonPdgId[i];
      if (std::abs(pdgId) == 11) {
        int idx = leptonElectronIdx[i];
        if (idx >= 0 && static_cast<size_t>(idx) < electronGenPartIdx.size()) {
          out[i] = electronGenPartIdx[idx];
        }
      } else if (std::abs(pdgId) == 13) {
        int idx = leptonMuonIdx[i];
        if (idx >= 0 && static_cast<size_t>(idx) < muonGenPartIdx.size()) {
          out[i] = muonGenPartIdx[idx];
        }
      }
    }
    return out;
  }
}
#endif
        """,
    ],
    "expr": "1.0",
}

aliases["Z0_idx"] = {
    "expr": "ZH4lMETZZCR::bestZ0Idx(Lepton_pt, Lepton_eta, Lepton_phi, Lepton_pdgId)"
}

aliases["X_idx"] = {
    "expr": "ZH4lMETZZCR::xPairIdx(Z0_idx, Lepton_pt)"
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

btag_WP_loose = 0.049
aliases["bVeto"] = {
    "expr": "Sum(CleanJet_pt > 20. && abs(CleanJet_eta) < 2.5 && "
    f"Take(Jet_btagDeepFlavB, CleanJet_jetIdx) > {btag_WP_loose}) == 0",
}

aliases["sumLeptonCharge"] = {
    "expr": "Sum(-Lepton_pdgId / abs(Lepton_pdgId))"
}

aliases["HT"] = {"expr": "Sum(CleanJet_pt)"}

aliases["GenMET_pt"] = {
    "expr": "0.0",
    "samples": ["DATA"],
}

aliases["GenMET_phi"] = {
    "expr": "0.0",
    "samples": ["DATA"],
}

aliases["GenPart_pdgId"] = {
    "expr": "ROOT::VecOps::RVec<int>()",
    "samples": ["DATA"],
}

aliases["GenPart_pt"] = {
    "expr": "ROOT::VecOps::RVec<float>()",
    "samples": ["DATA"],
}

aliases["GenPart_eta"] = {
    "expr": "ROOT::VecOps::RVec<float>()",
    "samples": ["DATA"],
}

aliases["GenPart_phi"] = {
    "expr": "ROOT::VecOps::RVec<float>()",
    "samples": ["DATA"],
}

aliases["Electron_genPartIdx"] = {
    "expr": "ROOT::VecOps::RVec<int>()",
    "samples": ["DATA"],
}

aliases["Muon_genPartIdx"] = {
    "expr": "ROOT::VecOps::RVec<int>()",
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
