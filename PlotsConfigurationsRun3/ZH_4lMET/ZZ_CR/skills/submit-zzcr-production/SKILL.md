---
name: submit-zzcr-production
description: Submit fresh ZZ_CR mkShapesRDF Condor campaigns for one or more Run 3 eras, including full all-sample/all-event production. Use when preparing, validating, submitting, or recording ZZ_CR jobs from FNAL LPC or CERN, especially when site wrappers, XRootD input, EOS destinations, profiles, file splitting, event limits, or stale compiled pickles could change the result.
---

# Submit ZZ_CR Production

## Overview

Submit the existing ZZ_CR workflow without changing analysis source. Resolve the site contract first, apply campaign settings afterward, compile a fresh configuration, and preserve enough evidence to identify every accepted cluster and its exact output.

## Read the live workflow

Work from the repository root. Read `PlotsConfigurationsRun3/ZH_4lMET/ZZ_CR/README.md` and the submission, status, and merge sections of `PlotsConfigurationsRun3/ZH_4lMET/ZZ_CR/USAGE.MD` before acting. Treat those files and the environment wrappers as authoritative if details differ from this skill.

Do not create a new submission script merely to launch an ordinary campaign. Use the existing wrappers and `mkShapesRDF` command.

## Establish the site contract

Source `start.sh`, then exactly one wrapper:

| Submission and destination | Wrapper |
| --- | --- |
| CERN to CERN CMS Store | `zzcr_lxplus_env.sh` |
| CERN to FNAL CMS Store | `zzcr_lxplus_fnal_env.sh` |
| FNAL LPC to FNAL CMS Store | `fnal_lpc_packaged_env.sh` |

Use paths relative to `PlotsConfigurationsRun3/ZH_4lMET/ZZ_CR/` for the wrapper names above. Direct CERN XRootD input reads are the normal default for all three workflows. Select whole-file stage-in only when explicitly requested.

Set identity inputs such as `FNAL_USER` or `CERN_USER` before the wrapper when the wrapper needs them. Set `YEAR`, profiles, filters, file splitting, and campaign names after the wrapper because sourcing a wrapper intentionally resets its complete site contract.

Do not enable shell nounset while sourcing `start.sh`; external LCG setup scripts may inspect unset variables.

## Define the requested analysis scope

For a full detailed all-sample, all-event histogram campaign, apply:

```bash
export ANALYSIS_PASS=ALL
export CATEGORY_PROFILE=detailed
export HISTOGRAM_PROFILE=analysis
export SAMPLE_PROFILE=presentation
export ENABLE_SYSTEMATICS=0
export HISTOGRAMS=1
export FILES_PER_JOB=10
unset SAMPLE_FILTER LIMIT_FILES_PER_SAMPLE DATA_STREAM_FILTER
```

Change `FILES_PER_JOB` only when requested or justified by completed job timing and resource evidence. `presentation` selects every logical MC output in the active era's configured plot groups plus DATA; it does not create a nonprompt estimate.

Use a unique, descriptive `PRODUCTION_CAMPAIGN` for each era. Treat campaign suffixes requested for one run as one-off labels, not durable conventions.

## Preflight without mutating analysis code

Confirm:

- the requested era is one of `2022`, `2022EE`, `2023`, `2023BPix`, or `2024`;
- `voms-proxy-info -identity -path -timeleft` reports a usable proxy;
- the selected wrapper resolves the intended input and output endpoints;
- the destination `/store/user/<user>/mkShapesRDF_rootfiles` is reachable with the destination's XRootD or EOS tools;
- no sample, data-stream, file, or event pilot limit remains active;
- direct reads remain selected unless stage-in was explicitly requested.

Do not perform whole-file input copies as a preflight for direct-read production.

## Compile and submit fresh jobs

Always combine fresh compilation and submission for production:

```bash
mkShapesRDF -c 1 --submit \
  -f PlotsConfigurationsRun3/ZH_4lMET/ZZ_CR \
  -l -1 -q workday
```

The `-c 1` is mandatory. Submission without it can load the selected or latest compiled pickle and silently retain stale profiles, filters, event limits, payload paths, endpoints, or destinations. The `-l -1` makes the all-event contract explicit.

For multiple eras, repeat the same command after setting `YEAR` and an era-specific `PRODUCTION_CAMPAIGN`. Keep all other requested settings unchanged. Wait for each command's scheduler result before proceeding to the next era.

## Resolve an ambiguous Condor timeout

A client timeout is not proof of rejection. Before retrying:

1. Check for `submit.receipt.txt` in the exact timestamped job-control directory.
2. Inspect a generated job's `log.txt` for event `000` and its cluster ID.
3. Query that cluster or schedd when responsive.
4. Check that no `condor_submit` process remains.

If event `000` exists, record the cluster as accepted and do not resubmit. If no receipt, submission event, queue entry, or client process exists, submit the already-generated `submit.jdl` once rather than recompiling. On FNAL LPC, invoke the site wrapper compatibly as `/bin/sh /usr/local/bin/condor_submit -terse submit.jdl` when direct execution reports `ENOEXEC`. At CERN, use the site's ordinary `condor_submit -terse submit.jdl` command.

Never infer rejection solely from missing terminal output, and never create a duplicate large cluster to obtain a cleaner receipt.

## Record the result

For every era, report:

- era and complete campaign name;
- exact timestamped mkShapesRDF tag and configuration pickle;
- cluster ID, first/last process, and process count;
- scheduler name when known;
- full XRootD output path;
- full receipt and submit-stderr paths when produced;
- profiles, systematics state, files per job, and explicit all-event setting.

Do not claim that jobs completed merely because submission was accepted. Do not merge, plot, remove, or resubmit jobs unless the user requested those actions.

## Keep the checkout clean

Generated configs, job controls, receipts, ROOT files, plots, caches, and local operational directories must remain ignored. After submission or documentation edits, inspect `git status` and stage only intentional source, skill, or documentation files.
