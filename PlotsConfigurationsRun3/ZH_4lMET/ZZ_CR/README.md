# ZZ_CR (ZH_4lMET) quick guide

Minimal map for running this config without guessing.

## Core files (what matters)

- `configuration.py`  
  Main switchboard: tag, output mode, batch folder, EOS/x509 flags, redirector.
- `samples.py`, `aliases.py`, `variables.py`, `cuts.py`, `nuisances.py`, `structure.py`, `plot.py`  
  Standard analysis definitions.
- `jdl_dict_zzcr.py`  
  Condor payload/JDL helper for EOS+x509 mode:
  - checks proxy,
  - creates target dir (`xrdfs mkdir -p`),
  - stages proxy,
  - runs runner,
  - `xrdcp` output.

## Operation modes

### 1) Default/local mode
- `useEOSUserOutput = False`
- `useX509Proxy = False`
- Outputs go to local `rootFiles/...`

### 2) EOS+x509 mode (Condor)
- `useEOSUserOutput = True`
- `useX509Proxy = True`
- Output base: `/eos/cms/store/user/<user>/...`
- Redirector configurable with:
  - `xrdRedirector = "cms-xrd-global.cern.ch"` (default)
  - or `cmsxrootd.fnal.gov`, `xrootd-cms.infn.it`, etc.

## Usage

```bash
# from this folder
mkShapesRDF -c 1 -o 0 -b 1 -l -1
```

### Inspect jobs

```bash
condor_q
cat condor/<tag>/<sample_idx>/out.txt
cat condor/<tag>/<sample_idx>/err.txt
cat condor/<tag>/<sample_idx>/log.txt
```

## Practical notes

- If EOS mode is on, keep a valid proxy alive:
  ```bash
  voms-proxy-init --voms cms -valid 192:0
  ```
- In EOS mode, transfer logs are printed in `out.txt` with `[ZZCR-JDL]` markers.
- If you don’t want EOS/x509 behavior, keep both flags off and use local mode.
