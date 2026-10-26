"""Second implementation (same author, no `brute` import) for study BRUTE-080-ALIGN-010 (G11).

Written from experiments/BRUTE_PLAN_010.json (arms J8, SP8, SC7, BSC7, BSP8; second_implementation) and committed
before any v0.8.0 brute/ file existed. NOT an independent or third-party audit: same author, same machine.

The audits are the frozen v070_reference S7/SC7 and BSC7 audits (copied here; the frozen file is untouched and still
imported for its helpers) with these plan-010 changes:

* J8 (rule RO, LU-R): the S7 decision, then the JUMP-HULL test. Rows after observations 0..T-1 (ref_observe), then a
  jump step in which every row moves to ANY target state < min(N, n_states_of_row + 1) whose output set meets the codes
  of observation T (paths unchanged; a new state gets unknown edges; current = target). With no action yet (T = 0) the
  hull rows are the current rows (there is no transition to remove). The certificate c is kept iff y1k_union over the
  hull rows (mask of observation T) == {c}: cert_rule = <S7 path> + '+hull'; else ABSTAIN / RESYNC_AMBIGUOUS with
  cert_rule 'hull-downgraded'. hull_union is audited at every step: {'0': [...], '1': [...]} when the family is
  supported before the forecast, else None; with hull_unknown > 0 the recorded union must be a superset.
* SP8 (rule CTR) / BSP8: the SC7 / BSC7 decision unchanged; the experiment scores are recomputed with LU-C: N(a,c)
  counts actions b whose post-(a,c) family support is a single code s, the post-(a,c) family is supported and not
  saturated, the post-(a,c) margin support for b equals s, and EITHER step t+1 is calm (no event u with (t+1)-u < W
  and t+1 >= burn_in, t = observations so far, events from the reference event list) OR y1k_union of the post-(a,c)
  rows for b with codes {c} == {s} (the LU-R condition). experiment.rule must be 'LU-C'.
* SC7, BSC7: the frozen v070 audits' logic unchanged (LU-R).
Report = COUNT of mismatching (case, arm) traces, plus a mutation test (20 traces, random.Random(20261026), >= 4 in J8
certificate/hull fields and >= 4 SP8 action choices).
"""
from __future__ import annotations
import copy,random
from fractions import Fraction
from math import log
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor
from experiments.brute_common import check,load,sha,VerificationError
from experiments.v90_independent_reference import ref_initial,ref_support,ref_observe,bit_compatible
from experiments.v011_independent_reference import RefSuffix1,ref_reason,expected_decision,_close
from experiments.v030_independent_reference import y1k_union,score,compatible_codes,full
from experiments.v040_reference import ref_world,_window_tier
from experiments.v050_reference import (_Alarm12,plan006_view,RefBudget,codes_of,k_initial,k_observe,k_support,
    k_saturated,k_y1k,k_score,choose,k_reason,breadth_world,passive_actions)
from experiments.v060_reference import recent_union
from bgr89.worlds import actions
from bgr90.worlds import step as new_step

ROOT=Path(__file__).resolve().parents[1]
PLAN=ROOT/'experiments/BRUTE_PLAN_010.json'
PLAN007=ROOT/'experiments/BRUTE_PLAN_007.json'
DRIFT=(12,23,34)
ARMS_2X2=('J8','SP8','SC7')
ARMS_BREADTH=('BSC7','BSP8')
RULE={'J8':'RO','SP8':'CTR','SC7':'CTR','BSC7':'CTR','BSP8':'CTR'}
POLICY={'J8':'LU-R','SP8':'LU-C','SC7':'LU-R','BSC7':'LU-R','BSP8':'LU-C'}


def plan_view(plan):
    """Plan 010 (as plan 009) inherits learner bounds, epsilon, row budget (160000) and window tier from the frozen BRUTE_PLAN_007;
    every key plan 010 defines overrides it."""
    v=dict(load(PLAN007));v.update(plan);v.update(plan['rule_constants_frozen'])
    v['actions_per_case_2x2']=plan['actions_per_case_2x2'];v['actions_per_case_breadth']=plan['actions_per_case_breadth']
    check(v['row_budget_enumeration']==160000,'row budget');return v


