# Run 3 ZH and ZZ four-lepton pairing study

`PairingStudy` is a compact, signal-and-control-sample-only mkShapesRDF
configuration for comparing reconstructed Z/X assignments in five Run 3
eras. It answers two different questions and never combines their efficiency
denominators:

- In ZH, did the reconstructed Z pair recover the two direct prompt daughters
  of the unique associated hard-process Z in
  `Z(ll)H(WW -> 2l2nu)`?
- In direct-four-lepton ZZ events, did the reconstructed `{Z,X}` partition
  recover the two generator-record neutral-current dilepton lineages, allowing
  the two boson labels to be swapped?

This directory does not change the production `ZZ_CR` configuration. It uses
only configured qqZH/ggZH HWW signals and the configured inclusive `ZZ`
sample; there is no DATA, reducible background, nuisance, or tree production.

## Physics and truth contracts

The pairing denominator begins with one pairing-independent quartet: the four
highest-pT valid tight electrons or muons, strict ordered thresholds
`25, 15, 10, 10 GeV`, zero total charge, and a fifth-common-lepton veto at
10 GeV. `PAIRING_PHYS_BASE` additionally requires every one of the quartet's
six dilepton masses to exceed 12 GeV. Neither denominator uses a chosen Z,
Z-mass window, X flavor or mass, MET, or an analysis-region label.

Every valid OS-SF pair is enumerated once as a Z candidate; X is its two-object
complement. The quartet topology is one of `4e`, `4mu`, `2e2mu`, `3e1mu`, or
`1e3mu` (`3mu1e`). The odd-flavor topologies are essential ZH channels: an
associated SF Z leaves a DF HWW pair. A direct two-Z `ee/mumu` truth decay can
only be `4e`, `4mu`, or `2e2mu`; odd-flavor ZZ quartets remain useful
tau/nonprompt/mismatch and reconstructed-XDF diagnostics but are not direct-ZZ
truth recoverable.

ZH truth selects one last-copy, from-hard-process `pdgId=23` lineage that is
not a Higgs descendant. Direct `Z -> ee/mumu` daughters are followed through
same-PDG copies and matched one-to-one to the quartet. `Z -> tautau`, partial
matches, ambiguous records, and source-alignment failures are separate
categories. Correctness is label-sensitive: the algorithm's unordered Z pair
must equal the matched associated-Z pair. When all four signal leptons are
recoverable, the complement is also checked against the HWW lepton pair.

ZZ truth requires two distinct hard Z/gamma* neutral-current lineages with
four direct prompt `e/mu` daughters matched one-to-one. FSR/conversion photons
and nonleptonic intermediate decays are not promoted to direct lineages.
Correctness is label-invariant:
the unordered set `{selected Z pair, selected X pair}` must equal the unordered
set of the two truth pairs. For `4e` and `4mu`, this is generator-record
partition fidelity, not a unique observable-level truth, because
identical-particle interference prevents a physically unique assignment. The
`2e2mu` partition is normally flavor-distinguishable. Tau decays, incomplete
records, duplicated matches, and unavailable or ambiguous partitions fail
closed.

## Samples and inputs

Inventories are derived at run time, without copying the catalog, from
[`../ZZ_CR/year_config.json`](../ZZ_CR/year_config.json):

```text
ZH = intersection(plot_groups["HWW_signal"].samples,
                  years[YEAR].mc.samples)
ZZ = intersection(plot_groups["ZZ"].samples,
                  years[YEAR].mc.samples)
```

The current resolved inventory is:

| Era | ZH logical samples | ZZ logical sample | HWWNano production | Processing step | Files (ZH1/ZH2/ZZ) |
| --- | --- | --- | --- | --- | ---: |
| 2022 | `ZH_Hto2Wto2L2Nu_M125`, `GluGluZH_Hto2Wto2L2Nu_M125` | `ZZ` | `Summer22_130x_nAODv12_Full2022v12` | `MCl2loose2022v12__MCCorr2022v12JetScaling__l2tight` | 53/5/21 |
| 2022EE | `ZH_Hto2Wto2L2Nu_M125`, `GluGluZH_Hto2Wto2L2Nu_M125` | `ZZ` | `Summer22EE_130x_nAODv12_Full2022v12` | `MCl2loose2022EEv12__MCCorr2022EEv12JetScaling__l2tight` | 23/19/38 |
| 2023 | `ZH_Hto2Wto2L2Nu_M125`, `GluGluZH_Hto2Wto2L2Nu_M125` | `ZZ` | `Summer23_130x_nAODv12_Full2023v12` | `MCl2loose2023v12__MCCorr2023v12JetScaling__l2tight` | 72/47/11 |
| 2023BPix | `ZH_Hto2Wto2L2Nu_M125`, `GluGluZH_Hto2Wto2L2Nu_M125` | `ZZ` | `Summer23BPix_130x_nAODv12_Full2023BPixv12` | `MCl2loose2023BPixv12__MCCorr2023BPixv12JetScaling__l2tight` | 58/33/5 |
| 2024 | `ZH_Zto2L_Hto2Wto2L2Nu_M125`, `GluGluZH_Zto2L_Hto2Wto2L2Nu_M125` | `ZZ` | `Summer24_150x_nAODv15_Full2024v15` | `MCl2loose2024v15__MCCorr2024v15__JERFrom23BPix__l2tight` | 161/158/76 |

