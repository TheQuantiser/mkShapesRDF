"""Shared configuration settings; I/O and Condor remain framework services.

Executed by ConfigLib in each leaf's shared configuration namespace.
"""

import os
import re
import shlex
from pathlib import Path


def setting_bool(name, default):
    value = os.environ.get(name, str(int(default)))
    if value not in ("0", "1"):
        raise ValueError(f"{name} must be 0 or 1")
    return value == "1"


zptFamilyDir = str(Path(__file__).resolve().parent)
zptVariant = Path(configDir).name
zptSite = os.environ.get("ZPT_SITE", "lpc")
if zptSite not in ("lpc", "cern"):
    raise ValueError("ZPT_SITE must be lpc or cern")
zptCampaign = os.environ.get("ZPT_CAMPAIGN", "nominal")
if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", zptCampaign):
    raise ValueError("ZPT_CAMPAIGN must contain only letters, digits, _, . or -")

zpt = {
    "upstream": "482bac950792bf2056a414b8759576177ec0a282",
    "variant": zptVariant,
    "site": zptSite,
    "campaign": zptCampaign,
    "run_dir": os.environ.get("ZPT_RUN_DIR", ""),
    "run_mode": os.environ.get("ZPT_RUN_MODE", "direct"),
    "sample": os.environ.get("ZPT_SAMPLE", ""),
    "dataset": os.environ.get("ZPT_DATASET", ""),
    "input_file": os.environ.get("ZPT_INPUT_FILE", ""),
    "limit_files": int(
        os.environ.get(
            "ZPT_LIMIT_FILES", "2" if zptVariant.startswith("2022") else "-1"
        )
    ),
    "files_per_job": int(os.environ.get("ZPT_FILES_PER_JOB", "0")),
    "systematics": setting_bool("ZPT_SYSTEMATICS", True),
    "apply_reweight": setting_bool("ZPT_APPLY_REWEIGHT", False),
    "reweight_json": str(
        Path(
            os.environ.get("ZPT_REWEIGHT_JSON", os.path.join(configDir, "dyZpTrw.json"))
        ).resolve()
    ),
}
if zpt["limit_files"] != -1 and zpt["limit_files"] < 1:
    raise ValueError("ZPT_LIMIT_FILES must be -1 (all files) or a positive integer")
if zpt["files_per_job"] < 0:
    raise ValueError("ZPT_FILES_PER_JOB must be 0 (upstream default) or positive")
if (zpt["dataset"] or zpt["input_file"]) and not zpt["sample"]:
    raise ValueError("ZPT_DATASET/ZPT_INPUT_FILE requires one exact ZPT_SAMPLE")
if zpt["input_file"] and not zpt["dataset"]:
    raise ValueError("ZPT_INPUT_FILE requires its exact ZPT_DATASET")
if zpt["apply_reweight"] and not os.environ.get("ZPT_REWEIGHT_JSON"):
    raise ValueError(
        "Applying weights requires ZPT_REWEIGHT_JSON pointing to a reviewed fit; bundled formulas are upstream reference inputs"
    )

tag = f"ZpTreweighting_{zptVariant}_{zptCampaign}"
outputFile = f"mkShapes__{tag}.root"
outputFolder = os.environ.get("ZPT_OUTPUT", os.path.join(configDir, "rootFiles", tag))
batchFolder = os.path.join(configDir, "condor")
plotPath = os.path.join(configDir, "plots", tag)
if zpt["run_dir"]:
    zpt["run_dir"] = str(Path(zpt["run_dir"]).resolve())
    outputFolder = os.path.join(zpt["run_dir"], "rootFiles")
    batchFolder = os.path.join(zpt["run_dir"], "condor")
    configsFolder = os.path.join(zpt["run_dir"], "configs")
    plotPath = os.path.join(zpt["run_dir"], "plots")
remoteIO = {
    "inputAccessMode": "xrootd",
    "xrdDiscoveryEndpoint": "root://eoscms.cern.ch",
    "xrdReadEndpoint": "root://eoscms.cern.ch",
    "xrdWriteEndpoint": (
        "root://cmseos.fnal.gov" if zptSite == "lpc" else "root://eoscms.cern.ch"
    ),
    "remoteCommandTimeout": 60,
    "remoteTransferRetries": 0,
    "existingOutputPolicy": "fail",
}
condorRuntimePackage = zptSite == "lpc"
useX509Proxy = True
_view = os.environ.get(
    "MKSHAPESRDF_LCG_VIEW", "/cvmfs/sft.cern.ch/lcg/views/LCG_109/x86_64-el9-gcc13-opt"
)
condorRuntimeSetup = [f"source {shlex.quote(_view.rstrip('/') + '/setup.sh')}"]
if zptSite == "lpc":
    # Same trust-store setting as the established RunStability LPC preset.
    # Workers need it before the framework's voms-proxy-info validation.
    condorRuntimeSetup.append(
        "export X509_VOMS_DIR=/cvmfs/grid.cern.ch/etc/grid-security/vomsdir"
    )
condorRuntimeIncludes = [
    os.path.join(zptFamilyDir, name) for name in ("runtime.py", "finalize.py")
]


def require_payload(path):
    """Declare exact source files for the existing runtime-package relocator."""
    path = str(Path(path).resolve(strict=True))
    if not Path(path).is_file():
        raise ValueError(f"Expected a calibration file: {path}")
    if path not in condorRuntimeIncludes:
        condorRuntimeIncludes.append(path)
    return path


def fake_payloads(base, year, electron_wp, muon_wp):
    paths = []
    for wp, particle in ((muon_wp, "Muon"), (electron_wp, "Ele")):
        paths.extend(
            str(Path(base) / year / wp / f"{particle}FR_jet{pt}.root")
            for pt in (20, 30, 40)
        )
    paths.extend(
        str(Path(base) / year / wp / f"{particle}PR.root")
        for wp, particle in ((muon_wp, "Muon"), (electron_wp, "Ele"))
    )
    return paths


def resolve_samples(catalog, paths, search):
    """Select before calling SearchFiles; preserve component-specific weights."""
    selected = zpt["sample"]
    if selected and selected not in catalog:
        raise ValueError(
            f"Unknown ZPT_SAMPLE {selected!r}; choose from {list(catalog)}"
        )
    if selected:
        catalog = {selected: catalog[selected]}
    for process, sample in catalog.items():
        components = sample["name"]
        if zpt["dataset"]:
            components = [item for item in components if item[0] == zpt["dataset"]]
            if not components:
                raise ValueError(f"ZPT_DATASET {zpt['dataset']!r} is not in {process}")
        resolved = []
        for name, _, *weight in components:
            if zpt["input_file"]:
                files = [zpt["input_file"]]
            else:
                files = search.searchFiles(
                    paths[name],
                    name,
                    redirector=remoteIO["xrdDiscoveryEndpoint"],
                    read_redirector=remoteIO["xrdReadEndpoint"],
                )
            if not files:
                raise FileNotFoundError(
                    f"No files for {process}/{name} in {paths[name]}"
                )
            if zpt["limit_files"] != -1:
                files = files[: zpt["limit_files"]]
            resolved.append((name, files, *weight))
        if not resolved:
            raise ValueError(f"No components for {process}")
        sample["name"] = resolved
        if zpt["files_per_job"]:
            sample["FilesPerJob"] = zpt["files_per_job"]
    return catalog


filesToExec.append(os.path.join(zptFamilyDir, "finalize.py"))
varsToKeep += [
    "zpt",
    "remoteIO",
    "condorRuntimePackage",
    "condorRuntimeSetup",
    "condorRuntimeIncludes",
    "useX509Proxy",
]
