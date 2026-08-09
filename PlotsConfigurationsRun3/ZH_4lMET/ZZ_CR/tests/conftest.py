import os
from pathlib import Path
import runpy
import sys

import pytest


CONFIG_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = CONFIG_DIR.parents[2]
for path in (str(CONFIG_DIR), str(REPO_ROOT)):
    if path not in sys.path:
        sys.path.insert(0, path)


@pytest.fixture
def load_state(monkeypatch):
    def _load(category="minimal", histogram="analysis", year="2024", analysis_pass="ALL", **extra):
        values = {
            "YEAR": year,
            "ANALYSIS_PASS": analysis_pass,
            "CATEGORY_PROFILE": category,
            "HISTOGRAM_PROFILE": histogram,
            "HISTOGRAMS": "1",
            "ENABLE_SYSTEMATICS": "0",
        }
        values.update({key: str(value) for key, value in extra.items()})
        for key in (
            "VARIABLE_INCLUDE", "VARIABLE_EXCLUDE", "ALLOW_LARGE_PLAN",
            "MAX_CATEGORIES", "MAX_HISTOGRAM_ACTIONS",
        ):
            monkeypatch.delenv(key, raising=False)
        for key, value in values.items():
            monkeypatch.setenv(key, value)
        state = {"CONFIG_DIR": str(CONFIG_DIR), "HISTOGRAMS": True}
        for filename in ("year_config.py", "selection_config.py", "cuts.py", "variables.py"):
            state.update(runpy.run_path(str(CONFIG_DIR / filename), init_globals=state))
        return state
    return _load
