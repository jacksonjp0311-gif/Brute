"""Study BRUTE-0320-NOISY-ACTIVE-ID-035 runner (experiments/BRUTE_PLAN_035.json; deviation #142 fixes every definition
added here). New file; the A9 arm logic, labels and checkpoint/seal plumbing follow experiments/brute_study_034.py (frozen,
imported where unchanged).

Cases: scale16_clean (6, eps 0, secondary), noisy_scale12 (12, eps 0.05), clean_scale12 (12, eps 0), noisy_scale8 (12,
eps 0.05), control (6, control_cycle3, eps 0) = 48, dispatched longest first in that order. World access: NoisyWorld, a
step-only wrapper with reset(), step(a) and reread(); every call returns the true state's code with the next row of the
seeded flip stream worlds_026.flips(seed, eps, HORIZON + FLIP_EXTRA) applied (sequential RNG, so the first HORIZON + 1 rows
are the plan's prefix flips; the prefix is rechecked against worlds_026.trajectory). Each arm gets a fresh NoisyWorld
(common random numbers). Declared bound N = the family's nominal size (8, 12, 16, 3). Declared rate eps_declared = 0.05 on
every case (given to A10_fixed and S7); B_max = B_end = flip_budget(177 readings * 2 bits) = 27 for A10.
Arms, in this order, each with its own budget (120 s; 240 s at 16 states):
  A10       brute.scalesearch10.active10 (adaptive, B0 0, B_max 27, K 64 / 128 at 16, r 3, 10 s cap, host hook);
  A10_fixed active10 with adaptive False and B0 = B_end = 27 from the first round;
  A9        brute.scalesearch9.active9 (frozen) on the noisy reading masks, single reads, K9, with the host hook patched into
            the module's _RegionQ (proxy solver forcing expect_interrupt; timer at min(deadline, query start + 10 s));
  S7        brute.scalesearch10.identify10 on the noisy passive prefix with B = B_end = 27, n_max 16 (S7 encoding + the
            031 identify probe);
  S5        brute.scalesearch6.identify6 (frozen) on the passive prefix masks, n_max 16, with the host hook patched into the
            module's _RegionID (per-query deadline min(deadline, start + 10 s), timer interrupt, walls recorded host-side).
Labels: A10 / A10_fixed / A9 as label9 (IDU unknown; AMB K_spent; IDF; ID iff stop ID and M1 behaviour-equal to the truth
from the start state; WRONG otherwise, including 'none'); S7 / S5 as the 033 label (IDU unknown; AMB second machine; ID iff
unique and canonical match; WRONG otherwise). within_budget (per arm): the truth's flips over the arm's final trace (the
fused, majority-voted readings for A10 / A10_fixed; the single readings for A9; the prefix for S7 / S5) <= B_max = 27.
Soundness per A10 round (evaluator): M1 / M2 fit the round trace under the round's B, the executed word re-simulated (equal
codes before its last action, different after), truth flips over the round trace recorded.
  PYTHONPATH=. python experiments/brute_study_035.py --block main --workers 8
  PYTHONPATH=. python experiments/brute_study_035.py --block smoke --output /tmp/x --workers 8
"""
from __future__ import annotations
import argparse,time
from pathlib import Path
from time import perf_counter
from concurrent.futures import ProcessPoolExecutor,as_completed
from brute.region import codes_mask
from brute.scalesearch import canonical_bfs
from brute.scalesearch7 import flip_budget,_cost
from brute.scalesearch8 import run_word,_RegionQ as _RegionQ8
from brute import scalesearch9 as S9
from brute import scalesearch6 as S6
from brute import scalesearch10 as S10
from experiments import worlds_026 as W
from experiments import brute_study_033 as S33
from experiments.brute_study_033 import _unexercised,_score
from experiments.brute_study_034 import behaviour_equal,label9,_verd
from experiments.brute_common_035 import PLAN,FREEZE,STUDY_DIR,load,sha,write_new,check_freeze,check,Checkpoint,HOOK
from scripts.check_seeds_035 import check_run_seeds,target_ranges,SMOKE,FAMILY_OF,EPS_OF

