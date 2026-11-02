"""Study BRUTE-0550-READBITS-058 runner (experiments/BRUTE_PLAN_058.json; pre-run deviation #190 fixes every definition added
here). New file. certify/20b is driven through its public interface only; no frozen runner is rebound.
Arms (plan design.arms), all certify/20b at bound 20, C 50000, B 2000000, K 400, conflict-only stop, max_chunks None:
  B2    scale20 (original 2-bit emissions), read_bits 2;   B2R  scale20r2 (random 2-bit emissions), read_bits 2;
  B3    scale20r3, read_bits 3;   B4  scale20r4, read_bits 4;   B4_b  B4 again (second pass, reversed seed order; determinism).
Per case: the passive prefix (worlds_026 actions, eps 0, the plan's horizon) is observed, then propose()/observe() until stop,
the readings coming from stepping the true world. truth_label: ID correct iff behaviour-equal to the truth from the start state;
IDF correct iff behaviour-equal from s1 to the truth from the true current state; K_spent / AMB -> AMB; unknown -> IDU.
Job order: per seed B4, B3, B2R, B2; then B4_b in reversed seed order. One 8-worker pool, max_tasks_per_child=1.
Cut rule (plan runtime_estimate, applied at the pre-freeze projection only, fixed in #190 before the freeze): N58 12 -> 8 if the
projected run exceeds 3300 s.
Smoke (pre-freeze only, never gated; outside results/study-058): 12550001-02, all five arms; 12550003-06 declared unused except
12550003 by the no-network check in api_checks_058.
  PYTHONPATH=. python experiments/brute_study_058.py --block main
  PYTHONPATH=. python experiments/brute_study_058.py --block smoke --output /tmp/x
"""
from __future__ import annotations
import argparse,time
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor,as_completed
from experiments import worlds_058 as W58
from brute.api import certify20b as C20B
from brute.scalesearch4 import SOLVER4
from experiments.brute_common import dumps
from experiments.brute_common_058 import (PLAN,FREEZE,STUDY_DIR,load,sha,write_new,check_freeze,check,Checkpoint,C58,B58,K58,BOUND,KEY,
                                          ARM_FAMILY,ALL_ARMS,WORKERS,HARD_KILL_S,GUARD_CALL_S,STOP_RULE,EMISSION_RNG)
from scripts.check_seeds_058 import check_run_seeds,target_ranges,SMOKE

N58=12      # declared cut rule: 12 -> 8 only if the projected run > 3300 s; fixed in #190 before the freeze
SCHEMA='brute.study.v55_0';SCHEMA_CASE='brute.case.v55_0'
SMOKE_FRESH=(SMOKE[0],SMOKE[0]+1)
WALL_KEYS=('query_walls','chunk_walls')


def beq(d1,e1,s1,d2,e2,s2):
    """Behaviour equality of two Moore machines from (s1, s2) (product walk)."""
    k=len(d1[0]);seen={(s1,s2)};st=[(s1,s2)]
    while st:
        p,q=st.pop()
        if e1[p]!=e2[q]:return False
        for a in range(k):
            x=(d1[p][a],d2[q][a])
            if x not in seen:seen.add(x);st.append(x)
    return True


def truth_label(stop,model,s1,w,q_now):
    if stop=='unknown':return 'IDU'
    if stop in ('AMB','K_spent'):return 'AMB'
    if model is None:return 'WRONG'
    d,e=model
    if stop=='ID':return 'ID' if beq(d,e,0,w.transitions,w.emissions,w.start) else 'WRONG'
    if stop=='IDF':return 'IDF' if beq(d,e,s1,w.transitions,w.emissions,q_now) else 'WRONG'
    return 'WRONG'


def _verd(S):return None if S is None else {'found':S['found'],'unknown':S['unknown'],'n':S['n'],'verdicts':S['verdicts'],'L':S['L']}


class _Step:
    def __init__(self,w):self.w=w;self.q=w.start;self.steps=0
    def read(self):return W58.bits(self.w.emissions[self.q],self.w.s)
    def step(self,a):
        check(a in range(self.w.k),'bad action');self.q=self.w.transitions[self.q][a];self.steps+=1;return self.read()


