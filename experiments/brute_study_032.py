"""Study BRUTE-0290-ROBUST-PERCEPTION-032 runner (experiments/BRUTE_PLAN_032.json; deviation #136 fixes every definition
added here). New file; built from experiments/brute_study_031.py (frozen, unchanged). Arm S1, truth and counts are imported
unchanged from experiments/brute_study_026.py; arm S5 is the frozen v0.27.0 class (brute.scalesearch5); new: arm S7
(brute.scalesearch7.ScaleRegion7, noise-tolerant encoding with flip budget B) and arm S7_contra
(brute.scalesearch7.ScaleRegion5C, S5 plus a per-step symmetry-on whole-trace grammar check; descriptive).

Cases: 30 noisy (noisy_scale8/12/16 target seeds, eps 0.05) + 12 clean regression (first 6 noisy_scale12 and first 6
noisy_scale16 seeds, eps 0) + 6 controls (control_cycle3, eps 0) = 48, dispatched longest first: noisy_scale16, clean
noisy_scale16, noisy_scale12, clean noisy_scale12, noisy_scale8, control (seed order within each). The world of family
noisy_scaleN is the frozen worlds_026 scaleN world of the seed (the prefix names the block only).
Per case, arms S7, S7_contra, S5, S1 in that order, each with a 55 s arm budget (the per-arm budget of studies 028-031)
and the 10 s per-query cap. Queries, deadlines, UNKNOWN rules and certificates rgn_decide(i+1, 8, ...) on exact answers
only: as study-031.
Per case (evaluator only; the simulator knows the flips): realised flips (flipped sensor readings), B at the end, within_B
(prefix flips <= B(sensor readings so far) at every step, i.e. the true machine is in S7's CNF at every query) and the
first step where that fails. Per arm: U_inf (U_count, or planned if status_end is grammar_contradicted), F_truth (exact
supports excluding the true next code; certificates contradicted by the true machine) and its checked count.
Per case clause S5_in_S7 (eps 0): S7 exact supports must contain S5's exact supports (S7 may be weaker; a code S5 proves
possible but S7 excludes is a mismatch); equal supports are counted too.
  PYTHONPATH=. python experiments/brute_study_032.py --block main --workers 8
  PYTHONPATH=. python experiments/brute_study_032.py --block smoke --output /tmp/x --workers 8
"""
from __future__ import annotations
import argparse,time
from pathlib import Path
from time import perf_counter
from concurrent.futures import ProcessPoolExecutor,as_completed
from brute.noisyregion import rgn_decide
from brute.scalesearch5 import ScaleRegion5
from brute.scalesearch7 import ScaleRegion7,ScaleRegion5C,flip_budget
from experiments import worlds_026 as W
from experiments import brute_study_026 as S26
from experiments.brute_common_032 import PLAN,FREEZE,STUDY_DIR,load,sha,write_new,check_freeze,check,Checkpoint
from scripts.check_seeds_032 import check_run_seeds,SMOKE

STEPS=W.HORIZON;BURN_IN=S26.BURN_IN;QUERY_S=S26.QUERY_S
SOLVER4='g3';ARM_BUDGET=55.0;EPS_NOISY=0.05
NOISY=('noisy_scale16','noisy_scale12','noisy_scale8');CLEAN=('noisy_scale16','noisy_scale12');CLEAN_PER=6
DISPATCH=('noisy/noisy_scale16','clean/noisy_scale16','noisy/noisy_scale12','clean/noisy_scale12','noisy/noisy_scale8',
          'control/control_cycle3')
SCHEMA_CASE='brute.case.v29_0'
ORDER=('S7','S7_contra','S5','S1')
EXACT_SEARCH=('S7','S7_contra','S5')


def base_family(f):return f[len('noisy_'):] if f.startswith('noisy_') else f


class _S5(S26._S2):
    def __init__(self,k):self.R=ScaleRegion5(S26.N_MAX,k,W.S_BITS,QUERY_S,True,SOLVER4,True)


