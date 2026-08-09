from pathlib import Path

import pytest


CONFIG_DIR = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def selected_pair_mass_evaluator():
    ROOT = pytest.importorskip("ROOT")
    macro = CONFIG_DIR / "macros" / "four_lepton_helpers.cc"
    ROOT.gInterpreter.Declare(f'#include "{macro}"')

    def evaluate(pt, eta, phi, pdg_id, zidx=(0, 1), xidx=(2, 3)):
        def floats(values):
            literals = []
            for value in values:
                literal = f"{float(value):.12g}"
                if "." not in literal and "e" not in literal.lower():
                    literal += ".0"
                literals.append(f"{literal}f")
            return ",".join(literals)

        def ints(values):
            return ",".join(str(int(value)) for value in values)

        frame = (
            ROOT.RDataFrame(1)
            .Define("pt", f"ROOT::VecOps::RVec<float>{{{floats(pt)}}}")
            .Define("eta", f"ROOT::VecOps::RVec<float>{{{floats(eta)}}}")
            .Define("phi", f"ROOT::VecOps::RVec<float>{{{floats(phi)}}}")
            .Define("pdgId", f"ROOT::VecOps::RVec<int>{{{ints(pdg_id)}}}")
            .Define("zidx", f"ROOT::VecOps::RVec<int>{{{ints(zidx)}}}")
            .Define("xidx", f"ROOT::VecOps::RVec<int>{{{ints(xidx)}}}")
            .Define(
                "minimum",
                "FourLepton::minimumSelectedPairMass("
                "pt, eta, phi, pdgId, zidx, xidx)",
            )
            .Define(
                "zMass",
                "FourLepton::pairMass(pt, eta, phi, pdgId, zidx)",
            )
            .Define(
                "xMass",
                "FourLepton::pairMass(pt, eta, phi, pdgId, xidx)",
            )
        )
        return {
            "minimum": float(frame.Max("minimum").GetValue()),
            "z_mass": float(frame.Max("zMass").GetValue()),
            "x_mass": float(frame.Max("xMass").GetValue()),
        }

    return evaluate


def test_all_six_selected_pair_masses_above_twelve(selected_pair_mass_evaluator):
    result = selected_pair_mass_evaluator(
        [45.6, 45.6, 20.0, 20.0],
        [0.0, 0.0, 0.0, 0.0],
        [0.0, 3.14159265, 1.57079633, -1.57079633],
        [-11, 11, -13, 13],
    )
    assert result["minimum"] > 12.0


def test_near_z_selected_pair_does_not_hide_low_cross_pair(
    selected_pair_mass_evaluator,
):
    result = selected_pair_mass_evaluator(
        [45.6, 45.6, 20.0, 18.0],
        [0.0, 0.0, 0.0, 0.0],
        [0.0, 3.14159265, 0.03, 0.10],
        [-11, 11, -13, 13],
    )
    assert result["z_mass"] == pytest.approx(91.2, abs=0.2)
    assert result["minimum"] < 12.0


def test_x_mass_above_twelve_does_not_hide_low_zx_cross_pair(
    selected_pair_mass_evaluator,
):
    result = selected_pair_mass_evaluator(
        [45.6, 45.6, 20.0, 20.0],
        [0.0, 0.0, 0.0, 0.0],
        [0.0, 3.14159265, 0.05, 2.0],
        [-11, 11, -13, 13],
    )
    assert result["x_mass"] > 12.0
    assert result["minimum"] < 12.0


@pytest.mark.parametrize(
    ("zidx", "xidx"),
    [((-1, 1), (2, 3)), ((0, 1), (1, 3)), ((0, 9), (2, 3))],
)
def test_invalid_or_duplicate_selected_indices_fail_closed(
    selected_pair_mass_evaluator, zidx, xidx
):
    result = selected_pair_mass_evaluator(
        [45.6, 45.6, 20.0, 20.0],
        [0.0, 0.0, 0.0, 0.0],
        [0.0, 3.14159265, 1.57079633, -1.57079633],
        [-11, 11, -13, 13],
        zidx,
        xidx,
    )
    assert result["minimum"] < 0.0
