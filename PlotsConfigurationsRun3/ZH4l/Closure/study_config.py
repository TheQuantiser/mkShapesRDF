"""Declarative, sparse DY-to-ZZ closure bridge built from a vendored contract."""

from __future__ import annotations

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
PRESELECTION = f"{TRIGGER_OR} && nLepton >= 2 && event_pass_leading_lepton_tight && event_pass_jet_horn_veto"
Z_VALID = "z_is_valid"
Z_CANDIDATE_10 = (
    "Alt(Lepton_pt, Alt(z_lepton_index, 0, -1), -999.f) > 10."
    " && Alt(Lepton_pt, Alt(z_lepton_index, 1, -1), -999.f) > 10."
)
Z_WINDOW = "abs(z_mass - 91.1876) < 15."
ANCHOR = (
    f"{Z_VALID} && ({Z_CANDIDATE_10}) && ({Z_WINDOW}) && event_pass_anchor_ordered_pt"
)

FOURL_VALID = (
    "z_is_valid && x_is_valid && zx_is_valid && x_mass > 4."
    " && Alt(Lepton_pt, Alt(x_lepton_index, 0, -1), -999.f) > 10."
    " && Alt(Lepton_pt, Alt(x_lepton_index, 1, -1), -999.f) > 10."
    " && zx_mass > 0. && zx_charge == 0"
)
FOURL_BRIDGE = f"({FOURL_VALID}) && ({Z_WINDOW}) && zx_pass_ordered_pt"

# These are formatted exactly as the live category_config.py contract.  Keep
# them separate from the simplified bridge vocabulary so reference-equivalence
# tests catch upstream drift instead of accepting a merely equivalent rewrite.
REFERENCE_DY_PARENT = (
    f"{TRIGGER_OR} && nLepton >= 2 && z_is_valid && z_mass > 30."
    " && Alt(Lepton_pt, Alt(z_lepton_index, 0, -1), -999.f) > 10"
    " && Alt(Lepton_pt, Alt(z_lepton_index, 1, -1), -999.f) > 10"
)
REFERENCE_FOURL_PARENT = (
    f"{REFERENCE_DY_PARENT} && nLepton >= 4 && x_is_valid && zx_is_valid"
    " && x_mass > 4. && Alt(Lepton_pt, Alt(x_lepton_index, 0, -1), -999.f) > 10"
    " && Alt(Lepton_pt, Alt(x_lepton_index, 1, -1), -999.f) > 10 && zx_mass > 0. && zx_charge == 0"
)

ZZ_TERMS = OrderedDict(
    (
        ("met", "PuppiMET_pt < 35."),
        ("xmass", "x_mass > 75. && x_mass < 105."),
        ("xflavor", "x_is_same_flavor"),
        ("bveto", "event_pass_b_veto"),
        ("lowmass", "zx_min_pair_mass > 12."),
        ("fifth", "event_pass_extra_lepton_veto"),
        ("fourlpt", "zx_pass_ordered_pt"),
        ("zwindow", Z_WINDOW),
    )
)


def _and(*terms):
    return " && ".join(f"({term})" for term in terms if term and term != "1") or "1"


