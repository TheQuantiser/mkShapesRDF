#ifndef MKSHAPESRDF_DY_ZZ_CLOSURE_HELPERS_CC
#define MKSHAPESRDF_DY_ZZ_CLOSURE_HELPERS_CC

#include <ROOT/RVec.hxx>
#include <algorithm>
#include <cmath>
#include <vector>

namespace ClosureBridge {
using RVecB = ROOT::VecOps::RVec<Bool_t>;
using RVecF = ROOT::VecOps::RVec<float>;
using RVecI = ROOT::VecOps::RVec<int>;

inline bool tightAt(unsigned i, const RVecI& pdgId, const RVecB& tightEle,
                    const RVecB& tightMu) {
  if (i >= pdgId.size()) return false;
  const int flavor = std::abs(pdgId[i]);
  return (flavor == 11 && i < tightEle.size() && tightEle[i]) ||
         (flavor == 13 && i < tightMu.size() && tightMu[i]);
}

inline bool passesAnchor2lPt(const RVecF& pt, const RVecI& pdgId,
                            const RVecB& tightEle, const RVecB& tightMu,
                            float lead, float sublead) {
  std::vector<float> eligible;
  for (unsigned i = 0; i < pt.size() && i < pdgId.size(); ++i)
    if (tightAt(i, pdgId, tightEle, tightMu)) eligible.push_back(pt[i]);
  std::sort(eligible.begin(), eligible.end(), std::greater<float>());
  return eligible.size() >= 2 && eligible[0] > lead && eligible[1] > sublead;
}

inline int nExtraTight10(const RVecF& pt, const RVecI& pdgId,
                         const RVecB& tightEle, const RVecB& tightMu,
                         const RVecI& zidx) {
  int count = 0;
  for (unsigned i = 0; i < pt.size() && i < pdgId.size(); ++i) {
    if (pt[i] <= 10.f || !tightAt(i, pdgId, tightEle, tightMu)) continue;
    if (zidx.size() >= 2 && (static_cast<int>(i) == zidx[0] || static_cast<int>(i) == zidx[1])) continue;
    ++count;
  }
  return count;
}

inline float selectedAbsEta(const RVecF& pt, const RVecF& eta,
                            const RVecI& idx, bool leading) {
  if (idx.size() < 2 || idx[0] < 0 || idx[1] < 0 ||
      static_cast<unsigned>(idx[0]) >= pt.size() ||
      static_cast<unsigned>(idx[1]) >= pt.size() ||
      static_cast<unsigned>(idx[0]) >= eta.size() ||
      static_cast<unsigned>(idx[1]) >= eta.size()) return -999.f;
  const int selected = (pt[idx[0]] >= pt[idx[1]]) == leading ? idx[0] : idx[1];
  return std::abs(eta[selected]);
}

inline float safeAbsRapidity(float pt, float eta, float phi, float mass) {
  if (!(pt >= 0.f) || !std::isfinite(pt) || !std::isfinite(eta) || !std::isfinite(phi) || !std::isfinite(mass)) return -999.f;
  const double pz = pt * std::sinh(eta);
  const double energy = std::sqrt(std::max(0.0, static_cast<double>(mass) * mass + static_cast<double>(pt) * pt + pz * pz));
  if (energy <= std::abs(pz)) return -999.f;
  return std::abs(static_cast<float>(0.5 * std::log((energy + pz) / (energy - pz))));
}

inline float phiEtaStar(float eta1, float phi1, float eta2, float phi2) {
  if (!std::isfinite(eta1) || !std::isfinite(phi1) || !std::isfinite(eta2) || !std::isfinite(phi2)) return -999.f;
  constexpr double pi = 3.14159265358979323846;
  double dphi = std::remainder(static_cast<double>(phi1) - phi2, 2.0 * pi);
  dphi = std::min(pi, std::abs(dphi));
  const double acop = std::max(0.0, pi - dphi);
  const double value = std::tan(0.5 * acop) / std::cosh(0.5 * (static_cast<double>(eta1) - eta2));
  return std::isfinite(value) ? static_cast<float>(value) : -999.f;
}
}  // namespace ClosureBridge
#endif
