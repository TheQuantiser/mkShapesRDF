# Proposed flexible ZH4l common toolkit

Status: original design rationale, 2026-09-10. The user authorized implementation
and the subsequent naming overhaul. This document preserves the proposal and
its initial findings; examples below are design sketches, not the supported API.
[ARCHITECTURE.md](ARCHITECTURE.md) describes the implemented nominal toolkit,
its exact APIs and limits; [NAMING.md](NAMING.md) supersedes earlier spellings.
Flattened candidate output and new nuisance evaluation remain deferred.
The review used framework revision `fc95f7c527358ca419752a048bbd82ead1412ae7`.

## Objective

Provide a common set of tools within ZH4l from which small, independent leaves
can compose different object definitions, candidate assignments, selections,
corrections, weights, histogram bookings, and selected ROOT trees. Several
definitions must be able to coexist in one analysis. Histograms only, trees
only, and both together are explicit output choices over the same definitions.
The existing nominal Z/ZX configuration becomes a reusable preset assembled
from these tools.

Implement nominal behavior first. Retain explicit extension points for future
nuisances without constructing a new nuisance model. Keep normal mkShapesRDF
configuration/output interfaces and use its execution and I/O services. This
proposal adds no logging, manifest, campaign-database, or reporting subsystem.

## Couplings found before implementation

- [common/objects.py](common/objects.py) builds one fixed public Z/X graph,
  selects `run3_lowpt`, and uses one electron/muon WP pair for both Z and X.
  Repeated calls produce the same public alias names.
- [common/macros/objects.cc](common/macros/objects.cc) selects Z first, then
  searches remaining leptons for an eligible opposite-sign X pair.
  [Pairing/macros/pairing.cc](Pairing/macros/pairing.cc) selects a quartet
  first and enumerates assignments within that quartet. These are distinct
  candidate policies, particularly when more than four eligible leptons exist.
- [common/corrections.py](common/corrections.py) binds corrections to literal
  `Z_idx`/`X_idx`, combines Z and ZX services in one builder, and owns both the
  physical b-veto predicate and its weight correction.
- [common/catalog.py](common/catalog.py) executes against shared globals,
  constructs sample weights, and performs discovery. Pairing has separate
  materialization mechanics for its diagnostic weight requirements.
- [Closure/study_config.py](Closure/study_config.py) derives correction
  policies partly from category-name prefixes. Its S0 flavor children retain
  the b veto but omit their parent's `bVetoSF` factor.
- The native runner filters on `abs(weight)>0` before histogram booking.
  Pairing accommodates this with a neutral core weight and explicit study
  weights. General raw-count and tree support need an explicit population
  contract.
- Earlier `ZH_4lMET/ZZ_CR/variables.py` at revision `509660f` built a
  `tree_branches` mapping and `variables["tree"]` restricted to `zz_cr`.
  It exported event/pair kinematics, selected-lepton properties and WP flags,
  trigger diagnostics, selected-WP SFs, and jet quantities. The current
  legacy ZZ_CR runner and ZH4l Pairing/Closure runners explicitly reject tree
  variables. Native snapshot support exists, but those adapters need deliberate
  integration; a histogram-only adapter cannot provide it automatically.

These are the principal design constraints, beyond reducing file lengths.

## Common concepts

Use small Python records and ordinary functions, backed by existing C++/RDF
helpers. Avoid a large class hierarchy or a second execution engine.

| Concept | Contains | Does not choose implicitly |
| --- | --- | --- |
| Source adapter | Retained collections, branch meanings, ordering, verified index maps, source capabilities | An analysis WP or a different input population |
| Object view | Source reference, original indices, kinematic representation, eligibility mask, explicit ordering | Event acceptance or an event weight |
| Candidate definition | Input views, cardinality, charge/flavor requirements, enumeration and ranking policies, deterministic tie rule | Additional analysis cuts |
| Selection | Named predicates referencing specified objects/candidates and explicit thresholds | Reconstruction of a different candidate or correction factors |
| Correction | Provider, target objects or decision, calibration definition, applicability, nominal result and validity | Whether an output's weight recipe applies it |
| Weight recipe | Explicit named normalization and correction factors for an applicable sample role | Selection changes or dependence on category labels |
| Histogram booking | Region, observable, axis, weight recipe, and event/object/candidate fill unit | A universal weight for every diagnostic |
| Tree output | Region or baseline selection, named branch expressions/groups, row unit, exported weight recipes, output identity | Additional selection, a single universal weight, or automatic candidate flattening |

