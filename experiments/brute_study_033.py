"""Study BRUTE-0300-ACTIVE-EXPERIMENTS-033 runner (experiments/BRUTE_PLAN_033.json; deviation #138 fixes every
definition added here). New file; job, checkpoint and seal plumbing built from experiments/brute_study_032.py (frozen,
unchanged).

Cases (all eps 0): scale16 (6, informational), scale12 (12), scale8 (12), control_cycle3 (6) = 36, dispatched longest
first in that family order (seed order within each). Every arm sees the world only through StepWorld (reset, then
step(action) -> reading); the true machine is read by the scorer only. Each arm starts from the same seeded passive
176-step prefix (worlds_026.actions); the prefix readings are rechecked against worlds_026.trajectory.
Arms, in this order, each with its own 120 s budget:
  A8        brute.scalesearch8.active8 (K = 64 extra actions, 10 s per-query cap);
  A8_random the prefix plus exactly A8's extra-action count of seeded uniform random actions (random.Random(seed*91033+33),
            continuing from the prefix end state), then one identify8 call (start n 1, 10 s per-query cap);
  S5        brute.scalesearch6.identify6 on the prefix (the 031 identify probe, unchanged; no per-query cap);
  S1        brute.scalesearch4.identify_trace on the prefix (frozen, unchanged; its S1 per-solve conflict budget).
Labels (as 031): IDU if unknown; else AMB if a second machine was found (S1: not unique); else ID if unique and the
canonical BFS of the model equals the truth's; else WRONG. A8 stops 'indistinguishable' or 'K_spent' with a second
machine still consistent, so both are AMB.
Soundness record per A8 round (evaluator): the two machines are consistent with the trace of that round, predict equal
codes before the last action of the word and different codes after it; the true machine is consistent with the trace at
every round and with the final extended trace (also for A8_random). When the two machines have no distinguishing word,
the round records (descriptive) same_future (both are the same machine from their current states, so they differ only in
the start state or the unreached past) and M1_future_match (M1 from its current state equals the truth from its current
state).
  PYTHONPATH=. python experiments/brute_study_033.py --block main --workers 8
  PYTHONPATH=. python experiments/brute_study_033.py --block smoke --output /tmp/x --workers 8
"""
from __future__ import annotations
import argparse,random,time
from pathlib import Path
from time import perf_counter
from concurrent.futures import ProcessPoolExecutor,as_completed
from brute.region import codes_mask
from brute.scalesearch import canonical_bfs,simulate
from brute.scalesearch4 import identify_trace
from brute.scalesearch6 import identify6
from brute.scalesearch8 import active8,identify8,run_word,QUERY_S8,K8
from experiments import worlds_026 as W
from experiments.brute_common_033 import PLAN,FREEZE,STUDY_DIR,load,sha,write_new,check_freeze,check,Checkpoint
from scripts.check_seeds_033 import check_run_seeds,target_ranges,SMOKE

STEPS=W.HORIZON;N_MAX=16;M=1<<W.S_BITS;SOLVER4='g3';ARM_BUDGET=120.0;EPS=0.0
FAM_ORDER=('scale16','scale12','scale8','control_cycle3')
SCHEMA_CASE='brute.case.v30_0'
ORDER=('A8','A8_random','S5','S1')
SMOKE_FAMS=('scale16','scale12','scale12','scale8','scale8','control_cycle3')


class StepWorld:
    """Step-only access: reset() -> first reading; step(action) -> next reading (bit tuple). No other attribute is read."""
    def __init__(self,w):self._w=w;self._h=None;self.k=w.k;self.steps=0

    def reset(self):self._h=self._w.start;self.steps=0;return W.bits(self._w.emissions[self._h])

    def step(self,a):
        if a not in range(self.k):raise ValueError('bad action')
        self._h=self._w.transitions[self._h][a];self.steps+=1;return W.bits(self._w.emissions[self._h])


def passive(sw,seed):
    """The seeded passive prefix through the wrapper: (masks, acts, readings)."""
    acts=list(W.actions(seed,EPS,sw.k));rd=[sw.reset()]
    for a in acts:rd.append(sw.step(a))
    return [codes_mask(o,W.S_BITS) for o in rd],acts,rd


def label(r,match,second):
    if r['unknown']:return 'IDU'
    if second:return 'AMB'
    if r['unique'] and match:return 'ID'
    return 'WRONG'


def _score(w,model):
    tc=canonical_bfs(w.transitions,w.emissions,w.start)
    return model is not None and canonical_bfs(model[0],model[1],0)==tc


