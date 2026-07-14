import errno
import subprocess
from pathlib import Path
import os
import shutil
import shlex
import sys
import re
from textwrap import dedent

from mkShapesRDF.lib.runtime_package import build_runtime_archive


def _run_condor_submit(argv, **run_kwargs):
    """Run Condor submission argv, with an ENOEXEC-only shell fallback."""
    command = list(argv)
    run_kwargs.setdefault("timeout", 120)
    try:
        result = subprocess.run(command, **run_kwargs)
        result.mkshapesrdf_enoexec_fallback = False
        return result
    except OSError as exc:
        if exc.errno != errno.ENOEXEC:
            raise
        resolved_executable = shutil.which(command[0])
        if resolved_executable is None:
            raise
        print(
            "condor_submit direct execution returned ENOEXEC; "
            f"retrying argument-safe via /bin/sh {resolved_executable}",
            file=sys.stderr,
        )
        result = subprocess.run(
            ["/bin/sh", resolved_executable, *command[1:]], **run_kwargs
        )
        result.mkshapesrdf_enoexec_fallback = True
        return result


class CondorSubmissionError(subprocess.CalledProcessError):
    """A Condor client ran and returned a checked nonzero status."""

    def __str__(self):
        return (
            f"Condor {self.action} client ran but returned status {self.returncode}. "
            "This is later than executable process creation; inspect the preserved "
            "stderr to distinguish wrapper/site setup, collector/schedd/authentication, "
            "or scheduler rejection. "
            f"Receipt: {self.receipt_path}; stderr: {self.stderr_path}"
        )


def _safe_terse_receipt(stdout):
    """Return one printable job-id range, without echoing arbitrary client output."""
    for line in (stdout or "").splitlines():
        candidate = line.strip()
        if re.fullmatch(r"[0-9]+\.[0-9]+(?:\s+-\s+[0-9]+\.[0-9]+)?", candidate):
            return candidate
    return None


def _record_condor_submit_result(result, submit_dir, action):
    """Persist raw evidence, validate status, and report the submission layer."""
    submit_dir = Path(submit_dir).resolve()
    receipt_path = submit_dir / "submit.receipt.txt"
    stderr_path = submit_dir / "submit.stderr.txt"
    receipt_path.write_text(result.stdout or "")
    stderr_path.write_text(result.stderr or "")

    if result.returncode != 0:
        error = CondorSubmissionError(
            result.returncode,
            result.args,
            output=result.stdout,
            stderr=result.stderr,
        )
        error.action = action
        error.receipt_path = receipt_path
        error.stderr_path = stderr_path
        raise error

    receipt = _safe_terse_receipt(result.stdout)
    if receipt:
        print(f"Condor {action} accepted by the scheduler: {receipt}")
    else:
        print(
            f"Condor {action} returned success; the raw receipt is preserved "
            f"({len(result.stdout or '')} bytes)."
        )
    if getattr(result, "mkshapesrdf_enoexec_fallback", False):
        print("ENOEXEC compatibility fallback completed successfully.")
    print(f"Raw receipt: {receipt_path}; submit stderr: {stderr_path}")


