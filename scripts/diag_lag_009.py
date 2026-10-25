"""Diagnostic a0 (BRUTE_PLAN_009 diagnostic_a0): event lag on the SEALED study-008 drift4 traces. Non-gated,
Observed on ALREADY-SEEN data; cannot pass or fail any v0.7.0 gate and cannot change any v0.7.0 rule (S7/SC7 are
fixed in BRUTE_PLAN_009 before this runs). No learner is rerun.

E1 on the recorded trace: residual_after > tau6 x 0.5, or a window-tier event. For R6/C6 the recorded
diagnostics.drift_events list (the frozen _note_event output) is used directly and cross-checked against the
residual rule; for A5/A4 the window-tier event is approximated by the first family contradiction step plus
residual_after > tau6/2 (window restarts are not in the slim per-step record; disclosed in the output).
E2: the taken-action certificate at step u is incompatible with the observation at u (bit c not in the mask).
E3: surprise at u > tau6 (recorded surprise, 12 d.p.).
A2 records only step/action/certificate/wrong/drift_step (slim trace): surprise-based quantities are reported as
unavailable for A2; false certificates are still listed.

  PYTHONPATH=. python scripts/diag_lag_009.py   # writes results/study-009/DIAG_LAG_009.json (refuses overwrite)
"""
import json,sys
from pathlib import Path
from bgr90.symbolic import mask_for_observation
from experiments.brute_common import check,load,sha,write_new
ROOT=Path(__file__).resolve().parents[1]
S8=ROOT/'results/study-008';OUT=ROOT/'results/study-009/DIAG_LAG_009.json'
DRIFT=(12,23,34);STEPS=44;W=8
ARMS=('R6','C6','A5','A4','A2')


def _incompatible(cert,obs):return cert is not None and not (mask_for_observation(tuple(obs))>>cert)&1


def _e1_steps(arm,a,tau):
    tr=a['trace']
    if arm in ('R6','C6'):return set(a['diagnostics']['drift_events'])
    ev={r['step'] for r in tr if r['residual_after'] is not None and r['residual_after']>tau*0.5}
    c=a['diagnostics'].get('contradiction_step')
    if c is not None:ev.add(c)
    return ev


def _lag(steps,d,nxt):
    hit=[u for u in sorted(steps) if d<=u<nxt]
    return (hit[0]-d,False) if hit else (nxt-d,True)


def analyse(case,arm,tau):
    a=case['arms'][arm];tr=a['trace'];full='surprise' in tr[0];by={r['step']:r for r in tr};out={'seed':case['seed'],'mask_rate':case['mask_rate']}
    falses=[r['step'] for r in tr if r['wrong']]
    out['false_steps']=falses;out['nondrift_false_steps']=[u for u in falses if not by[u]['drift_step']]
    if not full:
        out['full_trace']=False;return out
    e1=_e1_steps(arm,a,tau)
    e2={r['step'] for r in tr if _incompatible(r['certificate'],r['observed'])}
    e3={r['step'] for r in tr if r['surprise'] is not None and r['surprise']>tau}
    if arm in ('R6','C6'):
        res={r['step'] for r in tr if r['residual_after'] is not None and r['residual_after']>tau*0.5}
        out['e1_residual_subset_of_recorded']=res<=e1
    per=[]
    for i,d in enumerate(DRIFT):
        nxt=DRIFT[i+1] if i+1<len(DRIFT) else STEPS+1;r=by[d]
        win=[by[u]['surprise'] for u in range(max(1,d-W+1),d) if u in by]
        fal=[u for u in sorted(e2) if u>=d];wr=[u for u in falses if u>=d]
        per.append({'d':d,'s_d':r['surprise'],'residual_after_d':r['residual_after'],'E1_at_d':d in e1,'E2_at_d':d in e2,
                    'E3_at_d':d in e3,'lag_E1':_lag(e1,d,nxt),'lag_E2':_lag(e2,d,nxt),'lag_E3':_lag(e3,d,nxt),
                    'lag_E2E3':_lag(e2|e3,d,nxt),'first_falsified_cert_ge_d':fal[0] if fal else None,
                    'first_wrong_cert_ge_d':wr[0] if wr else None,'other7_window_sum':round(sum(win),12),
                    'window_sum_needed':round(W*tau*0.5,12)})
    out['drift']=per
    cls=[]
    for u in out['nondrift_false_steps']:
        d=u-1
        if d not in DRIFT:cls.append({'step':u,'class':'not at d+1'});continue
        c='i' if d in e2 else ('ii' if d in e3 else 'iii')
        cls.append({'step':u,'d':d,'class':c,'s_d':by[d]['surprise'],'cert_d':by[d]['certificate'],'observed_d':by[d]['observed']})
    out['nondrift_classes']=cls;out['full_trace']=True;return out


