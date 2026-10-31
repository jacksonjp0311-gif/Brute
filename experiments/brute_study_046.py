"""Study BRUTE-0430-CERTIFY16-046 runner (experiments/BRUTE_PLAN_046.json; pre-run deviation #165 fixes every definition
added here). New file built from experiments/brute_study_045.py (frozen): arm_active's record code is 045's, verbatim, apart from
the arm dispatch (_active below) and the extra 'api' fields; StepWorld / passive / _truth_ok (033), label9 / _rec9 / _verd /
behaviour_equal (034), last_phase (040), _calls_summary (041) are imported unchanged.
Arms (plan design.arms): API16 = brute.api.certify16.Certifier16 driven only through its public interface (constructor,
observe, propose, result, record, current): the passive prefix readings are observed step by step, then every proposed word is
executed on the world action by action and observed; A16_N = frozen brute.scalesearch16.active16. Both: declared N = family size
(16 / 3), cap 9.0 s, case budget 240 s, K = 128, solver g3; each job owns one SolverServer child under HardHook (host-side hard
cap), passed to certify/16 through its hook / factory parameters exactly as 045 passed them to active16.
Main: part a_replay: the 18 sealed 045 A16_N cases (scale16 11130001-12, control 11190001-06) rerun through API16 on the same
world and seed, compared with the sealed record (stop label, n_min, canonical model, T_final, executed words); part b_fresh: plan
heldout ranges, 36 jobs, one per (case, arm), scale16 first, arms API16 then A16_N within a key; 8 workers; 54 jobs in all.
Smoke (pre-freeze only, never gated; outside results/study-046): fresh arms on the smoke range (scale16 x 4, control x 2),
replays of sealed 045 scale16 11130005 and control 11190001 (seen before the freeze; declared in #165), and two API16 probes on
the smoke control seed (+4): K = 0 and a 0.5 s case budget.
  PYTHONPATH=. python experiments/brute_study_046.py --block main --workers 8
  PYTHONPATH=. python experiments/brute_study_046.py --block smoke --output /tmp/x --workers 8
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
from brute.api import certify16 as C16
from experiments import worlds_043 as W
from experiments.brute_study_033 import StepWorld,passive,_truth_ok
from experiments.brute_study_034 import label9,_rec9,_verd,behaviour_equal
from experiments.brute_study_040 import last_phase
from experiments.brute_study_041 import _calls_summary
from experiments.brute_common_046 import (PLAN,FREEZE,STUDY_DIR,load,sha,write_new,check_freeze,check,Checkpoint,HardHook,
                                          SolverServer,sealed045)
from scripts.check_seeds_046 import check_run_seeds,target_ranges,SMOKE,FAMILY_OF

M=1<<W.S_BITS;SOLVER4='g3';EPS=0.0
N_DECLARED=dict(W.SIZES)
KEY_ORDER=('scale16','control')
ARMS=('API16','A16_N');DELTA={'API16':None,'A16_N':None};JOB_ORDER=('API16','A16_N')
CAP={a:9.0 for a in ARMS};ARM_BUDGET={a:240.0 for a in ARMS}
Q_BOUND={a:CAP[a]+1.5 for a in ARMS}
check(S16.QUERY_S14==9.0 and S16.BUDGET14==240 and S16.K14==128 and C16.A16_MAX_BOUND==16 and C16.S_BITS==W.S_BITS,'frozen A16 constants')
SCHEMA_CASE='brute.case.v43_0'
K=S16.K14;BUDGET=S16.BUDGET14
SMOKE_KEYS=('scale16','scale16','scale16','scale16','control','control')
REPLAY_SEEDS={'scale16':tuple(range(11130001,11130013)),'control':tuple(range(11190001,11190007))}
SMOKE_REPLAY=(('scale16',11130005),('control',11190001))
PROBES={'K0':('control',SMOKE[0]+4,0,BUDGET),'B05':('control',SMOKE[0]+4,K,0.5)}


def _api16(rd,acts,k,N,sw,deadline,Kc,H,srv):
    """certify/16 through its public interface only: observe the prefix, then propose / execute / observe until None."""
    c=C16.Certifier16(rd[0],k,N,'a16',K=Kc,budget_s=BUDGET,query_s=CAP['API16'],deadline=deadline,solver=SOLVER4,hook=H,factory=srv.factory)
    try:
        for a,o in zip(acts,rd[1:]):c.observe(a,o)
        while True:
            w=c.propose()
            if w is None:break
            for a in w:c.observe(a,sw.step(a))
        res=dict(c.record());res['api_result']=c.result();res['api_current']=c.current();return res
    finally:c.close()


def _active(arm,masks,acts,rd,k,N,obs,sw,deadline,Kc,H,srv):
    if arm=='A16_N':return S16.active16(masks,acts,k,M,N,obs,deadline,Kc,CAP[arm],SOLVER4,H,srv.factory)
    if arm=='API16':
        res=_api16(rd,acts,k,N,sw,deadline,Kc,H,srv);check(res['masks'][:len(masks)]==masks,'API16 prefix masks differ from passive');return res
    raise ValueError(arm)


def arm_active(w,seed,N,arm,Kc=K,budget=None):
    budget=ARM_BUDGET[arm] if budget is None else budget
    sw=StepWorld(w);masks,acts,rd=passive(sw,seed);T0=len(acts);t0=perf_counter()
    obs=lambda a:codes_mask(sw.step(a),W.S_BITS);srv=SolverServer();H=HardHook()
    try:res=_active(arm,masks,acts,rd,w.k,N,obs,sw,t0+budget,Kc,H,srv)
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
    if 'api_result' in res:out['api']=res['api_result'];out['api_current']=res['api_current']
    return out


def run_fresh(seed,pkey,arm,Kc=K,budget=None):
    fam=FAMILY_OF[pkey];w=W.world(seed,fam);tr=W.trajectory(w,seed,EPS);sw=StepWorld(w);_,acts,rd=passive(sw,seed)
    check(rd==list(tr['readings']) and acts==list(tr['actions']),'prefix differs from worlds_026.trajectory')
    N=N_DECLARED[fam];check(w.n==N,'world size differs from the declared bound')
    if arm not in ARMS:raise ValueError(arm)
    return {'schema':SCHEMA_CASE,'key':pkey,'family':fam,'seed':seed,'eps':EPS,'n':w.n,'k':w.k,'N':N,'group':arm,
            'arms':{arm:arm_active(w,seed,N,arm,Kc,budget)},'truth_reachable':len(canonical_bfs(w.transitions,w.emissions,w.start)[1])}


def _canon(m):return None if m is None else canonical_bfs(m[0],m[1],0)


def compare_sealed(a,s):
    """#165 item 1: the replay comparison of an API16 record a with the sealed 045 A16_N record s."""
    wa=[r['word'] for r in a['rounds'] if r.get('word')];ws=[r['word'] for r in s['rounds'] if r.get('word')]
    first=next((i for i,(x,y) in enumerate(zip(wa,ws)) if x!=y),None if len(wa)==len(ws) else min(len(wa),len(ws)))
    out={'label':[a['label'],s['label']],'stop':[a['stop'],s['stop']],'n_min':[a['n_min'],s['n_min']],
         'canonical_model_equal':_canon(a['model'])==_canon(s['model']),'T_final':[a['T_final'],s['T_final']],
         'words_equal':wa==ws,'first_word_divergence':first,'capped':[a['capped'],s['capped']]}
    out['same']=bool(a['label']==s['label'] and a['n_min']==s['n_min'] and out['canonical_model_equal'])
    out['same_step']=bool(out['same'] and a['T_final']==s['T_final']);return out


