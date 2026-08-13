"""mkShapesRDF entry point for the compact all-era closure bridge."""

import os
from datetime import datetime, timezone
from pathlib import Path


CONFIG_DIR = Path(__file__).resolve().parent
if str(CONFIG_DIR) not in os.sys.path:
    os.sys.path.insert(0, str(CONFIG_DIR))
# The vendored alias graph appends ``PlotsConfigurationsRun3/...`` to
# this base.  Set it explicitly because mkShapesRDF's legacy global named
# ``configurations`` otherwise points at PlotsConfigurationsRun3 itself.
os.environ.setdefault("CONFIG_INCLUDE_BASE", str(CONFIG_DIR.parents[2]))

from study_config import SUPPORTED_ERAS  # noqa: E402

YEAR = os.environ.get("YEAR", "2024")
if YEAR not in SUPPORTED_ERAS:
    raise ValueError(f"Unsupported YEAR={YEAR}; available={SUPPORTED_ERAS}")
os.environ["YEAR"] = YEAR
ANALYSIS_PASS = "ALL"
ENABLE_SYSTEMATICS = False
HISTOGRAMS = True
CLOSURE_PROFILE = os.environ.get("CLOSURE_PROFILE", "default").strip().lower()
CLOSURE_SAMPLE_PROFILE = os.environ.get("CLOSURE_SAMPLE_PROFILE", "full").strip().lower()
if CLOSURE_PROFILE not in ("default", "focused_cross"):
    raise ValueError("CLOSURE_PROFILE must be default or focused_cross")
if CLOSURE_SAMPLE_PROFILE not in ("major", "full"):
    raise ValueError("CLOSURE_SAMPLE_PROFILE must be major or full")
os.environ["ANALYSIS_PASS"] = ANALYSIS_PASS
os.environ["ENABLE_SYSTEMATICS"] = "0"
os.environ["SAMPLE_PROFILE"] = "presentation"

exec(compile((CONFIG_DIR / "year_config.py").read_text(), str(CONFIG_DIR / "year_config.py"), "exec"), globals(), globals())
_, _selected_year, _ = load_selected_year()
lumi = float(_selected_year["lumi_fb"])

campaign = os.environ.get("CLOSURE_CAMPAIGN", datetime.now(timezone.utc).strftime("closure_%Y%m%d_%H%M%S")).strip()
if not campaign or "/" in campaign:
    raise ValueError("CLOSURE_CAMPAIGN must be a nonempty path-safe token")
tag = f"DYZZClosure_{YEAR}_{CLOSURE_SAMPLE_PROFILE}_{CLOSURE_PROFILE}_{campaign}"
runnerFile = "closure_runner.py"
outputFile = f"mkShapes__{tag}.root"
outputFolder = os.environ.get("CLOSURE_OUTPUT_FOLDER", f"rootFiles/{campaign}/{YEAR}")
batchFolder = os.environ.get("CLOSURE_BATCH_FOLDER", f"condor/{campaign}/{YEAR}")
configsFolder = os.environ.get("CLOSURE_CONFIGS_FOLDER", f"configs/{campaign}/{YEAR}")
plotPath = os.environ.get("CLOSURE_PLOT_PATH", f"plots/{campaign}/{YEAR}")

xrdReadEndpoint = os.environ.get("XRD_READ_ENDPOINT", "root://eoscms.cern.ch")
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

_package = os.environ.get("CONDOR_RUNTIME_PACKAGE", "0").strip().lower()
if _package not in ("0", "1", "false", "true", "no", "yes"):
    raise ValueError("CONDOR_RUNTIME_PACKAGE must be boolean")
condorRuntimePackage = _package in ("1", "true", "yes")
condorRuntimePackageName = os.environ.get("CONDOR_RUNTIME_PACKAGE_NAME", "mkshapesrdf_runtime.tgz")
condorRuntimeIncludes = []
condorRuntimeSetup = (["source /cvmfs/sft.cern.ch/lcg/views/LCG_109/x86_64-el9-gcc13-opt/setup.sh"] if condorRuntimePackage else [])
useX509Proxy = True
useEOSUserOutput = False
mountEOS = []
nuisances = {}

imports = ["os", "math", ("collections", "OrderedDict"), "ROOT"]
filesToExec = ["year_config.py", "samples.py", "selection_config.py", "aliases.py", "cuts.py", "variables.py", "plot.py", "nuisances_nominal.py", "structure.py"]
varsToKeep = [
    "batchVars", "outputFolder", "batchFolder", "configsFolder", "outputFile", "runnerFile", "tag",
    "samples", "aliases", "variables", "CATEGORY_VARIABLES", "HISTOGRAM_ACTION_COUNT", "CATEGORY_METADATA",
    ("cuts", {"cuts": "cuts", "preselections": "preselections"}),
    ("plot", {"plot": "plot", "groupPlot": "groupPlot", "legend": "legend"}),
    "nuisances", "structure", "lumi", "mountEOS", "remoteIO", "condorRuntimePackage",
    "condorRuntimePackageName", "condorRuntimeIncludes", "condorRuntimeSetup", "useX509Proxy", "useEOSUserOutput",
    "CLOSURE_SAMPLE_PROFILE", "CLOSURE_SAMPLE_INVENTORY", "CLOSURE_PROFILE", "YEAR",
]
batchVars = varsToKeep[varsToKeep.index("samples"):]
varsToKeep += ["plotPath"]