def _rule(rule,plain,recent,cert,s_,rs,events,i,rw,burn):
    ss=events[-1] if events else None
    if ss is not None and i-ss<rw:
        if recent(max(0,ss-1))==frozenset((cert,)):return s_,rs,cert,'Y1k-recent'
        return 'ABSTAIN','RESYNC_AMBIGUOUS',None,'downgraded'
    if plain()==frozenset((cert,)):return s_,rs,cert,'Y1k'
    if rule=='CTR' and i>=burn:return s_,rs,cert,'tracked-calm'
    return 'ABSTAIN','RESYNC_AMBIGUOUS',None,'downgraded'


# ------------------------------------------------------------------ plan-010 additions
def calm_after(events,i,rw,burn):
    """Step t+1 = i+1 is calm: no event u with (i+1) - u < W, and i+1 >= burn_in (events from the reference list)."""
    t1=i+1;ss=events[-1] if events else None
    return (ss is None or t1-ss>=rw) and t1>=burn


def score_c(r4,s4,r5,s5,alarm,a,k4,k5,b4,b5,calm):
    """LU-C on 2x2 (the v030 LU-R score with the Y1k condition waived when step t+1 is calm)."""
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
            if not calm and y1k_union(f,b,frozenset((c,)),k4)!=frozenset(s):continue
            if m is None:
                m,ms=ref_observe(r5,a,full(c),k5,b5)
                if ms!='supported':m=False
            if m is False:break
            tot+=ref_support(m,b,k5)==s
    return round(tot/len(S),12)


def k_score_c(r4,s4,r5,s5,alarm,a,N4,N5,k,m,budget,calm):
    """LU-C on breadth (the v050 k_score with the Y1k condition waived when step t+1 is calm)."""
    if s4!='supported' or s5!='supported' or alarm:return 0.
    S=k_support(r4,a,N4,k,m);tot=0
    for c in S:
        f,st=k_observe(r4,a,frozenset((c,)),N4,k,budget)
        if st!='supported' or k_saturated(f,N4):continue
        singles=[]
        for b in range(k):
            sb=k_support(f,b,N4,k,m)
            if len(sb)==1 and (calm or k_y1k(f,b,frozenset((c,)),N4,k,m)==frozenset(sb)):singles.append((b,sb))
        if not singles:continue
        g,gs=k_observe(r5,a,frozenset((c,)),N5,k,budget)
        if gs!='supported':continue
        tot+=sum(k_support(g,b,N5,k,m)==sb for b,sb in singles)
    return round(tot/len(S),12)


def jump_rows(rows,codes,N):
    """The JUMP step: every row moves to any target < min(N, n+1) whose output set meets `codes` (paths unchanged)."""
    new=set()
    for r in rows:
        n=len(r.outputs)
        for tg in range(min(N,n+1)):
            if tg==n:outs=r.outputs+(frozenset(codes),);paths=tuple(r.paths)+(-1,-1)
            else:
                v=r.outputs[tg]&codes
                if not v:continue
                outs=r.outputs[:tg]+(v,)+r.outputs[tg+1:];paths=tuple(r.paths)
            new.add(type(r)(paths,outs,tg))
    return frozenset(new)


def hull_unions(prev,cur,i,codes,k4):
    """{b: y1k_union over the hull rows} for b in (0, 1); hull rows = cur when i == 0, else jump_rows(prev)."""
    H=cur if i==0 else jump_rows(prev,codes,k4)
    return {b:y1k_union(H,b,codes,k4) for b in (0,1)}


# ------------------------------------------------------------------ planning objective from recorded counts
def e1(counts):
    N=sum(counts);return None if N==0 else Fraction(sum(n*n for n in counts),N)


def plan_choice(P,a_lur):
    """Recompute the planned action from the recorded counts. Returns (action, E1 list, E2 list or None)."""
    C=P['counts'];E1=[e1(C[a]) for a in (0,1)];check(all(x is not None for x in E1),'planned decision with N_a = 0')
    E2=None
    if P.get('counts2') is not None:
        E2=[]
        for a in (0,1):
            N=sum(C[a]);tot=Fraction(0)
            for c in range(len(C[a])):
                if C[a][c]==0:continue
                br=P['counts2'][f'{a},{c}'];vals=[e1(br[b]) for b in (0,1)];vals=[v for v in vals if v is not None]
                check(vals,'branch without pairs');tot+=Fraction(C[a][c],N)*min(vals)
            E2.append(tot)
        if E2[0]!=E2[1]:return (0 if E2[0]<E2[1] else 1),E1,E2
        if E1[0]!=E1[1]:return (0 if E1[0]<E1[1] else 1),E1,E2
        return a_lur,E1,E2
    if E1[0]!=E1[1]:return (0 if E1[0]<E1[1] else 1),E1,None
    return a_lur,E1,None


