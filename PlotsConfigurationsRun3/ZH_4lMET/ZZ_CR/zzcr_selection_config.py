"""Shared selection configuration for the ZH_4lMET ZZ control region."""

import os


if "load_selected_year" not in globals():
    _candidates = [
        globals().get("ZZCR_CONFIG_DIR"),
        globals().get("folder"),
        os.getcwd(),
        os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else None,
    ]
    _zzcr_config_dir = None
    for _cand in _candidates:
        if not _cand:
            continue
        _cand_abs = os.path.abspath(_cand)
        if os.path.exists(os.path.join(_cand_abs, "zzcr_year.py")):
            _zzcr_config_dir = _cand_abs
            break
    if _zzcr_config_dir is None:
        _zzcr_config_dir = os.path.abspath(os.getcwd())
    exec(
        open(os.path.join(_zzcr_config_dir, "zzcr_year.py")).read(),
        globals(),
        globals(),
    )

_, _selected_year, _ = load_selected_year()

_pair_cfg = _selected_year.get("lepton_ids", {})

# Pair-ID config for Z0/X lepton pairs.
PAIR_ID_CONFIG = {
    "eleWP": _pair_cfg.get("electron_wp", "cutBased_LooseID_tthMVA_Run3"),
    "muWP": _pair_cfg.get("muon_wp", "cut_TightID_pfIsoTight_HWW_tthmva_67"),
    # Required leptons passing the selected WP (0..2).
    "Z0_minPass": int(_pair_cfg.get("z0_min_pass", 2)),
    "X_minPass": int(_pair_cfg.get("x_min_pass", 2)),
    # Per-pair pT thresholds: (leading, subleading).
    "Z0_ptMins": tuple(_pair_cfg.get("z0_pt_mins", (10.0, 10.0))),
    "X_ptMins": tuple(_pair_cfg.get("x_pt_mins", (10.0, 10.0))),
}

# Shared pair indices/combinations for aliases and variables.
LEPTON_PAIR_INDEX_EXPRESSIONS = {
    "lZ1": "Alt(Z0_idx, 0, -1)",
    "lZ2": "Alt(Z0_idx, 1, -1)",
    "lX1": "Alt(X_idx, 0, -1)",
    "lX2": "Alt(X_idx, 1, -1)",
}

LEPTON_PAIR_COMBINATIONS = [
    ("lZ1", "lZ2"),
    ("lZ1", "lX1"),
    ("lZ1", "lX2"),
    ("lZ2", "lX1"),
    ("lZ2", "lX2"),
    ("lX1", "lX2"),
]
