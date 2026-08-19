"""Configuration entry point for the declarative DY run-stability analysis."""

import os
import getpass
import hashlib
from datetime import datetime, timezone

from run_stability_production import (
    DEFAULT_RUN_STABILITY_PRODUCTION_PROFILE,
    SELECTION_PROFILES,
    configured_category_names,
    run_stability_production_profile,
)


def _early_env_bool(name, default=False):
    value = os.environ.get(name)
    if value is None:
        return bool(default)
    normalized = value.strip().lower()
    if normalized in ("1", "true", "yes", "on"):
        return True
    if normalized in ("0", "false", "no", "off"):
        return False
    raise ValueError(f"{name} must be a boolean 0/1 value; received {value!r}")


def _resolve_config_dir():
    candidates = [
        globals().get("CONFIG_DIR"),
        globals().get("folder"),
        os.getcwd(),
        os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else None,
    ]
    for cand in candidates:
        if not cand:
            continue
        cand_abs = os.path.abspath(cand)
        if os.path.exists(os.path.join(cand_abs, "year_config.py")):
            return cand_abs
    # Fallback to cwd if no candidate contains year_config.py
    return os.path.abspath(os.getcwd())


CONFIG_DIR = _resolve_config_dir()

# This pure loader supplies only the early era luminosity needed by the core
# configuration object. The shared-global execution later materializes
# year_config.py exactly once for all analysis consumers.
from year_config import load_selected_year as _load_selected_year_early  # noqa: E402

# Central year selection used by samples, aliases, variables, and nuisances.
# Keep this in sync with keys available in year_config.json.
YEAR = os.environ.get("YEAR", "2024")
os.environ["YEAR"] = YEAR
_, _selected_year, _ = _load_selected_year_early()

RUN_STABILITY_PRODUCTION_PROFILE = (
    str(
        os.environ.get(
            "RUN_STABILITY_PRODUCTION_PROFILE",
            DEFAULT_RUN_STABILITY_PRODUCTION_PROFILE,
        )
    )
    .strip()
    .lower()
)
SELECTED_RUN_STABILITY_PRODUCTION_PROFILE = run_stability_production_profile(
    RUN_STABILITY_PRODUCTION_PROFILE
)
os.environ["RUN_STABILITY_PRODUCTION_PROFILE"] = RUN_STABILITY_PRODUCTION_PROFILE

ANALYSIS_PASS = (
    str(
        os.environ.get(
            "ANALYSIS_PASS",
            SELECTED_RUN_STABILITY_PRODUCTION_PROFILE["analysis_pass"],
        )
    )
    .strip()
    .upper()
)
if ANALYSIS_PASS != SELECTED_RUN_STABILITY_PRODUCTION_PROFILE["analysis_pass"]:
    raise ValueError(
        "RunStability is a dedicated stability leaf and requires "
        "ANALYSIS_PASS=RUN_STABILITY; "
        f"received {ANALYSIS_PASS!r}"
    )
os.environ["ANALYSIS_PASS"] = ANALYSIS_PASS

RUN_STABILITY_REGION = (
    str(
        os.environ.get(
            "RUN_STABILITY_REGION",
            SELECTED_RUN_STABILITY_PRODUCTION_PROFILE["region"],
        )
    )
    .strip()
    .upper()
)
if RUN_STABILITY_REGION != SELECTED_RUN_STABILITY_PRODUCTION_PROFILE["region"]:
    raise ValueError(
        "RunStability currently configures only RUN_STABILITY_REGION=DY; "
        f"received {RUN_STABILITY_REGION!r}"
    )
os.environ["RUN_STABILITY_REGION"] = RUN_STABILITY_REGION

SELECTED_RUN_STABILITY_PRODUCTION_PROFILE["categories"] = configured_category_names(
    SELECTED_RUN_STABILITY_PRODUCTION_PROFILE
)
SELECTED_RUN_STABILITY_PRODUCTION_PROFILE["category_selector"] = ",".join(
    SELECTED_RUN_STABILITY_PRODUCTION_PROFILE["categories"]
)

SELECTION_PROFILE = (
    str(
        os.environ.get(
            "SELECTION_PROFILE",
            (SELECTED_RUN_STABILITY_PRODUCTION_PROFILE["selection_profile"]),
        )
    )
    .strip()
    .lower()
)
if not SELECTION_PROFILE:
    raise ValueError("SELECTION_PROFILE cannot be empty")
