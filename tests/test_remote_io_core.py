import os
import subprocess
from pathlib import Path

import pytest

from mkShapesRDF.lib import remote_io


def test_missing_external_command_is_actionable_and_not_retried():
    calls = []

    def missing(argv, **kwargs):
        calls.append((argv, kwargs))
        raise FileNotFoundError(2, "missing command", argv[0])

    runner = remote_io.ExternalCommandRunner(retries=4, popen_factory=missing)
    with pytest.raises(remote_io.RemoteCommandError, match="FileNotFoundError") as raised:
        runner.run(["missing-xrd-tool", "arg with spaces"], "test-missing")
    assert raised.value.result.argv == ["missing-xrd-tool", "arg with spaces"]
    assert raised.value.result.returncode == 127
    assert len(calls) == 1


def test_remote_exists_propagates_auth_and_network_failures_but_accepts_not_found():
    class Runner:
        def __init__(self, detail):
            self.detail = detail

        def run(self, argv, operation):
            result = remote_io.CommandResult(
                argv, 54, "", self.detail, False, 1, operation
            )
            raise remote_io.RemoteCommandError(result)

    settings = remote_io.resolve_remote_io_config()
    auth_ops = remote_io.RemoteFileOps(settings, Runner("authorization denied"))
    with pytest.raises(remote_io.RemoteCommandError, match="authorization denied"):
        auth_ops.exists("root://write.example//store/output.root")

    network_ops = remote_io.RemoteFileOps(settings, Runner("connection reset"))
    with pytest.raises(remote_io.RemoteCommandError, match="connection reset"):
        network_ops.exists("root://write.example//store/output.root")

    missing_ops = remote_io.RemoteFileOps(
        settings, Runner("[3011] No such file or directory")
    )
    assert missing_ops.exists("root://write.example//store/missing.root") is False


def test_cli_config_precedence_boolean_optional_action():
    from mkShapesRDF.shapeAnalysis.mkShapesRDF import defaultParser, resolve_cli_remote_io

    parser = defaultParser()
    args = parser.parse_args([])
    config = {
        "inputAccessMode": "xrootd",
        "xrdReadEndpoint": "root://configured.example",
        "preserveStageInOnFailure": False,
    }
    resolved = resolve_cli_remote_io(args, config)
    assert resolved["inputAccessMode"] == "xrootd"
    assert resolved["xrdReadEndpoint"] == "root://configured.example"
    assert resolved["preserveStageInOnFailure"] is False

    args = parser.parse_args(
        [
            "--condor-runtime-package",
            "--runtime-include",
            "../shared/macros",
            "--use-x509-proxy",
            "--output-folder",
            "/store/user/test/output",
            "--remote-command-timeout",
            "42",
            "--remote-transfer-retries",
            "0",
        ]
    )
    assert args.condorRuntimePackage is True
    assert args.condorRuntimeIncludes == ["../shared/macros"]
    assert args.useX509Proxy is True
    assert args.outputFolderOverride == "/store/user/test/output"
    resolved = resolve_cli_remote_io(args, {})
    assert resolved["remoteCommandTimeout"] == 42
    assert resolved["remoteTransferRetries"] == 0

    args = parser.parse_args(
        ["--no-condor-runtime-package", "--no-use-x509-proxy"]
    )
    assert args.condorRuntimePackage is False
    assert args.useX509Proxy is False

    args = parser.parse_args(
        [
            "--input-access-mode",
            "stage-in",
            "--xrd-read-endpoint",
            "root://cli.example",
            "--preserve-stage-in-on-failure",
        ]
    )
    resolved = resolve_cli_remote_io(args, config)
    assert resolved["inputAccessMode"] == "stage-in"
    assert resolved["xrdReadEndpoint"] == "root://cli.example"
    assert resolved["preserveStageInOnFailure"] is True

    args = parser.parse_args(["--no-preserve-stage-in-on-failure"])
    resolved = resolve_cli_remote_io(args, {"preserveStageInOnFailure": True})
    assert resolved["preserveStageInOnFailure"] is False


