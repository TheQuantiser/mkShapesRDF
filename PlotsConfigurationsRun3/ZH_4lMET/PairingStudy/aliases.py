"""Cached aliases for the dual-domain four-lepton pairing study."""

import json
import os
from pathlib import Path


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
        if (path / "pairing_config.py").exists() or path.name == "PairingStudy":
            return path
    raise RuntimeError("Cannot resolve PairingStudy configuration directory")


CONFIG_DIR = _config_dir()
REPO_ROOT = CONFIG_DIR.parents[2]
YEAR_CONFIG_PATH = CONFIG_DIR.parent / "ZZ_CR" / "year_config.json"
with YEAR_CONFIG_PATH.open() as handle:
    _YEAR_SOURCE = json.load(handle)

_lepton_ids = _YEAR_SOURCE["year_defaults"]["lepton_ids"]
_ELECTRON_WP = _lepton_ids["electron_wp"]
_MUON_WP = _lepton_ids["muon_wp"]

aliases = {}
_MACRO = REPO_ROOT / "PlotsConfigurationsRun3" / "ZH_4lMET" / "PairingStudy" / "macros" / "pairing_study.cc"

aliases["PairingTightMask"] = {
    "linesToAdd": [f'#include "{_MACRO}"'],
    "expr": (
        "PairingStudy::combineTightMask("
        "Lepton_pdgId, "
        f"Lepton_isTightElectron_{_ELECTRON_WP}, "
        f"Lepton_isTightMuon_{_MUON_WP})"
    ),
}

