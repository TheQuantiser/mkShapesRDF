"""Sparse histogram plan for the closure bridge (hard cap: 300 actions)."""

from __future__ import annotations

import os
from collections import OrderedDict, defaultdict

from study_config import PRIMARY_STAGES, WEIGHT_SENTINELS, nominal_factor


def _axis(name, expression, title, bins, fold=3):
    return {"name": expression, "range": bins, "xaxis": title, "fold": fold}


EDGES = {
    "yield": (1, 0.0, 2.0),
    # Uniform axes throughout.  Overflow folding retains physically useful
    # tails without sacrificing resolution in the populated diagnostic range.
    "mZ": (60, 30.0, 150.0),       # 2 GeV: detector-scale DY mass resolution
    "ptZ": (70, 0.0, 140.0),         # 2 GeV: high-statistics DY recoil shape
    "Z0_absRapidity": (30, 0.0, 3.0),  # 0.1 across dilepton acceptance
    "phiEtaStar": (50, 0.0, 0.5),      # 0.01 in the recoil-sensitive core
    "Z_lead_pt": (40, 0.0, 100.0),     # 2.5 GeV; 15/25 thresholds are exact edges
    "Z_sublead_pt": (40, 0.0, 100.0),  # common pT schema aids direct comparison
    "absEta": (50, 0.0, 2.5),          # 0.05 through electron acceptance
    "PuppiMET_pt": (40, 0.0, 100.0),   # 2.5 GeV; 35 GeV is an exact bin edge
    "PV_npvsGood": (80, 0.0, 80.0),    # one bin per integer vertex count
    "nJet30": (8, -0.5, 7.5),
    "nExtraTight10": (6, -0.5, 5.5),
    "mX": (20, 0.0, 200.0),        # only coarse categories book this observable
    "ptX": (7, 0.0, 140.0),           # matches coarse four-lepton ptZ binning
    "m4l": (26, 80.0, 600.0),          # only coarse categories book this observable
    "minMll4l": (25, 0.0, 100.0), # 4 GeV; 12 GeV is an exact edge
    "nBLoose": (6, -0.5, 5.5),
    "X_flavor_code": (3, -0.5, 2.5),
    "selected4lPt": (15, 0.0, 150.0),  # ordered selected-4l lepton pT; tail folded
}

# The same observables use coarser *uniform* axes in categories that retain a
# four-lepton domain.  Those samples contain only O(10^2) events, whereas the
# Z/DY bridge can exploit the finer EDGES axes above.
COARSE_EDGES = {
    "yield": (1, 0.0, 2.0),
    "mZ": (14, 75.0, 110.0),
    "ptZ": (7, 0.0, 140.0),
    "Z0_absRapidity": (12, 0.0, 3.0),
    "phiEtaStar": (10, 0.0, 0.5),
    "Z_lead_pt": (10, 0.0, 100.0),
    "Z_sublead_pt": (10, 0.0, 100.0),
    "absEta": (10, 0.0, 2.5),
    "PuppiMET_pt": (20, 0.0, 100.0),
    "PV_npvsGood": (20, 0.0, 80.0),
    "nJet30": EDGES["nJet30"],
    "nExtraTight10": EDGES["nExtraTight10"],
    "mX": (12, 60.0, 120.0),
    "ptX": (7, 0.0, 140.0),
    "m4l": (26, 80.0, 600.0),
    "minMll4l": (15, 0.0, 60.0),
    "nBLoose": EDGES["nBLoose"],
    "X_flavor_code": EDGES["X_flavor_code"],
    "selected4lPt": (15, 0.0, 150.0),
}

