"""Study BRUTE-0470-SCALE20-REPLICATION-NOISE12-050 runner (experiments/BRUTE_PLAN_050.json; pre-run deviation #173 fixes every
definition added here). New file. The frozen 047 runner experiments/brute_study_047.py is imported, never edited: its arm_active,
canon16d and record builders are used unchanged. Runtime rebinding in this process and every forked worker only (as 048 / 049):
S47.caps -> (C 50000, B12), S47.ARMS / D_ARMS gain the 050 arms, S47._api16d -> _api (certify/16e or certify/16n through their
public interfaces). certify/16e itself (frozen in FREEZE_049) is unchanged.
Parts (plan design.parts):
  s: fresh scale20 (24) by API16E at family_bound 20, B20 4000000; API16E_b on the first N20B (12) scale20 cases;
  k: 6 controls, clean 12-state worlds (worlds_026 'scale12'), API16E and API16E_b, family_bound 12, B12;
  n: fresh noise12 (12) by API16N and API16N_b (first N12B, 12) through worlds_050.NoisyStepWorld (eps 0.05; the same noise
     seed for both passes), certify/16n with eps_bar 0.10, delta 0.001 and the anytime k rule, family_bound 12, B12;
  c: API16N_c (eps 0, reads 1) on the 6 control seeds; recount / gates compare it with the part-k API16E record (canon16e).
Cut order (plan runtime_estimate, fixed in #173 before the freeze): N12B 12 -> 6 first, then N20B 12 -> 6.
Smoke (pre-freeze only, never gated; outside results/study-050): 11810001-02 scale20, 11810003-04 control, 11810005-06 noise12,
each by both passes of its key, plus API16N_c on 11810003-04.
  PYTHONPATH=. python experiments/brute_study_050.py --block main --workers 8
  PYTHONPATH=. python experiments/brute_study_050.py --block smoke --output /tmp/x --workers 8
"""
from __future__ import annotations
import argparse,time
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor,as_completed
from experiments import brute_study_047 as S47
from experiments import worlds_050 as W50
from experiments.worlds_026 import trajectory
from experiments.brute_study_033 import StepWorld,passive
from brute.api import certify16e as C16E
from brute.api import certify16n as C16N
from experiments.brute_common import dumps,VerificationError
from experiments.brute_common_050 import (PLAN,FREEZE,STUDY_DIR,load,sha,write_new,check_freeze,check,Checkpoint,C50,B20,B12,budget_for,
                                          EPS_BAR,DELTA,NOISE_OF,E_ARMS,N_ARMS,ALL_ARMS)
from scripts.check_seeds_050 import check_run_seeds,target_ranges,SMOKE,FAMILY_OF

S47.caps=lambda:(C50,B12)          # plan 050 cap_rule (fixed); every job passes its budget explicitly
S47.ARMS=tuple(S47.ARMS)+ALL_ARMS;S47.D_ARMS=tuple(S47.D_ARMS)+ALL_ARMS
N20B=12    # declared cut order (plan runtime_estimate): N12B 12 -> 6 first, then N20B 12 -> 6; fixed in #173 before the freeze
N12B=12
KEY_ORDER=('scale20','control','noise12')
ARMS_OF={'scale20':E_ARMS,'control':E_ARMS,'noise12':('API16N','API16N_b')}
canon16d=S47.canon16d
SCHEMA='brute.study.v47_0';SCHEMA_CASE='brute.case.v47_0'
SMOKE_FRESH=(('scale20',SMOKE[0]),('scale20',SMOKE[0]+1),('control',SMOKE[0]+2),('control',SMOKE[0]+3),('noise12',SMOKE[0]+4),('noise12',SMOKE[0]+5))
CHUNK_ROUND=('call_chunks','chunk_conflicts')
_STATE={'arm':None,'seed':None,'last':None,'nw':None}


def _drive_e(c,rd,acts,sw):
    for a,o in zip(acts,rd[1:]):c.observe(a,o)
    while True:
        w=c.propose()
        if w is None:break
        for a in w:c.observe(a,sw.step(a))


def _api(rd,acts,k,N,sw,Kc,C,B,H):
    """certify/16e (API16E arms) or certify/16n (API16N arms) through their public interfaces only."""
    arm=_STATE['arm'];kw=dict(max_chunks=None,K=Kc,conflict_cap=C,budget_conflicts=B,wall_guard_case_s=S47.GUARD_CASE_S,
                              wall_guard_call_s=S47.GUARD_CALL_S,solver=S47.SOLVER4,hook=H,factory=C16E.counted16d)
    if arm in E_ARMS:
        c=C16E.Certifier16E(rd[0],k,N,'a16d',**kw)
        try:_drive_e(c,rd,acts,sw);res=dict(c.record())
        finally:c.close()
    else:
        eps,reads=NOISE_OF[arm];nw=W50.NoisyStepWorld(sw._w,_STATE['seed'],eps);nw.reset();_STATE['nw']=nw
        k0=reads if reads is not None else C16N.reads_for(1,EPS_BAR,DELTA)
        c=C16N.Certifier16N([nw.read() for _ in range(k0)],k,N,eps_bar=EPS_BAR,delta=DELTA,reads=reads,**kw)
        try:
            for a in acts:nw.step(a);c.observe(a,[nw.read() for _ in range(c.reads_needed())])
            while True:
                w=c.propose()
                if w is None:break
                for a in w:sw.step(a);nw.step(a);c.observe(a,[nw.read() for _ in range(c.reads_needed())])
            res=dict(c.record())
        finally:c.close()
    res['api_result']=c.result();res['api_current']=c.current();_STATE['last']=res;return res


