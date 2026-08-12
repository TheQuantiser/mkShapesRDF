"""ZH4l ZZCR inputs and the single selected-ZX correction domain."""

from pathlib import Path

FAMILY_DIR = Path(globals().get("FAMILY_DIR", Path(__file__).resolve().parent.parent))
from common.eras import *  # noqa: F403

CORRECTION_WEIGHT = "puWeight*LepSF_ZX*TriggerSF_ZX*bVetoSF"
exec((FAMILY_DIR / "common" / "catalog.py").read_text(), globals(), globals())
