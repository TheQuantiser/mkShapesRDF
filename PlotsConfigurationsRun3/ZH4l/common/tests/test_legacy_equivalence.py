import hashlib
from pathlib import Path


REPO = Path(__file__).resolve().parents[4]
FAMILY = REPO / "PlotsConfigurationsRun3" / "ZH4l"
LEGACY = REPO / "PlotsConfigurationsRun3" / "ZH_4lMET"


def _sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_validated_payloads_and_physics_kernels_are_byte_identical():
    pairs = (
        (LEGACY / "ZZ_CR/year_config.json", FAMILY / "common/eras.json"),
        (LEGACY / "ZZ_CR/macros/four_lepton_helpers.cc", FAMILY / "common/macros/objects.cc"),
        (LEGACY / "ZZ_CR/macros/selected_trigger_wrappers.cc", FAMILY / "common/macros/trigger.cc"),
        (LEGACY / "ZZ_CR/macros/fixed_wp_btag_sf.cc", FAMILY / "common/macros/btag.cc"),
        (LEGACY / "PairingStudy/macros/pairing_study.cc", FAMILY / "Pairing/macros/pairing.cc"),
    )
    for old, new in pairs:
        assert old.is_file() and new.is_file()
        assert _sha(old) == _sha(new), (old, new)


def test_accepted_public_rename_is_semantic_not_algorithmic():
    objects = (FAMILY / "common/objects.py").read_text()
    mapping = {
        '        "Z_idx": {': "bestZ0IdxWithID",
        '        "X_idx": {': "xPairIdxWithID",
        'aliases["mZ"]': "pairMass",
        'aliases["mX"]': "pairMass",
        'aliases["m4l"]': "fourLeptonMassFromPairs",
        'aliases["pt4l"]': "fourLeptonPtFromPairs",
        'aliases["minMll4l"]': "minimumSelectedPairMass",
        'aliases["q4l"]': "sumLeptonChargeFromPairs",
    }
    for public_name, kernel in mapping.items():
        start = objects.index(public_name)
        assert kernel in objects[start:start + 260]
