"""Ordinary mkShapesRDF configuration for the ZH4l ZZ control region."""

import os
from datetime import datetime, timezone
from pathlib import Path

CONFIG_DIR = Path(__file__).resolve().parent
FAMILY_DIR = CONFIG_DIR.parent
if str(FAMILY_DIR) not in os.sys.path:
    os.sys.path.insert(0, str(FAMILY_DIR))

from common.eras import load_selected_era  # noqa: E402
from common.runtime import batch_runtime_from_env, remote_io_from_env  # noqa: E402

ERA, ERA_CONFIG, _FULL_CONFIG = load_selected_era()
os.environ["ERA"] = ERA
_systematics_value = os.environ.get("ENABLE_SYSTEMATICS", "1").strip().lower()
if _systematics_value not in {"0", "1", "false", "true", "no", "yes", "off", "on"}:
    raise ValueError("ENABLE_SYSTEMATICS must be boolean")
ENABLE_SYSTEMATICS = _systematics_value in {"1", "true", "yes", "on"}
os.environ["ENABLE_SYSTEMATICS"] = "1" if ENABLE_SYSTEMATICS else "0"
SAMPLE_PROFILE = os.environ.get("SAMPLE_PROFILE", "full").strip().lower()
if SAMPLE_PROFILE not in {"quick", "full", "commissioning", "presentation"}:
    raise ValueError(
        "SAMPLE_PROFILE must be quick or full "
        "(legacy aliases: commissioning or presentation)"
    )
os.environ["SAMPLE_PROFILE"] = SAMPLE_PROFILE
campaign = os.environ.get(
    "ZH4L_CAMPAIGN", datetime.now(timezone.utc).strftime("zzcr_%Y%m%d_%H%M%S")
).strip()
if not campaign or "/" in campaign:
    raise ValueError("ZH4L_CAMPAIGN must be a nonempty path-safe name")

tag = f"ZH4l_ZZCR_{ERA}_{campaign}"
runnerFile = "default"
outputFile = f"mkShapes__{tag}.root"
outputFolder = os.environ.get("ZH4L_OUTPUT_FOLDER", f"rootFiles/{campaign}/{ERA}")
batchFolder = os.environ.get("ZH4L_BATCH_FOLDER", f"condor/{campaign}/{ERA}")
configsFolder = os.environ.get("ZH4L_CONFIGS_FOLDER", f"configs/{campaign}/{ERA}")
plotPath = os.environ.get("ZH4L_PLOT_PATH", f"plots/{campaign}/{ERA}")
lumi = float(ERA_CONFIG["lumi_fb"])

samplesFile = "samples.py"
aliasesFile = "aliases.py"
cutsFile = "cuts.py"
variablesFile = "variables.py"
plotFile = "plot.py"
structureFile = "structure.py"
nuisancesFile = "nuisances.py"

remoteIO = remote_io_from_env()
globals().update(batch_runtime_from_env())
imports = ["os", "math", ("collections", "OrderedDict"), "ROOT"]
filesToExec = [
    samplesFile,
    aliasesFile,
    cutsFile,
    variablesFile,
    plotFile,
    nuisancesFile,
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
    "ENABLE_SYSTEMATICS",
    "SAMPLE_PROFILE",
    "condorRuntimePackage",
    "condorRuntimePackageName",
    "condorRuntimeIncludes",
    "condorRuntimeSetup",
    "useX509Proxy",
    "useEOSUserOutput",
]
batchVars = varsToKeep[varsToKeep.index("samples") :]
varsToKeep += ["plotPath"]
