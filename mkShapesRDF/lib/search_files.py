import fnmatch
import subprocess
import glob
import sys
from mkShapesRDF.lib.remote_io import (
    ExternalCommandRunner,
    RemoteCommandError,
    RemoteIOError,
    is_root_url,
    mounted_eos_to_lfn,
    normalize_endpoint,
    split_root_uri,
)


class SearchFiles:
    """
    Class to search for files in a folder or DAS
    """

    _discovery_endpoint_override = None
    _read_endpoint_override = None

    @classmethod
    def configure_remote_endpoints(cls, discovery_endpoint=None, read_endpoint=None):
        """Set process-local explicit CLI overrides used during config loading."""
        cls._discovery_endpoint_override = discovery_endpoint
        cls._read_endpoint_override = read_endpoint

    def __init__(self, command_runner=None, timeout=120):
        # cache result of `glob.glob(folder)` and `xrdfs redirector ls folder`
        self.cached_list_of_files = {}
        self.command_runner = command_runner or ExternalCommandRunner(timeout, 0)

    def searchFiles(
        self,
        folder,
        process,
        redirector="root://eoscms.cern.ch/",
        isLatino=True,
        read_redirector=None,
        missing_ok=False,
    ):
        r"""Search for files in a folder. If redirector is specified, it will use xrdfs to query the redirector.

        Parameters
        ----------

            folder : str
                the folder to search in

            process : str
                the name of the process to search for

            redirector : str, optional, default: ``"root://eoscms.cern.ch/"``
                redirector to use.

            isLatino : bool, optional
                if the process is a latino process. Defaults to True. The process to search for will be ``"nanoLatino_" + process + "__part*.root"``.

        Returns
        -------

            `list of str`
                list of files found including the redirector
        """
        if self._discovery_endpoint_override is not None:
            redirector = self._discovery_endpoint_override
        if self._read_endpoint_override is not None:
            read_redirector = self._read_endpoint_override
        remote_discovery = redirector != ""
        if remote_discovery:
            redirector = normalize_endpoint(redirector)
            if not redirector or not redirector.startswith("root://"):
                raise RemoteIOError(
                    f"Malformed XRootD discovery endpoint for sample '{process}': "
                    f"{redirector!r}"
                )
            read_redirector = normalize_endpoint(read_redirector or redirector)
            if not read_redirector or not read_redirector.startswith("root://"):
                raise RemoteIOError(
                    f"Malformed XRootD read endpoint for sample '{process}': "
                    f"{read_redirector!r}"
                )
            if is_root_url(folder):
                _, folder = split_root_uri(folder)
            folder = mounted_eos_to_lfn(folder)

        if not folder.endswith("/"):
            folder += "/"

        listOfFiles = []
        cache_key = (folder, redirector if remote_discovery else "")
        if cache_key not in self.cached_list_of_files or (
            not remote_discovery and not self.cached_list_of_files[cache_key]
        ):
            print("Need to query for files for folder", folder)
            if remote_discovery:
                print("with redirector", redirector)
                try:
                    result = self.command_runner.run(
                        ["xrdfs", redirector, "ls", folder],
                        "discovery-list",
                        {
                            "redirector": redirector,
                            "folder": folder,
                            "sample": process,
                        },
                    )
                except RemoteCommandError as exc:
                    detail = f"{exc.result.stdout}\n{exc.result.stderr}".lower()
                    if missing_ok and "no such file" in detail:
                        return []
                    raise RemoteIOError(
                        "Remote discovery failed for "
                        f"sample='{process}', folder='{folder}', "
                        f"endpoint='{redirector}', operation='xrdfs ls': "
                        f"{exc.result.stderr.strip() or exc.result.stdout.strip()}"
                    ) from exc
                listOfFiles = result.stdout.split("\n")
                normalized_files = []
                for item in listOfFiles:
                    item = item.strip()
                    if not item:
                        continue
                    if is_root_url(item):
                        _, item = split_root_uri(item)
                    normalized_files.append(mounted_eos_to_lfn(item))
                listOfFiles = normalized_files
            else:
                listOfFiles = glob.glob(folder + "*")
            self.cached_list_of_files[cache_key] = listOfFiles
        else:
            listOfFiles = self.cached_list_of_files[cache_key]

        if isLatino:
            process = "nanoLatino_" + process + "__part*.root"
        else:
            process = process + "*.root"

        files = list(
            filter(lambda k: fnmatch.fnmatch(k, folder + process), listOfFiles)
        )

        if isLatino:
            files = sorted(
                files,
                key=lambda k: int(k.split("/")[-1].split(".")[0].split("__part")[-1]),
            )
        else:
            files = sorted(files)

        if remote_discovery:
            files = [
                item
                if is_root_url(item)
                else f"{read_redirector}/{item.lstrip('/') if not item.startswith('/') else item}"
                for item in files
            ]

        return files

    def searchFilesDAS(
        self, process, redirector="root://cms-xrd-global.cern.ch/", instance=""
    ):
        r"""Search for files given a DAS query. If instance is specified, it will search for files with the provided instance.

        Parameters
        ----------

            process : str
                the name of the process to search for

            redirector : str, optional, default:  ``"root://cms-xrd-global.cern.ch/"``.
                redirector to use.

            instance : str, optional
                instance to use. Defaults to "". instance="prod/phys03" will search for files generated with crab.


        Returns
        -------

            `list of str`
                list of files found including the redirector

        """

        files = []
        if (len(self.cached_list_of_files.get(("das", process), []))) == 0:
            procString = f'dasgoclient --query="file dataset={process}'
            if instance != "":
                procString += " instance=" + instance
            procString += '"'

            proc = subprocess.Popen(
                procString,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            out, err = proc.communicate()
            out = out.decode("utf-8")
            out = out.split("\n")
            files = list(filter(lambda k: k.strip() != "", out))
            print(files, len(files))
            err = err.decode("utf-8")
            if len(err) != 0:
                print("There were some errors in retrieving file:")
                print(err)
                sys.exit()
        else:
            files = self.cached_list_of_files[("das", process)]

        files = list(map(lambda k: redirector + k, files))
        return files
