# Run 3 ZH and ZZ four-lepton pairing results

## Executive result

The all-file, all-event Run 3 study supports retaining the current physical-mass
nearest-`mZ` pairing. It recovers the associated-Z pair in ZH with a raw
efficiency of **94.1712%** and the unlabeled two-boson partition in direct-4l ZZ
with **97.4749%** efficiency on the pairing-independent physical baseline.

Adding source-associated FSR gives the only positive net result: 851 net ZH
corrections and 3 net ZZ corrections. This is a small raw improvement of 0.1307
percentage points in ZH and 0.0338 points in ZZ. It also makes 8,149 ZH and 139
ZZ baseline events unavailable under the fail-closed source/score contract,
moves thousands of reconstructed ZH events across analysis-region boundaries,
and lowers both ZH signal-region and ZZ control-region acceptance. The
resolution-pull methods have negative net correctness in both domains.

The core and historical Run-2 methods are exactly the same massless rule on the
common quartet and share one selector implementation. Literal physical versus
massless lepton masses change only one ZH assignment in 668,539 physical-base
events and no ZZ assignment. Explicit X ranking adds no combinatorial choice:
for every event with a valid selected Z it returns exactly the two-lepton
complement, and the measured XSF/XDF off-diagonal count is zero.

## Scope and definitions

The starting audited revision was
`1a44b3143560703146039f03a1b6118e9a769243` on `ZH_devel`. No production
`ZZ_CR` or mkShapesRDF-core source was changed.

Both domains use the same pairing-independent quartet:

- four highest-pT leptons passing the configured Run 3 tight electron or muon
  WP;
- strict ordered pT thresholds `>25, >15, >10, >10 GeV`;
- total quartet charge zero;
- veto any fifth common `Lepton` with pT at or above 10 GeV; and
- for `PAIRING_PHYS_BASE`, require the minimum of all six quartet dilepton
  masses to exceed 12 GeV.

Every OS-SF pair is enumerated once as a possible Z and X is its two-object
complement. No denominator uses a selected Z, Z window, X mass/flavor, MET, or
analysis region.

ZH correctness is label-sensitive. The selected Z must be the pair matched
one-to-one to the direct `ee` or `mumu` daughters of the unique hard associated
Z that is not a Higgs descendant. ZZ correctness is label-invariant. Two direct
hard Z/gamma* neutral-current daughter pairs must match the quartet one-to-one,
and the unordered reconstructed `{Z pair, X pair}` must equal the unordered
truth pair-of-pairs. For 4e and 4mu this is generator-record partition fidelity,
not unique observable truth; 2e2mu is flavor distinguishable. The two truth
efficiencies are never combined.

## Inputs and production

Inventories, production steps, component weights, source normalizations, and
luminosities were materialized from `../ZZ_CR/year_config.json`. Every logical
sample below resolves to one same-named component with component weight `1.`.
The qqZH, ggZH, and ZZ source normalizations are respectively
`1.0119790366858`, `0.9651076466221233`, and `1.0`.

| Era | ZH components (files) | ZZ component | Production / step | Jobs |
| --- | --- | --- | --- | ---: |
| 2022 | `ZH_Hto2Wto2L2Nu_M125` (53), `GluGluZH_Hto2Wto2L2Nu_M125` (5) | `ZZ` (21) | `Summer22_130x_nAODv12_Full2022v12` / `MCl2loose2022v12__MCCorr2022v12JetScaling__l2tight` | 10 |
| 2022EE | `ZH_Hto2Wto2L2Nu_M125` (23), `GluGluZH_Hto2Wto2L2Nu_M125` (19) | `ZZ` (38) | `Summer22EE_130x_nAODv12_Full2022v12` / `MCl2loose2022EEv12__MCCorr2022EEv12JetScaling__l2tight` | 9 |
| 2023 | `ZH_Hto2Wto2L2Nu_M125` (72), `GluGluZH_Hto2Wto2L2Nu_M125` (47) | `ZZ` (11) | `Summer23_130x_nAODv12_Full2023v12` / `MCl2loose2023v12__MCCorr2023v12JetScaling__l2tight` | 15 |
| 2023BPix | `ZH_Hto2Wto2L2Nu_M125` (58), `GluGluZH_Hto2Wto2L2Nu_M125` (33) | `ZZ` (5) | `Summer23BPix_130x_nAODv12_Full2023BPixv12` / `MCl2loose2023BPixv12__MCCorr2023BPixv12JetScaling__l2tight` | 11 |
| 2024 | `ZH_Zto2L_Hto2Wto2L2Nu_M125` (161), `GluGluZH_Zto2L_Hto2Wto2L2Nu_M125` (158) | `ZZ` (76) | `Summer24_150x_nAODv15_Full2024v15` / `MCl2loose2024v15__MCCorr2024v15__JERFrom23BPix__l2tight` | 41 |

