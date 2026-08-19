import hashlib
import json
from pathlib import Path


CONFIG_DIR = Path(__file__).resolve().parents[1]
MANIFEST = CONFIG_DIR / "plot_reproduction.json"
EXPECTED = {
    "2022": (
        "5e1b8858659375adba2c683a8b840b7dcad32fd63f429f8f6f841711ffb2549f",
        "852508b2c1d2192ed7b37f10d12a99d1e0338ea651fa640d0ff08d423f83888e",
    ),
    "2022EE": (
        "5c1ebaf35b0db8b1a12f5b48de7c952c5062a3937d642065139d905f82a11050",
        "8c4e9f8b659488a80e6b3b50d2d9391fede4ac051bbbcea04fd175b8736a7900",
    ),
    "2023": (
        "e78c841d41f38c40b0b7077def01a73eabc25fbc2aff5dcd135043c224a81568",
        "3519375dae64fa82b2d94d25510c93e0d9f5a76d7f6494911a779c97ae863290",
    ),
    "2023BPix": (
        "6bb9da23ae1da462f2e2fa2ff1c3c6b59d9ecc01310100392d82b23194dc6551",
        "63d59b58cd79e46fc8ef62c5122f323abc13ed4c9c97aa1d64f1aefe0b3cf2b0",
    ),
    "2024": (
        "6f7fb49e310297baa0e2b0624d58a46d2e88c28f96481991bfc95e7dea2e86ef",
        "6b6a189a71b3c05ef2aad467e42014150a791469591f5d854420b36a213161f9",
    ),
}


def _sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def test_reproduction_manifest_pins_all_five_eras_and_exact_artifact_hashes():
    payload = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert payload["schema_version"] == 1
    assert payload["campaign"] == "DYRS_PT35_M60TO120_OBS6_20260819T021244Z"
    assert [entry["era"] for entry in payload["datasets"]] == list(EXPECTED)

    for entry in payload["datasets"]:
        era = entry["era"]
        expected_config, expected_input = EXPECTED[era]
        assert entry["config_sha256"] == expected_config
        assert entry["input_sha256"] == expected_input
        for field, digest_field in (
            ("config", "config_sha256"),
            ("input", "input_sha256"),
        ):
            relative = Path(entry[field])
            assert not relative.is_absolute()
            path = (CONFIG_DIR / relative).resolve()
            assert path.is_relative_to(CONFIG_DIR.resolve())
            assert path.is_file()
            assert _sha256(path) == entry[digest_field]
