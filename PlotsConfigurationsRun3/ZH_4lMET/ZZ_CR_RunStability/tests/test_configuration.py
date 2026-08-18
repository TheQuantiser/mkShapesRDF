from pathlib import Path
import runpy

import pytest


CONFIG_DIR = Path(__file__).resolve().parents[1]


def test_unified_all_systematics_fail_closed(monkeypatch):
    monkeypatch.setenv("YEAR", "2024")
    monkeypatch.setenv("ANALYSIS_PASS", "ALL")
    monkeypatch.setenv("ENABLE_SYSTEMATICS", "1")
    monkeypatch.setenv("CATEGORY_PROFILE", "minimal")
    monkeypatch.setenv("HISTOGRAM_PROFILE", "analysis")
    with pytest.raises(ValueError, match="cannot redefine the category weight"):
        runpy.run_path(
            str(CONFIG_DIR / "configuration.py"),
            init_globals={"CONFIG_DIR": str(CONFIG_DIR)},
        )
