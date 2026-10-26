"""EXPLORATORY diagnostic on SEEN study-011 data (not a gated result; written and run BEFORE BRUTE_PLAN_012).

Question (NEXT_ITERATION.md v0.9.0 -> v0.10.0): what mechanism makes the J9 jump-window hull downgrade SP8's TRUE
certificates, and is there an observable gate (e.g. surprise in the window) that separates SP8's 18 non-drift false
certificates from the true certificates J9 downgrades?

Part A (recorded traces, results/study-011/2x2/SCIENTIFIC.json): every SP8 certificate (taken and counterfactual
action) is paired with J9 at the same case/step/action (the action sequences are asserted identical: LU-C is
unchanged in J9). Recorded per certificate: SP8 truth, J9 kept/downgraded, the J9 hull for that action, window
surprise (observations T-K+1..T, K=4), family status before the decision, event triggers in the window.
Part B (re-run of J9 on the same seen seeds, instrumented, J9 decisions unchanged): at every SP8-kept certificate,
(i) which single window position t widens the hull (JumpWindowRegionK with the selector j_t forced),
Part B counts one decision per (case, step, action): the last _rule_decide call (predict is called more than
once per step; the last call is the published one).
(ii) the exact jump-window SUPPORT projection supW_K(action) (RegionK.support on JumpWindowRegionK) for K=4,6,8 and the
hull Y1kW_K for K=6,8, so candidate J10 keep-rules can be scored post hoc on the same certificates.
The instrumentation substitutes a subclass for WindowSyncLearner in the study-011 harness module namespace inside
this process only; no learner or frozen file is edited. Seen data: every number here is Observed on seen seeds and
can only inform the design of plan 012, never a gate.
"""
from __future__ import annotations
import argparse,json,os,sys,collections,time
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from scripts.diag_stale_010 import iter_cases

DRIFT=(12,23,34);K=4
OUT=Path('results/diag-012/DOWNGRADE_DIAG_SEEN.json')


def part_a(path):
    rows=[]
    for c in iter_cases(path):
        Ja=c['arms']['J9'];J=Ja['trace'];S=c['arms']['SP8']['trace']
        if [r['action'] for r in J]!=[r['action'] for r in S]:raise AssertionError(('actions differ',c['seed']))
        ev={s for s,_ in Ja['diagnostics']['event_triggers']}
        sur={r['step']:r['surprise'] for r in J};fs={r['step']:r['family_status_after'] for r in J}
        for j,s in zip(J,S):
            st=j['step'];T=st-1
            for side in ('taken','cf'):
                jq=j if side=='taken' else j['counterfactual'];sq=s if side=='taken' else s['counterfactual']
                if sq['certificate'] is None:continue
                a=j['action'] if side=='taken' else 1-j['action'];hu=j.get('hull_union')
                win=[sur[t] for t in range(max(1,T-K+1),T+1) if t in sur]
                rows.append({'family':c['family'],'seed':c['seed'],'mask_rate':c['mask_rate'],'step':st,'action':a,
                    'side':side,'sp8_wrong':bool(sq['wrong']),'sp8_rule':sq['cert_rule'],
                    'nondrift':c['family']=='drift4' and st>12 and st not in DRIFT,
                    'drift_step':c['family']=='drift4' and st in DRIFT,
                    'j9_keep':jq['certificate'] is not None,'hull':None if hu is None else hu[str(a)],
                    'win_surprise_max':max(win) if win else None,
                    'family_supported_before':(fs.get(T,'supported')=='supported') if T>=1 else True,
                    'event_in_window':any(t in ev for t in range(max(1,T-K+1),T+1))})
    return rows