DEFINITIONS = OrderedDict(
    (
        ("yield", _axis("yield", "1.f", "Events", EDGES["yield"], 0)),
        ("mZ", _axis("mZ", "mZ", "m_{ll} [GeV]", EDGES["mZ"])),
        ("ptZ", _axis("ptZ", "ptZ", "p_{T}(Z) [GeV]", EDGES["ptZ"])),
        ("Z0_absRapidity", _axis("Z0_absRapidity", "Z0_absRapidity", "|y(Z)|", EDGES["Z0_absRapidity"])),
        ("phiEtaStar", _axis("phiEtaStar", "phiEtaStar", "#phi^{*}_{#eta}", EDGES["phiEtaStar"])),
        ("Z_lead_pt", _axis("Z_lead_pt", "Z_lead_pt", "leading selected-Z p_{T} [GeV]", EDGES["Z_lead_pt"])),
        ("Z_sublead_pt", _axis("Z_sublead_pt", "Z_sublead_pt", "subleading selected-Z p_{T} [GeV]", EDGES["Z_sublead_pt"])),
        ("Z_lead_absEta", _axis("Z_lead_absEta", "Z_lead_absEta", "leading selected-Z |#eta|", EDGES["absEta"])),
        ("Z_sublead_absEta", _axis("Z_sublead_absEta", "Z_sublead_absEta", "subleading selected-Z |#eta|", EDGES["absEta"])),
        ("PuppiMET_pt", _axis("PuppiMET_pt", "PuppiMET_pt", "Puppi p_{T}^{miss} [GeV]", EDGES["PuppiMET_pt"])),
        ("PV_npvsGood", _axis("PV_npvsGood", "PV_npvsGood", "N_{PV}^{good}", EDGES["PV_npvsGood"])),
        ("nJet30", _axis("nJet30", "nJet30", "N_{jet}(p_{T}>30 GeV)", EDGES["nJet30"])),
        ("nExtraTight10", _axis("nExtraTight10", "nExtraTight10", "N_{extra tight l}(p_{T}>10 GeV)", EDGES["nExtraTight10"])),
        ("mX", _axis("mX", "mX", "m_{X} [GeV]", EDGES["mX"])),
        ("ptX", _axis("ptX", "ptX", "p_{T}(X) [GeV]", EDGES["ptX"])),
        ("m4l", _axis("m4l", "m4l", "m_{4l} [GeV]", EDGES["m4l"])),
        ("minMll4l", _axis("minMll4l", "minMll4l", "min m_{ij} [GeV]", EDGES["minMll4l"])),
        ("nBLoose", _axis("nBLoose", "nBLoose", "N_{b}^{loose}", EDGES["nBLoose"])),
        ("X_flavor_code", _axis("X_flavor_code", "2*isXSF + isXDF", "X flavor (0 other, 1 DF, 2 SF)", EDGES["X_flavor_code"], 0)),
        ("selected4lPt1", _axis("selected4lPt1", "Max(Take(Lepton_pt, Concatenate(Z_idx, X_idx)))", "selected 4l p_{T}^{1} [GeV]", EDGES["selected4lPt"])),
        ("selected4lPt4", _axis("selected4lPt4", "Min(Take(Lepton_pt, Concatenate(Z_idx, X_idx)))", "selected 4l p_{T}^{4} [GeV]", EDGES["selected4lPt"])),
    )
)

_booking = defaultdict(list)


def _book(categories, names):
    for category in categories:
        for name in names:
            if name not in _booking[category]:
                _booking[category].append(name)


_sentinels = ("S0_ZZCR", "S7_FOURL_BRIDGE", "S8_Z_BRIDGE", "D0_DY_ENRICHED_CURRENT", "D1_DY_ALL_CURRENT")
_other_primary = tuple(name for name in PRIMARY_STAGES if name not in _sentinels)
_book(_sentinels, ("yield", "mZ", "ptZ", "phiEtaStar", "PuppiMET_pt", "nJet30", "nExtraTight10"))
_book(("S8_Z_BRIDGE",), ("PV_npvsGood",))
_book(_other_primary, ("yield", "ptZ", "PuppiMET_pt", "nExtraTight10"))
_book(("S0_ZZCR", "S7_FOURL_BRIDGE"), ("mX", "ptX", "m4l", "minMll4l", "nBLoose", "selected4lPt1"))

