"""Instantiate only common nominal ZH4l physics aliases for ZZCR."""

from pathlib import Path

from common.corrections import build_correction_aliases
from common.eras import load_selected_era
from common.objects import build_object_aliases
from common.observables import build_observable_aliases

FAMILY_DIR = Path(globals().get("FAMILY_DIR", Path(__file__).resolve().parent.parent))
_, ERA_CONFIG, _ = load_selected_era()
AVAILABLE_BRANCHES = globals().get("AVAILABLE_BRANCHES")
aliases, SELECTED_WPS = build_object_aliases(ERA_CONFIG, FAMILY_DIR, AVAILABLE_BRANCHES)
aliases.update(build_observable_aliases())
aliases.update(
    build_correction_aliases(
        ERA_CONFIG, FAMILY_DIR, globals().get("samples", {}), SELECTED_WPS,
        systematics=globals().get("ENABLE_SYSTEMATICS", True),
    )
)
