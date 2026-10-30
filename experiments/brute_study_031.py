"""Study BRUTE-0280-SIXTEEN-STATE-ID-031 runner (experiments/BRUTE_PLAN_031.json; deviation #134 fixes every definition
added here). New file; built from experiments/brute_study_030.py (frozen, unchanged). Arm S1, truth and counts are
imported unchanged from experiments/brute_study_026.py; arm S5 is the frozen v0.27.0 class (brute.scalesearch5); new:
arms S6 and S6_noorder (brute.scalesearch6.ScaleRegion6, ordered True / False), query ordering for S6, clause a of S6
against S1, S5 and the latent truth, and the identify probe (brute.scalesearch6.identify6) with labels ID/AMB/WRONG/IDU/NR.

Cases: 48 main (target seeds, eps 0) + 6 stress (first 3 seeds of scale12/16, eps 0.05) = 54, dispatched longest first:
scale16, scale12, stress, scale8, control_cycle3 (within a family, seed order). Per case, in order:
  every eps: S6 [55 s at eps 0, 40 s at eps > 0], S6_noorder, S5, S1 (same budgets);
  eps 0: one identify probe [60 s] on the case trace (all 177 readings, 176 actions; the trace is the same for every
  arm), whose label is given to every arm that finished all 176 steps; an arm that did not finish gets NR.
Labels: ID (a unique least machine at n_min, canonically equal to the truth), AMB (a second non-isomorphic machine
found at n_min), WRONG (a unique least machine not equal to the truth; also no machine <= 16), IDU (deadline), NR.
Queries, deadlines, UNKNOWN rules and certificates rgn_decide(i+1, 8, ...) on exact answers only: as study-030; S6 and
S6_noorder answer the actions of a step in the arm's order() and record each answer under its action index.
  PYTHONPATH=. python experiments/brute_study_031.py --block main --workers 8
  PYTHONPATH=. python experiments/brute_study_031.py --block smoke --output /tmp/x --workers 8
"""
from __future__ import annotations
import argparse,time
from pathlib import Path
from time import perf_counter
from concurrent.futures import ProcessPoolExecutor,as_completed
from brute.noisyregion import rgn_decide
from brute.scalesearch import canonical_bfs,simulate
from brute.scalesearch5 import ScaleRegion5
from brute.scalesearch6 import ScaleRegion6,identify6
from brute.region import codes_mask
from experiments import worlds_026 as W
from experiments import brute_study_026 as S26
from experiments.brute_common_031 import PLAN,FREEZE,STUDY_DIR,load,sha,write_new,check_freeze,check,Checkpoint
from scripts.check_seeds_031 import check_run_seeds,SMOKE

STEPS=W.HORIZON;BURN_IN=S26.BURN_IN;QUERY_S=S26.QUERY_S;ID_S=60.0
SOLVER4='g3'
FAM_ORDER=('scale16','scale12','scale8','control_cycle3')
DISPATCH=('scale16','scale12','stress','scale8','control_cycle3')
STRESS_FAMILIES=('scale12','scale16')
SCHEMA_CASE='brute.case.v28_0'
ORDER=('S6','S6_noorder','S5','S1')
BUDGET={0:55.0,'noisy':40.0}
EXACT_SEARCH=('S6','S6_noorder','S5')
LABELS=('ID','AMB','WRONG','IDU','NR')


class _S5(S26._S2):
    def __init__(self,k):self.R=ScaleRegion5(S26.N_MAX,k,W.S_BITS,QUERY_S,True,SOLVER4,True)


class _S6(S26._S2):
    def __init__(self,k,ordered=True):self.R=ScaleRegion6(S26.N_MAX,k,W.S_BITS,QUERY_S,True,SOLVER4,ordered)
    def order(self):return self.R.order()


def make_arm(name,w):
    if name=='S6':return _S6(w.k)
    if name=='S6_noorder':return _S6(w.k,ordered=False)
    if name=='S5':return _S5(w.k)
    return S26.ARM_CLS[name](w.k)


def run_arm(name,w,tr,T,budget):
    """As brute_study_030.run_arm; S6 arms answer in order(); the exact-search arms observe the final action."""
    k=w.k;A=make_arm(name,w);t0=perf_counter();dl=t0+budget;omax=0.0
    sup=[[None]*k for _ in range(STEPS)];unk=[[-1]*k for _ in range(STEPS)];cert=[[None]*k for _ in range(STEPS)]
    qmax=0.0;steps_done=0;extra={};orders=[]
    try:
        A.initialize(tr['readings'][0],dl)
        for i in range(STEPS):
            if perf_counter()>=dl:break
            od=A.order() if hasattr(A,'order') else list(range(k));orders.append(od)
            for b in od:
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
            if name!='S5':extra.update({'extends':R.extends,'reordered_steps':sum(1 for o in orders if o!=sorted(o)),
                                        'clauses_end_informational':R.region.clauses if R.region is not None else 0})
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


def _missing(a,T):
    chk=sum(1 for i in range(STEPS) for j in range(len(a['unk'][i])) if a['unk'][i][j]==0 and a['sup'][i][j] is not None)
    mis=sum(1 for i in range(STEPS) for j in range(len(a['unk'][i]))
            if a['unk'][i][j]==0 and a['sup'][i][j] is not None and T[i][j] not in a['sup'][i][j])
    return chk,mis


