# ZZ_CR on FNAL CMS LPC Packaged Condor

This profile family is for the FNAL CMS LPC Condor cluster. It packages the
current `mkShapesRDF` checkout into a tarball transferred with each Condor job,
because LPC worker nodes must not rely on local checkout, AFS, or NFS paths
being mounted. It reads HWWNano inputs from CERN through XRootD. Outputs can
either be returned by HTCondor or staged to FNAL EOS through XRootD.

The 2026-07-12 bounded LXPLUS-to-FNAL two-input matrix passed in packaged mode with `ZZCR_CONDOR_RUNTIME_PACKAGE=1`, worker-scratch imports, and explicit proxy transfer. This validates the bounded pinned-input matrix and packaged Condor plumbing, not full production scale.

## Documentation basis

- FNAL LPC Condor docs: `https://uscms.org/uscms_at_work/computing/setup/batch_systems.shtml`
- FNAL LPC worker-node/NFS notes: `https://uscms.org/uscms_at_work/computing/setup/condor_worker_node.shtml`
- FNAL LPC EOS docs: `https://uscms.org/uscms_at_work/computing/LPC/usingEOSAtLPC.shtml`
- CERN/CMS AAA xrootd workbook: `https://twiki.cern.ch/twiki/bin/view/CMSPublic/WorkBookXrootdService`

The LPC docs state that Condor worker nodes do not provide the interactive-node
NFS view, that their working directory is `_CONDOR_SCRATCH_DIR`, and that EOS
I/O in workers should be done with XRootD. The packaged profiles therefore set
`ZZCR_CONDOR_RUNTIME_PACKAGE=1`. They never run `install.sh` in a worker.

On current LPC login nodes, `condor_submit` can be an executable text wrapper
without a shebang. `BatchSubmission` first uses normal direct argv execution.
If and only if process creation raises `ENOEXEC`, it resolves that wrapper and
retries it as `[/bin/sh, resolved-wrapper, ...original arguments]`. No
`shell=True` or unquoted command string is used. Initial submission and
resubmission share this behavior; native binaries and valid-shebang scripts,
including the normal LXPLUS case, continue to execute directly.

The command includes `-terse`, which changes only successful client output to
a stable job-ID range. The raw range is saved in `submit.receipt.txt`; raw
stderr is saved in `submit.stderr.txt`. After an FNAL compatibility fallback,
the framework prints either an explicit accepted range or a checked client
failure. The fallback line by itself is neither a job state nor proof that
submission failed.

## Setup

From the repository root on an LPC interactive node:

```bash
source start.sh
cd PlotsConfigurationsRun3/ZH_4lMET/ZZ_CR
# In configuration.py set:
# ZZCR_EXECUTION_PROFILE = "packaged_xrootd_eos_production"
# Or source zzcr_fnal_lpc_packaged_env.sh as a convenience wrapper.
export ZZCR_EOS_USER=<cern-username>
voms-proxy-init --voms cms -valid 192:00
mkShapesRDF -c 1 -o 0 -b 1 -f . -l -1
```

Use `-dR 1` first to inspect `jobs/<tag>/condor/<tag>/submit.jdl` and `run.sh` before submitting.
For proxy-authenticated jobs, `transfer_input_files` must list the copied proxy
inside that generated submit directory, not `/tmp/x509up_u<uid>` from the
interactive node.

For an interactive direct-read smoke test, select `local_xrootd`, local output,
and one pinned complete CERN XRootD URL. For a packaged two-proc dry-run, select
`packaged_xrootd_local`, two pinned URLs, one file per job, and `-b 1 -dR 1`.
Change to `local_stagein` or `packaged_stagein_local` to test task-owned scratch
copying and cleanup.

The packaged profiles' C++ include base is worker-relative `runtime` and those
profiles are batch-only. A packaged profile combined with `-b 0` fails early,
before discovery, JIT, or output. This prevents both a missing-runtime include
and accidental production EOS stage-out from a login-node smoke test:

```bash
export ZZCR_PINNED_SAMPLE=ZZ
export ZZCR_PINNED_FILES_PER_JOB=1
export ZZCR_PINNED_FILES='root://eoscms.cern.ch//store/...part0.root'
export ZZCR_EXECUTION_PROFILE=local_xrootd
export ZZCR_OUTPUT_MODE=local
mkShapesRDF -c 1 -o 0 -b 0 -f . -l 5 --input-access-mode xrootd

export ZZCR_PINNED_FILES='root://eoscms.cern.ch//store/...part0.root,root://eoscms.cern.ch//store/...part1.root'
export ZZCR_EXECUTION_PROFILE=packaged_xrootd_local
mkShapesRDF -c 1 -o 0 -b 1 -dR 1 -f . -l 5 --input-access-mode xrootd
```

