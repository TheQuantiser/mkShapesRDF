# Bounded 2024 HWWNano object-association demonstration

## Repair demonstration on this branch

**2026-09-30: the full configured event-producing DATA and MC chains wrote
six fresh nominal HWWNano Events snapshots, which passed independent
reopening and association audits.** This work is isolated on
`fix-demo/2024-hwwnano-object-associations`, based on the original demo at
`69ff2dad8ac45c052e0f3364c35317c8ee7c6fa0`. The measured producer repairs
are at `9a0e9be35c27e2907e6201460d0a5de58a091651`; `ZH_devel`, historical
ROOT files, Coffea and the older diagnostic branches were not changed.

Start with the [repair report](REPAIR_REPORT.md). It explains the code changes,
complete-file accepted-key checks, DATA witnesses, final Z replay, runtime,
failed attempts and scientific limits. Supporting files are:

- [repair-environment.json](repair-environment.json): original/repaired source
  trees, installed runtime, fixed PFNs/UUIDs, payloads and hashes.
- [repair-results.json](repair-results.json): stage counts, weighted gate
  outcomes, multiplicity/historical cross-tabs, reopened invariant checks,
  downstream replay and local artifact paths/hashes.
- [repair-witnesses.json](repair-witnesses.json): a small selected set of full-key
  witnesses with raw, maker, filtered, pre-correction and serialized arrays.
- [repair_demo.py](repair_demo.py): opt-in actual producer-through-snapshot
  runner. Normal production never imports it.
- [repair_audit.py](repair_audit.py): independent ROOT reopen and key/array
  audit; also emits selected witness records from already written outputs.
- [repair_original_gate.py](repair_original_gate.py): output-only extension of
  the unchanged original gate diagnostic, persisting the exact accepted keys.
- [repair_replay.py](repair_replay.py): bounded use of the commit-pinned
  historical replay and exact compiled selection/weights.

The two complete MC files produce **43,338 ee / 89,282 μμ events**, exactly
the independently aligned reference keys, with zero one-lepton survivors.
All six snapshots have zero checked association anomalies, including
**1,419 ee / 978 μμ** real corrected-pT reorderings. The four DATA outputs
retain 3,189 / 3,590 EGamma C/I and 11,927 / 11,447 Muon C/I entries from
their respective 0:50,000 prefixes. DATA's loose chain legitimately permits
single retained leptons.

### Environment and reproduction

Use the existing LPC framework installation and CMS remote-file access.
ROOT 6.38, the recorded CVMFS payloads, pinned input/historical PFNs, Golden
JSON and retained exact compiled RunStability pickle must remain accessible.
No DAS query, new normalization scan, scheduler submission or stage-out is
performed. The scripts reject changed source identities and pre-existing
output directories; do not substitute files silently.

The visible repair checkout used here is
`/uscms_data/d3/mwadud/private/mkShapesRDF_devel/fix-demo-2024-hwwnano-object-associations`.
From a clean checkout of this branch beside the established `mkShapesRDF`
installation, run:

```bash
source ../mkShapesRDF/start.sh
export PYTHONPATH="$PWD:${PYTHONPATH:-}"
export PYTHONHASHSEED=0
export XRD_REQUESTTIMEOUT=30
diag=PlotsConfigurationsRun3/ZH_4lMET/RunStability/diagnostics/hww_object_associations
revision=$(git rev-parse HEAD)
out="../codex_analysis/hww-repair-reproduce-$(date -u +%Y%m%dT%H%M%SZ)"
mkdir "$out"

for role in egamma_c egamma_i muon_c muon_i dy_ee dy_mumu; do
  timeout 1800 python -u "$diag/repair_demo.py" \
    --role "$role" --kind repaired --stop 50000 \
    --producer-root "$PWD" --producer-revision "$revision" \
    --output-dir "$out/final-repaired-$role" \
    > "$out/production-$role.log" 2>&1 || exit $?
done
```

`--stop 50000` applies only to DATA. MC uses its complete 158,487 / 222,331
input entries. The original manifest's longer DATA and 80,000-entry MC
windows belong to the earlier study; actual repair intervals are recorded
separately in `production.json`. Each process imports its explicitly pinned
producer checkout and archives the executed harness. The measured commands
used `--producer-revision 9a0e9be35c27e2907e6201460d0a5de58a091651`; a
later documentation-only HEAD has the same repaired producer tree.

