"""Exercise summary lookups against the current executable histogram schema."""

import math
from pathlib import Path
import runpy


def test_summary_consumers_resolve_current_histograms_and_keep_json_fields(monkeypatch):
    monkeypatch.setenv("ZH4L_OUTPUT_MODE", "histograms")
    here = Path(__file__).resolve().parents[1]
    variables = runpy.run_path(str(here / "variables.py"))["variables"]
    summary = runpy.run_path(str(here / "make_summary.py"))

    class SchemaReader:
        def aggregate(self, year, baseline, variable, samples, shape, required=False):
            assert variable in variables, variable
            return [0.0] * math.prod(shape)

    reader = SchemaReader()
    inputs = {"2024": "synthetic-schema-only"}
    inventories = {"2024": {"ZH": ("ZH_Zto2L_Hto2Wto2L2Nu_M125",), "ZZ": ("ZZ",)}}
    baselines = summary["BASELINES"]
    for family in ("ZH", "ZZ"):
        rows = summary["_efficiency_rows"](
            reader, inputs, inventories, family, baselines, []
        )
        assert rows
        assert all(
            "signed_weight_efficiency" in row and "absolute_weight_efficiency" in row
            for row in rows
        )
    for function in (
        "_aggregate_metric_rows",
        "_truth_diagnostics",
        "_x_ranking",
        "_plot_data",
        "_gain_loss_rows",
    ):
        result = summary[function](reader, inputs, inventories, baselines)
        assert result is not None
