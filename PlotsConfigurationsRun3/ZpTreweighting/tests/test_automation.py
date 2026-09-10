"""Controller and scheduler-state tests; no scheduler submission or physics fit."""

from copy import deepcopy
import importlib
import json
from pathlib import Path
from unittest.mock import Mock

import pytest


@pytest.fixture
def auto(monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1]))
    return importlib.import_module("automation")


@pytest.fixture
def submitted(auto, tmp_path, monkeypatch):
    folder = tmp_path / "condor" / "test"
    folder.mkdir(parents=True)
    (folder / "submit.receipt.txt").write_text(
        "123.0 - 123.1\nAttempting to submit jobs to fixture-schedd.fnal.gov\n"
    )
    config = {
        "batchFolder": str(folder.parent),
        "tag": "test",
        "zpt": {"run_dir": str(tmp_path), "site": "lpc"},
    }
    monkeypatch.setattr(
        auto,
        "job_outputs",
        lambda _: [tmp_path / "first.root", tmp_path / "second.root"],
    )
    monkeypatch.setattr(auto.wf, "check_root", Mock())
    ads = [
        {
            "ClusterId": 123,
            "ProcId": proc,
            "JobStatus": 4,
            "ExitCode": 0,
            "ExitBySignal": False,
            "Iwd": str(folder),
        }
        for proc in (0, 1)
    ]
    return config, ads


def test_wait_requires_complete_successful_history_and_reopens_outputs(
    auto, submitted, monkeypatch
):
    config, ads = submitted
    queued = [dict(ads[0], JobStatus=2)]
    query = Mock(side_effect=[queued, [], ads[:1], [], ads])
    sleep = Mock()
    monkeypatch.setattr(auto, "query_jobs", query)
    monkeypatch.setattr(auto.time, "sleep", sleep)
    auto.wait_for_jobs(config, 1)
    assert [call.args[0] for call in query.call_args_list] == [
        "condor_q",
        "condor_q",
        "condor_history",
        "condor_q",
        "condor_history",
    ]
    assert sleep.call_count == 2
    assert auto.wf.check_root.call_count == 2
    assert all(
        call.args[-1] == ["-name", "fixture-schedd.fnal.gov"]
        for call in query.call_args_list
    )


@pytest.mark.parametrize(
    "change,reason",
    [
        ({"JobStatus": 5, "HoldReason": "transfer failed"}, "held"),
        ({"JobStatus": 3}, "removed"),
        ({"ExitCode": 1}, "successful exit"),
        ({"ExitBySignal": True}, "successful exit"),
        ({"ExitBySignal": None}, "successful exit"),
        ({"Iwd": "/another/run"}, "directory"),
        ({"ClusterId": 999}, "identities"),
        ({"ProcId": 17}, "identities"),
    ],
)
def test_failed_or_unrelated_jobs_stop_before_outputs(
    auto, submitted, monkeypatch, change, reason
):
    config, ads = submitted
    ads[0].update(change)
    monkeypatch.setattr(auto, "query_jobs", Mock(return_value=ads))
    with pytest.raises(ValueError, match=reason):
        auto.wait_for_jobs(config, 1)
    auto.wf.check_root.assert_not_called()


def test_empty_queue_and_history_are_not_completion(auto, submitted, monkeypatch):
    config, _ = submitted
    monkeypatch.setattr(auto, "query_jobs", Mock(return_value=[]))
    with pytest.raises(TimeoutError, match="not cancelled"):
        auto.wait_for_jobs(config, 0)
    auto.wf.check_root.assert_not_called()


def test_successful_jobs_with_missing_output_stop(auto, submitted, monkeypatch):
    config, ads = submitted
    monkeypatch.setattr(auto, "query_jobs", Mock(side_effect=[[], ads]))
    monkeypatch.setattr(
        auto.wf, "check_root", Mock(side_effect=FileNotFoundError("missing output"))
    )
    with pytest.raises(FileNotFoundError):
        auto.wait_for_jobs(config, 1)


