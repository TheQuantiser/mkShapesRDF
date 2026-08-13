"""Declarative, sparse DY-to-ZZ closure bridge built from a vendored contract."""

from __future__ import annotations

import json
import os
from collections import OrderedDict
from pathlib import Path


HERE = Path(__file__).resolve().parent
REFERENCE_JSON = HERE / "year_config.json"
STARTING_SHA = "3659c2e930d58b8a3df387ca9080c9443bb528e8"
SUPPORTED_ERAS = ("2022", "2022EE", "2023", "2023BPix", "2024")
COMBINED_ERAS = {
    "combined_2022": ("2022", "2022EE"),
    "combined_2023": ("2023", "2023BPix"),
    "2024": ("2024",),
    "ALL_RUN3": SUPPORTED_ERAS,
}

TRIGGER_OR = (
    "(Trigger_ElMu || Trigger_sngMu || Trigger_dblMu || "
    "Trigger_sngEl || Trigger_dblEl)"
)
PRESELECTION = f"{TRIGGER_OR} && nLepton >= 2 && L2TightLeading2 && nJetInHorn == 0"
Z_VALID = "hasValidZ0"
Z_CANDIDATE_10 = (
    "Alt(Lepton_pt, Alt(Z0_idx, 0, -1), -999.f) > 10."
    " && Alt(Lepton_pt, Alt(Z0_idx, 1, -1), -999.f) > 10."
)
Z_WINDOW = "abs(Z0_mass - 91.1876) < 15."
ANCHOR = f"{Z_VALID} && ({Z_CANDIDATE_10}) && ({Z_WINDOW}) && PassesAnchor2lPt"

FOURL_VALID = (
    "hasValidZ0 && hasValidX && selectedIndicesDistinct && X_mass > 4."
    " && Alt(Lepton_pt, Alt(X_idx, 0, -1), -999.f) > 10."
    " && Alt(Lepton_pt, Alt(X_idx, 1, -1), -999.f) > 10."
    " && m4l > 0. && sumLeptonCharge == 0"
)
FOURL_BRIDGE = f"({FOURL_VALID}) && ({Z_WINDOW}) && Passes4lOrderedPt"

# These are formatted exactly as the live category_config.py contract.  Keep
# them separate from the simplified bridge vocabulary so reference-equivalence
# tests catch upstream drift instead of accepting a merely equivalent rewrite.
REFERENCE_DY_PARENT = (
    f"{TRIGGER_OR} && nLepton >= 2 && hasValidZ0 && Z0_mass > 30."
    " && Alt(Lepton_pt, Alt(Z0_idx, 0, -1), -999.f) > 10"
    " && Alt(Lepton_pt, Alt(Z0_idx, 1, -1), -999.f) > 10"
)
REFERENCE_FOURL_PARENT = (
    f"{REFERENCE_DY_PARENT} && nLepton >= 4 && hasValidX && selectedIndicesDistinct"
    " && X_mass > 4. && Alt(Lepton_pt, Alt(X_idx, 0, -1), -999.f) > 10"
    " && Alt(Lepton_pt, Alt(X_idx, 1, -1), -999.f) > 10 && m4l > 0. && sumLeptonCharge == 0"
)

ZZ_TERMS = OrderedDict(
    (
        ("met", "PuppiMET_pt < 35."),
        ("xmass", "X_mass > 75. && X_mass < 105."),
        ("xflavor", "X_isSF"),
        ("bveto", "physicalBtagVeto"),
        ("lowmass", "minSelectedPairMass > 12."),
        ("fifth", "fifthLeptonVeto"),
        ("fourlpt", "Passes4lOrderedPt"),
        ("zwindow", Z_WINDOW),
    )
)


def _and(*terms):
    return " && ".join(f"({term})" for term in terms if term and term != "1") or "1"


