"""Common ZH4l catalogue with the closure study's uncorrected base domain."""

from pathlib import Path

from common.eras import *  # noqa: F403

FAMILY_DIR = Path(globals().get("FAMILY_DIR", Path(__file__).resolve().parent.parent))
CLOSURE_SAMPLE_PROFILE = str(globals().get("CLOSURE_SAMPLE_PROFILE", "full"))
SAMPLE_PROFILE = "presentation"
if CLOSURE_SAMPLE_PROFILE == "major":
    _cfg = load_full_config()  # noqa: F405
    _era, _era_cfg, _ = load_selected_era()  # noqa: F405
    _scope = resolve_sample_selection(_era_cfg, _cfg, SAMPLE_PROFILE)  # noqa: F405
    _owners = {
        sample: group
        for group, definition in _cfg["plot_groups"].items()
        for sample in definition.get("samples", ())
    }
    _major = {"DY", "ZZ", "WZ", "Vg", "VgS", "top", "ttV_tZ"}
    SAMPLE_FILTER = ",".join(
        sample for sample in _scope["active_output_names"]
        if sample == "DATA" or _owners.get(sample) in _major
    )
CORRECTION_WEIGHT = "puWeight"
exec((FAMILY_DIR / "common" / "catalog.py").read_text(), globals(), globals())
CLOSURE_SAMPLE_INVENTORY = tuple(samples)
