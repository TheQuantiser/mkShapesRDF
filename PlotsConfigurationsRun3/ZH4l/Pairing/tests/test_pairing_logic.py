"""Focused executable tests for the fixed-quartet pairing contract."""

from __future__ import annotations

import math
import importlib.util
from pathlib import Path

import pytest


ROOT = pytest.importorskip("ROOT")
PAIRING_DIR = Path(__file__).resolve().parents[1]
MACRO = PAIRING_DIR / "macros" / "pairing.cc"


@pytest.fixture(scope="session", autouse=True)
def _declare_pairing_macro():
    ROOT.gInterpreter.Declare(f'#include "{MACRO}"')


def _rvec_float(values):
    return ROOT.VecOps.RVec("float")([float(value) for value in values])


def _rvec_int(values):
    return ROOT.VecOps.RVec("int")([int(value) for value in values])


def _candidate_vector(values):
    return ROOT.VecOps.RVec("PairingStudy::Candidate")(values)


def _enumerate(pdg_ids, pt=(60.0, 50.0, 40.0, 30.0), eta=None, phi=None):
    eta = eta or (0.1, -0.2, 0.4, -0.6)
    phi = phi or (0.0, 1.2, -2.1, 2.7)
    quartet = _rvec_int((0, 1, 2, 3))
    candidates = ROOT.PairingStudy.enumerateCandidates(
        _rvec_float(pt),
        _rvec_float(eta),
        _rvec_float(phi),
        _rvec_int(pdg_ids),
        quartet,
    )
    return quartet, candidates


@pytest.mark.parametrize(
    "pdg_ids, topology, n_candidates, n_partitions, x_flavor",
    (
        ((11, 11, -11, -11), 1, 4, 2, 1),
        ((13, 13, -13, -13), 2, 4, 2, 1),
        ((11, -11, 13, -13), 3, 2, 1, 1),
        ((11, 11, -11, -13), 4, 2, 2, 2),
        ((11, 13, -13, -13), 5, 2, 2, 2),
    ),
)
def test_all_topologies_have_expected_candidates_and_complements(
    pdg_ids, topology, n_candidates, n_partitions, x_flavor
):
    quartet, candidates = _enumerate(pdg_ids)

    assert ROOT.PairingStudy.topologyCode(_rvec_int(pdg_ids), quartet) == topology
    assert len(candidates) == n_candidates
    assert len({candidate.partition for candidate in candidates}) == n_partitions

    quartet_set = set(quartet)
    for candidate in candidates:
        z_pair = {candidate.z1, candidate.z2}
        x_pair = {candidate.x1, candidate.x2}
        assert z_pair.isdisjoint(x_pair)
        assert z_pair | x_pair == quartet_set
        assert x_pair == quartet_set - z_pair
        assert pdg_ids[candidate.z1] == -pdg_ids[candidate.z2]
        # Total quartet charge zero plus an OS Z forces the complement to be OS.
        assert pdg_ids[candidate.x1] * pdg_ids[candidate.x2] < 0
        assert candidate.xFlavor == x_flavor


def test_xsf_xdf_is_invariant_under_every_ossf_assignment():
    expected = {
        (11, 11, -11, -11): 1,
        (13, 13, -13, -13): 1,
        (11, -11, 13, -13): 1,
        (11, 11, -11, -13): 2,
        (11, 13, -13, -13): 2,
    }
    for pdg_ids, x_flavor in expected.items():
        _, candidates = _enumerate(pdg_ids)
        assert candidates
        assert {candidate.xFlavor for candidate in candidates} == {x_flavor}


