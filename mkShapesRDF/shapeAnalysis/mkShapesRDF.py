"""
Main script for the creation of shapes, starting from a configuration folder.

It gives the option to compile the configuration folder and save it as both JSON and pickle file.

It also gives the option to run the analysis in batch mode, or to check for errors in the batch submission.

The analysis can be run in batch mode or locally.

If run in batch mode it gives the ability to merge the output root files.
"""

import sys
from pathlib import Path
import argparse
import os
import glob
import subprocess
import ROOT
from copy import deepcopy
from mkShapesRDF.shapeAnalysis.histo_utils import postProcessNuisances
from mkShapesRDF.lib.remote_io import (
    DEFAULT_REMOTE_IO_CONFIG,
    EXISTING_OUTPUT_POLICIES,
    INPUT_ACCESS_MODES,
    STAGE_IN_CLEANUP_POLICIES,
    build_remote_uri,
    resolve_remote_io_config,
    stage_out,
)

ROOT.gROOT.SetBatch(True)

headersPath = os.path.dirname(os.path.dirname(__file__)) + "/include/headers.hh"
ROOT.gInterpreter.Declare(f'#include "{headersPath}"')


def defaultParser():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "-c",
        "--compile",
        type=int,
        choices=[0, 1],
        help="1 compile configuration and save JSON/pickle, 0 load a compiled configuration",
        required=False,
        default=0,
    )

    parser.add_argument(
        "-o",
        "--operationMode",
        type=int,
        choices=[0, 1, 2],
        help="0 do analysis in batch, 1 check for errors in batch submission, "
        "2 hadd root files",
        required=False,
        default=-1,
    )
    
    parser.add_argument(
        "--check",
        action='store_true',
        help="Check status of batch submission",
        required=False,
    )

    parser.add_argument(
        "--submit",
        action='store_true',
        help="Submit jobs for histograms creation to batch system",
        required=False,
    )

    parser.add_argument(
        "--histoadd",
        action='store_true',
        help="Hadd root files",
        required=False,
    )

    parser.add_argument(
        "-b",
        "--doBatch",
        help="0 (default) runs on local, 1 runs with condor",
        required=False,
        default="0",
    )

    parser.add_argument(
        "-dR",
        "--dryRun",
        choices=[0, 1],
        type=int,
        help="1 do not submit to condor",
        required=False,
        default=0,
    )

    parser.add_argument(
        "-f", "--folder", help="Path to folder", required=False, default="."
    )
    parser.add_argument(
        "--output-folder",
        dest="outputFolderOverride",
        help="Override the configured output folder without editing analysis source",
        default=None,
    )

    parser.add_argument(
        "-configs",
        "--configsFolder",
        help="Path to configurations folder",
        required=False,
        default="configs",
    )

    parser.add_argument(
        "-config",
        "--configFile",
        help="Path to configuration JSON file to load",
        required=False,
        default="latest",
    )

    parser.add_argument(
        "-l",
        "--limitEvents",
        type=int,
        help="Max number of events",
        required=False,
        default=-1,
    )

    parser.add_argument(
        "-r",
        "--resubmit",
        choices=[0, 1, 2],
        type=int,
        help="Resubmit jobs, 1 resubmit finished jobs with errors, 2 resubmit running jobs",
        required=False,
        default="0", # default 0 ?? Why not "1" as default?
    )
    parser.add_argument(
        "-q",
        "--queue",
        choices=[
            "espresso",
            "microcentury",
            "longlunch",
            "workday",
            "tomorrow",
            "testmatch",
        ],
        help="Condor queue",
        required=False,
        default="workday",
    )
    parser.add_argument(
        "--input-access-mode",
        dest="inputAccessMode",
        choices=INPUT_ACCESS_MODES,
        default=None,
    )
    parser.add_argument("--xrd-read-endpoint", dest="xrdReadEndpoint", default=None)
    parser.add_argument(
        "--xrd-discovery-endpoint", dest="xrdDiscoveryEndpoint", default=None
    )
    parser.add_argument("--xrd-write-endpoint", dest="xrdWriteEndpoint", default=None)
    parser.add_argument("--stage-in-scratch", dest="stageInScratch", default=None)
    parser.add_argument(
        "--stage-in-cleanup",
        dest="stageInCleanup",
        choices=STAGE_IN_CLEANUP_POLICIES,
        default=None,
    )
    parser.add_argument(
        "--preserve-stage-in-on-failure",
        dest="preserveStageInOnFailure",
        action=argparse.BooleanOptionalAction,
        default=None,
    )
    parser.add_argument(
        "--existing-output-policy",
        dest="existingOutputPolicy",
        choices=EXISTING_OUTPUT_POLICIES,
        default=None,
    )
    parser.add_argument(
        "--remote-command-timeout",
        dest="remoteCommandTimeout",
        type=float,
        default=None,
    )
    parser.add_argument(
        "--remote-transfer-retries",
        dest="remoteTransferRetries",
        type=int,
        default=None,
    )
    parser.add_argument(
        "--condor-runtime-package",
        dest="condorRuntimePackage",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Build a scratch-only runtime package for generic Condor mode",
    )
    parser.add_argument(
        "--runtime-include",
        dest="condorRuntimeIncludes",
        action="append",
        default=None,
        help="Additional file/directory needed by a packaged configuration; repeatable",
    )
    parser.add_argument(
        "--use-x509-proxy",
        dest="useX509Proxy",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Transfer the active VOMS proxy separately from the runtime package",
    )
    return parser


