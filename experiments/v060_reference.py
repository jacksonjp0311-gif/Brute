"""Second implementation (same author, no `brute` import) for study BRUTE-060-DRIFTSOUND-008 (G11; also used by GX2'
(iv) for BR6/BC6).

Written from experiments/BRUTE_PLAN_008.json (arms R6/C6/BR6/BC6, rule_constants_frozen) and committed before any
v0.6.0 brute/ file existed. NOT an independent or third-party audit: same author, same machine.

The audits are the frozen v050_reference A5 / B5 audits (copied here; the frozen file is untouched) with exactly one
decision line replaced by the plan-008 rule and the drift-event bookkeeping added:

* event steps: a step u is an event if, after observing u, the residual (mean of the last W surprises rounded to 12 d.p.)
  is > tau * surprise_fraction (tau6/2 for 2x2, tau7/2 for breadth), or a window-tier event happened at u (2x2: the
  family contradiction or a window restart; breadth has no window tier, its family contradiction is counted instead -
  no certificate can follow a contradiction, so this choice cannot change a decision).  s* = last event step.
* R6 / BR6 (rule RO): at a prediction made after i observations, the rule is active iff s* exists and i - s* < W (=8).
  Active: the Y1k union is replaced by the RECENT union: an edge (j, b) of a row that has been traversed, but only by
  transitions ending at observations < s* (transition index t < s*-1; transition t goes from observation t to t+1), is
  AGED and opens every code at every fibre state; non-aged traversed edges give the successor's code set; untraversed
  edges keep the Y1k convention (open only at the current state). Certified iff the union is exactly {c}; otherwise
  ABSTAIN / RESYNC_AMBIGUOUS. Not active: plain Y1k (= A5).
* C6 / BC6 (rule CT): if the plain Y1k union is {c}: certified (as A5). Otherwise the pre-Y1k certificate c (the
  tracked-state projection with the v0.1.0 gates, i.e. the v0.2.0/A2 rule on the region) is KEPT iff no event has
  happened so far and i >= burn_in (8); otherwise ABSTAIN / RESYNC_AMBIGUOUS.
* then the SOLVER_BUDGET overlay as in A5. Each certificate-bearing forecast records cert_rule in
  {None, 'Y1k', 'Y1k-recent', 'tracked-calm', 'downgraded'} and the diagnostics record drift_events.
LU-R scores, alarm, resume, probabilities are unchanged from A5 / B5.
Report = COUNT of mismatching (case, arm) traces, plus a mutation test (20 traces, random.Random(20261026)).
"""
from __future__ import annotations
import argparse,json
from math import log,log2
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor
from experiments.brute_common import check,load,sha,VerificationError
from experiments.v90_independent_reference import ref_initial,ref_support,ref_observe,bit_compatible
from experiments.v011_independent_reference import RefSuffix1,ref_reason,expected_decision,_close
from experiments.v030_independent_reference import y1k_union,score,full,compatible_codes
from experiments.v040_reference import ref_world,_window_tier
from experiments.v050_reference import (_Alarm12,plan006_view,RefBudget,codes_of,k_initial,k_observe,k_support,
    k_saturated,k_y1k,k_score,k_volume,choose,k_reason,breadth_world,passive_actions,mutate)
from bgr89.worlds import actions
from bgr90.worlds import step as new_step

ROOT=Path(__file__).resolve().parents[1]
PLAN=ROOT/'experiments/BRUTE_PLAN_008.json'
STUDY_DIR=ROOT/'results/study-008'
DRIFT=(12,23,34)
ARMS_2X2_DRIFT=('R6','C6')
ARMS_BREADTH_DRIFT=('BR6','BC6')
RULE={'R6':'RO','BR6':'RO','C6':'CT','BC6':'CT'}
PLAN007=ROOT/'experiments/BRUTE_PLAN_007.json'


