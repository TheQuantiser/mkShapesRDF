"""Sparse histogram plan for the closure bridge (hard cap: 300 actions)."""

from __future__ import annotations

import os
from collections import OrderedDict, defaultdict

from common.outputs import branches, with_tree_outputs
from study_config import PRIMARY_STAGES, WEIGHT_SENTINELS, nominal_factor


def _axis(name, expression, title, bins, fold=3):
    return {"name": expression, "range": bins, "xaxis": title, "fold": fold}


EDGES = {
    "yield": (1, 0.0, 2.0),
    # Uniform axes throughout.  Overflow folding retains physically useful
    # tails without sacrificing resolution in the populated diagnostic range.
    "z_mass": (60, 30.0, 150.0),  # 2 GeV: detector-scale DY mass resolution
    "z_pt": (70, 0.0, 140.0),  # 2 GeV: high-statistics DY recoil shape
    "z_abs_rapidity": (30, 0.0, 3.0),  # 0.1 across dilepton acceptance
    "z_phi_eta_star": (50, 0.0, 0.5),  # 0.01 in the recoil-sensitive core
    "z_lepton_lead_pt": (40, 0.0, 100.0),  # 2.5 GeV; 15/25 thresholds are exact edges
    "z_lepton_sublead_pt": (40, 0.0, 100.0),  # common pT schema aids direct comparison
    "lepton_abs_eta": (50, 0.0, 2.5),  # 0.05 through electron acceptance
    "PuppiMET_pt": (40, 0.0, 100.0),  # 2.5 GeV; 35 GeV is an exact bin edge
    "PV_npvsGood": (80, 0.0, 80.0),  # one bin per integer vertex count
    "selected_jet_count": (8, -0.5, 7.5),
    "extra_tight_lepton_count": (6, -0.5, 5.5),
    "x_mass": (20, 0.0, 200.0),  # only coarse categories book this observable
    "x_pt": (7, 0.0, 140.0),  # matches coarse four-lepton z_pt binning
    "zx_mass": (26, 80.0, 600.0),  # only coarse categories book this observable
    "zx_min_pair_mass": (25, 0.0, 100.0),  # 4 GeV; 12 GeV is an exact edge
    "tagged_jet_count": (6, -0.5, 5.5),
    "x_flavor_code": (3, -0.5, 2.5),
    "zx_lepton_pt": (15, 0.0, 150.0),  # ordered selected-4l lepton pT; tail folded
}

# The same observables use coarser *uniform* axes in categories that retain a
# four-lepton domain.  Those samples contain only O(10^2) events, whereas the
# Z/DY bridge can exploit the finer EDGES axes above.
COARSE_EDGES = {
    "yield": (1, 0.0, 2.0),
    "z_mass": (14, 75.0, 110.0),
    "z_pt": (7, 0.0, 140.0),
    "z_abs_rapidity": (12, 0.0, 3.0),
    "z_phi_eta_star": (10, 0.0, 0.5),
    "z_lepton_lead_pt": (10, 0.0, 100.0),
    "z_lepton_sublead_pt": (10, 0.0, 100.0),
    "lepton_abs_eta": (10, 0.0, 2.5),
    "PuppiMET_pt": (20, 0.0, 100.0),
    "PV_npvsGood": (20, 0.0, 80.0),
    "selected_jet_count": EDGES["selected_jet_count"],
    "extra_tight_lepton_count": EDGES["extra_tight_lepton_count"],
    "x_mass": (12, 60.0, 120.0),
    "x_pt": (7, 0.0, 140.0),
    "zx_mass": (26, 80.0, 600.0),
    "zx_min_pair_mass": (15, 0.0, 60.0),
    "tagged_jet_count": EDGES["tagged_jet_count"],
    "x_flavor_code": EDGES["x_flavor_code"],
    "zx_lepton_pt": (15, 0.0, 150.0),
}

