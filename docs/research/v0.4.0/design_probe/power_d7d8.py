"""Pre-registered power analysis for the v0.4.0 D7/D8 re-test (design data: sealed study-005 drift4, main + extended).

Per drift4 seed (3 mask rates pooled) we take the paired stale false-certificate counts (A2, E2) and stale-window
certificate counts. Scenarios: OBS = resample observed seed pairs (the effect as seen in study-005);
HALF = E2 counts binomially thinned to 50% of A2 per seed (the D7/D8 mechanism hypothesis); NULL = E2 := A2 thinned
by 1.0 (no effect). Decision rule (v0.4.0, D78): R = S(E2)/S(A2) with a seed-cluster bootstrap 95% CI (2000 reps).
CONFIRMED iff S(A2) >= 20, CI lower <= 0.5 and CI upper < 0.75 (consistent with halving, excludes a weak effect).
FALSIFIED iff S(A2) >= 20 and CI lower > 0.5 (excludes halving). Otherwise OPEN. (A first rule, 'R <= 0.5 and CI upper
< 1', was rejected in this probe: under the HALF scenario it confirms only ~50% at any N; disclosed.) Power = P(correct verdict | scenario) over 400 simulated studies per N.
"""
import json,random,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from experiments.brute_common_005 import is_stale

def per_seed():
    R=json.load(open(ROOT/'results/study-005/RESULTS.json'))
    out={}
    for c in R['cases']+R['extended_cases']:
        if c['family']!='drift4':continue
        x=out.setdefault(c['seed'],{'A2':0,'E2':0})
        for a in ('A2','E2'):
            x[a]+=sum(r['wrong']+r['counterfactual']['wrong'] for r in c['arms'][a]['trace'] if is_stale(r['step']))
    return [(v['A2'],v['E2']) for v in out.values()]

def ci_ratio(pairs,rnd,B=2000):
    n=len(pairs);rs=[]
    for _ in range(B):
        s=[pairs[rnd.randrange(n)] for _ in range(n)];a=sum(p[0] for p in s);e=sum(p[1] for p in s)
        rs.append(e/a if a else float('inf'))
    rs.sort();return rs[int(.025*B)],rs[int(.975*B)-1]

def verdict(pairs,rnd):
    a=sum(p[0] for p in pairs);e=sum(p[1] for p in pairs)
    if a<20:return 'OPEN'
    lo,hi=ci_ratio(pairs,rnd,1000)
    if lo>0.5:return 'FALSIFIED'
    if hi<0.75:return 'CONFIRMED'
    return 'OPEN'

if __name__=='__main__':
    base=per_seed();rnd=random.Random(20261025);out={'design_seeds':len(base),'S_A2':sum(p[0] for p in base),'S_E2':sum(p[1] for p in base),'by_N':{}}
    for N in (192,288,384,480,576,720):
        res={'OBS':{},'HALF':{},'NULL':{}}
        for sc in res:
            for _ in range(200):
                s=[base[rnd.randrange(len(base))] for _ in range(N)]
                if sc=='HALF':s=[(a,sum(rnd.random()<.5 for _ in range(a))) for a,_ in s]
                if sc=='NULL':s=[(a,a) for a,_ in s]
                v=verdict(s,rnd);res[sc][v]=res[sc].get(v,0)+1
        out['by_N'][N]=res;print(N,res,flush=True)
    json.dump(out,open(Path(__file__).parent/'outputs/power_d7d8.json','w'),indent=1)
