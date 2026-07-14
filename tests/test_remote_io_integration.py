import os
from pathlib import Path

import pytest


def test_stage_in_precedes_tchain_add(monkeypatch, tmp_path):
    from mkShapesRDF.shapeAnalysis import runner as runner_module

    events = []

    class FakeStageInManager:
        def __init__(self, settings):
            pass

        def prepare_files(self, files):
            events.append(("stage", tuple(files)))
            return [f"staged:{path}" for path in files]

    class FakeTChain:
        def __init__(self, name):
            self.name = name

        def Add(self, path):
            events.append(("add", path))

        def AddFriend(self, friend):
            events.append(("friend", friend.name))

    class FakeRDF:
        def __init__(self, tree):
            pass

        def GetColumnNames(self):
            return []

    class FakeROOT:
        TChain = FakeTChain
        RDataFrame = FakeRDF

    monkeypatch.setattr(runner_module, "StageInManager", FakeStageInManager)
    monkeypatch.setattr(runner_module, "ROOT", FakeROOT)

    samples = [("ZZ", ["/store/file.root"], "1.0", 0, False, {})]
    runner_module.RunAnalysis(
        samples,
        aliases={},
        variables={},
        cuts={"preselections": "1", "cuts": {}},
        nuisances={},
        lumi=1.0,
        remote_io_settings={
            "inputAccessMode": "stage-in",
            "xrdReadEndpoint": "root://read.example",
            "stageInScratch": str(tmp_path),
        },
    )
    assert events[0] == ("stage", ("/store/file.root",))
    assert events[1] == ("add", "staged:/store/file.root")


def test_release_input_handles_resets_tchains_before_stagein_cleanup():
    from mkShapesRDF.shapeAnalysis.runner import RunAnalysis

    events = []

    class FakeChain:
        def Reset(self):
            events.append("reset")

    class FakeManager:
        def cleanup(self, success):
            events.append(("cleanup", success))

    runner = RunAnalysis.__new__(RunAnalysis)
    runner.dfs = {"ZZ": {0: {"ttree": FakeChain(), "df": object()}}}
    runner.results = {"held": object()}
    runner.stage_in_managers = [FakeManager()]
    runner._release_input_handles()
    for manager in runner.stage_in_managers:
        manager.cleanup(True)
    assert events == ["reset", ("cleanup", True)]
    assert runner.dfs == {}
    assert runner.results == {}


def test_dataframe_construction_failure_applies_stagein_failure_cleanup(monkeypatch):
    from mkShapesRDF.shapeAnalysis import runner as runner_module

    events = []

    class Manager:
        def cleanup(self, success):
            events.append(("cleanup", success))

    manager = Manager()
    monkeypatch.setattr(
        runner_module.RunAnalysis,
        "prepareInputFiles",
        staticmethod(lambda files, friends, settings: (["staged.root"], [], manager)),
    )
    monkeypatch.setattr(
        runner_module.RunAnalysis,
        "getTTreeNomAndFriends",
        staticmethod(lambda files, friends: (_ for _ in ()).throw(RuntimeError("bad tree"))),
    )
    with pytest.raises(RuntimeError, match="bad tree"):
        runner_module.RunAnalysis.prepareDataFrame(
            ["remote.root"], [], {"inputAccessMode": "stage-in"}
        )
    assert events == [("cleanup", False)]


def test_batch_output_identifier_has_sample_id_without_shell_folder(tmp_path, monkeypatch):
    from mkShapesRDF.shapeAnalysis.BatchSubmission import BatchSubmission

    startpath = tmp_path / "start.sh"
    startpath.write_text("#!/bin/sh\n")
    monkeypatch.setenv("STARTPATH", str(startpath))

    batch = BatchSubmission(
        folder=str(tmp_path),
        outputPath=str(tmp_path / "out"),
        batchFolder=str(tmp_path / "batch"),
        headersPath=str(tmp_path / "headers.hh"),
        runnerPath=str(tmp_path / "runner.py"),
        tag="tag",
        samples=[("SAMPLE", ["input.root"], "1.0", 0, False, {})],
        d={
            "outputFile": "mkShapes.root",
            "mountEOS": [],
            "remoteIO": {"inputAccessMode": "as-configured"},
        },
        batchVars=["samples", "remoteIO"],
        jdlconfigfile="",
    )
    (tmp_path / "out").mkdir()
    batch.createBatches()
    batch.submit(dryRun=1)

    run_sh = (tmp_path / "batch" / "tag" / "run.sh").read_text()
    submit_jdl = (tmp_path / "batch" / "tag" / "submit.jdl").read_text()
    script_py = (tmp_path / "batch" / "tag" / "SAMPLE_0" / "script.py").read_text()
    assert "SAMPLE_0" in script_py
    assert '${1}' not in run_sh
    assert "$(Folder)" not in submit_jdl
    assert "__ALL__\" + job_id" in run_sh


def test_pinned_file_override_avoids_production_discovery(monkeypatch):
    import mkShapesRDF.lib.search_files as search_files

    def fail_search(*args, **kwargs):
        raise AssertionError("production discovery should not run for pinnedFiles")

    monkeypatch.setattr(search_files.SearchFiles, "searchFiles", fail_search)
    fixture = (
        Path(__file__).parents[1]
        / "PlotsConfigurationsRun3"
        / "ZH_4lMET"
        / "ZZ_CR"
        / "samples.py"
    )
    globs = {"pinnedFiles": ["pinned.root"], "__file__": str(fixture)}
    exec(fixture.read_text(), globs, globs)
    assert globs["samples"]["ZZ"]["name"] == [("ZZ", ["pinned.root"])]


def test_zzcr_config_time_remote_discovery_uses_discovery_and_read_endpoints(
    monkeypatch,
):
    import mkShapesRDF.lib.search_files as search_files

    calls = []

    def fake_search(
        self,
        folder,
        process,
        redirector="root://eoscms.cern.ch/",
        isLatino=True,
        read_redirector=None,
        **kwargs,
    ):
        calls.append((folder, process, redirector, read_redirector))
        return [f"{read_redirector}//store/fake/nanoLatino_{process}__part0.root"]

    monkeypatch.delenv("ZZCR_PINNED_FILES", raising=False)
    monkeypatch.setattr(search_files.SearchFiles, "searchFiles", fake_search)
    fixture = (
        Path(__file__).parents[1]
        / "PlotsConfigurationsRun3"
        / "ZH_4lMET"
        / "ZZ_CR"
        / "samples.py"
    )
    globs = {
        "__file__": str(fixture),
        "remoteIO": {
            "inputAccessMode": "xrootd",
            "xrdDiscoveryEndpoint": "root://discovery.example",
            "xrdReadEndpoint": "root://read.example",
        },
    }
    exec(fixture.read_text(), globs, globs)
    assert calls
    assert calls[0][0].startswith("/eos/cms/store/")
    assert calls[0][2] == "root://discovery.example"
    assert calls[0][3] == "root://read.example"
