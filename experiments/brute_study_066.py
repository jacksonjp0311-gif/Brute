"""Study BRUTE-0630-SEQNOISE24-066 runner (experiments/BRUTE_PLAN_066.json; the pre-run deviation #206 fixes every definition
added here). New file, built from experiments/brute_study_065.py (frozen); study 058's truth_label and _verd, the frozen
brute.certify/20p, certify/20s, certify/32p and the new brute.certify/32s are imported and driven through the public interface only;
no frozen runner is rebound and no global is patched.
Arms (plan design.arms), C 50000, B 8000000, K 400, node cap 200000, conflict-only stop, 1800 s in-process case guard:
  C20  frozen certify/20p on clean readings, N 20, worlds_066 'scale20' (6 seeds);
  S30  frozen certify/20s at eps 0.30 (eps_bar 0.35, delta 0.001), N 20, scale20 (6 seeds): every observation is read one noisy
       reading at a time (worlds_066.Noise) until more() is False, then observe(action, readings);
  C24  frozen certify/32p on clean readings, N 24, worlds_066 'scale24' (4 seeds);
  S24  certify/32s at eps 0.30 (eps_bar 0.35, delta 0.001), N 24, scale24 (4 seeds);
  S30b S30 again on the first scale20 seed (determinism).
Noisy records carry the study-065 noise fields (reads_per_obs, thresholds, settle_at, reads_total, fixed_reads_total,
settled_bit_errors, settled_obs_errors, noise_draws, readings_sha256).
Runner (the plan's liveness fix): one forked process per job, at most WORKERS = 7 alive, polled every POLL_S; a finished job writes its
record (JSON) to a private temp file that the parent reads and checkpoints; a job alive at JOB_KILL_S = 600 s wall is SIGKILLed and
checkpointed as a KILL record (label 'KILL', stop 'KILL', undecided, no trace). A job that exits without a record is an error (the
run raises; never relaunched). Job order: C24, S24, C20, S30 (seeds ascending), then S30b.
Main run cap MAIN_CAP_S from launch (then sealed partial by the operator, never relaunched). Smoke (pre-freeze only, never gated;
outside results/study-066; B 2000000): 12660301 on every arm (scale20 and scale24 worlds of the smoke seed).
  PYTHONPATH=. python experiments/brute_study_066.py --block main
  PYTHONPATH=. python experiments/brute_study_066.py --block smoke --output /tmp/x
"""
from __future__ import annotations
import argparse,hashlib,json,time
from pathlib import Path
import multiprocessing as mp,os,signal,tempfile
from experiments import worlds_066 as W66
from experiments.brute_study_058 import truth_label,_verd
from brute.api import certify20b as C20B
from brute.api import certify20p as C20P
from brute.api import certify20s as C20S
from brute.api import certify20n as C20N
from brute.api import certify32p as C32P
from brute.api import certify32s as C32S
from brute.scalesearch4 import SOLVER4
from experiments.brute_common_066 import (PLAN,FREEZE,STUDY_DIR,load,sha,write_new,check_freeze,check,dumps,Checkpoint,C66,B66,K66,READ_BITS,
                                          NODE_CAP,DELTA,ARM_NOISE,ARM_KEY,ARM_BOUND,CONTROL,ALL_ARMS,NOISY,WORKERS,HARD_KILL_S,GUARD_CALL_S,
                                          JOB_KILL_S,POLL_S,STOP_RULE,MAIN_CAP_S,NOISE_RNG)
from scripts.check_seeds_066 import check_run_seeds,target_ranges,SMOKE

N20=6     # plan cases C20 / S30
N24=4     # plan cases C24 / S24
N_S30B=1  # plan cases.S30b = 1
SCHEMA='brute.study.v63_0';SCHEMA_CASE='brute.case.v63_0'
SMOKE_SEED=SMOKE[0]
SMOKE_B66=2000000   # smoke budget (tooling check only, never gated)
WALL_KEYS=('query_walls','chunk_walls')
NOISE_FIELDS=('eps','eps_bar','delta','reads_per_obs','thresholds','settle_at','reads_total','reads_max','fixed_reads_total',
              'settled_bit_errors','settled_obs_errors','noise_draws','readings_sha256','observations')
__all__=['truth_label','canon66','canon_inner','run_fresh','jobs_for','run','seal_partial','fixed_reads','kill_record','N20','N24','N_S30B','NOISE_FIELDS']


def canon66(a):
    """GDET66 canonical form of one arm record: no wall fields, no arm name, no api_current (raw read counts included)."""
    from brute.evaluation import no_time
    x=no_time(dict(a));x.pop('arm',None);x.pop('api_current',None);return dumps(x)


