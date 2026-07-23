# ZZ_CR Manual

Run-3 `ZH_4lMET` ZZ control-region configuration for `mkShapesRDF`.

Active directory:

```bash
mkShapesRDF/PlotsConfigurationsRun3/ZH_4lMET/ZZ_CR
```

This is the migrated full ZZ_CR configuration. It supports local jobs, CERN
LXPLUS shared-checkout Condor, and FNAL LPC packaged Condor with CERN xrootd
inputs and FNAL EOS stage-out.

## Quick Start

```bash
cd mkShapesRDF
source start.sh
cd PlotsConfigurationsRun3/ZH_4lMET/ZZ_CR
# In configuration.py set:
# ZZCR_EXECUTION_PROFILE = "shared_xrootd_eos"
voms-proxy-init --voms cms -valid 192:00
mkShapesRDF -c 1 -o 0 -b 1 -dR 1 -f . -l 1
```

Remove `-dR 1` only after inspecting `jobs/<tag>/condor/<tag>/submit.jdl` and
`run.sh`.

Submission uses direct argv execution. If a site's executable text
`condor_submit` wrapper lacks a shebang and direct process creation raises
`ENOEXEC`, the framework performs one argument-safe `/bin/sh` retry of the
resolved wrapper. It never uses `shell=True`; initial submission and
resubmission share the helper, while native and valid-shebang executables stay
direct.

Both submission paths retain `-terse`: a successful client prints only its
cluster/proc range, which is stored verbatim in `submit.receipt.txt`. The option
does not affect scheduling or job state. On FNAL, the ENOEXEC line is an
informational compatibility choice, followed by an explicit scheduler-success
receipt or a checked error pointing at `submit.stderr.txt`.

Use the FNAL packaged convenience wrapper on LPC:

```bash
source zzcr_fnal_lpc_packaged_env.sh
export ZZCR_EOS_USER=<cern-or-cms-username>
```

The wrapper exports a complete packaged-production profile plus identity/output
conveniences, and those exports persist in the current shell. It does not run
Condor itself. A later local command in that shell must explicitly select a
local profile; packaged profiles are batch-only and reject `-b 0` before file
discovery or ROOT JIT.

## File Map

| File | Role |
| --- | --- |
| `configuration.py` | Runtime tag, output paths, remote I/O, Condor packaging. |
| `zzcr_year_config.json` | Year-dependent MC, DATA, luminosity, triggers, IDs, storage. |
| `zzcr_year.py` | Loads and validates the selected year. |
| `samples.py` | Builds MC/DATA samples from JSON or pinned test files. |
| `zzcr_selection_config.py` | Shared lepton-pair and trigger-path settings. |
| `aliases.py`, `variables.py`, `cuts.py` | Analysis definitions using the selected year. |
| `nuisances.py`, `plot.py`, `structure.py` | Plotting, nuisances, and sample structure. |
| `zzcr_lxplus_env.sh` | CERN shared-checkout convenience wrapper. |
| `zzcr_fnal_lpc_packaged_env.sh` | FNAL LPC packaged Condor convenience wrapper. |

## Choose The Mode

Edit the single line near the top of `configuration.py`:

```python
ZZCR_EXECUTION_PROFILE = "local"
```

Supported profiles are:

| Profile | Contract |
| --- | --- |
| `local` | Local/as-configured input and local output under `jobs/<tag>/<tag>`; no Condor package. |
| `local_xrootd` | Local output with direct CERN XRootD input; no Condor package. |
| `local_stagein` | Local output with input staged to task-owned scratch; no Condor package. |
| `shared_xrootd_local` | Shared-checkout Condor, CERN XRootD input, Condor-returned local output. |
| `shared_xrootd_eos` | Shared-checkout Condor, CERN XRootD input, test EOS stage-out. |
| `shared_xrootd_eos_production` | Shared-checkout Condor, CERN XRootD input, production EOS stage-out. |
| `packaged_xrootd_local` | Packaged Condor, CERN XRootD direct input, Condor-returned local output. |
| `packaged_xrootd_eos` | Packaged Condor, CERN XRootD direct input, test EOS stage-out. |
| `packaged_xrootd_eos_production` | Packaged Condor, CERN XRootD direct input, production EOS stage-out. |
| `packaged_stagein_local` | Packaged Condor, stage-in input, Condor-returned local output. |
| `packaged_stagein_eos` | Packaged Condor, stage-in input, test EOS stage-out. |
| `packaged_stagein_eos_production` | Packaged Condor, stage-in input, production EOS stage-out. |