aliases["PairingEvent"] = {
    "expr": (
        "PairingStudy::analyzeEvent("
        "Lepton_pt, Lepton_eta, Lepton_phi, Lepton_pdgId, PairingTightMask, "
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
    "PairingObjectBase": "PairingEvent.objectBase",
    "PairingPhysBase": "PairingEvent.physBase",
    "PairingQuartetValid": "PairingEvent.quartetValid",
    "PairingSourceAlignmentValid": "PairingEvent.sourceAlignmentValid",
    "PairingSourceAlignmentFailure": "PairingEvent.sourceAlignmentFailure",
    "PairingResolutionScoresValid": "PairingEvent.resolutionScoresValid",
    "PairingFSRScoresValid": "PairingEvent.fsrScoresValid",
    "PairingXComplementIdentical": "PairingEvent.xComplementIdentical",
    "PairingXDifferenceReason": "PairingEvent.xDifferenceReason",
    "QuartetTopology": "PairingEvent.topology",
    "PairingCandidateMultiplicity": "PairingEvent.nValidCandidates",
    "PairingDistinctPartitions": "PairingEvent.nDistinctPartitions",
    "PairingMinPairMass": "PairingEvent.minPairMass",
    "PairingM4l": "PairingEvent.m4l",
    "ZHTruthStatus": "PairingEvent.zhTruth.status",
    "ZZTruthStatus": "PairingEvent.zzTruth.status",
    "ZHTruthPtZ": "PairingEvent.zhTruth.referencePt",
    "ZZTruthPtZ": "PairingEvent.zzTruth.referencePt",
    "ZHTruthRecoverable": "PairingEvent.zhTruth.recoverable",
    "ZZTruthRecoverable": "PairingEvent.zzTruth.partitionValid",
    "ZHTruthDirect": "PairingEvent.zhTruth.direct",
    "ZZTruthDirect": "PairingEvent.zzTruth.direct",
    "ZHHWWComplementValid": "PairingEvent.zhTruth.hwwComplementValid",
    "ZZTruthIdenticalFlavorConvention": "PairingEvent.zzTruth.identicalFlavorConvention",
    "ZZTruthRecordAmbiguous": "PairingEvent.zzTruth.recordAmbiguous",
}
for name, expression in _scalar_fields.items():
    aliases[name] = {"expr": expression}

aliases.update(
    {
        "AlgorithmAxis": {"expr": "PairingStudy::algorithmAxis()"},
        "QuartetTopologyAxis": {
            "expr": "PairingStudy::constantWeights(static_cast<float>(QuartetTopology))"
        },
        "AlgorithmValidAxis": {
            "expr": "PairingStudy::intToFloat(PairingEvent.algorithmValid)"
        },
        "ZHCorrectAxis": {
            "expr": "PairingStudy::correctnessAxis(PairingEvent, true)"
        },
        "ZZCorrectAxis": {
            "expr": "PairingStudy::correctnessAxis(PairingEvent, false)"
        },
        "ZHGainLossAxis": {
            "expr": "PairingStudy::gainLossAxis(PairingEvent, true)"
        },
        "ZZGainLossAxis": {
            "expr": "PairingStudy::gainLossAxis(PairingEvent, false)"
        },
        "PairingSelectedCandidateAxis": {
            "expr": "PairingStudy::intToFloat(PairingEvent.selectedCandidate)"
        },
        "PairingSelectedZFlavorAxis": {
            "expr": "PairingStudy::intToFloat(PairingEvent.selectedZFlavor)"
        },
        "PairingBestScoreAxis": {"expr": "PairingEvent.selectedScore"},
        "PairingSecondScoreAxis": {"expr": "PairingEvent.secondScore"},
        "PairingMZAxis": {"expr": "PairingEvent.selectedMZ"},
        "PairingMXAxis": {"expr": "PairingEvent.selectedMX"},
        "PairingPtZAxis": {"expr": "PairingEvent.selectedPtZ"},
        "PairingPtXAxis": {"expr": "PairingEvent.selectedPtX"},
        "PairingDrZAxis": {"expr": "PairingEvent.selectedDrZ"},
        "PairingDrXAxis": {"expr": "PairingEvent.selectedDrX"},
        "PairingScoreGapAxis": {"expr": "PairingEvent.scoreGap"},
        "PairingRegionAxis": {
            "expr": "PairingStudy::intToFloat(PairingEvent.region)"
        },
        "PairingXFlavorAxis": {
            "expr": "PairingStudy::intToFloat(PairingEvent.selectedXFlavor)"
        },
        "ZHTruthPtZAxis": {"expr": "PairingStudy::truthPtAxis(PairingEvent, true)"},
        "ZZTruthPtZAxis": {"expr": "PairingStudy::truthPtAxis(PairingEvent, false)"},
        "ZHPtZResponseAxis": {
            "expr": "PairingStudy::responsePtZ(PairingEvent, true)"
        },
        "ZZPtZResponseAxis": {
            "expr": "PairingStudy::responsePtZ(PairingEvent, false)"
        },
        "ZHTruthStatusAxis": {
            "expr": "PairingStudy::constantWeights(static_cast<float>(ZHTruthStatus))"
        },
        "ZZTruthStatusAxis": {
            "expr": "PairingStudy::constantWeights(static_cast<float>(ZZTruthStatus))"
        },
        "BaselineCandidateAxis": {
            "expr": "PairingStudy::constantWeights(static_cast<float>(PairingEvent.selectedCandidate[0]))"
        },
        "BaselineRegionAxis": {
            "expr": "PairingStudy::constantWeights(static_cast<float>(PairingEvent.region[0]))"
        },
        "BaselineXFlavorAxis": {
            "expr": "PairingStudy::constantWeights(static_cast<float>(PairingEvent.selectedXFlavor[0]))"
        },
    }
)

aliases["StudyRawWeight"] = {"expr": "1.f", "afterNuis": True}
aliases["StudySignedWeight"] = {
    # `weight` carries luminosity, component source normalization, and any
    # configured component factor.  XS/PU are explicit here so the core
    # nonzero-weight prefilter cannot erase literal raw events.
    "expr": (
        "weight * static_cast<float>(XSWeight) * static_cast<float>(puWeight) * "
        "static_cast<float>(METFilter_Common)"
    ),
    "afterNuis": True,
}
aliases["StudyAbsWeight"] = {
    "expr": "abs(StudySignedWeight)",
    "afterNuis": True,
}
aliases["StudyRawWeightVec"] = {
    "expr": "PairingStudy::constantWeights(1.f)",
    "afterNuis": True,
}
aliases["StudySignedWeightVec"] = {
    "expr": "PairingStudy::constantWeights(StudySignedWeight)",
    "afterNuis": True,
}
aliases["StudyAbsWeightVec"] = {
    "expr": "PairingStudy::constantWeights(StudyAbsWeight)",
    "afterNuis": True,
}
aliases["StudyWeightSign"] = {
    "expr": "StudySignedWeight < 0.f ? -1.f : (StudySignedWeight > 0.f ? 1.f : 0.f)",
    "afterNuis": True,
}
