"""Independent audit of study BRUTE-020-ACTIVE-004 (plan G11). Imports NO brute module.

Written from the plan text (experiments/BRUTE_PLAN_004.json: experiment_rule, window_tier, probability_rule,
certification_rule = BRUTE_PLAN_002 gate order, residual_surprise, metrics, G9), not from brute/active.py.
The <=4 / <=5 supports, lookahead copies and window rows come from the separate non-vectorised solver in
experiments/v90_independent_reference.py; suffix-1 and the G8 reasons come from the study-003 reference
(experiments/v011_independent_reference.py, itself brute-free).

For arms A (active) and P (passive) it replays the world from the seed and recomputes, at every step:
the taken action (A: argmax LU score, exact tie -> passive action; P: passive action), every LU score,
<=4 and <=5 supports for BOTH actions, saturation, the decision for both actions (taken and counterfactual),
public certificates, wrong flags against the evaluator's hidden next emission for each action, surprise,
W-window residual and alarm, post-contradiction probabilities and forecast_source (margin_n5 / window_n4 /
suffix1), the window learner rows/status and restarts, the issued list (no duplicates) and every retraction
reason. For P it rechecks equality with the frozen v0.1.1 control (G8a). Before contradiction the v0.89/v0.90
term in the probabilities is checked for sum and floor only (as in studies 002/003). Explicit raises only.
"""
from __future__ import annotations
import argparse,json
from math import log
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor
from experiments.brute_common_004 import PLAN,FREEZE,STUDY_DIR,load,sha,check,check_freeze,write_new
from experiments.v90_independent_reference import ref_initial,ref_support,ref_observe,bit_compatible
from experiments.v011_independent_reference import RefSuffix1,ref_reason,expected_decision,PROB_TOL,_close
from bgr89.worlds import world as old_world,actions
from bgr90.worlds import world as new_world,step as new_step


def full(code):return ((code>>1)&1,code&1)


def lu_score(r4,s4,r5,s5,alarm,a,k4,k5,b4,b5):
    """experiment_rule LU, from the plan wording."""
    if s4!='supported' or s5!='supported' or alarm:return 0.
    S=ref_support(r4,a,k4);tot=0
    for c in S:
        f,st=ref_observe(r4,a,full(c),k4,b4)
        if st!='supported':continue
        if all(len(m.outputs)==k4 for m in f):continue
        m=None
        for b in (0,1):
            s=ref_support(f,b,k4)
            if len(s)!=1:continue
            if m is None:
                m,ms=ref_observe(r5,a,full(c),k5,b5)
                if ms!='supported':m=False
            if m is False:break
            tot+=ref_support(m,b,k5)==s
    return round(tot/len(S),12)


class _Arm:
    def __init__(self):self.surprises=[];self.alarm=False;self.alarm_step=None


