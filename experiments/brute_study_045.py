"""Study BRUTE-0420-A16-NFREE-STOP-045 runner (experiments/BRUTE_PLAN_045.json; pre-run deviation #163 fixes every definition
added here). New file built from experiments/brute_study_044.py (frozen) with the 045 ranges, keys and arms; brute.scalesearch16
(A16), brute.nfstop18 (A16_nf), experiments.worlds_043 (dispatch), StepWorld / passive / _truth_ok (033), label9 / _rec9 / _verd /
behaviour_equal (034), last_phase (040) and _calls_summary (041) are imported unchanged. Every SAT call runs in a per-job solver
child (experiments.solver_proxy_041) under HardHook: soft interrupt at the cap (or the case deadline if sooner), hard kill 1.0 s later.
Arms (plan design.arms): A16_N = A16 with declared bound N = the family size (16 / 3), cap 9.0 s, 240 s; A16_nf1 / A16_nf2 =
active18 with delta 1 / 2 (least search to the ceiling 16, rival searches n_min..n_min+delta), cap 9.0 s, 240 s; K = 128 in every
arm. A nf stop ID / IDF is the bounded claim ID_d / IDF_d (unique among machines with at most n_min+delta states). Every arm
record also carries future_match (the model from s1 behaves as the true machine from its true current state).
Main (fresh, eps 0): scale16 and control_cycle3 seeds from BRUTE_PLAN_045 heldout_ranges: 54 jobs, one per (case, arm), scale16
first, arms A16_nf2, A16_nf1, A16_N within a key, 8 workers.
Smoke (pre-freeze only, never gated; outside results/study-045): fresh arms on the plan's smoke range (scale16 x 4, control x 2);
replays (stop check only, A16_N) of the sealed 040 scale16 traces 10610001, 10610004, 10610008, 10610012; and two smoke-only probes
through the real nf code path: K = 0 and a 0.5 s case budget on the smoke control seed (+4) under A16_nf2.
  PYTHONPATH=. python experiments/brute_study_045.py --block main --workers 8
  PYTHONPATH=. python experiments/brute_study_045.py --block smoke --output /tmp/x --workers 8
"""
from __future__ import annotations
import argparse,time
from pathlib import Path
from time import perf_counter
from concurrent.futures import ProcessPoolExecutor,as_completed
from brute.region import codes_mask
from brute.scalesearch import canonical_bfs,simulate
from brute.scalesearch8 import run_word
from brute import scalesearch16 as S16
from brute import nfstop18 as N18
from experiments import worlds_043 as W
from experiments.brute_study_033 import StepWorld,passive,_truth_ok
from experiments.brute_study_034 import label9,_rec9,_verd,behaviour_equal
from experiments.brute_study_040 import last_phase
from experiments.brute_study_041 import _calls_summary
from experiments.brute_common_045 import (PLAN,FREEZE,STUDY_DIR,load,sha,write_new,check_freeze,check,Checkpoint,HardHook,
                                          SolverServer,sealed_cases,final_trace)
from scripts.check_seeds_045 import check_run_seeds,target_ranges,SMOKE,FAMILY_OF

M=1<<W.S_BITS;SOLVER4='g3';EPS=0.0
N_DECLARED=dict(W.SIZES)
KEY_ORDER=('scale16','control')
ARMS=('A16_N','A16_nf1','A16_nf2');DELTA={'A16_N':None,'A16_nf1':1,'A16_nf2':2};JOB_ORDER=('A16_nf2','A16_nf1','A16_N')
CAP={a:9.0 for a in ARMS};ARM_BUDGET={a:240.0 for a in ARMS}
Q_BOUND={a:CAP[a]+1.5 for a in ARMS}
check(N18.CEIL18==16 and N18.QUERY_S14==9.0 and S16.QUERY_S14==9.0 and S16.BUDGET14==240 and S16.K14==128,'frozen A16 constants')
SCHEMA_CASE='brute.case.v42_0';SCHEMA_REPLAY='brute.replay.v42_0'
K=S16.K14;BUDGET=S16.BUDGET14
SMOKE_KEYS=('scale16','scale16','scale16','scale16','control','control')
SMOKE_REPLAY=(10610001,10610004,10610008,10610012)
PROBES={'K0':('control',SMOKE[0]+4,0,BUDGET),'B05':('control',SMOKE[0]+4,K,0.5)}


