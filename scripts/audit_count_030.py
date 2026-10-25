"""Mismatch COUNT for the study-005 second implementation (v0.3.0 errata, review H1). Does not edit the frozen reference.

experiments/v030_independent_reference.audit() stops at the first mismatch and otherwise returns the literal
'mismatches': 0, so its "0 mismatches" means "ran to completion". This wrapper replays every (case, arm) trace with the
reference's own audit_arm(), catches each failure and keeps going, so it reports a real count of mismatching arm traces
(granularity: one count per (case, arm) trace; inside a trace the reference still stops at its first differing field,
which is recorded). `--mutate K` first injects K single-field errors into K distinct, deterministically chosen arm
traces of an in-memory copy and checks that exactly those K traces are counted (mutation test).

Wording (review H1): this is a second implementation by the same author, with no `brute` import, not an independent or
third-party audit; it shares the world generators bgr89/bgr90.worlds with the study runner.

  python scripts/audit_count_030.py --workers 4 [--limit N] [--mutate K] [--out PATH]
"""
from __future__ import annotations
import argparse,copy,json,random,sys,time
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common_005 import STUDY_DIR,load
from experiments.v030_independent_reference import audit_arm

MUTATIONS=('certificate','status','logloss','action')


def _one(args):
    c,arm,plan,tau=args
    full=arm in ('A3','P3') and 'observed' in c['arms'][arm]['trace'][0]
    try:audit_arm(c,arm,plan,tau,full);return None
    except Exception as e:return f'{type(e).__name__}: {str(e)[:300]}'


def mutate(c,arm,kind,rng):
    """Change one field of one step of c['arms'][arm]; returns a description."""
    tr=c['arms'][arm]['trace']
    if kind=='logloss' and not any(isinstance(r.get('logloss'),float) for r in tr):kind='certificate'   # slim arms store no log-loss
    idx=[i for i,r in enumerate(tr) if (kind!='logloss' or isinstance(r.get('logloss'),float))]
    i=rng.choice(idx);r=tr[i]
    if kind=='certificate':r['certificate']=(r['certificate']+1)%4 if r['certificate'] is not None else 0
    elif kind=='status':r['status']='CERTIFIED' if r['status']!='CERTIFIED' else 'POSSIBLE_SET'
    elif kind=='logloss':r['logloss']=r['logloss']+1e-6
    elif kind=='action':r['action']=1-r['action']
    return f'{kind} at step index {i}'


def count(res,workers=4,limit=None,mutate_k=0,seed=20261025):
    plan=res['plan'];tau=plan['residual_surprise']['tau']
    cases=res['cases']+res['extended_cases']
    if limit:cases=cases[:limit]
    jobs=[[c,arm] for c in cases for arm in sorted(c['arms'])]
    injected={}
    if mutate_k:
        rng=random.Random(seed);picks=rng.sample(range(len(jobs)),mutate_k)
        for n,j in enumerate(picks):
            c=copy.deepcopy(jobs[j][0]);jobs[j][0]=c
            injected[j]=mutate(c,jobs[j][1],MUTATIONS[n%len(MUTATIONS)],rng)
    args=[(c,arm,plan,tau) for c,arm in jobs]
    if workers<=1:outs=[_one(a) for a in args]
    else:
        with ProcessPoolExecutor(workers) as ex:outs=list(ex.map(_one,args,chunksize=4))
    mism=[{'family':jobs[k][0]['family'],'seed':jobs[k][0]['seed'],'mask_rate':jobs[k][0]['mask_rate'],'arm':jobs[k][1],'error':o}
          for k,o in enumerate(outs) if o is not None]
    out={'schema':'brute.audit-count.v1','study':plan['study'],'arm_traces_checked':len(jobs),'mismatching_arm_traces':len(mism),
         'mismatches':mism,'granularity':'one count per (case, arm) trace; first differing field recorded',
         'wording':'second implementation by the same author, no brute import; not an independent or third-party audit'}
    if mutate_k:
        flagged={k for k,o in enumerate(outs) if o is not None}
        out['mutation_test']={'injected':len(injected),'detected_injected':len(flagged&set(injected)),
                              'flagged_not_injected':len(flagged-set(injected)),
                              'injections':[{'arm':jobs[k][1],'seed':jobs[k][0]['seed'],'mask_rate':jobs[k][0]['mask_rate'],'what':v} for k,v in injected.items()],
                              'passed':flagged==set(injected)}
    return out


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--workers',type=int,default=4);ap.add_argument('--limit',type=int)
    ap.add_argument('--mutate',type=int,default=0);ap.add_argument('--out')
    a=ap.parse_args()
    from scripts.study005_storage import ensure_raw;ensure_raw(STUDY_DIR)
    t0=time.time();res=load(STUDY_DIR/'RESULTS.json')
    out=count(res,a.workers,a.limit,a.mutate);out['elapsed_informational_s']=round(time.time()-t0,1)
    s=json.dumps(out,indent=1,sort_keys=True)+'\n'
    if a.out:Path(a.out).parent.mkdir(parents=True,exist_ok=True);Path(a.out).write_text(s)
    print(json.dumps({k:v for k,v in out.items() if k!='mismatches'},indent=1)[:3000])
