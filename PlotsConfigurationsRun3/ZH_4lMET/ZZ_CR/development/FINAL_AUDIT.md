# Final compact-production audit

Recorded on 2026-08-09 after local and FNAL Condor validation.

## Current-contract addendum

This document preserves the dated minimal/category-refinement evidence below.
The current executable contract subsequently added three independent features:

- `DY_ENRICHED` applies the same `abs(Z0_mass - 91.1876) < 15` selected-Z
  window as ZZCR/SR. Every ordinary DY projection is mechanically mirrored as
  `DY_ENRICHED_*` with the matching histogram tier and DY weight.
- `minSelectedPairMass > 12 GeV` is evaluated over all six unordered masses
  formed from exactly the selected Z0+X leptons and applied only to ZZCR/SR;
  DY does not use it. Invalid selected inputs fail closed. The AN2019/238 v9
  XSF, XDF, and ZZCR boundaries remain 65, 70, and 75--105 GeV.
- `SAMPLE_PROFILE=commissioning` activates DATA plus live DY and ZZ outputs,
  while `SAMPLE_PROFILE=presentation` activates every logical output owned by
  the current plot groups. For 2024 those scopes contain 8 and 55 logical
  outputs. Nonprompt/fake background is not included.

The tag and generated contract now include the sample profile, and the
contract records profile groups, profile inventory, actual selection source,
and active outputs. The current focused suite passes 48 tests. A bounded
direct-XRootD 2024 ZZ run produced a healthy 839-histogram, no-tree ROOT file
and persisted the ZZCR/SR-only minimum-pair cut exactly. The ordinary FNAL
production mode is packaged direct XRootD input with FNAL CMS Store stage-out;
whole-file stage-in remains an explicit fallback. See `../CONFIGURATION.md`,
`../USAGE.MD`, and `SELECTION_SOURCE_NOTE.md` for the live runbook and source
mapping.

## Category refinement

The later commissioning refinement preserves the original validated evidence
below and makes `standard + analysis` the recommended ordinary view. The live
contract has 47 declared projections and 1,043 sparse actions: 24 DY, 12 ZZCR,
and 11 SR categories. The complete profile comparison is 150 minimal, 1,043
standard, 536 flavor, 402 stream, 570 trigger-priority, and 1,133 detailed
actions. Debug is a curated 1,553-action union and requires an explicit large
plan override. The 35-directory/839-action runtime measurements below predate
the additive `DY_ENRICHED` projection and remain historical evidence.

Variable activation now depends on `(physics_region, view_type)`. Inclusive,
flavor, stream, and curated-intersection views use 25/50, 19/31, 17/25, and
15/15 DY/four-lepton variables respectively. Category metadata and the
analysis contract now expose the view, partition family, exclusivity,
cross-family overlap, and diagnostic purpose without ID parsing.

Truth-table tests mechanically prove every requested flavor/topology/stream
partition and intersection. A selection-only occupancy study covers staged
v12/v15 ZZ across all five eras plus 2024 ZH and DATA. A real 100-event
standard run produced a healthy 35-directory sparse ROOT file. The updated
focused suite passes 36 tests. Ten packaged standard jobs spanning 2024 DATA,
ZZ, ZH, and v12 ZZ all exited zero. Their peak `MemoryUsage` was 647 MB, only
14.3% above the prior 566 MB peak despite a 6.712x action increase. Exact
evidence is recorded in `fnal_category_pilot_receipt.json`.

No physics selection, weight, correction, sample partition, nominal one-job-
set semantics, or FNAL stage-in/stage-out behavior changed during that
category-only refinement. The later current-contract changes are identified
in the addendum above. The original minimal full-production package remains
immutable at commit `0de38da`.

For future submissions, the FNAL wrapper was subsequently changed to make
packaged direct CERN XRootD reads the default. The packaged whole-file
stage-in profile remains an explicit option. This operational default avoids
the partial-destination `xrdcp` retry failure observed in the immutable first
full campaign; it does not change analysis or FNAL EOS stage-out semantics.

## Original minimal-production result

The original full-production graph was `ALL + minimal + analysis`: three final
categories, 53 active variables from a 509-entry immutable registry, and 125
actual histogram actions. The previous 46-category by 509-variable rectangle
had 23,414 actions, so the minimal booking reduction is 187.312x.

The exact minimal categories are `DY_ALL`, `ZZCR_ALL`, and `SR_ALL`. The
runner applies `SelectedLeptonSF_Z` below DY and
`SelectedLeptonSF_ZX*BTagVetoSF` below ZZCR/SR, after the common
`XSWeight*METFilter_Common*puWeight*TriggerSF_event` MC weight. DATA has its
exclusive stream-trigger/MET-filter weight and unit realizations of MC-only
corrections.

## Physics and configuration review

1. Luminosities and run lists remain the explicit values in
   `year_config.json`. They were not changed without a new luminosity source;
   schema checks require finite positive luminosities, unique run tags, and
   known DATA streams.