os.environ["SELECTION_PROFILE"] = SELECTION_PROFILE
RUN_STABILITY_OBSERVABLE_SELECTOR = str(
    os.environ.get(
        "RUN_STABILITY_OBSERVABLES",
        (SELECTED_RUN_STABILITY_PRODUCTION_PROFILE["observable_selector"]),
    )
).strip()
RUN_STABILITY_CATEGORY_SELECTOR = str(
    os.environ.get(
        "RUN_STABILITY_CATEGORIES",
        (SELECTED_RUN_STABILITY_PRODUCTION_PROFILE["category_selector"]),
    )
).strip()
if not RUN_STABILITY_OBSERVABLE_SELECTOR or not RUN_STABILITY_CATEGORY_SELECTOR:
    raise ValueError("Run-stability observable/category selectors cannot be empty")
if (
    RUN_STABILITY_OBSERVABLE_SELECTOR.lower()
    != SELECTED_RUN_STABILITY_PRODUCTION_PROFILE["observable_selector"]
):
    raise ValueError(
        "RunStability requires the exact observable selector declared by "
        "run_stability_profiles.json"
    )
if (
    RUN_STABILITY_CATEGORY_SELECTOR
    != SELECTED_RUN_STABILITY_PRODUCTION_PROFILE["category_selector"]
):
    raise ValueError(
        "RunStability requires the exact category tuple derived from "
        "run_stability_profiles.json and year_config.json"
    )

# PlotsConfigurationsRun3 convention: configuration.py selects either the
# full nuisance source or a separate empty nominal nuisance source.
ENABLE_SYSTEMATICS = _early_env_bool("ENABLE_SYSTEMATICS", False)
os.environ["ENABLE_SYSTEMATICS"] = "1" if ENABLE_SYSTEMATICS else "0"

# RunStability is deliberately histogram-only. Tree snapshots belong in a dedicated
# skim configuration, not in this production and plotting contract.
HISTOGRAMS = True
os.environ["HISTOGRAMS"] = "1"
CATEGORY_PROFILE = os.environ.get("CATEGORY_PROFILE", "standard").strip().lower()
if CATEGORY_PROFILE != "standard":
    raise ValueError(
        "RunStability supports CATEGORY_PROFILE=standard; "
        f"received {CATEGORY_PROFILE!r}"
    )
HISTOGRAM_PROFILE = (
    os.environ.get("HISTOGRAM_PROFILE", os.environ.get("HISTOGRAM_DETAIL", "analysis"))
    .strip()
    .lower()
)
if HISTOGRAM_PROFILE != "analysis":
    raise ValueError(
        "RunStability supports HISTOGRAM_PROFILE=analysis; "
        f"received {HISTOGRAM_PROFILE!r}"
    )
HISTOGRAM_DETAIL = HISTOGRAM_PROFILE
SAMPLE_PROFILE = os.environ.get("SAMPLE_PROFILE", "presentation").strip().lower()
if SAMPLE_PROFILE != "presentation":
    raise ValueError(
        "RunStability supports SAMPLE_PROFILE=presentation; "
        f"received {SAMPLE_PROFILE!r}"
    )
os.environ["CATEGORY_PROFILE"] = CATEGORY_PROFILE
os.environ["HISTOGRAM_PROFILE"] = HISTOGRAM_PROFILE
os.environ["HISTOGRAM_DETAIL"] = HISTOGRAM_DETAIL
os.environ["SAMPLE_PROFILE"] = SAMPLE_PROFILE
OUTPUT_PRODUCT = "HIST"
os.environ["OUTPUT_PRODUCT"] = OUTPUT_PRODUCT

if ENABLE_SYSTEMATICS:
    raise ValueError("RunStability is nominal-only")


_CANONICAL_RUN_STABILITY_IDENTITY = dict(SELECTED_RUN_STABILITY_PRODUCTION_PROFILE)
_CANONICAL_RUN_STABILITY_IDENTITY["category_count"] = len(
    _CANONICAL_RUN_STABILITY_IDENTITY["categories"]
)
_CANONICAL_RUN_STABILITY_IDENTITY["ordered_2l_pt_mins_gev"] = tuple(
    float(value)
    for value in SELECTION_PROFILES[
        _CANONICAL_RUN_STABILITY_IDENTITY["selection_profile"]
    ]["ordered_2l_pt_mins"]
)
_CANONICAL_RUN_STABILITY_IDENTITY["category_selector_sha256"] = hashlib.sha256(
    _CANONICAL_RUN_STABILITY_IDENTITY["category_selector"].encode()
).hexdigest()


def _csv_selector_names(value):
    names = tuple(part.strip() for part in str(value).split(","))
    if not names or any(not name for name in names) or len(set(names)) != len(names):
        return ()
    return names


