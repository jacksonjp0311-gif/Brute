"""Study BRUTE-0600-ANCHOR2B20-063 runner (experiments/BRUTE_PLAN_063.json; pre-run deviation #200 fixes every definition added
here). New file, built from experiments/brute_study_062.py (frozen); study 058's _Step, truth_label and _verd, the frozen
brute.certify/20b and the new brute.certify/20p are imported and driven through the public interface only; no frozen runner is
rebound and no global is patched.
Arms (plan design.arms), all noise-free at read_bits 2 on worlds_058 'scale20' (original 2-bit emissions), declared bound 20,
C 50000, B 8000000, K 400, node cap 200000, conflict-only stop:
  B2   frozen certify/20b, its usual policy (gated control), N_SEEDS seeds;
  P2   certify/20p, clique-anchored pool (exact max clique, re-pin on growth; gated headline), the same N_SEEDS seeds;
  P2b  P2 again on the first N_P2B seeds in reversed order (determinism).
Labels as study 058 (truth_label against the true machine). CLIQUE63 (secondary, reported): the P2 records carry 'clique_size',
'final_clique' and 'repins' from certify/20p; every record also carries the greedy apartness clique sizes of the passive prefix and
the final trace (frozen brute.scalesearch15 apart_matrix / greedy_clique; deterministic, so part of the canonical record).
Job order: P2 ascending, B2 ascending, P2b descending. One 6-worker pool, max_tasks_per_child=1. Cut rule (plan runtime_estimate;
fixed in #200 before the freeze, from the smoke projection only): N_P2B 3 -> 2 first, then N_SEEDS 8 -> 6 (all arms), so the projected
main run stays <= 3300 s. Smoke (pre-freeze only, never gated; outside results/study-063; B 2000000): 12630301-12630302 on all three
arms; 12630303 only for the api_checks no-network run.
  PYTHONPATH=. python experiments/brute_study_063.py --block main
  PYTHONPATH=. python experiments/brute_study_063.py --block smoke --output /tmp/x
"""
from __future__ import annotations
import argparse,time
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor,as_completed
from experiments import worlds_058 as W58
from experiments.brute_study_058 import truth_label,_Step,_verd
from brute.api import certify20b as C20B
from brute.api import certify20p as C20P
from brute.scalesearch4 import SOLVER4
from brute.scalesearch15 import apart_matrix,greedy_clique
from experiments.brute_common_063 import (PLAN,FREEZE,STUDY_DIR,load,sha,write_new,check_freeze,check,dumps,Checkpoint,C63,B63,K63,READ_BITS,
                                          BOUND,NODE_CAP,KEY,ARM_SPEC,ALL_ARMS,WORKERS,HARD_KILL_S,GUARD_CALL_S,STOP_RULE)
from scripts.check_seeds_063 import check_run_seeds,target_ranges,SMOKE

N_P2B=3   # set before the freeze from the smoke projection (cut rule 3 -> 2); fixed in #200
N_SEEDS=8  # set before the freeze from the smoke projection (cut rule 8 -> 6); fixed in #200
SCHEMA='brute.study.v60_0';SCHEMA_CASE='brute.case.v60_0'
SMOKE_FRESH=(SMOKE[0],SMOKE[0]+1)
SMOKE_B63=2000000   # smoke budget (tooling check only, never gated)
WALL_KEYS=('query_walls','chunk_walls')
__all__=['truth_label','canon63','run_fresh','jobs_for','run','seal_partial','clique_sizes','N_SEEDS','N_P2B']


def canon63(a):
    """GDET63 canonical form of one arm record: no wall fields, no arm name, no api_current."""
    from brute.evaluation import no_time
    x=no_time(dict(a));x.pop('arm',None);x.pop('api_current',None);return dumps(x)


def clique_sizes(masks,acts,T0):
    """(prefix, final) greedy apartness clique sizes (frozen apart_matrix / greedy_clique)."""
    return len(greedy_clique(apart_matrix(list(masks[:T0+1]),list(acts[:T0])))),len(greedy_clique(apart_matrix(list(masks),list(acts))))


