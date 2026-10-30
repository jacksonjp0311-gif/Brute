"""Study BRUTE-0260-QUERY-THROUGHPUT-029 runner (experiments/BRUTE_PLAN_029.json as amended by BRUTE_PLAN_029_A1;
deviation #130 fixes every definition added here). New file. The 026 arm S1, truth, counts and identify are imported
unchanged from experiments/brute_study_026.py; arm S3 is the frozen v0.25.0 class (brute.scalesearch3.ScaleRegion3);
new: arms S4, S4_nowit and S4_nosym (brute.scalesearch4.ScaleRegion4), throughput fields, clause a against S1, S3
and the latent truth, and S1 identify by the S4 routine on S1's own trace (S1 has no identify).

Cases: 42 main (target seeds, eps 0) + 9 stress (first 3 seeds of scale8/12/16, eps 0.05) = 51, dispatched in the
order control_cycle3, scale8, stress, scale12, scale16. Per case, in order:
  eps 0  : S4 [55 s], S4_nowit [55 s], S4_nosym [55 s], S1 [55 s], S3 [55 s]; identify [10 s] after each arm that
           finished all 176 steps;
  eps > 0: S4 [40 s], S1 [40 s], S3 [40 s] (F only).
Queries, deadlines, UNKNOWN rules, certificates rgn_decide(i+1, 8, ...) on exact answers only: as study-028.
  PYTHONPATH=. python experiments/brute_study_029.py --block main --workers 8
  PYTHONPATH=. python experiments/brute_study_029.py --block smoke --output /tmp/x --workers 8
"""
from __future__ import annotations
import argparse,time
from pathlib import Path
from time import perf_counter
from concurrent.futures import ProcessPoolExecutor,as_completed
from brute.noisyregion import rgn_decide
from brute.scalesearch3 import ScaleRegion3
from brute.scalesearch4 import ScaleRegion4,identify_trace
from brute.region import codes_mask
from experiments import worlds_026 as W
from experiments import brute_study_026 as S26
from experiments.brute_common_029 import PLAN,AMENDMENT,FREEZE,STUDY_DIR,load,sha,write_new,check_freeze,check,Checkpoint
from scripts.check_seeds_029 import check_run_seeds,SMOKE

STEPS=W.HORIZON;BURN_IN=S26.BURN_IN;QUERY_S=S26.QUERY_S;ID_S=10.0
SOLVER4='g3'       # deviation #130: g3 beat m22 on smoke seeds 9590004-006 (scale12) before the source freeze
FAM_ORDER=('scale16','scale12','scale8','control_cycle3')     # family list (as 026)
DISPATCH=('control_cycle3','scale8','stress','scale12','scale16')
SCHEMA_CASE='brute.case.v26_0'
BUDGET={0:{'S4':55.0,'S4_nowit':55.0,'S4_nosym':55.0,'S1':55.0,'S3':55.0},'noisy':{'S4':40.0,'S1':40.0,'S3':40.0}}
ORDER={0:('S4','S4_nowit','S4_nosym','S1','S3'),'noisy':('S4','S1','S3')}
EXACT_SEARCH=('S4','S4_nowit','S4_nosym','S3')
S4_ARMS=('S4','S4_nowit','S4_nosym')


class _S3(S26._S2):
    def __init__(self,k,n=S26.N_MAX):self.R=ScaleRegion3(n,k,W.S_BITS,QUERY_S)


class _S4(S26._S2):
    def __init__(self,k,witness=True,symmetry=True):self.R=ScaleRegion4(S26.N_MAX,k,W.S_BITS,QUERY_S,witness,SOLVER4,symmetry)


def make_arm(name,w):
    if name=='S3':return _S3(w.k)
    if name=='S4':return _S4(w.k)
    if name=='S4_nowit':return _S4(w.k,witness=False)
    if name=='S4_nosym':return _S4(w.k,symmetry=False)
    return S26.ARM_CLS[name](w.k)


