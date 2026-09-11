"""Synthetic ROOT mechanics: these tests make no physics-yield claim."""

import pytest

from common.runner import RunAnalysis
from common.outputs import branches, with_tree_outputs


def _input(ROOT, path, shift=0):
    frame = ROOT.RDataFrame(3)
    for name, expr in {
        "event": f"ULong64_t(9223372036854775808ULL + rdfentry_ + {shift}ULL)",
        "x": "float(rdfentry_) + 0.5f",
        "w": "rdfentry_ == 0 ? 0.f : (rdfentry_ == 1 ? 1.f : -2.f)",
        "sf": "2.f",
        "values": "ROOT::RVecF{float(rdfentry_)+0.25f,float(rdfentry_)+0.75f}",
    }.items():
        frame = frame.Define(name, expr)
    frame.Snapshot("Events", str(path))


@pytest.mark.parametrize("mode", ["histograms", "trees", "both"])
def test_outputs_preserve_identity_weights_and_all_chunks(ROOT, tmp_path, mode):
    files = [tmp_path / f"input{i}.root" for i in range(2)]
    for i, path in enumerate(files):
        _input(ROOT, path, 3 * i)
    samples = {
        "MC": {
            "name": [("a", [str(files[0])], "2.f"), ("b", [str(files[1])], "3.f")],
            "weight": "w",
        }
    }
    cuts = {"inclusive": "true", "empty": "false", "tail": "x > 1"}
    histograms = {
        "x": {
            "name": "x",
            "range": (3, 0.0, 3.0),
            "fold": 0,
            "weightFactor": "sf",
            "cuts": ["inclusive", "tail"],
        },
        "raw": {
            "name": "x",
            "range": (3, 0.0, 3.0),
            "fold": 0,
            "weight": "1.f",
            "cuts": ["inclusive"],
        },
        "vector": {
            "name": "values",
            "range": (3, 0.0, 3.0),
            "fold": 0,
            "weightFactor": "sf",
            "cuts": ["inclusive"],
        },
    }
    fields = branches("source", extra={"event": "event", "x": "x", "values": "values"})
    variables = with_tree_outputs(
        histograms, cuts, fields, mode=mode, tree_weight="weight*sf"
    )
    if mode != "histograms":
        variables["other"] = {
            "tree": {"x": "x+10.f", "event": "event"},
            "cuts": ["inclusive"],
            "treeName": "Other",
        }
    path = tmp_path / "output.root"
    runner = RunAnalysis(
        RunAnalysis.splitSamples(samples),
        {},
        variables,
        {"cuts": cuts, "preselections": "1"},
        {},
        2.0,
        outputFileMap=str(path),
    )
    runner.run()
    assert not list(tmp_path.glob(".zh4l-trees-*"))
    output = ROOT.TFile.Open(str(path))
    if mode != "histograms":
        tree = output.Get("trees/inclusive/MC/Events")
        assert tree and tree.GetEntries() == 6
        assert tree.GetLeaf("event").GetTypeName() == "ULong64_t"
        rows = [
            (
                int(row.event),
                str(row.source_file),
                int(row.source_entry),
                float(row.x),
                float(row.weight),
            )
            for row in tree
        ]
        assert {row[0] for row in rows} == set(range(2**63, 2**63 + 6))
        assert {(row[1], row[2]) for row in rows} == {
            (str(path), i) for path in files for i in range(3)
        }
        assert sum(row[4] for row in rows) == -20.0
        assert sum(row[4] ** 2 for row in rows) == 1040.0
        assert output.Get("trees/empty/MC/Events").GetEntries() == 0
        assert output.Get("trees/tail/MC/Events").GetEntries() == 4
        other = output.Get("trees/inclusive/MC/Other")
        assert other.GetEntries() == 6
        assert {float(row.x) for row in other} == {10.5, 11.5, 12.5}
        if mode == "both":
            histogram = output.Get("inclusive/x/histo_MC")
            for i in range(3):
                weights = [row[4] for row in rows if int(row[3]) == i]
                assert histogram.GetBinContent(i + 1) == sum(weights)
                assert histogram.GetBinError(i + 1) ** 2 == pytest.approx(
                    sum(w * w for w in weights)
                )
    if mode != "trees":
        assert output.Get("inclusive/raw/histo_MC").GetEntries() == 6
        assert output.Get("inclusive/x/histo_MC").Integral() == -20.0
        assert output.Get("inclusive/vector/histo_MC").Integral() == -40.0
        assert not output.Get("tail/raw")
    output.Close()