def _fr(x):return None if x is None else f'{x.numerator}/{x.denominator}'


# ------------------------------------------------------------------ 2x2 audit (J8, SP8, SC7)
def audit_2x2(c,arm,plan,tau6):
    p6=plan006_view(plan);fam=c['family'];seed=c['seed'];rate=c['mask_rate'];where=f'{fam} {seed} {rate} {arm}'
    k4=p6['family_state_cap'];k5=p6['margin_state_cap'];b4=b5=p6['row_budget_family'];rule=RULE[arm]
    W_=plan['window_W'];eps=plan['open_world_reserve_epsilon'];wt=_window_tier();frac=plan['surprise_fraction'];rw=plan['recency_window'];burn=plan['burn_in']
    A=c['arms'][arm];trace=A['trace']
    truth=ref_world(seed,fam);hidden=truth.start;initial=truth.observed(hidden,rate,-1)
    check(list(initial)==c['initial_visible'],'initial '+where)
    attested=fam in plan['in_family_2x2'];check(c['attested']==attested,'attested flag '+where)
    r4=ref_initial(initial);s4='supported';r5=ref_initial(initial);s5='supported';last=initial
    win=None;restarts=0;suffix=RefSuffix1(0.7,initial);al=_Alarm12(tau6,W_,True)
    issued=[];retracted=None;acts=[];events=[];trig=[];prev=None;pol=POLICY[arm]
    t={'steps':0,'certs':0,'cf_certs':0,'resumes':0,'unknown_forecasts':0,'applicable':0,'planned':0,'hull_steps':0,'hull_downgrades':0}
    for i,pa in enumerate(actions(seed,plan['actions_per_case_2x2'])):
        rec=trace[i];step=i+1;alarm=al.on
        check(rec['step']==step and rec['passive_action']==pa,'step '+where)
        if pol=='LU-C':calm=calm_after(events,i,rw,burn);sc=[score_c(r4,s4,r5,s5,alarm,b,k4,k5,b4,b5,calm) for b in (0,1)]
        else:sc=[score(r4,s4,r5,s5,alarm,b,k4,k5,b4,b5,True) for b in (0,1)]
        e=rec['experiment']
        live=s4=='supported' and s5=='supported' and not alarm
        a_l=(0 if sc[0]>sc[1] else 1) if sc[0]!=sc[1] else pa
        check(e['scores']==sc and e['tied']==(sc[0]==sc[1]) and e['check'] is False,f'experiment {where} {i}')
        check(e['proposal']==('PROPOSED' if live else 'NO_PROPOSAL'),f'proposal {where} {i}')
        check(e.get('volumes') is None and e.get('rule')==pol,f'volumes/rule {where} {i}')
        if rule=='A5':
            P=rec['planner'];app=live and i>=burn
            check(e['lur_action']==a_l,f'LU-R action {where} {i}')
            if not app:check(P is None,f'planner on a non-applicable step {where} {i}');a=a_l
            else:
                t['applicable']+=1;check(P is not None and P['lur_action']==a_l,f'planner record {where} {i}')
                if P['planned']:
                    a,E1,E2=plan_choice(P,a_l);t['planned']+=1
                    check(P['E1']==[_fr(x) for x in E1] and P['E2']==([_fr(x) for x in E2] if E2 else None),f'objective {where} {i}')
                    check(P['choice']==a,f'planner choice {where} {i}')
                else:check(P['fallback_reason'] and P['choice']==a_l,f'fallback {where} {i}');a=a_l
            check(e['score']==sc[a],f'score {where} {i}')
        else:
            a=a_l;check(e['score']==sc[a],f'score {where} {i}')
        check(rec['action']==a,f'action {where} {i}')
        sat=all(len(m.outputs)==k4 for m in r4) if s4=='supported' else None
        nxt=[new_step(truth,hidden,b,i) if fam=='drift4' else truth.next(hidden,b) for b in (0,1)]
        act=[truth.emission(h) for h in nxt];dec={};H=None
        if arm=='J8':
            if s4=='supported':
                H=hull_unions(prev,r4,i,compatible_codes(last),k4);hu=rec['hull_unknown'];check(isinstance(hu,int) and hu>=0,'hull_unknown '+where)
                ru=rec['hull_union'];check(set(ru)=={'0','1'},'hull_union keys '+where);t['hull_steps']+=1
                for b in (0,1):
                    if hu==0:check(ru[str(b)]==sorted(H[b]),f'hull_union {where} {i} {b}')
                    else:check(ru[str(b)] is None or set(H[b])<=set(ru[str(b)]),f'hull_union superset {where} {i} {b}')
            else:check(rec['hull_union'] is None and rec['hull_unknown']==0,'hull_union when unsupported '+where)
        for b,r in ((a,rec),(1-a,rec['counterfactual'])):
            sup=ref_support(r4,b,k4) if s4=='supported' else None
            msup=ref_support(r5,b,k5) if s5=='supported' else None
            unk=r['solver_unknown'];check(isinstance(unk,int) and unk>=0,'solver_unknown '+where);t['unknown_forecasts']+=unk>0
            if unk==0:
                check((list(sup) if sup is not None else None)==r['support'],f'support {where} {i} {b}')
                check((list(msup) if msup is not None else None)==r['margin_support'],f'margin {where} {i} {b}')
                check(sat==r['saturated'],f'saturation {where} {i}')
            else:check(sup is None or set(sup)<=set(r['support'] or ()),f'unknown support superset {where} {i}')
            s_,rs,cert=expected_decision(s4,alarm,sup,s5,msup,sat);path=None
            if rule=='A5':
                if cert is not None and y1k_union(r4,b,compatible_codes(last),k4)!=frozenset((cert,)):s_,rs,cert='ABSTAIN','RESYNC_AMBIGUOUS',None
            else:
                if cert is not None:
                    s_,rs,cert,path=_rule(rule,lambda:y1k_union(r4,b,compatible_codes(last),k4),
                                          lambda t0:recent_union(r4,b,compatible_codes(last),k4,2,4,acts,t0),cert,s_,rs,events,i,rw,burn)
                    if arm=='J8' and cert is not None:
                        if H[b]==frozenset((cert,)):path=path+'+hull'
                        else:s_,rs,cert,path='ABSTAIN','RESYNC_AMBIGUOUS',None,'hull-downgraded';t['hull_downgrades']+=1
                check(unk>0 or r['cert_rule']==path,f'cert_rule {where} {i} {b}')
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
        prev=r4
        if s4=='supported':r4,s4=ref_observe(r4,a,obs,k4,b4);r4=r4 or frozenset()
        if s5=='supported':r5,s5=ref_observe(r5,a,obs,k5,b5);r5=r5 or frozenset()
        if s4=='grammar_contradicted':
            if was=='supported':win=ref_initial(obs);restarts+=1;retracted=list(issued)
            else:
                w,ws=ref_observe(win,a,obs,wt['state_cap'],wt['row_budget'])
                if ws!='supported':win=ref_initial(obs);restarts+=1
                else:win=w
        R=al.push(step,rec['surprise'],s4,s5)
        if rule!='A5':
            f=[]
            if restarts>rs0 or (R is not None and R>tau6*frac):f.append('E1')
            if cert is not None and not bit_compatible(cert,obs):f.append('E2')
            if s>tau6:f.append('E3')
            if f:events.append(step);trig.append([step,f])
        check((R is None and rec['residual_after'] is None) or (R is not None and abs(R-rec['residual_after'])<1e-8),f'residual {where} {i}')
        check(rec['alarm_after']==al.on,f'alarm {where} {i}')
        check(rec['family_status_after']==s4 and rec['margin_status_after']==s5,'status after '+where)
        check(rec['family_rows_after'] is None and rec['margin_rows_after'] is None and rec['window_rows_after'] is None,'rows fields must be null '+where)
        check(rec['window_status_after']==(None if win is None else 'supported'),'window '+where)
        t['steps']+=1;t['certs']+=cert is not None;t['cf_certs']+=dec[1-a][0] is not None
    check(A['issued']==[[s_,k] for s_,k,_ in issued],'issued '+where)
    actsE={r['step']:r['actual_emission_EVALUATOR_ONLY'] for r in trace}
    exp=[{'step':s_,'certificate':k,'observed':list(o),'reason':ref_reason(k,o),'actual_EVALUATOR_ONLY':actsE[s_],'wrong':k!=actsE[s_]} for s_,k,o in (retracted or [])]
    check(A['retractions']==exp,'retractions '+where)
    d=A['diagnostics']
    if rule!='A5':check(d['drift_events']==events and d['event_triggers']==trig,'events '+where)
    check(d['window_restarts']==restarts and d['first_alarm_step']==al.first and d['alarm_steps']==al.sets and d['resume_steps']==al.resumes,'diagnostics '+where)
    check(d['certificates_issued']==len(issued) and d['certificates_retracted']==len(exp),'issued/retracted counts '+where)
    t['resumes']=len(al.resumes);return t