def run_arm(name,w,tr,T,budget):
    """As brute_study_028.run_arm; S4, S4_nowit, S4_nosym and S3 observe the final action; observe wall is recorded too."""
    k=w.k;A=make_arm(name,w);t0=perf_counter();dl=t0+budget;omax=0.0
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
                if i<STEPS-1 or name in EXACT_SEARCH:
                    to=perf_counter();A.observe(tr['actions'][i],tr['readings'][i+1],dl);omax=max(omax,perf_counter()-to)
                continue
            break
        extra['status_end']=A.status()
        if name=='S3':
            extra['n_lo']=A.R.n_lo;extra['pool']=len(A.R.pool);extra['solves']=A.R.solves;extra['n_max']=A.R.n
            extra['timing_informational']=dict(A.R.timing);extra['chunks']=A.R.S.chunks;extra['solver_wins']=dict(zip(A.R.S.names,A.R.S.wins))
        if name in S4_ARMS:
            R=A.R;extra.update({'pool':len(R.pool),'solves':R.solves,'solver_unknowns':R.unknowns,'chunks':R.chunks,'builds':R.builds,
                                'queries_by_witness':R.queries_by_witness,'queries_by_solve':R.queries_by_solve,'n_max':R.n,
                                'timing_informational':dict(R.timing)})
        extra['exact_answers']=sum(1 for r in unk for u in r if u==0)
        return A,{'sup':sup,'unk':unk,'cert':cert,'steps_done':steps_done,**extra,**S26._counts(unk,cert,T),
                  'arm_wall_informational':perf_counter()-t0,'query_max_informational':qmax,
                  'observe_max_informational':omax}
    except BaseException:
        A.close();raise


def _pair(a,b):
    cmpd=mis=exc=0
    for i in range(STEPS):
        for j in range(len(a['unk'][i])):
            if a['unk'][i][j]==0 and b['unk'][i][j]==0:cmpd+=1;mis+=a['sup'][i][j]!=b['sup'][i][j]
            else:exc+=1
    return {'compared':cmpd,'mismatches':mis,'excluded':exc}


def clause_a(arms,T):
    """Exact answers of S4 against S1 and S3 (where both answered exactly) and against the latent truth (the true next
    code must lie in every exact support at eps 0): {'vs_S1', 'vs_S3': (compared, mismatches, excluded), 'truth_missing'};
    S4_nowit and S4_nosym against S1 are recorded too (descriptive)."""
    out={}
    for o in ('S1','S3'):
        a,b=arms['S4'],arms[o];cmpd=mis=exc=0
        for i in range(STEPS):
            for j in range(len(a['unk'][i])):
                if a['unk'][i][j]==0 and b['unk'][i][j]==0:cmpd+=1;mis+=a['sup'][i][j]!=b['sup'][i][j]
                else:exc+=1
        out['vs_'+o]={'compared':cmpd,'mismatches':mis,'excluded':exc}
    for x in ('S4_nowit','S4_nosym'):
        if x in arms:out[x+'_vs_S1']=_pair(arms[x],arms['S1'])
    a=arms['S4'];out['truth_checked']=sum(1 for i in range(STEPS) for j in range(len(a['unk'][i])) if a['unk'][i][j]==0 and a['sup'][i][j] is not None)
    out['truth_missing']=sum(1 for i in range(STEPS) for j in range(len(a['unk'][i]))
                             if a['unk'][i][j]==0 and a['sup'][i][j] is not None and T[i][j] not in a['sup'][i][j])
    return out


