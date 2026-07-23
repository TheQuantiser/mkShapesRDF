"""
ZH(H->WW) -> 4l + MET ZZ control region configuration.
"""

import os
import getpass
from datetime import datetime, timezone

def _resolve_zzcr_config_dir():
    candidates = [
        globals().get("ZZCR_CONFIG_DIR"),
        globals().get("folder"),
        os.getcwd(),
        os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else None,
    ]
    for cand in candidates:
        if not cand:
            continue
        cand_abs = os.path.abspath(cand)
        if os.path.exists(os.path.join(cand_abs, "zzcr_year.py")):
            return cand_abs
    # Fallback to cwd if no candidate contains zzcr_year.py
    return os.path.abspath(os.getcwd())


ZZCR_CONFIG_DIR = _resolve_zzcr_config_dir()

if "load_selected_year" not in globals():
    exec(open(os.path.join(ZZCR_CONFIG_DIR, "zzcr_year.py")).read(), globals(), globals())

# Central ZZ_CR year selection (used by samples/aliases/variables/nuisances).
# Keep this in sync with keys available in zzcr_year_config.json.
ZZCR_YEAR = os.environ.get("ZZCR_YEAR", "2024")
os.environ["ZZCR_YEAR"] = ZZCR_YEAR
_, _selected_year, _ = load_selected_year()

tag = f"ZH_4lMET_ZZCR_{ZZCR_YEAR}"
tag = f"{tag}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"

runnerFile = "default"

outputFile = "mkShapes__{}.root".format(tag)

useEOSUserOutput = False

# Edit this one value to select the default execution contract for ordinary
# mkShapesRDF commands.  Environment variables can still override it for tests.
ZZCR_EXECUTION_PROFILE = "local"

_LCG_109_EL9_SETUP = (
    "source /cvmfs/sft.cern.ch/lcg/views/LCG_109/"
    "x86_64-el9-gcc13-opt/setup.sh"
)

