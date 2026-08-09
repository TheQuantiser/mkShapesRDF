from pathlib import Path
import subprocess


CONFIG_DIR = Path(__file__).resolve().parents[1]
WRAPPER = CONFIG_DIR / "fnal_lpc_packaged_env.sh"


def _source_wrapper(prefix=""):
    command = (
        f"{prefix} source {WRAPPER}; "
        "printf '%s|%s|%s|%s' \"$EXECUTION_PROFILE\" \"$INPUT_ACCESS_MODE\" "
        "\"$XRD_READ_ENDPOINT\" \"$XRD_WRITE_ENDPOINT\""
    )
    return subprocess.run(
        ["bash", "-c", command],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    ).stdout


def test_fnal_wrapper_defaults_to_direct_xrootd():
    assert _source_wrapper() == (
        "packaged_fnal_xrootd_eos_production|xrootd|"
        "root://eoscms.cern.ch|root://cmseos.fnal.gov"
    )


def test_fnal_wrapper_preserves_explicit_stage_in_option():
    assert _source_wrapper(
        "export EXECUTION_PROFILE=packaged_fnal_stagein_eos_production "
        "INPUT_ACCESS_MODE=stage-in;"
    ).startswith("packaged_fnal_stagein_eos_production|stage-in|")