def _truth_ok(w,acts,masks):return simulate(w.transitions,w.emissions,acts,masks,w.start)[0]


def _unexercised(w,acts):
    q=w.start;used=set()
    for a in acts:used.add((q,a));q=w.transitions[q][a]
    return w.n*w.k-len(used)


def _rec(w,r,acts,masks,lab,t0,extra):
    m=r['model'];qw=r.get('query_walls') or []
    return {'label':lab,'ID':int(lab=='ID'),'n_min':r['n_min'],'unique':bool(r['unique']),'unknown':bool(r['unknown']),
            'match':bool(_score(w,m)),'model_consistent':bool(m is not None and simulate(m[0],m[1],acts,masks)[0]),
            'truth_consistent_final':bool(_truth_ok(w,acts,masks)),'T_final':len(acts),
            'truth_pairs_unexercised':_unexercised(w,acts),'arm_wall_informational':perf_counter()-t0,
            'query_max_s':max(qw) if qw else None,'queries':len(qw),'model':m,'model2':r.get('model2'),**extra}


def arm_A8(w,seed):
    sw=StepWorld(w);masks,acts,_=passive(sw,seed);T0=len(acts);t0=perf_counter()
    obs=lambda a:codes_mask(sw.step(a),W.S_BITS)
    res=active8(masks,acts,w.k,M,N_MAX,obs,t0+ARM_BUDGET,K8,QUERY_S8,SOLVER4)
    fm,fa,f=res['masks'],res['acts'],res['final'];check(sw.steps==len(fa),'step count')
    rounds=[];wall=[q for x in res['rounds'] for q in x['query_walls']]
    for x in res['rounds']:
        T=x['T'];rr={'T':T,'n_min':x['n_min'],'n_start':x['n_start'],'unique':x['unique'],'unknown':x['unknown'],
                     'second_found':x['second_found'],'queries':len(x['query_walls']),'capped':x['capped'],
                     'query_max_s':max(x['query_walls']) if x['query_walls'] else None,
                     'truth_consistent':bool(_truth_ok(w,fa[:T],fm[:T+1]))}
        if 'word' in x:
            (d1,e1),(d2,e2)=x['M1'],x['M2'];w_=x['word'];rr['word']=w_;rr.update(M1=x['M1'],M2=x['M2'],s1=x['s1'],s2=x['s2'])
            rr['M1_consistent']=bool(simulate(d1,e1,fa[:T],fm[:T+1])[0]);rr['M2_consistent']=bool(simulate(d2,e2,fa[:T],fm[:T+1])[0])
            if w_ is None:
                rr['same_future']=canonical_bfs(d1,e1,x['s1'])==canonical_bfs(d2,e2,x['s2'])
                rr['M1_match']=bool(_score(w,x['M1']));rr['M2_match']=bool(_score(w,x['M2']))
                tq=simulate(w.transitions,w.emissions,fa[:T],fm[:T+1],w.start)[1]
                rr['M1_future_match']=canonical_bfs(d1,e1,x['s1'])==canonical_bfs(w.transitions,w.emissions,tq)
            else:
                p1=run_word(d1,e1,x['s1'],w_);p2=run_word(d2,e2,x['s2'],w_)
                rr['word_sound']=bool(('pred1' not in x or (p1==x['pred1'] and p2==x['pred2'])) and p1[:-1]==p2[:-1] and p1[-1]!=p2[-1])
                if 'obs' in x:
                    rr['executed']=True;rr['obs']=x['obs'];rr['M1_survives']=bool(all(o>>c&1 for o,c in zip(x['obs'],p1)))
                    rr['M2_survives']=bool(all(o>>c&1 for o,c in zip(x['obs'],p2)))
                else:rr['executed']=False
        rounds.append(rr)
    stop=res['stop'];second=stop in ('indistinguishable','K_spent') or f['second_found']
    lab=label(f,_score(w,f['model']),second)
    if stop=='none':lab='WRONG'
    extra={'stop':stop,'second_found':bool(f['second_found']),'used':res['used'],'rounds':rounds,'n_rounds':len(rounds),'extra_acts':fa[T0:],'extra_masks':fm[T0+1:],
           'words':[r.get('word') for r in rounds if r.get('executed')],'capped':sum(x['capped'] for x in res['rounds'])}
    out=_rec(w,f,fa,fm,lab,t0,extra);out['query_max_s']=max(wall) if wall else None;out['queries']=len(wall)
    out['words_checked']=sum(1 for r in rounds if r.get('word'));out['words_unsound']=sum(1 for r in rounds if r.get('word') and not r['word_sound'])
    out['truth_inconsistent_rounds']=sum(1 for r in rounds if not r['truth_consistent'])
    return out


