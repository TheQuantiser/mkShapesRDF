#!/usr/bin/env python3
"""Extract nominal closure, transition, composition, shape, and weight metrics."""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from study_config import COMBINED_ERAS, PRIMARY_STAGES, SUPPORTED_ERAS, WEIGHT_SENTINELS, load_live_json  # noqa: E402

STAGE_ORDER = tuple(PRIMARY_STAGES)
TRANSITIONS = tuple(zip(STAGE_ORDER[:8], STAGE_ORDER[1:9])) + (
    ("D0_DY_ENRICHED_CURRENT", "D1_DY_ALL_CURRENT"),
    ("D1_DY_ALL_CURRENT", "D2_DY_ALL_EVENTPT"),
)
CORE_SHAPES = ("mZ", "ptZ", "phiEtaStar", "PV_npvsGood", "nJet30", "PuppiMET_pt", "nExtraTight10", "mX", "minMll4l", "nBLoose")
NMINUS_VARIABLE = {
    "N1_NO_XMASS": "mX",
    "N1_NO_XFLAVOR": "X_flavor_code",
    "N1_NO_BVETO": "nBLoose",
    "N1_NO_LOWMASS": "minMll4l",
    "N1_NO_FIFTHVETO": "nExtraTight10",
    "N1_NO_4LPT": "selected4lPt1",
    "N1_NO_ZWINDOW": "mZ",
}


def ratio(a, b):
    return None if b is None or abs(b) < 1e-15 else a / b


def ratio_variance(numerator, denominator, covariance=0.0):
    """Variance of numerator/denominator with an optional covariance."""
    n, d = numerator["value"], denominator["value"]
    if abs(d) < 1e-15:
        return None
    value = (
        numerator["variance"] / (d * d)
        + n * n * denominator["variance"] / (d ** 4)
        - 2.0 * n * covariance / (d ** 3)
    )
    return max(0.0, value)


def ratio_error(numerator, denominator, covariance=0.0):
    variance = ratio_variance(numerator, denominator, covariance)
    return None if variance is None else math.sqrt(variance)


def json_number(value):
    return value if value is None or math.isfinite(value) else None


def parse_inputs(specs):
    out = {}
    for spec in specs:
        if "=" not in spec:
            raise ValueError(f"Input must be ERA=ROOT, got {spec!r}")
        era, path = spec.split("=", 1)
        if era not in SUPPORTED_ERAS or era in out:
            raise ValueError(f"Invalid or duplicate era {era!r}")
        if not path.startswith("root://") and not Path(path).expanduser().is_file():
            raise FileNotFoundError(path)
        out[era] = path if path.startswith("root://") else str(Path(path).expanduser().resolve())
    return out


class Reader:
    def __init__(self, inputs):
        import ROOT
        ROOT.gROOT.SetBatch(True)
        self.ROOT = ROOT
        self.files = {}
        for era, path in inputs.items():
            handle = ROOT.TFile.Open(path, "READ")
            if not handle or handle.IsZombie():
                raise OSError(f"Cannot open {era}={path}")
            self.files[era] = handle

    def close(self):
        for handle in self.files.values():
            handle.Close()

    def histogram(self, era, stage, variable, sample):
        return self.files[era].Get(f"{stage}/{variable}/histo_{sample}")

    def samples(self, era, stage="S8_Z_BRIDGE", variable="yield"):
        directory = self.files[era].Get(f"{stage}/{variable}")
        if not directory:
            return ()
        return tuple(key.GetName()[6:] for key in directory.GetListOfKeys() if key.GetName().startswith("histo_") and not key.GetName().endswith(("Up", "Down")))

    def categories(self, era):
        return tuple(key.GetName() for key in self.files[era].GetListOfKeys())

    def variables(self, era, category):
        directory = self.files[era].Get(category)
        return tuple(key.GetName() for key in directory.GetListOfKeys()) if directory else ()

    def aggregate(self, eras, stage, variable, samples):
        values = variances = 0.0
        bins = None
        binvars = None
        edges = None
        found = False
        for era in eras:
            for sample in samples:
                h = self.histogram(era, stage, variable, sample)
                if not h:
                    continue
                found = True
                n = h.GetNbinsX()
                if bins is None:
                    bins, binvars = [0.0] * n, [0.0] * n
                    edges = [h.GetXaxis().GetBinLowEdge(i) for i in range(1, n + 1)] + [h.GetXaxis().GetBinUpEdge(n)]
                if len(bins) != n:
                    raise ValueError(f"Inconsistent bins for {stage}/{variable}")
                for i in range(1, n + 1):
                    bins[i - 1] += h.GetBinContent(i)
                    binvars[i - 1] += h.GetBinError(i) ** 2
                values += h.Integral(0, n + 1)
                variances += sum(h.GetBinError(i) ** 2 for i in range(0, n + 2))
        return None if not found else {"value": values, "variance": variances, "bins": bins, "binvars": binvars, "edges": edges}


