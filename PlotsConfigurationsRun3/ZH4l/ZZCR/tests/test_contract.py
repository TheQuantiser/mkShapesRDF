import runpy
from pathlib import Path

from common.observables import OBSERVABLES


HERE = Path(__file__).resolve().parents[1]


def test_regions_are_physical_and_compact():
    namespace = runpy.run_path(str(HERE / "cuts.py"))
    cuts = namespace["cuts"]
    assert tuple(cuts) == (
        "ZZCR",
        "ZZCR_4e",
        "ZZCR_4mu",
        "ZZCR_2e2mu",
        "SR_XSF",
        "SR_XDF",
    )
    assert all("bVeto" in expression for expression in cuts.values())
    assert all(
        "LepSF" not in expression and "TriggerSF" not in expression
        for expression in cuts.values()
    )


def test_compact_histogram_contract_and_native_runner():
    variables = runpy.run_path(str(HERE / "variables.py"))["variables"]
    source = (HERE / "configuration.py").read_text()
    assert len(variables) == 9
    assert len(variables) * 6 == 54
    assert 'runnerFile = "default"' in source
    assert 'os.environ.get("SAMPLE_PROFILE", "full")' in source


def test_retained_observables_preserve_validated_legacy_axes_and_folds():
    expected = {
        "mZ": ((30, 40, 60, 80, 85, 90, 95, 100, 120), 3),
        "mX": ((30, 40, 60, 80, 85, 90, 95, 100, 120), 3),
        "m4l": ((60, 80, 100, 120, 140, 160, 180, 200, 250, 300, 400, 600), 3),
        "ptZ": (
            (0, 2, 4, 6, 8, 10, 15, 20, 25, 30, 35, 40, 50, 60, 70, 80, 100, 120),
            3,
        ),
        "ptX": (
            (0, 2, 4, 6, 8, 10, 15, 20, 25, 30, 35, 40, 50, 60, 70, 80, 100, 120),
            3,
        ),
        "pt4l": ((0, 20, 40, 60, 80, 100, 150, 200, 300, 400), 2),
        "PuppiMET_pt": ((0, 10, 20, 30, 40, 50, 80, 100, 120), 3),
    }
    for name, (edges, fold) in expected.items():
        assert tuple(OBSERVABLES[name]["range"][0]) == edges
        assert OBSERVABLES[name]["fold"] == fold


def test_equivalence_validator_tracks_every_nominal_axis_and_supported_era():
    validator = runpy.run_path(str(HERE / "validate_equivalence.py"))
    assert tuple(validator["ZH_SIGNAL_BY_ERA"]) == (
        "2022",
        "2022EE",
        "2023",
        "2023BPix",
        "2024",
    )
    axes = validator["HISTOGRAM_AXES"]
    assert set(axes) == set(OBSERVABLES)
    for name, (edges, fold) in axes.items():
        assert tuple(OBSERVABLES[name]["range"][0]) == edges
        assert OBSERVABLES[name]["fold"] == fold


def test_nominal_weight_has_exact_selected_zx_domain():
    source = (HERE / "samples.py").read_text()
    assert "puWeight*LepSF_ZX*TriggerSF_ZX*bVetoSF" in source
