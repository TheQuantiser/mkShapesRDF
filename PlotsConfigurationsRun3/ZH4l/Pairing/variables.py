"""Compact histogram registry for the ZH/ZZ pairing comparison."""

from common.outputs import branches, with_tree_outputs

variables = {}


def _hist(name, expression, axis, weight="weight_nominal", fold=0):
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

for process, correct in (("zh", "zh_correct_axis"), ("zz", "zz_correct_axis")):
    for convention, weight in (
        ("raw", "pairing_weight_raw"),
        ("signed", "pairing_weight_nominal"),
        ("absolute", "pairing_weight_abs_nominal"),
    ):
        _cube(
            f"{process}_efficiency_{convention}",
            f"algorithm_axis:quartet_topology_axis:{correct}",
            ALGO + TOPO + CORRECT,
            weight,
        )

for process, outcome in (("zh", "zh_gain_loss_axis"), ("zz", "zz_gain_loss_axis")):
    for convention, weight in (
        ("raw", "pairing_weight_raw"),
        ("signed", "pairing_weight_nominal"),
        ("absolute", "pairing_weight_abs_nominal"),
    ):
        _cube(
            f"{process}_gain_loss_{convention}",
            f"algorithm_axis:{outcome}",
            ALGO + GAINLOSS,
            weight,
        )

_hist(
    "zh_truth_status_topology",
    "zh_truth_status:pairing_quartet_topology",
    STATUS + TOPO,
    "weight_raw",
)
_hist(
    "zz_truth_status_topology",
    "zz_truth_status:pairing_quartet_topology",
    STATUS + TOPO,
    "weight_raw",
)
_hist(
    "zh_truth_direct_topology",
    "zh_truth_is_direct:pairing_quartet_topology",
    VALID + TOPO,
    "weight_raw",
)
_hist(
    "zz_truth_direct_topology",
    "zz_truth_is_direct:pairing_quartet_topology",
    VALID + TOPO,
    "weight_raw",
)
_hist(
    "algorithm_validity",
    "algorithm_axis:algorithm_valid_axis",
    ALGO + VALID,
    "pairing_weight_raw",
)
_hist(
    "candidate_multiplicity",
    "pairing_candidate_multiplicity",
    (7, -0.5, 6.5),
    "weight_raw",
)
_hist(
    "distinct_partition_multiplicity",
    "pairing_distinct_partitions",
    (4, -0.5, 3.5),
    "weight_raw",
)
_hist("quartet_topology", "pairing_quartet_topology", TOPO, "weight_raw")
_hist(
    "minimum_pair_mass",
    "pairing_quartet_min_pair_mass",
    (80, 0.0, 160.0),
    "weight_nominal",
)
_hist(
    "pairing_quartet_mass", "pairing_quartet_mass", (100, 60.0, 560.0), "weight_nominal"
)
_hist(
    "source_alignment_valid",
    "pairing_source_alignment_is_valid",
    VALID,
    "weight_raw",
)
_hist(
    "source_alignment_failure",
    "pairing_source_alignment_failure",
    (4, -0.5, 3.5),
    "weight_raw",
)
_hist(
    "resolution_scores_valid",
    "pairing_resolution_scores_are_valid",
    VALID,
    "weight_raw",
)
_hist(
    "fsr_scores_valid",
    "pairing_fsr_scores_are_valid",
    VALID,
    "weight_raw",
)
_hist(
    "x_complement_identical",
    "pairing_x_complement_is_identical",
    VALID,
    "weight_raw",
)
_hist(
    "x_difference_reason",
    "pairing_x_difference_reason",
    (4, -0.5, 3.5),
    "weight_raw",
)
_hist(
    "zh_hww_complement_valid",
    "zh_hww_complement_is_valid",
    VALID,
    "weight_raw",
)
_hist(
    "zz_identical_flavor_convention",
    "zz_truth_identical_flavor_convention",
    VALID,
    "weight_raw",
)
_hist(
    "zz_record_ambiguous",
    "zz_truth_record_is_ambiguous",
    VALID,
    "weight_raw",
)

for name, expression, bins in (
    ("selected_z_mass", "pairing_z_mass_axis", (100, 0.0, 200.0)),
    ("selected_x_mass", "pairing_x_mass_axis", (100, 0.0, 200.0)),
    ("selected_z_pt", "pairing_z_pt_axis", (80, 0.0, 400.0)),
    ("selected_x_pt", "pairing_x_pt_axis", (80, 0.0, 400.0)),
    ("selected_z_delta_r", "pairing_z_delta_r_axis", (60, 0.0, 6.0)),
    ("selected_x_delta_r", "pairing_x_delta_r_axis", (60, 0.0, 6.0)),
    ("score_gap", "pairing_score_gap_axis", (80, 0.0, 40.0)),
):
    _hist(
        name,
        f"algorithm_axis:{expression}",
        ALGO + bins,
        "pairing_weight_nominal",
    )

