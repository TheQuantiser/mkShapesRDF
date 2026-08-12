# ZH4l migration report

## Revision and scope

- Starting SHA: `3659c2e930d58b8a3df387ca9080c9443bb528e8`
- Starting branch/remote: local and `origin/ZH_devel` both pointed to the
  starting SHA after fetch on 2026-08-12.
- Final SHA: the commit containing this report; recorded exactly in the push
  handoff because a Git commit cannot contain its own future object ID.
- Core changes: none under the repository's `mkShapesRDF/` package.
- Legacy changes: none. The pre-existing modified/untracked work under
  `PlotsConfigurationsRun3/ZH_4lMET/` was neither edited nor staged, following
  the user's explicit instruction that existing configurations remain intact.

## Directory map

| Old owner | New owner |
|---|---|
| `ZH_4lMET/ZZ_CR/` | `ZH4l/ZZCR/` for nominal production; shared physics in `ZH4l/common/`; DY/diagnostic projections in `ZH4l/Closure/` |
| `ZH_4lMET/PairingStudy/` | `ZH4l/Pairing/` |
| untracked `ZH_4lMET/DY_ZZ_ClosureStudy/` present at execution | `ZH4l/Closure/` |
| overlapping `ZZ_CR/*env.sh` | `ZH4l/env/{lxplus,lxplus_fnal,fnal}.sh` |
| `year_config.json/.py` copies | one `ZH4l/common/eras.json` and `eras.py` |
| duplicated sample materializers | one `ZH4l/common/catalog.py` |
| duplicated object/trigger/btag helpers | one set under `ZH4l/common/macros/` |

No legacy file was removed because that would conflict with the later explicit
user constraint. Within the new family, redundant copied `README_LEGACY.md`
files were removed after their useful content was consolidated into leaf
READMEs; generated caches, configs, ROOT files, PDFs, TeX output, receipts, and
campaign products are ignored.

## Public alias map

| Old | New | Old | New |
|---|---|---|---|
| `Z0_idx` | `Z_idx` | `X_idx` | `X_idx` |
| `Z0_mass` | `mZ` | `X_mass` | `mX` |
| `Z0_pt` | `ptZ` | `X_pt` | `ptX` |
| `Z0_eta` | `etaZ` | `X_eta` | `etaX` |
| `Z0_phi` | `phiZ` | `X_phi` | `phiX` |
| `pT4l` | `pt4l` | `m4l` | `m4l` |
| `phi4l` | `phi4l` | `minSelectedPairMass` | `minMll4l` |
| `sumLeptonCharge` | `q4l` | `hasValidZ0` | `validZ` |
| `hasValidX` | `validX` | distinct-index predicate | `validZX` |
| `Passes2lOrderedPt` | `passZPt` | `Passes4lOrderedPt` | `pass4lPt` |
| `fifthLeptonVeto` | `veto5l` | `physicalBtagVeto` | `bVeto` |
| `Z0_isEE/MM` | `isZee/isZmm` | `X_isEE/MM` | `isXee/isXmm` |
| `X_isSF/DF` | `isXSF/isXDF` | `SelectedLeptonSF_Z/ZX` | `LepSF_Z/ZX` |
| `TriggerSF_Z/ZX` | unchanged | `BTagVetoSF` | `bVetoSF` |
| `dataStreamPriority` | `streamPriority` | `triggerFamilyPriority` | `triggerPriority` |

Native `mll` and `TriggerSFWeight_2l/4l` are explicitly forbidden collision
names. Technical implementation columns use `ZH4l_...`.

## Consolidation and native reuse

The following custom application layers were replaced by native mkShapesRDF
for nominal ZZCR: `zz_cr_runner.py`, sparse category/histogram profile
managers, worker-payload serialization, custom histogram output, and embedded
site orchestration. `ZZCR` now uses native `RunAnalysis`, `SearchFiles`,
variation/nuisance handling, plot dictionaries, batch packaging, and remote-I/O
interfaces. Existing processor outputs from LeptonSF, LeptonScaleSmearing, and
MET filters are consumed rather than recreated.

Retained custom code and reason:

- selected trigger adapter/wrapper: canonical TrigMaker owns and supplies the
  payload readers and formulae, but native outputs act on leading objects; ZH4l
  deliberately evaluates the same formula on selected `Z_idx`/`X_idx`;
- fixed-WP b-tag helper: no inspected native utility supplies the exact
  validated veto-efficiency event ratio with the same CleanJet acceptance;
- Pairing runner: variable-specific raw/signed/absolute scalar and vector
  weight domains cannot be represented by the native single graph weight;
- Closure runner: the 54-category/295-action sparse matrix and stage/variable
  factors are not a rectangular native booking;
- Pairing and Closure macros: these own study-specific truth/score and closure
  quantities, respectively.

## Runner, category, and histogram comparison

