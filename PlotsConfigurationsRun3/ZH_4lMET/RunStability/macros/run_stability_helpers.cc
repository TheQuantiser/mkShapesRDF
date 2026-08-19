#ifndef MKSHAPESRDF_RUN_STABILITY_HELPERS
#define MKSHAPESRDF_RUN_STABILITY_HELPERS

#include <Math/Vector4D.h>
#include <ROOT/RVec.hxx>

#include <algorithm>
#include <cmath>
#include <limits>
#include <utility>
#include <vector>

namespace RunStability {

ROOT::VecOps::RVec<float> productionAlignedPt(
    const ROOT::VecOps::RVec<float> &finalEta,
    const ROOT::VecOps::RVec<float> &finalPhi,
    const ROOT::VecOps::RVec<int> &finalPdgId,
    const ROOT::VecOps::RVec<float> &sourcePt,
    const ROOT::VecOps::RVec<float> &sourceEta,
    const ROOT::VecOps::RVec<float> &sourcePhi,
    const ROOT::VecOps::RVec<int> &sourcePdgId) {
  const size_t nFinal =
      std::min({finalEta.size(), finalPhi.size(), finalPdgId.size()});
  const size_t nSource = std::min(
      {sourcePt.size(), sourceEta.size(), sourcePhi.size(), sourcePdgId.size()});
  ROOT::VecOps::RVec<float> out(
      nFinal, std::numeric_limits<float>::quiet_NaN());
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
    if (best < 0 || !std::isfinite(sourcePt[best]) || sourcePt[best] <= 0.f)
      return {};
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
  const size_t nSource =
      std::min({sourceEta.size(), sourcePhi.size(), sourcePdgId.size()});
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
      return {};
    used[best] = true;
    out[i] = sourcePdgId[best];
  }
  return out;
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
      return {};
    ranked.emplace_back(pt[i], static_cast<int>(i));
  }
  std::stable_sort(ranked.begin(), ranked.end(),
                   [](const auto &left, const auto &right) {
                     return left.first > right.first;
                   });
  for (int index = 0; index < count; ++index)
    out.push_back(ranked[index].second);
  return out;
}

int productionGateIndex(const ROOT::VecOps::RVec<float> &productionPt,
                        int rank) {
  const auto indices = descendingPtIndices(productionPt, rank + 1);
  return rank >= 0 && indices.size() > static_cast<size_t>(rank) ? indices[rank]
                                                                 : -1;
}

int dataStreamPriorityCategory(bool triggerElMu, bool triggerSingleMu,
                               bool triggerDoubleMu, bool triggerSingleEle,
                               bool triggerDoubleEle) {
  if (triggerElMu)
    return 1;
  if (triggerSingleMu || triggerDoubleMu)
    return 2;
  if (triggerSingleEle || triggerDoubleEle)
    return 3;
  return 0;
}

ROOT::VecOps::RVec<float> unitFloatVec(size_t size) {
  return ROOT::VecOps::RVec<float>(size, 1.0f);
}

template <typename T>
float valueAtFloat(const ROOT::VecOps::RVec<T> &values, int index,
                   float fallback) {
  if (index < 0 || static_cast<size_t>(index) >= values.size())
    return fallback;
  return static_cast<float>(values[index]);
}

float selectedLeptonScaleFactor(
    const ROOT::VecOps::RVec<int> &pdgId,
    const ROOT::VecOps::RVec<float> &electronSF,
    const ROOT::VecOps::RVec<float> &muonSF, int index) {
  if (index < 0 || static_cast<size_t>(index) >= pdgId.size())
    return 1.0f;
  const int flavor = std::abs(pdgId[index]);
  if (flavor == 11)
    return valueAtFloat(electronSF, index, 1.0f);
  if (flavor == 13)
    return valueAtFloat(muonSF, index, 1.0f);
  return 1.0f;
}

float selectedLeptonSFProduct(
    const ROOT::VecOps::RVec<int> &pdgId,
    const ROOT::VecOps::RVec<int> &pairIndices,
    const ROOT::VecOps::RVec<float> &electronSF,
    const ROOT::VecOps::RVec<float> &muonSF, int) {
  if (pairIndices.size() < 2)
    return 1.0f;
  return selectedLeptonScaleFactor(pdgId, electronSF, muonSF, pairIndices[0]) *
         selectedLeptonScaleFactor(pdgId, electronSF, muonSF, pairIndices[1]);
}

