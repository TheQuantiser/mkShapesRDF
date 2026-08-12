"""Small, site-only runtime presets shared by ZH4l leaves."""

import os


DEFAULT_XRD_ENDPOINT = "root://eoscms.cern.ch"


def remote_io_from_env():
    read = os.environ.get("XRD_READ_ENDPOINT", DEFAULT_XRD_ENDPOINT).rstrip("/")
    discovery = os.environ.get("XRD_DISCOVERY_ENDPOINT", read).rstrip("/")
    if not read.startswith("root://") or not discovery.startswith("root://"):
        raise ValueError("XRD read/discovery endpoints must be root:// URLs")
    return {
        "inputAccessMode": os.environ.get("INPUT_ACCESS_MODE", "xrootd"),
        "xrdReadEndpoint": read,
        "xrdDiscoveryEndpoint": discovery,
        "xrdWriteEndpoint": os.environ.get("XRD_WRITE_ENDPOINT"),
        "stageInScratch": os.environ.get("STAGE_IN_SCRATCH") or None,
        "stageInCleanup": os.environ.get("STAGE_IN_CLEANUP", "on-success"),
        "preserveStageInOnFailure": True,
        "existingOutputPolicy": os.environ.get("EXISTING_OUTPUT_POLICY", "fail"),
        "remoteCommandTimeout": int(os.environ.get("REMOTE_COMMAND_TIMEOUT", "120")),
        "remoteTransferRetries": int(os.environ.get("REMOTE_TRANSFER_RETRIES", "2")),
    }


def batch_runtime_from_env():
    enabled = os.environ.get("CONDOR_RUNTIME_PACKAGE", "0").strip().lower()
    if enabled not in {"0", "1", "false", "true", "no", "yes"}:
        raise ValueError("CONDOR_RUNTIME_PACKAGE must be boolean")
    package = enabled in {"1", "true", "yes"}
    return {
        "condorRuntimePackage": package,
        "condorRuntimePackageName": os.environ.get(
            "CONDOR_RUNTIME_PACKAGE_NAME", "mkshapesrdf_runtime.tgz"
        ),
        "condorRuntimeIncludes": [],
        "condorRuntimeSetup": [
            "source /cvmfs/sft.cern.ch/lcg/views/LCG_109/x86_64-el9-gcc13-opt/setup.sh"
        ] if package else [],
        "useX509Proxy": True,
        "mountEOS": [],
        "useEOSUserOutput": False,
    }
