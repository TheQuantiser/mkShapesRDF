import os
import sys

_this_dir = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else os.getcwd()
if _this_dir not in sys.path:
    sys.path.insert(0, _this_dir)

from mkShapesRDF.lib.search_files import SearchFiles
from zzcr_year import load_selected_year, resolve_data_run_tags

searchFiles = SearchFiles()

redirector = ""
useXROOTD = False

treeBaseDir = "/eos/cms/store/group/phys_higgs/cmshww/amassiro/HWWNano"
limitFiles = -1

samples = {}

ZZCR_YEAR, _selected_year, _ = load_selected_year()
mcProduction = _selected_year["mc"]["production"]
mcSteps = _selected_year["mc"]["steps"]
dataReco = _selected_year["data"]["reco"]
dataSteps = _selected_year["data"]["steps"]


def makeMCDirectory(var=""):
    _treeBaseDir = treeBaseDir
    if redirector != "":
        _treeBaseDir = redirector + treeBaseDir
    if var == "":
        return "/".join([_treeBaseDir, mcProduction, mcSteps])
    return "/".join([_treeBaseDir, mcProduction, mcSteps + "__" + var])


def makeDataDirectory(stream_tag):
    _treeBaseDir = treeBaseDir
    if redirector != "":
        _treeBaseDir = redirector + treeBaseDir
    return "/".join([_treeBaseDir, f"{dataReco}_{stream_tag}", dataSteps])


mcDirectory = makeMCDirectory()

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


mcCommonWeight = _selected_year["mc"].get("common_weight", "XSWeight")
for mc_sample in _selected_year["mc"]["samples"]:
    files = nanoGetSampleFiles(mcDirectory, mc_sample)
    samples[mc_sample] = {"name": files, "weight": mcCommonWeight, "FilesPerJob": 10}


DataRunTags = resolve_data_run_tags(_selected_year)
DataSamples = _selected_year["data"]["samples"]

samples["DATA"] = {
    "name": [],
    "weight": _selected_year["data"].get("common_weight", "METFilter_DATA"),
    "weights": [],
    "isData": ["all"],
    "FilesPerJob": 10,
}

for run_tag in DataRunTags:
    for data_sample in DataSamples:
        dataset = data_sample["dataset"]
        stream_tag = data_sample["stream"]
        dataDirectory = makeDataDirectory(stream_tag)
        files = nanoGetSampleFiles(dataDirectory, dataset + "_" + run_tag)
        samples["DATA"]["name"].extend(files)
        addSampleWeight(samples, "DATA", dataset + "_" + run_tag, data_sample["trigger"])
