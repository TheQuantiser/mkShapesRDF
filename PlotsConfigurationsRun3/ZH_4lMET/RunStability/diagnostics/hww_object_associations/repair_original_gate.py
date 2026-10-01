"""Persist missing accepted-key references from the unchanged original gate audit.

Only adds output actions to the existing complete_gate Python diagnostic;
shared original producer modules are imported from the explicitly pinned tree.
"""
import argparse
import hashlib
import inspect
import json
import subprocess
from pathlib import Path

import complete_gate


def run(args):
    root = args.producer_root.resolve()
    commit = subprocess.run(['git','-C',str(root),'rev-parse','HEAD'],check=True,
                            capture_output=True,text=True).stdout.strip()
    if commit != '69ff2dad8ac45c052e0f3364c35317c8ee7c6fa0':
        raise ValueError('Original gate reference requires reviewed 69ff2dad HEAD')
    source = inspect.getsource(complete_gate.run)
    anchor = '    path = output_dir / f"{role}-complete-gate.json"\n'
    if source.count(anchor) != 1:
        raise ValueError('Original diagnostic output anchor changed')
    extra = '''    import numpy as np
    np.savez_compressed(output_dir / 'reference-gate-entries.npz',
        pregate_entries=np.asarray(entries,dtype=np.uint64),
        original_pass_entries=np.asarray(sorted(actual_set),dtype=np.uint64),
        aligned_pass_entries=np.asarray(sorted(aligned_set),dtype=np.uint64),
        run=np.asarray(values['take:run'],dtype=np.uint32),
        luminosityBlock=np.asarray(values['take:luminosityBlock'],dtype=np.uint32),
        event=np.asarray(values['take:event'],dtype=np.uint64),
        genWeight=np.asarray(values['take:genWeight'],dtype=np.float64))
'''
    globals_ = dict(complete_gate.__dict__)
    # All source checks remain active; only the owning checkout is explicit.
    complete_gate.REPO = root
    globals_['REPO'] = root
    exec(compile(source.replace(anchor,extra+anchor),str(Path(__file__)),'exec'),globals_)
    path,report = globals_['run'](complete_gate.HERE/'inputs/inputs.json',
                                 args.join_dir,args.output_dir,args.role)
    report['producer_revision'] = commit
    report['instrumentation'] = 'Output-only persistence of the existing original/aligned gate entry sets; no correction/snapshot modules run.'
    report['original_diagnostic_sha256'] = hashlib.sha256(Path(complete_gate.__file__).read_bytes()).hexdigest()
    report['reference_entries_sha256'] = hashlib.sha256((args.output_dir/'reference-gate-entries.npz').read_bytes()).hexdigest()
    path.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'reference':str(path),'original':report['original_gate_pass'],
                     'aligned':report['aligned_gate_pass'],'elapsed_seconds':report['elapsed_seconds']}))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--role',choices=('dy_ee','dy_mumu'),required=True)
    parser.add_argument('--producer-root',type=Path,required=True)
    parser.add_argument('--join-dir',type=Path,required=True)
    parser.add_argument('--output-dir',type=Path,required=True)
    run(parser.parse_args())
    import os, sys
    sys.stdout.flush()
    sys.stderr.flush()
    os._exit(0)  # Same explicit task-local ROOT/XRootD finalization policy as repair_demo.py.
