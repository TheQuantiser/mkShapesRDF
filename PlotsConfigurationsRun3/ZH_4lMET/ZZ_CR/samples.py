import os
import sys

_this_dir = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else os.getcwd()
if _this_dir not in sys.path:
    sys.path.insert(0, _this_dir)

from mkShapesRDF.lib.remote_io import resolve_input_uri
from mkShapesRDF.lib.search_files import SearchFiles

if (
    "load_selected_year" not in globals()
    or "resolve_data_run_tags" not in globals()
    or "resolve_overlap_model" not in globals()
    or "source_normalization" not in globals()
    or "resolve_tree_base_dir" not in globals()
):
    _candidates = [
        globals().get("CONFIG_DIR"),
        globals().get("folder"),
        os.getcwd(),
        os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else None,
    ]
    _config_dir = None
    for _cand in _candidates:
        if not _cand:
            continue
        _cand_abs = os.path.abspath(_cand)
        if os.path.exists(os.path.join(_cand_abs, "year_config.py")):
            _config_dir = _cand_abs
            break
    if _config_dir is None:
        _config_dir = os.path.abspath(os.getcwd())
    exec(
        open(os.path.join(_config_dir, "year_config.py")).read(),
        globals(),
        globals(),
    )

searchFiles = SearchFiles()

_remote_io = globals().get("remoteIO", {})
_remote_discovery_enabled = _remote_io.get("inputAccessMode") in (
    "xrootd",
    "stage-in",
)
redirector = (
    _remote_io.get("xrdDiscoveryEndpoint") if _remote_discovery_enabled else ""
)
readRedirector = (
    _remote_io.get("xrdReadEndpoint") if _remote_discovery_enabled else None
)
if _remote_discovery_enabled and not redirector:
    raise RuntimeError(
        "Four-lepton remote discovery requested but xrdDiscoveryEndpoint is missing"
    )
if _remote_discovery_enabled and not readRedirector:
    raise RuntimeError(
        "Four-lepton remote discovery requested but xrdReadEndpoint is missing"
    )
useXROOTD = _remote_discovery_enabled

limitFiles = int(os.environ.get("LIMIT_FILES_PER_SAMPLE", "-1"))
filesPerJob = int(os.environ.get("FILES_PER_JOB", "10"))
if filesPerJob < 1:
    raise RuntimeError("FILES_PER_JOB must be a positive integer")

samples = {}

YEAR, _selected_year, _full_config = load_selected_year()
_resolved_overlap = resolve_overlap_model(_selected_year, _full_config)
mcProduction = _selected_year["mc"]["production"]
mcSteps = _selected_year["mc"]["steps"]
dataReco = _selected_year["data"]["reco"]
dataSteps = _selected_year["data"]["steps"]


if "WEIGHT_MODE" in os.environ or "WEIGHT_MODE" in globals():
    raise RuntimeError(
        "WEIGHT_MODE is forbidden: ANALYSIS_PASS derives the only legal "
        "selected-object and b-tag weight contract"
    )

if "analysis_pass" not in globals():
    from selection_config import analysis_pass

_PASS = analysis_pass(globals().get("ANALYSIS_PASS") or os.environ.get("ANALYSIS_PASS"))
ANALYSIS_PASS = _PASS["name"]


def _selected_correction_weight():
    """Return the correction for the explicit selected-object pass.

    Ordinary passes declare either the selected Z object (``Z``) or the
    selected Z+X objects (``ZX``).  The nominal ``ALL`` pass leaves the
    selected-object and b-veto factors to the configuration-local runner,
    which applies ``cut_weights`` after each region filter.
    """
    if _PASS["name"] == "ALL":
        return "puWeight*TriggerSF_event"
    pair = _PASS["selected_lepton_sf"]
    factors = f"puWeight*SelectedLeptonSF_{pair}*TriggerSF_event"
    if _PASS["btag_sf"]:
        factors += "*BTagVetoSF"
    return factors


_known_samples = set(_resolved_overlap["output_names"]) | {"DATA"}
SAMPLE_PROFILE = str(
    globals().get("SAMPLE_PROFILE")
    or os.environ.get("SAMPLE_PROFILE", "commissioning")
).strip().lower()
try:
    _resolved_sample_profile = resolve_sample_selection(
        _selected_year,
        _full_config,
        SAMPLE_PROFILE,
        os.environ.get("SAMPLE_FILTER") if "SAMPLE_FILTER" in os.environ else None,
    )
except ValueError as _sample_scope_error:
    raise RuntimeError(
        f"Invalid sample scope for YEAR={YEAR}: {_sample_scope_error}"
    ) from _sample_scope_error
