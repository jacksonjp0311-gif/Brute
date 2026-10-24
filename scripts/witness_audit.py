"""F4 / R3 (v0.1.1): divergent-witness audit for certificates (learner_witness_audit).

For a learner about to predict `action`, search the <= margin_states hypothesis rows for a
complete deterministic Moore machine that explains every recorded observation but emits a
code different from `certificate` at the next step. Any witness is rebuilt as a full machine
and re-checked by replaying the evidence from scratch, so the result does not trust the rows.

Expected (BRUTE_PLAN_003.json R3): 0 witnesses on CERTIFIED steps (the margin support is the
certified singleton); witnesses on MARGIN_DISAGREES steps (why Brute abstained).
Report only; not a gate.
"""
from __future__ import annotations
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from bgr90.symbolic import mask_for_observation


def _lowest(mask):
    for c in range(4):
        if mask&(1<<c):return c
    raise ValueError('empty emission mask')


def _machine_from_row(row,action,code,max_states):
    """Complete machine from one hypothesis row whose next emission after `action` is `code`, or None."""
    trans=list(row.trans);masks=list(row.masks);used=row.used
    edge=row.current*2+action;dst=trans[edge]
    if dst>=0:
        if not masks[dst]&(1<<code):return None
        target=dst
    else:
        target=next((j for j in range(used) if masks[j]&(1<<code)),None)
        if target is None:
            if used>=max_states:return None
            target=used;used+=1;masks[target]=15
        trans[edge]=target
    emissions=[code if j==target else _lowest(masks[j]) for j in range(used)]
    trans=[t if 0<=t<used else 0 for t in trans[:2*used]]
    return {'states':used,'transitions':trans,'emissions':emissions,'start':0}


def replay_machine(machine,evidence):
    """Return the state after the evidence, or None if any observation is incompatible."""
    s=machine['start']
    if not mask_for_observation(evidence[0][1])&(1<<machine['emissions'][s]):return None
    for a,obs in evidence[1:]:
        s=machine['transitions'][s*2+a]
        if not mask_for_observation(obs)&(1<<machine['emissions'][s]):return None
    return s


def learner_witness_audit(learner,action,certificate):
    """Search learner.margin's rows for a verified witness that the next code differs from `certificate`."""
    margin=learner.margin
    if margin.status!='supported':return {'checked':False,'reason':'margin_'+margin.status}
    ev=margin.evidence;rows=0
    for row in sorted(margin.belief,key=lambda p:(p.used,p.trans,p.masks,p.current)):
        rows+=1
        for code in range(4):
            if code==certificate:continue
            m=_machine_from_row(row,action,code,margin.max_states)
            if m is None:continue
            end=replay_machine(m,ev)
            if end is None:continue
            nxt=m['emissions'][m['transitions'][end*2+action]]
            if nxt!=code:continue
            return {'checked':True,'witness':True,'code':code,'machine':m,'rows_scanned':rows,'verified_by_replay':True}
    return {'checked':True,'witness':False,'rows_scanned':rows}


def audit_study(plan,tau,families=None,seeds_per_family=None):
    from bgr89.worlds import world as old_world,actions
    from bgr90.worlds import world as new_world,step as new_step
    from brute.fallback import FallbackBruteLearner
    from brute.core.learner import Status,Reason
    out={}
    for fam in families or plan['in_family']+plan['out_of_family']:
        lo,hi=plan['heldout_ranges'][fam];seeds=range(lo,hi+1)
        if seeds_per_family:seeds=list(seeds)[:seeds_per_family]
        tally={'certified_steps':0,'certified_with_witness':0,'margin_disagrees_steps':0,
               'margin_disagrees_with_witness':0,'unchecked':0,'witness_examples':[]}
        for seed in seeds:
            for mask in plan['mask_rates']:
                truth=(new_world if fam in ('ood5','drift4') else old_world)(seed,fam)
                h=truth.start
                L=FallbackBruteLearner(plan['family_state_cap'],plan['margin_state_cap'],plan['row_budget_family'],
                                       plan['row_budget_margin'],plan['prediction_smoothing'],
                                       plan['open_world_reserve_epsilon'],plan['residual_surprise']['window_W'],tau)
                L.initialize(truth.observed(h,mask,-1))
                for i,a in enumerate(actions(seed,plan['actions_per_case'])):
                    f=L.predict(a)
                    kind=None
                    if f.status==Status.CERTIFIED:kind='certified';target=f.certificate
                    elif f.reason==Reason.MARGIN_DISAGREES:kind='margin_disagrees';target=f.support[0]
                    if kind:
                        r=learner_witness_audit(L,a,target)
                        tally[kind+'_steps']+=1
                        if not r['checked']:tally['unchecked']+=1
                        elif r['witness']:
                            tally[kind+'_with_witness']+=1
                            if len(tally['witness_examples'])<3:
                                tally['witness_examples'].append({'seed':seed,'mask_rate':mask,'step':i+1,'kind':kind,
                                    'certified_or_family_code':target,'witness_code':r['code'],'machine':r['machine']})
                    h=new_step(truth,h,a,i) if fam=='drift4' else truth.next(h,a)
                    L.observe(a,truth.observed(h,mask,i))
        out[fam]=tally
    return out


def main(argv=None):
    ap=argparse.ArgumentParser();ap.add_argument('--out',required=True);ap.add_argument('--seeds-per-family',type=int)
    args=ap.parse_args(argv)
    plan=json.loads((ROOT/'experiments/BRUTE_PLAN_003.json').read_text())
    tau=plan['residual_surprise']['tau']
    res={'schema':'brute.witness-audit.v1','study':plan['study'],'criterion':'R3_witness_audit_F14 (reported, not gated)',
         'method':'search <=5-state margin rows for a complete machine that explains all evidence and emits a different next code; every witness re-verified by replay from the start state',
         'seeds_per_family':args.seeds_per_family,'families':audit_study(plan,tau,seeds_per_family=args.seeds_per_family)}
    res['totals']={k:sum(v[k] for v in res['families'].values()) for k in
                   ('certified_steps','certified_with_witness','margin_disagrees_steps','margin_disagrees_with_witness','unchecked')}
    out=Path(args.out)
    if out.exists():raise SystemExit('refusing overwrite '+str(out))
    out.write_text(json.dumps(res,sort_keys=True,indent=2)+'\n')
    print(json.dumps(res['totals']))


if __name__=='__main__':main()
