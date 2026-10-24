"""Independent audit of study BRUTE-011-FALLBACK-003 (plan G10, amendment A5). Imports NO brute module.

Written from the plan text (experiments/BRUTE_PLAN_003.json: probability_rule, certification_rule
= BRUTE_PLAN_002 gate order, residual_surprise, G8 wording), not from brute/fallback.py.
The <=4 / <=5 supports come from the separate non-vectorised solver in
experiments/v90_independent_reference.py. For BOTH arms (v0.1.1 and the v0.1.0 control) it
recomputes supports, saturation, every decision, public certificates, surprise, the W-window
residual and the alarm. For v0.1.1 it also recomputes every post-contradiction probability and
forecast_source (margin_n5 / suffix-1 rebuilt from its definition / uniform), the ablation
log-loss, the retracted-certificate list and every retraction reason against evaluator truth.
Before contradiction the v0.1.1 probabilities must equal the v0.1.0 control exactly; the v0.89
term inside them is checked for sum and floor only (as in study-002). Explicit raises only.
"""
from __future__ import annotations
import argparse,json
from math import log
from pathlib import Path
from experiments.brute_common_003 import PLAN,FREEZE,STUDY_DIR,load,sha,check,check_freeze,write_new
from experiments.v90_independent_reference import ref_initial,ref_support,ref_observe,bit_compatible
from bgr89.worlds import world as old_world,actions
from bgr90.worlds import world as new_world,step as new_step

PROB_TOL=1e-11   # recorded probabilities are rounded to 12 d.p.


def expected_decision(fam_status,alarm,support,margin_status,margin_support,saturated):
    """BRUTE_PLAN_002 certification_rule gate order (unchanged in plan 003)."""
    if fam_status=='grammar_contradicted':return 'OUT_OF_FAMILY','FAMILY_CONTRADICTED',None
    if alarm:return 'OUT_OF_FAMILY','RESIDUAL_SURPRISE',None
    if fam_status=='budget_exhausted':return 'ABSTAIN','BUDGET_EXHAUSTED',None
    if len(support)!=1:return 'POSSIBLE_SET',None,None
    if margin_status=='budget_exhausted':return 'ABSTAIN','BUDGET_EXHAUSTED',None
    if margin_support!=support:return 'ABSTAIN','MARGIN_DISAGREES',None
    if saturated:return 'ABSTAIN','BOUND_SATURATED',None
    return 'CERTIFIED',None,support[0]


class RefSuffix1:
    """Suffix-1 frequency, rebuilt from its definition: context = (previous action, previous
    observation), current observation, next action; alpha-smoothed counts over the 4 codes;
    only fully unmasked observations are counted; masked ones still advance the context."""
    def __init__(self,alpha,first_obs):
        self.alpha=alpha;self.hist=[(None,tuple(first_obs))];self.table={}

    def _ctx(self,action):
        prev=self.hist[-1] if len(self.hist)>1 else None
        return (prev,self.hist[-1][1],action)

    def predict(self,action):
        t=self.table.get(self._ctx(action),[0.]*4);z=sum(t)+4*self.alpha
        return [(x+self.alpha)/z for x in t]

    def observe(self,action,obs):
        ctx=self._ctx(action);self.hist.append((action,tuple(obs)))
        if obs[0] is not None and obs[1] is not None:
            self.table.setdefault(ctx,[0.]*4)[2*obs[0]+obs[1]]+=1


def ref_reason(cert,obs):
    """G8 / A4 from the plan wording."""
    bits=((cert>>1)&1,cert&1)
    if any(o is not None and o!=b for o,b in zip(obs,bits)):return 'falsified_by_observation'
    if all(o is not None for o in obs):return 'scope_withdrawn'
    return 'unverifiable_masked'


def _close(a,b):return len(a)==len(b)==4 and all(abs(x-y)<=PROB_TOL for x,y in zip(a,b))


class _Arm:
    def __init__(self,name):self.name=name;self.surprises=[];self.alarm=False;self.alarm_step=None