M=1<<W.S_BITS;S=W.S_BITS;SOLVER4='g3';QUERY_S=10.0;N_MAX=16;EPS_DECLARED=0.05;FLIP_EXTRA=1200
B_END=flip_budget((W.HORIZON+1)*S,EPS_DECLARED);B_MAX=B_END
BUDGET={8:120.0,12:120.0,16:240.0,3:120.0}
N_DECLARED={'scale8':8,'scale12':12,'scale16':16,'control_cycle3':3}
KEY_ORDER=('scale16_clean','noisy_scale12','clean_scale12','noisy_scale8','control')
SCHEMA_CASE='brute.case.v32_0'
ORDER=('A10','A10_fixed','A9','S7','S5')
SMOKE_KEYS=('scale16_clean','noisy_scale12','noisy_scale12','clean_scale12','clean_scale12','noisy_scale8','noisy_scale8','control')
QUERY_WALLS=[]


# ---- host-side hook patches for the frozen arms (no source change) ----
class _ISolver:
    """Proxy: every solve_limited call runs with expect_interrupt=True; everything else is delegated."""
    def __init__(self,s):self._s=s
    def solve_limited(self,assumptions=[],expect_interrupt=False):return self._s.solve_limited(assumptions=assumptions,expect_interrupt=True)
    def __getattr__(self,nm):return getattr(self._s,nm)


class _RegionQH(_RegionQ8):
    def __init__(self,*a,**kw):
        _RegionQ8.__init__(self,*a,**kw);self.s=_ISolver(self.s)

    def _solve(self,assume):
        if self._skip:return _RegionQ8._solve(self,assume)
        t0=perf_counter();dl=min(self._dl,t0+self._owner.query_s);tok=HOOK.arm(self.s._s.interrupt,dl-t0)
        try:return _RegionQ8._solve(self,assume)
        finally:HOOK.disarm(tok);self.s._s.clear_interrupt()


_RegionID0=S6._RegionID


class _RegionIDH(_RegionID0):
    def __init__(self,*a,**kw):
        _RegionID0.__init__(self,*a,**kw);self.s=_ISolver(self.s)

    def _solve(self,assume):
        if self._skip:return _RegionID0._solve(self,assume)
        t0=perf_counter();full=self._dl;self._dl=min(full,t0+QUERY_S);tok=HOOK.arm(self.s._s.interrupt,self._dl-t0)
        try:return _RegionID0._solve(self,assume)
        finally:HOOK.disarm(tok);self.s._s.clear_interrupt();self._dl=full;QUERY_WALLS.append(perf_counter()-t0)


S9._RegionQ=_RegionQH;S6._RegionID=_RegionIDH


# ---- world ----
class NoisyWorld:
    """Step-only access with seeded reading flips: reset() / step(a) / reread() -> noisy reading (bit tuple)."""
    def __init__(self,w,seed,eps):
        self._w=w;self._h=None;self.k=w.k;self.steps=0;self.reads=0;self.flipped=0
        self._fl=W.flips(seed,eps,W.HORIZON+FLIP_EXTRA)

    def _read(self):
        check(self.reads<len(self._fl),'flip stream exhausted');fr=self._fl[self.reads];self.reads+=1;self.flipped+=sum(fr)
        return tuple(b^int(f) for b,f in zip(W.bits(self._w.emissions[self._h]),fr))

    def reset(self):self._h=self._w.start;self.steps=0;self.reads=0;self.flipped=0;return self._read()

    def step(self,a):
        if a not in range(self.k):raise ValueError('bad action')
        self._h=self._w.transitions[self._h][a];self.steps+=1;return self._read()

    def reread(self):return self._read()


def passive(nw,seed,eps):
    acts=list(W.actions(seed,eps,nw.k));rd=[nw.reset()]
    for a in acts:rd.append(nw.step(a))
    return rd,acts


def truth_flips(w,acts,readings):
    q=w.start;f=_cost(w.emissions[q],readings[0],S)
    for a,o in zip(acts,readings[1:]):q=w.transitions[q][a];f+=_cost(w.emissions[q],o,S)
    return f


def _qmax(qw):return max(qw) if qw else None


def _common(w,lab,stop,model,acts,rd,t0,qw,extra):
    tf=truth_flips(w,acts,rd)
    return {'label':lab,'ID':int(lab=='ID'),'stop':stop,'unknown':stop=='unknown' or lab=='IDU','model':model,
            'canonical_match':bool(_score(w,model)),
            'behaviour_match':bool(model is not None and behaviour_equal(model[0],model[1],0,w.transitions,w.emissions,w.start)),
            'truth_flips_trace':tf,'within_budget':tf<=B_MAX,'T_final':len(acts),'truth_pairs_unexercised':_unexercised(w,acts),
            'arm_wall_informational':perf_counter()-t0,'query_max_s':_qmax(qw),'queries':len(qw),**extra}


