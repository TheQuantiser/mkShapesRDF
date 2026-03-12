"""Shared selection configuration for the ZH_4lMET ZZ control region."""

# Pair-ID config for Z0/X lepton pairs.
PAIR_ID_CONFIG = {
    "eleWP": "cutBased_LooseID_tthMVA_Run3",
    "muWP": "cut_TightID_pfIsoTight_HWW_tthmva_67",
    # Required leptons passing the selected WP (0..2).
    "Z0_minPass": 2,
    "X_minPass": 2,
    # Per-pair pT thresholds: (leading, subleading).
    "Z0_ptMins": (10.0, 10.0),
    "X_ptMins": (10.0, 10.0),
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
