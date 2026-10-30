"""Study BRUTE-0230-SCALE-026 runner (experiments/BRUTE_PLAN_026.json; deviation #123, which fixes every definition used
here). New file.

Cases: 84 main (42 target seeds x eps 0 / 0.02) + 9 stress (first 3 seeds of scale8/12/16, eps 0.05) = 93, ordered
largest worlds first. Each case runs the declared random action policy for 176 actions (177 readings) and, in order:
  eps 0  : S2 = ScaleRegion(16, k) [55 s], identify() [10 s], S1 = frozen RegionSpace(16, k, s=2) [55 s];
  eps > 0: S2 [40 s], S1 [40 s], RGB6_on_S2 = ScaleBettingSpace(16, k) [35 s].
Per step i = 0..175 every arm answers support(b) for each action b (on readings 0..i), then observes action i and
reading i+1. An arm stops at its deadline (checked between calls); all its later queries are NOT RUN (unk -1, count as
UNKNOWN). S1 queries over 10 s wall are UNKNOWN with the answer discarded (sup None, unk >= 1). A query answers exactly
iff unk == 0. Certificates: rgn_decide(i+1, 8, support) on exact answers only (a support carrying an UNKNOWN code is never
certified); false iff different from the latent next code (evaluator-side only; no learner sees the truth).
Record (brute.case.v23_0): per arm 'sup'[i][b] (sorted code list or None), 'unk'[i][b] (int; -1 = not run),
'cert'[i][b] (code or None), counts; timing keys end in _informational. Seeds: scripts/check_seeds_026.
  PYTHONPATH=. python experiments/brute_study_026.py --block main --workers 8
  PYTHONPATH=. python experiments/brute_study_026.py --block smoke --output /tmp/x --workers 8
"""
from __future__ import annotations
import argparse,time
from pathlib import Path
from time import perf_counter
from concurrent.futures import ProcessPoolExecutor,as_completed
from brute.region import RegionSpace
from brute.noisyregion import rgn_decide
from brute.scalesearch import ScaleRegion,canonical_bfs
from brute.scalebetting import ScaleBettingSpace
from brute.evaluation import no_time
from experiments import worlds_026 as W
from experiments.brute_common_026 import PLAN,FREEZE,STUDY_DIR,load,sha,write_new,check_freeze,check,Checkpoint
from scripts.check_seeds_026 import check_run_seeds,SMOKE

N_MAX=16;BURN_IN=8;QUERY_S=10.0;STEPS=W.HORIZON
BUDGET={0:{'S2':55.0,'ID':10.0,'S1':55.0},'noisy':{'S2':40.0,'S1':40.0,'RGB6':35.0}}
ORDER={0:('S2','S1'),'noisy':('S2','S1','RGB6')}
FAM_ORDER=('scale16','scale12','scale8','control_cycle3')
SCHEMA_CASE='brute.case.v23_0'


def arms_for(eps):return ORDER[0 if eps==0 else 'noisy']


def budgets(eps):return BUDGET[0 if eps==0 else 'noisy']


def truth(w,tr):
    """Latent next code after each action b from the state at time i (evaluator only)."""
    return [[w.emissions[w.transitions[q][b]] for b in range(w.k)] for q in tr['states'][:STEPS]]


class _S1:
    def __init__(self,k):self.R=RegionSpace(N_MAX,k=k,s=W.S_BITS)
    def initialize(self,o,dl):self.R.initialize(o)
    def observe(self,a,o,dl):self.R.observe(a,o)
    def support(self,b,dl):
        R=self.R
        if R.status=='budget_exhausted':return None,1
        R.unk=0;t=perf_counter();s=R.predict_support(b);dt=perf_counter()-t
        if dt>QUERY_S:return None,max(1,R.unk)
        return (None if s is None else tuple(s)),R.unk
    def close(self):self.R.close()
    def status(self):return self.R.status