def clause_a(arms,T):
    """Exact answers of S6 against S1 and S5 and against the latent truth: {'vs_S1', 'vs_S5', 'truth_checked',
    'truth_missing'}; S6_noorder against S1, S6 and the truth is recorded too (descriptive)."""
    out={'vs_S1':_pair(arms['S6'],arms['S1']),'vs_S5':_pair(arms['S6'],arms['S5']),
         'S6_noorder_vs_S1':_pair(arms['S6_noorder'],arms['S1']),'S6_noorder_vs_S6':_pair(arms['S6_noorder'],arms['S6'])}
    out['truth_checked'],out['truth_missing']=_missing(arms['S6'],T)
    out['S6_noorder_truth_checked'],out['S6_noorder_truth_missing']=_missing(arms['S6_noorder'],T)
    return out


def identify_case(w,tr):
    """The identify probe on the case trace (eps 0): label, n_min, diagnostics."""
    masks=[codes_mask(o,W.S_BITS) for o in tr['readings'][:STEPS+1]];acts=list(tr['actions'][:STEPS])
    t=perf_counter();r=identify6(masks,acts,w.k,1<<W.S_BITS,S26.N_MAX,perf_counter()+ID_S,SOLVER4);wall=perf_counter()-t
    truth_c=canonical_bfs(w.transitions,w.emissions,w.start);m=r['model']
    match=m is not None and canonical_bfs(m[0],m[1],0)==truth_c
    consistent=m is not None and simulate(m[0],m[1],acts,masks)[0]
    if r['unknown']:lab='IDU'
    elif r['second_found']:lab='AMB'
    elif r['unique'] and match:lab='ID'
    else:lab='WRONG'
    used=set(zip(tr['states'][:STEPS],acts))
    return {'label':lab,'n_min':r['n_min'],'unique':bool(r['unique']),'match':bool(match),'unknown':bool(r['unknown']),
            'second_found':bool(r['second_found']),'model_consistent':bool(consistent),
            'WRONG_sound':int(lab=='WRONG' and not consistent),
            'truth_n':w.n,'truth_reachable':len(truth_c[1]),'truth_pairs':w.n*w.k,'truth_pairs_exercised':len(used),
            'truth_pairs_unexercised':w.n*w.k-len(used),'states_visited':len(set(tr['states'])),'wall_informational':wall}


def arm_identify(probe,steps_done):
    if steps_done!=STEPS:return {'ran':False,'label':'NR','ID':0}
    return {'ran':True,'label':probe['label'],'ID':int(probe['label']=='ID'),'n_min':probe['n_min']}


def run_case(seed,family,eps,block='main'):
    w=W.world(seed,family);tr=W.trajectory(w,seed,eps);T=S26.truth(w,tr);bud=BUDGET[0 if eps==0 else 'noisy'];arms={}
    for name in ORDER:
        A,rec=run_arm(name,w,tr,T,bud)
        A.close();arms[name]=rec
    out={'schema':SCHEMA_CASE,'family':family,'seed':seed,'eps':eps,'n':w.n,'k':w.k,'arms':arms}
    if eps==0:
        p=identify_case(w,tr);out['identify_probe']=p
        for name in ORDER:arms[name]['identify']=arm_identify(p,arms[name]['steps_done'])
    ca=clause_a(arms,T)
    if eps!=0:ca['truth_missing_note']='eps > 0: hard-masked exact search assumes noise-free readings; not a clause-a input'
    out['clause_a']=ca
    return out


def _rank(j):return DISPATCH.index('stress' if j[0]=='stress' else j[1])


def jobs_for(plan,block):
    R=plan['heldout_ranges']['targets']
    main=[('main',f,s,0.0) for f in FAM_ORDER for s in range(R[f][0],R[f][1]+1)]
    stress=[('stress',f,s,0.05) for f in STRESS_FAMILIES for s in range(R[f][0],R[f][0]+3)]
    if block=='main':return sorted(main+stress,key=_rank)
    if block=='smoke':
        out=[];s=SMOKE[0]
        for f in FAM_ORDER:
            for e in ((0.0,) if f in ('control_cycle3','scale8') else (0.0,0.05)):out.append(('smoke',f,s,e));s+=1
        return sorted(out,key=lambda j:DISPATCH.index('stress' if j[3]>0 else j[1]))
    raise ValueError(block)


def key(job):return '/'.join(map(str,job))


def check_job(job,plan):
    block,fam,seed,eps=job
    if block=='main':check(eps==0.0,'main eps');check_run_seeds('target',[seed],plan,family=fam)
    elif block=='stress':check(eps==0.05 and fam in STRESS_FAMILIES,'stress');check_run_seeds('target',[seed],plan,family=fam)
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
    result={'schema':'brute.study.v28_0','plan':plan,'block':block,'smoke':smoke,'complete':complete,'job_keys':keys,'cases':cases,**extra}
    write_new(output/'RESULTS.json',result);write_new(output/'SCIENTIFIC.json',no_time(result))
    write_new(output/'SEAL.json',{'study':plan['study'],'block':block,'results_sha256':sha(output/'RESULTS.json'),
        'scientific_sha256':sha(output/'SCIENTIFIC.json'),'plan_sha256':sha(PLAN),'freeze_sha256':None if smoke else sha(FREEZE),
        'case_count':len(cases),'expected_case_count':len(keys),'complete':complete,'smoke':smoke,
        **({'missing_job_keys':extra['missing_job_keys']} if 'missing_job_keys' in extra else {})})


def seal_partial(output,block,limit=None,reason='study cap',extra_checkpoint=None):
    """Seal what is there (as study 030); a restored pushed snapshot fills only keys the local checkpoint lacks, and any
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
    if a.block!='main':check(not Path(out).resolve().is_relative_to(STUDY_DIR.resolve()),'smoke output must not be inside results/study-031')
    if a.seal_partial:print('sealed partial',seal_partial(out,a.block,a.limit,a.reason,a.snapshot))
    else:run(out,a.workers,a.block,a.limit);print('done')