The file counts are an audited snapshot; executable resolution still fails
closed on an empty inventory. The configured `ZZ` alias is the inclusive
Pythia `/ZZ_TuneCP5_13p6TeV_pythia8/...` sample, not the separately available
forced `ZZTo4L` sample. Its direct-four-lepton truth subset is selected inside
the study. At the current catalog head every logical sample has one inclusive
source component with the same alias. The inherited source-normalization
factors are `1.0119790366858` for qqZH, `0.9651076466221233` for ggZH, and
`1.0` for ZZ in every era; executable metadata records these values rather
than duplicating them in analysis expressions.

At the default 10 files per job, component-aware splitting estimates
10, 9, 15, 11, and 41 jobs for 2022 through 2024 respectively: 86 jobs total.
This is intentionally not `ceil(780/10)`, because each logical component is
split independently.

The common storage base is:

```text
/eos/cms/store/group/phys_higgs/cmshww/amassiro/HWWNano
```

For direct reads use the configured CERN endpoint; for example the physical
path above is resolved as
`root://eoscms.cern.ch//eos/cms/store/group/...`. Representative files in all
five eras and both physics domains were opened successfully. Every checked
schema contains native electron/muon reco-to-gen links, complete GenPart
genealogy, lepton uncertainty inputs, NanoAOD FSR associations, and
`XSWeight`, `METFilter_Common`, and `puWeight`.

## Pairing methods

- `nearest_mZ`: live physical-lepton-mass baseline, minimizing
  `abs(mll - 91.1876 GeV)` with the live strict-comparison tie behavior.
- `core_l4kin_massless`: literal fixed-quartet comparator for the massless
  core `getZXLepIdx` convention.
- `historical_run2_massless`: provenance label for the historical Run-2 rule;
  it shares code when executable-equivalent to the core convention.
- `resolution_pull`: ranks by mass displacement divided by an independent,
  fixed-direction dilepton mass uncertainty. Electron relative uncertainty is
  `Electron_energyErr/E`; muons use `Muon_ptErr`.
- `fsr_nearest_mZ`: ranks with each source-associated `FsrPhoton` added at most
  once after forward/reverse-link validation.
- `fsr_resolution_pull`: uses the FSR-recovered mass and lepton-only mass
  uncertainty; the missing FSR-photon resolution is an explicit approximation.
- ZH and ZZ truth oracles are diagnostic ceilings only and never deployable
  reconstruction scores.

FSR changes candidate ranking only. Region observables always use ordinary
lepton-only kinematics so the migration study isolates the pairing decision.
No reconstruction score contains mX, MET, or region membership.

## Source-alignment limitation

The HWWNano schemas do not store a combined `Lepton_genPartIdx`. Native
`Electron_genPartIdx` and `Muon_genPartIdx` exist, but historical
`LeptonScaleSmearing` output can independently permute final `Lepton` pT,
eta, phi, ID, and origin-index vectors in rare events. Consequently the study
does not trust final `Lepton_electronIdx/muonIdx` or geometric guessing.

It attempts a deterministic one-to-one alignment to the coherent pre-scale
`VetoLepton` source collection and validates all coordinates, flavor, origin
indices, and uniqueness. Concretely, final eta/phi/PDG ID must match one
unused source tuple within the fixed tolerance, and the source flavor must
have exactly one valid native electron or muon index. Corrected pT is not
required to equal pre-scale source pT. If a coherent identity cannot be
proved, the live baseline may still be evaluated on the final production
columns, but truth, resolution, and FSR availability are false and the event
is counted in a source-alignment-failure category. This keeps the production
comparison exact without manufacturing generator truth.

## Weights and outputs

Both raw counts and the minimal base weight are retained. The mkShapesRDF
runner weight carries luminosity, the configured component factor, and the
source normalization exactly once; the signed study weight then multiplies:

```text
runner_weight * XSWeight * METFilter_Common * puWeight
```

Summaries report raw, signed-weight, and absolute-weight denominators and
efficiencies. Negative `XSWeight` entries occur in the ZH inputs, so signed and
absolute diagnostics are mandatory. Lepton, trigger, b-tag, recoil, and
nuisance weights are deliberately absent.

The nominal mkShapesRDF output is histogram-only. Post-processing writes
process-separated CSV/JSON summaries under `reports/<campaign>/` and concise
PNG/PDF figures under `plots/<campaign>/`. `ALL_RUN3` values are obtained by
summing yields, not by averaging era percentages. The completed all-file,
all-event production and its interpretation are recorded in
[`PAIRING_STUDY.md`](PAIRING_STUDY.md); pilot output is never used as a final
result.

