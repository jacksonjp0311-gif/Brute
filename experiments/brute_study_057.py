"""Study BRUTE-0540-SCALE20-COVERFIRST-057 runner (experiments/BRUTE_PLAN_057.json; pre-run deviation #188 fixes every
definition added here). New file; built from experiments/brute_study_056.py (frozen). The frozen 047 runner is imported, never
edited: its arm_active and record builders are used unchanged. The frozen 051 runner is imported only for its pure canon helpers.
Runtime rebinding in this process and every worker only (as 048-056): S47.caps -> (C20, B20), S47.ARMS / D_ARMS gain the 057
arms, S47._api16d -> _api. certify/16e is unchanged and driven through its public interface only.
Arms (plan design.arms), all certify/16e at bound 20, C20 50000, B20 2000000, conflict-only stop, max_chunks None:
  API16E20  passive prefix only (the 056 baseline);
  COV_O     prefix + oracle covering extension (harness-level, uses the truth to PLAN the walk; certify/16e sees only the trace;
            'oracle-planned, not deployable');
  LEN_R     prefix + seeded random extension of exactly the COV_O extension length on the same seed (length-matched control);
  COV_X     prefix + brute.cover20/1 extension (truth-free; h 1, 120 steps), then certify/16e;
  COV_X_b   COV_X again (second pass, reversed seed order; determinism).
One 8-worker pool, max_tasks_per_child=1. Job order: per seed COV_O, LEN_R, API16E20, COV_X; then COV_X_b in reversed seed order.
Cut rule (plan runtime_estimate, applied at the pre-freeze projection only, fixed in #188 before the freeze): N57 12 -> 8 if the
projected run exceeds 3300 s.
Smoke (pre-freeze only, never gated; outside results/study-057): 12430001-02, all five arms; 12430003-06 declared unused except
12430003 by the no-network check in api_checks_057.
  PYTHONPATH=. python experiments/brute_study_057.py --block main
  PYTHONPATH=. python experiments/brute_study_057.py --block smoke --output /tmp/x
"""
from __future__ import annotations
import argparse,random,time
from collections import deque
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor,as_completed
from experiments import brute_study_047 as S47
from experiments import brute_study_051 as S51
from experiments import worlds_050 as W50
from experiments.worlds_026 import trajectory
from experiments.brute_study_033 import StepWorld,passive
from brute.api import certify16e as C16E
from brute.api import cover20 as CV
from experiments.brute_common import dumps
from experiments.brute_common_057 import (PLAN,FREEZE,STUDY_DIR,load,sha,write_new,check_freeze,check,Checkpoint,C20,B20,BOUND,KEY,FAMILY,
                                          ALL_ARMS,EXT_ARMS,X_ARMS,WORKERS,HARD_KILL_S,STOP_RULE,COVER,LEN_RNG,ORACLE_RULE)
from scripts.check_seeds_057 import check_run_seeds,target_ranges,SMOKE

canon16e=S51.canon16e
S47.caps=lambda:(C20,B20)
S47.ARMS=tuple(S47.ARMS)+ALL_ARMS;S47.D_ARMS=tuple(S47.D_ARMS)+ALL_ARMS
N57=12      # declared cut rule: 12 -> 8 only if the projected run > 3300 s; fixed in #188 before the freeze
CUT_STEPS=(12,8);CUT_CAP_S=3300.0
SCHEMA='brute.study.v54_0';SCHEMA_CASE='brute.case.v54_0'
SMOKE_FRESH=(SMOKE[0],SMOKE[0]+1)
_STATE={'arm':None,'seed':None,'w':None,'last':None,'ext':None}


def canon57(r):
    """#188: canon16e plus the extension (length and actions) and the arm's api result; no wall fields."""
    return dumps({'e':canon16e(r).decode(),'ext_len':r.get('ext_len'),'ext_acts':r.get('ext_acts'),'api':r.get('api')})


def used_pairs(w,acts):
    q=w.start;used=set()
    for a in acts:used.add((q,a));q=w.transitions[q][a]
    return used,q


def reachable(w,q):
    seen={q};dq=deque([q])
    while dq:
        s=dq.popleft()
        for t in w.transitions[s]:
            if t not in seen:seen.add(t);dq.append(t)
    return seen