def _compact_number(value):
    number = float(value)
    if number.is_integer():
        return str(int(number))
    return format(number, ".12g").replace(".", "p")


def _canonical_run_stability_tag_contract():
    """Recognize only the selected declarative production identity.

    The later durable-contract writer validates every advertised semantic
    field against the resolved cuts, axes, selection profile, observables, and
    categories before it writes an analysis contract.
    """

    expected = _CANONICAL_RUN_STABILITY_IDENTITY
    category_names = _csv_selector_names(RUN_STABILITY_CATEGORY_SELECTOR)
    category_selector_sha256 = hashlib.sha256(
        RUN_STABILITY_CATEGORY_SELECTOR.encode()
    ).hexdigest()
    recognized = (
        ANALYSIS_PASS == "RUN_STABILITY"
        and RUN_STABILITY_REGION == "DY"
        and RUN_STABILITY_OBSERVABLE_SELECTOR.lower() == expected["observable_selector"]
        and SELECTION_PROFILE == expected["selection_profile"]
        and category_names == expected["categories"]
        and len(category_names) == expected["category_count"]
        and RUN_STABILITY_CATEGORY_SELECTOR == expected["category_selector"]
    )
    if not recognized:
        return None
    return {
        "schema_version": 1,
        "style": "declarative_run_stability",
        "analysis_pass": ANALYSIS_PASS,
        "region": RUN_STABILITY_REGION,
        "year": YEAR,
        "observable_selector": RUN_STABILITY_OBSERVABLE_SELECTOR,
        "observables": list(expected["observables"]),
        "category_selector": RUN_STABILITY_CATEGORY_SELECTOR,
        "categories": list(category_names),
        "category_selector_sha256": category_selector_sha256,
        "category_integrity": {
            "expected_count": int(expected["expected_category_contract"]["count"]),
            "expected_selector_sha256": expected["expected_category_contract"][
                "selector_sha256"
            ],
            "observed_count": len(category_names),
            "observed_selector_sha256": category_selector_sha256,
        },
        "selection_profile": SELECTION_PROFILE,
        "ordered_2l_pt_mins_gev": list(expected["ordered_2l_pt_mins_gev"]),
        "mass_window_gev": list(expected["mass_window_gev"]),
        "mass_window_strict": bool(expected["mass_window_strict"]),
    }


_tag_timestamp_utc = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
RUN_STABILITY_TAG_CONTRACT = _canonical_run_stability_tag_contract()
if RUN_STABILITY_TAG_CONTRACT is None:
    raise RuntimeError(
        "RunStability could not resolve its canonical JSON-backed numerical "
        "identity; clone-era fallback tags are unsupported"
    )
_tag_pt = RUN_STABILITY_TAG_CONTRACT["ordered_2l_pt_mins_gev"]
_tag_mass = RUN_STABILITY_TAG_CONTRACT["mass_window_gev"]
_tag_categories = RUN_STABILITY_TAG_CONTRACT["categories"]
tag = (
    f"DYRS_{YEAR}_pt"
    f"{_compact_number(_tag_pt[0])}"
    f"{'' if _tag_pt[0] == _tag_pt[1] else '-' + _compact_number(_tag_pt[1])}_"
    f"m{_compact_number(_tag_mass[0])}to{_compact_number(_tag_mass[1])}_"
    f"obs{len(RUN_STABILITY_TAG_CONTRACT['observables'])}_"
    f"cat{len(_tag_categories)}-"
    f"{RUN_STABILITY_TAG_CONTRACT['category_selector_sha256'][:8]}_"
    f"{_tag_timestamp_utc}"
)
RUN_STABILITY_TAG_CONTRACT["tag"] = tag
RUN_STABILITY_TAG_CONTRACT["timestamp_utc_compact"] = _tag_timestamp_utc

runnerFile = "run_stability_runner.py"

outputFile = "mkShapes__{}.root".format(tag)

useEOSUserOutput = False

# Edit this one value to select the default execution contract for ordinary
# mkShapesRDF commands.  Environment variables can still override it for tests.
EXECUTION_PROFILE = "local"

_LCG_109_EL9_SETUP = (
    "source /cvmfs/sft.cern.ch/lcg/views/LCG_109/" "x86_64-el9-gcc13-opt/setup.sh"
)