def test_data_applicability_does_not_require_mc_columns(ROOT, tmp_path):
    path = tmp_path / "data.root"
    ROOT.RDataFrame(2).Define("x", "1.f").Snapshot("Events", str(path))
    samples = {
        "DATA": {"name": [("data", [str(path)])], "weight": "1.f", "isData": ["all"]}
    }
    aliases = {"sf": {"expr": "missing_MC_branch", "dataExpr": "1.f"}}
    variables = {"events": {"tree": {"x": "x", "sf": "sf"}, "cuts": ["all"]}}
    output = tmp_path / "out.root"
    RunAnalysis(
        RunAnalysis.splitSamples(samples),
        aliases,
        variables,
        {"preselections": "1", "cuts": {"all": "true"}},
        {},
        100.0,
        outputFileMap=str(output),
    ).run()
    f = ROOT.TFile.Open(str(output))
    assert [
        (float(row.sf), float(row.weight)) for row in f.Get("trees/all/DATA/Events")
    ] == [(1.0, 1.0), (1.0, 1.0)]
    f.Close()


def test_multiple_files_in_one_chunk_and_independent_file_merge(ROOT, tmp_path):
    files = [tmp_path / f"source{i}.root" for i in range(2)]
    for i, path in enumerate(files):
        _input(ROOT, path, 3 * i)
    variables = {
        "events": {
            "tree": branches("source", extra={"event": "event"}),
            "cuts": ["all"],
        }
    }
    outputs = []
    for job in range(2):
        output = tmp_path / f"job{job}.root"
        sample = {
            "MC": {
                "name": [("mc", list(map(str, files)))],
                "weight": "w",
                "FilesPerJob": 2,
            }
        }
        chunks = RunAnalysis.splitSamples(sample)
        assert len(chunks) == 1
        RunAnalysis(
            chunks,
            {},
            variables,
            {
                "preselections": "true",
                "cuts": {"all": f"x {'<' if job == 0 else '>='} 1.f"},
            },
            {},
            1.0,
            outputFileMap=str(output),
        ).run()
        outputs.append(output)
    destination = tmp_path / "merged.root"
    merger = ROOT.TFileMerger()
    assert merger.OutputFile(str(destination))
    for output in outputs:
        assert merger.AddFile(str(output))
    assert merger.Merge()
    f = ROOT.TFile.Open(str(destination))
    tree = f.Get("trees/all/MC/Events")
    rows = {
        (str(row.source_file), int(row.source_entry), int(row.event)) for row in tree
    }
    assert tree.GetEntries() == 6
    assert rows == {
        (str(path), entry, 2**63 + 3 * i + entry)
        for i, path in enumerate(files)
        for entry in range(3)
    }
    f.Close()


def test_ambiguous_and_nonfinite_weights_fail(ROOT, tmp_path):
    path = tmp_path / "input.root"
    _input(ROOT, path)
    samples = RunAnalysis.splitSamples(
        {"MC": {"name": [("mc", [str(path)])], "weight": "w"}}
    )
    cuts = {"preselections": "true", "cuts": {"all": "true"}}
    histogram = {
        "x": {
            "name": "x",
            "range": (3, 0.0, 3.0),
            "weight": "1.f",
            "weightFactor": "sf",
        }
    }
    with pytest.raises(ValueError, match="one total weight"):
        RunAnalysis(samples, {}, histogram, cuts, {}, 1.0)
    histogram["x"].pop("weightFactor")
    histogram["x"]["weight"] = "std::numeric_limits<float>::quiet_NaN()"
    with pytest.raises(Exception, match="not finite"):
        RunAnalysis(
            samples,
            {},
            histogram,
            cuts,
            {},
            1.0,
            outputFileMap=str(tmp_path / "invalid.root"),
        ).run()


def test_branch_groups_allow_deliberate_replacement():
    fields = branches("identity", exclude=("event",), extra={"event": "other_event"})
    assert fields["event"] == "other_event"
    with pytest.raises(ValueError, match="already exists"):
        branches("identity", extra={"event": "other_event"})