Environment variables are convenience overrides for fast tests. CLI flags such
as `--input-access-mode`, `--xrd-read-endpoint`, `--xrd-discovery-endpoint`,
`--xrd-write-endpoint`, `--existing-output-policy`,
`--condor-runtime-package`, `--runtime-include`, and `--use-x509-proxy`
remain the highest-precedence framework-supported overrides.

Safe bounded FNAL local example after the site wrapper has previously been
sourced:

```bash
export ZZCR_EXECUTION_PROFILE=local_xrootd
export ZZCR_OUTPUT_MODE=local
export ZZCR_PINNED_SAMPLE=ZZ
export ZZCR_PINNED_FILES_PER_JOB=1
export ZZCR_PINNED_FILES='root://eoscms.cern.ch//store/.../nanoLatino_ZZ__part0.root'
mkShapesRDF -c 1 -o 0 -b 0 -f . -l 5
```

Here `-l 5` limits events after input preparation; it does not limit discovery.
Pinned files are what make the input inventory bounded. `-b 1 -dR 1` instead
generates the Condor package/JDL without calling `condor_submit`.

## Runtime Parameters

Set these as environment variables before running `mkShapesRDF`.

| Parameter | Default | Function | Set when |
| --- | --- | --- | --- |
| `ZZCR_EXECUTION_PROFILE` | `local` in `configuration.py` | Selects the profile table entry used to derive I/O, output, proxy, package, setup, and include-base values. | Testing a profile without editing the file or using a site wrapper. |
| `ZZCR_YEAR` | `2024` | Selects the year key in `zzcr_year_config.json`; used by all modules. | Running another era: `2022`, `2022EE`, `2023`, `2023BPix`, `2024`. |
| `ZZCR_SITE_PRESET` | profile-dependent | Labels the site preset and feeds production-output defaults. | Naming custom site output. |
| `ZZCR_OUTPUT_MODE` | profile-dependent | Chooses `local`, `test-remote`, or `production-remote` output. | Overriding a profile's output policy. |
| `ZZCR_EOS_USER` | `$CERN_USER` or `$USER` | Username used in `/store/user/<user>/...` defaults. | Your shell username is not your CMS EOS username. |
| `ZZCR_TEST_CAMPAIGN` | current `tag` | Names the test-output campaign. | Grouping repeated test submissions. |
| `ZZCR_PRODUCTION_CAMPAIGN` | profile-dependent site/campaign label | Names the production-output campaign before the tag leaf. | Grouping production by site or campaign while keeping each run tag-separated. |
| `ZZCR_TEST_OUTPUT_LFN` | current code default test LFN | Remote LFN for `test-remote`. | Always set explicitly for test remote output. |
| `ZZCR_PRODUCTION_OUTPUT_LFN` | profile-dependent under `/store/user/<user>/mkShapesRDF_rootfiles/.../<tag>` | Remote LFN for `production-remote`. | Any production or site-preset run. |
| `ZZCR_USE_X509_PROXY` | profile-dependent; forced on for remote output | Transfers the active proxy into Condor worker scratch. | Needed for authenticated XRootD read/write or packaged mode. |

`ZZCR_TEST_OUTPUT_LFN` and `ZZCR_PRODUCTION_OUTPUT_LFN` must be LFNs beginning
with `/store/`, not mounted paths such as `/eos/...`.
The default test LFN is whitespace-free, but set `ZZCR_TEST_OUTPUT_LFN`
explicitly for every bounded campaign so its ownership and cleanup scope are
unambiguous.

## Remote I/O Parameters

| Parameter | Default | Function | Set when |
| --- | --- | --- | --- |
| `ZZCR_INPUT_ACCESS_MODE` | profile-dependent; `local` uses `as-configured` | Input path handling. Valid: `as-configured`, `xrootd`, `stage-in`. | Use `xrootd` for CERN/FNAL Condor; use `stage-in` to copy inputs to worker scratch before processing. |
| `ZZCR_XRD_READ_ENDPOINT` | `root://eoscms.cern.ch` | Endpoint used to read logical `/store/...` or mounted `/eos/cms/store/...` inputs. | Reading from a different redirector. |
| `ZZCR_XRD_DISCOVERY_ENDPOINT` | read endpoint | Endpoint used for file discovery. | Discovery and read endpoints differ. |
| `ZZCR_XRD_WRITE_ENDPOINT` | `root://cmseos.fnal.gov` | Endpoint prepended to remote output LFNs. | Writing somewhere other than FNAL LPC EOS. |
| `ZZCR_STAGE_IN_SCRATCH` | `_CONDOR_SCRATCH_DIR`, then `$TMPDIR` or `/tmp` | Scratch root for `stage-in` inputs. | Worker scratch must be controlled explicitly. |
| `ZZCR_STAGE_IN_CLEANUP` | `on-success` | Stage-in cleanup policy. Valid: `on-success`, `always`, `never`. | Debugging or conserving scratch space. |
| `ZZCR_PRESERVE_STAGE_IN_ON_FAILURE` | `1` | Keeps staged inputs after failed jobs unless set to `0`, `false`, or `False`. | Disable only when failed-job scratch must be removed. |
| `ZZCR_EXISTING_OUTPUT_POLICY` | `fail` | Existing output behavior. Valid: `fail`, `replace`, `skip-if-verified-identical`. | Rerunning into a non-empty output directory. |
| `ZZCR_REMOTE_COMMAND_TIMEOUT` | `120` | Timeout in seconds for `xrdcp`/`xrdfs` commands. | Slow sites or large files need more time. |
| `ZZCR_REMOTE_TRANSFER_RETRIES` | `2` | Retries for transient remote-copy/stat failures. | Unstable network or redirector behavior. |

