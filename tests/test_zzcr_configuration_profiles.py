import os
import runpy
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
ZZCR_DIR = REPO_ROOT / "PlotsConfigurationsRun3" / "ZH_4lMET" / "ZZ_CR"
CONFIGURATION = ZZCR_DIR / "configuration.py"

ZZCR_ENV_KEYS = (
    "ZZCR_EXECUTION_PROFILE",
    "ZZCR_SITE_PRESET",
    "ZZCR_OUTPUT_MODE",
    "ZZCR_INPUT_ACCESS_MODE",
    "ZZCR_XRD_READ_ENDPOINT",
    "ZZCR_XRD_DISCOVERY_ENDPOINT",
    "ZZCR_XRD_WRITE_ENDPOINT",
    "ZZCR_STAGE_IN_SCRATCH",
    "ZZCR_STAGE_IN_CLEANUP",
    "ZZCR_PRESERVE_STAGE_IN_ON_FAILURE",
    "ZZCR_EXISTING_OUTPUT_POLICY",
    "ZZCR_REMOTE_COMMAND_TIMEOUT",
    "ZZCR_REMOTE_TRANSFER_RETRIES",
    "ZZCR_CONDOR_RUNTIME_PACKAGE",
    "ZZCR_CONDOR_RUNTIME_PACKAGE_NAME",
    "ZZCR_CONDOR_RUNTIME_SETUP",
    "ZZCR_CONDOR_RUNTIME_INCLUDES",
    "ZZCR_USE_X509_PROXY",
    "ZZCR_CONFIG_INCLUDE_BASE",
    "ZZCR_TEST_CAMPAIGN",
    "ZZCR_TEST_OUTPUT_LFN",
    "ZZCR_PRODUCTION_OUTPUT_LFN",
    "ZZCR_EOS_USER",
)


def _load_profile(
    monkeypatch, tmp_path, profile, extra_env=None, execution_mode=None
):
    for key in ZZCR_ENV_KEYS:
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("USER", "profiletester")
    monkeypatch.setenv("ZZCR_EXECUTION_PROFILE", profile)
    for key, value in (extra_env or {}).items():
        monkeypatch.setenv(key, value)
    monkeypatch.chdir(tmp_path)
    init_globals = {"ZZCR_CONFIG_DIR": str(ZZCR_DIR)}
    if execution_mode is not None:
        init_globals["mkShapesRDFExecutionMode"] = execution_mode
    return runpy.run_path(str(CONFIGURATION), init_globals=init_globals)


@pytest.mark.parametrize(
    "profile,input_mode,output_mode,packaged,proxy,include_base",
    [
        ("local", "as-configured", "local", False, False, "checkout"),
        ("local_xrootd", "xrootd", "local", False, False, "checkout"),
        ("local_stagein", "stage-in", "local", False, False, "checkout"),
        ("shared_xrootd_local", "xrootd", "local", False, True, "checkout"),
        ("shared_xrootd_eos", "xrootd", "test-remote", False, True, "checkout"),
        ("packaged_xrootd_local", "xrootd", "local", True, True, "runtime"),
        ("packaged_xrootd_eos", "xrootd", "test-remote", True, True, "runtime"),
        ("packaged_stagein_local", "stage-in", "local", True, True, "runtime"),
        ("packaged_stagein_eos", "stage-in", "test-remote", True, True, "runtime"),
    ],
)
def test_zzcr_execution_profiles_resolve_core_contract(
    monkeypatch,
    tmp_path,
    profile,
    input_mode,
    output_mode,
    packaged,
    proxy,
    include_base,
):
    data = _load_profile(monkeypatch, tmp_path, profile)

    assert data["ZZCR_SELECTED_EXECUTION_PROFILE"] == profile
    assert data["ZZCR_OUTPUT_MODE"] == output_mode
    assert data["remoteIO"]["inputAccessMode"] == input_mode
    assert data["remoteIO"]["xrdReadEndpoint"] == "root://eoscms.cern.ch"
    assert data["remoteIO"]["xrdDiscoveryEndpoint"] == "root://eoscms.cern.ch"
    assert data["remoteIO"]["xrdWriteEndpoint"] == "root://cmseos.fnal.gov"
    assert data["remoteIO"]["existingOutputPolicy"] == "fail"
    assert data["condorRuntimePackage"] is packaged
    assert data["useX509Proxy"] is proxy
    assert "condorRuntimeIncludes" in data["varsToKeep"]

    if packaged:
        assert data["condorRuntimeSetup"]
        assert "LCG_109" in data["condorRuntimeSetup"][0]
    else:
        assert data["condorRuntimeSetup"] == []

    if include_base == "runtime":
        assert data["ZZCR_CONFIG_INCLUDE_BASE"] == "runtime"
    else:
        assert data["ZZCR_CONFIG_INCLUDE_BASE"] == str(REPO_ROOT)

    if output_mode == "local":
        assert not data["outputFolder"].startswith("root://")
    else:
        assert data["outputFolder"].startswith("root://cmseos.fnal.gov//store/user/")


