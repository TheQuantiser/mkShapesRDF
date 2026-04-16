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
ZZCR_YEAR = "2024"
os.environ["ZZCR_YEAR"] = ZZCR_YEAR
_, _selected_year, _ = load_selected_year()

tag = f"ZH_4lMET_ZZCR_{ZZCR_YEAR}"
tag = f"{tag}_{datetime.now(timezone.utc).strftime('%Y%m%d')}"

runnerFile = "default"

outputFile = "mkShapes__{}.root".format(tag)

useEOSUserOutput = True
useX509Proxy =True

_user = os.environ.get("USER", getpass.getuser())
eosUserOutputFolder = (
    "/eos/cms/store/user/{}/mkShapesRDF_rootfiles/{}/rootFile/".format(_user, tag)
)

# xrdRedirector = "eoscms.cern.ch"
xrdRedirector = "cmseos.fnal.gov"

localJobDir = os.path.join("jobs", tag)

outputFolder = eosUserOutputFolder if useEOSUserOutput else os.path.join(localJobDir, "rootFiles")

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

jdlconfigfile = "jdl_dict_zzcr.py" if useX509Proxy else ""

varsToKeep = [
    "useEOSUserOutput",
    "useX509Proxy",
    "xrdRedirector",
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

varsToKeep += ["plotPath"]
