import os
import sys

_this_dir = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else os.getcwd()
if _this_dir not in sys.path:
    sys.path.insert(0, _this_dir)

from mkShapesRDF.lib.search_files import SearchFiles

if (
    "load_selected_year" not in globals()
    or "resolve_data_run_tags" not in globals()
    or "resolve_tree_base_dir" not in globals()
):
    _zzcr_config_dir = os.path.abspath(
        globals().get("ZZCR_CONFIG_DIR", globals().get("folder", os.getcwd()))
    )
    exec(
        open(os.path.join(_zzcr_config_dir, "zzcr_year.py")).read(),
        globals(),
        globals(),
    )

searchFiles = SearchFiles()

redirector = ""
useXROOTD = False

limitFiles = -1

samples = {}

ZZCR_YEAR, _selected_year, _ = load_selected_year()
mcProduction = _selected_year["mc"]["production"]
mcSteps = _selected_year["mc"]["steps"]
dataReco = _selected_year["data"]["reco"]
dataSteps = _selected_year["data"]["steps"]


def _with_redirector(tree_base_dir):
    if redirector != "":
        return redirector + tree_base_dir
    return tree_base_dir


def makeMCDirectory(sample_name, var=""):
    _treeBaseDir = _with_redirector(
        resolve_tree_base_dir(_selected_year, "mc", sample_name=sample_name)
    )
    if var == "":
        return "/".join([_treeBaseDir, mcProduction, mcSteps])
    return "/".join([_treeBaseDir, mcProduction, mcSteps + "__" + var])


def makeDataDirectory(dataset_name, stream_tag):
    _treeBaseDir = _with_redirector(
        resolve_tree_base_dir(
            _selected_year,
            "data",
            sample_name=dataset_name,
            stream_name=stream_tag,
        )
    )
    return [
        "/".join([_treeBaseDir, f"{dataReco}_{stream_tag}", dataSteps]),
        "/".join([_treeBaseDir, dataReco, dataSteps]),
    ]


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


def nanoGetSampleFilesWithFallback(paths, name):
    """
    Try multiple directory layouts and return the first non-empty sample file list.

    Needed because Run3 data campaigns are not fully uniform:
      - some years use <reco>_<stream>/<steps>
      - others use <reco>/<steps>
    """
    for path in paths:
        files = searchFiles.searchFiles(path, name, redirector=redirector)
        if not files:
            continue
        if limitFiles != -1 and len(files) > limitFiles:
            print(
                f"[nanoGetSampleFiles] Found {len(files)} files for '{name}' in '{path}' (returning first {limitFiles})."
            )
            return [(name, files[:limitFiles])]
        print(f"[nanoGetSampleFiles] Found {len(files)} files for '{name}' in '{path}'.")
        return [(name, files)]

    print(
        f"[nanoGetSampleFiles] No files found for sample '{name}' in any of: {paths}."
    )
    return [(name, [])]


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
    mcDirectory = makeMCDirectory(mc_sample)
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

for data_sample in DataSamples:
    dataset = data_sample["dataset"]
    stream_tag = data_sample["stream"]
    sample_run_tags = list(dict.fromkeys(data_sample.get("runs", DataRunTags)))
    for run_tag in sample_run_tags:
        dataDirectories = makeDataDirectory(dataset, stream_tag)
        files = nanoGetSampleFilesWithFallback(dataDirectories, dataset + "_" + run_tag)
        samples["DATA"]["name"].extend(files)
        addSampleWeight(samples, "DATA", dataset + "_" + run_tag, data_sample["trigger"])