def audit_case(c,plan,tau):
    fam=c['family'];seed=c['seed'];rate=c['mask_rate'];k4=plan['family_state_cap'];k5=plan['margin_state_cap']
    W=plan['residual_surprise']['window_W'];eps=plan['open_world_reserve_epsilon'];where=f'{fam} {seed} {rate}'
    truth=(new_world if fam in ('ood5','drift4') else old_world)(seed,fam)
    hidden=truth.start;initial=truth.observed(hidden,rate,-1)
    check(list(initial)==c['initial_visible'],'initial mismatch '+where)
    attested=fam in plan['in_family'];check(c['attested']==attested,'attestation flag mismatch')
    r4=ref_initial(initial);s4='supported';r5=ref_initial(initial);s5='supported'
    suffix=RefSuffix1(0.7,initial);arms={'v0.1.1':_Arm('v0.1.1'),'v0.1.0':_Arm('v0.1.0')}
    issued=[];retracted=None;contradiction_step=None
    t={'steps':0,'v011_certs':0,'v011_wrong':0,'v011_public':0,'v011_public_wrong':0,'v010_certs':0,'v010_wrong':0,
       'v090_wrong':0,'post_contradiction_probabilities_recomputed':0,'pre_contradiction_probabilities_equal':0,
       'forecast_sources_post':{}}
    for i,(a,rec) in enumerate(zip(actions(seed,plan['actions_per_case']),c['trace'])):
        ctl=c['control_trace'][i];step=i+1
        check(rec['step']==step==ctl['step'] and rec['action']==a,'action mismatch '+where)
        sup=ref_support(r4,a,k4) if s4=='supported' else None
        msup=ref_support(r5,a,k5) if s5=='supported' else None
        sat=all(len(m.outputs)==k4 for m in r4) if s4=='supported' else None
        check((list(sup) if sup is not None else None)==rec['support'],f'support mismatch {where} {i}')
        check((list(msup) if msup is not None else None)==rec['margin_support'],f'margin mismatch {where} {i}')
        check(sat==rec['saturated'],'saturation mismatch')
        check(rec['drift_step']==(fam=='drift4' and step%11==1 and step>1),'drift_step flag mismatch '+where)
        hidden=new_step(truth,hidden,a,i) if fam=='drift4' else truth.next(hidden,a)
        actual=truth.emission(hidden);obs=truth.observed(hidden,rate,i)
        check(rec['actual_emission_EVALUATOR_ONLY']==actual and rec['observed']==list(obs),'truth replay mismatch')
        decisions={}
        for name,r in (('v0.1.1',rec),('v0.1.0',ctl)):
            A=arms[name];st,rs,cert=expected_decision(s4,A.alarm,sup,s5,msup,sat)
            check((st,rs,cert)==(r['status'],r['reason'],r['certificate']),f'{name} decision mismatch {where} {i}')
            pub=cert if (cert is not None and attested) else None
            check(pub==r['public_certificate'],f'{name} public certificate mismatch')
            probs=r['probabilities']
            check(abs(sum(probs)-1)<1e-9,f'{name} probabilities do not sum to 1')
            check(min(probs)>=eps/4-1e-12 and abs(r['min_probability']-min(probs))<1e-12,f'{name} open-world reserve violated')
            check(r['brute_wrong']==(cert is not None and cert!=actual),f'{name} wrong flag mismatch')
            check(r['public_wrong']==(pub is not None and pub!=actual),f'{name} public wrong flag mismatch')
            check(abs(r['logloss_brute']+log(max(1e-12,probs[actual])))<1e-8,f'{name} logloss mismatch')
            s=-log(sum(p for code,p in enumerate(probs) if bit_compatible(code,obs)))
            check(abs(s-r['surprise'])<1e-8,f'{name} surprise mismatch {where} {i}');A.surprises.append(r['surprise'])
            if len(A.surprises)>=W:
                R=sum(A.surprises[-W:])/W;check(abs(R-r['residual_after'])<1e-8,f'{name} residual mismatch')
                if tau is not None and not A.alarm and r['residual_after']>tau:A.alarm=True;A.alarm_step=step
            else:check(r['residual_after'] is None,'residual defined too early')
            check(r['alarm_after']==A.alarm,f'{name} alarm mismatch {where} {i}')
            decisions[name]=(cert,pub)
        # v0.1.1 probability rule
        if s4!='grammar_contradicted':
            check(rec['forecast_source']=='v090','forecast_source before contradiction')
            check(rec['probabilities']==ctl['probabilities'],f'pre-contradiction probabilities differ from v0.1.0 {where} {i}')
            check(rec['logloss_ablation']==rec['logloss_brute'],'ablation before contradiction')
            t['pre_contradiction_probabilities_equal']+=1
        else:
            if s5=='supported' and msup:
                q=[(1-eps)*(1/len(msup) if code in msup else 0.)+eps/4 for code in range(4)];src='margin_n5';abl=q
            else:
                q=[(1-eps)*p+eps/4 for p in suffix.predict(a)];src='suffix1';abl=[.25]*4
            check(rec['forecast_source']==src,f'forecast_source mismatch {where} {i}')
            check(_close(rec['probabilities'],q),f'post-contradiction probability mismatch {where} {i}')
            check(abs(rec['logloss_ablation']+log(max(1e-12,abl[actual])))<1e-8,'ablation logloss mismatch')
            check(decisions['v0.1.1'][0] is None,'fallback certified')
            t['post_contradiction_probabilities_recomputed']+=1
        if step>c['burn_in']:t['forecast_sources_post'][rec['forecast_source']]=t['forecast_sources_post'].get(rec['forecast_source'],0)+1
        v090=sup[0] if sup is not None and len(sup)==1 else None
        check(rec['v090_certificate']==v090 and rec['v090_wrong']==(v090 is not None and v090!=actual),'v0.90 control mismatch')
        cert=decisions['v0.1.1'][0]
        if cert is not None:issued.append((step,cert,tuple(obs)))
        suffix.observe(a,obs)
        if s4=='supported':
            r4,s4=ref_observe(r4,a,obs,k4,plan['row_budget_family']);r4=r4 or frozenset()
        if s5=='supported':
            r5,s5=ref_observe(r5,a,obs,k5,plan['row_budget_margin']);r5=r5 or frozenset()
        if s4=='grammar_contradicted' and contradiction_step is None:contradiction_step=step;retracted=list(issued)
        check(rec['family_status_after']==s4 and rec['margin_status_after']==s5,'status mismatch')
        check(rec['family_rows_after']==len(r4) and rec['margin_rows_after']==len(r5),'row count mismatch')
        t['steps']+=1
        t['v011_certs']+=cert is not None;t['v011_wrong']+=cert is not None and cert!=actual
        t['v011_public']+=decisions['v0.1.1'][1] is not None;t['v011_public_wrong']+=rec['public_wrong']
        t['v010_certs']+=ctl['certificate'] is not None;t['v010_wrong']+=ctl['brute_wrong']
        t['v090_wrong']+=v090 is not None and v090!=actual
    # retractions (G8)
    acts={r['step']:r['actual_emission_EVALUATOR_ONLY'] for r in c['trace']}
    exp=[{'step':s,'certificate':k,'observed':list(o),'reason':ref_reason(k,o),'actual_EVALUATOR_ONLY':acts[s],'wrong':k!=acts[s]}
         for s,k,o in (retracted or [])]
    check(c['retractions']==exp,'retraction list/reason mismatch '+where)
    d=c['diagnostics']
    check(d['certificates_retracted']==len(exp) and d['certificates_issued']==len(issued),'retraction counts')
    check(d['retraction_reasons']=={x:sum(e['reason']==x for e in exp) for x in ('falsified_by_observation','scope_withdrawn','unverifiable_masked')},'diagnostic reasons')
    check(c['control_diagnostics']['certificates_retracted']==len(exp),'control retractions (pre-contradiction arms are identical)')
    falsified_truth=sum(e['wrong'] and any(o is not None and o!=b for o,b in zip(e['observed'],((e['certificate']>>1)&1,e['certificate']&1))) for e in exp)
    check(sum(e['reason']=='falsified_by_observation' for e in exp)==falsified_truth,'G8 falsified count != retracted wrong with contradicting bit')
    t['retractions']=len(exp);t['retracted_wrong']=sum(e['wrong'] for e in exp)
    t['retraction_reasons']=d['retraction_reasons']
    t['wrong_never_contradicted']=t['v011_wrong'] if contradiction_step is None else 0
    for name in arms:
        dd=c['diagnostics'] if name=='v0.1.1' else c['control_diagnostics']
        check(dd['alarm_step']==(None if arms[name].alarm_step is None else arms[name].alarm_step),f'{name} alarm step')
    return t


