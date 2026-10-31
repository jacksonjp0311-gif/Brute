"""Study BRUTE-0340-SOUND-NOISY-STOP-037 runner (experiments/BRUTE_PLAN_037.json; deviation #146 fixes every definition added
here). New file; NoisyWorld, passive(), truth_flips, labels and checkpoint/seal plumbing are re-stated from the frozen
experiments/brute_study_036.py (not imported, so no 036 module-level state is loaded).

Cases: noisy_scale12 (12, eps 0.05), clean_scale12 (12, eps 0), noisy_scale8 (12, eps 0.05), control (6, control_cycle3,
eps 0) = 42, dispatched longest first in that order. World access: NoisyWorld (reset / step / reread); every raw read takes
the next row of the seeded flip stream worlds_026.flips(seed, eps, HORIZON + FLIP_EXTRA); each arm gets a fresh NoisyWorld
(common random numbers). Declared bound N = the family's nominal size (8, 12, 3); declared rate 0.05 on every case (clean
and control included, as in 036), so B_max(3) = 6 and B_max(5) = 2 everywhere.
Timer armed at QUERY_S = 9.0 s for every arm (plan query_timer_s); GQB12 bound 10.5 s.
Arms, in this order, each with its own 120 s budget:
  A12_r5         brute.scalesearch12.active12, r 5, doubling probe, sound stop (B_max confirmation), B_max 2;
  A12_r3         r 3, doubling probe, sound stop, B_max 6;
  A12_r3_nostop  r 3, doubling probe, frozen A11 stop (ablation), B_max 6;
  A11_r3         brute.scalesearch11.active11 (frozen), r 3, bisection, B_max 6 (control);
  A11_r5         frozen, r 5, bisection, B_max 2 (control);
  S7             scalesearch10.identify10 on the single-read passive prefix, B 27, n_max 16 (context).
Base trace: position t is read r times (the step's read, then r - 1 re-reads) and fused by per-bit majority; executed words
likewise; K = 64 counts steps. within_budget (per arm): the truth's flips over the fused trace <= the arm's B_max.
  PYTHONPATH=. python experiments/brute_study_037.py --block main --workers 8
  PYTHONPATH=. python experiments/brute_study_037.py --block smoke --output /tmp/x --workers 8
"""
from __future__ import annotations
import argparse,time
from pathlib import Path
from time import perf_counter
from concurrent.futures import ProcessPoolExecutor,as_completed
from brute.scalesearch import canonical_bfs
from brute.scalesearch7 import flip_budget,_cost
from brute.scalesearch8 import run_word
from brute import scalesearch10 as S10
from brute import scalesearch11 as S11
from brute import scalesearch12 as S12
from experiments import worlds_026 as W
from experiments import brute_study_033 as S33
from experiments.brute_study_033 import _unexercised,_score
from experiments.brute_study_034 import behaviour_equal,label9,_verd
from experiments.brute_common_037 import PLAN,FREEZE,STUDY_DIR,load,sha,write_new,check_freeze,check,Checkpoint,HOOK
from scripts.check_seeds_037 import check_run_seeds,target_ranges,SMOKE,FAMILY_OF,EPS_OF

M=1<<W.S_BITS;S=W.S_BITS;SOLVER4='g3';QUERY_S=9.0;Q_BOUND=10.5;N_MAX=16;EPS_DECLARED=0.05;FLIP_EXTRA=3000
NB=(W.HORIZON+1)*S;B_END=flip_budget(NB,EPS_DECLARED)
B_MAX11={r:S11.b_max11(NB,EPS_DECLARED,r) for r in S11.R11}
BUDGET=120.0;K=64
N_DECLARED={'scale8':8,'scale12':12,'control_cycle3':3}
KEY_ORDER=('noisy_scale12','clean_scale12','noisy_scale8','control')
SCHEMA_CASE='brute.case.v34_0'
A12_ARMS={'A12_r5':(5,'double','sound'),'A12_r3':(3,'double','sound'),'A12_r3_nostop':(3,'double','a11')}
A11_ARMS={'A11_r3':(3,'bisect'),'A11_r5':(5,'bisect')}
ORDER=('A12_r5','A12_r3','A12_r3_nostop','A11_r3','A11_r5','S7')
SMOKE_KEYS=('noisy_scale12','noisy_scale12','clean_scale12','clean_scale12','noisy_scale8','noisy_scale8','control')


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


def passive(nw,seed,eps,r=1):
    """Base trace over the seeded passive actions; r > 1: r raw reads per position fused by majority. -> fused, acts, raw."""
    acts=list(W.actions(seed,eps,nw.k));first=nw.reset();raw=[[first]+[nw.reread() for _ in range(r-1)]]
    for a in acts:
        o=nw.step(a);raw.append([o]+[nw.reread() for _ in range(r-1)])
    rd=[S11.majority(x) if r>1 else x[0] for x in raw];return rd,acts,raw