_hist(
    "selected_z_flavor",
    "algorithm_axis:pairing_selected_z_flavor_axis",
    ALGO + (14, -0.5, 13.5),
    "pairing_weight_raw",
)
for name, expression in (
    ("best_score", "pairing_best_score_axis"),
    ("second_best_score", "pairing_second_score_axis"),
):
    _hist(
        name,
        f"algorithm_axis:{expression}",
        ALGO + (120, 0.0, 120.0),
        "pairing_weight_raw",
        fold=2,
    )

_hist(
    "zh_correct_vs_truth_z_pt",
    "algorithm_axis:zh_truth_z_pt_axis:zh_correct_axis",
    ALGO + (60, 0.0, 300.0) + CORRECT,
    "pairing_weight_raw",
)
_hist(
    "zz_correct_vs_truth_z_pt",
    "algorithm_axis:zz_truth_z_pt_axis:zz_correct_axis",
    ALGO + (60, 0.0, 300.0) + CORRECT,
    "pairing_weight_raw",
)
_hist(
    "zh_z_pt_response",
    "algorithm_axis:zh_z_pt_response_axis:zh_correct_axis",
    ALGO + (80, -2.0, 2.0) + CORRECT,
    "pairing_weight_nominal",
)
_hist(
    "zz_z_pt_response",
    "algorithm_axis:zz_z_pt_response_axis:zz_correct_axis",
    ALGO + (80, -2.0, 2.0) + CORRECT,
    "pairing_weight_nominal",
)
_hist(
    "candidate_migration",
    "algorithm_axis:baseline_candidate_axis:pairing_selected_candidate_axis",
    ALGO + CANDIDATE + CANDIDATE,
    "pairing_weight_raw",
)
_hist(
    "region_migration",
    "algorithm_axis:baseline_region_axis:pairing_region_axis",
    ALGO + REGION + REGION,
    "pairing_weight_nominal",
)
_hist(
    "region_migration_raw",
    "algorithm_axis:baseline_region_axis:pairing_region_axis",
    ALGO + REGION + REGION,
    "pairing_weight_raw",
)
_hist(
    "region_migration_absolute",
    "algorithm_axis:baseline_region_axis:pairing_region_axis",
    ALGO + REGION + REGION,
    "pairing_weight_abs_nominal",
)
_hist(
    "xflavor_closure",
    "algorithm_axis:baseline_x_flavor_axis:pairing_x_flavor_axis",
    ALGO + XFLAVOR + XFLAVOR,
    "pairing_weight_raw",
)
_hist(
    "selected_region",
    "algorithm_axis:pairing_region_axis",
    ALGO + REGION,
    "pairing_weight_nominal",
)
_hist(
    "zh_score_gap_correctness",
    "algorithm_axis:pairing_score_gap_axis:zh_correct_axis",
    ALGO + (80, 0.0, 40.0) + CORRECT,
    "pairing_weight_raw",
)
_hist(
    "zz_score_gap_correctness",
    "algorithm_axis:pairing_score_gap_axis:zz_correct_axis",
    ALGO + (80, 0.0, 40.0) + CORRECT,
    "pairing_weight_raw",
)
_hist(
    "signed_event_weight",
    "weight_nominal",
    (100, -0.1, 0.1),
    "weight_raw",
)
_hist(
    "event_weight_sign",
    "event_weight_sign",
    (3, -1.5, 1.5),
    "weight_raw",
)

# Event projections use the same cached pairing result and physical weights.

variables = with_tree_outputs(
    variables,
    globals().get("cuts", {}),
    branches(
        "identity",
        "source",
        extra={
            "pairing_quartet_lepton_index": "zh4l_internal_pairing_result.quartet",
            "pairing_candidate_choice": "zh4l_internal_pairing_result.selectedCandidate",
            "pairing_candidate_z_mass": "zh4l_internal_pairing_result.selectedMZ",
            "pairing_candidate_x_mass": "zh4l_internal_pairing_result.selectedMX",
            "weight_raw": "weight_raw",
            "weight_nominal": "weight_nominal",
            "weight_abs_nominal": "weight_abs_nominal",
        },
    ),
    tree_weight="weight_nominal",
)