SAMPLE_PROFILE = _resolved_sample_profile["name"]
SAMPLE_PROFILE_GROUPS = tuple(_resolved_sample_profile["plot_groups"])
SAMPLE_PROFILE_OUTPUTS = tuple(_resolved_sample_profile["output_names"])
SAMPLE_SELECTION_SOURCE = _resolved_sample_profile["selection_source"]
ACTIVE_SAMPLE_OUTPUTS = tuple(_resolved_sample_profile["active_output_names"])
_sample_filter = set(ACTIVE_SAMPLE_OUTPUTS)


def _sample_enabled(sample_name):
    return sample_name in _sample_filter


def _with_redirector(tree_base_dir):
    return tree_base_dir


def makeMCDirectory(sample_name, var=""):
    _treeBaseDir = _with_redirector(
        resolve_tree_base_dir(_selected_year, "mc", sample_name=sample_name)
    )
    if var == "":
        return "/".join([_treeBaseDir, mcProduction, mcSteps])
    return "/".join([_treeBaseDir, mcProduction, mcSteps + "__" + var])


def makeMCFriendDirectory(var):
    """Return a worker-readable friend directory for a suffix variation."""
    path = makeMCDirectory("", var)
    if not _remote_discovery_enabled:
        return path
    # Use the core URI resolver so mounted /eos/cms/store and logical /store
    # paths acquire the required double slash after the XRootD host.
    return resolve_input_uri(path, _remote_io)


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
    files = searchFiles.searchFiles(
        path,
        name,
        redirector=redirector,
        read_redirector=readRedirector,
    )

    if not files:
        if _remote_discovery_enabled:
            raise RuntimeError(
                "Remote discovery returned no files for "
                f"sample='{name}', folder='{path}', "
                f"discovery_endpoint='{redirector}', read_endpoint='{readRedirector}'"
            )
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
        files = searchFiles.searchFiles(
            path,
            name,
            redirector=redirector,
            read_redirector=readRedirector,
            missing_ok=_remote_discovery_enabled,
        )
        if not files:
            continue
        if limitFiles != -1 and len(files) > limitFiles:
            print(
                f"[nanoGetSampleFiles] Found {len(files)} files for '{name}' in '{path}' (returning first {limitFiles})."
            )
            return [(name, files[:limitFiles])]
        print(f"[nanoGetSampleFiles] Found {len(files)} files for '{name}' in '{path}'.")
        return [(name, files)]

    if _remote_discovery_enabled:
        raise RuntimeError(
            "Remote discovery returned no files in any fallback directory for "
            f"sample='{name}', folders={paths}, discovery_endpoint='{redirector}', "
            f"read_endpoint='{readRedirector}'"
        )
    print(f"[nanoGetSampleFiles] No files found for sample '{name}' in any of: {paths}.")
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
for mc_sample in _resolved_overlap["passthrough_sources"]:
    if not _sample_enabled(mc_sample):
        continue
    mcDirectory = makeMCDirectory(mc_sample)
    files = nanoGetSampleFiles(mcDirectory, mc_sample)
    _source_norm = source_normalization(mc_sample, _selected_year, _full_config)
    if _source_norm != 1.0:
        files = [(files[0][0], files[0][1], f"({_source_norm:.16g})")]
    samples[mc_sample] = {
        "name": files,
        "weight": mcCommonWeight + "*" + _selected_correction_weight(),
        "FilesPerJob": filesPerJob,
    }

for _process_name, _process_cfg in _resolved_overlap["processes"].items():
    if not _sample_enabled(_process_name):
        continue
    _components = []
    for _component in _process_cfg["components"]:
        _source_alias = _component["source_alias"]
        _files = nanoGetSampleFiles(
            makeMCDirectory(_source_alias), _source_alias
        )[0][1]
        _source_norm = source_normalization(
            _source_alias, _selected_year, _full_config
        )
        _components.append(
            (
                _source_alias,
                _files,
                f"({_component['weight']})*({_source_norm:.16g})",
            )
        )
    samples[_process_name] = {
        "name": _components,
        "weight": mcCommonWeight + "*" + _selected_correction_weight(),
        "FilesPerJob": filesPerJob,
    }


DataRunTags = resolve_data_run_tags(_selected_year)
_data_stream_filter = {
    item.strip()
    for item in os.environ.get("DATA_STREAM_FILTER", "").split(",")
    if item.strip()
}
try:
    DataSamples = resolve_data_samples(_selected_year, _data_stream_filter)
