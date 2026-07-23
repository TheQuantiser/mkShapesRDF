import os
import runpy
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
ZZCR_DIR = REPO_ROOT / "PlotsConfigurationsRun3" / "ZH_4lMET" / "ZZ_CR"
CONFIGURATION = ZZCR_DIR / "configuration.py"
SELECTION_CONFIG = ZZCR_DIR / "zzcr_selection_config.py"
ALIASES = ZZCR_DIR / "aliases.py"
SUPPORTED_ZZCR_YEARS = ("2022", "2022EE", "2023", "2023BPix", "2024")

ZZCR_ENV_KEYS = (
    "ZZCR_YEAR",
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
    "ZZCR_OUTPUT_LEAF",
    "ZZCR_CONDOR_RUNTIME_PACKAGE",
    "ZZCR_CONDOR_RUNTIME_PACKAGE_NAME",
    "ZZCR_CONDOR_RUNTIME_SETUP",
    "ZZCR_CONDOR_RUNTIME_INCLUDES",
    "ZZCR_USE_X509_PROXY",
    "ZZCR_CONFIG_INCLUDE_BASE",
    "ZZCR_TEST_CAMPAIGN",
    "ZZCR_PRODUCTION_CAMPAIGN",
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

    assert data["ZZCR_OUTPUT_LEAF"] == data["tag"]
    if output_mode == "local":
        assert not data["outputFolder"].startswith("root://")
        assert data["outputFolder"] == os.path.join(
            "jobs", data["tag"], data["tag"]
        )
    else:
        assert data["outputFolder"].startswith("root://cmseos.fnal.gov//store/user/")
        assert data["outputFolder"].endswith(f"/{data['tag']}")
        assert "/rootFile" not in data["outputFolder"]


@pytest.mark.parametrize(
    "profile,campaign",
    [
        ("shared_xrootd_eos_production", "lxplus"),
        ("packaged_xrootd_eos_production", "fnal_lpc_packaged"),
        ("packaged_stagein_eos_production", "fnal_lpc_packaged_stagein"),
    ],
)
def test_zzcr_production_remote_defaults_keep_campaign_and_tag_leaf(
    monkeypatch, tmp_path, profile, campaign
):
    data = _load_profile(monkeypatch, tmp_path, profile)

    assert data["ZZCR_OUTPUT_MODE"] == "production-remote"
    assert data["ZZCR_PRODUCTION_CAMPAIGN"] == campaign
    assert data["productionOutputLFN"].endswith(f"/{campaign}/{data['tag']}")
    assert data["outputFolder"].endswith(f"/{campaign}/{data['tag']}")
    assert "/rootFile" not in data["productionOutputLFN"]


def test_zzcr_production_campaign_override_keeps_tag_leaf(monkeypatch, tmp_path):
    data = _load_profile(
        monkeypatch,
        tmp_path,
        "shared_xrootd_eos_production",
        {"ZZCR_PRODUCTION_CAMPAIGN": "custom_campaign"},
    )

    assert data["ZZCR_PRODUCTION_CAMPAIGN"] == "custom_campaign"
    assert data["productionOutputLFN"].endswith(
        f"/custom_campaign/{data['tag']}"
    )


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


def _load_selection_config(monkeypatch, year):
    monkeypatch.setenv("ZZCR_YEAR", year)
    return runpy.run_path(
        str(SELECTION_CONFIG), init_globals={"ZZCR_CONFIG_DIR": str(ZZCR_DIR)}
    )


@pytest.mark.parametrize("year", SUPPORTED_ZZCR_YEARS)
def test_zzcr_trigger_object_schema_defaults_to_nanoaod_v15(monkeypatch, year):
    data = _load_selection_config(monkeypatch, year)

    assert data["DEFAULT_TRIGOBJ_NANOAOD_VERSION"] == 15
    assert data["trigobj_nanoaod_version"]() == 15
    assert data["trigobj_nanoaod_version"]({"l2tight_era": "Full2022v12"}) == 15


def test_zzcr_rejects_legacy_trigger_object_schema_override(monkeypatch):
    data = _load_selection_config(monkeypatch, "2024")

    with pytest.raises(ValueError, match="assumes NanoAODv15"):
        data["trigobj_nanoaod_version"]({"trigobj_nanoaod_version": 12})


@pytest.mark.parametrize("year", SUPPORTED_ZZCR_YEARS)
def test_zzcr_trigger_object_aliases_use_v15_bits(monkeypatch, year):
    monkeypatch.setenv("ZZCR_YEAR", year)
    data = runpy.run_path(
        str(ALIASES),
        init_globals={"ZZCR_CONFIG_DIR": str(ZZCR_DIR), "samples": {}},
    )
    aliases = data["aliases"]

    assert data["ZZCR_TRIGOBJ_NANOAOD_VERSION"] == 15
    assert ", 4)" in aliases["lZ1_trigObj_bit_ele_DoubleEleLeg1"]["expr"]
    assert ", 5)" in aliases["lZ1_trigObj_bit_ele_DoubleEleLeg2"]["expr"]
    assert ", 6)" in aliases["lZ1_trigObj_bit_ele_EleMu"]["expr"]
    assert ", 18)" in aliases["lZ1_trigObj_bit_ele_Ele30WPTight"]["expr"]
    assert (
        aliases["lZ1_trigObj_match_SingleEle"]["expr"]
        == "lZ1_trigObj_bit_ele_Ele30WPTight"
    )
    assert aliases["lZ1_trigObj_bits4l"]["expr"].endswith(", 15)")