def test_cli_resolution_preserves_nested_remote_io_values():
    from mkShapesRDF.shapeAnalysis.mkShapesRDF import defaultParser, resolve_cli_remote_io

    args = defaultParser().parse_args(["--input-access-mode", "stage-in"])
    resolved = resolve_cli_remote_io(
        args,
        {
            "remoteIO": {
                "inputAccessMode": "xrootd",
                "stageInScratch": "/task-owned/scratch",
                "stageInCleanup": "always",
                "preserveStageInOnFailure": False,
            }
        },
    )
    assert resolved["inputAccessMode"] == "stage-in"
    assert resolved["stageInScratch"] == "/task-owned/scratch"
    assert resolved["stageInCleanup"] == "always"
    assert resolved["preserveStageInOnFailure"] is False
    assert resolved["existingOutputPolicy"] == "fail"


def test_endpoint_normalization_requires_explicit_read_endpoint():
    settings = remote_io.resolve_remote_io_config({"inputAccessMode": "as-configured"})
    assert remote_io.resolve_input_uri("/tmp/a.root", settings) == "/tmp/a.root"
    assert (
        remote_io.resolve_input_uri("/eos/cms/store/a.root", settings)
        == "/eos/cms/store/a.root"
    )
    assert (
        remote_io.resolve_input_uri("root://already.example//store/a.root", settings)
        == "root://already.example//store/a.root"
    )

    settings = remote_io.resolve_remote_io_config({"inputAccessMode": "xrootd"})
    with pytest.raises(remote_io.RemoteIOError):
        remote_io.resolve_input_uri("/store/a.root", settings)

    settings = remote_io.resolve_remote_io_config(
        {"inputAccessMode": "xrootd", "xrdReadEndpoint": "root://read.example///"}
    )
    assert (
        remote_io.resolve_input_uri("/store/a.root", settings)
        == "root://read.example//store/a.root"
    )
    assert (
        remote_io.resolve_input_uri("/eos/cms/store/a.root", settings)
        == "root://read.example//store/a.root"
    )


def test_stage_in_cleanup_policies(tmp_path):
    class Validator:
        def validate(self, path, tree_name="Events"):
            return True

    source = tmp_path / "source.root"
    source.write_bytes(b"root")
    for policy, success, preserve, expect_exists in [
        ("on-success", True, True, False),
        ("on-success", False, True, True),
        ("always", False, True, False),
        ("never", True, True, True),
        ("on-success", False, False, False),
    ]:
        scratch = tmp_path / f"scratch_{policy}_{success}_{preserve}"
        settings = remote_io.resolve_remote_io_config(
            {
                "inputAccessMode": "stage-in",
                "stageInScratch": str(scratch),
                "stageInCleanup": policy,
                "preserveStageInOnFailure": preserve,
            }
        )
        manager = remote_io.StageInManager(settings, validator=Validator())
        staged = manager.prepare_files([str(source)])
        assert Path(staged[0]).exists()
        manager.cleanup(success=success)
        assert manager.scratch.exists() is expect_exists


def test_stage_in_prefers_condor_scratch(monkeypatch, tmp_path):
    class Validator:
        def validate(self, path, tree_name="Events"):
            return True

    source = tmp_path / "source.root"
    source.write_bytes(b"root")
    condor_scratch = tmp_path / "condor_scratch"
    condor_scratch.mkdir()
    monkeypatch.setenv("_CONDOR_SCRATCH_DIR", str(condor_scratch))
    monkeypatch.setenv("TMPDIR", str(tmp_path / "wrong_tmp"))
    settings = remote_io.resolve_remote_io_config(
        {"inputAccessMode": "stage-in", "stageInCleanup": "on-success"}
    )
    manager = remote_io.StageInManager(settings, validator=Validator())
    manager.prepare_files([str(source)])
    assert manager.scratch.parent == condor_scratch
    manager.cleanup(success=True)