References link these records. Numerical identity includes source, membership,
kinematics, selection/ranking policy, and calibration inputs as applicable;
plot labels and colors are separate. Reuse identical definitions within the
current compilation graph; no persistent cache service is required.

## Objects and candidate construction

Maintain separate views for electrons, muons, merged leptons, jets, and MET.
Composite candidates reference their constituent views and original indices.
Expose selected members and their complement explicitly: Z leptons, X leptons,
the Z+X union, other eligible leptons, veto leptons, accepted jets, and tagged
jets have different meanings.

Filtering and sorting a view must preserve its mapping to the retained source
collection. A local position in a sorted subset must never be used directly
to index an unrelated SF vector or native Electron/Muon/Jet collection.
Historical pre-scale/final-lepton alignment belongs in the source adapter;
it must not leak into every selection or correction implementation. Reuse
stored indices where their semantics are verified, and isolate any necessary
legacy alignment reconstruction with explicit validity.

An object view also identifies its kinematics. Stored corrected momenta,
pre-scale momenta, and a future dressed or shifted representation may refer
to the same physical objects but are not interchangeable inputs. Read retained
corrections first; do not reapply an upstream momentum calibration.

Candidate tools should separate enumeration, eligibility, ranking, and final
selection. Initially preserve both demonstrated policies:

1. choose Z from its declared lepton pool, then choose X from a declared pool
   excluding Z;
2. choose a quartet under an explicit rule, then compare its Z/X assignments.

Z and X may use different electron/muon WPs and thresholds. Their membership
must still be disjoint. A pairing change within a fixed quartet and a change
of quartet are distinct operations. Ranking inputs, kinematic conventions,
and tie breaking must be explicit. All-candidate output is an explicit mode
with constituent indices and an event/candidate fill policy.

Allow several named definitions simultaneously. Generated internal aliases
must not collide; short public names such as `mZ` may be exported for a leaf's
chosen default. A second definition must not replace the first by mutation.

The same rule applies to jets: select a jet view, define a tag decision on it,
then express a veto or multiplicity requirement. Existing CleanJet cleaning
semantics belong to the source adapter. A new cleaning prescription requires
suitable retained inputs and a declared rule. Merely changing a lepton view
must not silently relabel the stored CleanJet collection as newly cleaned.

## Selections and regions

Keep three levels distinct:

- eligibility used to construct candidates;
- predicates evaluated on a fixed selected candidate;
- event regions combining those predicates with trigger and event-quality
  requirements.

Selecting the best pair among pairs passing a tighter cut can choose another
pair; applying that cut to an already selected pair can reject the event.
Expose both operations and do not substitute one for the other.

Common functions provide pT, mass, flavor, charge, multiplicity, overlap,
validity, and veto predicates. Presets package established defaults. Leaf
regions compose them and may supply additional named C++ expressions with
declared dependencies. Strict/inclusive boundaries remain visible.

Region records reference their object definitions and weight recipes.
Subcategories inherit these references explicitly and add predicates.
Changing a weight is a declared override. N-minus-one selection and correction
removal are separate choices; neither is inferred from the category name.

Unsupported WPs, source schemas, or missing required quantities produce clear
errors. A downstream flexible selection cannot restore events removed by the
input production. A looser object definition requires both retained object
information and a suitable upstream event population.

## Corrections and weight composition

Separate kinematic transformations from yield corrections. A transformation
produces a new kinematic view. An efficiency/SF provider produces a value,
validity, and applicability attached to a specified object or decision.

Providers should consume exact retained products when equivalent. Stored
total lepton SFs must remain total SFs unless independently retained components
with matching semantics permit decomposition. A convenient ID/isolation/reco
factor interface is not evidence that a combined branch can be split.

The correction target includes both object identity and calibration context:

- per-electron/per-muon corrections refer to the selected indices, matching
  WP, era, and the provider's required kinematics;
- distinct Z and X WPs can use distinct supported providers, with each
  selected lepton corrected once for the declared efficiency component;
