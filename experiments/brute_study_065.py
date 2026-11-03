"""Study BRUTE-0620-SEQNOISE2B20-065 runner (experiments/BRUTE_PLAN_065.json; the pre-run deviation #204 fixes every definition
added here). New file, built from experiments/brute_study_064.py (frozen); study 058's truth_label and _verd, the frozen
brute.certify/20p and the new brute.certify/20s are imported and driven through the public interface only; no frozen runner is
rebound and no global is patched.
Arms (plan design.arms), all on worlds_065 (2-bit 20-state 'scale20'), declared N 20, C 50000, B 8000000, K 400, node cap 200000,
conflict-only stop, 1800 s case kill:
  C20  frozen certify/20p on clean readings (N_SEEDS seeds);
  S10, S20, S30  certify/20s at eps 0.10 / 0.20 / 0.30 (eps_bar 0.15 / 0.25 / 0.35, delta 0.001): every observation is read one
       noisy reading at a time (worlds_065.Noise) until certify/20s.more() is False, then observe(action, readings);
  S30b S30 again on the first N_S30B seeds (determinism).
Every noisy record carries: reads_per_obs, thresholds, settle_at (from certify/20s.record()), reads_total, the fixed-rule
counterfactual fixed_reads_total = sum over its observations t of certify20n.reads_for(t, eps_bar, 0.001, 2) (Exact for the trace
taken), settled_bit_errors / settled_obs_errors (settled reading vs the clean reading of the true state), noise_draws and
readings_sha256 (sha256 of the JSON list of every raw reading in order).
Job order: C20 ascending, S30 ascending, S20 ascending, S10 ascending, S30b. One 6-worker pool, max_tasks_per_child=1.
Cut rule (plan runtime_projection; applied only before the freeze from the smoke projection): N_S20 6 -> 3, then N_S10 6 -> 3.
Main run cap MAIN_CAP_S from launch (then sealed partial by the operator, never relaunched). Smoke (pre-freeze only, never gated;
outside results/study-065; B 2000000): 12650301 on every arm; 12650302 / 12650303 only for api_checks.
  PYTHONPATH=. python experiments/brute_study_065.py --block main
  PYTHONPATH=. python experiments/brute_study_065.py --block smoke --output /tmp/x
"""
from __future__ import annotations
import argparse,hashlib,json,time
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor,as_completed
from experiments import worlds_065 as W65
from experiments.brute_study_058 import truth_label,_verd
from brute.api import certify20b as C20B
from brute.api import certify20p as C20P
from brute.api import certify20s as C20S
from brute.api import certify20n as C20N
from brute.scalesearch4 import SOLVER4
from experiments.brute_common_065 import (PLAN,FREEZE,STUDY_DIR,load,sha,write_new,check_freeze,check,dumps,Checkpoint,C65,B65,K65,READ_BITS,
                                          NODE_CAP,BOUND,DELTA,ARM_NOISE,ALL_ARMS,NOISY,KEY,WORKERS,HARD_KILL_S,GUARD_CALL_S,STOP_RULE,MAIN_CAP_S,NOISE_RNG)
from scripts.check_seeds_065 import check_run_seeds,target_ranges,SMOKE

N_SEEDS=6  # plan cases C20 / S30
N_S20=6    # plan cases.S20 = 6 (cut rule: 3)
N_S10=6    # plan cases.S10 = 6 (cut rule: 3)
N_S30B=1   # plan cases.S30b = 1
SCHEMA='brute.study.v62_0';SCHEMA_CASE='brute.case.v62_0'
SMOKE_SEED=SMOKE[0]
SMOKE_B65=2000000   # smoke budget (tooling check only, never gated)
WALL_KEYS=('query_walls','chunk_walls')
NOISE_FIELDS=('eps','eps_bar','delta','reads_per_obs','thresholds','settle_at','reads_total','reads_max','fixed_reads_total',
              'settled_bit_errors','settled_obs_errors','noise_draws','readings_sha256','observations')
__all__=['truth_label','canon65','canon_inner','run_fresh','jobs_for','run','seal_partial','fixed_reads','N_SEEDS','N_S20','N_S10','N_S30B','NOISE_FIELDS']


def canon65(a):
    """GDET65 canonical form of one arm record: no wall fields, no arm name, no api_current (raw read counts included)."""
    from brute.evaluation import no_time
    x=no_time(dict(a));x.pop('arm',None);x.pop('api_current',None);return dumps(x)


def canon_inner(a):
    """GEQ65 canonical form: the inner certify/20p record (labels, proposals, n_min, conflicts, queries, rounds, pins), i.e. canon65
    minus the api result dict and every noise field."""
    from brute.evaluation import no_time
    x=no_time(dict(a))
    for f in ('arm','api_current','api')+NOISE_FIELDS:x.pop(f,None)
    return dumps(x)


