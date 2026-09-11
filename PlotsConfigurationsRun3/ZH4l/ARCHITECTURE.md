# ZH4l architecture

`ZH4l` is the development successor to `ZH_4lMET`, which remains the
production compatibility authority until an explicit cutover. `ZZCR`,
`Pairing`, `Closure`, and the small runnable `Example` are complete independent configuration leaves.
They consume `common/`; neither the common package nor a leaf imports a
sibling leaf. [NAMING.md](NAMING.md) defines the public vocabulary.

## Ownership and composition

| Concern | Owner |
|---|---|
| Era, production, luminosity, WP and payload metadata | `common/eras.json`, `common/eras.py` |
| Sample materialization, component normalization and exact file overrides | `common/samples.py`, `common/catalog.py`; Pairing retains its explicit study inventory |
| Sources, views, candidates, corrections, recipes and regions | `common/definitions.py` |
| Processed Lepton/CleanJet adapters, nominal pairs, selected trigger and b veto | `common/presets.py` |
| Explicit predicate composition and boundaries | `common/selections.py` |
| Established complete Z/X alias preset | `common/objects.py`, `common/corrections.py` |
| Shared kinematics, kernels and histogram axes | `common/macros/`, `common/observables.py` |
| Event projections and branch groups | `common/outputs.py` |
| Nominal sparse booking and snapshots | `common/runner.py`, thin leaf entry points |
| Process display and data/signal/background bookkeeping | `common/presentation.py`, leaf `plot.py` and `structure.py` |
| Pairing truth, scores and candidate comparison | `Pairing/macros/pairing.cc` and its Python configuration |
| Closure stages, category inheritance and sparse axes | `Closure/study_config.py`, `Closure/variables.py` |
| Site access, packaging and worker imports | `common/runtime.py`, `env/` |

An `Analysis` is a compilation graph of small immutable definitions. It emits
ordinary `aliases`, `cuts`, `preselections`, `variables`, and `nuisances`
dictionaries. It performs no input discovery. Only dependencies of the
requested outputs, their regions and preselection are compiled. Custom C++
expressions declare dependencies explicitly; the compiler does not parse
arbitrary expressions to guess dependencies.

A source declares retained fields, a physical index namespace (`identity`),
and kinematic/producer lineage. Views preserve original indices through
masking, sorting, complements and unions. Different representations of the
same collection must share its physical identity; this prevents applying an
efficiency twice merely by giving the source another name. Unions require the
same representation. A source field is distinct from an eligible object view,
a selected candidate, and an event selection.

`pair()` supports explicit charge/flavor constraints, per-flavor WPs,
ordered-pT eligibility, nearest-Z or highest-pT ranking, and an excluded view
or candidate. Ties retain the first pair in the declared pool order. Z and X
can have different WPs. `quartet()` chooses the highest-pT eligible four;
this is a separate policy from selecting Z then X from its complement.
The nominal preset delegates eligibility/kinematics to the retained C++
kernels. Those compatibility kernels remain byte-identical to the legacy
reference. The established leaves retain their complete alias presets;
new small studies can use the dependency-pruned graph directly.

`combine(name, z, x)` constructs a composite from existing selected candidates.
Its validity requires valid, mutually disjoint constituents; it does not
reselect members or turn overlapping pairs into a valid candidate. The
composite exposes source indices and mass/pT/eta/phi. The processed CleanJet
adapter maps native Jet tag/flavor fields into CleanJet order before any view
selection or sorting; every field consumed by `take()` shares that source's
index namespace.

## Small configuration example

[Example/README.md](Example/README.md) provides a complete, executed example
with pinned real 2024 ZZ/ZH inputs, separate Z/X WPs, composite candidates,
correction recipes, region inheritance, sparse/vector histograms, event trees,
and a direct tree-to-histogram checker. The shorter Z-only sketch below
illustrates a subset of the same API.

For this example, build samples with `materialize_catalog("puWeight")` so
the native `weight` contains sample/component normalization, luminosity,
MET filters and pileup, but no selected-lepton/trigger/b-veto correction.
The example chooses a Z-only domain and applies just its total lepton SF.
An analysis must add its own scientifically intended trigger and event cuts.

