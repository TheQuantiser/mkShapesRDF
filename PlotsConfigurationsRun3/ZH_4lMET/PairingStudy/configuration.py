"""mkShapesRDF entry point for the compact all-era pairing study."""

import os
from datetime import datetime, timezone
from pathlib import Path


CONFIG_DIR = Path(__file__).resolve().parent
if str(CONFIG_DIR) not in os.sys.path:
    os.sys.path.insert(0, str(CONFIG_DIR))

from pairing_config import (  # noqa: E402
    DEFAULT_XRD_ENDPOINT,
    SUPPORTED_YEARS,
    load_pairing_year,
)


YEAR = str(os.environ.get("YEAR", "2024"))
if YEAR not in SUPPORTED_YEARS:
    raise ValueError(f"Unsupported YEAR={YEAR!r}; available={list(SUPPORTED_YEARS)}")
os.environ["YEAR"] = YEAR
PAIRING_YEAR = load_pairing_year(YEAR)

PAIRING_CAMPAIGN = os.environ.get(
    "PAIRING_CAMPAIGN", datetime.now(timezone.utc).strftime("pairing_%Y%m%d_%H%M%S")
).strip()
if not PAIRING_CAMPAIGN or "/" in PAIRING_CAMPAIGN:
    raise ValueError("PAIRING_CAMPAIGN must be a nonempty path-safe name")

tag = f"PairingStudy_{YEAR}_{PAIRING_CAMPAIGN}"
# The core loader applies ``strip('.py')`` instead of removing a suffix, so a
# custom runner name must not begin or end with any of those characters.
runnerFile = "local_runner.py"
outputFile = f"mkShapes__{tag}.root"

outputFolder = os.environ.get(
    "PAIRING_OUTPUT_FOLDER", f"rootFiles/{PAIRING_CAMPAIGN}/{YEAR}"
)
batchFolder = os.environ.get(
    "PAIRING_BATCH_FOLDER", f"condor/{PAIRING_CAMPAIGN}/{YEAR}"
)
configsFolder = os.environ.get(
    "PAIRING_CONFIGS_FOLDER", f"configs/{PAIRING_CAMPAIGN}/{YEAR}"
)
plotPath = os.environ.get("PAIRING_PLOT_PATH", f"plots/{PAIRING_CAMPAIGN}")

lumi = PAIRING_YEAR["lumi_fb"]

pairingConfigFile = "pairing_config.py"
samplesFile = "samples.py"
aliasesFile = "aliases.py"
cutsFile = "cuts.py"
variablesFile = "variables.py"
plotFile = "plot.py"
structureFile = "structure.py"

# Nominal histogram-only study: no nuisance source and no snapshots.
nuisances = {}

xrdReadEndpoint = os.environ.get("XRD_READ_ENDPOINT", DEFAULT_XRD_ENDPOINT)
xrdDiscoveryEndpoint = os.environ.get("XRD_DISCOVERY_ENDPOINT", xrdReadEndpoint)
remoteIO = {
    "inputAccessMode": "xrootd",
    "xrdReadEndpoint": xrdReadEndpoint,
    "xrdDiscoveryEndpoint": xrdDiscoveryEndpoint,
    "xrdWriteEndpoint": os.environ.get("XRD_WRITE_ENDPOINT"),
    "stageInScratch": None,
    "stageInCleanup": "on-success",
    "preserveStageInOnFailure": True,
    "existingOutputPolicy": os.environ.get("EXISTING_OUTPUT_POLICY", "fail"),
    "remoteCommandTimeout": int(os.environ.get("REMOTE_COMMAND_TIMEOUT", "120")),
    "remoteTransferRetries": int(os.environ.get("REMOTE_TRANSFER_RETRIES", "2")),
}

# FNAL worker containers do not mount the LPC ``/uscms_data`` checkout.  Batch
# production therefore uses mkShapesRDF's deterministic source package while
# local pilots keep using the live checkout.  Packaging changes only the code
# delivery mechanism: event inputs are still streamed directly over XRootD.
_runtime_package_value = os.environ.get("CONDOR_RUNTIME_PACKAGE", "0").strip().lower()
if _runtime_package_value not in {"0", "1", "false", "true", "no", "yes"}:
    raise ValueError(
        "CONDOR_RUNTIME_PACKAGE must be one of 0/1, false/true, or no/yes"
    )
condorRuntimePackage = _runtime_package_value in {"1", "true", "yes"}
condorRuntimePackageName = os.environ.get(
    "CONDOR_RUNTIME_PACKAGE_NAME", "mkshapesrdf_runtime.tgz"
)
condorRuntimeIncludes = []
condorRuntimeSetup = (
    [
        "source /cvmfs/sft.cern.ch/lcg/views/LCG_109/"
        "x86_64-el9-gcc13-opt/setup.sh"
    ]
    if condorRuntimePackage
    else []
)
useX509Proxy = True
mountEOS = []
useEOSUserOutput = False

imports = ["os", "math", ("collections", "OrderedDict"), "ROOT"]
filesToExec = [
    pairingConfigFile,
    samplesFile,
    aliasesFile,
    cutsFile,
    variablesFile,
    plotFile,
    structureFile,
]

varsToKeep = [
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
    "mountEOS",
    "remoteIO",
    "condorRuntimePackage",
    "condorRuntimePackageName",
    "condorRuntimeIncludes",
    "condorRuntimeSetup",
    "useX509Proxy",
    "useEOSUserOutput",
    "PAIRING_SAMPLE_INVENTORY",
    "PAIRING_ESTIMATED_JOBS",
]

batchVars = varsToKeep[varsToKeep.index("samples") :]
varsToKeep += ["plotPath"]
