"""Orchestration regressions. Mocked commands do not test scheduling or physics."""

import importlib.util
import json
from pathlib import Path
import subprocess
from unittest.mock import Mock

import pytest


spec = importlib.util.spec_from_file_location(
    "zpt_workflow", Path(__file__).resolve().parents[1] / "workflow.py"
)
workflow = importlib.util.module_from_spec(spec)
spec.loader.exec_module(workflow)


def config(run_dir, mode="production", variant="2024_v15"):
    return {
        "zpt": {
            "run_dir": str(run_dir),
            "campaign": run_dir.name,
            "run_mode": mode,
            "variant": variant,
            "apply_reweight": False,
        },
        "tag": "test",
        "lumi": 17.3,
        "batchFolder": str(run_dir / "condor"),
        "outputFolder": str(run_dir / "rootFiles"),
        "outputFile": "merged.root",
        "plotPath": str(run_dir / "plots"),
        "samples": {"DY": {}, "DATA": {}},
    }


@pytest.mark.parametrize(
    "action,extra,mode",
    [
        ("smoke", [], "smoke"),
        ("smoke", ["--batch"], "smoke-batch"),
        ("prepare", [], "production"),
        (
            "prepare",
            ["--era", "2022", "--site", "cern", "--nominal-only"],
            "production",
        ),
    ],
)
def test_presets_ignore_stale_exports_and_never_submit(
    monkeypatch, tmp_path, action, extra, mode
):
    monkeypatch.setenv("ZPT_SAMPLE", "DATA")
    monkeypatch.setenv("ZPT_INPUT_FILE", "stale.root")
    monkeypatch.setenv("ZPT_TREE_BASE", "/wrong/campaign")
    args = workflow.parser().parse_args([action, "new", *extra])
    run_dir = tmp_path / "new"
    saved = config(run_dir, mode)

    def native(command, cwd, env):
        folder = workflow.batch_dir(saved)
        folder.mkdir(parents=True)
        (folder / "submit.jdl").write_text("queue 1")

    command = Mock(side_effect=native)
    monkeypatch.setattr(workflow, "execute", command)
    monkeypatch.setattr(
        workflow, "load_run", lambda _: (run_dir / "configs" / "one.pkl", saved)
    )
    monkeypatch.setattr(workflow, "check_root", Mock())
    workflow.create_run(args, run_dir)
    argv, cwd, env = command.call_args.args
    assert argv[:5] == ["mkShapesRDF", "-c", "1", "-o", "0"]
    assert cwd == run_dir
    assert "ZPT_TREE_BASE" not in env
    if action == "smoke":
        assert env["ZPT_INPUT_FILE"] == workflow.SMOKE_INPUT
        assert env["ZPT_SAMPLE"] == "DY"
        assert env["ZPT_LIMIT_FILES"] == env["ZPT_FILES_PER_JOB"] == "1"
        assert env["ZPT_SYSTEMATICS"] == "0"
        assert argv[argv.index("-l") + 1] == "100"
    else:
        assert "ZPT_SAMPLE" not in env and "ZPT_INPUT_FILE" not in env
        assert env["ZPT_LIMIT_FILES"] == "-1"
        assert env["ZPT_SITE"] == ("cern" if "--site" in extra else "lpc")
        assert env["ZPT_SYSTEMATICS"] == ("0" if "--nominal-only" in extra else "1")
    if mode != "smoke":
        assert argv[argv.index("-dR") + 1] == "1"
    with pytest.raises(FileExistsError):
        workflow.create_run(args, run_dir)
    assert command.call_count == 1


def test_saved_config_requires_one_pickle_and_original_run(monkeypatch, tmp_path):
    from mkShapesRDF.shapeAnalysis.ConfigLib import ConfigLib

    configs = tmp_path / "configs"
    configs.mkdir()
    with pytest.raises(ValueError, match="found 0"):
        workflow.load_run(tmp_path)
    (configs / "one.pkl").touch()
    saved = config(tmp_path)
    monkeypatch.setattr(ConfigLib, "loadPickle", lambda *_: saved)
    assert workflow.load_run(tmp_path)[1] == saved
    saved["zpt"]["run_dir"] = "/different/run"
    with pytest.raises(ValueError, match="different run"):
        workflow.load_run(tmp_path)
    (configs / "two.pkl").touch()
    with pytest.raises(ValueError, match="found 2"):
        workflow.load_run(tmp_path)


def test_submit_uses_prepared_jdl_and_prevents_duplicate(monkeypatch, tmp_path):
    import mkShapesRDF.shapeAnalysis.BatchSubmission as batch

    saved = config(tmp_path)
    folder = workflow.batch_dir(saved)
    folder.mkdir(parents=True)
    jdl = folder / "submit.jdl"
    jdl.write_text("prepared job description")
    native = Mock(
        return_value=subprocess.CompletedProcess([], 0, "123.0 - 123.2\n", "")
    )
    monkeypatch.setattr(batch, "_run_condor_submit", native)
    workflow.submit(saved)
    assert native.call_args.args[0] == ["condor_submit", "-terse", "submit.jdl"]
    assert native.call_args.kwargs["cwd"] == folder
    assert jdl.read_text() == "prepared job description"
    assert (folder / "submit.receipt.txt").read_text() == "123.0 - 123.2\n"
    with pytest.raises(ValueError, match="already attempted"):
        workflow.submit(saved)
    assert native.call_count == 1