float leptonMass(int pdgId) {
  const int flavor = std::abs(pdgId);
  if (flavor == 11)
    return 0.000511f;
  if (flavor == 13)
    return 0.105658f;
  return 0.0f;
}

ROOT::VecOps::RVec<int> orderPairByPt(
    const ROOT::VecOps::RVec<int> &indices,
    const ROOT::VecOps::RVec<float> &pt) {
  if (indices.size() < 2 || indices[0] < 0 || indices[1] < 0 ||
      static_cast<size_t>(indices[0]) >= pt.size() ||
      static_cast<size_t>(indices[1]) >= pt.size())
    return {-1, -1};
  return pt[indices[0]] >= pt[indices[1]]
             ? ROOT::VecOps::RVec<int>{indices[0], indices[1]}
             : ROOT::VecOps::RVec<int>{indices[1], indices[0]};
}

int clampPairMinPassID(int minimum) {
  return std::max(0, std::min(2, minimum));
}

float clampPtMin(float minimum) { return std::max(0.f, minimum); }

bool leptonPassesPairWP(int index, const ROOT::VecOps::RVec<int> &pdgId,
                        const ROOT::VecOps::RVec<bool> &passElectron,
                        const ROOT::VecOps::RVec<bool> &passMuon) {
  if (index < 0 || static_cast<size_t>(index) >= pdgId.size())
    return false;
  const int flavor = std::abs(pdgId[index]);
  if (flavor == 11)
    return static_cast<size_t>(index) < passElectron.size() &&
           passElectron[index] != 0;
  if (flavor == 13)
    return static_cast<size_t>(index) < passMuon.size() &&
           passMuon[index] != 0;
  return false;
}

bool pairPassesSelection(const ROOT::VecOps::RVec<int> &indices,
                         const ROOT::VecOps::RVec<float> &pt,
                         const ROOT::VecOps::RVec<int> &pdgId,
                         const ROOT::VecOps::RVec<bool> &passElectron,
                         const ROOT::VecOps::RVec<bool> &passMuon,
                         int minimumPassID, float leadingPtMinimum,
                         float subleadingPtMinimum) {
  if (indices.size() < 2 || indices[0] < 0 || indices[1] < 0)
    return false;
  const int required = clampPairMinPassID(minimumPassID);
  const int passing =
      static_cast<int>(leptonPassesPairWP(indices[0], pdgId, passElectron,
                                          passMuon)) +
      static_cast<int>(leptonPassesPairWP(indices[1], pdgId, passElectron,
                                          passMuon));
  const auto ordered = orderPairByPt(indices, pt);
  return passing >= required && ordered[0] >= 0 &&
         pt[ordered[0]] >= clampPtMin(leadingPtMinimum) &&
         pt[ordered[1]] >= clampPtMin(subleadingPtMinimum);
}

ROOT::VecOps::RVec<int> bestZ0IdxWithID(
    const ROOT::VecOps::RVec<float> &pt,
    const ROOT::VecOps::RVec<float> &eta,
    const ROOT::VecOps::RVec<float> &phi,
    const ROOT::VecOps::RVec<int> &pdgId,
    const ROOT::VecOps::RVec<bool> &passElectron,
    const ROOT::VecOps::RVec<bool> &passMuon, int minimumPassID,
    float leadingPtMinimum, float subleadingPtMinimum) {
  ROOT::VecOps::RVec<int> best = {-1, -1};
  constexpr float zMass = 91.1876f;
  float smallestDistance = std::numeric_limits<float>::infinity();
  const int size = std::min<int>(
      std::min<int>(pt.size(), eta.size()), std::min<int>(phi.size(), pdgId.size()));
  for (int first = 0; first < size; ++first) {
    const ROOT::Math::PtEtaPhiMVector firstVector(
        pt[first], eta[first], phi[first], leptonMass(pdgId[first]));
    for (int second = first + 1; second < size; ++second) {
      if (pdgId[first] != -pdgId[second])
        continue;
      const ROOT::VecOps::RVec<int> candidate = {first, second};
      if (!pairPassesSelection(candidate, pt, pdgId, passElectron, passMuon,
                               minimumPassID, leadingPtMinimum,
                               subleadingPtMinimum))
        continue;
      const ROOT::Math::PtEtaPhiMVector secondVector(
          pt[second], eta[second], phi[second], leptonMass(pdgId[second]));
      const float distance = std::abs((firstVector + secondVector).M() - zMass);
      if (distance < smallestDistance) {
        smallestDistance = distance;
        best = candidate;
      }
    }
  }
  return orderPairByPt(best, pt);
}

