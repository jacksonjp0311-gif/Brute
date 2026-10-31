"""Study BRUTE-0460-CERTIFY16E-RESUME-SCALE20-049 runner (experiments/BRUTE_PLAN_049.json; pre-run deviation #171 fixes every
definition added here). New file. The 047 runner experiments/brute_study_047.py (frozen) is imported, never edited: its
arm_active / run_fresh / canon16d / classify / compare_sealed are used unchanged. Runtime rebinding in this process and every
forked worker only (as 048 rebound caps): S47.caps -> (C 50000, B16), S47.ARMS / D_ARMS gain API16E, API16E_b, API16E_c1, and
S47._api16d -> _api16e (certify/16e through its public interface; max_chunks None for API16E / API16E_b, 1 for API16E_c1).
The chunk fields (per-call chunk counts, per-chunk conflicts and walls, max_chunks, chunks_total, chunk_wall_max, case wall) are
copied from the certify/16e record onto the arm record after run_fresh (one job per process, max_tasks_per_child=1).
Main (104 jobs at N20 = 8, R20 = True): part a scale16 x 12 + control x 6 and part d scale20 x N20, each by API16E and API16E_b;
part r: API16E over the 26 sealed 048 traces (12 scale16, 6 control, 8 scale20 if R20), compared with the sealed API16D record;
part c: API16E_c1 over the same 26 sealed traces, compared with the sealed 048 canon16d byte for byte.
Cut order (plan runtime_estimate, fixed in #171 before the freeze): R20 False first, then N20 6, then 4.
Smoke (pre-freeze only, never gated; outside results/study-049): 11690001-02 scale16, 11690003-04 scale20, 11690005-06 control,
each by API16E and API16E_b, plus part r and part c on sealed 048 scale16 11510002 (AMB) and control 11530001.
  PYTHONPATH=. python experiments/brute_study_049.py --block main --workers 8
  PYTHONPATH=. python experiments/brute_study_049.py --block smoke --output /tmp/x --workers 8
"""
from __future__ import annotations
import argparse,time
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor,as_completed
from experiments import brute_study_047 as S47
from brute.api import certify16e as C16E
from experiments.brute_common import dumps
from experiments.brute_common_049 import (PLAN,FREEZE,STUDY_DIR,load,sha,write_new,check_freeze,check,Checkpoint,C49,B16,B20,budget_for,
                                          MAX_CHUNKS,sealed048)
from scripts.check_seeds_049 import check_run_seeds,target_ranges,SMOKE

ARMS=('API16E','API16E_b');ALL_ARMS=('API16E','API16E_b','API16E_c1')
S47.caps=lambda:(C49,B16)          # plan 049 cap_rule (fixed); scale20 passes B20 explicitly
S47.ARMS=tuple(S47.ARMS)+ALL_ARMS;S47.D_ARMS=tuple(S47.D_ARMS)+ALL_ARMS
N20=8      # declared cut order (plan runtime_estimate): R20 False first, then N20 6, then 4; fixed in #171 before the freeze
R20=True
KEY_ORDER=('scale16','control','scale20')
canon16d=S47.canon16d;classify=S47.classify;compare_sealed=S47.compare_sealed
SCHEMA='brute.study.v46_0';SCHEMA_CASE='brute.case.v46_0'
SEALED_SEEDS={'scale16':tuple(range(11510001,11510013)),'control':tuple(range(11530001,11530007)),'scale20':tuple(range(11610001,11610009))}
SMOKE_FRESH=tuple((k,SMOKE[0]+i) for k,i in (('scale16',0),('scale16',1),('scale20',2),('scale20',3),('control',4),('control',5)))
SMOKE_SEALED=(('scale16',11510002),('control',11530001))
CHUNK_ROUND=('call_chunks','chunk_conflicts')
_STATE={'max_chunks':None,'last':None}