Inspect the two-proc JDL, package, proxy separation, and output contract before
removing `-dR 1`. For remote smoke output use only a unique owned namespace
under `/store/user/<CMS-EOS-user>/mkShapesRDF_zzcr_tests/<campaign>/...` with
`ZZCR_OUTPUT_MODE=test-remote`. A full-production submission is a separate
operator decision and must be generated without `ZZCR_PINNED_*` variables.

## Variables

- `ZZCR_YEAR`: analysis year key, default `2024`.
- `ZZCR_EXECUTION_PROFILE`: `packaged_xrootd_eos_production` for production
  remote output, `packaged_xrootd_eos` for a bounded test namespace,
  `packaged_xrootd_local` for Condor-returned output, and the corresponding
  `packaged_stagein_*` profiles for stage-in.
- `ZZCR_INPUT_ACCESS_MODE`: profile default `xrootd` or `stage-in`; the CERN
  `/eos/cms/store/...` paths in `cmshww_HWWNano_file_list_22to25.txt` are read
  as `root://eoscms.cern.ch//store/...`.
- `ZZCR_XRD_READ_ENDPOINT`: CERN read endpoint, default `root://eoscms.cern.ch`.
- `ZZCR_XRD_DISCOVERY_ENDPOINT`: CERN discovery endpoint, default `root://eoscms.cern.ch`.
- `ZZCR_XRD_WRITE_ENDPOINT`: FNAL LPC EOS endpoint, default `root://cmseos.fnal.gov`.
- `ZZCR_OUTPUT_MODE`: profile-dependent; production profiles use `production-remote`, test profiles use `test-remote`, local profiles use `local`.
- `ZZCR_EOS_USER`: CERN/CMS username for `/store/user/<name>/...`. Set it explicitly on LPC if your FNAL username differs.
- `ZZCR_PRODUCTION_OUTPUT_LFN`: default `/store/user/${ZZCR_EOS_USER}/mkShapesRDF_rootfiles/fnal_lpc_packaged/rootFile`.
- `ZZCR_CONDOR_RUNTIME_PACKAGE`: profile default `1`; the generated JDL transfers `mkshapesrdf_runtime.tgz`.
- `ZZCR_CONDOR_RUNTIME_SETUP`: profile default sources the LCG 109 EL9 view from CVMFS.
- `ZZCR_CONFIG_INCLUDE_BASE`: packaged-profile default `runtime`, so compiled C++ macro includes point at the extracted package in worker scratch. Packaged profiles require batch execution; local profiles resolve the same macro from the checkout.
- `ZZCR_USE_X509_PROXY`: profile default `1`; the framework copies the active proxy into the submit directory and the generated JDL transfers that copy separately.
- `ZZCR_PINNED_FILES`: optional test override. Keep multiple files comma/newline separated; do not split `root://` URLs on colons.

Config-time discovery and runtime reading are separate. The discovery endpoint
lists normalized `/store/...` LFNs with `xrdfs`; the read endpoint constructs
the URLs given to ROOT. In `as-configured` mode, mounted LXPLUS paths remain
unchanged. A requested remote discovery failure is fatal and contextual rather
than silently producing an empty production sample.

## Output path rule

FNAL EOS remote writes must use the LPC xrootd endpoint and an LFN:

```text
root://cmseos.fnal.gov//store/user/<cern-username>/mkShapesRDF_rootfiles/fnal_lpc_packaged/rootFile
```

Do not use local checkout paths, `/afs/...`, `/uscms_data/...`, `/eos/cms/...`, or `/eos/uscms/...` as Condor worker dependencies. The package is the code dependency; xrootd is the input/output dependency.

Package archives must exclude `codex_analysis`, `myenv`, `.git`, caches, generated `jobs`/`configs`/`rootFiles`, credentials, proxies, local setup state, logs, and previous package artifacts. The proxy is a separate Condor input, never part of `mkshapesrdf_runtime.tgz`.

For `ZZCR_OUTPUT_MODE=local`, packaged jobs rename the final ROOT file in worker
scratch to a collision-free name containing the logical job ID. HTCondor
returns and remaps that file into the deterministic submit-side `rootFiles`
directory. The worker does not copy to the submit checkout. For
`test-remote`/`production-remote`, framework `stage_out` writes an explicit
`/store/...` LFN through `root://cmseos.fnal.gov`; mounted EOS paths and
interactive-node aliases are invalid worker targets.

Before production, inspect holds with `condor_q`, the complete event log and
worker logs, then confirm terminal fields with `condor_history`. An idle job or
an empty queue is not completion evidence. A bounded two-file/five-event result
does not certify production-scale discovery, sandbox fan-out, or scheduling.
