"""Study BRUTE-0380-ENC-AUDIT-041 runner (experiments/BRUTE_PLAN_041.json; deviation #154 fixes every definition added
here). New file; brute.encaudit16 (variants E0-E4 and the frozen arms through them), StepWorld / passive / _truth_ok
(experiments.brute_study_033), label9 / _rec9 / _verd (experiments.brute_study_034) and last_phase (experiments.brute_study_040)
are imported unchanged.

Every SAT call runs in a per-job solver child (experiments.solver_proxy_041) under HardHook: soft interrupt at the query cap
(QUERY_S14 = 9.0 s, or the case deadline if sooner), hard kill 1.0 s later. GQB16 bound 10.5 s.
Part 1 (replay; no world is stepped): stop_check_audit(variant) on a sealed final A14 trace, n_lo = 1, deadline = start +
240 s, declared bound N = the case's N:
  a  the 30 sealed study-039 cases (scale12, perm12, control) whose A14 stop was decided, x E0-E4, once;
  b  sealed study-039 perm12 10540007 and 10540008 x E0-E4 x repeats 0, 1, 2 (declared repeats, not reruns);
  c  the 12 sealed study-040 scale16 cases x E0-E4, once.
Part 2 (fresh, eps 0): arms A14 / A15 / A15_cube = active_audit(E0 / E3 / E4), K = 128, 240 s, on perm12 10710001-12 and
control_cycle3 10760001-06 (worlds_039); labels as study-040 (label9).
Smoke (pre-freeze only, never gated): fresh arms on 10780001-06 (perm12 x 4, control x 2) and replays of the sealed study-039
scale14 traces 10520001, 10520002 x E0-E4 (traces outside part 1).
Jobs: one per (replay trace, variant, repeat) or (fresh case, arm); dispatched part c, b, a, then fresh (longest first) on 8
workers; the checkpoint holds one line per job; RESULTS keeps one record per job (replay) and per case (fresh, arms merged).
  PYTHONPATH=. python experiments/brute_study_041.py --block main --workers 8
  PYTHONPATH=. python experiments/brute_study_041.py --block smoke --output /tmp/x --workers 8
"""
from __future__ import annotations
import argparse,json,time
from pathlib import Path
from time import perf_counter
from concurrent.futures import ProcessPoolExecutor,as_completed
from brute.region import codes_mask
from brute.scalesearch import canonical_bfs,simulate
from brute.scalesearch8 import run_word
from brute import encaudit16 as EA
from experiments import worlds_039 as W
from experiments.brute_study_033 import StepWorld,passive,_truth_ok
from experiments.brute_study_034 import label9,_rec9,_verd
from experiments.brute_study_040 import last_phase
from experiments.brute_common_041 import (PLAN,FREEZE,STUDY_DIR,load,sha,write_new,check_freeze,check,Checkpoint,HardHook,
                                          SolverServer,sealed_cases,final_trace)
from scripts.check_seeds_041 import check_run_seeds,target_ranges,SMOKE,FAMILY_OF

M=1<<W.S_BITS;SOLVER4='g3';EPS=0.0;QUERY_S=EA.QUERY_S14;Q_BOUND=10.5
N_DECLARED=dict(W.SIZES)
KEY_ORDER=('perm12','control')
ARMS=('A14','A15','A15_cube')
VARIANTS=EA.VARIANTS
SCHEMA_CASE='brute.case.v38_0';SCHEMA_REPLAY='brute.replay.v38_0'
K=EA.K14;BUDGET=EA.BUDGET14
SMOKE_KEYS=('perm12','perm12','perm12','perm12','control','control')
GINC=(10540007,10540008);REPEATS=3
SMOKE_REPLAY=(('039','scale14',10520001),('039','scale14',10520002))


def part_a():
    cs=[c for c in sealed_cases('039').values() if c['key'] in ('scale12','perm12','control') and c['arms']['A14']['stop']!='unknown']
    cs.sort(key=lambda c:(('scale12','perm12','control').index(c['key']),c['seed']));check(len(cs)==30,'part a: 30 cases');return [('039',c['key'],c['seed']) for c in cs]


def part_b():return [('039','perm12',s) for s in GINC]


def part_c():
    cs=sorted(s for (k,s) in sealed_cases('040') if k=='scale16');check(len(cs)==12,'part c: 12 cases');return [('040','scale16',s) for s in cs]


def _calls_summary(calls):
    by={}
    for c in calls:
        b=by.setdefault(c['phase'],{'calls':0,'capped':0,'wall':0.0,'max_wall':0.0});b['calls']+=1;b['capped']+=c['capped'];b['wall']+=c['wall']
        b['max_wall']=max(b['max_wall'],c['wall'])
    return by