# ------------------------------------------------------------------ breadth audit (BSC7, BSP8)
def audit_breadth(c,arm,plan,tau7):
    """Step-by-step check of a BSC7/BSP8 trace until the enumeration exceeds its row budget."""
    fam=c['family'];seed=c['seed'];rate=c['mask_rate'];where=f'{fam} {seed} {rate} {arm}';rule=RULE[arm]
    lb=plan['breadth_worlds']['learner_bounds'][fam];N4=lb['family'];N5=lb['margin'];budget=plan['row_budget_enumeration']
    eps=plan['open_world_reserve_epsilon'];W_=plan['window_W'];steps=plan['actions_per_case_breadth']
    A=c['arms'][arm];trace=A['trace'];frac=plan['surprise_fraction'];rw=plan['recency_window'];burn=plan['burn_in']
    w=breadth_world(seed,fam);k=w.k;s=w.s;m=2**s
    check(c['k']==k and c['s']==s and c['attested']==lb['attested'],'case header '+where)
    hidden=w.start;initial=w.observed(hidden,rate,-1);check(list(initial)==c['initial_visible'],'initial '+where)
    tau=tau7;al=_Alarm12(tau,W_,True);issued=[];retracted=None;acts=[];events=[];trig=[]
    t={'steps':0,'steps_checked':0,'budget_stop':None,'certs':0,'unknown_forecasts':0}
    try:
        r4=k_initial(codes_of(initial,s),k);s4='supported';r5=k_initial(codes_of(initial,s),k);s5='supported';last=initial
    except RefBudget:t['budget_stop']=0;t['steps']=len(trace);return t
    pas=passive_actions(seed,steps,k);check(len(trace)==steps,'trace length '+where)
    for i,pa in enumerate(pas):
        rec=trace[i];step=i+1;alarm=al.on
        try:
            check(rec['step']==step and rec['passive_action']==pa,'step '+where)
            live=s4=='supported' and s5=='supported' and not alarm
            if POLICY[arm]=='LU-C':calm=calm_after(events,i,rw,burn);sc=[k_score_c(r4,s4,r5,s5,alarm,b,N4,N5,k,m,budget,calm) for b in range(k)]
            else:sc=[k_score(r4,s4,r5,s5,alarm,b,N4,N5,k,m,budget) for b in range(k)]
            tiedn=sum(x==max(sc) for x in sc)
            a=choose(sc,pa,None);e=rec['experiment']
            check(e['scores']==sc and e['score']==sc[a] and e['tied']==(tiedn>1) and e['volumes'] is None
                  and e['rule']==POLICY[arm] and e['proposal']==('PROPOSED' if live else 'NO_PROPOSAL'),f'experiment {where} {i}')
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
                s_,rs,cert=expected_decision(s4,alarm,sup,s5,msup,sat);path=None
                if cert is not None:
                    s_,rs,cert,path=_rule(rule,lambda:k_y1k(r4,b,codes_of(last,s),N4,k,m),
                                          lambda t0:recent_union(r4,b,codes_of(last,s),N4,k,m,acts,t0),cert,s_,rs,events,i,rw,burn)
                check(unk>0 or r['cert_rule']==path,f'cert_rule {where} {i} {b}')
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
            R=al.push(step,rec['surprise'],s4,s5);f=[]
            if (s4=='grammar_contradicted' and was=='supported') or (R is not None and R>tau*frac):f.append('E1')
            if cert is not None and cert not in cs:f.append('E2')
            if sp>tau:f.append('E3')
            if f:events.append(step);trig.append([step,f])
            check((R is None and rec['residual_after'] is None) or (R is not None and abs(R-rec['residual_after'])<1e-8),f'residual {where} {i}')
            check(rec['alarm_after']==al.on,f'alarm {where} {i}')
            check(rec['family_status_after']==s4 and rec['margin_status_after']==s5,'status after '+where)
        except RefBudget:
            t['budget_stop']=i;t['steps']=len(trace);return t
        t['steps_checked']+=1;t['certs']+=cert is not None
    t['steps']=len(trace)
    check(A['issued']==[[s_,x] for s_,x,_ in issued],'issued '+where)
    actsE={r['step']:r['forecasts'][r['action']]['actual_EVALUATOR_ONLY'] for r in trace}
    exp=[{'step':s_,'certificate':x,'observed':list(o),'reason':k_reason(x,o,s),'actual_EVALUATOR_ONLY':actsE[s_],'wrong':x!=actsE[s_]} for s_,x,o in (retracted or [])]
    check(A['retractions']==exp,'retractions '+where)
    d=A['diagnostics']
    check(d['drift_events']==events and d['event_triggers']==trig,'events '+where)
    check(d['first_alarm_step']==al.first and d['alarm_steps']==al.sets and d['resume_steps']==al.resumes,'diagnostics '+where)
    check(d['certificates_issued']==len(issued) and d['certificates_retracted']==len(exp),'issued/retracted counts '+where)
    return t