def canon_inner(a):
    """GEQ66 canonical form: the inner certify/20p or certify/32p record (labels, proposals, n_min, conflicts, queries, rounds, pins), i.e. canon66
    minus the api result dict and every noise field."""
    from brute.evaluation import no_time
    x=no_time(dict(a))
    for f in ('arm','api_current','api')+NOISE_FIELDS:x.pop(f,None)
    return dumps(x)


def fixed_reads(T,eps_bar,delta=DELTA,read_bits=READ_BITS):
    """Fixed-rule (certify/20n) reads for T observations (t = 1..T)."""
    return sum(C20N.reads_for(t,eps_bar,delta,read_bits) for t in range(1,T+1))


class _World:
    """Clean stepping plus the noisy reader for the certify/20s and certify/32s arms."""
    def __init__(self,w,seed,eps):self.w=w;self.q=w.start;self.steps=0;self.nz=W66.Noise(seed,eps);self.raw=[];self.bit_err=0;self.obs_err=0
    def clean(self):return W66.clean(self.w,self.q)
    def step(self,a):
        check(a in range(self.w.k),'bad action');self.q=self.w.transitions[self.q][a];self.steps+=1
    def readings(self,c):
        """Draw one noisy reading at a time until c.more(readings) is False (c None: the first observation, via a probe threshold)."""
        rs=[];cl=self.clean()
        while True:
            rs.append(self.nz.read(cl))
            if not c(rs):break
        self.raw.append([list(r) for r in rs]);return rs
    def tally(self,settled):
        e=sum(1 for x,y in zip(settled,self.clean()) if x!=y);self.bit_err+=e;self.obs_err+=e>0


def make(arm,first,k,B):
    kw=dict(max_chunks=None,K=K66,conflict_cap=C66,budget_conflicts=B,wall_guard_case_s=HARD_KILL_S,wall_guard_call_s=GUARD_CALL_S,
            solver=SOLVER4,hook=None,factory=C20B.counted16d)
    eps,eb=ARM_NOISE[arm];N=ARM_BOUND[arm]
    if arm=='C20':return C20P.Certifier20P(first,k,N,'a16d',read_bits=READ_BITS,node_cap=NODE_CAP,**kw)
    if arm=='C24':return C32P.Certifier32P(first,k,N,'a16d',read_bits=READ_BITS,node_cap=NODE_CAP,**kw)
    if arm in ('S30','S30b'):return C20S.Certifier20S(first,k,N,read_bits=READ_BITS,eps_bar=eb,delta=DELTA,node_cap=NODE_CAP,**kw)
    check(arm=='S24','unknown arm')
    return C32S.Certifier32S(first,k,N,read_bits=READ_BITS,eps_bar=eb,delta=DELTA,node_cap=NODE_CAP,**kw)