| Analysis | Old runner | New runner | Old categories/actions | New categories/actions |
|---|---|---|---:|---:|
| nominal ZZCR/SR production | custom sparse runner | native `default` | current legacy standard profile: 47 / 1,043; earlier curated validated receipt: 35 / 839 | 6 / 54 |
| Pairing | custom study runner | minimal migrated study runner | 2 / 110 | 2 / 110 |
| Closure | custom sparse study runner | minimal migrated study runner | 54 / 295 | 54 / 295 |

The ZZCR difference is intentional scope decomposition, not a dropped nominal
region: DY, stream, trigger, and diagnostic projections are owned by Closure.
Pairing and Closure study scopes are unchanged.

## Equivalence evidence

The authoritative validated inputs/kernels are byte-identical old-to-new:

| Contract | SHA-256 |
|---|---|
| era/process/payload JSON | `32933872686956c97d44c95dfb965c477142ea8cc696a009c1fa00f59d3d7fcd` |
| selected Z/X, pT, fifth-veto, low-mass and observable C++ kernel | `ce5d3e32a4b1ec0f90f2f9f839981501d9dccad417941ca51778a9916c61c762` |
| selected-domain canonical trigger wrapper | `0b6558b380bd6ba8a79ced32cf224ff09bc50ff9900c701c65faaa8861b3100e` |
| fixed-WP b-veto/event-SF kernel | `9633b720b09c35a5f596b7ca0fe9c171eaffd5619a5f44d6b8e305eb16759359` |
| Pairing candidate/truth/score kernel | `07733b8a7c6fe05f1788f6235c3e584751d26e05359f5e370244645a762f058c` |

Automated tests freeze these hashes, map each renamed public alias to the same
kernel, exercise real C++ candidate/boundary semantics, enforce exact sample
inventories, preserve Pairing truth/summary behavior, freeze Closure stage
expressions, and fail on alias collisions or leaf redefinitions.

New ZZCR was then run through native RunAnalysis against one real remotely
opened `ZZ` NanoAOD file per era with `LIMIT_FILES_PER_SAMPLE=1`, 100 input
events, and nominal-only nuisances:

| ERA | TrigMaker key exercised | preselection count | wall time | peak RSS |
|---|---|---:|---:|---:|
| 2022 | `Full2022v12` | 63 | 24.16 s | 909,476 KB |
| 2022EE | `Full2022EEv12` | 72 | 31.80 s | 908,760 KB |
| 2023 | `Full2023v12` | 66 | 44.87 s | 916,132 KB |
| 2023BPix | `Full2023BPixv12` | 67 | 44.39 s | 914,344 KB |
| 2024 | `Full2024v15` | 64 | 25.04 s | 906,936 KB |

The migrated Pairing leaf was also compiled and run on three real 2024 logical
inputs (two ZH and one ZZ), 100 input events each: 17, 22, and 2 events passed
preselection; combined compile/run wall time was 47.27 s and peak RSS was
1,005,216 KB. The Closure major profile compiled with 54 cuts and 295 sparse
actions in 14.88 s at 584,912 KB peak RSS.

Legacy evidence already present in the immutable source records 100-event
ZZCR wall times of 34.74–37.36 s and approximately 1.00–1.02 GB local RSS for
all five trigger eras; its packaged standard campaign peaked at 647 MB worker
memory for 839 actions. The new bounded timings are comparable or lower and
the nominal action count is reduced from 1,043 to 54. The new 2024 ZZCR
configuration-only compile took 6.04 s and 583,436 KB. No separate legacy
configuration-only timing was recorded in the available audit, so no invented
number is reported. A full-systematics 2024 configuration compile, including
real-file systematic branch inspection, took 13.70 s and 912,344 KB.

## Site/runtime validation

- CERN direct-XRootD discovery/read: passed on all five era smoke tests.
- Runtime path/config serialization and native local output: passed.
- LXPLUS shared-checkout contract: statically validated by environment script
  and native dry-run serialization; not submitted during this migration.
- FNAL packaged contract: passed a new dry-run build. The 81,192,142-byte
  runtime archive, manifest, worker script, JDL, proxy transfer entry, CERN
  read endpoint, FNAL write endpoint, and runtime-rebased `ZH4l/common` macro
  paths were inspected. No new remote Condor job was submitted.
- LXPLUS-to-FNAL stage-out contract: statically validated, not remotely
  submitted.

## Remaining limitations

1. The user explicitly prohibited changing existing `ZH_4lMET`
   configurations. Therefore the old tree remains as an immutable duplicate
   validation oracle; it was not replaced with a deprecation stub or removed,
   even though the original task's preferred final state requested retirement.
2. To avoid generating any new artifact under that protected old tree, the
   migration did not execute a second old configuration in place. Equivalence
   is established by byte-identical validated JSON/C++ kernels, frozen renamed
   expressions and existing legacy real-event evidence, plus new real-event
   execution in every era. A fully independent old/new per-event dump was not
   produced in this turn.
3. No new CERN/FNAL Condor job or remote stage-out was launched. The local
   native graph and remote reads are validated; site scripts still require a
   valid user proxy and writable destination at production time.