def make(arm,first,k,B):
    kw=dict(max_chunks=None,K=K63,conflict_cap=C63,budget_conflicts=B,wall_guard_case_s=HARD_KILL_S,wall_guard_call_s=GUARD_CALL_S,
            solver=SOLVER4,hook=None,factory=C20B.counted16d)
    if ARM_SPEC[arm][3]=='certify20p':return C20P.Certifier20P(first,k,BOUND,'a16d',read_bits=READ_BITS,node_cap=NODE_CAP,**kw)
    return C20B.Certifier20B(first,k,BOUND,'a16d',read_bits=READ_BITS,**kw)


def run_fresh(seed,arm,budget=None):
    B=B63 if budget is None else budget
    key_,fam,N,api=ARM_SPEC[arm];w=W58.world(seed,fam);check(w.n==N==BOUND,'world size differs from the declared bound')
    acts=list(W58.actions(seed,0.0,w.k));sw=_Step(w);T0=len(acts);t0=time.perf_counter()
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
       'sizes':list(R.get('sizes') or []),'api':res,'api_current':cur,'K':K63,'distinct_codes':len(set(w.emissions)),
       'node_cap':NODE_CAP if api=='certify20p' else None,'clique_prefix':cp,'clique_final':cf,
       'clique_size':res.get('clique_size'),'final_clique':list(R.get('final_clique') or []),'repins':[list(x) for x in R.get('repins') or []],
       'guards_closed':R.get('guards_closed'),
       'stop_rule':STOP_RULE,'hard_kill_s':HARD_KILL_S,'case_wall_informational':time.perf_counter()-t0}
    check(a['budget_conflicts']==B and a['conflict_cap']==C63 and a['max_chunks'] is None,'063 caps not applied')
    check(res['api']==(C20P.API if api=='certify20p' else C20B.API) and res['family_bound']==N,'api or declared bound not applied')
    check(a['used']<=K63 and a['used']==len(a['extra_acts']),'K accounting')
    return {'schema':SCHEMA_CASE,'key':key_,'seed':seed,'eps':0.0,'n':w.n,'k':w.k,'N':N,'group':arm,'arms':{arm:a}}


def seeds_of(plan,k=KEY):
    R=target_ranges(plan);return list(range(R[k][0],R[k][1]+1))


def declared_list(plan):return seeds_of(plan)[:N_SEEDS]
def declared_b(plan):return declared_list(plan)[:N_P2B]


def _order(s,block,sb=None):
    sb=s if sb is None else sb
    return [(block,KEY,x,'P2') for x in s]+[(block,KEY,x,'B2') for x in s]+[(block,KEY,x,'P2b') for x in reversed(sb)]


def jobs_for(plan,block):
    if block=='main':return _order(declared_list(plan),'main',declared_b(plan))
    if block=='smoke':return _order(list(SMOKE_FRESH),'smoke')
    raise ValueError(block)


def key(job):return ':'.join(str(x) for x in job)
def case_key(job):return f'{job[0]}:{job[1]}:{job[2]}'


def check_job(job,plan):
    b,k,s,g=job;check(g in ALL_ARMS and k==ARM_SPEC[g][0],'arm/key')
    if b=='main':check_run_seeds('target',[s],plan,key=k);check(s in (declared_b(plan) if g=='P2b' else declared_list(plan)),'case not in the declared (cut) list')
    elif b=='smoke':check_run_seeds('smoke',[s],plan)
    else:raise ValueError(b)


def run_job(job,plan):
    check_job(job,plan);t0=time.perf_counter();c=run_fresh(job[2],job[3],None if job[0]=='main' else SMOKE_B63)
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
            'caps':[C63,B63,K63],'read_bits':READ_BITS,'bound':BOUND,'node_cap':NODE_CAP,'arms':list(ALL_ARMS),'arm_spec':ARM_SPEC,
            'workers':WORKERS,'stop':{'hard_kill_s':HARD_KILL_S,'stop_rule':STOP_RULE},'n_seeds':N_SEEDS,'n_p2b':N_P2B,**extra}
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
    if block=='main':fz=check_freeze();check(fz.get('n_seeds')==N_SEEDS and fz.get('n_p2b')==N_P2B,'cut variable differs from the freeze')
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
    if a.block!='main':check(not Path(out).resolve().is_relative_to(STUDY_DIR.resolve()),'smoke output must not be inside results/study-063')
    if a.seal_partial:print('sealed partial',seal_partial(out,a.block,a.reason))
    else:run(out,a.block);print('done')
