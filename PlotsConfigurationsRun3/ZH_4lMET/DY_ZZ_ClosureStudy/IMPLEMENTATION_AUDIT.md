# Implementation audit

## Provenance and scope

- Starting branch: `ZH_devel`
- Starting SHA: `3659c2e930d58b8a3df387ca9080c9443bb528e8`
- Audit date: 2026-08-12
- Supported periods: `2022`, `2022EE`, `2023`, `2023BPix`, `2024`
- Output mode: nominal sparse histograms only; no trees or systematics
- Scope: source changes only under this directory

The user explicitly overrode the prompt's reuse preference and required only
this configuration to be self-contained.  The pairing, ID, selected-trigger,
fixed-WP b-tag, year/sample/overlap, stream de-duplication, plot, and structure
implementations were copied from the live implementation at the starting SHA,
then all local macro paths were retargeted here.  Tests freeze the audited cut
expressions by SHA-256 digest.  There are no runtime sibling imports/includes.

## Exact selection contract

The common preselection is:

```cpp
(Trigger_ElMu || Trigger_sngMu || Trigger_dblMu || Trigger_sngEl || Trigger_dblEl)
&& nLepton >= 2 && L2TightLeading2 && nJetInHorn == 0
```

`EXACT_ZZCR`, `CURRENT_DY`, and `CURRENT_DY_ENRICHED` are frozen verbatim in
`study_config.py`.  Their audited SHA-256 values are:

| Contract | SHA-256 |
| --- | --- |
| preselection | `e4552a5838b3a959516cc3c0903929cbcde434cead1107cd174062540d9c2582` |
| exact ZZCR | `a32dfee62259463af7ebd3a794c64901a4c8dc4282feb5d4189525cc2203d0dc` |
| current DY | `c4c69be26f4ebe57dd7cb7dc0ea7c6f1b153d4bb73c30f071884bd6253bfed89` |
| enriched DY | `d0c4314b370a0730d61210932b3c6e0a0223dd2cbbdd8e543d943f8b9c2115a6` |

The exact ZZCR is the current four-lepton parent plus fifth-lepton veto,
`minSelectedPairMass > 12`, physical b veto, ±15 GeV Z window, ordered quartet
25/15/10/10 GeV, same-flavor X, 75–105 GeV X mass, and MET below 35 GeV.
Current DY is the current broad selected-Z parent plus selected-Z ordered
25/15 GeV.  Enriched DY adds the same ±15 GeV Z window.

## Pairing and pT semantics

DY and ZZCR use the same `bestZ0IdxWithID` algorithm: among tight OS-SF pairs
whose two candidate leptons satisfy the 10/10 GeV guards, choose the pair
closest to the nominal Z mass.  X uses the same vendored four-lepton helper
contract after Z selection.

The important nominal mismatch is preserved:

- DY: selected Z leptons themselves must pass strict `>25, >15` GeV;
- ZZCR: the selected Z+X quartet collectively passes strict
  `>25, >15, >10, >10` GeV.

`PassesAnchor2lPt` selects electron/muon objects with the same tight WPs,
sorts them by reconstructed pT, and applies strict `>25, >15` GeV independent
of which pair was chosen as Z.  Representative-event tests mechanically prove
`ZZCR → Z_BRIDGE` and `DY_ENRICHED → Z_BRIDGE`, as well as the cumulative S0–S8
nesting and D0→D1 relation.

## Weights

The framework multiplies the common MC base
`XSWeight*METFilter_Common*puWeight` (and luminosity).  DATA receives the DATA
filter and unit physics weight only.

| Domain | Stage correction |
| --- | --- |
| Z-only | `SelectedLeptonSF_Z*TriggerSF_Z` |
| four-lepton | `SelectedLeptonSF_ZX*TriggerSF_ZX` |
| stage retaining physical b veto | additionally `BTagVetoSF` |