EXECUTION_PROFILES = {
    "local": {
        "description": "Local input/output, no Condor runtime package.",
        "inputAccessMode": "as-configured",
        "outputMode": "local",
        "condorRuntimePackage": False,
        "condorRuntimeSetup": [],
        "configIncludeBase": "checkout",
        "useX509Proxy": False,
        "sitePreset": "local",
    },
    "local_xrootd": {
        "description": "Local output with direct CERN XRootD input.",
        "inputAccessMode": "xrootd",
        "outputMode": "local",
        "condorRuntimePackage": False,
        "condorRuntimeSetup": [],
        "configIncludeBase": "checkout",
        "useX509Proxy": False,
        "sitePreset": "local",
    },
    "local_stagein": {
        "description": "Local output with input staged to task-owned scratch.",
        "inputAccessMode": "stage-in",
        "outputMode": "local",
        "condorRuntimePackage": False,
        "condorRuntimeSetup": [],
        "configIncludeBase": "checkout",
        "useX509Proxy": False,
        "sitePreset": "local",
    },
    "shared_xrootd_local": {
        "description": "Shared-checkout Condor, CERN XRootD input, returned output.",
        "inputAccessMode": "xrootd",
        "outputMode": "local",
        "condorRuntimePackage": False,
        "condorRuntimeSetup": [],
        "configIncludeBase": "checkout",
        "useX509Proxy": True,
        "sitePreset": "lxplus",
    },
    "shared_xrootd_eos": {
        "description": "Shared-checkout Condor, CERN XRootD input, test EOS stage-out.",
        "inputAccessMode": "xrootd",
        "outputMode": "test-remote",
        "condorRuntimePackage": False,
        "condorRuntimeSetup": [],
        "configIncludeBase": "checkout",
        "useX509Proxy": True,
        "sitePreset": "lxplus",
    },
    "shared_xrootd_eos_production": {
        "description": "Shared-checkout CERN Condor, CERN XRootD input and CERN EOS stage-out.",
        "inputAccessMode": "xrootd",
        "outputMode": "production-remote",
        "condorRuntimePackage": False,
        "condorRuntimeSetup": [],
        "configIncludeBase": "checkout",
        "useX509Proxy": True,
        "sitePreset": "lxplus",
        "productionCampaign": "lxplus",
        "xrdReadEndpoint": "root://eoscms.cern.ch",
        "xrdDiscoveryEndpoint": "root://eoscms.cern.ch",
        "xrdWriteEndpoint": "root://eoscms.cern.ch",
    },
    "shared_xrootd_fnal_eos_production": {
        "description": "Shared-checkout CERN Condor, CERN XRootD input and FNAL EOS stage-out.",
        "inputAccessMode": "xrootd",
        "outputMode": "production-remote",
        "condorRuntimePackage": False,
        "condorRuntimeSetup": [],
        "configIncludeBase": "checkout",
        "useX509Proxy": True,
        "sitePreset": "lxplus",
        "productionCampaign": "lxplus_fnal",
        "xrdReadEndpoint": "root://eoscms.cern.ch",
        "xrdDiscoveryEndpoint": "root://eoscms.cern.ch",
        "xrdWriteEndpoint": "root://cmseos.fnal.gov",
    },
    "packaged_xrootd_local": {
        "description": "Packaged Condor, CERN XRootD direct input, returned output.",
        "inputAccessMode": "xrootd",
        "outputMode": "local",
        "condorRuntimePackage": True,
        "condorRuntimeSetup": [_LCG_109_EL9_SETUP],
        "configIncludeBase": "runtime",
        "useX509Proxy": True,
        "sitePreset": "packaged",
    },
    "packaged_xrootd_eos": {
        "description": "Packaged Condor, CERN XRootD direct input, test EOS stage-out.",
        "inputAccessMode": "xrootd",
        "outputMode": "test-remote",
        "condorRuntimePackage": True,
        "condorRuntimeSetup": [_LCG_109_EL9_SETUP],
        "configIncludeBase": "runtime",
        "useX509Proxy": True,
        "sitePreset": "packaged",
    },
    "packaged_xrootd_eos_production": {
        "description": "Packaged LXPLUS Condor, CERN XRootD input and CERN EOS stage-out.",
        "inputAccessMode": "xrootd",
        "outputMode": "production-remote",
        "condorRuntimePackage": True,
        "condorRuntimeSetup": [_LCG_109_EL9_SETUP],
        "configIncludeBase": "runtime",
        "useX509Proxy": True,
        "sitePreset": "lxplus",
        "productionCampaign": "lxplus_packaged",
        "xrdWriteEndpoint": "root://eoscms.cern.ch",
    },
    "packaged_fnal_xrootd_eos_production": {
        "description": "Packaged FNAL Condor, CERN XRootD input and FNAL EOS stage-out.",
        "inputAccessMode": "xrootd",
        "outputMode": "production-remote",
        "condorRuntimePackage": True,
        "condorRuntimeSetup": [_LCG_109_EL9_SETUP],
        "configIncludeBase": "runtime",
        "useX509Proxy": True,
        "sitePreset": "fnal_lpc_packaged",
        "productionCampaign": "fnal_lpc_packaged",
        "xrdWriteEndpoint": "root://cmseos.fnal.gov",
    },
    "packaged_stagein_local": {
        "description": "Packaged Condor, stage-in input, returned output.",
        "inputAccessMode": "stage-in",
        "outputMode": "local",
        "condorRuntimePackage": True,
        "condorRuntimeSetup": [_LCG_109_EL9_SETUP],
        "configIncludeBase": "runtime",
        "useX509Proxy": True,
        "sitePreset": "packaged",
    },
    "packaged_stagein_eos": {
        "description": "Packaged Condor, stage-in input, test EOS stage-out.",
        "inputAccessMode": "stage-in",
        "outputMode": "test-remote",
        "condorRuntimePackage": True,
        "condorRuntimeSetup": [_LCG_109_EL9_SETUP],
        "configIncludeBase": "runtime",
        "useX509Proxy": True,
        "sitePreset": "packaged",
    },
    "packaged_stagein_eos_production": {
        "description": "Packaged Condor, stage-in input, production EOS stage-out.",
        "inputAccessMode": "stage-in",
        "outputMode": "production-remote",
        "condorRuntimePackage": True,
        "condorRuntimeSetup": [_LCG_109_EL9_SETUP],
        "configIncludeBase": "runtime",
        "useX509Proxy": True,
        "sitePreset": "fnal_lpc_packaged",
        "productionCampaign": "fnal_lpc_packaged_stagein",
        "xrdWriteEndpoint": "root://cmseos.fnal.gov",
    },
    "packaged_fnal_stagein_eos_production": {
        "description": "Packaged FNAL Condor, CERN xrdcp stage-in, FNAL EOS stage-out.",
        "inputAccessMode": "stage-in",
        "outputMode": "production-remote",
        "condorRuntimePackage": True,
        "condorRuntimeSetup": [_LCG_109_EL9_SETUP],
        "configIncludeBase": "runtime",
        "useX509Proxy": True,
        "sitePreset": "fnal_lpc_packaged",
        "productionCampaign": "fnal_lpc_packaged_stagein",
        "xrdReadEndpoint": "root://eoscms.cern.ch",
        "xrdDiscoveryEndpoint": "root://eoscms.cern.ch",
        "xrdWriteEndpoint": "root://cmseos.fnal.gov",
    },
}