class _S7(S26._S2):
    def __init__(self,k):self.R=ScaleRegion7(S26.N_MAX,k,W.S_BITS,QUERY_S,True,SOLVER4,True)


class _S7C(S26._S2):
    def __init__(self,k):self.R=ScaleRegion5C(S26.N_MAX,k,W.S_BITS,QUERY_S,True,SOLVER4,True)


def make_arm(name,w):
    if name=='S7':return _S7(w.k)
    if name=='S7_contra':return _S7C(w.k)
    if name=='S5':return _S5(w.k)
    return S26.ARM_CLS[name](w.k)


def _truth_missing(a,T):
    chk=sum(1 for i in range(STEPS) for j in range(len(a['unk'][i])) if a['unk'][i][j]==0 and a['sup'][i][j] is not None)
    mis=sum(1 for i in range(STEPS) for j in range(len(a['unk'][i]))
            if a['unk'][i][j]==0 and a['sup'][i][j] is not None and T[i][j] not in a['sup'][i][j])
    return chk,mis


def run_arm(name,w,tr,T,budget=ARM_BUDGET):
    """As brute_study_031.run_arm (actions in index order); the exact-search arms observe the final action."""
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
        if name in EXACT_SEARCH:
            R=A.R;extra.update({'pool':len(R.pool),'solves':R.solves,'solver_unknowns':R.unknowns,'chunks':R.chunks,'builds':R.builds,
                                'queries_by_witness':R.queries_by_witness,'queries_by_solve':R.queries_by_solve,'n_max':R.n,
                                'timing_informational':dict(R.timing),'cap_stops':R.cap_stops,'build_skips':R.build_skips,
                                'max_chunk_s_informational':R.max_chunk_s,'prop_rate_end_informational':R.prate})
            if name=='S7':extra.update({'flip_budget_end':R.bound,'sensor_readings':R.sensor_readings})
            if name=='S7_contra':extra.update({'contra_checks':R.contra_checks,'contra_unknown':R.contra_unknown})
        extra['exact_answers']=sum(1 for r in unk for u in r if u==0)
        rec={'sup':sup,'unk':unk,'cert':cert,'steps_done':steps_done,**extra,**S26._counts(unk,cert,T),
             'arm_wall_informational':perf_counter()-t0,'query_max_informational':qmax,'observe_max_informational':omax}
        rec['grammar_contradicted']=int(rec['status_end']=='grammar_contradicted')
        rec['U_inf_count']=rec['planned'] if rec['grammar_contradicted'] else rec['U_count']
        rec['F_truth_checked'],rec['F_truth']=_truth_missing(rec,T)
        return A,rec
    except BaseException:
        A.close();raise


def flip_profile(seed,eps):
    """Realised flips (flipped sensor readings), B at the end, within_B at every step (prefix flips <= B(prefix))."""
    fl=W.flips(seed,eps);tot=0;sens=0;first=None
    for t,fr in enumerate(fl[:STEPS+1]):
        tot+=sum(1 for x in fr if x);sens+=len(fr)
        if first is None and tot>flip_budget(sens):first=t
    return {'realised_flips':tot,'sensor_readings':sens,'B_end':flip_budget(sens),'within_B':first is None,'first_exceed_reading':first}


def s5_in_s7(arms):
    a,b=arms['S7'],arms['S5'];cmpd=mis=eq=0
    for i in range(STEPS):
        for j in range(len(a['unk'][i])):
            if a['unk'][i][j]==0 and b['unk'][i][j]==0:
                cmpd+=1;sa,sb=a['sup'][i][j],b['sup'][i][j]
                if sa==sb:eq+=1
                elif sa is None or (sb is not None and not set(sb)<=set(sa)):mis+=1
    return {'compared':cmpd,'mismatches':mis,'equal':eq}