@pytest.fixture
def pipeline(auto, monkeypatch):
    configs = {}
    actions = []

    def create(args, folder):
        folder.mkdir(parents=True)
        actions.append(("prepare", folder.name))
        variant = auto.wf.ERAS[args.era]
        config = {
            "zpt": {
                "variant": variant,
                "site": args.site,
                "run_dir": str(folder),
                "systematics": not args.nominal_only,
                "run_mode": "production",
                "apply_reweight": args.weights is not None,
                "sample": "",
                "limit_files": -1,
                "reweight_json": str(args.weights),
            },
            "batchFolder": str(folder / "condor"),
            "tag": "test",
            "outputFolder": str(folder / "rootFiles"),
            "outputFile": "merged.root",
            "plotPath": str(folder / "plots"),
            "cuts": {},
            "variables": {},
            "nuisances": {},
            "lumi": 1,
            "samples": {
                "DY": {"weight": "nominal", "name": [("dy", ["fixed.root"])]},
                "DATA": {},
            },
            "aliases": {"DY_NLO_ZpTrw": {"expr": "fixture_formula"}},
        }
        if args.weights:
            config["samples"]["DY"]["weight"] += "*DY_NLO_ZpTrw"
        configs[folder] = config
        auto.wf.batch_dir(config).mkdir(parents=True)

    def submit(config):
        actions.append(("submit", Path(config["zpt"]["run_dir"]).name))
        (auto.wf.batch_dir(config) / "submit.receipt.txt").write_text("123.0\n")

    def merge(config, pickle_path, folder):
        actions.append(("merge", folder.name))
        output = auto.wf.root_output(config)
        output.parent.mkdir()
        output.touch()

    def plot(config, folder):
        actions.append(("plot", folder.name))
        Path(config["plotPath"]).mkdir()

    def extract(config, folder):
        actions.append(("extract", folder.name))
        output = folder / "weights" / "dyZpTrw.json"
        output.parent.mkdir()
        year, kind, jets = auto.wf.fit_keys(config["zpt"]["variant"])
        output.write_text(
            json.dumps({year: {f"{kind}_{jet}j": "fixture_formula" for jet in jets}})
        )

    monkeypatch.setattr(auto.wf, "create_run", create)
    monkeypatch.setattr(
        auto.wf, "load_run", lambda folder: (folder / "one.pkl", configs[folder])
    )
    monkeypatch.setattr(auto.wf, "submit", submit)
    monkeypatch.setattr(auto.wf, "merge", merge)
    monkeypatch.setattr(auto.wf, "plot", plot)
    monkeypatch.setattr(auto.wf, "extract", extract)
    monkeypatch.setattr(auto, "wait_for_jobs", Mock())
    monkeypatch.setattr(auto, "check_histograms", Mock())
    monkeypatch.setattr(auto, "check_plots", Mock())
    return configs, actions


def test_review_pause_then_resume_and_completed_rerun(auto, pipeline, tmp_path):
    configs, actions = pipeline
    folder = tmp_path / "study"
    auto.run(
        auto.wf.parser().parse_args(
            ["auto", "study", "--era", "2022", "--nominal-only"]
        ),
        folder,
    )
    assert actions == [
        (stage, "baseline")
        for stage in ("prepare", "submit", "merge", "plot", "extract")
    ]
    assert not (folder / "corrected").exists()
    weights = folder / "baseline/weights/dyZpTrw.json"
    data = json.loads(weights.read_text())
    data["2022_v12"]["LO_0j"] = "edited_fixture_formula"
    weights.write_text(json.dumps(data))
    resume = auto.wf.parser().parse_args(["auto", "study", "--weights", str(weights)])
    auto.run(resume, folder)
    assert configs[folder / "corrected"]["zpt"]["variant"] == "2022_v12"
    assert not configs[folder / "corrected"]["zpt"]["systematics"]
    assert actions[-4:] == [
        (stage, "corrected") for stage in ("prepare", "submit", "merge", "plot")
    ]
    before = list(actions)
    auto.run(auto.wf.parser().parse_args(["auto", "study"]), folder)
    assert actions == before  # No duplicate submission, merge, plotting or extraction.


