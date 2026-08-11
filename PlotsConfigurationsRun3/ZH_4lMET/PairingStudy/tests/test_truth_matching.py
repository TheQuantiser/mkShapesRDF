from pathlib import Path

import pytest


CONFIG_DIR = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def ROOT():
    root = pytest.importorskip("ROOT")
    macro = CONFIG_DIR / "macros" / "pairing_study.cc"
    assert root.gInterpreter.Declare(f'#include "{macro}"')
    return root


def _one_event(ROOT, definitions, results):
    frame = ROOT.RDataFrame(1)
    for name, expression in definitions:
        frame = frame.Define(name, expression)
    for name, (expression, _) in results.items():
        frame = frame.Define(name, expression)
    return {
        name: frame.Take[column_type](name).GetValue()[0]
        for name, (_, column_type) in results.items()
    }


def _flags(*bits):
    value = sum(1 << bit for bit in bits)
    return str(value)


SOURCE_DEFINITIONS = (
    ("quartet", "ROOT::RVecI{0,1,2,3}"),
    ("sourceMap", "ROOT::RVecI{0,1,2,3}"),
    ("sourcePdg", "ROOT::RVecI{-11,11,-13,13}"),
    ("sourceEle", "ROOT::RVecI{0,1,-1,-1}"),
    ("sourceMu", "ROOT::RVecI{-1,-1,0,1}"),
)


def _zh_direct_definitions():
    # The associated Z has first/last copies (0/1). Its direct electrons also
    # have first/last copies (2->3 and 4->5). A Higgs and two W lineages supply
    # the complementary reconstructed muons.
    return SOURCE_DEFINITIONS + (
        (
            "genPdg",
            "ROOT::RVecI{23,23,-11,-11,11,11,25,24,-24,-13,13}",
        ),
        ("genMother", "ROOT::RVecI{-1,0,1,2,1,4,-1,6,6,7,8}"),
        (
            "genFlags",
            "ROOT::RVecI{%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s}"
            % (
                _flags(7, 8, 12),
                _flags(8, 11, 13),
                _flags(8, 12),
                _flags(8, 13),
                _flags(8, 12),
                _flags(8, 13),
                _flags(7, 8, 13),
                _flags(8, 13),
                _flags(8, 13),
                _flags(8, 13),
                _flags(8, 13),
            ),
        ),
        ("genPt", "ROOT::RVecF{70,70,45,44,40,39,80,35,30,28,24}"),
        ("electronGen", "ROOT::RVecI{3,5}"),
        ("muonGen", "ROOT::RVecI{9,10}"),
        (
            "truth",
            "PairingStudy::buildZHTruth("
            "quartet,sourceMap,sourcePdg,sourceEle,sourceMu,"
            "electronGen,muonGen,genPdg,genMother,genFlags,genPt)",
        ),
    )


def _zz_direct_definitions(identical_flavor=False):
    if identical_flavor:
        source_pdg = "ROOT::RVecI{-11,11,-11,11}"
        source_ele = "ROOT::RVecI{0,1,2,3}"
        source_mu = "ROOT::RVecI{-1,-1,-1,-1}"
        gen_pdg = "ROOT::RVecI{23,23,-11,11,23,23,-11,11}"
        electron_gen = "ROOT::RVecI{2,3,6,7}"
        muon_gen = "ROOT::RVecI{}"
    else:
        source_pdg = "ROOT::RVecI{-11,11,-13,13}"
        source_ele = "ROOT::RVecI{0,1,-1,-1}"
        source_mu = "ROOT::RVecI{-1,-1,0,1}"
        gen_pdg = "ROOT::RVecI{23,23,-11,11,23,23,-13,13}"
        electron_gen = "ROOT::RVecI{2,3}"
        muon_gen = "ROOT::RVecI{6,7}"
    return (
        ("quartet", "ROOT::RVecI{0,1,2,3}"),
        ("sourceMap", "ROOT::RVecI{0,1,2,3}"),
        ("sourcePdg", source_pdg),
        ("sourceEle", source_ele),
        ("sourceMu", source_mu),
        ("electronGen", electron_gen),
        ("muonGen", muon_gen),
        ("genPdg", gen_pdg),
        ("genMother", "ROOT::RVecI{-1,0,1,1,-1,4,5,5}"),
        (
            "genFlags",
            "ROOT::RVecI{%s,%s,%s,%s,%s,%s,%s,%s}"
            % (
                _flags(7, 8, 12),
                _flags(8, 11, 13),
                _flags(8, 13),
                _flags(8, 13),
                _flags(7, 8, 12),
                _flags(8, 11, 13),
                _flags(8, 13),
                _flags(8, 13),
            ),
        ),
        ("genPt", "ROOT::RVecF{80,80,45,35,60,60,32,24}"),
        ("genEta", "ROOT::RVecF(8,0.f)"),
        ("genPhi", "ROOT::RVecF(8,0.f)"),
        ("genMass", "ROOT::RVecF{91,91,0,0,89,89,0,0}"),
        (
            "truth",
            "PairingStudy::buildZZTruth("
            "quartet,sourceMap,sourcePdg,sourceEle,sourceMu,"
            "electronGen,muonGen,genPdg,genMother,genFlags,"
            "genPt,genEta,genPhi,genMass)",
        ),
    )