```python
from common.definitions import Analysis
from common.eras import load_selected_era
from common.outputs import branches, output_mode
from common.presets import nominal_pairs
from common.selections import window

_, era, _ = load_selected_era()
analysis = Analysis()
z, _ = nominal_pairs(analysis, era, with_x=False)
z_window = window(analysis, "z_pass_mass_window", z.mass, 75., 105.)
sf_z = analysis.lepton_sf("sf_lepton_z", z)
weight_z = analysis.weight("weight_z", sf_z)
z_peak = analysis.region(
    "z_peak", f"{z.valid} && {z_window}",
    dependencies=(z.valid, z_window), weight=weight_z,
)
analysis.histogram(
    "z_mass", z.mass, (75., 80., 85., 90., 95., 100., 105.),
    regions=[z_peak], title="m(Z) [GeV]",
)
analysis.tree(
    "events",
    branches("identity", "source", extra={
        "z_lepton_index": z.indices, "z_is_valid": z.valid,
        "z_mass": z.mass, "sf_lepton_z": sf_z.value,
    }),
    regions=[z_peak], weight=weight_z,
)
globals().update(analysis.compile(mode=output_mode()))
```

This block may be executed in a leaf's shared configuration namespace before
serialization. Use the shared nominal runner entry point, import `common`
from the family directory, and keep normal `filesToExec`/`varsToKeep` ordering.
`histogram()` currently provides one-dimensional explicit-edge bookings;
ordinary variable dictionaries support native 1D/2D/3D axes and vector fills.
`take()` rejects invalid source indices: guard invalid candidates explicitly
before consuming selected field vectors. Candidate scalar kinematic helpers
retain their documented sentinel behavior.

## Corrections and weights

A correction identifies its exact target, efficiency component, calibration,
value and validity. `lepton_sf()` uses the retained matching-WP total SF;
it does not invent separate reconstruction/ID/isolation factors. Different-WP
views require separate corrections. The selected-trigger provider evaluates
the canonical two- or four-lepton union on the supported processed Lepton
representation. Multiplying two pair trigger SFs is rejected as a duplicate
trigger component, not interpreted as a four-lepton union.

The b-veto provider returns `event_pass_<name>` and `sf_<name>` for the same
accepted jet view. Its present payload supports the configured loose WP and
subsets of pT > 20 GeV, |eta| < 2.5. Wider acceptance or another tagger/WP
requires a matching provider. DATA applicability comes from sample metadata;
unit factors on DATA do not imply that an invalid MC calculation is valid.

Weight recipes compose the native normalized base once, or an explicitly
chosen base. `base="1.0"` gives a literal count. Duplicate factors/components
are rejected; potentially overlapping same-component views get an explicit
membership-disjointness check. Invalid recipes carry a false validity column
and NaN value. Output booking rejects non-finite weights with an error.
A tree may export correction validity for diagnostics; it must still choose
a valid output weight. Signed and zero weights are preserved.

Regions inherit recipes through explicit parent references. A typed histogram
spanning regions with different recipes compiles one public histogram booking
with a `regionWeights` mapping of flat region names to total-weight expressions.
An explicit histogram `weight` overrides region recipes for comparisons.
`regionWeights` must cover exactly the booking's selected flat regions and
cannot be combined with another total or relative weight field. The Closure
preset now uses a declared category-parent map: S0's 4e, 4mu and 2e2mu
children receive the parent's `sf_b_veto`. This corrects an omitted factor in
the former prefix-based lookup. Selections and binning are unchanged; those
children's MC yields intentionally change. N-minus-one selection changes and
correction removal remain separate explicit decisions.

## Outputs and execution

`ZH4L_OUTPUT_MODE=histograms|trees|both` selects outputs in each leaf;
`histograms` is the default. Trees are nominal, one event row per selected
region, with vector-valued object/candidate fields where appropriate.
Flattened candidate rows are not implemented. Overlapping regions can contain
the same event. Comparisons must use identity rather than row order.

