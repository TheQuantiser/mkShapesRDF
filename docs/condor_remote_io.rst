Condor And Remote I/O
=====================

Runtime Setup
-------------

A fresh checkout intentionally has no generated ``start.sh``. Run ``./install.sh`` on a login or build node before the first ``source start.sh``; run it again after framework dependency changes or when ``myenv``, ``start.sh``, ``utils/bin/hadd2``, editable install metadata, or JSON POG data are missing or stale. The default prepared runtimes are x86-64 CentOS 7 with LCG 105 and x86-64 EL9-compatible systems with LCG 109. A different compatible LCG view can be selected with ``MKSHAPESRDF_LCG_VIEW=/path/to/view``. CVMFS, Python, ROOT/``root-config``, a C++ compiler, and sufficient local space are prerequisites.

``./install.sh --check`` is read-only and verifies that ``start.sh`` resolves this checkout. Dependency installation is fingerprinted by checkout path plus ``pyproject.toml``/``setup.cfg``; a second ordinary install skips pip when those inputs are unchanged. ``--force-dependencies`` deliberately repeats the network-capable pip step. ``--skip-dependencies`` is only for a complete, already prepared system/LCG Python stack and still prepares the local venv wrapper, ``hadd2``, data link/copy, and relocation-aware ``start.sh``.

Do not run ``install.sh`` inside normal Condor workers or packaged Condor workers. Normal interactive work should instead source the generated runtime setup from the repository root:

.. code:: bash

   cd /path/to/mkShapesRDF
   source start.sh

Condor Submission Execution
---------------------------

Framework submission normally executes ``condor_submit`` directly with an
argument vector. Some FNAL LPC login nodes provide an executable-text
``condor_submit`` wrapper whose first line is a shell command rather than a
shebang. A shell can run that wrapper through its traditional ``ENOEXEC``
fallback, while Python's direct process creation raises ``Exec format error``.

``BatchSubmission`` keeps direct argument-vector execution as the normal path.
Only when process creation itself raises ``ENOEXEC`` does it resolve the
executable and retry ``/bin/sh /resolved/condor_submit`` with every original
argument still a separate argument-vector element. It does not use
``shell=True`` or build a command string. Native executables and scripts with a
valid shebang stay on the direct path. Ordinary nonzero exits, missing or
non-executable commands, timeouts, and unrelated operating-system errors are
not retried. Initial submission and ``resubmitJobs()`` use this same helper and
write captured receipt/stderr before propagating a nonzero Condor result.

Both paths invoke ``condor_submit -terse``. For the installed HTCondor client,
``-terse`` changes successful standard output from human-oriented prose to only
the submitted job-ID range, for example ``84846211.0 - 84846211.1909``. It
does not change queue size, resource requests, scheduling, worker behavior, or
job state, and it cannot cause or repair ``ENOEXEC`` because executable format
is checked before HTCondor sees any option. The framework preserves the raw
standard output in ``submit.receipt.txt`` and standard error in
``submit.stderr.txt``. On success it prints the bounded job-ID range and both
evidence paths. On nonzero return it reports that the client ran and points to
the preserved stderr, where wrapper setup, collector/schedd selection,
authentication, and scheduler rejection can be distinguished.

Command-line topology and bounds
--------------------------------

``-b 0`` runs the analysis in the interactive process; ``-b 1`` generates and,
unless dry-run is selected, submits a Condor payload. ``-dR 1`` is framework
submission dry-run: package/JDL/scripts are generated but ``condor_submit`` is
not called. ``-l N`` limits events with ``RDataFrame.Range(N)`` after inputs
have been discovered and prepared. It is not a file-discovery limit. Use a
configuration's pinned-file interface, such as ``PINNED_FILES``, to keep
discovery and job count bounded.

Unpackaged Condor
-----------------

Unpackaged Condor validates the framework-generated batch payload on a shared filesystem. The worker relies on ``$MASTER`` being visible through AFS or an equivalent shared filesystem. The generated ``run.sh`` sources ``STARTPATH`` before running ``runner.py`` and keeps strict shell mode, with nounset disabled only while sourcing CVMFS/runtime setup.

For ZZ_CR, this mode is selected directly in
``PlotsConfigurationsRun3/ZH_4lMET/ZZ_CR/configuration.py`` with
``EXECUTION_PROFILE="shared_xrootd_local"``,
``"shared_xrootd_eos"``, ``"shared_xrootd_eos_production"``, or
``"shared_xrootd_fnal_eos_production"``. Source
``zzcr_lxplus_env.sh`` for CERN input and CERN CMS Store output, or
``zzcr_lxplus_fnal_env.sh`` for CERN input and FNAL CMS Store output. Both
select shared-checkout CERN Condor with no runtime package. The compatibility
``lxplus_env.sh`` entry point selects the CERN-output contract.

