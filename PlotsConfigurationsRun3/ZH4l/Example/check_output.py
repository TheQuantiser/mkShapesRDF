"""Reopen a combined Example output and compare its event trees to every histogram."""

import argparse
import math
from pathlib import Path
import sys

import ROOT

from mkShapesRDF.shapeAnalysis.ConfigLib import ConfigLib

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from common.eras import load_selected_era, source_normalization  # noqa: E402


def close(actual, expected):
    # Tree observables/SFs include float32 values; histograms accumulate doubles.
    return math.isclose(actual, expected, rel_tol=1.0e-6, abs_tol=1.0e-9)


def check(config_path, output_path, *, check_inputs=False):
    config = ConfigLib.loadPickle(str(config_path), {})
    variables = config["variables"]
    if not any("tree" in value for value in variables.values()) or not any(
        "name" in value for value in variables.values()
    ):
        raise ValueError(
            "This check requires an Example configuration compiled with mode=both"
        )
    output = ROOT.TFile.Open(str(output_path))
    if not output or output.IsZombie():
        raise OSError(output_path)
    inputs = {}
    comparisons = 0
    memberships = {}
    try:
        for region in config["cuts"]["cuts"]:
            for sample, sample_config in config["samples"].items():
                tree = output.Get(f"trees/{region}/{sample}/Events")
                assert tree, (region, sample, "missing tree")
                assert tree.GetLeaf("event").GetTypeName() in {"Long64_t", "ULong64_t"}
                assert tree.GetLeaf("source_entry").GetTypeName() == "ULong64_t"
                allowed = {
                    uri for component in sample_config["name"] for uri in component[1]
                }
                histograms = {}
                for name, definition in variables.items():
                    if "tree" in definition or region not in definition["cuts"]:
                        continue
                    histogram = output.Get(f"{region}/{name}/histo_{sample}")
                    assert histogram, (region, name, sample, "missing histogram")
                    reference = histogram.Clone(f"check_{comparisons}_{name}")
                    reference.SetDirectory(0)
                    reference.Reset()
                    histograms[name] = (definition, histogram, reference)
                seen, sum_weights = set(), 0.0
                for row in tree:
                    identity = (str(row.source_file), int(row.source_entry))
                    assert identity[0] in allowed and identity not in seen
                    seen.add(identity)
                    assert getattr(row, f"region_{region}_pass")
                    assert row.weight_is_valid and math.isfinite(row.weight)
                    recipe = (
                        row.weight_lepton_trigger
                        if region == "four_lepton"
                        else row.weight_nominal
                    )
                    assert close(row.weight, recipe)
                    assert close(
                        row.weight_lepton,
                        row.weight_base * row.sf_lepton_z * row.sf_lepton_x,
                    )
                    assert close(
                        row.weight_lepton_trigger, row.weight_lepton * row.sf_trigger_zx
                    )
                    assert row.weight_nominal_is_valid == row.event_pass_b_veto
                    if row.event_pass_b_veto:
                        assert close(
                            row.weight_nominal,
                            row.weight_lepton_trigger * row.sf_b_veto,
                        )
                    else:
                        assert math.isnan(row.weight_nominal)
                    assert len(set(row.z_lepton_index) | set(row.x_lepton_index)) == 4
                    assert list(row.zx_lepton_index) == list(row.z_lepton_index) + list(
                        row.x_lepton_index
                    )
                    if check_inputs:
                        _check_source(row, identity, inputs, config, sample)
                    sum_weights += row.weight
                    for definition, _, reference in histograms.values():
                        value = getattr(row, definition["name"])
                        weight_name = definition.get("regionWeights", {}).get(
                            region, definition.get("weight", "weight")
                        )
                        weight = getattr(row, weight_name)
                        for item in (
                            [value] if isinstance(value, (int, float)) else value
                        ):
                            # All example axes explicitly fold both flows. Fill at bin
                            # centers so folding also reproduces per-object sumw2.
                            index = max(
                                1,
                                min(
                                    reference.GetNbinsX(),
                                    reference.FindFixBin(float(item)),
                                ),
                            )
                            reference.Fill(reference.GetBinCenter(index), weight)
                memberships[region, sample] = seen
                for _, histogram, reference in histograms.values():
                    for index in range(histogram.GetNbinsX() + 2):
                        assert close(
                            histogram.GetBinContent(index),
                            reference.GetBinContent(index),
                        ), (region, sample, histogram.GetName(), index, "content")
                        assert close(
                            histogram.GetBinError(index) ** 2,
                            reference.GetBinError(index) ** 2,
                        ), (region, sample, histogram.GetName(), index, "sumw2")
                    comparisons += 1
                print(
                    f"{region:20s} {sample:34s} rows={tree.GetEntries():4d} sumw={sum_weights:.9g}"
                )
        for sample in config["samples"]:
            baseline = memberships["four_lepton", sample]
            veto = memberships["b_veto", sample]
            assert veto <= baseline
            children = [
                memberships[name, sample]
                for name in ("zz_control", "x_same_flavor", "x_different_flavor")
            ]
            assert all(child <= veto for child in children)
            assert sum(map(len, children)) == len(set().union(*children))
        print(
            f"Passed: {comparisons} histogram/tree bin-content and sumw2 comparisons; typed identities, weights and region membership."
        )
    finally:
        output.Close()
        for file in inputs.values():
            file.Close()


def _check_source(row, identity, inputs, config, sample):
    uri, entry = identity
    if uri not in inputs:
        inputs[uri] = ROOT.TFile.Open(uri)
        assert inputs[uri] and not inputs[uri].IsZombie()
    source = inputs[uri].Get("Events")
    assert 0 <= entry < source.GetEntries() and source.GetEntry(entry) > 0
    assert (row.run, row.luminosityBlock, row.event) == (
        source.run,
        source.luminosityBlock,
        source.event,
    )
    for position, index in enumerate(row.zx_lepton_index):
        assert row.zx_lepton_pt[position] == source.Lepton_pt[index]
        assert row.zx_lepton_pdg_id[position] == source.Lepton_pdgId[index]
    _, era, full = load_selected_era(era=config["ERA"])
    for position, index in enumerate(row.accepted_jet_index):
        assert (
            row.accepted_jet_tag[position]
            == getattr(source, "Jet_" + era["btag"]["algo"])[index]
        )
    expected_base = (
        source.XSWeight
        * source.METFilter_Common
        * source.puWeight
        * config["lumi"]
        * source_normalization(sample, era, full)
    )
    assert close(row.weight_base, expected_base)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("config", type=Path, help="Exact timestamped compiled .pkl")
    parser.add_argument("output", type=Path)
    parser.add_argument(
        "--check-inputs",
        action="store_true",
        help="Also reopen pinned sources to verify identity, object mapping and normalization",
    )
    args = parser.parse_args()
    check(args.config, args.output, check_inputs=args.check_inputs)
