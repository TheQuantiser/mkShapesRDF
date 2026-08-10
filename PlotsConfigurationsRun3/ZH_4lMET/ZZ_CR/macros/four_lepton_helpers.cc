#ifndef FOUR_LEPTON_HELPERS
#define FOUR_LEPTON_HELPERS

#include <Math/Vector4D.h>
#include <ROOT/RVec.hxx>
#include "correction.h"

#include <algorithm>
#include <cmath>
#include <cstdint>
#include <limits>
#include <map>
#include <memory>
#include <mutex>
#include <string>
#include <utility>
#include <vector>

namespace FourLepton {

ROOT::VecOps::RVec<float> productionAlignedPt(
    const ROOT::VecOps::RVec<float> &finalEta,
    const ROOT::VecOps::RVec<float> &finalPhi,
    const ROOT::VecOps::RVec<int> &finalPdgId,
    const ROOT::VecOps::RVec<float> &sourcePt,
    const ROOT::VecOps::RVec<float> &sourceEta,
    const ROOT::VecOps::RVec<float> &sourcePhi,
    const ROOT::VecOps::RVec<int> &sourcePdgId) {
  // TrigMaker and l2tight run before LeptonScaleSmearing.  The latter resorts
  // every Lepton_* vector, while VetoLepton_* preserves the earlier object
  // kinematics and order.  Match immutable flavor/eta/phi coordinates to
  // recover the exact pre-scale pT aligned to the final selected collection.
  const size_t nFinal = std::min({finalEta.size(), finalPhi.size(),
                                  finalPdgId.size()});
  const size_t nSource = std::min({sourcePt.size(), sourceEta.size(),
                                   sourcePhi.size(), sourcePdgId.size()});
  ROOT::VecOps::RVec<float> out(nFinal,
                                std::numeric_limits<float>::quiet_NaN());
  std::vector<bool> used(nSource, false);
  constexpr float maxDeltaR2 = 1.e-8f;
  for (size_t i = 0; i < nFinal; ++i) {
    int best = -1;
    float bestDeltaR2 = maxDeltaR2;
    for (size_t j = 0; j < nSource; ++j) {
      // LeptonScaleSmearing has historical files in which integer Lepton_*
      // vectors did not follow a pT-order swap while eta/phi did.  Match on
      // the unchanged floating-point coordinates and recover both pT and ID
      // from the coherent pre-scale VetoLepton collection.
      if (used[j])
        continue;
      const float dEta = finalEta[i] - sourceEta[j];
      const float dPhi = ROOT::VecOps::DeltaPhi(finalPhi[i], sourcePhi[j]);
      const float deltaR2 = dEta * dEta + dPhi * dPhi;
      if (std::isfinite(deltaR2) && deltaR2 <= bestDeltaR2) {
        best = static_cast<int>(j);
        bestDeltaR2 = deltaR2;
      }
    }
    if (best < 0 || !std::isfinite(sourcePt[best]) || sourcePt[best] <= 0.f)
      return ROOT::VecOps::RVec<float>();
    used[best] = true;
    out[i] = sourcePt[best];
  }
  return out;
}

ROOT::VecOps::RVec<int> productionAlignedPdgId(
    const ROOT::VecOps::RVec<float> &finalEta,
    const ROOT::VecOps::RVec<float> &finalPhi,
    const ROOT::VecOps::RVec<float> &sourceEta,
    const ROOT::VecOps::RVec<float> &sourcePhi,
    const ROOT::VecOps::RVec<int> &sourcePdgId) {
  const size_t nFinal = std::min(finalEta.size(), finalPhi.size());
  const size_t nSource = std::min({sourceEta.size(), sourcePhi.size(),
                                   sourcePdgId.size()});
  ROOT::VecOps::RVec<int> out(nFinal, 0);
  std::vector<bool> used(nSource, false);
  constexpr float maxDeltaR2 = 1.e-8f;
  for (size_t i = 0; i < nFinal; ++i) {
    int best = -1;
    float bestDeltaR2 = maxDeltaR2;
    for (size_t j = 0; j < nSource; ++j) {
      if (used[j])
        continue;
      const float dEta = finalEta[i] - sourceEta[j];
      const float dPhi = ROOT::VecOps::DeltaPhi(finalPhi[i], sourcePhi[j]);
      const float deltaR2 = dEta * dEta + dPhi * dPhi;
      if (std::isfinite(deltaR2) && deltaR2 <= bestDeltaR2) {
        best = static_cast<int>(j);
        bestDeltaR2 = deltaR2;
      }
    }
    if (best < 0 || (std::abs(sourcePdgId[best]) != 11 &&
                     std::abs(sourcePdgId[best]) != 13))
      return ROOT::VecOps::RVec<int>();
    used[best] = true;
    out[i] = sourcePdgId[best];
  }
  return out;
}

template <typename T>
bool sameMultiset(const ROOT::VecOps::RVec<T> &left,
                  const ROOT::VecOps::RVec<T> &right,
                  double tolerance = 0.) {
  if (left.size() != right.size())
    return false;
  std::vector<bool> used(right.size(), false);
  for (const auto &value : left) {
    int match = -1;
    for (size_t j = 0; j < right.size(); ++j) {
      if (!used[j] && std::abs(static_cast<double>(value) -
                               static_cast<double>(right[j])) <= tolerance) {
        match = static_cast<int>(j);
        break;
      }
    }
    if (match < 0)
      return false;
    used[match] = true;
  }
  return true;
}

ROOT::VecOps::RVec<int> selectedProductionSourceIndices(
    const ROOT::VecOps::RVec<float> &finalEta,
    const ROOT::VecOps::RVec<float> &finalPhi,
    const ROOT::VecOps::RVec<int> &finalPdgId,
    const ROOT::VecOps::RVec<float> &sourceEta,
    const ROOT::VecOps::RVec<float> &sourcePhi,
    const ROOT::VecOps::RVec<int> &sourcePdgId) {
  // Some historical LeptonScale outputs independently permuted integer,
  // eta, and phi vectors when the scale correction changed pT ordering.
  // Their multisets remain intact.  Select the coherent source objects by
  // eta membership, then validate the independent phi and PDG-ID multisets.
  if (finalEta.size() != finalPhi.size() || finalEta.size() != finalPdgId.size())
    return {};
  std::vector<bool> selected(sourceEta.size(), false);
  for (const float eta : finalEta) {
    int best = -1;
    float bestDelta = 1.e-4f;
    for (size_t j = 0; j < sourceEta.size(); ++j) {
      const float delta = std::abs(eta - sourceEta[j]);
      if (!selected[j] && std::isfinite(delta) && delta <= bestDelta) {
        best = static_cast<int>(j);
        bestDelta = delta;
      }
    }
    if (best < 0)
      return {};
    selected[best] = true;
  }
  ROOT::VecOps::RVec<int> indices;
  ROOT::VecOps::RVec<float> selectedPhi;
  ROOT::VecOps::RVec<int> selectedPdgId;
  for (size_t j = 0; j < selected.size(); ++j) {
    if (!selected[j])
      continue;
    if (j >= sourcePhi.size() || j >= sourcePdgId.size())
      return {};
    indices.push_back(static_cast<int>(j));
    selectedPhi.push_back(sourcePhi[j]);
    selectedPdgId.push_back(sourcePdgId[j]);
  }
  if (!sameMultiset(finalPhi, selectedPhi, 1.e-4) ||
      !sameMultiset(finalPdgId, selectedPdgId))
    return {};
  return indices;
}

ROOT::VecOps::RVec<int> descendingPtIndices(
    const ROOT::VecOps::RVec<float> &pt, int count) {
  ROOT::VecOps::RVec<int> out;
  if (count < 0 || pt.size() < static_cast<size_t>(count))
    return out;
  std::vector<std::pair<float, int>> ranked;
  ranked.reserve(pt.size());
  for (size_t i = 0; i < pt.size(); ++i) {
    if (!std::isfinite(pt[i]) || pt[i] <= 0.f)
      return ROOT::VecOps::RVec<int>();
    ranked.emplace_back(pt[i], static_cast<int>(i));
  }
  std::stable_sort(ranked.begin(), ranked.end(),
                   [](const auto &lhs, const auto &rhs) {
                     return lhs.first > rhs.first;
                   });
  for (int i = 0; i < count; ++i)
    out.push_back(ranked[i].second);
  return out;
}

int productionGateIndex(const ROOT::VecOps::RVec<float> &productionPt,
                        int rank) {
  const auto indices = descendingPtIndices(productionPt, rank + 1);
  return rank >= 0 && indices.size() > static_cast<size_t>(rank)
             ? indices[rank]
             : -1;
}

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

bool bVetoDeepFlavBAtPt(const ROOT::VecOps::RVec<float> &cleanJetPt,
                        const ROOT::VecOps::RVec<float> &cleanJetEta,
                        const ROOT::VecOps::RVec<int> &cleanJetJetIdx,
                        const ROOT::VecOps::RVec<float> &jetBtagDeepFlavB,
                        float btagVetoWP,
                        float jetPtMin) {
  const size_t n = std::min<size_t>(
      cleanJetPt.size(),
      std::min<size_t>(cleanJetEta.size(), cleanJetJetIdx.size()));
  for (size_t i = 0; i < n; ++i) {
    if (cleanJetPt[i] <= jetPtMin || std::abs(cleanJetEta[i]) >= 2.5f)
      continue;
    const int jetIdx = cleanJetJetIdx[i];
    if (jetIdx < 0 || static_cast<size_t>(jetIdx) >= jetBtagDeepFlavB.size())
      continue;
    if (jetBtagDeepFlavB[jetIdx] > btagVetoWP)
      return false;
  }
  return true;
}

bool bVetoDeepFlavB(const ROOT::VecOps::RVec<float> &cleanJetPt,
                    const ROOT::VecOps::RVec<float> &cleanJetEta,
                    const ROOT::VecOps::RVec<int> &cleanJetJetIdx,
                    const ROOT::VecOps::RVec<float> &jetBtagDeepFlavB,
                    float btagVetoWP) {
  return bVetoDeepFlavBAtPt(cleanJetPt, cleanJetEta, cleanJetJetIdx,
                            jetBtagDeepFlavB, btagVetoWP, 30.f);
}

float btagVetoShapeSF(const ROOT::VecOps::RVec<float> &cleanJetPt,
                      const ROOT::VecOps::RVec<float> &cleanJetEta,
                      const ROOT::VecOps::RVec<int> &cleanJetJetIdx,
                      const ROOT::VecOps::RVec<int> &jetHadronFlavour,
                      const ROOT::VecOps::RVec<float> &jetBtagDeepFlavB,
                      const std::string &jsonPath,
                      const std::string &systematic) {
  // This is the established Run-3 shape-SF event product used by the
  // reference HWW configurations.  A fixed-WP SF needs an efficiency map;
  // the local four-lepton contract intentionally uses the available DeepFlavB
  // shape payload instead of borrowing a legacy working point.
  using Set = correction::CorrectionSet;
  static std::map<std::string, std::shared_ptr<Set>> sets;
  static std::mutex setsMutex;
  std::shared_ptr<Set> set;
  {
    std::lock_guard<std::mutex> lock(setsMutex);
    auto found = sets.find(jsonPath);
    if (found == sets.end()) {
      std::unique_ptr<Set> loaded = Set::from_file(jsonPath);
      set = std::shared_ptr<Set>(loaded.release());
      sets.emplace(jsonPath, set);
    } else {
      set = found->second;
    }
  }
  if (!set)
    return 1.0f;
  auto correction = set->at("deepJet_shape");
  const size_t n = std::min<size_t>(
      cleanJetPt.size(),
      std::min<size_t>(cleanJetEta.size(), cleanJetJetIdx.size()));
  float product = 1.0f;
  for (size_t i = 0; i < n; ++i) {
    if (cleanJetPt[i] < 20.0001f || std::abs(cleanJetEta[i]) > 2.49999f)
      continue;
    const int jetIdx = cleanJetJetIdx[i];
    if (jetIdx < 0 || static_cast<size_t>(jetIdx) >= jetHadronFlavour.size() ||
        static_cast<size_t>(jetIdx) >= jetBtagDeepFlavB.size())
      continue;
    const float discr = jetBtagDeepFlavB[jetIdx];
    if (!std::isfinite(discr) || discr < 0.f || discr > 19.999f)
      continue;
    const int rawFlavour = std::abs(jetHadronFlavour[jetIdx]);
    const int flavour = rawFlavour == 5 ? 5 : (rawFlavour == 4 ? 4 : 0);
    // Match the core producer's flavour applicability rules for the shape
    // payload: cferr is charm-only, while hf/lf are not evaluated on charm.
    if (systematic.find("cferr") != std::string::npos && flavour != 4)
      continue;
    if ((systematic.find("hf") != std::string::npos ||
         systematic.find("lf") != std::string::npos) && flavour == 4)
      continue;
    product *= static_cast<float>(correction->evaluate(
        {systematic, flavour, std::abs(cleanJetEta[i]), cleanJetPt[i], discr}));
  }
  return product;
}

bool fifthLeptonVeto(const ROOT::VecOps::RVec<float> &leptonPt,
                     float vetoPt) {
  int nAbove = 0;
  for (float pt : leptonPt) {
    // The legacy requirement is Alt$(Lepton_pt[4],0) < 10: a fifth lepton
    // exactly on the threshold must therefore fail.
    if (pt >= vetoPt)
      ++nAbove;
  }
  return nAbove <= 4;
}

ROOT::VecOps::RVec<float> unitFloatVec(size_t n) {
  return ROOT::VecOps::RVec<float>(n, 1.0f);
}

float sfValue(const ROOT::VecOps::RVec<float> &electronSF,
              const ROOT::VecOps::RVec<float> &muonSF,
              const ROOT::VecOps::RVec<int> &pdgId,
              int idx) {
  if (idx < 0 || static_cast<size_t>(idx) >= pdgId.size())
    return 1.0f;
  const int absId = std::abs(pdgId[idx]);
  if (absId == 11)
    return valueAtFloat(electronSF, idx, 1.0f);
  if (absId == 13)
    return valueAtFloat(muonSF, idx, 1.0f);
  return 1.0f;
}

float selectedLeptonSFProduct(const ROOT::VecOps::RVec<int> &pdgId,
                              const ROOT::VecOps::RVec<int> &pairIdx,
                              const ROOT::VecOps::RVec<float> &electronSF,
                              const ROOT::VecOps::RVec<float> &muonSF,
                              int) {
  if (pairIdx.size() < 2)
    return 1.0f;
  return sfValue(electronSF, muonSF, pdgId, pairIdx[0]) *
         sfValue(electronSF, muonSF, pdgId, pairIdx[1]);
}

float selectedLeptonSFProduct4(const ROOT::VecOps::RVec<int> &pdgId,
                               const ROOT::VecOps::RVec<int> &zidx,
                               const ROOT::VecOps::RVec<int> &xidx,
                               const ROOT::VecOps::RVec<float> &electronSF,
                               const ROOT::VecOps::RVec<float> &muonSF) {
  if (zidx.size() < 2 || xidx.size() < 2)
    return 1.0f;
  return sfValue(electronSF, muonSF, pdgId, zidx[0]) *
         sfValue(electronSF, muonSF, pdgId, zidx[1]) *
         sfValue(electronSF, muonSF, pdgId, xidx[0]) *
         sfValue(electronSF, muonSF, pdgId, xidx[1]);
}

float selectedLeptonSFProductFlavor(const ROOT::VecOps::RVec<int> &pdgId,
                                    const ROOT::VecOps::RVec<int> &pairIdx,
                                    const ROOT::VecOps::RVec<float> &electronSF,
                                    const ROOT::VecOps::RVec<float> &muonSF,
                                    int variedFlavor) {
  if (pairIdx.size() < 2)
    return 1.0f;
  float product = 1.0f;
  for (size_t i = 0; i < 2; ++i) {
    const int idx = pairIdx[i];
    const int absId = (idx >= 0 && static_cast<size_t>(idx) < pdgId.size())
                          ? std::abs(pdgId[idx])
                          : 0;
    const auto &sf = (absId == 11) ? electronSF : muonSF;
    product *= (absId == variedFlavor) ? valueAtFloat(sf, idx, 1.0f)
                                       : sfValue(electronSF, muonSF, pdgId, idx);
  }
  return product;
}

float selectedLeptonSFProductFlavor4(const ROOT::VecOps::RVec<int> &pdgId,
                                     const ROOT::VecOps::RVec<int> &zidx,
                                     const ROOT::VecOps::RVec<int> &xidx,
                                     const ROOT::VecOps::RVec<float> &electronSF,
                                     const ROOT::VecOps::RVec<float> &muonSF,
                                     int variedFlavor) {
  if (zidx.size() < 2 || xidx.size() < 2)
    return 1.0f;
  ROOT::VecOps::RVec<int> idx = {zidx[0], zidx[1], xidx[0], xidx[1]};
  float product = 1.0f;
  for (const int i : idx) {
    const int absId = (i >= 0 && static_cast<size_t>(i) < pdgId.size())
                          ? std::abs(pdgId[i])
                          : 0;
    const auto &sf = (absId == 11) ? electronSF : muonSF;
    product *= (absId == variedFlavor) ? valueAtFloat(sf, i, 1.0f)
                                       : sfValue(electronSF, muonSF, pdgId, i);
  }
  return product;
}

bool fourSelectedIndicesDistinct(const ROOT::VecOps::RVec<int> &zidx,
                                 const ROOT::VecOps::RVec<int> &xidx,
                                 size_t nLepton) {
  if (zidx.size() < 2 || xidx.size() < 2)
    return false;
  ROOT::VecOps::RVec<int> idx = {zidx[0], zidx[1], xidx[0], xidx[1]};
  for (const int i : idx) {
    if (i < 0 || static_cast<size_t>(i) >= nLepton)
      return false;
  }
  for (size_t i = 0; i < idx.size(); ++i)
    for (size_t j = i + 1; j < idx.size(); ++j)
      if (idx[i] == idx[j])
        return false;
  return true;
}

bool selectedPairIsLeading(const ROOT::VecOps::RVec<int> &idx) {
  return idx.size() >= 2 && idx[0] == 0 && idx[1] == 1;
}

bool selectedPairsAreLeading(const ROOT::VecOps::RVec<int> &zidx,
                             const ROOT::VecOps::RVec<int> &xidx) {
  if (zidx.size() < 2 || xidx.size() < 2)
    return false;
  return zidx[0] == 0 && zidx[1] == 1 && xidx[0] == 2 && xidx[1] == 3;
}

float selectedTriggerWeight2(const ROOT::VecOps::RVec<int> &idx,
                             float canonicalEventWeight) {
  // TriggerMaker stores an event-level 2-lepton correction, not a tensor
  // indexed by every possible selected pair.  Apply that canonical event
  // correction to every valid selected pair; never turn a valid non-leading
  // selection into unity.  The leading-pair equality is the regression
  // contract, while TriggerSF_Z_Valid remains the coverage diagnostic.
  return (idx.size() >= 2 && idx[0] >= 0 && idx[1] >= 0)
             ? canonicalEventWeight
             : 1.0f;
}

float selectedTriggerWeight4(const ROOT::VecOps::RVec<int> &zidx,
                             const ROOT::VecOps::RVec<int> &xidx,
                             float canonicalEventWeight) {
  // See selectedTriggerWeight2.  The stored 4-lepton TrigMaker correction is
  // the canonical event payload and is applied to any valid selected Z+X
  // index set, including selected sets that are not [0,1,2,3].
  return (zidx.size() >= 2 && xidx.size() >= 2 && zidx[0] >= 0 &&
          zidx[1] >= 0 && xidx[0] >= 0 && xidx[1] >= 0)
             ? canonicalEventWeight
             : 1.0f;
}

float lepMass(int pdgId) {
  return (std::abs(pdgId) == 11) ? 0.000511f : 0.105658f;
}

float minimumSelectedPairMass(
    const ROOT::VecOps::RVec<float> &pt,
    const ROOT::VecOps::RVec<float> &eta,
    const ROOT::VecOps::RVec<float> &phi,
    const ROOT::VecOps::RVec<int> &pdgId,
    const ROOT::VecOps::RVec<int> &zidx,
    const ROOT::VecOps::RVec<int> &xidx) {
  // The physical four-lepton veto is defined on exactly the selected Z0+X
  // objects, not on arbitrary additional event leptons.  Return a negative
  // sentinel for every malformed input so ``minSelectedPairMass > 12`` fails
  // closed in the ZZCR/SR common selection.
  const size_t nKinematics =
      std::min({pt.size(), eta.size(), phi.size(), pdgId.size()});
  if (!fourSelectedIndicesDistinct(zidx, xidx, nKinematics))
    return -1.f;

  const ROOT::VecOps::RVec<int> indices = {
      zidx[0], zidx[1], xidx[0], xidx[1]};
  std::vector<ROOT::Math::PtEtaPhiMVector> leptons;
  leptons.reserve(indices.size());
  for (const int index : indices) {
    const int absPdgId = std::abs(pdgId[index]);
    if ((absPdgId != 11 && absPdgId != 13) ||
        !std::isfinite(pt[index]) || pt[index] <= 0.f ||
        !std::isfinite(eta[index]) || !std::isfinite(phi[index]))
      return -1.f;
    leptons.emplace_back(
        pt[index], eta[index], phi[index], lepMass(pdgId[index]));
  }

  float minimumMass = std::numeric_limits<float>::infinity();
  for (size_t first = 0; first < leptons.size(); ++first) {
    for (size_t second = first + 1; second < leptons.size(); ++second) {
      const float mass = static_cast<float>((leptons[first] + leptons[second]).M());
      if (!std::isfinite(mass) || mass < 0.f)
        return -1.f;
      minimumMass = std::min(minimumMass, mass);
    }
  }
  return std::isfinite(minimumMass) ? minimumMass : -1.f;
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

bool passesOrdered2lPtThresholdsFromPair(
    const ROOT::VecOps::RVec<float> &pt,
    const ROOT::VecOps::RVec<int> &idx,
    float pt1Min,
    float pt2Min) {
  if (idx.size() < 2 || idx[0] == idx[1])
    return false;
  if (idx[0] < 0 || idx[1] < 0 ||
      static_cast<size_t>(idx[0]) >= pt.size() ||
      static_cast<size_t>(idx[1]) >= pt.size())
    return false;

  ROOT::VecOps::RVec<float> lepPt = {pt[idx[0]], pt[idx[1]]};
  ROOT::VecOps::RVec<float> sortedPt =
      ROOT::VecOps::Reverse(ROOT::VecOps::Sort(lepPt));

  return sortedPt[0] > clampPtMin(pt1Min) &&
         sortedPt[1] > clampPtMin(pt2Min);
}

bool passesOrdered4lPtThresholdsFromPairs(
    const ROOT::VecOps::RVec<float> &pt,
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

  return sortedPt[0] > min1 && sortedPt[1] > min2 && sortedPt[2] > min3 &&
         sortedPt[3] > min4;
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

}  // namespace FourLepton

// Histogram expressions are split on ':' by the stock runner, so expose a
// concise global wrapper whose call does not require a C++ namespace token.
ROOT::VecOps::RVec<float> maskedHistogramValue(float value, bool applicable) {
  if (!applicable)
    return {};
  return {value};
}

#endif
