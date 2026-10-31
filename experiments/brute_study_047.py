"""Study BRUTE-0440-CERTIFY16D-SCALE20-047 runner (experiments/BRUTE_PLAN_047.json; pre-run deviation #167 fixes every definition
added here). New file built from experiments/brute_study_046.py (frozen): arm_active's record code is 046's, verbatim, apart from
the arm dispatch (_active below), the host objects per arm and the extra certify/16d fields (per-round call_conflicts and
call_capped; conflicts_spent, wall_guard, guard_events). StepWorld / passive / _truth_ok (033), label9 / _rec9 / _verd /
behaviour_equal (034), last_phase (040), _calls_summary (041), compare_sealed / _canon (046) are imported unchanged.
Arms (plan design.arms):
  API16D   brute.api.certify16d.Certifier16D through its public interface (constructor, observe, propose, result, record,
           current), conflict_cap C and budget_conflicts B from the ledgered calibration (cap_calibration_047), K 128, g3,
           declared N = family size (16 / 3 / 20); in-process solver (counted16d) and the host wall guard TimerHook (30 s per
           call, 600 s per case);
  API16D_b the same arm, a second independent pass: its jobs are queued after every other job, in reverse case order;
  A16_N    frozen brute.scalesearch16.active16 at the 046 settings (9.0 s, 240 s, SolverServer + HardHook);
  API16    frozen brute.api.certify16.Certifier16 at the 046 settings (replays only, part a2).
Every job runs in its own fresh worker process (ProcessPoolExecutor max_tasks_per_child=1), 8 workers.
Main (138 jobs): a1 A16_N on the 18 sealed 045 cases; a2 API16 on the 18 sealed 046 fresh cases; a3 API16D on the 18 sealed 045
and the 18 sealed 046 cases (same world and seed; compared with the sealed A16_N record and classified); b/c fresh scale16 x 12 and
control x 6 by API16D, A16_N, API16D_b; d fresh scale20 x 12 by API16D (dropped if the pre-freeze cut rule fires: see CUT_D).
Smoke (pre-freeze only, never gated; outside results/study-047): smoke range 11570001-04 scale16 (API16D, API16D_b, A16_N),
11570001-02 scale20 (API16D), 11570005-06 control (all three), one replay of each part-a kind (sealed 045 scale16 11130005, sealed
046 scale16 11230001), and two API16D probes on control 11570005: K = 0 and a 50-conflict case budget.
  PYTHONPATH=. python experiments/brute_study_047.py --block main --workers 8
  PYTHONPATH=. python experiments/brute_study_047.py --block smoke --output /tmp/x --workers 8
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
from brute.api import certify16d as C16D
from experiments import worlds_047 as W
from experiments.brute_study_033 import StepWorld,passive,_truth_ok
from experiments.brute_study_034 import label9,_rec9,_verd,behaviour_equal
from experiments.brute_study_040 import last_phase
from experiments.brute_study_041 import _calls_summary
from experiments.brute_study_046 import compare_sealed,_canon
from experiments.brute_common import dumps
from experiments.brute_common_047 import (PLAN,FREEZE,STUDY_DIR,load,sha,write_new,check_freeze,check,Checkpoint,HardHook,
                                          SolverServer,TimerHook,sealed045,sealed046,caps)
from scripts.check_seeds_047 import check_run_seeds,target_ranges,SMOKE,FAMILY_OF

M=1<<W.S_BITS;SOLVER4='g3';EPS=0.0
N_DECLARED=dict(W.SIZES)
KEY_ORDER=('scale16','control','scale20')
ARMS=('API16D','API16D_b','A16_N','API16');D_ARMS=('API16D','API16D_b');WALL_ARMS=('A16_N','API16')
FRESH_ARMS={'scale16':('API16D','A16_N'),'control':('API16D','A16_N'),'scale20':('API16D',)}
CUT_D=False   # pre-freeze cut rule (plan runtime_estimate): set True in the pre-run deviation if the projection exceeds 3600 s
CAP_S=9.0;BUDGET_S=240.0;GUARD_CASE_S=C16D.GUARD_CASE_S;GUARD_CALL_S=C16D.GUARD_CALL_S
Q_BOUND={'A16_N':CAP_S+1.5,'API16':CAP_S+1.5,'API16D':GUARD_CALL_S,'API16D_b':GUARD_CALL_S}
check(S16.QUERY_S14==9.0 and S16.BUDGET14==240 and S16.K14==128 and C16.A16_MAX_BOUND==16 and C16D.A16D_MAX_BOUND==20
      and C16.S_BITS==W.S_BITS and C16D.API=='brute.certify/16d','frozen A16 / certify16d constants')
SCHEMA_CASE='brute.case.v44_0'
K=S16.K14
REPLAY_SEEDS={'045':{'scale16':tuple(range(11130001,11130013)),'control':tuple(range(11190001,11190007))},
              '046':{'scale16':tuple(range(11230001,11230013)),'control':tuple(range(11270001,11270007))}}
REPLAY_PARTS={'a1':('045','A16_N'),'a2':('046','API16'),'a3_045':('045','API16D'),'a3_046':('046','API16D')}
SMOKE_FRESH=tuple([('scale16',SMOKE[0]+i,g) for i in range(4) for g in ('API16D','A16_N','API16D_b')]
                  +[('scale20',SMOKE[0]+i,'API16D') for i in range(2)]
                  +[('control',SMOKE[0]+i,g) for i in (4,5) for g in ('API16D','A16_N','API16D_b')])
SMOKE_REPLAY=(('a1','scale16',11130005),('a3_045','scale16',11130005),('a2','scale16',11230001),('a3_046','scale16',11230001))
PROBES={'K0':('control',SMOKE[0]+4,0,None),'B50':('control',SMOKE[0]+4,K,50)}


def sealed(src):return sealed045() if src=='045' else sealed046()


def _api16d(rd,acts,k,N,sw,Kc,C,B,H):
    """certify/16d through its public interface only: observe the prefix, then propose / execute / observe until None."""
    c=C16D.Certifier16D(rd[0],k,N,'a16d',K=Kc,conflict_cap=C,budget_conflicts=B,wall_guard_case_s=GUARD_CASE_S,
                        wall_guard_call_s=GUARD_CALL_S,solver=SOLVER4,hook=H,factory=C16D.counted16d)
    try:
        for a,o in zip(acts,rd[1:]):c.observe(a,o)
        while True:
            w=c.propose()
            if w is None:break
            for a in w:c.observe(a,sw.step(a))
        res=dict(c.record());res['api_result']=c.result();res['api_current']=c.current();return res
    finally:c.close()


def _api16(rd,acts,k,N,sw,deadline,Kc,H,srv):
    c=C16.Certifier16(rd[0],k,N,'a16',K=Kc,budget_s=BUDGET_S,query_s=CAP_S,deadline=deadline,solver=SOLVER4,hook=H,factory=srv.factory)
    try:
        for a,o in zip(acts,rd[1:]):c.observe(a,o)
        while True:
            w=c.propose()
            if w is None:break
            for a in w:c.observe(a,sw.step(a))
        res=dict(c.record());res['api_result']=c.result();res['api_current']=c.current();return res
    finally:c.close()


class _NoSrv:
    kills=None;starts=None;events=()

    def close(self):pass


def arm_active(w,seed,N,arm,Kc=K,budget=None):
    """One arm on one world. budget: seconds for A16_N / API16 (default 240), conflicts for API16D arms (default B)."""
    sw=StepWorld(w);masks,acts,rd=passive(sw,seed);T0=len(acts);t0=perf_counter()
    obs=lambda a:codes_mask(sw.step(a),W.S_BITS)
    if arm in D_ARMS:
        C,B=caps();budget=B if budget is None else budget;srv=_NoSrv();H=TimerHook()
        try:res=_api16d(rd,acts,w.k,N,sw,Kc,C,budget,H)
        finally:srv.close()
        check(res['masks'][:len(masks)]==masks,'API16D prefix masks differ from passive')
    else:
        budget=BUDGET_S if budget is None else budget;srv=SolverServer();H=HardHook()
        try:
            if arm=='A16_N':res=S16.active16(masks,acts,w.k,M,N,obs,t0+budget,Kc,CAP_S,SOLVER4,H,srv.factory)
            elif arm=='API16':
                res=_api16(rd,acts,w.k,N,sw,t0+budget,Kc,H,srv);check(res['masks'][:len(masks)]==masks,'API16 prefix masks differ from passive')
            else:raise ValueError(arm)
        finally:srv.close()
    fm,fa,f=res['masks'],res['acts'],res['final'];check(sw.steps==len(fa),'step count')
    rounds=[];wall=[q for x in res['rounds'] for q in x['query_walls']]
    for x in res['rounds']:
        T=x['T'];rr={'T':T,'n_min':x['n_min'],'check':x['check'],'bound':x.get('bound'),'queries':len(x['query_walls']),'capped':x['capped'],
                     'query_max_s':max(x['query_walls']) if x['query_walls'] else None,'future':_verd(x['future']),'start':_verd(x['start']),
                     'M1':x['M1'],'s1':x['s1'],'truth_consistent':bool(_truth_ok(w,fa[:T],fm[:T+1]))}
        if 'call_conflicts' in x:rr['call_conflicts']=list(x['call_conflicts']);rr['call_capped']=list(x['call_capped'])
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
           'cap_s':None if arm in D_ARMS else CAP_S,'delta':None,'bound':N,'ceil':res.get('ceil')}
    if arm in D_ARMS:
        extra.update(conflict_cap=res['conflict_cap'],budget_conflicts=res['budget_conflicts'],conflicts_spent=res['conflicts_spent'],
                     wall_guard=res['wall_guard'],guard_events=res['guard_events'],hook_arms=H.arms,hook_fires=H.fires)
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


CANON_ROUND=('T','n_min','check','M1','s1','word','M2','s2','obs','capped','call_conflicts','call_capped')
CANON_ARM=('label','stop','n_min','model','s1','T_final','used','extra_acts','extra_masks','words','capped','conflicts_spent','wall_guard')


def canon16d(r):
    """#167: the canonical API16D record compared byte for byte by GDET (no wall fields)."""
    return dumps({'arm':{x:r.get(x) for x in CANON_ARM},'rounds':[{x:rr.get(x) for x in CANON_ROUND} for rr in r['rounds']]})


