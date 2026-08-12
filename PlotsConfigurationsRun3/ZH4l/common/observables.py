"""Reusable ZH4l observable aliases and histogram definitions."""

PUBLIC_OBSERVABLE_ALIASES = frozenset(
    {"dPhiMETZ", "dPhiMETX", "dPhiMET4l", "recoilUpar", "recoilUperp"}
)


def build_observable_aliases():
    return {
        "dPhiMETZ": {"expr": "FourLepton::deltaPhi(PuppiMET_phi,phiZ)"},
        "dPhiMETX": {"expr": "FourLepton::deltaPhi(PuppiMET_phi,phiX)"},
        "dPhiMET4l": {"expr": "FourLepton::deltaPhi(PuppiMET_phi,phi4l)"},
        "recoilUpar": {
            "expr": "FourLepton::recoilUpar(pt4l,phi4l,PuppiMET_pt,PuppiMET_phi)"
        },
        "recoilUperp": {
            "expr": "FourLepton::recoilUperp(pt4l,phi4l,PuppiMET_pt,PuppiMET_phi)"
        },
    }


_PAIR_PT_EDGES = (0, 2, 4, 6, 8, 10, 15, 20, 25, 30, 35, 40, 50, 60, 70, 80, 100, 120)


def _axis(name, edges, xaxis, fold):
    """Build a one-dimensional variable-edge mkShapesRDF axis."""
    return {
        "name": name,
        "range": ([float(edge) for edge in edges],),
        "xaxis": xaxis,
        "fold": fold,
    }


# These seven axes are the validated legacy ZZ_CR presentation contract.  The
# public observable names changed, but neither their edges nor their flow
# policies do.  ``minMll4l`` and ``nLepton10`` are new public observables and
# therefore have explicitly documented family axes below.
OBSERVABLES = {
    "mZ": _axis("mZ", (30, 40, 60, 80, 85, 90, 95, 100, 120), "m_{Z} [GeV]", 3),
    "mX": _axis("mX", (30, 40, 60, 80, 85, 90, 95, 100, 120), "m_{X} [GeV]", 3),
    "m4l": _axis(
        "m4l",
        (60, 80, 100, 120, 140, 160, 180, 200, 250, 300, 400, 600),
        "m_{4l} [GeV]",
        3,
    ),
    "ptZ": _axis("ptZ", _PAIR_PT_EDGES, "p_{T}^{Z} [GeV]", 3),
    "ptX": _axis("ptX", _PAIR_PT_EDGES, "p_{T}^{X} [GeV]", 3),
    "pt4l": _axis(
        "pt4l",
        (0, 20, 40, 60, 80, 100, 150, 200, 300, 400),
        "p_{T}^{4l} [GeV]",
        2,
    ),
    "PuppiMET_pt": _axis(
        "PuppiMET_pt",
        (0, 10, 20, 30, 40, 50, 80, 100, 120),
        "p_{T}^{miss} [GeV]",
        3,
    ),
    "minMll4l": _axis(
        "minMll4l",
        (0, 4, 8, 12, 16, 20, 30, 40, 60, 80),
        "min m_{ll} [GeV]",
        3,
    ),
    "nLepton10": _axis(
        "nLepton10",
        (-0.5, 0.5, 1.5, 2.5, 3.5, 4.5, 5.5, 6.5),
        "N_{l}(p_{T} >= 10 GeV)",
        3,
    ),
}


def select_observables(*names):
    missing = sorted(set(names) - set(OBSERVABLES))
    if missing:
        raise KeyError(f"Unknown common observables: {missing}")
    return {name: dict(OBSERVABLES[name]) for name in names}