S47._api16d=_api


def canon16e(r):
    """#173 (as #171): canon16d plus each round's per-call chunk counts and per-chunk conflict counts (no wall fields)."""
    return dumps({'arm':{x:r.get(x) for x in S47.CANON_ARM},
                  'rounds':[{x:rr.get(x) for x in S47.CANON_ROUND+CHUNK_ROUND} for rr in r['rounds']]})


def canon16n(r):
    """#173: canon16e plus k per observation, eps_bar, delta, reads and the per-observation per-bit vote counts."""
    return dumps({'e':canon16e(r),'reads_per_obs':r.get('reads_per_obs'),'votes':r.get('votes'),'eps_bar':r.get('eps_bar'),
                  'delta':r.get('delta'),'reads':r.get('reads')})


def truth_codes(w,acts):
    q=w.start;out=[w.emissions[q]]
    for a in acts:q=w.transitions[q][a];out.append(w.emissions[q])
    return out


def run_fresh(seed,key,arm):
    fam=FAMILY_OF[key];w=W50.world(seed,fam);N=W50.SIZES[fam];check(w.n==N,'world size differs from the declared bound')
    tr=trajectory(w,seed,0.0);_,acts,rd=passive(StepWorld(w),seed)
    check(rd==list(tr['readings']) and acts==list(tr['actions']),'prefix differs from worlds_026.trajectory')
    _STATE.update(arm=arm,seed=seed,last=None,nw=None);B=budget_for(key)
    try:a=S47.arm_active(w,seed,N,arm,S47.K,B)
    except VerificationError as e:
        if arm in N_ARMS and 'prefix masks differ' in str(e):
            a={'label':'WRONG','stop':'majority_error','error':str(e),'rounds':[],'conflicts_spent':0,'budget_conflicts':B,'wall_guard':0}
        else:raise
    res=_STATE['last']
    if res is not None and a.get('stop')!='majority_error':
        check(a['budget']==B and a['conflict_cap']==C50 and a['budget_conflicts']==B and res['max_chunks'] is None
              and res['api_result']['api']==(C16E.API if arm in E_ARMS else C16N.API),'050 caps not applied')
        check(len(res['rounds'])==len(a['rounds']),'round count')
        for rr,x in zip(a['rounds'],res['rounds']):
            check(rr['call_conflicts']==x['call_conflicts'],'round alignment')
            rr['call_chunks']=list(x['call_chunks']);rr['chunk_conflicts']=[list(y) for y in x['chunk_conflicts']]
            rr['chunk_walls_informational']=[list(y) for y in x['chunk_walls']]
        a['max_chunks']=res['max_chunks'];a['chunks_total']=res['chunks_total'];a['chunk_wall_max']=res['chunk_wall_max']
        a['case_wall_informational']=res['case_wall'];a['calls_total']=sum(len(x['call_conflicts']) for x in res['rounds'])
        if arm in N_ARMS:
            nw=_STATE['nw'];eps,reads=NOISE_OF[arm]
            tc=truth_codes(w,res['acts']);a['majority_errors']=sum(1 for m,t in zip(res['masks'],tc) if m!=1<<t)
            a.update(reads_per_obs=list(res['reads_per_obs']),votes=[list(v) for v in res['votes']],eps=eps,eps_bar=EPS_BAR,delta=DELTA,
                     reads=reads,reads_total=sum(res['reads_per_obs']),reads_max=max(res['reads_per_obs']),bits_flipped=nw.flipped,world_reads=nw.reads)
    return {'schema':SCHEMA_CASE,'key':key,'family':fam,'seed':seed,'eps':NOISE_OF[arm][0] if arm in N_ARMS else 0.0,'n':w.n,'k':w.k,'N':N,
            'group':arm,'arms':{arm:a},'truth_reachable':len(S47.canonical_bfs(w.transitions,w.emissions,w.start)[1])}


def seeds_of(plan,k):
    R=target_ranges(plan);return list(range(R[k][0],R[k][1]+1))