class _S2:
    def __init__(self,k):self.R=ScaleRegion(N_MAX,k,W.S_BITS,QUERY_S)
    def initialize(self,o,dl):self.R.initialize(o)
    def observe(self,a,o,dl):self.R.observe(a,o,dl)
    def support(self,b,dl):return self.R.support(b,dl)
    def close(self):self.R.close()
    def status(self):return self.R.status


class _RGB6:
    def __init__(self,k):self.R=ScaleBettingSpace(N_MAX,k,query_s=QUERY_S)
    def initialize(self,o,dl):self.R.initialize(o)
    def observe(self,a,o,dl):self.R.observe(a,o)
    def support(self,b,dl):
        R=self.R
        if R.status=='budget_exhausted':return None,1
        u0=R.unknown_total;s=R.predict_support(b);u=R.unknown_total-u0
        return (None if s is None else tuple(s)),u
    def close(self):
        if self.R.region is not None:self.R.region.close();self.R.region=None
    def status(self):return self.R.status


ARM_CLS={'S1':_S1,'S2':_S2,'RGB6':_RGB6}


def run_arm(name,w,tr,T,budget):
    k=w.k;A=ARM_CLS[name](k);t0=perf_counter();dl=t0+budget
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
                if i<STEPS-1 or name=='S2':A.observe(tr['actions'][i],tr['readings'][i+1],dl)
                continue
            break
        extra['status_end']=A.status()
        if name=='S2':extra['n_lo']=A.R.n_lo;extra['pool']=len(A.R.pool);extra['solves']=A.R.solves
        if name=='RGB6':extra['T6_last']=A.R.last['T'] if A.R.last else None
        return A,{'sup':sup,'unk':unk,'cert':cert,'steps_done':steps_done,**extra,**_counts(unk,cert,T),
                  'arm_wall_informational':perf_counter()-t0,'query_max_informational':qmax}
    except BaseException:
        A.close();raise



def _counts(unk,cert,T):
    planned=sum(len(r) for r in unk);U=sum(1 for r in unk for u in r if u!=0)
    nc=sum(1 for r in cert for c in r if c is not None)
    F=sum(1 for i,r in enumerate(cert) for b,c in enumerate(r) if c is not None and c!=T[i][b])
    late=[(i,b) for i in range(88,STEPS) for b in range(len(unk[0]))]
    return {'planned':planned,'U_count':U,'certificates':nc,'F':F,'late_queries':len(late),
            'late_certificates':sum(1 for i,b in late if cert[i][b] is not None)}


def identify(A,w,steps_done,budget):
    if steps_done!=STEPS:return {'ran':False,'n_min':None,'unique':False,'match':False,'unknown':True,'ID':0}
    t=perf_counter();r=A.R.identify(perf_counter()+budget)
    m=r['model'];truth_c=canonical_bfs(w.transitions,w.emissions,w.start)
    match=m is not None and canonical_bfs(m[0],m[1],0)==truth_c
    return {'ran':True,'n_min':r['n_min'],'unique':bool(r['unique']),'match':bool(match),'unknown':bool(r['unknown']),
            'ID':int(bool(r['unique']) and match),'wall_informational':perf_counter()-t}


def clause_a(cs):
    """Queries where S1 and S2 both answered exactly: (compared, mismatches, excluded)."""
    a,b=cs['S2'],cs['S1'];cmpd=mis=exc=0
    for i in range(STEPS):
        for j in range(len(a['unk'][i])):
            if a['unk'][i][j]==0 and b['unk'][i][j]==0:
                cmpd+=1;mis+=a['sup'][i][j]!=b['sup'][i][j]
            else:exc+=1
    return {'compared':cmpd,'mismatches':mis,'excluded':exc}