def _env_bool(name, default=False):
    value = os.environ.get(name)
    if value is None:
        return bool(default)
    return value.strip().lower() in ("1", "true", "yes", "on")


def _env_int(name, default):
    value = os.environ.get(name)
    if value is None:
        return default
    return int(value)


def _env_split(name, default=()):
    value = os.environ.get(name)
    if value is None:
        return list(default or [])
    return [item.strip() for item in value.split(";;") if item.strip()]


def _checkout_include_base():
    return os.path.abspath(os.path.join(CONFIG_DIR, "../../.."))


def _resolve_include_base(value):
    if value in (None, "", "checkout"):
        return _checkout_include_base()
    return value


def _resolve_execution_profile():
    requested = os.environ.get("EXECUTION_PROFILE", EXECUTION_PROFILE)
    if requested not in EXECUTION_PROFILES:
        available = ", ".join(sorted(EXECUTION_PROFILES))
        raise ValueError(
            f"Unsupported EXECUTION_PROFILE={requested!r}. "
            f"Available profiles: {available}"
        )
    return requested, dict(EXECUTION_PROFILES[requested])


SELECTED_EXECUTION_PROFILE, _profile = _resolve_execution_profile()
PROFILE_DESCRIPTION = _profile["description"]
SITE_PRESET = os.environ.get(
    "SITE_PRESET", _profile.get("sitePreset", SELECTED_EXECUTION_PROFILE)
)

_user = os.environ.get("USER", getpass.getuser())
_eos_user = os.environ.get("EOS_USER") or os.environ.get("CERN_USER") or _user
OUTPUT_LEAF = tag
TEST_CAMPAIGN = os.environ.get("TEST_CAMPAIGN", tag)
OUTPUT_MODE = os.environ.get("OUTPUT_MODE", _profile["outputMode"])


