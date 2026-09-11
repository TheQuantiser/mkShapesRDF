"""Small, site-only runtime presets shared by ZH4l leaves."""

import os
from pathlib import Path


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
        "condorRuntimeIncludes": [str(Path(__file__).resolve().parent)],
        "zh4lCommonPath": str(Path(__file__).resolve().parent),
        "condorRuntimeSetup": (
            [
                "source /cvmfs/sft.cern.ch/lcg/views/LCG_109/x86_64-el9-gcc13-opt/setup.sh"
            ]
            if package
            else []
        ),
        "useX509Proxy": _boolean("USE_X509_PROXY", True),
        "mountEOS": [],
        "useEOSUserOutput": False,
    }


def _boolean(name, default):
    value = os.environ.get(name, str(int(default))).strip().lower()
    if value not in {"0", "1", "false", "true", "no", "yes", "off", "on"}:
        raise ValueError(f"{name} must be boolean")
    return value in {"1", "true", "yes", "on"}


def common_import_statement(common_dir):
    """Import a relocated common package from an explicitly serialized path."""
    directory = str(Path(common_dir).resolve())
    return (
        "import importlib.util, sys; "
        f"_zh4l_spec = importlib.util.spec_from_file_location('common', {directory + '/__init__.py'!r}, submodule_search_locations=[{directory!r}]); "
        "_zh4l_module = sys.modules.get('common'); "
        "_zh4l_module = _zh4l_module if _zh4l_module is not None else importlib.util.module_from_spec(_zh4l_spec); "
        "_zh4l_new = 'common' not in sys.modules; sys.modules['common'] = _zh4l_module; "
        "_zh4l_spec.loader.exec_module(_zh4l_module) if _zh4l_new else None; "
    )