def coverage(w,acts):
    """(unexercised pairs of all n*k, unexercised pairs at states reachable from the state after acts)."""
    used,q=used_pairs(w,acts);R=reachable(w,q)
    return w.n*w.k-len(used),sum(1 for s in R for a in range(w.k) if (s,a) not in used)


def oracle_walk(w,acts):
    """Plan design.oracle_walk (harness-level, uses the truth): BFS in action-index order from the current true state to the nearest
    state with an unexercised action, walk there and take its lowest unexercised action; repeat until none is reachable."""
    used,q=used_pairs(w,acts);ext=[]
    while True:
        prev={q:None};dq=deque([q]);tgt=None
        while dq:
            s=dq.popleft();un=[a for a in range(w.k) if (s,a) not in used]
            if un:tgt=(s,un[0]);break
            for a in range(w.k):
                t=w.transitions[s][a]
                if t not in prev:prev[t]=(s,a);dq.append(t)
        if tgt is None:return ext
        s,a0=tgt;path=[]
        while prev[s] is not None:ps,pa=prev[s];path.append(pa);s=ps
        for a in path[::-1]+[a0]:used.add((q,a));ext.append(a);q=w.transitions[q][a]


def len_control(seed,n,k):
    """Plan design.length_matched_control: n actions from random.Random(seed*7+57).randrange(k)."""
    r=random.Random(seed*7+57);return [r.randrange(k) for _ in range(n)]


def extension(arm,w,seed,rd,acts,sw):
    """The arm's extension actions and observations (stepped on sw, so the world wrapper counts them)."""
    if arm=='API16E20':return [],[]
    if arm in X_ARMS:
        return CV.cover20(rd[0],acts,rd[1:],w.k,sw.step,COVER['h'],COVER['steps'])
    ext=oracle_walk(w,acts) if arm=='COV_O' else len_control(seed,len(oracle_walk(w,acts)),w.k) if arm=='LEN_R' else None
    check(ext is not None,'unknown arm '+str(arm))
    return ext,[sw.step(a) for a in ext]


def _api(rd,acts,k,N,sw,Kc,C,B,H):
    """certify/16e through its public interface on prefix + the arm's extension, then its own proposals. Conflict-only stop: hook
    None (no wall interrupt) and the case guard at the 900 s hard kill."""
    arm=_STATE['arm'];w=_STATE['w']
    ext,eo=extension(arm,w,_STATE['seed'],rd,acts,sw);_STATE['ext']=list(ext)
    kw=dict(max_chunks=None,K=Kc,conflict_cap=C,budget_conflicts=B,wall_guard_case_s=HARD_KILL_S,
            wall_guard_call_s=S47.GUARD_CALL_S,solver=S47.SOLVER4,hook=None,factory=C16E.counted16d)
    c=C16E.Certifier16E(rd[0],k,N,'a16d',**kw)
    try:
        for a,o in zip(list(acts)+list(ext),list(rd[1:])+list(eo)):c.observe(a,o)
        while True:
            x=c.propose()
            if x is None:break
            for a in x:c.observe(a,sw.step(a))
        res=dict(c.record())
    finally:c.close()
    res['api_result']=c.result();res['api_current']=c.current();_STATE['last']=res;return res


S47._api16d=_api


