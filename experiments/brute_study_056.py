"""Study BRUTE-0530-SCALE20-LSTAR-056 runner (experiments/BRUTE_PLAN_056.json, no amendment; pre-run deviation #185 fixes
every definition added here). New file; built from experiments/brute_study_055.py (frozen). The frozen 047 runner is imported, never
edited: its arm_active and record builders are used unchanged. The frozen 051 runner is imported only for its pure canon / BFS /
truth helpers. Runtime rebinding in this process and every worker only (as 048-055): S47.caps -> the job's (C, B), S47.ARMS / D_ARMS
gain the 056 arms, S47._api16d -> _api (certify/20l or certify/16e through their public interfaces). certify/16e, 16n, 16s, 20t
and 20c are unchanged.
Parts (plan design.arms):
  scale20t: the first N20L of 6 fresh clean 20-state worlds (worlds_047 'scale20' via worlds_050.world), API20L and API20L_b
            (certify/20l at bound 20) and API16E20 (certify/16e at bound 20, once), C20 50000, B20 2000000;
  compat20t: the first NC20L of 6 fresh clean 16-state controls (worlds_043 'scale16'), API20L (certify/20l at bound 16) and
            API16E (certify/16e at bound 16), C 50000, B 3000000.
Every arm: conflict-only stop (hook None; case guard = 900 s hard kill as a safety net), max_chunks None.
One phase: a 4-worker pool for scale20t and a 4-worker pool for compat20t run concurrently; one process.
Cut rule (plan runtime_estimate, applied at the pre-freeze projection only, fixed in #185 before the freeze): N20L 6 -> 4 if the
projected run exceeds 3300 s, then NC20L 6 -> 4.
Smoke (pre-freeze only, never gated; outside results/study-056): 12370001-02 scale20t (three arms), 12370003-04 compat20t (two
arms); 12370005-06 are declared unused.
  PYTHONPATH=. python experiments/brute_study_056.py --block main
  PYTHONPATH=. python experiments/brute_study_056.py --block smoke --output /tmp/x
"""
from __future__ import annotations
import argparse,time
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor,as_completed
from experiments import brute_study_047 as S47
from experiments import brute_study_051 as S51
from experiments import worlds_050 as W50
from experiments.worlds_026 import trajectory
from experiments.brute_study_033 import StepWorld,passive
from brute.api import certify16e as C16E
from brute.api import certify20l as C20L
from experiments.brute_common import dumps
from experiments.brute_common_056 import (PLAN,FREEZE,STUDY_DIR,load,sha,write_new,check_freeze,check,Checkpoint,CAPS_OF,caps_for,
                                          BOUND_OF,T_ARMS,E_ARMS,ALL_ARMS,ARMS_OF,WORKERS,WORKERS_S,WORKERS_C,HARD_KILL_S,STOP_RULE)
from scripts.check_seeds_056 import check_run_seeds,target_ranges,SMOKE,FAMILY_OF

canon16e=S51.canon16e;machine_canon=S51.machine_canon;_bfs=S51._bfs;truth_codes=S51.truth_codes;_drive=S51._drive
S47.caps=lambda:CAPS_OF['compat20t']   # rebound per job in run_fresh (each job runs in its own worker process)
S47.ARMS=tuple(S47.ARMS)+ALL_ARMS;S47.D_ARMS=tuple(S47.D_ARMS)+ALL_ARMS
N20L=6      # declared cut rule: 6 -> 4 only if the projected run > 3300 s; fixed in #185 before the freeze
NC20L=6     # declared cut rule: 6 -> 4 only if the projected run still > 3300 s after N20L = 4; fixed in #185 before the freeze
CUT_STEPS=(6,4);CUT_CAP_S=3300.0
KEY_ORDER=('scale20t','compat20t')
SCHEMA='brute.study.v53_0';SCHEMA_CASE='brute.case.v53_0'
SMOKE_FRESH=(('scale20t',SMOKE[0]),('scale20t',SMOKE[0]+1),('compat20t',SMOKE[0]+2),('compat20t',SMOKE[0]+3))
_STATE={'arm':None,'seed':None,'last':None}