ZZCR_EXECUTION_PROFILES = {
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
        "description": "Shared-checkout Condor, CERN XRootD input, production EOS stage-out.",
        "inputAccessMode": "xrootd",
        "outputMode": "production-remote",
        "condorRuntimePackage": False,
        "condorRuntimeSetup": [],
        "configIncludeBase": "checkout",
        "useX509Proxy": True,
        "sitePreset": "lxplus",
        "productionCampaign": "lxplus",
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
        "description": "Packaged Condor, CERN XRootD direct input, production EOS stage-out.",
        "inputAccessMode": "xrootd",
        "outputMode": "production-remote",
        "condorRuntimePackage": True,
        "condorRuntimeSetup": [_LCG_109_EL9_SETUP],
        "configIncludeBase": "runtime",
        "useX509Proxy": True,
        "sitePreset": "fnal_lpc_packaged",
        "productionCampaign": "fnal_lpc_packaged",
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
    return os.path.abspath(os.path.join(ZZCR_CONFIG_DIR, "../../.."))


def _resolve_include_base(value):
    if value in (None, "", "checkout"):
        return _checkout_include_base()
    return value


def _resolve_execution_profile():
    requested = os.environ.get("ZZCR_EXECUTION_PROFILE", ZZCR_EXECUTION_PROFILE)
    if requested not in ZZCR_EXECUTION_PROFILES:
        available = ", ".join(sorted(ZZCR_EXECUTION_PROFILES))
        raise ValueError(
            f"Unsupported ZZCR_EXECUTION_PROFILE={requested!r}. "
            f"Available profiles: {available}"
        )
    return requested, dict(ZZCR_EXECUTION_PROFILES[requested])


ZZCR_SELECTED_EXECUTION_PROFILE, _profile = _resolve_execution_profile()
ZZCR_PROFILE_DESCRIPTION = _profile["description"]
ZZCR_SITE_PRESET = os.environ.get(
    "ZZCR_SITE_PRESET", _profile.get("sitePreset", ZZCR_SELECTED_EXECUTION_PROFILE)
)

_user = os.environ.get("USER", getpass.getuser())
_eos_user = os.environ.get("ZZCR_EOS_USER") or os.environ.get("CERN_USER") or _user
ZZCR_OUTPUT_LEAF = tag
ZZCR_TEST_CAMPAIGN = os.environ.get("ZZCR_TEST_CAMPAIGN", tag)
ZZCR_OUTPUT_MODE = os.environ.get("ZZCR_OUTPUT_MODE", _profile["outputMode"])


def _default_output_lfn(campaign):
    base_lfn = f"/store/user/{_eos_user}/mkShapesRDF_rootfiles"
    campaign = (campaign or "").strip("/")
    output_leaf = ZZCR_OUTPUT_LEAF.strip("/")
    if campaign and campaign != output_leaf:
        return f"{base_lfn}/{campaign}/{output_leaf}"
    return f"{base_lfn}/{output_leaf}"

xrdReadEndpoint = os.environ.get(
    "ZZCR_XRD_READ_ENDPOINT", _profile.get("xrdReadEndpoint", "root://eoscms.cern.ch")
)
xrdDiscoveryEndpoint = os.environ.get(
    "ZZCR_XRD_DISCOVERY_ENDPOINT",
    _profile.get("xrdDiscoveryEndpoint") or xrdReadEndpoint,
)
xrdWriteEndpoint = os.environ.get(
    "ZZCR_XRD_WRITE_ENDPOINT", _profile.get("xrdWriteEndpoint", "root://cmseos.fnal.gov")
)
xrdRedirector = xrdReadEndpoint.replace("root://", "").strip("/")

testOutputLFN = os.environ.get(
    "ZZCR_TEST_OUTPUT_LFN",
    _default_output_lfn(ZZCR_TEST_CAMPAIGN),
)
ZZCR_PRODUCTION_CAMPAIGN = os.environ.get(
    "ZZCR_PRODUCTION_CAMPAIGN", _profile.get("productionCampaign", tag)
)
productionOutputLFN = os.environ.get(
    "ZZCR_PRODUCTION_OUTPUT_LFN",
    _default_output_lfn(ZZCR_PRODUCTION_CAMPAIGN),
)

ZZCR_CONFIG_INCLUDE_BASE = _resolve_include_base(
    os.environ.get("ZZCR_CONFIG_INCLUDE_BASE", _profile.get("configIncludeBase"))
)

os.environ["ZZCR_EXECUTION_PROFILE"] = ZZCR_SELECTED_EXECUTION_PROFILE
os.environ["ZZCR_SITE_PRESET"] = ZZCR_SITE_PRESET
os.environ["ZZCR_OUTPUT_MODE"] = ZZCR_OUTPUT_MODE
os.environ["ZZCR_INPUT_ACCESS_MODE"] = os.environ.get(
    "ZZCR_INPUT_ACCESS_MODE", _profile["inputAccessMode"]
)
os.environ["ZZCR_XRD_READ_ENDPOINT"] = xrdReadEndpoint
os.environ["ZZCR_XRD_DISCOVERY_ENDPOINT"] = xrdDiscoveryEndpoint
os.environ["ZZCR_XRD_WRITE_ENDPOINT"] = xrdWriteEndpoint
os.environ["ZZCR_CONFIG_INCLUDE_BASE"] = ZZCR_CONFIG_INCLUDE_BASE
os.environ["ZZCR_OUTPUT_LEAF"] = ZZCR_OUTPUT_LEAF
os.environ["ZZCR_TEST_CAMPAIGN"] = ZZCR_TEST_CAMPAIGN
os.environ["ZZCR_PRODUCTION_CAMPAIGN"] = ZZCR_PRODUCTION_CAMPAIGN

remoteIO = {
    "inputAccessMode": os.environ["ZZCR_INPUT_ACCESS_MODE"],
    "xrdReadEndpoint": xrdReadEndpoint,
    "xrdDiscoveryEndpoint": xrdDiscoveryEndpoint,
    "xrdWriteEndpoint": xrdWriteEndpoint,
    "stageInScratch": os.environ.get("ZZCR_STAGE_IN_SCRATCH")
    or _profile.get("stageInScratch"),
    "stageInCleanup": os.environ.get(
        "ZZCR_STAGE_IN_CLEANUP", _profile.get("stageInCleanup", "on-success")
    ),
    "preserveStageInOnFailure": _env_bool(
        "ZZCR_PRESERVE_STAGE_IN_ON_FAILURE",
        _profile.get("preserveStageInOnFailure", True),
    ),
    "existingOutputPolicy": os.environ.get(
        "ZZCR_EXISTING_OUTPUT_POLICY", _profile.get("existingOutputPolicy", "fail")
    ),
    "remoteCommandTimeout": _env_int(
        "ZZCR_REMOTE_COMMAND_TIMEOUT", _profile.get("remoteCommandTimeout", 120)
    ),
    "remoteTransferRetries": _env_int(
        "ZZCR_REMOTE_TRANSFER_RETRIES", _profile.get("remoteTransferRetries", 2)
    ),
}

condorRuntimePackage = _env_bool(
    "ZZCR_CONDOR_RUNTIME_PACKAGE", _profile.get("condorRuntimePackage", False)
)
condorRuntimePackageName = os.environ.get(
    "ZZCR_CONDOR_RUNTIME_PACKAGE_NAME", "mkshapesrdf_runtime.tgz"
)
condorRuntimeSetup = _env_split(
    "ZZCR_CONDOR_RUNTIME_SETUP", _profile.get("condorRuntimeSetup", [])
)
condorRuntimeIncludes = _env_split(
    "ZZCR_CONDOR_RUNTIME_INCLUDES", _profile.get("condorRuntimeIncludes", [])
)
useX509Proxy = _env_bool("ZZCR_USE_X509_PROXY", _profile.get("useX509Proxy", False))

requiredExecutionMode = "batch" if condorRuntimePackage else None
executionModeRemediation = (
    "For a safe FNAL login-node run, select "
    "ZZCR_EXECUTION_PROFILE=local_xrootd and ZZCR_OUTPUT_MODE=local, then "
    "recompile with -c 1."
)
if (
    globals().get("mkShapesRDFExecutionMode") == "local"
    and requiredExecutionMode == "batch"
):
    raise RuntimeError(
        f"ZZCR profile {ZZCR_SELECTED_EXECUTION_PROFILE!r} is batch-only, but "
        "local execution (-b 0) was requested. "
        f"{executionModeRemediation} Packaged profiles deliberately use the "
        "worker-relative runtime include tree and must not stage production "
        "output from an interactive smoke test."
    )

zzcrRemoteOutputLFN = (
    productionOutputLFN
    if ZZCR_OUTPUT_MODE == "production-remote"
    else testOutputLFN
)
eosUserOutputFolder = f"{xrdWriteEndpoint}/{zzcrRemoteOutputLFN}"

localJobDir = os.path.join("jobs", tag)

outputFolder = (
    eosUserOutputFolder
    if ZZCR_OUTPUT_MODE in ("test-remote", "production-remote")
    else os.path.join(localJobDir, ZZCR_OUTPUT_LEAF)
)
if ZZCR_OUTPUT_MODE in ("test-remote", "production-remote"):
    useX509Proxy = True

batchFolder = os.path.join(localJobDir, "condor")

# mkShapesRDF batch submission removes "{batchFolder}/{tag}" before creating it.
# Pre-creating it here avoids a noisy first-run FileNotFoundError message.
os.makedirs(os.path.join(batchFolder, tag), exist_ok=True)

configsFolder = os.path.join(localJobDir, "configs")

lumi = _selected_year.get("lumi_fb", 26.49)

aliasesFile = "aliases.py"

selectionConfigFile = "zzcr_selection_config.py"

variablesFile = "variables.py"

cutsFile = "cuts.py"

samplesFile = "samples.py"

plotFile = "plot.py"

structureFile = "structure.py"

nuisancesFile = "nuisances.py"

plotPath = os.path.join(localJobDir, "plots")

mountEOS = []

imports = ["os", "glob", ("collections", "OrderedDict"), "ROOT"]

filesToExec = [
    "zzcr_year.py",
    samplesFile,
    selectionConfigFile,
    aliasesFile,
    variablesFile,
    cutsFile,
    plotFile,
    nuisancesFile,
    structureFile,
]

jdlconfigfile = ""

varsToKeep = [
    "ZZCR_SELECTED_EXECUTION_PROFILE",
    "ZZCR_PROFILE_DESCRIPTION",
    "ZZCR_SITE_PRESET",
    "ZZCR_OUTPUT_MODE",
    "ZZCR_CONFIG_INCLUDE_BASE",
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
    "ZZCR_OUTPUT_LEAF",
    "ZZCR_TEST_CAMPAIGN",
    "ZZCR_PRODUCTION_CAMPAIGN",
    "zzcrRemoteOutputLFN",
    "eosUserOutputFolder",
    "jdlconfigfile",
    "batchVars",
    "outputFolder",
    "batchFolder",
    "configsFolder",
    "outputFile",
    "runnerFile",
    "tag",
    "samples",
    "aliases",
    "variables",
    ("cuts", {"cuts": "cuts", "preselections": "preselections"}),
    ("plot", {"plot": "plot", "groupPlot": "groupPlot", "legend": "legend"}),
    "nuisances",
    "structure",
    "lumi",
]

batchVars = varsToKeep[varsToKeep.index("samples") :]

for _remote_key in ("remoteIO", "xrdWriteEndpoint", "xrdReadEndpoint", "xrdDiscoveryEndpoint"):
    if _remote_key not in batchVars:
        batchVars.append(_remote_key)

varsToKeep += ["plotPath"]
