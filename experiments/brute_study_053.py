"""Study BRUTE-0500-NOISE16-SCALE20-CONFLICTSTOP-053 runner (experiments/BRUTE_PLAN_053.json; pre-run deviation #179 fixes every
definition added here). New file. The frozen 047 runner experiments/brute_study_047.py is imported, never edited: its arm_active and
record builders are used unchanged. The frozen 051 runner is imported only for its pure canon / BFS / truth helpers (canon16e,
canon16n, machine_canon, _bfs, truth_codes, _drive). Runtime rebinding in this process and every worker only (as 048-052):
S47.caps -> the job's (C, B) from CAPS_OF, S47.ARMS / D_ARMS gain the 053 arms, S47._api16d -> _api (certify/16e or certify/16n
through their public interfaces). certify/16n (FREEZE_050), certify/16e (FREEZE_049) and certify/16s (FREEZE_051) are unchanged.
Parts (plan design.parts):
  A noise16: 12 fresh clean 16-state worlds (worlds_043 'scale16' via worlds_050.world) through worlds_050.NoisyStepWorld at eps
           0.05, API16N16 and API16N16_b (certify/16n, eps_bar 0.10, delta 0.001, anytime k rule), family_bound 16, C 50000, B16N 1500000;
  A noise16_bar: the first N16BAR of 6 fresh worlds at eps 0.10 (= eps_bar), API16N16_bar once, same caps;
  A compat16: 6 fresh clean controls, API16N16_c (certify/16n at eps 0, reads 1) and API16E (certify/16e at bound 16), C 50000, B16 3000000;
  B scale20c: the first N20C of 6 fresh clean 20-state worlds (worlds_047 'scale20'), API16E20 and API16E20_b (certify/16e at bound
           20, C20 50000, B20 2000000), conflict-only stop (hook None, case guard = 900 s hard kill), all jobs serial on 1 worker.
One phase: a 1-worker pool for part B and a 7-worker pool for part A run concurrently; one process.
Cut rule (plan runtime_estimate, applied at the pre-freeze projection only, fixed in #179 before the freeze): N20C 6 -> 3 if the
projected part B exceeds 3300 s; N16BAR 6 -> 3 if the projected part A exceeds 3300 s; never noise16 or compat16.
Smoke (pre-freeze only, never gated; outside results/study-053): 12130001-02 noise16 (both passes), 12130003-04 noise16_bar,
12130005 compat16 (both arms), 12130006 scale20c (both passes, part B pool).
  PYTHONPATH=. python experiments/brute_study_053.py --block main
  PYTHONPATH=. python experiments/brute_study_053.py --block smoke --output /tmp/x
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
from brute.api import certify16n as C16N
from experiments.brute_common import dumps,VerificationError
from experiments.brute_common_053 import (PLAN,FREEZE,STUDY_DIR,load,sha,write_new,check_freeze,check,Checkpoint,CAPS_OF,caps_for,
                                          EPS_BAR,DELTA,NOISE_OF,E_ARMS,B_ARMS,N_ARMS,ALL_ARMS,WORKERS,WORKERS_A,WORKERS_B,
                                          PART_B_KEYS,HARD_KILL_B_S,STOP_RULE)
from scripts.check_seeds_053 import check_run_seeds,target_ranges,SMOKE,FAMILY_OF

canon16e=S51.canon16e;canon16n=S51.canon16n;machine_canon=S51.machine_canon;_bfs=S51._bfs;truth_codes=S51.truth_codes;_drive=S51._drive
S47.caps=lambda:CAPS_OF['compat16']   # rebound per job in run_fresh (each job runs in its own worker process)
S47.ARMS=tuple(S47.ARMS)+ALL_ARMS;S47.D_ARMS=tuple(S47.D_ARMS)+ALL_ARMS
N16BAR=6    # declared cut rule: 6 -> 3 only if projected part A > 3300 s; fixed in #179 before the freeze
N20C=3      # declared cut rule: 6 -> 3 if projected part B > 3300 s (plan worst case 5448 s at 4503 c/s); fixed in #179 before the freeze
CUT_STEPS=(6,3);CUT_CAP_S=3300.0
KEY_ORDER=('noise16','noise16_bar','compat16','scale20c')
ARMS_OF={'noise16':('API16N16','API16N16_b'),'noise16_bar':('API16N16_bar',),'compat16':('API16N16_c','API16E'),'scale20c':B_ARMS}
SCHEMA='brute.study.v50_0';SCHEMA_CASE='brute.case.v50_0'
SMOKE_FRESH=(('noise16',SMOKE[0]),('noise16',SMOKE[0]+1),('noise16_bar',SMOKE[0]+2),('noise16_bar',SMOKE[0]+3),('compat16',SMOKE[0]+4),('scale20c',SMOKE[0]+5))
_STATE={'arm':None,'seed':None,'last':None,'nw':None}


def api_of(arm):return C16E.API if arm in E_ARMS else C16N.API
def part_of(key):return 'B' if key in PART_B_KEYS else 'A'


def _api(rd,acts,k,N,sw,Kc,C,B,H):
    """certify/16e (API16E, API16E20 arms) or certify/16n (API16N16 arms) through their public interfaces only (as 050-052).
    Part B arms: conflict-only stop, hook None (no wall interrupt) and the case guard at the 900 s hard kill."""
    arm=_STATE['arm'];pb=arm in B_ARMS
    kw=dict(max_chunks=None,K=Kc,conflict_cap=C,budget_conflicts=B,wall_guard_case_s=HARD_KILL_B_S if pb else S47.GUARD_CASE_S,
            wall_guard_call_s=S47.GUARD_CALL_S,solver=S47.SOLVER4,hook=None if pb else H,factory=C16E.counted16d)
    if arm in E_ARMS:
        c=C16E.Certifier16E(rd[0],k,N,'a16d',**kw)
        try:_drive(c,rd,acts,sw);res=dict(c.record())
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


def canon_for(arm):return canon16e if arm in E_ARMS else canon16n


def run_fresh(seed,key,arm):
    fam=FAMILY_OF[key];w=W50.world(seed,fam);N=W50.SIZES[fam];check(w.n==N,'world size differs from the declared bound')
    tr=trajectory(w,seed,0.0);_,acts,rd=passive(StepWorld(w),seed)
    check(rd==list(tr['readings']) and acts==list(tr['actions']),'prefix differs from worlds_026.trajectory')
    _STATE.update(arm=arm,seed=seed,last=None,nw=None);C,B=caps_for(key);S47.caps=lambda:(C,B)
    try:a=S47.arm_active(w,seed,N,arm,S47.K,B)
    except VerificationError as e:
        if arm in N_ARMS and 'prefix masks differ' in str(e):
            a={'label':'WRONG','stop':'majority_error','error':str(e),'rounds':[],'conflicts_spent':0,'budget_conflicts':B,'wall_guard':0}
        else:raise
    res=_STATE['last']
    if res is not None and a.get('stop')!='majority_error':
        check(a['budget']==B and a['conflict_cap']==C and a['budget_conflicts']==B and res['max_chunks'] is None
              and res['api_result']['api']==api_of(arm),'053 caps not applied')
        check(len(res['rounds'])==len(a['rounds']),'round count')
        for rr,x in zip(a['rounds'],res['rounds']):
            check(rr['call_conflicts']==x['call_conflicts'],'round alignment')
            rr['call_chunks']=list(x['call_chunks']);rr['chunk_conflicts']=[list(y) for y in x['chunk_conflicts']]
            rr['chunk_walls_informational']=[list(y) for y in x['chunk_walls']]
        a['max_chunks']=res['max_chunks'];a['chunks_total']=res['chunks_total'];a['chunk_wall_max']=res['chunk_wall_max']
        a['case_wall_informational']=res['case_wall'];a['calls_total']=sum(len(x['call_conflicts']) for x in res['rounds'])
        a['part']=part_of(key);a['stop_rule']=STOP_RULE[part_of(key)]
        if arm in B_ARMS:check(a['hook_arms']==0,'part B: a wall hook was armed (conflict-only stop violated)');a['hard_kill_s']=HARD_KILL_B_S
        if arm in N_ARMS:
            nw=_STATE['nw'];eps,reads=NOISE_OF[arm]
            tc=truth_codes(w,res['acts']);a['majority_errors']=sum(1 for m,t in zip(res['masks'],tc) if m!=1<<t)
            a.update(reads_per_obs=list(res['reads_per_obs']),votes=[list(v) for v in res['votes']],eps=eps,eps_bar=EPS_BAR,noise_delta=DELTA,
                     reads=reads,reads_total=sum(res['reads_per_obs']),reads_max=max(res['reads_per_obs']),bits_flipped=nw.flipped,world_reads=nw.reads)
    return {'schema':SCHEMA_CASE,'key':key,'family':fam,'seed':seed,'eps':NOISE_OF[arm][0] if arm in N_ARMS else 0.0,'n':w.n,'k':w.k,'N':N,
            'group':arm,'arms':{arm:a},'truth_reachable':len(S47.canonical_bfs(w.transitions,w.emissions,w.start)[1])}


def seeds_of(plan,k):
    R=target_ranges(plan);return list(range(R[k][0],R[k][1]+1))


def declared_list(plan,k):
    sl=seeds_of(plan,k)
    return sl[:N16BAR] if k=='noise16_bar' else sl[:N20C] if k=='scale20c' else sl


def jobs_for(plan,block):
    if block=='main':
        n16=seeds_of(plan,'noise16');nb=declared_list(plan,'noise16_bar');cp=seeds_of(plan,'compat16');s20=declared_list(plan,'scale20c')
        out=[('main','scale20c',s,'API16E20') for s in s20]+[('main','scale20c',s,'API16E20_b') for s in s20]
        out+=[('main','compat16',s,g) for g in ARMS_OF['compat16'] for s in cp]
        out+=[('main','noise16',s,'API16N16') for s in n16]+[('main','noise16',s,'API16N16_b') for s in reversed(n16)]
        out+=[('main','noise16_bar',s,'API16N16_bar') for s in nb]
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
    return ' '.join(f'{a}={v["label"]}/{v["stop"]} g={v["wall_guard"]} ch={v.get("chunks_total")} cf={v["conflicts_spent"]}'
                    +(f' maj_err={v.get("majority_errors")} reads={v.get("reads_total")}' if a in N_ARMS else '') for a,v in c['arms'].items())


def run_jobs(jobs,plan,ckpt,log=print):
    """Part B jobs on a dedicated 1-worker pool (serial, in list order), part A jobs on a 7-worker pool, both submitted at once."""
    for j in jobs:check_job(j,plan)
    todo=[j for j in jobs if key(j) not in ckpt.done];tb=[j for j in todo if part_of(j[1])=='B'];ta=[j for j in todo if part_of(j[1])=='A']
    log(f'{len(jobs)-len(todo)} cached, {len(todo)} to run: part B {len(tb)} on {WORKERS_B} worker, part A {len(ta)} on {WORKERS_A} workers',flush=True)
    with ProcessPoolExecutor(WORKERS_B,max_tasks_per_child=1) as eb,ProcessPoolExecutor(WORKERS_A,max_tasks_per_child=1) as ea:
        futs=[eb.submit(_job,(j,plan)) for j in tb]+[ea.submit(_job,(j,plan)) for j in ta]
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
            'caps':{k:list(v) for k,v in CAPS_OF.items()},'workers':{'total':WORKERS,'A':WORKERS_A,'B':WORKERS_B},
            'noise':{'eps_bar':EPS_BAR,'delta':DELTA,'arms':{k:list(v) for k,v in NOISE_OF.items()}},
            'part_b':{'keys':list(PART_B_KEYS),'hard_kill_s':HARD_KILL_B_S,'stop_rule':STOP_RULE['B']},
            'n_noise16_bar':N16BAR,'n_scale20c':N20C,**extra}
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
    if block=='main':fz=check_freeze();check(fz.get('n_noise16_bar')==N16BAR and fz.get('n_scale20c')==N20C,'cut variables differ from the freeze')
    for nm in ('RESULTS.json','SCIENTIFIC.json','SEAL.json'):check(not (output/nm).exists(),'refusing overwrite '+str(output/nm))
    t0=time.perf_counter();jobs=jobs_for(plan,block)
    output.mkdir(parents=True,exist_ok=True);ck=Checkpoint(output/'CHECKPOINT.jsonl')
    if block=='main':check(not ck.done,'main checkpoint not empty: never resume (standing rule; resume clause not approved)')
    run_jobs(jobs,plan,ck)
    _write(output,plan,block,[key(j) for j in jobs],merge(jobs,ck.done),True,{'total_elapsed_informational':time.perf_counter()-t0})


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--block',choices=('main','smoke'),default='main')
    ap.add_argument('--output');ap.add_argument('--seal-partial',action='store_true');ap.add_argument('--reason',default='study cap')
    a=ap.parse_args();out=a.output or str(STUDY_DIR/a.block)
    if a.block!='main':check(not Path(out).resolve().is_relative_to(STUDY_DIR.resolve()),'smoke output must not be inside results/study-053')
    if a.seal_partial:print('sealed partial',seal_partial(out,a.block,a.reason))
    else:run(out,a.block);print('done')
