"""Independent audit of study BRUTE-030-CHANGEPOINT-005 (plan G11). Imports NO brute module.

Written from the plan text (experiments/BRUTE_PLAN_005.json: certification_rule Y1k, experiment_rule LU-R and its
check_option, arms, metrics, G9), not from brute/changepoint.py. Supports, lookahead copies and window rows come from
the separate non-vectorised solver in experiments/v90_independent_reference.py; the v0.2.0 gate order, LU score,
suffix-1 and retraction reasons come from the brute-free study-003/004 references.

Full arms (A3, P3) are replayed exactly as in the study-004 reference (experiments/v020_independent_reference.py)
plus the Y1k union for the taken and the counterfactual action and the LU-R scores; P3 is checked against the frozen
v0.1.1 control at every step (only RESYNC_AMBIGUOUS downgrades of a control certificate may differ).
Slim arms (A2, P2, E2 in the main block; A3, A2, E2 in the extended drift4 block) recompute every LU / LU-R score,
the chosen action, the untaken-branch check flag, both decisions (taken + counterfactual), wrong flags against the
evaluator's hidden next emission, the issued list and the stale / check / switch metrics. Slim records carry no
probabilities, so for them the residual alarm is read from the record's alarm_after flag (stated in the report).
Explicit raises only.
"""
from __future__ import annotations
import argparse,json
from math import log
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor
from experiments.brute_common_005 import PLAN,FREEZE,STUDY_DIR,load,sha,check,check_freeze,write_new
from experiments.v90_independent_reference import ref_initial,ref_support,ref_observe,bit_compatible
from experiments.v011_independent_reference import RefSuffix1,ref_reason,expected_decision,PROB_TOL,_close
from bgr89.worlds import world as old_world,actions
from bgr90.worlds import world as new_world,step as new_step

ARM_SPEC={'A3':(True,True,0),'P3':(False,True,0),'A2':(True,False,0),'P2':(False,False,0),'E2':(True,False,3)}  # active,resync,check_run
DRIFT=(12,23,34)


def window_tier(plan):
    """Plan 005 says its window tier is identical to BRUTE_PLAN_004's; take the parameters from there."""
    wt=plan['window_tier']
    if isinstance(wt,str):
        check(wt.startswith('identical to BRUTE_PLAN_004'),'unexpected window_tier wording')
        wt=load(PLAN.with_name('BRUTE_PLAN_004.json'))['window_tier']
    return wt


def full(code):return ((code>>1)&1,code&1)


def compatible_codes(obs):return frozenset(c for c in range(4) if bit_compatible(c,obs))


def y1k_union(rows,b,codes,k4):
    """certification_rule Y1k, from the plan wording: union over rows and visited states meeting `codes`."""
    U=set()
    for m in rows:
        for j,out in enumerate(m.outputs):
            if not (out&codes):continue
            d=m.paths[j*2+b]
            if d>=0:U|=m.outputs[d]
            elif j==m.current:
                for o in m.outputs:U|=o
                if len(m.outputs)<k4:U|=set(range(4))
    return frozenset(U)


def score(r4,s4,r5,s5,alarm,a,k4,k5,b4,b5,resync):
    """experiment_rule LU (resync False) / LU-R (resync True)."""
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
            if resync and y1k_union(f,b,frozenset((c,)),k4)!=frozenset(s):continue
            if m is None:
                m,ms=ref_observe(r5,a,full(c),k5,b5)
                if ms!='supported':m=False
            if m is False:break
            tot+=ref_support(m,b,k5)==s
    return round(tot/len(S),12)


class _Arm:
    def __init__(self):self.surprises=[];self.alarm=False;self.alarm_step=None


