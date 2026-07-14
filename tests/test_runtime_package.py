import io
import json
import os
import subprocess
import sys
import tarfile
from pathlib import Path

import pytest

from mkShapesRDF.lib.runtime_package import (
    RuntimePackageError,
    build_runtime_archive,
    safe_extract_runtime_archive,
)
from mkShapesRDF.shapeAnalysis.BatchSubmission import BatchSubmission


def _minimal_framework(root):
    package = root / "mkShapesRDF"
    (package / "lib").mkdir(parents=True)
    (package / "shapeAnalysis").mkdir()
    (package / "__init__.py").write_text("VALUE = 'packaged'\n")
    (package / "lib" / "remote_io.py").write_text("REMOTE = True\n")
    (package / "shapeAnalysis" / "runner.py").write_text("RUNNER = True\n")
    binary = root / "utils" / "bin" / "hadd2"
    binary.parent.mkdir(parents=True)
    binary.write_text("#!/bin/sh\nexit 0\n")
    binary.chmod(0o755)


def test_external_package_is_deterministic_minimal_and_credential_free(tmp_path):
    framework = tmp_path / "candidate"
    config = tmp_path / "plots" / "analysis"
    sibling_reference = tmp_path / "latinos_mkShapesRDF"
    _minimal_framework(framework)
    config.mkdir(parents=True)
    (config / "configuration.py").write_text("tag = 'external'\n")
    (config / "helper.cc").write_text("int helper() { return 1; }\n")
    (config / "proxyW.cc").write_text("int physics_proxy() { return 1; }\n")
    (config / "private_proxy.dat").write_text("must not be packaged\n")
    sibling_reference.mkdir()
    (sibling_reference / "sentinel.py").write_text("REFERENCE = True\n")

    include = tmp_path / "shared" / "calibration.json"
    include.parent.mkdir()
    include.write_text('{"value": 1}\n')
    first = build_runtime_archive(framework, config, tmp_path / "one.tgz", [include])
    second = build_runtime_archive(framework, config, tmp_path / "two.tgz", [include])

    assert first.archive_sha256 == second.archive_sha256
    assert Path(first.archive).read_bytes() == Path(second.archive).read_bytes()
    assert "mkShapesRDF/__init__.py" in first.members
    assert "configuration/configuration.py" in first.members
    assert "configuration/helper.cc" in first.members
    assert "configuration/proxyW.cc" in first.members
    assert not any("private_proxy" in name for name in first.members)
    assert not any("latinos_mkShapesRDF" in name for name in first.members)
    assert any(
        name.startswith("runtime_includes/000_calibration.json")
        for name in first.members
    )
    manifest = json.loads(Path(first.manifest).read_text())
    assert manifest["credentials_in_archive"] is False
    assert manifest["archive_sha256"] == first.archive_sha256


def test_safe_extract_rejects_traversal_links_duplicates_and_missing_members(tmp_path):
    def write_archive(path, members):
        with tarfile.open(path, "w:gz") as archive:
            for info, payload in members:
                if payload is not None:
                    info.size = len(payload)
                    archive.addfile(info, io.BytesIO(payload))
                else:
                    archive.addfile(info)

    traversal = tarfile.TarInfo("../outside")
    write_archive(tmp_path / "traversal.tgz", [(traversal, b"bad")])
    with pytest.raises(RuntimePackageError, match="Unsafe runtime archive member"):
        safe_extract_runtime_archive(
            tmp_path / "traversal.tgz", tmp_path / "extract_traversal"
        )
    assert not (tmp_path / "outside").exists()

    link = tarfile.TarInfo("link")
    link.type = tarfile.SYMTYPE
    link.linkname = "/tmp/escape"
    write_archive(tmp_path / "link.tgz", [(link, None)])
    with pytest.raises(RuntimePackageError, match="Unsupported runtime archive"):
        safe_extract_runtime_archive(tmp_path / "link.tgz", tmp_path / "extract_link")

    regular = tarfile.TarInfo("module.py")
    write_archive(tmp_path / "regular.tgz", [(regular, b"VALUE = 1\n")])
    with pytest.raises(RuntimePackageError, match="missing required members"):
        safe_extract_runtime_archive(
            tmp_path / "regular.tgz",
            tmp_path / "extract_missing",
            ["required.py"],
        )