def _any_capped(r):return bool(r['capped'])


def classify(cmp,a,s):
    """#167 difference classes. 'none': label, n_min, canonical model and executed words all equal (capped counts may differ);
    else 'infidelity' if neither record has a capped call; else 'cap-timing' if the words are equal (label / n_min / model differ
    after a capped call); else 'word-divergence'."""
    if cmp['same'] and cmp['words_equal']:return 'none'
    if not _any_capped(a) and not _any_capped(s):return 'infidelity'
    return 'cap-timing' if cmp['words_equal'] else 'word-divergence'


def run_replay(part,key_,seed):
    src,arm=REPLAY_PARTS[part];s=sealed(src)[(key_,seed)];c=run_fresh(seed,key_,arm)
    check(all(c[x]==s[x] for x in ('family','seed','n','k','N','truth_reachable')),'replay world differs from the sealed case')
    sa=s['arms']['A16_N'];a=c['arms'][arm];cmp=compare_sealed(a,sa);cmp['class']=classify(cmp,a,sa)
    cmp['sealed_capped_any']=_any_capped(sa);cmp['replay_capped_any']=_any_capped(a);c['replay']=cmp;c['part']=part;c['source']=src
    return c


def jobs_for(plan,block):
    if block=='main':
        R=target_ranges(plan);out=[]
        for p,(src,_) in REPLAY_PARTS.items():out+=[(p,k,s,REPLAY_PARTS[p][1]) for k in ('scale16','control') for s in REPLAY_SEEDS[src][k]]
        for k in KEY_ORDER:
            if k=='scale20' and CUT_D:continue
            for g in FRESH_ARMS[k]:out+=[('main',k,s,g) for s in range(R[k][0],R[k][1]+1)]
        out+=[('main',k,s,'API16D_b') for k in ('control','scale16') for s in range(R[k][1],R[k][0]-1,-1)]
        return out
    if block=='smoke':
        return ([(p,k,s,REPLAY_PARTS[p][1]) for p,k,s in SMOKE_REPLAY]+[('probe',p,PROBES[p][1],'API16D') for p in PROBES]
                +[('smoke',k,s,g) for k,s,g in SMOKE_FRESH])
    raise ValueError(block)