def test_source_alignment_independent_component_permutation_fails_closed(ROOT):
    # This reproduces the historical failure mode seen in real v12 input:
    # eta remains in source order while phi and PDG ID are independently
    # swapped. No final tuple corresponds to either physical source electron.
    values = _one_event(
        ROOT,
        (
            (
                "finalPt",
                "ROOT::RVecF{45.f,40.f,30.f,25.f}",
            ),
            (
                "finalEta",
                "ROOT::RVecF{-1.6882324f,-1.796875f,0.2f,-0.3f}",
            ),
            (
                "finalPhi",
                "ROOT::RVecF{-1.7229004f,-0.7067871f,1.0f,-1.0f}",
            ),
            ("finalPdg", "ROOT::RVecI{-11,11,-13,13}"),
            (
                "sourcePt",
                "ROOT::RVecF{44.f,41.f,30.f,25.f}",
            ),
            (
                "sourceEta",
                "ROOT::RVecF{-1.6882324f,-1.796875f,0.2f,-0.3f}",
            ),
            (
                "sourcePhi",
                "ROOT::RVecF{-0.7067871f,-1.7229004f,1.0f,-1.0f}",
            ),
            ("sourcePdg", "ROOT::RVecI{11,-11,-13,13}"),
            ("quartet", "ROOT::RVecI{0,1,2,3}"),
            (
                "mapping",
                "PairingStudy::coherentSourceMap("
                "finalPt,finalEta,finalPhi,finalPdg,"
                "sourcePt,sourceEta,sourcePhi,sourcePdg,"
                "quartet)",
            ),
        ),
        {"mappingSize": ("int(mapping.size())", "int")},
    )
    assert values["mappingSize"] == 0


def test_source_alignment_requires_physical_source_pt_without_pt_equality(ROOT):
    values = _one_event(
        ROOT,
        (
            ("finalPt", "ROOT::RVecF{45.f,40.f,30.f,25.f}"),
            ("finalEta", "ROOT::RVecF{0.f,0.1f,0.2f,0.3f}"),
            ("finalPhi", "ROOT::RVecF{0.f,1.f,2.f,3.f}"),
            ("finalPdg", "ROOT::RVecI{-11,11,-13,13}"),
            ("sourcePt", "ROOT::RVecF{44.f,41.f,-1.f,26.f}"),
            ("sourceEta", "ROOT::RVecF{0.f,0.1f,0.2f,0.3f}"),
            ("sourcePhi", "ROOT::RVecF{0.f,1.f,2.f,3.f}"),
            ("sourcePdg", "ROOT::RVecI{-11,11,-13,13}"),
            ("quartet", "ROOT::RVecI{0,1,2,3}"),
            (
                "mapping",
                "PairingStudy::coherentSourceMap("
                "finalPt,finalEta,finalPhi,finalPdg,"
                "sourcePt,sourceEta,sourcePhi,sourcePdg,quartet)",
            ),
        ),
        {"mappingSize": ("int(mapping.size())", "int")},
    )
    assert values["mappingSize"] == 0


