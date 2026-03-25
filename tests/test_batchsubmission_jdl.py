import os
import tempfile
from pathlib import Path

from mkShapesRDF.shapeAnalysis.BatchSubmission import BatchSubmission


def test_batchsubmission_uses_jdl_scope_with_self():
    with tempfile.TemporaryDirectory() as tmpdir:
        project = Path(tmpdir) / "project"
        batch = Path(tmpdir) / "condor"
        project.mkdir(parents=True, exist_ok=True)

        jdl_file = project / "custom_jdl.py"
        jdl_file.write_text(
            """
executable = [
    "#!/bin/bash",
    "echo custom-jdl",
    f"echo runner={self.runnerPath}",
]
jdl_dict = {"transfer_output_files": '""'}
condor_config = []
""".strip()
        )

        b = BatchSubmission(
            folder=str(project),
            outputPath=str(project / "out"),
            batchFolder=str(batch),
            headersPath="/tmp/headers.hh",
            runnerPath="/tmp/runner.py",
            tag="TAG",
            samples=[("SAMPLE", ["f.root"], 1.0, 0)],
            d={"outputFile": "mkShapes__TAG.root", "mountEOS": []},
            batchVars=["samples"],
            jdlconfigfile="custom_jdl.py",
        )
        b.createBatches()
        b.submit(dryRun=1)

        run_sh = (batch / "TAG" / "run.sh").read_text()
        submit_jdl = (batch / "TAG" / "submit.jdl").read_text()

        assert "custom-jdl" in run_sh
        assert "runner=/tmp/runner.py" in run_sh
        assert 'transfer_output_files = ""' in submit_jdl


def test_createbatches_resets_folder_list():
    with tempfile.TemporaryDirectory() as tmpdir:
        project = Path(tmpdir) / "project"
        batch = Path(tmpdir) / "condor"
        project.mkdir(parents=True, exist_ok=True)

        b = BatchSubmission(
            folder=str(project),
            outputPath=str(project / "out"),
            batchFolder=str(batch),
            headersPath="/tmp/headers.hh",
            runnerPath="/tmp/runner.py",
            tag="TAG",
            samples=[("SAMPLE", ["f.root"], 1.0, 0)],
            d={"outputFile": "mkShapes__TAG.root", "mountEOS": []},
            batchVars=["samples"],
            jdlconfigfile="",
        )

        b.createBatches()
        assert b.folders == ["SAMPLE_0"]
        b.createBatches()
        assert b.folders == ["SAMPLE_0"]


def test_batchsubmission_invalid_jdl_fails_fast():
    with tempfile.TemporaryDirectory() as tmpdir:
        project = Path(tmpdir) / "project"
        batch = Path(tmpdir) / "condor"
        project.mkdir(parents=True, exist_ok=True)

        # Invalid type for executable -> should raise RuntimeError from submit.
        (project / "broken_jdl.py").write_text(
            "\n".join(
                [
                    'executable = "not-a-list"',
                    "jdl_dict = {}",
                    "condor_config = []",
                ]
            )
        )

        b = BatchSubmission(
            folder=str(project),
            outputPath=str(project / "out"),
            batchFolder=str(batch),
            headersPath="/tmp/headers.hh",
            runnerPath="/tmp/runner.py",
            tag="TAG",
            samples=[("SAMPLE", ["f.root"], 1.0, 0)],
            d={"outputFile": "mkShapes__TAG.root", "mountEOS": []},
            batchVars=["samples"],
            jdlconfigfile="broken_jdl.py",
        )
        b.createBatches()

        try:
            b.submit(dryRun=1)
            raised = False
        except RuntimeError as exc:
            raised = True
            assert "Could not parse jdlconfigfile" in str(exc)

        assert raised