DEFINITIONS = OrderedDict(
    (
        ("yield", _axis("yield", "1.f", "Events", EDGES["yield"], 0)),
        ("z_mass", _axis("z_mass", "z_mass", "m_{ll} [GeV]", EDGES["z_mass"])),
        ("z_pt", _axis("z_pt", "z_pt", "p_{T}(Z) [GeV]", EDGES["z_pt"])),
        (
            "z_abs_rapidity",
            _axis(
                "z_abs_rapidity", "z_abs_rapidity", "|y(Z)|", EDGES["z_abs_rapidity"]
            ),
        ),
        (
            "z_phi_eta_star",
            _axis(
                "z_phi_eta_star",
                "z_phi_eta_star",
                "#phi^{*}_{#eta}",
                EDGES["z_phi_eta_star"],
            ),
        ),
        (
            "z_lepton_lead_pt",
            _axis(
                "z_lepton_lead_pt",
                "z_lepton_lead_pt",
                "leading selected-Z p_{T} [GeV]",
                EDGES["z_lepton_lead_pt"],
            ),
        ),
        (
            "z_lepton_sublead_pt",
            _axis(
                "z_lepton_sublead_pt",
                "z_lepton_sublead_pt",
                "subleading selected-Z p_{T} [GeV]",
                EDGES["z_lepton_sublead_pt"],
            ),
        ),
        (
            "z_lepton_lead_abs_eta",
            _axis(
                "z_lepton_lead_abs_eta",
                "z_lepton_lead_abs_eta",
                "leading selected-Z |#eta|",
                EDGES["lepton_abs_eta"],
            ),
        ),
        (
            "z_lepton_sublead_abs_eta",
            _axis(
                "z_lepton_sublead_abs_eta",
                "z_lepton_sublead_abs_eta",
                "subleading selected-Z |#eta|",
                EDGES["lepton_abs_eta"],
            ),
        ),
        (
            "PuppiMET_pt",
            _axis(
                "PuppiMET_pt",
                "PuppiMET_pt",
                "Puppi p_{T}^{miss} [GeV]",
                EDGES["PuppiMET_pt"],
            ),
        ),
        (
            "PV_npvsGood",
            _axis("PV_npvsGood", "PV_npvsGood", "N_{PV}^{good}", EDGES["PV_npvsGood"]),
        ),
        (
            "selected_jet_count",
            _axis(
                "selected_jet_count",
                "selected_jet_count",
                "N_{jet}(p_{T}>30 GeV)",
                EDGES["selected_jet_count"],
            ),
        ),
        (
            "extra_tight_lepton_count",
            _axis(
                "extra_tight_lepton_count",
                "extra_tight_lepton_count",
                "N_{extra tight l}(p_{T}>10 GeV)",
                EDGES["extra_tight_lepton_count"],
            ),
        ),
        ("x_mass", _axis("x_mass", "x_mass", "m_{X} [GeV]", EDGES["x_mass"])),
        ("x_pt", _axis("x_pt", "x_pt", "p_{T}(X) [GeV]", EDGES["x_pt"])),
        ("zx_mass", _axis("zx_mass", "zx_mass", "m_{4l} [GeV]", EDGES["zx_mass"])),
        (
            "zx_min_pair_mass",
            _axis(
                "zx_min_pair_mass",
                "zx_min_pair_mass",
                "min m_{ij} [GeV]",
                EDGES["zx_min_pair_mass"],
            ),
        ),
        (
            "tagged_jet_count",
            _axis(
                "tagged_jet_count",
                "tagged_jet_count",
                "N_{b}^{loose}",
                EDGES["tagged_jet_count"],
            ),
        ),
        (
            "x_flavor_code",
            _axis(
                "x_flavor_code",
                "2*x_is_same_flavor + x_is_different_flavor",
                "X flavor (0 other, 1 DF, 2 SF)",
                EDGES["x_flavor_code"],
                0,
            ),
        ),
        (
            "zx_lepton_rank1_pt",
            _axis(
                "zx_lepton_rank1_pt",
                "Max(Take(Lepton_pt, Concatenate(z_lepton_index, x_lepton_index)))",
                "selected 4l p_{T}^{1} [GeV]",
                EDGES["zx_lepton_pt"],
            ),
        ),
        (
            "zx_lepton_rank4_pt",
            _axis(
                "zx_lepton_rank4_pt",
                "Min(Take(Lepton_pt, Concatenate(z_lepton_index, x_lepton_index)))",
                "selected 4l p_{T}^{4} [GeV]",
                EDGES["zx_lepton_pt"],
            ),
        ),
    )
)

_booking = defaultdict(list)


def _book(categories, names):
    for category in categories:
        for name in names:
            if name not in _booking[category]:
                _booking[category].append(name)