CLI options such as `--input-access-mode`, `--xrd-read-endpoint`,
`--xrd-discovery-endpoint`, `--xrd-write-endpoint`, and
`--existing-output-policy` override the environment resolved through
`configuration.py`. Production discovery uses the discovery endpoint to list
LFNs; the resulting processing URLs use the read endpoint. The two endpoints
need not be the same.

## Condor Packaging Parameters

| Parameter | Default | Function | Set when |
| --- | --- | --- | --- |
| `ZZCR_CONDOR_RUNTIME_PACKAGE` | profile-dependent | Packages the current checkout as `mkshapesrdf_runtime.tgz` and transfers it with each job. | Worker nodes cannot see the checkout path. |
| `ZZCR_CONDOR_RUNTIME_PACKAGE_NAME` | `mkshapesrdf_runtime.tgz` | Name of the transferred runtime archive. | Avoiding archive-name collisions. |
| `ZZCR_CONDOR_RUNTIME_SETUP` | profile-dependent; packaged profiles source LCG 109 | Worker setup commands separated by `;;`. | Packaged jobs need CVMFS or site setup. |
| `ZZCR_CONDOR_RUNTIME_INCLUDES` | empty | Extra package inputs separated by `;;`. CLI `--runtime-include` is preferred for ad hoc additions. | Dependencies live outside the selected config directory. |
| `ZZCR_CONFIG_INCLUDE_BASE` | checkout root for non-packaged profiles; `runtime` for packaged profiles | Base path used by compiled C++ helper includes. Packaged profiles require `-b 1`; workers resolve the helper below extracted scratch `runtime/`. | Advanced package-layout debugging, not converting a packaged production profile into local mode. |
| `STARTPATH` | required when not packaged | Shell setup file embedded in shared-checkout Condor `run.sh`. | LXPLUS/shared-checkout mode. |

For remote-output Condor jobs, the generated JDL must transfer the copied proxy
from `jobs/<tag>/condor/<tag>/x509up_u<uid>`, not `/tmp/x509up_u<uid>`.
For packaged local-output jobs, the final ROOT file remains in worker scratch
under a logical-job-specific name. HTCondor's `transfer_output_files` and
`transfer_output_remaps` return it to the submit directory. The worker never
copies directly to an `/uscms_data`, home-NFS, or AFS path.

## Pinned-File Test Parameters

Pinned mode bypasses production discovery and creates only one sample.

| Parameter | Default | Function | Set when |
| --- | --- | --- | --- |
| `ZZCR_PINNED_FILES` | unset | Comma- or newline-separated ROOT inputs. | Fast validation, schema probing, or remote I/O tests. |
| `ZZCR_PINNED_SAMPLE` | `ZZ` | Sample name created for pinned inputs. | Testing a non-`ZZ` sample name. |
| `ZZCR_PINNED_FILES_PER_JOB` | `1` | Files per Condor job in pinned mode. | Grouping several pinned files per job. |

Example:

```bash
ZZCR_PINNED_FILES='root://eoscms.cern.ch//store/path/input1.root,root://eoscms.cern.ch//store/path/input2.root' \
ZZCR_OUTPUT_MODE=test-remote \
mkShapesRDF -c 1 -o 0 -b 1 -dR 1 -f . -l 1
```

## NanoAOD Trigger-Object Schema

The trigger-audit aliases assume the NanoAODv15 `TrigObj_filterBits` layout for
all supported ZZ_CR year profiles.  This is intentionally independent of
`l2tight_era`: older 2022-2023 profile strings and input campaign names may
still contain `v12`, but they no longer select the legacy NanoAODv12
trigger-object bit map.

