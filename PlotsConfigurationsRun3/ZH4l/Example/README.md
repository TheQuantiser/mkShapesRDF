# A small, realistic ZH4l configuration

Start with [analysis.py](analysis.py). It defines a four-lepton analysis using
the common tools, with no copied object kernels or study runner. The other
files provide standard configuration serialization, two pinned MC inputs,
the shared runner entry point, and an empty native nuisance extension point.

This is an executable example, not a production replacement for `ZZCR` or
`ZH_4lMET`. It deliberately uses different working points for Z and X and
processes a small fraction of two samples. Its yields are smoke-test yields,
not full-sample predictions or an efficiency measurement.

## Features demonstrated

| Feature | Use in this example |
|---|---|
| Independent object definitions | Z uses the era's default electron/muon WPs; X uses `mvaWinter22V2Iso_WP90` and `cut_Tight_HWW` |
| Candidate policy | Nearest-mass OSSF Z, then highest-pT opposite-sign X excluding Z; both selected pairs are combined without reselection |
| Source identity | Lepton indices retain their original collection positions; selected CleanJets retain their native Jet mapping |
| Separate correction domains | Matching retained total lepton SFs for Z and X, one selected four-lepton trigger union, and the loose b-veto correction |
| Weight composition | Native base, literal counts, lepton-corrected, lepton-plus-trigger, and full nominal recipes |
| Region inheritance | A four-lepton baseline, its b-veto child, and three control/signal-style children that inherit the full weight |
| Sparse histograms | Five observables in every region; four alternative-weight X-mass bookings only in the b-veto region |
| Vector output | Four selected lepton pT values fill an object distribution; leptons and accepted jets are vectors in event trees |
| Typed tree projection | Candidates, correction values/validity, recipes, region flags, event identity and original file/entry identity |
| Output choice | `ZH4L_OUTPUT_MODE=histograms`, `trees`, or `both` |
| Normal framework integration | Native samples, plot/structure metadata, timestamped compiled configurations, and `mkPlot` |

The Z and X WPs are intentionally distinct. Their lepton SFs correct disjoint
selected members exactly once. The trigger correction is evaluated for their
union; it is not a product of two pair trigger corrections. A tighter jet
subset can be supplied to the b-veto provider only within its supported
calibration acceptance.

All object momenta are the retained final processed momenta. `CleanJet`
already carries the producer's cleaning; choosing a new lepton view does not
reclean those jets. Generic `tag` and `flavor` fields are mapped through
`CleanJet_jetIdx` before view selection or sorting.

## Run it

From the framework checkout, with the supported runtime and valid site access:

```bash
source start.sh
source PlotsConfigurationsRun3/ZH4l/env/fnal.sh  # use lxplus.sh at CERN
export ERA=2024 ENABLE_SYSTEMATICS=0 CONDOR_RUNTIME_PACKAGE=0
export SAMPLE_FILTER=ZZ,ZH_Zto2L_Hto2Wto2L2Nu_M125
export ZH4L_OUTPUT_MODE=both

example_dir="$PWD/PlotsConfigurationsRun3/ZH4l/Example"
mkdir -p "$example_dir/outputs"
example_run=$(mktemp -d "$example_dir/outputs/example_XXXXXXXX")
export ZH4L_CAMPAIGN=$(basename "$example_run")
export ZH4L_OUTPUT_FOLDER="$example_run/rootFiles"
export ZH4L_PLOT_PATH="$example_run/plots"

mkShapesRDF -c 1 -o 0 -b 0 -f "$example_dir" \
  -configs "$example_run/configs" -l 500
python "$example_dir/check_output.py" \
  "$example_run"/configs/config_*.pkl \
  "$example_run"/rootFiles/mkShapes__*.root --check-inputs
```

Each fresh directory contains exactly one compiled pickle and one ROOT output;
the globs above therefore identify that run unambiguously. An independent
rerun should use another fresh directory. Compilation uses the two explicit
URIs in [samples.py](samples.py), never a campaign listing. `-l 500` bounds
each input dataframe; one pinned file per sample bounds the input inventory.
`SAMPLE_FILTER` may select either or both of these two processes. Another era
or an unsupported sample is rejected rather than assigned the 2024 files.

For a small plot, using that exact run's `configs` directory:

```bash
(
  cd "$example_run"
  mkPlot --inputFile "$ZH4L_OUTPUT_FOLDER"/mkShapes__*.root \
    --onlyCut b_veto --onlyVariable x_mass --onlyPlot c \
    --linearOnly --fileFormats png
)
```

