"""Lag diagnostic on SEEN data for v0.9.0 (NEXT_ITERATION.md step 1). EXPLORATORY: these cases are sealed studies
008-010 that informed v0.6.0-v0.8.0; nothing here is v0.9.0 evidence. Written and run BEFORE BRUTE_PLAN_011 and before
any v0.9.0 learner code; its output fixes the J9 window constant that the plan pre-registers.

For every drift4 false certificate (taken and counterfactual action) of every certifying arm (all arms except the
A-baselines) in the listed sealed files it records:
  lag      = step - d, d = the last drift step (12, 23, 34) < step (drift-step forecasts, step in {12,23,34}, are the
             drift class and are counted separately; step <= 12 false certificates are pre-drift and listed apart);
  rule     = forecast cert_rule when the arm records one (S7/SC7/SP8/J8), else null (R6/C6);
  events   = recorded drift events u with d <= u < step (diagnostics.drift_events, when the arm records them);
  contradiction_step = diagnostics.contradiction_step (first step the no-jump family region was contradicted;
             a PROXY for "the true machine left the region": the drifted world is not a fixed Moore machine);
  obs_after_jump = lag - 1 = observations after the jumped observation d before the forecast was issued.
Usage: PYTHONPATH=. python scripts/diag_lag_011.py --output results/diag-011/LAG_DIAG_SEEN.json
"""
import argparse,json,sys
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.diag_stale_010 import iter_cases
DRIFT=(12,23,34)
INPUTS=(('study-008','results/study-008/RESULTS.json'),('study-009','results/study-009/2x2/SCIENTIFIC.json'),
        ('study-010','results/study-010/2x2/SCIENTIFIC.json'))
BASELINES=('A2','A4','A5')


def classify(s):
    """(class, d, lag) of a forecast for step s."""
    d=max([x for x in DRIFT if x<s],default=None)
    cls='drift_step' if s in DRIFT else ('pre_drift' if d is None else 'non_drift')
    return cls,d,None if d is None else s-d


def records(study,path):
    out=[];cases=0;per_arm=Counter()
    for c in iter_cases(ROOT/path):
        if c['family']!='drift4':continue
        cases+=1
        for arm,A in c['arms'].items():
            if arm in BASELINES:continue
            per_arm[arm]+=1;dg=A.get('diagnostics',{});ev=dg.get('drift_events')
            for r in A['trace']:
                for side,q in (('taken',r),('counterfactual',r.get('counterfactual') or {})):
                    if not q.get('wrong'):continue
                    s=r['step'];cls,d,_=classify(s)
                    out.append({'study':study,'arm':arm,'seed':c['seed'],'mask':c['mask_rate'],'step':s,'side':side,'class':cls,
                                'd':d,'lag':None if d is None else s-d,'rule':q.get('cert_rule'),'public':bool(q.get('public_wrong')),
                                'events_between':None if ev is None or d is None else [u for u in ev if d<=u<s],
                                'contradiction_step':dg.get('contradiction_step'),'reason':q.get('reason')})
    return out,cases,dict(per_arm)


def summarise(R):
    nd=[x for x in R if x['class']=='non_drift']
    def hist(xs,k):return dict(sorted(Counter(str(x[k]) for x in xs).items()))
    by_arm={}
    for x in nd:
        a=by_arm.setdefault(f"{x['study']}/{x['arm']}",{'n':0,'taken':0,'lags':Counter()});a['n']+=1;a['taken']+=x['side']=='taken';a['lags'][x['lag']]+=1
    for a in by_arm.values():a['lags']=dict(sorted(a['lags'].items()))
    lags=sorted(x['lag'] for x in nd);n=len(lags)
    cum={L:round(sum(l<=L for l in lags)/n,4) for L in range(1,12)} if n else {}
    ev=[x for x in nd if x['events_between'] is not None]
    return {'non_drift_total':n,'non_drift_taken':sum(x['side']=='taken' for x in nd),'lag_histogram':hist(nd,'lag'),
            'lag_cumulative_fraction':cum,'rule_histogram':hist(nd,'rule'),'by_study_arm':by_arm,
            'distinct_events':len({(x['study'],x['seed'],x['mask'],x['step'],x['side']) for x in nd}),
            'with_event_between_d_and_step':sum(bool(x['events_between']) for x in ev),'with_event_info':len(ev),
            'contradicted_before_step':sum(1 for x in nd if x['contradiction_step'] is not None and x['contradiction_step']<x['step']),
            'contradicted_after_step':sum(1 for x in nd if x['contradiction_step'] is not None and x['contradiction_step']>=x['step']),
            'never_contradicted':sum(1 for x in nd if x['contradiction_step'] is None),
            'drift_step_total':sum(x['class']=='drift_step' for x in R),'pre_drift_total':sum(x['class']=='pre_drift' for x in R)}


def main(argv=None):
    ap=argparse.ArgumentParser();ap.add_argument('--output',required=True);a=ap.parse_args(argv)
    R=[];meta={}
    for study,path in INPUTS:
        r,n,pa=records(study,path);R+=r;meta[study]={'file':path,'drift4_cases':n,'arms_cases':pa}
    rep={'label':'EXPLORATORY, SEEN DATA (sealed studies 008-010); not v0.9.0 evidence','inputs':meta,'summary':summarise(R),
         'summary_taken_only':summarise([x for x in R if x['side']=='taken']),'false_certificates':R}
    Path(a.output).write_text(json.dumps(rep,indent=1,sort_keys=True)+'\n')
    print(json.dumps({'inputs':meta,'summary':rep['summary']},indent=1,sort_keys=True));return 0


if __name__=='__main__':sys.exit(main())
