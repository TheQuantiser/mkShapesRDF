"""mkShapesRDF entry point for the compact all-era pairing study."""

import os
from datetime import datetime, timezone
from pathlib import Path


CONFIG_DIR = Path(__file__).resolve().parent
FAMILY_DIR = CONFIG_DIR.parent
for _path in (CONFIG_DIR, FAMILY_DIR):
    if str(_path) not in os.sys.path:
        os.sys.path.insert(0, str(_path))

from pairing_config import (  # noqa: E402
    DEFAULT_XRD_ENDPOINT,
    SUPPORTED_ERAS,
    load_pairing_year,
)


from common.eras import resolve_era  # noqa: E402
from common.runtime import batch_runtime_from_env, remote_io_from_env  # noqa: E402

ERA = resolve_era() or "2024"
if ERA not in SUPPORTED_ERAS:
    raise ValueError(f"Unsupported ERA={ERA!r}; available={list(SUPPORTED_ERAS)}")
os.environ["ERA"] = ERA
PAIRING_ERA = load_pairing_year(ERA)

PAIRING_CAMPAIGN = os.environ.get(
    "PAIRING_CAMPAIGN", datetime.now(timezone.utc).strftime("pairing_%Y%m%d_%H%M%S")
).strip()
if not PAIRING_CAMPAIGN or "/" in PAIRING_CAMPAIGN:
    raise ValueError("PAIRING_CAMPAIGN must be a nonempty path-safe name")

tag = f"ZH4l_Pairing_{ERA}_{PAIRING_CAMPAIGN}"
# The core loader applies ``strip('.py')`` instead of removing a suffix, so a
# custom runner name must not begin or end with any of those characters.
runnerFile = "runner.py"
outputFile = f"mkShapes__{tag}.root"

outputFolder = os.environ.get(
    "PAIRING_OUTPUT_FOLDER", f"rootFiles/{PAIRING_CAMPAIGN}/{ERA}"
)
batchFolder = os.environ.get(
    "PAIRING_BATCH_FOLDER", f"condor/{PAIRING_CAMPAIGN}/{ERA}"
)
configsFolder = os.environ.get(
    "PAIRING_CONFIGS_FOLDER", f"configs/{PAIRING_CAMPAIGN}/{ERA}"
)
plotPath = os.environ.get("PAIRING_PLOT_PATH", f"plots/{PAIRING_CAMPAIGN}")

lumi = PAIRING_ERA["lumi_fb"]

pairingConfigFile = "pairing_config.py"
samplesFile = "samples.py"
aliasesFile = "aliases.py"
cutsFile = "cuts.py"
variablesFile = "variables.py"
plotFile = "plot.py"
structureFile = "structure.py"

remoteIO = remote_io_from_env()
globals().update(batch_runtime_from_env())
nuisancesFile = "nuisances.py"

imports = ["os", "math", ("collections", "OrderedDict"), "ROOT"]
filesToExec = [
    pairingConfigFile,
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