def run_replay(key_,seed,part):
    s=sealed045()[(key_,seed)];c=run_fresh(seed,key_,'API16')
    check(all(c[x]==s[x] for x in ('family','seed','n','k','N','truth_reachable')),'replay world differs from the sealed 045 case')
    c['replay']=compare_sealed(c['arms']['API16'],s['arms']['A16_N']);c['part']=part;return c


def jobs_for(plan,block):
    if block=='main':
        R=target_ranges(plan);out=[('replay',k,s,'API16') for k in KEY_ORDER for s in REPLAY_SEEDS[k]]
        for k in KEY_ORDER:
            for g in JOB_ORDER:out+=[('main',k,s,g) for s in range(R[k][0],R[k][1]+1)]
        return out
    if block=='smoke':
        return ([('sreplay',k,s,'API16') for k,s in SMOKE_REPLAY]+[('probe',p,PROBES[p][1],'API16') for p in PROBES]
                +[('smoke',k,SMOKE[0]+i,g) for i,k in enumerate(SMOKE_KEYS) for g in ARMS])
    raise ValueError(block)


def key(job):return ':'.join(str(x) for x in job)


def case_key(job):return f'{job[0]}:{job[1]}:{job[2]}'


def check_job(job,plan):
    g=job[3];check(g in ARMS,'arm')
    if job[0] in ('replay','sreplay'):
        check(g=='API16' and job[1] in KEY_ORDER and job[2] in REPLAY_SEEDS[job[1]] and (job[1],job[2]) in sealed045(),'sealed 045 case')
        if job[0]=='sreplay':check((job[1],job[2]) in SMOKE_REPLAY,'smoke replay')
        return
    if job[0]=='probe':check(job[1] in PROBES and PROBES[job[1]][1]==job[2] and g=='API16','probe');check_run_seeds('smoke',[job[2]],plan);return
    block,k,seed,_=job;check(k in KEY_ORDER,'key')
    if block=='main':check_run_seeds('target',[seed],plan,key=k)
    elif block=='smoke':check_run_seeds('smoke',[seed],plan)
    else:raise ValueError(block)


def run_job(job,plan):
    check_job(job,plan);t0=perf_counter()
    if job[0] in ('replay','sreplay'):c=run_replay(job[1],job[2],'a_replay' if job[0]=='replay' else 'smoke');c['block']=job[0]
    elif job[0]=='probe':
        k,s,Kc,b=PROBES[job[1]];c=run_fresh(s,k,job[3],Kc,b);c['block']='probe';c['probe']=job[1]
    else:c=run_fresh(job[2],job[1],job[3]);c['block']=job[0]
    c['job_wall_informational']=perf_counter()-t0;return key(job),c


def _job(x):return run_job(*x)


def _lab(c):
    s=' '.join(f'{a}={v["label"]}/{v["stop"]}' for a,v in c['arms'].items())
    return s+(f" replay_same={c['replay']['same']}" if 'replay' in c else '')


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
        if j[0] in ('replay','sreplay'):reps.append(g);continue
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
    result={'schema':'brute.study.v43_0','plan':plan,'block':block,'smoke':smoke,'complete':complete,'job_keys':keys,'replays':reps,
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
    if a.block!='main':check(not Path(out).resolve().is_relative_to(STUDY_DIR.resolve()),'smoke output must not be inside results/study-046')
    if a.seal_partial:print('sealed partial',seal_partial(out,a.block,a.reason,a.snapshot))
    else:run(out,a.workers,a.block);print('done')