def arm_A10(w,seed,eps,N,adaptive):
    nw=NoisyWorld(w,seed,eps);rd,acts=passive(nw,seed,eps);T0=len(acts);t0=perf_counter();K=S10.K10.get(N,64)
    res=S10.active10(rd,acts,w.k,S,N,nw.step,nw.reread,t0+BUDGET[N],K,B_MAX,0 if adaptive else B_END,adaptive,S10.R10,QUERY_S,SOLVER4,HOOK)
    tr=res['trace'];f=res['final'];check(nw.steps==len(tr.acts),'step count')
    rounds=[];wall=[q for x in res['rounds'] for q in x['query_walls']]
    for x in res['rounds']:
        T=x['T'];B=x['B'];sub=S10.Trace10(tr.readings[:T+1],tr.acts[:T],S)
        rr={k_:x.get(k_) for k_ in ('T','B','n_min','check','capped','M1','s1','raise_to','raise_status','reps')}
        rr.update(queries=len(x['query_walls']),query_max_s=_qmax(x['query_walls']),future=_verd(x['future']),start=_verd(x['start']),
                  truth_flips=truth_flips(w,tr.acts[:T],tr.readings[:T+1]))
        if x['M1'] is not None:rr['M1_fits']=bool(S10.fits(x['M1'],sub,B))
        if 'word' in x:
            (d1,e1),(d2,e2)=x['M1'],x['M2'];w_=x['word'];rr.update(word=w_,M2=x['M2'],s2=x['s2'],M2_fits=bool(S10.fits(x['M2'],sub,B)))
            p1=run_word(d1,e1,x['s1'],w_);p2=run_word(d2,e2,x['s2'],w_)
            rr['word_sound']=bool(('pred1' not in x or (p1==x['pred1'] and p2==x['pred2'])) and p1[:-1]==p2[:-1] and p1[-1]!=p2[-1])
            if 'obs' in x:rr.update(executed=True,obs=x['obs'],raw=x['raw'])
            else:rr['executed']=False
        rounds.append(rr)
    stop=res['stop'];lab=label9(stop,w,f['model']);fm=f['model']
    extra={'N':N,'K':K,'used':res['used'],'B_final':res['B'],'B_history':res['B_history'],'rounds':rounds,'n_rounds':len(rounds),
           'extra_acts':tr.acts[T0:],'extra_readings':tr.readings[T0+1:],'reads':nw.reads,'world_flips_drawn':nw.flipped,
           'n_min':f['n_min'],'future':_verd(f.get('future')),'start':_verd(f.get('start')),'capped':sum(x['capped'] for x in res['rounds']),
           'words_checked':sum(1 for r in rounds if r.get('word')),'words_unsound':sum(1 for r in rounds if r.get('word') and not r['word_sound']),
           'truth_over_Bmax_rounds':sum(1 for r in rounds if r['truth_flips']>B_MAX),'adaptive':adaptive}
    if fm is not None and f.get('s1') is not None:
        tq=S10.final_state(w.transitions,tr.acts,w.start);extra['M1_future_match']=bool(behaviour_equal(fm[0],fm[1],f['s1'],w.transitions,w.emissions,tq))
    return _common(w,lab,stop,fm,tr.acts,tr.readings,t0,wall,extra)


def arm_A9(w,seed,eps,N):
    nw=NoisyWorld(w,seed,eps);rd,acts=passive(nw,seed,eps);T0=len(acts);t0=perf_counter()
    masks=[codes_mask(o,S) for o in rd];obs=lambda a:codes_mask(nw.step(a),S)
    res=S9.active9(masks,acts,w.k,M,N,obs,t0+BUDGET[N],S9.K9,QUERY_S,SOLVER4)
    fa,f=res['acts'],res['final'];check(nw.steps==len(fa),'step count')
    wall=[q for x in res['rounds'] for q in x['query_walls']]
    full=W.flips(seed,eps,W.HORIZON+FLIP_EXTRA);q=S10.final_state(w.transitions,acts,w.start);rdx=list(rd)
    for a in fa[T0:]:q=w.transitions[q][a];rdx.append(tuple(b^int(z) for b,z in zip(W.bits(w.emissions[q]),full[len(rdx)])))
    check([codes_mask(o,S) for o in rdx]==list(res['masks']),'A9 readings differ from the flip stream')
    lab=label9(res['stop'],w,f['model'])
    return _common(w,lab,res['stop'],f['model'],fa,rdx,t0,wall,{'N':N,'used':res['used'],'n_min':f['n_min'],'n_rounds':len(res['rounds']),
                   'capped':sum(x['capped'] for x in res['rounds']),'extra_acts':fa[T0:],'future':_verd(f.get('future')),'start':_verd(f.get('start'))})


