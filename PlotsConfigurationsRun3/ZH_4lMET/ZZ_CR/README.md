# ZZ_CR (ZH_4lMET)

Configuration package for the `ZH_4lMET` ZZ control region in Run 3.

## Layout

- `configuration.py`  
  Entry point for runtime settings (tag, output mode, EOS/x509, selected year).
- `zzcr_year_config.json`  
  Single source of year-dependent settings.
- `zzcr_year.py`  
  Loader/validator for the selected year and helpers shared by other modules.
- `samples.py`, `aliases.py`, `variables.py`, `cuts.py`, `nuisances.py`, `plot.py`, `structure.py`  
  Analysis definitions using the selected year configuration.
- `jdl_dict_zzcr.py`  
  Condor JDL helper for EOS+x509 workflows.

## Year selection

The active year is controlled in `configuration.py` with:

- `ZZCR_YEAR = "..."` (for example: `2024`, `2023BPix`, `2023`, `2022EE`, `2022`)

`configuration.py` exports this key to the process environment; all ZZ_CR modules read the same selected year through `zzcr_year.py`.
The output `tag` is built from this year key and the UTC date (`YYYYMMDD`).

## What is year-configured

From `zzcr_year_config.json`, ZZ_CR uses:

- MC production and steps
- DATA reco and steps
- Explicit MC sample list
- Explicit DATA sample list (`dataset`, `stream`, `trigger`)
- Data run tags
- Common sample weights (`mc.common_weight`, `data.common_weight`)
- `l2tight_era` for lepton WP expansion
- b-tag veto algorithm / WP
- Luminosity nuisance (`name`, `value`)
- Integrated luminosity (`lumi_fb`) used by `configuration.py` and `plot.py`

## Run-3 policy in this config

- Only non-`_OLD` campaigns are used.
- 2024 DATA defaults to non-prompt ReReco runs (`C/D/E`).
- For years where only prompt-era datasets are available in repository inputs (notably `2022EE`, `2023`, `2023BPix`), those prompt entries are retained.
- Year configuration is validated at load time (required keys, non-empty sample lists, and required DATA sample fields).

## Execution

Run from this directory:

```bash
mkShapesRDF -c 1 -o 0 -b 1 -l -1
```

Inspect Condor jobs (when batch mode is enabled):

```bash
condor_q
cat jobs/<tag>/condor/<sample_idx>/out.txt
cat jobs/<tag>/condor/<sample_idx>/err.txt
cat jobs/<tag>/condor/<sample_idx>/log.txt
```

## Job output layout

All local job artifacts are namespaced under one tag directory:

- `jobs/<tag>/condor`
- `jobs/<tag>/configs`
- `jobs/<tag>/plots`
- `jobs/<tag>/rootFiles` (local mode)

In EOS mode, ROOT outputs are written to:

- `/eos/cms/store/user/<user>/mkShapesRDF_rootfiles/<tag>/rootFile/`

This keeps local and remote outputs coherent and non-clashing across runs.

## EOS/x509 notes

- Local mode: `useEOSUserOutput = False`, `useX509Proxy = False`
- EOS mode: `useEOSUserOutput = True`, `useX509Proxy = True`
- Keep a valid proxy in EOS mode:

```bash
voms-proxy-init --voms cms -valid 192:0
```
