"""Study BRUTE-0610-SCALE2B24-064 runner (experiments/BRUTE_PLAN_064.json; the pre-run deviation fixes every definition added
here). New file, built from experiments/brute_study_063.py (frozen); study 058's _Step, truth_label and _verd, the frozen
brute.certify/20p and brute.certify/32b and the new brute.certify/32p are imported and driven through the public interface only;
no frozen runner is rebound and no global is patched.
Arms (plan design.arms), all noise-free at read_bits 2 (original 2-bit emissions), C 50000, B 8000000, K 400, node cap 200000,
conflict-only stop, 1800 s case kill:
  P24  certify/32p, declared N 24, worlds_064 'scale24' (gated headline), N_SEEDS seeds;
  B24  frozen certify/32b, declared N 24, 'scale24', first N_B24 seeds (reported time-capped control, not gated);
  P20  frozen certify/20p, declared N 20, worlds_064 'scale20' (gated replication), N_SEEDS seeds;
  P20b P20 again on the first N_P20B seeds in reversed order (determinism).
Labels as study 058 (truth_label against the true machine). Every record carries the greedy apartness clique sizes of the passive
prefix and of the final trace (frozen brute.scalesearch15), and the P records carry 'clique_size', 'final_clique' and 'repins'.
Job order: B24 ascending, P24 ascending, P20 ascending, P20b descending. One 6-worker pool, max_tasks_per_child=1. Cut rule (plan
runtime_estimate; applied only before the freeze from the smoke projection): N_P20B 2 -> 1, then N_B24 3 -> 2. Main run cap
MAIN_CAP_S from launch (then sealed partial by the operator, never relaunched). Smoke (pre-freeze only, never gated; outside
results/study-064; B 2000000): 12640301 (scale24) and 12640302 (scale20) on their arms; 12640303 only for the api_checks
no-network run.
  PYTHONPATH=. python experiments/brute_study_064.py --block main
  PYTHONPATH=. python experiments/brute_study_064.py --block smoke --output /tmp/x
"""
from __future__ import annotations
import argparse,time
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor,as_completed
from experiments import worlds_064 as W64
from experiments.brute_study_058 import truth_label,_Step,_verd
from brute.api import certify20b as C20B
from brute.api import certify20p as C20P
from brute.api import certify32b as C32B
from brute.api import certify32p as C32P
from brute.scalesearch4 import SOLVER4
from brute.scalesearch15 import apart_matrix,greedy_clique
from experiments.brute_common_064 import (PLAN,FREEZE,STUDY_DIR,load,sha,write_new,check_freeze,check,dumps,Checkpoint,C64,B64,K64,READ_BITS,
                                          NODE_CAP,ARM_SPEC,ALL_ARMS,WORKERS,HARD_KILL_S,GUARD_CALL_S,STOP_RULE,MAIN_CAP_S)
from scripts.check_seeds_064 import check_run_seeds,target_ranges,SMOKE

N_SEEDS=6  # per size (plan cases)
N_B24=2    # plan cases.scale24p_b24 = 3; cut rule applied before the freeze (prefreeze projection exhausted, deviation #202)
N_P20B=1   # plan cases.scale20p_b = 2; cut rule applied before the freeze (prefreeze projection exhausted, deviation #202)
SCHEMA='brute.study.v61_0';SCHEMA_CASE='brute.case.v61_0'
SMOKE24=SMOKE[0];SMOKE20=SMOKE[0]+1
SMOKE_B64=2000000   # smoke budget (tooling check only, never gated)
WALL_KEYS=('query_walls','chunk_walls')
__all__=['truth_label','canon64','run_fresh','jobs_for','run','seal_partial','clique_sizes','N_SEEDS','N_B24','N_P20B']


def canon64(a):
    """GDET64 canonical form of one arm record: no wall fields, no arm name, no api_current."""
    from brute.evaluation import no_time
    x=no_time(dict(a));x.pop('arm',None);x.pop('api_current',None);return dumps(x)


def clique_sizes(masks,acts,T0):
    """(prefix, final) greedy apartness clique sizes (frozen apart_matrix / greedy_clique)."""
    return len(greedy_clique(apart_matrix(list(masks[:T0+1]),list(acts[:T0])))),len(greedy_clique(apart_matrix(list(masks),list(acts))))


API_OF={'certify32p':C32P.API,'certify32b':C32B.API,'certify20p':C20P.API}


def make(arm,first,k,B):
    kw=dict(max_chunks=None,K=K64,conflict_cap=C64,budget_conflicts=B,wall_guard_case_s=HARD_KILL_S,wall_guard_call_s=GUARD_CALL_S,
            solver=SOLVER4,hook=None,factory=C20B.counted16d)
    N=ARM_SPEC[arm][2];api=ARM_SPEC[arm][3]
    if api=='certify32p':return C32P.Certifier32P(first,k,N,'a16d',read_bits=READ_BITS,node_cap=NODE_CAP,**kw)
    if api=='certify20p':return C20P.Certifier20P(first,k,N,'a16d',read_bits=READ_BITS,node_cap=NODE_CAP,**kw)
    if api=='certify32b':return C32B.Certifier32B(first,k,N,'a16d',read_bits=READ_BITS,**kw)
    raise ValueError(api)