Each successful output directory contains `production.json`,
`input-identity.npz`, `computed-events.root`, `<role>-repaired.root`, and, for
MC, `gate-ledger.npz`. All configured event-producing modules are run. The
actual HWW Snapshot callback uses the configured wildcard nominal column
selection from the native checkpoint, subject to its existing serialization
exclusions (`BeamSpot_type`, `Electron_seediEtaOriX`, `Photon_seediEtaOriX`
in these inputs). Auxiliary-key copying and remote publication are outside this
Events-only demonstration. Detailed ROOT and NPZ products remain local.

### Original gate reference and independent audit

The existing complete join is under
`../codex_analysis/hww-complete-join-dy-20260930-bf75c7f-8db4/`. Its source-entry
maps and hashes are described in [complete-join-receipt.json](complete-join-receipt.json).
Reuse it; do not repeat the NanoAOD join. To reproduce the gate reference,
use the clean **original** demo checkout and a separate process:

```bash
original=../demo-2024-hwwnano-object-associations
join=../codex_analysis/hww-complete-join-dy-20260930-bf75c7f-8db4
for role in dy_ee dy_mumu; do
  PYTHONPATH="$(realpath "$original"):$PYTHONPATH" timeout 600 python -u \
    "$diag/repair_original_gate.py" --role "$role" \
    --producer-root "$original" --join-dir "$join" \
    --output-dir "$out/reference-gate-$role" \
    > "$out/reference-$role.log" 2>&1 || exit $?
done

for role in egamma_c egamma_i muon_c muon_i dy_ee dy_mumu; do
  extra=()
  if [[ "$role" == dy_* ]]; then
    extra=(--reference-gate-dir "$out/reference-gate-$role" --join-dir "$join")
  fi
  timeout 600 python "$diag/repair_audit.py" \
    --repaired-dir "$out/final-repaired-$role" \
    --output-dir "$out/audit-final-$role" "${extra[@]}" || exit $?
  timeout 600 python "$diag/repair_audit.py" --witness-only \
    --audit-json "$out/audit-final-$role/audit.json" \
    --repaired-dir "$out/final-repaired-$role" \
    --output-dir "$out/witnesses-final-$role" "${extra[@]}" || exit $?
done
```

The original script requires original HEAD `69ff2dad`, processor/include
tree checks and pinned source evidence. The reference persists existing
actual/aligned gate sets without changing modules or executing smearing.
The audit requires exact accepted keys, not just expected counts, and
independently reopens final ROOT fields. There is no fresh original
final-kinematic snapshot claim.

### Fixed historical-policy Z replay

```bash
for role in egamma_c egamma_i muon_c muon_i dy_ee dy_mumu; do
  for view in repaired historical; do
    extra=()
    if [ "$view" = historical ]; then extra=(--historical); fi
    timeout 600 python -u "$diag/repair_replay.py" \
      --role "$role" --production-dir "$out/final-repaired-$role" \
      --output-dir "$out/replay-$view-$role" "${extra[@]}" \
      > "$out/replay-$view-$role.log" 2>&1 || exit $?
  done
done
```

The executed final outputs are in
`../codex_analysis/hww-repair-demo-20260930/`; their exact paths and hashes,
including the actual replay directory names, are in `repair-results.json`.
Every final producer command ran into a fresh directory and its real output
was audited; no complete scan was repeated just to edit prose. Replays book
one RDF traversal per view. MC uses retained full-source baseW and reports
one-file contributions at 1 fb⁻¹, never partial-file normalization.

Sequential production random draws were preserved. Gate acceptance and
association checks are causal repair evidence; before/after final weights
and yields are descriptive because common-event random variates were not
held fixed. The exact old dirty producer and historical eta-only operation
remain unresolved. Full systematic production, full-year frequency and
published discrepancy attribution are not established by this demonstration.
The task-local CLI explicitly exits after its outputs close and a basic
reopen/count succeeds to avoid the recorded ROOT/XRootD teardown stall;
independent reopening is the output acceptance gate. The report also records
the separate unsigned-high-bit Snapshot limitation.

## Original demonstration retained as evidence

