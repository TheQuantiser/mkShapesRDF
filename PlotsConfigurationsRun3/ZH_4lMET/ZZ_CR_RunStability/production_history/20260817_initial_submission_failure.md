# 2026-08-17 initial full-submission failure

This record preserves the durable facts from the first all-era FNAL LPC
submission before its generated local `jobs/` directories were removed at
operator request.

The submission used the run-stability `standard`/`analysis`/`presentation`
nominal profile, all configured samples and files, ten input files per job,
direct CERN XRootD input, packaged FNAL workers, and FNAL EOS stage-out.

| Era | Cluster | Schedd | Jobs | Final status |
| --- | ---: | --- | ---: | --- |
| 2022 | 3849888 | `lpcschedd4.fnal.gov` | 505 | 505 completed with exit code 1 |
| 2022EE | 3849889 | `lpcschedd4.fnal.gov` | 1,216 | 1,216 completed with exit code 1 |
| 2023 | 85155682 | `lpcschedd6.fnal.gov` | 707 | 707 completed with exit code 1 |
| 2023BPix | 30071843 | `lpcschedd5.fnal.gov` | 455 | 455 completed with exit code 1 |
| 2024 | 3849890 | `lpcschedd4.fnal.gov` | 3,967 | 3,967 completed with exit code 1 |

All 6,850 worker standard-error files were byte-identical. Their SHA-256 was
`f1227bd81342b044720cb27c02bb0cdf9aec8afe0771b8ca75778f04463f15af` and
their complete diagnostic was:

```text
WARNING: Cannot verify AC signature! Underlying error: Cannot find certificate of AC issuer for vo cms
```

No worker standard output reached the launcher's proxy-mode message or the
analysis. No configured remote output directory was created. Reproducing the
worker check with the staged proxy returned exit code 1 when `X509_VOMS_DIR`
was empty and exit code 0 with:

```text
/cvmfs/grid.cern.ch/etc/grid-security/vomsdir
```

The leaf-local FNAL wrapper was therefore updated to serialize that CVMFS VOMS
trust directory into the worker launcher before proxy validation. The
original CERN-XRootD-input/FNAL-EOS-output transport contract was retained;
mkShapesRDF core was not changed.