def test_external_batch_package_relocates_paths_and_imports_from_scratch(tmp_path):
    config = tmp_path / "external_plots" / "analysis"
    config.mkdir(parents=True)
    (config / "configuration.py").write_text("tag = 'external'\n")
    helper = config / "helper.cc"
    helper.write_text("int helper() { return 1; }\n")
    output = tmp_path / "returned output"
    output.mkdir()
    framework_root = Path(__file__).parents[1]
    batch = BatchSubmission(
        folder=str(config),
        outputPath=str(output),
        batchFolder=str(tmp_path / "batch"),
        headersPath=str(framework_root / "mkShapesRDF" / "include" / "headers.hh"),
        runnerPath=str(framework_root / "mkShapesRDF" / "shapeAnalysis" / "runner.py"),
        tag="tag",
        samples=[
            ("SAMPLE", ["root://read.example//store/input.root"], "1.0", 0, False, {})
        ],
        d={
            "outputFile": "mkShapes.root",
            "mountEOS": [],
            "remoteIO": {"inputAccessMode": "xrootd"},
            "aliases": {"helper": {"linesToAdd": [f'#include "{helper}"']}},
            "condorRuntimePackage": True,
            "condorRuntimePackageName": "runtime.tgz",
        },
        batchVars=["samples", "aliases", "remoteIO"],
        jdlconfigfile="",
    )
    batch.createBatches()
    batch.submit(dryRun=1)
    submit_dir = Path(batch.batchFolder) / batch.tag
    script = (submit_dir / "SAMPLE_0" / "script.py").read_text()
    assert str(config) not in script
    assert "__MKSHAPESRDF_CONFIG_ROOT__" in script
    with tarfile.open(submit_dir / "runtime.tgz") as archive:
        names = archive.getnames()
    assert "configuration/configuration.py" in names
    assert "configuration/helper.cc" in names
    assert not any("latinos_mkShapesRDF" in name for name in names)
    assert not any("PlotsConfigurationsRun3/WH_SS" in name for name in names)

    scratch = tmp_path / "scratch"
    safe_extract_runtime_archive(
        submit_dir / "runtime.tgz",
        scratch,
        ["mkShapesRDF/__init__.py", "configuration/configuration.py"],
    )
    env = {
        "PATH": os.environ.get("PATH", ""),
        "PYTHONPATH": str(scratch),
        "PYTHONNOUSERSITE": "1",
        "MKSHAPESRDF_RUNTIME_DIR": str(scratch),
    }
    probe = subprocess.run(
        [
            sys.executable,
            "-c",
            "import mkShapesRDF,runpy; "
            "d=runpy.run_path(r'%s'); "
            "print(mkShapesRDF.__file__); print(d['aliases']['helper']['linesToAdd'][0])"
            % (submit_dir / "SAMPLE_0" / "script.py"),
        ],
        cwd=tmp_path,
        env=env,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=30,
    )
    lines = probe.stdout.splitlines()
    assert str(scratch / "mkShapesRDF" / "__init__.py") == lines[0]
    assert str(scratch / "configuration" / "helper.cc") in lines[1]
    assert str(framework_root) not in probe.stdout


def test_package_name_must_be_worker_local_basename(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    (project / "module.py").write_text("VALUE = 1\n")
    batch = BatchSubmission(
        str(project),
        str(tmp_path / "out"),
        str(tmp_path / "batch"),
        str(tmp_path / "headers.hh"),
        str(tmp_path / "runner.py"),
        "tag",
        [("SAMPLE", ["input.root"], "1", 0, False, {})],
        {
            "outputFile": "output.root",
            "mountEOS": [],
            "remoteIO": {},
            "condorRuntimePackage": True,
            "condorRuntimePackageName": "../escape.tgz",
        },
        ["samples", "remoteIO"],
        "",
    )
    batch.createBatches()
    with pytest.raises(RuntimeError, match="worker-local basename"):
        batch.submit(dryRun=1)