def audit_arm(c,arm,plan,tau):
    fam=c['family'];seed=c['seed'];rate=c['mask_rate'];k4=plan['family_state_cap'];k5=plan['margin_state_cap']
    b4=plan['row_budget_family'];b5=plan['row_budget_margin'];wt=plan['window_tier']
    W_=plan['residual_surprise']['window_W'];eps=plan['open_world_reserve_epsilon'];where=f'{fam} {seed} {rate} {arm}'
    A=c['arms'][arm];trace=A['trace']
    truth=(new_world if fam in ('ood5','drift4') else old_world)(seed,fam)
    hidden=truth.start;initial=truth.observed(hidden,rate,-1)
    check(list(initial)==c['initial_visible'],'initial mismatch '+where)
    attested=fam in plan['in_family'];check(c['attested']==attested,'attestation flag')
    r4=ref_initial(initial);s4='supported';r5=ref_initial(initial);s5='supported'
    win=None;restarts=0;suffix=RefSuffix1(0.7,initial);st=_Arm();ctl_st=_Arm()
    issued=[];retracted=None;contradiction=None
    t={'steps':0,'certs':0,'wrong':0,'cf_certs':0,'cf_wrong':0,'public':0,'public_wrong':0,'scores_recomputed':0,
       'actions_recomputed':0,'cf_public':0,'cf_public_wrong':0,'post_contradiction_probabilities_recomputed':0,'window_n4_steps':0,'g8a_steps_checked':0}
    for i,pa in enumerate(actions(seed,plan['actions_per_case'])):
        rec=trace[i];step=i+1
        check(rec['step']==step and rec['passive_action']==pa,'step/passive mismatch '+where)
        if arm=='A':
            sc=[lu_score(r4,s4,r5,s5,st.alarm,b,k4,k5,b4,b5) for b in (0,1)]
            a=pa if sc[0]==sc[1] else (0 if sc[0]>sc[1] else 1)
            check(rec['experiment']=={'scores':sc,'score':sc[a],'tied':sc[0]==sc[1]},f'experiment score mismatch {where} {i}')
            t['scores_recomputed']+=2
        else:
            a=pa;check('experiment' not in rec,'P arm has experiment')
        check(rec['action']==a,f'action mismatch {where} {i}');t['actions_recomputed']+=1
        sat=all(len(m.outputs)==k4 for m in r4) if s4=='supported' else None
        nxt=[new_step(truth,hidden,b,i) if fam=='drift4' else truth.next(hidden,b) for b in (0,1)]
        act=[truth.emission(h) for h in nxt]
        dec={}
        for b,r in ((a,rec),(1-a,rec['counterfactual'])):
            sup=ref_support(r4,b,k4) if s4=='supported' else None
            msup=ref_support(r5,b,k5) if s5=='supported' else None
            check((list(sup) if sup is not None else None)==r['support'],f'support mismatch {where} {i} {b}')
            check((list(msup) if msup is not None else None)==r['margin_support'],f'margin mismatch {where} {i} {b}')
            check(sat==r['saturated'],'saturation mismatch '+where)
            s_,rs,cert=expected_decision(s4,st.alarm,sup,s5,msup,sat)
            check((s_,rs,cert)==(r['status'],r['reason'],r['certificate']),f'decision mismatch {where} {i} {b}')
            pub=cert if (cert is not None and attested) else None
            check(pub==r['public_certificate'],'public certificate mismatch '+where)
            check(r['wrong']==(cert is not None and cert!=act[b]) and r['public_wrong']==(pub is not None and pub!=act[b]),'wrong flag '+where)
            probs=r['probabilities'];check(abs(sum(probs)-1)<1e-9 and min(probs)>=eps/4-1e-12,'probability sum/floor '+where)
            if s4!='grammar_contradicted':
                check(r['forecast_source']=='v090','forecast_source before contradiction '+where)
            else:
                if s5=='supported' and msup:
                    q=[(1-eps)*(1/len(msup) if x in msup else 0.)+eps/4 for x in range(4)];src='margin_n5'
                else:
                    sx=suffix.predict(b);ws=ref_support(win,b,wt['state_cap']) if win else None
                    if ws:
                        z=sum(sx[x] for x in ws);q=[(1-eps)*(sx[x]/z if x in ws else 0.)+eps/4 for x in range(4)];src='window_n4'
                    else:q=[(1-eps)*p+eps/4 for p in sx];src='suffix1'
                check(r['forecast_source']==src,f'forecast_source mismatch {where} {i} {b}')
                check(_close(probs,q),f'post-contradiction probability mismatch {where} {i} {b}')
                check(cert is None,'fallback certified');t['post_contradiction_probabilities_recomputed']+=1
                t['window_n4_steps']+=src=='window_n4' and b==a
            dec[b]=(cert,pub)
        check(abs(rec['min_probability']-min(min(rec['probabilities']),min(rec['counterfactual']['probabilities'])))<1e-12,'min prob')
        check(rec['actual_emission_EVALUATOR_ONLY']==act[a] and rec['counterfactual_actual_EVALUATOR_ONLY']==act[1-a],'truth replay '+where)
        check(rec['drift_step']==(fam=='drift4' and step in (12,23,34)),'drift flag')
        hidden=nxt[a];obs=truth.observed(hidden,rate,i);check(rec['observed']==list(obs),'observation replay '+where)
        check(abs(rec['logloss']+log(max(1e-12,rec['probabilities'][act[a]])))<1e-8,'logloss')
        sup=ref_support(r4,a,k4) if s4=='supported' else None
        v090=sup[0] if sup is not None and len(sup)==1 else None
        check(rec['v090_certificate']==v090 and rec['v090_wrong']==(v090 is not None and v090!=act[a]),'v0.90 control '+where)
        # surprise / residual / alarm (taken action's published probabilities)
        s=-log(sum(p for x,p in enumerate(rec['probabilities']) if bit_compatible(x,obs)))
        check(abs(s-rec['surprise'])<1e-8,f'surprise mismatch {where} {i}');st.surprises.append(rec['surprise'])
        if len(st.surprises)>=W_:
            R=sum(st.surprises[-W_:])/W_;check(abs(R-rec['residual_after'])<1e-8,'residual '+where)
            if tau is not None and not st.alarm and rec['residual_after']>tau:st.alarm=True;st.alarm_step=step
        else:check(rec['residual_after'] is None,'residual too early')
        check(rec['alarm_after']==st.alarm,f'alarm mismatch {where} {i}')
        # P vs frozen v0.1.1 control (G8a)
        if arm=='P':
            q=A['control_trace'][i]
            for k in ('status','reason','certificate','public_certificate'):check(q[k]==rec[k],f'G8a {k} {where} {i}')
            if rec['forecast_source']!='window_n4':
                check(q['probabilities']==rec['probabilities'] and q['forecast_source']==rec['forecast_source'],f'G8a probabilities {where} {i}')
            else:
                check(q['forecast_source']=='suffix1','window replaced a non-suffix1 tier')
                sx=suffix.predict(a);check(_close(q['probabilities'],[(1-eps)*p+eps/4 for p in sx]),'control suffix1')
            check(q['wrong']==(q['certificate'] is not None and q['certificate']!=act[a]),'control wrong')
            sc_=-log(sum(p for x,p in enumerate(q['probabilities']) if bit_compatible(x,obs)))
            check(abs(sc_-q['surprise'])<1e-8,'control surprise');ctl_st.surprises.append(q['surprise'])
            if len(ctl_st.surprises)>=W_:
                if tau is not None and not ctl_st.alarm and q['residual_after']>tau:ctl_st.alarm=True;ctl_st.alarm_step=step
            check(q['alarm_after']==ctl_st.alarm,'control alarm')
            t['g8a_steps_checked']+=1
        cert=dec[a][0]
        if cert is not None and (step,cert) not in [(x[0],x[1]) for x in issued]:issued.append((step,cert,tuple(obs)))
        suffix.observe(a,obs)
        was=s4
        if s4=='supported':r4,s4=ref_observe(r4,a,obs,k4,b4);r4=r4 or frozenset()
        if s5=='supported':r5,s5=ref_observe(r5,a,obs,k5,b5);r5=r5 or frozenset()
        if s4=='grammar_contradicted':
            if was=='supported':win=ref_initial(obs);restarts+=1;contradiction=step;retracted=list(issued)
            else:
                w,ws=ref_observe(win,a,obs,wt['state_cap'],wt['row_budget'])
                if ws!='supported':win=ref_initial(obs);restarts+=1
                else:win=w
        check(rec['family_status_after']==s4 and rec['margin_status_after']==s5,'status mismatch '+where)
        check(rec['family_rows_after']==len(r4) and rec['margin_rows_after']==len(r5),'row count mismatch '+where)
        check(rec['window_status_after']==(None if win is None else 'supported') and
              rec['window_rows_after']==(None if win is None else len(win)),f'window mismatch {where} {i}')
        t['steps']+=1;t['certs']+=cert is not None;t['wrong']+=rec['wrong'];t['public']+=dec[a][1] is not None
        t['public_wrong']+=rec['public_wrong'];t['cf_certs']+=dec[1-a][0] is not None;t['cf_wrong']+=rec['counterfactual']['wrong']
        t['cf_public']+=dec[1-a][1] is not None;t['cf_public_wrong']+=rec['counterfactual']['public_wrong']
    check(A['issued']==[[s_,k] for s_,k,_ in issued],'issued list mismatch '+where)
    acts={r['step']:r['actual_emission_EVALUATOR_ONLY'] for r in trace}
    exp=[{'step':s_,'certificate':k,'observed':list(o),'reason':ref_reason(k,o),'actual_EVALUATOR_ONLY':acts[s_],'wrong':k!=acts[s_]}
         for s_,k,o in (retracted or [])]
    check(A['retractions']==exp,'retraction list/reason mismatch '+where)
    check(len({(e['step'],e['certificate']) for e in exp})==len(exp),'duplicate retraction')
    d=A['diagnostics']
    check(d['certificates_retracted']==len(exp) and d['certificates_issued']==len(issued),'retraction counts '+where)
    check(d['alarm_step']==st.alarm_step and d['window_restarts']==restarts,'alarm step / window restarts '+where)
    if arm=='P':check(A['control_diagnostics']['alarm_step']==ctl_st.alarm_step,'control alarm step')
    t['retractions']=len(exp);t['retracted_wrong']=sum(e['wrong'] for e in exp);t['window_restarts']=restarts
    t['alarm_case']=int(st.alarm_step is not None)
    return t