def key(job):return ':'.join(str(x) for x in job)


def case_key(job):return f'{job[0]}:{job[1]}:{job[2]}'


def check_job(job,plan):
    g=job[3];check(g in ARMS,'arm')
    if job[0] in REPLAY_PARTS:
        src,arm=REPLAY_PARTS[job[0]]
        check(g==arm and job[1] in REPLAY_SEEDS[src] and job[2] in REPLAY_SEEDS[src][job[1]] and (job[1],job[2]) in sealed(src),'sealed case');return
    if job[0]=='probe':check(job[1] in PROBES and PROBES[job[1]][1]==job[2] and g=='API16D','probe');check_run_seeds('smoke',[job[2]],plan);return
    block,k,seed,_=job;check(k in KEY_ORDER and g in FRESH_ARMS[k]+(('API16D_b',) if k!='scale20' else ()),'key/arm')
    if block=='main':check_run_seeds('target',[seed],plan,key=k);check(not (k=='scale20' and CUT_D),'part d cut')
    elif block=='smoke':check_run_seeds('smoke',[seed],plan)
    else:raise ValueError(block)


def run_job(job,plan):
    check_job(job,plan);t0=perf_counter()
    if job[0] in REPLAY_PARTS:c=run_replay(job[0],job[1],job[2]);c['block']=job[0]
    elif job[0]=='probe':
        k,s,Kc,b=PROBES[job[1]];c=run_fresh(s,k,job[3],Kc,b);c['block']='probe';c['probe']=job[1]
    else:c=run_fresh(job[2],job[1],job[3]);c['block']=job[0]
    c['job_wall_informational']=perf_counter()-t0;return key(job),c


