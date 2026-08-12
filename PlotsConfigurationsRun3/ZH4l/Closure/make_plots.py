#!/usr/bin/env python3
"""Render the concise closure-study deliverable from make_summary.py outputs."""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
STAGES = ("S0_ZZCR", "S1_NO_MET", "S2_NO_XMASS", "S3_NO_XFLAVOR", "S4_NO_BVETO", "S5_NO_LOWMASS", "S6_NO_FIFTHVETO", "S7_FOURL_BRIDGE", "S8_Z_BRIDGE", "D0_DY_ENRICHED_CURRENT", "D1_DY_ALL_CURRENT", "D2_DY_ALL_EVENTPT")
LIMITATION = "Nonprompt/fake background is not included."


def rows(path):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def number(value):
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if math.isfinite(result) else None


class Book:
    def __init__(self, output, formats):
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        self.plt, self.output, self.formats, self.manifest = plt, output, formats, []
        output.mkdir(parents=True, exist_ok=True)
        plt.rcParams.update({"font.size": 9, "axes.grid": True, "grid.alpha": .2, "figure.dpi": 130, "savefig.bbox": "tight"})

    def save(self, name, fig, note=""):
        files = []
        fig.text(.01, .005, LIMITATION, fontsize=7, color="#444444")
        for fmt in self.formats:
            path = self.output / f"{name}.{fmt}"
            fig.savefig(path, dpi=180 if fmt == "png" else None)
            files.append(path.name)
        self.plt.close(fig)
        self.manifest.append({"name": name, "files": files, "note": note})

    def finish(self):
        (self.output / "plot_manifest.json").write_text(json.dumps({"plots": self.manifest, "limitation": LIMITATION, "style": {"hatches": False, "palette": "tab10+Okabe-Ito-like categorical", "formats": self.formats}}, indent=2, sort_keys=True) + "\n")


def stage_plot(book, records, field, name, ylabel, era):
    selected = {row["stage"]: number(row.get(field)) for row in records if row["era"] == era}
    x, y = zip(*[(stage, selected[stage]) for stage in STAGES if selected.get(stage) is not None]) if selected else ((), ())
    fig, ax = book.plt.subplots(figsize=(10, 4.8)); ax.plot(range(len(y)), y, marker="o", color="#0072B2")
    ax.set_xticks(range(len(x)), x, rotation=45, ha="right"); ax.set_ylabel(ylabel); ax.set_title(f"{era}: {ylabel}")
    if "ratio" in name: ax.axhline(1, color="black", lw=1)
    book.save(name, fig)


def heatmap(book, matrix, xlabels, ylabels, name, title, fmt=".2f"):
    import numpy as np
    values = np.array(matrix, dtype=float)
    fig, ax = book.plt.subplots(figsize=(max(7, .7 * len(xlabels)), max(3.5, .42 * len(ylabels))))
    image = ax.imshow(values, aspect="auto", cmap="viridis")
    ax.set_xticks(range(len(xlabels)), xlabels, rotation=45, ha="right"); ax.set_yticks(range(len(ylabels)), ylabels)
    ax.set_title(title); fig.colorbar(image, ax=ax, pad=.02)
    if values.size <= 120:
        for iy in range(values.shape[0]):
            for ix in range(values.shape[1]):
                if math.isfinite(values[iy, ix]): ax.text(ix, iy, format(values[iy, ix], fmt), ha="center", va="center", fontsize=6, color="white" if values[iy, ix] < np.nanmean(values) else "black")
    book.save(name, fig)


def distribution(book, record, name):
    edges, data, mc = record["edges"], record["data"], record["mc"]
    centers = [(a + b) / 2 for a, b in zip(edges, edges[1:])]
    widths = [b - a for a, b in zip(edges, edges[1:])]
    de = [math.sqrt(max(0, value)) for value in record["data_variance"]]
    me = [math.sqrt(max(0, value)) for value in record["mc_variance"]]
    fig, (ax, ratio_ax) = book.plt.subplots(2, 1, figsize=(7, 6), gridspec_kw={"height_ratios": [3, 1]}, sharex=True)
    ax.bar(centers, mc, widths, color="#56B4E9", edgecolor="#0072B2", label=f"Prompt MC: {sum(mc):.2f} ± {math.sqrt(sum(v for v in record['mc_variance'])):.2f}")
    ax.fill_between(edges, [*(max(0, v-e) for v,e in zip(mc,me)), max(0, mc[-1]-me[-1])], [*(v+e for v,e in zip(mc,me)), mc[-1]+me[-1]], step="post", color="#999999", alpha=.35, label="MC statistical uncertainty")
    ax.errorbar(centers, data, yerr=de, fmt="o", color="black", ms=3, label=f"Data: {sum(data):.0f} ± {math.sqrt(sum(record['data_variance'])):.1f}")
    ratios = [d/m if m > 0 else float("nan") for d,m in zip(data,mc)]
    ratio_ax.axhline(1, color="black", lw=1); ratio_ax.plot(centers, ratios, "o", color="black", ms=3); ratio_ax.set_ylim(0, 2); ratio_ax.set_ylabel("Data/MC")
    ratio_ax.set_xlabel(record["variable"]); ax.set_ylabel("Events"); ax.set_title(f"{record['era']} · {record['category']}"); ax.legend(frameon=False, fontsize=7)
    book.save(name, fig, "Prompt-only nominal statistical comparison")