**Status: six pinned event witnesses and a complete two-file DY MC reverse
lookup, observed locally on LPC on 2026-09-30.**
The following sections describe the original producer diagnostic on the separate
`demo/2024-hwwnano-object-associations` branch. It does not change the shared
producer, historical HWWNano, RunStability selections, or published yields.
The [full local result](observed-summary.json) contains exact event keys,
PFNs, ROOT UUIDs, arrays, and stage outcomes. The detailed `events.json`
from the terminal run is under
`../codex_analysis/hww-object-associations-demo-20260930-v2/` in the LPC
workspace; that scratch directory is not part of Git.
The committed summary combines that six-witness result with the separately
executed one-entry correction-column trace and two fresh one-entry MC chain
ledgers described below. It does not present those separate commands as a
single full DATA producer run.

## Complete paired DY files: membership and producer gate

This extension reads **every** `Events` identity in each pinned central
DY→ee/DY→μμ NanoAOD file and its exact historical HWW `part0`. The
manifest's `0:80000` ranges belong to the earlier paired selection study;
this producer audit deliberately uses the verified **complete** entries of
these same two physical MC files and leaves the four DATA files untouched.
The [join script](complete_join.py) checks UUIDs, complete entry counts, parent
evidence, uniqueness on both sides, and HWW's signed `int64` event branch.
The join converts its event value to the unsigned 64-bit bit pattern; these
two files have no negative signed event values, so the high-bit case is an
implemented boundary rule rather than a real-file observation here. A small
in-memory check round-tripped `2^63` and `2^64−1` through signed 64-bit
representations, without claiming an end-to-end high-bit HWW witness. Its
compressed source-entry maps remain in LPC
scratch; the [join receipt](complete-join-receipt.json) and
[compact two-file results](complete-two-file-summary.json) are committed
here. The complete per-role gate JSON remains in LPC scratch with its hash
recorded in the compact result. The matching
`Runs` counts and sums support **file lineage only**; the analysis below
uses uncut `Events.genWeight` and does not normalize these partial files.

| Pinned pair | Central entries | Matched HWW `part0` | Central only | HWW only | Ambiguous |
| --- | ---: | ---: | ---: | ---: | ---: |
| DY→ee | 158,487 | 68,421 | 90,066 | 0 | 0 |
| DY→μμ | 222,331 | 88,692 | 133,639 | 0 | 0 |

The [gate script](complete_gate.py) runs the configured
`MCl2loose2024v15__MCCorr2024v15__JERFrom23BPix__l2tight` modules on
each complete central file, stopping before lepton scale correction and
snapshot. It books all stage counts and pre-gate original indices, tight
vectors, identity and `genWeight` in one `ROOT.RDF.RunGraphs` traversal per
file. A second in-memory branch remaps **all seven electron and six muon**
working-point vectors from `VetoLepton` raw indices to the retained
`Lepton` indices; it then calls the **unchanged** `L2TightSelection` module.
The remap checks unique `(electronIdx,muonIdx)` identities and matching
`pdgId`, with no pT/coordinate matching. Since the unchanged gate indexes
positions 0 and 1, its aligned branch first rejects events with fewer than
two retained leptons. The original branch runs as configured: it can read a
second **prefilter** bit even when only one lepton remains.

| Current producer stage | DY→ee | DY→μμ |
| --- | ---: | ---: |
| Complete central input | 158,487 | 222,331 |
| Chain `nElectron+nMuon>1` | 94,106 | 129,548 |
| After `leptonMaker` | 93,059 | 127,633 |
| After `lepSel` | 78,696 | 121,809 |
| After `jetSelMask` and all intervening modules, immediately before `l2tight` | 74,938 | 116,303 |
| Original `l2tight` accepts | **68,421** | **88,692** |
| Aligned `l2tight` accepts | **43,338** | **89,282** |

The original gate's accepted **keys**, not merely its counts, equal the
historical paired `part0` membership in both files. In the current chain,
83,549 ee and 106,028 μμ entries leave before the gate; another 6,517 ee
and 27,611 μμ fail the original gate. The exact historical failure stage is
unrecoverable from output membership alone because its dirty producer
worktree is unavailable. The eventwise equality is strong corroboration of
the current retention mechanism for these two files, not proof that the old
producer executed the same source lines.
The live producer modules came from the clean `bf75c7f50245891ddad20aa3bced35057148fca2`
demo checkout; no shared module was edited for this measurement.

