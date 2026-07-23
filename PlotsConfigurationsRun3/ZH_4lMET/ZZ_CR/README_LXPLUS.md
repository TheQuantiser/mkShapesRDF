# ZZ_CR on CERN LXPLUS

This profile runs the ZZ_CR configuration from the shared checkout on CERN
LXPLUS. It reads the HWWNano files that live on CERN EOS through XRootD and
writes the produced ROOT files to the FNAL LPC EOS namespace with
`root://cmseos.fnal.gov`.

The FNAL-side 2026-07-12 regression generated and inspected this
shared-checkout mode with `ZZCR_CONDOR_RUNTIME_PACKAGE=0`, but did not submit it
from LXPLUS. That result is `STATIC_REGRESSION_PASSED_LIVE_NOT_RUN`; it validates
payload compatibility, not a new live LXPLUS result or full production scale.

LXPLUS normally executes its native or valid-shebang `condor_submit` directly.
The generic framework fallback is considered only for a process-creation
`ENOEXEC`; it does not use `shell=True`, alter arguments, or add FNAL host
detection.

## Documentation basis

- CERN/CMS AAA xrootd workbook: `https://twiki.cern.ch/twiki/bin/view/CMSPublic/WorkBookXrootdService`
- CERN EOS documentation: `https://eos-docs.web.cern.ch/diopside/`
- FNAL LPC EOS documentation for the target output namespace: `https://uscms.org/uscms_at_work/computing/LPC/usingEOSAtLPC.shtml`

The file list `cmshww_HWWNano_file_list_22to25.txt` contains CERN-mounted examples such as `/eos/cms/store/group/.../nanoLatino_*.root`. In this profile those mounted paths are converted to XRootD reads with:

```text
root://eoscms.cern.ch//store/group/phys_higgs/cmshww/...
```

## Setup

From the repository root:

```bash
source start.sh
cd PlotsConfigurationsRun3/ZH_4lMET/ZZ_CR
# In configuration.py set:
# ZZCR_EXECUTION_PROFILE = "shared_xrootd_eos_production"
# Or source zzcr_lxplus_env.sh as a convenience wrapper.
voms-proxy-init --voms cms -valid 192:00
mkShapesRDF -c 1 -o 0 -b 1 -f . -l -1
```

Use `-dR 1` for a dry-run Condor generation.

For remote-output Condor jobs, inspect the generated `submit.jdl` before real
submission. Its `transfer_input_files` line must contain the copied proxy under
`jobs/<tag>/condor/<tag>/x509up_u<uid>`, not the submit shell's
`/tmp/x509up_u<uid>` path. The generated `run.sh` then points
`X509_USER_PROXY` at `$PWD/x509up_u<uid>` inside worker scratch.

## Variables

- `ZZCR_EXECUTION_PROFILE`: `shared_xrootd_eos_production` for the
  production-output shared-checkout LXPLUS profile. Use `shared_xrootd_eos`
  for a bounded test namespace, `shared_xrootd_local` for Condor-returned
  local output, and `local_xrootd` or `local_stagein` for login-node smoke
  tests.
- `ZZCR_YEAR`: analysis year key, default `2024`.
- `ZZCR_INPUT_ACCESS_MODE`: profile default `xrootd`, so
  `/eos/cms/store/...` and `/store/...` inputs become XRootD URLs.
- `ZZCR_XRD_READ_ENDPOINT`: CERN read endpoint, default `root://eoscms.cern.ch`.
- `ZZCR_XRD_DISCOVERY_ENDPOINT`: endpoint used for file discovery, default `root://eoscms.cern.ch`.
- `ZZCR_XRD_WRITE_ENDPOINT`: FNAL LPC EOS endpoint, default `root://cmseos.fnal.gov`.
- `ZZCR_OUTPUT_MODE`: profile default `production-remote`, meaning framework stage-out writes to FNAL EOS.
- `ZZCR_EOS_USER`: CERN/CMS username used in `/store/user/<name>/...`; set this explicitly if it differs from `$USER`.
- `ZZCR_PRODUCTION_CAMPAIGN`: production campaign directory before the tag leaf, default `lxplus`.
- `ZZCR_PRODUCTION_OUTPUT_LFN`: output LFN under FNAL EOS, default `/store/user/${ZZCR_EOS_USER}/mkShapesRDF_rootfiles/lxplus/<tag>`.
- `ZZCR_CONDOR_RUNTIME_PACKAGE`: profile default `0`; LXPLUS mode uses the visible checkout and `STARTPATH`.
- `ZZCR_CONFIG_INCLUDE_BASE`: profile default is the repository root, so the
  compiled C++ helper include points at the checked-out macro.
- `ZZCR_PINNED_FILES`: optional comma/newline separated input override for tests. Use full xrootd URLs or CERN mounted paths from the file list.

## Output path rule

Use FNAL EOS LFNs, not CERN mount paths, for remote writes. Correct:

```text
root://cmseos.fnal.gov//store/user/<cern-username>/mkShapesRDF_rootfiles/lxplus/<tag>
```

Do not configure FNAL output as `/eos/cms/...` or `/eos/uscms/...`; the framework remote stage-out expects a `/store/...` LFN plus `root://cmseos.fnal.gov`.