Histograms use `<region>/<observable>/histo_<sample>`. Trees use
`trees/<region>/<sample>/Events`; explicit `treeName` values allow different
schemas in the same region. All native chunks are concatenated, including
empty schema-bearing chunks. Branch projection captures expressions before
renaming fields, preventing order-dependent collisions. Conflicting tree
paths/schemas fail. Selected trees do not represent events that would migrate
into a region under future kinematic variations.

Snapshot scratch is removed after the native runner releases its graphs and
file handles. Earlier deletion can leave open `.nfs` files on shared storage.
Failed runs retain their task-owned scratch for diagnosis.

The common branch groups are `identity`, `source`, `z`, `x`, `zx`, `leptons`,
`jets_met`, `corrections`, and `trigger`. Add fields explicitly or exclude
fields before replacing them. Native event identity types are preserved;
`source_file` records the original input URI and `source_entry` the original
file-local entry as an unsigned integer. These distinguish MC events whose
run/lumi/event triples are not globally unique.

`branches()` also accepts typed candidates, views, columns, corrections and
weights. It exports their actual names and retains their graph dependencies,
so prefixed or alternate definitions need no hand-written field map. Candidate
groups contain membership, validity and kinematics; correction/weight groups
contain value and validity. String groups such as `"z"` continue to refer to
the established complete alias preset.

A tree's `weight` is its chosen total recipe. With ordinary variables, the
default is native `weight` times the region factor. `treeWeight` overrides it.
Pairing exports raw, nominal and absolute nominal recipes and uses nominal
as the default tree weight; Closure also exports `weight_base`. Typed recipe
exports add `weight_is_valid`. Histogram `weight` supplies a total, whereas
`weightFactor` multiplies the native weight. Ambiguous combinations fail.
The old `studyWeight`/`studyWeightFactor` spellings remain supported by the
adapter for existing leaf dictionaries.

| Configuration | Execution |
|---|---|
| ZZCR, `ENABLE_SYSTEMATICS=0` | Shared nominal adapter; any output mode |
| ZZCR, `ENABLE_SYSTEMATICS=1` | Existing native nuisance route; histograms only |
| Pairing, Closure and Example | Shared nominal adapter through small local runner shims |

The adapter subclasses native `RunAnalysis` and retains its input, sample,
normalization, subsample, fold/unroll and I/O machinery. Its delta is sparse
per-booking weights, preservation of zero-weight rows, explicit DATA alias
expressions, and event-tree projection/assembly. It accepts the native
`type="auto"` finite-MC datacard directive but evaluates no varied graph.
New correction variation metadata and tree variation-policy fields are
reserved and reject unsupported non-nominal requests. The established ZZCR
nuisance path is retained separately; the new graph is nominal-only.

`condorRuntimeIncludes` explicitly includes `common/`. `zh4lCommonPath`
travels with the compiled configuration and is relocated by native batch path
tokenization. All leaf shims import that package path. Do not rely on the
worker's access to the original checkout or import another leaf's runner.

## Compatibility and validation

`full` remains ZZCR's default configured MC+DATA scope; `quick` limits it to
DY+ZZ+DATA. `presentation`/`commissioning` remain profile aliases. Exact
`SAMPLE_FILTER` overrides are respected by all three leaves within each
leaf's supported inventory. `PINNED_FILES` is a shared-namespace mapping from
exact source aliases to explicit file lists; it bypasses discovery and fails
when a selected component is missing. Importing the callable sample helper
performs no discovery.

The retained nominal histogram edges/folds, source normalization and object
kernels are regression protected. [common/tests](common/tests) covers lazy
dependencies, source indices, independent WPs, correction composition,
selection boundaries, all output modes, zero/signed weights, full-width event
identity, sparse/vector booking and chunk/file assembly. The leaf tests cover
selection/axis and study-specific contracts. Historical validation reports
predate the naming/output migration; they are not evidence for a current
production campaign. See the README for current bounded checks.

No framework-core or legacy-production source change is required for these
tools. No new logging, manifest, receipt or campaign database is introduced.
