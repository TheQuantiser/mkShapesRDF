"""Compact histogram registry for the ZH/ZZ pairing comparison."""

variables = {}


def _hist(name, expression, axis, weight="StudySignedWeight", fold=0):
    variables[name] = {
        "name": expression,
        "range": axis,
        "xaxis": name,
        "fold": fold,
        "studyWeight": weight,
    }


def _cube(name, expression, axis, weight):
    _hist(name, expression, axis, weight)


ALGO = (6, -0.5, 5.5)
TOPO = (5, 0.5, 5.5)
# Correctness status: -2 algorithm unavailable, -1 truth unavailable,
# 0 truth-recoverable wrong assignment, 1 truth-recoverable correct assignment.
CORRECT = (4, -2.5, 1.5)
# Relative to algorithm 0: -2 comparator unavailable, -1 truth unavailable,
# 0 both wrong, 1 baseline-only correct (loss), 2 comparator-only correct
# (gain), 3 both correct.
GAINLOSS = (6, -2.5, 3.5)
STATUS = (7, -0.5, 6.5)
VALID = (2, -0.5, 1.5)
REGION = (4, -0.5, 3.5)
XFLAVOR = (3, -0.5, 2.5)
CANDIDATE = (8, -1.5, 6.5)

for process, correct in (("zh", "ZHCorrectAxis"), ("zz", "ZZCorrectAxis")):
    for convention, weight in (
        ("raw", "StudyRawWeightVec"),
        ("signed", "StudySignedWeightVec"),
        ("absolute", "StudyAbsWeightVec"),
    ):
        _cube(
            f"{process}_efficiency_{convention}",
            f"AlgorithmAxis:QuartetTopologyAxis:{correct}",
            ALGO + TOPO + CORRECT,
            weight,
        )

for process, outcome in (("zh", "ZHGainLossAxis"), ("zz", "ZZGainLossAxis")):
    for convention, weight in (
        ("raw", "StudyRawWeightVec"),
        ("signed", "StudySignedWeightVec"),
        ("absolute", "StudyAbsWeightVec"),
    ):
        _cube(
            f"{process}_gain_loss_{convention}",
            f"AlgorithmAxis:{outcome}",
            ALGO + GAINLOSS,
            weight,
        )

_hist(
    "zh_truth_status_topology",
    "ZHTruthStatus:QuartetTopology",
    STATUS + TOPO,
    "StudyRawWeight",
)
_hist(
    "zz_truth_status_topology",
    "ZZTruthStatus:QuartetTopology",
    STATUS + TOPO,
    "StudyRawWeight",
)
_hist(
    "zh_truth_direct_topology",
    "ZHTruthDirect:QuartetTopology",
    VALID + TOPO,
    "StudyRawWeight",
)
_hist(
    "zz_truth_direct_topology",
    "ZZTruthDirect:QuartetTopology",
    VALID + TOPO,
    "StudyRawWeight",
)
_hist(
    "algorithm_validity",
    "AlgorithmAxis:AlgorithmValidAxis",
    ALGO + VALID,
    "StudyRawWeightVec",
)
_hist(
    "candidate_multiplicity",
    "PairingCandidateMultiplicity",
    (7, -0.5, 6.5),
    "StudyRawWeight",
)
_hist(
    "distinct_partition_multiplicity",
    "PairingDistinctPartitions",
    (4, -0.5, 3.5),
    "StudyRawWeight",
)
_hist("quartet_topology", "QuartetTopology", TOPO, "StudyRawWeight")
_hist(
    "minimum_pair_mass",
    "PairingMinPairMass",
    (80, 0.0, 160.0),
    "StudySignedWeight",
)
_hist("m4l", "PairingM4l", (100, 60.0, 560.0), "StudySignedWeight")
_hist(
    "source_alignment_valid",
    "PairingSourceAlignmentValid",
    VALID,
    "StudyRawWeight",
)
_hist(
    "source_alignment_failure",
    "PairingSourceAlignmentFailure",
    (4, -0.5, 3.5),
    "StudyRawWeight",
)
_hist(
    "resolution_scores_valid",
    "PairingResolutionScoresValid",
    VALID,
    "StudyRawWeight",
)
_hist(
    "fsr_scores_valid",
    "PairingFSRScoresValid",
    VALID,
    "StudyRawWeight",
)
_hist(
    "x_complement_identical",
    "PairingXComplementIdentical",
    VALID,
    "StudyRawWeight",
)
_hist(
    "x_difference_reason",
    "PairingXDifferenceReason",
    (4, -0.5, 3.5),
    "StudyRawWeight",
)
_hist(
    "zh_hww_complement_valid",
    "ZHHWWComplementValid",
    VALID,
    "StudyRawWeight",
)
_hist(
    "zz_identical_flavor_convention",
    "ZZTruthIdenticalFlavorConvention",
    VALID,
    "StudyRawWeight",
)
_hist(
    "zz_record_ambiguous",
    "ZZTruthRecordAmbiguous",
    VALID,
    "StudyRawWeight",
)