These site wrappers unconditionally reset their execution profile, I/O and
output modes, packaging mode, include base, proxy policy, endpoints, site,
output user, and default campaign. Set identity inputs such as ``CERN_USER``
or ``FNAL_USER`` before sourcing when necessary; set deliberate analysis or
profile overrides afterward. Re-sourcing a wrapper resets those overrides.

Local ZZ_CR smoke tests can also be selected from ``configuration.py`` with
``local`` for as-configured paths, ``local_xrootd`` for direct XRootD reads, or
``local_stagein`` for framework stage-in with local output.

The generated submit description should include:

.. code:: text

   should_transfer_files = YES
   when_to_transfer_output = ON_EXIT

Transfer ``script.py``, ``headers.hh``, ``runner.py``, and an explicit task-owned proxy file only when remote authentication is required. The framework resolves the active proxy from ``X509_USER_PROXY`` or ``/tmp/x509up_u<uid>``, copies it into the generated submit directory as ``x509up_u<uid>`` with restrictive permissions, and writes that copied path into ``transfer_input_files``. The transfer inputs use HTCondor's comma-delimited file-list syntax without quoting the complete list; quoting the complete list is interpreted as literal filename quotes by current FNAL schedds. If the generated JDL also declares ``x509userproxy``, it uses HTCondor's unquoted file-path syntax for the copied submit-directory proxy; quoted proxy paths are rejected by the current LXPLUS submit client. The generated ``run.sh`` then sets ``X509_USER_PROXY`` to ``$PWD/x509up_u<uid>``. The proxy is a job input, not an implicit dependency on the submit shell's node-local ``/tmp``.

Packaged Condor
---------------

Packaged Condor is the scratch-only mode. Enable it in configuration with ``condorRuntimePackage=True`` or at the CLI with ``--condor-runtime-package``. Regenerate the runtime archive from the current source and selected configuration before submitting. For an external ``PlotsConfigurationsRun3`` checkout, the builder packages the candidate framework and only the selected configuration directory; it does not use the common workspace parent as an import/package root. Dependencies outside that selected directory must be declared with repeatable ``--runtime-include PATH`` or the configuration list ``condorRuntimeIncludes``. This is an explicit dependency-closure contract, not permission to capture an entire external repository.

Archive members are sorted and have normalized ownership/timestamps/modes, so identical inputs produce identical gzip/tar bytes. A sidecar ``*.manifest.json`` records the archive hash, size, modes, roles, required members, and exclusions. Tracked ROOT calibration data are retained; ignored/untracked ROOT outputs are excluded. Source helpers whose names contain ``proxy`` (for example a physics ``proxyW.cc``) are not mistaken for credentials, while X.509 proxies, key formats, credential-like files, ``myenv``, ``start.sh``, ``.git``, caches, generated ``jobs``/``configs``/``rootFiles``, logs, prior archives, and campaign artifacts are excluded.

The worker uses a separately transferred standard-library bootstrap to reject absolute, traversal, duplicate, link, special-mode, special-type, or missing required archive members before extraction. It extracts under the Condor working/scratch directory, sets ``PYTHONNOUSERSITE=1``, puts the extracted package first on ``PYTHONPATH``, and may keep CVMFS Python paths needed for ROOT. Serialized paths below the framework, selected configuration, and declared runtime includes are relocated to the extracted tree. Framework imports must resolve from worker scratch, not from the source checkout. Remote-output jobs transfer the submit-directory proxy copy separately; the proxy is never part of the archive. Normal workers never run ``install.sh`` or pip.

For ZZ_CR, packaged mode is selected directly in ``configuration.py`` with
``packaged_xrootd_local``, ``packaged_xrootd_eos``,
``packaged_xrootd_eos_production``, ``packaged_stagein_local``,
``packaged_stagein_eos``, or ``packaged_stagein_eos_production``. These
profiles set ``condorRuntimePackage=True``, ``CONFIG_INCLUDE_BASE=runtime``,
the LCG 109 worker setup command, and explicit proxy transfer. The
``fnal_lpc_packaged_env.sh`` script is only a convenience wrapper that
forcibly selects the production direct-read packaged profile, FNAL endpoint,
runtime packaging, and output naming defaults. This prevents stale CERN or
stage-in settings from leaking into a new FNAL submission. Deliberate
alternatives, such as ``packaged_fnal_stagein_eos_production`` with
``INPUT_ACCESS_MODE=stage-in``, must be exported after the wrapper is sourced;
re-sourcing returns to direct-read packaged production.

