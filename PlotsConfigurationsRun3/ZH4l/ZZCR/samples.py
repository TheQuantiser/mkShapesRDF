"""ZH4l ZZCR inputs and the single selected-ZX correction domain."""

from pathlib import Path
from common.samples import materialize_catalog

FAMILY_DIR = Path(globals().get("FAMILY_DIR", Path(__file__).resolve().parent.parent))

CORRECTION_WEIGHT = "puWeight*sf_lepton_zx*sf_trigger_zx*sf_b_veto"
globals().update(
    materialize_catalog(
        CORRECTION_WEIGHT,
        remote_io=globals().get("remoteIO"),
        sample_profile=globals().get("SAMPLE_PROFILE", "full"),
        sample_filter=globals().get("SAMPLE_FILTER"),
        pinned_files=globals().get("PINNED_FILES"),
    )
)