def _add(acc,t):
    for k,v in t.items():
        if isinstance(v,dict):
            sub=acc.setdefault(k,{})
            for kk,vv in v.items():sub[kk]=sub.get(kk,0)+vv
        else:acc[k]=acc.get(k,0)+v


def audit(directory=STUDY_DIR):
    directory=Path(directory);res=load(directory/'RESULTS.json');seal=load(directory/'SEAL.json')
    check(sha(directory/'RESULTS.json')==seal['results_sha256'],'RESULTS hash')
    check(sha(directory/'SCIENTIFIC.json')==seal['scientific_sha256'],'SCIENTIFIC hash')
    check(sha(PLAN)==seal['plan_sha256'] and res['plan']==load(PLAN),'plan mismatch')
    check(sha(FREEZE)==seal['freeze_sha256'],'freeze mismatch');check_freeze()
    cal=load(directory/'CALIBRATION_CHECK.json')
    check(sha(directory/'CALIBRATION_CHECK.json')==seal['calibration_check_sha256'] and cal==res['calibration_check'],'calibration check mismatch')
    plan=res['plan'];tau=plan['residual_surprise']['tau'];check(cal['tau']==tau and cal['tau_reproduced'] is True,'tau')
    seen=set();fams={}
    for c in res['cases']:
        lo,hi=plan['heldout_ranges'][c['family']];check(lo<=c['seed']<=hi and c['mask_rate'] in plan['mask_rates'],'case outside plan')
        key=(c['family'],c['seed'],c['mask_rate']);check(key not in seen,'duplicate case');seen.add(key)
        check(c['tau']==tau,'case tau');_add(fams.setdefault(c['family'],{}),audit_case(c,plan,tau))
    expected=sum((hi-lo+1)*len(plan['mask_rates']) for lo,hi in plan['heldout_ranges'].values())
    check(len(seen)==expected==seal['case_count'],'case count')
    for fam,t in fams.items():
        s=res['summary'][fam]
        check(s['v0.1.1']['certs_all']==t['v011_certs'] and s['v0.1.1']['false_certs_all']==t['v011_wrong'],'summary v0.1.1 '+fam)
        check(s['v0.1.1']['public_certs_all']==t['v011_public'] and s['v0.1.1']['public_false_certs_all']==t['v011_public_wrong'],'summary public '+fam)
        check(s['v0.1.0']['certs_all']==t['v010_certs'] and s['v0.1.0']['false_certs_all']==t['v010_wrong'],'summary v0.1.0 '+fam)
        check(s['v0.90']['false_certs_all']==t['v090_wrong'],'summary v0.90 '+fam)
        check(s['retraction_reasons']==t['retraction_reasons'] and s['retracted_wrong']==t['retracted_wrong'],'summary retractions '+fam)
        check({k:v for k,v in s['forecast_source_steps_post'].items() if v}==t['forecast_sources_post'],'summary forecast sources '+fam)
        check(s['wrong_certs_in_never_contradicted_cases']==t['wrong_never_contradicted'],'summary never-contradicted '+fam)
    return {'schema':'brute.independent-audit.v1_1','status':'passed','mismatches':0,'study':plan['study'],
            'source_results_sha256':seal['results_sha256'],'cases':len(seen),
            'steps_replayed':sum(t['steps'] for t in fams.values()),'per_family':fams,'tau':tau,
            'probability_tolerance':PROB_TOL,
            'scope':('independent solver (experiments/v90_independent_reference.py) rebuilt <=4 and <=5 supports and saturation; '
                     'decisions, public certificates, surprise, residual and alarms recomputed for both the v0.1.1 and v0.1.0 arms; '
                     'v0.1.1 post-contradiction probabilities, forecast_source and ablation log-loss recomputed (suffix-1 rebuilt '
                     'from its definition); retraction lists and G8 reasons recomputed against evaluator truth; pre-contradiction '
                     'v0.1.1 probabilities checked equal to the v0.1.0 arm exactly; v0.89 catalogue term checked for sum and floor only')}


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--results-dir',default=str(STUDY_DIR));ap.add_argument('--write',action='store_true')
    a=ap.parse_args();rep=audit(a.results_dir)
    if a.write:write_new(Path(a.results_dir)/'INDEPENDENT_AUDIT.json',rep)
    print(json.dumps({k:v for k,v in rep.items() if k!='per_family'},indent=2))