LPC workers do not mount submit-host ``/uscms_data`` or user-home NFS, and they
must not depend on AFS or mounted EOS. Their working directory is
``_CONDOR_SCRATCH_DIR``. Packaged local-output jobs therefore leave a uniquely
named ROOT file in scratch and use ``transfer_output_files`` plus
``transfer_output_remaps`` to return it. Remote-output jobs instead call the
framework stage-out implementation and set an empty transfer-output list so a
large duplicate ROOT file is not returned.

Before submitting a packaged job, inspect the archive manifest for credentials, proxies, caches, generated outputs, absolute dependencies on the source checkout, and misspellings of the active ``PlotsConfigurationsRun3`` path.

Remote I/O Options
------------------

``--input-access-mode`` controls input handling. Common values are ``xrootd`` for direct remote reads and ``stage-in`` for copying input to task-owned scratch before processing. ``--remote-command-timeout`` and ``--remote-transfer-retries`` provide bounded policy overrides; zero retries is valid.

``--xrd-read-endpoint`` is the read endpoint, for example ``root://eoscms.cern.ch``. ``--xrd-discovery-endpoint`` controls config-time ``xrdfs`` directory listing and may differ from the read endpoint. An explicit CLI discovery endpoint also overrides legacy ``SearchFiles`` calls during configuration loading, so an unedited configuration that passes an empty mounted-site redirector can be compiled remotely. Mounted CERN-style ``/eos/cms/store/...`` production directories are normalized to ``/store/...`` for remote discovery; discovered LFNs are then mapped to the read endpoint for processing. ``--xrd-write-endpoint`` independently controls remote output writes. A complete ``root://`` output folder works directly; alternatively ``--output-folder /store/...`` plus the write endpoint builds the remote URL. Namespace policy remains explicit: a CERN ``/eos/user`` path is not automatically rewritten into an FNAL namespace.

Stage-in cleanup is controlled with ``--stage-in-cleanup`` and ``--preserve-stage-in-on-failure``. Remote output replacement behavior is controlled with ``--existing-output-policy``; use ``fail`` for first-write validation, ``skip-if-verified-identical`` for idempotent retries, and ``replace`` only when overwriting is intended.

Stage-in uses task-owned scratch (preferring ``_CONDOR_SCRATCH_DIR`` on a
worker), validates each copied ROOT file before analysis, and records the
source-to-local mapping. ``on-success`` removes scratch after successful ROOT
processing; failure preservation is controlled separately. The current
``skip-if-verified-identical`` contract verifies size, not a cryptographic
content digest.

Remote existence checks distinguish a definite storage ``not found`` response from authentication, authorization, timeout, and network failures. Only definite absence permits a create path; operational failures abort instead of being silently treated as a missing destination.

Bounded FNAL LPC Smoke Test
---------------------------

On an installed login-node checkout, source ``start.sh``; do not rerun
``install.sh`` unless the installed runtime is demonstrably missing or stale.
Use two pinned files, one file per job, and at most five events. For example:

.. code:: bash

   source start.sh
   cd PlotsConfigurationsRun3/ZH_4lMET/ZZ_CR
   export EXECUTION_PROFILE=local_xrootd
   export PINNED_SAMPLE=ZZ
   export PINNED_FILES_PER_JOB=1
   export PINNED_FILES='root://eoscms.cern.ch//store/...part0.root'
   export OUTPUT_MODE=local
   mkShapesRDF -c 1 -o 0 -b 0 -f . -l 5 \
     --input-access-mode xrootd \
     --xrd-discovery-endpoint root://eoscms.cern.ch \
     --xrd-read-endpoint root://eoscms.cern.ch

   export EXECUTION_PROFILE=packaged_xrootd_local
   export PINNED_FILES='root://eoscms.cern.ch//store/...part0.root,root://eoscms.cern.ch//store/...part1.root'
   mkShapesRDF -c 1 -o 0 -b 1 -dR 1 -f . -l 5 \
     --input-access-mode xrootd

For an unmodified external configuration, the equivalent generic dry-run can opt into packaging and site/output policy entirely from the CLI:

.. code:: bash

   mkShapesRDF -c 1 -o 0 -b 1 -dR 1 -f /path/to/selected/config \
     --input-access-mode xrootd \
     --xrd-discovery-endpoint root://eoscms.cern.ch \
     --xrd-read-endpoint root://eoscms.cern.ch \
     --condor-runtime-package --use-x509-proxy \
     --output-folder /path/to/returned/rootFiles

Add ``--runtime-include /path/to/shared/resource`` only for dependencies outside the selected configuration directory. Use a complete authorized remote URL, or ``/store/...`` plus ``--xrd-write-endpoint``, for remote output.