def summarise_a(rows):
    D=[r for r in rows if not r['j9_keep']];Tr=[r for r in D if not r['sp8_wrong']]
    W=[r for r in rows if r['sp8_wrong'] and r['nondrift']]
    stat=lambda R,f:dict(sorted(collections.Counter(str(f(r)) for r in R).items()))
    out={'sp8_certificates':len(rows),'j9_downgraded':len(D),'j9_downgraded_sp8_true':len(Tr),
         'j9_downgraded_sp8_wrong':len(D)-len(Tr),'sp8_nondrift_false':len(W),
         'sp8_nondrift_false_kept_by_j9':sum(r['j9_keep'] for r in W),
         'downgraded_true_by_family':stat(Tr,lambda r:r['family']),
         'downgraded_true_by_hull_size':stat(Tr,lambda r:len(r['hull']) if r['hull'] else None),
         'nondrift_false_by_hull_size':stat(W,lambda r:len(r['hull']) if r['hull'] else None),
         'downgraded_true_by_sp8_rule':stat(Tr,lambda r:r['sp8_rule']),'nondrift_false_by_sp8_rule':stat(W,lambda r:r['sp8_rule']),
         'family_supported_before':{'downgraded_true':stat(Tr,lambda r:r['family_supported_before']),
                                    'nondrift_false':stat(W,lambda r:r['family_supported_before'])},
         'event_in_window':{'downgraded_true':stat(Tr,lambda r:r['event_in_window']),'nondrift_false':stat(W,lambda r:r['event_in_window'])}}
    gates={}
    for th in (0.02,0.03,0.05,0.08,0.1,0.2,0.5,0.82):
        # surprise gate: apply the hull only if some window surprise > th, else keep SP8's certificate
        gates[str(th)]={'nondrift_false_kept':sum(1 for r in W if (r['win_surprise_max'] or 0)<=th),
                        'downgraded_true_recovered':sum(1 for r in Tr if (r['win_surprise_max'] or 0)<=th)}
    out['surprise_gate_scan']=gates
    out['nondrift_false_cases']=[{k:r[k] for k in ('seed','mask_rate','step','side','sp8_rule','hull','win_surprise_max',
                                                     'family_supported_before','event_in_window')} for r in W]
    return out


# ---------------------------------------------------------------- part B
def _job(args):
    seed,family,rate=args
    import experiments.brute_study_011 as S
    from brute.jumpwindow import WindowSyncLearner,JumpWindowRegionK
    log=[]
    class Instr(WindowSyncLearner):
        def _rule_decide(self,action,mask,cert):
            keep0,path0=super(WindowSyncLearner,self)._rule_decide(action,mask,cert)
            keep,path=super()._rule_decide(action,mask,cert)
            if not keep0:return keep,path
            sp=self.support;rec={'step':len(sp.evidence),'action':action,'cert':cert,'j9_keep':keep}
            def mk(Kk):return JumpWindowRegionK(sp.max_states,sp.k,sp.m,sp.masks,sp.acts,sp.conf_budget,sp.region.solver,sp.region.symmetry,K=Kk)
            for Kk in (4,6,8):
                R=mk(Kk)
                try:
                    if R._sat is not True:rec[f'supW{Kk}']=None;rec[f'y1kW{Kk}']=None;continue
                    rec[f'supW{Kk}']=list(R.support(action)[0])
                    if Kk!=4:rec[f'y1kW{Kk}']=list(R.y1k(action,mask)[0])
                finally:R.close()
            if not keep:
                wid=[]
                for t in __import__('brute.jumpwindow',fromlist=['x']).window_positions(len(sp.acts),4):
                    R=mk(4)
                    try:
                        R.s.add_clause([R.j[t]]);R._sat=R._solve([])
                        h=R.y1k(action,mask)[0] if R._sat else None
                    finally:R.close()
                    wid.append({'t':t,'lag_from_T':len(sp.acts)-t,'hull':None if h is None else list(h)})
                rec['per_position']=wid
            log.append(rec);return keep,path
    S.WindowSyncLearner=Instr
    from experiments.brute_common_011 import PLAN,load,plan_view,plan006_keys
    from brute.core.learner import ScopeAttestation
    plan=load(PLAN);v=plan_view(plan);p6=plan006_keys(v);attest=family in plan['in_family_2x2']
    def att():return ScopeAttestation(p6['declared_family'],'evaluator','synthetic world built inside the family') if attest else None
    truth,initial,out=S.trajectory_2x2('J9',seed,family,rate,v,p6,plan['tau6']['value'],att)
    tr=out['trace']
    for r in log:
        t=tr[r['step']-1];r['truth']=t['actual_emission_EVALUATOR_ONLY'] if r['action']==t['action'] else t['counterfactual_actual_EVALUATOR_ONLY']
    return {'seed':seed,'family':family,'mask_rate':rate,'certs':log}