def resolve_cli_remote_io(args, config_dict):
    cli_values = {
        "inputAccessMode": args.inputAccessMode,
        "xrdReadEndpoint": args.xrdReadEndpoint,
        "xrdDiscoveryEndpoint": args.xrdDiscoveryEndpoint,
        "xrdWriteEndpoint": args.xrdWriteEndpoint,
        "stageInScratch": args.stageInScratch,
        "stageInCleanup": args.stageInCleanup,
        "preserveStageInOnFailure": args.preserveStageInOnFailure,
        "existingOutputPolicy": args.existingOutputPolicy,
        "remoteCommandTimeout": args.remoteCommandTimeout,
        "remoteTransferRetries": args.remoteTransferRetries,
    }
    config_values = dict(config_dict.get("remoteIO") or {})
    for key in DEFAULT_REMOTE_IO_CONFIG:
        if config_dict.get(key) is not None:
            config_values[key] = config_dict[key]
    return resolve_remote_io_config(config_values, cli_values)


def validate_config_execution_mode(config_dict, do_batch):
    """Fail before runner/JIT work when a config requires another topology."""
    required = config_dict.get("requiredExecutionMode")
    if not required:
        return
    actual = "batch" if int(do_batch) == 1 else "local"
    if required == actual:
        return
    remediation = config_dict.get("executionModeRemediation")
    detail = f" {remediation}" if remediation else ""
    raise RuntimeError(
        f"This configuration requires {required} execution, but {actual} execution "
        f"was requested.{detail}"
    )


