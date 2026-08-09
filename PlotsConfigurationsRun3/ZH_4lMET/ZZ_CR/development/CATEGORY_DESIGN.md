# Bounded category design

## Decision

The recommended `standard` profile contains 35 diagnostic projections and
839 category-variable actions. It retains the three rich inclusive views,
then adds only declared flavor, stream, and selected stream-by-flavor views.
No code constructs a general Cartesian product.

| Region | Inclusive | Flavor/topology | Stream | Curated intersection | Total |
| --- | ---: | ---: | ---: | ---: | ---: |
| DY | 1 | 2 | 3 | 6 | 12 |
| ZZCR | 1 | 3 | 3 | 5 | 12 |
| SR | 1 | 7 | 3 | 0 | 11 |
| Total | 3 | 12 | 9 | 11 | 35 |

DY keeps its full 3-by-2 stream-priority versus selected-Z-flavor closure
matrix. This is the one region where every leaf directly diagnoses dataset
stream/trigger closure. The cross-flavor stream leaves are logically possible
because DY does not veto extra leptons; their zero occupancy in some bounded
samples is itself a useful contamination check.

ZZCR keeps the expected pure-flavor leaves `EGAMMA_4E` and `MUON_4MU`, plus
all three stream-priority views of `2E2MU`. The four remaining members of a
blind 3-by-3 matrix are omitted. Fifth-lepton vetoes and trigger legs make
MuonEG/Muon 4e and MuonEG/EGamma 4mu either logically incompatible with the
selected final state under normal trigger behavior or useful only as raw
trigger-path anomalies; the stream and topology marginals already expose
those anomalies at lower cost. The two zero-occupancy mixed-topology fallback
leaves remain because they test a concrete priority/de-duplication failure
mode and are logically possible when the cross trigger is inefficient.

SR keeps both X-flavor marginals and a mechanically exclusive/exhaustive
five-topology partition built only from selected `Z0` and `X` flavors. The
six stream-by-X-flavor views are useful in `detailed`, where bounded ZH
occupancy populated five of six leaves, but are not needed in `standard`.
The 15 stream-by-topology leaves are omitted from every ordinary profile.

## Metadata semantics

Every category records `view_type`, `partition_family`,
`is_exclusive_within_family`, `is_overlapping_projection`, and
`diagnostic_purpose`. Flavor, stream, topology, trigger-priority, and DY
stream-by-flavor families are exclusive internally. The curated ZZ family is
also mutually exclusive but intentionally not exhaustive. Families overlap
one another as projections: an event may simultaneously appear in an
inclusive, flavor, stream, and curated-intersection view.

The trigger profile uses the exclusive integer `triggerFamilyPriority`
partition. It does not filter on overlapping raw `Trigger_*` bits.

## Variable tiers

Activation is keyed by `(physics_region, view_type)`:

| View | DY variables/category | ZZCR/SR variables/category | Purpose |
| --- | ---: | ---: | --- |
| inclusive | 25 | 50 | Full normal analysis view |
| flavor/topology | 19 | 31 | Physics closure without recoil/angular duplication |
| stream | 17 | 25 | Trigger/stream acceptance diagnostics |
| stream-flavor | 15 | 15 | Focused intersection check |
| trigger priority | 17 | 25 | Exclusive trigger-family acceptance |

Definitions, binning, folds, and registry hashes remain immutable. Exact
`VARIABLE_INCLUDE` bypasses the normal view tier for requested variables but
still respects region applicability; `VARIABLE_EXCLUDE` removes requested
entries without altering definitions.

## Occupancy evidence

`category_occupancy.json` records Filter/Count results from staged CERN
NanoAOD: ZZ files for all five eras, a 2024 ZH file, and 2024 MuonEG DATA.
The study covers four v12 MC samples, two v15 MC samples, one v15 DATA sample,
and 45,376 examined entries. It dependency-sliced the graph to selection
aliases and booked no histograms or correction weights.

The bounded ZZ samples populate the expected `EGAMMA_4E`, `MUON_4MU`, and
`MUONEG_2E2MU` leaves in every era with sufficient ZZCR occupancy. The
Muon/EGamma fallback `2E2MU` leaves were zero in this proxy but remain standard
because logical possibility and de-duplication diagnostic value take priority
over a bounded zero. SR stream-by-X-flavor occupancy supports retaining those
six leaves only in `detailed`. A bounded zero is never treated as proof of
logical impossibility.

## Algebra and cost

Truth-table tests prove the DY flavor/stream/intersection identities, ZZCR
topology partition and curated intersections, and the SR topology/X-flavor
identities. The final nominal action counts are:

| Profile | Categories | Actions |
| --- | ---: | ---: |
| minimal | 3 | 125 |
| standard | 35 | 839 |
| flavor | 15 | 473 |
| stream | 12 | 326 |
| trigger | 18 | 460 |
| detailed | 41 | 929 |
| debug | 56 | 1,264 (requires `ALLOW_LARGE_PLAN=1`) |

Standard is 6.712 times the minimal action count but 27.907 times smaller
than the former 23,414-action rectangle. It remains one nominal `ALL` job set
with unchanged region-specific weight factors.