def test_stage_out_existing_output_policies_and_replace_rollback(tmp_path):
    local = tmp_path / "local.root"
    local.write_bytes(b"new")

    class FakeOps:
        def __init__(self):
            self.files = {"dest.root": b"old"}
            self.fail_final_move = False

        def exists(self, uri):
            return uri in self.files

        def stat(self, uri):
            if uri not in self.files:
                raise remote_io.RemoteIOError(uri)
            return {"size": len(self.files[uri])}

        def copy(self, source, destination):
            self.files[destination] = Path(source).read_bytes()

        def move(self, source, destination):
            if self.fail_final_move and source.startswith("dest.root.tmp."):
                raise remote_io.RemoteIOError("forced final move failure")
            self.files[destination] = self.files.pop(source)

        def remove(self, uri):
            self.files.pop(uri, None)

    settings = remote_io.resolve_remote_io_config({"existingOutputPolicy": "fail"})
    with pytest.raises(remote_io.RemoteIOError):
        remote_io.stage_out(str(local), "dest.root", settings, ops=FakeOps())

    same = FakeOps()
    same.files["dest.root"] = b"new"
    settings = remote_io.resolve_remote_io_config(
        {"existingOutputPolicy": "skip-if-verified-identical"}
    )
    ledger = []
    assert remote_io.stage_out(str(local), "dest.root", settings, ops=same, ledger=ledger)
    assert ledger[0]["action"] == "skip-identical"

    replace = FakeOps()
    settings = remote_io.resolve_remote_io_config({"existingOutputPolicy": "replace"})
    remote_io.stage_out(str(local), "dest.root", settings, ops=replace, ledger=[])
    assert replace.files["dest.root"] == b"new"

    rollback = FakeOps()
    rollback.fail_final_move = True
    with pytest.raises(remote_io.RemoteIOError):
        remote_io.stage_out(str(local), "dest.root", settings, ops=rollback, ledger=[])
    assert rollback.files["dest.root"] == b"old"


def test_external_command_timeout_is_captured():
    def timeout(*args, **kwargs):
        raise subprocess.TimeoutExpired(args[0], kwargs["timeout"])

    runner = remote_io.ExternalCommandRunner(timeout=1, retries=0, popen_factory=timeout)
    with pytest.raises(remote_io.RemoteCommandError) as exc:
        runner.run(["xrdfs", "root://example", "ls", "/store"], "discovery-list")
    assert exc.value.result.timed_out is True
    assert exc.value.result.attempt == 1


def test_hanging_listing_uses_structured_runner():
    from mkShapesRDF.lib.search_files import SearchFiles

    class Runner:
        def __init__(self):
            self.argv = None

        def run(self, argv, operation, metadata=None):
            self.argv = argv
            return remote_io.CommandResult(argv, 0, "/store/nanoLatino_ZZ__part0.root\n", "", False, 1, operation, metadata or {})

    command_runner = Runner()
    files = SearchFiles(command_runner=command_runner).searchFiles(
        "/store", "ZZ", redirector="root://read.example"
    )
    assert command_runner.argv == ["xrdfs", "root://read.example", "ls", "/store/"]
    assert files == ["root://read.example//store/nanoLatino_ZZ__part0.root"]


def test_remote_discovery_normalizes_mounted_folder_and_separates_endpoints():
    from mkShapesRDF.lib.search_files import SearchFiles

    class Runner:
        def __init__(self):
            self.calls = []

        def run(self, argv, operation, metadata=None):
            self.calls.append((argv, operation, metadata))
            return remote_io.CommandResult(
                argv,
                0,
                "\n".join(
                    [
                        "/store/campaign/nanoLatino_ZZ__part10.root",
                        "/store/campaign/nanoLatino_ZZ__part2.root",
                        "/store/campaign/nanoLatino_ZZ__part1.root",
                    ]
                ),
                "",
                False,
                1,
                operation,
                metadata or {},
            )

    runner = Runner()
    search = SearchFiles(command_runner=runner)
    files = search.searchFiles(
        "/eos/cms/store/campaign",
        "ZZ",
        redirector="root://discovery.example",
        read_redirector="root://read.example",
    )
    assert runner.calls[0][0] == [
        "xrdfs",
        "root://discovery.example",
        "ls",
        "/store/campaign/",
    ]
    assert files == [
        "root://read.example//store/campaign/nanoLatino_ZZ__part1.root",
        "root://read.example//store/campaign/nanoLatino_ZZ__part2.root",
        "root://read.example//store/campaign/nanoLatino_ZZ__part10.root",
    ]
    assert all(item.count("root://") == 1 for item in files)