REFERENCE_PHYSICAL_COMMON = (
    f"{REFERENCE_FOURL_PARENT} && event_pass_extra_lepton_veto && zx_min_pair_mass > 12."
    f" && event_pass_b_veto && {Z_WINDOW} && zx_pass_ordered_pt"
)
EXACT_ZZCR = (
    f"{REFERENCE_PHYSICAL_COMMON} && x_is_same_flavor"
    " && x_mass > 75. && x_mass < 105. && PuppiMET_pt < 35."
)
CURRENT_DY = f"({REFERENCE_DY_PARENT}) && z_pass_ordered_pt"
CURRENT_DY_ENRICHED = f"({CURRENT_DY}) && ({Z_WINDOW})"
DY_EVENTPT = _and(
    "z_is_valid",
    "z_mass > 30.",
    "Alt(Lepton_pt, Alt(z_lepton_index, 0, -1), -999.f) > 10.",
    "Alt(Lepton_pt, Alt(z_lepton_index, 1, -1), -999.f) > 10.",
    "event_pass_anchor_ordered_pt",
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
        (
            "N1_NO_XMASS",
            _and(FOURL_VALID, *(v for k, v in ZZ_TERMS.items() if k != "xmass")),
        ),
        (
            "N1_NO_XFLAVOR",
            _and(FOURL_VALID, *(v for k, v in ZZ_TERMS.items() if k != "xflavor")),
        ),
        (
            "N1_NO_BVETO",
            _and(FOURL_VALID, *(v for k, v in ZZ_TERMS.items() if k != "bveto")),
        ),
        (
            "N1_NO_LOWMASS",
            _and(FOURL_VALID, *(v for k, v in ZZ_TERMS.items() if k != "lowmass")),
        ),
        (
            "N1_NO_FIFTHVETO",
            _and(FOURL_VALID, *(v for k, v in ZZ_TERMS.items() if k != "fifth")),
        ),
        (
            "N1_NO_4LPT",
            _and(FOURL_VALID, *(v for k, v in ZZ_TERMS.items() if k != "fourlpt")),
        ),
        (
            "N1_NO_ZWINDOW",
            _and(FOURL_VALID, *(v for k, v in ZZ_TERMS.items() if k != "zwindow")),
        ),
    )
)

FLAVOR_SPLITS = OrderedDict((("ZEE", "z_is_ee"), ("ZMM", "z_is_mumu")))
TOPOLOGY_SPLITS = OrderedDict(
    (
        ("4E", "z_is_ee && x_is_ee"),
        ("4MU", "z_is_mumu && x_is_mumu"),
        ("2E2MU", "(z_is_ee && x_is_mumu) || (z_is_mumu && x_is_ee)"),
    )
)
EXTRA_SPLITS = OrderedDict(
    (
        ("EXTRA0", "extra_tight_lepton_count == 0"),
        ("EXTRA1", "extra_tight_lepton_count == 1"),
        ("EXTRA2P", "extra_tight_lepton_count >= 2"),
    )
)
TRIGGER_SPLITS = OrderedDict(
    (
        ("TRGPRIO_ELMU", "event_trigger_priority == 1"),
        ("TRGPRIO_SINGLEMU", "event_trigger_priority == 2"),
        ("TRGPRIO_DOUBLEMU", "event_trigger_priority == 3"),
        ("TRGPRIO_SINGLEEL", "event_trigger_priority == 4"),
        ("TRGPRIO_DOUBLEEL", "event_trigger_priority == 5"),
    )
)
STREAM_SPLITS = OrderedDict(
    (
        ("STREAM_MUONEG", "event_stream_is_muoneg"),
        ("STREAM_MUON", "event_stream_is_muon"),
        ("STREAM_EGAMMA", "event_stream_is_egamma"),
    )
)

MIGRATION = OrderedDict(
    (
        (
            "PT_ENRICHED_CURRENT_ONLY",
            _and(CURRENT_DY_ENRICHED, "!event_pass_anchor_ordered_pt"),
        ),
        ("PT_ENRICHED_EVENTPT_ONLY", _and(ANCHOR, "!z_pass_ordered_pt")),
        ("PT_BROAD_CURRENT_ONLY", _and(CURRENT_DY, "!event_pass_anchor_ordered_pt")),
        ("PT_BROAD_EVENTPT_ONLY", _and(DY_EVENTPT, "!z_pass_ordered_pt")),
    )
)

FOURL_STAGES = frozenset(
    name for name in PRIMARY_STAGES if name.startswith("S") and name != "S8_Z_BRIDGE"
)
BVETO_STAGES = frozenset(("S0_ZZCR", "S1_NO_MET", "S2_NO_XMASS", "S3_NO_XFLAVOR"))
WEIGHT_SENTINELS = (
    "S0_ZZCR",
    "S7_FOURL_BRIDGE",
    "S8_Z_BRIDGE",
    "D0_DY_ENRICHED_CURRENT",
    "D1_DY_ALL_CURRENT",
)


