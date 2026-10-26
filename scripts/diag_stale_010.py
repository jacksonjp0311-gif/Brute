"""GD classifier for study-010 (BRUTE_PLAN_010 diagnostic_GD, criteria GD_stale_cause_diagnostic).

(i) every NON-DRIFT false certificate (taken action `wrong`, counterfactual action `counterfactual.wrong`; drift4,
    step > 12 and step not in {12, 23, 34}) of the listed arms is classified: d = the last drift step < step;
    `at_d_plus_1` = (step == d + 1); `event_at_d` = d in diagnostics.drift_events (the event list of the frozen
    SyncEventLearner: an event "at u" fired after observing step u, i.e. before the forecast for u + 1 was issued).
    The stale class is at_d_plus_1 and not event_at_d.
(ii) J8 hull containment: in every drift4 case where the J8 family status after observation 12 is 'supported'
    (trace[11].family_status_after), the step-13 record's hull_union[str(a)] must contain the realised code of
    action a for both actions (taken: actual_emission_EVALUATOR_ONLY, other: counterfactual_actual_EVALUATOR_ONLY).
    hull_union is the union recorded at forecast time (after observation 12). Non-vacuity = steps where some
    hull_union is not all codes.

Input: one or more RESULTS.json / SCIENTIFIC.json (streamed) or CHECKPOINT.jsonl files.
  PYTHONPATH=. python scripts/diag_stale_010.py --arms SC7 SP8 --hull-arm J8 --output OUT.json FILE [FILE ...]
"""
import argparse,json,sys
from pathlib import Path
DRIFT=(12,23,34)
MIN_EVENTS=3
THRESHOLD=0.8


def iter_cases(path):
    path=Path(path)
    if path.suffix=='.jsonl':
        with open(path) as f:
            for line in f:
                line=line.strip()
                if line:
                    o=json.loads(line);yield o.get('case',o)
        return
    s=path.read_text();i=s.index('"cases":');i=s.index('[',i)+1;dec=json.JSONDecoder()
    while True:
        while s[i] in ' \n\r\t,':i+=1
        if s[i]==']':return
        o,i=dec.raw_decode(s,i);yield o


def non_drift(step):return step>12 and step not in DRIFT


def classify_arm(case,arm):
    A=case['arms'][arm];ev=set(A['diagnostics'].get('drift_events') or []);out=[]
    for r in A['trace']:
        for kind,rec in (('taken',r),('counterfactual',r.get('counterfactual') or {})):
            if not rec.get('wrong') or not non_drift(r['step']):continue
            d=max(x for x in DRIFT if x<r['step'])
            out.append({'arm':arm,'seed':case['seed'],'mask':case['mask_rate'],'step':r['step'],'action_kind':kind,'d':d,
                        'at_d_plus_1':r['step']==d+1,'event_at_d':d in ev,'cert_rule':rec.get('cert_rule'),
                        'stale_class':r['step']==d+1 and d not in ev})
    return out


def hull_check(case,arm,m=4):
    A=case['arms'][arm];tr=A['trace']
    if len(tr)<13 or tr[11].get('family_status_after')!='supported':return None
    r=tr[12];assert r['step']==13;H=r.get('hull_union')
    if H is None:return {'seed':case['seed'],'mask':case['mask_rate'],'missing':True,'contained':False,'nonvacuous':False}
    a=r['action'];codes={a:r['actual_emission_EVALUATOR_ONLY'],1-a:r['counterfactual_actual_EVALUATOR_ONLY']}
    cont=all(codes[b] in H[str(b)] for b in (0,1));nonvac=any(len(H[str(b)])<m for b in (0,1))
    return {'seed':case['seed'],'mask':case['mask_rate'],'missing':False,'contained':cont,'nonvacuous':nonvac,
            'hull_union':H,'realised':{str(b):codes[b] for b in (0,1)}}


def run(files,arms,hull_arm=None):
    F=[];H=[];n=0
    for p in files:
        for c in iter_cases(p):
            if c['family']!='drift4':continue
            n+=1
            for a in arms:
                if a in c['arms']:F+=classify_arm(c,a)
            if hull_arm and hull_arm in c['arms']:
                h=hull_check(c,hull_arm)
                if h is not None:H.append(h)
    k=sum(x['stale_class'] for x in F);N=len(F)
    by={a:{'nd_false':sum(1 for x in F if x['arm']==a),'stale_class':sum(1 for x in F if x['arm']==a and x['stale_class'])} for a in arms}
    i_eval=N>=MIN_EVENTS;i_pass=i_eval and k/N>=THRESHOLD
    rep={'drift4_cases':n,'arms':arms,'nd_false_total':N,'stale_class':k,'fraction':(k/N if N else None),'by_arm':by,
         'clause_i':{'evaluable':i_eval,'pass':i_pass,'reason':None if i_eval else 'INSUFFICIENT_EVENTS','min_events':MIN_EVENTS,'threshold':THRESHOLD},
         'false_certificates':F}
    if hull_arm:
        exc=[h for h in H if not h['contained']]
        rep['clause_ii']={'arm':hull_arm,'supported_cases':len(H),'exceptions':len(exc),'missing':sum(h['missing'] for h in H),
                          'nonvacuous_cases':sum(h['nonvacuous'] for h in H),'pass':not exc,'exception_detail':exc[:20]}
        rep['GD_pass']=i_pass and not exc
    return rep


def main(argv=None):
    ap=argparse.ArgumentParser();ap.add_argument('files',nargs='+');ap.add_argument('--arms',nargs='+',default=['SC7','SP8'])
    ap.add_argument('--hull-arm',default=None);ap.add_argument('--output',required=True);a=ap.parse_args(argv)
    rep=run(a.files,a.arms,a.hull_arm);rep['inputs']=a.files
    Path(a.output).write_text(json.dumps(rep,indent=1,sort_keys=True)+'\n')
    print(json.dumps({k:v for k,v in rep.items() if k!='false_certificates'},indent=1,sort_keys=True));return 0


if __name__=='__main__':sys.exit(main())
