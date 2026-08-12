#ifndef ZH4LMET_PAIRING_STUDY_CC
#define ZH4LMET_PAIRING_STUDY_CC

#include <Math/Vector4D.h>
#include <ROOT/RVec.hxx>

#include <algorithm>
#include <array>
#include <cmath>
#include <limits>
#include <map>
#include <set>
#include <utility>
#include <vector>

namespace PairingStudy {

using ROOT::VecOps::RVec;
using RVecF = RVec<float>;
using RVecI = RVec<int>;
using P4 = ROOT::Math::PtEtaPhiMVector;

constexpr float Z_MASS = 91.1876f;
constexpr float ELECTRON_MASS = 0.000511f;
constexpr float MUON_MASS = 0.105658f;
constexpr float INVALID = -9999.f;
constexpr int N_ALGORITHMS = 6;

enum AlgorithmCode {
  NEAREST_MZ = 0,
  CORE_L4KIN_MASSLESS = 1,
  HISTORICAL_RUN2_MASSLESS = 2,
  RESOLUTION_PULL = 3,
  FSR_NEAREST_MZ = 4,
  FSR_RESOLUTION_PULL = 5
};

enum TopologyCode {
  TOPOLOGY_INVALID = 0,
  TOPOLOGY_4E = 1,
  TOPOLOGY_4MU = 2,
  TOPOLOGY_2E2MU = 3,
  TOPOLOGY_3E1MU = 4,
  TOPOLOGY_1E3MU = 5
};

enum RegionCode {
  REGION_OUTSIDE = 0,
  REGION_ZZCR = 1,
  REGION_XSF_SR = 2,
  REGION_XDF_SR = 3
};

enum TruthStatus {
  TRUTH_UNAVAILABLE = 0,
  TRUTH_DIRECT = 1,
  TRUTH_TAU = 2,
  TRUTH_UNRECOVERABLE = 3,
  TRUTH_RECOVERABLE = 4,
  TRUTH_AMBIGUOUS = 5,
  TRUTH_ALIGNMENT_INVALID = 6
};

inline float leptonMass(int pdgId) {
  return std::abs(pdgId) == 11 ? ELECTRON_MASS : MUON_MASS;
}

inline P4 p4(float pt, float eta, float phi, int pdgId, bool massless = false) {
  return P4(pt, eta, phi, massless ? 0.f : leptonMass(pdgId));
}

inline bool finitePositive(float value) {
  return std::isfinite(value) && value > 0.f;
}

inline bool validIndex(int index, size_t size) {
  return index >= 0 && static_cast<size_t>(index) < size;
}

inline std::array<int, 2> canonicalPair(int first, int second) {
  return first < second ? std::array<int, 2>{first, second}
                        : std::array<int, 2>{second, first};
}

inline bool samePair(int a, int b, int c, int d) {
  return canonicalPair(a, b) == canonicalPair(c, d);
}

inline std::array<int, 4> canonicalPartition(int a, int b, int c, int d) {
  const auto first = canonicalPair(a, b);
  const auto second = canonicalPair(c, d);
  if (first < second)
    return {first[0], first[1], second[0], second[1]};
  return {second[0], second[1], first[0], first[1]};
}

struct Candidate {
  int z1 = -1;
  int z2 = -1;
  int x1 = -1;
  int x2 = -1;
  int partition = -1;
  int zFlavor = 0;
  int xFlavor = 0;
  float mZ = INVALID;
  float mX = INVALID;
  float ptZ = INVALID;
  float ptX = INVALID;
  float drZ = INVALID;
  float drX = INVALID;
  float dphiZ = INVALID;
  float dphiX = INVALID;
  float dmZ = std::numeric_limits<float>::infinity();
  float masslessMZ = INVALID;
  float masslessDmZ = std::numeric_limits<float>::infinity();
  float sigmaMZ = INVALID;
  float pull = std::numeric_limits<float>::infinity();
  float fsrMZ = INVALID;
  float fsrDmZ = std::numeric_limits<float>::infinity();
  float fsrPull = std::numeric_limits<float>::infinity();
  bool resolutionValid = false;
  bool fsrValid = false;
};

struct TruthResult {
  int status = TRUTH_UNAVAILABLE;
  int pair1a = -1;
  int pair1b = -1;
  int pair2a = -1;
  int pair2b = -1;
  int referencePair = -1;
  float referencePt = INVALID;
  bool direct = false;
  bool recoverable = false;
  bool partitionValid = false;
  bool identicalFlavorConvention = false;
  bool recordAmbiguous = false;
  bool hwwComplementValid = false;
};

struct EventResult {
  RVecI quartet;
  RVec<Candidate> candidates;
  RVecI selectedCandidate;
  RVecF selectedScore;
  RVecF secondScore;
  RVecF scoreGap;
  RVecI selectedZ1;
  RVecI selectedZ2;
  RVecI selectedX1;
  RVecI selectedX2;
  RVecI selectedZFlavor;
  RVecF selectedMZ;
  RVecF selectedMX;
  RVecF selectedPtZ;
  RVecF selectedPtX;
  RVecF selectedDrZ;
  RVecF selectedDrX;
  RVecI selectedXFlavor;
  RVecI region;
  RVecI zhCorrect;
  RVecI zzCorrect;
  RVecI algorithmValid;
  TruthResult zhTruth;
  TruthResult zzTruth;
  bool quartetValid = false;
  bool objectBase = false;
  bool physBase = false;
  bool sourceAlignmentValid = false;
  bool resolutionScoresValid = false;
  bool fsrScoresValid = false;
  bool xComplementIdentical = false;
  int xDifferenceReason = 3;
  int sourceAlignmentFailure = 1;
  int topology = TOPOLOGY_INVALID;
  int nValidCandidates = 0;
  int nDistinctPartitions = 0;
  float minPairMass = INVALID;
  float m4l = INVALID;
};

inline int topologyCode(const RVecI &pdgId, const RVecI &quartet) {
  if (quartet.size() != 4)
    return TOPOLOGY_INVALID;
  int electrons = 0;
  int muons = 0;
  for (int idx : quartet) {
    if (!validIndex(idx, pdgId.size()))
      return TOPOLOGY_INVALID;
    if (std::abs(pdgId[idx]) == 11)
      ++electrons;
    else if (std::abs(pdgId[idx]) == 13)
      ++muons;
    else
      return TOPOLOGY_INVALID;
  }
  if (electrons == 4)
    return TOPOLOGY_4E;
  if (muons == 4)
    return TOPOLOGY_4MU;
  if (electrons == 2)
    return TOPOLOGY_2E2MU;
  if (electrons == 3)
    return TOPOLOGY_3E1MU;
  if (electrons == 1)
    return TOPOLOGY_1E3MU;
  return TOPOLOGY_INVALID;
}

inline RVecI buildQuartet(const RVecF &pt, const RVecI &pdgId,
                          const RVecI &tightMask) {
  const size_t n = std::min({pt.size(), pdgId.size(), tightMask.size()});
  std::vector<std::pair<float, int>> eligible;
  eligible.reserve(n);
  for (size_t i = 0; i < n; ++i) {
    if (!tightMask[i] || !finitePositive(pt[i]))
      continue;
    if (std::abs(pdgId[i]) != 11 && std::abs(pdgId[i]) != 13)
      continue;
    eligible.emplace_back(pt[i], static_cast<int>(i));
  }
  std::stable_sort(eligible.begin(), eligible.end(),
                   [](const auto &left, const auto &right) {
                     if (left.first != right.first)
                       return left.first > right.first;
                     return left.second < right.second;
                   });
  RVecI out;
  for (size_t rank = 0; rank < std::min<size_t>(4, eligible.size()); ++rank)
    out.push_back(eligible[rank].second);
  return out;
}

inline bool passesObjectBase(const RVecF &pt, const RVecI &pdgId,
                             const RVecI &quartet) {
  if (quartet.size() != 4)
    return false;
  const std::array<float, 4> thresholds{25.f, 15.f, 10.f, 10.f};
  int chargeSignSum = 0;
  for (size_t rank = 0; rank < 4; ++rank) {
    const int idx = quartet[rank];
    if (!validIndex(idx, pt.size()) || !validIndex(idx, pdgId.size()) ||
        !(pt[idx] > thresholds[rank]))
      return false;
    chargeSignSum += pdgId[idx] > 0 ? 1 : -1;
  }
  int nAtTen = 0;
  for (float value : pt)
    if (std::isfinite(value) && value >= 10.f)
      ++nAtTen;
  return chargeSignSum == 0 && nAtTen <= 4;
}

inline float quartetMinPairMass(const RVecF &pt, const RVecF &eta,
                                const RVecF &phi, const RVecI &pdgId,
                                const RVecI &quartet) {
  if (quartet.size() != 4)
    return INVALID;
  float minimum = std::numeric_limits<float>::infinity();
  for (size_t i = 0; i < quartet.size(); ++i) {
    for (size_t j = i + 1; j < quartet.size(); ++j) {
      const int a = quartet[i];
      const int b = quartet[j];
      if (!validIndex(a, pt.size()) || !validIndex(a, eta.size()) ||
          !validIndex(a, phi.size()) || !validIndex(a, pdgId.size()) ||
          !validIndex(b, pt.size()) || !validIndex(b, eta.size()) ||
          !validIndex(b, phi.size()) || !validIndex(b, pdgId.size()))
        return INVALID;
      minimum = std::min(
          minimum, static_cast<float>((p4(pt[a], eta[a], phi[a], pdgId[a]) +
                                       p4(pt[b], eta[b], phi[b], pdgId[b]))
                                          .M()));
    }
  }
  return std::isfinite(minimum) ? minimum : INVALID;
}

inline RVecI coherentSourceMap(const RVecF &finalPt,
                               const RVecF &finalEta, const RVecF &finalPhi,
                               const RVecI &finalPdgId,
                               const RVecF &sourcePt,
                               const RVecF &sourceEta,
                               const RVecF &sourcePhi,
                               const RVecI &sourcePdgId,
                               const RVecI &quartet) {
  RVecI out;
  if (quartet.size() != 4)
    return out;
  std::vector<bool> used(sourceEta.size(), false);
  constexpr float tolerance2 = 1.e-8f;
  for (int finalIdx : quartet) {
    if (!validIndex(finalIdx, finalPt.size()) ||
        !finitePositive(finalPt[finalIdx]) ||
        !validIndex(finalIdx, finalEta.size()) ||
        !validIndex(finalIdx, finalPhi.size()) ||
        !validIndex(finalIdx, finalPdgId.size()))
      return {};
    int match = -1;
    float best = tolerance2;
    bool ambiguous = false;
    for (size_t sourceIdx = 0; sourceIdx < sourceEta.size(); ++sourceIdx) {
      if (used[sourceIdx] || sourceIdx >= sourcePt.size() ||
          !finitePositive(sourcePt[sourceIdx]) ||
          sourceIdx >= sourcePhi.size() ||
          sourceIdx >= sourcePdgId.size() ||
          sourcePdgId[sourceIdx] != finalPdgId[finalIdx])
        continue;
      const float dEta = finalEta[finalIdx] - sourceEta[sourceIdx];
      const float dPhi =
          ROOT::VecOps::DeltaPhi(finalPhi[finalIdx], sourcePhi[sourceIdx]);
      const float dr2 = dEta * dEta + dPhi * dPhi;
      if (std::isfinite(dr2) && dr2 <= best) {
        if (match >= 0 && std::abs(dr2 - best) <= 1.e-12f) {
          ambiguous = true;
        } else {
          best = dr2;
          match = static_cast<int>(sourceIdx);
          ambiguous = false;
        }
      }
    }
    if (match < 0 || ambiguous)
      return {};
    used[match] = true;
    out.push_back(match);
  }
  // finalPt is scale/smearing corrected while sourcePt is pre-scale.  Both
  // must be physical, but equality would reject correctly scaled objects.
  return out;
}

inline int sourceObjectIndex(int finalIdx, const RVecI &quartet,
                             const RVecI &sourceMap,
                             const RVecI &sourcePdgId,
                             const RVecI &sourceElectronIdx,
                             const RVecI &sourceMuonIdx) {
  auto found = std::find(quartet.begin(), quartet.end(), finalIdx);
  if (found == quartet.end())
    return -1;
  const size_t rank = std::distance(quartet.begin(), found);
  if (rank >= sourceMap.size())
    return -1;
  const int source = sourceMap[rank];
  if (!validIndex(source, sourcePdgId.size()))
    return -1;
  if (std::abs(sourcePdgId[source]) == 11)
    return validIndex(source, sourceElectronIdx.size())
               ? sourceElectronIdx[source]
               : -1;
  if (std::abs(sourcePdgId[source]) == 13)
    return validIndex(source, sourceMuonIdx.size()) ? sourceMuonIdx[source] : -1;
  return -1;
}

inline float relativePtError(int finalIdx, const RVecI &quartet,
                             const RVecI &sourceMap,
                             const RVecI &sourcePdgId,
                             const RVecI &sourceElectronIdx,
                             const RVecI &sourceMuonIdx,
                             const RVecF &electronPt,
                             const RVecF &electronEta,
                             const RVecF &electronEnergyErr,
                             const RVecF &muonPt,
                             const RVecF &muonPtErr) {
  auto found = std::find(quartet.begin(), quartet.end(), finalIdx);
  if (found == quartet.end())
    return INVALID;
  const size_t rank = std::distance(quartet.begin(), found);
  if (rank >= sourceMap.size())
    return INVALID;
  const int source = sourceMap[rank];
  if (!validIndex(source, sourcePdgId.size()))
    return INVALID;
  const int absPdg = std::abs(sourcePdgId[source]);
  if (absPdg == 11) {
    const int idx = sourceObjectIndex(finalIdx, quartet, sourceMap, sourcePdgId,
                                      sourceElectronIdx, sourceMuonIdx);
    if (!validIndex(idx, electronPt.size()) ||
        !validIndex(idx, electronEta.size()) ||
        !validIndex(idx, electronEnergyErr.size()))
      return INVALID;
    const float energy = electronPt[idx] * std::cosh(electronEta[idx]);
    return finitePositive(energy) && finitePositive(electronEnergyErr[idx])
               ? electronEnergyErr[idx] / energy
               : INVALID;
  }
  if (absPdg == 13) {
    const int idx = sourceObjectIndex(finalIdx, quartet, sourceMap, sourcePdgId,
                                      sourceElectronIdx, sourceMuonIdx);
    if (!validIndex(idx, muonPt.size()) || !validIndex(idx, muonPtErr.size()))
      return INVALID;
    return finitePositive(muonPt[idx]) && finitePositive(muonPtErr[idx])
               ? muonPtErr[idx] / muonPt[idx]
               : INVALID;
  }
  return INVALID;
}

inline int sourceFsrIndex(int finalIdx, const RVecI &quartet,
                          const RVecI &sourceMap,
                          const RVecI &sourcePdgId,
                          const RVecI &sourceElectronIdx,
                          const RVecI &sourceMuonIdx,
                          const RVecI &electronFsrIdx,
                          const RVecI &muonFsrIdx,
                          const RVecI &fsrElectronIdx,
                          const RVecI &fsrMuonIdx) {
  auto found = std::find(quartet.begin(), quartet.end(), finalIdx);
  if (found == quartet.end())
    return -1;
  const size_t rank = std::distance(quartet.begin(), found);
  if (rank >= sourceMap.size())
    return -1;
  const int source = sourceMap[rank];
  if (!validIndex(source, sourcePdgId.size()))
    return -1;
  const int object = sourceObjectIndex(finalIdx, quartet, sourceMap, sourcePdgId,
                                       sourceElectronIdx, sourceMuonIdx);
  if (std::abs(sourcePdgId[source]) == 11) {
    if (!validIndex(object, electronFsrIdx.size()))
      return -2;
    const int photon = electronFsrIdx[object];
    if (photon < 0)
      return -1;
    return validIndex(photon, fsrElectronIdx.size()) &&
                   fsrElectronIdx[photon] == object
               ? photon
               : -2;
  }
  if (std::abs(sourcePdgId[source]) == 13) {
    if (!validIndex(object, muonFsrIdx.size()))
      return -2;
    const int photon = muonFsrIdx[object];
    if (photon < 0)
      return -1;
    return validIndex(photon, fsrMuonIdx.size()) &&
                   fsrMuonIdx[photon] == object
               ? photon
               : -2;
  }
  return -1;
}

inline RVec<Candidate>
enumerateCandidates(const RVecF &pt, const RVecF &eta, const RVecF &phi,
                    const RVecI &pdgId, const RVecI &quartet,
                    const RVecI &sourceMap = {},
                    const RVecI &sourcePdgId = {},
                    const RVecI &sourceElectronIdx = {},
                    const RVecI &sourceMuonIdx = {},
                    const RVecF &electronPt = {},
                    const RVecF &electronEta = {},
                    const RVecF &electronEnergyErr = {},
                    const RVecF &muonPt = {},
                    const RVecF &muonPtErr = {},
                    const RVecI &electronFsrIdx = {},
                    const RVecI &muonFsrIdx = {},
                    const RVecF &fsrPt = {}, const RVecF &fsrEta = {},
                    const RVecF &fsrPhi = {},
                    const RVecI &fsrElectronIdx = {},
                    const RVecI &fsrMuonIdx = {}) {
  RVec<Candidate> out;
  if (quartet.size() != 4)
    return out;
  std::map<std::array<int, 4>, int> partitionCodes;
  for (size_t left = 0; left < quartet.size(); ++left) {
    for (size_t right = left + 1; right < quartet.size(); ++right) {
      const int z1 = quartet[left];
      const int z2 = quartet[right];
      if (!validIndex(z1, pdgId.size()) || !validIndex(z2, pdgId.size()) ||
          pdgId[z1] != -pdgId[z2])
        continue;
      if (!validIndex(z1, pt.size()) || !validIndex(z2, pt.size()) ||
          !validIndex(z1, eta.size()) || !validIndex(z2, eta.size()) ||
          !validIndex(z1, phi.size()) || !validIndex(z2, phi.size()))
        continue;
      if (std::max(pt[z1], pt[z2]) < 10.f ||
          std::min(pt[z1], pt[z2]) < 10.f)
        continue;
      int x1 = -1;
      int x2 = -1;
      for (int idx : quartet) {
        if (idx == z1 || idx == z2)
          continue;
        if (x1 < 0)
          x1 = idx;
        else
          x2 = idx;
      }
      if (x1 < 0 || x2 < 0)
        continue;
      Candidate candidate;
      if (pt[z2] > pt[z1]) {
        candidate.z1 = z2;
        candidate.z2 = z1;
      } else {
        candidate.z1 = z1;
        candidate.z2 = z2;
      }
      if (pt[x2] > pt[x1]) {
        candidate.x1 = x2;
        candidate.x2 = x1;
      } else {
        candidate.x1 = x1;
        candidate.x2 = x2;
      }
      const auto nominalZ = p4(pt[z1], eta[z1], phi[z1], pdgId[z1]) +
                            p4(pt[z2], eta[z2], phi[z2], pdgId[z2]);
      const auto nominalX = p4(pt[x1], eta[x1], phi[x1], pdgId[x1]) +
                            p4(pt[x2], eta[x2], phi[x2], pdgId[x2]);
      const auto masslessZ = p4(pt[z1], eta[z1], phi[z1], pdgId[z1], true) +
                             p4(pt[z2], eta[z2], phi[z2], pdgId[z2], true);
      candidate.mZ = nominalZ.M();
      candidate.mX = nominalX.M();
      candidate.ptZ = nominalZ.Pt();
      candidate.ptX = nominalX.Pt();
      candidate.drZ =
          ROOT::VecOps::DeltaR(eta[z1], eta[z2], phi[z1], phi[z2]);
      candidate.drX =
          ROOT::VecOps::DeltaR(eta[x1], eta[x2], phi[x1], phi[x2]);
      candidate.dphiZ =
          std::abs(ROOT::VecOps::DeltaPhi(phi[z1], phi[z2]));
      candidate.dphiX =
          std::abs(ROOT::VecOps::DeltaPhi(phi[x1], phi[x2]));
      candidate.zFlavor = std::abs(pdgId[z1]);
      candidate.xFlavor =
          std::abs(pdgId[x1]) == std::abs(pdgId[x2]) ? 1 : 2;
      candidate.dmZ = std::abs(candidate.mZ - Z_MASS);
      candidate.masslessMZ = masslessZ.M();
      candidate.masslessDmZ = std::abs(candidate.masslessMZ - Z_MASS);

      const float rel1 = relativePtError(
          z1, quartet, sourceMap, sourcePdgId, sourceElectronIdx,
          sourceMuonIdx, electronPt, electronEta, electronEnergyErr, muonPt,
          muonPtErr);
      const float rel2 = relativePtError(
          z2, quartet, sourceMap, sourcePdgId, sourceElectronIdx,
          sourceMuonIdx, electronPt, electronEta, electronEnergyErr, muonPt,
          muonPtErr);
      if (finitePositive(rel1) && finitePositive(rel2) &&
          finitePositive(candidate.mZ)) {
        candidate.sigmaMZ =
            0.5f * candidate.mZ * std::sqrt(rel1 * rel1 + rel2 * rel2);
        candidate.resolutionValid = finitePositive(candidate.sigmaMZ);
        if (candidate.resolutionValid)
          candidate.pull = candidate.dmZ / candidate.sigmaMZ;
      }

      P4 fsrZ = nominalZ;
      std::set<int> usedPhotons;
      bool associationsValid = sourceMap.size() == quartet.size();
      for (int zidx : {z1, z2}) {
        const int photon = sourceFsrIndex(
            zidx, quartet, sourceMap, sourcePdgId, sourceElectronIdx,
            sourceMuonIdx, electronFsrIdx, muonFsrIdx, fsrElectronIdx,
            fsrMuonIdx);
        if (photon == -2) {
          associationsValid = false;
          break;
        }
        if (photon < 0)
          continue;
        if (!validIndex(photon, fsrPt.size()) ||
            !validIndex(photon, fsrEta.size()) ||
            !validIndex(photon, fsrPhi.size()) ||
            !finitePositive(fsrPt[photon]) ||
            !std::isfinite(fsrEta[photon]) ||
            !std::isfinite(fsrPhi[photon])) {
          associationsValid = false;
          break;
        }
        if (usedPhotons.insert(photon).second)
          fsrZ += P4(fsrPt[photon], fsrEta[photon], fsrPhi[photon], 0.f);
      }
      candidate.fsrValid = associationsValid;
      if (candidate.fsrValid) {
        candidate.fsrMZ = fsrZ.M();
        candidate.fsrDmZ = std::abs(candidate.fsrMZ - Z_MASS);
        if (candidate.resolutionValid)
          candidate.fsrPull = candidate.fsrDmZ / candidate.sigmaMZ;
      }

      const auto partitionKey = canonicalPartition(z1, z2, x1, x2);
      auto inserted = partitionCodes.emplace(
          partitionKey, static_cast<int>(partitionCodes.size()));
      candidate.partition = inserted.first->second;
      out.push_back(candidate);
    }
  }
  return out;
}

inline float candidateScore(const Candidate &candidate, int algorithm) {
  if (algorithm == NEAREST_MZ)
    return candidate.dmZ;
  if (algorithm == CORE_L4KIN_MASSLESS ||
      algorithm == HISTORICAL_RUN2_MASSLESS)
    return candidate.masslessDmZ;
  if (algorithm == RESOLUTION_PULL && candidate.resolutionValid)
    return candidate.pull;
  if (algorithm == FSR_NEAREST_MZ && candidate.fsrValid)
    return candidate.fsrDmZ;
  if (algorithm == FSR_RESOLUTION_PULL && candidate.fsrValid &&
      candidate.resolutionValid)
    return candidate.fsrPull;
  return std::numeric_limits<float>::infinity();
}

inline bool algorithmScoresValid(const RVec<Candidate> &candidates,
                                 int algorithm) {
  if (candidates.empty())
    return false;
  for (const auto &candidate : candidates)
    if (!std::isfinite(candidateScore(candidate, algorithm)))
      return false;
  return true;
}

inline int selectCandidate(const RVec<Candidate> &candidates, int algorithm) {
  // Never improve a comparator by silently dropping candidates whose special
  // score is unavailable.  Every method consumes the exhaustive common set.
  if (!algorithmScoresValid(candidates, algorithm))
    return -1;
  float best = std::numeric_limits<float>::infinity();
  int selected = -1;
  for (size_t index = 0; index < candidates.size(); ++index) {
    const float score = candidateScore(candidates[index], algorithm);
    if (score < best) { // strict first-encounter tie behavior
      best = score;
      selected = static_cast<int>(index);
    }
  }
  return selected;
}

inline std::array<float, 3> scoreSummary(const RVec<Candidate> &candidates,
                                         int algorithm) {
  if (!algorithmScoresValid(candidates, algorithm))
    return {INVALID, INVALID, INVALID};
  float best = std::numeric_limits<float>::infinity();
  float second = std::numeric_limits<float>::infinity();
  for (const auto &candidate : candidates) {
    const float score = candidateScore(candidate, algorithm);
    if (!std::isfinite(score))
      continue;
    if (score < best) {
      second = best;
      best = score;
    } else if (score < second) {
      second = score;
    }
  }
  return {std::isfinite(best) ? best : INVALID,
          std::isfinite(second) ? second : INVALID,
          std::isfinite(best) && std::isfinite(second) ? second - best
                                                        : INVALID};
}

inline int regionCode(const Candidate &candidate, float met, float m4l) {
  if (!(candidate.dmZ < 15.f))
    return REGION_OUTSIDE;
  if (candidate.xFlavor == 1 && candidate.mX > 75.f &&
      candidate.mX < 105.f && met < 35.f)
    return REGION_ZZCR;
  if (candidate.xFlavor == 1 && candidate.mX > 10.f &&
      candidate.mX < 65.f && met > 35.f && m4l > 140.f)
    return REGION_XSF_SR;
  if (candidate.xFlavor == 2 && candidate.mX > 10.f &&
      candidate.mX < 70.f && met > 20.f)
    return REGION_XDF_SR;
  return REGION_OUTSIDE;
}

inline bool statusFlag(int flags, int bit) {
  return flags >= 0 && ((flags >> bit) & 1);
}

inline bool hasAncestorAbsPdg(int index, int absPdgId, const RVecI &genPdgId,
                              const RVecI &genMother) {
  std::set<int> visited;
  int current = index;
  while (validIndex(current, genMother.size()) && visited.insert(current).second) {
    const int mother = genMother[current];
    if (!validIndex(mother, genPdgId.size()))
      return false;
    if (std::abs(genPdgId[mother]) == absPdgId)
      return true;
    current = mother;
  }
  return false;
}

inline int canonicalBosonAncestor(int index, const RVecI &genPdgId,
                                  const RVecI &genMother,
                                  const RVecI &genStatusFlags,
                                  bool allowPhoton = true) {
  std::set<int> visited;
  int current = index;
  while (validIndex(current, genMother.size()) && visited.insert(current).second) {
    const int mother = genMother[current];
    if (!validIndex(mother, genPdgId.size()))
      return -1;
    const int absId = std::abs(genPdgId[mother]);
    if (absId == 23 || (allowPhoton && absId == 22)) {
      const bool hard = validIndex(mother, genStatusFlags.size()) &&
                        (statusFlag(genStatusFlags[mother], 7) ||
                         statusFlag(genStatusFlags[mother], 8) ||
                         statusFlag(genStatusFlags[mother], 11));
      if (absId == 23 || hard) {
        int canonical = mother;
        int parent = validIndex(canonical, genMother.size())
                         ? genMother[canonical]
                         : -1;
        while (validIndex(parent, genPdgId.size()) &&
               std::abs(genPdgId[parent]) == absId) {
          canonical = parent;
          parent = validIndex(canonical, genMother.size())
                       ? genMother[canonical]
                       : -1;
        }
        return canonical;
      }
    }
    current = mother;
  }
  return -1;
}

inline int directHardBosonAncestor(int index, const RVecI &genPdgId,
                                   const RVecI &genMother,
                                   const RVecI &genStatusFlags,
                                   bool allowPhoton = true) {
  if (!validIndex(index, genPdgId.size()))
    return -1;
  const int leptonAbsPdg = std::abs(genPdgId[index]);
  if (leptonAbsPdg != 11 && leptonAbsPdg != 13)
    return -1;
  std::set<int> visited;
  int current = index;
  while (validIndex(current, genMother.size()) && visited.insert(current).second) {
    const int mother = genMother[current];
    if (!validIndex(mother, genPdgId.size()))
      return -1;
    const int motherAbsPdg = std::abs(genPdgId[mother]);
    if (motherAbsPdg == leptonAbsPdg) {
      current = mother;
      continue;
    }
    if (motherAbsPdg != 23 && !(allowPhoton && motherAbsPdg == 22))
      return -1;
    const bool hard = validIndex(mother, genStatusFlags.size()) &&
                      (statusFlag(genStatusFlags[mother], 7) ||
                       statusFlag(genStatusFlags[mother], 8) ||
                       statusFlag(genStatusFlags[mother], 11));
    if (!hard)
      return -1;
    int canonical = mother;
    int parent = validIndex(canonical, genMother.size())
                     ? genMother[canonical]
                     : -1;
    while (validIndex(parent, genPdgId.size()) &&
           std::abs(genPdgId[parent]) == motherAbsPdg) {
      canonical = parent;
      parent = validIndex(canonical, genMother.size())
                   ? genMother[canonical]
                   : -1;
    }
    return canonical;
  }
  return -1;
}

inline int sourceGenIndex(int finalIdx, const RVecI &quartet,
                          const RVecI &sourceMap,
                          const RVecI &sourcePdgId,
                          const RVecI &sourceElectronIdx,
                          const RVecI &sourceMuonIdx,
                          const RVecI &electronGenIdx,
                          const RVecI &muonGenIdx) {
  auto found = std::find(quartet.begin(), quartet.end(), finalIdx);
  if (found == quartet.end())
    return -1;
  const size_t rank = std::distance(quartet.begin(), found);
  if (rank >= sourceMap.size())
    return -1;
  const int source = sourceMap[rank];
  if (!validIndex(source, sourcePdgId.size()))
    return -1;
  const int object = sourceObjectIndex(finalIdx, quartet, sourceMap, sourcePdgId,
                                       sourceElectronIdx, sourceMuonIdx);
  if (std::abs(sourcePdgId[source]) == 11)
    return validIndex(object, electronGenIdx.size()) ? electronGenIdx[object] : -1;
  if (std::abs(sourcePdgId[source]) == 13)
    return validIndex(object, muonGenIdx.size()) ? muonGenIdx[object] : -1;
  return -1;
}

inline int canonicalLeptonLineage(int index, const RVecI &genPdgId,
                                  const RVecI &genMother) {
  if (!validIndex(index, genPdgId.size()) ||
      (std::abs(genPdgId[index]) != 11 && std::abs(genPdgId[index]) != 13))
    return -1;
  const int signedPdgId = genPdgId[index];
  std::set<int> visited;
  int canonical = index;
  while (validIndex(canonical, genMother.size()) &&
         visited.insert(canonical).second) {
    const int mother = genMother[canonical];
    if (!validIndex(mother, genPdgId.size()) ||
        genPdgId[mother] != signedPdgId)
      break;
    canonical = mother;
  }
  return canonical;
}

inline int associatedZIndex(const RVecI &genPdgId, const RVecI &genMother,
                            const RVecI &genStatusFlags) {
  std::set<int> candidates;
  for (size_t i = 0; i < genPdgId.size(); ++i) {
    if (std::abs(genPdgId[i]) != 23 ||
        !validIndex(i, genStatusFlags.size()) ||
        !statusFlag(genStatusFlags[i], 13))
      continue;
    const bool hard = statusFlag(genStatusFlags[i], 7) ||
                      statusFlag(genStatusFlags[i], 8) ||
                      statusFlag(genStatusFlags[i], 11);
    if (hard && !hasAncestorAbsPdg(static_cast<int>(i), 25, genPdgId, genMother)) {
      int canonical = static_cast<int>(i);
      int parent = validIndex(canonical, genMother.size())
                       ? genMother[canonical]
                       : -1;
      while (validIndex(parent, genPdgId.size()) &&
             std::abs(genPdgId[parent]) == 23) {
        canonical = parent;
        parent = validIndex(canonical, genMother.size())
                     ? genMother[canonical]
                     : -1;
      }
      candidates.insert(canonical);
    }
  }
  if (candidates.empty())
    return -1;
  if (candidates.size() != 1)
    return -2;
  return *candidates.begin();
}

inline TruthResult buildZHTruth(
    const RVecI &quartet, const RVecI &sourceMap,
    const RVecI &sourcePdgId, const RVecI &sourceElectronIdx,
    const RVecI &sourceMuonIdx, const RVecI &electronGenIdx,
    const RVecI &muonGenIdx, const RVecI &genPdgId,
    const RVecI &genMother, const RVecI &genStatusFlags,
    const RVecF &genPt) {
  TruthResult truth;
  if (sourceMap.size() != quartet.size()) {
    truth.status = TRUTH_ALIGNMENT_INVALID;
    return truth;
  }
  const int associatedZ = associatedZIndex(genPdgId, genMother, genStatusFlags);
  if (associatedZ == -2) {
    truth.status = TRUTH_AMBIGUOUS;
    return truth;
  }
  if (associatedZ < 0)
    return truth;

  std::vector<int> directTruthLeptons;
  bool tauDecay = false;
  for (size_t gen = 0; gen < genPdgId.size(); ++gen) {
    if (std::abs(genPdgId[gen]) != 11 && std::abs(genPdgId[gen]) != 13)
      continue;
    if (!validIndex(gen, genStatusFlags.size()) ||
        !statusFlag(genStatusFlags[gen], 13))
      continue;
    const int broadBoson = canonicalBosonAncestor(
        static_cast<int>(gen), genPdgId, genMother, genStatusFlags, false);
    if (broadBoson != associatedZ)
      continue;
    if (hasAncestorAbsPdg(static_cast<int>(gen), 15, genPdgId, genMother)) {
      tauDecay = true;
      continue;
    }
    const int directBoson = directHardBosonAncestor(
        static_cast<int>(gen), genPdgId, genMother, genStatusFlags, false);
    if (directBoson == associatedZ)
      directTruthLeptons.push_back(static_cast<int>(gen));
  }
  truth.direct = directTruthLeptons.size() == 2 &&
                 genPdgId[directTruthLeptons[0]] ==
                     -genPdgId[directTruthLeptons[1]];
  if (!truth.direct) {
    truth.status = tauDecay ? TRUTH_TAU : TRUTH_UNRECOVERABLE;
    return truth;
  }

  std::map<int, int> targetLineageToReco;
  for (int gen : directTruthLeptons) {
    const int lineage = canonicalLeptonLineage(gen, genPdgId, genMother);
    if (lineage < 0 || !targetLineageToReco.emplace(lineage, -1).second) {
      truth.status = TRUTH_AMBIGUOUS;
      return truth;
    }
  }
  std::vector<int> hww;
  std::set<int> usedRecoGenLineages;
  for (int reco : quartet) {
    const int gen = sourceGenIndex(
        reco, quartet, sourceMap, sourcePdgId, sourceElectronIdx,
        sourceMuonIdx, electronGenIdx, muonGenIdx);
    if (!validIndex(gen, genPdgId.size()))
      continue;
    const int lineage = canonicalLeptonLineage(gen, genPdgId, genMother);
    auto target = targetLineageToReco.find(lineage);
    if (target != targetLineageToReco.end()) {
      if (target->second >= 0 || !usedRecoGenLineages.insert(lineage).second) {
        truth.status = TRUTH_UNRECOVERABLE;
        return truth;
      }
      target->second = reco;
    }
    if (lineage >= 0 && hasAncestorAbsPdg(gen, 25, genPdgId, genMother) &&
        hasAncestorAbsPdg(gen, 24, genPdgId, genMother) &&
        usedRecoGenLineages.insert(lineage).second)
      hww.push_back(reco);
  }
  if (std::any_of(targetLineageToReco.begin(), targetLineageToReco.end(),
                  [](const auto &item) { return item.second < 0; })) {
    truth.status = TRUTH_UNRECOVERABLE;
    return truth;
  }
  auto target = targetLineageToReco.begin();
  truth.pair1a = target->second;
  truth.pair1b = std::next(target)->second;
  truth.recoverable = true;
  truth.status = TRUTH_RECOVERABLE;
  truth.referencePt =
      validIndex(associatedZ, genPt.size()) ? genPt[associatedZ] : INVALID;
  if (hww.size() == 2) {
    truth.pair2a = hww[0];
    truth.pair2b = hww[1];
    std::array<int, 4> truthIndices{truth.pair1a, truth.pair1b,
                                    truth.pair2a, truth.pair2b};
    std::array<int, 4> quartetIndices{quartet[0], quartet[1], quartet[2],
                                      quartet[3]};
    std::sort(truthIndices.begin(), truthIndices.end());
    std::sort(quartetIndices.begin(), quartetIndices.end());
    truth.hwwComplementValid = truthIndices == quartetIndices;
  }
  return truth;
}

inline TruthResult buildZZTruth(
    const RVecI &quartet, const RVecI &sourceMap,
    const RVecI &sourcePdgId, const RVecI &sourceElectronIdx,
    const RVecI &sourceMuonIdx, const RVecI &electronGenIdx,
    const RVecI &muonGenIdx, const RVecI &genPdgId,
    const RVecI &genMother, const RVecI &genStatusFlags,
    const RVecF &genPt, const RVecF &genEta, const RVecF &genPhi,
    const RVecF &genMass) {
  TruthResult truth;
  if (sourceMap.size() != quartet.size()) {
    truth.status = TRUTH_ALIGNMENT_INVALID;
    return truth;
  }

  // Establish the generator-record contract without reference to reco.  This
  // keeps direct-four-lepton and four-reco-matched counts genuinely distinct.
  std::map<int, std::vector<int>> directGroups;
  bool tau = false;
  for (size_t gen = 0; gen < genPdgId.size(); ++gen) {
    if ((std::abs(genPdgId[gen]) != 11 && std::abs(genPdgId[gen]) != 13) ||
        !validIndex(gen, genStatusFlags.size()) ||
        !statusFlag(genStatusFlags[gen], 13))
      continue;
    const bool fromTau = hasAncestorAbsPdg(
        static_cast<int>(gen), 15, genPdgId, genMother);
    const int boson = directHardBosonAncestor(
        static_cast<int>(gen), genPdgId, genMother, genStatusFlags, true);
    if (fromTau) {
      if (canonicalBosonAncestor(static_cast<int>(gen), genPdgId, genMother,
                                 genStatusFlags, true) >= 0)
        tau = true;
      continue;
    }
    if (boson >= 0)
      directGroups[boson].push_back(static_cast<int>(gen));
  }

  if (directGroups.size() != 2) {
    truth.status = tau ? TRUTH_TAU
                       : (directGroups.size() > 2 ? TRUTH_AMBIGUOUS
                                                  : TRUTH_UNRECOVERABLE);
    return truth;
  }
  auto first = directGroups.begin();
  auto second = std::next(first);
  if (first->second.size() != 2 || second->second.size() != 2) {
    truth.status = TRUTH_AMBIGUOUS;
    return truth;
  }
  auto groupIsOSSF = [&](const std::vector<int> &group) {
    return group.size() == 2 && validIndex(group[0], genPdgId.size()) &&
           validIndex(group[1], genPdgId.size()) &&
           genPdgId[group[0]] == -genPdgId[group[1]];
  };
  if (!groupIsOSSF(first->second) || !groupIsOSSF(second->second)) {
    truth.status = TRUTH_UNRECOVERABLE;
    return truth;
  }
  truth.direct = true;

  truth.identicalFlavorConvention =
      std::abs(genPdgId[first->second[0]]) ==
      std::abs(genPdgId[second->second[0]]);
  truth.recordAmbiguous = truth.identicalFlavorConvention;

  std::map<int, std::pair<int, int>> lineageTargets;
  for (const auto &group : directGroups) {
    for (int gen : group.second) {
      const int lineage = canonicalLeptonLineage(gen, genPdgId, genMother);
      if (lineage < 0 ||
          !lineageTargets.emplace(lineage,
                                  std::make_pair(group.first, -1)).second) {
        truth.status = TRUTH_AMBIGUOUS;
        return truth;
      }
    }
  }
  for (int reco : quartet) {
    const int gen = sourceGenIndex(
        reco, quartet, sourceMap, sourcePdgId, sourceElectronIdx,
        sourceMuonIdx, electronGenIdx, muonGenIdx);
    const int lineage = canonicalLeptonLineage(gen, genPdgId, genMother);
    auto target = lineageTargets.find(lineage);
    if (target == lineageTargets.end())
      continue;
    if (target->second.second >= 0) {
      truth.status = TRUTH_UNRECOVERABLE;
      return truth;
    }
    target->second.second = reco;
  }
  if (std::any_of(lineageTargets.begin(), lineageTargets.end(),
                  [](const auto &item) { return item.second.second < 0; })) {
    truth.status = TRUTH_UNRECOVERABLE;
    return truth;
  }
  std::map<int, std::vector<int>> recoGroups;
  for (const auto &target : lineageTargets)
    recoGroups[target.second.first].push_back(target.second.second);
  if (recoGroups.size() != 2 || recoGroups[first->first].size() != 2 ||
      recoGroups[second->first].size() != 2) {
    truth.status = TRUTH_UNRECOVERABLE;
    return truth;
  }
  truth.pair1a = recoGroups[first->first][0];
  truth.pair1b = recoGroups[first->first][1];
  truth.pair2a = recoGroups[second->first][0];
  truth.pair2b = recoGroups[second->first][1];
  truth.recoverable = true;
  truth.partitionValid = true;
  truth.status = TRUTH_RECOVERABLE;

  auto truthPairP4 = [&](const std::vector<int> &group, P4 &pair) {
    if (group.size() != 2)
      return false;
    for (int gen : group)
      if (!validIndex(gen, genPt.size()) || !validIndex(gen, genEta.size()) ||
          !validIndex(gen, genPhi.size()) || !validIndex(gen, genMass.size()) ||
          !finitePositive(genPt[gen]) || !std::isfinite(genEta[gen]) ||
          !std::isfinite(genPhi[gen]) || !std::isfinite(genMass[gen]))
        return false;
    pair = P4(genPt[group[0]], genEta[group[0]], genPhi[group[0]],
              genMass[group[0]]) +
           P4(genPt[group[1]], genEta[group[1]], genPhi[group[1]],
              genMass[group[1]]);
    return std::isfinite(pair.M()) && std::isfinite(pair.Pt());
  };
  P4 firstPair(0.f, 0.f, 0.f, 0.f);
  P4 secondPair(0.f, 0.f, 0.f, 0.f);
  const bool firstValid = truthPairP4(first->second, firstPair);
  const bool secondValid = truthPairP4(second->second, secondPair);
  if (firstValid || secondValid) {
    const float firstDistance = firstValid
                                    ? std::abs(firstPair.M() - Z_MASS)
                                    : std::numeric_limits<float>::infinity();
    const float secondDistance = secondValid
                                     ? std::abs(secondPair.M() - Z_MASS)
                                     : std::numeric_limits<float>::infinity();
    truth.referencePair = firstDistance <= secondDistance ? 0 : 1;
    truth.referencePt =
        truth.referencePair == 0 ? firstPair.Pt() : secondPair.Pt();
  }
  return truth;
}

inline bool candidateCorrectZH(const Candidate &candidate,
                               const TruthResult &truth) {
  return truth.recoverable &&
         samePair(candidate.z1, candidate.z2, truth.pair1a, truth.pair1b);
}

inline bool candidateCorrectZZ(const Candidate &candidate,
                               const TruthResult &truth) {
  if (!truth.partitionValid)
    return false;
  return canonicalPartition(candidate.z1, candidate.z2, candidate.x1,
                            candidate.x2) ==
         canonicalPartition(truth.pair1a, truth.pair1b, truth.pair2a,
                            truth.pair2b);
}

inline RVecI liveStyleX(const RVecF &pt, const RVecI &pdgId,
                        const RVecI &tightMask, int z1, int z2) {
  const size_t n = std::min({pt.size(), pdgId.size(), tightMask.size()});
  int best1 = -1;
  int best2 = -1;
  float bestLead = -1.f;
  float bestSublead = -1.f;
  for (size_t i = 0; i < n; ++i) {
    if (static_cast<int>(i) == z1 || static_cast<int>(i) == z2 ||
        !tightMask[i] || !finitePositive(pt[i]))
      continue;
    for (size_t j = i + 1; j < n; ++j) {
      if (static_cast<int>(j) == z1 || static_cast<int>(j) == z2 ||
          !tightMask[j] || !finitePositive(pt[j]) ||
          pdgId[i] * pdgId[j] >= 0)
        continue;
      const float lead = std::max(pt[i], pt[j]);
      const float sublead = std::min(pt[i], pt[j]);
      if (lead < 10.f || sublead < 10.f)
        continue;
      if (lead > bestLead || (lead == bestLead && sublead > bestSublead)) {
        bestLead = lead;
        bestSublead = sublead;
        if (pt[j] > pt[i]) {
          best1 = static_cast<int>(j);
          best2 = static_cast<int>(i);
        } else {
          best1 = static_cast<int>(i);
          best2 = static_cast<int>(j);
        }
      }
    }
  }
  return {best1, best2};
}

template <typename ElectronMaskType, typename MuonMaskType>
inline RVecI combineTightMask(const RVecI &pdgId,
                              const RVec<ElectronMaskType> &tightElectron,
                              const RVec<MuonMaskType> &tightMuon) {
  RVecI mask(pdgId.size(), 0);
  for (size_t i = 0; i < pdgId.size(); ++i) {
    if (std::abs(pdgId[i]) == 11 && i < tightElectron.size())
      mask[i] = tightElectron[i] != 0;
    else if (std::abs(pdgId[i]) == 13 && i < tightMuon.size())
      mask[i] = tightMuon[i] != 0;
  }
  return mask;
}

inline EventResult analyzeEvent(
    const RVecF &leptonPt, const RVecF &leptonEta,
    const RVecF &leptonPhi, const RVecI &leptonPdgId,
    const RVecI &tightMask, const RVecF &sourcePt,
    const RVecF &sourceEta, const RVecF &sourcePhi,
    const RVecI &sourcePdgId, const RVecI &sourceElectronIdx,
    const RVecI &sourceMuonIdx, const RVecF &electronPt,
    const RVecF &electronEta, const RVecF &electronEnergyErr,
    const RVecI &electronGenIdx, const RVecI &electronFsrIdx,
    const RVecF &muonPt, const RVecF &muonPtErr,
    const RVecI &muonGenIdx, const RVecI &muonFsrIdx,
    const RVecF &fsrPt, const RVecF &fsrEta, const RVecF &fsrPhi,
    const RVecI &fsrElectronIdx, const RVecI &fsrMuonIdx,
    const RVecI &genPdgId, const RVecI &genMother,
    const RVecI &genStatusFlags, const RVecF &genPt,
    const RVecF &genEta, const RVecF &genPhi, const RVecF &genMass,
    float metPt) {
  EventResult result;
  result.quartet = buildQuartet(leptonPt, leptonPdgId, tightMask);
  result.quartetValid = result.quartet.size() == 4;
  result.objectBase =
      passesObjectBase(leptonPt, leptonPdgId, result.quartet);
  result.topology = topologyCode(leptonPdgId, result.quartet);
  result.minPairMass = quartetMinPairMass(
      leptonPt, leptonEta, leptonPhi, leptonPdgId, result.quartet);
  result.physBase =
      result.objectBase && result.minPairMass > 12.f;

  if (result.quartetValid) {
    P4 four(0.f, 0.f, 0.f, 0.f);
    bool first = true;
    for (int idx : result.quartet) {
      const P4 object =
          p4(leptonPt[idx], leptonEta[idx], leptonPhi[idx], leptonPdgId[idx]);
      if (first) {
        four = object;
        first = false;
      } else {
        four += object;
      }
    }
    result.m4l = four.M();
  }

  RVecI sourceMap = coherentSourceMap(
      leptonPt, leptonEta, leptonPhi, leptonPdgId, sourcePt, sourceEta,
      sourcePhi, sourcePdgId, result.quartet);
  bool originsValid = sourceMap.size() == result.quartet.size() &&
                      result.quartet.size() == 4;
  result.sourceAlignmentFailure = result.quartet.size() == 4 ? 2 : 1;
  for (int source : sourceMap) {
    if (!validIndex(source, sourcePt.size()) ||
        !finitePositive(sourcePt[source]) ||
        !validIndex(source, sourcePdgId.size()) ||
        !validIndex(source, sourceElectronIdx.size()) ||
        !validIndex(source, sourceMuonIdx.size())) {
      originsValid = false;
      result.sourceAlignmentFailure = 3;
      break;
    }
    if (std::abs(sourcePdgId[source]) == 11) {
      originsValid = originsValid && sourceMuonIdx[source] < 0 &&
                     validIndex(sourceElectronIdx[source], electronPt.size());
    } else if (std::abs(sourcePdgId[source]) == 13) {
      originsValid = originsValid && sourceElectronIdx[source] < 0 &&
                     validIndex(sourceMuonIdx[source], muonPt.size());
    } else {
      originsValid = false;
    }
    if (!originsValid) {
      result.sourceAlignmentFailure = 3;
      break;
    }
  }
  result.sourceAlignmentValid = originsValid;
  if (originsValid)
    result.sourceAlignmentFailure = 0;
  if (!originsValid)
    sourceMap.clear();

  result.candidates = enumerateCandidates(
      leptonPt, leptonEta, leptonPhi, leptonPdgId, result.quartet, sourceMap,
      sourcePdgId, sourceElectronIdx, sourceMuonIdx, electronPt, electronEta,
      electronEnergyErr, muonPt, muonPtErr, electronFsrIdx, muonFsrIdx, fsrPt,
      fsrEta, fsrPhi, fsrElectronIdx, fsrMuonIdx);
  result.nValidCandidates = result.candidates.size();
  std::set<int> partitions;
  for (const auto &candidate : result.candidates)
    partitions.insert(candidate.partition);
  result.nDistinctPartitions = partitions.size();
  result.resolutionScoresValid =
      algorithmScoresValid(result.candidates, RESOLUTION_PULL);
  result.fsrScoresValid =
      algorithmScoresValid(result.candidates, FSR_NEAREST_MZ);

  result.zhTruth = buildZHTruth(
      result.quartet, sourceMap, sourcePdgId, sourceElectronIdx,
      sourceMuonIdx, electronGenIdx, muonGenIdx, genPdgId, genMother,
      genStatusFlags, genPt);
  result.zzTruth = buildZZTruth(
      result.quartet, sourceMap, sourcePdgId, sourceElectronIdx,
      sourceMuonIdx, electronGenIdx, muonGenIdx, genPdgId, genMother,
      genStatusFlags, genPt, genEta, genPhi, genMass);

  for (int algorithm = 0; algorithm < N_ALGORITHMS; ++algorithm) {
    const int selected = selectCandidate(result.candidates, algorithm);
    const auto scores = scoreSummary(result.candidates, algorithm);
    result.selectedCandidate.push_back(selected);
    result.selectedScore.push_back(scores[0]);
    result.secondScore.push_back(scores[1]);
    result.scoreGap.push_back(scores[2]);
    const bool valid = validIndex(selected, result.candidates.size());
    result.algorithmValid.push_back(valid ? 1 : 0);
    if (!valid) {
      result.selectedZ1.push_back(-1);
      result.selectedZ2.push_back(-1);
      result.selectedX1.push_back(-1);
      result.selectedX2.push_back(-1);
      result.selectedZFlavor.push_back(0);
      result.selectedMZ.push_back(INVALID);
      result.selectedMX.push_back(INVALID);
      result.selectedPtZ.push_back(INVALID);
      result.selectedPtX.push_back(INVALID);
      result.selectedDrZ.push_back(INVALID);
      result.selectedDrX.push_back(INVALID);
      result.selectedXFlavor.push_back(0);
      result.region.push_back(REGION_OUTSIDE);
      result.zhCorrect.push_back(0);
      result.zzCorrect.push_back(0);
      continue;
    }
    const Candidate &candidate = result.candidates[selected];
    result.selectedZ1.push_back(candidate.z1);
    result.selectedZ2.push_back(candidate.z2);
    result.selectedX1.push_back(candidate.x1);
    result.selectedX2.push_back(candidate.x2);
    result.selectedZFlavor.push_back(candidate.zFlavor);
    result.selectedMZ.push_back(candidate.mZ);
    result.selectedMX.push_back(candidate.mX);
    result.selectedPtZ.push_back(candidate.ptZ);
    result.selectedPtX.push_back(candidate.ptX);
    result.selectedDrZ.push_back(candidate.drZ);
    result.selectedDrX.push_back(candidate.drX);
    result.selectedXFlavor.push_back(candidate.xFlavor);
    result.region.push_back(regionCode(candidate, metPt, result.m4l));
    result.zhCorrect.push_back(candidateCorrectZH(candidate, result.zhTruth));
    result.zzCorrect.push_back(candidateCorrectZZ(candidate, result.zzTruth));
  }

  if (!result.candidates.empty()) {
    const int nearest = result.selectedCandidate[NEAREST_MZ];
    if (validIndex(nearest, result.candidates.size())) {
      const Candidate &candidate = result.candidates[nearest];
      const auto liveX = liveStyleX(leptonPt, leptonPdgId, tightMask,
                                    candidate.z1, candidate.z2);
      result.xComplementIdentical =
          liveX.size() == 2 &&
          samePair(liveX[0], liveX[1], candidate.x1, candidate.x2);
      if (result.xComplementIdentical)
        result.xDifferenceReason = 0;
      else if (liveX.size() != 2 || liveX[0] < 0 || liveX[1] < 0)
        result.xDifferenceReason = 1;
      else
        result.xDifferenceReason = 2;
    }
  }
  return result;
}

inline RVecF algorithmAxis() {
  RVecF out;
  for (int algorithm = 0; algorithm < N_ALGORITHMS; ++algorithm)
    out.push_back(static_cast<float>(algorithm));
  return out;
}

inline RVecF intToFloat(const RVecI &values) {
  RVecF out;
  out.reserve(values.size());
  for (int value : values)
    out.push_back(static_cast<float>(value));
  return out;
}

inline RVecF correctnessAxis(const EventResult &event, bool useZH) {
  RVecF out(N_ALGORITHMS, -2.f);
  const bool recoverable =
      useZH ? event.zhTruth.recoverable : event.zzTruth.partitionValid;
  const RVecI &correct = useZH ? event.zhCorrect : event.zzCorrect;
  for (int algorithm = 0; algorithm < N_ALGORITHMS; ++algorithm) {
    if (!validIndex(algorithm, event.algorithmValid.size()) ||
        !event.algorithmValid[algorithm]) {
      out[algorithm] = -2.f; // reconstruction score unavailable
    } else if (!recoverable) {
      out[algorithm] = -1.f; // truth denominator unavailable
    } else if (validIndex(algorithm, correct.size())) {
      out[algorithm] = correct[algorithm] ? 1.f : 0.f;
    }
  }
  return out;
}

// Joint event-level correctness relative to the live nearest-mZ baseline.
// Unlike a subtraction of marginal efficiencies, this preserves migrations
// where one method fixes (gain) or breaks (loss) the same event.
inline RVecF gainLossAxis(const EventResult &event, bool useZH) {
  RVecF out(N_ALGORITHMS, -2.f);
  const bool recoverable =
      useZH ? event.zhTruth.recoverable : event.zzTruth.partitionValid;
  const RVecI &correct = useZH ? event.zhCorrect : event.zzCorrect;
  const bool baselineAvailable =
      validIndex(NEAREST_MZ, event.algorithmValid.size()) &&
      event.algorithmValid[NEAREST_MZ] &&
      validIndex(NEAREST_MZ, correct.size());
  for (int algorithm = 0; algorithm < N_ALGORITHMS; ++algorithm) {
    if (!baselineAvailable ||
        !validIndex(algorithm, event.algorithmValid.size()) ||
        !event.algorithmValid[algorithm] ||
        !validIndex(algorithm, correct.size())) {
      out[algorithm] = -2.f; // baseline or comparator unavailable
    } else if (!recoverable) {
      out[algorithm] = -1.f; // truth denominator unavailable
    } else {
      const bool baselineCorrect = correct[NEAREST_MZ];
      const bool comparatorCorrect = correct[algorithm];
      if (!baselineCorrect && !comparatorCorrect)
        out[algorithm] = 0.f; // both wrong
      else if (baselineCorrect && !comparatorCorrect)
        out[algorithm] = 1.f; // comparator loss
      else if (!baselineCorrect && comparatorCorrect)
        out[algorithm] = 2.f; // comparator gain
      else
        out[algorithm] = 3.f; // both correct
    }
  }
  return out;
}

inline RVecF constantWeights(float value) {
  return RVecF(N_ALGORITHMS, value);
}

inline RVecF truthPtAxis(const EventResult &event, bool useZH) {
  return RVecF(N_ALGORITHMS,
               useZH ? event.zhTruth.referencePt : event.zzTruth.referencePt);
}

inline RVecF responsePtZ(const EventResult &event, bool useZH) {
  const float truthPt =
      useZH ? event.zhTruth.referencePt : event.zzTruth.referencePt;
  RVecF out(N_ALGORITHMS, INVALID);
  if (!finitePositive(truthPt))
    return out;
  for (int algorithm = 0; algorithm < N_ALGORITHMS; ++algorithm)
    if (validIndex(algorithm, event.selectedPtZ.size()) &&
        finitePositive(event.selectedPtZ[algorithm]))
      out[algorithm] =
          (event.selectedPtZ[algorithm] - truthPt) / truthPt;
  return out;
}

} // namespace PairingStudy

#endif
