"""Study BRUTE-0310-SOUND-ACTIVE-ID-034 runner (experiments/BRUTE_PLAN_034.json; deviation #140 fixes every definition
added here). New file; the A8, S5 and S1 arms, StepWorld, the passive prefix and the checkpoint/seal plumbing are imported
unchanged from experiments/brute_study_033.py (frozen).

Cases (all eps 0): scale16 (6, informational), scale12 (12), scale8 (12), control_cycle3 (6) = 36, dispatched longest
first in that family order. Every arm sees the world only through StepWorld; the truth is read by the scorer only. Each
arm starts from the same seeded passive 176-step prefix (worlds_026.actions), rechecked against worlds_026.trajectory.
Declared bound N = the family's nominal size (scale8 8, scale12 12, scale16 16, control_cycle3 3), given to A9 and
A9_random as a prior. Arms, in this order, each with its own 120 s budget:
  A9        brute.scalesearch9.active9 (N, K = 64 extra actions, 10 s per-query cap);
  A9_random the prefix plus exactly A9's extra-action count of seeded uniform random actions (random.Random(seed*91034+34),
            continuing from the prefix end state), then brute.scalesearch9.stop_check9 (start n 1, no further actions);
  A8, S5, S1 the frozen 033 arms (experiments/brute_study_033 arm_A8, arm_S5, arm_S1), unchanged, with their 033 labels.
A9 / A9_random labels: IDU if the stop is 'unknown'; AMB if 'K_spent' (A9) or a future M2 still exists (A9_random); IDF if
no M2 differs from the current state but one differs from the start state; ID if no M2 <= N differs from the start state
and M1 is behaviourally equal to the truth from the start state (product BFS over the two machines); WRONG otherwise
(including 'none', no machine <= N). The descriptive field canonical_match records the 033 canonical-BFS comparison too.
Soundness record per A9 round (evaluator): M1 and (if found) M2 consistent with the round's trace, the executed word
re-simulated (equal codes before its last action, different after), the truth consistent at every round and with the final
trace; for IDF, M1_future_match (M1 from its current state equals the truth from its current state).
  PYTHONPATH=. python experiments/brute_study_034.py --block main --workers 8
  PYTHONPATH=. python experiments/brute_study_034.py --block smoke --output /tmp/x --workers 8
"""
from __future__ import annotations
import argparse,random,time
from pathlib import Path
from time import perf_counter
from concurrent.futures import ProcessPoolExecutor,as_completed
from brute.region import codes_mask
from brute.scalesearch import canonical_bfs,simulate
from brute.scalesearch8 import run_word
from brute.scalesearch9 import active9,stop_check9,QUERY_S9,K9
from experiments import worlds_026 as W
from experiments import brute_study_033 as S33
from experiments.brute_study_033 import StepWorld,passive,arm_A8,arm_S5,arm_S1,_truth_ok,_unexercised,_score
from experiments.brute_common_034 import PLAN,FREEZE,STUDY_DIR,load,sha,write_new,check_freeze,check,Checkpoint
from scripts.check_seeds_034 import check_run_seeds,target_ranges,SMOKE

M=1<<W.S_BITS;SOLVER4='g3';ARM_BUDGET=120.0;EPS=0.0
N_DECLARED={'scale8':8,'scale12':12,'scale16':16,'control_cycle3':3}
FAM_ORDER=('scale16','scale12','scale8','control_cycle3')
SCHEMA_CASE='brute.case.v31_0'
ORDER=('A9','A9_random','A8','S5','S1')
SMOKE_FAMS=('scale16','scale12','scale12','scale8','scale8','control_cycle3')


def behaviour_equal(d1,e1,s1,d2,e2,s2):
    """True iff the two machines emit the same codes on every word from the given states (product BFS)."""
    k=len(d1[0]);seen={(s1,s2)};st=[(s1,s2)]
    while st:
        p,q=st.pop()
        if e1[p]!=e2[q]:return False
        for a in range(k):
            x=(d1[p][a],d2[q][a])
            if x not in seen:seen.add(x);st.append(x)
    return True


def label9(stop,w,model):
    if stop=='unknown':return 'IDU'
    if stop in ('K_spent','AMB'):return 'AMB'
    if stop=='IDF':return 'IDF'
    if stop=='ID' and model is not None and behaviour_equal(model[0],model[1],0,w.transitions,w.emissions,w.start):return 'ID'
    return 'WRONG'


def _verd(S):return None if S is None else {'found':S['found'],'unknown':S['unknown'],'n':S['n'],'verdicts':S['verdicts'],'L':S['L']}