The final campaign is `pairing_dual_full_packaged_v2_20260811`: 780 input
files, 10 files per job, 86 jobs, all events (`-l -1`), and direct reads from
`root://eoscms.cern.ch`. Each era was freshly compiled. The exact pickle and
FNAL scheduler receipt are:

| Era | Pickle | Cluster on `lpcschedd4.fnal.gov` |
| --- | --- | --- |
| 2022 | `configs/pairing_dual_full_packaged_v2_20260811/2022/config_26-08-11_15_54_06.pkl` | `3798586.0-9` |
| 2022EE | `configs/pairing_dual_full_packaged_v2_20260811/2022EE/config_26-08-11_15_57_29.pkl` | `3798587.0-8` |
| 2023 | `configs/pairing_dual_full_packaged_v2_20260811/2023/config_26-08-11_15_58_10.pkl` | `3798588.0-14` |
| 2023BPix | `configs/pairing_dual_full_packaged_v2_20260811/2023BPix/config_26-08-11_15_58_42.pkl` | `3798589.0-10` |
| 2024 | `configs/pairing_dual_full_packaged_v2_20260811/2024/config_26-08-11_15_59_19.pkl` | `3798590.0-40` |

All 86 logs end in normal termination with return value zero. The five normal
mkShapesRDF histogram merges succeeded without a reported `hadd` failure. An
earlier campaign (`3798577` through `3798581`) failed before analysis because
the FNAL worker container did not mount `/uscms_data/start.sh`; it produced no
physics output and was stopped. The final campaign used the ordinary
mkShapesRDF deterministic runtime package to transport code, while continuing
to stream all event inputs directly over XRootD. A three-process packaged
smoke cluster (`3798585`) succeeded before the full resubmission.

## Algorithms

| Code | Name | Executable score |
| ---: | --- | --- |
| 0 | `nearest_mZ` | Physical e/mu masses; minimize `abs(mll-91.1876)` with strict-first tie behavior. |
| 1 | `core_l4kin_massless` | Literal core fixed-quartet massless nearest-mZ rule. |
| 2 | `historical_run2_massless` | Same executable rule as code 1, with historical provenance. |
| 3 | `resolution_pull` | `abs(mll-mZ)/sigma_mll` with independent fixed-direction lepton uncertainties. |
| 4 | `fsr_nearest_mZ` | Nearest mZ after validated source-associated FSR recovery. |
| 5 | `fsr_resolution_pull` | FSR mass with the lepton-only resolution approximation. |

The normalized physical/core/historical equivalence is a report-level proof,
not a duplicate executable algorithm. The known-bug core `getZAZBLepIdx` is
audited but deliberately excluded as a universal selector. Truth oracles are
diagnostic ceilings only. No score uses mX, MET, or region membership.

## Truth and source quality

On `PAIRING_PHYS_BASE`, ZH has 668,539 events. Of these, 651,340 (97.4274%)
contain a direct associated `Z -> ee/mumu` truth target and 651,076 (97.3879%)
are fully truth recoverable. The matched HWW pair is exactly the complement in
650,701 events, or 99.9424% of the recoverable denominator.

ZZ has 9,179 events. There are 8,873 (96.6663%) direct four-lepton truth records
and 8,871 (96.6445%) valid reco-matched partitions. Of the valid partitions,
4,657 (52.4969%) carry the identical-flavor generator-record ambiguity flag.

Provable source alignment succeeds for 661,530/668,539 ZH events (98.9516%) and
9,040/9,179 ZZ events (98.4857%). Resolution and FSR scores are complete for
660,390 ZH and 9,040 ZZ events. Invalid source records fail closed for truth,
resolution, and FSR; no geometric identity is manufactured.

Candidate multiplicity itself shows the ambiguity structure. ZH contains
1,146 zero-candidate events, 490,807 two-candidate events, and 176,586
four-candidate events. ZZ contains 4,395 two-candidate and 4,784 four-candidate
events, with no zero-candidate physical-base events. In ZZ, current correctness
is 96.44% for a score gap below 0.5 GeV and generally approaches unity for
larger gaps, although high-gap bins have smaller statistics.

## ZH associated-Z results

Efficiencies below use the 651,076 truth-recoverable events. Raw, signed, and
absolute weights are shown separately; the signed weight is the minimal
luminosity/source-normalized `XSWeight*puWeight*METFilter_Common` weight.

| Algorithm | Correct | Raw efficiency | Signed efficiency | Absolute efficiency |
| --- | ---: | ---: | ---: | ---: |
| nearest mZ | 613,126 | 94.1712% | 93.9976% | 94.0079% |
| core massless | 613,125 | 94.1710% | 93.9976% | 94.0079% |
| historical massless | 613,125 | 94.1710% | 93.9976% | 94.0079% |
| resolution pull | 609,024 | 93.5412% | 93.5228% | 93.5267% |
| FSR nearest mZ | 613,977 | 94.3019% | 94.0965% | 94.1089% |
| FSR resolution pull | 610,086 | 93.7043% | 93.6531% | 93.6559% |