def audit_arm(c,arm,plan,tau,fullrec):
    active,resync,check_run=ARM_SPEC[arm]
    fam=c['family'];seed=c['seed'];rate=c['mask_rate'];k4=plan['family_state_cap'];k5=plan['margin_state_cap']
    b4=plan['row_budget_family'];b5=plan['row_budget_margin'];wt=window_tier(plan)
    W_=plan['residual_surprise']['window_W'];eps=plan['open_world_reserve_epsilon'];where=f'{fam} {seed} {rate} {arm}'
    A=c['arms'][arm];trace=A['trace'];B=c['burn_in']
    truth=(new_world if fam in ('ood5','drift4') else old_world)(seed,fam)
    hidden=truth.start;initial=truth.observed(hidden,rate,-1)
    check(list(initial)==c['initial_visible'],'initial mismatch '+where)
    attested=fam in plan['in_family'];check(c['attested']==attested,'attestation flag')
    r4=ref_initial(initial);s4='supported';r5=ref_initial(initial);s5='supported';last=initial
    win=None;restarts=0;suffix=RefSuffix1(0.7,initial);st=_Arm();ctl_st=_Arm()
    issued=[];retracted=None;taken=[]
    t={'steps':0,'certs':0,'wrong':0,'cf_certs':0,'cf_wrong':0,'public':0,'public_wrong':0,'cf_public':0,'cf_public_wrong':0,
       'scores_recomputed':0,'actions_recomputed':0,'checks':0,'switches_post':0,'resync_downgrades':0,'stale_false':0,
       'post_contradiction_probabilities_recomputed':0,'window_n4_steps':0,'g8a_steps_checked':0}
    for i,pa in enumerate(actions(seed,plan['actions_per_case'])):
        rec=trace[i];step=i+1
        check(rec['step']==step and rec['passive_action']==pa,'step/passive mismatch '+where)
        alarm=st.alarm if fullrec else (i>0 and trace[i-1]['alarm_after'])
        if active:
            sc=[score(r4,s4,r5,s5,alarm,b,k4,k5,b4,b5,resync) for b in (0,1)]
            a=pa if sc[0]==sc[1] else (0 if sc[0]>sc[1] else 1);chk=False
            if check_run and s4=='supported' and s5=='supported' and not alarm and len(taken)>=check_run \
               and all(x==a for x in taken[-check_run:]):a=1-a;chk=True
            e=rec['experiment']
            check(e['scores']==sc and e['score']==sc[a] and e['tied']==(sc[0]==sc[1]) and e['check']==chk,
                  f'experiment mismatch {where} {i}')
            want='PROPOSED' if (s4=='supported' and s5=='supported' and not alarm) else 'NO_PROPOSAL'
            if resync or check_run:check(e['proposal']==want,f'proposal mismatch {where} {i}')
            t['scores_recomputed']+=2;t['checks']+=chk and i>=B
        else:
            a=pa;check('experiment' not in rec,'passive arm has experiment')
        check(rec['action']==a,f'action mismatch {where} {i}');t['actions_recomputed']+=1
        if i>=B:t['switches_post']+=a!=taken[-1]
        sat=all(len(m.outputs)==k4 for m in r4) if s4=='supported' else None
        nxt=[new_step(truth,hidden,b,i) if fam=='drift4' else truth.next(hidden,b) for b in (0,1)]
        act=[truth.emission(h) for h in nxt]
        dec={}
        for b,r in ((a,rec),(1-a,rec['counterfactual'])):
            sup=ref_support(r4,b,k4) if s4=='supported' else None
            msup=ref_support(r5,b,k5) if s5=='supported' else None
            if 'support' in r:
                check((list(sup) if sup is not None else None)==r['support'],f'support mismatch {where} {i} {b}')
                check((list(msup) if msup is not None else None)==r['margin_support'],f'margin mismatch {where} {i} {b}')
                check(sat==r['saturated'],'saturation mismatch '+where)
            s_,rs,cert=expected_decision(s4,alarm,sup,s5,msup,sat);v020=cert
            if resync and cert is not None and y1k_union(r4,b,compatible_codes(last),k4)!=frozenset((cert,)):
                s_,rs,cert='ABSTAIN','RESYNC_AMBIGUOUS',None;t['resync_downgrades']+=1
            check((s_,rs,cert)==(r['status'],r['reason'],r['certificate']),f'decision mismatch {where} {i} {b}')
            pub=cert if (cert is not None and attested) else None
            check(pub==r['public_certificate'],'public certificate mismatch '+where)
            check(r['wrong']==(cert is not None and cert!=act[b]) and r['public_wrong']==(pub is not None and pub!=act[b]),'wrong flag '+where)
            if 'probabilities' in r:
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
            dec[b]=(cert,pub,v020)
        check(rec['actual_emission_EVALUATOR_ONLY']==act[a] and rec['counterfactual_actual_EVALUATOR_ONLY']==act[1-a],'truth replay '+where)
        check(rec['drift_step']==(fam=='drift4' and step in DRIFT),'drift flag')
        if fam=='drift4' and step>DRIFT[0] and step not in DRIFT:t['stale_false']+=rec['wrong']+rec['counterfactual']['wrong']
        hidden=nxt[a];obs=truth.observed(hidden,rate,i)
        if 'probabilities' in rec:check(abs(rec['logloss']+log(max(1e-12,rec['probabilities'][act[a]])))<1e-8,'logloss')
        if fullrec:
            check(rec['observed']==list(obs),'observation replay '+where)
            check(abs(rec['min_probability']-min(min(rec['probabilities']),min(rec['counterfactual']['probabilities'])))<1e-12,'min prob')
            sup=ref_support(r4,a,k4) if s4=='supported' else None
            v090=sup[0] if sup is not None and len(sup)==1 else None
            check(rec['v090_certificate']==v090 and rec['v090_wrong']==(v090 is not None and v090!=act[a]),'v0.90 control '+where)
            s=-log(sum(p for x,p in enumerate(rec['probabilities']) if bit_compatible(x,obs)))
            check(abs(s-rec['surprise'])<1e-8,f'surprise mismatch {where} {i}');st.surprises.append(rec['surprise'])
            if len(st.surprises)>=W_:
                R=sum(st.surprises[-W_:])/W_;check(abs(R-rec['residual_after'])<1e-8,'residual '+where)
                if tau is not None and not st.alarm and rec['residual_after']>tau:st.alarm=True;st.alarm_step=step
            else:check(rec['residual_after'] is None,'residual too early')
            check(rec['alarm_after']==st.alarm,f'alarm mismatch {where} {i}')
        if arm=='P3':
            q=A['control_trace'][i]
            if rec['reason']=='RESYNC_AMBIGUOUS':
                check(q['status']=='CERTIFIED' and q['certificate']==dec[a][2],f'G8a resync vs control {where} {i}')
            else:
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
        suffix.observe(a,obs);taken.append(a);last=obs
        was=s4
        if s4=='supported':r4,s4=ref_observe(r4,a,obs,k4,b4);r4=r4 or frozenset()
        if s5=='supported':r5,s5=ref_observe(r5,a,obs,k5,b5);r5=r5 or frozenset()
        if s4=='grammar_contradicted':
            if was=='supported':win=ref_initial(obs);restarts+=1;retracted=list(issued)
            else:
                w,ws=ref_observe(win,a,obs,wt['state_cap'],wt['row_budget'])
                if ws!='supported':win=ref_initial(obs);restarts+=1
                else:win=w
        if fullrec:
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
    d=A['diagnostics']
    check(d['certificates_retracted']==len(exp) and d['certificates_issued']==len(issued),'retraction counts '+where)
    check(d['window_restarts']==restarts and d['resync']==resync and d['check_run']==check_run if 'resync' in d else d['window_restarts']==restarts,
          'window restarts / arm settings '+where)
    if fullrec:check(d['alarm_step']==st.alarm_step,'alarm step '+where)
    if arm=='P3':check(A['control_diagnostics']['alarm_step']==ctl_st.alarm_step,'control alarm step')
    t['retractions']=len(exp);t['retracted_wrong']=sum(e['wrong'] for e in exp);t['window_restarts']=restarts
    t['alarm_case']=int(d['alarm_step'] is not None)
    return t