def process_groups():
    groups = load_live_json()["plot_groups"]
    out = {
        "DY": set(groups["DY"]["samples"]), "ZZ": set(groups["ZZ"]["samples"]),
        "WZ": set(groups["WZ"]["samples"]), "Vg/VgS": set(groups["Vg"]["samples"]) | set(groups["VgS"]["samples"]),
        "top+ttV/tZ": set(groups["top"]["samples"]) | set(groups["ttV_tZ"]["samples"]),
        "WW+ggWW": set(groups["WW"]["samples"]) | set(groups["ggWW"]["samples"]),
        "VVV": set(groups["VVV"]["samples"]),
        "Higgs": set().union(*(set(groups[name]["samples"]) for name in ("HWW_signal", "HWW_contamination", "H_other"))),
    }
    return out


def chi2_metrics(data, mc):
    if not data or not mc or len(data["bins"]) != len(mc["bins"]):
        return None
    valid = [i for i in range(len(data["bins"])) if data["binvars"][i] + mc["binvars"][i] > 0]
    if not valid:
        return None
    pulls = [(data["bins"][i] - mc["bins"][i]) / math.sqrt(data["binvars"][i] + mc["binvars"][i]) for i in valid]
    absolute = sum(value * value for value in pulls)
    data_sum, mc_sum = sum(data["bins"]), sum(mc["bins"])
    shape = None
    if data_sum > 0 and mc_sum > 0:
        scale = data_sum / mc_sum
        terms = []
        for i in valid:
            variance = data["binvars"][i] + scale * scale * mc["binvars"][i]
            if variance > 0:
                terms.append((data["bins"][i] - scale * mc["bins"][i]) ** 2 / variance)
        if terms:
            shape = sum(terms) / max(1, len(terms) - 1)
    return {"absolute_chi2_ndf": absolute / max(1, len(valid)), "shape_chi2_ndf": shape, "max_abs_bin_pull": max(map(abs, pulls)), "bins_used": len(valid)}


def write_csv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = sorted(set().union(*(row.keys() for row in rows))) if rows else []
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader(); writer.writerows(rows)