def build(summary, output, era, formats):
    book = Book(output, formats)
    stages = rows(summary / "stage_metrics.csv"); transitions = rows(summary / "transitions.csv")
    composition = rows(summary / "process_composition.csv"); shapes = rows(summary / "shape_metrics.csv")
    categories = rows(summary / "category_metrics.csv"); ablations = rows(summary / "weight_ablation.csv")
    stage_plot(book, stages, "DATA_MC_full", "01_data_mc_ratio_vs_stage", "DATA / prompt MC", era)
    tr = [row for row in transitions if row["era"] == era and number(row.get("kappa")) is not None]
    fig, ax = book.plt.subplots(figsize=(9,4.5)); ax.plot(range(len(tr)), [number(row["kappa"]) for row in tr], "o-", color="#D55E00"); ax.axhline(1,color="black",lw=1); ax.set_xticks(range(len(tr)), [f"{r['tight']}→{r['loose']}" for r in tr], rotation=45, ha="right"); ax.set_ylabel("κ"); ax.set_title(f"{era}: selection transition double ratios"); book.save("02_kappa_vs_transition", fig)
    comp = [row for row in composition if row["era"] == era]; groups = tuple(dict.fromkeys(row["process_group"] for row in comp)); matrix = [[number(next((r["fraction"] for r in comp if r["process_group"]==g and r["stage"]==s), "nan")) for s in STAGES] for g in groups]; heatmap(book,matrix,STAGES,groups,"03_process_composition_vs_stage",f"{era}: prompt process fractions")
    stage_plot(book, stages, "stat_pull", "04_stat_pull_vs_stage", "Stat-only pull", era)
    shp=[r for r in shapes if r["era"]==era]; variables=tuple(dict.fromkeys(r["variable"] for r in shp)); matrix=[[number(next((r["shape_chi2_ndf"] for r in shp if r["variable"]==v and r["stage"]==s),"nan")) for s in STAGES] for v in variables]; heatmap(book,matrix,STAGES,variables,"05_shape_chi2_heatmap",f"{era}: area-normalized χ²/ndf")
    extra=[r for r in categories if r["era"]==era and r["category"] in ("S8_EXTRA0","S8_EXTRA1","S8_EXTRA2P")]; fig,ax=book.plt.subplots(figsize=(6,4.5)); ax.plot([r["category"].replace("S8_","") for r in extra],[number(r["DATA_MC"]) for r in extra],"o-",color="#009E73"); ax.axhline(1,color="black",lw=1); ax.set_ylabel("DATA / prompt MC"); ax.set_title(f"{era}: extra-lepton closure at Z bridge"); book.save("06_extra_lepton_closure_at_Z_bridge",fig)
    lookup={r["stage"]:number(r["DATA_MC_full"]) for r in stages if r["era"]==era}; labels=("S8_Z_BRIDGE","D0_DY_ENRICHED_CURRENT","D1_DY_ALL_CURRENT","D2_DY_ALL_EVENTPT"); fig,ax=book.plt.subplots(figsize=(7,4.5)); ax.bar(range(len(labels)),[lookup.get(x,float('nan')) for x in labels],color=("#56B4E9","#0072B2","#E69F00","#D55E00")); ax.axhline(1,color="black",lw=1); ax.set_xticks(range(len(labels)),labels,rotation=30,ha="right"); ax.set_ylabel("DATA / prompt MC"); ax.set_title(f"{era}: current vs event-pT DY contracts"); book.save("07_current_vs_eventPt_DY_comparison",fig)
    abl=[r for r in ablations if r["era"]==era]; stages_abl=tuple(dict.fromkeys(r["stage"] for r in abl)); steps=("base","selected_lepton","selected_lepton_trigger","full"); matrix=[[number(next((r["DATA_MC"] for r in abl if r["stage"]==s and r["step"]==step),"nan")) for step in steps] for s in stages_abl]; heatmap(book,matrix,steps,stages_abl,"08_weight_ablation",f"{era}: DATA/MC through correction steps")
    distributions=json.loads((summary/"distributions.json").read_text()); selected=[r for r in distributions if r["era"]==era]
    for record in selected:
        if record["category"] in ("S0_ZZCR","S7_FOURL_BRIDGE","S8_Z_BRIDGE","D0_DY_ENRICHED_CURRENT","D1_DY_ALL_CURRENT") or record["category"].startswith("N1_"):
            distribution(book,record,f"dist_{record['category']}_{record['variable']}")
    book.finish(); print(f"Wrote {len(book.manifest)} plots to {output}"); print(LIMITATION)


def main():
    parser=argparse.ArgumentParser(); parser.add_argument("--summary",type=Path,default=HERE/"summary"); parser.add_argument("--output",type=Path,default=HERE/"plots"); parser.add_argument("--era",default="ALL_RUN3"); parser.add_argument("--formats",default="png,pdf"); args=parser.parse_args()
    build(args.summary,args.output,args.era,tuple(x.strip() for x in args.formats.split(",") if x.strip()))


if __name__=="__main__": main()