def _rec9(w,fin,acts,masks,lab,t0,stop,extra):
    m=fin['model'];qw=fin.get('query_walls') or []
    out={'label':lab,'ID':int(lab=='ID'),'stop':stop,'n_min':fin['n_min'],'unknown':stop=='unknown',
         'canonical_match':bool(_score(w,m)),'behaviour_match':bool(m is not None and behaviour_equal(m[0],m[1],0,w.transitions,w.emissions,w.start)),
         'model_consistent':bool(m is not None and simulate(m[0],m[1],acts,masks)[0]),
         'truth_consistent_final':bool(_truth_ok(w,acts,masks)),'T_final':len(acts),'truth_pairs_unexercised':_unexercised(w,acts),
         'arm_wall_informational':perf_counter()-t0,'query_max_s':max(qw) if qw else None,'queries':len(qw),'model':m,
         'future':_verd(fin.get('future')),'start':_verd(fin.get('start')),**extra}
    if m is not None and fin.get('s1') is not None:
        tq=simulate(w.transitions,w.emissions,acts,masks,w.start)[1]
        out['M1_future_match']=bool(behaviour_equal(m[0],m[1],fin['s1'],w.transitions,w.emissions,tq))
    return out


def arm_A9(w,seed,N):
    sw=StepWorld(w);masks,acts,_=passive(sw,seed);T0=len(acts);t0=perf_counter()
    obs=lambda a:codes_mask(sw.step(a),W.S_BITS)
    res=active9(masks,acts,w.k,M,N,obs,t0+ARM_BUDGET,K9,QUERY_S9,SOLVER4)
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
    extra={'N':N,'used':res['used'],'rounds':rounds,'n_rounds':len(rounds),'extra_acts':fa[T0:],'extra_masks':fm[T0+1:],
           'words':[r.get('word') for r in rounds if r.get('executed')],'capped':sum(x['capped'] for x in res['rounds'])}
    out=_rec9(w,f,fa,fm,lab,t0,stop,extra);out['query_max_s']=max(wall) if wall else None;out['queries']=len(wall)
    out['words_checked']=sum(1 for r in rounds if r.get('word'));out['words_unsound']=sum(1 for r in rounds if r.get('word') and not r['word_sound'])
    out['truth_inconsistent_rounds']=sum(1 for r in rounds if not r['truth_consistent'])
    return out


def arm_A9_random(w,seed,N,used):
    sw=StepWorld(w);masks,acts,_=passive(sw,seed);t0=perf_counter();rng=random.Random(seed*91034+34);ra=[]
    for _ in range(min(used,K9)):a=rng.randrange(w.k);ra.append(a);acts.append(a);masks.append(codes_mask(sw.step(a),W.S_BITS))
    r=stop_check9(masks,acts,w.k,M,N,t0+ARM_BUDGET,1,QUERY_S9,SOLVER4)
    return _rec9(w,r,acts,masks,label9(r['stop'],w,r['model']),t0,r['stop'],{'N':N,'used':len(ra),'extra_acts':ra,'capped':r['capped']})


def run_case(seed,family):
    w=W.world(seed,family);tr=W.trajectory(w,seed,EPS);sw=StepWorld(w);_,_,rd=passive(sw,seed)
    check(rd==list(tr['readings']) and list(tr['actions'])==list(W.actions(seed,EPS,w.k)),'prefix differs from worlds_026.trajectory')
    N=N_DECLARED[family];check(w.n==N,'world size differs from the declared bound')
    arms={'A9':arm_A9(w,seed,N)}
    arms['A9_random']=arm_A9_random(w,seed,N,arms['A9']['used']);arms['A8']=arm_A8(w,seed);arms['S5']=arm_S5(w,seed);arms['S1']=arm_S1(w,seed)
    return {'schema':SCHEMA_CASE,'family':family,'seed':seed,'eps':EPS,'n':w.n,'k':w.k,'N':N,'arms':arms,
            'truth_reachable':len(canonical_bfs(w.transitions,w.emissions,w.start)[1])}


def jobs_for(plan,block):
    if block=='main':
        R=target_ranges(plan);return [('main',f,s) for f in FAM_ORDER for s in range(R[f][0],R[f][1]+1)]
    if block=='smoke':return [('smoke',f,SMOKE[0]+i) for i,f in enumerate(SMOKE_FAMS)]
    raise ValueError(block)


key=S33.key


def check_job(job,plan):
    block,fam,seed=job;check(fam in FAM_ORDER,'family')
    if block=='main':check_run_seeds('target',[seed],plan,family=fam)
    elif block=='smoke':check_run_seeds('smoke',[seed],plan)
    else:raise ValueError(block)


def run_job(job,plan):
    check_job(job,plan);t0=perf_counter();c=run_case(job[2],job[1]);c['block']=job[0]
    c['case_wall_informational']=perf_counter()-t0;return key(job),c