_sentinels = (
    "S0_ZZCR",
    "S7_FOURL_BRIDGE",
    "S8_Z_BRIDGE",
    "D0_DY_ENRICHED_CURRENT",
    "D1_DY_ALL_CURRENT",
)
_other_primary = tuple(name for name in PRIMARY_STAGES if name not in _sentinels)
_book(
    _sentinels,
    (
        "yield",
        "z_mass",
        "z_pt",
        "z_phi_eta_star",
        "PuppiMET_pt",
        "selected_jet_count",
        "extra_tight_lepton_count",
    ),
)
_book(("S8_Z_BRIDGE",), ("PV_npvsGood",))
_book(_other_primary, ("yield", "z_pt", "PuppiMET_pt", "extra_tight_lepton_count"))
_book(
    ("S0_ZZCR", "S7_FOURL_BRIDGE"),
    (
        "x_mass",
        "x_pt",
        "zx_mass",
        "zx_min_pair_mass",
        "tagged_jet_count",
        "zx_lepton_rank1_pt",
    ),
)

_nminus = {
    "N1_NO_XMASS": ("x_mass", "PuppiMET_pt"),
    "N1_NO_XFLAVOR": ("x_flavor_code", "x_mass"),
    "N1_NO_BVETO": ("tagged_jet_count", "selected_jet_count"),
    "N1_NO_LOWMASS": ("zx_min_pair_mass", "x_mass"),
    "N1_NO_FIFTHVETO": ("extra_tight_lepton_count", "yield"),
    "N1_NO_4LPT": ("zx_lepton_rank1_pt", "zx_lepton_rank4_pt"),
    "N1_NO_ZWINDOW": ("z_mass", "z_pt"),
}
for _category, _names in _nminus.items():
    _book((_category,), _names)

_extra_categories = ("S8_EXTRA0", "S8_EXTRA1", "S8_EXTRA2P")
_book(
    _extra_categories,
    ("yield", "z_mass", "z_pt", "z_phi_eta_star", "PuppiMET_pt", "selected_jet_count"),
)

_flavor_categories = tuple(
    f"{parent}_{flavor}"
    for parent in ("S8_Z_BRIDGE", "D0_DY_ENRICHED_CURRENT", "D1_DY_ALL_CURRENT")
    for flavor in ("ZEE", "ZMM")
)
_book(
    _flavor_categories,
    (
        "z_mass",
        "z_pt",
        "z_phi_eta_star",
        "z_lepton_lead_pt",
        "z_lepton_sublead_pt",
        "z_lepton_lead_abs_eta",
        "z_lepton_sublead_abs_eta",
        "PV_npvsGood",
    ),
)

_topology_categories = tuple(
    f"{parent}_{topology}"
    for parent in ("S0_ZZCR", "S7_FOURL_BRIDGE")
    for topology in ("4E", "4MU", "2E2MU")
)
_book(
    _topology_categories,
    ("yield", "z_mass", "x_mass", "z_pt", "PuppiMET_pt", "zx_mass"),
)

_migration_categories = (
    "PT_ENRICHED_CURRENT_ONLY",
    "PT_ENRICHED_EVENTPT_ONLY",
    "PT_BROAD_CURRENT_ONLY",
    "PT_BROAD_EVENTPT_ONLY",
)
_book(
    _migration_categories,
    (
        "z_mass",
        "z_pt",
        "z_phi_eta_star",
        "extra_tight_lepton_count",
        "z_lepton_lead_pt",
        "z_lepton_sublead_pt",
    ),
)

_trigger_categories = tuple(
    f"{parent}_{suffix}"
    for parent in ("S8_Z_BRIDGE", "D0_DY_ENRICHED_CURRENT")
    for suffix in (
        "TRGPRIO_ELMU",
        "TRGPRIO_SINGLEMU",
        "TRGPRIO_DOUBLEMU",
        "TRGPRIO_SINGLEEL",
        "TRGPRIO_DOUBLEEL",
    )
)
_book(_trigger_categories, ("yield", "z_pt", "z_lepton_lead_pt", "z_lepton_sublead_pt"))
_stream_categories = tuple(
    f"{parent}_{suffix}"
    for parent in ("S8_Z_BRIDGE", "D0_DY_ENRICHED_CURRENT")
    for suffix in ("STREAM_MUONEG", "STREAM_MUON", "STREAM_EGAMMA")
)
_book(_stream_categories, ("yield", "z_pt"))

# Selection-only BASE and sentinel correction-ablation counters.
for _stage in PRIMARY_STAGES:
    _name = f"{_stage}__BASE"
    DEFINITIONS[_name] = {
        **DEFINITIONS["yield"],
        "studyWeightFactor": "1.f",
        "outputName": "yield_base",
    }
    _booking[_stage].append(_name)
