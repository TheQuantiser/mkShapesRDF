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
- Optional per-sample DATA run override (`runs`) when a dataset exists only in a subset of eras
  (must be a duplicate-free subset of year-level `data.runs`)
- Data run tags
- Common sample weights (`mc.common_weight`, `data.common_weight`)
- `l2tight_era` for lepton WP expansion
- b-tag veto algorithm / WP
- Luminosity nuisance (`name`, `value`)
- Integrated luminosity (`lumi_fb`) used by `configuration.py` and `plot.py`
- Storage path policy (`storage`) for default/per-kind/per-sample EOS trees
- Lepton-pair ID policy (`lepton_ids`) for electron/muon WP and pair-level pass thresholds

## Per-sample EOS base directory configuration

`samples.py` now resolves EOS base directories through `zzcr_year_config.json` so you can
set a global default and override it by kind (`mc`/`data`) and by specific sample.

In each year block, use:

- `storage.default_tree_base_dir`: fallback for everything
- `storage.mc_tree_base_dir`: default for MC (falls back to `default_tree_base_dir`)
- `storage.data_tree_base_dir`: default for DATA (falls back to `default_tree_base_dir`)
- `storage.mc_tree_base_dir_by_sample`: per-MC-sample override, keyed by MC sample name
- `storage.data_tree_base_dir_by_sample`: per-DATA-dataset override, keyed by `dataset`
- `storage.data_tree_base_dir_by_stream`: per-DATA-stream override, keyed by `stream`

Resolution priority is:

1. Per-sample override
2. Per-kind default (`mc_tree_base_dir`/`data_tree_base_dir`)
3. Year default (`default_tree_base_dir`)
4. Legacy fallback (`/eos/cms/store/group/phys_higgs/cmshww/amassiro/HWWNano`)

Example (for data produced under another user area on EOS):

```json
"storage": {
  "default_tree_base_dir": "/eos/cms/store/group/phys_higgs/cmshww/amassiro/HWWNano",
  "mc_tree_base_dir": "/eos/cms/store/group/phys_higgs/cmshww/amassiro/HWWNano",
  "data_tree_base_dir": "/eos/cms/store/group/phys_higgs/cmshww/amassiro/HWWNano",
  "mc_tree_base_dir_by_sample": {
    "ZZ": "/eos/cms/store/group/phys_higgs/cmshww/<producer>/HWWNano"
  },
  "data_tree_base_dir_by_sample": {
    "Muon": "/eos/cms/store/group/phys_higgs/cmshww/<producer>/HWWNano"
  },
  "data_tree_base_dir_by_stream": {
    "EGamma": "/eos/cms/store/group/phys_higgs/cmshww/<producer>/HWWNano"
  }
}
```

## Lepton and b-tag IDs in JSON (year/era aware)

The ZZ_CR year JSON is now the source of truth for these IDs:

- `lepton_ids.electron_wp`
- `lepton_ids.muon_wp`
- `lepton_ids.z0_min_pass`
- `lepton_ids.x_min_pass`
- `lepton_ids.z0_pt_mins`
- `lepton_ids.x_pt_mins`
- `btag.algo`
- `btag.veto_wp`

`zzcr_selection_config.py` reads `lepton_ids` from the selected year instead of hard-coding WPs.
This keeps the lepton-ID and b-tag veto settings coherent across eras and avoids hidden constants in Python/C++.

## Run-3 policy in this config

- Only non-`_OLD` campaigns are used.
- 2024 DATA includes non-`_OLD` ReReco/prompt eras configured in JSON (`C/D/E/F/G/H/I`).
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