def run_case(seed,family,eps):
    w=W.world(seed,family);tr=W.trajectory(w,seed,eps);T=truth(w,tr);B=budgets(eps);arms={}
    for name in arms_for(eps):
        A,rec=run_arm(name,w,tr,T,B[name])
        try:
            if name=='S2' and eps==0:rec['identify']=identify(A,w,rec['steps_done'],B['ID'])
        finally:A.close()
        arms[name]=rec
    return {'schema':SCHEMA_CASE,'family':family,'seed':seed,'eps':eps,'n':w.n,'k':w.k,'arms':arms,'clause_a':clause_a(arms)}


def jobs_for(plan,block):
    R=plan['heldout_ranges']['targets']
    main=[('main',f,s,e) for f in FAM_ORDER for e in (0.02,0.0) for s in range(R[f][0],R[f][1]+1)]
    stress=[('stress',f,s,0.05) for f in FAM_ORDER[:3] for s in range(R[f][0],R[f][0]+3)]
    if block=='main':   # all 93 cases (main + stress), largest worlds first
        return sorted(main+stress,key=lambda j:(FAM_ORDER.index(j[1]),j[0]!='stress'))
    if block=='smoke':   # 4 families x eps (0, 0.02, 0.05 for scale) on smoke seeds; never a gate input
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
    smoke=block!='main'
    result={'schema':'brute.study.v23_0','plan':plan,'block':block,'smoke':smoke,'complete':complete,'job_keys':keys,'cases':cases,**extra}
    write_new(output/'RESULTS.json',result);write_new(output/'SCIENTIFIC.json',no_time(result))
    write_new(output/'SEAL.json',{'study':plan['study'],'block':block,'results_sha256':sha(output/'RESULTS.json'),
        'scientific_sha256':sha(output/'SCIENTIFIC.json'),'plan_sha256':sha(PLAN),'freeze_sha256':None if smoke else sha(FREEZE),
        'case_count':len(cases),'expected_case_count':len(keys),'complete':complete,'smoke':smoke,
        **({'missing_job_keys':extra['missing_job_keys']} if 'missing_job_keys' in extra else {})})


def seal_partial(output,block,limit=None,reason='study cap'):
    output=Path(output);plan=load(PLAN)
    for nm in ('RESULTS.json','SCIENTIFIC.json','SEAL.json'):check(not (output/nm).exists(),'refusing overwrite '+str(output/nm))
    jobs=jobs_for(plan,block)[:limit] if limit else jobs_for(plan,block);ck=Checkpoint(output/'CHECKPOINT.jsonl');keys=[key(j) for j in jobs]
    done=[k for k in keys if k in ck.done];missing=[k for k in keys if k not in ck.done]
    _write(output,plan,block,keys,[ck.done[k] for k in done],False,{'stop_reason':reason,'missing_job_keys':missing})
    return len(done),len(keys)


def run(output,workers,block,limit=None):
    output=Path(output);plan=load(PLAN)
    if block=='main':check_freeze()
    for nm in ('RESULTS.json','SCIENTIFIC.json','SEAL.json'):check(not (output/nm).exists(),'refusing overwrite '+str(output/nm))
    t0=time.perf_counter();jobs=jobs_for(plan,block);jobs=jobs[:limit] if limit else jobs
    output.mkdir(parents=True,exist_ok=True);cases=run_jobs(jobs,plan,workers,Checkpoint(output/'CHECKPOINT.jsonl'))
    _write(output,plan,block,[key(j) for j in jobs],cases,True,{'total_elapsed_informational':time.perf_counter()-t0})


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--block',choices=('main','smoke'),default='main')
    ap.add_argument('--output');ap.add_argument('--workers',type=int,default=8);ap.add_argument('--limit',type=int)
    ap.add_argument('--seal-partial',action='store_true')
    a=ap.parse_args();out=a.output or str(STUDY_DIR/a.block)
    if a.block!='main':check(not Path(out).resolve().is_relative_to(STUDY_DIR.resolve()),'smoke output must not be inside results/study-026')
    if a.seal_partial:print('sealed partial',seal_partial(out,a.block,a.limit))
    else:run(out,a.workers,a.block,a.limit);print('done')