def _job(x):return run_job(*x)


def run_jobs(jobs,plan,workers,ckpt,log=print):
    for j in jobs:check_job(j,plan)
    todo=[j for j in jobs if key(j) not in ckpt.done];log(f'{len(jobs)-len(todo)} cached, {len(todo)} to run',flush=True)
    with ProcessPoolExecutor(max(1,workers)) as ex:
        futs=[ex.submit(_job,(j,plan)) for j in todo]
        for n,fu in enumerate(as_completed(futs)):
            k_,c=fu.result();ckpt.add(k_,c)
            log(f'done {n+1}/{len(todo)} {k_} {c["case_wall_informational"]:.1f}s '+' '.join(f'{a}={c["arms"][a]["label"]}' for a in ORDER),flush=True)
    return [ckpt.done[key(j)] for j in jobs]


def _write(output,plan,block,keys,cases,complete,extra):
    """The 033 RESULTS / SCIENTIFIC / SEAL writer with the 034 schema, plan and freeze."""
    from brute.evaluation import no_time
    smoke=block!='main'
    result={'schema':'brute.study.v31_0','plan':plan,'block':block,'smoke':smoke,'complete':complete,'job_keys':keys,'cases':cases,**extra}
    write_new(output/'RESULTS.json',result);write_new(output/'SCIENTIFIC.json',no_time(result))
    write_new(output/'SEAL.json',{'study':plan['study'],'block':block,'results_sha256':sha(output/'RESULTS.json'),
        'scientific_sha256':sha(output/'SCIENTIFIC.json'),'plan_sha256':sha(PLAN),'freeze_sha256':None if smoke else sha(FREEZE),
        'case_count':len(cases),'expected_case_count':len(keys),'complete':complete,'smoke':smoke,
        **({'missing_job_keys':extra['missing_job_keys']} if 'missing_job_keys' in extra else {})})


def seal_partial(output,block,limit=None,reason='study cap',extra_checkpoint=None):
    import json
    output=Path(output);plan=load(PLAN)
    for nm in ('RESULTS.json','SCIENTIFIC.json','SEAL.json'):check(not (output/nm).exists(),'refusing overwrite '+str(output/nm))
    jobs=jobs_for(plan,block)[:limit] if limit else jobs_for(plan,block);ck=Checkpoint(output/'CHECKPOINT.jsonl');keys=[key(j) for j in jobs]
    done=dict(ck.done);src={'local':len(done),'snapshot_only':0}
    if extra_checkpoint:
        ex=Checkpoint(extra_checkpoint)
        for k_,c in ex.done.items():
            if k_ in done:check(json.dumps(done[k_],sort_keys=True)==json.dumps(c,sort_keys=True),'snapshot differs from local: '+k_)
            else:done[k_]=c;src['snapshot_only']+=1
    have=[k for k in keys if k in done];missing=[k for k in keys if k not in done]
    _write(output,plan,block,keys,[done[k] for k in have],False,{'stop_reason':reason,'missing_job_keys':missing,'case_sources':src})
    return len(have),len(keys)


def run(output,workers,block,limit=None):
    output=Path(output);plan=load(PLAN)
    if block=='main':check_freeze()
    for nm in ('RESULTS.json','SCIENTIFIC.json','SEAL.json'):check(not (output/nm).exists(),'refusing overwrite '+str(output/nm))
    t0=time.perf_counter();jobs=jobs_for(plan,block);jobs=jobs[:limit] if limit else jobs
    output.mkdir(parents=True,exist_ok=True);ck=Checkpoint(output/'CHECKPOINT.jsonl')
    if block=='main':check(not ck.done,'main checkpoint not empty: never resume (standing rule; resume clause not approved)')
    cases=run_jobs(jobs,plan,workers,ck)
    _write(output,plan,block,[key(j) for j in jobs],cases,True,{'total_elapsed_informational':time.perf_counter()-t0})


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--block',choices=('main','smoke'),default='main')
    ap.add_argument('--output');ap.add_argument('--workers',type=int,default=8);ap.add_argument('--limit',type=int)
    ap.add_argument('--seal-partial',action='store_true');ap.add_argument('--snapshot');ap.add_argument('--reason',default='study cap')
    a=ap.parse_args();out=a.output or str(STUDY_DIR/a.block)
    if a.block!='main':check(not Path(out).resolve().is_relative_to(STUDY_DIR.resolve()),'smoke output must not be inside results/study-034')
    if a.seal_partial:print('sealed partial',seal_partial(out,a.block,a.limit,a.reason,a.snapshot))
    else:run(out,a.workers,a.block,a.limit);print('done')
