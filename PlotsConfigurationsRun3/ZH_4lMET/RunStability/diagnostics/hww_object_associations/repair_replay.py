"""Bounded nominal Z replay using the existing commit-pinned historical runner."""
import argparse
import hashlib
import json
import subprocess
import sys
from collections import defaultdict
from pathlib import Path
from types import ModuleType

HERE = Path(__file__).resolve().parent
LEAF = HERE.parents[1]
REPO = HERE.parents[4]
RUNNER_COMMIT = '7843a7ff8680f6c9ff48b9372cc0a7784468cb6f'
RUNNER_PATH = 'PlotsConfigurationsRun3/ZH_4lMET/RunStability/historical_hww_diagnostic.py'
RUNNER_SHA = '7c92db4b03256f005e3dc095ad708449d9310ddb9392642d9f490cc15e1eb0fa'


def load_reference():
    raw = subprocess.run(['git','-C',str(REPO),'show',RUNNER_COMMIT + ':' + RUNNER_PATH],
                         check=True,capture_output=True).stdout
    if hashlib.sha256(raw).hexdigest() != RUNNER_SHA:
        raise ValueError('Pinned historical replay source bytes changed')
    module = ModuleType('pinned_historical_replay')
    module.__file__ = str(LEAF / 'historical_hww_diagnostic.py')
    exec(compile(raw,module.__file__,'exec'),module.__dict__)
    return module


