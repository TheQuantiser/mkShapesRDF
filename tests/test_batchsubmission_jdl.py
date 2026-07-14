import errno
import os
import subprocess
import tarfile
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from mkShapesRDF.shapeAnalysis.BatchSubmission import (
    BatchSubmission,
    _run_condor_submit,
)


class CondorSubmitCommandRunnerTests(unittest.TestCase):
    @staticmethod
    def _script(path, contents, executable=True):
        path.write_text(contents)
        if executable:
            path.chmod(path.stat().st_mode | 0o700)
        return path

    def test_native_executable_runs_directly_without_fallback(self):
        with mock.patch(
            "mkShapesRDF.shapeAnalysis.BatchSubmission.shutil.which",
            side_effect=AssertionError("native execution must not resolve fallback"),
        ):
            result = _run_condor_submit(
                ["/bin/echo", "native-ok"],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "native-ok\n")
        self.assertIs(result.mkshapesrdf_enoexec_fallback, False)

    def test_valid_shebang_script_runs_directly_without_fallback(self):
        with tempfile.TemporaryDirectory() as tmp:
            script = self._script(
                Path(tmp) / "valid_shebang",
                "#!/bin/sh\nprintf 'shebang:%s\\n' \"$1\"\n",
            )
            with mock.patch(
                "mkShapesRDF.shapeAnalysis.BatchSubmission.shutil.which",
                side_effect=AssertionError("shebang execution must not use fallback"),
            ):
                result = _run_condor_submit(
                    [str(script), "direct"],
                    text=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "shebang:direct\n")

    def test_no_shebang_fallback_preserves_argv_cwd_streams_and_returncode(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            cwd = tmp_path / "working directory"
            cwd.mkdir()
            marker = tmp_path / "must_not_exist"
            wrapper = self._script(
                tmp_path / "condor_submit",
                "printf 'cwd=%s\\n' \"$PWD\"\n"
                "for arg in \"$@\"; do printf 'arg=%s\\n' \"$arg\"; done\n"
                "printf 'fallback-stderr\\n' >&2\n"
                "exit 7\n",
            )
            literal_args = [
                "value with spaces",
                f"$(touch {marker})",
                "*.root",
                "; echo injected",
            ]
            with mock.patch(
                "mkShapesRDF.shapeAnalysis.BatchSubmission.shutil.which",
                wraps=__import__("shutil").which,
            ) as which:
                result = _run_condor_submit(
                    [str(wrapper), *literal_args],
                    cwd=cwd,
                    text=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )
            which.assert_called_once_with(str(wrapper))
            self.assertEqual(result.returncode, 7)
            self.assertEqual(
                result.stdout.splitlines(),
                [f"cwd={cwd}", *[f"arg={arg}" for arg in literal_args]],
            )
            self.assertEqual(result.stderr, "fallback-stderr\n")
            self.assertFalse(marker.exists())

    def test_enoexec_fallback_executes_wrapper_once(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            counter = tmp_path / "counter"
            wrapper = self._script(
                tmp_path / "condor_submit",
                f"printf x >> {counter}\nprintf '123.0 - 123.0\\n'\n",
            )
            result = _run_condor_submit(
                [str(wrapper), "-terse", "submit.jdl"],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            self.assertEqual(result.returncode, 0)
            self.assertEqual(result.stdout, "123.0 - 123.0\n")
            self.assertEqual(counter.read_text(), "x")
            self.assertIs(result.mkshapesrdf_enoexec_fallback, True)

    def test_only_enoexec_triggers_fallback(self):
        with tempfile.TemporaryDirectory() as tmp:
            non_executable = self._script(
                Path(tmp) / "not_executable", "#!/bin/sh\nexit 0\n", executable=False
            )
            with mock.patch(
                "mkShapesRDF.shapeAnalysis.BatchSubmission.shutil.which"
            ) as which:
                with self.assertRaises(PermissionError):
                    _run_condor_submit([str(non_executable)])
                which.assert_not_called()

        with mock.patch(
            "mkShapesRDF.shapeAnalysis.BatchSubmission.shutil.which"
        ) as which:
            with self.assertRaises(FileNotFoundError):
                _run_condor_submit(["definitely_missing_condor_submit_fixture"])
            which.assert_not_called()

        unrelated = OSError(errno.EIO, "forced unrelated I/O error")
        with mock.patch(
            "mkShapesRDF.shapeAnalysis.BatchSubmission.subprocess.run",
            side_effect=unrelated,
        ) as run:
            with mock.patch(
                "mkShapesRDF.shapeAnalysis.BatchSubmission.shutil.which"
            ) as which:
                with self.assertRaises(OSError) as raised:
                    _run_condor_submit(["condor_submit"])
                self.assertEqual(raised.exception.errno, errno.EIO)
                self.assertEqual(run.call_count, 1)
                which.assert_not_called()

    def test_timeout_and_normal_nonzero_are_not_retried(self):
        with mock.patch(
            "mkShapesRDF.shapeAnalysis.BatchSubmission.shutil.which"
        ) as which:
            with self.assertRaises(subprocess.TimeoutExpired):
                _run_condor_submit(["/bin/sleep", "1"], timeout=0.01)
            which.assert_not_called()

        with tempfile.TemporaryDirectory() as tmp:
            script = self._script(
                Path(tmp) / "nonzero", "#!/bin/sh\nprintf 'ordinary failure\\n' >&2\nexit 9\n"
            )
            with mock.patch(
                "mkShapesRDF.shapeAnalysis.BatchSubmission.shutil.which"
            ) as which:
                result = _run_condor_submit(
                    [str(script)],
                    text=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )
                which.assert_not_called()
        self.assertEqual(result.returncode, 9)
        self.assertEqual(result.stderr, "ordinary failure\n")


class BatchSubmissionProxyTests(unittest.TestCase):
    def _make_batch(self, tmp_path, d=None):
        project = tmp_path / "project"
        project.mkdir(exist_ok=True)
        (project / "module.py").write_text("VALUE = 1\n")
        startpath = tmp_path / "start.sh"
        startpath.write_text("#!/bin/sh\n")
        base_config = {
            "outputFile": "mkShapes.root",
            "mountEOS": [],
            "remoteIO": {"inputAccessMode": "as-configured"},
        }
        base_config.update(d or {})
        return BatchSubmission(
            folder=str(project),
            outputPath=str(tmp_path / "out"),
            batchFolder=str(tmp_path / "batch"),
            headersPath=str(tmp_path / "headers.hh"),
            runnerPath=str(tmp_path / "runner.py"),
            tag="tag",
            samples=[("SAMPLE", ["input.root"], "1.0", 0, False, {})],
            d=base_config,
            batchVars=["samples", "remoteIO"],
            jdlconfigfile="",
        )

    def _create_outputs(self, batch, env):
        with mock.patch.dict(os.environ, env, clear=False):
            batch.createBatches()
            batch.submit(dryRun=1)
        submit_dir = Path(batch.batchFolder) / batch.tag
        return (
            submit_dir,
            (submit_dir / "submit.jdl").read_text(),
            (submit_dir / "run.sh").read_text(),
        )

    def test_x509_proxy_is_copied_to_submit_dir_and_used_by_jdl_and_run_sh(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            proxy = tmp_path / "x509up_u999999"
            proxy.write_text("proxy")
            batch = self._make_batch(tmp_path, {"useX509Proxy": True})

            submit_dir, submit_jdl, run_sh = self._create_outputs(
                batch,
                {"STARTPATH": str(tmp_path / "start.sh"), "X509_USER_PROXY": str(proxy)},
            )

            copied_proxy = submit_dir / f"x509up_u{os.getuid()}"
            self.assertTrue(copied_proxy.is_file())
            self.assertEqual(copied_proxy.read_text(), "proxy")
            self.assertEqual(copied_proxy.stat().st_mode & 0o777, 0o600)
            self.assertIn(str(copied_proxy), submit_jdl)
            self.assertNotIn(str(proxy), submit_jdl)
            self.assertNotIn("/tmp/x509up_u", submit_jdl)
            self.assertIn(f"x509userproxy = {copied_proxy}", submit_jdl)
            self.assertIn(
                f'export X509_USER_PROXY="$PWD/{copied_proxy.name}"',
                run_sh,
            )
            self.assertIn('voms-proxy-info -file "$X509_USER_PROXY" -timeleft', run_sh)

    def test_transfer_input_files_use_unquoted_condor_list_syntax(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            batch = self._make_batch(tmp_path)

            _, submit_jdl, _ = self._create_outputs(
                batch, {"STARTPATH": str(tmp_path / "start.sh")}
            )

            line = next(
                item
                for item in submit_jdl.splitlines()
                if item.startswith("transfer_input_files = ")
            )
            value = line.split("=", 1)[1].strip()
            self.assertFalse(value.startswith('"'))
            self.assertEqual(
                value,
                f"$(JobId)/script.py, {tmp_path / 'headers.hh'}, "
                f"{tmp_path / 'runner.py'}",
            )

    def test_transfer_input_file_list_rejects_ambiguous_paths(self):
        for value in ("a,b", 'a"b', " leading", "trailing ", "a\nb", "a\0b"):
            with self.subTest(value=value):
                with self.assertRaisesRegex(ValueError, "transfer input paths"):
                    BatchSubmission._jdl_file_list([value])

    def test_missing_x509_proxy_fails_before_writing_unsafe_jdl(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            missing_proxy = tmp_path / "missing_proxy"
            batch = self._make_batch(tmp_path, {"useX509Proxy": True})

            with mock.patch.dict(
                os.environ,
                {"STARTPATH": str(tmp_path / "start.sh"), "X509_USER_PROXY": str(missing_proxy)},
                clear=False,
            ):
                batch.createBatches()
                with self.assertRaisesRegex(RuntimeError, "no readable proxy exists"):
                    batch.submit(dryRun=1)

    def test_runtime_package_keeps_proxy_separate_from_tarball(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            project = tmp_path / "project"
            project.mkdir()
            (project / "module.py").write_text("VALUE = 1\n")
            proxy = project / "private_proxy.dat"
            proxy.write_text("proxy")
            batch = self._make_batch(
                tmp_path,
                {
                    "useX509Proxy": True,
                    "condorRuntimePackage": True,
                    "condorRuntimePackageName": "runtime.tgz",
                },
            )

            submit_dir, submit_jdl, run_sh = self._create_outputs(
                batch,
                {"STARTPATH": str(tmp_path / "start.sh"), "X509_USER_PROXY": str(proxy)},
            )

            copied_proxy = submit_dir / f"x509up_u{os.getuid()}"
            runtime_package = submit_dir / "runtime.tgz"
            self.assertIn(str(runtime_package), submit_jdl)
            self.assertIn(str(copied_proxy), submit_jdl)
            self.assertIn(
                "python3 runtime_package.py extract runtime.tgz runtime", run_sh
            )
            self.assertIn("export PYTHONNOUSERSITE=1", run_sh)
            with tarfile.open(runtime_package) as archive:
                members = archive.getnames()
            self.assertIn("module.py", members)
            self.assertFalse(any("x509" in name or "proxy" in name for name in members))

    def test_packaged_local_output_stays_in_scratch_and_is_remapped(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            project = tmp_path / "project"
            project.mkdir()
            (project / "module.py").write_text("VALUE = 1\n")
            output_dir = tmp_path / "returned"
            output_dir.mkdir()
            batch = self._make_batch(
                tmp_path,
                {"condorRuntimePackage": True, "limitEvents": 5},
            )
            batch.batchVars.append("limitEvents")
            batch.outputPath = str(output_dir)
            _, submit_jdl, run_sh = self._create_outputs(
                batch, {"STARTPATH": str(tmp_path / "start.sh")}
            )
            self.assertNotIn(str(output_dir), run_sh)
            self.assertNotIn("shutil.copy2", run_sh)
            self.assertIn("os.replace(source, output_name)", run_sh)
            self.assertIn(
                f"transfer_output_files = mkShapes__ALL__$(JobId).root",
                submit_jdl,
            )
            self.assertIn(
                str(output_dir / "mkShapes__ALL__$(JobId).root"), submit_jdl
            )
            self.assertIn("transfer_output_remaps", submit_jdl)
            script_py = (Path(batch.batchFolder) / batch.tag / "SAMPLE_0" / "script.py").read_text()
            self.assertIn("limitEvents = _expand_runtime_paths(5)", script_py)

    def test_packaged_remote_output_does_not_return_root_or_sandbox(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            batch = self._make_batch(
                tmp_path,
                {"condorRuntimePackage": True},
            )
            batch.outputPath = "root://cmseos.fnal.gov//store/user/test/campaign"
            _, submit_jdl, run_sh = self._create_outputs(
                batch, {"STARTPATH": str(tmp_path / "start.sh")}
            )
            self.assertIn("stage_out(source, destination", run_sh)
            self.assertIn('transfer_output_files = ""', submit_jdl)
            self.assertNotIn("transfer_output_remaps", submit_jdl)

    def test_unpackaged_local_output_retains_shared_checkout_behavior(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            output_dir = tmp_path / "shared"
            output_dir.mkdir()
            batch = self._make_batch(tmp_path)
            batch.outputPath = str(output_dir)
            _, submit_jdl, run_sh = self._create_outputs(
                batch, {"STARTPATH": str(tmp_path / "start.sh")}
            )
            self.assertIn(
                f"set +u\nsource {tmp_path / 'start.sh'}\nset -u", run_sh
            )
            self.assertIn("shutil.copy2(source, destination)", run_sh)
            self.assertNotIn("transfer_output_remaps", submit_jdl)

    def test_use_x509_proxy_false_does_not_add_proxy_transfer(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            proxy = tmp_path / "x509up_u999999"
            proxy.write_text("proxy")
            batch = self._make_batch(tmp_path, {"useX509Proxy": False})

            submit_dir, submit_jdl, run_sh = self._create_outputs(
                batch,
                {"STARTPATH": str(tmp_path / "start.sh"), "X509_USER_PROXY": str(proxy)},
            )

            self.assertNotIn("x509up_u", submit_jdl)
            self.assertNotIn("X509_USER_PROXY", run_sh)
            self.assertFalse((submit_dir / f"x509up_u{os.getuid()}").exists())

    def test_submit_uses_shared_runner_and_writes_evidence_before_nonzero_raises(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            batch = self._make_batch(tmp_path)
            with mock.patch.dict(
                os.environ, {"STARTPATH": str(tmp_path / "start.sh")}, clear=False
            ):
                batch.createBatches()
                completed = subprocess.CompletedProcess(
                    ["condor_submit"], 3, stdout="partial receipt\n", stderr="rejected\n"
                )
                with mock.patch(
                    "mkShapesRDF.shapeAnalysis.BatchSubmission._run_condor_submit",
                    return_value=completed,
                ) as runner:
                    with self.assertRaisesRegex(
                        subprocess.CalledProcessError,
                        "Condor submission client ran but returned status 3",
                    ):
                        batch.submit(dryRun=0)
            submit_dir = Path(batch.batchFolder) / batch.tag
            self.assertEqual((submit_dir / "submit.receipt.txt").read_text(), "partial receipt\n")
            self.assertEqual((submit_dir / "submit.stderr.txt").read_text(), "rejected\n")
            runner.assert_called_once()
            self.assertEqual(
                runner.call_args.args[0], ["condor_submit", "-terse", "submit.jdl"]
            )

    def test_submit_prints_unambiguous_success_receipt_and_evidence_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            batch = self._make_batch(tmp_path)
            with mock.patch.dict(
                os.environ, {"STARTPATH": str(tmp_path / "start.sh")}, clear=False
            ):
                batch.createBatches()
                completed = subprocess.CompletedProcess(
                    ["condor_submit"],
                    0,
                    stdout="789.0 - 789.1\n",
                    stderr="",
                )
                completed.mkshapesrdf_enoexec_fallback = True
                with mock.patch(
                    "mkShapesRDF.shapeAnalysis.BatchSubmission._run_condor_submit",
                    return_value=completed,
                ):
                    with mock.patch("builtins.print") as output:
                        batch.submit(dryRun=0)
            rendered = "\n".join(
                " ".join(str(arg) for arg in call.args) for call in output.call_args_list
            )
            self.assertIn("Condor submission accepted", rendered)
            self.assertIn("789.0 - 789.1", rendered)
            self.assertIn("ENOEXEC compatibility fallback completed", rendered)
            self.assertIn("submit.receipt.txt", rendered)
            self.assertIn("submit.stderr.txt", rendered)

    def test_resubmit_uses_same_shared_runner_and_preserves_queue_rewrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            batch = self._make_batch(tmp_path)
            self._create_outputs(batch, {"STARTPATH": str(tmp_path / "start.sh")})
            completed = subprocess.CompletedProcess(
                ["condor_submit"], 0, stdout="456.0 - 456.0\n", stderr=""
            )
            with mock.patch(
                "mkShapesRDF.shapeAnalysis.BatchSubmission._run_condor_submit",
                return_value=completed,
            ) as runner:
                BatchSubmission.resubmitJobs(
                    batch.batchFolder,
                    batch.tag,
                    ["SAMPLE_0"],
                    dryRun=0,
                    queue="espresso",
                )
            submit_dir = Path(batch.batchFolder) / batch.tag
            jdl = (submit_dir / "submit.jdl").read_text()
            self.assertIn("queue 1 JobId in SAMPLE_0", jdl)
            self.assertIn('+JobFlavour = "espresso"', jdl)
            self.assertEqual((submit_dir / "submit.receipt.txt").read_text(), "456.0 - 456.0\n")
            runner.assert_called_once()
            self.assertEqual(
                runner.call_args.args[0], ["condor_submit", "-terse", "submit.jdl"]
            )

    def test_resubmit_writes_evidence_before_nonzero_raises(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            batch = self._make_batch(tmp_path)
            self._create_outputs(batch, {"STARTPATH": str(tmp_path / "start.sh")})
            completed = subprocess.CompletedProcess(
                ["condor_submit"], 4, stdout="partial resubmit receipt\n", stderr="denied\n"
            )
            with mock.patch(
                "mkShapesRDF.shapeAnalysis.BatchSubmission._run_condor_submit",
                return_value=completed,
            ) as runner:
                with self.assertRaises(subprocess.CalledProcessError):
                    BatchSubmission.resubmitJobs(
                        batch.batchFolder,
                        batch.tag,
                        ["SAMPLE_0"],
                        dryRun=0,
                        queue="espresso",
                    )
            submit_dir = Path(batch.batchFolder) / batch.tag
            self.assertEqual(
                (submit_dir / "submit.receipt.txt").read_text(),
                "partial resubmit receipt\n",
            )
            self.assertEqual(
                (submit_dir / "submit.stderr.txt").read_text(), "denied\n"
            )
            runner.assert_called_once()

    def test_dry_run_never_executes_shared_submit_runner(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            batch = self._make_batch(tmp_path)
            with mock.patch(
                "mkShapesRDF.shapeAnalysis.BatchSubmission._run_condor_submit"
            ) as runner:
                self._create_outputs(batch, {"STARTPATH": str(tmp_path / "start.sh")})
                runner.assert_not_called()


if __name__ == "__main__":
    unittest.main()