The next table partitions **all current pre-gate events**. “Actual” means
the configured producer's unchanged tight vectors; “aligned” means those
same WP decisions attached to their retained raw objects. Each row shows
where its events appear in the historical paired `part0`. The signed sums
are raw `genWeight`, in millions; the squared sums are in 10¹². These are
accounting quantities, **not normalized yields**.

| File | Gate outcome | Historical membership | Events | Σ genWeight / 10⁶ | Σ genWeight² / 10¹² |
| --- | --- | --- | ---: | ---: | ---: |
| DY→ee | Pass both | Present | 42,732 | 778.066 | 30.646 |
| DY→ee | Rejected only by actual | Absent | 606 | 10.176 | 0.435 |
| DY→ee | Accepted only by actual | Present | 25,689 | 449.717 | 18.423 |
| DY→ee | Reject both | Absent | 5,911 | 101.577 | 4.239 |
| DY→μμ | Pass both | Present | 83,368 | 1,525.389 | 59.789 |
| DY→μμ | Rejected only by actual | Absent | 5,914 | 105.245 | 4.241 |
| DY→μμ | Accepted only by actual | Present | 5,324 | 77.716 | 3.818 |
| DY→μμ | Reject both | Absent | 21,697 | 379.714 | 15.560 |

Every unlisted opposite historical-membership cell is zero. The net
aligned-gate change is −25,083 ee and +590 μμ in these **two producer files**,
but these are gross producer-retention changes, not changes to the
RunStability Z-mass yield. The current pre-gate replay contains **31,488 ee
and 26,108 μμ events with fewer than two retained leptons**; the aligned
two-position gate rejects all of them. Directly reopening all historical
`Lepton_pt` vectors confirmed `nLepton` equals vector length: **25,638 ee and
5,269 μμ historical survivors have only one retained lepton**. The retained
examples below demonstrate that some are accepted by a stale second bit.
This run did not retain a file-wide eventwise cross-tab of *current* versus
*historical* lepton multiplicity, so the historical one-lepton totals must
not be subtracted from the actual-only outcome as though object multiplicity
were independently proven identical for every key. A one-lepton survivor
cannot form the later two-lepton Z candidate, so treating all these gate
migrations as a plotted-yield change would be wrong.

Representative full-key records are in the compact JSON result. For each
prefilter and retained slot it lists every true configured working point;
all other points in that result's `configured_wp_columns` list are false.

| File/source entry and `(run,lumi,event)` | Actual HWW `part0` | Identity and gate decision |
| --- | --- | --- |
| ee 174 `(1,384532,2060318616)` | Absent | Prefilter `[(e0),(μ0),(e1)]` becomes retained `[e0,e1]`; positions `[0,2]`. Electron WPs such as `wp90iso` are `[1,0,1]`, correctly `[1,1]` after alignment. Actual rejects; aligned accepts. |
| μμ 5 `(1,260002,1443525631)` | Absent | Prefilter `[μ0,μ1,μ2]` becomes `[μ1,μ2]`; positions `[1,2]`. The muon WP union is false at old slot 0 but true at both retained slots. Actual rejects; aligned accepts. |
| ee 8 `(1,384532,2060317109)` | HWW entry 2 | One electron survives; a removed electron's old slot 1 has true WP bits. Actual accepts; aligned two-lepton gate rejects. Direct HWW read confirms `nLepton=1`. |
| μμ 102 `(1,260002,1443526295)` | HWW entry 39 | One muon survives; the prefilter second slot belongs to a removed electron with `testrecipes=true`. Actual accepts; aligned rejects. Direct HWW read confirms `nLepton=1`. |
| μμ 127 `(1,260002,1443526502)` | Absent | Only one muon survives and its prefilter second slot fails the all-WP OR. Both gates reject: this is the expected one-retained-lepton control, not a proven erroneous loss. |

