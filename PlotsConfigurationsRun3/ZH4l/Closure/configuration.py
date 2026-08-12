"""mkShapesRDF entry point for the compact all-era closure bridge."""

import os
from datetime import datetime, timezone
from pathlib import Path


CONFIG_DIR = Path(__file__).resolve().parent
FAMILY_DIR = CONFIG_DIR.parent
for _path in (CONFIG_DIR, FAMILY_DIR):
    if str(_path) not in os.sys.path:
        os.sys.path.insert(0, str(_path))

from study_config import SUPPORTED_ERAS  # noqa: E402
from common.eras import load_selected_era, resolve_era  # noqa: E402
from common.runtime import batch_runtime_from_env, remote_io_from_env  # noqa: E402

ERA = resolve_era() or "2024"
if ERA not in SUPPORTED_ERAS:
    raise ValueError(f"Unsupported ERA={ERA}; available={SUPPORTED_ERAS}")
os.environ["ERA"] = ERA
ENABLE_SYSTEMATICS = False
HISTOGRAMS = True
CLOSURE_PROFILE = os.environ.get("CLOSURE_PROFILE", "default").strip().lower()
CLOSURE_SAMPLE_PROFILE = os.environ.get("CLOSURE_SAMPLE_PROFILE", "full").strip().lower()
if CLOSURE_PROFILE not in ("default", "focused_cross"):
    raise ValueError("CLOSURE_PROFILE must be default or focused_cross")
if CLOSURE_SAMPLE_PROFILE not in ("major", "full"):
    raise ValueError("CLOSURE_SAMPLE_PROFILE must be major or full")
os.environ["ENABLE_SYSTEMATICS"] = "0"
os.environ["SAMPLE_PROFILE"] = "presentation"

_, ERA_CONFIG, _ = load_selected_era()
lumi = float(ERA_CONFIG["lumi_fb"])

campaign = os.environ.get("CLOSURE_CAMPAIGN", datetime.now(timezone.utc).strftime("closure_%Y%m%d_%H%M%S")).strip()
if not campaign or "/" in campaign:
    raise ValueError("CLOSURE_CAMPAIGN must be a nonempty path-safe token")
tag = f"ZH4l_Closure_{ERA}_{CLOSURE_SAMPLE_PROFILE}_{CLOSURE_PROFILE}_{campaign}"
runnerFile = "runner.py"
outputFile = f"mkShapes__{tag}.root"
outputFolder = os.environ.get("CLOSURE_OUTPUT_FOLDER", f"rootFiles/{campaign}/{ERA}")
batchFolder = os.environ.get("CLOSURE_BATCH_FOLDER", f"condor/{campaign}/{ERA}")
configsFolder = os.environ.get("CLOSURE_CONFIGS_FOLDER", f"configs/{campaign}/{ERA}")
plotPath = os.environ.get("CLOSURE_PLOT_PATH", f"plots/{campaign}/{ERA}")

remoteIO = remote_io_from_env()
globals().update(batch_runtime_from_env())

imports = ["os", "math", ("collections", "OrderedDict"), "ROOT"]
filesToExec = ["samples.py", "aliases.py", "cuts.py", "variables.py", "plot.py", "nuisances.py", "structure.py"]
varsToKeep = [
    "batchVars", "outputFolder", "batchFolder", "configsFolder", "outputFile", "runnerFile", "tag",
    "samples", "aliases", "variables", "CATEGORY_VARIABLES", "HISTOGRAM_ACTION_COUNT", "CATEGORY_METADATA",
    ("cuts", {"cuts": "cuts", "preselections": "preselections"}),
    ("plot", {"plot": "plot", "groupPlot": "groupPlot", "legend": "legend"}),
    "nuisances", "structure", "lumi", "mountEOS", "remoteIO", "condorRuntimePackage",
    "condorRuntimePackageName", "condorRuntimeIncludes", "condorRuntimeSetup", "useX509Proxy", "useEOSUserOutput",
    "CLOSURE_SAMPLE_PROFILE", "CLOSURE_SAMPLE_INVENTORY", "CLOSURE_PROFILE", "ERA",
]
batchVars = varsToKeep[varsToKeep.index("samples"):]
varsToKeep += ["plotPath"]