def plan_view(plan):
    """Plan 008 defines R6/C6/BR6/BC6 as subclasses of the frozen v0.5.0 learners on the frozen study-007 worlds and
    does not restate their configuration; the learner bounds, epsilon, row budget (160000, as in G11) and window tier
    are therefore read from the frozen BRUTE_PLAN_007, and every key that plan 008 does define overrides it."""
    v=dict(load(PLAN007));v.update(plan);v.update(plan['rule_constants_frozen'])
    check(v['row_budget_enumeration']==160000,'row budget');return v


def last_traversals(row,acts,k):
    """{(state, action): last transition index t} of the row's (unique, canonical, start 0) path under `acts`."""
    q=0;last={}
    for t,a in enumerate(acts):
        last[(q,a)]=t;q=row.paths[q*k+a];check(q>=0,'row path uses an untraversed edge')
    check(q==row.current,'row path does not end at the current state');return last


def recent_union(rows,b,codes,N,k,m,acts,t0):
    """RO union: aged traversed edges (all traversals at t < t0) open every code at every fibre state."""
    U=set();everything=frozenset(range(m))
    for r in rows:
        last=last_traversals(r,acts,k)
        for j,out in enumerate(r.outputs):
            if not (out&codes):continue
            d=r.paths[j*k+b]
            if d>=0:
                check((j,b) in last,'known edge never traversed')
                if last[(j,b)]<t0:return everything
                U|=r.outputs[d]
            elif j==r.current:
                for o in r.outputs:U|=o
                if len(r.outputs)<N:U|=set(range(m))
    return frozenset(U)


def _rule(arm,plain,recent,cert,s_,rs,events,i,rw,burn):
    if RULE[arm]=='RO':
        ss=events[-1] if events else None
        if ss is not None and i-ss<rw:U=recent(max(0,ss-1));path='Y1k-recent'
        else:U=plain();path='Y1k'
        if U==frozenset((cert,)):return s_,rs,cert,path
        return 'ABSTAIN','RESYNC_AMBIGUOUS',None,'downgraded'
    if plain()==frozenset((cert,)):return s_,rs,cert,'Y1k'
    if not events and i>=burn:return s_,rs,cert,'tracked-calm'
    return 'ABSTAIN','RESYNC_AMBIGUOUS',None,'downgraded'


def rule_2x2(arm,r4,b,codes,k4,cert,s_,rs,acts,events,i,rw,burn):
    return _rule(arm,lambda:y1k_union(r4,b,codes,k4),lambda t0:recent_union(r4,b,codes,k4,2,4,acts,t0),cert,s_,rs,events,i,rw,burn)


def rule_breadth(arm,r4,b,codes,N4,k,m,cert,s_,rs,acts,events,i,rw,burn):
    return _rule(arm,lambda:k_y1k(r4,b,codes,N4,k,m),lambda t0:recent_union(r4,b,codes,N4,k,m,acts,t0),cert,s_,rs,events,i,rw,burn)