def _active(arm,masks,acts,k,N,obs,deadline,Kc,H,srv,seed):
    if arm=='A16_N':return S16.active16(masks,acts,k,M,N,obs,deadline,Kc,CAP[arm],SOLVER4,H,srv.factory)
    if arm in ('A16_nf1','A16_nf2'):return N18.active18(masks,acts,k,M,DELTA[arm],obs,deadline,Kc,CAP[arm],SOLVER4,H,srv.factory)
    raise ValueError(arm)


def replay(seed,arm):
    case=sealed_cases('040')[('scale16',seed)];masks,acts=final_trace('040',case);srv=SolverServer();H=HardHook();t0=perf_counter()
    check(arm=='A16_N','replays run A16_N at the 9 s cap only')
    try:r=S16.stop_check16(masks,acts,case['k'],M,case['N'],t0+BUDGET,1,CAP[arm],SOLVER4,None,H,srv.factory)
    finally:srv.close()
    wall=r['query_walls'];sr=case['arms']['A14']['rounds'][-1];au=r['audit']
    return {'schema':SCHEMA_REPLAY,'study':'040','key':'scale16','seed':seed,'variant':arm,'repeat':0,'k':case['k'],'N':case['N'],
            'T':len(acts),'stop':r['stop'],'n_min':r['n_min'],'model':r['model'],'s1':r['s1'],'future':_verd(r['future']),
            'start':_verd(r['start']),'sealed':[sr['check'],sr['n_min']],'queries':len(wall),'capped':r['capped'],
            'query_walls':list(wall),'query_max_s':max(wall) if wall else None,'calls':au['calls'],'by_phase':_calls_summary(au['calls']),
            'clique':au.get('clique'),'pairs':au.get('pairs'),'cube':au.get('cube'),'kills':srv.kills,'child_starts':srv.starts,
            'kill_events':list(srv.events),'wall_informational':perf_counter()-t0,
            'model_consistent':None if r['model'] is None else bool(simulate(r['model'][0],r['model'][1],acts,masks)[0])}


def arm_active(w,seed,N,arm,Kc=K,budget=None):
    budget=ARM_BUDGET[arm] if budget is None else budget
    sw=StepWorld(w);masks,acts,_=passive(sw,seed);T0=len(acts);t0=perf_counter()
    obs=lambda a:codes_mask(sw.step(a),W.S_BITS);srv=SolverServer();H=HardHook()
    try:res=_active(arm,masks,acts,w.k,N,obs,t0+budget,Kc,H,srv,seed)
    finally:srv.close()
    fm,fa,f=res['masks'],res['acts'],res['final'];check(sw.steps==len(fa),'step count')
    rounds=[];wall=[q for x in res['rounds'] for q in x['query_walls']]
    for x in res['rounds']:
        T=x['T'];rr={'T':T,'n_min':x['n_min'],'check':x['check'],'bound':x.get('bound'),'queries':len(x['query_walls']),'capped':x['capped'],
                     'query_max_s':max(x['query_walls']) if x['query_walls'] else None,'future':_verd(x['future']),'start':_verd(x['start']),
                     'M1':x['M1'],'s1':x['s1'],'truth_consistent':bool(_truth_ok(w,fa[:T],fm[:T+1]))}
        if x['M1'] is not None:rr['M1_consistent']=bool(simulate(x['M1'][0],x['M1'][1],fa[:T],fm[:T+1])[0])
        if 'word' in x:
            (d1,e1),(d2,e2)=x['M1'],x['M2'];w_=x['word'];rr.update(word=w_,M2=x['M2'],s2=x['s2'])
            rr['M2_consistent']=bool(simulate(d2,e2,fa[:T],fm[:T+1])[0])
            p1=run_word(d1,e1,x['s1'],w_);p2=run_word(d2,e2,x['s2'],w_)
            rr['word_sound']=bool(('pred1' not in x or (p1==x['pred1'] and p2==x['pred2'])) and p1[:-1]==p2[:-1] and p1[-1]!=p2[-1])
            if 'obs' in x:
                rr['executed']=True;rr['obs']=x['obs'];rr['M1_survives']=bool(all(o>>c&1 for o,c in zip(x['obs'],p1)))
                rr['M2_survives']=bool(all(o>>c&1 for o,c in zip(x['obs'],p2)))
            else:rr['executed']=False
        rounds.append(rr)
    stop=res['stop'];lab=label9(stop,w,f['model']);capped=sum(x['capped'] for x in res['rounds']);au=res['audit']
    extra={'N':N,'K':Kc,'budget':budget,'used':res['used'],'rounds':rounds,'n_rounds':len(rounds),'extra_acts':fa[T0:],
           'extra_masks':fm[T0+1:],'words':[r.get('word') for r in rounds if r.get('executed')],
           'capped':capped,'capped_case':capped>0,'last_phase':last_phase(res['rounds'][-1]),
           'inc_guards':res['guards'],'inc_sizes':res['sizes'],'clique':res.get('clique'),'cube':res.get('cube'),'pairs':au.get('pairs'),
           'calls':au['calls'],'by_phase':_calls_summary(au['calls']),'kills':srv.kills,'child_starts':srv.starts,'kill_events':list(srv.events),
           'cap_s':CAP[arm],'delta':DELTA[arm],'bound':res.get('bound') if DELTA[arm] is not None else N,'ceil':res.get('ceil')}
    out=_rec9(w,f,fa,fm,lab,t0,stop,extra);out['query_max_s']=max(wall) if wall else None;out['queries']=len(wall)
    out['s1']=f.get('s1');q=w.start
    for a_ in fa:q=w.transitions[q][a_]
    m_=f['model'];out['truth_state_final']=q
    out['future_match']=bool(m_ is not None and f.get('s1') is not None and behaviour_equal(m_[0],m_[1],f['s1'],w.transitions,w.emissions,q))
    out['words_checked']=sum(1 for r in rounds if r.get('word'));out['words_unsound']=sum(1 for r in rounds if r.get('word') and not r['word_sound'])
    out['truth_inconsistent_rounds']=sum(1 for r in rounds if not r['truth_consistent'])
    return out