def audit_case(args):
    c,plan,tau=args
    return {arm:audit_arm(c,arm,plan,tau,arm in ('A3','P3') and 'observed' in c['arms'][arm]['trace'][0]) for arm in c['arms']}


def _add(acc,t):
    for k,v in t.items():acc[k]=acc.get(k,0)+v


def _check_summary(summary,fams,label):
    for fam,arms in fams.items():
        s=summary[fam]
        for arm,t in arms.items():
            S=s[arm];w=f'{label} {arm} {fam}'
            check(S['certs_all']==t['certs'] and S['false_certs_all']==t['wrong'],'summary '+w)
            check(S['counterfactual_certs_all']==t['cf_certs'] and S['counterfactual_false_certs_all']==t['cf_wrong'],'summary cf '+w)
            check(S['public_certs_all']==t['public']+t['cf_public'] and S['public_false_certs_all']==t['public_wrong']+t['cf_public_wrong'],'summary public '+w)
            check(S['certificates_retracted']==t['retractions'] and S['retracted_wrong']==t['retracted_wrong'],'summary retractions '+w)
            check(S['window_restarts']==t['window_restarts'] and S['cases_with_alarm']==t['alarm_case'],'summary window/alarm '+w)
            check(S['stale_false_certs']==t['stale_false'] and S['check_steps_post']==t['checks'],'summary stale/check '+w)
            check(abs(S['switch_rate_post']-round(t['switches_post']/S_post(s,arm),6))<1e-9,'summary switch '+w)
            check(S['duplicate_issued_pairs']==0 and S['duplicate_retraction_pairs']==0,'duplicates')