def run_case(seed,family,eps,block='noisy'):
    w=W.world(seed,base_family(family));tr=W.trajectory(w,seed,eps);T=S26.truth(w,tr);arms={}
    for name in ORDER:
        A,rec=run_arm(name,w,tr,T)
        A.close();arms[name]=rec
    out={'schema':SCHEMA_CASE,'family':family,'seed':seed,'eps':eps,'n':w.n,'k':w.k,'arms':arms,'noise':flip_profile(seed,eps),
         'S5_in_S7':s5_in_s7(arms)}
    return out


def _rank(j):return DISPATCH.index(f'{j[0] if j[0]!="smoke" else ("noisy" if j[3]>0 else ("control" if j[1]=="control_cycle3" else "clean"))}/{j[1]}')


def jobs_for(plan,block):
    R=plan['heldout_ranges']['targets']
    noisy=[('noisy',f,s,EPS_NOISY) for f in NOISY for s in range(R[f][0],R[f][1]+1)]
    clean=[('clean',f,s,0.0) for f in CLEAN for s in range(R[f][0],R[f][0]+CLEAN_PER)]
    ctrl=[('control','control_cycle3',s,0.0) for s in range(R['control_cycle3'][0],R['control_cycle3'][1]+1)]
    if block=='main':return sorted(noisy+clean+ctrl,key=_rank)
    if block=='smoke':
        out=[];s=SMOKE[0]
        for f,e in (('noisy_scale16',EPS_NOISY),('noisy_scale16',0.0),('noisy_scale12',EPS_NOISY),('noisy_scale12',0.0),
                    ('noisy_scale8',EPS_NOISY),('control_cycle3',0.0)):out.append(('smoke',f,s,e));s+=1
        return sorted(out,key=_rank)
    raise ValueError(block)


def key(job):return '/'.join(map(str,job))


def check_job(job,plan):
    block,fam,seed,eps=job;R=plan['heldout_ranges']['targets']
    if block=='noisy':check(eps==EPS_NOISY and fam in NOISY,'noisy');check_run_seeds('target',[seed],plan,family=fam)
    elif block=='clean':
        check(eps==0.0 and fam in CLEAN and seed<R[fam][0]+CLEAN_PER,'clean');check_run_seeds('target',[seed],plan,family=fam)
    elif block=='control':check(eps==0.0 and fam=='control_cycle3','control');check_run_seeds('target',[seed],plan,family=fam)
    elif block=='smoke':check_run_seeds('smoke',[seed],plan)
    else:raise ValueError(block)


def run_job(job,plan):
    check_job(job,plan);t0=perf_counter();c=run_case(job[2],job[1],job[3],job[0]);c['block']=job[0]
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
    result={'schema':'brute.study.v29_0','plan':plan,'block':block,'smoke':smoke,'complete':complete,'job_keys':keys,'cases':cases,**extra}
    write_new(output/'RESULTS.json',result);write_new(output/'SCIENTIFIC.json',no_time(result))
    write_new(output/'SEAL.json',{'study':plan['study'],'block':block,'results_sha256':sha(output/'RESULTS.json'),
        'scientific_sha256':sha(output/'SCIENTIFIC.json'),'plan_sha256':sha(PLAN),'freeze_sha256':None if smoke else sha(FREEZE),
        'case_count':len(cases),'expected_case_count':len(keys),'complete':complete,'smoke':smoke,
        **({'missing_job_keys':extra['missing_job_keys']} if 'missing_job_keys' in extra else {})})


def seal_partial(output,block,limit=None,reason='study cap',extra_checkpoint=None):
    """Seal what is there (as study 031); a restored pushed snapshot fills only keys the local checkpoint lacks, and any
    key in both must be byte-identical."""
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
    if a.block!='main':check(not Path(out).resolve().is_relative_to(STUDY_DIR.resolve()),'smoke output must not be inside results/study-032')
    if a.seal_partial:print('sealed partial',seal_partial(out,a.block,a.limit,a.reason,a.snapshot))
    else:run(out,a.workers,a.block,a.limit);print('done')