def _api16e(rd,acts,k,N,sw,Kc,C,B,H):
    """certify/16e through its public interface only: observe the prefix, then propose / execute / observe until None."""
    c=C16E.Certifier16E(rd[0],k,N,'a16d',max_chunks=_STATE['max_chunks'],K=Kc,conflict_cap=C,budget_conflicts=B,
                        wall_guard_case_s=S47.GUARD_CASE_S,wall_guard_call_s=S47.GUARD_CALL_S,solver=S47.SOLVER4,hook=H,factory=C16E.counted16d)
    try:
        for a,o in zip(acts,rd[1:]):c.observe(a,o)
        while True:
            w=c.propose()
            if w is None:break
            for a in w:c.observe(a,sw.step(a))
        res=dict(c.record());res['api_result']=c.result();res['api_current']=c.current();_STATE['last']=res;return res
    finally:c.close()


S47._api16d=_api16e


def canon16e(r):
    """#171: canon16d plus each round's per-call chunk counts and per-chunk conflict counts (no wall fields)."""
    return dumps({'arm':{x:r.get(x) for x in S47.CANON_ARM},
                  'rounds':[{x:rr.get(x) for x in S47.CANON_ROUND+CHUNK_ROUND} for rr in r['rounds']]})


def seeds_of(plan,k):
    R=target_ranges(plan);s=list(range(R[k][0],R[k][1]+1))
    return s[:N20] if k=='scale20' else s


def run_arm(seed,k,arm):
    check(arm in ALL_ARMS,'arm');_STATE['max_chunks']=MAX_CHUNKS[arm];_STATE['last']=None
    c=S47.run_fresh(seed,k,arm,S47.K,budget_for(k));a=c['arms'][arm];res=_STATE['last']
    check(res is not None and a['budget']==budget_for(k) and a['conflict_cap']==C49 and a['budget_conflicts']==budget_for(k)
          and res['max_chunks']==MAX_CHUNKS[arm] and res['api_result']['api']==C16E.API,'049 caps / max_chunks not applied')
    check(len(res['rounds'])==len(a['rounds']),'round count')
    for rr,x in zip(a['rounds'],res['rounds']):
        check(rr['call_conflicts']==x['call_conflicts'],'round alignment')
        rr['call_chunks']=list(x['call_chunks']);rr['chunk_conflicts']=[list(y) for y in x['chunk_conflicts']]
        rr['chunk_walls_informational']=[list(y) for y in x['chunk_walls']]
    a['max_chunks']=res['max_chunks'];a['chunks_total']=res['chunks_total'];a['chunk_wall_max']=res['chunk_wall_max']
    a['case_wall_informational']=res['case_wall'];a['calls_total']=sum(len(x['call_conflicts']) for x in res['rounds'])
    c['schema']=SCHEMA_CASE;return c


def run_sealed(part,k,seed):
    """Part r (API16E) or part c (API16E_c1) on a sealed 048 trace, compared with the sealed API16D record."""
    arm={'r':'API16E','c':'API16E_c1'}[part];s=sealed048()[(k,seed)];c=run_arm(seed,k,arm)
    check(all(c[x]==s[x] for x in ('family','seed','n','k','N','truth_reachable')),'replay world differs from the sealed case')
    sa=s['arms']['API16D'];a=c['arms'][arm];cmp=compare_sealed(a,sa);cmp['class']=classify(cmp,a,sa)
    cmp['sealed_capped_any']=bool(sa['capped']);cmp['replay_capped_any']=bool(a['capped'])
    cmp['canon16d_equal']=canon16d(a)==canon16d(sa);cmp['sealed_label']=sa['label'];cmp['sealed_stop']=sa['stop']
    c['replay']=cmp;c['part']=part;c['source']='048';return c


