"""Reusable ZH4l observable aliases and histogram definitions."""


PUBLIC_OBSERVABLE_ALIASES = frozenset(
    {"dPhiMETZ", "dPhiMETX", "dPhiMET4l", "recoilUpar", "recoilUperp"}
)


def build_observable_aliases():
    return {
        "dPhiMETZ": {"expr": "FourLepton::deltaPhi(PuppiMET_phi,phiZ)"},
        "dPhiMETX": {"expr": "FourLepton::deltaPhi(PuppiMET_phi,phiX)"},
        "dPhiMET4l": {"expr": "FourLepton::deltaPhi(PuppiMET_phi,phi4l)"},
        "recoilUpar": {"expr": "FourLepton::recoilUpar(pt4l,phi4l,PuppiMET_pt,PuppiMET_phi)"},
        "recoilUperp": {"expr": "FourLepton::recoilUperp(pt4l,phi4l,PuppiMET_pt,PuppiMET_phi)"},
    }


OBSERVABLES = {
    "mZ": {"name": "mZ", "range": (60, 60.0, 120.0), "xaxis": "m_{Z} [GeV]", "fold": 0},
    "mX": {"name": "mX", "range": (50, 0.0, 150.0), "xaxis": "m_{X} [GeV]", "fold": 0},
    "m4l": {"name": "m4l", "range": (60, 70.0, 370.0), "xaxis": "m_{4l} [GeV]", "fold": 3},
    "ptZ": {"name": "ptZ", "range": (40, 0.0, 200.0), "xaxis": "p_{T}^{Z} [GeV]", "fold": 3},
    "ptX": {"name": "ptX", "range": (40, 0.0, 200.0), "xaxis": "p_{T}^{X} [GeV]", "fold": 3},
    "pt4l": {"name": "pt4l", "range": (40, 0.0, 200.0), "xaxis": "p_{T}^{4l} [GeV]", "fold": 3},
    "PuppiMET_pt": {"name": "PuppiMET_pt", "range": (40, 0.0, 200.0), "xaxis": "p_{T}^{miss} [GeV]", "fold": 3},
    "minMll4l": {"name": "minMll4l", "range": (40, 0.0, 80.0), "xaxis": "min m_{ll} [GeV]", "fold": 3},
    "nLepton10": {"name": "nLepton10", "range": (7, -0.5, 6.5), "xaxis": "N_{l}(p_{T} >= 10 GeV)", "fold": 3},
}


def select_observables(*names):
    missing = sorted(set(names) - set(OBSERVABLES))
    if missing:
        raise KeyError(f"Unknown common observables: {missing}")
    return {name: dict(OBSERVABLES[name]) for name in names}
