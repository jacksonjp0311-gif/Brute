"""Study BRUTE-0450-CERTIFY16D-WALLFREE-SCALE20-048 runner (experiments/BRUTE_PLAN_048.json; pre-run deviation #169 fixes every
definition added here). New file. The 047 runner experiments/brute_study_047.py (frozen) is imported, never edited: its
arm_active / run_fresh / run_replay / canon16d / classify are used unchanged; the only runtime change is that its caps() name is
bound to the plan-048 fixed caps (C 50000, B16 1500000) in this process and in every forked worker, and scale20 cases pass
B20 = 1000000 explicitly. No calibration file is read.
Arms (plan design.arms): API16D (brute.api.certify16d through its public interface, K 128, g3, declared N = 16 / 3 / 20, the
host wall guard TimerHook at the certify/16d defaults 30 s per call, 600 s per case) and API16D_b (the same arm, a second
independent pass, its jobs queued after every API16D job, in reverse case order).
Main (52 + 18 = 70 jobs at N20 = 8): part a_fresh16 scale16 x 12 and control x 6, part d_scale20 scale20 x N20 (the declared
step-down 8 -> 6 -> 4 -> 0 fixes N20 before the freeze), each by API16D and API16D_b; part r: API16D replays of the 18 sealed
046 fresh traces (block 'r'; compared with the sealed A16_N record and classified).
Smoke (pre-freeze only, never gated; outside results/study-048): 11590001-02 scale16, 11590003-04 scale20, 11590005-06 control,
each by API16D and API16D_b, plus one part-r replay of sealed 046 scale16 11230004 (a 047 guard firing).
  PYTHONPATH=. python experiments/brute_study_048.py --block main --workers 8
  PYTHONPATH=. python experiments/brute_study_048.py --block smoke --output /tmp/x --workers 8
"""
from __future__ import annotations
import argparse,time
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor,as_completed
from experiments import brute_study_047 as S47
from experiments.brute_common import dumps
from experiments.brute_common_048 import (PLAN,FREEZE,STUDY_DIR,load,sha,write_new,check_freeze,check,Checkpoint,C48,B16,B20,budget_for)
from scripts.check_seeds_048 import check_run_seeds,target_ranges,SMOKE

S47.caps=lambda:(C48,B16)          # plan 048 cap_rule (fixed); scale20 passes B20 explicitly
N20=8      # declared step-down (plan runtime_estimate): 8, else 6, else 4, else 0 (part d dropped), fixed in #169 before the freeze
KEY_ORDER=('scale16','control','scale20');ARMS=('API16D','API16D_b')
canon16d=S47.canon16d;classify=S47.classify
SCHEMA='brute.study.v45_0'
REPLAY_SEEDS={'scale16':tuple(range(11230001,11230013)),'control':tuple(range(11270001,11270007))}
SMOKE_FRESH=tuple((k,SMOKE[0]+i) for k,i in (('scale16',0),('scale16',1),('scale20',2),('scale20',3),('control',4),('control',5)))
SMOKE_REPLAY=(('scale16',11230004),)


def seeds_of(plan,k):
    R=target_ranges(plan);s=list(range(R[k][0],R[k][1]+1))
    return s[:N20] if k=='scale20' else s


def run_fresh(seed,k,arm):
    c=S47.run_fresh(seed,k,arm,S47.K,budget_for(k));check(c['arms'][arm]['budget']==budget_for(k)
        and c['arms'][arm]['conflict_cap']==C48 and c['arms'][arm]['budget_conflicts']==budget_for(k),'048 caps not applied')
    c['schema']='brute.case.v45_0';return c


def run_replay(k,seed):
    c=S47.run_replay('a3_046',k,seed);a=c['arms']['API16D']
    check(a['conflict_cap']==C48 and a['budget_conflicts']==B16,'048 caps not applied (replay)');c['schema']='brute.case.v45_0';return c


def jobs_for(plan,block):
    if block=='main':
        out=[('main','scale20',s,'API16D') for s in seeds_of(plan,'scale20')]+[('main','scale16',s,'API16D') for s in seeds_of(plan,'scale16')]
        out+=[('r',k,s,'API16D') for k in ('scale16','control') for s in REPLAY_SEEDS[k]]
        out+=[('main','control',s,'API16D') for s in seeds_of(plan,'control')]
        out+=[('main',k,s,'API16D_b') for k in ('scale20','scale16','control') for s in reversed(seeds_of(plan,k))]
        return out
    if block=='smoke':
        return [('r',k,s,'API16D') for k,s in SMOKE_REPLAY]+[('smoke',k,s,g) for g in ARMS for k,s in SMOKE_FRESH]
    raise ValueError(block)


def key(job):return ':'.join(str(x) for x in job)
def case_key(job):return f'{job[0]}:{job[1]}:{job[2]}'


def check_job(job,plan):
    b,k,s,g=job;check(g in ARMS and k in KEY_ORDER,'arm/key')
    if b=='r':check(g=='API16D' and k in REPLAY_SEEDS and s in REPLAY_SEEDS[k],'sealed 046 case');return
    if b=='main':check_run_seeds('target',[s],plan,key=k);check(s in seeds_of(plan,k),'case not in the declared (stepped-down) list')
    elif b=='smoke':check_run_seeds('smoke',[s],plan)
    else:raise ValueError(b)


def run_job(job,plan):
    check_job(job,plan);t0=time.perf_counter()
    if job[0]=='r':c=run_replay(job[1],job[2]);c['part']='r'
    else:c=run_fresh(job[2],job[1],job[3])
    c['block']=job[0];c['job_wall_informational']=time.perf_counter()-t0;return key(job),c


def _job(x):return run_job(*x)


def _lab(c):
    s=' '.join(f'{a}={v["label"]}/{v["stop"]} g={v["wall_guard"]}' for a,v in c['arms'].items())
    return s+(f" class={c['replay']['class']}" if 'replay' in c else '')


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
        if j[0]=='r':reps.append(g);continue
        ck=case_key(j)
        if ck not in cases:
            cases[ck]={x:g[x] for x in ('schema','key','family','seed','eps','n','k','N','truth_reachable','block')};cases[ck]['arms']={}
            cases[ck]['group_walls_informational']={};order.append(ck)
        check(all(cases[ck][x]==g[x] for x in ('family','seed','n','k','N','truth_reachable')),'group records disagree: '+ck)
        cases[ck]['arms'].update(g['arms']);cases[ck]['group_walls_informational'][j[3]]=g['job_wall_informational']
    for c in cases.values():c['arms']={a:c['arms'][a] for a in ARMS if a in c['arms']}
    rank={k:i for i,k in enumerate(KEY_ORDER)};order.sort(key=lambda ck:(rank[cases[ck]['key']],cases[ck]['seed']))
    reps.sort(key=lambda r:(r['key'],r['seed']))
    return reps,[cases[ck] for ck in order]


def _write(output,plan,block,keys,merged,complete,extra):
    from brute.evaluation import no_time
    reps,cases=merged;smoke=block!='main'
    result={'schema':SCHEMA,'plan':plan,'block':block,'smoke':smoke,'complete':complete,'job_keys':keys,'replays':reps,'cases':cases,
            'conflict_cap':C48,'budget_conflicts':{'scale16':B16,'control':B16,'scale20':B20},'n_scale20':N20,**extra}
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
    if a.block!='main':check(not Path(out).resolve().is_relative_to(STUDY_DIR.resolve()),'smoke output must not be inside results/study-048')
    if a.seal_partial:print('sealed partial',seal_partial(out,a.block,a.reason))
    else:run(out,a.workers,a.block);print('done')
