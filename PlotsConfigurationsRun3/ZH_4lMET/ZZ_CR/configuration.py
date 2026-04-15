"""
ZH(H->WW) -> 4l + MET ZZ control region configuration.
"""

import os
import getpass
from datetime import datetime, timezone

if "load_selected_year" not in globals():
    exec(open("zzcr_year.py").read(), globals(), globals())

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