def test_truth_builders_mark_missing_source_alignment_invalid(ROOT):
    values = _one_event(
        ROOT,
        SOURCE_DEFINITIONS
        + (
            ("emptyMap", "ROOT::RVecI{}"),
            ("emptyI", "ROOT::RVecI{}"),
            ("emptyF", "ROOT::RVecF{}"),
            (
                "zh",
                "PairingStudy::buildZHTruth("
                "quartet,emptyMap,sourcePdg,sourceEle,sourceMu,emptyI,emptyI,"
                "emptyI,emptyI,emptyI,emptyF)",
            ),
            (
                "zz",
                "PairingStudy::buildZZTruth("
                "quartet,emptyMap,sourcePdg,sourceEle,sourceMu,emptyI,emptyI,"
                "emptyI,emptyI,emptyI,emptyF,emptyF,emptyF,emptyF)",
            ),
        ),
        {
            "zhStatus": ("zh.status", "int"),
            "zzStatus": ("zz.status", "int"),
        },
    )
    assert values == {
        "zhStatus": 6,  # TRUTH_ALIGNMENT_INVALID
        "zzStatus": 6,
    }


def test_zh_associated_z_copy_chain_and_hww_complement(ROOT):
    values = _one_event(
        ROOT,
        _zh_direct_definitions(),
        {
            "status": ("truth.status", "int"),
            "direct": ("truth.direct", "bool"),
            "recoverable": ("truth.recoverable", "bool"),
            "zPair": (
                "PairingStudy::samePair(truth.pair1a,truth.pair1b,0,1)",
                "bool",
            ),
            "hwwPair": (
                "PairingStudy::samePair(truth.pair2a,truth.pair2b,2,3)",
                "bool",
            ),
            "hwwComplement": ("truth.hwwComplementValid", "bool"),
        },
    )
    assert values == {
        "status": 4,
        "direct": True,
        "recoverable": True,
        "zPair": True,
        "hwwPair": True,
        "hwwComplement": True,
    }


def test_zh_duplicate_reco_to_gen_match_is_not_recoverable(ROOT):
    definitions = [
        (name, "ROOT::RVecI{3,3}" if name == "electronGen" else expression)
        for name, expression in _zh_direct_definitions()
    ]
    values = _one_event(
        ROOT,
        tuple(definitions),
        {
            "direct": ("truth.direct", "bool"),
            "recoverable": ("truth.recoverable", "bool"),
            "status": ("truth.status", "int"),
        },
    )
    assert values == {"direct": True, "recoverable": False, "status": 3}


def test_zh_rejects_higgs_descendant_z_when_finding_associated_z(ROOT):
    values = _one_event(
        ROOT,
        (
            # Z index 2 is last-copy but descends from H index 0. Z index 4 is
            # the unique non-Higgs associated lineage and must be selected.
            ("genPdg", "ROOT::RVecI{25,23,23,23,23}"),
            ("genMother", "ROOT::RVecI{-1,0,1,-1,3}"),
            (
                "genFlags",
                "ROOT::RVecI{%s,%s,%s,%s,%s}"
                % (
                    _flags(7, 8, 13),
                    _flags(7, 8, 12),
                    _flags(8, 11, 13),
                    _flags(7, 8, 12),
                    _flags(8, 11, 13),
                ),
            ),
        ),
        {
            "associated": (
                "PairingStudy::associatedZIndex(genPdg,genMother,genFlags)",
                "int",
            )
        },
    )
    # The helper returns the canonical first copy of the accepted lineage.
    assert values["associated"] == 3


def test_zh_multiple_non_higgs_hard_z_lineages_are_ambiguous(ROOT):
    values = _one_event(
        ROOT,
        SOURCE_DEFINITIONS
        + (
            ("genPdg", "ROOT::RVecI{23,23,23,23}"),
            ("genMother", "ROOT::RVecI{-1,0,-1,2}"),
            (
                "genFlags",
                "ROOT::RVecI{%s,%s,%s,%s}"
                % (
                    _flags(7, 8, 12),
                    _flags(8, 11, 13),
                    _flags(7, 8, 12),
                    _flags(8, 11, 13),
                ),
            ),
            ("empty", "ROOT::RVecI{}"),
            ("genPt", "ROOT::RVecF{80,80,60,60}"),
            (
                "truth",
                "PairingStudy::buildZHTruth("
                "quartet,sourceMap,sourcePdg,sourceEle,sourceMu,empty,empty,"
                "genPdg,genMother,genFlags,genPt)",
            ),
        ),
        {
            "associated": (
                "PairingStudy::associatedZIndex(genPdg,genMother,genFlags)",
                "int",
            ),
            "status": ("truth.status", "int"),
            "recoverable": ("truth.recoverable", "bool"),
        },
    )
    assert values == {"associated": -2, "status": 5, "recoverable": False}


