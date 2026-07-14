import hashlib
import os
import shutil
import subprocess
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path


DEFAULT_REMOTE_IO_CONFIG = {
    "inputAccessMode": "as-configured",
    "xrdReadEndpoint": None,
    "xrdDiscoveryEndpoint": None,
    "xrdWriteEndpoint": None,
    "stageInScratch": None,
    "stageInCleanup": "on-success",
    "preserveStageInOnFailure": True,
    "existingOutputPolicy": "fail",
    "remoteCommandTimeout": 120,
    "remoteTransferRetries": 2,
}

INPUT_ACCESS_MODES = ("as-configured", "xrootd", "stage-in")
STAGE_IN_CLEANUP_POLICIES = ("on-success", "always", "never")
EXISTING_OUTPUT_POLICIES = ("fail", "replace", "skip-if-verified-identical")


class RemoteIOError(RuntimeError):
    pass


class RemoteObjectNotFound(RemoteIOError):
    pass


class RemoteCommandError(RemoteIOError):
    def __init__(self, result):
        self.result = result
        detail = result.stderr.strip() or result.stdout.strip() or "no command output"
        timeout_note = " after timeout" if result.timed_out else ""
        super().__init__(
            f"{result.operation} failed{timeout_note} with exit "
            f"{result.returncode}: {detail}"
        )


@dataclass
class CommandResult:
    argv: list
    returncode: int
    stdout: str
    stderr: str
    timed_out: bool
    attempt: int
    operation: str
    metadata: dict = field(default_factory=dict)


class ExternalCommandRunner:
    def __init__(self, timeout=120, retries=2, popen_factory=subprocess.run):
        self.timeout = timeout
        self.retries = retries
        self.popen_factory = popen_factory

    @staticmethod
    def classify_failure(result):
        text = f"{result.stdout}\n{result.stderr}".lower()
        deterministic = (
            "permission denied",
            "authorization",
            "authentication",
            "no such file",
            "destination exists",
            "checksum",
            "root file",
            "invalid path",
        )
        if result.timed_out:
            return "transient"
        if any(token in text for token in deterministic):
            return "deterministic"
        if result.returncode in (0,):
            return "success"
        if result.returncode in (5, 11, 28, 52, 54, 56, 110):
            return "transient"
        return "deterministic"

    def run(self, argv, operation, metadata=None, timeout=None, retries=None):
        if isinstance(argv, str):
            raise TypeError("External commands must be structured argv, not strings")
        metadata = metadata or {}
        timeout = self.timeout if timeout is None else timeout
        retries = self.retries if retries is None else retries
        if not isinstance(timeout, (int, float)) or isinstance(timeout, bool) or timeout <= 0:
            raise ValueError("External command timeout must be a positive number")
        if not isinstance(retries, int) or isinstance(retries, bool) or retries < 0:
            raise ValueError("External command retries must be a non-negative integer")
        last = None
        for attempt in range(1, retries + 2):
            try:
                completed = self.popen_factory(
                    list(argv),
                    shell=False,
                    text=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    timeout=timeout,
                )
                last = CommandResult(
                    list(argv),
                    completed.returncode,
                    completed.stdout or "",
                    completed.stderr or "",
                    False,
                    attempt,
                    operation,
                    dict(metadata),
                )
            except subprocess.TimeoutExpired as exc:
                last = CommandResult(
                    list(argv),
                    124,
                    exc.stdout or "",
                    exc.stderr or "",
                    True,
                    attempt,
                    operation,
                    dict(metadata),
                )
            except OSError as exc:
                last = CommandResult(
                    list(argv),
                    127,
                    "",
                    f"{type(exc).__name__}: {exc}",
                    False,
                    attempt,
                    operation,
                    dict(metadata),
                )
            if last.returncode == 0:
                return last
            if attempt > retries or self.classify_failure(last) != "transient":
                raise RemoteCommandError(last)
            time.sleep(min(2 ** (attempt - 1), 5))
        raise RemoteCommandError(last)


def resolve_remote_io_config(config=None, cli=None):
    config = config or {}
    cli = cli or {}
    resolved = {}
    for key, default in DEFAULT_REMOTE_IO_CONFIG.items():
        if cli.get(key) is not None:
            value = cli[key]
        elif config.get(key) is not None:
            value = config[key]
        else:
            value = default
        resolved[key] = value
    _validate_remote_io_config(resolved)
    return resolved


def _validate_remote_io_config(config):
    if config["inputAccessMode"] not in INPUT_ACCESS_MODES:
        raise ValueError(f"Unsupported inputAccessMode {config['inputAccessMode']}")
    if config["stageInCleanup"] not in STAGE_IN_CLEANUP_POLICIES:
        raise ValueError(f"Unsupported stageInCleanup {config['stageInCleanup']}")
    if config["existingOutputPolicy"] not in EXISTING_OUTPUT_POLICIES:
        raise ValueError(
            f"Unsupported existingOutputPolicy {config['existingOutputPolicy']}"
        )