# ------------------------------------------------------------------ count / mutate
def audit_trace(c,arm,plan,tau6,tau7):
    """(ok, message, counts). Never raises on a mismatch."""
    try:
        if arm in ARMS_2X2:t=audit_2x2(c,arm,plan,tau6)
        elif arm in ARMS_BREADTH:t=audit_breadth(c,arm,plan,tau7)
        else:return True,'not audited',None
        return True,None,t
    except (VerificationError,KeyError,IndexError,TypeError,ValueError,AssertionError,ZeroDivisionError) as exc:
        return False,f'{type(exc).__name__}: {exc}',None


def _job(x):
    i,c,plan,tau6,tau7,arms=x
    return i,{arm:audit_trace(c,arm,plan,tau6,tau7) for arm in arms if arm in c['arms']}


def count(cases,plan,tau6,tau7,arms=ARMS_2X2+ARMS_BREADTH,workers=4):
    jobs=[(i,c,plan,tau6,tau7,arms) for i,c in enumerate(cases)]
    if workers<=1:outs=[_job(j) for j in jobs]
    else:
        with ProcessPoolExecutor(workers) as ex:outs=list(ex.map(_job,jobs,chunksize=1))
    checked=0;bad=[];coverage={};plan_stats={'applicable':0,'planned':0}
    for i,o in sorted(outs,key=lambda x:x[0]):
        for arm,(ok,msg,t) in o.items():
            if msg=='not audited':continue
            checked+=1
            if not ok:bad.append({'case':i,'family':cases[i]['family'],'seed':cases[i]['seed'],'mask_rate':cases[i]['mask_rate'],'arm':arm,'first_difference':msg})
            elif arm in ARMS_BREADTH:
                g=coverage.setdefault(f"{cases[i]['family']}/{arm}",{'steps':0,'steps_checked':0,'traces_budget_stopped':0})
                g['steps']+=t['steps'];g['steps_checked']+=t['steps_checked'];g['traces_budget_stopped']+=t['budget_stop'] is not None
            elif arm=='P7':plan_stats['applicable']+=t['applicable'];plan_stats['planned']+=t['planned']
    return checked,bad,coverage,plan_stats