def test_zh_tau_decay_is_separate_and_not_recoverable(ROOT):
    values = _one_event(
        ROOT,
        SOURCE_DEFINITIONS
        + (
            ("genPdg", "ROOT::RVecI{23,23,-15,15,-11,11,-13,13}"),
            ("genMother", "ROOT::RVecI{-1,0,1,1,2,3,-1,-1}"),
            (
                "genFlags",
                "ROOT::RVecI{%s,%s,%s,%s,%s,%s,%s,%s}"
                % (
                    _flags(7, 8, 12),
                    _flags(8, 11, 13),
                    _flags(8, 13),
                    _flags(8, 13),
                    _flags(8, 13),
                    _flags(8, 13),
                    _flags(13),
                    _flags(13),
                ),
            ),
            ("genPt", "ROOT::RVecF(8,30.f)"),
            ("electronGen", "ROOT::RVecI{4,5}"),
            ("muonGen", "ROOT::RVecI{6,7}"),
            (
                "truth",
                "PairingStudy::buildZHTruth("
                "quartet,sourceMap,sourcePdg,sourceEle,sourceMu,"
                "electronGen,muonGen,genPdg,genMother,genFlags,genPt)",
            ),
        ),
        {
            "status": ("truth.status", "int"),
            "direct": ("truth.direct", "bool"),
            "recoverable": ("truth.recoverable", "bool"),
        },
    )
    assert values == {"status": 2, "direct": False, "recoverable": False}


def test_zh_nonleptonic_intermediate_is_not_a_direct_z_daughter(ROOT):
    values = _one_event(
        ROOT,
        SOURCE_DEFINITIONS
        + (
            # The electrons descend from b hadrons produced by the Z. They
            # must not be promoted to direct Z daughters merely because a Z
            # appears somewhere in their ancestry.
            ("genPdg", "ROOT::RVecI{23,23,-5,5,-11,11,-13,13}"),
            ("genMother", "ROOT::RVecI{-1,0,1,1,2,3,-1,-1}"),
            (
                "genFlags",
                "ROOT::RVecI{%s,%s,%s,%s,%s,%s,%s,%s}"
                % (
                    _flags(7, 8, 12),
                    _flags(8, 11, 13),
                    _flags(8, 13),
                    _flags(8, 13),
                    _flags(13),
                    _flags(13),
                    _flags(13),
                    _flags(13),
                ),
            ),
            ("genPt", "ROOT::RVecF(8,30.f)"),
            ("electronGen", "ROOT::RVecI{4,5}"),
            ("muonGen", "ROOT::RVecI{6,7}"),
            (
                "truth",
                "PairingStudy::buildZHTruth("
                "quartet,sourceMap,sourcePdg,sourceEle,sourceMu,"
                "electronGen,muonGen,genPdg,genMother,genFlags,genPt)",
            ),
        ),
        {
            "status": ("truth.status", "int"),
            "direct": ("truth.direct", "bool"),
            "recoverable": ("truth.recoverable", "bool"),
        },
    )
    assert values == {"status": 3, "direct": False, "recoverable": False}


def test_zz_direct_2e2mu_partition_is_label_invariant(ROOT):
    values = _one_event(
        ROOT,
        _zz_direct_definitions(),
        {
            "status": ("truth.status", "int"),
            "valid": ("truth.partitionValid", "bool"),
            "identical": ("truth.identicalFlavorConvention", "bool"),
            "nominal": (
                "PairingStudy::candidateCorrectZZ("
                "PairingStudy::Candidate{0,1,2,3},truth)",
                "bool",
            ),
            "bosonSwap": (
                "PairingStudy::candidateCorrectZZ("
                "PairingStudy::Candidate{2,3,0,1},truth)",
                "bool",
            ),
            "crossPair": (
                "PairingStudy::candidateCorrectZZ("
                "PairingStudy::Candidate{0,2,1,3},truth)",
                "bool",
            ),
        },
    )
    assert values == {
        "status": 4,
        "valid": True,
        "identical": False,
        "nominal": True,
        "bosonSwap": True,
        "crossPair": False,
    }