The v15 assumption controls the decoded per-lepton trigger-object branches:
double-electron leg bits use electron bits 4 and 5, the electron leg of
electron-muon triggers uses bit 6, and the single-electron object match uses
the explicit `Ele30_WPTight_Gsf` bit 18 rather than the broad WPTight bit.
`TRIGGER_AUDIT.md` records the CMSSW/NanoAOD evidence and the postprocessing
branches saved for this diagnostic tree.

## Year JSON Parameters

Edit `zzcr_year_config.json` when physics inputs change. Do not hard-code these
values in Python.

| JSON key | Function | Set when |
| --- | --- | --- |
| `default_year` | Year used when `ZZCR_YEAR` is unset. | Changing the campaign default. |
| `years.<year>.mc.production` | MC production directory component. | MC campaign changes. |
| `years.<year>.mc.steps` | MC processing-step directory component. | NanoAOD/postprocessing steps change. |
| `years.<year>.mc.samples` | MC sample names to discover. Empty lists are allowed for staged configs. | Adding/removing MC samples. |
| `years.<year>.mc.common_weight` | Common MC event weight. | Weight policy changes. |
| `years.<year>.data.reco` | DATA reco directory component. | DATA campaign changes. |
| `years.<year>.data.steps` | DATA processing-step directory component. | DATA postprocessing changes. |
| `years.<year>.data.runs` | Allowed DATA run tags. | Adding/removing eras. |
| `years.<year>.data.samples[]` | DATA dataset, stream, trigger, and optional run subset. | Dataset availability or trigger priority changes. |
| `years.<year>.data.common_weight` | Common DATA weight. | DATA filter policy changes. |
| `years.<year>.trigger_paths` | Maps aggregate `Trigger_*` flags to concrete `HLT_*` branches. | Trigger menu changes or downstream HLT inspection is needed. |
| `years.<year>.l2tight_era` | Lepton WP era used by aliases/variables. | Lepton ID configuration changes. |
| `years.<year>.lepton_ids` | Electron/muon WPs, pair pass counts, pair pT thresholds. | ZZ pair-ID policy changes. |
| `years.<year>.btag.algo` | Jet b-tag branch used for veto. | Algorithm changes. |
| `years.<year>.btag.veto_wp` | B-tag veto working point. | Era-specific WP changes. |
| `years.<year>.lumi_nuisance` | Luminosity nuisance name and value. | Datacard/plot nuisance policy changes. |
| `years.<year>.lumi_fb` | Integrated luminosity used by config and plots. | Luminosity update. |
| `years.<year>.storage` | EOS tree base directory defaults and overrides. | Samples live under different producers or storage roots. |

Storage priority is:

1. Per-sample override.
2. Per-stream DATA override.
3. Per-kind default: `mc_tree_base_dir` or `data_tree_base_dir`.
4. Year default: `default_tree_base_dir`.
5. Legacy fallback: `/eos/cms/store/group/phys_higgs/cmshww/amassiro/HWWNano`.

DATA sample entries require:

```json
{"dataset": "EGamma", "stream": "EGamma", "trigger": "Trigger_sngEl"}
```

Add `runs` only when that dataset exists for a subset of the year-level
`data.runs`.

## Output Path Rules

Use remote LFNs with xrootd endpoints:

```text
root://cmseos.fnal.gov//store/user/<user>/mkShapesRDF_rootfiles/<campaign>/<tag>
```

Do not use `/afs/...`, `/uscms_data/...`, `/eos/cms/...`, or `/eos/uscms/...` as
Condor worker output targets. The framework expects a `/store/...` LFN plus an
xrootd write endpoint.

## Validation

Lightweight syntax and unit checks:

```bash
source start.sh

python -m py_compile \
  mkShapesRDF/lib/remote_io.py \
  mkShapesRDF/shapeAnalysis/BatchSubmission.py \
  mkShapesRDF/shapeAnalysis/mkShapesRDF.py \
  PlotsConfigurationsRun3/ZH_4lMET/ZZ_CR/*.py \
  tests/test_remote_io_unittest.py

python -m unittest tests.test_remote_io_unittest -v

python -m pytest tests/test_zzcr_configuration_profiles.py -q
```

The 2026-07-12 bounded matrix passed with two pinned ZZ inputs, CERN xrootd
reads, local and FNAL remote outputs, LXPLUS shared-checkout Condor, and FNAL LPC
packaged Condor. That validates the bounded pinned-input workflow and Condor
plumbing; it does not certify full production scale.