MUTATIONS=('certificate','status','logloss','action')


def _flip_hull(rec,rng):
    """Toggle one code in the recorded hull_union of one action (a single-field error)."""
    b=str(rng.randrange(2));u=set(rec['hull_union'][b]);c=rng.randrange(4)
    u.symmetric_difference_update({c})
    if u==set(rec['hull_union'][b]):u.add((c+1)%4)
    rec['hull_union'][b]=sorted(u)


def mutate(cases,k,rng_seed=20261026,arms=ARMS_2X2+ARMS_BREADTH,max_step=8,j8=4,sp8=4):
    """Inject one single-field error into k distinct (case, arm) traces: the first `j8` go to J8 traces (alternately a
    toggled code in hull_union at a supported step, and a changed certificate), the next `sp8` flip the recorded action
    of an SP8 step (SP8 action choice), the rest are the v070 kinds. Returns (cases, keys)."""
    rng=random.Random(rng_seed);cases=copy.deepcopy(cases);inj=[]
    pj=[(i,'J8') for i,c in enumerate(cases) if 'J8' in c['arms'] and 'J8' in arms]
    ps=[(i,'SP8') for i,c in enumerate(cases) if 'SP8' in c['arms'] and 'SP8' in arms]
    rng.shuffle(pj);rng.shuffle(ps)
    for n,(i,a) in enumerate(pj[:j8]):
        tr=cases[i]['arms'][a]['trace']
        if n%2==0:
            st=[r for r in tr if r.get('hull_union') is not None]
            if st:_flip_hull(rng.choice(st),rng);inj.append((i,a));continue
        rec=tr[rng.randrange(min(len(tr),max_step))]
        rec['certificate']=(rec['certificate']+1)%4 if rec['certificate'] is not None else 0;inj.append((i,a))
    for i,a in ps[:sp8]:
        tr=cases[i]['arms'][a]['trace'];rec=tr[rng.randrange(min(len(tr),max_step))];rec['action']=1-rec['action'];inj.append((i,a))
    keys=[(i,a) for i,c in enumerate(cases) for a in arms if a in c['arms'] and (i,a) not in inj];rng.shuffle(keys)
    for n,(i,a) in enumerate(keys[:k-len(inj)]):
        tr=cases[i]['arms'][a]['trace'];rec=tr[rng.randrange(min(len(tr),max_step or len(tr)))];kind=MUTATIONS[n%len(MUTATIONS)]
        r=rec['forecasts'][rec['action']] if 'forecasts' in rec else rec
        if kind=='certificate':r['certificate']=(r['certificate']+1)%len(r['probabilities']) if r['certificate'] is not None else 0
        elif kind=='status':r['status']='CERTIFIED' if r['status']!='CERTIFIED' else 'ABSTAIN'
        elif kind=='logloss':rec['logloss']=rec['logloss']+1e-6
        else:rec['action']=(rec['action']+1)%len(rec['forecasts']) if 'forecasts' in rec else 1-rec['action']
        inj.append((i,a))
    return cases,set(inj)


