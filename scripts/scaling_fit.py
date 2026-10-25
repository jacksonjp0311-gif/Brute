"""Correctly specified scaling fits for GR2-type claims (added 2026-10-25 after v0.4.0 review M1 / 06:17 steering).

Not pre-registered; every number here is Inferred (a model fitted to Observed points). Points are PER CASE (not means of
means). Censored points (enumeration budget exhausted) are EXCLUDED from fits and counted separately: their true value is
only bounded below, so including them would bias the slope down.

Models (ordinary least squares, numpy.linalg.lstsq):
  power        log y = a + b log n          (y ~ n^b)
  exponential  log y = a + c n              (y ~ e^(c n); reported as base e^c per extra state)
  cubic        y     = c0 + c1 n + c2 n^2 + c3 n^3   (for clause counts only; the frozen CNF has O(T n^2 + n^3) clauses)
Reported per model: coefficients, R^2 on the fitted scale, residual SD, and the mean residual at every n (systematic
curvature in those residuals is what rejects a model, not R^2 alone).

  PYTHONPATH=. python scripts/scaling_fit.py --gr2 results/study-006/GR2.json --scaling results/study-007/SCALING_007.json --out X.json
"""
import argparse,json,math
from collections import defaultdict
from pathlib import Path
import numpy as np


def _fit(X,y):
    beta,*_=np.linalg.lstsq(X,y,rcond=None);r=y-X@beta;ss=float(((y-y.mean())**2).sum())
    return beta,r,(1-float((r**2).sum())/ss) if ss>0 else None


def fit(points,models=('power','exponential')):
    """points: list of (n, y) with y>0 for log models."""
    n=np.array([p[0] for p in points],float);y=np.array([p[1] for p in points],float);out={'points':len(points),'n_values':sorted({int(v) for v in n})}
    for m in models:
        if m in('power','exponential'):
            ok=y>0;nn,ly=n[ok],np.log(y[ok]);X=np.column_stack([np.ones_like(nn),np.log(nn) if m=='power' else nn])
            b,r,R2=_fit(X,ly);res={'model':'log y = a + b log n' if m=='power' else 'log y = a + c n','a':round(float(b[0]),4),
                ('b_exponent' if m=='power' else 'c_per_state'):round(float(b[1]),4),'R2_log_scale':None if R2 is None else round(R2,4),
                'residual_sd_log':round(float(r.std(ddof=2)),4) if len(r)>2 else None,'dropped_nonpositive':int((~ok).sum())}
            if m=='exponential':res['growth_factor_per_state']=round(math.exp(float(b[1])),3)
            nv=nn
        else:
            X=np.column_stack([n**j for j in range(4)]);b,r,R2=_fit(X,y)
            res={'model':'y = c0 + c1 n + c2 n^2 + c3 n^3','coef':[round(float(v),4) for v in b],'R2':None if R2 is None else round(R2,6),
                 'residual_sd':round(float(r.std(ddof=4)),3) if len(r)>4 else None};nv=n
        g=defaultdict(list)
        for v,e in zip(nv,r):g[int(v)].append(float(e))
        res['mean_residual_by_n']={str(k):round(sum(v)/len(v),4) for k,v in sorted(g.items())}
        out[m]=res
    return out


def raw(points):
    g=defaultdict(list)
    for n,y in points:g[n].append(y)
    return {str(n):{'cases':len(v),'median':round(float(np.median(v)),6),'mean':round(float(np.mean(v)),6),'max':round(float(max(v)),6)} for n,v in sorted(g.items())}


def gr2_006(path):
    d=json.loads(Path(path).read_text());E=[];Ec=defaultdict(int);T=[];C=[];S=[]
    for c in d['per_case']:
        for n,e in c['enum'].items():
            n=int(n)
            if e['final_status']=='budget_exhausted':Ec[n]+=1;continue
            E.append((n,e['peak_rows']));T.append((n,e['time_s']))
        for n,s in c['sat'].items():C.append((int(n),s['max_clauses']));S.append((int(n),s['time_s']))
    return {'source':str(path),'withdrawn_v040_loglog_slopes':d.get('loglog_slopes'),
            'enumeration_peak_rows':{'censored_cases_excluded':dict(Ec),'raw':raw(E),'fit_n2_5':fit([p for p in E if p[0]<=5]),
                                     'note':'n=6 has 10/84 censored cases (160000-row budget) and is excluded from the fit; its raw mean is a lower bound'},
            'enumeration_case_seconds_informational':{'raw':raw(T),'fit_n2_5':fit([p for p in T if p[0]<=5])},
            'sat_max_clauses':{'raw':raw(C),'fit':fit(C,('power','exponential','cubic'))},
            'sat_case_seconds_informational':{'raw':raw(S),'fit':fit(S),'note':'wall clock on a shared loaded box; non-monotone in n; fits are descriptive only'}}


def scaling_007(path):
    d=json.loads(Path(path).read_text());cases=d.get('cases') or d.get('per_case') or []
    by=defaultdict(lambda:{'rows':[],'cens':defaultdict(int),'clauses':[],'secs':[],'unknown':defaultdict(int)})
    for c in cases:
        a=by[c['alphabet']];n=c['n'];st=c['steps']
        a['clauses'].append((n,max(s['clauses'] for s in st)));a['secs'].append((n,c['case_seconds_informational']))
        a['unknown'][n]+=sum(s['unknown_answers'] for s in st)
        if c['enumeration']['run']:
            if c['enumeration']['exhausted_at_step'] is not None:a['cens'][n]+=1
            else:
                r=[s['enum_rows'] for s in st if s.get('enum_rows') is not None]
                if r:a['rows'].append((n,max(r)))
    out={'source':str(path)}
    for al,a in sorted(by.items()):
        out[al]={'sat_unknown_answers_by_n':{str(k):v for k,v in sorted(a['unknown'].items())},
                 'enumeration_peak_rows':{'censored_cases_excluded':{str(k):v for k,v in a['cens'].items()},'raw':raw(a['rows']),
                                          'fit':fit(a['rows']) if len({p[0] for p in a['rows']})>=3 else 'fewer than 3 uncensored n values; no fit'},
                 'sat_max_clauses':{'raw':raw(a['clauses']),'fit':fit(a['clauses'],('power','exponential','cubic')) if len({p[0] for p in a['clauses']})>=5 else 'fewer than 5 n values; cubic not identifiable'},
                 'sat_case_seconds_informational':{'raw':raw(a['secs'])}}
    return out


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--gr2');ap.add_argument('--scaling');ap.add_argument('--out');a=ap.parse_args()
    rep={'schema':'brute.scaling-fit.v1','label':'Inferred (models fitted post hoc to Observed per-case points; not pre-registered)'}
    if a.gr2:rep['study_006_GR2']=gr2_006(a.gr2)
    if a.scaling:rep['study_007_scaling']=scaling_007(a.scaling)
    s=json.dumps(rep,indent=1,sort_keys=True)
    if a.out:
        p=Path(a.out);assert not p.exists(),'refusing overwrite';p.write_text(s+'\n')
    print(s)
