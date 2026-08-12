"""Declarative, sparse DY-to-ZZ closure bridge built from a vendored contract."""

from __future__ import annotations

import os
import sys
from collections import OrderedDict
from pathlib import Path


HERE = Path(__file__).resolve().parent
FAMILY_DIR = HERE.parent
if str(FAMILY_DIR) not in sys.path:
    sys.path.insert(0, str(FAMILY_DIR))
from common.eras import load_full_config  # noqa: E402
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
PRESELECTION = f"{TRIGGER_OR} && nLepton >= 2 && passLeading2Tight && noJetInHorn"
Z_VALID = "validZ"
Z_CANDIDATE_10 = (
    "Alt(Lepton_pt, Alt(Z_idx, 0, -1), -999.f) > 10."
    " && Alt(Lepton_pt, Alt(Z_idx, 1, -1), -999.f) > 10."
)
Z_WINDOW = "abs(mZ - 91.1876) < 15."
ANCHOR = f"{Z_VALID} && ({Z_CANDIDATE_10}) && ({Z_WINDOW}) && passAnchor2lPt"

FOURL_VALID = (
    "validZ && validX && validZX && mX > 4."
    " && Alt(Lepton_pt, Alt(X_idx, 0, -1), -999.f) > 10."
    " && Alt(Lepton_pt, Alt(X_idx, 1, -1), -999.f) > 10."
    " && m4l > 0. && q4l == 0"
)
FOURL_BRIDGE = f"({FOURL_VALID}) && ({Z_WINDOW}) && pass4lPt"

# These are formatted exactly as the live category_config.py contract.  Keep
# them separate from the simplified bridge vocabulary so reference-equivalence
# tests catch upstream drift instead of accepting a merely equivalent rewrite.
REFERENCE_DY_PARENT = (
    f"{TRIGGER_OR} && nLepton >= 2 && validZ && mZ > 30."
    " && Alt(Lepton_pt, Alt(Z_idx, 0, -1), -999.f) > 10"
    " && Alt(Lepton_pt, Alt(Z_idx, 1, -1), -999.f) > 10"
)
REFERENCE_FOURL_PARENT = (
    f"{REFERENCE_DY_PARENT} && nLepton >= 4 && validX && validZX"
    " && mX > 4. && Alt(Lepton_pt, Alt(X_idx, 0, -1), -999.f) > 10"
    " && Alt(Lepton_pt, Alt(X_idx, 1, -1), -999.f) > 10 && m4l > 0. && q4l == 0"
)

ZZ_TERMS = OrderedDict(
    (
        ("met", "PuppiMET_pt < 35."),
        ("xmass", "mX > 75. && mX < 105."),
        ("xflavor", "isXSF"),
        ("bveto", "bVeto"),
        ("lowmass", "minMll4l > 12."),
        ("fifth", "veto5l"),
        ("fourlpt", "pass4lPt"),
        ("zwindow", Z_WINDOW),
    )
)


def _and(*terms):
    return " && ".join(f"({term})" for term in terms if term and term != "1") or "1"


REFERENCE_PHYSICAL_COMMON = (
    f"{REFERENCE_FOURL_PARENT} && veto5l && minMll4l > 12."
    f" && bVeto && {Z_WINDOW} && pass4lPt"
)
EXACT_ZZCR = (
    f"{REFERENCE_PHYSICAL_COMMON} && isXSF"
    " && mX > 75. && mX < 105. && PuppiMET_pt < 35."
)
CURRENT_DY = f"({REFERENCE_DY_PARENT}) && passZPt"
CURRENT_DY_ENRICHED = f"({CURRENT_DY}) && ({Z_WINDOW})"
DY_EVENTPT = _and(
    "validZ",
    "mZ > 30.",
    "Alt(Lepton_pt, Alt(Z_idx, 0, -1), -999.f) > 10.",
    "Alt(Lepton_pt, Alt(Z_idx, 1, -1), -999.f) > 10.",
    "passAnchor2lPt",
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

FLAVOR_SPLITS = OrderedDict((("ZEE", "isZee"), ("ZMM", "isZmm")))
TOPOLOGY_SPLITS = OrderedDict(
    (
        ("4E", "isZee && isXee"),
        ("4MU", "isZmm && isXmm"),
        ("2E2MU", "(isZee && isXmm) || (isZmm && isXee)"),
    )
)
EXTRA_SPLITS = OrderedDict(
    (("EXTRA0", "nExtraTight10 == 0"), ("EXTRA1", "nExtraTight10 == 1"), ("EXTRA2P", "nExtraTight10 >= 2"))
)
TRIGGER_SPLITS = OrderedDict(
    (
        ("TRGPRIO_ELMU", "triggerPriority == 1"),
        ("TRGPRIO_SINGLEMU", "triggerPriority == 2"),
        ("TRGPRIO_DOUBLEMU", "triggerPriority == 3"),
        ("TRGPRIO_SINGLEEL", "triggerPriority == 4"),
        ("TRGPRIO_DOUBLEEL", "triggerPriority == 5"),
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
        ("PT_ENRICHED_CURRENT_ONLY", _and(CURRENT_DY_ENRICHED, "!passAnchor2lPt")),
        ("PT_ENRICHED_EVENTPT_ONLY", _and(ANCHOR, "!passZPt")),
        ("PT_BROAD_CURRENT_ONLY", _and(CURRENT_DY, "!passAnchor2lPt")),
        ("PT_BROAD_EVENTPT_ONLY", _and(DY_EVENTPT, "!passZPt")),
    )
)

FOURL_STAGES = frozenset(name for name in PRIMARY_STAGES if name.startswith("S") and name != "S8_Z_BRIDGE")
BVETO_STAGES = frozenset(("S0_ZZCR", "S1_NO_MET", "S2_NO_XMASS", "S3_NO_XFLAVOR"))
WEIGHT_SENTINELS = ("S0_ZZCR", "S7_FOURL_BRIDGE", "S8_Z_BRIDGE", "D0_DY_ENRICHED_CURRENT", "D1_DY_ALL_CURRENT")


def nominal_factor(stage):
    if stage in FOURL_STAGES or stage.startswith("N1_") or stage.startswith("S0_") or stage.startswith("S7_"):
        factor = "LepSF_ZX*TriggerSF_ZX"
        if stage in BVETO_STAGES or (stage.startswith("N1_") and stage != "N1_NO_BVETO"):
            factor += "*bVetoSF"
        return factor
    return "LepSF_Z*TriggerSF_Z"


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
        cuts["S8_FOCUSED_ZEE_EGAMMA"] = _and(ANCHOR, "isZee", "streamPriority_EGamma")
        cuts["S8_FOCUSED_ZMM_MUON"] = _and(ANCHOR, "isZmm", "streamPriority_Muon")
    return cuts


def load_live_json():
    return load_full_config()


def supported_eras_from_live():
    return tuple(load_live_json()["years"])


def assert_live_era_contract():
    live = supported_eras_from_live()
    if live != SUPPORTED_ERAS:
        raise RuntimeError(f"Supported-era drift: study={SUPPORTED_ERAS}, vendored catalog={live}")
    return live


assert_live_era_contract()