except ValueError as _data_filter_error:
    raise RuntimeError(
        f"Invalid DATA_STREAM_FILTER for YEAR={YEAR}: {_data_filter_error}"
    ) from _data_filter_error

if _sample_enabled("DATA"):
    samples["DATA"] = {
        "name": [],
        "weight": _selected_year["data"].get("common_weight", "METFilter_DATA"),
        "weights": [],
        "isData": ["all"],
        "FilesPerJob": filesPerJob,
    }

    for data_sample in DataSamples:
        dataset = data_sample["dataset"]
        stream_tag = data_sample["stream"]
        sample_run_tags = list(dict.fromkeys(data_sample.get("runs", DataRunTags)))
        for run_tag in sample_run_tags:
            dataDirectories = makeDataDirectory(dataset, stream_tag)
            files = nanoGetSampleFilesWithFallback(
                dataDirectories, dataset + "_" + run_tag
            )
            samples["DATA"]["name"].extend(files)
            addSampleWeight(
                samples, "DATA", dataset + "_" + run_tag, data_sample["trigger"]
            )


def _env_enabled(name, default=True):
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() not in ("0", "false", "no", "off")


# Per-sample input contract used to book heterogeneous theory vectors safely.
# Only one representative real file per physical source/output split is
# opened here.  The bounded matrix executes every resulting logical output;
# the full production is the stage that reads every booked input file.
AVAILABLE_BRANCHES_BY_SAMPLE = {}
THEORY_VECTOR_LENGTHS_BY_SAMPLE = {}
SYSTEMATIC_INPUT_DETAILS_BY_SAMPLE = {}
if _env_enabled(
    "INSPECT_SYSTEMATIC_BRANCHES",
    _env_enabled("ENABLE_SYSTEMATICS", True),
):
    try:
        import ROOT
    except ImportError:
        ROOT = None
    if ROOT is not None:
        for _sample_name, _sample_cfg in samples.items():
            if _sample_name == "DATA" or not _sample_cfg.get("name"):
                continue
            _component_branches = []
            _component_lengths = []
            _details = []
            for _component in _sample_cfg["name"]:
                _source_alias, _files = _component[0], _component[1]
                if not _files:
                    continue
                _source = _files[0]
                _fobj = ROOT.TFile.Open(_source)
                if not _fobj or _fobj.IsZombie():
                    raise RuntimeError(
                        f"Cannot open representative systematic-contract file {_source}"
                    )
                _tree = _fobj.Get("Events")
                if not _tree:
                    _fobj.Close()
                    raise RuntimeError(f"Missing Events tree in {_source}")
                _branches = {
                    str(branch.GetName()) for branch in _tree.GetListOfBranches()
                }
                _lengths = {}
                _entries = min(int(_tree.GetEntries()), 100)
                for _count_branch in (
                    "nPSWeight",
                    "nLHEScaleWeight",
                    "nLHEPdfWeight",
                ):
                    if _count_branch not in _branches:
                        continue
                    _values = []
                    for _entry in range(_entries):
                        _tree.GetEntry(_entry)
                        _values.append(int(getattr(_tree, _count_branch)))
                    if _values:
                        _lengths[_count_branch] = {
                            "min": min(_values),
                            "max": max(_values),
                            "entries_scanned": len(_values),
                        }
                _component_branches.append(_branches)
                _component_lengths.append(_lengths)
                _details.append(
                    {
                        "source_alias": _source_alias,
                        "representative_file": _source,
                        "branches": _branches,
                        "theory_lengths": _lengths,
                    }
                )
                _fobj.Close()
            if not _component_branches:
                continue
            _common_branches = set(_component_branches[0])
            for _branches in _component_branches[1:]:
                _common_branches &= _branches
            AVAILABLE_BRANCHES_BY_SAMPLE[_sample_name] = _common_branches
            _combined_lengths = {}
            for _count_branch in (
                "nPSWeight",
                "nLHEScaleWeight",
                "nLHEPdfWeight",
            ):
                _records = [
                    lengths[_count_branch]
                    for lengths in _component_lengths
                    if _count_branch in lengths
                ]
                if len(_records) != len(_component_lengths):
                    continue
                _combined_lengths[_count_branch] = {
                    "min": min(record["min"] for record in _records),
                    "max": max(record["max"] for record in _records),
                    "entries_scanned": sum(
                        record["entries_scanned"] for record in _records
                    ),
                    "components_scanned": len(_records),
                }
            THEORY_VECTOR_LENGTHS_BY_SAMPLE[_sample_name] = _combined_lengths
            SYSTEMATIC_INPUT_DETAILS_BY_SAMPLE[_sample_name] = _details