def test_zzcr_environment_overrides_profile_values(monkeypatch, tmp_path):
    data = _load_profile(
        monkeypatch,
        tmp_path,
        "packaged_xrootd_eos",
        {
            "ZZCR_INPUT_ACCESS_MODE": "stage-in",
            "ZZCR_OUTPUT_MODE": "local",
            "ZZCR_CONDOR_RUNTIME_PACKAGE": "0",
            "ZZCR_USE_X509_PROXY": "0",
            "ZZCR_CONFIG_INCLUDE_BASE": "/custom/include/base",
            "ZZCR_XRD_READ_ENDPOINT": "root://read.example",
            "ZZCR_XRD_DISCOVERY_ENDPOINT": "root://discover.example",
            "ZZCR_XRD_WRITE_ENDPOINT": "root://write.example",
            "ZZCR_EXISTING_OUTPUT_POLICY": "skip-if-verified-identical",
            "ZZCR_CONDOR_RUNTIME_SETUP": "source /cvmfs/example/setup.sh;;echo ready",
            "ZZCR_CONDOR_RUNTIME_INCLUDES": "extra.json;;calibrations",
        },
    )

    assert data["ZZCR_OUTPUT_MODE"] == "local"
    assert data["remoteIO"]["inputAccessMode"] == "stage-in"
    assert data["remoteIO"]["xrdReadEndpoint"] == "root://read.example"
    assert data["remoteIO"]["xrdDiscoveryEndpoint"] == "root://discover.example"
    assert data["remoteIO"]["xrdWriteEndpoint"] == "root://write.example"
    assert data["remoteIO"]["existingOutputPolicy"] == "skip-if-verified-identical"
    assert data["condorRuntimePackage"] is False
    assert data["useX509Proxy"] is False
    assert data["ZZCR_CONFIG_INCLUDE_BASE"] == "/custom/include/base"
    assert data["condorRuntimeSetup"] == [
        "source /cvmfs/example/setup.sh",
        "echo ready",
    ]
    assert data["condorRuntimeIncludes"] == ["extra.json", "calibrations"]


def test_zzcr_remote_output_forces_proxy_even_if_disabled(monkeypatch, tmp_path):
    data = _load_profile(
        monkeypatch,
        tmp_path,
        "shared_xrootd_eos",
        {"ZZCR_USE_X509_PROXY": "0"},
    )

    assert data["ZZCR_OUTPUT_MODE"] == "test-remote"
    assert data["useX509Proxy"] is True


def test_zzcr_invalid_profile_fails_clearly(monkeypatch, tmp_path):
    with pytest.raises(ValueError, match="Unsupported ZZCR_EXECUTION_PROFILE"):
        _load_profile(monkeypatch, tmp_path, "not_a_profile")


def test_packaged_profile_rejects_local_execution_before_file_discovery(
    monkeypatch, tmp_path
):
    with pytest.raises(
        RuntimeError,
        match=r"packaged_xrootd_eos_production.*batch-only.*local_xrootd",
    ):
        _load_profile(
            monkeypatch,
            tmp_path,
            "packaged_xrootd_eos_production",
            execution_mode="local",
        )


def test_packaged_profile_accepts_batch_and_local_profile_accepts_local(
    monkeypatch, tmp_path
):
    packaged = _load_profile(
        monkeypatch,
        tmp_path,
        "packaged_xrootd_local",
        execution_mode="batch",
    )
    assert packaged["requiredExecutionMode"] == "batch"

    local = _load_profile(
        monkeypatch,
        tmp_path,
        "local_xrootd",
        execution_mode="local",
    )
    assert local["requiredExecutionMode"] is None