- event trigger corrections specify the selected lepton domain and trigger
  decision/algebra. Independent Z and X event-trigger SFs must not be multiplied
  to manufacture a correction for their union;
- a b-veto correction references the exact jet view, tagger/WP, acceptance,
  and veto decision. Another tag/multiplicity region needs a provider whose
  method supports that region;
- DATA/MC applicability comes from explicit sample metadata. Unit weights for
  inapplicable corrections are distinct from invalid or unavailable MC
  corrections; invalidity is not silently converted to a successful unit SF.

Creating a correction makes it available. A weight recipe explicitly applies
it. This permits uncorrected/corrected comparisons and component ablations
without rebuilding objects or changing event selections.

Separate sample normalization, event-quality predicates, pileup, selected
lepton corrections, event-trigger corrections, and tagging corrections.
Respect the existing `XSWeight` content and native luminosity multiplication
so normalization occurs once. Make raw count, base MC weight, full nominal
weight, absolute diagnostic weight, and an explicit alternative recipe
independently bookable on the declared population.

Known factors carry stable identities and covered efficiency components so
obvious double application is rejected. Union operations preserve unique
object membership. Arbitrary user expressions remain allowed through an
explicit factor with applicability and dependency declarations; algebraic
equivalence of arbitrary C++ expressions cannot be automatically guaranteed.

## Observables and execution integration

Keep an observable's physical expression and validity separate from histogram
binning. The same object observable may have several independent axes and
weight recipes. Invalid candidates must not enter normal physics bins through
sentinel folding; diagnostic invalid-state counts are explicit bookings.
Copied or overridden axes must not mutate shared definitions.

Resolve only requested definitions and dependencies. Defining, histogramming,
or saving Z alone should not require X, b-tag payloads, or generator-truth inputs.

Lower common definitions to ordinary mkShapesRDF aliases, samples, cuts,
variables, plotting/structure dictionaries, and the existing nuisance field.
Keep standard leaf files as a readable boundary. Use native RunAnalysis for
representable ordinary bookings and one optional family adapter for sparse
booking, explicit weight recipes, scalar/vector fills, and tree integration
where needed. The adapter must preserve the declared raw-event and tree
populations despite the native nonzero-weight prefilter. Reuse existing study
mechanics before adding a new path.

Truth interpretation, alternative pairing scores, closure ladders, and
analysis-specific statistical summaries remain leaf-owned. Common tools
provide shared object/matching mechanics where actual reuse warrants it.

Use the existing runtime packager and declare common dependencies correctly.
The source adapter and runtime boundary should validate compatibility and
materialize ordinary configuration state without an extra operational layer.

## Tree outputs

Tree production is a first-class common capability. A leaf selects its output
mode and composes branch groups, using the same object views, candidates,
predicates, observables, and corrections used by its histograms. Tree fields
must not be reconstructed by parsing histogram definitions or axis expressions.
Small leaves should be able to request a standard branch group and add or
remove explicit fields without copying the legacy branch-building machinery.

Provide reusable branch groups for event identity, object collections and their
source indices, selected Z/X constituents and kinematics, selection/validity
flags, trigger diagnostics, correction components, and named total weights.
Expensive diagnostics and generator information are opt-in and subject to
source capabilities and DATA/MC applicability. Resolve branch names, types,
missing-field policy, and dependencies before execution; never silently change
a requested field name or disguise a missing decision as a valid false result.
Optional unavailable quantities need an explicit representation and validity.

Each tree declares its saved population independently of histogram bookings:
either a selected region or a broader baseline with stored region flags.
Overlapping per-region trees can contain the same event; a baseline tree with
flags permits a single event record for several downstream selections. Shared
preselection must retain every requested output's population. Saving a broader
tree cannot recover events removed upstream or justify assigning a selected
candidate correction to events where that candidate is invalid.

The normal row unit is one event per selected input event, with scalar fields
and vectors for collections or multiple candidate definitions. A flattened
object/pair/candidate table is a separate explicit row policy requiring an
adapter; native event Snapshot does not provide automatic flattening. Retain
typed run/lumisection/event identities plus source-file/source-entry identity
where needed, original object indices, and candidate ordinals for expanded
rows. MC event numbers alone are not assumed unique. Output ordering is not
an identity contract, especially under multithreading or batch merging.