REFERENCE_PHYSICAL_COMMON = (
    f"{REFERENCE_FOURL_PARENT} && fifthLeptonVeto && minSelectedPairMass > 12."
    f" && physicalBtagVeto && {Z_WINDOW} && Passes4lOrderedPt"
)
EXACT_ZZCR = (
    f"{REFERENCE_PHYSICAL_COMMON} && X_isSF"
    " && X_mass > 75. && X_mass < 105. && PuppiMET_pt < 35."
)
CURRENT_DY = f"({REFERENCE_DY_PARENT}) && Passes2lOrderedPt"
CURRENT_DY_ENRICHED = f"({CURRENT_DY}) && ({Z_WINDOW})"
DY_EVENTPT = _and(
    "hasValidZ0",
    "Z0_mass > 30.",
    "Alt(Lepton_pt, Alt(Z0_idx, 0, -1), -999.f) > 10.",
    "Alt(Lepton_pt, Alt(Z0_idx, 1, -1), -999.f) > 10.",
    "PassesAnchor2lPt",
)

PRIMARY_STAGES = OrderedDict(
    (
        ("S0_ZZCR", EXACT_ZZCR),
        ("S1_NO_MET", _and(FOURL_VALID, *list(ZZ_TERMS.values())[1:])),
        ("S2_NO_XMASS", _and(FOURL_VALID, *list(ZZ_TERMS.values())[2:])),
        ("S3_NO_XFLAVOR", _and(FOURL_VALID, *list(ZZ_TERMS.values())[3:])),
        ("S4_NO_BVETO", _and(FOURL_VALID, *list(ZZ_TERMS.values())[4:])),
        ("S5_NO_LOWMASS", _and(FOURL_VALID, *list(ZZ_TERMS.values())[5:])),
        ("S6_NO_FIFTHVETO", _and(FOURL_VALID, *list(ZZ_TERMS.values())[6:])),
        ("S7_FOURL_BRIDGE", FOURL_BRIDGE),
        ("S8_Z_BRIDGE", ANCHOR),
        ("D0_DY_ENRICHED_CURRENT", CURRENT_DY_ENRICHED),
        ("D1_DY_ALL_CURRENT", CURRENT_DY),
        ("D2_DY_ALL_EVENTPT", DY_EVENTPT),
    )
)

NMINUS1 = OrderedDict(
    (
        ("N1_NO_XMASS", _and(FOURL_VALID, *(v for k, v in ZZ_TERMS.items() if k != "xmass"))),
        ("N1_NO_XFLAVOR", _and(FOURL_VALID, *(v for k, v in ZZ_TERMS.items() if k != "xflavor"))),
        ("N1_NO_BVETO", _and(FOURL_VALID, *(v for k, v in ZZ_TERMS.items() if k != "bveto"))),
        ("N1_NO_LOWMASS", _and(FOURL_VALID, *(v for k, v in ZZ_TERMS.items() if k != "lowmass"))),
        ("N1_NO_FIFTHVETO", _and(FOURL_VALID, *(v for k, v in ZZ_TERMS.items() if k != "fifth"))),
        ("N1_NO_4LPT", _and(FOURL_VALID, *(v for k, v in ZZ_TERMS.items() if k != "fourlpt"))),
        ("N1_NO_ZWINDOW", _and(FOURL_VALID, *(v for k, v in ZZ_TERMS.items() if k != "zwindow"))),
    )
)

FLAVOR_SPLITS = OrderedDict((("ZEE", "Z0_isEE"), ("ZMM", "Z0_isMM")))
TOPOLOGY_SPLITS = OrderedDict(
    (
        ("4E", "Z0_isEE && X_isEE"),
        ("4MU", "Z0_isMM && X_isMM"),
        ("2E2MU", "(Z0_isEE && X_isMM) || (Z0_isMM && X_isEE)"),
    )
)
EXTRA_SPLITS = OrderedDict(
    (("EXTRA0", "nExtraTight10 == 0"), ("EXTRA1", "nExtraTight10 == 1"), ("EXTRA2P", "nExtraTight10 >= 2"))
)
TRIGGER_SPLITS = OrderedDict(
    (
        ("TRGPRIO_ELMU", "triggerFamilyPriority == 1"),
        ("TRGPRIO_SINGLEMU", "triggerFamilyPriority == 2"),
        ("TRGPRIO_DOUBLEMU", "triggerFamilyPriority == 3"),
        ("TRGPRIO_SINGLEEL", "triggerFamilyPriority == 4"),
        ("TRGPRIO_DOUBLEEL", "triggerFamilyPriority == 5"),
    )
)
STREAM_SPLITS = OrderedDict(
    (
        ("STREAM_MUONEG", "streamPriority_MuonEG"),
        ("STREAM_MUON", "streamPriority_Muon"),
        ("STREAM_EGAMMA", "streamPriority_EGamma"),
    )
)