def test_submit_timeout_preserves_unknown_attempt(monkeypatch, tmp_path):
    import mkShapesRDF.shapeAnalysis.BatchSubmission as batch

    saved = config(tmp_path)
    folder = workflow.batch_dir(saved)
    folder.mkdir(parents=True)
    (folder / "submit.jdl").touch()
    native = Mock(side_effect=subprocess.TimeoutExpired("condor_submit", 120))
    monkeypatch.setattr(batch, "_run_condor_submit", native)
    with pytest.raises(subprocess.TimeoutExpired):
        workflow.submit(saved)
    with pytest.raises(ValueError, match="already attempted"):
        workflow.submit(saved)
    assert native.call_count == 1


def test_merge_requires_all_expected_inputs_before_native_command(
    monkeypatch, tmp_path
):
    from mkShapesRDF.shapeAnalysis.runner import RunAnalysis

    saved = config(tmp_path)
    monkeypatch.setattr(
        RunAnalysis,
        "splitSamples",
        lambda _: [("DY", None, None, 0), ("DY", None, None, 1)],
    )
    check = Mock(side_effect=[None, FileNotFoundError("second job missing")])
    native = Mock()
    monkeypatch.setattr(workflow, "check_root", check)
    monkeypatch.setattr(workflow, "execute", native)
    with pytest.raises(FileNotFoundError, match="second job"):
        workflow.merge(saved, tmp_path / "one.pkl", tmp_path)
    assert [call.args[0].name for call in check.call_args_list] == [
        "merged__ALL__DY_0.root",
        "merged__ALL__DY_1.root",
    ]
    native.assert_not_called()


@pytest.mark.parametrize(
    "variant,year,kind,jets",
    [
        ("2022_v12", "2022_v12", "LO", (0, 1, 2)),
        ("2023_v12", "2023", "NLO", (0, 1, 2)),
        ("2024_v15_incl", "2024_v15", "LO", (0,)),
    ],
)
def test_extraction_keys_and_result_directory(
    monkeypatch, tmp_path, variant, year, kind, jets
):
    saved = config(tmp_path, variant=variant)
    monkeypatch.setattr(workflow, "check_root", Mock())
    seen = []

    def fake_fit(argv, cwd):
        # Formula is a software fixture, never a fit or a physics expectation.
        assert argv[argv.index("--lumi") + 1] == str(saved["lumi"])
        jet = int(argv[argv.index("-nj") + 1])
        seen.append(jet)
        path = Path(argv[argv.index("--write-json") + 1])
        data = json.loads(path.read_text()) if path.exists() else {year: {}}
        data[year][f"{kind}_{jet}j"] = "fixture_formula"
        path.write_text(json.dumps(data))

    monkeypatch.setattr(workflow, "execute", fake_fit)
    workflow.extract(saved, tmp_path)
    assert tuple(seen) == jets
    workflow.check_weights(tmp_path / "weights" / "dyZpTrw.json", variant)
    with pytest.raises(FileExistsError):
        workflow.extract(saved, tmp_path)


def test_failed_fit_cannot_report_success_or_feed_weighted_run(monkeypatch, tmp_path):
    saved = config(tmp_path)
    monkeypatch.setattr(workflow, "check_root", Mock())
    monkeypatch.setattr(
        workflow, "execute", Mock()
    )  # Upstream exits zero but writes nothing.
    with pytest.raises(ValueError, match="Fit did not write"):
        workflow.extract(saved, tmp_path)
    saved["zpt"]["run_mode"] = "smoke"
    with pytest.raises(ValueError, match="full unweighted"):
        workflow.extract(saved, tmp_path)
    path = tmp_path / "partial.json"
    path.write_text('{"2024_v15": {"LO_0j": "fixture_formula"}}')
    with pytest.raises(ValueError, match="nonempty"):
        workflow.check_weights(path, "2024_v15")


def test_smoke_plot_uses_own_config_and_populated_linear_regions(monkeypatch, tmp_path):
    saved = config(tmp_path, mode="smoke")
    saved["samples"] = {"DY": {}}
    monkeypatch.setattr(workflow, "check_root", Mock())

    def native(argv, cwd):
        assert cwd == tmp_path
        assert (cwd / "configs").is_dir()
        assert "--linearOnly" in argv
        assert argv[argv.index("--onlyCut") + 1] == "Zmm_0j,Zmm_1j,Zmm_2j"
        assert argv[argv.index("--onlyPlot") + 1] == "c"
        target = Path(saved["plotPath"])
        target.mkdir()
        (target / "test.png").touch()

    (tmp_path / "configs").mkdir()
    monkeypatch.setattr(workflow, "execute", native)
    workflow.plot(saved, tmp_path)
    with pytest.raises(FileExistsError):
        workflow.plot(saved, tmp_path)