def jobs_for(plan,block):
    if block=='main':
        rk=('scale20','scale16') if R20 else ('scale16',)
        out=[('main','scale20',s,'API16E') for s in seeds_of(plan,'scale20')]+[('main','scale16',s,'API16E') for s in seeds_of(plan,'scale16')]
        out+=[('r',k,s,'API16E') for k in rk for s in SEALED_SEEDS[k]]
        out+=[('main',k,s,'API16E_b') for k in ('scale20','scale16') for s in reversed(seeds_of(plan,k))]
        out+=[('main','control',s,g) for g in ARMS for s in seeds_of(plan,'control')]
        out+=[('r','control',s,'API16E') for s in SEALED_SEEDS['control']]
        out+=[('c',k,s,'API16E_c1') for k in ('scale20','scale16','control') for s in SEALED_SEEDS[k]]
        return out
    if block=='smoke':
        return ([(p,k,s,g) for k,s in SMOKE_SEALED for p,g in (('r','API16E'),('c','API16E_c1'))]
                +[('smoke',k,s,g) for g in ARMS for k,s in SMOKE_FRESH])
    raise ValueError(block)


def key(job):return ':'.join(str(x) for x in job)
def case_key(job):return f'{job[0]}:{job[1]}:{job[2]}'


def check_job(job,plan):
    b,k,s,g=job;check(g in ALL_ARMS and k in KEY_ORDER,'arm/key')
    if b in ('r','c'):
        check(g==('API16E' if b=='r' else 'API16E_c1') and s in SEALED_SEEDS[k],'sealed 048 case')
        if b=='r' and k=='scale20':check(R20,'part r scale20 dropped')
        return
    check(g in ARMS,'fresh arm')
    if b=='main':check_run_seeds('target',[s],plan,key=k);check(s in seeds_of(plan,k),'case not in the declared (cut) list')
    elif b=='smoke':check_run_seeds('smoke',[s],plan)
    else:raise ValueError(b)


def run_job(job,plan):
    check_job(job,plan);t0=time.perf_counter()
    if job[0] in ('r','c'):c=run_sealed(job[0],job[1],job[2])
    else:c=run_arm(job[2],job[1],job[3])
    c['block']=job[0];c['job_wall_informational']=time.perf_counter()-t0;return key(job),c


def _job(x):return run_job(*x)


def _lab(c):
    s=' '.join(f'{a}={v["label"]}/{v["stop"]} g={v["wall_guard"]} ch={v["chunks_total"]} cf={v["conflicts_spent"]}' for a,v in c['arms'].items())
    return s+(f" class={c['replay']['class']} c16d={c['replay']['canon16d_equal']}" if 'replay' in c else '')


def run_jobs(jobs,plan,workers,ckpt,log=print):
    for j in jobs:check_job(j,plan)
    todo=[j for j in jobs if key(j) not in ckpt.done];log(f'{len(jobs)-len(todo)} cached, {len(todo)} to run',flush=True)
    with ProcessPoolExecutor(max(1,workers),max_tasks_per_child=1) as ex:
        futs=[ex.submit(_job,(j,plan)) for j in todo]
        for n,fu in enumerate(as_completed(futs)):
            k_,c=fu.result();ckpt.add(k_,c)
            log(f'done {n+1}/{len(todo)} {k_} {c["job_wall_informational"]:.1f}s {_lab(c)}',flush=True)


def merge(jobs,done):
    reps=[];cases={};order=[]
    for j in jobs:
        if key(j) not in done:continue
        g=done[key(j)]
        if j[0] in ('r','c'):reps.append(g);continue
        ck=case_key(j)
        if ck not in cases:
            cases[ck]={x:g[x] for x in ('schema','key','family','seed','eps','n','k','N','truth_reachable','block')};cases[ck]['arms']={}
            cases[ck]['group_walls_informational']={};order.append(ck)
        check(all(cases[ck][x]==g[x] for x in ('family','seed','n','k','N','truth_reachable')),'group records disagree: '+ck)
        cases[ck]['arms'].update(g['arms']);cases[ck]['group_walls_informational'][j[3]]=g['job_wall_informational']
    for c in cases.values():c['arms']={a:c['arms'][a] for a in ARMS if a in c['arms']}
    rank={k:i for i,k in enumerate(KEY_ORDER)};order.sort(key=lambda ck:(rank[cases[ck]['key']],cases[ck]['seed']))
    reps.sort(key=lambda r:(r['part'],rank[r['key']],r['seed']))
    return reps,[cases[ck] for ck in order]