for name, expression, bins in (
    ("selected_mz", "PairingMZAxis", (100, 0.0, 200.0)),
    ("selected_mx", "PairingMXAxis", (100, 0.0, 200.0)),
    ("selected_ptz", "PairingPtZAxis", (80, 0.0, 400.0)),
    ("selected_ptx", "PairingPtXAxis", (80, 0.0, 400.0)),
    ("selected_drz", "PairingDrZAxis", (60, 0.0, 6.0)),
    ("selected_drx", "PairingDrXAxis", (60, 0.0, 6.0)),
    ("score_gap", "PairingScoreGapAxis", (80, 0.0, 40.0)),
):
    _hist(
        name,
        f"AlgorithmAxis:{expression}",
        ALGO + bins,
        "StudySignedWeightVec",
    )

_hist(
    "selected_z_flavor",
    "AlgorithmAxis:PairingSelectedZFlavorAxis",
    ALGO + (14, -0.5, 13.5),
    "StudyRawWeightVec",
)
for name, expression in (
    ("best_score", "PairingBestScoreAxis"),
    ("second_best_score", "PairingSecondScoreAxis"),
):
    _hist(
        name,
        f"AlgorithmAxis:{expression}",
        ALGO + (120, 0.0, 120.0),
        "StudyRawWeightVec",
        fold=2,
    )

_hist(
    "zh_correct_vs_truth_ptz",
    "AlgorithmAxis:ZHTruthPtZAxis:ZHCorrectAxis",
    ALGO + (60, 0.0, 300.0) + CORRECT,
    "StudyRawWeightVec",
)
_hist(
    "zz_correct_vs_truth_ptz",
    "AlgorithmAxis:ZZTruthPtZAxis:ZZCorrectAxis",
    ALGO + (60, 0.0, 300.0) + CORRECT,
    "StudyRawWeightVec",
)
_hist(
    "zh_ptz_response",
    "AlgorithmAxis:ZHPtZResponseAxis:ZHCorrectAxis",
    ALGO + (80, -2.0, 2.0) + CORRECT,
    "StudySignedWeightVec",
)
_hist(
    "zz_ptz_response",
    "AlgorithmAxis:ZZPtZResponseAxis:ZZCorrectAxis",
    ALGO + (80, -2.0, 2.0) + CORRECT,
    "StudySignedWeightVec",
)
_hist(
    "candidate_migration",
    "AlgorithmAxis:BaselineCandidateAxis:PairingSelectedCandidateAxis",
    ALGO + CANDIDATE + CANDIDATE,
    "StudyRawWeightVec",
)
_hist(
    "region_migration",
    "AlgorithmAxis:BaselineRegionAxis:PairingRegionAxis",
    ALGO + REGION + REGION,
    "StudySignedWeightVec",
)
_hist(
    "region_migration_raw",
    "AlgorithmAxis:BaselineRegionAxis:PairingRegionAxis",
    ALGO + REGION + REGION,
    "StudyRawWeightVec",
)
_hist(
    "region_migration_absolute",
    "AlgorithmAxis:BaselineRegionAxis:PairingRegionAxis",
    ALGO + REGION + REGION,
    "StudyAbsWeightVec",
)
_hist(
    "xflavor_closure",
    "AlgorithmAxis:BaselineXFlavorAxis:PairingXFlavorAxis",
    ALGO + XFLAVOR + XFLAVOR,
    "StudyRawWeightVec",
)
_hist(
    "selected_region",
    "AlgorithmAxis:PairingRegionAxis",
    ALGO + REGION,
    "StudySignedWeightVec",
)
_hist(
    "zh_score_gap_correctness",
    "AlgorithmAxis:PairingScoreGapAxis:ZHCorrectAxis",
    ALGO + (80, 0.0, 40.0) + CORRECT,
    "StudyRawWeightVec",
)
_hist(
    "zz_score_gap_correctness",
    "AlgorithmAxis:PairingScoreGapAxis:ZZCorrectAxis",
    ALGO + (80, 0.0, 40.0) + CORRECT,
    "StudyRawWeightVec",
)
_hist(
    "signed_event_weight",
    "StudySignedWeight",
    (100, -0.1, 0.1),
    "StudyRawWeight",
)
_hist(
    "event_weight_sign",
    "StudyWeightSign",
    (3, -1.5, 1.5),
    "StudyRawWeight",
)