def test_pairing_independent_quartet_threshold_and_fifth_lepton_contract():
    pdg_ids = _rvec_int((11, -11, 13, -13, 11))
    tight = _rvec_int((1, 1, 1, 1, 0))

    passing_pt = _rvec_float((30.0, 20.0, 12.0, 11.0, 9.0))
    quartet = ROOT.PairingStudy.buildQuartet(passing_pt, pdg_ids, tight)
    assert list(quartet) == [0, 1, 2, 3]
    assert ROOT.PairingStudy.passesObjectBase(passing_pt, pdg_ids, quartet)

    boundary_pt = _rvec_float((30.0, 20.0, 12.0, 10.0, 9.0))
    assert not ROOT.PairingStudy.passesObjectBase(boundary_pt, pdg_ids, quartet)

    fifth_at_ten = _rvec_float((30.0, 20.0, 12.0, 11.0, 10.0))
    # The fifth object is not tight, but the live veto counts every common
    # Lepton at or above 10 GeV.
    assert not ROOT.PairingStudy.passesObjectBase(fifth_at_ten, pdg_ids, quartet)


def test_nearest_mz_reproduces_strict_first_encounter_tie_breaking():
    # All four OS-SF masses are exactly equal by construction.  Candidate
    # enumeration is (0,2), (0,3), (1,2), (1,3), so strict `<` keeps (0,2).
    pdg_ids = (11, 11, -11, -11)
    _, candidates = _enumerate(
        pdg_ids,
        pt=(50.0, 50.0, 50.0, 50.0),
        eta=(0.0, 0.0, 0.0, 0.0),
        phi=(0.0, 0.0, math.pi, math.pi),
    )
    assert [(item.z1, item.z2) for item in candidates] == [
        (0, 2),
        (0, 3),
        (1, 2),
        (1, 3),
    ]
    assert ROOT.PairingStudy.selectCandidate(
        candidates, ROOT.PairingStudy.NEAREST_MZ
    ) == 0
    assert ROOT.PairingStudy.selectCandidate(
        candidates, ROOT.PairingStudy.CORE_L4KIN_MASSLESS
    ) == 0
    assert ROOT.PairingStudy.selectCandidate(
        candidates, ROOT.PairingStudy.HISTORICAL_RUN2_MASSLESS
    ) == 0

    scores = ROOT.PairingStudy.scoreSummary(
        candidates, ROOT.PairingStudy.NEAREST_MZ
    )
    assert scores[2] == pytest.approx(0.0, abs=1.0e-7)


def test_live_nearest_is_first_minimum_and_core_equals_historical():
    for pdg_ids in (
        (11, 11, -11, -11),
        (13, 13, -13, -13),
        (11, -11, 13, -13),
        (11, 11, -11, -13),
        (11, 13, -13, -13),
    ):
        _, candidates = _enumerate(pdg_ids)
        live_expected = min(range(len(candidates)), key=lambda i: candidates[i].dmZ)
        assert ROOT.PairingStudy.selectCandidate(
            candidates, ROOT.PairingStudy.NEAREST_MZ
        ) == live_expected
        assert ROOT.PairingStudy.selectCandidate(
            candidates, ROOT.PairingStudy.CORE_L4KIN_MASSLESS
        ) == ROOT.PairingStudy.selectCandidate(
            candidates, ROOT.PairingStudy.HISTORICAL_RUN2_MASSLESS
        )


def test_literal_massless_convention_can_change_the_selected_pair():
    # Tune ee and mumu masses within the O(0.1 MeV) muon-mass correction.  The
    # live physical-mass score selects ee; literal core/Run-2 massless scores
    # select mumu.  This locks the documented non-equivalence edge case.
    z_mass = float(ROOT.PairingStudy.Z_MASS)
    electron_pt = (z_mass + 0.00008) / 2.0
    muon_pt = (z_mass - 0.00005) / 2.0
    _, candidates = _enumerate(
        (11, -11, 13, -13),
        pt=(electron_pt, electron_pt, muon_pt, muon_pt),
        eta=(0.0, 0.0, 0.0, 0.0),
        phi=(0.0, math.pi, 0.0, math.pi),
    )

    live = ROOT.PairingStudy.selectCandidate(candidates, ROOT.PairingStudy.NEAREST_MZ)
    core = ROOT.PairingStudy.selectCandidate(
        candidates, ROOT.PairingStudy.CORE_L4KIN_MASSLESS
    )
    historical = ROOT.PairingStudy.selectCandidate(
        candidates, ROOT.PairingStudy.HISTORICAL_RUN2_MASSLESS
    )
    assert candidates[live].zFlavor == 11
    assert candidates[core].zFlavor == 13
    assert core == historical
    assert live != core