def run_fresh(seed,pkey,arm,Kc=K,budget=None):
    fam=FAMILY_OF[pkey];w=W.world(seed,fam);tr=W.trajectory(w,seed,EPS);sw=StepWorld(w);_,acts,rd=passive(sw,seed)
    check(rd==list(tr['readings']) and acts==list(tr['actions']),'prefix differs from worlds_026.trajectory')
    N=N_DECLARED[fam];check(w.n==N,'world size differs from the declared bound')
    if arm not in ARMS:raise ValueError(arm)
    return {'schema':SCHEMA_CASE,'key':pkey,'family':fam,'seed':seed,'eps':EPS,'n':w.n,'k':w.k,'N':N,'group':arm,
            'arms':{arm:arm_active(w,seed,N,arm,Kc,budget)},'truth_reachable':len(canonical_bfs(w.transitions,w.emissions,w.start)[1])}


def jobs_for(plan,block):
    if block=='main':
        R=target_ranges(plan);out=[]
        for k in KEY_ORDER:
            for g in JOB_ORDER:out+=[('main',k,s,g) for s in range(R[k][0],R[k][1]+1)]
        return out
    if block=='smoke':
        return ([('replay','smoke',s,'A16_N') for s in SMOKE_REPLAY]+[('probe',p,PROBES[p][1],'A16_nf2') for p in PROBES]
                +[('smoke',k,SMOKE[0]+i,g) for i,k in enumerate(SMOKE_KEYS) for g in ARMS])
    raise ValueError(block)


def key(job):return ':'.join(str(x) for x in job)


def case_key(job):return f'{job[0]}:{job[1]}:{job[2]}'


def check_job(job,plan):
    g=job[3];check(g in ARMS,'arm')
    if job[0]=='replay':check(job[1]=='smoke' and ('scale16',job[2]) in sealed_cases('040'),'sealed case');return
    if job[0]=='probe':check(job[1] in PROBES and PROBES[job[1]][1]==job[2],'probe');check_run_seeds('smoke',[job[2]],plan);return
    block,k,seed,_=job;check(k in KEY_ORDER,'key')
    if block=='main':check_run_seeds('target',[seed],plan,key=k)
    elif block=='smoke':check_run_seeds('smoke',[seed],plan)
    else:raise ValueError(block)


def run_job(job,plan):
    check_job(job,plan);t0=perf_counter()
    if job[0]=='replay':c=replay(job[2],job[3]);c['part']='smoke'
    elif job[0]=='probe':
        k,s,Kc,b=PROBES[job[1]];c=run_fresh(s,k,job[3],Kc,b);c['block']='probe';c['probe']=job[1]
    else:c=run_fresh(job[2],job[1],job[3]);c['block']=job[0]
    c['job_wall_informational']=perf_counter()-t0;return key(job),c


def _job(x):return run_job(*x)


def _lab(c):return c['stop'] if c['schema']==SCHEMA_REPLAY else ' '.join(f'{a}={v["label"]}/{v["stop"]}' for a,v in c['arms'].items())


