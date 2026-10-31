"""Study BRUTE-0360-CLEAN-SCALE-039 runner (experiments/BRUTE_PLAN_039.json; deviation #150 fixes every definition added
here). New file; the A9 arm (experiments.brute_study_034.arm_A9), StepWorld and the passive prefix (experiments.brute_study_033)
are imported unchanged (frozen).

Cases (all eps 0): scale16 (12), scale14 (12), scale12 (12), perm12 (12), control (6, control_cycle3) = 54; worlds from
experiments.worlds_039. Every arm sees the world only through StepWorld; the truth is read by the scorer only. Each arm
starts from the same seeded passive 176-step prefix (worlds_026.actions), rechecked against worlds_026.trajectory. Declared
bound N = the family's nominal size (16, 14, 12, 12, 3), given to every arm as a prior.
Arms (timer hook armed at QUERY_S14 = 9.0 s for the A14 arms; GQB14 bound 10.5 s):
  A14        brute.scalesearch14.active14, K = 128 extra actions, 240 s case budget;
  A14_random the prefix plus exactly A14's extra-action count of seeded uniform random actions (random.Random(seed*91039+39),
             continuing from the prefix end state), then brute.scalesearch14.stop_check14 (start n 1, a fresh pool, 240 s);
  A14_k64    active14 with K = 64 and a 120 s budget;
  A9         the frozen v0.31.0 arm (brute.scalesearch9.active9, K 64, 120 s, its own 10 s cap, no hook), unchanged.
Labels (A9's label9): IDU if 'unknown'; AMB if 'K_spent' or a future rival still exists (A14_random); IDF; ID only if no
rival <= N differs from the start state and M1 equals the truth from the start state; WRONG otherwise.
Jobs (deviation #150): one job per (case, group), groups 'A14' (A14 then A14_random, which needs A14's count), 'A14_k64' and
'A9', dispatched group-major (all A14 jobs first, longest family first) on 8 workers; the checkpoint holds one line per job
and the sealed RESULTS holds one record per case with the arms merged in the order ORDER.
  PYTHONPATH=. python experiments/brute_study_039.py --block main --workers 8
  PYTHONPATH=. python experiments/brute_study_039.py --block smoke --output /tmp/x --workers 8
"""
from __future__ import annotations
import argparse,json,random,time
from pathlib import Path
from time import perf_counter
from concurrent.futures import ProcessPoolExecutor,as_completed
from brute.region import codes_mask
from brute.scalesearch import canonical_bfs,simulate
from brute.scalesearch8 import run_word
from brute import scalesearch14 as S14
from experiments import worlds_039 as W
from experiments.brute_study_033 import StepWorld,passive,_truth_ok
from experiments.brute_study_034 import arm_A9,label9,_rec9,_verd,behaviour_equal
from experiments.brute_common_039 import PLAN,FREEZE,STUDY_DIR,load,sha,write_new,check_freeze,check,Checkpoint,HOOK
from scripts.check_seeds_039 import check_run_seeds,target_ranges,SMOKE,FAMILY_OF

M=1<<W.S_BITS;SOLVER4='g3';EPS=0.0;QUERY_S=S14.QUERY_S14;Q_BOUND=10.5
N_DECLARED=dict(W.SIZES)
KEY_ORDER=('scale16','scale14','scale12','perm12','control')
GROUPS=('A14','A14_k64','A9')
GROUP_ARMS={'A14':('A14','A14_random'),'A14_k64':('A14_k64',),'A9':('A9',)}
ORDER=('A14','A14_random','A14_k64','A9')
SCHEMA_CASE='brute.case.v36_0'
ARM_CFG={'A14':(S14.K14,S14.BUDGET14),'A14_k64':(S14.K14_64,S14.BUDGET14_64)}
SMOKE_KEYS=('scale16','scale16','scale16','scale14','scale14','scale14','scale12','scale12','perm12','perm12','perm12','control')


def arm_A14(w,seed,N,K,budget):
    sw=StepWorld(w);masks,acts,_=passive(sw,seed);T0=len(acts);t0=perf_counter()
    obs=lambda a:codes_mask(sw.step(a),W.S_BITS)
    res=S14.active14(masks,acts,w.k,M,N,obs,t0+budget,K,QUERY_S,SOLVER4,HOOK)
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
    stop=res['stop'];lab=label9(stop,w,f['model'])
    extra={'N':N,'K':K,'budget':budget,'used':res['used'],'rounds':rounds,'n_rounds':len(rounds),'extra_acts':fa[T0:],
           'extra_masks':fm[T0+1:],'words':[r.get('word') for r in rounds if r.get('executed')],
           'capped':sum(x['capped'] for x in res['rounds']),'inc_guards':res['guards'],'inc_sizes':res['sizes']}
    out=_rec9(w,f,fa,fm,lab,t0,stop,extra);out['query_max_s']=max(wall) if wall else None;out['queries']=len(wall)
    out['words_checked']=sum(1 for r in rounds if r.get('word'));out['words_unsound']=sum(1 for r in rounds if r.get('word') and not r['word_sound'])
    out['truth_inconsistent_rounds']=sum(1 for r in rounds if not r['truth_consistent'])
    return out