For stage-in, change the last option to ``--input-access-mode stage-in`` and
select the cleanup/preservation policy explicitly. Inspect the generated JDL,
worker script, per-job scripts, archive manifest, proxy mode, and output remaps
before removing ``-dR 1``. Submit only the bounded payload first. For a bounded
FNAL EOS test, set ``OUTPUT_MODE=test-remote``, an explicit campaign-owned
``TEST_OUTPUT_LFN=/store/user/<user>/mkShapesRDF_four_lepton_tests/<unique-campaign>/...``, and
``XRD_WRITE_ENDPOINT=root://cmseos.fnal.gov``.

The packaged profiles are batch-only and set
``CONFIG_INCLUDE_BASE=runtime`` for Condor workers. Interactive ``-b 0``
with a packaged profile fails during configuration with a precise remediation,
before input discovery, ROOT JIT, or output creation. Use ``local_xrootd`` or
``local_stagein`` for login-node tests; do not override the include token of a
production packaged profile. A full-production command must remain a separate
operator decision after the bounded dry-run and must not reuse the pinned-file
variables.

Use ``fail`` when validating that a campaign creates new outputs, ``skip-if-verified-identical`` for retried campaigns that should not rewrite matching ROOT files, and ``replace`` only for deliberate overwrite campaigns with cleanup evidence.

Validation Scope
----------------

For normal framework or ZZ_CR edits, start with lightweight checks:

.. code:: bash

   python3 -m py_compile \
     mkShapesRDF/lib/remote_io.py \
     mkShapesRDF/shapeAnalysis/BatchSubmission.py \
     mkShapesRDF/shapeAnalysis/mkShapesRDF.py \
     PlotsConfigurationsRun3/ZH_4lMET/ZZ_CR/*.py \
     tests/test_remote_io_unittest.py

   python3 -m unittest tests.test_remote_io_unittest -v

For four-lepton remote-I/O changes, an optional bounded dry-run can use
``PINNED_FILES`` with one or more comma/newline separated inputs and ``-dR 1``
to inspect generated Condor payloads without submitting a full production
campaign.

The 2026-07-12 bounded LXPLUS-to-FNAL two-input matrix passed for pinned ZZ inputs with non-identical optional branch schemas. The configuration now uses branch-aware fallbacks for optional pinned-input branches. That result certifies the bounded test matrix; it does not certify full production scale.

Artifact Hygiene
----------------

Development evidence belongs outside ``mkShapesRDF`` under the top-level ``codex_analysis`` directory. The repository should remain source-focused.

Generated Condor ``jobs/``, generated ``configs/``, ``rootFiles/``, package archives, logs, cache directories, proxies, credentials, and local virtual environments are not source deliverables unless deliberately retained as fixtures.

Packaged runtime archives must exclude ``codex_analysis``, ``myenv``, ``.git``, caches, generated ``jobs``/``rootFiles``/``configs``, credentials, proxies, local setup state, and previous package artifacts.

FNAL EOS Checks
---------------

FNAL EOS paths should use LFNs under ``/store/...`` and XRootD URLs like:

.. code:: text

   root://cmseos.fnal.gov//store/user/<user>/...

Verify remote outputs with ``xrdfs stat``, parent ``xrdfs ls``, ``xrdcp -f`` download, and a ROOT-open oracle before cleanup:

.. code:: bash

   xrdfs root://cmseos.fnal.gov stat /store/user/<user>/path/output.root
   xrdfs root://cmseos.fnal.gov ls /store/user/<user>/path
   xrdcp -f root://cmseos.fnal.gov//store/user/<user>/path/output.root output.root

Condor Evidence Standard
------------------------

A Condor job is complete only with all of the following evidence:

* raw ``condor_submit -terse`` receipt;
* cluster/proc id;
* periodic ``condor_q`` samples;
* event log containing submit, execute, and terminate events;
* worker stdout and stderr;
* successful narrow ``condor_history`` record with ``JobStatus=4``, ``ExitCode=0``, and ``ExitBySignal=false``;
* expected output;
* ROOT oracle for ROOT outputs;
* for remote outputs, ``xrdfs stat``, ``xrdcp`` download, ROOT oracle, remote ledger, and cleanup evidence.

An idle-only accepted job is not a pass. An empty ``condor_q`` result is not completion proof by itself.

For failures, triage in this order: event log termination status, ``condor_history`` exit fields, worker stderr, worker stdout, transferred output presence, ROOT-open oracle, and remote ``xrdfs``/``xrdcp`` evidence. For remote-output jobs, also check that the proxy was transferred explicitly and that the write endpoint matches the intended site.
