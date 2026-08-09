"""Four-lepton control and reference selections for Run-3 production."""

import os
import getpass
from datetime import datetime, timezone


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

if "load_selected_year" not in globals():
    exec(open(os.path.join(CONFIG_DIR, "year_config.py")).read(), globals(), globals())

# Central year selection used by samples, aliases, variables, and nuisances.
# Keep this in sync with keys available in year_config.json.
YEAR = os.environ.get("YEAR", "2024")
os.environ["YEAR"] = YEAR
_, _selected_year, _ = load_selected_year()

ANALYSIS_PASS = str(os.environ.get("ANALYSIS_PASS", "ALL")).strip().upper()
if ANALYSIS_PASS not in ("ALL", "ZPARENT", "FOURL_BASE", "CONTROL"):
    raise ValueError(
        "ANALYSIS_PASS must be ALL, ZPARENT, FOURL_BASE, or CONTROL; "
        f"received {ANALYSIS_PASS!r}"
    )
os.environ["ANALYSIS_PASS"] = ANALYSIS_PASS

# PlotsConfigurationsRun3 convention: configuration.py selects either the
# full nuisance source or a separate empty nominal nuisance source.
ENABLE_SYSTEMATICS = _early_env_bool("ENABLE_SYSTEMATICS", False)
os.environ["ENABLE_SYSTEMATICS"] = "1" if ENABLE_SYSTEMATICS else "0"
if ANALYSIS_PASS == "ALL" and ENABLE_SYSTEMATICS:
    raise ValueError(
        "ANALYSIS_PASS=ALL currently supports nominal production only; "
        "ROOT cannot redefine the category weight after that column depends "
        "on variations. Set ENABLE_SYSTEMATICS=0; no variation is silently dropped"
    )

# ZZ_CR is deliberately histogram-only.  Tree snapshots belong in a dedicated
# skim configuration, not in this production and plotting contract.
HISTOGRAMS = True
os.environ["HISTOGRAMS"] = "1"
CATEGORY_PROFILE = os.environ.get("CATEGORY_PROFILE", "standard").strip().lower()
if CATEGORY_PROFILE not in (
    "minimal", "standard", "flavor", "stream", "trigger", "detailed", "debug"
):
    raise ValueError(
        "CATEGORY_PROFILE must be minimal, standard, flavor, stream, trigger, "
        "detailed, or debug; "
        f"received {CATEGORY_PROFILE!r}"
    )
HISTOGRAM_PROFILE = os.environ.get(
    "HISTOGRAM_PROFILE", os.environ.get("HISTOGRAM_DETAIL", "analysis")
).strip().lower()
if HISTOGRAM_PROFILE not in ("analysis", "trigger", "objects", "quality", "weights", "all"):
    raise ValueError(
        "HISTOGRAM_PROFILE must be analysis, trigger, objects, quality, weights, or all; "
        f"received {HISTOGRAM_PROFILE!r}"
    )
HISTOGRAM_DETAIL = HISTOGRAM_PROFILE
SAMPLE_PROFILE = os.environ.get("SAMPLE_PROFILE", "commissioning").strip().lower()
if SAMPLE_PROFILE not in ("commissioning", "presentation"):
    raise ValueError(
        "SAMPLE_PROFILE must be commissioning or presentation; "
        f"received {SAMPLE_PROFILE!r}"
    )
os.environ["CATEGORY_PROFILE"] = CATEGORY_PROFILE
os.environ["HISTOGRAM_PROFILE"] = HISTOGRAM_PROFILE
os.environ["HISTOGRAM_DETAIL"] = HISTOGRAM_DETAIL
os.environ["SAMPLE_PROFILE"] = SAMPLE_PROFILE
OUTPUT_PRODUCT = "HIST"
os.environ["OUTPUT_PRODUCT"] = OUTPUT_PRODUCT

_systematics_tag = "FULLSYST" if ENABLE_SYSTEMATICS else "NOMINAL"
tag = (
    f"FourLepton_{YEAR}_{ANALYSIS_PASS}_{CATEGORY_PROFILE}_"
    f"{HISTOGRAM_PROFILE}_{SAMPLE_PROFILE}_{OUTPUT_PRODUCT}_{_systematics_tag}"
)
tag = f"{tag}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"

runnerFile = "zz_cr_runner.py"

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

jobControlDir = os.path.join("jobs", tag)

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

nuisancesFile = "nuisances.py" if ENABLE_SYSTEMATICS else "nuisances_nominal.py"

plotPath = os.path.join(jobControlDir, "plots")

mountEOS = []

imports = ["os", "glob", ("collections", "OrderedDict"), "ROOT"]

filesToExec = [
    "year_config.py",
    samplesFile,
    selectionConfigFile,
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
    "analysisContract",
    "analysisContractPath",
    ("cuts", {"cuts": "cuts", "preselections": "preselections"}),
    ("plot", {"plot": "plot", "groupPlot": "groupPlot", "legend": "legend"}),
    "nuisances",
    "structure",
    "lumi",
]

# The stock standalone-job representation repeats every entry in ``batchVars``
# in every process script.  ZZ_CR keeps the large, category-specific analysis
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
    "OUTPUT_MODE",
    "analysisRemoteOutputLFN",
):
    if _worker_contract_key not in batchVars:
        batchVars.append(_worker_contract_key)

varsToKeep += ["plotPath"]