def run_jobs(jobs,plan,workers,ckpt,log=print):
    for j in jobs:check_job(j,plan)
    todo=[j for j in jobs if key(j) not in ckpt.done];log(f'{len(jobs)-len(todo)} cached, {len(todo)} to run',flush=True)
    with ProcessPoolExecutor(max(1,workers)) as ex:
        futs=[ex.submit(_job,(j,plan)) for j in todo]
        for n,fu in enumerate(as_completed(futs)):
            k_,c=fu.result();ckpt.add(k_,c)
            log(f'done {n+1}/{len(todo)} {k_} {c["job_wall_informational"]:.1f}s {_lab(c)}',flush=True)
    return [ckpt.done[key(j)] for j in jobs]


def merge(jobs,done):
    """Replay records one per job (job order); fresh and probe records one per case, arms merged in ARMS order."""
    reps=[];cases={};order=[]
    for j in jobs:
        if key(j) not in done:continue
        g=done[key(j)]
        if j[0]=='replay':reps.append(g);continue
        ck=case_key(j)
        if ck not in cases:
            cases[ck]={x:g[x] for x in ('schema','key','family','seed','eps','n','k','N','truth_reachable','block')};cases[ck]['arms']={}
            if 'probe' in g:cases[ck]['probe']=g['probe']
            cases[ck]['group_walls_informational']={};order.append(ck)
        check(all(cases[ck][x]==g[x] for x in ('family','seed','n','k','N','truth_reachable')),'group records disagree: '+ck)
        cases[ck]['arms'].update(g['arms']);cases[ck]['group_walls_informational'][j[3]]=g['job_wall_informational']
    for c in cases.values():c['arms']={a:c['arms'][a] for a in ARMS if a in c['arms']}
    rank={k:i for i,k in enumerate(KEY_ORDER)};order.sort(key=lambda ck:(cases[ck]['block']=='probe',rank[cases[ck]['key']],cases[ck]['seed']))
    return reps,[cases[ck] for ck in order]


def _write(output,plan,block,keys,merged,complete,extra):
    from brute.evaluation import no_time
    reps,cases=merged;smoke=block!='main'
    result={'schema':'brute.study.v42_0','plan':plan,'block':block,'smoke':smoke,'complete':complete,'job_keys':keys,'replays':reps,
            'cases':cases,**extra}
    write_new(output/'RESULTS.json',result);write_new(output/'SCIENTIFIC.json',no_time(result))
    write_new(output/'SEAL.json',{'study':plan['study'],'block':block,'results_sha256':sha(output/'RESULTS.json'),
        'scientific_sha256':sha(output/'SCIENTIFIC.json'),'plan_sha256':sha(PLAN),'freeze_sha256':None if smoke else sha(FREEZE),
        'case_count':len(cases),'replay_count':len(reps),'job_count':len(keys),'complete':complete,'smoke':smoke,
        **({'missing_job_keys':extra['missing_job_keys']} if 'missing_job_keys' in extra else {})})


def seal_partial(output,block,reason='study cap',extra_checkpoint=None):
    import json
    output=Path(output);plan=load(PLAN)
    for nm in ('RESULTS.json','SCIENTIFIC.json','SEAL.json'):check(not (output/nm).exists(),'refusing overwrite '+str(output/nm))
    jobs=jobs_for(plan,block);ck=Checkpoint(output/'CHECKPOINT.jsonl');keys=[key(j) for j in jobs]
    done=dict(ck.done);src={'local':len(done),'snapshot_only':0}
    if extra_checkpoint:
        ex=Checkpoint(extra_checkpoint)
        for k_,c in ex.done.items():
            if k_ in done:check(json.dumps(done[k_],sort_keys=True)==json.dumps(c,sort_keys=True),'snapshot differs from local: '+k_)
            else:done[k_]=c;src['snapshot_only']+=1
    missing=[k for k in keys if k not in done]
    _write(output,plan,block,keys,merge(jobs,done),False,{'stop_reason':reason,'missing_job_keys':missing,'case_sources':src})
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
    ap.add_argument('--seal-partial',action='store_true');ap.add_argument('--snapshot');ap.add_argument('--reason',default='study cap')
    a=ap.parse_args();out=a.output or str(STUDY_DIR/a.block)
    if a.block!='main':check(not Path(out).resolve().is_relative_to(STUDY_DIR.resolve()),'smoke output must not be inside results/study-045')
    if a.seal_partial:print('sealed partial',seal_partial(out,a.block,a.reason,a.snapshot))
    else:run(out,a.workers,a.block);print('done')
