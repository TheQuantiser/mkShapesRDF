#ifndef ZH4L_VIEWS_H
#define ZH4L_VIEWS_H
#include "objects.cc"
#include <algorithm>
#include <limits>
#include <stdexcept>

namespace ZH4lViews {
using ROOT::RVecI;
using ROOT::RVecF;

template <class Mask>
RVecI indices(const RVecF &pt, const Mask &mask, bool sortPt) {
  if (pt.size() != mask.size()) throw std::runtime_error("Object mask size mismatch");
  RVecI out;
  for (size_t i = 0; i < pt.size(); ++i) if (mask[i]) out.push_back(i);
  if (sortPt) std::stable_sort(out.begin(), out.end(), [&](int a, int b) { return pt[a] > pt[b]; });
  return out;
}

inline bool valid(const RVecI &indices, size_t size) {
  RVecI seen;
  for (int index : indices) {
    if (index < 0 || size_t(index) >= size || std::find(seen.begin(), seen.end(), index) != seen.end()) return false;
    seen.push_back(index);
  }
  return true;
}

template <class T>
ROOT::VecOps::RVec<T> take(const ROOT::VecOps::RVec<T> &values, const RVecI &indices) {
  if (!valid(indices, values.size())) throw std::runtime_error("Invalid source indices in object view");
  return ROOT::VecOps::Take(values, indices);
}

inline RVecI without(const RVecI &members, const RVecI &excluded) {
  RVecI out;
  for (int i : members) if (std::find(excluded.begin(), excluded.end(), i) == excluded.end()) out.push_back(i);
  return out;
}

inline RVecI unite(const RVecI &left, const RVecI &right) {
  RVecI out = left;
  for (int i : right) if (std::find(out.begin(), out.end(), i) == out.end()) out.push_back(i);
  return out;
}

inline RVecI leading(RVecI idx, const RVecF &pt, size_t count) {
  if (!valid(idx,pt.size())) throw std::runtime_error("Invalid quartet source indices");
  std::stable_sort(idx.begin(),idx.end(),[&](int a,int b){return pt[a]>pt[b];});
  if (idx.size()<count) return {};
  idx.resize(count);
  return idx;
}

inline bool orderedPt(const RVecF &pt, const RVecI &indices,
                      const RVecF &thresholds, bool inclusive) {
  if (!valid(indices,pt.size()) || indices.size()!=thresholds.size()) return false;
  RVecF selected=take(pt,indices);
  std::sort(selected.begin(),selected.end(),std::greater<float>());
  for (size_t i=0;i<selected.size();++i)
    if (!std::isfinite(selected[i]) || (inclusive ? selected[i]<thresholds[i] : selected[i]<=thresholds[i])) return false;
  return true;
}

inline bool disjoint(const RVecI &a, const RVecI &b) {
  for (int i : a) if (std::find(b.begin(), b.end(), i) != b.end()) return false;
  return true;
}

inline ROOT::Math::PtEtaPhiMVector momentum(const RVecI &idx, const RVecF &pt,
                                           const RVecF &eta, const RVecF &phi,
                                           const RVecI &pdg) {
  if (!valid(idx,pt.size()) || eta.size()!=pt.size() || phi.size()!=pt.size() || pdg.size()!=pt.size())
    throw std::runtime_error("Incompatible selected lepton kinematics");
  ROOT::Math::PtEtaPhiMVector total;
  for (int i : idx) total += ROOT::Math::PtEtaPhiMVector(pt[i],eta[i],phi[i],FourLepton::lepMass(pdg[i]));
  return total;
}

// Source indices are retained throughout. Membership/order belongs to the
// view; eligibility and ordered-pT boundaries use the established kernels.
inline RVecI pair(const RVecI &pool, const RVecF &pt, const RVecF &eta,
                  const RVecF &phi, const RVecI &pdg,
                  const ROOT::RVecB &ele, const ROOT::RVecB &mu,
                  bool nearestZ, int minPass, float lead, float sublead,
                  int charge, int flavor) {
  if (!valid(pool, pt.size()) || eta.size()!=pt.size() || phi.size()!=pt.size() || pdg.size()!=pt.size()
      || ele.size()!=pt.size() || mu.size()!=pt.size()) throw std::runtime_error("Incompatible lepton view columns");
  RVecI best{-1,-1};
  float distance=1.e9f, bestLead=-1.f, bestSub=-1.f;
  for (size_t a=0; a<pool.size(); ++a) for (size_t b=a+1; b<pool.size(); ++b) {
    int i=pool[a], j=pool[b];
    if (charge && ((pdg[i]*pdg[j]<0) != (charge<0))) continue;
    if (flavor && ((std::abs(pdg[i])==std::abs(pdg[j])) != (flavor>0))) continue;
    RVecI candidate = FourLepton::orderPairByPt(RVecI{i,j},pt);
    if (!FourLepton::pairPassesSelection(candidate,pt,pdg,ele,mu,minPass,lead,sublead)) continue;
    if (nearestZ) {
      float diff=std::abs(FourLepton::pairMass(pt,eta,phi,pdg,candidate)-91.1876f);
      if (diff<distance) { distance=diff; best=candidate; }
    } else if (pt[candidate[0]]>bestLead || (!(pt[candidate[0]]<bestLead) && pt[candidate[1]]>bestSub)) {
      bestLead=pt[candidate[0]]; bestSub=pt[candidate[1]]; best=candidate;
    }
  }
  return best;
}

inline float leptonSF(const RVecI &pdg, const RVecI &idx, const RVecF &ele, const RVecF &mu) {
  if (!valid(idx,pdg.size())) return std::numeric_limits<float>::quiet_NaN();
  float product=1.f;
  for (int i : idx) {
    const auto &sf = std::abs(pdg[i])==11 ? ele : mu;
    if ((std::abs(pdg[i])!=11 && std::abs(pdg[i])!=13) || size_t(i)>=sf.size() || !std::isfinite(sf[i]))
      return std::numeric_limits<float>::quiet_NaN();
    product *= sf[i];
  }
  return product;
}

inline bool allPass(const RVecI &pdg, const RVecI &idx, const ROOT::RVecB &ele, const ROOT::RVecB &mu) {
  if (!valid(idx,pdg.size())) return false;
  for (int i : idx) {
    if (std::abs(pdg[i])==11) { if (size_t(i)>=ele.size() || !ele[i]) return false; }
    else if (std::abs(pdg[i])==13) { if (size_t(i)>=mu.size() || !mu[i]) return false; }
    else return false;
  }
  return true;
}
}
#endif