_nminus = {
    "N1_NO_XMASS": ("mX", "PuppiMET_pt"),
    "N1_NO_XFLAVOR": ("X_flavor_code", "mX"),
    "N1_NO_BVETO": ("nBLoose", "nJet30"),
    "N1_NO_LOWMASS": ("minMll4l", "mX"),
    "N1_NO_FIFTHVETO": ("nExtraTight10", "yield"),
    "N1_NO_4LPT": ("selected4lPt1", "selected4lPt4"),
    "N1_NO_ZWINDOW": ("mZ", "ptZ"),
}
for _category, _names in _nminus.items():
    _book((_category,), _names)

_extra_categories = ("S8_EXTRA0", "S8_EXTRA1", "S8_EXTRA2P")
_book(_extra_categories, ("yield", "mZ", "ptZ", "phiEtaStar", "PuppiMET_pt", "nJet30"))

_flavor_categories = tuple(
    f"{parent}_{flavor}"
    for parent in ("S8_Z_BRIDGE", "D0_DY_ENRICHED_CURRENT", "D1_DY_ALL_CURRENT")
    for flavor in ("ZEE", "ZMM")
)
_book(_flavor_categories, ("mZ", "ptZ", "phiEtaStar", "Z_lead_pt", "Z_sublead_pt", "Z_lead_absEta", "Z_sublead_absEta", "PV_npvsGood"))

_topology_categories = tuple(
    f"{parent}_{topology}"
    for parent in ("S0_ZZCR", "S7_FOURL_BRIDGE")
    for topology in ("4E", "4MU", "2E2MU")
)
_book(_topology_categories, ("yield", "mZ", "mX", "ptZ", "PuppiMET_pt", "m4l"))

_migration_categories = ("PT_ENRICHED_CURRENT_ONLY", "PT_ENRICHED_EVENTPT_ONLY", "PT_BROAD_CURRENT_ONLY", "PT_BROAD_EVENTPT_ONLY")
_book(_migration_categories, ("mZ", "ptZ", "phiEtaStar", "nExtraTight10", "Z_lead_pt", "Z_sublead_pt"))

_trigger_categories = tuple(
    f"{parent}_{suffix}"
    for parent in ("S8_Z_BRIDGE", "D0_DY_ENRICHED_CURRENT")
    for suffix in ("TRGPRIO_ELMU", "TRGPRIO_SINGLEMU", "TRGPRIO_DOUBLEMU", "TRGPRIO_SINGLEEL", "TRGPRIO_DOUBLEEL")
)
_book(_trigger_categories, ("yield", "ptZ", "Z_lead_pt", "Z_sublead_pt"))
_stream_categories = tuple(
    f"{parent}_{suffix}"
    for parent in ("S8_Z_BRIDGE", "D0_DY_ENRICHED_CURRENT")
    for suffix in ("STREAM_MUONEG", "STREAM_MUON", "STREAM_EGAMMA")
)
_book(_stream_categories, ("yield", "ptZ"))

# Selection-only BASE and sentinel correction-ablation counters.
for _stage in PRIMARY_STAGES:
    _name = f"{_stage}__BASE"
    DEFINITIONS[_name] = {**DEFINITIONS["yield"], "studyWeightFactor": "1.f"}
    _booking[_stage].append(_name)
for _stage in WEIGHT_SENTINELS:
    _is_four = _stage in ("S0_ZZCR", "S7_FOURL_BRIDGE")
    _lep = "LepSF_ZX" if _is_four else "LepSF_Z"
    _trig = "TriggerSF_ZX" if _is_four else "TriggerSF_Z"
    for _suffix, _factor in (("LEP", _lep), ("LEP_TRIG", f"{_lep}*{_trig}"), ("FULL", nominal_factor(_stage))):
        _name = f"{_stage}__ABL_{_suffix}"
        DEFINITIONS[_name] = {**DEFINITIONS["yield"], "studyWeightFactor": _factor}
        _booking[_stage].append(_name)