def arm_S7(w,seed,eps):
    nw=NoisyWorld(w,seed,eps);rd,acts=passive(nw,seed,eps);t0=perf_counter()
    r=S10.identify10(rd,acts,w.k,S,N_MAX,B_END,t0+BUDGET[w.n],QUERY_S,SOLVER4,HOOK)
    lab=S33.label(r,_score(w,r['model']),r['second_found'])
    return _common(w,lab,'unknown' if r['unknown'] else 'done',r['model'],acts,rd,t0,r['query_walls'],
                   {'used':0,'n_min':r['n_min'],'unique':bool(r['unique']),'second_found':bool(r['second_found']),'B':B_END,'capped':r['capped']})


def arm_S5(w,seed,eps):
    nw=NoisyWorld(w,seed,eps);rd,acts=passive(nw,seed,eps);t0=perf_counter();masks=[codes_mask(o,S) for o in rd];QUERY_WALLS.clear()
    r=S6.identify6(masks,acts,w.k,M,N_MAX,t0+BUDGET[w.n],SOLVER4)
    lab=S33.label(r,_score(w,r['model']),r['second_found'])
    return _common(w,lab,'unknown' if r['unknown'] else 'done',r['model'],acts,rd,t0,list(QUERY_WALLS),
                   {'used':0,'n_min':r['n_min'],'unique':bool(r['unique']),'second_found':bool(r['second_found'])})


def run_case(seed,pkey):
    fam=FAMILY_OF[pkey];eps=EPS_OF[pkey];w=W.world(seed,fam);tr=W.trajectory(w,seed,eps);nw=NoisyWorld(w,seed,eps);rd,acts=passive(nw,seed,eps)
    check(rd==list(tr['readings']) and acts==list(tr['actions']),'prefix differs from worlds_026.trajectory')
    N=N_DECLARED[fam];check(w.n==N,'world size differs from the declared bound')
    arms={'A10':arm_A10(w,seed,eps,N,True),'A10_fixed':arm_A10(w,seed,eps,N,False),'A9':arm_A9(w,seed,eps,N),
          'S7':arm_S7(w,seed,eps),'S5':arm_S5(w,seed,eps)}
    return {'schema':SCHEMA_CASE,'key':pkey,'family':fam,'seed':seed,'eps':eps,'eps_declared':EPS_DECLARED,'B_max':B_MAX,
            'n':w.n,'k':w.k,'N':N,'arms':arms,'prefix_truth_flips':truth_flips(w,acts,rd),
            'truth_reachable':len(canonical_bfs(w.transitions,w.emissions,w.start)[1])}


def jobs_for(plan,block):
    if block=='main':
        R=target_ranges(plan);return [('main',k,s) for k in KEY_ORDER for s in range(R[k][0],R[k][1]+1)]
    if block=='smoke':return [('smoke',k,SMOKE[0]+i) for i,k in enumerate(SMOKE_KEYS)]
    raise ValueError(block)


def key(job):return f'{job[0]}:{job[1]}:{job[2]}'


def check_job(job,plan):
    block,k,seed=job;check(k in KEY_ORDER,'key')
    if block=='main':check_run_seeds('target',[seed],plan,key=k)
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
    from brute.evaluation import no_time
    smoke=block!='main'
    result={'schema':'brute.study.v32_0','plan':plan,'block':block,'smoke':smoke,'complete':complete,'job_keys':keys,'cases':cases,**extra}
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
    if a.block!='main':check(not Path(out).resolve().is_relative_to(STUDY_DIR.resolve()),'smoke output must not be inside results/study-035')
    if a.seal_partial:print('sealed partial',seal_partial(out,a.block,a.limit,a.reason,a.snapshot))
    else:run(out,a.workers,a.block,a.limit);print('done')
