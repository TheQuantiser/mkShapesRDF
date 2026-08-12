#ifndef FIXED_WP_BTAG_SF
#define FIXED_WP_BTAG_SF

#include <ROOT/RVec.hxx>
#include <TFile.h>
#include <TH2F.h>
#include "correction.h"

#include <algorithm>
#include <cmath>
#include <map>
#include <memory>
#include <mutex>
#include <stdexcept>
#include <string>

namespace FixedWPBTag {

struct Payload {
  std::unique_ptr<correction::CorrectionSet> corrections;
  std::unique_ptr<TH2F> bEff;
  std::unique_ptr<TH2F> cEff;
  std::unique_ptr<TH2F> lightEff;
};

std::shared_ptr<Payload> loadPayload(const std::string &mapPath,
                                     const std::string &correctionPath) {
  static std::mutex mutex;
  static std::map<std::string, std::shared_ptr<Payload>> cache;
  const std::string key = mapPath + "|" + correctionPath;
  std::lock_guard<std::mutex> lock(mutex);
  auto found = cache.find(key);
  if (found != cache.end())
    return found->second;

  auto payload = std::make_shared<Payload>();
  payload->corrections = correction::CorrectionSet::from_file(correctionPath);
  if (!payload->corrections)
    throw std::runtime_error("Cannot load BTV payload " + correctionPath);

  std::unique_ptr<TFile> input(TFile::Open(mapPath.c_str(), "READ"));
  if (!input || input->IsZombie())
    throw std::runtime_error("Cannot open b-tag efficiency map " + mapPath);
  auto clone = [&](const char *name) -> std::unique_ptr<TH2F> {
    auto *source = dynamic_cast<TH2F *>(input->Get(name));
    if (!source)
      throw std::runtime_error("Missing histogram " + std::string(name) +
                               " in " + mapPath);
    auto *copy = dynamic_cast<TH2F *>(source->Clone());
    if (!copy)
      throw std::runtime_error("Cannot clone histogram " + std::string(name));
    copy->SetDirectory(nullptr);
    return std::unique_ptr<TH2F>(copy);
  };
  payload->bEff = clone("bjet_eff");
  payload->cEff = clone("cjet_eff");
  payload->lightEff = clone("ljet_eff");
  cache.emplace(key, payload);
  return payload;
}

float efficiency(const Payload &payload, int flavor, float pt, float eta) {
  const TH2F *hist = flavor == 5   ? payload.bEff.get()
                     : flavor == 4 ? payload.cEff.get()
                                   : payload.lightEff.get();
  if (!hist)
    throw std::runtime_error("Null b-tag efficiency histogram");
  const double xmax = hist->GetXaxis()->GetXmax();
  const double xmin = hist->GetXaxis()->GetXmin();
  const double safePt = std::min<double>(
      std::max<double>(pt, xmin + 1.e-4), xmax - 1.e-4);
  const int xbin = hist->GetXaxis()->FindBin(safePt);
  const int ybin = hist->GetYaxis()->FindBin(eta);
  const float value = hist->GetBinContent(xbin, ybin);
  if (!std::isfinite(value) || value < 0.f || value > 1.f)
    throw std::runtime_error("Invalid fixed-WP b-tag efficiency");
  return value;
}

template <typename IndexT>
bool veto(const ROOT::RVecF &cleanPt, const ROOT::RVecF &cleanEta,
          const ROOT::VecOps::RVec<IndexT> &cleanJetIdx, const ROOT::RVecF &jetBtag,
          float wp, float ptMin = 20.f) {
  const size_t n = std::min({cleanPt.size(), cleanEta.size(), cleanJetIdx.size()});
  for (size_t i = 0; i < n; ++i) {
    if (cleanPt[i] <= ptMin || std::abs(cleanEta[i]) >= 2.5f)
      continue;
    const long long rawIdx = static_cast<long long>(cleanJetIdx[i]);
    if (rawIdx < 0 || static_cast<size_t>(rawIdx) >= jetBtag.size())
      continue;
    if (jetBtag[rawIdx] > wp)
      return false;
  }
  return true;
}

template <typename IndexT, typename FlavorT>
float eventSF(const ROOT::RVecF &cleanPt, const ROOT::RVecF &cleanEta,
              const ROOT::VecOps::RVec<IndexT> &cleanJetIdx,
              const ROOT::VecOps::RVec<FlavorT> &jetFlavor,
              const ROOT::RVecF &jetBtag, const std::string &mapPath,
              const std::string &correctionPath, const std::string &tagger,
              const std::string &systematic, int flavorGroup,
              float expectedWP) {
  auto payload = loadPayload(mapPath, correctionPath);
  auto wpCorrection = payload->corrections->at(tagger + "_wp_values");
  auto sfCorrection = payload->corrections->at(
      tagger + (flavorGroup == 0 ? "_light" : "_comb"));
  if (!wpCorrection || !sfCorrection)
    throw std::runtime_error("Missing fixed-WP BTV correction for " + tagger);
  const float wp = static_cast<float>(wpCorrection->evaluate({"L"}));
  if (!std::isfinite(wp) || std::abs(wp - expectedWP) > 5.e-5f)
    throw std::runtime_error("Configured and POG loose b-tag WPs disagree");

  const size_t n = std::min({cleanPt.size(), cleanEta.size(), cleanJetIdx.size()});
  double product = 1.;
  for (size_t i = 0; i < n; ++i) {
    if (cleanPt[i] <= 20.f || std::abs(cleanEta[i]) >= 2.5f)
      continue;
    const long long rawIdx = static_cast<long long>(cleanJetIdx[i]);
    if (rawIdx < 0 || static_cast<size_t>(rawIdx) >= jetBtag.size() ||
        static_cast<size_t>(rawIdx) >= jetFlavor.size())
      continue;
    const int rawFlavor = std::abs(static_cast<int>(jetFlavor[rawIdx]));
    const int flavor = rawFlavor == 5 ? 5 : (rawFlavor == 4 ? 4 : 0);
    if ((flavorGroup == 0 && flavor != 0) ||
        (flavorGroup != 0 && flavor == 0))
      continue;

    const double sf = sfCorrection->evaluate(
        {systematic, "L", flavor, std::abs(cleanEta[i]), cleanPt[i]});
    if (!std::isfinite(sf))
      throw std::runtime_error("Non-finite fixed-WP b-tag SF");
    if (jetBtag[rawIdx] > wp) {
      product *= sf;
      continue;
    }
    const float eff = efficiency(*payload, flavor, cleanPt[i], cleanEta[i]);
    // Match the established PlotsConfigurationsRun3 fixed-WP convention:
    // an untagged jet in a map bin whose efficiency is exactly one does not
    // contribute a veto-SF factor.  The analytic (1-eff*SF)/(1-eff) form is
    // undefined there, while efficiency() already rejects values above one.
    if (eff == 1.f)
      continue;
    product *= (1. - eff * sf) / (1. - eff);
  }
  if (!std::isfinite(product))
    throw std::runtime_error("Non-finite fixed-WP event b-tag SF");
  return static_cast<float>(product);
}

template <typename IndexT>
int mapOverflowJetCount(const ROOT::RVecF &cleanPt,
                        const ROOT::RVecF &cleanEta,
                        const ROOT::VecOps::RVec<IndexT> &cleanJetIdx) {
  const size_t n = std::min({cleanPt.size(), cleanEta.size(), cleanJetIdx.size()});
  int count = 0;
  for (size_t i = 0; i < n; ++i)
    if (cleanPt[i] > 20.f && std::abs(cleanEta[i]) < 2.5f && cleanPt[i] >= 1000.f)
      ++count;
  return count;
}

} // namespace FixedWPBTag

#endif