The shell remains local. These commands do not submit Condor jobs or stage
outputs to remote storage. Generated files remain under the ignored
`outputs/` directory; no campaign database or extra manifest is used.
The current native `mkPlot` uses the compiled `plotPath` for its destination;
set `ZH4L_PLOT_PATH` before compilation as shown, rather than relying on its
`--outputDirPlots` option. The parent directory must already exist.
The example labels plots as an MC subset; the configured luminosity remains
in the numerical weights and serialized configuration.

## Selections and outputs

The shared preselection requires the retained trigger OR, `METFilter_Common`,
at least four retained leptons, and the established jet-horn veto. The baseline
requires valid disjoint pairs, ordered lepton pT strictly above 25/15/10/10 GeV,
a Z mass within 15 GeV of 91.1876 GeV, X mass above 4 GeV, every selected pair
mass above 12 GeV, and exactly four retained leptons with pT at least 10 GeV.

The `b_veto` region adds the calibrated loose veto for jets with pT > 20 GeV
and |eta| < 2.5. Its children use these strict bounds:

| Region | Additional selection |
|---|---|
| `zz_control` | Same-flavor X, 75 < m(X) < 105 GeV, missing pT < 35 GeV |
| `x_same_flavor` | Same-flavor X, 10 < m(X) < 65 GeV, missing pT > 35 GeV, m(4l) > 140 GeV |
| `x_different_flavor` | Different-flavor X, 10 < m(X) < 70 GeV, missing pT > 20 GeV |

These three children are mutually exclusive and are not exhaustive. Baseline
and child regions overlap deliberately. The input production already applies
loose-lepton retention and the `l2tight` requirement on its leading two
leptons. This configuration cannot recover discarded events or establish an
unbiased denominator for a looser efficiency measurement.

Histograms are stored at `<region>/<observable>/histo_<sample>`. The combined
run produces 58 histograms: five observables × five regions × two samples,
plus four weight-comparison histograms × two samples. Both underflow and
overflow are folded. Each selected lepton contributes one fill to
`zx_lepton_pt`; its sumw2 is the usual per-fill ROOT sumw2 and does not encode
within-event covariance for a statistical fit.

The ten trees are at `trees/<region>/<sample>/Events`, including readable
empty selections. Each row is one event; object vectors are not flattened.
`source_file` and `source_entry` refer to the original input. The tree's
`weight` is the total actually used for that region. Named alternatives and
their validity flags remain available for comparisons.

The broad `four_lepton` tree includes events failing the b veto. Their
`sf_b_veto_is_valid` and `weight_nominal_is_valid` are false, and the unapplied
`weight_nominal` is NaN. Its chosen `weight_lepton_trigger` remains finite.
That explicit invalidity must not be replaced with a unit correction or used
as the weight of a b-veto-corrected histogram.

## Executed checks

On 2026-09-10, the CLI ran locally on FNAL LPC with Python 3.13.11 and ROOT
6.38.00, using the first 500 entries of each pinned 2024 file. The source files
contained 12,465 ZZ events and 560 ZH events. They retain the selected WPs,
matching total-SF branches, final Lepton and CleanJet collections, native Jet
maps, VetoLepton trigger-alignment inputs, and normalization fields required
by the providers.

| Region | ZZ rows | ZH rows |
|---|---:|---:|
| `four_lepton` | 3 | 32 |
| `b_veto` | 2 | 30 |
| `zz_control` | 1 | 0 |
| `x_same_flavor` | 0 | 7 |
| `x_different_flavor` | 0 | 13 |

The output checker independently reopened every histogram/tree, checked typed
identities, recipe composition and region membership, and reproduced all 58
histograms' bin contents and sumw2 from the trees. `--check-inputs` also
reopened the pinned inputs and checked event identity, selected lepton/jet
mapping, and the native normalization including luminosity and the catalogue
source factor. The tolerance is relative 1e-6 and absolute 1e-9, accounting
for float32 retained observables/SFs and double histogram accumulation.
An independent fresh compile/run reproduced all 58 histograms' bin contents
and errors and every branch of all ten trees exactly after matching source
identity, including the deliberately invalid NaN alternatives. Native `mkPlot`
also produced and was used to inspect the b-veto X-mass plot. The full ZH4l
suite passed 108 tests; scoped Black/flake8 checks passed for all 59 changed
Python files.

The first 100-entry attempt exposed premature deletion of open snapshot files
on NFS. The ZH4l runner now releases ROOT graphs before deleting successful
snapshot scratch; failed runs retain their scratch for diagnosis. The fresh
500-entry run completed on the shared filesystem. Configuration tests cover
all three output modes without event-file discovery, and common tests cover
jet-index permutations, candidate overlaps, region-specific weights, signed
and zero weights, and shared-filesystem tree assembly. These establish bounded
software/numerical behavior; full-sample normalization, systematics, data
agreement and statistical inference remain outside this example's validation.