for _stage in WEIGHT_SENTINELS:
    _is_four = _stage in ("S0_ZZCR", "S7_FOURL_BRIDGE")
    _lep = "sf_lepton_zx" if _is_four else "sf_lepton_z"
    _trig = "sf_trigger_zx" if _is_four else "sf_trigger_z"
    for _suffix, _factor in (
        ("LEP", _lep),
        ("LEP_TRIG", f"{_lep}*{_trig}"),
        ("FULL", nominal_factor(_stage)),
    ):
        _name = f"{_stage}__ABL_{_suffix}"
        _output = {
            "LEP": "yield_lepton",
            "LEP_TRIG": "yield_lepton_trigger",
            "FULL": "yield_nominal",
        }[_suffix]
        DEFINITIONS[_name] = {
            **DEFINITIONS["yield"],
            "studyWeightFactor": _factor,
            "outputName": _output,
        }
        _booking[_stage].append(_name)

if os.environ.get("CLOSURE_PROFILE", "default").strip().lower() == "focused_cross":
    _book(("S8_FOCUSED_ZEE_EGAMMA", "S8_FOCUSED_ZMM_MUON"), ("yield", "z_mass", "z_pt"))

_RANGE_KEYS = {
    "z_lepton_lead_abs_eta": "lepton_abs_eta",
    "z_lepton_sublead_abs_eta": "lepton_abs_eta",
    "zx_lepton_rank1_pt": "zx_lepton_pt",
    "zx_lepton_rank4_pt": "zx_lepton_pt",
}


def _is_four_lepton_category(category):
    return category.startswith(
        ("S0_", "S1_", "S2_", "S3_", "S4_", "S5_", "S6_", "S7_", "N1_")
    )


def _coarse_range(name, category, fallback):
    """Choose a uniform 4l axis from its domain and DATA-only FD scale."""
    range_key = _RANGE_KEYS.get(name, name)
    if range_key == "z_mass":
        # The on-window topology samples give FD widths of 1.0--2.1 GeV;
        # 2.5 GeV is a stable rounded choice for the 86-event 4e leaf.
        return (24, 30.0, 150.0) if category == "N1_NO_ZWINDOW" else (14, 75.0, 110.0)
    if range_key == "x_mass":
        retains_x_window = category.startswith(("S0_", "S1_")) or (
            category.startswith("N1_") and category != "N1_NO_XMASS"
        )
        # DATA FD widths are 1.7--3.4 GeV in ZZCR; use 5 GeV in the
        # populated window and 10 GeV for the deliberately released tail.
        return (12, 60.0, 120.0) if retains_x_window else (20, 0.0, 200.0)
    if range_key == "zx_mass":
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
    _categories = tuple(
        category for category, names in _booking.items() if _name in names
    )
    if not _categories:
        continue
    _fine_categories = tuple(
        category for category in _categories if not _is_four_lepton_category(category)
    )
    _coarse_categories = tuple(
        category for category in _categories if _is_four_lepton_category(category)
    )
    _range_key = _RANGE_KEYS.get(_name, _name)
    _groups = OrderedDict()
    if _fine_categories:
        _groups[("fine", EDGES.get(_range_key, _definition["range"]))] = (
            _fine_categories
        )
    for _category in _coarse_categories:
        _range = _coarse_range(_name, _category, _definition["range"])
        _groups.setdefault(("coarse", _range), tuple())
        _groups[("coarse", _range)] += (_category,)
    for _index, ((_resolution, _range), _selected_categories) in enumerate(
        _groups.items()
    ):
        _key = f"{_name}__{_resolution}_{_index}"
        variables[_key] = {
            **_definition,
            "range": _range,
            "cuts": _selected_categories,
            "outputName": _definition.get("outputName", _name),
            "resolutionClass": _resolution,
        }

CATEGORY_VARIABLES = OrderedDict(
    (category, tuple(names)) for category, names in _booking.items()
)
HISTOGRAM_ACTION_COUNT = sum(len(names) for names in CATEGORY_VARIABLES.values())
MAX_HISTOGRAM_ACTIONS = int(os.environ.get("MAX_HISTOGRAM_ACTIONS", "300"))
if (
    HISTOGRAM_ACTION_COUNT > MAX_HISTOGRAM_ACTIONS
    and os.environ.get("ALLOW_LARGE_PLAN") != "1"
):
    raise RuntimeError(
        f"Closure plan has {HISTOGRAM_ACTION_COUNT} actions > {MAX_HISTOGRAM_ACTIONS}"
    )


variables = with_tree_outputs(
    variables,
    globals().get("cuts", {}),
    branches(
        "identity",
        "source",
        "z",
        "x",
        "zx",
        "corrections",
        extra={"weight_base": "weight"},
    ),
)