def test_zzcr_jdl_dict_builds_expected_commands():
    zzcr_jdl = (
        Path("PlotsConfigurationsRun3")
        / "ZH_4lMET"
        / "ZZ_CR"
        / "jdl_dict_zzcr.py"
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        proxy_src = Path(tmpdir) / "x509up_u123"
        proxy_src.write_text("proxy")

        fake_voms = Path(tmpdir) / "voms-proxy-info"
        fake_voms.write_text(
            "\n".join(
                [
                    "#!/bin/bash",
                    'if [[ \"$1\" == \"-exists\" ]]; then exit 0; fi',
                    'if [[ \"$1\" == \"-path\" ]]; then echo \"'
                    + str(proxy_src)
                    + '\"; exit 0; fi',
                    "exit 1",
                ]
            )
        )
        fake_voms.chmod(0o755)
        fake_xrdfs = Path(tmpdir) / "xrdfs"
        fake_xrdfs.write_text("#!/bin/bash\nexit 0\n")
        fake_xrdfs.chmod(0o755)

        old_path = os.environ.get("PATH", "")
        os.environ["PATH"] = f"{tmpdir}:{old_path}"
        try:
            batch_folder = Path(tmpdir) / "condor"
            tag = "TAG"
            (batch_folder / tag).mkdir(parents=True, exist_ok=True)

            class DummySelf:
                outputPath = "/eos/user/t/test/zzcr/rootFile"
                d = {"outputFile": "mkShapes__ZH_4lMET_ZZCR_2024v15.root"}
                headersPath = "/tmp/headers.hh"
                runnerPath = "/tmp/runner.py"
                batchFolder = str(batch_folder)
                tag = "TAG"

            scope = {"self": DummySelf, "os": os}
            exec(zzcr_jdl.read_text(), scope)

            executable = scope["executable"]
            jdl_dict = scope["jdl_dict"]

            assert any("X509_USER_PROXY" in line for line in executable)
            assert any("PYTHON_BIN=$(command -v python3" in line for line in executable)
            assert any("xrdcp -f -v output.root" in line for line in executable)
            assert any("xrdfs " in line and " rm " in line for line in executable)
            assert not any("xrdfs " in line and " rm -f " in line for line in executable)
            assert "x509up" in jdl_dict["transfer_input_files"]
            assert (batch_folder / tag / "x509up").exists()
        finally:
            os.environ["PATH"] = old_path


def test_zzcr_jdl_dict_requires_voms_proxy_info_binary():
    zzcr_jdl = (
        Path("PlotsConfigurationsRun3")
        / "ZH_4lMET"
        / "ZZ_CR"
        / "jdl_dict_zzcr.py"
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        batch_folder = Path(tmpdir) / "condor"
        tag = "TAG"
        (batch_folder / tag).mkdir(parents=True, exist_ok=True)

        class DummySelf:
            outputPath = "/eos/user/t/test/zzcr/rootFile"
            d = {"outputFile": "mkShapes__ZH_4lMET_ZZCR_2024v15.root"}
            headersPath = "/tmp/headers.hh"
            runnerPath = "/tmp/runner.py"
            batchFolder = str(batch_folder)
            tag = "TAG"

        old_path = os.environ.get("PATH", "")
        os.environ["PATH"] = ""
        try:
            try:
                exec(zzcr_jdl.read_text(), {"self": DummySelf, "os": os})
                raised = False
            except RuntimeError as exc:
                raised = True
                assert "xrdfs" in str(exc) or "voms-proxy-info" in str(exc)
            assert raised
        finally:
            os.environ["PATH"] = old_path


def test_zzcr_jdl_maps_eos_home_to_eos_user_for_xrdcp():
    zzcr_jdl = (
        Path("PlotsConfigurationsRun3")
        / "ZH_4lMET"
        / "ZZ_CR"
        / "jdl_dict_zzcr.py"
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        proxy_src = Path(tmpdir) / "x509up_u123"
        proxy_src.write_text("proxy")

        fake_voms = Path(tmpdir) / "voms-proxy-info"
        fake_voms.write_text(
            "\n".join(
                [
                    "#!/bin/bash",
                    'if [[ \"$1\" == \"-exists\" ]]; then exit 0; fi',
                    'if [[ \"$1\" == \"-path\" ]]; then echo \"'
                    + str(proxy_src)
                    + '\"; exit 0; fi',
                    "exit 1",
                ]
            )
        )
        fake_voms.chmod(0o755)
        fake_xrdfs = Path(tmpdir) / "xrdfs"
        fake_xrdfs.write_text("#!/bin/bash\nexit 0\n")
        fake_xrdfs.chmod(0o755)

        old_path = os.environ.get("PATH", "")
        os.environ["PATH"] = f"{tmpdir}:{old_path}"
        try:
            batch_folder = Path(tmpdir) / "condor"
            tag = "TAG"
            (batch_folder / tag).mkdir(parents=True, exist_ok=True)

            class DummySelf:
                outputPath = "/eos/home-m/mwadud/mkShapesRDF_rootfiles/ZH_4lMET/rootFile"
                d = {"outputFile": "mkShapes__ZH_4lMET_ZZCR_2024v15.root"}
                headersPath = "/tmp/headers.hh"
                runnerPath = "/tmp/runner.py"
                batchFolder = str(batch_folder)
                tag = "TAG"

            scope = {"self": DummySelf, "os": os}
            exec(zzcr_jdl.read_text(), scope)

            executable = scope["executable"]
            xrdcp_lines = [line for line in executable if "xrdcp -f -v output.root" in line]
            assert len(xrdcp_lines) == 1
            assert "/eos/user/m/mwadud/" in xrdcp_lines[0]
            assert "/eos/home-m/" not in xrdcp_lines[0]
        finally:
            os.environ["PATH"] = old_path


def test_zzcr_jdl_uses_store_namespace_for_eos_cms_path():
    zzcr_jdl = (
        Path("PlotsConfigurationsRun3")
        / "ZH_4lMET"
        / "ZZ_CR"
        / "jdl_dict_zzcr.py"
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        proxy_src = Path(tmpdir) / "x509up_u123"
        proxy_src.write_text("proxy")

        fake_voms = Path(tmpdir) / "voms-proxy-info"
        fake_voms.write_text(
            "\n".join(
                [
                    "#!/bin/bash",
                    'if [[ \"$1\" == \"-exists\" ]]; then exit 0; fi',
                    'if [[ \"$1\" == \"-path\" ]]; then echo \"'
                    + str(proxy_src)
                    + '\"; exit 0; fi',
                    "exit 1",
                ]
            )
        )
        fake_voms.chmod(0o755)
        fake_xrdfs = Path(tmpdir) / "xrdfs"
        fake_xrdfs.write_text("#!/bin/bash\nexit 0\n")
        fake_xrdfs.chmod(0o755)

        old_path = os.environ.get("PATH", "")
        os.environ["PATH"] = f"{tmpdir}:{old_path}"
        try:
            batch_folder = Path(tmpdir) / "condor"
            tag = "TAG"
            (batch_folder / tag).mkdir(parents=True, exist_ok=True)

            class DummySelf:
                outputPath = "/eos/cms/store/user/mwadud/mkShapesRDF_rootfiles/ZH_4lMET/rootFile"
                d = {"outputFile": "mkShapes__ZH_4lMET_ZZCR_2024v15.root"}
                headersPath = "/tmp/headers.hh"
                runnerPath = "/tmp/runner.py"
                batchFolder = str(batch_folder)
                tag = "TAG"

            scope = {"self": DummySelf, "os": os}
            exec(zzcr_jdl.read_text(), scope)

            executable = scope["executable"]
            xrdcp_lines = [line for line in executable if "xrdcp -f -v output.root" in line]
            assert len(xrdcp_lines) == 1
            assert "root://eoscms.cern.ch//store/user/mwadud/" in xrdcp_lines[0]
            assert "/eos/cms/store/" not in xrdcp_lines[0]
        finally:
            os.environ["PATH"] = old_path


def test_zzcr_jdl_uses_custom_redirector_from_configuration():
    zzcr_jdl = (
        Path("PlotsConfigurationsRun3")
        / "ZH_4lMET"
        / "ZZ_CR"
        / "jdl_dict_zzcr.py"
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        proxy_src = Path(tmpdir) / "x509up_u123"
        proxy_src.write_text("proxy")

        fake_voms = Path(tmpdir) / "voms-proxy-info"
        fake_voms.write_text(
            "\n".join(
                [
                    "#!/bin/bash",
                    'if [[ \"$1\" == \"-exists\" ]]; then exit 0; fi',
                    'if [[ \"$1\" == \"-path\" ]]; then echo \"'
                    + str(proxy_src)
                    + '\"; exit 0; fi',
                    "exit 1",
                ]
            )
        )
        fake_voms.chmod(0o755)
        fake_xrdfs = Path(tmpdir) / "xrdfs"
        fake_xrdfs.write_text("#!/bin/bash\nexit 0\n")
        fake_xrdfs.chmod(0o755)

        old_path = os.environ.get("PATH", "")
        os.environ["PATH"] = f"{tmpdir}:{old_path}"
        try:
            batch_folder = Path(tmpdir) / "condor"
            tag = "TAG"
            (batch_folder / tag).mkdir(parents=True, exist_ok=True)

            class DummySelf:
                outputPath = "/eos/cms/store/user/mwadud/mkShapesRDF_rootfiles/ZH_4lMET/rootFile"
                d = {
                    "outputFile": "mkShapes__ZH_4lMET_ZZCR_2024v15.root",
                    "xrdRedirector": "xrootd-cms.infn.it",
                }
                headersPath = "/tmp/headers.hh"
                runnerPath = "/tmp/runner.py"
                batchFolder = str(batch_folder)
                tag = "TAG"

            scope = {"self": DummySelf, "os": os}
            exec(zzcr_jdl.read_text(), scope)

            executable = scope["executable"]
            xrdcp_lines = [line for line in executable if "xrdcp -f -v output.root" in line]
            assert len(xrdcp_lines) == 1
            assert "root://xrootd-cms.infn.it//store/user/mwadud/" in xrdcp_lines[0]
        finally:
            os.environ["PATH"] = old_path