Current raw efficiency is stable by era:

| Era | Correct / recoverable | Efficiency |
| --- | ---: | ---: |
| 2022 | 7,911 / 8,399 | 94.1898% |
| 2022EE | 26,917 / 28,591 | 94.1450% |
| 2023 | 17,770 / 18,828 | 94.3807% |
| 2023BPix | 8,812 / 9,355 | 94.1956% |
| 2024 | 551,716 / 585,903 | 94.1651% |

All five signal topologies are retained:

| Topology | Correct / recoverable | Current raw efficiency |
| --- | ---: | ---: |
| 4e | 45,622 / 51,261 | 88.9994% |
| 4mu | 109,346 / 121,664 | 89.8754% |
| 2e2mu | 156,518 / 157,749 | 99.2196% |
| 3e1mu | 124,380 / 132,297 | 94.0157% |
| 1e3mu | 177,260 / 188,105 | 94.2346% |

The 3e1mu and 1e3mu rows are genuine XDF ZH signal, not ZZ-only sidebands.
Correct current assignments have a signed binned mean pT(Z) response
`(reco-truth)/truth` of +0.0106; wrong assignments have a much broader negative
mean near -0.344. FSR nearest mZ changes those means only to +0.0103 and -0.340.
The signed binned mean selected mX changes from 41.64 GeV (current) to 41.41 GeV
with FSR nearest mZ; resolution-only gives 41.70 GeV. These are descriptive
reco distributions, not truth-mX responses.

## ZZ partition results

Efficiencies below use the 8,871 valid direct-four-lepton partitions.

| Algorithm | Correct | Raw efficiency | Signed/absolute efficiency |
| --- | ---: | ---: | ---: |
| nearest mZ | 8,647 | 97.4749% | 97.7491% |
| core massless | 8,647 | 97.4749% | 97.7491% |
| historical massless | 8,647 | 97.4749% | 97.7491% |
| resolution pull | 8,640 | 97.3960% | 97.6135% |
| FSR nearest mZ | 8,650 | 97.5087% | 97.7715% |
| FSR resolution pull | 8,639 | 97.3847% | 97.6137% |

Current raw efficiency by era is 97.3171%, 97.0472%, 97.0390%, 98.4529%, and
97.8274% for 2022, 2022EE, 2023, 2023BPix, and 2024 respectively. By topology:

| Topology | Correct / partition-valid | Current raw efficiency | Interpretation |
| --- | ---: | ---: | --- |
| 4e | 1,202 / 1,283 | 93.6867% | identical-flavor generator-record convention |
| 4mu | 3,229 / 3,372 | 95.7592% | identical-flavor generator-record convention |
| 2e2mu | 4,216 / 4,216 | 100.0000% | flavor-distinguishable partition |
| 3e1mu | 0 / 0 | not defined | not a direct-4l ZZ truth topology |
| 1e3mu | 0 / 0 | not defined | not a direct-4l ZZ truth topology |

The current signed binned mean selected mX is 88.22 GeV; all alternatives stay
within 0.11 GeV. The ZZ pT(Z) response uses a disclosed deterministic reference
truth pair—the truth dilepton closest to mZ—but that label never enters the
partition-correctness decision.

## Exact gains, losses, and agreement

The table reports joint event-level transitions relative to current nearest mZ,
not differences inferred from marginal efficiencies.

| Domain | Alternative | Current-wrong -> alt-correct | Current-correct -> alt-wrong | Net raw | Candidate agreement |
| --- | --- | ---: | ---: | ---: | ---: |
| ZH | core/historical massless | 0 | 1 | -1 | 99.99985% |
| ZH | resolution pull | 4,635 | 8,737 | -4,102 | 96.6343% |
| ZH | FSR nearest mZ | 1,541 | 690 | +851 | 98.6083% |
| ZH | FSR resolution pull | 5,877 | 8,917 | -3,040 | 96.4235% |
| ZZ | core/historical massless | 0 | 0 | 0 | 100.0000% |
| ZZ | resolution pull | 20 | 27 | -7 | 88.6698% |
| ZZ | FSR nearest mZ | 8 | 5 | +3 | 96.9169% |
| ZZ | FSR resolution pull | 25 | 33 | -8 | 87.6239% |

For FSR nearest mZ, the signed net gain is +0.01250 in ZH and +0.4171 in ZZ;
the corresponding signed efficiencies rise by about 0.099 and 0.022 percentage
points. Negative ZH weights are retained explicitly; ZZ has no negative weight
in the final selected sample, so signed and absolute ZZ efficiencies coincide.

