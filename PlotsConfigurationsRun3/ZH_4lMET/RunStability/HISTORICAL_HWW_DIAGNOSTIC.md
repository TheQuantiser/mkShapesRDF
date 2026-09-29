# Paired 2024 HWW historical diagnostic

`historical_hww_diagnostic.py` is an opt-in local replay of one verified
HWWNano `part0` against the first 80,000 or 200,000 entries of its paired
central NanoAOD parent. It does not edit or recompile the retained 2024
RunStability configuration. Its inputs are the frozen central manifest and
the independently checked parent-pair evidence produced for the paired
low-pT study.

The script pins
`config_26-08-18_21_38_40.pkl` by SHA256
`6f7fb49e310297baa0e2b0624d58a46d2e88c28f96481991bfc95e7dea2e86ef`.
It uses the compiled aliases, sample/component weights, DY parent cut,
category expressions, `Z0_mass` axis, and 109.08 fb^-1 MC multiplier. The
compiled runner was `zz_cr_runner.py` in the former
`ZZ_CR_RunStability` leaf. The current `run_stability_runner.py` has the same
executable methods as the historical file at Git revision `6f9b4ff`; their
diff contains only a module docstring and an error message. The deleted
runtime include paths are redirected to four retained, byte-identical
helpers under `ZH_4lMET/ZZ_CR`, with each helper SHA256 checked before use.
The diagnostic omits the compiled DATA run-resolved TH2 contract because it
books only the two requested trigger-path categories and their historical
`Z0_mass` TH1s.

From the mkShapesRDF checkout, with `COFFEA` set to the local Coffea checkout:

```bash
source start.sh
python PlotsConfigurationsRun3/ZH_4lMET/RunStability/historical_hww_diagnostic.py \
  --manifest "$COFFEA/docs/diagnostics/paired-2024-lowpt/inputs.json" \
  --pair-evidence "$COFFEA/docs/diagnostics/paired-2024-lowpt/parent-pair-evidence.json" \
  --role dy_ee \
  --output-dir /path/to/new/local/diagnostic/dy_ee
```

The `--role` choices are `dy_ee`, `dy_mumu`, `muon_c`, `muon_i`,
`egamma_c`, and `egamma_i`. The two applicable historical path categories
for that role are always booked together in one graph; `--include-all` also
books `DY_ALL`. The output directory must not already exist.

Each fresh output has `historical_histograms.root`,
`historical_rows.jsonl`, and `receipt.json`. One row represents one HWW
event whose full `(run, luminosityBlock, event)` key occurs in the selected
central prefix. It carries the original central entry index, HWW part entry,
full-width event identity, independent historical gate decisions, selected-Z
pair indices and kinematics, retained tight WP bits, trigger/stream and
weight components, the actual preselection result, and both final category
results. The receipt names unavailable detail fields explicitly and records
the exact inputs, source ID, hashes, cutflow, and ROOT graph-run count. The
reader rejects duplicate keys at every stage. Central NanoAOD identity is
unsigned 32/32/64; HWW stores all three fields as signed 64-bit. HWW event
values use the checked two's-complement inverse `value & (2**64 - 1)` before
the key join. Run and luminosity block must lie in unsigned 32-bit range.

The central-prefix key filter runs before historical aliases and weights.
Full-alias diagnostic actions are booked before the original preselection;
the historical runner then books both category histograms. ROOT executes
the actions lazily when the runner asks for its preselection count. The
DY ee representative receipt `dy_ee_v4` reported `rdf_graph_runs: 1`.
The first successful outputs for the other five roles used the same runner
graph construction but were not independently instrumented with this counter.

## Interpreting the retained tight-muon bit

In the paired Muon C DATA prefix, central source entry 234 is retained as
historical HWW part0 entry 65, with `(run, luminosityBlock, event) =
(379416, 147, 131724611)`. The retained `Lepton_muonIdx` values are `[1, 2]`.
The raw HWW `Muon` collection has three muons: index 0 has `tightId = false`
and `promptMVA ≈ -0.049`, while indices 1 and 2 satisfy every named 2024
tight-muon working-point ingredient in that same file. Their raw tight-WP
statuses are `[false, true, true]`. The retained
`Lepton_isTightMuon_cut_TightID_pfIsoTight_HWW_tthmva_67` values are instead
`[false, true]`; the selected pair should have `[true, true]` when the bits
are indexed by the retained `Lepton_muonIdx` values. The stored bit therefore
disagrees with the raw inputs for the first retained lepton. The independent
`nLepton_isTightMuon` count is 2. This `Lepton_isTightMuon_*` array records
an offline working-point decision, not a trigger bit. The historical
RunStability aliases use this stored array for both `L2TightLeading2` and
`bestZ0IdxWithID`, so this event fails the leading-two gate and has no valid
historical Z candidate.

The same HWW event retains `VetoLepton_muonIdx = [0, 1, 2]`, the ordering
before HLT-safe removal. Its recomputed tight statuses are `[false, true,
true]`, whose first two bits equal the stored retained vector `[false,
true]`. In an HWW-only audit of the 508 paired Muon C/I `IsoMu24` events
selected only by Coffea and failing the historical leading-two gate, 503
stored vectors disagree with the tight statuses at the retained raw-muon
indices. In 507 of the 508 events, the stored vector equals the prefix of
the tight-status vector in `VetoLepton_muonIdx` order. Both conditions hold
in 502 events. These are comparisons of branches within the retained HWW
files and strongly identify stale prefilter positional indexing in those
records; they do not require assuming that the central NanoAOD muon contents
match another file.

The current `LeptonMaker.py` sorts the original combined lepton collection by
`pT`. The current `LeptonSel.py` defines the propagated tight arrays on that
collection, then applies the HLT-safe mask to only six core `Lepton_*` arrays
(`pt`, `eta`, `phi`, `pdgId`, `electronIdx`, `muonIdx`). It does not filter the
already defined tight arrays in the same step. This source ordering is
consistent with an unfiltered tight bit remaining at a position whose core
lepton was removed. The historical HWW producer ran from a dirty worktree;
its exact source is unavailable, so this is a plausible source mechanism,
not proof of the precise historical code path. The retained HWW branch
values and raw-muon working-point inputs directly establish a positional
association error in that event. The intended Coffea selection still requires
both selected Z leptons to pass their tight working point; it deliberately omits
the separate leading-two event gate.

This replay measures the historical shape selection only for HWW-retained
events. A central-prefix event absent from HWW cannot be assigned a historical
post-HWW alias or category decision by this route; the central producer
entry ledger is needed to identify the first upstream divergence. The replay
does not establish complete DATA certification, global stream deduplication,
full-catalog normalization, or physics equivalence of central and HWW
producers.