def arm_A14_random(w,seed,N,used):
    sw=StepWorld(w);masks,acts,_=passive(sw,seed);t0=perf_counter();rng=random.Random(seed*91039+39);ra=[]
    for _ in range(min(used,S14.K14)):a=rng.randrange(w.k);ra.append(a);acts.append(a);masks.append(codes_mask(sw.step(a),W.S_BITS))
    r=S14.stop_check14(masks,acts,w.k,M,N,t0+S14.BUDGET14,1,QUERY_S,SOLVER4,hook=HOOK)
    return _rec9(w,r,acts,masks,label9(r['stop'],w,r['model']),t0,r['stop'],
                 {'N':N,'used':len(ra),'extra_acts':ra,'capped':r['capped'],'budget':S14.BUDGET14})


def run_group(seed,pkey,group):
    fam=FAMILY_OF[pkey];w=W.world(seed,fam);tr=W.trajectory(w,seed,EPS);sw=StepWorld(w);_,acts,rd=passive(sw,seed)
    check(rd==list(tr['readings']) and acts==list(tr['actions']),'prefix differs from worlds_026.trajectory')
    N=N_DECLARED[fam];check(w.n==N,'world size differs from the declared bound');arms={}
    if group=='A14':
        arms['A14']=arm_A14(w,seed,N,*ARM_CFG['A14']);arms['A14_random']=arm_A14_random(w,seed,N,arms['A14']['used'])
    elif group=='A14_k64':arms['A14_k64']=arm_A14(w,seed,N,*ARM_CFG['A14_k64'])
    elif group=='A9':arms['A9']=arm_A9(w,seed,N)
    else:raise ValueError(group)
    return {'schema':SCHEMA_CASE,'key':pkey,'family':fam,'seed':seed,'eps':EPS,'n':w.n,'k':w.k,'N':N,'group':group,'arms':arms,
            'truth_reachable':len(canonical_bfs(w.transitions,w.emissions,w.start)[1])}


def plan_groups(plan):
    """Groups actually run per plan key (deviation-adjustable via plan; default every group on every key)."""
    return {k:GROUPS for k in KEY_ORDER}


def jobs_for(plan,block,groups=None):
    G=groups or plan_groups(plan)
    if block=='main':
        R=target_ranges(plan);return [('main',k,s,g) for g in GROUPS for k in KEY_ORDER if g in G[k] for s in range(R[k][0],R[k][1]+1)]
    if block=='smoke':return [('smoke',k,SMOKE[0]+i,g) for g in GROUPS for i,k in enumerate(SMOKE_KEYS)]
    raise ValueError(block)


def key(job):return f'{job[0]}:{job[1]}:{job[2]}:{job[3]}'


def case_key(job):return f'{job[0]}:{job[1]}:{job[2]}'


def check_job(job,plan):
    block,k,seed,g=job;check(k in KEY_ORDER,'key');check(g in GROUPS,'group')
    if block=='main':check_run_seeds('target',[seed],plan,key=k)
    elif block=='smoke':check_run_seeds('smoke',[seed],plan)
    else:raise ValueError(block)


def run_job(job,plan):
    check_job(job,plan);t0=perf_counter();c=run_group(job[2],job[1],job[3]);c['block']=job[0]
    c['job_wall_informational']=perf_counter()-t0;return key(job),c


def _job(x):return run_job(*x)


def run_jobs(jobs,plan,workers,ckpt,log=print):
    for j in jobs:check_job(j,plan)
    todo=[j for j in jobs if key(j) not in ckpt.done];log(f'{len(jobs)-len(todo)} cached, {len(todo)} to run',flush=True)
    with ProcessPoolExecutor(max(1,workers)) as ex:
        futs=[ex.submit(_job,(j,plan)) for j in todo]
        for n,fu in enumerate(as_completed(futs)):
            k_,c=fu.result();ckpt.add(k_,c)
            log(f'done {n+1}/{len(todo)} {k_} {c["job_wall_informational"]:.1f}s '+' '.join(f'{a}={v["label"]}' for a,v in c['arms'].items()),flush=True)
    return [ckpt.done[key(j)] for j in jobs]