def test_zh_truth_is_label_sensitive_but_zz_truth_is_partition_invariant():
    truth = ROOT.PairingStudy.TruthResult()
    truth.recoverable = True
    truth.partitionValid = True
    truth.pair1a, truth.pair1b = 0, 2
    truth.pair2a, truth.pair2b = 1, 3

    nominal = ROOT.PairingStudy.Candidate()
    nominal.z1, nominal.z2 = 0, 2
    nominal.x1, nominal.x2 = 1, 3
    assert ROOT.PairingStudy.candidateCorrectZH(nominal, truth)
    assert ROOT.PairingStudy.candidateCorrectZZ(nominal, truth)

    label_swap = ROOT.PairingStudy.Candidate()
    label_swap.z1, label_swap.z2 = 1, 3
    label_swap.x1, label_swap.x2 = 0, 2
    assert not ROOT.PairingStudy.candidateCorrectZH(label_swap, truth)
    assert ROOT.PairingStudy.candidateCorrectZZ(label_swap, truth)

    wrong_partition = ROOT.PairingStudy.Candidate()
    wrong_partition.z1, wrong_partition.z2 = 0, 3
    wrong_partition.x1, wrong_partition.x2 = 1, 2
    assert not ROOT.PairingStudy.candidateCorrectZZ(wrong_partition, truth)


def test_alternative_scores_can_migrate_region_without_xflavor_migration():
    nearest_candidate = ROOT.PairingStudy.Candidate()
    nearest_candidate.dmZ = 1.0
    nearest_candidate.masslessDmZ = 2.0
    nearest_candidate.mX = 80.0
    nearest_candidate.xFlavor = 1

    massless_candidate = ROOT.PairingStudy.Candidate()
    massless_candidate.dmZ = 2.0
    massless_candidate.masslessDmZ = 1.0
    massless_candidate.mX = 50.0
    massless_candidate.xFlavor = 1

    candidates = _candidate_vector((nearest_candidate, massless_candidate))
    nearest = ROOT.PairingStudy.selectCandidate(
        candidates, ROOT.PairingStudy.NEAREST_MZ
    )
    massless = ROOT.PairingStudy.selectCandidate(
        candidates, ROOT.PairingStudy.CORE_L4KIN_MASSLESS
    )
    assert nearest == 0
    assert massless == 1
    assert candidates[nearest].xFlavor == candidates[massless].xFlavor == 1
    assert ROOT.PairingStudy.regionCode(candidates[nearest], 30.0, 150.0) == 1
    assert ROOT.PairingStudy.regionCode(candidates[massless], 40.0, 150.0) == 2

    xdf = ROOT.PairingStudy.Candidate()
    xdf.dmZ = 1.0
    xdf.mX = 50.0
    xdf.xFlavor = 2
    assert ROOT.PairingStudy.regionCode(xdf, 25.0, 120.0) == 3


def test_region_boundaries_are_strict():
    candidate = ROOT.PairingStudy.Candidate()
    candidate.xFlavor = 1
    candidate.mX = 80.0
    candidate.dmZ = 15.0
    assert ROOT.PairingStudy.regionCode(candidate, 30.0, 150.0) == 0
    candidate.dmZ = 14.999
    assert ROOT.PairingStudy.regionCode(candidate, 30.0, 150.0) == 1