def run_fresh(seed,arm,budget=None):
    B=B66 if budget is None else budget;BOUND=ARM_BOUND[arm];FAM=ARM_KEY[arm]
    eps,eb=ARM_NOISE[arm];noisy=eb is not None;w=W66.world(seed,FAM);check(w.n==BOUND,'world size differs from the declared bound')
    acts=list(W66.actions(seed,0.0,w.k));sw=_World(w,seed,eps);T0=len(acts);t0=time.perf_counter()
    if noisy:
        m1=C20S.threshold(1,eb,DELTA,READ_BITS);first=sw.readings(lambda rs:C20S.settle(rs,m1,READ_BITS)[0] is None)
        c=make(arm,first,w.k,B);sw.tally(C20S.settle(first,m1,READ_BITS)[0])
        def obs(a):
            sw.step(a);rs=sw.readings(c.more);m=C20S.threshold(c.t+1,eb,DELTA,READ_BITS);sw.tally(C20S.settle(rs,m,READ_BITS)[0]);c.observe(a,rs)
    else:
        c=make(arm,sw.clean(),w.k,B)
        def obs(a):sw.step(a);c.observe(a,sw.clean())
    try:
        for a in acts:obs(a)
        while True:
            x=c.propose()
            if x is None:break
            for a in x:obs(a)
        R=c.record();res=c.result();cur=c.current()
    finally:c.close()
    f=R['final'];check(sw.steps==len(R['acts']),'step count');check(R['acts'][:T0]==acts,'prefix actions')
    rounds=[]
    for x in R['rounds']:
        rr={k:v for k,v in x.items() if k not in WALL_KEYS and k not in ('future','start')}
        rr['future']=_verd(x['future']);rr['start']=_verd(x['start'])
        rr['query_walls_informational']=list(x['query_walls']);rr['chunk_walls_informational']=[list(y) for y in x.get('chunk_walls',[])]
        rounds.append(rr)
    a={'arm':arm,'family':FAM,'read_bits':READ_BITS,'bound':BOUND,'true_size':w.n,'stop':R['stop'],'api_label':res['label'],
       'label':truth_label(R['stop'],f['model'],f['s1'],w,sw.q),'n_min':f['n_min'],'model':f['model'],'s1':f['s1'],
       'future':_verd(f['future']),'start':_verd(f['start']),'extra_acts':list(R['acts'][T0:]),'extra_masks':list(R['masks'][T0+1:]),
       'prefix_masks':list(R['masks'][:T0+1]),'used':R['used'],'n_rounds':len(R['rounds']),'rounds':rounds,
       'conflicts_spent':R['conflicts_spent'],'conflict_cap':R['conflict_cap'],'budget_conflicts':R['budget_conflicts'],
       'wall_guard':R['wall_guard'],'guard_events':list(R['guard_events']),'max_chunks':R['max_chunks'],'chunks_total':R['chunks_total'],
       'sizes':list(R.get('sizes') or []),'api':res,'api_current':cur,'K':K66,'distinct_codes':len(set(w.emissions)),'node_cap':NODE_CAP,
       'clique_size':res.get('clique_size'),'final_clique':list(R.get('final_clique') or []),'repins':[list(x) for x in R.get('repins') or []],
       'guards_closed':R.get('guards_closed'),'stop_rule':STOP_RULE,'hard_kill_s':HARD_KILL_S,'case_wall_informational':time.perf_counter()-t0}
    T=len(R['acts'])+1
    if noisy:
        check(len(R['reads_per_obs'])==T==len(sw.raw),'observation count')
        a.update(eps=eps,eps_bar=eb,delta=DELTA,observations=T,reads_per_obs=list(R['reads_per_obs']),thresholds=list(R['thresholds']),
                 settle_at=[list(x) for x in R['settle_at']],reads_total=sum(R['reads_per_obs']),reads_max=max(R['reads_per_obs']),
                 fixed_reads_total=fixed_reads(T,eb),settled_bit_errors=sw.bit_err,settled_obs_errors=sw.obs_err,noise_draws=sw.nz.draws,
                 readings_sha256=hashlib.sha256(json.dumps(sw.raw,separators=(',',':')).encode()).hexdigest())
        exp=(C20S.API,C20P.API) if arm!='S24' else (C32S.API,C32P.API)
        check(res['api']==exp[0] and res['inner_api']==exp[1],'api not applied')
    else:check(res['api']==(C20P.API if arm=='C20' else C32P.API),'api not applied')
    check(a['budget_conflicts']==B and a['conflict_cap']==C66 and a['max_chunks'] is None,'066 caps not applied')
    check(res['family_bound']==BOUND,'declared bound not applied')
    check(a['used']<=K66 and a['used']==len(a['extra_acts']),'K accounting')
    return {'schema':SCHEMA_CASE,'key':FAM,'seed':seed,'eps':0.0,'n':w.n,'k':w.k,'N':BOUND,'group':arm,'arms':{arm:a}}


def kill_record(job,wall):
    """The KILL record of a job killed at JOB_KILL_S (undecided, no trace; host-dependent, can only remove decisions)."""
    b,k,s,g=job;w=W66.world(s,k)
    a={'arm':g,'family':k,'read_bits':READ_BITS,'bound':ARM_BOUND[g],'true_size':w.n,'stop':'KILL','api_label':None,'label':'KILL',
       'n_min':None,'model':None,'s1':None,'used':None,'conflicts_spent':None,'stop_rule':STOP_RULE,'job_kill_s':JOB_KILL_S,
       'kill_wall_informational':wall}
    if g in NOISY:a.update(eps=ARM_NOISE[g][0],eps_bar=ARM_NOISE[g][1],delta=DELTA)
    return {'schema':SCHEMA_CASE,'key':k,'seed':s,'eps':0.0,'n':w.n,'k':w.k,'N':ARM_BOUND[g],'group':g,'arms':{g:a},'block':b,
            'killed':True,'job_wall_informational':wall}


def seeds_of(plan,k):
    R=target_ranges(plan);return list(range(R[k][0],R[k][1]+1))


def declared(plan,arm):
    s20=seeds_of(plan,'scale20')[:N20];s24=seeds_of(plan,'scale24')[:N24]
    return {'C20':s20,'S30':s20,'C24':s24,'S24':s24,'S30b':s20[:N_S30B]}[arm]