def S_post(s,arm):return s['steps_post_burn_in']


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
        check(sorted(c['arms'])==sorted(ARM_SPEC),'main arms')
        key=(c['family'],c['seed'],c['mask_rate']);check(key not in seen,'duplicate case');seen.add(key);check(c['tau']==tau,'case tau')
    expected=sum((hi-lo+1)*len(plan['mask_rates']) for lo,hi in plan['heldout_ranges'].values())
    check(len(seen)==expected==seal['case_count'],'case count')
    X=plan['extended_drift4_block'];xs=set()
    for c in res['extended_cases']:
        check(c['family']=='drift4' and X['range'][0]<=c['seed']<=X['range'][1] and c['mask_rate'] in X['mask_rates'],'extended case outside plan')
        check(sorted(c['arms'])==sorted(X['arms']),'extended arms');key=(c['seed'],c['mask_rate']);check(key not in xs,'dup');xs.add(key)
    check(len(xs)==(X['range'][1]-X['range'][0]+1)*len(X['mask_rates'])==seal['extended_case_count'],'extended case count')
    jobs=[(c,plan,tau) for c in res['cases']+res['extended_cases']]
    if workers<=1:outs=[audit_case(j) for j in jobs]
    else:
        with ProcessPoolExecutor(workers) as ex:outs=list(ex.map(audit_case,jobs,chunksize=1))
    n=len(res['cases']);fams={};ext={}
    for idx,(c,o) in enumerate(zip(res['cases']+res['extended_cases'],outs)):
        tgt=fams if idx<n else ext
        for arm,t in o.items():_add(tgt.setdefault(c['family'],{}).setdefault(arm,{}),t)
    _check_summary(res['summary'],fams,'main');_check_summary(res['extended_summary'],ext,'extended')
    return {'schema':'brute.independent-audit.v3_0','status':'passed','mismatches':0,'study':plan['study'],
            'source_results_sha256':seal['results_sha256'],'cases':len(seen),'extended_cases':len(xs),
            'arm_steps_replayed':sum(t['steps'] for a in list(fams.values())+list(ext.values()) for t in a.values()),
            'per_family':fams,'extended_per_family':ext,'tau':tau,'probability_tolerance':PROB_TOL,
            'scope':('full arms A3/P3: independent solver rebuilt <=4/<=5 supports for both actions, saturation, the Y1k union '
                     'for both actions, LU-R lookahead copies (A3) and window rows; every score and action, every decision '
                     'incl. RESYNC_AMBIGUOUS downgrades, public certificates, wrong flags, surprise/residual/alarm, '
                     'post-contradiction probabilities and forecast_source, issued lists and retraction reasons recomputed; '
                     'P3 checked against the frozen v0.1.1 control at every step. Slim arms (A2, P2, E2 and the extended '
                     'block): scores, actions, check flags, both decisions, wrong flags, issued/retraction lists, stale and '
                     'switch metrics recomputed; their alarm flag is read from the trace (no probabilities stored).')}


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--results-dir',default=str(STUDY_DIR));ap.add_argument('--write',action='store_true')
    ap.add_argument('--workers',type=int,default=4)
    a=ap.parse_args();rep=audit(a.results_dir,a.workers)
    if a.write:write_new(Path(a.results_dir)/'INDEPENDENT_AUDIT.json',rep)
    print(json.dumps({k:v for k,v in rep.items() if k not in ('per_family','extended_per_family')},indent=2))