def truth_flips(w,acts,readings):
    q=w.start;f=_cost(w.emissions[q],readings[0],S)
    for a,o in zip(acts,readings[1:]):q=w.transitions[q][a];f+=_cost(w.emissions[q],o,S)
    return f


def _qmax(qw):return max(qw) if qw else None


def _common(w,lab,stop,model,acts,rd,t0,qw,bmax,nw,extra):
    tf=truth_flips(w,acts,rd)
    return {'label':lab,'ID':int(lab=='ID'),'stop':stop,'unknown':stop=='unknown' or lab=='IDU','model':model,
            'canonical_match':bool(_score(w,model)),
            'behaviour_match':bool(model is not None and behaviour_equal(model[0],model[1],0,w.transitions,w.emissions,w.start)),
            'truth_flips_trace':tf,'B_max':bmax,'within_budget':tf<=bmax,'T_final':len(acts),'truth_pairs_unexercised':_unexercised(w,acts),
            'steps':nw.steps,'reads':nw.reads,'reads_per_step':nw.reads/(nw.steps+1),'world_flips_drawn':nw.flipped,
            'arm_wall_informational':perf_counter()-t0,'query_max_s':_qmax(qw),'queries':len(qw),
            'queries_over_bound':sum(1 for q in qw if q>Q_BOUND),**extra}


def _active_record(w,res,T0,bmax):
    """Per-round record; a word taken from the B_max confirmation is checked against a rival fitting B_max, not B."""
    tr=res['trace'];f=res['final'];rounds=[];wall=[q for x in res['rounds'] for q in x['query_walls']]
    for x in res['rounds']:
        T=x['T'];B=x['B'];sub=S10.Trace10(tr.readings[:T+1],tr.acts[:T],S)
        rr={k_:x.get(k_) for k_ in ('T','B','n_min','check','capped','M1','s1','raise_to','raise_status','reps','probes')}
        rr.update(queries=len(x['query_walls']),query_max_s=_qmax(x['query_walls']),future=_verd(x['future']),start=_verd(x['start']),
                  truth_flips=truth_flips(w,tr.acts[:T],tr.readings[:T+1]))
        if 'confirm' in x:
            C=x['confirm'];rr['confirm']={'verdict':C['verdict'],'B_max':C['B_max'],'future':_verd(C['future']),'start':_verd(C['start'])}
        if x['M1'] is not None:rr['M1_fits']=bool(S10.fits(x['M1'],sub,B))
        if 'word' in x:
            Bw=bmax if 'confirm' in x else B
            (d1,e1),(d2,e2)=x['M1'],x['M2'];w_=x['word'];rr.update(word=w_,M2=x['M2'],s2=x['s2'],M2_fits=bool(S10.fits(x['M2'],sub,Bw)),word_from_confirm='confirm' in x)
            p1=run_word(d1,e1,x['s1'],w_);p2=run_word(d2,e2,x['s2'],w_)
            rr['word_sound']=bool(('pred1' not in x or (p1==x['pred1'] and p2==x['pred2'])) and p1[:-1]==p2[:-1] and p1[-1]!=p2[-1])
            if 'obs' in x:rr.update(executed=True,obs=x['obs'],raw=x['raw'])
            else:rr['executed']=False
        rounds.append(rr)
    fm=f['model'];probes=[p for r in rounds for p in (r.get('probes') or [])]
    extra={'K':K,'used':res['used'],'B_final':res['B'],'B_history':res['B_history'],'rounds':rounds,'n_rounds':len(rounds),
           'extra_acts':tr.acts[T0:],'extra_readings':tr.readings[T0+1:],'n_min':f['n_min'],'future':_verd(f.get('future')),
           'start':_verd(f.get('start')),'capped':sum(x['capped'] for x in res['rounds']),
           'words_checked':sum(1 for r in rounds if r.get('word')),'words_unsound':sum(1 for r in rounds if r.get('word') and not r['word_sound']),
           'models_unfit':sum(1 for r in rounds if r.get('M1_fits') is False or r.get('M2_fits') is False),
           'truth_over_Bmax_rounds':sum(1 for r in rounds if r['truth_flips']>bmax),
           'confirmations':[r['confirm']['verdict'] for r in rounds if 'confirm' in r],
           'least_B_searches':sum(1 for r in rounds if r.get('raise_status') is not None),'probes_total':len(probes),
           'probes_capped':sum(1 for p in probes if p[1] is None)}
    if fm is not None and f.get('s1') is not None:
        tq=S10.final_state(w.transitions,tr.acts,w.start);extra['M1_future_match']=bool(behaviour_equal(fm[0],fm[1],f['s1'],w.transitions,w.emissions,tq))
    return tr,fm,wall,extra


