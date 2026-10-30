"""Study BRUTE-0240-SCALE-REPLAY-027 runner (experiments/BRUTE_PLAN_027.json; deviation #126 fixes every definition
added here). New file. The 026 arm classes, truth, counts, identify and clause a are imported unchanged from
experiments/brute_study_026.py (frozen in BRUTE_SOURCE_FREEZE_026); only the job order, the seeds and the informational
arm S2_tight are new.

Cases: 84 main (42 target seeds x eps 0 / 0.02) + 9 stress (first 3 seeds of scale8/12/16, eps 0.05) = 93, dispatched
in the order control_cycle3, scale8, stress, scale12, scale16 (plan 027 new_items.job_order). Per case, in order:
  eps 0  : S2 [55 s], identify(S2) [10 s], S1 [55 s], then S2_tight [TIGHT_S s] and identify(S2_tight) [10 s];
  eps > 0: S2 [40 s], S1 [40 s], RGB6_on_S2 [35 s].
S2_tight = ScaleRegion(n, k) with n_max equal to the world's true state count n (plan 027 informational_arm; it reads
only the family's declared state count, never the hidden machine). It runs on eps-0 main cases only and is never gated.
Everything else (queries, deadlines, UNKNOWN rules, certificates rgn_decide(i+1, 8, ...) on exact answers only, record
layout brute.case.v23_0 plus arm 'S2_tight') is as study-026.
  PYTHONPATH=. python experiments/brute_study_027.py --block main --workers 8
  PYTHONPATH=. python experiments/brute_study_027.py --block smoke --output /tmp/x --workers 8
"""
from __future__ import annotations
import argparse,time
from pathlib import Path
from time import perf_counter
from concurrent.futures import ProcessPoolExecutor,as_completed
from brute.noisyregion import rgn_decide
from brute.scalesearch import ScaleRegion
from experiments import worlds_026 as W
from experiments import brute_study_026 as S26
from experiments.brute_common_027 import PLAN,FREEZE,STUDY_DIR,load,sha,write_new,check_freeze,check,Checkpoint
from scripts.check_seeds_027 import check_run_seeds,SMOKE

STEPS=W.HORIZON;BURN_IN=S26.BURN_IN;QUERY_S=S26.QUERY_S;TIGHT_S=25.0;ID_S=10.0
FAM_ORDER=('scale16','scale12','scale8','control_cycle3')     # family list (as 026)
DISPATCH=('control_cycle3','scale8','stress','scale12','scale16')
SCHEMA_CASE='brute.case.v24_0'


class _S2Tight(S26._S2):
    def __init__(self,k,n):self.R=ScaleRegion(n,k,W.S_BITS,QUERY_S)


def run_arm(name,w,tr,T,budget):
    """As brute_study_026.run_arm, for any arm object; S2 and S2_tight observe the final action (deviation #124 item 3)."""
    k=w.k;A=_S2Tight(k,w.n) if name=='S2_tight' else S26.ARM_CLS[name](k);t0=perf_counter();dl=t0+budget
    sup=[[None]*k for _ in range(STEPS)];unk=[[-1]*k for _ in range(STEPS)];cert=[[None]*k for _ in range(STEPS)]
    qmax=0.0;steps_done=0;extra={}
    try:
        A.initialize(tr['readings'][0],dl)
        for i in range(STEPS):
            if perf_counter()>=dl:break
            for b in range(k):
                if perf_counter()>=dl:break
                tq=perf_counter();s,u=A.support(b,dl);qmax=max(qmax,perf_counter()-tq)
                sup[i][b]=None if s is None else list(s);unk[i][b]=int(u)
                if u==0:cert[i][b]=rgn_decide(i+1,BURN_IN,s)
            else:
                steps_done=i+1
                if i<STEPS-1 or name in ('S2','S2_tight'):A.observe(tr['actions'][i],tr['readings'][i+1],dl)
                continue
            break
        extra['status_end']=A.status()
        if name in ('S2','S2_tight'):extra['n_lo']=A.R.n_lo;extra['pool']=len(A.R.pool);extra['solves']=A.R.solves;extra['n_max']=A.R.n
        if name=='RGB6':extra['T6_last']=A.R.last['T'] if A.R.last else None
        return A,{'sup':sup,'unk':unk,'cert':cert,'steps_done':steps_done,**extra,**S26._counts(unk,cert,T),
                  'arm_wall_informational':perf_counter()-t0,'query_max_informational':qmax}
    except BaseException:
        A.close();raise


def run_case(seed,family,eps,block='main'):
    w=W.world(seed,family);tr=W.trajectory(w,seed,eps);T=S26.truth(w,tr);B=S26.budgets(eps);arms={}
    names=list(S26.arms_for(eps))+(['S2_tight'] if eps==0 else [])
    for name in names:
        A,rec=run_arm(name,w,tr,T,TIGHT_S if name=='S2_tight' else B[name])
        try:
            if name in ('S2','S2_tight') and eps==0:rec['identify']=S26.identify(A,w,rec['steps_done'],ID_S)
        finally:A.close()
        arms[name]=rec
    return {'schema':SCHEMA_CASE,'family':family,'seed':seed,'eps':eps,'n':w.n,'k':w.k,'arms':arms,
            'clause_a':S26.clause_a({'S2':arms['S2'],'S1':arms['S1']})}


def _rank(j):return DISPATCH.index('stress' if j[0]=='stress' else j[1])


