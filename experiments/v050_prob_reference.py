"""Second implementation (same author, no brute / bgr import) of the 2x2 forecast PROBABILITIES in the v0.90 regime.

Added after the v0.4.0 review (finding M2: the G11 second implementation checked v0.90-source probabilities only for
internal consistency). Written 2026-10-25 ~06:20-06:35 EDT, AFTER study-007 run_start (06:13:54) and after the source
freeze: this is an additional, non-pre-registered audit, not a gate (BRUTE_DEVIATIONS_007, item D-prob).

What is recomputed, for every step of every 2x2 trace of the audited arms, for the taken AND the untaken action, when
the recorded forecast_source is 'v090':
  p_legacy  = predictive mixture of the v0.89 latent version space (deterministic Moore machines with 1..3 states, two
              actions, 4 emission codes, start state 0, uniform prior over the class sizes, each class weighted by its
              surviving fraction), computed here by counting completions of partial machines (exact Fractions) instead
              of enumerating the catalogue;
  relaxed   = uniform on the recorded family support (the support itself is checked by the G11 count);
  p90       = 0.92 * p_legacy + 0.08 * relaxed   (relaxed alone once the latent space is contradicted; uniform if no support)
  published = (1 - eps) * p90 + eps / 4.
Also re-derived from the recomputed taken-branch vector: logloss, surprise, min_probability.
Mutation test: probability swaps (reversed counterfactual vector; reversed taken vector with logloss/surprise/min
re-derived coherently) in 20 distinct traces, random.Random(20261025).

  python -m experiments.v050_prob_reference --results-dir results/study-007 --workers 6 --mutate 20 --out PROB.json
"""
from __future__ import annotations
import argparse,copy,json,random,sys
from fractions import Fraction
from math import log
from multiprocessing import Pool
from pathlib import Path

SMOOTH=Fraction(2,25)  # 0.08
TOL=1e-11  # recorded vectors are rounded to 12 d.p.


def compat(obs):
    return frozenset(c for c in range(4) if (obs[0] is None or ((c>>1)&1)==obs[0]) and (obs[1] is None or (c&1)==obs[1]))


class Latent:
    """Partial Moore machines: (assigned transitions, allowed emission set per state, current state)."""
    def __init__(self,obs,sizes=(1,2,3)):
        c0=compat(obs);self.parts={}
        for n in sizes:
            em=[c0]+[frozenset(range(4))]*(n-1)
            self.parts[n]=[({},tuple(em),0)] if c0 else []
        self.valid=any(self.parts.values())

    @staticmethod
    def _count(n,tr,em):
        k=n**(2*n-len(tr))
        for e in em:k*=len(e)
        return k

    def predict(self,a):
        post={};votes={}
        for n,ps in self.parts.items():
            tot=0;v=[Fraction(0)]*4
            for tr,em,cur in ps:
                cnt=self._count(n,tr,em);tot+=cnt
                succ=[tr[(cur,a)]] if (cur,a) in tr else list(range(n))
                for t in succ:
                    w=Fraction(cnt,len(succ)*len(em[t]))
                    for c in em[t]:v[c]+=w
            post[n]=Fraction(tot,n**(2*n)*4**n);votes[n]=(v,tot)
        z=sum(post.values())
        out=[Fraction(0)]*4
        for n,(v,tot) in votes.items():
            if tot:
                for c in range(4):out[c]+=post[n]/z*v[c]/tot
        s=sum(out);return [x/s for x in out]

    def observe(self,a,obs):
        C=compat(obs);new={}
        for n,ps in self.parts.items():
            q=[]
            for tr,em,cur in ps:
                succ=[tr[(cur,a)]] if (cur,a) in tr else list(range(n))
                for t in succ:
                    e=em[t]&C
                    if not e:continue
                    tr2=tr if (cur,a) in tr else {**tr,(cur,a):t}
                    q.append((tr2,em[:t]+(e,)+em[t+1:],t))
            new[n]=q
        if any(new.values()):self.parts=new
        else:self.valid=False


def expected(lat,a,support,eps):
    if support is None:p=[Fraction(1,4)]*4
    else:
        rel=[Fraction(1,len(support)) if c in support else Fraction(0) for c in range(4)]
        p=rel if not lat.valid else [(1-SMOOTH)*l+SMOOTH*r for l,r in zip(lat.predict(a),rel)]
    e=Fraction(eps).limit_denominator(10**12) if not isinstance(eps,Fraction) else eps
    return [float((1-e)*x+e/4) for x in p]


def close(x,y):return len(x)==len(y) and all(abs(a-b)<=TOL for a,b in zip(x,y))