def _write(output,plan,block,keys,merged,complete,extra):
    from brute.evaluation import no_time
    reps,cases=merged;smoke=block!='main'
    result={'schema':SCHEMA,'plan':plan,'block':block,'smoke':smoke,'complete':complete,'job_keys':keys,'replays':reps,'cases':cases,
            'conflict_cap':C49,'budget_conflicts':{'scale16':B16,'control':B16,'scale20':B20},'max_chunks':MAX_CHUNKS,
            'n_scale20':N20,'r_scale20':R20,**extra}
    write_new(output/'RESULTS.json',result);write_new(output/'SCIENTIFIC.json',no_time(result))
    write_new(output/'SEAL.json',{'study':plan['study'],'block':block,'results_sha256':sha(output/'RESULTS.json'),
        'scientific_sha256':sha(output/'SCIENTIFIC.json'),'plan_sha256':sha(PLAN),'freeze_sha256':None if smoke else sha(FREEZE),
        'case_count':len(cases),'replay_count':len(reps),'job_count':len(keys),'complete':complete,'smoke':smoke,
        'checkpoint_sha256':sha(output/'CHECKPOINT.jsonl') if (output/'CHECKPOINT.jsonl').exists() else None,
        **({'missing_job_keys':extra['missing_job_keys']} if 'missing_job_keys' in extra else {})})


def seal_partial(output,block,reason='study cap'):
    output=Path(output);plan=load(PLAN)
    for nm in ('RESULTS.json','SCIENTIFIC.json','SEAL.json'):check(not (output/nm).exists(),'refusing overwrite '+str(output/nm))
    jobs=jobs_for(plan,block);ck=Checkpoint(output/'CHECKPOINT.jsonl');keys=[key(j) for j in jobs];done=dict(ck.done)
    missing=[k for k in keys if k not in done]
    _write(output,plan,block,keys,merge(jobs,done),False,{'stop_reason':reason,'missing_job_keys':missing})
    return len(keys)-len(missing),len(keys)


def run(output,workers,block):
    output=Path(output);plan=load(PLAN)
    if block=='main':check_freeze()
    for nm in ('RESULTS.json','SCIENTIFIC.json','SEAL.json'):check(not (output/nm).exists(),'refusing overwrite '+str(output/nm))
    t0=time.perf_counter();jobs=jobs_for(plan,block);sealed048()
    output.mkdir(parents=True,exist_ok=True);ck=Checkpoint(output/'CHECKPOINT.jsonl')
    if block=='main':check(not ck.done,'main checkpoint not empty: never resume (standing rule; resume clause not approved)')
    run_jobs(jobs,plan,workers,ck)
    _write(output,plan,block,[key(j) for j in jobs],merge(jobs,ck.done),True,{'total_elapsed_informational':time.perf_counter()-t0})


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--block',choices=('main','smoke'),default='main')
    ap.add_argument('--output');ap.add_argument('--workers',type=int,default=8)
    ap.add_argument('--seal-partial',action='store_true');ap.add_argument('--reason',default='study cap')
    a=ap.parse_args();out=a.output or str(STUDY_DIR/a.block)
    if a.block!='main':check(not Path(out).resolve().is_relative_to(STUDY_DIR.resolve()),'smoke output must not be inside results/study-049')
    if a.seal_partial:print('sealed partial',seal_partial(out,a.block,a.reason))
    else:run(out,a.workers,a.block);print('done')
