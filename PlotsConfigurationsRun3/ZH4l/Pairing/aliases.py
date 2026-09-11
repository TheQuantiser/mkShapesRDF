"""Cached aliases for the dual-domain four-lepton pairing study."""

from pathlib import Path

from common.eras import load_selected_era
from common.objects import build_object_aliases


def _config_dir():
    candidates = (
        globals().get("CONFIG_DIR"),
        globals().get("folder"),
        Path(__file__).resolve().parent if "__file__" in globals() else None,
        Path.cwd(),
    )
    for candidate in candidates:
        if not candidate:
            continue
        path = Path(candidate).resolve()
        if (path / "pairing_config.py").exists() or path.name == "Pairing":
            return path
    raise RuntimeError("Cannot resolve pairing configuration directory")


CONFIG_DIR = _config_dir()
FAMILY_DIR = CONFIG_DIR.parent
_, _ERA_CONFIG, _ = load_selected_era()
aliases, _SELECTED_WPS = build_object_aliases(
    _ERA_CONFIG, FAMILY_DIR, globals().get("AVAILABLE_BRANCHES")
)
_ELECTRON_WP = _SELECTED_WPS["electron_wp"]
_MUON_WP = _SELECTED_WPS["muon_wp"]
_MACRO = CONFIG_DIR / "macros" / "pairing.cc"

aliases["zh4l_internal_pairing_tight_mask"] = {
    "linesToAdd": [f'#include "{_MACRO}"'],
    "expr": (
        "PairingStudy::combineTightMask("
        "Lepton_pdgId, "
        f"Lepton_isTightElectron_{_ELECTRON_WP}, "
        f"Lepton_isTightMuon_{_MUON_WP})"
    ),
}

aliases["zh4l_internal_pairing_result"] = {
    "expr": (
        "PairingStudy::analyzeEvent("
        "Lepton_pt, Lepton_eta, Lepton_phi, Lepton_pdgId, zh4l_internal_pairing_tight_mask, "
        "VetoLepton_pt, VetoLepton_eta, VetoLepton_phi, VetoLepton_pdgId, "
        "VetoLepton_electronIdx, VetoLepton_muonIdx, "
        "Electron_pt, Electron_eta, Electron_energyErr, "
        "Electron_genPartIdx, Electron_fsrPhotonIdx, "
        "Muon_pt, Muon_ptErr, Muon_genPartIdx, Muon_fsrPhotonIdx, "
        "FsrPhoton_pt, FsrPhoton_eta, FsrPhoton_phi, "
        "FsrPhoton_electronIdx, FsrPhoton_muonIdx, "
        "GenPart_pdgId, GenPart_genPartIdxMother, GenPart_statusFlags, "
        "GenPart_pt, GenPart_eta, GenPart_phi, GenPart_mass, PuppiMET_pt)"
    )
}

_scalar_fields = {
    "pairing_pass_object_base": "zh4l_internal_pairing_result.objectBase",
    "pairing_pass_physics_base": "zh4l_internal_pairing_result.physBase",
    "pairing_quartet_is_valid": "zh4l_internal_pairing_result.quartetValid",
    "pairing_source_alignment_is_valid": "zh4l_internal_pairing_result.sourceAlignmentValid",
    "pairing_source_alignment_failure": "zh4l_internal_pairing_result.sourceAlignmentFailure",
    "pairing_resolution_scores_are_valid": "zh4l_internal_pairing_result.resolutionScoresValid",
    "pairing_fsr_scores_are_valid": "zh4l_internal_pairing_result.fsrScoresValid",
    "pairing_x_complement_is_identical": "zh4l_internal_pairing_result.xComplementIdentical",
    "pairing_x_difference_reason": "zh4l_internal_pairing_result.xDifferenceReason",
    "pairing_quartet_topology": "zh4l_internal_pairing_result.topology",
    "pairing_candidate_multiplicity": "zh4l_internal_pairing_result.nValidCandidates",
    "pairing_distinct_partitions": "zh4l_internal_pairing_result.nDistinctPartitions",
    "pairing_quartet_min_pair_mass": "zh4l_internal_pairing_result.minPairMass",
    "pairing_quartet_mass": "zh4l_internal_pairing_result.m4l",
    "zh_truth_status": "zh4l_internal_pairing_result.zhTruth.status",
    "zz_truth_status": "zh4l_internal_pairing_result.zzTruth.status",
    "zh_truth_z_pt": "zh4l_internal_pairing_result.zhTruth.referencePt",
    "zz_truth_z_pt": "zh4l_internal_pairing_result.zzTruth.referencePt",
    "zh_truth_is_recoverable": "zh4l_internal_pairing_result.zhTruth.recoverable",
    "zz_truth_is_recoverable": "zh4l_internal_pairing_result.zzTruth.partitionValid",
    "zh_truth_is_direct": "zh4l_internal_pairing_result.zhTruth.direct",
    "zz_truth_is_direct": "zh4l_internal_pairing_result.zzTruth.direct",
    "zh_hww_complement_is_valid": "zh4l_internal_pairing_result.zhTruth.hwwComplementValid",
    "zz_truth_identical_flavor_convention": "zh4l_internal_pairing_result.zzTruth.identicalFlavorConvention",
    "zz_truth_record_is_ambiguous": "zh4l_internal_pairing_result.zzTruth.recordAmbiguous",
}
for name, expression in _scalar_fields.items():
    aliases[name] = {"expr": expression}