@pytest.mark.parametrize("identical_flavor", [True])
def test_zz_identical_flavor_is_generator_record_convention(ROOT, identical_flavor):
    values = _one_event(
        ROOT,
        _zz_direct_definitions(identical_flavor=identical_flavor),
        {
            "valid": ("truth.partitionValid", "bool"),
            "identical": ("truth.identicalFlavorConvention", "bool"),
            "ambiguous": ("truth.recordAmbiguous", "bool"),
            "recordPartition": (
                "PairingStudy::candidateCorrectZZ("
                "PairingStudy::Candidate{0,1,2,3},truth)",
                "bool",
            ),
            "alternatePartition": (
                "PairingStudy::candidateCorrectZZ("
                "PairingStudy::Candidate{0,3,1,2},truth)",
                "bool",
            ),
        },
    )
    assert values == {
        "valid": True,
        "identical": True,
        "ambiguous": True,
        "recordPartition": True,
        "alternatePartition": False,
    }


def test_zz_direct_four_lepton_is_independent_of_reco_partition(ROOT):
    definitions = [
        (name, "ROOT::RVecI{}" if name == "muonGen" else expression)
        for name, expression in _zz_direct_definitions()
    ]
    values = _one_event(
        ROOT,
        tuple(definitions),
        {
            "direct": ("truth.direct", "bool"),
            "recoverable": ("truth.recoverable", "bool"),
            "valid": ("truth.partitionValid", "bool"),
            "status": ("truth.status", "int"),
        },
    )
    assert values == {
        "direct": True,
        "recoverable": False,
        "valid": False,
        "status": 3,
    }


def test_zz_duplicated_reco_match_is_not_a_valid_partition(ROOT):
    definitions = list(_zz_direct_definitions())
    definitions = [
        (name, "ROOT::RVecI{2,2}" if name == "electronGen" else expression)
        for name, expression in definitions
    ]
    values = _one_event(
        ROOT,
        tuple(definitions),
        {
            "status": ("truth.status", "int"),
            "recoverable": ("truth.recoverable", "bool"),
            "valid": ("truth.partitionValid", "bool"),
        },
    )
    assert values == {"status": 3, "recoverable": False, "valid": False}


def test_zz_tau_lineage_is_diagnostic_not_direct_four_lepton_truth(ROOT):
    values = _one_event(
        ROOT,
        (
            ("quartet", "ROOT::RVecI{0,1,2,3}"),
            ("sourceMap", "ROOT::RVecI{0,1,2,3}"),
            ("sourcePdg", "ROOT::RVecI{-11,11,-13,13}"),
            ("sourceEle", "ROOT::RVecI{0,1,-1,-1}"),
            ("sourceMu", "ROOT::RVecI{-1,-1,0,1}"),
            ("electronGen", "ROOT::RVecI{2,3}"),
            ("muonGen", "ROOT::RVecI{8,9}"),
            (
                "genPdg",
                "ROOT::RVecI{23,23,-11,11,23,23,-15,15,-13,13}",
            ),
            ("genMother", "ROOT::RVecI{-1,0,1,1,-1,4,5,5,6,7}"),
            (
                "genFlags",
                "ROOT::RVecI{%s,%s,%s,%s,%s,%s,%s,%s,%s,%s}"
                % (
                    _flags(7, 8, 12),
                    _flags(8, 11, 13),
                    _flags(8, 13),
                    _flags(8, 13),
                    _flags(7, 8, 12),
                    _flags(8, 11, 13),
                    _flags(8, 13),
                    _flags(8, 13),
                    _flags(8, 13),
                    _flags(8, 13),
                ),
            ),
            ("genPt", "ROOT::RVecF(10,30.f)"),
            ("genEta", "ROOT::RVecF(10,0.f)"),
            ("genPhi", "ROOT::RVecF(10,0.f)"),
            ("genMass", "ROOT::RVecF(10,0.f)"),
            (
                "truth",
                "PairingStudy::buildZZTruth("
                "quartet,sourceMap,sourcePdg,sourceEle,sourceMu,"
                "electronGen,muonGen,genPdg,genMother,genFlags,"
                "genPt,genEta,genPhi,genMass)",
            ),
        ),
        {
            "status": ("truth.status", "int"),
            "direct": ("truth.direct", "bool"),
            "valid": ("truth.partitionValid", "bool"),
        },
    )
    assert values == {"status": 2, "direct": False, "valid": False}