def audit(c,arm,eps):
    """Return (steps_checked, v090_forecasts_checked, first mismatch or None)."""
    lat=Latent(tuple(c['initial_visible']));n=0;f=0
    for rec in c['arms'][arm]['trace']:
        a=rec['action'];where=f"{c['family']} {c['seed']} {c['mask_rate']} {arm} step {rec['step']}"
        for b,r in ((a,rec),(1-a,rec['counterfactual'])):
            if r.get('forecast_source')!='v090':continue
            q=expected(lat,b,r['support'],eps);f+=1
            if not close(r['probabilities'],q):return n,f,f'probabilities {where} action {b}: recorded {r["probabilities"]} expected {q}'
        if rec.get('forecast_source')=='v090':
            obs=tuple(rec['observed']);P=rec['probabilities']
            if abs(rec['logloss']+log(max(1e-12,P[rec['actual_emission_EVALUATOR_ONLY']])))>1e-8:return n,f,'logloss '+where
            if abs(rec['surprise']+log(sum(P[x] for x in compat(obs))))>1e-8:return n,f,'surprise '+where
        if 'probabilities' in rec['counterfactual'] and abs(rec['min_probability']-min(min(rec['probabilities']),min(rec['counterfactual']['probabilities'])))>1e-12:return n,f,'min_probability '+where
        lat.observe(a,tuple(rec['observed']));n+=1
    return n,f,None


def _job(x):
    c,arm,eps=x;s,f,m=audit(c,arm,eps);return f"{c['family']}/{c['seed']}/{c['mask_rate']}",arm,s,f,m


def count(cases,arms,eps,workers):
    jobs=[(c,a,eps) for c in cases if c['block']=='2x2' for a in arms if a in c['arms']]
    with Pool(workers) as p:res=p.map(_job,jobs,chunksize=4)
    bad=[{'case':k,'arm':a,'message':m} for k,a,s,f,m in res if m]
    return len(res),sum(f for *_,f,m in res),bad


def mutate(cases,k,arms,seed=20261025):
    rng=random.Random(seed);cases=copy.deepcopy(cases);cand=[]
    for i,c in enumerate(cases):
        if c['block']!='2x2':continue
        for a in arms:
            if a not in c['arms']:continue
            st=[j for j,r in enumerate(c['arms'][a]['trace']) if r.get('forecast_source')=='v090' and r['counterfactual'].get('forecast_source')=='v090'
                and r['probabilities']!=r['probabilities'][::-1] and r['counterfactual']['probabilities']!=r['counterfactual']['probabilities'][::-1]]
            if st:cand.append((i,a,st))
    inj=set()
    for i,a,st in rng.sample(cand,k):
        c=cases[i];r=c['arms'][a]['trace'][rng.choice(st)];kind=rng.choice(('cf_swap','taken_swap_coherent'))
        if kind=='cf_swap':r['counterfactual']['probabilities']=r['counterfactual']['probabilities'][::-1]
        else:
            P=r['probabilities'][::-1];r['probabilities']=P
            r['logloss']=-log(max(1e-12,P[r['actual_emission_EVALUATOR_ONLY']]))
            r['surprise']=-log(sum(P[x] for x in compat(tuple(r['observed']))))
            r['min_probability']=min(min(P),min(r['counterfactual']['probabilities']))
        inj.add((f"{c['family']}/{c['seed']}/{c['mask_rate']}",a))
    return cases,inj


def run(directory,workers=6,mutate_k=0,arms=('A4','A5','M5')):
    d=json.loads((Path(directory)/'RESULTS.json').read_text());eps=d['plan']['open_world_reserve_epsilon']
    two=[c for c in d['cases'] if c['block']=='2x2']
    n,f,bad=count(two,arms,eps,workers)
    import hashlib
    rep={'schema':'brute.second-implementation-probabilities.v1',
         'wording':'second implementation by the same author, no brute or bgr import; post-run addition (not pre-registered); not an independent audit',
         'arms':list(arms),'arm_traces_checked':n,'v090_forecasts_checked':f,'mismatching_arm_traces':len(bad),'mismatches':bad[:200],
         'source_results_sha256':hashlib.sha256((Path(directory)/'RESULTS.json').read_bytes()).hexdigest()}
    if mutate_k:
        mc,inj=mutate(two,mutate_k,arms);_,_,mb=count(mc,arms,eps,workers)
        fl={(b['case'],b['arm']) for b in mb};base={(b['case'],b['arm']) for b in bad}
        rep['mutation_test']={'kinds':['cf_swap','taken_swap_coherent'],'injected':len(inj),'detected_injected':len(inj&fl),
                              'flagged_not_injected':len(fl-inj-base),'passed':inj<=fl and not (fl-inj-base)}
    return rep


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--results-dir',required=True);ap.add_argument('--workers',type=int,default=6)
    ap.add_argument('--mutate',type=int,default=0);ap.add_argument('--out');ap.add_argument('--arms',default='A4,A5,M5')
    a=ap.parse_args();rep=run(a.results_dir,a.workers,a.mutate,tuple(a.arms.split(',')))
    if a.out:
        p=Path(a.out);assert not p.exists(),'refusing overwrite';p.write_text(json.dumps(rep,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:v for k,v in rep.items() if k!='mismatches'},indent=2));print(json.dumps(rep['mismatches'][:3],indent=1))
