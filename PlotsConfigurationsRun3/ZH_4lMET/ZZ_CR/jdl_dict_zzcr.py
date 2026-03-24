import os
import shlex
import shutil
import subprocess


eos_output_path = os.path.realpath(self.outputPath).rstrip("/")
if not eos_output_path.startswith("/eos/"):
    raise RuntimeError(
        "ZZ_CR x509 JDL is intended for EOS output paths. "
        f"Found outputPath={self.outputPath}"
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

# 1) Run mkShapes runner.
# 2) Export proxy in the worker sandbox.
# 3) Copy output to EOS using xrdcp.
executable = setup_lines + [
    "#!/bin/bash",
    "set -e",
    "echo \"Running in: $PWD\"",
    "ls -l .",
    f"export X509_USER_PROXY={shlex.quote(proxy_filename)}",
    "voms-proxy-info -all -file \"$X509_USER_PROXY\"",
    "PYTHON_BIN=$(command -v python3 || command -v python || true)",
    'if [ -z "$PYTHON_BIN" ]; then echo "No python interpreter found in PATH" >&2; exit 127; fi',
    f'time "$PYTHON_BIN" {shlex.quote(os.path.basename(self.runnerPath))}',
    (
        "xrdcp -f output.root "
        f"root://eosuser.cern.ch/{eos_output_path}/"
        + f"{output_file_trunc}__ALL__"
        + "${1}.root"
    ),
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
