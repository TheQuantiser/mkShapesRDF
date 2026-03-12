"""
ZH(H->WW) -> 4l + MET ZZ control region configuration.
"""

tag = "ZH_4lMET_ZZCR_2024v15"

runnerFile = "default"

outputFile = "mkShapes__{}.root".format(tag)

outputFolder = "rootFiles/ZH_4lMET/rootFiles__{}".format(tag)

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
]

batchVars = varsToKeep[varsToKeep.index("samples") :]

varsToKeep += ["plotPath"]
