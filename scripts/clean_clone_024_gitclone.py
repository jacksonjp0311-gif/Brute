"""Supplementary clean-clone rescoring for study-024 (BRUTE_PLAN_024 release checks; adapted from clean_clone_023_gitclone).
Same steps as scripts/clean_clone_024.py (restore, then make_paired_024 / make_reproducibility_024 / make_gates_024 --check),
but the tree comes from `git clone --no-local` at the commit, so .git is present. Reported next to GCC; it never replaces or
re-scores GCC. Output: results/study-024/CLEAN_CLONE_024_GITCLONE.json (refuses overwrite).
  PYTHONPATH=. python scripts/clean_clone_024_gitclone.py [--commit <sha>]"""
from __future__ import annotations
import argparse,os,subprocess,sys,tempfile,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common import write_new
from scripts.clean_clone_024 import S,SCRIPTS,SCORING_INPUTS,git,tracked_check


def run(commit='HEAD'):
    commit=git('rev-parse',commit).decode().strip();t=time.time()
    rep={'schema':'brute.clean-clone-gitclone.v1','commit':commit,'scoring_inputs':SCORING_INPUTS,'tracked':tracked_check(commit),
         'label':'Observed; supplementary to the frozen GCC (git archive), which stays FAIL'}
    with tempfile.TemporaryDirectory(prefix='brute-gitclone-024-') as td:
        r=Path(td)/'r';subprocess.run(['git','clone','-q','--no-local',str(ROOT),str(r)],check=True)
        subprocess.run(['git','-c','advice.detachedHead=false','checkout','-q',commit],cwd=r,check=True)
        env={k:v for k,v in os.environ.items() if not k.startswith(('BRUTE_','STUDY_DIR','SMOKE'))};env['PYTHONPATH']=str(r)
        steps=[('restore',[sys.executable,'scripts/study024_storage.py','restore'])]+[(Path(s).stem,[sys.executable,s,'--check']) for s in SCRIPTS]
        rep['steps']={}
        for name,cmd in steps:
            p=subprocess.run(cmd,cwd=r,env=env,capture_output=True,text=True)
            rep['steps'][name]={'returncode':p.returncode,'stdout_tail':p.stdout[-400:],'stderr_tail':p.stderr[-800:]}
    rep['elapsed_informational_s']=round(time.time()-t,1)
    rep['passed']=rep['tracked']['passed'] and all(v['returncode']==0 for v in rep['steps'].values());return rep


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--commit',default='HEAD')
    ap.add_argument('--output',default=str(ROOT/S/'CLEAN_CLONE_024_GITCLONE.json'));a=ap.parse_args()
    r=run(a.commit);write_new(Path(a.output),r)
    print({'passed':r['passed'],'steps':{k:v['returncode'] for k,v in r['steps'].items()}});raise SystemExit(0 if r['passed'] else 1)
