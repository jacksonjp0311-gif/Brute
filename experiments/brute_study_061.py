"""Study BRUTE-0580-BUDGET24W-061 runner (experiments/BRUTE_PLAN_061.json; pre-run deviation #196 fixes every definition added
here). New file, built from experiments/brute_study_060.py (frozen); its _Step, truth_label, canon60 (= canon59) and the frozen
brute.certify/32b are imported and driven through the public interface only; no frozen runner is rebound and no global is patched.
Arms (plan design.arms), all noise-free at read_bits 4, C 50000, B = B61 (from budget_probe_061), K 400, conflict-only stop:
  S24  key scale24w, worlds_060 'scale24r4', declared bound 24, N24 seeds (gated headline; plan: 12, cut to 6 by deviation #196 on the user's 60-min cap);
  S24b S24 again on the first N24B seeds in reversed order (determinism);
  S32  key scale32w, worlds_060 'scale32r4', declared bound 32, N32 seeds (soundness gated; decisions reported only).
Labels as study 060 (truth_label against the true machine). Job order: S32 ascending, S24 ascending, S24b descending. One 8-worker
pool, max_tasks_per_child=1. Cut rule (plan runtime_estimate; fixed in #196 before the freeze, from the probe projection only):
N32 4 -> 0 first, then N24B 6 -> 3, so the projected main run stays <= 3300 s. Smoke (pre-freeze only, never gated; outside
results/study-061; B 2000000): 12610301-12610302 on all three arms; 12610303 only for the api_checks no-network run.
  PYTHONPATH=. python experiments/brute_study_061.py --block main
  PYTHONPATH=. python experiments/brute_study_061.py --block smoke --output /tmp/x
"""
from __future__ import annotations
import argparse,time
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor,as_completed
from experiments import worlds_060 as W60
from experiments.brute_study_059 import beq,_verd
from experiments.brute_study_060 import truth_label,_Step,canon60
from brute.api import certify32b as C32B
from brute.scalesearch4 import SOLVER4
from experiments.brute_common_061 import (PLAN,FREEZE,STUDY_DIR,load,sha,write_new,check_freeze,check,Checkpoint,C61,B61,K61,READ_BITS,
                                          ARM_SPEC,ALL_ARMS,WORKERS,HARD_KILL_S,GUARD_CALL_S,STOP_RULE)
from scripts.check_seeds_061 import check_run_seeds,target_ranges,SMOKE

N32=0   # declared before the freeze from the probe projection (cut rule 4 -> 0); fixed in #196
N24B=2  # declared before the freeze from the probe projection (cut rule 6 -> 3, only after N32 = 0); fixed in #196
N24=6       # plan 12; cut to 6 in #196 (user instruction 14:59 EST: fewer seeds rather than exceed the cap)
SCHEMA='brute.study.v58_0';SCHEMA_CASE='brute.case.v58_0'
SMOKE_FRESH=(SMOKE[0],SMOKE[0]+1)
SMOKE_B61=2000000   # smoke budget (tooling check only, never gated)
WALL_KEYS=('query_walls','chunk_walls')
canon61=canon60
__all__=['beq','truth_label','canon61','run_fresh','jobs_for','run','seal_partial','N32','N24','N24B']


