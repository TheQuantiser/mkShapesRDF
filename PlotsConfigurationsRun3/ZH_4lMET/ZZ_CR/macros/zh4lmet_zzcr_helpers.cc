#ifndef ZH4LMET_ZZCR_HELPERS
#define ZH4LMET_ZZCR_HELPERS
#include <Math/Vector4D.h>
#include <ROOT/RVec.hxx>
#include <cmath>
namespace ZH4lMETZZCR {
float zeroFloat() { return 0.0f; }
ROOT::VecOps::RVec<int> emptyIntVec() { return ROOT::VecOps::RVec<int>(); }
ROOT::VecOps::RVec<float> emptyFloatVec() {
  return ROOT::VecOps::RVec<float>();
}
bool bVetoDeepFlavB(const ROOT::VecOps::RVec<float> &cleanJetPt,
                    const ROOT::VecOps::RVec<float> &cleanJetEta,
                    const ROOT::VecOps::RVec<int> &cleanJetJetIdx,
                    const ROOT::VecOps::RVec<float> &jetBtagDeepFlavB,
                    float btagVetoWP) {
  const size_t n = std::min<size_t>(
      cleanJetPt.size(),
      std::min<size_t>(cleanJetEta.size(), cleanJetJetIdx.size()));
  for (size_t i = 0; i < n; ++i) {
    if (cleanJetPt[i] <= 30.f || std::abs(cleanJetEta[i]) >= 2.5f)
      continue;
    const int jetIdx = cleanJetJetIdx[i];
    if (jetIdx < 0 || static_cast<size_t>(jetIdx) >= jetBtagDeepFlavB.size())
      continue;
    if (jetBtagDeepFlavB[jetIdx] > btagVetoWP)
      return false;
  }
  return true;
}
float lepMass(int pdgId) {
  return (std::abs(pdgId) == 11) ? 0.000511f : 0.105658f;
}
ROOT::VecOps::RVec<int> orderPairByPt(const ROOT::VecOps::RVec<int> &idx,
                                      const ROOT::VecOps::RVec<float> &pt) {
  if (idx.size() < 2 || idx[0] < 0 || idx[1] < 0)
    return {-1, -1};
  int i0 = idx[0];
  int i1 = idx[1];
  if (static_cast<size_t>(i0) >= pt.size() ||
      static_cast<size_t>(i1) >= pt.size())
    return {-1, -1};
  return (pt[i0] >= pt[i1]) ? ROOT::VecOps::RVec<int>{i0, i1}
                            : ROOT::VecOps::RVec<int>{i1, i0};
}

int clampPairMinPassID(int minPassID) {
  if (minPassID < 0)
    return 0;
  if (minPassID > 2)
    return 2;
  return minPassID;
}
float clampPtMin(float ptMin) { return (ptMin < 0.f) ? 0.f : ptMin; }
bool leptonPassesPairWP(int idx, const ROOT::VecOps::RVec<int> &pdgId,
                        const ROOT::VecOps::RVec<bool> &passEleWP,
                        const ROOT::VecOps::RVec<bool> &passMuWP) {
  if (idx < 0 || static_cast<size_t>(idx) >= pdgId.size())
    return false;
  const int absPdgId = std::abs(pdgId[idx]);
  if (absPdgId == 11) {
    return static_cast<size_t>(idx) < passEleWP.size() && passEleWP[idx] != 0;
  }
  if (absPdgId == 13) {
    return static_cast<size_t>(idx) < passMuWP.size() && passMuWP[idx] != 0;
  }
  return false;
}
bool pairPassesIDRequirement(const ROOT::VecOps::RVec<int> &pairIdx,
                             const ROOT::VecOps::RVec<int> &pdgId,
                             const ROOT::VecOps::RVec<bool> &passEleWP,
                             const ROOT::VecOps::RVec<bool> &passMuWP,
                             int minPassID) {
  if (pairIdx.size() < 2 || pairIdx[0] < 0 || pairIdx[1] < 0)
    return false;
  const int required = clampPairMinPassID(minPassID);
  if (required == 0)
    return true;

  int nPass = 0;
  if (leptonPassesPairWP(pairIdx[0], pdgId, passEleWP, passMuWP))
    ++nPass;
  if (leptonPassesPairWP(pairIdx[1], pdgId, passEleWP, passMuWP))
    ++nPass;
  return nPass >= required;
}
bool pairPassesPtRequirement(const ROOT::VecOps::RVec<int> &pairIdx,
                             const ROOT::VecOps::RVec<float> &pt,
                             float leadPtMin, float subleadPtMin) {
  ROOT::VecOps::RVec<int> ordered = orderPairByPt(pairIdx, pt);
  if (ordered.size() < 2 || ordered[0] < 0 || ordered[1] < 0)
    return false;
  const float leadMin = clampPtMin(leadPtMin);
  const float subleadMin = clampPtMin(subleadPtMin);
  return pt[ordered[0]] >= leadMin && pt[ordered[1]] >= subleadMin;
}
bool pairPassesSelection(const ROOT::VecOps::RVec<int> &pairIdx,
                         const ROOT::VecOps::RVec<float> &pt,
                         const ROOT::VecOps::RVec<int> &pdgId,
                         const ROOT::VecOps::RVec<bool> &passEleWP,
                         const ROOT::VecOps::RVec<bool> &passMuWP,
                         int minPassID, float leadPtMin, float subleadPtMin) {
  return pairPassesIDRequirement(pairIdx, pdgId, passEleWP, passMuWP,
                                 minPassID) &&
         pairPassesPtRequirement(pairIdx, pt, leadPtMin, subleadPtMin);
}
ROOT::VecOps::RVec<int> bestZ0IdxWithID(
    const ROOT::VecOps::RVec<float> &pt, const ROOT::VecOps::RVec<float> &eta,
    const ROOT::VecOps::RVec<float> &phi, const ROOT::VecOps::RVec<int> &pdgId,
    const ROOT::VecOps::RVec<bool> &passEleWP,
    const ROOT::VecOps::RVec<bool> &passMuWP, int minPassID, float leadPtMin,
    float subleadPtMin) {
  ROOT::VecOps::RVec<int> out = {-1, -1};
  const float mZ = 91.1876f;
  float bestDiff = 1e9f;
  int n = std::min<int>(std::min<int>(pt.size(), eta.size()),
                        std::min<int>(phi.size(), pdgId.size()));
  for (int i = 0; i < n; ++i) {
    ROOT::Math::PtEtaPhiMVector v1(pt[i], eta[i], phi[i], lepMass(pdgId[i]));
    for (int j = i + 1; j < n; ++j) {
      if (std::abs(pdgId[i]) != std::abs(pdgId[j]))
        continue;
      ROOT::VecOps::RVec<int> cand = {i, j};
      if (!pairPassesSelection(cand, pt, pdgId, passEleWP, passMuWP, minPassID,
                               leadPtMin, subleadPtMin))
        continue;
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
ROOT::VecOps::RVec<int> bestZ0Idx(const ROOT::VecOps::RVec<float> &pt,
                                  const ROOT::VecOps::RVec<float> &eta,
                                  const ROOT::VecOps::RVec<float> &phi,
                                  const ROOT::VecOps::RVec<int> &pdgId) {
  return bestZ0IdxWithID(
      pt, eta, phi, pdgId, ROOT::VecOps::RVec<bool>(pdgId.size(), false),
      ROOT::VecOps::RVec<bool>(pdgId.size(), false), 0, 0.f, 0.f);
}
ROOT::VecOps::RVec<int>
xPairIdxWithID(const ROOT::VecOps::RVec<int> &zidx,
               const ROOT::VecOps::RVec<float> &pt,
               const ROOT::VecOps::RVec<int> &pdgId,
               const ROOT::VecOps::RVec<bool> &passEleWP,
               const ROOT::VecOps::RVec<bool> &passMuWP, int minPassID,
               float leadPtMin, float subleadPtMin) {
  if (zidx.size() < 2 || zidx[0] < 0 || zidx[1] < 0 || zidx[0] == zidx[1])
    return {-1, -1};
  if (static_cast<size_t>(zidx[0]) >= pt.size() ||
      static_cast<size_t>(zidx[1]) >= pt.size())
    return {-1, -1};

  int lead = -1;
  int sublead = -1;
  for (size_t i = 0; i < pt.size(); ++i) {
    int idx = static_cast<int>(i);
    if (idx == zidx[0] || idx == zidx[1])
      continue;
    if (lead < 0 || pt[idx] > pt[lead]) {
      sublead = lead;
      lead = idx;
    } else if (sublead < 0 || pt[idx] > pt[sublead]) {
      sublead = idx;
    }
  }

  if (lead < 0 || sublead < 0)
    return {-1, -1};
  ROOT::VecOps::RVec<int> pair =
      orderPairByPt(ROOT::VecOps::RVec<int>{lead, sublead}, pt);
  if (!pairPassesSelection(pair, pt, pdgId, passEleWP, passMuWP, minPassID,
                           leadPtMin, subleadPtMin))
    return {-1, -1};
  return pair;
}
ROOT::VecOps::RVec<int> xPairIdx(const ROOT::VecOps::RVec<int> &zidx,
                                 const ROOT::VecOps::RVec<float> &pt) {
  if (zidx.size() < 2 || zidx[0] < 0 || zidx[1] < 0 || zidx[0] == zidx[1])
    return {-1, -1};
  if (static_cast<size_t>(zidx[0]) >= pt.size() ||
      static_cast<size_t>(zidx[1]) >= pt.size())
    return {-1, -1};

  int lead = -1;
  int sublead = -1;
  for (size_t i = 0; i < pt.size(); ++i) {
    int idx = static_cast<int>(i);
    if (idx == zidx[0] || idx == zidx[1])
      continue;
    if (lead < 0 || pt[idx] > pt[lead]) {
      sublead = lead;
      lead = idx;
    } else if (sublead < 0 || pt[idx] > pt[sublead]) {
      sublead = idx;
    }
  }

  if (lead < 0 || sublead < 0)
    return {-1, -1};
  ROOT::VecOps::RVec<int> pair = {lead, sublead};
  return orderPairByPt(pair, pt);
}
bool validLeptonIndex(int idx, const ROOT::VecOps::RVec<float> &pt,
                      const ROOT::VecOps::RVec<float> &eta,
                      const ROOT::VecOps::RVec<float> &phi,
                      const ROOT::VecOps::RVec<int> &pdgId) {
  if (idx < 0)
    return false;
  size_t i = static_cast<size_t>(idx);
  return i < pt.size() && i < eta.size() && i < phi.size() && i < pdgId.size();
}
bool validPairIndices(const ROOT::VecOps::RVec<int> &idx,
                      const ROOT::VecOps::RVec<float> &pt,
                      const ROOT::VecOps::RVec<float> &eta,
                      const ROOT::VecOps::RVec<float> &phi,
                      const ROOT::VecOps::RVec<int> &pdgId) {
  if (idx.size() < 2)
    return false;
  return validLeptonIndex(idx[0], pt, eta, phi, pdgId) &&
         validLeptonIndex(idx[1], pt, eta, phi, pdgId);
}
float pairMass(const ROOT::VecOps::RVec<float> &pt,
               const ROOT::VecOps::RVec<float> &eta,
               const ROOT::VecOps::RVec<float> &phi,
               const ROOT::VecOps::RVec<int> &pdgId,
               const ROOT::VecOps::RVec<int> &idx) {
  if (!validPairIndices(idx, pt, eta, phi, pdgId))
    return -999.0f;
  ROOT::Math::PtEtaPhiMVector v1(pt[idx[0]], eta[idx[0]], phi[idx[0]],
                                 lepMass(pdgId[idx[0]]));
  ROOT::Math::PtEtaPhiMVector v2(pt[idx[1]], eta[idx[1]], phi[idx[1]],
                                 lepMass(pdgId[idx[1]]));
  return (v1 + v2).M();
}
float pairPt(const ROOT::VecOps::RVec<float> &pt,
             const ROOT::VecOps::RVec<float> &eta,
             const ROOT::VecOps::RVec<float> &phi,
             const ROOT::VecOps::RVec<int> &pdgId,
             const ROOT::VecOps::RVec<int> &idx) {
  if (!validPairIndices(idx, pt, eta, phi, pdgId))
    return -999.0f;
  ROOT::Math::PtEtaPhiMVector v1(pt[idx[0]], eta[idx[0]], phi[idx[0]],
                                 lepMass(pdgId[idx[0]]));
  ROOT::Math::PtEtaPhiMVector v2(pt[idx[1]], eta[idx[1]], phi[idx[1]],
                                 lepMass(pdgId[idx[1]]));
  return (v1 + v2).Pt();
}
float pairPhi(const ROOT::VecOps::RVec<float> &pt,
              const ROOT::VecOps::RVec<float> &eta,
              const ROOT::VecOps::RVec<float> &phi,
              const ROOT::VecOps::RVec<int> &pdgId,
              const ROOT::VecOps::RVec<int> &idx) {
  if (!validPairIndices(idx, pt, eta, phi, pdgId))
    return -999.0f;
  ROOT::Math::PtEtaPhiMVector v1(pt[idx[0]], eta[idx[0]], phi[idx[0]],
                                 lepMass(pdgId[idx[0]]));
  ROOT::Math::PtEtaPhiMVector v2(pt[idx[1]], eta[idx[1]], phi[idx[1]],
                                 lepMass(pdgId[idx[1]]));
  return (v1 + v2).Phi();
}
int pairFlavor(const ROOT::VecOps::RVec<int> &pdgId,
               const ROOT::VecOps::RVec<int> &idx) {
  if (idx.size() < 2 || idx[0] < 0 || idx[1] < 0)
    return 0;
  if (static_cast<size_t>(idx[0]) >= pdgId.size() ||
      static_cast<size_t>(idx[1]) >= pdgId.size())
    return 0;
  int flav = std::abs(pdgId[idx[0]]);
  return (flav == std::abs(pdgId[idx[1]])) ? flav : 0;
}
float fourLeptonMassFromPairs(const ROOT::VecOps::RVec<float> &pt,
                              const ROOT::VecOps::RVec<float> &eta,
                              const ROOT::VecOps::RVec<float> &phi,
                              const ROOT::VecOps::RVec<int> &pdgId,
                              const ROOT::VecOps::RVec<int> &zidx,
                              const ROOT::VecOps::RVec<int> &xidx) {
  if (!validPairIndices(zidx, pt, eta, phi, pdgId) ||
      !validPairIndices(xidx, pt, eta, phi, pdgId))
    return -999.0f;
  if (zidx[0] == xidx[0] || zidx[0] == xidx[1] || zidx[1] == xidx[0] ||
      zidx[1] == xidx[1])
    return -999.0f;
  ROOT::Math::PtEtaPhiMVector vz1(pt[zidx[0]], eta[zidx[0]], phi[zidx[0]],
                                  lepMass(pdgId[zidx[0]]));
  ROOT::Math::PtEtaPhiMVector vz2(pt[zidx[1]], eta[zidx[1]], phi[zidx[1]],
                                  lepMass(pdgId[zidx[1]]));
  ROOT::Math::PtEtaPhiMVector vx1(pt[xidx[0]], eta[xidx[0]], phi[xidx[0]],
                                  lepMass(pdgId[xidx[0]]));
  ROOT::Math::PtEtaPhiMVector vx2(pt[xidx[1]], eta[xidx[1]], phi[xidx[1]],
                                  lepMass(pdgId[xidx[1]]));
  return (vz1 + vz2 + vx1 + vx2).M();
}
float fourLeptonPtFromPairs(const ROOT::VecOps::RVec<float> &pt,
                            const ROOT::VecOps::RVec<float> &eta,
                            const ROOT::VecOps::RVec<float> &phi,
                            const ROOT::VecOps::RVec<int> &pdgId,
                            const ROOT::VecOps::RVec<int> &zidx,
                            const ROOT::VecOps::RVec<int> &xidx) {
  if (!validPairIndices(zidx, pt, eta, phi, pdgId) ||
      !validPairIndices(xidx, pt, eta, phi, pdgId))
    return -999.0f;
  if (zidx[0] == xidx[0] || zidx[0] == xidx[1] || zidx[1] == xidx[0] ||
      zidx[1] == xidx[1])
    return -999.0f;
  ROOT::Math::PtEtaPhiMVector vz1(pt[zidx[0]], eta[zidx[0]], phi[zidx[0]],
                                  lepMass(pdgId[zidx[0]]));
  ROOT::Math::PtEtaPhiMVector vz2(pt[zidx[1]], eta[zidx[1]], phi[zidx[1]],
                                  lepMass(pdgId[zidx[1]]));
  ROOT::Math::PtEtaPhiMVector vx1(pt[xidx[0]], eta[xidx[0]], phi[xidx[0]],
                                  lepMass(pdgId[xidx[0]]));
  ROOT::Math::PtEtaPhiMVector vx2(pt[xidx[1]], eta[xidx[1]], phi[xidx[1]],
                                  lepMass(pdgId[xidx[1]]));
  return (vz1 + vz2 + vx1 + vx2).Pt();
}
float fourLeptonPhiFromPairs(const ROOT::VecOps::RVec<float> &pt,
                             const ROOT::VecOps::RVec<float> &eta,
                             const ROOT::VecOps::RVec<float> &phi,
                             const ROOT::VecOps::RVec<int> &pdgId,
                             const ROOT::VecOps::RVec<int> &zidx,
                             const ROOT::VecOps::RVec<int> &xidx) {
  if (!validPairIndices(zidx, pt, eta, phi, pdgId) ||
      !validPairIndices(xidx, pt, eta, phi, pdgId))
    return -999.0f;
  if (zidx[0] == xidx[0] || zidx[0] == xidx[1] || zidx[1] == xidx[0] ||
      zidx[1] == xidx[1])
    return -999.0f;
  ROOT::Math::PtEtaPhiMVector vz1(pt[zidx[0]], eta[zidx[0]], phi[zidx[0]],
                                  lepMass(pdgId[zidx[0]]));
  ROOT::Math::PtEtaPhiMVector vz2(pt[zidx[1]], eta[zidx[1]], phi[zidx[1]],
                                  lepMass(pdgId[zidx[1]]));
  ROOT::Math::PtEtaPhiMVector vx1(pt[xidx[0]], eta[xidx[0]], phi[xidx[0]],
                                  lepMass(pdgId[xidx[0]]));
  ROOT::Math::PtEtaPhiMVector vx2(pt[xidx[1]], eta[xidx[1]], phi[xidx[1]],
                                  lepMass(pdgId[xidx[1]]));
  return (vz1 + vz2 + vx1 + vx2).Phi();
}
float leptonPhiAtIdx(const ROOT::VecOps::RVec<float> &phi, int idx) {
  if (idx < 0 || static_cast<size_t>(idx) >= phi.size())
    return -999.0f;
  return phi[idx];
}
float deltaPhi(float phi1, float phi2) {
  if (phi1 <= -998.0f || phi2 <= -998.0f)
    return -999.0f;
  return std::abs(std::atan2(std::sin(phi1 - phi2), std::cos(phi1 - phi2)));
}
float recoilUx(float pT4l, float phi4l, float metPt, float metPhi) {
  return -(pT4l * std::cos(phi4l) + metPt * std::cos(metPhi));
}
float recoilUy(float pT4l, float phi4l, float metPt, float metPhi) {
  return -(pT4l * std::sin(phi4l) + metPt * std::sin(metPhi));
}
float recoilUt(float pT4l, float phi4l, float metPt, float metPhi) {
  const float ux = recoilUx(pT4l, phi4l, metPt, metPhi);
  const float uy = recoilUy(pT4l, phi4l, metPt, metPhi);
  return std::hypot(ux, uy);
}
float recoilUpar(float pT4l, float phi4l, float metPt, float metPhi) {
  if (pT4l <= 1.0e-6f)
    return -999.0f;
  const float nx = std::cos(phi4l);
  const float ny = std::sin(phi4l);
  const float ux = recoilUx(pT4l, phi4l, metPt, metPhi);
  const float uy = recoilUy(pT4l, phi4l, metPt, metPhi);
  return ux * nx + uy * ny;
}
float recoilUperp(float pT4l, float phi4l, float metPt, float metPhi) {
  if (pT4l <= 1.0e-6f)
    return -999.0f;
  const float nx = std::cos(phi4l);
  const float ny = std::sin(phi4l);
  const float ux = recoilUx(pT4l, phi4l, metPt, metPhi);
  const float uy = recoilUy(pT4l, phi4l, metPt, metPhi);
  return ux * (-ny) + uy * nx;
}
int sumLeptonChargeFromPairs(const ROOT::VecOps::RVec<int> &pdgId,
                             const ROOT::VecOps::RVec<int> &zidx,
                             const ROOT::VecOps::RVec<int> &xidx) {
  if (zidx.size() < 2 || xidx.size() < 2)
    return -999;
  ROOT::VecOps::RVec<int> idx = {zidx[0], zidx[1], xidx[0], xidx[1]};
  int chargeSum = 0;
  for (int i : idx) {
    if (i < 0 || static_cast<size_t>(i) >= pdgId.size())
      return -999;
    if (pdgId[i] == 0)
      continue;
    chargeSum += (pdgId[i] < 0) ? 1 : -1;
  }
  return chargeSum;
}
ROOT::VecOps::RVec<int>
genPdgIdFromIdx(const ROOT::VecOps::RVec<int> &genIdx,
                const ROOT::VecOps::RVec<int> &genPdgId) {
  ROOT::VecOps::RVec<int> out(genIdx.size(), 0);
  for (size_t i = 0; i < genIdx.size(); ++i) {
    int idx = genIdx[i];
    if (idx >= 0 && static_cast<size_t>(idx) < genPdgId.size()) {
      out[i] = genPdgId[idx];
    }
  }
  return out;
}
ROOT::VecOps::RVec<float>
genFloatFromIdx(const ROOT::VecOps::RVec<int> &genIdx,
                const ROOT::VecOps::RVec<float> &genValues) {
  ROOT::VecOps::RVec<float> out(genIdx.size(), 0.0f);
  for (size_t i = 0; i < genIdx.size(); ++i) {
    int idx = genIdx[i];
    if (idx >= 0 && static_cast<size_t>(idx) < genValues.size()) {
      out[i] = genValues[idx];
    }
  }
  return out;
}
ROOT::VecOps::RVec<int>
leptonGenPartIdx(const ROOT::VecOps::RVec<int> &leptonPdgId,
                 const ROOT::VecOps::RVec<int> &leptonElectronIdx,
                 const ROOT::VecOps::RVec<int> &leptonMuonIdx,
                 const ROOT::VecOps::RVec<int> &electronGenPartIdx,
                 const ROOT::VecOps::RVec<int> &muonGenPartIdx) {
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
} // namespace ZH4lMETZZCR
#endif