if os.environ.get("CLOSURE_PROFILE", "default").strip().lower() == "focused_cross":
    _book(("S8_FOCUSED_ZEE_EGAMMA", "S8_FOCUSED_ZMM_MUON"), ("yield", "mZ", "ptZ"))

_RANGE_KEYS = {
    "Z_lead_absEta": "absEta",
    "Z_sublead_absEta": "absEta",
    "selected4lPt1": "selected4lPt",
    "selected4lPt4": "selected4lPt",
}


def _is_four_lepton_category(category):
    return category.startswith(("S0_", "S1_", "S2_", "S3_", "S4_", "S5_", "S6_", "S7_", "N1_"))


def _coarse_range(name, category, fallback):
    """Choose a uniform 4l axis from its domain and DATA-only FD scale."""
    range_key = _RANGE_KEYS.get(name, name)
    if range_key == "mZ":
        # The on-window topology samples give FD widths of 1.0--2.1 GeV;
        # 2.5 GeV is a stable rounded choice for the 86-event 4e leaf.
        return (24, 30.0, 150.0) if category == "N1_NO_ZWINDOW" else (14, 75.0, 110.0)
    if range_key == "mX":
        retains_x_window = (
            category.startswith(("S0_", "S1_"))
            or (category.startswith("N1_") and category != "N1_NO_XMASS")
        )
        # DATA FD widths are 1.7--3.4 GeV in ZZCR; use 5 GeV in the
        # populated window and 10 GeV for the deliberately released tail.
        return (12, 60.0, 120.0) if retains_x_window else (20, 0.0, 200.0)
    if range_key == "m4l":
        # On-shell ZZ DATA begins near 160 GeV (median about 238 GeV), so a
        # 150 GeV upper edge would put every event in overflow.  Inclusive
        # FD is 20 GeV; the low-stat topology leaves motivate 40 GeV.
        is_topology = category.endswith(("_4E", "_4MU", "_2E2MU"))
        low = 160.0 if category.startswith("S0_") else 80.0
        width = 40.0 if is_topology else 20.0
        return (int((600.0 - low) / width), low, 600.0)
    return COARSE_EDGES.get(range_key, fallback)


variables = OrderedDict()
for _name, _definition in DEFINITIONS.items():
    _categories = tuple(category for category, names in _booking.items() if _name in names)
    if not _categories:
        continue
    _fine_categories = tuple(category for category in _categories if not _is_four_lepton_category(category))
    _coarse_categories = tuple(category for category in _categories if _is_four_lepton_category(category))
    _range_key = _RANGE_KEYS.get(_name, _name)
    _groups = OrderedDict()
    if _fine_categories:
        _groups[("fine", EDGES.get(_range_key, _definition["range"]))] = _fine_categories
    for _category in _coarse_categories:
        _range = _coarse_range(_name, _category, _definition["range"])
        _groups.setdefault(("coarse", _range), tuple())
        _groups[("coarse", _range)] += (_category,)
    for _index, ((_resolution, _range), _selected_categories) in enumerate(_groups.items()):
        _key = f"{_name}__{_resolution}_{_index}"
        variables[_key] = {
            **_definition,
            "range": _range,
            "cuts": _selected_categories,
            "outputName": _name,
            "resolutionClass": _resolution,
        }

CATEGORY_VARIABLES = OrderedDict((category, tuple(names)) for category, names in _booking.items())
HISTOGRAM_ACTION_COUNT = sum(len(names) for names in CATEGORY_VARIABLES.values())
MAX_HISTOGRAM_ACTIONS = int(os.environ.get("MAX_HISTOGRAM_ACTIONS", "300"))
if HISTOGRAM_ACTION_COUNT > MAX_HISTOGRAM_ACTIONS and os.environ.get("ALLOW_LARGE_PLAN") != "1":
    raise RuntimeError(f"Closure plan has {HISTOGRAM_ACTION_COUNT} actions > {MAX_HISTOGRAM_ACTIONS}")