aliases.update(
    {
        "algorithm_axis": {"expr": "PairingStudy::algorithmAxis()"},
        "quartet_topology_axis": {
            "expr": "PairingStudy::constantWeights(static_cast<float>(pairing_quartet_topology))"
        },
        "algorithm_valid_axis": {
            "expr": "PairingStudy::intToFloat(zh4l_internal_pairing_result.algorithmValid)"
        },
        "zh_correct_axis": {
            "expr": "PairingStudy::correctnessAxis(zh4l_internal_pairing_result, true)"
        },
        "zz_correct_axis": {
            "expr": "PairingStudy::correctnessAxis(zh4l_internal_pairing_result, false)"
        },
        "zh_gain_loss_axis": {
            "expr": "PairingStudy::gainLossAxis(zh4l_internal_pairing_result, true)"
        },
        "zz_gain_loss_axis": {
            "expr": "PairingStudy::gainLossAxis(zh4l_internal_pairing_result, false)"
        },
        "pairing_selected_candidate_axis": {
            "expr": "PairingStudy::intToFloat(zh4l_internal_pairing_result.selectedCandidate)"
        },
        "pairing_selected_z_flavor_axis": {
            "expr": "PairingStudy::intToFloat(zh4l_internal_pairing_result.selectedZFlavor)"
        },
        "pairing_best_score_axis": {
            "expr": "zh4l_internal_pairing_result.selectedScore"
        },
        "pairing_second_score_axis": {
            "expr": "zh4l_internal_pairing_result.secondScore"
        },
        "pairing_z_mass_axis": {"expr": "zh4l_internal_pairing_result.selectedMZ"},
        "pairing_x_mass_axis": {"expr": "zh4l_internal_pairing_result.selectedMX"},
        "pairing_z_pt_axis": {"expr": "zh4l_internal_pairing_result.selectedPtZ"},
        "pairing_x_pt_axis": {"expr": "zh4l_internal_pairing_result.selectedPtX"},
        "pairing_z_delta_r_axis": {"expr": "zh4l_internal_pairing_result.selectedDrZ"},
        "pairing_x_delta_r_axis": {"expr": "zh4l_internal_pairing_result.selectedDrX"},
        "pairing_score_gap_axis": {"expr": "zh4l_internal_pairing_result.scoreGap"},
        "pairing_region_axis": {
            "expr": "PairingStudy::intToFloat(zh4l_internal_pairing_result.region)"
        },
        "pairing_x_flavor_axis": {
            "expr": "PairingStudy::intToFloat(zh4l_internal_pairing_result.selectedXFlavor)"
        },
        "zh_truth_z_pt_axis": {
            "expr": "PairingStudy::truthPtAxis(zh4l_internal_pairing_result, true)"
        },
        "zz_truth_z_pt_axis": {
            "expr": "PairingStudy::truthPtAxis(zh4l_internal_pairing_result, false)"
        },
        "zh_z_pt_response_axis": {
            "expr": "PairingStudy::responsePtZ(zh4l_internal_pairing_result, true)"
        },
        "zz_z_pt_response_axis": {
            "expr": "PairingStudy::responsePtZ(zh4l_internal_pairing_result, false)"
        },
        "zh_truth_status_axis": {
            "expr": "PairingStudy::constantWeights(static_cast<float>(zh_truth_status))"
        },
        "zz_truth_status_axis": {
            "expr": "PairingStudy::constantWeights(static_cast<float>(zz_truth_status))"
        },
        "baseline_candidate_axis": {
            "expr": "PairingStudy::constantWeights(static_cast<float>(zh4l_internal_pairing_result.selectedCandidate[0]))"
        },
        "baseline_region_axis": {
            "expr": "PairingStudy::constantWeights(static_cast<float>(zh4l_internal_pairing_result.region[0]))"
        },
        "baseline_x_flavor_axis": {
            "expr": "PairingStudy::constantWeights(static_cast<float>(zh4l_internal_pairing_result.selectedXFlavor[0]))"
        },
    }
)

aliases["weight_raw"] = {"expr": "1.f", "afterNuis": True}
aliases["weight_nominal"] = {
    # `weight` carries luminosity, component source normalization, and any
    # configured component factor.  XS/PU are explicit here so the core
    # nonzero-weight prefilter cannot erase literal raw events.
    "expr": (
        "weight * static_cast<float>(XSWeight) * static_cast<float>(puWeight) * "
        "static_cast<float>(METFilter_Common)"
    ),
    "afterNuis": True,
}
aliases["weight_abs_nominal"] = {
    "expr": "abs(weight_nominal)",
    "afterNuis": True,
}
aliases["pairing_weight_raw"] = {
    "expr": "PairingStudy::constantWeights(1.f)",
    "afterNuis": True,
}
aliases["pairing_weight_nominal"] = {
    "expr": "PairingStudy::constantWeights(weight_nominal)",
    "afterNuis": True,
}
aliases["pairing_weight_abs_nominal"] = {
    "expr": "PairingStudy::constantWeights(weight_abs_nominal)",
    "afterNuis": True,
}
aliases["event_weight_sign"] = {
    "expr": "weight_nominal < 0.f ? -1.f : (weight_nominal > 0.f ? 1.f : 0.f)",
    "afterNuis": True,
}