def fixed_reads(T,eps_bar,delta=DELTA,read_bits=READ_BITS):
    """Fixed-rule (certify/20n) reads for T observations (t = 1..T)."""
    return sum(C20N.reads_for(t,eps_bar,delta,read_bits) for t in range(1,T+1))


class _World:
    """Clean stepping plus the noisy reader for the certify/20s arms."""
    def __init__(self,w,seed,eps):self.w=w;self.q=w.start;self.steps=0;self.nz=W65.Noise(seed,eps);self.raw=[];self.bit_err=0;self.obs_err=0
    def clean(self):return W65.clean(self.w,self.q)
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
    kw=dict(max_chunks=None,K=K65,conflict_cap=C65,budget_conflicts=B,wall_guard_case_s=HARD_KILL_S,wall_guard_call_s=GUARD_CALL_S,
            solver=SOLVER4,hook=None,factory=C20B.counted16d)
    eps,eb=ARM_NOISE[arm]
    if eb is None:return C20P.Certifier20P(first,k,BOUND,'a16d',read_bits=READ_BITS,node_cap=NODE_CAP,**kw)
    return C20S.Certifier20S(first,k,BOUND,read_bits=READ_BITS,eps_bar=eb,delta=DELTA,node_cap=NODE_CAP,**kw)


def run_fresh(seed,arm,budget=None):
    B=B65 if budget is None else budget
    eps,eb=ARM_NOISE[arm];noisy=eb is not None;w=W65.world(seed);check(w.n==BOUND,'world size differs from the declared bound')
    acts=list(W65.actions(seed,0.0,w.k));sw=_World(w,seed,eps);T0=len(acts);t0=time.perf_counter()
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
    a={'arm':arm,'family':W65.FAMILY,'read_bits':READ_BITS,'bound':BOUND,'true_size':w.n,'stop':R['stop'],'api_label':res['label'],
       'label':truth_label(R['stop'],f['model'],f['s1'],w,sw.q),'n_min':f['n_min'],'model':f['model'],'s1':f['s1'],
       'future':_verd(f['future']),'start':_verd(f['start']),'extra_acts':list(R['acts'][T0:]),'extra_masks':list(R['masks'][T0+1:]),
       'prefix_masks':list(R['masks'][:T0+1]),'used':R['used'],'n_rounds':len(R['rounds']),'rounds':rounds,
       'conflicts_spent':R['conflicts_spent'],'conflict_cap':R['conflict_cap'],'budget_conflicts':R['budget_conflicts'],
       'wall_guard':R['wall_guard'],'guard_events':list(R['guard_events']),'max_chunks':R['max_chunks'],'chunks_total':R['chunks_total'],
       'sizes':list(R.get('sizes') or []),'api':res,'api_current':cur,'K':K65,'distinct_codes':len(set(w.emissions)),'node_cap':NODE_CAP,
       'clique_size':res.get('clique_size'),'final_clique':list(R.get('final_clique') or []),'repins':[list(x) for x in R.get('repins') or []],
       'guards_closed':R.get('guards_closed'),'stop_rule':STOP_RULE,'hard_kill_s':HARD_KILL_S,'case_wall_informational':time.perf_counter()-t0}
    T=len(R['acts'])+1
    if noisy:
        check(len(R['reads_per_obs'])==T==len(sw.raw),'observation count')
        a.update(eps=eps,eps_bar=eb,delta=DELTA,observations=T,reads_per_obs=list(R['reads_per_obs']),thresholds=list(R['thresholds']),
                 settle_at=[list(x) for x in R['settle_at']],reads_total=sum(R['reads_per_obs']),reads_max=max(R['reads_per_obs']),
                 fixed_reads_total=fixed_reads(T,eb),settled_bit_errors=sw.bit_err,settled_obs_errors=sw.obs_err,noise_draws=sw.nz.draws,
                 readings_sha256=hashlib.sha256(json.dumps(sw.raw,separators=(',',':')).encode()).hexdigest())
        check(res['api']==C20S.API and res['inner_api']==C20P.API,'api not applied')
    else:check(res['api']==C20P.API,'api not applied')
    check(a['budget_conflicts']==B and a['conflict_cap']==C65 and a['max_chunks'] is None,'065 caps not applied')
    check(res['family_bound']==BOUND,'declared bound not applied')
    check(a['used']<=K65 and a['used']==len(a['extra_acts']),'K accounting')
    return {'schema':SCHEMA_CASE,'key':KEY,'seed':seed,'eps':0.0,'n':w.n,'k':w.k,'N':BOUND,'group':arm,'arms':{arm:a}}


def seeds_of(plan):
    R=target_ranges(plan);return list(range(R[KEY][0],R[KEY][1]+1))


def declared(plan,arm):
    s=seeds_of(plan)[:N_SEEDS]
    return {'C20':s,'S30':s,'S20':s[:N_S20],'S10':s[:N_S10],'S30b':s[:N_S30B]}[arm]