## Validation and execution

From the repository root, initialize mkShapesRDF and run the focused tests:

```bash
source start.sh
pytest -q PlotsConfigurationsRun3/ZH_4lMET/PairingStudy/tests
```

For a bounded direct-XRootD pilot, set one era and a one-file limit, freshly
compile the configuration, and process a small event count:

```bash
source start.sh
export YEAR=2024
export LIMIT_FILES_PER_SAMPLE=1
export FILES_PER_JOB=1
export EXECUTION_PROFILE=local_xrootd
export INPUT_ACCESS_MODE=xrootd
export OUTPUT_MODE=local

mkShapesRDF -c 1 -o 0 -b 0 \
  -f PlotsConfigurationsRun3/ZH_4lMET/PairingStudy -l 1000
```

Run a fresh compile independently for every era. The convenience driver takes
one of `compile`, `pilot`, `full-local`, `submit`, `merge`, `summary`, or
`plots`. Keep one explicit campaign name across compile, submit, merge, and
post-processing; otherwise the driver's timestamp default intentionally
creates a new directory:

```bash
export PAIRING_CAMPAIGN=pairing_validation_20260811
bash PlotsConfigurationsRun3/ZH_4lMET/PairingStudy/run_all_years.sh compile
bash PlotsConfigurationsRun3/ZH_4lMET/PairingStudy/run_all_years.sh pilot

# Only after all five pilots pass:
bash PlotsConfigurationsRun3/ZH_4lMET/PairingStudy/run_all_years.sh submit

# Monitor the cluster ranges written to each submit.receipt.txt.
condor_q -name <schedd> <cluster>

bash PlotsConfigurationsRun3/ZH_4lMET/PairingStudy/run_all_years.sh merge
bash PlotsConfigurationsRun3/ZH_4lMET/PairingStudy/run_all_years.sh summary
bash PlotsConfigurationsRun3/ZH_4lMET/PairingStudy/run_all_years.sh plots
```

Before full production, require readable representative ZH and ZZ files,
nonzero expected truth categories, finite raw efficiencies, healthy output for
both domains in every era, and successful pilot summaries and plots. Full jobs
must use all resolved files and `-l -1`, a newly compiled timestamped pickle,
direct XRootD event reads, and recorded cluster/scheduler/output receipts.
`submit` enables the ordinary mkShapesRDF deterministic runtime package
because FNAL workers do not mount the submit host's `/uscms_data` checkout;
this transports code only and does not stage the HWWNano inputs. Check and
merge each exact pickle with ordinary mkShapesRDF commands:

```bash
mkShapesRDF -c 0 --check -b 1 \
  -f PlotsConfigurationsRun3/ZH_4lMET/PairingStudy \
  -config PlotsConfigurationsRun3/ZH_4lMET/PairingStudy/configs/config_<exact>.pkl

mkShapesRDF -c 0 --histoadd -b 0 \
  -f PlotsConfigurationsRun3/ZH_4lMET/PairingStudy \
  -config PlotsConfigurationsRun3/ZH_4lMET/PairingStudy/configs/config_<exact>.pkl
```

Do not commit generated pickles, Condor controls, ROOT files, caches,
summaries, plots, or receipts unless a specific compact final artifact is
deliberately selected for the report.

The implementation was validated with representative-file schema checks,
all-era pilots, a three-process packaged worker smoke test, and the final
campaign `pairing_dual_full_packaged_v2_20260811`. The final campaign read all
780 files directly over XRootD in 86 jobs; every split returned zero, all five
ordinary histogram merges succeeded, strict post-processing produced no
warnings, and 14 supported plot products were generated in PNG and PDF. The
two requested truth-mX response plots are explicitly skipped because no
defensible truth-mX response observable is booked. Exact clusters, pickles,
ROOT paths, efficiencies, migrations, and limitations are in
[`PAIRING_STUDY.md`](PAIRING_STUDY.md).

## File map

- `configuration.py` wires the compact mkShapesRDF graph and runtime I/O.
- `pairing_config.py` resolves live era settings, inventories, thresholds,
  algorithms, and region constants.
- `samples.py` discovers only target ZH HWW and configured ZZ files.
- `aliases.py` exposes the single candidate/truth cache and its projections.
- `cuts.py` defines pairing-independent object and physical baselines.
- `variables.py`, `plot.py`, and `structure.py` define the compact nominal
  histogram output.
- `local_runner.py` is the small histogram-only runner extension that allows
  raw, signed-base, and absolute-base diagnostic weights per variable.
- `macros/pairing_study.cc` owns source alignment, quartet construction,
  exhaustive candidates, algorithms, truth contracts, and region codes.
- `make_summary.py` and `make_plots.py` create the final tables and figures.
- `IMPLEMENTATION_AUDIT.md` records exact live/core/historical provenance and
  invariants; `PAIRING_STUDY.md` records validated final results.
