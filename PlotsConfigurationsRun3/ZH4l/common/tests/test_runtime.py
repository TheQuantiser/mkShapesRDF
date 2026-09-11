from pathlib import Path

from mkShapesRDF.shapeAnalysis.BatchSubmission import BatchSubmission
from common.runtime import common_import_statement


def test_native_batch_relocates_common_paths_before_framework_paths():
    family = Path(__file__).resolve().parents[2]
    repository = family.parents[1]
    common = family / "common"
    submission = BatchSubmission.__new__(BatchSubmission)
    submission.runnerPath = str(repository / "mkShapesRDF/shapeAnalysis/runner.py")
    submission.project_folder = str(family / "ZZCR")
    submission.d = {"condorRuntimeIncludes": [str(common)]}
    specs = submission._runtime_path_specs()
    config = {
        "zh4lCommonPath": str(common),
        "aliases": {
            "value": {
                "linesToAdd": [f'#include "{common}/macros/views.h"'],
                "linesToProcess": [common_import_statement(common)],
            }
        },
    }
    relocated = submission._tokenize_runtime_paths(config, specs)
    assert relocated["zh4lCommonPath"] == "__MKSHAPESRDF_RUNTIME_INCLUDE_000__"
    assert str(repository) not in repr(relocated)
    assert "__MKSHAPESRDF_RUNTIME_INCLUDE_000__/macros/views.h" in repr(relocated)
    assert "__MKSHAPESRDF_RUNTIME_INCLUDE_000__/__init__.py" in repr(relocated)
    assert config["zh4lCommonPath"] == str(common)