def replay(study,key,seed,variant,rep):
    case=sealed_cases(study)[(key,seed)];masks,acts=final_trace(study,case);srv=SolverServer();H=HardHook();t0=perf_counter()
    try:r=EA.stop_check_audit(variant,masks,acts,case['k'],M,case['N'],t0+BUDGET,1,QUERY_S,SOLVER4,None,H,srv.factory)
    finally:srv.close()
    wall=r['query_walls'];sr=case['arms']['A14']['rounds'][-1];au=r['audit']
    return {'schema':SCHEMA_REPLAY,'study':study,'key':key,'seed':seed,'variant':variant,'repeat':rep,'k':case['k'],'N':case['N'],
            'T':len(acts),'stop':r['stop'],'n_min':r['n_min'],'model':r['model'],'s1':r['s1'],'future':_verd(r['future']),
            'start':_verd(r['start']),'sealed':[sr['check'],sr['n_min']],'queries':len(wall),'capped':r['capped'],
            'query_walls':list(wall),'query_max_s':max(wall) if wall else None,'calls':au['calls'],'by_phase':_calls_summary(au['calls']),
            'clique':au.get('clique'),'pairs':au.get('pairs'),'cube':au.get('cube'),'kills':srv.kills,'child_starts':srv.starts,
            'kill_events':list(srv.events),'wall_informational':perf_counter()-t0,
            'model_consistent':None if r['model'] is None else bool(simulate(r['model'][0],r['model'][1],acts,masks)[0])}