def normalize_endpoint(endpoint):
    if endpoint is None:
        return None
    endpoint = endpoint.strip()
    while endpoint.endswith("/"):
        endpoint = endpoint[:-1]
    return endpoint


def build_remote_uri(endpoint, logical_path):
    endpoint = normalize_endpoint(endpoint)
    if endpoint is None:
        raise RemoteIOError("xrdWriteEndpoint is required for logical remote output")
    logical_path = str(logical_path)
    if not is_logical_cms_path(logical_path):
        raise RemoteIOError(f"Remote logical output must start with /store/: {logical_path}")
    return f"{endpoint}/{logical_path}"


def is_root_url(path):
    return str(path).startswith("root://")


def is_mounted_eos_path(path):
    return str(path).startswith("/eos/cms/store/")


def is_logical_cms_path(path):
    return str(path).startswith("/store/")


def mounted_eos_to_lfn(path):
    path = str(path)
    if is_mounted_eos_path(path):
        return path[len("/eos/cms") :]
    return path


def resolve_input_uri(path, settings):
    mode = settings["inputAccessMode"]
    path = str(path)
    if mode == "as-configured":
        return path
    if is_root_url(path):
        return path
    lfn = mounted_eos_to_lfn(path)
    if is_logical_cms_path(lfn):
        endpoint = normalize_endpoint(settings.get("xrdReadEndpoint"))
        if endpoint is None:
            raise RemoteIOError(
                "xrdReadEndpoint is required to map logical or mounted CMS paths"
            )
        return f"{endpoint}/{lfn}"
    return path


def _safe_stage_name(source):
    basename = os.path.basename(str(source).split("?")[0]) or "input.root"
    digest = hashlib.sha256(str(source).encode("utf-8")).hexdigest()[:16]
    return f"{digest}_{basename}"


class RootValidator:
    def validate(self, path, tree_name="Events"):
        try:
            import ROOT
        except ImportError:
            return True
        fobj = ROOT.TFile.Open(path)
        try:
            if not fobj or fobj.IsZombie():
                raise RemoteIOError(f"ROOT failed to open staged file {path}")
            tree = fobj.Get(tree_name)
            if not tree:
                raise RemoteIOError(f"Tree {tree_name} not found in staged file {path}")
        finally:
            if fobj:
                fobj.Close()
        return True


class StageInManager:
    def __init__(self, settings, runner=None, validator=None):
        self.settings = settings
        self.runner = runner or ExternalCommandRunner(
            settings["remoteCommandTimeout"], settings["remoteTransferRetries"]
        )
        self.validator = validator or RootValidator()
        self.scratch = None
        self.mapping = {}

    def prepare_files(self, files, tree_name="Events"):
        if self.settings["inputAccessMode"] != "stage-in":
            return [resolve_input_uri(path, self.settings) for path in files]
        if self.scratch is None:
            root = (
                self.settings.get("stageInScratch")
                or os.environ.get("_CONDOR_SCRATCH_DIR")
                or os.environ.get("TMPDIR", "/tmp")
            )
            self.scratch = Path(root) / f"mkShapesRDF_stagein_{uuid.uuid4().hex}"
            self.scratch.mkdir(parents=True, exist_ok=False)
        staged = []
        for source in files:
            try:
                uri = resolve_input_uri(source, self.settings)
                final = self.scratch / _safe_stage_name(uri)
                temp = final.with_suffix(final.suffix + f".part.{uuid.uuid4().hex}")
                if is_root_url(uri):
                    self.runner.run(
                        ["xrdcp", "--nopbar", uri, str(temp)],
                        "stage-in",
                        {"source": uri, "destination": str(temp)},
                    )
                else:
                    shutil.copy2(uri, temp)
                if not temp.exists():
                    raise RemoteIOError(f"Stage-in did not create {temp}")
                expected_size = None
                if is_root_url(uri):
                    expected_size = RemoteFileOps(self.settings, self.runner).stat(uri).get(
                        "size"
                    )
                elif os.path.exists(uri):
                    expected_size = os.path.getsize(uri)
                if expected_size is not None and expected_size != temp.stat().st_size:
                    raise RemoteIOError(f"Stage-in size mismatch for {uri}")
                self.validator.validate(str(temp), tree_name)
                os.replace(temp, final)
                self.mapping[str(source)] = str(final)
                staged.append(str(final))
                print(f"Stage-in mapping: {source} -> {final}")
            except Exception as exc:
                scratch = str(self.scratch) if self.scratch else "<not-created>"
                try:
                    self.cleanup(success=False)
                except Exception as cleanup_exc:
                    raise RemoteIOError(
                        f"Stage-in failed for source '{source}' in task scratch "
                        f"'{scratch}': {exc}; failure cleanup also failed: {cleanup_exc}"
                    ) from exc
                raise RemoteIOError(
                    f"Stage-in failed for source '{source}' in task scratch "
                    f"'{scratch}': {exc}"
                ) from exc
        return staged

    def cleanup(self, success=True):
        policy = self.settings["stageInCleanup"]
        preserve_failure = self.settings["preserveStageInOnFailure"]
        if success:
            should_cleanup = policy in ("always", "on-success")
        else:
            should_cleanup = policy == "always" or (
                policy == "on-success" and not preserve_failure
            )
        if should_cleanup and self.scratch and self.scratch.exists():
            last_error = None
            for attempt in range(3):
                try:
                    shutil.rmtree(self.scratch)
                    return
                except FileNotFoundError:
                    return
                except OSError as exc:
                    last_error = exc
                    time.sleep(min(0.2 * (attempt + 1), 1.0))
            if self.scratch.exists():
                raise last_error


