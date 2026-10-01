"""Opt-in full producer/snapshot demonstration; ordinary production never imports this."""
import argparse
import hashlib
import json
import math
import runpy
import shutil
import subprocess
import time
from collections import Counter, defaultdict
from pathlib import Path

from full_mc import HERE, CHAIN, PRODUCTION, MANIFEST_SHA, NORMALIZATION_SHA
from complete_gate import ASSOCIATION_CPP, mapping_for_role, vector, cell, add

DATA_CHAIN = 'DATAl2loose2024v15__l2loose'
CORE = ['pt', 'eta', 'phi', 'pdgId', 'electronIdx', 'muonIdx']
KEYS = ['run', 'luminosityBlock', 'event']
EXPECTED = {'dy_ee': [42732, 606, 25689, 5911],
            'dy_mumu': [83368, 5914, 5324, 21697]}


def git(root, *args):
    return subprocess.run(['git', '-C', str(root), *args], check=True,
                          capture_output=True, text=True).stdout.strip()


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, value):
    Path(path).write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')


def run(args):
    import ROOT
    import mkShapesRDF
    import numpy as np
    from mkShapesRDF.processor.framework.mRDF import mRDF
    from mkShapesRDF.processor.framework.Steps_cfg import Steps
    from mkShapesRDF.processor.framework.Productions_cfg import Productions
    from mkShapesRDF.processor.data.LeptonSel_cfg import ElectronWP, MuonWP

    started = time.monotonic()
    root = args.producer_root.resolve()
    framework = Path(mkShapesRDF.__file__).resolve().parent
    if framework.parent != root:
        raise RuntimeError(f'Wrong imported producer: {framework}')
    if git(root, 'rev-parse', 'HEAD') != args.producer_revision:
        raise ValueError('Producer HEAD is not the explicitly pinned revision')
    paths = ['mkShapesRDF/processor', 'mkShapesRDF/include']
    if git(root, 'status', '--porcelain', '--', *paths):
        raise ValueError('Uncommitted producer changes invalidate this run')
    trees = {p: git(root, 'rev-parse', f'HEAD:{p}') for p in paths}
    if args.kind == 'original' and trees['mkShapesRDF/processor'] != '9c86299cdd2a8419fd30f48ad73a4fc530a567aa':
        raise ValueError('Original producer tree is not the reviewed demo tree')
    if args.output_dir.exists():
        raise FileExistsError(args.output_dir)
    args.output_dir.mkdir(parents=True)
    harness_sha = digest(__file__)
    shutil.copyfile(__file__, args.output_dir / 'repair_demo-used.py')
    manifest = HERE / 'inputs/inputs.json'
    if digest(manifest) != MANIFEST_SHA:
        raise ValueError('Manifest bytes changed')
    source = next(x for x in json.loads(manifest.read_text())['files'] if x['role'] == args.role)
    is_data = source['is_data']
    stop = args.stop if is_data else source['verified_events_entries']
    if not 0 < stop <= source['verified_events_entries']:
        raise ValueError('Invalid half-open source range')
    if is_data and args.kind != 'repaired':
        raise ValueError('Original DATA is intentionally not rerun with its unsupported JEC configuration')
    receipt = None
    if not is_data:
        p = HERE / 'inputs' / f'normalization-{args.role}.json'
        if digest(p) != NORMALIZATION_SHA[args.role]:
            raise ValueError('Existing full-source receipt changed')
        receipt = json.loads(p.read_text())
        if (receipt['sample'] != source['sample'] or receipt['dataset'] != source['dataset']
            or receipt['matched_input_lfn'] != source['lfn'] or receipt['status'] != 'verified'):
            raise ValueError('Receipt source mismatch')
    if is_data and digest(source['golden_json']) != source['golden_sha256']:
        raise ValueError('Golden JSON bytes changed')
    with __import__('uproot').open(source['pfn'], timeout=60) as f:
        if str(f.file.uuid) != source['verified_root_uuid'] or f['Events'].num_entries != source['verified_events_entries']:
            raise ValueError('Source UUID/entries changed')
    ROOT.gROOT.SetBatch(True)
    if ROOT.IsImplicitMTEnabled():
        raise ValueError('One-thread diagnostic requires implicit MT disabled')
    ROOT.gInterpreter.Declare(f'#include "{framework / "include/headers.hh"}"')
    ROOT.gInterpreter.Declare(ASSOCIATION_CPP)
    chain = DATA_CHAIN if is_data else CHAIN
    xs_file = Productions[PRODUCTION]['xsFile']
    xs_db = runpy.run_path(str((framework / 'processor/framework' / xs_file).resolve()))['xs_db']
    if receipt:
        xs = float(xs_db[source['sample']][0].split('=')[1])
        if not math.isclose(xs, receipt['cross_section_pb'], rel_tol=1e-12):
            raise ValueError('Cross section changed')
    output = args.output_dir / f'{args.role}-{args.kind}.root'
    replacements = {'RPLME_FW': str(framework), 'RPLME_CMSSW': 'Full2024v15',
                    'RPLME_LUMI': '/processor/data/certification/' + Path(source['golden_json']).name if is_data else '',
                    'RPLME_SAMPLENAME': source['sample'],
                    'RPLME_genEventSumw': repr(receipt['gen_event_sumw']) if receipt else '0',
                    'RPLME_OUTPUTFILENAMETMP': repr(str(args.output_dir.resolve())),
                    'RPLME_OUTPUTFILENAME': output.name,
                    'RPLME_EOSPATH': str(args.output_dir.resolve())}
    state = {'sampleName': source['sample'], 'files': [source['pfn']], 'xs_db': xs_db, 'values': []}
    df = mRDF().readRDF('Events', [source['pfn']])
    df = df.Define('diagnostic_source_entry', 'rdfentry_')
    df.df = df.df.Range(0, stop)
    actions = [('input_entries', df.Count())]
    raw_cols = KEYS + ['diagnostic_source_entry'] + ([] if is_data else ['genWeight'])
    raw = df.df.AsNumpy(raw_cols, lazy=True)
    if not is_data:
        df = df.Define('diag_genw2', '(double)genWeight*(double)genWeight')
        actions += [('input_gen_sumw', df.Sum('genWeight')), ('input_gen_sumw2', df.Sum('diag_genw2'))]
    df = df.Filter('((nElectron+nMuon)>1)')
    actions.append(('chain_selection', df.Count()))
    wp_names = ([f'Lepton_isTightElectron_{w}' for w in ElectronWP['Full2024v15']['TightObjWP']]
              + [f'Lepton_isTightMuon_{w}' for w in MuonWP['Full2024v15']['TightObjWP']])
    observations = []
    pre_gate = None
    original_define = mRDF.Define

    def observed_define(self, name, expression, *extra, **kwargs):
        out = original_define(self, name, expression, *extra, **kwargs)
        if name in wp_names or name == 'isLoose':
            if name not in self.GetColumnNames():
                out = original_define(out, 'diag_pre_' + name, name, excludeVariations=['*'])
        return out

    def freeze(frame, prefix, names):
        for name in names:
            frame = frame.Define(prefix + name, name, excludeVariations=['*'])
        return frame

    snapshot_records = []
    for step in Steps[chain]['subTargets']:
        spec = Steps[step]
        if spec['isChain']:
            raise ValueError('Unexpected nested chain')
        if step == 'l2tight':
            # Actual original decision uses prefilter slots. Aligned decision
            # uses the same raw-object mapping and unchanged all-WP OR.
            df = df.Define('diag_positions', 'hwwAssociationPositions(VetoLepton_electronIdx,VetoLepton_muonIdx,VetoLepton_pdgId,Lepton_electronIdx,Lepton_muonIdx,Lepton_pdgId)')
            for name in wp_names:
                df = df.Define('diag_aligned_' + name,
                    f'hwwAlignedBits(diag_pre_{name},diag_positions,VetoLepton_pt.size())')
            terms = lambda prefix: ' || '.join(f'{prefix}{w}[SLOT]>0.5' for w in wp_names)
            def predicate(prefix, multiplicity):
                return f'{multiplicity}>=2 && (' + terms(prefix).replace('SLOT','0') + ') && (' + terms(prefix).replace('SLOT','1') + ')'
            df = df.Define('diag_original_gate', predicate('diag_pre_', 'VetoLepton_pt.size()'))
            df = df.Define('diag_aligned_gate', predicate('diag_aligned_', 'Lepton_pt.size()'))
            cols = KEYS + ['diagnostic_source_entry', 'genWeight', 'diag_original_gate', 'diag_aligned_gate', 'Lepton_pt', 'Lepton_electronIdx', 'Lepton_muonIdx', 'VetoLepton_electronIdx', 'VetoLepton_muonIdx']
            pre_gate = df.df.AsNumpy(cols, lazy=True)
        exec('from ' + spec['import'] + ' import *', state)
        declaration = spec['declare']
        for old, new in replacements.items():
            declaration = declaration.replace(old, new)
        exec(declaration, state)
        module = eval(spec['module'], state)
        if step.startswith('finalSnapshot_'):
            # Explicit bounded NOMINAL persistence; module sequence and all
            # correction expressions remain intact. Systematic spectra are
            # outside this demo's runtime claim.
            module.includeVariations = False
            module.splitVariations = False
            # Keep the configured all-column contract; the typed local
            # checkpoint avoids the former many-column Cache template limit.
            module.columns = ['*']
        if step == 'lepSel':
            mRDF.Define = observed_define
        try:
            df = module.run(df, state['values'])
        finally:
            mRDF.Define = original_define
        actions.append((step, df.Count()))
        if step == 'leptonMaker':
            df = freeze(df, 'diag_maker_', ['Lepton_' + p for p in CORE])
        if step == 'lepSel':
            df = freeze(df, 'diag_sel_', ['Lepton_' + p for p in CORE] + wp_names + ['isLoose'])
        if step == 'jetSelMask':
            # before corrections (MC SF columns are filled later).
            df = freeze(df, 'diag_precorr_', ['Lepton_' + p for p in CORE])
        if step == 'leptonSF':
            names = [n for n in df.GetColumnNames() if n.startswith('Lepton_') and ('SF' in n)]
            df = freeze(df, 'diag_sf_', names)
        if step.startswith('finalSnapshot_'):
            snapshot_records = [v for v in state['values'] if v[0] == 'snapshot']
    if len(snapshot_records) != 1:
        raise ValueError('Expected one nominal configured snapshot callback')
    callback, saved_cols = snapshot_records[0][1]
    # Freeze the computed nominal columns once with ROOT's typed native
    # Snapshot. A many-column Cache compiles a huge tuple and exceeded 23 GiB
    # before event processing here. The supported HWW callback still writes
    # the final file, reading this local immutable checkpoint in its 10k
    # chunks; correction/RNG calculations are not repeated.
    print(f'Checkpointing {len(saved_cols)} nominal columns', flush=True)
    checkpoint = args.output_dir / 'computed-events.root'
    opts = ROOT.RDF.RSnapshotOptions()
    opts.fLazy = True
    frozen = df.df.Snapshot('Events', str(checkpoint), saved_cols, opts)
    frozen.GetValue()
    cache = ROOT.RDataFrame('Events', str(checkpoint))
    raw_values = raw.GetValue()
    gate_values = pre_gate.GetValue() if pre_gate else None
    stages = {n: int(a.GetValue()) for n, a in actions}
    identities = [tuple(int(raw_values[k][i]) for k in KEYS) for i in range(stop)]
    if len(set(identities)) != stop:
        raise ValueError('Duplicate source keys')
    np.savez_compressed(args.output_dir / 'input-identity.npz', **raw_values)
    if gate_values is not None:
        np.savez_compressed(args.output_dir / 'gate-ledger.npz', **gate_values)
    callback(cache)
    if not output.exists():
        raise ValueError('Configured snapshot did not materialize')
    report = {'role': args.role, 'kind': args.kind, 'producer_revision': args.producer_revision,
              'producer_root': str(root), 'imported_package': str(framework), 'producer_trees': trees,
              'manifest_sha256': MANIFEST_SHA, 'harness_sha256': harness_sha, 'source': source, 'range': [0, stop],
              'chain': chain, 'stages': stages, 'output': str(output.resolve()),
              'snapshot_scope': 'actual configured Snapshot module, explicit nominal-only persistence of all configured fields; all preceding modules intact',
              'saved_columns': saved_cols, 'saved_column_count': len(saved_cols),
              'checkpoint_scope': 'exact computed nominal columns written once by ROOT; supported HWW callback consumes local checkpoint without recomputing corrections',
              'rng_scope': 'unchanged sequential production RNG; final before/after yield differences are descriptive, not association-only kinematic attribution',
              'elapsed_seconds': time.monotonic() - started,
              'root_version': ROOT.gROOT.GetVersion(), 'wp_columns': wp_names}
    if not is_data:
        report['input_gen_sumw'] = float(next(a for n,a in actions if n=='input_gen_sumw').GetValue())
        report['input_gen_sumw2'] = float(next(a for n,a in actions if n=='input_gen_sumw2').GetValue())
    with __import__('uproot').open(output) as reopened:
        if reopened['Events'].num_entries != stages[Steps[chain]['subTargets'][-1]]:
            raise ValueError('Reopened snapshot count differs from final producer count')
    report['basic_reopen_count_verified'] = True
    save(args.output_dir / 'production.json', report)
    print(json.dumps({'production': str(args.output_dir / 'production.json'), 'stages': stages, 'elapsed_seconds': report['elapsed_seconds']}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--role', choices=('dy_ee','dy_mumu','muon_c','muon_i','egamma_c','egamma_i'), required=True)
    parser.add_argument('--kind', choices=('original','repaired'), required=True)
    parser.add_argument('--producer-root', type=Path, required=True)
    parser.add_argument('--producer-revision', required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--stop', type=int, default=50000, help='DATA prefix stop; MC always full input')
    run(parser.parse_args())
    # Task-local terminal process only. ROOT/XRootD input-file destruction
    # blocked in File::Close after successful serialization (stack retained).
    # All output callbacks have closed, basic reopening has passed, and failure
    # exceptions above retain their nonzero exit. The separate invariant audit
    # is the scientific acceptance gate.
    import os
    import sys
    sys.stdout.flush()
    sys.stderr.flush()
    os._exit(0)