The `l2tight` union includes the configured `Electron_testrecipes` point,
whose source cut is only `Electron_pt>10`. This producer gate is therefore
**not** equivalent to the named tight electron/muon working points used later
by RunStability. The RunStability leaf has no `LepWPCut` alias; its named
selected-Z WPs, leading-two gate, sample weights, and histogram cuts are
separate downstream decisions. No post-HWW selection is fabricated for an
event missing from `part0`.
The two-file MC result does not measure a full-year rate or explain a DATA
discrepancy: DATA does not pass through this MC production `l2tight` skim.

### Exact local commands and retained artifacts

After the environment setup below, from this demo checkout run:

```bash
diag=PlotsConfigurationsRun3/ZH_4lMET/RunStability/diagnostics/hww_object_associations
python "$diag/complete_join.py" --output-dir /path/to/a/new/local/complete-join
python "$diag/complete_gate.py" --manifest "$diag/inputs/inputs.json" \
  --join-dir /path/to/a/new/local/complete-join \
  --output-dir /path/to/a/new/local/complete-ee --role dy_ee
python "$diag/complete_gate.py" --manifest "$diag/inputs/inputs.json" \
  --join-dir /path/to/a/new/local/complete-join \
  --output-dir /path/to/a/new/local/complete-mumu --role dy_mumu
```

The separate read-only historical one-lepton check used:

```bash
python - <<'PY'
import json, uproot, awkward as ak, numpy as np
files = json.load(open('PlotsConfigurationsRun3/ZH_4lMET/RunStability/diagnostics/hww_object_associations/inputs/inputs.json'))['files']
for role in ('dy_ee', 'dy_mumu'):
    item = next(row for row in files if row['role'] == role)
    with uproot.open(item['hww_part0_pfn'], timeout=30) as root:
        arrays = root['Events'].arrays(['nLepton', 'Lepton_pt'], library='ak')
        length = ak.to_numpy(ak.num(arrays['Lepton_pt']))
        assert np.array_equal(length, ak.to_numpy(arrays['nLepton']))
        print(role, int(np.count_nonzero(length == 1)))
PY
```

Each output directory must be fresh. The actual 2026-09-30 run used
`../codex_analysis/hww-complete-join-dy-20260930-bf75c7f-8db4/`,
`../codex_analysis/hww-complete-gate-ee-20260930-bf75c7f/`, and
`../codex_analysis/hww-complete-gate-mumu-20260930-bf75c7f/`.
The identity join took **19.7 s total**; the ee and μμ producer passes took
**83.0 s** and **107.1 s**, respectively. The local compressed entry maps
are SHA-256 `5a3361a93bc3a0aecc5a38be452cbe6975b6d408c1ce1cd8470f`
and `72fdef1c4a28f7439d0a9e91e0f56fd6e998873db318ce5c222cb3ef763a2ad7`;
the committed result includes their exact paths and source UUIDs. No
Condor/DAG job, other sample, production snapshot, or new normalization
scan was run. The existing baseW receipt was supplied only because the
configured chain requires it; these partial files were never divided by
their own `genWeight` sum.
The producer was clean at `bf75c7f` during the measurement; the script now
checks the pinned `processor/` and `include/` Git tree hashes and refuses
dirty or changed producer code on a rerun. The first run's diagnostic
`input_gen_sumw2` used a ROOT `float` product; an independent `float64`
read of the uncut `Events.genWeight` branch gives about
`1.13661967686e14` (ee) and `1.59448907088e14` (μμ), about `5e-9`
relative above that diagnostic field. The committed gate script now casts
to double before squaring. Its per-outcome sums in the table were accumulated
in Python double precision and do not use that full-input reducer.
After the one producer pass per file, the script also gained fail-closed
source-tree, join-map, and raw-index validation; the tree and map checks
passed separately on the retained artifacts. The full producer pass was
not repeated just to exercise those validation-only additions. The reported
counts and weights are the observed first-pass results, and a future run
will use the stricter checks and double squared-weight expression.

## Input and execution contract

