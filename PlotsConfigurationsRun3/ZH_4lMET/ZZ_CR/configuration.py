"""
ZH(H->WW) -> 4l + MET ZZ control region configuration.
"""

import os
import getpass

tag = "ZH_4lMET_ZZCR_2024v15_2"

runnerFile = "default"

outputFile = "mkShapes__{}.root".format(tag)

useEOSUserOutput = True
useX509Proxy =True

_user = os.environ.get("USER", getpass.getuser())
eosUserOutputFolder = (
    "/eos/cms/store/user/{}/mkShapesRDF_rootfiles/{}/rootFile/".format(_user, tag)
)

xrdRedirector = "cms-xrd-global.cern.ch"

outputFolder = (
    eosUserOutputFolder
    if useEOSUserOutput
    else "rootFiles/ZH_4lMET/rootFiles__{}".format(tag)
)

batchFolder = "condor"

configsFolder = "configs"

lumi = 26.49

aliasesFile = "aliases.py"

selectionConfigFile = "zzcr_selection_config.py"

variablesFile = "variables.py"

cutsFile = "cuts.py"

samplesFile = "samples.py"

plotFile = "plot.py"

structureFile = "structure.py"

nuisancesFile = "nuisances.py"

plotPath = "plots/{}".format(tag)

mountEOS = []

imports = ["os", "glob", ("collections", "OrderedDict"), "ROOT"]

filesToExec = [
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