def run(args):
    import numpy as np
    import ROOT
    sys.path.insert(0,str(LEAF))
    ref = load_reference()
    evidence = json.loads((HERE / 'inputs/parent-pair-evidence.json').read_text())
    pair = next(x for x in evidence['pairs'] if x['role'] == args.role)
    receipt = json.loads((args.production_dir / 'production.json').read_text())
    if receipt['role'] != args.role:
        raise ValueError('Production role mismatch')
    source = receipt['source']
    if source['pfn'] != pair['central_pfn'] or source['source_id'] != pair['source_id']:
        raise ValueError('Production and historical pair refer to different sources')
    environment = json.loads((HERE / 'repair-environment.json').read_text())
    if receipt['manifest_sha256'] != environment['pinned_inputs']['manifest_sha256']:
        raise ValueError('Unexpected input manifest')
    for path, tree in receipt['producer_trees'].items():
        actual = subprocess.run(['git', '-C', str(REPO), 'rev-parse',
                                 receipt['producer_revision'] + ':' + path],
                                check=True, capture_output=True, text=True).stdout.strip()
        if actual != tree:
            raise ValueError('Producer tree does not match recorded revision')
    if receipt['range'][0] != 0:
        raise ValueError('This bounded replay requires a zero-based input prefix')
    if Path(receipt['output']).resolve().parent != args.production_dir.resolve():
        raise ValueError('Snapshot is outside the recorded production directory')
    with np.load(args.production_dir / 'input-identity.npz',allow_pickle=False) as archive:
        raw = {name: archive[name] for name in ref.KEY_FIELDS}
    central = {(int(raw['run'][i]),int(raw['luminosityBlock'][i]),int(raw['event'][i])):
               {'central_source_entry':i,'run':int(raw['run'][i]),
                'luminosityBlock':int(raw['luminosityBlock'][i]),'event':int(raw['event'][i])}
               for i in range(len(raw['event']))}
    if len(central) != receipt['range'][1]:
        raise ValueError('Source key inventory incomplete')
    config = ref.load_compiled(evidence['hww_exact_compiled_pickle_path'])
    categories = ref.TARGET_CATEGORIES[args.role]
    # Retain the exact historical component weight/selection, replacing only
    # its input URI for a fresh snapshot; historical replay keeps original URI.
    original_selector = ref.selected_sample
    if not args.historical:
        def select(config,pair):
            name,samples = original_selector(config,pair)
            sample = samples[name]
            component = sample['name'][0]
            sample['name'] = [(component[0],[receipt['output']],*component[2:])]
            return name,samples
        ref.selected_sample = select
    args.output_dir.mkdir(parents=True,exist_ok=False)
    output_root = args.output_dir / 'z-mass.root'
    raw,full,pre,selected,types,unavailable,runs = ref.replay(
        config,pair,central,categories,LEAF,output_root)
    gate = {}
    if args.role.startswith('dy_'):
        with np.load(args.production_dir / 'gate-ledger.npz',allow_pickle=False) as archive:
            ledger = {name: archive[name] for name in (
                'diagnostic_source_entry', 'diag_original_gate', 'diag_aligned_gate')}
            for i,entry in enumerate(ledger['diagnostic_source_entry']):
                a,b = bool(ledger['diag_original_gate'][i]),bool(ledger['diag_aligned_gate'][i])
                gate[int(entry)] = ('passes_both' if a and b else
                                   'rejected_only_by_actual' if b else
                                   'accepted_only_by_actual' if a else 'rejected_both')
    def total(rows):
        weights = [r['weight'] / (config['lumi'] if args.role.startswith('dy_') else 1) for r in rows]
        return {'events':len(rows),'sumw':sum(weights),'sumw2':sum(w*w for w in weights)}
    summaries = {}
    def outcome(entry):
        if not args.role.startswith('dy_'):
            return 'DATA'
        if entry not in gate:
            if not args.historical:
                raise ValueError('Repaired MC selection is outside its recorded gate universe')
            return 'outside_repaired_gate_universe'
        return gate[entry]

    for category,rows in selected.items():
        groups = defaultdict(list)
        seen = set()
        for row in rows:
            key = tuple(row[k] for k in ref.KEY_FIELDS)
            if key in seen:
                raise ValueError('Duplicate selected event key in category ' + category)
            seen.add(key)
            entry = central[key]['central_source_entry']
            groups[outcome(entry)].append(row)
        summaries[category] = {**total(rows),'by_producer_outcome': {k:total(v) for k,v in groups.items()}}
    ledger_path = args.output_dir / 'selected-events.jsonl'
    with ledger_path.open('x') as stream:
        for category,rows in selected.items():
            for row in rows:
                key = tuple(row[k] for k in ref.KEY_FIELDS)
                entry = central[key]['central_source_entry']
                stream.write(json.dumps({'category':category,'source_entry':entry,
                    'producer_outcome':outcome(entry),**row},sort_keys=True)+'\n')
    summary = {'role':args.role,'view':'historical_part0' if args.historical else receipt['kind'],
               'producer_revision':receipt['producer_revision'],'categories':summaries,
               'compiled_pickle_sha256':ref.PICKLE_SHA256,'reference_runner_commit':RUNNER_COMMIT,
               'reference_runner_sha256':RUNNER_SHA,'recorded_source_lumi_fb':config['lumi'],
               'unit':'MC at 1 fb^-1 using retained full-source baseW; DATA counts',
               'hww_input':pair['hww_pfn'] if args.historical else receipt['output'],
               'rdf_graph_runs':runs,'identity_branch_types':types,'unavailable_details':unavailable,
               'rng_limit':'Original, repaired and historical smearing draws are not held equal; final migration/yield differences are descriptive, not association-only causal effects.',
               'input_scope':'two complete individual MC files or fixed DATA prefix, not complete source/year',
               'root_sha256':hashlib.sha256(output_root.read_bytes()).hexdigest(),
               'selected_ledger_sha256':hashlib.sha256(ledger_path.read_bytes()).hexdigest()}
    (args.output_dir / 'replay.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n')
    print(json.dumps(summaries,sort_keys=True))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--role',required=True)
    parser.add_argument('--production-dir',type=Path,required=True)
    parser.add_argument('--output-dir',type=Path,required=True)
    parser.add_argument('--historical',action='store_true')
    run(parser.parse_args())
