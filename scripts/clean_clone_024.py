"""Clean-clone check for study-024 (BRUTE_PLAN_024 GCC; adapted from clean_clone_023). Exports `git archive <commit>` (default HEAD,
no .git) into a temporary directory, restores the gzipped raw files (scripts/study024_storage.py restore, sha256-checked
against the block SEALs), and re-runs make_paired_024 --check, make_reproducibility_024 --check and make_gates_024 --check
there. make_gates_024 reads no live git (git-history clauses come from experiments/COMMIT_ORDER_024.json; deviation #112
fix), so the archive tree must regenerate every gate byte. PASS iff the tracked-inputs check passes and all three
reproduce byte-for-byte. Output: results/study-024/CLEAN_CLONE_024.json (refuses overwrite; ledger clean_clone_024).
SCORING_INPUTS lists every repository file the three scoring scripts read.
  PYTHONPATH=. python scripts/clean_clone_024.py [--commit <sha>] [--print]"""
from __future__ import annotations
import argparse,json,os,subprocess,sys,tarfile,tempfile,time,io
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common import check,dumps,write_new

S='results/study-024/'
RAW_GZ=[S+b+'/'+f for b in ('transfer','repro/reproset') for f in ('RESULTS.json','SCIENTIFIC.json')]
TRACKED=[S+x for x in ('transfer/SEAL.json','repro/reproset/SEAL.json',
         'PAIRED_ANALYSIS_024.json','REPRODUCIBILITY_024.json','SECOND_IMPLEMENTATION_024.json','TEST_SUITE_024.json',
         'RUN_STATE_024.json','RUN_T0','HEARTBEAT_024.jsonl','SEAL.json','GATES_024.json','RUN_024.log','LAUNCH_024.json',
         'LIVE_REFUSAL_024.json')]+['experiments/COMMIT_ORDER_024.json','experiments/BRUTE_SOURCE_FREEZE_024.json','results/RESEARCH_LEDGER.jsonl',
         'results/study-023/PAIRED_ANALYSIS_023.json','results/diag-024/HN_RECOUNT_024.json']+['results/smoke-024/'+x for x in
         ('KILL_DRILL_024.json','RESUME_DRILL_024.json','API_CHECK_024.json')]
OPTIONAL_TRACKED=[S+x for x in ('RUN_DONE_024.json','STOP_024.json','STOP_024_ORCHESTRATOR.json','HB_SENTINEL_024.jsonl','HEARTBEAT_ATTRIBUTION_024.json')]+['results/diag-024/EARLY_WINDOW_024.json',
         'results/diag-024/HOST_PAUSE_PROBE_024.json']
SCORING_INPUTS={'tracked':TRACKED,'tracked_if_present':OPTIONAL_TRACKED,'gz_restored':RAW_GZ}
SCRIPTS=('scripts/make_paired_024.py','scripts/make_reproducibility_024.py','scripts/make_gates_024.py')


def git(*a,cwd=ROOT):return subprocess.run(['git',*a],cwd=cwd,check=True,capture_output=True).stdout


def tracked_check(commit='HEAD',root=ROOT):
    files=set(git('ls-tree','-r','--name-only',commit,cwd=root).decode().split('\n'))
    bad=[f for f in TRACKED if f not in files]+[f+'.gz' for f in RAW_GZ if f+'.gz' not in files]
    bad+=[f for f in OPTIONAL_TRACKED if (Path(root)/f).exists() and f not in files]
    ignored_raw=[f for f in RAW_GZ if f in files]
    return {'missing_from_tree':bad,'raw_json_committed_unexpectedly':ignored_raw,'passed':not bad}


def run(commit='HEAD'):
    commit=git('rev-parse',commit).decode().strip();t=time.time();rep={'schema':'brute.clean-clone.v4','commit':commit,
        'scoring_inputs':SCORING_INPUTS,'tracked':tracked_check(commit)}
    with tempfile.TemporaryDirectory(prefix='brute-clean-024-') as td:
        tarfile.open(fileobj=io.BytesIO(git('archive','--format=tar',commit)),mode='r:').extractall(td,filter='data')
        env={k:v for k,v in os.environ.items() if not k.startswith(('BRUTE_','STUDY_DIR'))};env['PYTHONPATH']=td
        steps=[('restore',[sys.executable,'scripts/study024_storage.py','restore'])]+[(Path(s).stem,[sys.executable,s,'--check']) for s in SCRIPTS]
        rep['steps']={}
        for name,cmd in steps:
            p=subprocess.run(cmd,cwd=td,env=env,capture_output=True,text=True)
            rep['steps'][name]={'returncode':p.returncode,'stdout_tail':p.stdout[-400:],'stderr_tail':p.stderr[-800:]}
    rep['elapsed_informational_s']=round(time.time()-t,1)
    rep['passed']=rep['tracked']['passed'] and all(v['returncode']==0 for v in rep['steps'].values());return rep


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--commit',default='HEAD');ap.add_argument('--print',action='store_true')
    ap.add_argument('--output',default=str(ROOT/S/'CLEAN_CLONE_024.json'));a=ap.parse_args()
    r=run(a.commit)
    if a.print:print(json.dumps(r,indent=1));raise SystemExit(0 if r['passed'] else 1)
    write_new(Path(a.output),r);print({'passed':r['passed'],'tracked':r['tracked'],'steps':{k:v['returncode'] for k,v in r['steps'].items()}})
    raise SystemExit(0 if r['passed'] else 1)
