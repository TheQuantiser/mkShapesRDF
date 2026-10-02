"""Exercise the generated worker interface without submitting jobs."""

from copy import deepcopy
from pathlib import Path
import runpy

import pytest

from mkShapesRDF.shapeAnalysis.BatchSubmission import BatchSubmission


@pytest.mark.parametrize("packaged", [False, True])
@pytest.mark.parametrize("custom", [False, True])
def test_generated_worker_filters_samples_and_preserves_runtime(
    tmp_path, monkeypatch, packaged, custom
):
    repository = Path(__file__).resolve().parents[1]
    project = tmp_path / "configuration"
    project.mkdir()
    (project / "configuration.py").write_text("# test configuration\n")
    include = tmp_path / "common"
    include.mkdir()
    runner = repository / "mkShapesRDF/shapeAnalysis/runner.py"
    if custom:
        runner = project / "runner.py"
        runner.write_text("# custom runner\n")
    sample = (
        "DY",
        [("part", ["root://example.invalid/input.root"], "1")],
        "genWeight",
        3,
        False,
        {"FilesPerJob": 1, "custom_metadata": "retained"},
    )
    config = {
        "aliases": {
            "shared": {"expr": "1"},
            "dy": {
                "expr": "2",
                "samples": ["DY", "ZZ"],
                "linesToAdd": [f'#include "{include}/views.h"'],
            },
            "zz": {"expr": "3", "samples": ["ZZ"]},
        },
        "nuisances": {
            "shared": {"type": "lnN", "name": "lumi"},
            "shape": {
                "type": "shape",
                "kind": "suffix",
                "samples": {"DY": ["1", "1"], "ZZ": ["2", "2"]},
                "folderUp": {"DY": str(include / "up"), "ZZ": "/other/up"},
                "folderDown": {"DY": str(include / "down"), "ZZ": "/other/down"},
            },
            "zz": {"type": "shape", "samples": {"ZZ": ["1", "1"]}},
        },
        "limitEvents": 17,
        "remoteIO": {
            "inputAccessMode": "stage-in",
            "stageInScratch": str(project / "scratch"),
        },
        "zh4lCommonPath": str(include),
        "extra_setting": {"enabled": True},
        "condorRuntimeIncludes": [str(include)],
        "condorRuntimePackage": packaged,
    }
    original = deepcopy(config)
    submission = BatchSubmission(
        str(project),
        str(tmp_path / "outputs"),
        str(tmp_path / "jobs"),
        str(repository / "mkShapesRDF/include/headers.hh"),
        str(runner),
        "test",
        [sample],
        config,
        list(config),
        "",
    )
    submission.createBatch(sample)
    runtime = tmp_path / "runtime"
    monkeypatch.setenv("MKSHAPESRDF_RUNTIME_DIR", str(runtime))
    worker = runpy.run_path(str(tmp_path / "jobs/test/DY_3/script.py"))
    assert worker["aliases"].keys() == {"shared", "dy"}
    assert worker["aliases"]["dy"]["samples"] == ["DY"]
    assert worker["nuisances"].keys() == {"shared", "shape"}
    assert worker["nuisances"]["shape"]["samples"] == {"DY": ["1", "1"]}
    expected_include = runtime / "runtime_includes/000_common" if packaged else include
    assert worker["nuisances"]["shape"]["folderUp"] == str(expected_include / "up")
    assert worker["nuisances"]["shape"]["folderDown"] == str(expected_include / "down")
    assert worker["aliases"]["dy"]["linesToAdd"] == [
        f'#include "{expected_include}/views.h"'
    ]
    assert worker["limitEvents"] == 17
    expected_project = runtime / "configuration" if packaged else project
    assert worker["remoteIO"] == {
        "inputAccessMode": "stage-in",
        "stageInScratch": str(expected_project / "scratch"),
    }
    assert worker["zh4lCommonPath"] == str(expected_include)
    assert worker["extra_setting"] == {"enabled": True}
    assert worker["samples"][0][5] == sample[5]
    assert worker["job_id"] == "DY_3"
    assert config == original


def test_generated_worker_keeps_its_subsample_nuisances_and_aliases(tmp_path):
    repository = Path(__file__).resolve().parents[1]
    sample = (
        "DY",
        [("part", ["input.root"], "1")],
        "1",
        0,
        False,
        {},
        {"ee": "flavor == 11"},
    )
    config = {
        "aliases": {
            "child": {"expr": "1", "afterNuis": True, "samples": ["DY_ee", "ZZ_ee"]}
        },
        "nuisances": {
            "child": {
                "name": "child_weight",
                "kind": "weight",
                "type": "shape",
                "samples": {"DY_ee": ["1.1", "0.9"], "ZZ_ee": ["2", "0.5"]},
            }
        },
    }
    original = deepcopy(config)
    submission = BatchSubmission(
        str(tmp_path),
        str(tmp_path / "outputs"),
        str(tmp_path / "jobs"),
        str(repository / "mkShapesRDF/include/headers.hh"),
        str(repository / "mkShapesRDF/shapeAnalysis/runner.py"),
        "test",
        [sample],
        config,
        list(config),
        "",
    )
    submission.createBatch(sample)
    worker = runpy.run_path(str(tmp_path / "jobs/test/DY_0/script.py"))
    assert worker["aliases"]["child"]["samples"] == ["DY_ee"]
    assert worker["nuisances"]["child"]["samples"] == {"DY_ee": ["1.1", "0.9"]}
    assert worker["samples"][0][6] == {"ee": "flavor == 11"}
    assert config == original
