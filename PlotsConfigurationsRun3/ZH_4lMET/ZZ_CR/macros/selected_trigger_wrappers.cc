#ifndef SELECTED_TRIGGER_WRAPPERS
#define SELECTED_TRIGGER_WRAPPERS

#include <ROOT/RVec.hxx>

#include <algorithm>
#include <cmath>
#include <vector>

namespace SelectedTrigger {

using RVecF = ROOT::RVecF;
using RVecI = ROOT::RVecI;

// Result layout: data nominal/down/up, MC nominal, SF nominal/down/up, valid.
RVecF neutralResult() { return {1.f, 1.f, 1.f, 1.f, 1.f, 1.f, 1.f, 0.f}; }

RVecF expose(const RVecF &canonical, int sfOffset) {
  if (canonical.size() <= static_cast<size_t>(sfOffset + 2))
    return neutralResult();
  const float data = canonical[0];
  const float sf = canonical[sfOffset];
  const float mc = (std::isfinite(data) && std::isfinite(sf) && sf != 0.f)
                       ? data / sf
                       : 0.f;
  RVecF out = {canonical[0], canonical[1], canonical[2], mc,
               canonical[sfOffset], canonical[sfOffset + 1],
               canonical[sfOffset + 2], 1.f};
  for (float value : out) {
    if (!std::isfinite(value))
      return neutralResult();
  }
  return out;
}

bool compact(const RVecF &pt, const RVecF &eta, const RVecF &phi,
             const RVecI &pdgId, const std::vector<int> &indices,
             RVecF &outPt, RVecF &outEta, RVecF &outPhi, RVecI &outId) {
  outPt.clear();
  outEta.clear();
  outPhi.clear();
  outId.clear();
  std::vector<int> seen;
  for (const int idx : indices) {
    if (idx < 0 || static_cast<size_t>(idx) >= pt.size() ||
        static_cast<size_t>(idx) >= eta.size() ||
        static_cast<size_t>(idx) >= phi.size() ||
        static_cast<size_t>(idx) >= pdgId.size() ||
        std::find(seen.begin(), seen.end(), idx) != seen.end())
      return false;
    if (std::abs(pdgId[idx]) != 11 && std::abs(pdgId[idx]) != 13)
      return false;
    if (!std::isfinite(pt[idx]) || !std::isfinite(eta[idx]) ||
        !std::isfinite(phi[idx]) || pt[idx] <= 0.f)
      return false;
    seen.push_back(idx);
    outPt.push_back(pt[idx]);
    outEta.push_back(eta[idx]);
    outPhi.push_back(phi[idx]);
    outId.push_back(pdgId[idx]);
  }
  return true;
}

void sortByPt(RVecF &pt, RVecF &eta, RVecF &phi, RVecI &id) {
  const auto order = ROOT::VecOps::Reverse(ROOT::VecOps::Argsort(pt));
  pt = ROOT::VecOps::Take(pt, order);
  eta = ROOT::VecOps::Take(eta, order);
  phi = ROOT::VecOps::Take(phi, order);
  id = ROOT::VecOps::Take(id, order);
}

RVecF exactTwo(const RVecF &pt, const RVecF &eta, const RVecF &phi,
               const RVecI &id, int npv, int runPeriod) {
  if (pt.size() != 2 || eta.size() != 2 || phi.size() != 2 || id.size() != 2)
    return neutralResult();
  const float dEta = eta[0] - eta[1];
  const float dPhi = ROOT::VecOps::DeltaPhi(phi[0], phi[1]);
  const float dR = std::hypot(dEta, dPhi);
  auto data = get_eff(id[0], pt[0], eta[0], id[1], pt[1], eta[1],
                      runPeriod, true);
  auto mc = get_eff(id[0], pt[0], eta[0], id[1], pt[1], eta[1], runPeriod,
                    false);
  auto dz = get_dz_eff(id[0], pt[0], eta[0], id[1], pt[1], eta[1], npv,
                       runPeriod);
  auto global = get_gl_eff(id[0], id[1], runPeriod);
  return expose(get_w(id[0], id[1], data, mc, dz, global,
                      drll_sf(id[0], id[1], dR, runPeriod)),
                12);
}

RVecF exactThreeOrFour(const RVecF &pt, const RVecF &eta, const RVecF &phi,
                       const RVecI &id, int npv, int runPeriod) {
  if (pt.size() == 3)
    return expose(get_l3w(pt, eta, phi, id, npv, runPeriod), 7);
  if (pt.size() == 4)
    return expose(get_nlw(pt, eta, phi, id, npv, runPeriod), 7);
  return neutralResult();
}

RVecF generalizedMany(const RVecF &pt, const RVecF &eta, const RVecF &phi,
                      const RVecI &id, int npv, int runPeriod) {
  const size_t n = std::min({pt.size(), eta.size(), phi.size(), id.size()});
  if (n < 5)
    return neutralResult();

  RVecF dataEvt(7, 0.f), mcEvt(7, 0.f);
  for (int variation = 0; variation < 7; ++variation) {
    double dataDoubleInv = 1.;
    double mcDoubleInv = 1.;
    for (size_t i = 0; i < n; ++i) {
      for (size_t j = i + 1; j < n; ++j) {
        auto data = get_eff(id[i], pt[i], eta[i], id[j], pt[j], eta[j],
                            runPeriod, true);
        auto mc = get_eff(id[i], pt[i], eta[i], id[j], pt[j], eta[j],
                          runPeriod, false);
        auto dz = get_dz_eff(id[i], pt[i], eta[i], id[j], pt[j], eta[j],
                             npv, runPeriod);
        auto global = get_gl_eff(id[i], id[j], runPeriod);
        const float dzData = variation == 0 ? dz[0]
                             : variation == 1 ? dz[1]
                             : variation == 2 ? dz[2]
                                              : (variation < 5 ? dz[variation - 2]
                                                               : dz[0]);
        const float dzMC = variation == 0 ? dz[3]
                           : variation == 1 ? dz[4]
                           : variation == 2 ? dz[5]
                                            : (variation < 5 ? dz[variation + 1]
                                                             : dz[3]);
        const double dProb =
            (data[2][variation] * data[5][variation] +
             (1. - data[2][variation] * data[5][variation]) *
                 data[3][variation] * data[4][variation]) *
            dzData * global[2][variation];
        const double mProb =
            (mc[2][variation] * mc[5][variation] +
             (1. - mc[2][variation] * mc[5][variation]) *
                 mc[3][variation] * mc[4][variation]) *
            dzMC * global[2][variation];
        dataDoubleInv *= 1. - dProb;
        mcDoubleInv *= 1. - mProb;
      }
    }

    double dataSingleInv = 1.;
    double mcSingleInv = 1.;
    for (size_t i = 0; i < n; ++i) {
      const size_t j = (i + 1 < n) ? i + 1 : 0;
      const bool first = i < j;
      const size_t a = first ? i : j;
      const size_t b = first ? j : i;
      auto data = get_eff(id[a], pt[a], eta[a], id[b], pt[b], eta[b],
                          runPeriod, true);
      auto mc = get_eff(id[a], pt[a], eta[a], id[b], pt[b], eta[b],
                        runPeriod, false);
      auto global = get_gl_eff(id[a], id[b], runPeriod);
      const int leg = first ? 0 : 1;
      dataSingleInv *= 1. - data[leg][variation] * global[leg][variation];
      mcSingleInv *= 1. - mc[leg][variation] * global[leg][variation];
    }
    dataEvt[variation] = 1. - dataDoubleInv * dataSingleInv;
    mcEvt[variation] = 1. - mcDoubleInv * mcSingleInv;
  }

  RVecF canonical(10, 0.f);
  for (int i = 0; i < 7; ++i)
    canonical[i] = dataEvt[i];
  canonical[7] = get_sf(dataEvt[0], mcEvt[0]);
  auto uncertainty = get_sf_unc(dataEvt, mcEvt);
  canonical[8] = uncertainty[0];
  canonical[9] = uncertainty[1];
  return expose(canonical, 7);
}

RVecF selectedPairResult(const RVecF &pt, const RVecF &eta, const RVecF &phi,
                         const RVecI &id, const RVecI &idx, int npv,
                         int runPeriod) {
  if (idx.size() < 2)
    return neutralResult();
  RVecF cpt, ceta, cphi;
  RVecI cid;
  if (!compact(pt, eta, phi, id, {idx[0], idx[1]}, cpt, ceta, cphi, cid))
    return neutralResult();
  sortByPt(cpt, ceta, cphi, cid);
  return exactTwo(cpt, ceta, cphi, cid, npv, runPeriod);
}

RVecF selectedFourResult(const RVecF &pt, const RVecF &eta, const RVecF &phi,
                         const RVecI &id, const RVecI &zidx,
                         const RVecI &xidx, int npv, int runPeriod) {
  if (zidx.size() < 2 || xidx.size() < 2)
    return neutralResult();
  RVecF cpt, ceta, cphi;
  RVecI cid;
  if (!compact(pt, eta, phi, id,
               {zidx[0], zidx[1], xidx[0], xidx[1]}, cpt, ceta, cphi, cid))
    return neutralResult();
  sortByPt(cpt, ceta, cphi, cid);
  return exactThreeOrFour(cpt, ceta, cphi, cid, npv, runPeriod);
}

RVecF eventResult(const RVecF &pt, const RVecF &eta, const RVecF &phi,
                  const RVecI &id, int npv, int runPeriod) {
  RVecF cpt, ceta, cphi;
  RVecI cid;
  std::vector<int> indices;
  const size_t n = std::min({pt.size(), eta.size(), phi.size(), id.size()});
  for (size_t i = 0; i < n; ++i) {
    if (std::abs(id[i]) == 11 || std::abs(id[i]) == 13)
      indices.push_back(static_cast<int>(i));
  }
  if (!compact(pt, eta, phi, id, indices, cpt, ceta, cphi, cid) || cpt.size() < 2)
    return neutralResult();
  sortByPt(cpt, ceta, cphi, cid);
  if (cpt.size() == 2)
    return exactTwo(cpt, ceta, cphi, cid, npv, runPeriod);
  if (cpt.size() <= 4)
    return exactThreeOrFour(cpt, ceta, cphi, cid, npv, runPeriod);
  return generalizedMany(cpt, ceta, cphi, cid, npv, runPeriod);
}

float at(const RVecF &result, int index, float fallback = 1.f) {
  return index >= 0 && static_cast<size_t>(index) < result.size()
             ? result[index]
             : fallback;
}

} // namespace SelectedTrigger

#endif
