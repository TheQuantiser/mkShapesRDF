import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from mkShapesRDF.lib import remote_io


class RemoteIOCoreTests(unittest.TestCase):
    def test_cli_help_describes_compile_and_bounded_execution_flags(self):
        from mkShapesRDF.shapeAnalysis.mkShapesRDF import defaultParser

        parser = defaultParser()
        actions = {action.dest: action for action in parser._actions}
        self.assertIn("1 compile configuration", actions["compile"].help)
        self.assertIn("0 load", actions["compile"].help)
        self.assertIn("events", actions["limitEvents"].help.lower())
        self.assertIn("condor", actions["doBatch"].help.lower())
        self.assertIn("do not submit", actions["dryRun"].help.lower())

    def test_configuration_execution_mode_contract(self):
        from mkShapesRDF.shapeAnalysis.mkShapesRDF import (
            validate_config_execution_mode,
        )

        validate_config_execution_mode({}, do_batch=0)
        validate_config_execution_mode(
            {"requiredExecutionMode": "batch"}, do_batch=1
        )
        with self.assertRaisesRegex(
            RuntimeError, "requires batch execution.*local_xrootd"
        ):
            validate_config_execution_mode(
                {
                    "requiredExecutionMode": "batch",
                    "executionModeRemediation": (
                        "Select ZZCR_EXECUTION_PROFILE=local_xrootd."
                    ),
                },
                do_batch=0,
            )

    def test_resolved_input_summary_is_bounded_and_keeps_provenance(self):
        from mkShapesRDF.shapeAnalysis.runner import RunAnalysis

        files = [f"root://read.example//store/huge/input_{index}.root" for index in range(10000)]
        summary = RunAnalysis._summarize_resolved_inputs(files)
        self.assertIn("count=10000", summary)
        self.assertIn(files[0], summary)
        self.assertIn(files[-1], summary)
        self.assertNotIn(files[5000], summary)
        self.assertLess(len(summary), 1000)

        one = RunAnalysis._summarize_resolved_inputs([files[0]])
        self.assertIn("count=1", one)
        self.assertIn(files[0], one)

    def test_cli_config_precedence_boolean_optional_action(self):
        from mkShapesRDF.shapeAnalysis.mkShapesRDF import (
            defaultParser,
            resolve_cli_remote_io,
        )

        parser = defaultParser()
        args = parser.parse_args([])
        config = {
            "inputAccessMode": "xrootd",
            "xrdReadEndpoint": "root://configured.example",
            "xrdWriteEndpoint": "root://configured-write.example",
            "preserveStageInOnFailure": False,
        }
        resolved = resolve_cli_remote_io(args, config)
        self.assertEqual(resolved["inputAccessMode"], "xrootd")
        self.assertEqual(resolved["xrdReadEndpoint"], "root://configured.example")
        self.assertEqual(resolved["xrdWriteEndpoint"], "root://configured-write.example")
        self.assertIs(resolved["preserveStageInOnFailure"], False)
        self.assertEqual(resolved["existingOutputPolicy"], "fail")

        args = parser.parse_args(
            [
                "--input-access-mode",
                "stage-in",
                "--xrd-read-endpoint",
                "root://cli.example",
                "--xrd-write-endpoint",
                "root://cli-write.example",
                "--preserve-stage-in-on-failure",
            ]
        )
        resolved = resolve_cli_remote_io(args, config)
        self.assertEqual(resolved["inputAccessMode"], "stage-in")
        self.assertEqual(resolved["xrdReadEndpoint"], "root://cli.example")
        self.assertEqual(resolved["xrdWriteEndpoint"], "root://cli-write.example")
        self.assertIs(resolved["preserveStageInOnFailure"], True)

        args = parser.parse_args(["--no-preserve-stage-in-on-failure"])
        resolved = resolve_cli_remote_io(args, {"preserveStageInOnFailure": True})
        self.assertIs(resolved["preserveStageInOnFailure"], False)

    def test_cli_resolution_preserves_nested_remote_io_values(self):
        from mkShapesRDF.shapeAnalysis.mkShapesRDF import (
            defaultParser,
            resolve_cli_remote_io,
        )

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
        self.assertEqual(resolved["inputAccessMode"], "stage-in")
        self.assertEqual(resolved["stageInScratch"], "/task-owned/scratch")
        self.assertEqual(resolved["stageInCleanup"], "always")
        self.assertIs(resolved["preserveStageInOnFailure"], False)

    def test_endpoint_normalization_requires_explicit_read_endpoint(self):
        settings = remote_io.resolve_remote_io_config(
            {"inputAccessMode": "as-configured"}
        )
        self.assertEqual(remote_io.resolve_input_uri("/tmp/a.root", settings), "/tmp/a.root")
        self.assertEqual(
            remote_io.resolve_input_uri("/eos/cms/store/a.root", settings),
            "/eos/cms/store/a.root",
        )
        self.assertEqual(
            remote_io.resolve_input_uri("root://already.example//store/a.root", settings),
            "root://already.example//store/a.root",
        )

        settings = remote_io.resolve_remote_io_config({"inputAccessMode": "xrootd"})
        with self.assertRaises(remote_io.RemoteIOError):
            remote_io.resolve_input_uri("/store/a.root", settings)

        settings = remote_io.resolve_remote_io_config(
            {"inputAccessMode": "xrootd", "xrdReadEndpoint": "root://read.example///"}
        )
        self.assertEqual(
            remote_io.resolve_input_uri("/store/a.root", settings),
            "root://read.example//store/a.root",
        )
        self.assertEqual(
            remote_io.resolve_input_uri("/eos/cms/store/a.root", settings),
            "root://read.example//store/a.root",
        )
        self.assertEqual(
            remote_io.build_remote_uri(
                "root://cmseos.fnal.gov/", "/store/user/test/out.root"
            ),
            "root://cmseos.fnal.gov//store/user/test/out.root",
        )
        with self.assertRaises(remote_io.RemoteIOError):
            remote_io.build_remote_uri("root://cmseos.fnal.gov", "/tmp/out.root")

    def test_stage_in_cleanup_policies(self):
        class Validator:
            def validate(self, path, tree_name="Events"):
                return True

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            source = tmp_path / "source.root"
            source.write_bytes(b"root")
            cases = [
                ("on-success", True, True, False),
                ("on-success", False, True, True),
                ("always", False, True, False),
                ("never", True, True, True),
                ("on-success", False, False, False),
            ]
            for policy, success, preserve, expect_exists in cases:
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
                self.assertTrue(Path(staged[0]).exists())
                manager.cleanup(success=success)
                self.assertIs(manager.scratch.exists(), expect_exists)

    def test_stage_out_existing_output_policies_and_replace_rollback(self):
        with tempfile.TemporaryDirectory() as tmp:
            local = Path(tmp) / "local.root"
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
            with self.assertRaises(remote_io.RemoteIOError):
                remote_io.stage_out(str(local), "dest.root", settings, ops=FakeOps())

            same = FakeOps()
            same.files["dest.root"] = b"new"
            settings = remote_io.resolve_remote_io_config(
                {"existingOutputPolicy": "skip-if-verified-identical"}
            )
            ledger = []
            self.assertEqual(
                remote_io.stage_out(str(local), "dest.root", settings, ops=same, ledger=ledger),
                "dest.root",
            )
            self.assertEqual(ledger[0]["action"], "skip-identical")

            replace = FakeOps()
            settings = remote_io.resolve_remote_io_config({"existingOutputPolicy": "replace"})
            remote_io.stage_out(str(local), "dest.root", settings, ops=replace, ledger=[])
            self.assertEqual(replace.files["dest.root"], b"new")

            rollback = FakeOps()
            rollback.fail_final_move = True
            with self.assertRaises(remote_io.RemoteIOError):
                remote_io.stage_out(str(local), "dest.root", settings, ops=rollback, ledger=[])
            self.assertEqual(rollback.files["dest.root"], b"old")

            class CopyFailOps(FakeOps):
                def copy(self, source, destination):
                    raise remote_io.RemoteIOError("forced copy failure")

            stale = CopyFailOps()
            with self.assertRaises(remote_io.RemoteIOError):
                remote_io.stage_out(str(local), "dest.root", settings, ops=stale, ledger=[])
            self.assertEqual(stale.files["dest.root"], b"old")

    def test_external_command_timeout_is_captured(self):
        def timeout(*args, **kwargs):
            raise subprocess.TimeoutExpired(args[0], kwargs["timeout"])

        runner = remote_io.ExternalCommandRunner(timeout=1, retries=0, popen_factory=timeout)
        with self.assertRaises(remote_io.RemoteCommandError) as ctx:
            runner.run(["xrdfs", "root://example", "ls", "/store"], "discovery-list")
        self.assertIs(ctx.exception.result.timed_out, True)
        self.assertEqual(ctx.exception.result.attempt, 1)

    def test_hanging_listing_uses_structured_runner(self):
        from mkShapesRDF.lib.search_files import SearchFiles

        class Runner:
            def __init__(self):
                self.argv = None

            def run(self, argv, operation, metadata=None):
                self.argv = argv
                return remote_io.CommandResult(
                    argv,
                    0,
                    "/store/nanoLatino_ZZ__part0.root\n",
                    "",
                    False,
                    1,
                    operation,
                    metadata or {},
                )

        command_runner = Runner()
        files = SearchFiles(command_runner=command_runner).searchFiles(
            "/store", "ZZ", redirector="root://read.example"
        )
        self.assertEqual(command_runner.argv, ["xrdfs", "root://read.example", "ls", "/store/"])
        self.assertEqual(files, ["root://read.example//store/nanoLatino_ZZ__part0.root"])