def part_b(workers,limit=None):
    plan=json.load(open('experiments/BRUTE_PLAN_011.json'))
    jobs=[(s,f,r) for f,(lo,hi) in plan['heldout_ranges_2x2'].items() for s in range(lo,hi+1) for r in plan['mask_rates']]
    if limit:jobs=jobs[::max(1,len(jobs)//limit)]
    with ProcessPoolExecutor(workers) as ex:return list(ex.map(_job,jobs,chunksize=2))


def summarise_b(cases):
    rules={'J9_y1kW4':lambda r:r['j9_keep'],'SP8':lambda r:True}
    for Kk in (4,6,8):rules[f'supW{Kk}']=(lambda Kk:lambda r:r[f'supW{Kk}']==[r['cert']])(Kk)
    for Kk in (6,8):rules[f'y1kW{Kk}']=(lambda Kk:lambda r:r[f'y1kW{Kk}']==[r['cert']])(Kk)
    rules['J9_or_supW4']=lambda r:r['j9_keep'] or r['supW4']==[r['cert']]
    agg={k:collections.Counter() for k in rules};pos=collections.Counter();lagw=collections.Counter()
    for c in cases:
        last={}
        for r in c['certs']:last[(r['step'],r['action'])]=r     # one decision per (step, action): the last call
        for r in last.values():
            wrong=r['cert']!=r['truth'];st=r['step']
            nd=c['family']=='drift4' and st>12 and st not in DRIFT;ds=c['family']=='drift4' and st in DRIFT
            infam=c['family'] in ('cycle3','switch3','unstructured3','unaliased2','ood4','perm4')
            for k,f in rules.items():
                if f(r):
                    agg[k]['kept']+=1;agg[k]['kept_true']+=not wrong;agg[k]['false_nondrift']+=wrong and nd
                    agg[k]['false_drift_step']+=wrong and ds;agg[k]['false_in_family']+=wrong and infam
                    agg[k]['false_total']+=wrong
            for w in r.get('per_position',[]):
                pos[(w['lag_from_T'],'widens' if w['hull'] is not None and w['hull']!=[r['cert']] else 'singleton_or_infeasible')]+=1
            if 'per_position' in r:
                lagw[tuple(w['lag_from_T'] for w in r['per_position'] if w['hull'] is not None and w['hull']!=[r['cert']])]+=1
    return {'rules':{k:dict(v) for k,v in agg.items()},
            'per_position_widening':{f'lag{a}:{b}':n for (a,b),n in sorted(pos.items())},
            'downgrades_by_widening_lag_set':{str(list(k)):n for k,n in lagw.most_common()}}


def main(argv=None):
    ap=argparse.ArgumentParser();ap.add_argument('--workers',type=int,default=6);ap.add_argument('--limit',type=int)
    ap.add_argument('--out',default=str(OUT));a=ap.parse_args(argv)
    t0=time.time();A=part_a('results/study-011/2x2/SCIENTIFIC.json');sa=summarise_a(A);t1=time.time()
    B=part_b(a.workers,a.limit);sb=summarise_b(B);t2=time.time()
    out={'schema':'brute.diag.downgrade.v012','label':'EXPLORATORY on SEEN study-011 seeds; not a gate; informs plan 012 design',
         'source':'results/study-011/2x2/SCIENTIFIC.json + instrumented J9 re-run on the same seeds','window_K':K,
         'part_a':sa,'part_b':sb,'part_b_cases':len(B),'elapsed_informational_s':{'part_a':round(t1-t0,1),'part_b':round(t2-t1,1)}}
    p=Path(a.out);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(out,indent=1,sort_keys=True)+'\n')
    print(json.dumps({'part_a':{k:sa[k] for k in ('sp8_certificates','j9_downgraded','j9_downgraded_sp8_true','sp8_nondrift_false','sp8_nondrift_false_kept_by_j9')},'part_b':sb},indent=1))


if __name__=='__main__':main()
