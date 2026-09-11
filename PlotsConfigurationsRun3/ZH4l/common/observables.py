"""Reusable ZH4l observable aliases and histogram definitions."""

from copy import deepcopy

PUBLIC_OBSERVABLE_ALIASES = frozenset(
    {
        "met_z_delta_phi",
        "met_x_delta_phi",
        "met_zx_delta_phi",
        "recoil_u_parallel",
        "recoil_u_perpendicular",
    }
)


def build_observable_aliases():
    return {
        "met_z_delta_phi": {"expr": "FourLepton::deltaPhi(PuppiMET_phi,z_phi)"},
        "met_x_delta_phi": {"expr": "FourLepton::deltaPhi(PuppiMET_phi,x_phi)"},
        "met_zx_delta_phi": {"expr": "FourLepton::deltaPhi(PuppiMET_phi,zx_phi)"},
        "recoil_u_parallel": {
            "expr": "FourLepton::recoilUpar(zx_pt,zx_phi,PuppiMET_pt,PuppiMET_phi)"
        },
        "recoil_u_perpendicular": {
            "expr": "FourLepton::recoilUperp(zx_pt,zx_phi,PuppiMET_pt,PuppiMET_phi)"
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
# policies do.  ``zx_min_pair_mass`` and ``veto_lepton_count`` are new public observables and
# therefore have explicitly documented family axes below.
OBSERVABLES = {
    "z_mass": _axis("z_mass", (30, 40, 60, 80, 85, 90, 95, 100, 120), "m_{Z} [GeV]", 3),
    "x_mass": _axis("x_mass", (30, 40, 60, 80, 85, 90, 95, 100, 120), "m_{X} [GeV]", 3),
    "zx_mass": _axis(
        "zx_mass",
        (60, 80, 100, 120, 140, 160, 180, 200, 250, 300, 400, 600),
        "m_{4l} [GeV]",
        3,
    ),
    "z_pt": _axis("z_pt", _PAIR_PT_EDGES, "p_{T}^{Z} [GeV]", 3),
    "x_pt": _axis("x_pt", _PAIR_PT_EDGES, "p_{T}^{X} [GeV]", 3),
    "zx_pt": _axis(
        "zx_pt",
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
    "zx_min_pair_mass": _axis(
        "zx_min_pair_mass",
        (0, 4, 8, 12, 16, 20, 30, 40, 60, 80),
        "min m_{ll} [GeV]",
        3,
    ),
    "veto_lepton_count": _axis(
        "veto_lepton_count",
        (-0.5, 0.5, 1.5, 2.5, 3.5, 4.5, 5.5, 6.5),
        "N_{l}(p_{T} >= 10 GeV)",
        3,
    ),
}


def select_observables(*names):
    missing = sorted(set(names) - set(OBSERVABLES))
    if missing:
        raise KeyError(f"Unknown common observables: {missing}")
    return {name: deepcopy(OBSERVABLES[name]) for name in names}