After the b veto is released, its SF is also removed.  One-bin BASE counters
use only the common MC base.  Five sentinel stages contain selected-lepton,
selected-lepton+trigger, and full correction-ablation counters.

## Trigger and DATA stream partitions

Trigger priority is exclusive in this order:

1. ElMu
2. single muon
3. double muon
4. single electron
5. double electron

The exclusive DATA rules are:

```text
MuonEG = Trigger_ElMu
Muon   = !Trigger_ElMu && (Trigger_sngMu || Trigger_dblMu)
EGamma = !Trigger_ElMu && !Trigger_sngMu && !Trigger_dblMu
         && (Trigger_sngEl || Trigger_dblEl)
```

An exhaustive 32-bit-pattern test proves trigger and stream exclusivity and
exhaustiveness.  The exact `cat.txt` split matrix is regression-tested.

## Samples

The full profile resolves all current prompt groups: DATA, DY, ZZ, WZ, Vγ,
Vγ*, WW, ggWW, top, ttV/tZ/ttγ, VVV, target ZH/ggZH, and other configured
Higgs contamination.  It resolves 53 logical outputs in 2022–2023BPix and 55
in 2024.  `major` is a strict pilot subset.  Existing overlap/stitching and
source-normalization rules are retained in the local catalog implementation.

**Nonprompt/fake background is not included.**

## Input and binning audit

Fresh compile checks opened direct CERN XRootD inputs such as:

```text
root://eoscms.cern.ch//store/group/phys_higgs/cmshww/amassiro/HWWNano/
Summer24_150x_nAODv15_Full2024v15/MCl2loose2024v15__MCCorr2024v15__
JERFrom23BPix__l2tight/nanoLatino_ZZ__part0.root
```

The histogram binning was selected from DATA only in the latest completed
2024 full-profile merged job.  Its directory contains 3,967 Condor job
directories, including 1,069 DATA jobs, and no DATA error-log signature was
found.  The merged DATA populations and occupied ranges justify fine uniform
DY axes and coarse uniform four-lepton axes; no MC histogram influenced this
choice.  Overflow folding is retained for residual tails.

The raw DATA-only Freedman--Diaconis widths are 0.029/0.091/0.087 GeV for DY
`mZ`/`pT(Z)`/MET and 0.80/12.98/3.40 GeV for inclusive ZZCR.  The adopted
uniform widths are rounded upward to detector- and model-resolvable scales;
the 86-event 4e topology controls the coarse floors.  In particular, the
on-shell S0 `m4l` axis is 160--600 GeV in 20 GeV bins (40 GeV in topology
leaves), because the observed DATA begin around 160 GeV and have an inclusive
FD width near 20 GeV.  The relaxed S7 bridge uses 80--600 GeV.  Thus the
requested 150 GeV endpoint applies to ordered selected-four-lepton pT, while
using it as the invariant-mass upper edge would fold every S0 DATA event into
overflow.

## Budget and validation

- 54 executable categories (documented cap 60)
- 295 category-variable actions (documented cap 300)
- zero trees
- full local test suite: 18 tests
- fresh compile-only validation: all five supported eras
- full campaign: `dyzz_closure_full_fd_20260812`, 6,850/6,850 jobs complete
- strict batch checks: 505/505 (2022), 1,216/1,216 (2022EE), 707/707
  (2023), 455/455 (2023BPix), and 3,967/3,967 (2024)
- five merged ROOT files: open, non-zombie, and exactly 54 top-level categories
- summary products: 96 stage, 80 transition, 768 composition, 464 shape,
  160 weight-ablation, 432 category, and 80 pT-contract rows
- plot products: 416 plots in both PNG and PDF (832 image files), plus eight
  JSON manifests, across five eras and three combined periods

The original 40/250 targets could not coexist with the user's explicit request
to materialize all flavor/topology/trigger/stream families from `cat.txt` as
literal categories.  The small deliberate excess remains sparse and avoids
all Cartesian products.