def test_special_algorithm_never_selects_a_reduced_candidate_subset():
    first = ROOT.PairingStudy.Candidate()
    first.dmZ = 1.0
    first.masslessDmZ = 1.0
    first.resolutionValid = True
    first.pull = 2.0
    first.fsrValid = True
    first.fsrDmZ = 2.0
    first.fsrPull = 2.0

    second = ROOT.PairingStudy.Candidate()
    second.dmZ = 2.0
    second.masslessDmZ = 2.0
    # Missing uncertainty and FSR links invalidate the method for the whole
    # event; it must not appear to improve by considering `first` alone.
    second.resolutionValid = False
    second.fsrValid = False

    candidates = _candidate_vector((first, second))
    assert ROOT.PairingStudy.selectCandidate(
        candidates, ROOT.PairingStudy.NEAREST_MZ
    ) == 0
    for algorithm in (
        ROOT.PairingStudy.RESOLUTION_PULL,
        ROOT.PairingStudy.FSR_NEAREST_MZ,
        ROOT.PairingStudy.FSR_RESOLUTION_PULL,
    ):
        assert not ROOT.PairingStudy.algorithmScoresValid(candidates, algorithm)
        assert ROOT.PairingStudy.selectCandidate(candidates, algorithm) == -1
        assert list(ROOT.PairingStudy.scoreSummary(candidates, algorithm)) == [
            ROOT.PairingStudy.INVALID,
            ROOT.PairingStudy.INVALID,
            ROOT.PairingStudy.INVALID,
        ]


def test_event_level_gain_loss_axis_is_joint_and_domain_specific():
    event = ROOT.PairingStudy.EventResult()
    event.algorithmValid = _rvec_int((1, 1, 1, 0, 1, 1))
    event.zhTruth.recoverable = True
    event.zzTruth.partitionValid = True
    event.zhCorrect = _rvec_int((1, 0, 1, 1, 0, 1))
    event.zzCorrect = _rvec_int((0, 0, 1, 1, 0, 1))

    # ZH baseline is correct: comparator-only failures are losses.
    assert list(ROOT.PairingStudy.gainLossAxis(event, True)) == [
        3.0, 1.0, 3.0, -2.0, 1.0, 3.0
    ]
    # ZZ baseline is wrong: comparator-only successes are gains.
    assert list(ROOT.PairingStudy.gainLossAxis(event, False)) == [
        0.0, 0.0, 2.0, -2.0, 0.0, 2.0
    ]

    event.zzTruth.partitionValid = False
    assert list(ROOT.PairingStudy.gainLossAxis(event, False)) == [
        -1.0, -1.0, -1.0, -2.0, -1.0, -1.0
    ]

    # A missing reference algorithm makes every comparison unavailable.
    event.algorithmValid = _rvec_int((0, 1, 1, 1, 1, 1))
    assert list(ROOT.PairingStudy.gainLossAxis(event, True)) == [-2.0] * 6


def test_summary_decoder_uses_first_logical_axis_fastest():
    spec = importlib.util.spec_from_file_location(
        "pairing_make_summary", PAIRING_DIR / "make_summary.py"
    )
    assert spec is not None and spec.loader is not None
    make_summary = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(make_summary)

    shape = (2, 3, 4)
    sentinel = [0.0] * math.prod(shape)
    for x in range(shape[0]):
        for y in range(shape[1]):
            for z in range(shape[2]):
                value = float(100 * x + 10 * y + z)
                sentinel[make_summary._flat_index(shape, (x, y, z))] = value

    assert sentinel[:8] == [0.0, 100.0, 10.0, 110.0, 20.0, 120.0, 1.0, 101.0]
    assert make_summary._cell(sentinel, shape, 1, 2, 3) == 123.0
    # Fixing y=2,z=3 leaves x free: 23 + 123 = 146.
    assert make_summary._project(sentinel, shape, {1: 2, 2: 3}) == 146.0

    # The X-flavor closure has bin 0 for an unavailable algorithm and physical
    # bins 1=SF, 2=DF.  Unavailable<->physical transitions are diagnostics, not
    # SF<->DF migrations; only the latter may test the fixed-quartet theorem.
    closure_shape = (6, 3, 3)
    closure = [0.0] * math.prod(closure_shape)
    closure[make_summary._flat_index(closure_shape, (3, 1, 0))] = 11.0
    closure[make_summary._flat_index(closure_shape, (4, 0, 2))] = 13.0
    assert make_summary._physical_xflavor_offdiagonal(closure) == 0.0
    closure[make_summary._flat_index(closure_shape, (5, 1, 2))] = 1.0
    assert make_summary._physical_xflavor_offdiagonal(closure) == 1.0