def test_search_files_without_redirector_preserves_mounted_style_paths(tmp_path):
    from mkShapesRDF.lib.search_files import SearchFiles

    for part in (10, 2, 1):
        (tmp_path / f"nanoLatino_ZZ__part{part}.root").touch()

    files = SearchFiles().searchFiles(str(tmp_path), "ZZ", redirector="")

    assert files == [
        str(tmp_path / "nanoLatino_ZZ__part1.root"),
        str(tmp_path / "nanoLatino_ZZ__part2.root"),
        str(tmp_path / "nanoLatino_ZZ__part10.root"),
    ]


def test_local_empty_discovery_preserves_upstream_requery_behavior(monkeypatch, tmp_path):
    from mkShapesRDF.lib.search_files import SearchFiles

    expected = tmp_path / "nanoLatino_SAMPLE__part0.root"
    calls = []

    def changing_glob(pattern):
        calls.append(pattern)
        return [] if len(calls) == 1 else [str(expected)]

    monkeypatch.setattr("mkShapesRDF.lib.search_files.glob.glob", changing_glob)
    search = SearchFiles()
    assert search.searchFiles(str(tmp_path), "SAMPLE", redirector="") == []
    assert search.searchFiles(str(tmp_path), "SAMPLE", redirector="") == [
        str(expected)
    ]
    assert len(calls) == 2


def test_process_local_cli_endpoint_override_applies_during_legacy_discovery():
    from mkShapesRDF.lib.search_files import SearchFiles

    class Runner:
        def __init__(self):
            self.argv = None

        def run(self, argv, operation, metadata):
            self.argv = argv
            return remote_io.CommandResult(
                argv,
                0,
                "/store/data/nanoLatino_SAMPLE__part0.root\n",
                "",
                False,
                1,
                operation,
                metadata,
            )

    runner = Runner()
    SearchFiles.configure_remote_endpoints(
        "root://discovery.example", "root://read.example"
    )
    try:
        files = SearchFiles(command_runner=runner).searchFiles(
            "/eos/cms/store/data", "SAMPLE", redirector=""
        )
    finally:
        SearchFiles.configure_remote_endpoints(None, None)
    assert runner.argv == [
        "xrdfs",
        "root://discovery.example",
        "ls",
        "/store/data/",
    ]
    assert files == ["root://read.example//store/data/nanoLatino_SAMPLE__part0.root"]


def test_discovery_cache_key_includes_redirector():
    from mkShapesRDF.lib.search_files import SearchFiles

    class Runner:
        def __init__(self):
            self.calls = []

        def run(self, argv, operation, metadata=None):
            self.calls.append(argv)
            return remote_io.CommandResult(
                argv,
                0,
                "/store/campaign/nanoLatino_ZZ__part0.root\n",
                "",
                False,
                1,
                operation,
                metadata or {},
            )

    runner = Runner()
    search = SearchFiles(command_runner=runner)
    search.searchFiles("/store/campaign", "ZZ", redirector="root://one.example")
    search.searchFiles("/store/campaign", "ZZ", redirector="root://two.example")
    assert len(runner.calls) == 2


def test_malformed_remote_discovery_endpoint_fails_clearly():
    from mkShapesRDF.lib.search_files import SearchFiles

    with pytest.raises(remote_io.RemoteIOError, match="discovery endpoint"):
        SearchFiles().searchFiles(
            "/eos/cms/store/campaign",
            "ZZ",
            redirector="https://not-xrootd.example",
        )