def run_fresh(seed,arm,budget=None):
    B=B64 if budget is None else budget
    key_,fam,N,api=ARM_SPEC[arm];w=W64.world(seed,fam);check(w.n==N,'world size differs from the declared bound')
    acts=list(W64.actions(seed,0.0,w.k));sw=_Step(w);T0=len(acts);t0=time.perf_counter()
    c=make(arm,sw.read(),w.k,B)
    try:
        for a in acts:c.observe(a,sw.step(a))
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
    cp,cf=clique_sizes(R['masks'],R['acts'],T0)
    a={'arm':arm,'family':fam,'read_bits':READ_BITS,'bound':N,'true_size':w.n,'stop':R['stop'],'api_label':res['label'],
       'label':truth_label(R['stop'],f['model'],f['s1'],w,sw.q),'n_min':f['n_min'],'model':f['model'],'s1':f['s1'],
       'future':_verd(f['future']),'start':_verd(f['start']),'extra_acts':list(R['acts'][T0:]),'extra_masks':list(R['masks'][T0+1:]),
       'prefix_masks':list(R['masks'][:T0+1]),'used':R['used'],'n_rounds':len(R['rounds']),'rounds':rounds,
       'conflicts_spent':R['conflicts_spent'],'conflict_cap':R['conflict_cap'],'budget_conflicts':R['budget_conflicts'],
       'wall_guard':R['wall_guard'],'guard_events':list(R['guard_events']),'max_chunks':R['max_chunks'],'chunks_total':R['chunks_total'],
       'sizes':list(R.get('sizes') or []),'api':res,'api_current':cur,'K':K64,'distinct_codes':len(set(w.emissions)),
       'node_cap':NODE_CAP if api in ('certify20p','certify32p') else None,'clique_prefix':cp,'clique_final':cf,
       'clique_size':res.get('clique_size'),'final_clique':list(R.get('final_clique') or []),'repins':[list(x) for x in R.get('repins') or []],
       'guards_closed':R.get('guards_closed'),
       'stop_rule':STOP_RULE,'hard_kill_s':HARD_KILL_S,'case_wall_informational':time.perf_counter()-t0}
    check(a['budget_conflicts']==B and a['conflict_cap']==C64 and a['max_chunks'] is None,'064 caps not applied')
    check(res['api']==API_OF[api] and res['family_bound']==N,'api or declared bound not applied')
    check(a['used']<=K64 and a['used']==len(a['extra_acts']),'K accounting')
    return {'schema':SCHEMA_CASE,'key':key_,'seed':seed,'eps':0.0,'n':w.n,'k':w.k,'N':N,'group':arm,'arms':{arm:a}}


def seeds_of(plan,k):
    R=target_ranges(plan);return list(range(R[k][0],R[k][1]+1))


def declared(plan,arm):
    s=seeds_of(plan,ARM_SPEC[arm][0])[:N_SEEDS]
    return s[:N_B24] if arm=='B24' else s[:N_P20B] if arm=='P20b' else s


def _order(s24,b24,s20,b20,block):
    return ([(block,'scale24p',x,'B24') for x in b24]+[(block,'scale24p',x,'P24') for x in s24]+
            [(block,'scale20p',x,'P20') for x in s20]+[(block,'scale20p',x,'P20b') for x in reversed(b20)])


def jobs_for(plan,block):
    if block=='main':return _order(declared(plan,'P24'),declared(plan,'B24'),declared(plan,'P20'),declared(plan,'P20b'),'main')
    if block=='smoke':return _order([SMOKE24],[SMOKE24],[SMOKE20],[SMOKE20],'smoke')
    raise ValueError(block)


def key(job):return ':'.join(str(x) for x in job)
def case_key(job):return f'{job[0]}:{job[1]}:{job[2]}'


def check_job(job,plan):
    b,k,s,g=job;check(g in ALL_ARMS and k==ARM_SPEC[g][0],'arm/key')
    if b=='main':check_run_seeds('target',[s],plan,key=k);check(s in declared(plan,g),'case not in the declared (cut) list')
    elif b=='smoke':check_run_seeds('smoke',[s],plan)
    else:raise ValueError(b)


def run_job(job,plan):
    check_job(job,plan);t0=time.perf_counter();c=run_fresh(job[2],job[3],None if job[0]=='main' else SMOKE_B64)
    c['block']=job[0];c['job_wall_informational']=time.perf_counter()-t0;return key(job),c


def _job(x):return run_job(*x)


def _lab(c):
    return ' '.join(f'{a}={v["label"]}/{v["stop"]} n={v["n_min"]} g={v["wall_guard"]} cf={v["conflicts_spent"]} used={v["used"]} nr={v["n_rounds"]} cl={v["clique_prefix"]}/{v["clique_final"]} cs={v["clique_size"]} rp={len(v["repins"])}' for a,v in c['arms'].items())


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
            'caps':[C64,B64,K64],'read_bits':READ_BITS,'node_cap':NODE_CAP,'arms':list(ALL_ARMS),'arm_spec':ARM_SPEC,
            'workers':WORKERS,'stop':{'hard_kill_s':HARD_KILL_S,'stop_rule':STOP_RULE,'main_cap_s':MAIN_CAP_S},
            'n_seeds':N_SEEDS,'n_b24':N_B24,'n_p20b':N_P20B,**extra}
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
    if block=='main':fz=check_freeze();check(fz.get('n_seeds')==N_SEEDS and fz.get('n_b24')==N_B24 and fz.get('n_p20b')==N_P20B,'cut variable differs from the freeze')
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
    if a.block!='main':check(not Path(out).resolve().is_relative_to(STUDY_DIR.resolve()),'smoke output must not be inside results/study-064')
    if a.seal_partial:print('sealed partial',seal_partial(out,a.block,a.reason))
    else:run(out,a.block);print('done')
