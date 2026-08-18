from pathlib import Path

import pytest


CONFIG_DIR = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def ROOT():
    root = pytest.importorskip("ROOT")
    helper_macro = CONFIG_DIR / "macros" / "four_lepton_helpers.cc"
    btag_macro = CONFIG_DIR / "macros" / "fixed_wp_btag_sf.cc"
    root.gInterpreter.Declare(f'#include "{helper_macro}"')
    root.gInterpreter.Declare(f'#include "{btag_macro}"')
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
            (name, "bool" if name.startswith("passes") else "int")
            for name in results
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
                "FourLepton::bestZ0IdxWithID(pt,eta,phi,pdgId,passEle,passMu,2,25.f,10.f)",
            ),
        ),
        {"best0": "best[0]", "best1": "best[1]"},
    )
    assert values == {"best0": 0, "best1": 1}


def test_x_pair_uses_highest_leading_then_subleading_pt(ROOT):
    values = _one_event(
        ROOT,
        (
            ("pt", "ROOT::RVecF{50.f,45.f,30.f,25.f,28.f,15.f}"),
            ("pdgId", "ROOT::RVecI{-11,11,11,-11,-13,13}"),
            ("passEle", "ROOT::RVecB{true,true,true,true,true,true}"),
            ("passMu", "ROOT::RVecB{true,true,true,true,true,true}"),
            ("zidx", "ROOT::RVecI{0,1}"),
            (
                "xidx",
                "FourLepton::xPairIdxWithID(zidx,pt,pdgId,passEle,passMu,2,10.f,10.f)",
            ),
        ),
        {"x0": "xidx[0]", "x1": "xidx[1]"},
    )
    # Candidate (2,4) ties candidate (2,3) in leading pT and wins on the
    # 28 GeV subleading lepton.  It is different flavor and opposite sign.
    assert values == {"x0": 2, "x1": 4}


def test_ordered_pt_and_fifth_lepton_boundaries_are_strict(ROOT):
    definitions = (
        ("zidx", "ROOT::RVecI{0,1}"),
        ("xidx", "ROOT::RVecI{2,3}"),
        ("above", "ROOT::RVecF{25.1f,15.1f,10.1f,10.1f}"),
        ("atLead", "ROOT::RVecF{25.f,15.1f,10.1f,10.1f}"),
        ("fourPlusLow", "ROOT::RVecF{25.f,15.f,11.f,10.f,9.999f}"),
        ("fiveAtThreshold", "ROOT::RVecF{25.f,15.f,11.f,10.f,10.f}"),
    )
    values = _one_event(
        ROOT,
        definitions,
        {
            "passesAbove": (
                "FourLepton::passesOrdered4lPtThresholdsFromPairs("
                "above,zidx,xidx,25.f,15.f,10.f,10.f)"
            ),
            "passesAtLead": (
                "FourLepton::passesOrdered4lPtThresholdsFromPairs("
                "atLead,zidx,xidx,25.f,15.f,10.f,10.f)"
            ),
            "passesFourPlusLow": "FourLepton::fifthLeptonVeto(fourPlusLow,10.f)",
            "passesFiveAtThreshold": (
                "FourLepton::fifthLeptonVeto(fiveAtThreshold,10.f)"
            ),
        },
    )
    assert values == {
        "passesAbove": True,
        "passesAtLead": False,
        "passesFourPlusLow": True,
        "passesFiveAtThreshold": False,
    }


def test_ordered_two_lepton_pt_sorts_selected_pair_and_is_strict(ROOT):
    values = _one_event(
        ROOT,
        (
            ("reversedIdx", "ROOT::RVecI{1,0}"),
            ("duplicateIdx", "ROOT::RVecI{0,0}"),
            ("above", "ROOT::RVecF{15.1f,25.1f}"),
            ("atSublead", "ROOT::RVecF{15.f,25.1f}"),
        ),
        {
            "passesAbove": (
                "FourLepton::passesOrdered2lPtThresholdsFromPair("
                "above,reversedIdx,25.f,15.f)"
            ),
            "passesAtSublead": (
                "FourLepton::passesOrdered2lPtThresholdsFromPair("
                "atSublead,reversedIdx,25.f,15.f)"
            ),
            "passesDuplicate": (
                "FourLepton::passesOrdered2lPtThresholdsFromPair("
                "above,duplicateIdx,25.f,15.f)"
            ),
        },
    )
    assert values == {
        "passesAbove": True,
        "passesAtSublead": False,
        "passesDuplicate": False,
    }


def test_selected_charge_and_pair_flavor_are_consistent(ROOT):
    values = _one_event(
        ROOT,
        (
            ("pdgId", "ROOT::RVecI{-11,11,-13,13}"),
            ("zidx", "ROOT::RVecI{0,1}"),
            ("xidx", "ROOT::RVecI{2,3}"),
            ("dfidx", "ROOT::RVecI{1,2}"),
        ),
        {
            "charge": "FourLepton::sumLeptonChargeFromPairs(pdgId,zidx,xidx)",
            "xFlavor": "FourLepton::pairFlavor(pdgId,xidx)",
            "dfFlavor": "FourLepton::pairFlavor(pdgId,dfidx)",
        },
    )
    assert values == {"charge": 0, "xFlavor": 13, "dfFlavor": 0}


def test_trigger_and_stream_priorities_cover_every_fired_combination(ROOT):
    for mask in range(1, 1 << 5):
        fired = tuple(bool(mask & (1 << index)) for index in range(5))
        stream = ROOT.FourLepton.dataStreamPriorityCategory(*fired)
        family = ROOT.FourLepton.triggerFamilyPriorityCategory(*fired)
        assert stream in (1, 2, 3)
        assert family in (1, 2, 3, 4, 5)
        if fired[0]:
            assert stream == family == 1
        elif fired[1]:
            assert stream == 2
            assert family == 2
        elif fired[2]:
            assert stream == 2
            assert family == 3
        elif fired[3]:
            assert stream == 3
            assert family == 4
        else:
            assert stream == 3
            assert family == 5


@pytest.mark.parametrize(
    ("pt", "eta", "discriminator", "expected"),
    (
        (20.0, 0.0, 0.9, True),
        (20.1, 0.0, 0.9, False),
        (30.0, 2.5, 0.9, True),
        (30.0, 2.49, 0.9, False),
        (30.0, 0.0, 0.1, True),
    ),
)
def test_physical_btag_veto_boundaries(ROOT, pt, eta, discriminator, expected):
    frame = (
        ROOT.RDataFrame(1)
        .Define("cleanPt", f"ROOT::RVecF{{{pt}f}}")
        .Define("cleanEta", f"ROOT::RVecF{{{eta}f}}")
        .Define("cleanIdx", "ROOT::RVecI{0}")
        .Define("btag", f"ROOT::RVecF{{{discriminator}f}}")
        .Define(
            "passesVeto",
            "FixedWPBTag::veto(cleanPt,cleanEta,cleanIdx,btag,0.5f,20.f)",
        )
    )
    assert bool(frame.Take["bool"]("passesVeto").GetValue()[0]) is expected
