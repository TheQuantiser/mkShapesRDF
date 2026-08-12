"""Direct-XRootD ZH and ZZ inputs for the compact pairing study."""

import math
import os

from mkShapesRDF.lib.search_files import SearchFiles


if "load_pairing_year" not in globals():
    from pairing_config import DEFAULT_XRD_ENDPOINT, load_pairing_year


PAIRING_ERA = load_pairing_year(globals().get("ERA") or os.environ.get("ERA"))
ERA = PAIRING_ERA["era"]

filesPerJob = int(os.environ.get("FILES_PER_JOB", "10"))
limitFiles = int(os.environ.get("LIMIT_FILES_PER_SAMPLE", "-1"))
if filesPerJob < 1:
    raise ValueError("FILES_PER_JOB must be a positive integer")
if limitFiles == 0 or limitFiles < -1:
    raise ValueError("LIMIT_FILES_PER_SAMPLE must be -1 or a positive integer")

xrdReadEndpoint = os.environ.get("XRD_READ_ENDPOINT", DEFAULT_XRD_ENDPOINT).rstrip("/")
xrdDiscoveryEndpoint = os.environ.get("XRD_DISCOVERY_ENDPOINT", xrdReadEndpoint).rstrip(
    "/"
)
if not xrdReadEndpoint.startswith("root://"):
    raise ValueError(f"Invalid XRD_READ_ENDPOINT={xrdReadEndpoint!r}")
if not xrdDiscoveryEndpoint.startswith("root://"):
    raise ValueError(f"Invalid XRD_DISCOVERY_ENDPOINT={xrdDiscoveryEndpoint!r}")

searchFiles = SearchFiles()
samples = {}
PAIRING_SAMPLE_INVENTORY = {
    "era": ERA,
    "production": PAIRING_ERA["production"],
    "steps": PAIRING_ERA["steps"],
    "lumi_fb": PAIRING_ERA["lumi_fb"],
    "families": {family: [] for family in ("ZH", "ZZ")},
}


def _component_directory(component):
    return "/".join(
        (
            component["tree_base_dir"].rstrip("/"),
            PAIRING_ERA["production"],
            PAIRING_ERA["steps"],
        )
    )


def _discover(component):
    source = component["source_alias"]
    directory = _component_directory(component)
    files = searchFiles.searchFiles(
        directory,
        source,
        redirector=xrdDiscoveryEndpoint,
        read_redirector=xrdReadEndpoint,
    )
    if not files:
        raise RuntimeError(
            f"ERA={ERA} found no files for source={source!r} under {directory!r}"
        )
    available_file_count = len(files)
    if limitFiles != -1:
        files = files[:limitFiles]
    if not files:
        raise RuntimeError(
            f"ERA={ERA} source={source!r} became empty after file limiting"
        )
    return list(files), directory, available_file_count


for _family in ("ZH", "ZZ"):
    for _logical_sample in PAIRING_ERA["inventory"][_family]:
        _sample_components = []
        _inventory_components = []
        for _component in PAIRING_ERA["logical_components"][_logical_sample]:
            _files, _directory, _available_file_count = _discover(_component)
            _source_norm = _component["source_normalization"]
            _component_weight = f"({_component['weight']})*({_source_norm:.16g})"
            _sample_components.append(
                (_component["source_alias"], _files, _component_weight)
            )
            _inventory_components.append(
                {
                    "source_alias": _component["source_alias"],
                    "directory": _directory,
                    "file_count": len(_files),
                    "available_file_count": _available_file_count,
                    "component_weight": _component["weight"],
                    "source_normalization": _source_norm,
                    "first_file": _files[0],
                }
            )

        samples[_logical_sample] = {
            "name": _sample_components,
            # The local runner books raw, signed, and absolute diagnostics
            # from one graph.  Keep METFilter_Common out of the core `weight`
            # column so its nonzero-weight prefilter does not erase events
            # from raw counts; StudySignedWeight applies it exactly once.
            # Keep the runner's mandatory `abs(weight)>0` prefilter neutral so
            # StudyRawWeight is a literal event count.  The signed study alias
            # applies XSWeight*puWeight*METFilter_Common exactly once; the
            # runner still folds luminosity and the component source factor
            # above into its `weight` column.
            "weight": "1.0",
            "FilesPerJob": filesPerJob,
        }
        PAIRING_SAMPLE_INVENTORY["families"][_family].append(
            {
                "logical_sample": _logical_sample,
                "components": _inventory_components,
                "file_count": sum(item["file_count"] for item in _inventory_components),
                "available_file_count": sum(
                    item["available_file_count"] for item in _inventory_components
                ),
            }
        )

if set(samples) != set(
    PAIRING_ERA["inventory"]["ZH"] + PAIRING_ERA["inventory"]["ZZ"]
):
    raise RuntimeError("Resolved samples differ from the fail-closed study inventory")

PAIRING_ESTIMATED_JOBS = sum(
    math.ceil(component["file_count"] / filesPerJob)
    for family in PAIRING_SAMPLE_INVENTORY["families"].values()
    for logical in family
    for component in logical["components"]
)

print(f"[Pairing] ERA={ERA}")
print(
    f"[Pairing] production={PAIRING_ERA['production']} "
    f"steps={PAIRING_ERA['steps']}"
)
for _family in ("ZH", "ZZ"):
    _aliases = tuple(PAIRING_ERA["inventory"][_family])
    print(f"[PairingStudy] {_family} aliases={_aliases}")
    for _logical in PAIRING_SAMPLE_INVENTORY["families"][_family]:
        _details = ", ".join(
            f"{item['source_alias']}:{item['file_count']}/"
            f"{item['available_file_count']} selected/available files "
            f"(norm={item['source_normalization']:.8g})"
            for item in _logical["components"]
        )
        print(f"[PairingStudy]   {_logical['logical_sample']}: {_details}")
print(
    f"[PairingStudy] files/job={filesPerJob}; estimated jobs={PAIRING_ESTIMATED_JOBS}"
)