def arm_A8_random(w,seed,used):
    sw=StepWorld(w);masks,acts,_=passive(sw,seed);t0=perf_counter();rng=random.Random(seed*91033+33);ra=[]
    for _ in range(min(used,K8)):a=rng.randrange(w.k);ra.append(a);acts.append(a);masks.append(codes_mask(sw.step(a),W.S_BITS))
    r=identify8(masks,acts,w.k,M,N_MAX,t0+ARM_BUDGET,1,QUERY_S8,SOLVER4)
    return _rec(w,r,acts,masks,label(r,_score(w,r['model']),r['second_found']),t0,
                {'used':len(ra),'extra_acts':ra,'second_found':bool(r['second_found']),'capped':r['capped']})


def arm_S5(w,seed):
    sw=StepWorld(w);masks,acts,_=passive(sw,seed);t0=perf_counter()
    r=identify6(masks,acts,w.k,M,N_MAX,t0+ARM_BUDGET,SOLVER4)
    return _rec(w,r,acts,masks,label(r,_score(w,r['model']),r['second_found']),t0,{'used':0,'second_found':bool(r['second_found'])})


def arm_S1(w,seed):
    sw=StepWorld(w);masks,acts,_=passive(sw,seed);t0=perf_counter()
    r=identify_trace(masks,acts,w.k,M,N_MAX,t0+ARM_BUDGET,SOLVER4)
    second=(not r['unknown']) and r['n_min'] is not None and not r['unique']
    return _rec(w,r,acts,masks,label(r,_score(w,r['model']),second),t0,{'used':0,'second_found':bool(second)})


def run_case(seed,family):
    w=W.world(seed,family);tr=W.trajectory(w,seed,EPS);sw=StepWorld(w);_,_,rd=passive(sw,seed)
    check(rd==list(tr['readings']) and list(tr['actions'])==list(W.actions(seed,EPS,w.k)),'prefix differs from worlds_026.trajectory')
    arms={'A8':arm_A8(w,seed)}
    arms['A8_random']=arm_A8_random(w,seed,arms['A8']['used']);arms['S5']=arm_S5(w,seed);arms['S1']=arm_S1(w,seed)
    return {'schema':SCHEMA_CASE,'family':family,'seed':seed,'eps':EPS,'n':w.n,'k':w.k,'arms':arms,
            'truth_reachable':len(canonical_bfs(w.transitions,w.emissions,w.start)[1])}


def jobs_for(plan,block):
    if block=='main':
        R=target_ranges(plan);return [('main',f,s) for f in FAM_ORDER for s in range(R[f][0],R[f][1]+1)]
    if block=='smoke':return [('smoke',f,SMOKE[0]+i) for i,f in enumerate(SMOKE_FAMS)]
    raise ValueError(block)


def key(job):return '/'.join(map(str,job))


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
    """The 032 RESULTS / SCIENTIFIC / SEAL writer with the 033 schema, plan and freeze."""
    from brute.evaluation import no_time
    smoke=block!='main'
    result={'schema':'brute.study.v30_0','plan':plan,'block':block,'smoke':smoke,'complete':complete,'job_keys':keys,'cases':cases,**extra}
    write_new(output/'RESULTS.json',result);write_new(output/'SCIENTIFIC.json',no_time(result))
    write_new(output/'SEAL.json',{'study':plan['study'],'block':block,'results_sha256':sha(output/'RESULTS.json'),
        'scientific_sha256':sha(output/'SCIENTIFIC.json'),'plan_sha256':sha(PLAN),'freeze_sha256':None if smoke else sha(FREEZE),
        'case_count':len(cases),'expected_case_count':len(keys),'complete':complete,'smoke':smoke,
        **({'missing_job_keys':extra['missing_job_keys']} if 'missing_job_keys' in extra else {})})


def seal_partial(output,block,limit=None,reason='study cap',extra_checkpoint=None):
    """Seal what is there (as study 032)."""
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
    if a.block!='main':check(not Path(out).resolve().is_relative_to(STUDY_DIR.resolve()),'smoke output must not be inside results/study-033')
    if a.seal_partial:print('sealed partial',seal_partial(out,a.block,a.limit,a.reason,a.snapshot))
    else:run(out,a.workers,a.block,a.limit);print('done')
