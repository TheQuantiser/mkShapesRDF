from pathlib import Path
import runpy
import sys

import pytest


CONFIG_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = CONFIG_DIR.parents[2]
WORKSPACE_ROOT = CONFIG_DIR.parents[3]
FROZEN_LUMI_RESULTS = (
    CONFIG_DIR
    / "lumi"
    / "audits"
    / "ZZ_CR_RunStability_BCD_afa86d85_conjunction_20260818T200415Z"
    / "results"
)
for path in (str(CONFIG_DIR), str(REPO_ROOT)):
    if path not in sys.path:
        sys.path.insert(0, path)


@pytest.fixture
def load_state(monkeypatch):
    def _load(
        category="standard",
        histogram="analysis",
        year="2024",
        analysis_pass="RUN_STABILITY",
        **extra,
    ):
        values = {
            "YEAR": year,
            "ANALYSIS_PASS": analysis_pass,
            "CATEGORY_PROFILE": category,
            "HISTOGRAM_PROFILE": histogram,
            "HISTOGRAMS": "1",
            "ENABLE_SYSTEMATICS": "0",
            "RUN_STABILITY_PRODUCTION_PROFILE": "dy",
            "SELECTION_PROFILE": "dy",
            "RUN_STABILITY_REGION": "DY",
            "RUN_STABILITY_OBSERVABLES": "configured",
        }
        if analysis_pass == "RUN_STABILITY":
            values["RUN_STABILITY_LUMI_DIR"] = str(FROZEN_LUMI_RESULTS)
        values.update({key: str(value) for key, value in extra.items()})
        for key in (
            "VARIABLE_INCLUDE",
            "VARIABLE_EXCLUDE",
            "ALLOW_LARGE_PLAN",
            "MAX_CATEGORIES",
            "MAX_HISTOGRAM_ACTIONS",
            "RUN_STABILITY_REGION",
            "RUN_STABILITY_OBSERVABLES",
            "RUN_STABILITY_CATEGORIES",
            "RUN_STABILITY_LUMI_DIR",
            "SELECTION_PROFILE",
            "RUN_STABILITY_PRODUCTION_PROFILE",
        ):
            monkeypatch.delenv(key, raising=False)
        for key, value in values.items():
            monkeypatch.setenv(key, value)
        state = {
            "CONFIG_DIR": str(CONFIG_DIR),
            "HISTOGRAMS": True,
            "ANALYSIS_PASS": analysis_pass,
            "RUN_STABILITY_REGION": values.get("RUN_STABILITY_REGION", "DY"),
            "YEAR": year,
        }
        filenames = ["year_config.py", "selection_config.py", "category_config.py"]
        if analysis_pass == "RUN_STABILITY":
            filenames.append("run_stability_config.py")
        filenames.extend(("cuts.py", "variables.py"))
        for filename in filenames:
            state.update(runpy.run_path(str(CONFIG_DIR / filename), init_globals=state))
            if filename == "year_config.py":
                _, selected_year, _ = state["load_selected_year"]()
                state["_selected_year"] = selected_year
                state["lumi"] = selected_year["lumi_fb"]
        return state

    return _load