def _default_output_lfn(campaign):
    base_lfn = f"/store/user/{_eos_user}/mkShapesRDF_rootfiles"
    campaign = (campaign or "").strip("/")
    output_leaf = OUTPUT_LEAF.strip("/")
    if campaign and campaign != output_leaf:
        return f"{base_lfn}/{campaign}/{output_leaf}"
    return f"{base_lfn}/{output_leaf}"


xrdReadEndpoint = os.environ.get(
    "XRD_READ_ENDPOINT", _profile.get("xrdReadEndpoint", "root://eoscms.cern.ch")
)
xrdDiscoveryEndpoint = os.environ.get(
    "XRD_DISCOVERY_ENDPOINT",
    _profile.get("xrdDiscoveryEndpoint") or xrdReadEndpoint,
)
xrdWriteEndpoint = os.environ.get(
    "XRD_WRITE_ENDPOINT", _profile.get("xrdWriteEndpoint", "root://eoscms.cern.ch")
)
xrdRedirector = xrdReadEndpoint.replace("root://", "").strip("/")

testOutputLFN = os.environ.get(
    "TEST_OUTPUT_LFN",
    _default_output_lfn(TEST_CAMPAIGN),
)
PRODUCTION_CAMPAIGN = os.environ.get(
    "PRODUCTION_CAMPAIGN", _profile.get("productionCampaign", tag)
)
productionOutputLFN = os.environ.get(
    "PRODUCTION_OUTPUT_LFN",
    _default_output_lfn(PRODUCTION_CAMPAIGN),
)

CONFIG_INCLUDE_BASE = _resolve_include_base(
    os.environ.get("CONFIG_INCLUDE_BASE", _profile.get("configIncludeBase"))
)

os.environ["EXECUTION_PROFILE"] = SELECTED_EXECUTION_PROFILE
os.environ["SITE_PRESET"] = SITE_PRESET
os.environ["OUTPUT_MODE"] = OUTPUT_MODE
os.environ["INPUT_ACCESS_MODE"] = os.environ.get(
    "INPUT_ACCESS_MODE", _profile["inputAccessMode"]
)
os.environ["XRD_READ_ENDPOINT"] = xrdReadEndpoint
os.environ["XRD_DISCOVERY_ENDPOINT"] = xrdDiscoveryEndpoint
os.environ["XRD_WRITE_ENDPOINT"] = xrdWriteEndpoint
os.environ["CONFIG_INCLUDE_BASE"] = CONFIG_INCLUDE_BASE
os.environ["OUTPUT_LEAF"] = OUTPUT_LEAF
os.environ["TEST_CAMPAIGN"] = TEST_CAMPAIGN
os.environ["PRODUCTION_CAMPAIGN"] = PRODUCTION_CAMPAIGN

JOB_CAMPAIGN = os.environ.get("JOB_CAMPAIGN", "").strip("/")
if JOB_CAMPAIGN:
    if JOB_CAMPAIGN in (".", "..") or "/" in JOB_CAMPAIGN or "\\" in JOB_CAMPAIGN:
        raise ValueError(
            "JOB_CAMPAIGN must be one nonempty directory name without path separators"
        )
    os.environ["JOB_CAMPAIGN"] = JOB_CAMPAIGN

remoteIO = {
    "inputAccessMode": os.environ["INPUT_ACCESS_MODE"],
    "xrdReadEndpoint": xrdReadEndpoint,
    "xrdDiscoveryEndpoint": xrdDiscoveryEndpoint,
    "xrdWriteEndpoint": xrdWriteEndpoint,
    "stageInScratch": os.environ.get("STAGE_IN_SCRATCH")
    or _profile.get("stageInScratch"),
    "stageInCleanup": os.environ.get(
        "STAGE_IN_CLEANUP", _profile.get("stageInCleanup", "on-success")
    ),
    "preserveStageInOnFailure": _env_bool(
        "PRESERVE_STAGE_IN_ON_FAILURE",
        _profile.get("preserveStageInOnFailure", True),
    ),
    "existingOutputPolicy": os.environ.get(
        "EXISTING_OUTPUT_POLICY", _profile.get("existingOutputPolicy", "fail")
    ),
    "remoteCommandTimeout": _env_int(
        "REMOTE_COMMAND_TIMEOUT", _profile.get("remoteCommandTimeout", 120)
    ),
    "remoteTransferRetries": _env_int(
        "REMOTE_TRANSFER_RETRIES", _profile.get("remoteTransferRetries", 2)
    ),
}

