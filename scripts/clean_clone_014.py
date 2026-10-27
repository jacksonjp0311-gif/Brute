"""Clean-clone check for study-014 (BRUTE_PLAN_014 clean_clone; adapted from clean_clone_013, frozen). Exports `git archive <commit>` (default HEAD) into a
fresh temporary directory, restores the gitignored sealed raw files there from their tracked .json.gz
(scripts/study014_storage.py restore, sha256-checked against the block SEALs), and re-runs
make_gates_014 --check, make_paired_014 --check and make_reproducibility_014 --check inside that directory.
PASS iff the tracked-inputs check passes and all three reproduce byte-for-byte. Output: results/study-014/CLEAN_CLONE_014.json
(refuses overwrite; ledger clean_clone_014).

SCORING_INPUTS lists every results/ file the three scoring scripts read (shared with tests/test_release_0110.py::
test_scoring_inputs_tracked): each must be git-tracked, or be a gitignored raw JSON whose tracked .gz restores to its seal.
  PYTHONPATH=. python scripts/clean_clone_014.py [--commit <sha>] [--print]"""
from __future__ import annotations
import argparse,json,os,subprocess,sys,tarfile,tempfile,time,io
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common import check,dumps,write_new

S='results/study-014/'
RAW_GZ=[S+b+'/'+f for b in ('transfer','repro/transfer') for f in ('RESULTS.json','SCIENTIFIC.json')]
TRACKED=[S+x for x in ('transfer/SEAL.json','repro/transfer/SEAL.json',
         'PAIRED_ANALYSIS_014.json','REPRODUCIBILITY_014.json','SECOND_IMPLEMENTATION_014.json','TEST_SUITE_014.json',
         'RUN_STATE_014.json','RUN_T0','HEARTBEAT_014.jsonl','KILL_DRILL_014.json','SEAL.json','GATES_014.json')]+\
        ['results/diag-014/LICENSE_DIAG_SEEN.json','results/diag-014/LICENSE_DIAG_SEEN_B.json']
OPTIONAL_TRACKED=[S+x for x in ('RUN_DONE_014.json','STOP_014.json','STOP_014_ORCHESTRATOR.json')]
SCORING_INPUTS={'tracked':TRACKED,'tracked_if_present':OPTIONAL_TRACKED,'gz_restored':RAW_GZ}
SCRIPTS=('scripts/make_paired_014.py','scripts/make_reproducibility_014.py','scripts/make_gates_014.py')


def git(*a,cwd=ROOT):return subprocess.run(['git',*a],cwd=cwd,check=True,capture_output=True).stdout


def tracked_check(commit='HEAD',root=ROOT):
    files=set(git('ls-tree','-r','--name-only',commit,cwd=root).decode().split('\n'))
    bad=[f for f in TRACKED if f not in files]+[f+'.gz' for f in RAW_GZ if f+'.gz' not in files]
    bad+=[f for f in OPTIONAL_TRACKED if (Path(root)/f).exists() and f not in files]
    ignored_raw=[f for f in RAW_GZ if f in files]
    return {'missing_from_tree':bad,'raw_json_committed_unexpectedly':ignored_raw,'passed':not bad}


def run(commit='HEAD'):
    commit=git('rev-parse',commit).decode().strip();t=time.time();rep={'schema':'brute.clean-clone.v2','commit':commit,
        'scoring_inputs':SCORING_INPUTS,'tracked':tracked_check(commit)}
    with tempfile.TemporaryDirectory(prefix='brute-clean-014-') as td:
        tarfile.open(fileobj=io.BytesIO(git('archive','--format=tar',commit)),mode='r:').extractall(td,filter='data')
        env={k:v for k,v in os.environ.items() if not k.startswith(('BRUTE_','STUDY_DIR'))};env['PYTHONPATH']=td
        steps=[('restore',[sys.executable,'scripts/study014_storage.py','restore'])]+[(Path(s).stem,[sys.executable,s,'--check']) for s in SCRIPTS]
        rep['steps']={}
        for name,cmd in steps:
            p=subprocess.run(cmd,cwd=td,env=env,capture_output=True,text=True)
            rep['steps'][name]={'returncode':p.returncode,'stdout_tail':p.stdout[-400:],'stderr_tail':p.stderr[-800:]}
    rep['elapsed_informational_s']=round(time.time()-t,1)
    rep['passed']=rep['tracked']['passed'] and all(v['returncode']==0 for v in rep['steps'].values());return rep


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--commit',default='HEAD');ap.add_argument('--print',action='store_true')
    ap.add_argument('--output',default=str(ROOT/S/'CLEAN_CLONE_014.json'));a=ap.parse_args()
    r=run(a.commit)
    if a.print:print(json.dumps(r,indent=1));raise SystemExit(0 if r['passed'] else 1)
    write_new(Path(a.output),r);print({'passed':r['passed'],'tracked':r['tracked'],'steps':{k:v['returncode'] for k,v in r['steps'].items()}})
    raise SystemExit(0 if r['passed'] else 1)