bool passesOrdered2lPtThresholdsFromPair(
    const ROOT::VecOps::RVec<float> &pt,
    const ROOT::VecOps::RVec<int> &indices, float leadingPtMinimum,
    float subleadingPtMinimum) {
  if (indices.size() < 2 || indices[0] == indices[1] || indices[0] < 0 ||
      indices[1] < 0 || static_cast<size_t>(indices[0]) >= pt.size() ||
      static_cast<size_t>(indices[1]) >= pt.size())
    return false;
  const auto ordered = orderPairByPt(indices, pt);
  return pt[ordered[0]] > clampPtMin(leadingPtMinimum) &&
         pt[ordered[1]] > clampPtMin(subleadingPtMinimum);
}

bool validPairIndices(const ROOT::VecOps::RVec<int> &indices,
                      const ROOT::VecOps::RVec<float> &pt,
                      const ROOT::VecOps::RVec<float> &eta,
                      const ROOT::VecOps::RVec<float> &phi,
                      const ROOT::VecOps::RVec<int> &pdgId) {
  if (indices.size() < 2 || indices[0] < 0 || indices[1] < 0)
    return false;
  for (const int index : {indices[0], indices[1]}) {
    const size_t position = static_cast<size_t>(index);
    if (position >= pt.size() || position >= eta.size() ||
        position >= phi.size() || position >= pdgId.size())
      return false;
  }
  return true;
}

float pairMass(const ROOT::VecOps::RVec<float> &pt,
               const ROOT::VecOps::RVec<float> &eta,
               const ROOT::VecOps::RVec<float> &phi,
               const ROOT::VecOps::RVec<int> &pdgId,
               const ROOT::VecOps::RVec<int> &indices) {
  if (!validPairIndices(indices, pt, eta, phi, pdgId))
    return -999.0f;
  const ROOT::Math::PtEtaPhiMVector first(
      pt[indices[0]], eta[indices[0]], phi[indices[0]],
      leptonMass(pdgId[indices[0]]));
  const ROOT::Math::PtEtaPhiMVector second(
      pt[indices[1]], eta[indices[1]], phi[indices[1]],
      leptonMass(pdgId[indices[1]]));
  return (first + second).M();
}

float pairPt(const ROOT::VecOps::RVec<float> &pt,
             const ROOT::VecOps::RVec<float> &eta,
             const ROOT::VecOps::RVec<float> &phi,
             const ROOT::VecOps::RVec<int> &pdgId,
             const ROOT::VecOps::RVec<int> &indices) {
  if (!validPairIndices(indices, pt, eta, phi, pdgId))
    return -999.0f;
  const ROOT::Math::PtEtaPhiMVector first(
      pt[indices[0]], eta[indices[0]], phi[indices[0]],
      leptonMass(pdgId[indices[0]]));
  const ROOT::Math::PtEtaPhiMVector second(
      pt[indices[1]], eta[indices[1]], phi[indices[1]],
      leptonMass(pdgId[indices[1]]));
  return (first + second).Pt();
}

int pairFlavor(const ROOT::VecOps::RVec<int> &pdgId,
               const ROOT::VecOps::RVec<int> &indices) {
  if (indices.size() < 2 || indices[0] < 0 || indices[1] < 0 ||
      static_cast<size_t>(indices[0]) >= pdgId.size() ||
      static_cast<size_t>(indices[1]) >= pdgId.size())
    return 0;
  const int first = std::abs(pdgId[indices[0]]);
  return first == std::abs(pdgId[indices[1]]) ? first : 0;
}

} // namespace RunStability

#endif