condorRuntimePackage = _env_bool(
    "CONDOR_RUNTIME_PACKAGE", _profile.get("condorRuntimePackage", False)
)
condorRuntimePackageName = os.environ.get(
    "CONDOR_RUNTIME_PACKAGE_NAME", "mkshapesrdf_runtime.tgz"
)
condorRuntimeSetup = _env_split(
    "CONDOR_RUNTIME_SETUP", _profile.get("condorRuntimeSetup", [])
)
condorRuntimeIncludes = _env_split(
    "CONDOR_RUNTIME_INCLUDES", _profile.get("condorRuntimeIncludes", [])
)
useX509Proxy = _env_bool("USE_X509_PROXY", _profile.get("useX509Proxy", False))

requiredExecutionMode = "batch" if condorRuntimePackage else None
executionModeRemediation = (
    "For a safe login-node run, select "
    "EXECUTION_PROFILE=local_xrootd and OUTPUT_MODE=local, then "
    "recompile with -c 1."
)
if (
    globals().get("mkShapesRDFExecutionMode") == "local"
    and requiredExecutionMode == "batch"
):
    raise RuntimeError(
        f"Analysis profile {SELECTED_EXECUTION_PROFILE!r} is batch-only, but "
        "local execution (-b 0) was requested. "
        f"{executionModeRemediation} Packaged profiles deliberately use the "
        "worker-relative runtime include tree and must not stage production "
        "output from an interactive smoke test."
    )

analysisRemoteOutputLFN = (
    productionOutputLFN if OUTPUT_MODE == "production-remote" else testOutputLFN
)
eosUserOutputFolder = f"{xrdWriteEndpoint}/{analysisRemoteOutputLFN}"

jobControlDir = (
    os.path.join("jobs", JOB_CAMPAIGN, tag)
    if JOB_CAMPAIGN
    else os.path.join("jobs", tag)
)

# The stock merge path writes its local hadd target below ``localJobDir``.
# Keep durable configs/JDLs in the checkout, while giving CERN remote-output
# merges enough scratch space on EOS user storage.  Other sites can supply an
# absolute task-owned location explicitly.
_merge_scratch_override = os.environ.get("MERGE_SCRATCH_ROOT")
if _merge_scratch_override:
    mergeScratchRoot = os.path.abspath(os.path.expanduser(_merge_scratch_override))
    if not os.path.isabs(os.path.expanduser(_merge_scratch_override)):
        raise ValueError("MERGE_SCRATCH_ROOT must be an absolute path")
elif OUTPUT_MODE in ("test-remote", "production-remote") and SITE_PRESET == "lxplus":
    _merge_campaign = (
        PRODUCTION_CAMPAIGN if OUTPUT_MODE == "production-remote" else TEST_CAMPAIGN
    )
    mergeScratchRoot = os.path.join(
        "/eos/user",
        _eos_user[0],
        _eos_user,
        "mkShapesRDF_merge_scratch",
        _merge_campaign,
    )
else:
    mergeScratchRoot = None

# The core appends the remote output leaf (the tag) below this base.
localJobDir = mergeScratchRoot or jobControlDir

outputFolder = (
    eosUserOutputFolder
    if OUTPUT_MODE in ("test-remote", "production-remote")
    else os.path.join(jobControlDir, OUTPUT_LEAF)
)
if OUTPUT_MODE in ("test-remote", "production-remote"):
    useX509Proxy = True

batchFolder = os.path.join(jobControlDir, "condor")

# mkShapesRDF batch submission removes "{batchFolder}/{tag}" before creating it.
# Pre-creating it here avoids a noisy first-run FileNotFoundError message.
os.makedirs(os.path.join(batchFolder, tag), exist_ok=True)

configsFolder = os.path.join(jobControlDir, "configs")

lumi = _selected_year.get("lumi_fb", 26.49)

aliasesFile = "aliases.py"

selectionConfigFile = "selection_config.py"

variablesFile = "variables.py"

cutsFile = "cuts.py"

samplesFile = "samples.py"

plotFile = "plot.py"

structureFile = "structure.py"

nuisancesFile = "nuisances_nominal.py"

plotPath = os.path.join(jobControlDir, "plots")

mountEOS = []

imports = ["os", "glob", ("collections", "OrderedDict"), "ROOT"]

filesToExec = [
    "year_config.py",
    selectionConfigFile,
    "category_config.py",
    samplesFile,
    "run_stability_config.py",
    aliasesFile,
    cutsFile,
    variablesFile,
    plotFile,
    nuisancesFile,
    structureFile,
    "write_contract.py",
    "worker_payload.py",
]

jdlconfigfile = ""

