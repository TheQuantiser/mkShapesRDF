"""Common ZH4l catalogue with the closure study's uncorrected base domain."""

from pathlib import Path
import os

from common.eras import load_full_config, load_selected_era, resolve_sample_selection
from common.samples import materialize_catalog

FAMILY_DIR = Path(globals().get("FAMILY_DIR", Path(__file__).resolve().parent.parent))
CLOSURE_SAMPLE_PROFILE = str(globals().get("CLOSURE_SAMPLE_PROFILE", "full"))
SAMPLE_PROFILE = "presentation"
if CLOSURE_SAMPLE_PROFILE == "major" and not (
    globals().get("SAMPLE_FILTER") or os.environ.get("SAMPLE_FILTER")
):
    _cfg = load_full_config()
    _era, _era_cfg, _ = load_selected_era()
    _scope = resolve_sample_selection(_era_cfg, _cfg, SAMPLE_PROFILE)
    _owners = {
        sample: group
        for group, definition in _cfg["plot_groups"].items()
        for sample in definition.get("samples", ())
    }
    _major = {"DY", "ZZ", "WZ", "Vg", "VgS", "top", "ttV_tZ"}
    SAMPLE_FILTER = ",".join(
        sample
        for sample in _scope["active_output_names"]
        if sample == "DATA" or _owners.get(sample) in _major
    )
CORRECTION_WEIGHT = "puWeight"
globals().update(
    materialize_catalog(
        CORRECTION_WEIGHT,
        remote_io=globals().get("remoteIO"),
        sample_profile=SAMPLE_PROFILE,
        sample_filter=globals().get("SAMPLE_FILTER"),
        pinned_files=globals().get("PINNED_FILES"),
    )
)
CLOSURE_SAMPLE_INVENTORY = tuple(samples)