## Region and acceptance effects

Region kinematics always use nominal lepton-only four-vectors. Only the pairing
choice changes. Raw acceptance on the physical baseline is:

| Method | ZH XSF+XDF SR | ZH ZZCR | ZZ ZZCR |
| --- | ---: | ---: | ---: |
| current/core/historical | 492,952 (73.7357%) | 1,871 (0.2799%) | 6,031 (65.7043%) |
| resolution pull | 488,146 (73.0168%) | 1,861 (0.2784%) | 5,977 (65.1160%) |
| FSR nearest mZ | 490,048 (73.3013%) | 1,829 (0.2736%) | 5,976 (65.1051%) |
| FSR resolution pull | 488,281 (73.0370%) | 1,847 (0.2763%) | 5,977 (65.1160%) |

For ZH, FSR nearest mZ moves 9 outside events into ZZCR, 260 into XSF SR, and
301 into XDF SR, while moving 51 ZZCR, 1,735 XSF, and 1,730 XDF events outside.
Resolution pull has 62/872/976 outside-to-region migrations and
72/2,972/3,682 reverse migrations. The combined FSR-resolution rule has
68/1,094/1,198 gains and 92/3,102/3,861 losses.

For ZZ, FSR nearest mZ moves 4 events from outside to ZZCR but 59 from ZZCR to
outside, plus 2 XSF events outside. Resolution pull moves 15 outside events to
ZZCR and 69 back outside; FSR-resolution moves 18 in and 72 out. No alternative
produces a direct ZZCR-to-SR or XSF-to-XDF transition: nontrivial changes pass
through `outside`, and the fixed-quartet X flavor is invariant.

## X-ranking result

The measured result agrees exactly with the combinatorial proof. In a
charge-zero quartet, removing an OS pair leaves one positive and one negative
lepton, so X is necessarily OS. Once a Z pair is selected from four distinct
objects, only two objects remain; there is no X candidate to rank.

On `PAIRING_PHYS_BASE`, 667,393/667,393 valid-Z ZH events and
9,179/9,179 valid-Z ZZ events have live X identical to the complement. The
remaining 1,146 ZH events have no valid nearest-Z candidate and are not X
disagreements. The physical SF-to-DF and DF-to-SF migration count is exactly
zero. Consequently the explicit live X ranking is redundant within this fixed
quartet, although this study does not authorize changing production `ZZ_CR`.

## Validation, outputs, and limitations

The C++ implementation and Python integration have 37 focused passing tests,
including all five topologies, exact tie behavior, physical-versus-massless
edge cases, source corruption, FSR link validation, all-candidate score
validity, ZH and ZZ truth contracts, label-swap invariance, duplicate matches,
region migrations, gain/loss states, and mkShapes first-axis-fastest histogram
decoding. Representative schemas from every era and both domains contain all
required reco/gen/error/FSR/weight branches. The final strict summary completed
with zero warnings. All merged ROOT files open normally. Fourteen plot products
were generated in both PNG and PDF and representative efficiency, topology,
region-migration, and gain/loss figures were visually inspected.

Products 10 and 11 (`mX` truth response for ZH and ZZ) are intentionally
omitted: no unique, defensible truth-mX response is booked for both domains,
and the selected-mX distribution is not relabeled as truth response. All other
requested plot products are present.

Generated artifacts are deliberately ignored by Git:

- merged ROOT files: `rootFiles/pairing_dual_full_packaged_v2_20260811/<era>/`;
- machine-readable results: `reports/pairing_dual_full_packaged_v2_20260811/`;
- figures and manifest: `plots/pairing_dual_full_packaged_v2_20260811/`;
- submission controls and receipts:
  `condor/pairing_dual_full_packaged_v2_20260811/`; and
- complete submission and merge logs:
  `submit_pairing_dual_full_packaged_v2_20260811.log` and
  `merge_pairing_dual_full_packaged_v2_20260811.log`.

The study compares generator-record truth and minimal nominal MC weights; it is
not a detector-systematics or analysis-SF study. The resolution score neglects
correlations/directional errors, and the combined FSR-resolution score lacks a
photon-resolution term. Rare historical scale-smearing vector incoherence is
handled by exclusion from source-dependent denominators, not repaired here.

## Recommendation

Retain current physical-mass nearest mZ pairing. It is simple, stable across
eras and all five ZH topologies, exactly reproduces the established live rule,
and already gives high associated-Z and ZZ-partition fidelity. FSR nearest mZ
has a real but small net truth gain in both domains; the gain is not large
enough to offset its source-alignment/FSR-link implementation burden, its
fail-closed unavailable population, and its lower signal-region and ZZCR
acceptance. Resolution-aware variants are disfavored because they lose net
correct assignments in both ZH and ZZ. No production change is justified by
these results.