def _order(d,block):
    return [(block,ARM_KEY[g],x,g) for g in ALL_ARMS for x in d[g]]


def jobs_for(plan,block):
    if block=='main':return _order({a:declared(plan,a) for a in ALL_ARMS},'main')
    if block=='smoke':return _order({a:[SMOKE_SEED] for a in ALL_ARMS},'smoke')
    raise ValueError(block)


def key(job):return ':'.join(str(x) for x in job)
def case_key(job):return f'{job[0]}:{job[1]}:{job[2]}'


def check_job(job,plan):
    b,k,s,g=job;check(g in ALL_ARMS and k==ARM_KEY[g],'arm/key')
    if b=='main':check_run_seeds('target',[s],plan,key=k);check(s in declared(plan,g),'case not in the declared list')
    elif b=='smoke':check_run_seeds('smoke',[s],plan)
    else:raise ValueError(b)


def run_job(job,plan):
    check_job(job,plan);t0=time.perf_counter();c=run_fresh(job[2],job[3],None if job[0]=='main' else SMOKE_B66)
    c['block']=job[0];c['killed']=False;c['job_wall_informational']=time.perf_counter()-t0;return key(job),c


def _child(job,plan,path):
    """Forked child: run one job, write its record atomically, exit 0 (any exception: exit 3 with no record)."""
    try:
        k_,c=run_job(job,plan);tmp=path+'.part'
        with open(tmp,'w') as fh:json.dump(c,fh)
        os.replace(tmp,path);os._exit(0)
    except BaseException as e:
        try:
            with open(path+'.err','w') as fh:fh.write(repr(e))
        except Exception:pass
        os._exit(3)


def _lab(c):
    return ' '.join(f'{a}={v["label"]}/{v["stop"]} n={v["n_min"]} cf={v["conflicts_spent"]} used={v["used"]} '
                    f'reads={v.get("reads_total")} fixed={v.get("fixed_reads_total")} err={v.get("settled_bit_errors")}' for a,v in c['arms'].items())


def run_jobs(jobs,plan,ckpt,log=print,kill_s=None):
    """Process-per-job scheduler with a hard SIGKILL at kill_s (JOB_KILL_S) wall per job."""
    kill_s=JOB_KILL_S if kill_s is None else kill_s
    for j in jobs:check_job(j,plan)
    todo=[j for j in jobs if key(j) not in ckpt.done];tmpd=tempfile.mkdtemp(prefix='brute066_')
    log(f'{len(jobs)-len(todo)} cached, {len(todo)} to run on {WORKERS} processes, kill at {kill_s:.0f}s',flush=True)
    ctx=mp.get_context('fork');alive={};n=0;errors=[];q=list(todo)
    while q or alive:
        while q and len(alive)<WORKERS:
            j=q.pop(0);path=os.path.join(tmpd,f'job{len(todo)-len(q):03d}.json')
            p=ctx.Process(target=_child,args=(j,plan,path),daemon=False);p.start();alive[key(j)]=(j,p,path,time.perf_counter())
        time.sleep(POLL_S)
        for k_,(j,p,path,t0) in list(alive.items()):
            wall=time.perf_counter()-t0
            if p.exitcode is None and wall<kill_s:continue
            if p.exitcode is None:
                os.kill(p.pid,signal.SIGKILL);p.join();c=kill_record(j,wall)
            else:
                p.join()
                if p.exitcode!=0 or not os.path.exists(path):
                    err=open(path+'.err').read() if os.path.exists(path+'.err') else f'exit {p.exitcode}'
                    errors.append([k_,err]);del alive[k_];log(f'ERROR {k_} {err}',flush=True);continue
                with open(path) as fh:c=json.load(fh)
            ckpt.add(k_,c);del alive[k_];n+=1
            log(f'done {n}/{len(todo)} {k_} {c["job_wall_informational"]:.1f}s {"KILL" if c.get("killed") else ""} {_lab(c)}',flush=True)
    check(not errors,f'jobs exited without a record: {errors}')


