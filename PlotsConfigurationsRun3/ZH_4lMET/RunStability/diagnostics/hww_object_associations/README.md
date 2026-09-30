# Bounded 2024 HWWNano object-association demonstration

**Status: six pinned event witnesses, observed locally on LPC on 2026-09-30.**
This is a producer diagnostic on the separate
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