2. All five era dictionaries validate. Their overlap models partition every
   physical input exactly once between consumed and pass-through sources and
   produce unique logical output names.
3. The declared YR5 production-normalization ratios are retained and checked
   to target only active physical aliases. No unsupported central-factor
   change was made.
4. The `Vg`, `VgS`, `WZ`, and `ZZ` phase-space/source partition is unchanged
   by the category refactor and passes disjoint/complete validation.
5. `category_binning.json` is still preserved as proxy-derived provenance.
   Registry metadata labels that contract; it is not represented as a new
   full-statistics optimization.
6. The 509-definition 2024 registry contains opt-in low-level diagnostics,
   but the 53-variable analysis activation removes their default duplication
   cost. Definitions and hashes do not change when activated/deactivated.
7. Applicability sentinels remain outside visible physics axes with `fold=0`,
   or are represented by empty value vectors. Default active variables do not
   fold a `-999` sentinel into a physics bin.
8. `plot.py` and `structure.py` consume sample/process dictionaries rather
   than hard-coded old category IDs. The sparse ROOT directories use the clean
   IDs directly.
9. Output tags now include year, analysis pass, category profile, histogram
   profile, sample profile, product, systematic mode, and UTC timestamp.
10. `USAGE.MD` and `CONFIGURATION.md` were rewritten; stale 46-category,
    rectangular 509-variable, local-map, CERN-only, and hard-coded 4 GB
    instructions were removed.

## B-tag payload decision

The full CVMFS JSONs were recursively inspected and evaluated with
correctionlib. Every era contains the required `<tagger>_wp_values`,
`<tagger>_comb`, and `<tagger>_light` corrections and all tested central,
correlated, and uncorrelated shifts are finite. Their loose WPs are 0.0470,
0.0499, 0.0358, 0.0359, and 0.0246.

Those JSONs do not contain the exact `bjet_eff`, `cjet_eff`, and `ljet_eff`
objects required by the fixed-WP event formula. The five selected ROOT maps
were therefore placed at
`/store/user/mwadud/ZH4lMET/btag/` and are accessed through full
`root://cmseos.fnal.gov//store/...` URLs. Local/remote Adler-32 checks matched,
ROOT opened all maps, and an end-to-end 5 eras x 3 flavors x tagged/untagged x
5 shifts probe produced 150 finite evaluations. The two-input design is
required; a ROOT efficiency map alone is not a scale-factor payload.

## Execution evidence

- Local CERN stage-in copied a 47,440,187-byte 2024 ZZ file in 5.434 s,
  opened a 12,465-entry `Events` tree, matched SHA-256, and cleaned only the
  task-owned scratch.
- Real local `ALL` processing of 100 events completed in 34.74 s with
  1,016,500 KB maximum RSS and wrote a healthy 81,426-byte sparse ROOT file.
- Real staged files for 2022EE, 2023, and 2023BPix completed in 35.55, 36.91,
  and 37.36 s with approximately 1.00--1.02 GB login-node RSS. Together with
  the 2022 and 2024 pilots this exercises every configured TrigMaker era.
- Condor clusters 85068165, 85068167, 85068168, and 85068169 all exited zero.
  Ten remote ROOT files were opened from FNAL EOS and each had exactly
  25/50/50 variable directories. `DY_ALL/X_mass` was absent and the ZZCR/SR
  copies were present. Condor `MemoryUsage` peaked at 566 MB.
- Worker logs show CERN URLs mapped into `/srv/mkShapesRDF_stagein_*` on
  FNAL scratch. All outputs exist only below the FNAL EOS campaigns recorded
  in `fnal_pilot_receipt.json`.

## Packaging and contract

The fresh 81,333,994-byte runtime archive contains the configuration-local
runner, worker payload logic, category/histogram registries, contract writer,
and trigger/b-tag macros. Worker scripts and the serialized payload have no
`/uscms_data` or `/afs` dependency. Submit-side absolute transfer paths in the
JDL are expected. The proxy is worker-local with mode 0600. The external FNAL
b-tag map remains an authenticated XRootD URL rather than being duplicated in
the archive.

Every compile writes the self-digested `analysis_contract.json` both beside
job controls and in `configs/`. Tests compare its cuts, category factors,
variables, binning, context, and digest to executable state.

## Remaining limitations

- Unified `ALL + ENABLE_SYSTEMATICS=1` remains deliberately fail-closed. A
  direct ROOT regression proved that `RDataFrame::Redefine` rejects a weight
  column after it depends on variations. Sparse conversion/save does retain
  variations when no category-weight redefine is required.
- Core stage-in prints the exact source-to-scratch mapping but does not expose
  a separate timer; the receipt therefore records the measured standalone
  xrdcp time and labels Condor runner wall times as including stage-in.
- The repository had no tracked standalone `trigger_regression.py` or
  `btag_regression.py` at the starting SHA. Real five-era event runs and the
  explicit 150-point b-tag probe supply the corresponding execution evidence.
- Binning derived from the DY+ZZ proxy is useful provenance, not a claim of
  final full-statistics physics optimization.
