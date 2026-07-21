#ifndef ZH4LMET_ZZCR_HELPERS
#define ZH4LMET_ZZCR_HELPERS

#include <Math/Vector4D.h>
#include <ROOT/RVec.hxx>

#include <algorithm>
#include <cmath>
#include <cstdint>

namespace ZH4lMETZZCR {

float zeroFloat() {
  return 0.0f;
}

ROOT::VecOps::RVec<int> emptyIntVec() {
  return ROOT::VecOps::RVec<int>();
}

ROOT::VecOps::RVec<float> emptyFloatVec() {
  return ROOT::VecOps::RVec<float>();
}

template <typename T>
float valueAtFloat(const ROOT::VecOps::RVec<T> &values, int idx, float defaultValue) {
  if (idx < 0 || static_cast<size_t>(idx) >= values.size())
    return defaultValue;
  return static_cast<float>(values[idx]);
}

template <typename T>
int valueAtInt(const ROOT::VecOps::RVec<T> &values, int idx, int defaultValue) {
  if (idx < 0 || static_cast<size_t>(idx) >= values.size())
    return defaultValue;
  return static_cast<int>(values[idx]);
}

template <typename T>
unsigned long long valueAtULL(const ROOT::VecOps::RVec<T> &values,
                              int idx,
                              unsigned long long defaultValue) {
  if (idx < 0 || static_cast<size_t>(idx) >= values.size())
    return defaultValue;
  return static_cast<unsigned long long>(values[idx]);
}

template <typename TrigObjIdT>
ROOT::VecOps::RVec<int> createTrigIndexTnP(
    const ROOT::VecOps::RVec<float> &leptonEta,
    const ROOT::VecOps::RVec<float> &leptonPhi,
    const ROOT::VecOps::RVec<int> &leptonPdgId,
    const ROOT::VecOps::RVec<float> &trigObjEta,
    const ROOT::VecOps::RVec<float> &trigObjPhi,
    const ROOT::VecOps::RVec<TrigObjIdT> &trigObjId,
    float minDR = 0.1f) {
  // TnP-style nearest matching with flavor guard and robust bounds.
  const size_t nLepton = std::min({leptonEta.size(), leptonPhi.size(), leptonPdgId.size()});
  const size_t nTrigObj = std::min({trigObjEta.size(), trigObjPhi.size(), trigObjId.size()});
  // Output aligned to Lepton_* indexing; -1 means "no matched TrigObj".
  ROOT::VecOps::RVec<int> leptonTrigIdx(leptonPdgId.size(), -1);
  for (size_t iLep = 0; iLep < nLepton; ++iLep) {
    float bestDR = minDR;
    const int recoAbsPdgId = std::abs(leptonPdgId[iLep]);
    if (recoAbsPdgId != 11 && recoAbsPdgId != 13)
      continue;
    for (size_t iTr = 0; iTr < nTrigObj; ++iTr) {
      if (recoAbsPdgId != std::abs(static_cast<int>(trigObjId[iTr])))
        continue;
      const float deta = leptonEta[iLep] - trigObjEta[iTr];
      const float dphi = ROOT::VecOps::DeltaPhi(leptonPhi[iLep], trigObjPhi[iTr]);
      const float dR = std::sqrt(deta * deta + dphi * dphi);
      if (dR < bestDR) {
        bestDR = dR;
        leptonTrigIdx[iLep] = static_cast<int>(iTr);
      }
    }
  }
  return leptonTrigIdx;
}

template <typename TrigObjIdT>
ROOT::VecOps::RVec<float> createTrigMatchDRTnP(
    const ROOT::VecOps::RVec<float> &leptonEta,
    const ROOT::VecOps::RVec<float> &leptonPhi,
    const ROOT::VecOps::RVec<int> &leptonPdgId,
    const ROOT::VecOps::RVec<float> &trigObjEta,
    const ROOT::VecOps::RVec<float> &trigObjPhi,
    const ROOT::VecOps::RVec<TrigObjIdT> &trigObjId,
    float minDR = 0.1f) {
  const size_t nLepton = std::min({leptonEta.size(), leptonPhi.size(), leptonPdgId.size()});
  const size_t nTrigObj = std::min({trigObjEta.size(), trigObjPhi.size(), trigObjId.size()});
  ROOT::VecOps::RVec<float> bestDRs(leptonPdgId.size(), -999.0f);
  for (size_t iLep = 0; iLep < nLepton; ++iLep) {
    float bestDR = minDR;
    const int recoAbsPdgId = std::abs(leptonPdgId[iLep]);
    if (recoAbsPdgId != 11 && recoAbsPdgId != 13)
      continue;
    for (size_t iTr = 0; iTr < nTrigObj; ++iTr) {
      if (recoAbsPdgId != std::abs(static_cast<int>(trigObjId[iTr])))
        continue;
      const float deta = leptonEta[iLep] - trigObjEta[iTr];
      const float dphi = ROOT::VecOps::DeltaPhi(leptonPhi[iLep], trigObjPhi[iTr]);
      const float dR = std::sqrt(deta * deta + dphi * dphi);
      if (dR < bestDR) {
        bestDR = dR;
        bestDRs[iLep] = dR;
      }
    }
  }
  return bestDRs;
}

template <typename TrigObjIdT>
ROOT::VecOps::RVec<int> countTrigMatchesTnP(
    const ROOT::VecOps::RVec<float> &leptonEta,
    const ROOT::VecOps::RVec<float> &leptonPhi,
    const ROOT::VecOps::RVec<int> &leptonPdgId,
    const ROOT::VecOps::RVec<float> &trigObjEta,
    const ROOT::VecOps::RVec<float> &trigObjPhi,
    const ROOT::VecOps::RVec<TrigObjIdT> &trigObjId,
    float minDR = 0.1f) {
  const size_t nLepton = std::min({leptonEta.size(), leptonPhi.size(), leptonPdgId.size()});
  const size_t nTrigObj = std::min({trigObjEta.size(), trigObjPhi.size(), trigObjId.size()});
  ROOT::VecOps::RVec<int> counts(leptonPdgId.size(), 0);
  for (size_t iLep = 0; iLep < nLepton; ++iLep) {
    const int recoAbsPdgId = std::abs(leptonPdgId[iLep]);
    if (recoAbsPdgId != 11 && recoAbsPdgId != 13)
      continue;
    for (size_t iTr = 0; iTr < nTrigObj; ++iTr) {
      if (recoAbsPdgId != std::abs(static_cast<int>(trigObjId[iTr])))
        continue;
      const float deta = leptonEta[iLep] - trigObjEta[iTr];
      const float dphi = ROOT::VecOps::DeltaPhi(leptonPhi[iLep], trigObjPhi[iTr]);
      const float dR = std::sqrt(deta * deta + dphi * dphi);
      if (dR < minDR)
        ++counts[iLep];
    }
  }
  return counts;
}

ROOT::VecOps::RVec<int> createTrigMatchStateTnP(
    const ROOT::VecOps::RVec<int> &leptonPdgId,
    const ROOT::VecOps::RVec<int> &trigIdx,
    const ROOT::VecOps::RVec<int> &matchCount) {
  const size_t n = std::min({leptonPdgId.size(), trigIdx.size(), matchCount.size()});
  ROOT::VecOps::RVec<int> state(leptonPdgId.size(), -1);
  for (size_t i = 0; i < n; ++i) {
    const int absPdgId = std::abs(leptonPdgId[i]);
    if (absPdgId != 11 && absPdgId != 13) {
      state[i] = -1;
    } else if (matchCount[i] <= 0 || trigIdx[i] < 0) {
      state[i] = 0;
    } else if (matchCount[i] == 1) {
      state[i] = 1;
    } else {
      state[i] = 2;
    }
  }
  return state;
}

bool trigObjHasFilterBit(unsigned long long trigObjFilterBits, int bitIdx) {
  if (bitIdx < 0)
    return false;
  return ((trigObjFilterBits >> bitIdx) & 0x1ULL) != 0ULL;
}

unsigned int pack4lTrigObjBits(int leptonPdgId,
                               unsigned long long trigObjFilterBits,
                               int nanoAODVersion) {
  // Compact diagnostic mask; explicit booleans are saved separately.
  const int absPdgId = std::abs(leptonPdgId);
  auto hasBit = [&](int bitIdx) -> bool { return trigObjHasFilterBit(trigObjFilterBits, bitIdx); };
  const bool isV15 = nanoAODVersion >= 15;

  unsigned int packed = 0u;
  if (absPdgId == 11) {
    const bool eEleMu = hasBit(isV15 ? 6 : 5);
    const bool eDoubleEle = isV15 ? (hasBit(4) || hasBit(5)) : hasBit(4);
    const bool eDoubleEleLeg1 = isV15 && hasBit(4);
    const bool eDoubleEleLeg2 = isV15 && hasBit(5);
    const bool eSingleEle = isV15 ? hasBit(18) : hasBit(1);
    const bool eWPTight = hasBit(1);
    const bool eEle30 = isV15 && hasBit(18);
    // e: [0]=EleMu, [1]=DoubleEle, [2]=DoubleEleLeg1,
    //    [3]=DoubleEleLeg2, [4]=SingleEle family, [5]=Ele30 exact,
    //    [6]=1e WPTight broad bit.
    if (eEleMu)
      packed |= (1u << 0);
    if (eDoubleEle)
      packed |= (1u << 1);
    if (eDoubleEleLeg1)
      packed |= (1u << 2);
    if (eDoubleEleLeg2)
      packed |= (1u << 3);
    if (eSingleEle)
      packed |= (1u << 4);
    if (eEle30)
      packed |= (1u << 5);
    if (eWPTight)
      packed |= (1u << 6);
  } else if (absPdgId == 13) {
    // mu: [0]=EleMu, [1]=DoubleMu, [2]=SingleMu, [3]=Iso, [4]=TrkIsoVVL.
    if (hasBit(5))
      packed |= (1u << 0);
    if (hasBit(4))
      packed |= (1u << 1);
    if (hasBit(3))
      packed |= (1u << 2);
    if (hasBit(1))
      packed |= (1u << 3);
    if (hasBit(0))
      packed |= (1u << 4);
  }
  return packed;
}

unsigned int pack4lTrigObjBits(int leptonPdgId, unsigned long long trigObjFilterBits) {
  return pack4lTrigObjBits(leptonPdgId, trigObjFilterBits, 15);
}

int dataStreamPriorityCategory(bool triggerElMu,
                               bool triggerSingleMu,
                               bool triggerDoubleMu,
                               bool triggerSingleEle,
                               bool triggerDoubleEle) {
  if (triggerElMu)
    return 1;
  if (triggerSingleMu || triggerDoubleMu)
    return 2;
  if (triggerSingleEle || triggerDoubleEle)
    return 3;
  return 0;
}

int triggerFamilyPriorityCategory(bool triggerElMu,
                                  bool triggerSingleMu,
                                  bool triggerDoubleMu,
                                  bool triggerSingleEle,
                                  bool triggerDoubleEle) {
  if (triggerElMu)
    return 1;
  if (triggerSingleMu)
    return 2;
  if (triggerDoubleMu)
    return 3;
  if (triggerSingleEle)
    return 4;
  if (triggerDoubleEle)
    return 5;
  return 0;
}

int countFiredTriggerFamilies(bool triggerElMu,
                              bool triggerSingleMu,
                              bool triggerDoubleMu,
                              bool triggerSingleEle,
                              bool triggerDoubleEle) {
  return static_cast<int>(triggerElMu) + static_cast<int>(triggerSingleMu) +
         static_cast<int>(triggerDoubleMu) + static_cast<int>(triggerSingleEle) +
         static_cast<int>(triggerDoubleEle);
}

int hltPathPriorityCategory(bool mu23Ele12,
                            bool mu12Ele23,
                            bool mu8Ele23,
                            bool mu17Mu8,
                            bool isoMu24,
                            bool ele23Ele12,
                            bool ele30) {
  if (mu23Ele12)
    return 1;
  if (mu12Ele23)
    return 2;
  if (mu8Ele23)
    return 3;
  if (mu17Mu8)
    return 4;
  if (isoMu24)
    return 5;
  if (ele23Ele12)
    return 6;
  if (ele30)
    return 7;
  return 0;
}

int countFiredHLTPaths(bool mu23Ele12,
                       bool mu12Ele23,
                       bool mu8Ele23,
                       bool mu17Mu8,
                       bool isoMu24,
                       bool ele23Ele12,
                       bool ele30) {
  return static_cast<int>(mu23Ele12) + static_cast<int>(mu12Ele23) +
         static_cast<int>(mu8Ele23) + static_cast<int>(mu17Mu8) +
         static_cast<int>(isoMu24) + static_cast<int>(ele23Ele12) +
         static_cast<int>(ele30);
}

int combineTrigMatchState2(int idx0, int idx1, int state0, int state1) {
  if (idx0 < 0 || idx1 < 0 || state0 < 0 || state1 < 0)
    return -1;
  if (state0 == 2 || state1 == 2)
    return 3;
  const int nMatched = static_cast<int>(state0 == 1) + static_cast<int>(state1 == 1);
  if (nMatched == 2)
    return 2;
  if (nMatched == 1)
    return 1;
  return 0;
}

int combineTrigMatchState4(int idx0,
                           int idx1,
                           int idx2,
                           int idx3,
                           int state0,
                           int state1,
                           int state2,
                           int state3) {
  if (idx0 < 0 || idx1 < 0 || idx2 < 0 || idx3 < 0 ||
      state0 < 0 || state1 < 0 || state2 < 0 || state3 < 0)
    return -1;
  if (state0 == 2 || state1 == 2 || state2 == 2 || state3 == 2)
    return 3;
  const int nMatched = static_cast<int>(state0 == 1) + static_cast<int>(state1 == 1) +
                       static_cast<int>(state2 == 1) + static_cast<int>(state3 == 1);
  if (nMatched == 4)
    return 2;
  if (nMatched > 0)
    return 1;
  return 0;
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

float clampPtMin(float ptMin) {
  return (ptMin < 0.f) ? 0.f : ptMin;
}

bool leptonPassesPairWP(int idx,
                        const ROOT::VecOps::RVec<int> &pdgId,
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
                             float leadPtMin,
                             float subleadPtMin) {
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
                         int minPassID,
                         float leadPtMin,
                         float subleadPtMin) {
  return pairPassesIDRequirement(
             pairIdx, pdgId, passEleWP, passMuWP, minPassID) &&
         pairPassesPtRequirement(pairIdx, pt, leadPtMin, subleadPtMin);
}

ROOT::VecOps::RVec<int> bestZ0IdxWithID(
    const ROOT::VecOps::RVec<float> &pt,
    const ROOT::VecOps::RVec<float> &eta,
    const ROOT::VecOps::RVec<float> &phi,
    const ROOT::VecOps::RVec<int> &pdgId,
    const ROOT::VecOps::RVec<bool> &passEleWP,
    const ROOT::VecOps::RVec<bool> &passMuWP,
    int minPassID,
    float leadPtMin,
    float subleadPtMin) {
  ROOT::VecOps::RVec<int> out = {-1, -1};
  const float mZ = 91.1876f;
  float bestDiff = 1e9f;
  int n = std::min<int>(std::min<int>(pt.size(), eta.size()),
                        std::min<int>(phi.size(), pdgId.size()));
  for (int i = 0; i < n; ++i) {
    ROOT::Math::PtEtaPhiMVector v1(pt[i], eta[i], phi[i], lepMass(pdgId[i]));
    for (int j = i + 1; j < n; ++j) {
      if (pdgId[i] != -pdgId[j])
        continue;
      ROOT::VecOps::RVec<int> cand = {i, j};
      if (!pairPassesSelection(cand,
                               pt,
                               pdgId,
                               passEleWP,
                               passMuWP,
                               minPassID,
                               leadPtMin,
                               subleadPtMin))
        continue;
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

ROOT::VecOps::RVec<int> xPairIdxWithID(
    const ROOT::VecOps::RVec<int> &zidx,
    const ROOT::VecOps::RVec<float> &pt,
    const ROOT::VecOps::RVec<int> &pdgId,
    const ROOT::VecOps::RVec<bool> &passEleWP,
    const ROOT::VecOps::RVec<bool> &passMuWP,
    int minPassID,
    float leadPtMin,
    float subleadPtMin) {
  if (zidx.size() < 2 || zidx[0] < 0 || zidx[1] < 0 || zidx[0] == zidx[1])
    return {-1, -1};

  const int n = std::min<int>(pt.size(), pdgId.size());
  if (zidx[0] >= n || zidx[1] >= n)
    return {-1, -1};

  auto isZ = [&](int i) {
    return i == zidx[0] || i == zidx[1];
  };

  ROOT::VecOps::RVec<int> best = {-1, -1};
  float bestLeadPt = -1.f;
  float bestSubPt = -1.f;

  for (int i = 0; i < n; ++i) {
    if (isZ(i))
      continue;
    for (int j = i + 1; j < n; ++j) {
      if (isZ(j))
        continue;
      if (pdgId[i] * pdgId[j] >= 0)
        continue;

      ROOT::VecOps::RVec<int> cand =
          orderPairByPt(ROOT::VecOps::RVec<int>{i, j}, pt);

      if (!pairPassesSelection(cand,
                               pt,
                               pdgId,
                               passEleWP,
                               passMuWP,
                               minPassID,
                               leadPtMin,
                               subleadPtMin))
        continue;

      const float leadPt = pt[cand[0]];
      const float subPt = pt[cand[1]];

      if (leadPt > bestLeadPt ||
          (!(leadPt < bestLeadPt) && subPt > bestSubPt)) {
        bestLeadPt = leadPt;
        bestSubPt = subPt;
        best = cand;
      }
    }
  }

  return best;
}

bool passesOrderedPtThresholdsFromPairs(const ROOT::VecOps::RVec<float> &pt,
                                        const ROOT::VecOps::RVec<int> &zidx,
                                        const ROOT::VecOps::RVec<int> &xidx,
                                        float pt1Min,
                                        float pt2Min,
                                        float pt3Min,
                                        float pt4Min) {
  if (zidx.size() < 2 || xidx.size() < 2)
    return false;

  ROOT::VecOps::RVec<int> lepIdx = {zidx[0], zidx[1], xidx[0], xidx[1]};
  for (const int idx : lepIdx) {
    if (idx < 0 || static_cast<size_t>(idx) >= pt.size())
      return false;
  }

  // Require 4 distinct leptons.
  for (size_t i = 0; i < lepIdx.size(); ++i) {
    for (size_t j = i + 1; j < lepIdx.size(); ++j) {
      if (lepIdx[i] == lepIdx[j])
        return false;
    }
  }

  ROOT::VecOps::RVec<float> lepPt = {
      pt[lepIdx[0]], pt[lepIdx[1]], pt[lepIdx[2]], pt[lepIdx[3]]};
  ROOT::VecOps::RVec<float> sortedPt =
      ROOT::VecOps::Reverse(ROOT::VecOps::Sort(lepPt));

  const float min1 = clampPtMin(pt1Min);
  const float min2 = clampPtMin(pt2Min);
  const float min3 = clampPtMin(pt3Min);
  const float min4 = clampPtMin(pt4Min);

  return sortedPt[0] >= min1 && sortedPt[1] >= min2 && sortedPt[2] >= min3 &&
         sortedPt[3] >= min4;
}

bool validLeptonIndex(int idx,
                      const ROOT::VecOps::RVec<float> &pt,
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
  ROOT::Math::PtEtaPhiMVector v1(
      pt[idx[0]], eta[idx[0]], phi[idx[0]], lepMass(pdgId[idx[0]]));
  ROOT::Math::PtEtaPhiMVector v2(
      pt[idx[1]], eta[idx[1]], phi[idx[1]], lepMass(pdgId[idx[1]]));
  return (v1 + v2).M();
}

float pairPt(const ROOT::VecOps::RVec<float> &pt,
             const ROOT::VecOps::RVec<float> &eta,
             const ROOT::VecOps::RVec<float> &phi,
             const ROOT::VecOps::RVec<int> &pdgId,
             const ROOT::VecOps::RVec<int> &idx) {
  if (!validPairIndices(idx, pt, eta, phi, pdgId))
    return -999.0f;
  ROOT::Math::PtEtaPhiMVector v1(
      pt[idx[0]], eta[idx[0]], phi[idx[0]], lepMass(pdgId[idx[0]]));
  ROOT::Math::PtEtaPhiMVector v2(
      pt[idx[1]], eta[idx[1]], phi[idx[1]], lepMass(pdgId[idx[1]]));
  return (v1 + v2).Pt();
}

float pairPhi(const ROOT::VecOps::RVec<float> &pt,
              const ROOT::VecOps::RVec<float> &eta,
              const ROOT::VecOps::RVec<float> &phi,
              const ROOT::VecOps::RVec<int> &pdgId,
              const ROOT::VecOps::RVec<int> &idx) {
  if (!validPairIndices(idx, pt, eta, phi, pdgId))
    return -999.0f;
  ROOT::Math::PtEtaPhiMVector v1(
      pt[idx[0]], eta[idx[0]], phi[idx[0]], lepMass(pdgId[idx[0]]));
  ROOT::Math::PtEtaPhiMVector v2(
      pt[idx[1]], eta[idx[1]], phi[idx[1]], lepMass(pdgId[idx[1]]));
  return (v1 + v2).Phi();
}

float pairEta(const ROOT::VecOps::RVec<float> &pt,
              const ROOT::VecOps::RVec<float> &eta,
              const ROOT::VecOps::RVec<float> &phi,
              const ROOT::VecOps::RVec<int> &pdgId,
              const ROOT::VecOps::RVec<int> &idx) {
  if (!validPairIndices(idx, pt, eta, phi, pdgId))
    return -999.0f;
  ROOT::Math::PtEtaPhiMVector v1(
      pt[idx[0]], eta[idx[0]], phi[idx[0]], lepMass(pdgId[idx[0]]));
  ROOT::Math::PtEtaPhiMVector v2(
      pt[idx[1]], eta[idx[1]], phi[idx[1]], lepMass(pdgId[idx[1]]));
  return (v1 + v2).Eta();
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
  ROOT::Math::PtEtaPhiMVector vz1(
      pt[zidx[0]], eta[zidx[0]], phi[zidx[0]], lepMass(pdgId[zidx[0]]));
  ROOT::Math::PtEtaPhiMVector vz2(
      pt[zidx[1]], eta[zidx[1]], phi[zidx[1]], lepMass(pdgId[zidx[1]]));
  ROOT::Math::PtEtaPhiMVector vx1(
      pt[xidx[0]], eta[xidx[0]], phi[xidx[0]], lepMass(pdgId[xidx[0]]));
  ROOT::Math::PtEtaPhiMVector vx2(
      pt[xidx[1]], eta[xidx[1]], phi[xidx[1]], lepMass(pdgId[xidx[1]]));
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
  ROOT::Math::PtEtaPhiMVector vz1(
      pt[zidx[0]], eta[zidx[0]], phi[zidx[0]], lepMass(pdgId[zidx[0]]));
  ROOT::Math::PtEtaPhiMVector vz2(
      pt[zidx[1]], eta[zidx[1]], phi[zidx[1]], lepMass(pdgId[zidx[1]]));
  ROOT::Math::PtEtaPhiMVector vx1(
      pt[xidx[0]], eta[xidx[0]], phi[xidx[0]], lepMass(pdgId[xidx[0]]));
  ROOT::Math::PtEtaPhiMVector vx2(
      pt[xidx[1]], eta[xidx[1]], phi[xidx[1]], lepMass(pdgId[xidx[1]]));
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
  ROOT::Math::PtEtaPhiMVector vz1(
      pt[zidx[0]], eta[zidx[0]], phi[zidx[0]], lepMass(pdgId[zidx[0]]));
  ROOT::Math::PtEtaPhiMVector vz2(
      pt[zidx[1]], eta[zidx[1]], phi[zidx[1]], lepMass(pdgId[zidx[1]]));
  ROOT::Math::PtEtaPhiMVector vx1(
      pt[xidx[0]], eta[xidx[0]], phi[xidx[0]], lepMass(pdgId[xidx[0]]));
  ROOT::Math::PtEtaPhiMVector vx2(
      pt[xidx[1]], eta[xidx[1]], phi[xidx[1]], lepMass(pdgId[xidx[1]]));
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

float deltaEta(float eta1, float eta2) {
  if (eta1 <= -998.0f || eta2 <= -998.0f)
    return -999.0f;
  return std::abs(eta1 - eta2);
}

float deltaR(float eta1, float phi1, float eta2, float phi2) {
  const float dEta = deltaEta(eta1, eta2);
  const float dPhi = deltaPhi(phi1, phi2);
  if (dEta <= -998.0f || dPhi <= -998.0f)
    return -999.0f;
  return std::hypot(dEta, dPhi);
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

ROOT::VecOps::RVec<int> genPdgIdFromIdx(
    const ROOT::VecOps::RVec<int> &genIdx,
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

ROOT::VecOps::RVec<float> genFloatFromIdx(
    const ROOT::VecOps::RVec<int> &genIdx,
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

ROOT::VecOps::RVec<int> leptonGenPartIdx(
    const ROOT::VecOps::RVec<int> &leptonPdgId,
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

}  // namespace ZH4lMETZZCR
#endif