class RemoteIOIntegrationTests(unittest.TestCase):
    def test_stage_in_precedes_tchain_add(self):
        from mkShapesRDF.shapeAnalysis import runner as runner_module

        events = []

        class FakeStageInManager:
            def __init__(self, settings):
                pass

            def prepare_files(self, files):
                events.append(("stage", tuple(files)))
                return [f"staged:{path}" for path in files]

        class FakeTChain:
            def __init__(self, name):
                self.name = name

            def Add(self, path):
                events.append(("add", path))

            def AddFriend(self, friend):
                events.append(("friend", friend.name))

        class FakeRDF:
            def __init__(self, tree):
                pass

            def GetColumnNames(self):
                return []

        class FakeROOT:
            TChain = FakeTChain
            RDataFrame = FakeRDF

        with tempfile.TemporaryDirectory() as tmp:
            with mock.patch.object(runner_module, "StageInManager", FakeStageInManager):
                with mock.patch.object(runner_module, "ROOT", FakeROOT):
                    samples = [("ZZ", ["/store/file.root"], "1.0", 0, False, {})]
                    runner_module.RunAnalysis(
                        samples,
                        aliases={},
                        variables={},
                        cuts={"preselections": "1", "cuts": {}},
                        nuisances={},
                        lumi=1.0,
                        remote_io_settings={
                            "inputAccessMode": "stage-in",
                            "xrdReadEndpoint": "root://read.example",
                            "stageInScratch": tmp,
                        },
                    )
        self.assertEqual(events[0], ("stage", ("/store/file.root",)))
        self.assertEqual(events[1], ("add", "staged:/store/file.root"))

    def test_batch_output_identifier_has_sample_id_without_shell_folder(self):
        from mkShapesRDF.shapeAnalysis.BatchSubmission import BatchSubmission

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            startpath = tmp_path / "start.sh"
            startpath.write_text("#!/bin/sh\n")
            old_startpath = os.environ.get("STARTPATH")
            os.environ["STARTPATH"] = str(startpath)
            try:
                batch = BatchSubmission(
                    folder=str(tmp_path),
                    outputPath=str(tmp_path / "out"),
                    batchFolder=str(tmp_path / "batch"),
                    headersPath=str(tmp_path / "headers.hh"),
                    runnerPath=str(tmp_path / "runner.py"),
                    tag="tag",
                    samples=[("SAMPLE", ["input.root"], "1.0", 0, False, {})],
                    d={
                        "outputFile": "mkShapes.root",
                        "mountEOS": [],
                        "remoteIO": {"inputAccessMode": "as-configured"},
                    },
                    batchVars=["samples", "remoteIO"],
                    jdlconfigfile="",
                )
                (tmp_path / "out").mkdir()
                batch.createBatches()
                batch.submit(dryRun=1)
            finally:
                if old_startpath is None:
                    os.environ.pop("STARTPATH", None)
                else:
                    os.environ["STARTPATH"] = old_startpath

            run_sh = (tmp_path / "batch" / "tag" / "run.sh").read_text()
            submit_jdl = (tmp_path / "batch" / "tag" / "submit.jdl").read_text()
            script_py = (tmp_path / "batch" / "tag" / "SAMPLE_0" / "script.py").read_text()
            self.assertIn("SAMPLE_0", script_py)
            self.assertNotIn("${1}", run_sh)
            self.assertNotIn("$(Folder)", submit_jdl)
            self.assertIn('__ALL__" + job_id', run_sh)
            self.assertTrue(run_sh.startswith("#!/bin/bash\nset -euo pipefail\n"))
            self.assertIn(
                f"set +u\nsource {startpath}\nset -u\n", run_sh
            )
            self.assertIn("when_to_transfer_output = ON_EXIT", submit_jdl)

    def test_pinned_file_override_avoids_production_discovery(self):
        import mkShapesRDF.lib.search_files as search_files

        def fail_search(*args, **kwargs):
            raise AssertionError("production discovery should not run for pinnedFiles")

        fixture = (
            Path(__file__).parents[1]
            / "PlotsConfigurationsRun3"
            / "ZH_4lMET"
            / "ZZ_CR"
            / "samples.py"
        )
        with mock.patch.object(search_files.SearchFiles, "searchFiles", fail_search):
            globs = {"pinnedFiles": ["pinned.root"], "__file__": str(fixture)}
            exec(fixture.read_text(), globs, globs)
        self.assertEqual(globs["samples"]["ZZ"]["name"], [("ZZ", ["pinned.root"])])

        root_url = "root://eoscms.cern.ch//store/test/pinned.root"
        with mock.patch.object(search_files.SearchFiles, "searchFiles", fail_search):
            with mock.patch.dict(os.environ, {"ZZCR_PINNED_FILES": root_url}):
                globs = {"__file__": str(fixture)}
                exec(fixture.read_text(), globs, globs)
        self.assertEqual(globs["samples"]["ZZ"]["name"], [("ZZ", [root_url])])

    def test_plural_zzcr_config_compiles_with_pinned_file(self):
        from mkShapesRDF.shapeAnalysis.ConfigLib import ConfigLib

        cfg_dir = (
            Path(__file__).parents[1]
            / "PlotsConfigurationsRun3"
            / "ZH_4lMET"
            / "ZZ_CR"
        )
        old_cwd = os.getcwd()
        try:
            os.chdir(cfg_dir)
            globs = {
                "__file__": str(cfg_dir / "configuration.py"),
                "pinnedFiles": ["root://eoscms.cern.ch//store/test/pinned.root"],
            }
            ConfigLib.loadConfig(["configuration.py"], globs)
            ConfigLib.loadConfig(globs["filesToExec"], globs, globs["imports"])
            self.assertIn("ZZ", globs["samples"])
            self.assertIn("remoteIO", globs["varsToKeep"])
            self.assertIn("remoteIO", globs["batchVars"])
            self.assertEqual(globs["xrdWriteEndpoint"], "root://cmseos.fnal.gov")
            self.assertTrue(globs["zzcrRemoteOutputLFN"].startswith("/store/user/"))
        finally:
            os.chdir(old_cwd)

    def test_remote_batch_uses_framework_stage_out(self):
        from mkShapesRDF.shapeAnalysis.BatchSubmission import BatchSubmission

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            startpath = tmp_path / "start.sh"
            startpath.write_text("#!/bin/sh\n")
            with mock.patch.dict(os.environ, {"STARTPATH": str(startpath)}):
                batch = BatchSubmission(
                    folder=str(tmp_path),
                    outputPath="root://cmseos.fnal.gov//store/user/test/mkShapesRDF_zzcr_tests/campaign/rootFile",
                    batchFolder=str(tmp_path / "batch"),
                    headersPath=str(tmp_path / "headers.hh"),
                    runnerPath=str(tmp_path / "runner.py"),
                    tag="tag",
                    samples=[("SAMPLE", ["input.root"], "1.0", 0, False, {})],
                    d={
                        "outputFile": "mkShapes.root",
                        "mountEOS": [],
                        "remoteIO": {
                            "inputAccessMode": "as-configured",
                            "xrdWriteEndpoint": "root://cmseos.fnal.gov",
                            "existingOutputPolicy": "fail",
                        },
                    },
                    batchVars=["samples", "remoteIO"],
                    jdlconfigfile="",
                )
                batch.createBatches()
                batch.submit(dryRun=1)
            run_sh = (tmp_path / "batch" / "tag" / "run.sh").read_text()
            self.assertIn("stage_out(source, destination", run_sh)
            self.assertIn("root://cmseos.fnal.gov//store/user/test", run_sh)
            self.assertNotIn("${1}", run_sh)
            self.assertNotIn("destination already exists after failed xrdcp", run_sh)

    def test_default_zzcr_test_lfn_has_no_whitespace(self):
        cfg_dir = (
            Path(__file__).parents[1]
            / "PlotsConfigurationsRun3"
            / "ZH_4lMET"
            / "ZZ_CR"
        )
        with tempfile.TemporaryDirectory() as tmp:
            old_cwd = os.getcwd()
            try:
                os.chdir(tmp)
                with mock.patch.dict(
                    os.environ,
                    {
                        "ZZCR_OUTPUT_MODE": "local",
                        "ZZCR_CONFIG_DIR": str(cfg_dir),
                    },
                    clear=False,
                ):
                    os.environ.pop("ZZCR_TEST_OUTPUT_LFN", None)
                    globs = {"__file__": str(cfg_dir / "configuration.py")}
                    exec((cfg_dir / "configuration.py").read_text(), globs, globs)
            finally:
                os.chdir(old_cwd)
        assert globs["testOutputLFN"].startswith("/store/")
        assert not any(char.isspace() for char in globs["testOutputLFN"])


if __name__ == "__main__":
    unittest.main()