MIGRATION = OrderedDict(
    (
        ("PT_ENRICHED_CURRENT_ONLY", _and(CURRENT_DY_ENRICHED, "!PassesAnchor2lPt")),
        ("PT_ENRICHED_EVENTPT_ONLY", _and(ANCHOR, "!Passes2lOrderedPt")),
        ("PT_BROAD_CURRENT_ONLY", _and(CURRENT_DY, "!PassesAnchor2lPt")),
        ("PT_BROAD_EVENTPT_ONLY", _and(DY_EVENTPT, "!Passes2lOrderedPt")),
    )
)

FOURL_STAGES = frozenset(name for name in PRIMARY_STAGES if name.startswith("S") and name != "S8_Z_BRIDGE")
BVETO_STAGES = frozenset(("S0_ZZCR", "S1_NO_MET", "S2_NO_XMASS", "S3_NO_XFLAVOR"))
WEIGHT_SENTINELS = ("S0_ZZCR", "S7_FOURL_BRIDGE", "S8_Z_BRIDGE", "D0_DY_ENRICHED_CURRENT", "D1_DY_ALL_CURRENT")


def nominal_factor(stage):
    if stage in FOURL_STAGES or stage.startswith("N1_") or stage.startswith("S0_") or stage.startswith("S7_"):
        factor = "SelectedLeptonSF_ZX*TriggerSF_ZX"
        if stage in BVETO_STAGES or (stage.startswith("N1_") and stage != "N1_NO_BVETO"):
            factor += "*BTagVetoSF"
        return factor
    return "SelectedLeptonSF_Z*TriggerSF_Z"


def build_categories(profile="default"):
    if profile not in ("default", "focused_cross"):
        raise ValueError("CLOSURE_PROFILE must be default or focused_cross")
    cuts = OrderedDict(PRIMARY_STAGES)
    cuts.update(NMINUS1)
    for suffix, expr in EXTRA_SPLITS.items():
        cuts[f"S8_{suffix}"] = _and(ANCHOR, expr)
    for parent in ("S8_Z_BRIDGE", "D0_DY_ENRICHED_CURRENT", "D1_DY_ALL_CURRENT"):
        for suffix, expr in FLAVOR_SPLITS.items():
            cuts[f"{parent}_{suffix}"] = _and(PRIMARY_STAGES[parent], expr)
    for parent in ("S0_ZZCR", "S7_FOURL_BRIDGE"):
        for suffix, expr in TOPOLOGY_SPLITS.items():
            cuts[f"{parent}_{suffix}"] = _and(PRIMARY_STAGES[parent], expr)
    for parent in ("S8_Z_BRIDGE", "D0_DY_ENRICHED_CURRENT"):
        for suffix, expr in TRIGGER_SPLITS.items():
            cuts[f"{parent}_{suffix}"] = _and(PRIMARY_STAGES[parent], expr)
        for suffix, expr in STREAM_SPLITS.items():
            cuts[f"{parent}_{suffix}"] = _and(PRIMARY_STAGES[parent], expr)
    cuts.update(MIGRATION)
    if profile == "focused_cross":
        cuts["S8_FOCUSED_ZEE_EGAMMA"] = _and(ANCHOR, "Z0_isEE", "streamPriority_EGamma")
        cuts["S8_FOCUSED_ZMM_MUON"] = _and(ANCHOR, "Z0_isMM", "streamPriority_Muon")
    return cuts


def load_live_json():
    with REFERENCE_JSON.open(encoding="utf-8") as handle:
        return json.load(handle)


def supported_eras_from_live():
    return tuple(load_live_json()["years"])


def assert_live_era_contract():
    live = supported_eras_from_live()
    if live != SUPPORTED_ERAS:
        raise RuntimeError(f"Supported-era drift: study={SUPPORTED_ERAS}, vendored catalog={live}")
    return live


assert_live_era_contract()