class RemoteFileOps:
    def __init__(self, settings, runner=None):
        self.settings = settings
        self.runner = runner or ExternalCommandRunner(
            settings["remoteCommandTimeout"], settings["remoteTransferRetries"]
        )

    def exists(self, uri):
        try:
            self.stat(uri)
            return True
        except RemoteObjectNotFound:
            return False

    def stat(self, uri):
        if is_root_url(uri):
            endpoint, path = split_root_uri(uri)
            try:
                result = self.runner.run(
                    ["xrdfs", endpoint, "stat", path], "remote-stat"
                )
            except RemoteCommandError as exc:
                detail = f"{exc.result.stdout}\n{exc.result.stderr}".lower()
                if "no such file" in detail or "not found" in detail:
                    raise RemoteObjectNotFound(f"Remote object does not exist: {uri}") from exc
                raise
            return parse_xrdfs_stat(result.stdout)
        if not os.path.exists(uri):
            raise RemoteObjectNotFound(f"{uri} does not exist")
        return {"size": os.path.getsize(uri)}

    def checksum(self, uri):
        return None

    def copy(self, source, destination):
        if is_root_url(source) or is_root_url(destination):
            self.runner.run(
                ["xrdcp", "--nopbar", source, destination],
                "remote-copy",
                {"source": source, "destination": destination},
            )
        else:
            shutil.copy2(source, destination)

    def remove(self, uri):
        if is_root_url(uri):
            endpoint, path = split_root_uri(uri)
            self.runner.run(["xrdfs", endpoint, "rm", path], "remote-remove")
        else:
            os.remove(uri)

    def move(self, source, destination):
        if is_root_url(source) or is_root_url(destination):
            endpoint, source_path = split_root_uri(source)
            dest_endpoint, dest_path = split_root_uri(destination)
            if endpoint != dest_endpoint:
                raise RemoteIOError("Remote move requires common endpoint")
            self.runner.run(
                ["xrdfs", endpoint, "mv", source_path, dest_path], "remote-move"
            )
        else:
            os.replace(source, destination)


def split_root_uri(uri):
    rest = uri[len("root://") :]
    host, _, path = rest.partition("/")
    return "root://" + host, "/" + path.lstrip("/")


def parse_xrdfs_stat(stdout):
    data = {}
    for line in stdout.splitlines():
        parts = line.strip().split()
        if len(parts) >= 2 and parts[0].lower().startswith("size"):
            data["size"] = int(parts[-1])
    return data


def stage_out(local_file, destination, settings, ops=None, ledger=None):
    policy = settings["existingOutputPolicy"]
    ops = ops or RemoteFileOps(settings)
    ledger = ledger if ledger is not None else []
    local_size = os.path.getsize(local_file)
    exists = ops.exists(destination)
    if exists:
        dest_stat = ops.stat(destination)
        identical = dest_stat.get("size") == local_size
        if policy == "fail":
            raise RemoteIOError(f"Destination exists: {destination}")
        if policy == "skip-if-verified-identical":
            if identical:
                ledger.append({"action": "skip-identical", "destination": destination})
                return destination
            raise RemoteIOError(f"Destination exists and differs: {destination}")
    temp = f"{destination}.tmp.{uuid.uuid4().hex}"
    backup = f"{destination}.bak.{uuid.uuid4().hex}"
    try:
        ops.copy(local_file, temp)
        temp_stat = ops.stat(temp)
        if temp_stat.get("size") != local_size:
            raise RemoteIOError(f"Stage-out size mismatch for {temp}")
        if exists and policy == "replace":
            ops.move(destination, backup)
            ledger.append({"action": "backup", "source": destination, "backup": backup})
        ops.move(temp, destination)
        final_stat = ops.stat(destination)
        if final_stat.get("size") != local_size:
            raise RemoteIOError(f"Final stage-out size mismatch for {destination}")
        if exists and policy == "replace":
            ops.remove(backup)
            ledger.append({"action": "remove-backup", "backup": backup})
        ledger.append({"action": "stage-out", "destination": destination})
        return destination
    except Exception:
        if exists and policy == "replace" and ops.exists(backup):
            if ops.exists(destination):
                ops.remove(destination)
            ops.move(backup, destination)
            ledger.append({"action": "rollback", "destination": destination})
        if ops.exists(temp):
            ops.remove(temp)
        raise