# ------------------------------------------------------------------ audits (copied from v050_reference, rule replaced)
def audit_drift_2x2(c,arm,plan,tau6):
    """Full check of an R6 or C6 trace: the A5 audit of v050_reference (copied) with the Y1k line replaced by the
    plan-008 rule (rule_2x2) and the drift-event bookkeeping added."""
    p6=plan006_view(plan);fam=c['family'];seed=c['seed'];rate=c['mask_rate'];where=f'{fam} {seed} {rate} {arm}'
    k4=p6['family_state_cap'];k5=p6['margin_state_cap'];b4=b5=p6['row_budget_family']
    W_=plan['window_W'];eps=plan['open_world_reserve_epsilon'];wt=_window_tier();M=False;frac=plan['surprise_fraction'];rw=plan['recency_window'];burn=plan['burn_in']
    A=c['arms'][arm];trace=A['trace']
    truth=ref_world(seed,fam);hidden=truth.start;initial=truth.observed(hidden,rate,-1)
    check(list(initial)==c['initial_visible'],'initial '+where)
    attested=fam in plan['in_family_2x2'];check(c['attested']==attested,'attested flag '+where)
    r4=ref_initial(initial);s4='supported';r5=ref_initial(initial);s5='supported';last=initial
    win=None;restarts=0;suffix=RefSuffix1(0.7,initial);al=_Alarm12(tau6,W_,True)
    issued=[];retracted=None;acts=[];events=[];t={'steps':0,'certs':0,'cf_certs':0,'resumes':0,'unknown_forecasts':0}
    for i,pa in enumerate(actions(seed,plan['actions_per_case_2x2'])):
        rec=trace[i];step=i+1;alarm=al.on
        check(rec['step']==step and rec['passive_action']==pa,'step '+where)
        sc=[score(r4,s4,r5,s5,alarm,b,k4,k5,b4,b5,True) for b in (0,1)];e=rec['experiment']
        live=s4=='supported' and s5=='supported' and not alarm
        vol=[volume_2x2(r4,b,k4,b4) for b in (0,1)] if (M and live and sc[0]==sc[1]) else None
        if sc[0]!=sc[1]:a=0 if sc[0]>sc[1] else 1
        elif vol is not None and vol[0]!=vol[1]:a=0 if vol[0]<vol[1] else 1
        else:a=pa
        check(e['scores']==sc and e['score']==sc[a] and e['tied']==(sc[0]==sc[1]) and e['check'] is False,f'experiment {where} {i}')
        check(e['proposal']==('PROPOSED' if live else 'NO_PROPOSAL'),f'proposal {where} {i}')
        check(e.get('volumes')==vol and e.get('rule')==('M' if M else 'LU-R'),f'volumes {where} {i}')
        check(rec['action']==a,f'action {where} {i}')
        sat=all(len(m.outputs)==k4 for m in r4) if s4=='supported' else None
        nxt=[new_step(truth,hidden,b,i) if fam=='drift4' else truth.next(hidden,b) for b in (0,1)]
        act=[truth.emission(h) for h in nxt];dec={}
        for b,r in ((a,rec),(1-a,rec['counterfactual'])):
            sup=ref_support(r4,b,k4) if s4=='supported' else None
            msup=ref_support(r5,b,k5) if s5=='supported' else None
            unk=r['solver_unknown'];check(isinstance(unk,int) and unk>=0,'solver_unknown '+where);t['unknown_forecasts']+=unk>0
            if unk==0:
                check((list(sup) if sup is not None else None)==r['support'],f'support {where} {i} {b}')
                check((list(msup) if msup is not None else None)==r['margin_support'],f'margin {where} {i} {b}')
                check(sat==r['saturated'],f'saturation {where} {i}')
            else:  # conservative: recorded supports are supersets
                check(sup is None or set(sup)<=set(r['support'] or ()),f'unknown support superset {where} {i}')
            s_,rs,cert=expected_decision(s4,alarm,sup,s5,msup,sat)
            path=None
            if cert is not None:s_,rs,cert,path=rule_2x2(arm,r4,b,compatible_codes(last),k4,cert,s_,rs,acts,events,i,rw,burn)
            check(r['cert_rule']==path,f'cert_rule {where} {i} {b}')
            if unk>0 and s_!='OUT_OF_FAMILY':s_,rs,cert='ABSTAIN','SOLVER_BUDGET',None
            check((s_,rs,cert)==(r['status'],r['reason'],r['certificate']),f'decision {where} {i} {b}')
            pub=cert if (cert is not None and attested and not al.ever) else None
            check(pub==r['public_certificate'],f'public {where} {i} {b}')
            check(r['wrong']==(cert is not None and cert!=act[b]) and r['public_wrong']==(pub is not None and pub!=act[b]),'wrong flag '+where)
            probs=r['probabilities'];check(abs(sum(probs)-1)<1e-9 and min(probs)>=eps/4-1e-12,'probability floor '+where)
            if s4!='grammar_contradicted':check(r['forecast_source']=='v090','forecast_source '+where)
            else:
                if s5=='supported' and msup:q=[(1-eps)*(1/len(msup) if x in msup else 0.)+eps/4 for x in range(4)];src='margin_n5'
                else:
                    sx=suffix.predict(b);ws=ref_support(win,b,wt['state_cap']) if win else None
                    if ws:z=sum(sx[x] for x in ws);q=[(1-eps)*(sx[x]/z if x in ws else 0.)+eps/4 for x in range(4)];src='window_n4'
                    else:q=[(1-eps)*p+eps/4 for p in sx];src='suffix1'
                check(r['forecast_source']==src and _close(probs,q),f'fallback probabilities {where} {i} {b}');check(cert is None,'fallback certified')
            dec[b]=(cert,pub)
        check(rec['actual_emission_EVALUATOR_ONLY']==act[a] and rec['counterfactual_actual_EVALUATOR_ONLY']==act[1-a],'truth '+where)
        check(rec['drift_step']==(fam=='drift4' and step in DRIFT),'drift flag')
        hidden=nxt[a];obs=truth.observed(hidden,rate,i)
        check(rec['observed']==list(obs),'observation '+where)
        check(abs(rec['logloss']+log(max(1e-12,rec['probabilities'][act[a]])))<1e-8,'logloss '+where)
        check(abs(rec['min_probability']-min(min(rec['probabilities']),min(rec['counterfactual']['probabilities'])))<1e-12,'min prob')
        sup=ref_support(r4,a,k4) if s4=='supported' else None;v090=sup[0] if sup is not None and len(sup)==1 else None
        check(rec['v090_certificate']==v090 and rec['v090_wrong']==(v090 is not None and v090!=act[a]),'v0.90 control '+where)
        s=-log(sum(p for x,p in enumerate(rec['probabilities']) if bit_compatible(x,obs)))
        check(abs(s-rec['surprise'])<1e-8,f'surprise {where} {i}')
        cert=dec[a][0]
        if cert is not None and (step,cert) not in [(x[0],x[1]) for x in issued]:issued.append((step,cert,tuple(obs)))
        suffix.observe(a,obs);last=obs;was=s4;rs0=restarts;acts.append(a)
        if s4=='supported':r4,s4=ref_observe(r4,a,obs,k4,b4);r4=r4 or frozenset()
        if s5=='supported':r5,s5=ref_observe(r5,a,obs,k5,b5);r5=r5 or frozenset()
        if s4=='grammar_contradicted':
            if was=='supported':win=ref_initial(obs);restarts+=1;retracted=list(issued)
            else:
                w,ws=ref_observe(win,a,obs,wt['state_cap'],wt['row_budget'])
                if ws!='supported':win=ref_initial(obs);restarts+=1
                else:win=w
        R=al.push(step,rec['surprise'],s4,s5)
        if restarts>rs0 or (R is not None and R>tau6*frac):events.append(step)
        check((R is None and rec['residual_after'] is None) or (R is not None and abs(R-rec['residual_after'])<1e-8),f'residual {where} {i}')
        check(rec['alarm_after']==al.on,f'alarm {where} {i}')
        check(rec['family_status_after']==s4 and rec['margin_status_after']==s5,'status after '+where)
        check(rec['family_rows_after'] is None and rec['margin_rows_after'] is None and rec['window_rows_after'] is None,'rows fields must be null '+where)
        check(rec['window_status_after']==(None if win is None else 'supported'),'window '+where)
        t['steps']+=1;t['certs']+=cert is not None;t['cf_certs']+=dec[1-a][0] is not None
    check(A['issued']==[[s_,k] for s_,k,_ in issued],'issued '+where)
    acts={r['step']:r['actual_emission_EVALUATOR_ONLY'] for r in trace}
    exp=[{'step':s_,'certificate':k,'observed':list(o),'reason':ref_reason(k,o),'actual_EVALUATOR_ONLY':acts[s_],'wrong':k!=acts[s_]} for s_,k,o in (retracted or [])]
    check(A['retractions']==exp,'retractions '+where)
    d=A['diagnostics']
    check(d['drift_events']==events,'drift events '+where)
    check(d['window_restarts']==restarts and d['first_alarm_step']==al.first and d['alarm_steps']==al.sets and d['resume_steps']==al.resumes,'diagnostics '+where)
    check(d['certificates_issued']==len(issued) and d['certificates_retracted']==len(exp),'issued/retracted counts '+where)
    t['resumes']=len(al.resumes);return t