def canon20l(r):
    """#185: canon16e plus the record's observation table (basis, rows, columns, hypotheses, counterexamples, fill steps and the
    per-step log of fill and check entries); no wall fields."""
    return dumps({'e':canon16e(r).decode(),'table':r.get('table')})


def api_of(arm):return C20L.API if arm in T_ARMS else C16E.API


def _api(rd,acts,k,N,sw,Kc,C,B,H):
    """certify/20l (API20L arms) or certify/16e (API16E arms) through their public interfaces only. Conflict-only stop: hook None
    (no wall interrupt) and the case guard at the 900 s hard kill."""
    arm=_STATE['arm']
    kw=dict(max_chunks=None,K=Kc,conflict_cap=C,budget_conflicts=B,wall_guard_case_s=HARD_KILL_S,
            wall_guard_call_s=S47.GUARD_CALL_S,solver=S47.SOLVER4,hook=None,factory=C16E.counted16d)
    c=C20L.Certifier20L(rd[0],k,N,'a20l',**kw) if arm in T_ARMS else C16E.Certifier16E(rd[0],k,N,'a16d',**kw)
    try:_drive(c,rd,acts,sw);res=dict(c.record())
    finally:c.close()
    res['api_result']=c.result();res['api_current']=c.current();_STATE['last']=res;return res


S47._api16d=_api


def run_fresh(seed,key,arm):
    fam=FAMILY_OF[key];w=W50.world(seed,fam);N=W50.SIZES[fam];check(w.n==N==BOUND_OF[key],'world size differs from the declared bound')
    tr=trajectory(w,seed,0.0);_,acts,rd=passive(StepWorld(w),seed)
    check(rd==list(tr['readings']) and acts==list(tr['actions']),'prefix differs from worlds_026.trajectory')
    _STATE.update(arm=arm,seed=seed,last=None);C,B=caps_for(key);S47.caps=lambda:(C,B)
    a=S47.arm_active(w,seed,N,arm,S47.K,B);res=_STATE['last']
    check(a['budget']==B and a['conflict_cap']==C and a['budget_conflicts']==B and res['max_chunks'] is None
          and res['api_result']['api']==api_of(arm),'056 caps not applied')
    check(len(res['rounds'])==len(a['rounds']),'round count')
    for rr,x in zip(a['rounds'],res['rounds']):
        check(rr['call_conflicts']==x['call_conflicts'],'round alignment')
        rr['call_chunks']=list(x['call_chunks']);rr['chunk_conflicts']=[list(y) for y in x['chunk_conflicts']]
        rr['chunk_walls_informational']=[list(y) for y in x['chunk_walls']]
        if arm in T_ARMS:rr['M1_source']=x.get('M1_source');rr.update({'repair':x['repair']} if 'repair' in x else {})   # #185 M1 repair provenance
    a['max_chunks']=res['max_chunks'];a['chunks_total']=res['chunks_total'];a['chunk_wall_max']=res['chunk_wall_max']
    a['case_wall_informational']=res['case_wall'];a['calls_total']=sum(len(x['call_conflicts']) for x in res['rounds'])
    a['stop_rule']=STOP_RULE;check(a['hook_arms']==0,'a wall hook was armed (conflict-only stop violated)');a['hard_kill_s']=HARD_KILL_S
    a['api']=res['api_result'];a['sizes']=list(res.get('sizes') or [])
    a['table']=res.get('table') if arm in T_ARMS else None
    check(arm not in T_ARMS or a['table'] is not None,'table not kept')
    return {'schema':SCHEMA_CASE,'key':key,'family':fam,'seed':seed,'eps':0.0,'n':w.n,'k':w.k,'N':N,
            'group':arm,'arms':{arm:a},'truth_reachable':len(S47.canonical_bfs(w.transitions,w.emissions,w.start)[1])}


def seeds_of(plan,k):
    R=target_ranges(plan);return list(range(R[k][0],R[k][1]+1))


def declared_list(plan,k):
    sl=seeds_of(plan,k);return sl[:N20L] if k=='scale20t' else sl[:NC20L]