def run_fresh(seed,arm):
    w=W50.world(seed,FAMILY);N=W50.SIZES[FAMILY];check(w.n==N==BOUND,'world size differs from the declared bound')
    tr=trajectory(w,seed,0.0);_,acts,rd=passive(StepWorld(w),seed)
    check(rd==list(tr['readings']) and acts==list(tr['actions']),'prefix differs from worlds_026.trajectory')
    _STATE.update(arm=arm,seed=seed,w=w,last=None,ext=None)
    a=S47.arm_active(w,seed,N,arm,S47.K,B20);res=_STATE['last'];ext=_STATE['ext']
    check(a['budget']==B20 and a['conflict_cap']==C20 and a['budget_conflicts']==B20 and res['max_chunks'] is None
          and res['api_result']['api']==C16E.API,'057 caps not applied')
    check(len(res['rounds'])==len(a['rounds']),'round count')
    for rr,x in zip(a['rounds'],res['rounds']):
        check(rr['call_conflicts']==x['call_conflicts'],'round alignment')
        rr['call_chunks']=list(x['call_chunks']);rr['chunk_conflicts']=[list(y) for y in x['chunk_conflicts']]
        rr['chunk_walls_informational']=[list(y) for y in x['chunk_walls']]
    a['max_chunks']=res['max_chunks'];a['chunks_total']=res['chunks_total'];a['chunk_wall_max']=res['chunk_wall_max']
    a['case_wall_informational']=res['case_wall'];a['calls_total']=sum(len(x['call_conflicts']) for x in res['rounds'])
    a['stop_rule']=STOP_RULE;check(a['hook_arms']==0,'a wall hook was armed (conflict-only stop violated)');a['hard_kill_s']=HARD_KILL_S
    a['api']=res['api_result'];a['sizes']=list(res.get('sizes') or [])
    check(list(a['extra_acts'][:len(ext)])==ext and len(a['extra_acts'])==len(ext)+a['used'],'extension bookkeeping')
    u0,ur0=coverage(w,acts);uh,urh=coverage(w,acts+ext);uf,urf=coverage(w,acts+list(a['extra_acts']))
    a.update(ext_len=len(ext),ext_acts=list(ext),truth_pairs_unexercised_prefix=u0,truth_pairs_unexercised_handoff=uh,
             truth_pairs_unexercised_handoff_reachable=urh,truth_pairs_unexercised_final=uf,truth_pairs_unexercised_final_reachable=urf,
             oracle_planned=arm=='COV_O',explorer=(dict(COVER) if arm in X_ARMS else None),len_rng=(LEN_RNG if arm=='LEN_R' else None))
    return {'schema':SCHEMA_CASE,'key':KEY,'family':FAMILY,'seed':seed,'eps':0.0,'n':w.n,'k':w.k,'N':N,
            'group':arm,'arms':{arm:a},'truth_reachable':len(S47.canonical_bfs(w.transitions,w.emissions,w.start)[1])}


def seeds_of(plan):
    R=target_ranges(plan);return list(range(R[KEY][0],R[KEY][1]+1))


def declared_list(plan):return seeds_of(plan)[:N57]


def _order(seeds,block):
    return [(block,KEY,s,g) for s in seeds for g in ('COV_O','LEN_R','API16E20','COV_X')]+[(block,KEY,s,'COV_X_b') for s in reversed(seeds)]


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
    return ' '.join(f'{a}={v["label"]}/{v["stop"]} g={v["wall_guard"]} ext={v["ext_len"]} uh={v["truth_pairs_unexercised_handoff"]} uf={v["truth_pairs_unexercised_final"]} cf={v["conflicts_spent"]} nr={v["n_rounds"]}' for a,v in c['arms'].items())


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
            cases[ck]={x:g[x] for x in ('schema','key','family','seed','n','k','N','truth_reachable','block')};cases[ck]['arms']={}
            cases[ck]['eps']=g['eps'];cases[ck]['group_walls_informational']={};order.append(ck)
        check(all(cases[ck][x]==g[x] for x in ('family','seed','n','k','N','truth_reachable')),'group records disagree: '+ck)
        cases[ck]['arms'].update(g['arms']);cases[ck]['group_walls_informational'][j[3]]=g['job_wall_informational']
    for c in cases.values():c['arms']={a:c['arms'][a] for a in ALL_ARMS if a in c['arms']}
    order.sort(key=lambda ck:cases[ck]['seed']);return [cases[ck] for ck in order]


def _write(output,plan,block,keys,cases,complete,extra):
    from brute.evaluation import no_time
    smoke=block!='main'
    result={'schema':SCHEMA,'plan':plan,'block':block,'smoke':smoke,'complete':complete,'job_keys':keys,'cases':cases,
            'caps':[C20,B20],'bound':BOUND,'arms':list(ALL_ARMS),'workers':WORKERS,
            'stop':{'hard_kill_s':HARD_KILL_S,'stop_rule':STOP_RULE},'cover':COVER,'len_rng':LEN_RNG,'oracle_rule':ORACLE_RULE,'n57':N57,**extra}
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
    if block=='main':fz=check_freeze();check(fz.get('n57')==N57,'cut variable differs from the freeze')
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
    if a.block!='main':check(not Path(out).resolve().is_relative_to(STUDY_DIR.resolve()),'smoke output must not be inside results/study-057')
    if a.seal_partial:print('sealed partial',seal_partial(out,a.block,a.reason))
    else:run(out,a.block);print('done')