def run_fresh(seed,arm,budget=None):
    B=B61 if budget is None else budget
    key_,fam,N=ARM_SPEC[arm];w=W60.world(seed,fam);check(w.n==N,'world size differs from the declared bound')
    acts=list(W60.actions(seed,0.0,w.k));sw=_Step(w);T0=len(acts);t0=time.perf_counter()
    c=C32B.Certifier32B(sw.read(),w.k,N,'a16d',read_bits=READ_BITS,max_chunks=None,K=K61,conflict_cap=C61,budget_conflicts=B,
                        wall_guard_case_s=HARD_KILL_S,wall_guard_call_s=GUARD_CALL_S,solver=SOLVER4,hook=None,factory=C32B.counted16d)
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
    a={'arm':arm,'family':fam,'read_bits':READ_BITS,'bound':N,'true_size':W60.true_size(w),'stop':R['stop'],'api_label':res['label'],
       'label':truth_label(R['stop'],f['model'],f['s1'],w,sw.q),'n_min':f['n_min'],'model':f['model'],'s1':f['s1'],
       'future':_verd(f['future']),'start':_verd(f['start']),'extra_acts':list(R['acts'][T0:]),'extra_masks':list(R['masks'][T0+1:]),
       'prefix_masks':list(R['masks'][:T0+1]),'used':R['used'],'n_rounds':len(R['rounds']),'rounds':rounds,
       'conflicts_spent':R['conflicts_spent'],'conflict_cap':R['conflict_cap'],'budget_conflicts':R['budget_conflicts'],
       'wall_guard':R['wall_guard'],'guard_events':list(R['guard_events']),'max_chunks':R['max_chunks'],'chunks_total':R['chunks_total'],
       'sizes':list(R.get('sizes') or []),'api':res,'api_current':cur,'K':K61,'distinct_codes':len(set(w.emissions)),
       'stop_rule':STOP_RULE,'hard_kill_s':HARD_KILL_S,'case_wall_informational':time.perf_counter()-t0}
    check(a['budget_conflicts']==B and a['conflict_cap']==C61 and a['max_chunks'] is None and res['api']==C32B.API,'061 caps not applied')
    check(res['family_bound']==N,'declared bound not applied')
    return {'schema':SCHEMA_CASE,'key':key_,'seed':seed,'eps':0.0,'n':w.n,'k':w.k,'N':N,'group':arm,'arms':{arm:a}}


def seeds_of(plan,k):
    R=target_ranges(plan);return list(range(R[k][0],R[k][1]+1))


def declared_list(plan,k):return seeds_of(plan,k)[:(N24 if k=='scale24w' else N32)]
def declared_b(plan):return declared_list(plan,'scale24w')[:N24B]


def _order(s24,s32,block,s24b=None):
    s24b=s24 if s24b is None else s24b
    return ([(block,'scale32w',s,'S32') for s in s32]+[(block,'scale24w',s,'S24') for s in s24]+
            [(block,'scale24w',s,'S24b') for s in reversed(s24b)])


def jobs_for(plan,block):
    if block=='main':return _order(declared_list(plan,'scale24w'),declared_list(plan,'scale32w'),'main',declared_b(plan))
    if block=='smoke':return _order(list(SMOKE_FRESH),list(SMOKE_FRESH),'smoke')
    raise ValueError(block)


def key(job):return ':'.join(str(x) for x in job)
def case_key(job):return f'{job[0]}:{job[1]}:{job[2]}'


def check_job(job,plan):
    b,k,s,g=job;check(g in ALL_ARMS and k==ARM_SPEC[g][0],'arm/key')
    if b=='main':check_run_seeds('target',[s],plan,key=k);check(s in (declared_b(plan) if g=='S24b' else declared_list(plan,k)),'case not in the declared (cut) list')
    elif b=='smoke':check_run_seeds('smoke',[s],plan)
    else:raise ValueError(b)


def run_job(job,plan):
    check_job(job,plan);t0=time.perf_counter();c=run_fresh(job[2],job[3],None if job[0]=='main' else SMOKE_B61)
    c['block']=job[0];c['job_wall_informational']=time.perf_counter()-t0;return key(job),c


def _job(x):return run_job(*x)


def _lab(c):
    return ' '.join(f'{a}={v["label"]}/{v["stop"]} n={v["n_min"]}/{v["true_size"]} g={v["wall_guard"]} cf={v["conflicts_spent"]} used={v["used"]} nr={v["n_rounds"]}' for a,v in c['arms'].items())


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
            'caps':[C61,B61,K61],'read_bits':READ_BITS,'arms':list(ALL_ARMS),'arm_spec':ARM_SPEC,'workers':WORKERS,
            'stop':{'hard_kill_s':HARD_KILL_S,'stop_rule':STOP_RULE},'n24':N24,'n24b':N24B,'n32':N32,**extra}
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
    if block=='main':fz=check_freeze();check(fz.get('n32')==N32 and fz.get('n24')==N24 and fz.get('n24b')==N24B,'cut variable differs from the freeze')
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
    if a.block!='main':check(not Path(out).resolve().is_relative_to(STUDY_DIR.resolve()),'smoke output must not be inside results/study-061')
    if a.seal_partial:print('sealed partial',seal_partial(out,a.block,a.reason))
    else:run(out,a.block);print('done')