def audit_case(args):
    c,plan,tau=args
    return {arm:audit_arm(c,arm,plan,tau) for arm in ('A','P')}


def _add(acc,t):
    for k,v in t.items():acc[k]=acc.get(k,0)+v


def audit(directory=STUDY_DIR,workers=4):
    directory=Path(directory);res=load(directory/'RESULTS.json');seal=load(directory/'SEAL.json')
    check(sha(directory/'RESULTS.json')==seal['results_sha256'],'RESULTS hash')
    check(sha(directory/'SCIENTIFIC.json')==seal['scientific_sha256'],'SCIENTIFIC hash')
    check(sha(PLAN)==seal['plan_sha256'] and res['plan']==load(PLAN),'plan mismatch')
    check(sha(FREEZE)==seal['freeze_sha256'],'freeze mismatch');check_freeze()
    cal=load(directory/'CALIBRATION_CHECK.json')
    check(sha(directory/'CALIBRATION_CHECK.json')==seal['calibration_check_sha256'] and cal==res['calibration_check'],'calibration check')
    plan=res['plan'];tau=plan['residual_surprise']['tau'];check(cal['tau']==tau and cal['tau_reproduced'] is True,'tau')
    seen=set()
    for c in res['cases']:
        lo,hi=plan['heldout_ranges'][c['family']];check(lo<=c['seed']<=hi and c['mask_rate'] in plan['mask_rates'],'case outside plan')
        key=(c['family'],c['seed'],c['mask_rate']);check(key not in seen,'duplicate case');seen.add(key);check(c['tau']==tau,'case tau')
    expected=sum((hi-lo+1)*len(plan['mask_rates']) for lo,hi in plan['heldout_ranges'].values())
    check(len(seen)==expected==seal['case_count'],'case count')
    jobs=[(c,plan,tau) for c in res['cases']]
    if workers<=1:outs=[audit_case(j) for j in jobs]
    else:
        with ProcessPoolExecutor(workers) as ex:outs=list(ex.map(audit_case,jobs,chunksize=1))
    fams={}
    for c,o in zip(res['cases'],outs):
        for arm,t in o.items():_add(fams.setdefault(c['family'],{}).setdefault(arm,{}),t)
    for fam,arms in fams.items():
        s=res['summary'][fam]
        for arm,t in arms.items():
            S=s[arm]
            check(S['certs_all']==t['certs'] and S['false_certs_all']==t['wrong'],f'summary {arm} {fam}')
            check(S['counterfactual_certs_all']==t['cf_certs'] and S['counterfactual_false_certs_all']==t['cf_wrong'],f'summary cf {arm} {fam}')
            check(S['public_certs_all']==t['public']+t['cf_public'] and S['public_false_certs_all']==t['public_wrong']+t['cf_public_wrong'],
                  f'summary public {arm} {fam}')
            check(S['certificates_retracted']==t['retractions'] and S['retracted_wrong']==t['retracted_wrong'],f'summary retractions {arm} {fam}')
            check(S['window_restarts']==t['window_restarts'] and S['cases_with_alarm']==t['alarm_case'],f'summary window/alarm {arm} {fam}')
            check(S['duplicate_issued_pairs']==0 and S['duplicate_retraction_pairs']==0,'duplicates')
    return {'schema':'brute.independent-audit.v2_0','status':'passed','mismatches':0,'study':plan['study'],
            'source_results_sha256':seal['results_sha256'],'cases':len(seen),
            'steps_replayed_per_arm':sum(t['steps'] for a in fams.values() for t in a.values())//2,'per_family':fams,'tau':tau,
            'probability_tolerance':PROB_TOL,
            'scope':('independent solver (experiments/v90_independent_reference.py) rebuilt <=4 and <=5 supports for both actions, '
                     'saturation, LU lookahead copies and window rows; every LU score and chosen action (A), every decision for the '
                     'taken and counterfactual action, public certificates, wrong flags against evaluator truth for each action, '
                     'surprise, residual and alarms, post-contradiction probabilities and forecast_source (margin_n5 / window_n4 / '
                     'suffix1, suffix-1 rebuilt from its definition), window restarts, issued lists (no duplicates) and retraction '
                     'reasons recomputed; P checked against the frozen v0.1.1 control at every step (G8a); the v0.89 catalogue term '
                     'before contradiction checked for sum and floor only')}


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--results-dir',default=str(STUDY_DIR));ap.add_argument('--write',action='store_true')
    ap.add_argument('--workers',type=int,default=4)
    a=ap.parse_args();rep=audit(a.results_dir,a.workers)
    if a.write:write_new(Path(a.results_dir)/'INDEPENDENT_AUDIT.json',rep)
    print(json.dumps({k:v for k,v in rep.items() if k!='per_family'},indent=2))
