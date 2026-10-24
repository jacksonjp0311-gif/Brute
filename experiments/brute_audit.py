"""Independent audit of study-002. Imports NO brute module for decisions.

The <=4 and <=5 supports are rebuilt by experiments/v90_independent_reference.py
(a separate non-vectorized solver). Truth, masks, gate order, saturation,
surprise, residual window, alarm and public-certificate rules are recomputed
here from the plan text. Uses explicit raises (survives python -O).
"""
from __future__ import annotations
import argparse,json
from math import log
from pathlib import Path
from experiments.brute_common import PLAN,FREEZE,STUDY_DIR,load,sha,check,check_freeze,VerificationError
from experiments.v90_independent_reference import ref_initial,ref_support,ref_observe,bit_compatible
from bgr89.worlds import world as old_world,actions
from bgr90.worlds import world as new_world,step as new_step


def expected_decision(fam_status,alarm,support,margin_status,margin_support,saturated):
    if fam_status=='grammar_contradicted':return 'OUT_OF_FAMILY','FAMILY_CONTRADICTED',None
    if alarm:return 'OUT_OF_FAMILY','RESIDUAL_SURPRISE',None
    if fam_status=='budget_exhausted':return 'ABSTAIN','BUDGET_EXHAUSTED',None
    if len(support)!=1:return 'POSSIBLE_SET',None,None
    if margin_status=='budget_exhausted':return 'ABSTAIN','BUDGET_EXHAUSTED',None
    if margin_support!=support:return 'ABSTAIN','MARGIN_DISAGREES',None
    if saturated:return 'ABSTAIN','BOUND_SATURATED',None
    return 'CERTIFIED',None,support[0]


def audit_case(c,plan,tau):
    fam=c['family'];seed=c['seed'];rate=c['mask_rate'];k4=plan['family_state_cap'];k5=plan['margin_state_cap']
    W=plan['residual_surprise']['window_W'];eps=plan['open_world_reserve_epsilon']
    truth=(new_world if fam in ('ood5','drift4') else old_world)(seed,fam)
    hidden=truth.start;initial=truth.observed(hidden,rate,-1)
    check(list(initial)==c['initial_visible'],'initial mismatch')
    attested=fam in plan['in_family'];check(c['attested']==attested,'attestation flag mismatch')
    r4=ref_initial(initial);s4='supported';r5=ref_initial(initial);s5='supported'
    surprises=[];alarm=False;tally={'steps':0,'certs':0,'wrong':0,'public':0,'public_wrong':0,'v090_wrong':0}
    for i,(a,rec) in enumerate(zip(actions(seed,plan['actions_per_case']),c['trace'])):
        check(rec['step']==i+1 and rec['action']==a,'action mismatch')
        sup=ref_support(r4,a,k4) if s4=='supported' else None
        msup=ref_support(r5,a,k5) if s5=='supported' else None
        sat=all(len(m.outputs)==k4 for m in r4) if s4=='supported' else None
        check((list(sup) if sup is not None else None)==rec['support'],f'support mismatch {fam} {seed} {rate} {i}')
        check((list(msup) if msup is not None else None)==rec['margin_support'],f'margin mismatch {fam} {seed} {rate} {i}')
        check(sat==rec['saturated'],'saturation mismatch')
        st,rs,cert=expected_decision(s4,alarm,sup,s5,msup,sat)
        check((st,rs,cert)==(rec['status'],rec['reason'],rec['certificate']),f'decision mismatch {fam} {seed} {rate} {i}')
        pub=cert if (cert is not None and attested) else None
        check(pub==rec['public_certificate'],'public certificate mismatch')
        probs=rec['probabilities']
        check(abs(sum(probs)-1)<1e-9,'probabilities do not sum to 1')
        check(min(probs)>=eps/4-1e-12,'open-world reserve violated')
        hidden=new_step(truth,hidden,a,i) if fam=='drift4' else truth.next(hidden,a)
        actual=truth.emission(hidden);obs=truth.observed(hidden,rate,i)
        check(rec['actual_emission_EVALUATOR_ONLY']==actual and rec['observed']==list(obs),'truth replay mismatch')
        s=-log(sum(p for code,p in enumerate(probs) if bit_compatible(code,obs)))
        check(abs(s-rec['surprise'])<1e-8,'surprise mismatch');surprises.append(rec['surprise'])
        if len(surprises)>=W:
            R=sum(surprises[-W:])/W;check(abs(R-rec['residual_after'])<1e-8,'residual mismatch')
            if tau is not None and rec['residual_after']>tau:alarm=True
        else:check(rec['residual_after'] is None,'residual defined too early')
        check(rec['alarm_after']==alarm,'alarm mismatch')
        v090=sup[0] if sup is not None and len(sup)==1 else None
        check(rec['v090_certificate']==v090,'v0.90 control mismatch')
        check(rec['brute_wrong']==(cert is not None and cert!=actual),'wrong flag mismatch')
        check(rec['v090_wrong']==(v090 is not None and v090!=actual),'v090 wrong flag mismatch')
        check(rec['public_wrong']==(pub is not None and pub!=actual),'public wrong flag mismatch')
        if s4=='supported':
            r4,s4=ref_observe(r4,a,obs,k4,plan['row_budget_family']);r4=r4 or frozenset()
        if s5=='supported':
            r5,s5=ref_observe(r5,a,obs,k5,plan['row_budget_margin']);r5=r5 or frozenset()
        check(rec['family_status_after']==s4 and rec['margin_status_after']==s5,'status mismatch')
        check(rec['family_rows_after']==len(r4) and rec['margin_rows_after']==len(r5),'row count mismatch')
        tally['steps']+=1;tally['certs']+=cert is not None;tally['wrong']+=cert is not None and cert!=actual
        tally['public']+=pub is not None;tally['public_wrong']+=pub is not None and pub!=actual
        tally['v090_wrong']+=v090 is not None and v090!=actual
    return tally