def _order(d,block):
    return ([(block,KEY,x,'C20') for x in d['C20']]+[(block,KEY,x,'S30') for x in d['S30']]+[(block,KEY,x,'S20') for x in d['S20']]+
            [(block,KEY,x,'S10') for x in d['S10']]+[(block,KEY,x,'S30b') for x in d['S30b']])


def jobs_for(plan,block):
    if block=='main':return _order({a:declared(plan,a) for a in ALL_ARMS},'main')
    if block=='smoke':return _order({a:[SMOKE_SEED] for a in ALL_ARMS},'smoke')
    raise ValueError(block)


def key(job):return ':'.join(str(x) for x in job)
def case_key(job):return f'{job[0]}:{job[1]}:{job[2]}'


def check_job(job,plan):
    b,k,s,g=job;check(g in ALL_ARMS and k==KEY,'arm/key')
    if b=='main':check_run_seeds('target',[s],plan,key=k);check(s in declared(plan,g),'case not in the declared (cut) list')
    elif b=='smoke':check_run_seeds('smoke',[s],plan)
    else:raise ValueError(b)


def run_job(job,plan):
    check_job(job,plan);t0=time.perf_counter();c=run_fresh(job[2],job[3],None if job[0]=='main' else SMOKE_B65)
    c['block']=job[0];c['job_wall_informational']=time.perf_counter()-t0;return key(job),c


def _job(x):return run_job(*x)


def _lab(c):
    return ' '.join(f'{a}={v["label"]}/{v["stop"]} n={v["n_min"]} g={v["wall_guard"]} cf={v["conflicts_spent"]} used={v["used"]} nr={v["n_rounds"]} '
                    f'reads={v.get("reads_total")} fixed={v.get("fixed_reads_total")} err={v.get("settled_bit_errors")}' for a,v in c['arms'].items())


def run_jobs(jobs,plan,ckpt,log=print):
    for j in jobs:check_job(j,plan)
    todo=[j for j in jobs if key(j) not in ckpt.done]
    log(f'{len(jobs)-len(todo)} cached, {len(todo)} to run on {WORKERS} workers',flush=True)
    with ProcessPoolExecutor(WORKERS,max_tasks_per_child=1) as ex:
        futs=[ex.submit(_job,(j,plan)) for j in todo]
        for n,fu in enumerate(as_completed(futs)):
            k_,c=fu.result();ckpt.add(k_,c)
            log(f'done {n+1}/{len(todo)} {k_} {c["job_wall_informational"]:.1f}s {_lab(c)}',flush=True)


def merge(jobs,done):
    cases={};order=[]
    for j in jobs:
        if key(j) not in done:continue
        g=done[key(j)];ck=case_key(j)
        if ck not in cases:
            cases[ck]={x:g[x] for x in ('schema','key','seed','n','k','N','block','eps')};cases[ck]['arms']={}
            cases[ck]['group_walls_informational']={};order.append(ck)
        check(all(cases[ck][x]==g[x] for x in ('seed','n','k','N')),'group records disagree: '+ck)
        cases[ck]['arms'].update(g['arms']);cases[ck]['group_walls_informational'][j[3]]=g['job_wall_informational']
    for c in cases.values():c['arms']={a:c['arms'][a] for a in ALL_ARMS if a in c['arms']}
    order.sort(key=lambda ck:(cases[ck]['key'],cases[ck]['seed']));return [cases[ck] for ck in order]


def _write(output,plan,block,keys,cases,complete,extra):
    from brute.evaluation import no_time
    smoke=block!='main'
    result={'schema':SCHEMA,'plan':plan,'block':block,'smoke':smoke,'complete':complete,'job_keys':keys,'cases':cases,
            'caps':[C65,B65,K65],'read_bits':READ_BITS,'node_cap':NODE_CAP,'bound':BOUND,'delta':DELTA,'arms':list(ALL_ARMS),'arm_noise':ARM_NOISE,
            'noise_rng':NOISE_RNG,'workers':WORKERS,'stop':{'hard_kill_s':HARD_KILL_S,'stop_rule':STOP_RULE,'main_cap_s':MAIN_CAP_S},
            'n_seeds':N_SEEDS,'n_s20':N_S20,'n_s10':N_S10,'n_s30b':N_S30B,**extra}
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
        fz=check_freeze();check(fz.get('n_seeds')==N_SEEDS and fz.get('n_s20')==N_S20 and fz.get('n_s10')==N_S10 and fz.get('n_s30b')==N_S30B,'cut variable differs from the freeze')
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
    if a.block!='main':check(not Path(out).resolve().is_relative_to(STUDY_DIR.resolve()),'smoke output must not be inside results/study-065')
    if a.seal_partial:print('sealed partial',seal_partial(out,a.block,a.reason))
    else:run(out,a.block);print('done')