Export complete named weight recipes, with optional individual correction
factors and validity flags. Document whether each total includes luminosity,
sample/component normalization, and region-specific factors. The conventional
`weight` branch must identify its chosen recipe; it must not silently expose
a neutral runner weight used internally for diagnostic booking. Other recipes
can coexist as separate branches. Zero or negative analysis weight is not an
implicit tree selection. A stored correction value and its inclusion in an
exported total weight remain separate choices.

Use existing ROOT/RDataFrame lazy Snapshot and framework I/O, sharing the
resolved graph with histogram actions when both are requested. The native
interface is `variables[name] = {"tree": branch_mapping, "cuts": parent_cuts}`;
the current core snapshots an `Events` tree and writes it under
`trees/<cut>/<sample>/Events` in the final ROOT file. Preserve that layout as a
compatibility choice. Its temporary filenames and final tree paths omit the
tree-variable name, so multiple outputs for the same cut/sample cannot simply
be lowered as independent native tree entries. Coalesce compatible requests
or assign explicit distinct identities through the family adapter. Check
branch-name collisions as well as file/tree-path collisions.

Tree-only and combined outputs must survive local execution, chunk assembly,
and the established batch/merge path with every selected row accounted for.
Reopening a final ROOT file and comparing its contents is the relevant check;
no new logs, manifests, or output-management subsystem is proposed.

## Future nuisances

Keep `nuisances.py` and the native serialized nuisance interface. New nominal
recipes can use an empty nuisance dictionary. Preserve the existing ZZCR
nuisance path during migration; constructing a replacement model is deferred.

Reserve a nominal result plus optional named variations on correction
providers, and explicit dependencies on kinematic views. Empty variations mean
no variation booking, shifted-branch requirement, or extra payload evaluation.
Future integration must distinguish normalization variations, weight-only
variations, and kinematic variations that can change object ordering,
candidate assignment, region membership, and observables. Correlation scopes
and nuisance names require a later explicit analysis decision.

Tree definitions reserve an optional variation export policy with nominal-only
behavior initially. Exporting a future varied weight and representing migrated
events under a kinematic variation are different requirements; a nominal skim
alone may exclude events needed by the latter. Keep those extension points
without producing shifted trees or requiring variation branches now.

Do not freeze selected indices in an interface that would prevent their
recomputation under a future kinematic variation. Do not implement systematic
propagation, friend production, envelopes, or a new statistical model now.

## Ownership and implementation sequence

Evolve the existing `common` modules around source adapters, objects,
candidates, selections, correction providers, weight recipes, observables,
tree branch groups, presets, and a thin framework adapter. These are
responsibilities, not a requirement to create one package or class hierarchy
per concept. Keep era facts and calibration availability separate from
analysis-choice presets.

1. Establish object-view identity and candidate-policy interfaces, preserving
   existing kernels and adding an explicit nominal preset.
2. Bind selections and corrections to those references; introduce named
   weight recipes and explicit region inheritance.
3. Integrate sample construction and selective alias materialization with
   native dictionaries; centralize necessary sparse/weight booking and tree
   output mechanics.
4. Demonstrate ordinary nominal ZZCR, a Z-only analysis, different Z/X object
   definitions, and simultaneous alternative-pairing/weight comparisons;
   exercise histogram-only, tree-only, and combined output modes.
5. Migrate existing leaves progressively, with explicit differences and no
   change of production authority until the established cutover decision.

Focused checks should establish preserved source indices after sorting,
independent simultaneous views and axes, candidate-policy distinctions,
consistent selection/correction domains, inherited parent/child weights,
raw counts with zero/signed weights, and no unused nuisance dependencies.
Preserved nominal recipes need fixed-input event/weight/histogram comparisons.
Tree checks must reopen outputs, verify branch names/types and source/selected
indices, round-trip 64-bit identities including unsigned values with the high
bit set, and account for all rows across chunks and merged jobs. Rebuilding
histograms from exported observables and the matching weight recipe must
reproduce direct bin contents and sums of squared weights with the same fill
unit, validity, selection, and flow rules. Include zero/signed weights,
overlapping regions, empty selections, and simultaneous tree definitions.
Packaged operation needs a bounded worker check of common dependencies.
These are implementation acceptance criteria, not checks executed for this
proposal. No physics or runtime behavior has been changed by this document.