def arm_A12(w,seed,eps,N,r,search,stop):
    nw=NoisyWorld(w,seed,eps);rd,acts,raw=passive(nw,seed,eps,r);T0=len(acts);t0=perf_counter();bmax=B_MAX11[r]
    res=S12.active12(rd,acts,w.k,S,N,nw.step,nw.reread,t0+BUDGET,K,bmax,r,search,stop,QUERY_S,SOLVER4,HOOK)
    tr,fm,wall,extra=_active_record(w,res,T0,bmax);check(nw.steps==len(tr.acts),'step count')
    check(res['reads']+r*(T0+1)==nw.reads,'A12 read count')
    extra.update(N=N,r=r,search=search,stop_rule=stop,base_readings=rd,prefix_truth_flips_raw_first=truth_flips(w,acts,[x[0] for x in raw]))
    return _common(w,label9(res['stop'],w,fm),res['stop'],fm,tr.acts,tr.readings,t0,wall,bmax,nw,extra)


def arm_A11(w,seed,eps,N,r,search):
    nw=NoisyWorld(w,seed,eps);rd,acts,raw=passive(nw,seed,eps,r);T0=len(acts);t0=perf_counter();bmax=B_MAX11[r]
    res=S11.active11(rd,acts,w.k,S,N,nw.step,nw.reread,t0+BUDGET,K,bmax,r,search,QUERY_S,SOLVER4,HOOK)
    tr,fm,wall,extra=_active_record(w,res,T0,bmax);check(nw.steps==len(tr.acts),'step count')
    check(res['reads']+r*(T0+1)==nw.reads,'A11 read count')
    extra.update(N=N,r=r,search=search,stop_rule='a11',base_readings=rd,prefix_truth_flips_raw_first=truth_flips(w,acts,[x[0] for x in raw]))
    return _common(w,label9(res['stop'],w,fm),res['stop'],fm,tr.acts,tr.readings,t0,wall,bmax,nw,extra)


def arm_S7(w,seed,eps):
    nw=NoisyWorld(w,seed,eps);rd,acts,_=passive(nw,seed,eps);t0=perf_counter()
    r=S10.identify10(rd,acts,w.k,S,N_MAX,B_END,t0+BUDGET,QUERY_S,SOLVER4,HOOK)
    lab=S33.label(r,_score(w,r['model']),r['second_found'])
    return _common(w,lab,'unknown' if r['unknown'] else 'done',r['model'],acts,rd,t0,r['query_walls'],B_END,nw,
                   {'used':0,'n_min':r['n_min'],'unique':bool(r['unique']),'second_found':bool(r['second_found']),'B_final':B_END,'capped':r['capped']})


def run_case(seed,pkey):
    fam=FAMILY_OF[pkey];eps=EPS_OF[pkey];w=W.world(seed,fam);tr=W.trajectory(w,seed,eps);nw=NoisyWorld(w,seed,eps);rd,acts,_=passive(nw,seed,eps)
    check(rd==list(tr['readings']) and acts==list(tr['actions']),'prefix differs from worlds_026.trajectory')
    N=N_DECLARED[fam];check(w.n==N,'world size differs from the declared bound')
    arms={nm:arm_A12(w,seed,eps,N,r,sr,st) for nm,(r,sr,st) in A12_ARMS.items()}
    arms.update({nm:arm_A11(w,seed,eps,N,r,sr) for nm,(r,sr) in A11_ARMS.items()})
    arms['S7']=arm_S7(w,seed,eps)
    return {'schema':SCHEMA_CASE,'key':pkey,'family':fam,'seed':seed,'eps':eps,'eps_declared':EPS_DECLARED,
            'B_max':{'S7':B_END,**{nm:B_MAX11[v[0]] for nm,v in {**A12_ARMS,**A11_ARMS}.items()}},
            'n':w.n,'k':w.k,'N':N,'arms':{a:arms[a] for a in ORDER},'prefix_truth_flips':truth_flips(w,acts,rd),
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
    result={'schema':'brute.study.v34_0','plan':plan,'block':block,'smoke':smoke,'complete':complete,'job_keys':keys,'cases':cases,**extra}
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
    if a.block!='main':check(not Path(out).resolve().is_relative_to(STUDY_DIR.resolve()),'smoke output must not be inside results/study-037')
    if a.seal_partial:print('sealed partial',seal_partial(out,a.block,a.limit,a.reason,a.snapshot))
    else:run(out,a.workers,a.block,a.limit);print('done')
