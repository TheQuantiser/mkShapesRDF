"""A small, bounded 2024 MC example using the shared nominal toolkit."""

import os
from datetime import datetime, timezone
from pathlib import Path

CONFIG_DIR = Path(__file__).resolve().parent
os.sys.path.insert(0, str(CONFIG_DIR.parent))

from common.eras import load_selected_era  # noqa: E402
from common.outputs import output_mode  # noqa: E402
from common.runtime import batch_runtime_from_env, remote_io_from_env  # noqa: E402

ERA, ERA_CONFIG, FULL_CONFIG = load_selected_era()
if ERA != "2024":
    raise ValueError("Example pins 2024 inputs; use ERA=2024")
if os.environ.get("ENABLE_SYSTEMATICS", "0").lower() not in {"0", "false", "no", "off"}:
    raise ValueError("Example is nominal-only; use ENABLE_SYSTEMATICS=0")
ENABLE_SYSTEMATICS = False
ZH4L_OUTPUT_MODE = output_mode()
campaign = os.environ.get(
    "ZH4L_CAMPAIGN", datetime.now(timezone.utc).strftime("example_%Y%m%d_%H%M%S")
)
if not campaign or not all(c.isalnum() or c in "_-" for c in campaign):
    raise ValueError("ZH4L_CAMPAIGN must contain only letters, digits, _ or -")
tag = f"ZH4l_Example_{ERA}_{campaign}"
lumi = float(ERA_CONFIG["lumi_fb"])
runnerFile = "runner.py"
outputFile = f"mkShapes__{tag}.root"
outputFolder = os.environ.get("ZH4L_OUTPUT_FOLDER", f"rootFiles/{campaign}")
batchFolder = f"condor/{campaign}"
plotPath = os.environ.get("ZH4L_PLOT_PATH", str(CONFIG_DIR / "plots" / campaign))
remoteIO = remote_io_from_env()
globals().update(batch_runtime_from_env())

imports = []
filesToExec = ["samples.py", "analysis.py", "nuisances.py"]
varsToKeep = [
    "batchVars",
    "tag",
    "outputFile",
    "outputFolder",
    "batchFolder",
    "runnerFile",
    "plotPath",
    "lumi",
    "ERA",
    "ENABLE_SYSTEMATICS",
    "ZH4L_OUTPUT_MODE",
    "samples",
    "aliases",
    "variables",
    ("cuts", {"cuts": "cuts", "preselections": "preselections"}),
    ("plot", {"plot": "plot", "groupPlot": "groupPlot", "legend": "legend"}),
    "structure",
    "nuisances",
    "remoteIO",
    "mountEOS",
    "useEOSUserOutput",
    "condorRuntimePackage",
    "condorRuntimePackageName",
    "condorRuntimeIncludes",
    "zh4lCommonPath",
    "condorRuntimeSetup",
    "useX509Proxy",
]
batchVars = [entry for entry in varsToKeep if entry != "batchVars"]