def jobs_for(plan,block):
    if block=='main':
        s20=seeds_of(plan,'scale20');n12=seeds_of(plan,'noise12');ct=seeds_of(plan,'control')
        out=[('main','scale20',s,'API16E') for s in s20]+[('main','scale20',s,'API16E_b') for s in reversed(s20[:N20B])]
        out+=[('main','noise12',s,'API16N') for s in n12]+[('main','noise12',s,'API16N_b') for s in reversed(n12[:N12B])]
        out+=[('main','control',s,g) for g in E_ARMS for s in ct]+[('c','control',s,'API16N_c') for s in ct]
        return out
    if block=='smoke':
        return ([('smoke',k,s,g) for k,s in SMOKE_FRESH for g in ARMS_OF[k]]
                +[('c','control',s,'API16N_c') for k,s in SMOKE_FRESH if k=='control'])
    raise ValueError(block)


def key(job):return ':'.join(str(x) for x in job)
def case_key(job):return f'{job[0]}:{job[1]}:{job[2]}'


def check_job(job,plan):
    b,k,s,g=job;check(g in ALL_ARMS and k in KEY_ORDER,'arm/key')
    if b=='c':
        check(g=='API16N_c' and k=='control','part c arm')
        if s>=SMOKE[0] and s<=SMOKE[1]:check_run_seeds('smoke',[s],plan)
        else:check_run_seeds('target',[s],plan,key='control')
        return
    check(g in ARMS_OF[k],'arm for key')
    if b=='main':
        check_run_seeds('target',[s],plan,key=k);sl=seeds_of(plan,k)
        if g=='API16E_b' and k=='scale20':sl=sl[:N20B]
        if g=='API16N_b':sl=sl[:N12B]
        check(s in sl,'case not in the declared (cut) list')
    elif b=='smoke':check_run_seeds('smoke',[s],plan)
    else:raise ValueError(b)


def run_job(job,plan):
    check_job(job,plan);t0=time.perf_counter();c=run_fresh(job[2],job[1],job[3])
    c['block']=job[0];c['job_wall_informational']=time.perf_counter()-t0;return key(job),c


def _job(x):return run_job(*x)


def _lab(c):
    return ' '.join(f'{a}={v["label"]}/{v["stop"]} g={v["wall_guard"]} ch={v.get("chunks_total")} cf={v["conflicts_spent"]}'
                    +(f' maj_err={v.get("majority_errors")} reads={v.get("reads_total")}' if a in N_ARMS else '') for a,v in c['arms'].items())


def run_jobs(jobs,plan,workers,ckpt,log=print):
    for j in jobs:check_job(j,plan)
    todo=[j for j in jobs if key(j) not in ckpt.done];log(f'{len(jobs)-len(todo)} cached, {len(todo)} to run',flush=True)
    with ProcessPoolExecutor(max(1,workers),max_tasks_per_child=1) as ex:
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
    rank={k:i for i,k in enumerate(KEY_ORDER)};order.sort(key=lambda ck:(cases[ck]['block']=='c',rank[cases[ck]['key']],cases[ck]['seed']))
    return [cases[ck] for ck in order]


def _write(output,plan,block,keys,cases,complete,extra):
    from brute.evaluation import no_time
    smoke=block!='main'
    result={'schema':SCHEMA,'plan':plan,'block':block,'smoke':smoke,'complete':complete,'job_keys':keys,'cases':cases,
            'conflict_cap':C50,'budget_conflicts':{'scale20':B20,'control':B12,'noise12':B12},
            'noise':{'eps_bar':EPS_BAR,'delta':DELTA,'arms':{k:list(v) for k,v in NOISE_OF.items()}},'n_scale20_b':N20B,'n_noise12_b':N12B,**extra}
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


def run(output,workers,block):
    output=Path(output);plan=load(PLAN)
    if block=='main':check_freeze()
    for nm in ('RESULTS.json','SCIENTIFIC.json','SEAL.json'):check(not (output/nm).exists(),'refusing overwrite '+str(output/nm))
    t0=time.perf_counter();jobs=jobs_for(plan,block)
    output.mkdir(parents=True,exist_ok=True);ck=Checkpoint(output/'CHECKPOINT.jsonl')
    if block=='main':check(not ck.done,'main checkpoint not empty: never resume (standing rule; resume clause not approved)')
    run_jobs(jobs,plan,workers,ck)
    _write(output,plan,block,[key(j) for j in jobs],merge(jobs,ck.done),True,{'total_elapsed_informational':time.perf_counter()-t0})


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--block',choices=('main','smoke'),default='main')
    ap.add_argument('--output');ap.add_argument('--workers',type=int,default=8)
    ap.add_argument('--seal-partial',action='store_true');ap.add_argument('--reason',default='study cap')
    a=ap.parse_args();out=a.output or str(STUDY_DIR/a.block)
    if a.block!='main':check(not Path(out).resolve().is_relative_to(STUDY_DIR.resolve()),'smoke output must not be inside results/study-050')
    if a.seal_partial:print('sealed partial',seal_partial(out,a.block,a.reason))
    else:run(out,a.workers,a.block);print('done')