def test_unattended_mode_connects_both_passes(auto, pipeline, tmp_path):
    configs, actions = pipeline
    folder = tmp_path / "study"
    auto.run(auto.wf.parser().parse_args(["auto", "study", "--apply-fitted"]), folder)
    assert ("submit", "corrected") in actions
    assert configs[folder / "corrected"]["zpt"]["reweight_json"] == str(
        folder / "baseline/weights/dyZpTrw.json"
    )


def test_incomplete_fit_stops_before_corrected_preparation(
    auto, pipeline, tmp_path, monkeypatch
):
    _, actions = pipeline
    monkeypatch.setattr(auto.wf, "extract", lambda *_: None)
    with pytest.raises(FileNotFoundError):
        auto.run(
            auto.wf.parser().parse_args(["auto", "study", "--apply-fitted"]),
            tmp_path / "study",
        )
    assert not any(phase == "corrected" for _, phase in actions)


def test_changed_resume_options_fail_before_submission(auto, pipeline, tmp_path):
    _, actions = pipeline
    folder = tmp_path / "study"
    auto.run(auto.wf.parser().parse_args(["auto", "study"]), folder)
    before = list(actions)
    with pytest.raises(ValueError, match="Options differ"):
        auto.run(
            auto.wf.parser().parse_args(["auto", "study", "--site", "cern"]), folder
        )
    assert actions == before


def test_changed_input_population_cannot_be_applied(auto):
    baseline = {
        "samples": {"DY": {"weight": "nominal", "name": [("dy", ["first.root"])]}}
    }
    corrected = deepcopy(baseline)
    corrected["samples"]["DY"]["weight"] += "*DY_NLO_ZpTrw"
    corrected["samples"]["DY"]["name"][0][1].append("another.root")
    with pytest.raises(ValueError, match="inputs"):
        auto.check_application(baseline, corrected)


def test_condor_shell_wrapper_preserves_argument_boundaries(auto, tmp_path):
    import subprocess

    client = tmp_path / "client"
    client.write_text('printf "%s\\n" "$@"\n')  # Like LPC wrappers, no shebang.
    client.chmod(0o700)
    result = subprocess.run(
        auto.wf.condor_command([str(client), "one argument", "$(false)"]),
        text=True,
        stdout=subprocess.PIPE,
        check=True,
    )
    assert result.stdout.splitlines() == ["one argument", "$(false)"]


def test_second_controller_cannot_advance_same_campaign(auto, pipeline, tmp_path):
    import fcntl

    _, actions = pipeline
    folder = tmp_path / "study"
    folder.mkdir()
    with (folder / ".controller.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        with pytest.raises(ValueError, match="Another controller"):
            auto.run(auto.wf.parser().parse_args(["auto", "study"]), folder)
    assert not actions


def test_nominal_member_check_rejects_partial_root_file(auto, tmp_path):
    import ROOT

    output = tmp_path / "partial.root"
    with ROOT.TFile(str(output), "RECREATE") as handle:
        directory = handle.mkdir("Zmm_0j").mkdir("ptll")
        directory.cd()
        # Structural fixture: no event data or claimed physics yield.
        ROOT.TH1D("histo_DY", "", 1, 0, 1).Write()
    config = {
        "outputFolder": str(tmp_path),
        "outputFile": output.name,
        "cuts": {"cuts": {"Zmm": {"categories": {"0j": "1"}}}},
        "samples": {"DY": {}, "DATA": {}},
        "variables": {"ptll": {}},
    }
    with pytest.raises(ValueError, match="histo_DATA"):
        auto.check_histograms(config)


def test_lpc_missing_scheduler_fails_before_query(auto, submitted, monkeypatch):
    config, _ = submitted
    (auto.wf.batch_dir(config) / "submit.receipt.txt").write_text("123.0 - 123.1\n")
    query = Mock()
    monkeypatch.setattr(auto, "query_jobs", query)
    with pytest.raises(ValueError, match="LPC scheduler"):
        auto.wait_for_jobs(config, 1)
    query.assert_not_called()


def test_receipt_scheduler_wins_over_lpc_environment_override(auto, monkeypatch):
    monkeypatch.setenv("FERMIHTC_SCHEDD_OVERRIDE", "different-schedd")
    assert "FERMIHTC_SCHEDD_OVERRIDE" not in auto.wf.condor_environment()