def arm_active(w,seed,N,arm):
    sw=StepWorld(w);masks,acts,_=passive(sw,seed);T0=len(acts);t0=perf_counter()
    obs=lambda a:codes_mask(sw.step(a),W.S_BITS);srv=SolverServer();H=HardHook()
    try:res=EA.active_audit(EA.ARM_VARIANT[arm],masks,acts,w.k,M,N,obs,t0+BUDGET,K,QUERY_S,SOLVER4,H,srv.factory)
    finally:srv.close()
    fm,fa,f=res['masks'],res['acts'],res['final'];check(sw.steps==len(fa),'step count')
    rounds=[];wall=[q for x in res['rounds'] for q in x['query_walls']]
    for x in res['rounds']:
        T=x['T'];rr={'T':T,'n_min':x['n_min'],'check':x['check'],'queries':len(x['query_walls']),'capped':x['capped'],
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
    extra={'N':N,'K':K,'budget':BUDGET,'used':res['used'],'rounds':rounds,'n_rounds':len(rounds),'extra_acts':fa[T0:],
           'extra_masks':fm[T0+1:],'words':[r.get('word') for r in rounds if r.get('executed')],
           'capped':capped,'capped_case':capped>0,'last_phase':last_phase(res['rounds'][-1]),
           'inc_guards':res['guards'],'inc_sizes':res['sizes'],'clique':res.get('clique'),'cube':res.get('cube'),
           'calls':au['calls'],'by_phase':_calls_summary(au['calls']),'kills':srv.kills,'child_starts':srv.starts,'kill_events':list(srv.events)}
    out=_rec9(w,f,fa,fm,lab,t0,stop,extra);out['query_max_s']=max(wall) if wall else None;out['queries']=len(wall)
    out['words_checked']=sum(1 for r in rounds if r.get('word'));out['words_unsound']=sum(1 for r in rounds if r.get('word') and not r['word_sound'])
    out['truth_inconsistent_rounds']=sum(1 for r in rounds if not r['truth_consistent'])
    return out


def run_fresh(seed,pkey,arm):
    fam=FAMILY_OF[pkey];w=W.world(seed,fam);tr=W.trajectory(w,seed,EPS);sw=StepWorld(w);_,acts,rd=passive(sw,seed)
    check(rd==list(tr['readings']) and acts==list(tr['actions']),'prefix differs from worlds_026.trajectory')
    N=N_DECLARED[fam];check(w.n==N,'world size differs from the declared bound')
    if arm not in ARMS:raise ValueError(arm)
    return {'schema':SCHEMA_CASE,'key':pkey,'family':fam,'seed':seed,'eps':EPS,'n':w.n,'k':w.k,'N':N,'group':arm,
            'arms':{arm:arm_active(w,seed,N,arm)},'truth_reachable':len(canonical_bfs(w.transitions,w.emissions,w.start)[1])}


def jobs_for(plan,block):
    if block=='main':
        R=target_ranges(plan);out=[]
        for part,tr,reps in (('c',part_c(),1),('b',part_b(),REPEATS),('a',part_a(),1)):
            for (st,k,s) in tr:
                for v in VARIANTS:
                    for rep in range(reps):out.append(('replay',part,st,k,s,v,rep))
        return out+[('main',k,s,g) for g in ARMS for k in KEY_ORDER for s in range(R[k][0],R[k][1]+1)]
    if block=='smoke':
        return ([('replay','smoke',st,k,s,v,0) for (st,k,s) in SMOKE_REPLAY for v in VARIANTS]
                +[('smoke',k,SMOKE[0]+i,g) for g in ARMS for i,k in enumerate(SMOKE_KEYS)])
    raise ValueError(block)


def key(job):return ':'.join(str(x) for x in job)


def case_key(job):return f'{job[0]}:{job[1]}:{job[2]}'


def check_job(job,plan):
    if job[0]=='replay':
        _,part,st,k,s,v,rep=job;check(v in VARIANTS,'variant');check(st in ('039','040'),'study');check((k,s) in sealed_cases(st),'sealed case')
        check(part in ('a','b','c','smoke'),'part');return
    block,k,seed,g=job;check(k in KEY_ORDER,'key');check(g in ARMS,'arm')
    if block=='main':check_run_seeds('target',[seed],plan,key=k)
    elif block=='smoke':check_run_seeds('smoke',[seed],plan)
    else:raise ValueError(block)


def run_job(job,plan):
    check_job(job,plan);t0=perf_counter()
    if job[0]=='replay':c=replay(*job[2:]);c['part']=job[1]
    else:c=run_fresh(job[2],job[1],job[3]);c['block']=job[0]
    c['job_wall_informational']=perf_counter()-t0;return key(job),c


def _job(x):return run_job(*x)


def _lab(c):return c['stop'] if c['schema']==SCHEMA_REPLAY else ' '.join(f'{a}={v["label"]}' for a,v in c['arms'].items())


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
    """Replay records one per job (in job order); fresh records one per case, arms merged in ARMS order."""
    reps=[];cases={};order=[]
    for j in jobs:
        if key(j) not in done:continue
        g=done[key(j)]
        if j[0]=='replay':reps.append(g);continue
        ck=case_key(j)
        if ck not in cases:
            cases[ck]={x:g[x] for x in ('schema','key','family','seed','eps','n','k','N','truth_reachable','block')};cases[ck]['arms']={}
            cases[ck]['group_walls_informational']={};order.append(ck)
        check(all(cases[ck][x]==g[x] for x in ('family','seed','n','k','N','truth_reachable')),'group records disagree: '+ck)
        cases[ck]['arms'].update(g['arms']);cases[ck]['group_walls_informational'][j[3]]=g['job_wall_informational']
    for c in cases.values():c['arms']={a:c['arms'][a] for a in ARMS if a in c['arms']}
    rank={k:i for i,k in enumerate(KEY_ORDER)};order.sort(key=lambda ck:(rank[cases[ck]['key']],cases[ck]['seed']))
    return reps,[cases[ck] for ck in order]


def _write(output,plan,block,keys,merged,complete,extra):
    from brute.evaluation import no_time
    reps,cases=merged;smoke=block!='main'
    result={'schema':'brute.study.v38_0','plan':plan,'block':block,'smoke':smoke,'complete':complete,'job_keys':keys,'replays':reps,
            'cases':cases,**extra}
    write_new(output/'RESULTS.json',result);write_new(output/'SCIENTIFIC.json',no_time(result))
    write_new(output/'SEAL.json',{'study':plan['study'],'block':block,'results_sha256':sha(output/'RESULTS.json'),
        'scientific_sha256':sha(output/'SCIENTIFIC.json'),'plan_sha256':sha(PLAN),'freeze_sha256':None if smoke else sha(FREEZE),
        'case_count':len(cases),'replay_count':len(reps),'job_count':len(keys),'complete':complete,'smoke':smoke,
        **({'missing_job_keys':extra['missing_job_keys']} if 'missing_job_keys' in extra else {})})


def seal_partial(output,block,reason='study cap',extra_checkpoint=None):
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
    if a.block!='main':check(not Path(out).resolve().is_relative_to(STUDY_DIR.resolve()),'smoke output must not be inside results/study-041')
    if a.seal_partial:print('sealed partial',seal_partial(out,a.block,a.reason,a.snapshot))
    else:run(out,a.workers,a.block);print('done')