varsToKeep = [
    "ANALYSIS_PASS",
    "ENABLE_SYSTEMATICS",
    "HISTOGRAMS",
    "HISTOGRAM_DETAIL",
    "HISTOGRAM_PROFILE",
    "CATEGORY_PROFILE",
    "SAMPLE_PROFILE",
    "OUTPUT_PRODUCT",
    "YEAR",
    "SELECTED_EXECUTION_PROFILE",
    "PROFILE_DESCRIPTION",
    "SITE_PRESET",
    "OUTPUT_MODE",
    "CONFIG_INCLUDE_BASE",
    "useEOSUserOutput",
    "useX509Proxy",
    "xrdRedirector",
    "xrdReadEndpoint",
    "xrdDiscoveryEndpoint",
    "xrdWriteEndpoint",
    "remoteIO",
    "condorRuntimePackage",
    "condorRuntimePackageName",
    "condorRuntimeSetup",
    "condorRuntimeIncludes",
    "requiredExecutionMode",
    "executionModeRemediation",
    "testOutputLFN",
    "productionOutputLFN",
    "OUTPUT_LEAF",
    "TEST_CAMPAIGN",
    "PRODUCTION_CAMPAIGN",
    "JOB_CAMPAIGN",
    "analysisRemoteOutputLFN",
    "eosUserOutputFolder",
    "jdlconfigfile",
    "batchVars",
    "jobControlDir",
    "mergeScratchRoot",
    "localJobDir",
    "outputFolder",
    "batchFolder",
    "configsFolder",
    "outputFile",
    "runnerFile",
    "sharedBatchPayload",
    "tag",
    "samples",
    "aliases",
    "variables",
    "VARIABLE_REGISTRY",
    "VARIABLE_REGISTRY_HASHES",
    "CATEGORY_VARIABLES",
    "CATEGORY_METADATA",
    "SAMPLE_PROFILE_GROUPS",
    "SAMPLE_PROFILE_OUTPUTS",
    "SAMPLE_SELECTION_SOURCE",
    "ACTIVE_SAMPLE_OUTPUTS",
    "RUN_STABILITY_OBSERVABLES",
    "RUN_STABILITY_OBSERVABLE_SELECTORS",
    "RUN_STABILITY_CATEGORIES",
    "RUN_STABILITY_PRODUCTION_PROFILE",
    "SELECTED_RUN_STABILITY_PRODUCTION_PROFILE",
    "RUN_STABILITY_REGION",
    "RUN_STABILITY_OBSERVABLE_SELECTOR",
    "RUN_STABILITY_CATEGORY_SELECTOR",
    "RUN_STABILITY_TAG_CONTRACT",
    "SELECTION_PROFILE",
    "SELECTED_SELECTION_PROFILE",
    "TWO_LEPTON_PT_MINS",
    "RUN_STABILITY_METADATA_PATHS",
    "RUN_STABILITY_LUMINOSITY_SOURCE_DEFINITIONS",
    "RUN_STABILITY_CATEGORY_LUMINOSITY_SOURCES",
    "RUN_STABILITY_CONTRACT",
    "analysisContract",
    "analysisContractPath",
    ("cuts", {"cuts": "cuts", "preselections": "preselections"}),
    ("plot", {"plot": "plot", "groupPlot": "groupPlot", "legend": "legend"}),
    "nuisances",
    "structure",
    "lumi",
]

# The stock standalone-job representation repeats every entry in ``batchVars``
# in every process script. RunStability keeps the category-specific analysis
# dictionaries in one generated payload and sends only split-sample metadata
# plus its path to each worker.  Plotting metadata remains in ``varsToKeep``.
batchVars = ["samples", "sharedBatchPayload"]

for _remote_key in (
    "remoteIO",
    "xrdWriteEndpoint",
    "xrdReadEndpoint",
    "xrdDiscoveryEndpoint",
):
    if _remote_key not in batchVars:
        batchVars.append(_remote_key)

for _worker_contract_key in (
    "ANALYSIS_PASS",
    "ENABLE_SYSTEMATICS",
    "HISTOGRAMS",
    "HISTOGRAM_DETAIL",
    "HISTOGRAM_PROFILE",
    "CATEGORY_PROFILE",
    "SAMPLE_PROFILE",
    "OUTPUT_PRODUCT",
    "YEAR",
    "SELECTION_PROFILE",
    "OUTPUT_MODE",
    "analysisRemoteOutputLFN",
):
    if _worker_contract_key not in batchVars:
        batchVars.append(_worker_contract_key)

varsToKeep += ["plotPath"]