def _job(x):return run_job(*x)


def _lab(c):
    s=' '.join(f'{a}={v["label"]}/{v["stop"]}' for a,v in c['arms'].items())
    return s+(f" class={c['replay']['class']}" if 'replay' in c else '')


def run_jobs(jobs,plan,workers,ckpt,log=print):
    for j in jobs:check_job(j,plan)
    todo=[j for j in jobs if key(j) not in ckpt.done];log(f'{len(jobs)-len(todo)} cached, {len(todo)} to run',flush=True)
    with ProcessPoolExecutor(max(1,workers),max_tasks_per_child=1) as ex:
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
        if j[0] in REPLAY_PARTS:reps.append(g);continue
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
    reps,cases=merged;smoke=block!='main';C,B=caps()
    result={'schema':'brute.study.v44_0','plan':plan,'block':block,'smoke':smoke,'complete':complete,'job_keys':keys,'replays':reps,
            'cases':cases,'conflict_cap':C,'budget_conflicts':B,'cut_d':CUT_D,**extra}
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
    if a.block!='main':check(not Path(out).resolve().is_relative_to(STUDY_DIR.resolve()),'smoke output must not be inside results/study-047')
    if a.seal_partial:print('sealed partial',seal_partial(out,a.block,a.reason,a.snapshot))
    else:run(out,a.workers,a.block);print('done')