def nominal_factor(stage):
    _, parents = _categories("focused_cross")
    while stage in parents:
        stage = parents[stage]
    factors = {name: "sf_lepton_z*sf_trigger_z" for name in PRIMARY_STAGES}
    factors.update({name: "sf_lepton_zx*sf_trigger_zx" for name in FOURL_STAGES})
    for name in BVETO_STAGES:
        factors[name] += "*sf_b_veto"
    factors.update(
        {
            name: "sf_lepton_zx*sf_trigger_zx"
            + ("" if name == "N1_NO_BVETO" else "*sf_b_veto")
            for name in NMINUS1
        }
    )
    if stage not in factors:
        raise ValueError(f"No correction policy for category {stage}")
    return factors[stage]


def _categories(profile="default"):
    if profile not in ("default", "focused_cross"):
        raise ValueError("CLOSURE_PROFILE must be default or focused_cross")
    cuts = OrderedDict(PRIMARY_STAGES)
    cuts.update(NMINUS1)
    parents = {}
    for suffix, expr in EXTRA_SPLITS.items():
        cuts[f"S8_{suffix}"] = _and(ANCHOR, expr)
        parents[f"S8_{suffix}"] = "S8_Z_BRIDGE"
    for parent in ("S8_Z_BRIDGE", "D0_DY_ENRICHED_CURRENT", "D1_DY_ALL_CURRENT"):
        for suffix, expr in FLAVOR_SPLITS.items():
            cuts[f"{parent}_{suffix}"] = _and(PRIMARY_STAGES[parent], expr)
            parents[f"{parent}_{suffix}"] = parent
    for parent in ("S0_ZZCR", "S7_FOURL_BRIDGE"):
        for suffix, expr in TOPOLOGY_SPLITS.items():
            cuts[f"{parent}_{suffix}"] = _and(PRIMARY_STAGES[parent], expr)
            parents[f"{parent}_{suffix}"] = parent
    for parent in ("S8_Z_BRIDGE", "D0_DY_ENRICHED_CURRENT"):
        for suffix, expr in TRIGGER_SPLITS.items():
            cuts[f"{parent}_{suffix}"] = _and(PRIMARY_STAGES[parent], expr)
            parents[f"{parent}_{suffix}"] = parent
        for suffix, expr in STREAM_SPLITS.items():
            cuts[f"{parent}_{suffix}"] = _and(PRIMARY_STAGES[parent], expr)
            parents[f"{parent}_{suffix}"] = parent
    cuts.update(MIGRATION)
    parents.update({name: "S8_Z_BRIDGE" for name in MIGRATION})
    if profile == "focused_cross":
        cuts["S8_FOCUSED_ZEE_EGAMMA"] = _and(
            ANCHOR, "z_is_ee", "event_stream_is_egamma"
        )
        cuts["S8_FOCUSED_ZMM_MUON"] = _and(ANCHOR, "z_is_mumu", "event_stream_is_muon")
        parents.update(
            {
                "S8_FOCUSED_ZEE_EGAMMA": "S8_Z_BRIDGE",
                "S8_FOCUSED_ZMM_MUON": "S8_Z_BRIDGE",
            }
        )
    return cuts, parents


def build_categories(profile="default"):
    return _categories(profile)[0]


def load_live_json():
    return load_full_config()


def supported_eras_from_live():
    return tuple(load_live_json()["years"])


def assert_live_era_contract():
    live = supported_eras_from_live()
    if live != SUPPORTED_ERAS:
        raise RuntimeError(
            f"Supported-era drift: study={SUPPORTED_ERAS}, vendored catalog={live}"
        )
    return live


assert_live_era_contract()