def merge(jobs,done):
    cases={};order=[]
    for j in jobs:
        if key(j) not in done:continue
        g=done[key(j)];ck=case_key(j)
        if ck not in cases:
            cases[ck]={x:g[x] for x in ('schema','key','seed','n','k','block','eps')};cases[ck]['arms']={}
            cases[ck]['group_walls_informational']={};cases[ck]['killed_arms']=[];order.append(ck)
        check(all(cases[ck][x]==g[x] for x in ('seed','n','k')),'group records disagree: '+ck)
        cases[ck]['arms'].update(g['arms']);cases[ck]['group_walls_informational'][j[3]]=g['job_wall_informational']
        if g.get('killed'):cases[ck]['killed_arms'].append(j[3])
    for c in cases.values():c['arms']={a:c['arms'][a] for a in ALL_ARMS if a in c['arms']}
    order.sort(key=lambda ck:(cases[ck]['key'],cases[ck]['seed']));return [cases[ck] for ck in order]


def _write(output,plan,block,keys,cases,complete,extra):
    from brute.evaluation import no_time
    smoke=block!='main'
    result={'schema':SCHEMA,'plan':plan,'block':block,'smoke':smoke,'complete':complete,'job_keys':keys,'cases':cases,
            'caps':[C66,B66,K66],'read_bits':READ_BITS,'node_cap':NODE_CAP,'arm_bound':ARM_BOUND,'arm_key':ARM_KEY,'delta':DELTA,
            'arms':list(ALL_ARMS),'arm_noise':ARM_NOISE,'noise_rng':NOISE_RNG,'workers':WORKERS,
            'stop':{'hard_kill_s':HARD_KILL_S,'job_kill_s':JOB_KILL_S,'stop_rule':STOP_RULE,'main_cap_s':MAIN_CAP_S},
            'n20':N20,'n24':N24,'n_s30b':N_S30B,'killed_job_keys':sorted(k for c in cases for k in
              [f"{c['block']}:{c['key']}:{c['seed']}:{a}" for a in c['killed_arms']]),**extra}
    write_new(output/'RESULTS.json',result);write_new(output/'SCIENTIFIC.json',no_time(result))
    write_new(output/'SEAL.json',{'study':plan['study'],'block':block,'results_sha256':sha(output/'RESULTS.json'),
        'scientific_sha256':sha(output/'SCIENTIFIC.json'),'plan_sha256':sha(PLAN),'freeze_sha256':None if smoke else sha(FREEZE),
        'case_count':len(cases),'job_count':len(keys),'complete':complete,'smoke':smoke,
        'checkpoint_sha256':sha(output/'CHECKPOINT.jsonl') if (output/'CHECKPOINT.jsonl').exists() else None,
        **({'missing_job_keys':extra['missing_job_keys']} if 'missing_job_keys' in extra else {})})


def seal_partial(output,block,reason='study cap'):
    output=Path(output);plan=load(PLAN)
    for nm in ('RESULTS.json','SCIENTIFIC.json','SEAL.json'):check(not (output/nm).exists(),'refusing overwrite '+str(output/nm))
    jobs=jobs_for(plan,block);ck=Checkpoint(output/'CHECKPOINT.jsonl');keys=[key(j) for j in jobs];done=dict(ck.done)
    missing=[k for k in keys if k not in done]
    _write(output,plan,block,keys,merge(jobs,done),False,{'stop_reason':reason,'missing_job_keys':missing})
    return len(keys)-len(missing),len(keys)


def run(output,block):
    output=Path(output);plan=load(PLAN)
    if block=='main':
        fz=check_freeze();check(fz.get('n20')==N20 and fz.get('n24')==N24 and fz.get('n_s30b')==N_S30B and (fz.get('stop') or {}).get('job_kill_s')==JOB_KILL_S,'case counts or job kill differ from the freeze')
    for nm in ('RESULTS.json','SCIENTIFIC.json','SEAL.json'):check(not (output/nm).exists(),'refusing overwrite '+str(output/nm))
    t0=time.perf_counter();jobs=jobs_for(plan,block)
    output.mkdir(parents=True,exist_ok=True);ck=Checkpoint(output/'CHECKPOINT.jsonl')
    if block=='main':check(not ck.done,'main checkpoint not empty: never resume (standing rule)')
    run_jobs(jobs,plan,ck)
    _write(output,plan,block,[key(j) for j in jobs],merge(jobs,ck.done),True,{'total_elapsed_informational':time.perf_counter()-t0})


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--block',choices=('main','smoke'),default='main')
    ap.add_argument('--output');ap.add_argument('--seal-partial',action='store_true');ap.add_argument('--reason',default='study cap')
    a=ap.parse_args();out=a.output or str(STUDY_DIR/a.block)
    if a.block!='main':check(not Path(out).resolve().is_relative_to(STUDY_DIR.resolve()),'smoke output must not be inside results/study-066')
    if a.seal_partial:print('sealed partial',seal_partial(out,a.block,a.reason))
    else:run(out,a.block);print('done')
