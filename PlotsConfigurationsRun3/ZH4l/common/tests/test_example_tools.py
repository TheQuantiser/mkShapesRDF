"""Synthetic mechanics for the interfaces exercised by the real-input example."""

import pytest

from common.definitions import Analysis
from common.outputs import branches
from common.presets import cleanjet_source
from common.runner import RunAnalysis


def _define(ROOT, frame, aliases):
    for name, definition in aliases.items():
        for line in definition.get("linesToAdd", ()):
            assert ROOT.gInterpreter.Declare(line)
        frame = frame.Define(name, definition["expr"])
    return frame


def test_cleanjet_fields_follow_native_index_map_and_view_sort(ROOT):
    a = Analysis()
    source = cleanjet_source(a, {"btag": {"algo": "score"}})
    jets = a.view("ordered", source, order="pt")
    fields = {
        field: a.take(f"selected_{field}", jets, field)
        for field in ("pt", "jet_index", "tag", "flavor")
    }
    a.tree("events", fields, regions=[a.region("all", "true")])
    frame = ROOT.RDataFrame(1)
    for name, expression in {
        "CleanJet_pt": "ROOT::RVecF{25.f,60.f}",
        "CleanJet_jetIdx": "ROOT::RVecI{2,0}",
        "Jet_score": "ROOT::RVecF{0.1f,0.8f,0.3f}",
        "Jet_hadronFlavour": "ROOT::RVecI{5,4,0}",
    }.items():
        frame = frame.Define(name, expression)
    frame = _define(ROOT, frame, a.compile()["aliases"])
    row = frame.AsNumpy([str(column) for column in fields.values()])
    assert list(row["selected_pt"][0]) == [60.0, 25.0]
    assert list(row["selected_jet_index"][0]) == [0, 2]
    assert list(row["selected_tag"][0]) == pytest.approx([0.1, 0.3])
    assert list(row["selected_flavor"][0]) == [5, 0]


def test_composite_and_typed_exports_preserve_members_and_reject_overlap(ROOT):
    a = Analysis()
    source = a.source(
        "leptons",
        "lepton",
        {
            "pt": "pt",
            "eta": "eta",
            "phi": "phi",
            "pdg_id": "pdg",
            "electron_tight": "tight",
            "muon_tight": "tight",
        },
        lineage="synthetic",
    )
    pool = a.view("pool", source, electron_wp="tight", muon_wp="tight")
    z = a.pair("z", pool)
    x = a.pair("x", pool, exclude=z, min_pt=(10, 10))
    zx = a.combine("zx", z, x)
    overlap = a.combine("overlap", z, z)
    fields = branches(z, x, zx, overlap)
    a.tree("events", fields, regions=[a.region("all", "true")])
    frame = ROOT.RDataFrame(1)
    for name, expression in {
        "pt": "ROOT::RVecF{46.f,45.f,30.f,20.f}",
        "eta": "ROOT::RVecF{0.1f,-0.2f,0.3f,-0.4f}",
        "phi": "ROOT::RVecF{0.f,3.14f,1.f,-1.f}",
        "pdg": "ROOT::RVecI{11,-11,13,-13}",
        "tight": "ROOT::RVecB(4,true)",
    }.items():
        frame = frame.Define(name, expression)
    frame = _define(ROOT, frame, a.compile()["aliases"])
    frame = frame.Define(
        "reference_mass",
        "FourLepton::fourLeptonMassFromPairs(pt,eta,phi,pdg,z_lepton_index,x_lepton_index)",
    )
    row = frame.AsNumpy([*fields, "reference_mass"])
    assert list(row["zx_lepton_index"][0]) == [0, 1, 2, 3]
    assert row["zx_is_valid"][0]
    assert row["zx_mass"][0] == pytest.approx(row["reference_mass"][0], rel=1e-6)
    assert not row["overlap_is_valid"][0]
    assert row["overlap_mass"][0] == -999.0
    assert fields["zx_mass"] is zx.mass


def test_histogram_inherits_each_regions_total_weight(ROOT, tmp_path):
    source = tmp_path / "input.root"
    ROOT.RDataFrame(3).Define("value", "float(rdfentry_)+0.5f").Define(
        "base", "rdfentry_ == 0 ? 0.0 : (rdfentry_ == 1 ? 1.0 : -2.0)"
    ).Snapshot("Events", str(source))
    a = Analysis()
    value = a.column("observable", "value")
    raw = a.weight("weight_raw", base="1.0")
    normalized = a.weight("weight_normalized")
    regions = [
        a.region("raw", "true", weight=raw),
        a.region("normalized", "true", weight=normalized),
    ]
    a.histogram("value", value, (0, 1, 2, 3), regions=regions)
    for region in regions:
        a.tree(
            f"{region.name}_events",
            branches(value, region.weight),
            regions=[region],
            weight=region.weight,
        )
    plan = a.compile()
    assert list(plan["variables"]) == ["value", "raw_events", "normalized_events"]
    samples = {"MC": {"name": [("mc", [str(source)], "2.0")], "weight": "base"}}
    target = tmp_path / "output.root"
    RunAnalysis(
        RunAnalysis.splitSamples(samples),
        plan["aliases"],
        plan["variables"],
        {"cuts": plan["cuts"], "preselections": plan["preselections"]},
        {},
        3.0,
        outputFileMap=str(target),
    ).run()
    output = ROOT.TFile.Open(str(target))
    for region, expected in (
        ("raw", [1.0, 1.0, 1.0]),
        ("normalized", [0.0, 6.0, -12.0]),
    ):
        histogram = output.Get(f"{region}/value/histo_MC")
        tree = output.Get(f"trees/{region}/MC/Events")
        assert tree.GetEntries() == 3
        assert [float(row.weight) for row in tree] == expected
        assert [histogram.GetBinContent(i) for i in (1, 2, 3)] == expected
        assert [histogram.GetBinError(i) ** 2 for i in (1, 2, 3)] == pytest.approx(
            [w * w for w in expected]
        )
    output.Close()


@pytest.mark.parametrize("weights", [{}, {"unknown": "1.0"}])
def test_incomplete_or_unknown_region_weights_fail_before_input_read(ROOT, weights):
    with pytest.raises(ValueError, match="cover exactly"):
        RunAnalysis(
            [],
            {},
            {"x": {"name": "x", "range": (1, 0, 1), "regionWeights": weights}},
            {"cuts": {"all": "true"}, "preselections": "1"},
            {},
            1.0,
        )


def test_region_weights_resolve_native_parent_categories(ROOT, tmp_path):
    variables = {
        "x": {
            "name": "x",
            "range": (1, 0, 1),
            "cuts": ["parent"],
            "regionWeights": {"parent_a": "1.0", "parent_b": "2.0"},
        }
    }
    runner = RunAnalysis(
        [],
        {},
        variables,
        {
            "cuts": {
                "parent": {"expr": "true", "categories": {"a": "true", "b": "false"}}
            },
            "preselections": "1",
        },
        {},
        1.0,
        outputFileMap=str(tmp_path / "unused.root"),
    )
    assert "x" in runner._variables_for_cut("parent_a")
    assert "x" in runner._variables_for_cut("parent_b")


@pytest.mark.parametrize("weights", [None, {"all": None}, {"all": " "}])
def test_region_weight_expressions_are_explicit(ROOT, weights):
    with pytest.raises(ValueError, match="total-weight expressions"):
        RunAnalysis(
            [],
            {},
            {"x": {"name": "x", "regionWeights": weights}},
            {"cuts": {"all": "true"}, "preselections": "1"},
            {},
            1.0,
        )