def audit_drift_breadth(c,arm,plan,tau7):
    """Check a BR6/BC6 trace (the B5 audit of v050_reference, copied, with the plan-008 rule) step by step until the
    enumeration exceeds its row budget.
    Returns counts incl. steps_checked and budget_stop (step index or None)."""
    fam=c['family'];seed=c['seed'];rate=c['mask_rate'];where=f'{fam} {seed} {rate} {arm}'
    lb=plan['breadth_worlds']['learner_bounds'][fam];N4=lb['family'];N5=lb['margin'];budget=plan['row_budget_enumeration']
    eps=plan['open_world_reserve_epsilon'];W_=plan['window_W'];steps=plan['actions_per_case_breadth']
    A=c['arms'][arm];trace=A['trace'];active=True;M=False;frac=plan['surprise_fraction'];rw=plan['recency_window'];burn=plan['burn_in']
    w=breadth_world(seed,fam);k=w.k;s=w.s;m=2**s
    check(c['k']==k and c['s']==s and c['attested']==lb['attested'],'case header '+where)
    hidden=w.start;initial=w.observed(hidden,rate,-1);check(list(initial)==c['initial_visible'],'initial '+where)
    tau=tau7
    al=_Alarm12(tau,W_,True);issued=[];retracted=None;acts=[];events=[]
    t={'steps':0,'steps_checked':0,'budget_stop':None,'certs':0,'unknown_forecasts':0}
    try:
        r4=k_initial(codes_of(initial,s),k);s4='supported';r5=k_initial(codes_of(initial,s),k);s5='supported';last=initial
    except RefBudget:t['budget_stop']=0;return t
    pas=passive_actions(seed,steps,k);check(len(trace)==steps,'trace length '+where)
    for i,pa in enumerate(pas):
        rec=trace[i];step=i+1;alarm=al.on
        try:
            check(rec['step']==step and rec['passive_action']==pa,'step '+where)
            live=s4=='supported' and s5=='supported' and not alarm
            if active:
                sc=[k_score(r4,s4,r5,s5,alarm,b,N4,N5,k,m,budget) for b in range(k)]
                tiedn=sum(x==max(sc) for x in sc)
                vol=[k_volume(r4,b,N4,k,m,budget) for b in range(k)] if (M and live and tiedn>1) else None
                a=choose(sc,pa,vol);e=rec['experiment']
                check(e['scores']==sc and e['score']==sc[a] and e['tied']==(tiedn>1) and e['volumes']==vol
                      and e['rule']==('M' if M else 'LU-R') and e['proposal']==('PROPOSED' if live else 'NO_PROPOSAL'),f'experiment {where} {i}')
            else:
                a=pa;check('experiment' not in rec,'passive experiment '+where)
            check(rec['action']==a,f'action {where} {i}')
            sat=k_saturated(r4,N4) if s4=='supported' else None
            nxt=[w.next(hidden,b) for b in range(k)];act=[w.emission(h) for h in nxt];fc=rec['forecasts'];check(len(fc)==k,'forecasts '+where)
            dec={}
            for b in range(k):
                r=fc[b];sup=k_support(r4,b,N4,k,m) if s4=='supported' else None
                msup=k_support(r5,b,N5,k,m) if s5=='supported' else None
                unk=r['solver_unknown'];check(isinstance(unk,int) and unk>=0,'solver_unknown '+where);t['unknown_forecasts']+=unk>0
                if unk==0:
                    check((list(sup) if sup is not None else None)==r['support'],f'support {where} {i} {b}')
                    check((list(msup) if msup is not None else None)==r['margin_support'],f'margin {where} {i} {b}')
                    check(sat==r['saturated'],f'saturation {where} {i}')
                else:check(sup is None or set(sup)<=set(r['support'] or ()),f'unknown support superset {where} {i}')
                s_,rs,cert=expected_decision(s4,alarm,sup,s5,msup,sat)
                path=None
                if cert is not None:s_,rs,cert,path=rule_breadth(arm,r4,b,codes_of(last,s),N4,k,m,cert,s_,rs,acts,events,i,rw,burn)
                check(r['cert_rule']==path,f'cert_rule {where} {i} {b}')
                if unk>0 and s_!='OUT_OF_FAMILY':s_,rs,cert='ABSTAIN','SOLVER_BUDGET',None
                check((s_,rs,cert)==(r['status'],r['reason'],r['certificate']),f'decision {where} {i} {b}')
                pub=cert if (cert is not None and lb['attested'] and not al.ever) else None
                check(pub==r['public_certificate'],f'public {where} {i} {b}')
                check(r['actual_EVALUATOR_ONLY']==act[b] and r['wrong']==(cert is not None and cert!=act[b]) and r['public_wrong']==(pub is not None and pub!=act[b]),'wrong flag '+where)
                if s4=='supported':S=set(r['support']) if unk else set(sup);src='family'
                elif s5=='supported' and msup:S=set(msup);src='margin'
                else:S=None;src='uniform'
                q=[1/m]*m if S is None else [(1-eps)*(1/len(S) if x in S else 0.)+eps/m for x in range(m)]
                probs=r['probabilities']
                check(r['forecast_source']==src and len(probs)==m and all(abs(x-y)<=1e-11 for x,y in zip(probs,q)),f'probabilities {where} {i} {b}')
                dec[b]=cert
            hidden=nxt[a];obs=w.observed(hidden,rate,i)
            check(rec['observed']==list(obs),'observation '+where)
            P=fc[a]['probabilities']
            check(abs(rec['logloss']+log(max(1e-12,P[act[a]])))<1e-8,'logloss '+where)
            check(abs(rec['min_probability']-min(min(f['probabilities']) for f in fc))<1e-12,'min prob '+where)
            cs=codes_of(obs,s);sp=-log(sum(P[x] for x in cs));check(abs(sp-rec['surprise'])<1e-8,f'surprise {where} {i}')
            cert=dec[a]
            if cert is not None and (step,cert) not in [(x[0],x[1]) for x in issued]:issued.append((step,cert,tuple(obs)))
            last=obs;was=s4;acts.append(a)
            if s4=='supported':r4,s4=k_observe(r4,a,cs,N4,k,budget)
            if s5=='supported':r5,s5=k_observe(r5,a,cs,N5,k,budget)
            if s4=='grammar_contradicted' and was=='supported':retracted=list(issued)
            R=al.push(step,rec['surprise'],s4,s5)
            if (s4=='grammar_contradicted' and was=='supported') or (R is not None and R>tau*frac):events.append(step)
            check((R is None and rec['residual_after'] is None) or (R is not None and abs(R-rec['residual_after'])<1e-8),f'residual {where} {i}')
            check(rec['alarm_after']==al.on,f'alarm {where} {i}')
            check(rec['family_status_after']==s4 and rec['margin_status_after']==s5,'status after '+where)
        except RefBudget:
            t['budget_stop']=i;t['steps']=len(trace);return t
        t['steps_checked']+=1;t['certs']+=cert is not None
    t['steps']=len(trace)
    check(A['issued']==[[s_,x] for s_,x,_ in issued],'issued '+where)
    acts={r['step']:r['forecasts'][r['action']]['actual_EVALUATOR_ONLY'] for r in trace}
    exp=[{'step':s_,'certificate':x,'observed':list(o),'reason':k_reason(x,o,s),'actual_EVALUATOR_ONLY':acts[s_],'wrong':x!=acts[s_]} for s_,x,o in (retracted or [])]
    check(A['retractions']==exp,'retractions '+where)
    d=A['diagnostics']
    check(t['budget_stop'] is not None or d['drift_events']==events,'drift events '+where)
    check(d['first_alarm_step']==al.first and d['alarm_steps']==al.sets and d['resume_steps']==al.resumes,'diagnostics '+where)
    check(d['certificates_issued']==len(issued) and d['certificates_retracted']==len(exp),'issued/retracted counts '+where)
    return t