class BatchSubmission:
    @staticmethod
    def _runtime_pythonpath(project_folder):
        module_path = Path(__file__).resolve()
        for candidate in module_path.parents:
            if (candidate / "mkShapesRDF" / "__init__.py").is_file():
                return str(candidate)
        folder = Path(project_folder).resolve()
        for candidate in [folder, *folder.parents]:
            if (candidate / "mkShapesRDF" / "__init__.py").is_file():
                return str(candidate)
        return str(folder)

    @staticmethod
    def _create_runtime_package(
        project_folder,
        destination,
        framework_root=None,
        additional_includes=None,
        return_layout=False,
    ):
        # The two-argument form remains a useful internal/testing seam.  Real
        # BatchSubmission calls pass the framework root resolved from runner.py.
        framework_root = framework_root or project_folder
        layout = build_runtime_archive(
            framework_root,
            project_folder,
            destination,
            additional_includes=additional_includes,
        )
        return layout if return_layout else layout.archive

    def _framework_root(self):
        runner = Path(self.runnerPath).resolve()
        for candidate in runner.parents:
            if (candidate / "mkShapesRDF" / "__init__.py").is_file():
                return candidate
        project = Path(self.project_folder).resolve()
        if not (project / "configuration.py").is_file():
            return project
        return Path(self._runtime_pythonpath(project)).resolve()

    def _runtime_path_specs(self):
        framework = self._framework_root()
        project = Path(self.project_folder).resolve()
        if project == framework:
            config_archive_root = "."
        elif os.path.commonpath((str(project), str(framework))) == str(framework):
            config_archive_root = project.relative_to(framework).as_posix()
        else:
            config_archive_root = "configuration"
        specs = [
            (str(framework), "__MKSHAPESRDF_RUNTIME_ROOT__", "."),
            (str(project), "__MKSHAPESRDF_CONFIG_ROOT__", config_archive_root),
        ]
        for index, include in enumerate(self.d.get("condorRuntimeIncludes", [])):
            include_path = Path(include).expanduser()
            if not include_path.is_absolute():
                include_path = project / include_path
            include_path = include_path.resolve(strict=True)
            safe_name = "".join(
                char if char.isalnum() or char in "._-" else "_"
                for char in include_path.name
            ) or f"include_{index}"
            archive_root = f"runtime_includes/{index:03d}_{safe_name}"
            specs.append(
                (
                    str(include_path),
                    f"__MKSHAPESRDF_RUNTIME_INCLUDE_{index:03d}__",
                    archive_root,
                )
            )
        return sorted(specs, key=lambda item: len(item[0]), reverse=True)

    @staticmethod
    def _tokenize_runtime_paths(value, specs):
        if isinstance(value, str):
            for source, token, _archive_root in specs:
                value = value.replace(source, token)
            return value
        if isinstance(value, list):
            return [BatchSubmission._tokenize_runtime_paths(item, specs) for item in value]
        if isinstance(value, tuple):
            return tuple(
                BatchSubmission._tokenize_runtime_paths(item, specs) for item in value
            )
        if isinstance(value, dict):
            return {
                key: BatchSubmission._tokenize_runtime_paths(item, specs)
                for key, item in value.items()
            }
        return value

    @staticmethod
    def _jdl_string(value):
        value = str(value)
        if "\n" in value or "\r" in value or "\0" in value:
            raise ValueError("HTCondor values cannot contain NUL or newlines")
        return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'

    @staticmethod
    def _jdl_remap_destination(value):
        value = str(value)
        if any(token in value for token in (";", "=", "\n", "\r", "\0", '"')):
            raise ValueError(
                "HTCondor output remap destinations cannot contain ;, =, quotes, NUL, or newlines"
            )
        return value

    @staticmethod
    def _jdl_x509_proxy(value):
        value = str(value)
        if any(token in value for token in (" ", "\t", "\n", "\r", "\0", '"')):
            raise ValueError(
                "HTCondor x509userproxy paths cannot contain whitespace, quotes, NUL, or newlines"
            )
        return value

    @staticmethod
    def _jdl_file_list(values):
        """Render HTCondor's comma-delimited file-list syntax.

        Quoting the complete list makes the quote part of the first/last file
        name on FNAL schedds.  Keep the upstream-compatible list form and
        reject characters that would change its item boundaries.
        """
        rendered = []
        for value in values:
            value = str(value)
            if value != value.strip() or any(
                token in value for token in (",", "\n", "\r", "\0", '"')
            ):
                raise ValueError(
                    "HTCondor transfer input paths cannot contain commas, quotes, "
                    "NUL, newlines, or leading/trailing whitespace"
                )
            rendered.append(value)
        return ", ".join(rendered)

    @staticmethod
    def _stage_x509_proxy(batchFolder, tag):
        source = Path(os.environ.get("X509_USER_PROXY") or f"/tmp/x509up_u{os.getuid()}")
        if not source.is_file() or not os.access(source, os.R_OK):
            raise RuntimeError(
                f"useX509Proxy is enabled but no readable proxy exists: {source}"
            )

        destination = Path(batchFolder) / tag / f"x509up_u{os.getuid()}"
        destination.parent.mkdir(parents=True, exist_ok=True)
        if source.resolve() != destination.resolve():
            shutil.copyfile(source, destination)
        os.chmod(destination, 0o600)
        return str(destination.resolve())

    @staticmethod
    def resubmitJobs(batchFolder, tag, samples, dryRun, queue):
        """
        Resubmit failed jobs and rename the old error file to err-1.txt
        Args:
            batchFolder (string): path to the batch folder
            tag (string): string used to tag the configuration
            samples (list of strings): samples to be resubmitted in the form of ['DY_0', ...]
        """

        # Path(f'{self.batchFolder}/{self.tag}/{sampleName}_{str(i)}').mkdir(parents=True, exist_ok=False)
        for sample in samples:
            if os.path.exists(f"{batchFolder}/{tag}/{sample}/err.txt"):
                os.rename(
                    f"{batchFolder}/{tag}/{sample}/err.txt",
                    f"{batchFolder}/{tag}/{sample}/err-1.txt",
                )
        with open(f"{batchFolder}/{tag}/submit.jdl") as file:
            txt = file.read()
        lines = txt.split("\n")
        line = list(filter(lambda k: k.startswith("queue"), lines))[0]
        jobflavour = list(filter(lambda k: k.startswith("+JobFlavour"), lines))[0]
        lines[lines.index(line)] = f'queue 1 JobId in {", ".join(samples)}\n '
        lines[lines.index(jobflavour)] = f'+JobFlavour = "{queue}"\n '
        with open(f"{batchFolder}/{tag}/submit.jdl", "w") as file:
            file.write("\n".join(lines))

        if dryRun != 1:
            result = _run_condor_submit(
                ["condor_submit", "-terse", "submit.jdl"],
                cwd=f"{batchFolder}/{tag}",
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            _record_condor_submit_result(
                result, f"{batchFolder}/{tag}", "resubmission"
            )

    def __init__(
        self,
        folder,
        outputPath,
        batchFolder,
        headersPath,
        runnerPath,
        tag,
        samples,
        d,
        batchVars,
        jdlconfigfile,
    ):
        self.project_folder = folder
        self.outputPath = outputPath
        self.batchFolder = batchFolder
        self.headersPath = headersPath
        self.runnerPath = runnerPath
        self.tag = tag

        self.samples = samples
        self.d = d
        self.batchVars = batchVars
        self.jdlconfigfile = jdlconfigfile

        self.folders = []

    def createBatch(self, sample):
        # 1. create submission folder
        # 2. create executable python file
        # 3. create bash file
        # 4. create condor file
        # 5. append condor file to submit files

        # submission folder
        sampleName = sample[0]
        i = sample[3]
        try:
            Path(f"{self.batchFolder}/{self.tag}/{sampleName}_{str(i)}").mkdir(
                parents=True, exist_ok=False
            )
        except:  # noqa E722
            print("Error creating condor folder!")
        self.folders.append(f"{sampleName}_{str(i)}")
        # python file

        packaged = bool(self.d.get("condorRuntimePackage"))
        runtime_specs = self._runtime_path_specs() if packaged else []
        txtpy = "from collections import OrderedDict\n"
        if packaged:
            replacements = {}
            for _source, token, archive_root in runtime_specs:
                if archive_root in ("", "."):
                    replacements[token] = "__RUNTIME_ROOT__"
                else:
                    replacements[token] = f"__RUNTIME_ROOT__/{archive_root}"
            txtpy += "import os\n"
            txtpy += '_runtime_root = os.environ.get("MKSHAPESRDF_RUNTIME_DIR")\n'
            txtpy += "if not _runtime_root:\n"
            txtpy += "    raise RuntimeError('MKSHAPESRDF_RUNTIME_DIR is required')\n"
            txtpy += f"_runtime_replacements = {repr(replacements)}\n"
            txtpy += "_runtime_replacements = {key: value.replace('__RUNTIME_ROOT__', _runtime_root) for key, value in _runtime_replacements.items()}\n"
            txtpy += "def _expand_runtime_paths(value):\n"
            txtpy += "    if isinstance(value, str):\n"
            txtpy += "        for key, replacement in _runtime_replacements.items():\n"
            txtpy += "            value = value.replace(key, replacement)\n"
            txtpy += "        return value\n"
            txtpy += "    if isinstance(value, list):\n"
            txtpy += "        return [_expand_runtime_paths(item) for item in value]\n"
            txtpy += "    if isinstance(value, tuple):\n"
            txtpy += "        return tuple(_expand_runtime_paths(item) for item in value)\n"
            txtpy += "    if isinstance(value, dict):\n"
            txtpy += "        return {key: _expand_runtime_paths(item) for key, item in value.items()}\n"
            txtpy += "    return value\n"
        txtpy += f"job_id = {repr(sampleName + '_' + str(i))}\n"

        _samples = [sample]
        if packaged:
            _samples = self._tokenize_runtime_paths(_samples, runtime_specs)
            txtpy += f"samples = _expand_runtime_paths({repr(_samples)})\n"
        else:
            txtpy += f"samples = {str(_samples)}\n"

        for var in self.batchVars:
            _var = var
            if not isinstance(var, str):
                _var = var[0]

            if _var == "samples":
                continue
            value = self.d[_var]
            if packaged:
                value = self._tokenize_runtime_paths(value, runtime_specs)
                txtpy += f"{_var} = _expand_runtime_paths({repr(value)})\n"
            elif isinstance(value, int) or isinstance(value, float):
                txtpy += f"{_var} = {value}\n"
            else:
                txtpy += f"{_var} = {repr(value)}\n"

        with open(
            f"{self.batchFolder}/{self.tag}/{sampleName}_{str(i)}/script.py", "w"
        ) as f:
            f.write(txtpy)

    def createBatches(self):
        try:
            print("Removing dir:", os.path.abspath(f"{self.batchFolder}/{self.tag}"))
            shutil.rmtree(os.path.abspath(f"{self.batchFolder}/{self.tag}"))
        except Exception as e:
            print("Error removing directory", e)

        for sample in self.samples:
            self.createBatch(sample)

    def submit(self, dryRun=0, queue="workday"):

        txtsh = "#!/bin/bash\n"
        txtsh += "set -euo pipefail\n"
        use_jdlconfigfile = (
            self.jdlconfigfile != "" and not self.d.get("condorRuntimePackage")
        )
        proxy_input = None
        package_layout = None
        runtime_package_helper = None
        if self.d.get("useX509Proxy"):
            proxy_input = self._stage_x509_proxy(self.batchFolder, self.tag)

        if use_jdlconfigfile:
            try:
                print("Opening jdlconfigfile")
                print(self.project_folder + "/" + self.jdlconfigfile)
                exec(
                    open(self.project_folder + "/" + self.jdlconfigfile).read(),
                    globals(),
                )
            except Exception as e:
                print('could not parse jdlconfigfile "', self.jdlconfigfile, '"\n', e)
                use_jdlconfigfile = False

        if use_jdlconfigfile:
            txtsh += "\n".join(executable)
        else:
            package_input = None
            package_name = self.d.get("condorRuntimePackageName", "mkshapesrdf_runtime.tgz")
            if self.d.get("condorRuntimePackage"):
                if not package_name or Path(package_name).name != package_name:
                    raise RuntimeError(
                        "condorRuntimePackageName must be a worker-local basename"
                    )
                package_layout = self._create_runtime_package(
                    self.project_folder,
                    Path(f"{self.batchFolder}/{self.tag}") / package_name,
                    framework_root=self._framework_root(),
                    additional_includes=self.d.get("condorRuntimeIncludes", []),
                    return_layout=True,
                )
                package_input = package_layout.archive
                runtime_package_helper = Path(__file__).resolve().parents[1] / "lib" / "runtime_package.py"
                extract_command = [
                    "python3",
                    runtime_package_helper.name,
                    "extract",
                    os.path.basename(package_input),
                    "runtime",
                ]
                for required_member in package_layout.required_members:
                    extract_command.extend(["--require", required_member])
                txtsh += shlex.join(extract_command) + "\n"
                txtsh += 'export MKSHAPESRDF_RUNTIME_DIR="$PWD/runtime"\n'
                txtsh += "export PYTHONNOUSERSITE=1\n"
                if self.d.get("condorRuntimeSetup", []):
                    txtsh += "set +u\n"
                    for setup_line in self.d.get("condorRuntimeSetup", []):
                        txtsh += f"{setup_line}\n"
                    txtsh += "set -u\n"
                txtsh += 'export PYTHONPATH="$PWD/runtime:${PYTHONPATH:-}"\n'
                txtsh += 'export PATH="$PWD/runtime/utils/bin:${PATH:-}"\n'
            else:
                startpath = Path(os.environ["STARTPATH"]).resolve()
                if not startpath.is_file() or not os.access(startpath, os.R_OK):
                    raise RuntimeError(f"STARTPATH is not a readable file: {startpath}")
                txtsh += "set +u\n"
                txtsh += f"source {shlex.quote(str(startpath))}\n"
                txtsh += "set -u\n"

                txtsh += f'export PYTHONPATH="{self._runtime_pythonpath(self.project_folder)}:${{PYTHONPATH:-}}"\n'

            if proxy_input:
                txtsh += f'export X509_USER_PROXY="$PWD/{os.path.basename(proxy_input)}"\n'
                txtsh += 'test -r "$X509_USER_PROXY"\n'
                txtsh += 'test "$(stat -c %a "$X509_USER_PROXY")" = "600"\n'
                txtsh += 'proxy_timeleft=$(voms-proxy-info -file "$X509_USER_PROXY" -timeleft)\n'
                txtsh += 'test "$proxy_timeleft" -gt 0\n'
                txtsh += 'printf "X509 proxy mode=600 timeleft=%s\\n" "$proxy_timeleft"\n'

            mE = self.d.get("mountEOS", [])
            for line in mE:
                txtsh += line

            runnerScriptFilename = self.runnerPath.split("/")[-1]
            txtsh += f"time python3 {shlex.quote(runnerScriptFilename)}\n"

            outputFileTrunc = ".".join(self.d["outputFile"].split(".")[:-1])

            printable_output_path = (
                self.outputPath
                if str(self.outputPath).startswith("root://")
                else os.path.realpath(self.outputPath)
            )
            print("\n\nReal output path:", printable_output_path, "\n\n")

            if os.path.realpath(self.outputPath).startswith("/eos"):
                # eos is not supported -> use xrdcp
                fullOutfile = f"{os.path.realpath(self.outputPath)}/"
            else:
                fullOutfile = f"{self.outputPath}/"

            packaged_local_return = self.d.get("condorRuntimePackage") and not str(
                self.outputPath
            ).startswith("root://")
            if packaged_local_return:
                output_file_arg = shlex.quote(outputFileTrunc)
                txtsh += dedent(
                    f"""\
                    python3 - "$1" "output.root" {output_file_arg} <<'PY'
                    import os
                    import sys

                    job_id, source, output_file_trunc = sys.argv[1:4]
                    output_name = output_file_trunc + "__ALL__" + job_id + ".root"
                    os.replace(source, output_name)
                    PY
                    """
                )
            else:
                output_dir_arg = shlex.quote(fullOutfile)
                output_file_arg = shlex.quote(outputFileTrunc)
                txtsh += dedent(
                    f"""\
                    python3 - "$1" "output.root" {output_dir_arg} {output_file_arg} <<'PY'
                    import os
                    import shutil
                    import sys
                    from mkShapesRDF.lib.remote_io import stage_out

                    job_id, source, output_dir, output_file_trunc = sys.argv[1:5]
                    output_name = output_file_trunc + "__ALL__" + job_id + ".root"
                    if output_dir.startswith("root://"):
                        destination = output_dir.rstrip("/") + "/" + output_name
                        stage_out(source, destination, {repr(self.d.get("remoteIO", {}))})
                    else:
                        destination = os.path.join(output_dir, output_name)
                        shutil.copy2(source, destination)
                    PY
                    """
                )
            txtsh += "rm -f output.root\n"
            txtsh += "rm -f script.py\n"

        # write the run.sh file
        run_script = Path(f"{self.batchFolder}/{self.tag}/run.sh")
        with open(run_script, "w") as file:
            file.write(txtsh)
        # make it executable
        os.chmod(run_script, 0o755)

        txtjdl = "universe = vanilla \n"
        txtjdl += "executable = run.sh\n"
        txtjdl += "arguments = $(JobId)\n"

        txtjdl += "should_transfer_files = YES\n"
        txtjdl += "when_to_transfer_output = ON_EXIT\n"
        if proxy_input:
            txtjdl += f"x509userproxy = {self._jdl_x509_proxy(proxy_input)}\n"

        if use_jdlconfigfile:

            for key in jdl_dict:
                if jdl_dict[key] != "":

                    txtjdl += key + " = " + jdl_dict[key] + "\n"
        else:

            transfer_inputs = [
                "$(JobId)/script.py",
                self.headersPath,
                self.runnerPath,
            ]
            if self.d.get("condorRuntimePackage"):
                transfer_inputs.append(package_input)
                transfer_inputs.append(str(runtime_package_helper))
            if proxy_input:
                transfer_inputs.append(proxy_input)
            txtjdl += (
                "transfer_input_files = "
                + self._jdl_file_list(transfer_inputs)
                + "\n"
            )

            if self.d.get("condorRuntimePackage"):
                if str(self.outputPath).startswith("root://"):
                    txtjdl += 'transfer_output_files = ""\n'
                else:
                    Path(self.outputPath).mkdir(parents=True, exist_ok=True)
                    output_file_trunc = ".".join(self.d["outputFile"].split(".")[:-1])
                    returned_name = f"{output_file_trunc}__ALL__$(JobId).root"
                    returned_path = self._jdl_remap_destination(
                        Path(self.outputPath).resolve() / returned_name
                    )
                    txtjdl += f"transfer_output_files = {returned_name}\n"
                    txtjdl += (
                        "transfer_output_remaps = "
                        + self._jdl_string(f"{returned_name} = {returned_path}")
                        + "\n"
                    )

        txtjdl += "output = $(JobId)/out.txt\n"
        txtjdl += "error  = $(JobId)/err.txt\n"
        txtjdl += "log    = $(JobId)/log.txt\n"

        txtjdl += "request_cpus   = 1\n"
        txtjdl += f'+JobFlavour = "{queue}"\n'

        txtjdl += f'queue 1 JobId in {", ".join(self.folders)}\n'
        with open(f"{self.batchFolder}/{self.tag}/submit.jdl", "w") as file:
            file.write(txtjdl)

        condor_args = []
        if dryRun != 1:

            if use_jdlconfigfile:
                condor_args = list(condor_config)

            proc_command = ["condor_submit", "-terse"] + condor_args + ["submit.jdl"]
            print(" ".join(proc_command))

            result = _run_condor_submit(
                proc_command,
                cwd=f"{self.batchFolder}/{self.tag}",
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            _record_condor_submit_result(
                result, f"{self.batchFolder}/{self.tag}", "submission"
            )