def audit(directory=STUDY_DIR):
    directory=Path(directory);res=load(directory/'RESULTS.json');seal=load(directory/'SEAL.json')
    check(sha(directory/'RESULTS.json')==seal['results_sha256'],'RESULTS hash')
    check(sha(directory/'SCIENTIFIC.json')==seal['scientific_sha256'],'SCIENTIFIC hash')
    check(sha(PLAN)==seal['plan_sha256'] and res['plan']==load(PLAN),'plan mismatch')
    check(sha(FREEZE)==seal['freeze_sha256'],'freeze mismatch');check_freeze()
    cal=load(directory/'CALIBRATION.json');check(sha(directory/'CALIBRATION.json')==seal['calibration_sha256'] and cal==res['calibration'],'calibration mismatch')
    plan=res['plan'];tau=cal['tau'];seen=set();fams={}
    for c in res['cases']:
        lo,hi=plan['heldout_ranges'][c['family']];check(lo<=c['seed']<=hi and c['mask_rate'] in plan['mask_rates'],'case outside plan')
        key=(c['family'],c['seed'],c['mask_rate']);check(key not in seen,'duplicate case');seen.add(key)
        t=audit_case(c,plan,tau);f=fams.setdefault(c['family'],{k:0 for k in t})
        for k,v in t.items():f[k]+=v
    expected=sum((hi-lo+1)*len(plan['mask_rates']) for lo,hi in plan['heldout_ranges'].values())
    check(len(seen)==expected==seal['case_count'],'case count')
    for fam,t in fams.items():
        s=res['summary'][fam]
        check(s['brute_certs_all']==t['certs'] and s['brute_false_certs_all']==t['wrong'],'summary certs '+fam)
        check(s['public_certs_all']==t['public'] and s['public_false_certs_all']==t['public_wrong'],'summary public '+fam)
        check(s['v090_false_certs_all']==t['v090_wrong'],'summary v090 '+fam)
    return {'schema':'brute.independent-audit.v1','status':'passed','study':plan['study'],
            'source_results_sha256':seal['results_sha256'],'cases':len(seen),
            'steps_replayed':sum(t['steps'] for t in fams.values()),
            'per_family':fams,'tau':tau,
            'scope':'independent solver rebuilt <=4 and <=5 supports, saturation, decisions, surprise, residual, alarms and public certificates; v0.89 catalogue probabilities are not recomputed here (audited in study-001)'}


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--results-dir',default=str(STUDY_DIR));ap.add_argument('--write',action='store_true')
    a=ap.parse_args();rep=audit(a.results_dir)
    if a.write:
        from experiments.brute_common import write_new;write_new(Path(a.results_dir)/'INDEPENDENT_AUDIT.json',rep)
    print(json.dumps({k:v for k,v in rep.items() if k!='per_family'},indent=2))