def main():
    seal=load(S8/'SEAL.json');check(sha(S8/'RESULTS.json')==seal['results_sha256'],'study-008 RESULTS.json does not match SEAL')
    R=load(S8/'RESULTS.json');cases=[c for c in R['cases'] if c.get('block')=='2x2' and c['family']=='drift4']
    check(len(cases)==144,f'expected 144 drift4 cases, got {len(cases)}')
    tau=cases[0]['tau6'];arms={}
    for arm in ARMS:
        rows=[analyse(c,arm,tau) for c in cases];s={'cases':len(rows),'false_total':sum(len(r['false_steps']) for r in rows),
            'nondrift_false':[[r['seed'],r['mask_rate'],u] for r in rows for u in r['nondrift_false_steps']]}
        if rows[0]['full_trace']:
            D=[x for r in rows for x in r['drift']]
            for k in ('E1','E2','E3','E2E3'):
                det=[x['lag_'+k][0] for x in D if not x['lag_'+k][1]]
                s['lag_'+k]={'drift_steps':len(D),'detected':len(det),'censored':len(D)-len(det),
                             'lag0':sum(v==0 for v in det),'lag_ge1':sum(v>=1 for v in det),
                             'hist':{str(v):det.count(v) for v in sorted(set(det))}}
            s['at_d']={k:sum(x[k+'_at_d'] for x in D) for k in ('E1','E2','E3')}
            s['E3_without_E1_at_d']=sum(x['E3_at_d'] and not x['E1_at_d'] for x in D)
            s['max_s_d']=max(x['s_d'] for x in D);s['max_other7_window_sum']=max(x['other7_window_sum'] for x in D)
            s['nondrift_classes']=[dict(c,seed=r['seed'],mask_rate=r['mask_rate']) for r in rows for c in r['nondrift_classes']]
            s['class_counts']={k:sum(c['class']==k for c in s['nondrift_classes']) for k in ('i','ii','iii','not at d+1')}
            if arm in ('R6','C6'):s['e1_residual_subset_of_recorded_all']=all(r['e1_residual_subset_of_recorded'] for r in rows)
        else:s['note']='slim trace (no observed/surprise fields): lag and class quantities unavailable'
        arms[arm]={'summary':s,'cases':rows}
    out={'schema':'brute.diag-lag.v1','study':'BRUTE-070-SYNCPLAN-009','label':load(ROOT/'experiments/BRUTE_PLAN_009.json')['diagnostic_a0']['label'],
         'source':'results/study-008/RESULTS.json','source_sha256':seal['results_sha256'],'tau6':tau,'W':W,'drift_steps':list(DRIFT),
         'window_arithmetic':{'max_single_surprise_2x2':5.298317366548,'window_sum_needed_2x2':round(W*tau*0.5,12),
                              'max_single_surprise_8codes':5.991464547108,'window_sum_needed_breadth':round(W*2.07944154168*0.5,12)},
         'E1_approximation_A5_A4':'residual_after > tau6/2 or first family contradiction step (window restarts not recorded per step)',
         'arms':arms}
    write_new(OUT,out)
    print(json.dumps({a:{k:v for k,v in arms[a]['summary'].items() if k!='nondrift_classes'} for a in ARMS},indent=1))
    for a in ARMS:print(a,arms[a]['summary'].get('nondrift_classes'))
    return 0


if __name__=='__main__':sys.exit(main())