def merge(jobs,done):
    """One record per case (job order of first appearance), arms merged in ORDER; group walls kept per group."""
    cases={};order=[]
    for j in jobs:
        if key(j) not in done:continue
        g=done[key(j)];ck=case_key(j)
        if ck not in cases:
            cases[ck]={x:g[x] for x in ('schema','key','family','seed','eps','n','k','N','truth_reachable','block')};cases[ck]['arms']={}
            cases[ck]['group_walls_informational']={};order.append(ck)
        check(all(cases[ck][x]==g[x] for x in ('family','seed','n','k','N','truth_reachable')),'group records disagree: '+ck)
        cases[ck]['arms'].update(g['arms']);cases[ck]['group_walls_informational'][j[3]]=g['job_wall_informational']
    for c in cases.values():c['arms']={a:c['arms'][a] for a in ORDER if a in c['arms']}
    rank={k:i for i,k in enumerate(KEY_ORDER)};order.sort(key=lambda ck:(rank[cases[ck]['key']],cases[ck]['seed']))
    return [cases[ck] for ck in order]


def _write(output,plan,block,keys,cases,complete,extra):
    from brute.evaluation import no_time
    smoke=block!='main'
    result={'schema':'brute.study.v36_0','plan':plan,'block':block,'smoke':smoke,'complete':complete,'job_keys':keys,'cases':cases,**extra}
    write_new(output/'RESULTS.json',result);write_new(output/'SCIENTIFIC.json',no_time(result))
    write_new(output/'SEAL.json',{'study':plan['study'],'block':block,'results_sha256':sha(output/'RESULTS.json'),
        'scientific_sha256':sha(output/'SCIENTIFIC.json'),'plan_sha256':sha(PLAN),'freeze_sha256':None if smoke else sha(FREEZE),
        'case_count':len(cases),'job_count':len(keys),'complete':complete,'smoke':smoke,
        **({'missing_job_keys':extra['missing_job_keys']} if 'missing_job_keys' in extra else {})})


def seal_partial(output,block,limit=None,reason='study cap',extra_checkpoint=None):
    output=Path(output);plan=load(PLAN)
    for nm in ('RESULTS.json','SCIENTIFIC.json','SEAL.json'):check(not (output/nm).exists(),'refusing overwrite '+str(output/nm))
    jobs=jobs_for(plan,block)[:limit] if limit else jobs_for(plan,block);ck=Checkpoint(output/'CHECKPOINT.jsonl');keys=[key(j) for j in jobs]
    done=dict(ck.done);src={'local':len(done),'snapshot_only':0}
    if extra_checkpoint:
        ex=Checkpoint(extra_checkpoint)
        for k_,c in ex.done.items():
            if k_ in done:check(json.dumps(done[k_],sort_keys=True)==json.dumps(c,sort_keys=True),'snapshot differs from local: '+k_)
            else:done[k_]=c;src['snapshot_only']+=1
    missing=[k for k in keys if k not in done]
    _write(output,plan,block,keys,merge(jobs,done),False,{'stop_reason':reason,'missing_job_keys':missing,'case_sources':src})
    return len(keys)-len(missing),len(keys)


def run(output,workers,block,limit=None):
    output=Path(output);plan=load(PLAN)
    if block=='main':check_freeze()
    for nm in ('RESULTS.json','SCIENTIFIC.json','SEAL.json'):check(not (output/nm).exists(),'refusing overwrite '+str(output/nm))
    t0=time.perf_counter();jobs=jobs_for(plan,block);jobs=jobs[:limit] if limit else jobs
    output.mkdir(parents=True,exist_ok=True);ck=Checkpoint(output/'CHECKPOINT.jsonl')
    if block=='main':check(not ck.done,'main checkpoint not empty: never resume (standing rule; resume clause not approved)')
    run_jobs(jobs,plan,workers,ck)
    _write(output,plan,block,[key(j) for j in jobs],merge(jobs,ck.done),True,{'total_elapsed_informational':time.perf_counter()-t0})


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--block',choices=('main','smoke'),default='main')
    ap.add_argument('--output');ap.add_argument('--workers',type=int,default=8);ap.add_argument('--limit',type=int)
    ap.add_argument('--seal-partial',action='store_true');ap.add_argument('--snapshot');ap.add_argument('--reason',default='study cap')
    a=ap.parse_args();out=a.output or str(STUDY_DIR/a.block)
    if a.block!='main':check(not Path(out).resolve().is_relative_to(STUDY_DIR.resolve()),'smoke output must not be inside results/study-039')
    if a.seal_partial:print('sealed partial',seal_partial(out,a.block,a.limit,a.reason,a.snapshot))
    else:run(out,a.workers,a.block,a.limit);print('done')