def run_fresh(seed,arm):
    fam=ARM_FAMILY[arm];w=W58.world(seed,fam);N=W58.SIZES[fam];check(w.n==N==BOUND,'world size differs from the declared bound')
    acts=list(W58.actions(seed,0.0,w.k));sw=_Step(w);rd=[sw.read()]+[sw.step(a) for a in acts];T0=len(acts)
    kw=dict(max_chunks=None,K=K58,conflict_cap=C58,budget_conflicts=B58,wall_guard_case_s=HARD_KILL_S,
            wall_guard_call_s=GUARD_CALL_S,solver=SOLVER4,hook=None,factory=C20B.counted16d)
    t0=time.perf_counter();c=C20B.Certifier20B(rd[0],w.k,N,'a16d',read_bits=w.s,**kw)
    try:
        for a,o in zip(acts,rd[1:]):c.observe(a,o)
        while True:
            x=c.propose()
            if x is None:break
            for a in x:c.observe(a,sw.step(a))
        R=c.record();res=c.result();cur=c.current()
    finally:c.close()
    f=R['final'];check(sw.steps==len(R['acts']),'step count');check(R['acts'][:T0]==acts,'prefix actions')
    rounds=[]
    for x in R['rounds']:
        rr={k:v for k,v in x.items() if k not in WALL_KEYS and k not in ('future','start')}
        rr['future']=_verd(x['future']);rr['start']=_verd(x['start'])
        rr['query_walls_informational']=list(x['query_walls']);rr['chunk_walls_informational']=[list(y) for y in x.get('chunk_walls',[])]
        rounds.append(rr)
    a={'arm':arm,'family':fam,'read_bits':w.s,'stop':R['stop'],'api_label':res['label'],
       'label':truth_label(R['stop'],f['model'],f['s1'],w,sw.q),'n_min':f['n_min'],'model':f['model'],'s1':f['s1'],
       'future':_verd(f['future']),'start':_verd(f['start']),'extra_acts':list(R['acts'][T0:]),'extra_masks':list(R['masks'][T0+1:]),
       'prefix_masks':list(R['masks'][:T0+1]),'used':R['used'],'n_rounds':len(R['rounds']),'rounds':rounds,
       'conflicts_spent':R['conflicts_spent'],'conflict_cap':R['conflict_cap'],'budget_conflicts':R['budget_conflicts'],
       'wall_guard':R['wall_guard'],'guard_events':list(R['guard_events']),'max_chunks':R['max_chunks'],'chunks_total':R['chunks_total'],
       'sizes':list(R.get('sizes') or []),'api':res,'api_current':cur,'K':K58,'distinct_codes':len(set(w.emissions)),
       'stop_rule':STOP_RULE,'hard_kill_s':HARD_KILL_S,'case_wall_informational':time.perf_counter()-t0}
    check(a['budget_conflicts']==B58 and a['conflict_cap']==C58 and a['max_chunks'] is None and res['api']==C20B.API,'058 caps not applied')
    return {'schema':SCHEMA_CASE,'key':KEY,'seed':seed,'eps':0.0,'n':w.n,'k':w.k,'N':N,'group':arm,'arms':{arm:a}}


def canon58(a):
    """GDET58 canonical form of one arm record: no wall fields, no arm name."""
    from brute.evaluation import no_time
    x=no_time(dict(a));x.pop('arm',None);x['api']={k:v for k,v in x['api'].items()};x.pop('api_current',None)
    return dumps(x)


def seeds_of(plan):
    R=target_ranges(plan);return list(range(R[KEY][0],R[KEY][1]+1))


def declared_list(plan):return seeds_of(plan)[:N58]


def _order(seeds,block):
    return [(block,KEY,s,g) for s in seeds for g in ('B4','B3','B2R','B2')]+[(block,KEY,s,'B4_b') for s in reversed(seeds)]


def jobs_for(plan,block):
    if block=='main':return _order(declared_list(plan),'main')
    if block=='smoke':return _order(list(SMOKE_FRESH),'smoke')
    raise ValueError(block)


def key(job):return ':'.join(str(x) for x in job)
def case_key(job):return f'{job[0]}:{job[1]}:{job[2]}'


def check_job(job,plan):
    b,k,s,g=job;check(g in ALL_ARMS and k==KEY,'arm/key')
    if b=='main':check_run_seeds('target',[s],plan,key=k);check(s in declared_list(plan),'case not in the declared (cut) list')
    elif b=='smoke':check_run_seeds('smoke',[s],plan)
    else:raise ValueError(b)


def run_job(job,plan):
    check_job(job,plan);t0=time.perf_counter();c=run_fresh(job[2],job[3])
    c['block']=job[0];c['job_wall_informational']=time.perf_counter()-t0;return key(job),c


def _job(x):return run_job(*x)


def _lab(c):
    return ' '.join(f'{a}={v["label"]}/{v["stop"]} n={v["n_min"]} g={v["wall_guard"]} cf={v["conflicts_spent"]} used={v["used"]} nr={v["n_rounds"]}' for a,v in c['arms'].items())


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
    order.sort(key=lambda ck:cases[ck]['seed']);return [cases[ck] for ck in order]


def _write(output,plan,block,keys,cases,complete,extra):
    from brute.evaluation import no_time
    smoke=block!='main'
    result={'schema':SCHEMA,'plan':plan,'block':block,'smoke':smoke,'complete':complete,'job_keys':keys,'cases':cases,
            'caps':[C58,B58,K58],'bound':BOUND,'arms':list(ALL_ARMS),'arm_family':ARM_FAMILY,'workers':WORKERS,
            'stop':{'hard_kill_s':HARD_KILL_S,'stop_rule':STOP_RULE},'emission_rng':EMISSION_RNG,'n58':N58,**extra}
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
    if block=='main':fz=check_freeze();check(fz.get('n58')==N58,'cut variable differs from the freeze')
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
    if a.block!='main':check(not Path(out).resolve().is_relative_to(STUDY_DIR.resolve()),'smoke output must not be inside results/study-058')
    if a.seal_partial:print('sealed partial',seal_partial(out,a.block,a.reason))
    else:run(out,a.block);print('done')