def jobs_for(plan,block):
    R=plan['heldout_ranges']['targets']
    main=[('main',f,s,e) for f in FAM_ORDER for e in (0.0,0.02) for s in range(R[f][0],R[f][1]+1)]
    stress=[('stress',f,s,0.05) for f in ('scale8','scale12','scale16') for s in range(R[f][0],R[f][0]+3)]
    if block=='main':return sorted(main+stress,key=_rank)     # stable: within a rank, eps 0 then 0.02, seed order
    if block=='smoke':
        out=[];s=SMOKE[0]
        for f in FAM_ORDER:
            for e in ((0.0,0.02) if f=='control_cycle3' else (0.0,0.02,0.05)):out.append(('smoke',f,s,e));s+=1
        return out
    raise ValueError(block)


def key(job):return '/'.join(map(str,job))


def check_job(job,plan):
    block,fam,seed,eps=job
    if block=='main':check(eps in (0.0,0.02),'main eps');check_run_seeds('target',[seed],plan,family=fam)
    elif block=='stress':check(eps==0.05 and fam!='control_cycle3','stress');check_run_seeds('target',[seed],plan,family=fam)
    elif block=='smoke':check_run_seeds('smoke',[seed],plan)
    else:raise ValueError(block)


def run_job(job,plan):
    check_job(job,plan);t0=perf_counter();c=run_case(job[2],job[1],job[3]);c['block']=job[0]
    c['case_wall_informational']=perf_counter()-t0;return key(job),c


def _job(x):return run_job(*x)


def run_jobs(jobs,plan,workers,ckpt,log=print):
    for j in jobs:check_job(j,plan)
    todo=[j for j in jobs if key(j) not in ckpt.done];log(f'{len(jobs)-len(todo)} cached, {len(todo)} to run',flush=True)
    with ProcessPoolExecutor(max(1,workers)) as ex:
        futs=[ex.submit(_job,(j,plan)) for j in todo]
        for n,fu in enumerate(as_completed(futs)):
            k_,c=fu.result();ckpt.add(k_,c);log(f'done {n+1}/{len(todo)} {k_} {c["case_wall_informational"]:.1f}s',flush=True)
    return [ckpt.done[key(j)] for j in jobs]


def _write(output,plan,block,keys,cases,complete,extra):
    from brute.evaluation import no_time
    smoke=block!='main'
    result={'schema':'brute.study.v24_0','plan':plan,'block':block,'smoke':smoke,'complete':complete,'job_keys':keys,'cases':cases,**extra}
    write_new(output/'RESULTS.json',result);write_new(output/'SCIENTIFIC.json',no_time(result))
    write_new(output/'SEAL.json',{'study':plan['study'],'block':block,'results_sha256':sha(output/'RESULTS.json'),
        'scientific_sha256':sha(output/'SCIENTIFIC.json'),'plan_sha256':sha(PLAN),'freeze_sha256':None if smoke else sha(FREEZE),
        'case_count':len(cases),'expected_case_count':len(keys),'complete':complete,'smoke':smoke,
        **({'missing_job_keys':extra['missing_job_keys']} if 'missing_job_keys' in extra else {})})


def seal_partial(output,block,limit=None,reason='study cap',extra_checkpoint=None):
    """Seal what is there. extra_checkpoint: a restored pushed snapshot (deviation #126 item 5); its cases are used only
    for keys the local checkpoint lacks, and any key in both must be byte-identical."""
    import json
    output=Path(output);plan=load(PLAN)
    for nm in ('RESULTS.json','SCIENTIFIC.json','SEAL.json'):check(not (output/nm).exists(),'refusing overwrite '+str(output/nm))
    jobs=jobs_for(plan,block)[:limit] if limit else jobs_for(plan,block);ck=Checkpoint(output/'CHECKPOINT.jsonl');keys=[key(j) for j in jobs]
    done=dict(ck.done);src={'local':len(done),'snapshot_only':0}
    if extra_checkpoint:
        ex=Checkpoint(extra_checkpoint)
        for k_,c in ex.done.items():
            if k_ in done:check(json.dumps(done[k_],sort_keys=True)==json.dumps(c,sort_keys=True),'snapshot differs from local: '+k_)
            else:done[k_]=c;src['snapshot_only']+=1
    have=[k for k in keys if k in done];missing=[k for k in keys if k not in done]
    _write(output,plan,block,keys,[done[k] for k in have],False,{'stop_reason':reason,'missing_job_keys':missing,'case_sources':src})
    return len(have),len(keys)


def run(output,workers,block,limit=None):
    output=Path(output);plan=load(PLAN)
    if block=='main':check_freeze()
    for nm in ('RESULTS.json','SCIENTIFIC.json','SEAL.json'):check(not (output/nm).exists(),'refusing overwrite '+str(output/nm))
    t0=time.perf_counter();jobs=jobs_for(plan,block);jobs=jobs[:limit] if limit else jobs
    output.mkdir(parents=True,exist_ok=True);ck=Checkpoint(output/'CHECKPOINT.jsonl')
    if block=='main':check(not ck.done,'main checkpoint not empty: never resume (standing rule; resume clause not approved)')
    cases=run_jobs(jobs,plan,workers,ck)
    _write(output,plan,block,[key(j) for j in jobs],cases,True,{'total_elapsed_informational':time.perf_counter()-t0})


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--block',choices=('main','smoke'),default='main')
    ap.add_argument('--output');ap.add_argument('--workers',type=int,default=8);ap.add_argument('--limit',type=int)
    ap.add_argument('--seal-partial',action='store_true');ap.add_argument('--snapshot');ap.add_argument('--reason',default='study cap')
    a=ap.parse_args();out=a.output or str(STUDY_DIR/a.block)
    if a.block!='main':check(not Path(out).resolve().is_relative_to(STUDY_DIR.resolve()),'smoke output must not be inside results/study-027')
    if a.seal_partial:print('sealed partial',seal_partial(out,a.block,a.limit,a.reason,a.snapshot))
    else:run(out,a.workers,a.block,a.limit);print('done')
