import os

from mkShapesRDF.lib.search_files import SearchFiles

searchFiles = SearchFiles()

redirector = ""
useXROOTD = False

mcProduction = "Summer24_150x_nAODv15_Full2024v15"
mcSteps = "MCl2loose2024v15__MCCorr2024v15__JERFrom23BPix__l2tight"
dataReco = "Run2024_ReRecoCDE_PromptFGHI_nAODv15_Full2024v15"
dataSteps = "DATAl2loose2024v15__l2loose"

treeBaseDir = "/eos/cms/store/group/phys_higgs/cmshww/amassiro/HWWNano"
limitFiles = -1

samples = {}


def makeMCDirectory(var=""):
    _treeBaseDir = treeBaseDir + ""
    if redirector != "":
        _treeBaseDir = redirector + treeBaseDir
    if var == "":
        return "/".join([_treeBaseDir, mcProduction, mcSteps])
    return "/".join([_treeBaseDir, mcProduction, mcSteps + "__" + var])


def makeDataDirectory(stream_tag):
    _treeBaseDir = treeBaseDir + ""
    if redirector != "":
        _treeBaseDir = redirector + treeBaseDir
    # stream_tag examples: "MuonEG", "Muon", "EGamma"
    return "/".join([_treeBaseDir, f"{dataReco}_{stream_tag}", dataSteps])


mcDirectory = makeMCDirectory()

# dataset -> stream tag used in the directory name
DATASET_STREAM = {
    "MuonEG": "MuonEG",
    "Muon0": "Muon",
    "Muon1": "Muon",
    "EGamma0": "EGamma",
    "EGamma1": "EGamma",
}


def nanoGetSampleFiles(path, name):
    files = searchFiles.searchFiles(path, name, redirector=redirector)

    if not files:
        print(
            f"[nanoGetSampleFiles] No files found for sample '{name}' under path '{path}'."
        )
        return [(name, [])]

    if limitFiles != -1 and len(files) > limitFiles:
        print(
            f"[nanoGetSampleFiles] Found {len(files)} files for '{name}' (returning first {limitFiles})."
        )
        return [(name, files[:limitFiles])]

    print(f"[nanoGetSampleFiles] Found {len(files)} files for '{name}'.")
    return [(name, files)]


def addSampleWeight(samples, sampleName, sampleNameType, weight):
    obj = list(filter(lambda k: k[0] == sampleNameType, samples[sampleName]["name"]))[0]
    samples[sampleName]["name"] = list(
        filter(lambda k: k[0] != sampleNameType, samples[sampleName]["name"])
    )
    if len(obj) > 2:
        samples[sampleName]["name"].append(
            (obj[0], obj[1], obj[2] + "*(" + weight + ")")
        )
    else:
        samples[sampleName]["name"].append((obj[0], obj[1], "(" + weight + ")"))


mcCommonWeight = "XSWeight"

files = nanoGetSampleFiles(mcDirectory, "ZZ")
samples["ZZ"] = {"name": files, "weight": mcCommonWeight, "FilesPerJob": 10}

# files = nanoGetSampleFiles(mcDirectory, "WZTo3LNu")
# samples["WZ"] = {"name": files, "weight": mcCommonWeight, "FilesPerJob": 10}

# files = (
#     nanoGetSampleFiles(mcDirectory, "DYto2E-2Jets_MLL-50")
#     + nanoGetSampleFiles(mcDirectory, "DYto2Mu-2Jets_MLL-50")
#     + nanoGetSampleFiles(mcDirectory, "DYto2Tau-2Jets_MLL-50")
# )
# samples["DY"] = {"name": files, "weight": mcCommonWeight, "FilesPerJob": 20}

# files = (
#     nanoGetSampleFiles(mcDirectory, "TTTo2L2Nu")
#     + nanoGetSampleFiles(mcDirectory, "TbarWplusto2L2Nu")
#     + nanoGetSampleFiles(mcDirectory, "TWminusto2L2Nu")
# )
# samples["top"] = {"name": files, "weight": mcCommonWeight, "FilesPerJob": 15}

DataRun = [
    ["C", "Run2024C-ReReco-v1"],
    ["D", "Run2024D-ReReco-v1"],
    ["E", "Run2024E-ReReco-v1"],
    # ["F", "Run2024F-Prompt-v1"],
    # ["G", "Run2024G-Prompt-v1"],
    # ["H", "Run2024H-Prompt-v1"],
    # ["I", "Run2024I-Prompt-v1"],
    # ["I", "Run2024I-Prompt-v2"],
]

DataSets = ["MuonEG", "Muon0", "Muon1", "EGamma0", "EGamma1"]
# DataSets = ["EGamma0", "EGamma1"]
DataTrig = {
    "MuonEG": "Trigger_ElMu",
    "Muon0": "!Trigger_ElMu && (Trigger_sngMu || Trigger_dblMu)",
    "Muon1": "!Trigger_ElMu && (Trigger_sngMu || Trigger_dblMu)",
    "EGamma0": "!Trigger_ElMu && !Trigger_sngMu && !Trigger_dblMu && (Trigger_sngEl || Trigger_dblEl)",
    "EGamma1": "!Trigger_ElMu && !Trigger_sngMu && !Trigger_dblMu && (Trigger_sngEl || Trigger_dblEl)",
}

samples["DATA"] = {
    "name": [],
    "weight": "METFilter_DATA",
    "weights": [],
    "isData": ["all"],
    "FilesPerJob": 10,
}

for run in DataRun:
    for dataset in DataSets:
        stream_tag = DATASET_STREAM[dataset]
        dataDirectory = makeDataDirectory(stream_tag)
        files = nanoGetSampleFiles(dataDirectory, dataset + "_" + run[1])
        samples["DATA"]["name"].extend(files)
        addSampleWeight(samples, "DATA", dataset + "_" + run[1], DataTrig[dataset])
