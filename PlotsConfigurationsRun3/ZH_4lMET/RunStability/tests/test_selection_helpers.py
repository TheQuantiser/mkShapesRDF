from pathlib import Path

import pytest


CONFIG_DIR = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def ROOT():
    root = pytest.importorskip("ROOT")
    helper_macro = CONFIG_DIR / "macros" / "run_stability_helpers.cc"
    root.gInterpreter.Declare(f'#include "{helper_macro}"')
    return root


def _one_event(ROOT, definitions, results):
    frame = ROOT.RDataFrame(1)
    for name, expression in definitions:
        frame = frame.Define(name, expression)
    for name, expression in results.items():
        frame = frame.Define(name, expression)
    return {
        name: frame.Take[column_type](name).GetValue()[0]
        for name, column_type in (
            (name, "bool" if name.startswith("passes") else "int") for name in results
        )
    }


def test_z_candidate_is_closest_ossf_pair_and_is_pt_ordered(ROOT):
    values = _one_event(
        ROOT,
        (
            ("pt", "ROOT::RVecF{45.6f,45.6f,30.f,20.f}"),
            ("eta", "ROOT::RVecF{0.f,0.f,0.f,0.f}"),
            ("phi", "ROOT::RVecF{0.f,3.14159265f,0.5f,2.5f}"),
            ("pdgId", "ROOT::RVecI{-11,11,-13,13}"),
            ("passEle", "ROOT::RVecB{true,true,true,true}"),
            ("passMu", "ROOT::RVecB{true,true,true,true}"),
            (
                "best",
                "RunStability::bestZ0IdxWithID(pt,eta,phi,pdgId,passEle,passMu,2,35.f,35.f)",
            ),
        ),
        {"best0": "best[0]", "best1": "best[1]"},
    )
    assert values == {"best0": 0, "best1": 1}


def test_ordered_two_lepton_pt_sorts_pair_and_uses_strict_35_35(ROOT):
    values = _one_event(
        ROOT,
        (
            ("reversedIdx", "ROOT::RVecI{1,0}"),
            ("duplicateIdx", "ROOT::RVecI{0,0}"),
            ("above", "ROOT::RVecF{35.001f,35.001f}"),
            ("atThreshold", "ROOT::RVecF{35.f,35.001f}"),
        ),
        {
            "passesAbove": (
                "RunStability::passesOrdered2lPtThresholdsFromPair("
                "above,reversedIdx,35.f,35.f)"
            ),
            "passesAtThreshold": (
                "RunStability::passesOrdered2lPtThresholdsFromPair("
                "atThreshold,reversedIdx,35.f,35.f)"
            ),
            "passesDuplicate": (
                "RunStability::passesOrdered2lPtThresholdsFromPair("
                "above,duplicateIdx,35.f,35.f)"
            ),
        },
    )
    assert values == {
        "passesAbove": True,
        "passesAtThreshold": False,
        "passesDuplicate": False,
    }


def test_trigger_and_stream_priorities_cover_every_fired_combination(ROOT):
    for mask in range(1, 1 << 5):
        fired = tuple(bool(mask & (1 << index)) for index in range(5))
        stream = ROOT.RunStability.dataStreamPriorityCategory(*fired)
        assert stream in (1, 2, 3)
        if fired[0]:
            assert stream == 1
        elif fired[1] or fired[2]:
            assert stream == 2
        else:
            assert stream == 3