def run(cases,plan,workers=4,mutate_k=0,arms=None,source_sha=None):
    check(plan==load(PLAN),'plan mismatch');tau6=plan['tau6']['value'];tau7=plan['tau7']['value']
    arms=arms or ARMS_2X2+ARMS_BREADTH
    view=plan_view(plan);checked,bad,cov,ps=count(cases,view,tau6,tau7,arms,workers=workers)
    rep={'schema':'brute.second-implementation-count.v5','study':plan['study'],
         'wording':'second implementation by the same author, no brute import; not an independent or third-party audit',
         'arm_traces_checked':checked,'mismatching_arm_traces':len(bad),'mismatches':bad,'tau6':tau6,'tau7':tau7,
         'breadth_steps_checked':cov,'planning':ps,'row_budget':view['row_budget_enumeration'],
         'granularity':'one count per (case, arm) trace; the first differing field inside a trace is recorded',
         'scope':'J8 (S7 audit + jump-row hull), SP8 (SC7 audit + LU-C scores), SC7 (v070 audit); BSC7/BSP8 (breadth '
                 'enumeration up to the row budget, BSP8 with LU-C)','source_sha256':source_sha}
    if mutate_k:
        mc,inj=mutate(cases,mutate_k,arms=arms);_,mbad,_,_=count(mc,view,tau6,tau7,arms,workers=workers)
        flagged={(b['case'],b['arm']) for b in mbad};base={(b['case'],b['arm']) for b in bad}
        rep['mutation_test']={'injected':len(inj),'injected_j8':sum(a=='J8' for _,a in inj),'injected_sp8':sum(a=='SP8' for _,a in inj),'detected_injected':len(inj&flagged),
                              'flagged_not_injected':len(flagged-inj-base),'rng':'random.Random(20261026)','passed':inj<=flagged and not (flagged-inj-base)}
    return rep