The [copied manifest](inputs/inputs.json) and
[parent-pair evidence](inputs/parent-pair-evidence.json) are byte-identical
to the Coffea paired diagnostic inputs at
[`2b5ba43`](https://github.com/TheQuantiser/ZH4l_coffea/tree/2b5ba43d6a264a441498a6a5c76af6e253dd2847/docs/diagnostics/paired-2024-lowpt).
Their SHA-256 hashes are `c47bc8fde91a4c06aeead3c488115585df85194331d5886024f6f74333d8ee98`
and `a49c3c2bddda0a0d006114933cdca43125cfaf24d05996944ea66997dcad7f6b`.
They name exact central NanoAOD and historical HWW `part0` PFNs. The script
requires their hashes, checks the central and HWW ROOT UUIDs and entry counts,
verifies the full `(run, luminosityBlock, event)` identity, and rejects
ambiguous matches. It interprets signed HWW event values by their full
unsigned 64-bit pattern. Historical absence means absence from the **paired
part0**, not from every HWW part or dataset.

The six source entries are Muon C 234, EGamma C 20774, EGamma I 27025 and
46209, DY→ee 174, and DY→μμ 127. The first four HWW entries are 65, 991,
1936, and 3325. [The historical reader](historical.py) reevaluates the named
`Full2024v15` tight working points from raw branches *inside those same HWW
events*. The [live reader](live.py) runs the actual `LeptonMaker`, `LeptonSel`,
and, for MC, `L2TightSelection` modules on exact NanoAOD entries. For one
period-I DATA witness it also runs `LeptonScaleSmearing` directly after
`LeptonSel`. It records the original corrected-pT permutation and the actual
column iteration order through an observation-only wrapper around `mRDF`.
There are **no framework edits or patched nominal vectors**.

| Added file and function | Observation it owns |
| --- | --- |
| [`historical.py` `inspect`](historical.py) | Opens each pinned central/HWW pair, verifies event identity and parent evidence, recomputes raw HWW working-point decisions, and checks the retained bit/eta/phi associations. |
| [`live.py` `run`](live.py) | Runs existing producer modules on a one-entry `RDataFrame`; an opt-in wrapper records the correction permutation and `GetColumnNames` loop order, then restores both Python methods. |
| [`full_mc.py` `run`](full_mc.py) | Runs every configured 2024 MC module on one pinned entry through `l2tight`, recording the first stage to reject it; stops before correction and snapshot. |
| [`run.py` `main` and `check_witness`](run.py) | Fixes the six witnesses, starts a fresh process for each ROOT module declaration, checks their expected association patterns, and writes one local `events.json`. |

The only instrumentation is inside the new diagnostic script. The nominal
`LeptonMaker`, `LeptonSel`, `L2TightSelection`, `LeptonScaleSmearing`, `mRDF`,
and snapshot code are unchanged.

The runtime needs LPC access to the two XRootD endpoints, the repository's
installed ROOT/Coffea-independent mkShapesRDF environment, CVMFS correction
payloads for the one scale witness, and a valid proxy as required by those
endpoints. From a clean LPC checkout of this demo branch, use the repository's
supported [`install.sh`](../../../../../install.sh) once, then activate it:

```bash
cd /path/to/mkShapesRDF-demo-checkout
./install.sh
./install.sh --check
source start.sh
export PYTHONPATH="$PWD:${PYTHONPATH:-}"
export PYTHONHASHSEED=0
```

The actual LPC run reused the already installed runtime from the adjacent
`mkShapesRDF` checkout (the commands below differ only in that setup step):

```bash
cd /uscms_data/d3/mwadud/private/mkShapesRDF_devel/demo-2024-hwwnano-object-associations
source ../mkShapesRDF/start.sh
export PYTHONPATH="$PWD:${PYTHONPATH:-}"
export PYTHONHASHSEED=0
python PlotsConfigurationsRun3/ZH_4lMET/RunStability/diagnostics/hww_object_associations/run.py \
  --manifest PlotsConfigurationsRun3/ZH_4lMET/RunStability/diagnostics/hww_object_associations/inputs/inputs.json \
  --pair-evidence PlotsConfigurationsRun3/ZH_4lMET/RunStability/diagnostics/hww_object_associations/inputs/parent-pair-evidence.json \
  --output-dir /path/to/a/new/local/output-directory
```

`--output-dir` must not exist. The command creates one JSON file and prints
one line per witness. The final LPC verification used the same hashed
input bytes from the adjacent Coffea checkout and a **fresh**
`../codex_analysis/hww-object-associations-demo-20260930-v2` output
directory. It exited zero and wrote `events.json` (58,490 bytes). The only
terminal stderr was ROOT's existing missing EDM dictionary warnings. The
script will fail clearly if a pinned file, payload, UUID, or branch is
unavailable; it never substitutes another file.

To establish the **first failing MC producer stage in this fresh demo**, run
the two exact-entry configured-chain commands after the same setup. They
use the two small, copied
[normalization receipts](inputs/normalization-dy_ee.json) solely to satisfy
the chain's `baseW` module; no MC yield is reported or normalized here.

```bash
python PlotsConfigurationsRun3/ZH_4lMET/RunStability/diagnostics/hww_object_associations/full_mc.py \
  --manifest PlotsConfigurationsRun3/ZH_4lMET/RunStability/diagnostics/hww_object_associations/inputs/inputs.json \
  --role dy_ee --entry 174 --key 1 384532 2060318616 > /path/to/new/local/dy-ee-stage.jsonl
python PlotsConfigurationsRun3/ZH_4lMET/RunStability/diagnostics/hww_object_associations/full_mc.py \
  --manifest PlotsConfigurationsRun3/ZH_4lMET/RunStability/diagnostics/hww_object_associations/inputs/inputs.json \
  --role dy_mumu --entry 127 --key 1 260002 1443526502 > /path/to/new/local/dy-mumu-stage.jsonl
```

The last line of each file is the JSON stage ledger; earlier stdout records
normal module setup. Both bounded commands were executed on LPC and exited
zero. Every earlier module, including corrected jets, `jetSelMask`,
`formulasMC`, and the weight modules, retained the event; `l2tight` was the
first failing stage in each. These fresh one-entry ledgers agree with the
previous larger-prefix producer ledgers in LPC scratch. A zero exit from
`run.py` alone establishes the lepton-module and historical-record patterns,
not the first MC failure in the full chain.

## Observations, with evidence class kept separate

| Witness | Actual historical HWW `part0` | Live current code | Interpretation |
| --- | --- | --- | --- |
| Muon C 234, `(379416,147,131724611)` | Retained raw muons `[1,2]`; named tight bits `[false,true]`, although raw decisions are `[false,true,true]` for `[0,1,2]`. Eta and phi follow the indices. | `LeptonMaker` has `[0,1,2]`; `LeptonSel` retains `[1,2]` while its tight vector remains `[false,true,true]` with length 3. | Historical retained bit 0 describes the removed muon. Current `LeptonSel` demonstrates the prefilter-vector mechanism, but the old snapshot's shortening step cannot be assigned to an exact dirty-worktree line. |
| EGamma C 20774, `(379729,907,1396820419)` | Retained electrons `[0,1]` have `[false,true]`; both raw electrons pass the named tight WP. | Prefilter `VetoLepton` indices contain earlier nonretained leptons; retained indices are `[0,1]` but the tight vector remains the five-position prefilter vector `[false,true,true,false,false]`. | The same positional mask mechanism is live; the historical retained wrong bit is directly observed. |
| EGamma I 27025, `(386509,159,333332716)` | Retained `electronIdx=[0,1]`, eta `[-2.0571,-0.9336]`, raw eta `[-0.9336,-2.0571]`; phi follows `[0,1]` and tight bits are correct. | Before correction, all retained coordinates follow `[0,1]`. Corrected-pT permutation is `[1,0]`. In the fixed-seed run, the actual correction loop leaves **phi** attached to the wrong index (details below). | The historical eta-only error is real. The current run demonstrates a correction-order association hazard, but does **not** recreate the exact historical field pattern. Historical operation unresolved. |
| EGamma I 46209, `(386509,735,1539152813)` | Tight-vector and eta/index mismatches coexist; phi follows the indices. | Prefilter tight vector retains an earlier false position. | Two association failures can coexist; do not add them as independent event losses. |
| DY→ee 174, `(1,384532,2060318616)` | Key absent from the exact 68,421-entry HWW `part0`. | Retained electrons `[0,1]` have current prefilter tight vector `[true,false,true]`; actual isolated `l2tight` rejects. The fresh one-entry configured MC chain records all earlier steps passing and first loss at `l2tight`. | A producer-level loss consistent with stale positional bits. The historical file's absence does not prove the unavailable old producer failed at that same stage. |
| DY→μμ 127, `(1,260002,1443526502)` | Key absent from the exact 88,692-entry HWW `part0`. | One muon survives HLT-safe selection; named tight decisions are false and `l2tight` rejects. The fresh configured chain likewise puts first loss at `l2tight`. | A legitimate configured gate control, not a demonstrated object-association bug or a published Coffea migration. |

The six-witness command runs the real lepton and isolated `l2tight` modules;
the two additional one-entry commands run the full configured MC path through
that filter. `l2tight` precedes lepton correction and the HWW snapshot in the
[2024 MC chain](../../../../../mkShapesRDF/processor/framework/Steps_cfg.py).
An event it rejects cannot be restored by changing a downstream RunStability
alias. DATA has no production `l2tight` stage in this chain; a wrong retained
bit can instead affect RunStability's leading-two and best-Z decisions.

### What the corrected-pT witness establishes

For EGamma I entry 27025, the actual `leptonScale_data` input pT order is
`[38.1262,37.5937]` and `Lepton_newPt` is
`[38.3769,39.2280]`, giving `Lepton_sorting=[1,0]`. The fixed-seed current
loop processed `Lepton_eta` and `Lepton_electronIdx` **before** it redefined
`Lepton_sorting`, and `Lepton_phi` **after**. After the loop, the current
indices and eta are `[1,0]` and `[-2.0571,-0.9336]`, but phi remains in its
old order `[-1.2280,1.9678]`: both phi/index association checks fail.
The detailed result records the complete loop order and each check.

The live event record also lists the `Lepton_*` and `VetoLepton_*` column names
available immediately after `LeptonSel` and after the isolated correction.
Those are **stage-local would-be fields**, not a claimed final current HWWNano
schema: intervening modules were not run for DATA. The configured 2024
[`finalSnapshot_DATA` and `finalSnapshot_JES`](../../../../../mkShapesRDF/processor/framework/Steps_cfg.py)
use `columns=['*']`; the directly reopened historical `part0` supplies the
actual stored branch values used in this comparison.

This behavior follows the current
[`LeptonScaleSmearing.py`](../../../../../mkShapesRDF/processor/modules/LeptonScaleSmearing.py)
loop, which includes `Lepton_sorting` itself and uses its mutable value when
reordering later columns. `mRDF.Define` builds its column list through
`list(set(...))`, so loop order is not an object-association contract. The
`Lepton_rochesterSF` product is also already permuted before that generic
loop. The observed correction result is a **current-source** finding for an
order-changing witness; it cannot identify the exact line that produced the
historical eta-only record because the historical producer's dirty source is
unavailable. The known [issues report](../../KNOWN_HWWNANO_ISSUES.md)
explains the wider implications and keeps the nominal jet-cleaning concern
separate.

## Limits and reproducibility notes

The DATA trace deliberately stops after `LeptonSel`, except for the one
isolated correction witness. An earlier attempted full DATA producer run
failed at a JME `Regrouped_*` `map::at` lookup; this demo neither bypasses JEC
nor claims a full DATA chain or a newly generated snapshot. Direct historical
HWW reading establishes the actual stored snapshot fields. The four DATA
entries establish **existence** of these misassociations, not their 2024
frequency. The two MC absences are limited to their exact paired `part0`.
Neither the published 12.4% muon nor 2.8% electron full-year difference is
quantified by six event witnesses. The source-level correction hazard, the
producer MC skim, and downstream RunStability rejection are distinct
consequences. Original central NanoAOD records are not declared invalid.

The script checks the current producer package tree against the clean
revision pinned by the input manifest. The historical files were produced
from an **unavailable dirty worktree**; that check does not equate the
current clean source to the historical executable. For the previous
historical selection replay and local yield scope, see the
[paired event report](https://github.com/TheQuantiser/ZH4l_coffea/blob/062cfea35ba6a6395b926854228efc94753d02cb/docs/2024-paired-lowpt-event-diagnostic-20260929.md)
and [historical replay note](https://github.com/TheQuantiser/mkShapesRDF/blob/7843a7ff8680f6c9ff48b9372cc0a7784468cb6f/PlotsConfigurationsRun3/ZH_4lMET/RunStability/HISTORICAL_HWW_DIAGNOSTIC.md).