# ------------------------------------------------------------------ count / mutate
def audit_trace(c,arm,plan,tau6,tau7):
    """(ok, message, counts). Never raises on a mismatch."""
    try:
        if arm in ARMS_2X2_DRIFT:t=audit_drift_2x2(c,arm,plan,tau6)
        elif arm in ARMS_BREADTH_DRIFT:t=audit_drift_breadth(c,arm,plan,tau7)
        else:return True,'not audited',None
        return True,None,t
    except (VerificationError,KeyError,IndexError,TypeError,ValueError,AssertionError) as exc:
        return False,f'{type(exc).__name__}: {exc}',None


def _job(x):
    i,c,plan,tau6,tau7,arms=x
    return i,{arm:audit_trace(c,arm,plan,tau6,tau7) for arm in arms if arm in c['arms']}


def count(cases,plan,tau6,tau7,arms=ARMS_2X2_DRIFT+ARMS_BREADTH_DRIFT,workers=4):
    jobs=[(i,c,plan,tau6,tau7,arms) for i,c in enumerate(cases)]
    if workers<=1:outs=[_job(j) for j in jobs]
    else:
        with ProcessPoolExecutor(workers) as ex:outs=list(ex.map(_job,jobs,chunksize=1))
    checked=0;bad=[];coverage={}
    for i,o in sorted(outs,key=lambda x:x[0]):
        for arm,(ok,msg,t) in o.items():
            if msg=='not audited':continue
            checked+=1
            if not ok:bad.append({'case':i,'family':cases[i]['family'],'seed':cases[i]['seed'],'mask_rate':cases[i]['mask_rate'],'arm':arm,'first_difference':msg})
            elif arm in ARMS_BREADTH_DRIFT:
                g=coverage.setdefault(f"{cases[i]['family']}/{arm}",{'steps':0,'steps_checked':0,'traces_budget_stopped':0})
                g['steps']+=t['steps'];g['steps_checked']+=t['steps_checked'];g['traces_budget_stopped']+=t['budget_stop'] is not None
    return checked,bad,coverage