def jobs_for(plan,block):
    if block=='main':
        s20=declared_list(plan,'scale20t');cp=declared_list(plan,'compat20t')
        out=[('main','scale20t',s,'API20L') for s in s20]+[('main','scale20t',s,'API16E20') for s in s20]
        out+=[('main','scale20t',s,'API20L_b') for s in reversed(s20)]
        out+=[('main','compat20t',s,g) for g in ARMS_OF['compat20t'] for s in cp]
        return out
    if block=='smoke':return [('smoke',k,s,g) for k,s in SMOKE_FRESH for g in ARMS_OF[k]]
    raise ValueError(block)


def key(job):return ':'.join(str(x) for x in job)
def case_key(job):return f'{job[0]}:{job[1]}:{job[2]}'


def check_job(job,plan):
    b,k,s,g=job;check(g in ALL_ARMS and k in KEY_ORDER,'arm/key');check(g in ARMS_OF[k],'arm for key')
    if b=='main':
        check_run_seeds('target',[s],plan,key=k);check(s in declared_list(plan,k),'case not in the declared (cut) list')
    elif b=='smoke':check_run_seeds('smoke',[s],plan)
    else:raise ValueError(b)


def run_job(job,plan):
    check_job(job,plan);t0=time.perf_counter();c=run_fresh(job[2],job[1],job[3])
    c['block']=job[0];c['job_wall_informational']=time.perf_counter()-t0;return key(job),c


def _job(x):return run_job(*x)


def _lab(c):
    return ' '.join(f'{a}={v["label"]}/{v["stop"]} g={v["wall_guard"]} ch={v.get("chunks_total")} cf={v["conflicts_spent"]} rows={len((v.get("table") or {}).get("basis") or [])} cx={(v.get("table") or {}).get("counterexamples") or 0}' for a,v in c['arms'].items())


def run_jobs(jobs,plan,ckpt,log=print):
    """scale20t jobs on a 4-worker pool, compat20t jobs on a 4-worker pool, both submitted at once (list order within a pool)."""
    for j in jobs:check_job(j,plan)
    todo=[j for j in jobs if key(j) not in ckpt.done];ts=[j for j in todo if j[1]=='scale20t'];tc=[j for j in todo if j[1]=='compat20t']
    log(f'{len(jobs)-len(todo)} cached, {len(todo)} to run: scale20t {len(ts)} on {WORKERS_S} workers, compat20t {len(tc)} on {WORKERS_C} workers',flush=True)
    with ProcessPoolExecutor(WORKERS_S,max_tasks_per_child=1) as es,ProcessPoolExecutor(WORKERS_C,max_tasks_per_child=1) as ec:
        futs=[es.submit(_job,(j,plan)) for j in ts]+[ec.submit(_job,(j,plan)) for j in tc]
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
    rank={k:i for i,k in enumerate(KEY_ORDER)};order.sort(key=lambda ck:(rank[cases[ck]['key']],cases[ck]['seed']))
    return [cases[ck] for ck in order]


def _write(output,plan,block,keys,cases,complete,extra):
    from brute.evaluation import no_time
    smoke=block!='main'
    result={'schema':SCHEMA,'plan':plan,'block':block,'smoke':smoke,'complete':complete,'job_keys':keys,'cases':cases,
            'caps':{k:list(v) for k,v in CAPS_OF.items()},'bounds':BOUND_OF,'arms_of':{k:list(v) for k,v in ARMS_OF.items()},
            'workers':{'total':WORKERS,'scale20t':WORKERS_S,'compat20t':WORKERS_C},
            'stop':{'hard_kill_s':HARD_KILL_S,'stop_rule':STOP_RULE},'hyp_rounds':C20L.HYP_ROUNDS,'n_scale20t':N20L,'n_compat20t':NC20L,**extra}
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
    if block=='main':fz=check_freeze();check(fz.get('n_scale20t')==N20L and fz.get('n_compat20t')==NC20L,'cut variables differ from the freeze')
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
    if a.block!='main':check(not Path(out).resolve().is_relative_to(STUDY_DIR.resolve()),'smoke output must not be inside results/study-056')
    if a.seal_partial:print('sealed partial',seal_partial(out,a.block,a.reason))
    else:run(out,a.block);print('done')