def main():
    parser = defaultParser()
    args = parser.parse_args()

    compileFolder = args.compile
    operationMode = args.operationMode
    doBatch = int(args.doBatch)
    dryRun = int(args.dryRun)
    queue = args.queue

    #
    # if "check" is triggered, override the operation mode and just "check" the status of the submission of jobs
    #    "operationMode = 1" means check jobs
    #
    if args.check :
      operationMode = 1
      print ("check jobs")

    #
    # if "submit" is triggered, override the operation mode and just "submit" to batch system the creation of histograms
    #    "operationMode = 0" means submit
    #
    if args.submit :
      operationMode = 0
      doBatch = 1       # if "submit" it means on the batch system!
      print ("submit jobs on the batch system")

    #
    # if "histoadd" is triggered, override the operation mode and just "hadd" the histograms
    #    "operationMode = 2" means perform hadd of the histograms
    #
    if args.histoadd :
      operationMode = 2
      print ("hadd histograms")

    mkShapesRDFExecutionMode = (
        ("batch" if doBatch == 1 else "local")
        if operationMode == 0
        else "management"
    )
    globals()["mkShapesRDFExecutionMode"] = mkShapesRDFExecutionMode




    global folder
    global batchFolder
    global outputFolder

    folder = os.path.abspath(args.folder)
    configs_path = Path(args.configsFolder).expanduser()
    if not configs_path.is_absolute():
        configs_path = Path(folder) / configs_path
    configsFolder = str(configs_path.resolve())
    configFile = args.configFile
    resubmit = int(args.resubmit)

    if compileFolder == 1:
        print(os.getcwd())
        print(os.path.abspath(f"{folder}/configuration.py"))
        if not os.path.exists(folder) or not os.path.exists(
            f"{folder}/configuration.py"
        ):
            print("Error, configuration folder does not exists!")
            sys.exit()

        from mkShapesRDF.shapeAnalysis.ConfigLib import ConfigLib

        # variables before execution of files
        configVars1 = dict(list(globals().items()) + list(locals().items()))

        old_cwd = os.getcwd()
        sys.path.insert(0, folder)
        try:
            os.chdir(folder)
            ConfigLib.loadConfig(["configuration.py"], globals())
            pre_config = {"remoteIO": globals().get("remoteIO", {})}
            for _key in DEFAULT_REMOTE_IO_CONFIG:
                if _key in globals():
                    pre_config[_key] = globals()[_key]
            pre_remote_io = resolve_cli_remote_io(args, pre_config)
            globals()["remoteIO"] = pre_remote_io
            for _key, _value in pre_remote_io.items():
                globals()[_key] = _value
            from mkShapesRDF.lib.search_files import SearchFiles

            discovery_override = None
            read_override = None
            if (
                args.xrdDiscoveryEndpoint is not None
                or pre_remote_io["inputAccessMode"] != "as-configured"
            ):
                discovery_override = pre_remote_io.get("xrdDiscoveryEndpoint")
                read_override = pre_remote_io.get("xrdReadEndpoint")
            SearchFiles.configure_remote_endpoints(
                discovery_override, read_override
            )
            ConfigLib.loadConfig(filesToExec, globals(), imports)
        finally:
            os.chdir(old_cwd)
            try:
                sys.path.remove(folder)
            except ValueError:
                pass

        globals()["varsToKeep"].insert(0, "folder")

        d = ConfigLib.createConfigDict(
            varsToKeep, dict(list(globals().items()) + list(locals().items()))
        )

        # variables after execution of files
        configVars2 = dict(list(globals().items()) + list(locals().items()))

        import datetime

        dt = datetime.datetime.now()
        Path(configsFolder).mkdir(parents=True, exist_ok=True)

        fileName = configsFolder + "/config_" + dt.strftime("%y-%m-%d_%H_%M_%S")
        fileNameJson = configsFolder + "/config"

        ConfigLib.dumpConfigDict(d, fileName)
        ConfigLib.dumpConfigDict(d, fileNameJson, doJson=True)

        ConfigLib.loadDict(d, globals())

    else:
        from mkShapesRDF.shapeAnalysis.ConfigLib import ConfigLib

        if configFile != "latest":
            p = os.path.abspath(configFile)
            if not os.path.exists(p):
                print("Config file", configFile, "doest not exists at path", p)
                sys.exit()
            else:
                d = ConfigLib.loadPickle(p, globals())
        else:
            d = ConfigLib.loadLatestPickle(configsFolder, globals())

    if operationMode == 0:
        validate_config_execution_mode(d, doBatch)

    samples = globals()["samples"]
    aliases = globals()["aliases"]
    variables = globals()["variables"]
    cuts = globals()["cuts"]
    nuisances = globals()["nuisances"]
    lumi = globals()["lumi"]
    print(samples.keys())
    print(d.keys())

    remoteIO = resolve_cli_remote_io(args, d)
    globals()["remoteIO"] = remoteIO
    d["remoteIO"] = remoteIO
    for _key, _value in remoteIO.items():
        globals()[_key] = _value
        d[_key] = _value
    for _key in remoteIO:
        if _key not in batchVars:
            batchVars.append(_key)
    if "remoteIO" not in batchVars:
        batchVars.append("remoteIO")

    if args.outputFolderOverride is not None:
        outputFolder = args.outputFolderOverride
        globals()["outputFolder"] = outputFolder
        d["outputFolder"] = outputFolder
    for _name in ("condorRuntimePackage", "condorRuntimeIncludes", "useX509Proxy"):
        _value = getattr(args, _name)
        if _value is not None:
            globals()[_name] = _value
            d[_name] = _value

    print("\n\n", batchVars, "\n\n")

    batch_path = Path(batchFolder).expanduser()
    if not batch_path.is_absolute():
        batch_path = Path(folder) / batch_path
    batchFolder = str(batch_path.resolve())

    remoteOutputDestination = None
    if str(outputFolder).startswith("root://") or (
        str(outputFolder).startswith("/store/") and remoteIO.get("xrdWriteEndpoint")
    ):
        outputPath = (
            str(outputFolder).rstrip("/")
            if str(outputFolder).startswith("root://")
            else build_remote_uri(remoteIO["xrdWriteEndpoint"], outputFolder)
        )
        if doBatch == 1:
            outputFileMap = "output.root"
        else:
            remote_output_leaf = (
                str(outputPath).rstrip("/").rsplit("/", 1)[-1] or "rootFiles"
            )
            localRemoteOutputPath = Path(folder) / localJobDir / remote_output_leaf
            localRemoteOutputPath.mkdir(parents=True, exist_ok=True)
            outputFileMap = f"{localRemoteOutputPath}/{outputFile}"
            remoteOutputDestination = f"{outputPath}/{outputFile}"
    elif Path(outputFolder).expanduser().is_absolute():
        Path(outputFolder).expanduser().mkdir(parents=True, exist_ok=True)
        outputPath = str(Path(outputFolder).expanduser().resolve())
        outputFileMap = f"{outputPath}/{outputFile}"
    else: 
        Path(f"{folder}/{outputFolder}").mkdir(parents=True, exist_ok=True)
        outputPath = os.path.abspath(f"{folder}/{outputFolder}")
        outputFileMap = f"{outputPath}/{outputFile}"

    if operationMode == 2 and os.path.exists(outputFileMap):
        print("Can't merge files, output already exists")
        print(f"You can run: \nrm {outputFileMap}")
        sys.exit()

    limit = int(args.limitEvents)
    d["limitEvents"] = limit
    globals()["limitEvents"] = limit
    if "limitEvents" not in batchVars:
        batchVars.append("limitEvents")

    # PROCESSING
    runnerFile = globals()["runnerFile"]
    if runnerFile == "default":
        runnerPath = os.path.realpath(os.path.dirname(__file__)) + "/runner.py"
        runnerFile = "runner.py"
    else:
        runnerPath = f"{folder}/{runnerFile}"
    print("\n\nRunner path: ", runnerPath, "\n\n")
    if not os.path.exists(runnerPath):
        print("Runner file / path does not exist!")
        sys.exit()

    _results = {}
    sys.path.insert(0, os.path.dirname(runnerPath))
    runnerModule = __import__(runnerFile.strip(".py"))
    if not hasattr(runnerModule, "RunAnalysis"):
        raise AttributeError(
            f"Runner module {runnerFile} from {runnerPath} has no attribute RunAnalysis"
        )
    RunAnalysis = runnerModule.RunAnalysis

    if operationMode == 0:
        print("#" * 20, "\n\n", "   Doing analysis", "\n\n", "#" * 20)

        if doBatch == 1:
            print("#" * 20, "\n\n", " Running on condor  ", "\n\n", "#" * 20)

            _samples = RunAnalysis.splitSamples(samples)

            from mkShapesRDF.shapeAnalysis.BatchSubmission import BatchSubmission

            batch = BatchSubmission(
                folder,
                outputPath,
                batchFolder,
                headersPath,
                runnerPath,
                tag,
                _samples,
                d,
                batchVars,
                globals().get("jdlconfigfile", ""),
            )
            batch.createBatches()
            batch.submit(dryRun, queue)

        else:
            print("#" * 20, "\n\n", " Running on local machine  ", "\n\n", "#" * 20)

            _samples = RunAnalysis.splitSamples(samples, False)

            runner = RunAnalysis(
                _samples,
                aliases,
                deepcopy(variables),
                deepcopy(cuts),
                nuisances,
                lumi,
                limit,
                outputFileMap,
                remoteIO,
            )
            runner.run()
            cuts = cuts["cuts"]
            postProcessNuisances(
                outputFileMap, samples, aliases, variables, cuts, nuisances
            )
            if remoteOutputDestination:
                stage_out(outputFileMap, remoteOutputDestination, remoteIO)

    elif operationMode == 1:
        errs = glob.glob("{}/{}/*/err.txt".format(batchFolder, tag))
        files = glob.glob("{}/{}/*/script.py".format(batchFolder, tag))

        errsD = list(map(lambda k: "/".join(k.split("/")[:-1]), errs))
        filesD = list(map(lambda k: "/".join(k.split("/")[:-1]), files))
        # print(files)
        notFinished = list(set(filesD).difference(set(errsD)))
        sort_key = lambda k: (k.split("_")[0], int(k.split("_")[-1]))
        notFinishedShort = sorted(
            list(map(lambda k: k.split("/")[-1], notFinished)), key=sort_key
        )
        finishedShort = sorted(
            list(map(lambda k: k.split("/")[-2], errs)), key=sort_key
        )
        allSamples = {}
        for file in finishedShort:
            sample = "_".join(file.split("_")[:-1])
            if sample not in allSamples:
                allSamples[sample] = {"done": 1, "running": 0}
            else:
                allSamples[sample]["done"] += 1
        for file in notFinishedShort:
            sample = "_".join(file.split("_")[:-1])
            if sample not in allSamples:
                allSamples[sample] = {"done": 0, "running": 1}
            else:
                allSamples[sample]["running"] += 1


        import tabulate

        tabulated = [["Sample", "Total", "Finished", "Running"]]
        for sample in allSamples:
            tot = allSamples[sample]["done"] + allSamples[sample]["running"]
            tabulated.append(
                [
                    sample,
                    str(tot),
                    "\033[92m " + str(allSamples[sample]["done"]) + "\033[00m",
                    "\033[93m " + str(allSamples[sample]["running"]) + "\033[00m",
                ]
            )
        print(tabulate.tabulate(tabulated, headers="firstrow", tablefmt="fancy_grid"))

        #
        # Change colour depending if running jobs is 0 or not, it will help spotting problematic jobs
        #   ANSI color codes
        #   RED = "\033[91m"
        #   GREEN = "\033[92m"
        #   YELLOW = "\033[93m"
        #   RESET = "\033[0m"
        #

        tabulated = []
        tabulated.append(["Total jobs", "Finished jobs", "Running jobs"])
        tabulated.append(
            [
                len(files),
                "\033[92m " + str(len(errs)) + "\033[00m",
                "\033[91m " + str(len(notFinished)) + "\033[00m",
            ]
        )

        print(tabulate.tabulate(tabulated, headers="firstrow", tablefmt="fancy_grid"))
        # print('queue 1 Folder in ' + ' '.join(list(map(lambda k: k.split('/')[-1], notFinished))))
        normalErrs = """Warning in <TClass::Init>: no dictionary for class edm::ProcessHistory is available
        Warning in <TClass::Init>: no dictionary for class edm::ProcessConfiguration is available
        Warning in <TClass::Init>: no dictionary for class edm::ParameterSetBlob is available
        Warning in <TClass::Init>: no dictionary for class edm::Hash<1> is available
        Warning in <TClass::Init>: no dictionary for class pair<edm::Hash<1>,edm::ParameterSetBlob> is available
        Warning in <TInterpreter::ReadRootmapFile>: class  podio::
        real
        user
        sys
        run locally
        No TTree was created for
        Warning in <Snapshot>: A lazy Snapshot action was booked but never triggered.
        cling::DynamicLibraryManager::loadLibrary(): libOpenGL.so.0: cannot open shared object file: No such file or directory
        Error in <AutoloadLibraryMU>: Failed to load library /cvmfs/sft.cern.ch/lcg/releases/ROOT/6.28.00
        TClass::Init:0: RuntimeWarning: no dictionary for class edm::Hash<1> is available
        TClass::Init:0: RuntimeWarning: no dictionary for class edm::ParameterSetBlob is available
        TClass::Init:0: RuntimeWarning: no dictionary for class edm::ProcessHistory is available
        TClass::Init:0: RuntimeWarning: no dictionary for class edm::ProcessConfiguration is available
        TClass::Init:0: RuntimeWarning: no dictionary for class pair<edm::Hash<1>,edm::ParameterSetBlob> is available
        During startup - Warning message:
        Setting LC_CTYPE failed, using "C" 
        """
        normalErrs = normalErrs.split("\n")
        normalErrs = list(map(lambda k: k.strip(" ").strip("\t"), normalErrs))
        normalErrs = list(filter(lambda k: k != "", normalErrs))

        toResubmit = []

        def normalErrsF(k):
            for s in normalErrs:
                if s in k:
                    return True
                elif k.startswith(s):
                    return True
            return False

        for err in errs:
            with open(err) as file:
                lines = file.read()
            txt = lines.split("\n")
            # txt = list(filter(lambda k: k not in normalErrs, txt))
            txt = list(filter(lambda k: not normalErrsF(k), txt))
            txt = list(filter(lambda k: k.strip() != "", txt))
            if len(txt) > 0:
                print("Found unusual error in")
                print(err)
                print("\n")
                print("\n".join(txt))
                print("\n\n")
                toResubmit.append(err)
        toResubmit = list(map(lambda k: "".join(k.split("/")[-2]), toResubmit))
        print(toResubmit)
        if len(toResubmit) > 0:
            print("\n\nShould resubmit the following files\n")
            print(
                "queue 1 Folder in "
                + " ".join(list(map(lambda k: k.split("/")[-1], toResubmit)))
            )
            if resubmit == 1:
                from mkShapesRDF.shapeAnalysis.BatchSubmission import BatchSubmission

                BatchSubmission.resubmitJobs(
                    batchFolder, tag, toResubmit, dryRun, queue
                )

        if resubmit == 2:
            # resubmit all the jobs that are not finished
            toResubmit = list(map(lambda k: "".join(k.split("/")[-1]), notFinished))
            print(toResubmit)
            from mkShapesRDF.shapeAnalysis.BatchSubmission import BatchSubmission

            BatchSubmission.resubmitJobs(batchFolder, tag, toResubmit, dryRun, queue)

    elif operationMode == 2:
        print(
            "",
            "".join(["#" for _ in range(20)]),
            "\n\n",
            "Merging root files",
            "\n\n",
            "".join(["#" for _ in range(20)]),
        )

        _samples = RunAnalysis.splitSamples(samples)
        print(len(_samples))
        outputFileTrunc = ".".join(outputFile.split(".")[:-1])
        mergeInputPath = str(outputPath).rstrip("/")
        filesToMerge = list(
            map(
                lambda k: f"{mergeInputPath}/{outputFileTrunc}__ALL__{k[0]}_{str(k[3])}.root",
                _samples,
            )
        )
        print("\n\nMerging files\n\n")
        print("\n\n", filesToMerge, "\n\n")

        print(f"Hadding files into {outputFileMap}")
        with open(f"filesToMerge_{outputFile}.txt", "w") as filesToMergeHandle:
            for fileToMerge in filesToMerge:
                filesToMergeHandle.write(f"{fileToMerge}\n")
        process = subprocess.Popen(
            f'hadd2 -j 10 {outputFileMap} @filesToMerge_{outputFile}.txt; \
            rm filesToMerge_{outputFile}.txt',
            shell=True,
        )

        process.communicate()

        if process.returncode == 0:
            print("Hadd was successful")
            cuts = cuts["cuts"]
            print(f"outputFileMap = {outputFileMap}")
            postProcessNuisances(
                outputFileMap, samples, aliases, variables, cuts, nuisances
            )
            if remoteOutputDestination:
                stage_out(outputFileMap, remoteOutputDestination, remoteIO)
        else:
            print("mkShapesRDF: Hadd failed!", file=sys.stderr)
            sys.exit(1)

    else:
        print("Operating mode was set to -1, nothing was done")


if __name__ == "__main__":
    main()