def build(inputs, output):
    reader = Reader(inputs)
    try:
        combinations = {era: (era,) for era in inputs}
        combinations.update({name: tuple(era for era in eras if era in inputs) for name, eras in COMBINED_ERAS.items()})
        combinations = {name: eras for name, eras in combinations.items() if eras}
        all_samples = {era: reader.samples(era) for era in inputs}
        mc_by_era = {era: tuple(sample for sample in samples if sample != "DATA") for era, samples in all_samples.items()}
        stage_rows, transition_rows, composition_rows, shape_rows = [], [], [], []
        ablation_rows, category_rows, pt_contract_rows, distributions = [], [], [], []
        groups = process_groups()
        for label, eras in combinations.items():
            mc_samples = tuple(dict.fromkeys(sample for era in eras for sample in mc_by_era[era]))
            for stage in STAGE_ORDER:
                data = reader.aggregate(eras, stage, "yield", ("DATA",))
                mc = reader.aggregate(eras, stage, "yield", mc_samples)
                data_base = reader.aggregate(eras, stage, f"{stage}__BASE", ("DATA",))
                mc_base = reader.aggregate(eras, stage, f"{stage}__BASE", mc_samples)
                if not data or not mc or not data_base or not mc_base:
                    continue
                denom = math.sqrt(max(0.0, data["variance"] + mc["variance"]))
                stage_rows.append({
                    "era": label, "stage": stage, "N_DATA": data["value"], "N_MC": mc["value"],
                    "MC_stat": math.sqrt(max(0.0, mc["variance"])), "DATA_MC_full": ratio(data["value"], mc["value"]),
                    "DATA_MC_full_stat": ratio_error(data, mc),
                    "DATA_MC_BASE": ratio(data_base["value"], mc_base["value"]),
                    "DATA_MC_BASE_stat": ratio_error(data_base, mc_base),
                    "stat_pull": None if denom == 0 else (data["value"] - mc["value"]) / denom,
                    "nonprompt_fake_included": False,
                })
                group_yields = {}
                for group, configured in groups.items():
                    result = reader.aggregate(eras, stage, "yield", tuple(sample for sample in mc_samples if sample in configured))
                    group_yields[group] = result["value"] if result else 0.0
                total = sum(group_yields.values())
                for group, value in group_yields.items():
                    composition_rows.append({"era": label, "stage": stage, "process_group": group, "yield": value, "fraction": ratio(value, total), "non_DY_prompt_gt_10pct": bool(group != "DY" and total and value / total > .1), "fake_limitation_flag": stage in ("S4_NO_BVETO", "S5_NO_LOWMASS", "S6_NO_FIFTHVETO", "S7_FOURL_BRIDGE", "S8_Z_BRIDGE")})
                for variable in CORE_SHAPES:
                    dshape = reader.aggregate(eras, stage, variable, ("DATA",))
                    mcshape = reader.aggregate(eras, stage, variable, mc_samples)
                    metric = chi2_metrics(dshape, mcshape)
                    if metric:
                        shape_rows.append({"era": label, "stage": stage, "variable": variable, **metric})
                        distributions.append({"era": label, "category": stage, "variable": variable, "edges": dshape["edges"], "data": dshape["bins"], "data_variance": dshape["binvars"], "mc": mcshape["bins"], "mc_variance": mcshape["binvars"]})
            categories = tuple(dict.fromkeys(category for era in eras for category in reader.categories(era)))
            for category in categories:
                variables = tuple(dict.fromkeys(variable for era in eras for variable in reader.variables(era, category)))
                preferred = NMINUS_VARIABLE.get(category)
                variable = preferred if preferred in variables else next(
                    (name for name in ("yield", "mZ", "ptZ", "mX", *variables) if name in variables),
                    None,
                )
                if variable is None:
                    continue
                data = reader.aggregate(eras, category, variable, ("DATA",))
                mc = reader.aggregate(eras, category, variable, mc_samples)
                if data and mc:
                    category_rows.append({"era": label, "category": category, "source_variable": variable, "N_DATA": data["value"], "N_MC": mc["value"], "DATA_MC": ratio(data["value"], mc["value"])})
                    if category.startswith("N1_"):
                        distributions.append({"era": label, "category": category, "variable": variable, "edges": data["edges"], "data": data["bins"], "data_variance": data["binvars"], "mc": mc["bins"], "mc_variance": mc["binvars"]})
            stage_lookup = {(row["stage"]): row for row in stage_rows if row["era"] == label}
            for tight, loose in TRANSITIONS:
                dt = reader.aggregate(eras, tight, f"{tight}__BASE", ("DATA",)); dl = reader.aggregate(eras, loose, f"{loose}__BASE", ("DATA",))
                mt = reader.aggregate(eras, tight, f"{tight}__BASE", mc_samples); ml = reader.aggregate(eras, loose, f"{loose}__BASE", mc_samples)
                if not all((dt, dl, mt, ml)):
                    continue
                ed, em = ratio(dt["value"], dl["value"]), ratio(mt["value"], ml["value"])
                kappa = None if ed is None or em is None else ratio(ed, em)
                ed_variance = ratio_variance(dt, dl, dt["variance"])
                em_variance = ratio_variance(mt, ml, mt["variance"])
                kappa_variance = None
                if kappa is not None and ed and em and ed_variance is not None and em_variance is not None:
                    kappa_variance = kappa * kappa * (ed_variance / (ed * ed) + em_variance / (em * em))
                transition_rows.append({
                    "era": label, "tight": tight, "loose": loose,
                    "epsilon_DATA": ed,
                    "epsilon_DATA_stat": None if ed_variance is None else math.sqrt(ed_variance),
                    "epsilon_MC_BASE": em,
                    "epsilon_MC_BASE_stat": None if em_variance is None else math.sqrt(em_variance),
                    "kappa": kappa,
                    "kappa_stat": None if kappa_variance is None else math.sqrt(max(0.0, kappa_variance)),
                    "covariance_model": "Nested counts: Cov(tight,loose)=sumw2(tight); DATA uses unit-weight sumw2",
                })
            for stage in WEIGHT_SENTINELS:
                data = reader.aggregate(eras, stage, "yield", ("DATA",))
                for step, variable in (("base", f"{stage}__BASE"), ("selected_lepton", f"{stage}__ABL_LEP"), ("selected_lepton_trigger", f"{stage}__ABL_LEP_TRIG"), ("full", f"{stage}__ABL_FULL")):
                    mc = reader.aggregate(eras, stage, variable, mc_samples)
                    if data and mc:
                        ablation_rows.append({"era": label, "stage": stage, "step": step, "MC_yield": mc["value"], "DATA_MC": ratio(data["value"], mc["value"])})
            for scope, both_category, current_only_category, event_only_category in (
                ("enriched", "D0_DY_ENRICHED_CURRENT", "PT_ENRICHED_CURRENT_ONLY", "PT_ENRICHED_EVENTPT_ONLY"),
                ("broad", "D1_DY_ALL_CURRENT", "PT_BROAD_CURRENT_ONLY", "PT_BROAD_EVENTPT_ONLY"),
            ):
                populations = {}
                for population, category in (
                    ("both", both_category),
                    ("current_only", current_only_category),
                    ("eventPt_only", event_only_category),
                ):
                    dpop = reader.aggregate(eras, category, "mZ", ("DATA",))
                    mpop = reader.aggregate(eras, category, "mZ", mc_samples)
                    if dpop and mpop:
                        populations[population] = (dpop, mpop)
                        pt_contract_rows.append({
                            "era": label, "scope": scope, "population": population,
                            "N_DATA": dpop["value"], "N_MC": mpop["value"],
                            "DATA_MC": ratio(dpop["value"], mpop["value"]),
                            "DATA_MC_stat": ratio_error(dpop, mpop),
                        })
                if set(populations) == {"both", "current_only", "eventPt_only"}:
                    for sample_kind, index in (("DATA", 0), ("MC", 1)):
                        values = {name: pair[index]["value"] for name, pair in populations.items()}
                        union = sum(values.values())
                        migrated = values["current_only"] + values["eventPt_only"]
                        pt_contract_rows.append({
                            "era": label, "scope": scope, "population": "migration_fraction",
                            "sample_kind": sample_kind, "N_union": union,
                            "N_migrated": migrated, "fraction_migrated": ratio(migrated, union),
                        })
        output.mkdir(parents=True, exist_ok=True)
        write_csv(output / "stage_metrics.csv", stage_rows)
        write_csv(output / "transitions.csv", transition_rows)
        write_csv(output / "process_composition.csv", composition_rows)
        write_csv(output / "shape_metrics.csv", shape_rows)
        write_csv(output / "weight_ablation.csv", ablation_rows)
        write_csv(output / "category_metrics.csv", category_rows)
        write_csv(output / "pt_contract_metrics.csv", pt_contract_rows)
        (output / "distributions.json").write_text(json.dumps(distributions, indent=2, sort_keys=True, allow_nan=False) + "\n")
        metadata = {"inputs": inputs, "eras_and_combinations": combinations, "nonprompt_fake_background_included": False, "statement": "Nonprompt/fake background is not included.", "statistical_scope": "nominal/stat-only; no systematic-significance p-values"}
        (output / "summary_metadata.json").write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n")
        return metadata
    finally:
        reader.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("inputs", nargs="+", help="ERA=merged.root")
    parser.add_argument("--output", type=Path, default=HERE / "summary")
    args = parser.parse_args()
    build(parse_inputs(args.inputs), args.output)
    print(f"Wrote closure summaries to {args.output}")
    print("Nonprompt/fake background is not included.")


if __name__ == "__main__":
    main()