def identify_s1(A,w,tr,steps_done):
    """S1 has no identify: the S4 routine (brute.scalesearch4.identify_trace) on S1's own trace, including the final
    reading S1 does not observe; run only when S1 finished all steps (as every exact arm)."""
    class _R:pass
    B=_R();B.R=_R();R=A.R
    masks=list(R.masks)+[codes_mask(tr['readings'][STEPS],W.S_BITS)];acts=list(R.acts)+[tr['actions'][STEPS-1]]
    B.R.identify=lambda dl:identify_trace(masks,acts,w.k,1<<W.S_BITS,S26.N_MAX,dl,SOLVER4)
    if steps_done==STEPS:check(len(masks)==STEPS+1,'S1 trace length')
    return S26.identify(B,w,steps_done,ID_S)


def run_case(seed,family,eps,block='main'):
    w=W.world(seed,family);tr=W.trajectory(w,seed,eps);T=S26.truth(w,tr);B=BUDGET[0 if eps==0 else 'noisy'];arms={}
    for name in ORDER[0 if eps==0 else 'noisy']:
        A,rec=run_arm(name,w,tr,T,B[name])
        try:
            if eps==0:rec['identify']=S26.identify(A,w,rec['steps_done'],ID_S) if name in EXACT_SEARCH else identify_s1(A,w,tr,rec['steps_done'])
        finally:A.close()
        arms[name]=rec
    ca=clause_a(arms,T)
    if eps!=0:ca['truth_missing_note']='eps > 0: hard-masked exact search assumes noise-free readings; not a clause-a input'
    return {'schema':SCHEMA_CASE,'family':family,'seed':seed,'eps':eps,'n':w.n,'k':w.k,'arms':arms,'clause_a':ca}


def _rank(j):return DISPATCH.index('stress' if j[0]=='stress' else j[1])


def jobs_for(plan,block):
    R=plan['heldout_ranges']['targets']
    main=[('main',f,s,0.0) for f in FAM_ORDER for s in range(R[f][0],R[f][1]+1)]
    stress=[('stress',f,s,0.05) for f in ('scale8','scale12','scale16') for s in range(R[f][0],R[f][0]+3)]
    if block=='main':return sorted(main+stress,key=_rank)     # stable: within a rank, seed order
    if block=='smoke':
        out=[];s=SMOKE[0]
        for f in FAM_ORDER:
            for e in ((0.0,) if f=='control_cycle3' else (0.0,0.05)):out.append(('smoke',f,s,e));s+=1
        return out
    raise ValueError(block)


def key(job):return '/'.join(map(str,job))


def check_job(job,plan):
    block,fam,seed,eps=job
    if block=='main':check(eps==0.0,'main eps');check_run_seeds('target',[seed],plan,family=fam)
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
    result={'schema':'brute.study.v26_0','plan':plan,'block':block,'smoke':smoke,'complete':complete,'job_keys':keys,'cases':cases,**extra}
    write_new(output/'RESULTS.json',result);write_new(output/'SCIENTIFIC.json',no_time(result))
    write_new(output/'SEAL.json',{'study':plan['study'],'block':block,'results_sha256':sha(output/'RESULTS.json'),
        'scientific_sha256':sha(output/'SCIENTIFIC.json'),'plan_sha256':sha(PLAN),'amendment_sha256':sha(AMENDMENT),'freeze_sha256':None if smoke else sha(FREEZE),
        'case_count':len(cases),'expected_case_count':len(keys),'complete':complete,'smoke':smoke,
        **({'missing_job_keys':extra['missing_job_keys']} if 'missing_job_keys' in extra else {})})


def seal_partial(output,block,limit=None,reason='study cap',extra_checkpoint=None):
    """Seal what is there. extra_checkpoint: a restored pushed snapshot (deviation #126 item 5, reused by #128 and #130); its cases are used only
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
    check(load(AMENDMENT)['amendment']=='A1','amendment A1 missing')
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
    if a.block!='main':check(not Path(out).resolve().is_relative_to(STUDY_DIR.resolve()),'smoke output must not be inside results/study-029')
    if a.seal_partial:print('sealed partial',seal_partial(out,a.block,a.limit,a.reason,a.snapshot))
    else:run(out,a.workers,a.block,a.limit);print('done')
