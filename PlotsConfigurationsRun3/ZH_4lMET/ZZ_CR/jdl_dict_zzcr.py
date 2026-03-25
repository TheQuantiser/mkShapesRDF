import os
import shlex
import shutil
import subprocess


eos_output_path = os.path.abspath(self.outputPath).rstrip("/")
if eos_output_path.startswith("/eos/home-"):
    # /eos/home-x/<user> is a filesystem-level path. xrootd authorization for
    # user areas is handled through /eos/user/x/<user>.
    _tail = eos_output_path[len("/eos/home-") :]
    _initial, _rest = _tail.split("/", 1)
    eos_output_path = f"/eos/user/{_initial}/{_rest}"
if not eos_output_path.startswith("/eos/"):
    raise RuntimeError(
        "ZZ_CR x509 JDL is intended for EOS output paths. "
        f"Found outputPath={self.outputPath}"
    )

# Select xrootd endpoint and target namespace path.
xrd_endpoint = "root://eosuser.cern.ch"
xrd_target_path = eos_output_path
if eos_output_path.startswith("/eos/cms/store/"):
    # Use the EOS CMS MGM endpoint by default for write operations.
    # Global redirectors are primarily read-oriented and can cause unstable
    # destination behavior for writes.
    redirector = str(self.d.get("xrdRedirector", "eoscms.cern.ch")).strip()
    redirector = redirector.replace("root://", "").strip("/")
    if redirector == "":
        redirector = "eoscms.cern.ch"
    xrd_endpoint = f"root://{redirector}"
    xrd_target_path = eos_output_path[len("/eos/cms") :]

# Ensure destination directory exists before submission.
target_dir = xrd_target_path.rstrip("/")
print(f"[ZZCR-JDL] xrdfs mkdir -p endpoint={xrd_endpoint} path={target_dir}")
try:
    subprocess.run(
        ["xrdfs", xrd_endpoint, "mkdir", "-p", target_dir],
        capture_output=True,
        text=True,
        check=True,
    )
except FileNotFoundError as exc:
    raise RuntimeError(
        "`xrdfs` was not found in PATH. "
        "Load ROOT/XRootD tools before submitting."
    ) from exc
except subprocess.CalledProcessError as exc:
    stderr = (exc.stderr or "").strip()
    # Some EOS/XRootD endpoints report a non-zero exit code even for
    # `mkdir -p` if the directory already exists (e.g. error code 3018).
    if "already exists" not in stderr.lower() and "[3018]" not in stderr:
        raise RuntimeError(
            "Could not create EOS destination directory via xrdfs.\n"
            f"endpoint={xrd_endpoint}\n"
            f"path={target_dir}\n"
            f"stderr={stderr}"
        ) from exc
    print(
        "[ZZCR-JDL] xrdfs mkdir returned an 'already exists' condition; "
        "continuing."
    )

try:
    proxy_check = subprocess.run(
        ["voms-proxy-info", "-exists", "-hours", "1"], capture_output=True, text=True
    )
except FileNotFoundError as exc:
    raise RuntimeError(
        "`voms-proxy-info` was not found in PATH. "
        "Load the grid environment and run `voms-proxy-init --voms cms -valid 192:0`."
    ) from exc

if proxy_check.returncode != 0:
    raise RuntimeError(
        "No valid VOMS proxy found (>=1 hour). "
        "Please run `voms-proxy-init --voms cms -valid 192:0` and submit again."
    )

output_file_trunc = ".".join(self.d["outputFile"].split(".")[:-1])
proxy_path_cmd = subprocess.run(
    ["voms-proxy-info", "-path"], capture_output=True, text=True, check=True
)
proxy_path = proxy_path_cmd.stdout.strip()
if proxy_path == "" or not os.path.exists(proxy_path):
    raise RuntimeError(
        "Could not resolve proxy path from `voms-proxy-info -path`."
    )

# Stage proxy inside the batch folder so Condor can always transfer it reliably.
proxy_staged = os.path.join(self.batchFolder, self.tag, "x509up")
shutil.copy2(proxy_path, proxy_staged)
os.chmod(proxy_staged, 0o600)
proxy_filename = os.path.basename(proxy_staged)

setup_lines = []
startpath = os.environ.get("STARTPATH", "").strip()
if startpath != "" and os.path.exists(startpath):
    with open(startpath) as f:
        setup_lines = [line.rstrip("\n") for line in f.readlines()]

output_file_eos = f"{xrd_endpoint}/{xrd_target_path}/{output_file_trunc}__ALL__" + "${1}.root"
output_file_rel = f"{xrd_target_path}/{output_file_trunc}__ALL__" + "${1}.root"

# 1) Run mkShapes runner.
# 2) Export proxy in the worker sandbox.
# 3) Copy output to EOS using xrdcp.
executable = setup_lines + [
    "#!/bin/bash",
    "set -e",
    "echo \"Running in: $PWD\"",
    "ls -l .",
    f'echo "[ZZCR-JDL] EOS endpoint: {xrd_endpoint}"',
    f'echo "[ZZCR-JDL] EOS target directory: {xrd_target_path}"',
    f"export X509_USER_PROXY={shlex.quote(proxy_filename)}",
    "voms-proxy-info -all -file \"$X509_USER_PROXY\"",
    "PYTHON_BIN=$(command -v python3 || command -v python || true)",
    'if [ -z "$PYTHON_BIN" ]; then echo "No python interpreter found in PATH" >&2; exit 127; fi',
    f'time "$PYTHON_BIN" {shlex.quote(os.path.basename(self.runnerPath))}',
    'if [ ! -f output.root ]; then echo "[ZZCR-JDL] ERROR: output.root not found before transfer" >&2; exit 66; fi',
    'echo "[ZZCR-JDL] output.root size:"',
    "ls -lh output.root",
    f'echo "[ZZCR-JDL] xrdcp destination: {output_file_eos}"',
    "set +e",
    "xrdcp_status=1",
    "for attempt in 1 2 3; do",
    '  echo "[ZZCR-JDL] xrdcp attempt ${attempt}/3"',
    f"  xrdcp -f -v output.root {output_file_eos}",
    "  xrdcp_status=$?",
    "  if [ ${xrdcp_status} -eq 0 ]; then",
    "    break",
    "  fi",
    "  if [ ${attempt} -eq 1 ]; then",
    '    echo "[ZZCR-JDL] first xrdcp failed, removing stale destination and retrying..."',
    f"    xrdfs {xrd_endpoint} rm {output_file_rel} || true",
    "  fi",
    '  echo "[ZZCR-JDL] transient xrdcp failure (status=${xrdcp_status}), sleeping before retry..."',
    "  sleep 20",
    "done",
    "set -e",
    'if [ ${xrdcp_status} -ne 0 ]; then echo "[ZZCR-JDL] ERROR: xrdcp failed after retries" >&2; exit ${xrdcp_status}; fi',
    'echo "[ZZCR-JDL] xrdcp finished successfully"',
    "rm -f output.root script.py",
]

jdl_dict = {
    "transfer_input_files": (
        f"$(Folder)/script.py, {self.headersPath}, {self.runnerPath}, {proxy_staged}"
    ),
    "when_to_transfer_output": "ON_EXIT",
    "transfer_output_files": '""',
}

# Keep default condor_submit invocation untouched.
condor_config = []
