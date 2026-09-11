"""Leaf entry point for the shared nominal histogram/tree adapter."""

import importlib.util
from pathlib import Path
import sys

if __name__ == "__main__":
    exec(Path("script.py").read_text(), globals(), globals())
_common = Path(
    globals().get("zh4lCommonPath", Path(__file__).resolve().parent.parent / "common")
)
if "common" not in sys.modules:
    _spec = importlib.util.spec_from_file_location(
        "common", _common / "__init__.py", submodule_search_locations=[str(_common)]
    )
    _module = importlib.util.module_from_spec(_spec)
    sys.modules["common"] = _module
    _spec.loader.exec_module(_module)
from common.runner import RunAnalysis, main  # noqa: E402

__all__ = ["RunAnalysis"]

if __name__ == "__main__":
    main(globals())