def run(cases,plan,workers=4,mutate_k=0,arms=None,source_sha=None):
    check(plan==load(PLAN),'plan mismatch');tau6=plan['tau6']['value'];tau7=plan['tau7']['value']
    arms=arms or ARMS_2X2_DRIFT+ARMS_BREADTH_DRIFT
    view=plan_view(plan);checked,bad,cov=count(cases,view,tau6,tau7,arms,workers=workers)
    rep={'schema':'brute.second-implementation-count.v3','study':plan['study'],
         'wording':'second implementation by the same author, no brute import; not an independent or third-party audit',
         'arm_traces_checked':checked,'mismatching_arm_traces':len(bad),'mismatches':bad,'tau6':tau6,'tau7':tau7,
         'breadth_steps_checked':cov,'row_budget':view['row_budget_enumeration'],
         'granularity':'one count per (case, arm) trace; the first differing field inside a trace is recorded',
         'scope':'R6/C6 with the v050_reference A5 audit + plan-008 rule (2x2 enumeration); BR6/BC6 with the v050_reference '
                 'B5 audit + plan-008 rule up to the row budget','source_sha256':source_sha}
    if mutate_k:
        mc,inj=mutate(cases,mutate_k,rng_seed=20261026,arms=arms,max_step=8);_,mbad,_=count(mc,view,tau6,tau7,arms,workers=workers)
        flagged={(b['case'],b['arm']) for b in mbad};base={(b['case'],b['arm']) for b in bad}
        rep['mutation_test']={'injected':len(inj),'detected_injected':len(inj&flagged),'flagged_not_injected':len(flagged-inj-base),
                              'rng':'random.Random(20261026)','passed':inj<=flagged and not (flagged-inj-base)}
    return rep
