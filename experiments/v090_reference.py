"""Second implementation (same author, no `brute` import) for study BRUTE-090-WINDOW-011 (G11, GLV).

Written from experiments/BRUTE_PLAN_011.json (arms J9, SP8; second_implementation, jump_window_definition) and
committed before brute/jumpwindow.py existed. NOT an independent or third-party audit: same author, same machine.

* SP8: the frozen experiments/v080_reference.audit_2x2(c, 'SP8', ...) imported unchanged.
* J9: a copy of that SP8 audit path (rule CTR, LU-C scores, every other field as SP8) plus the WINDOW-HULL test by
  row enumeration (a different encoding from the SAT selector encoding of brute/jumpwindow.py):
  with T = observations so far (= loop index i) and J(T) = {max(1, T-K+1), ..., T-1}, the hull rows are the current
  no-jump rows UNION, for every t in J(T), jump_rows(rows after observations 0..t-1, codes of observation t)
  (v080_reference.jump_rows: any target state < min(N, n+1) whose output set meets the codes; paths unchanged)
  followed by ref_observe of observations t+1..T with their actions. A branch that is contradicted contributes no
  row; a branch that exceeds the frozen row budget makes the step UNAUDITABLE (hull fields accepted as recorded,
  decisions then follow the recorded hull; counted in hull_unauditable). A kept SP8 certificate c survives iff
  y1k_union(hull rows, b, codes of observation T) == {c}: cert_rule <SP8 path> + '+whull'; else ABSTAIN /
  RESYNC_AMBIGUOUS, cert_rule 'whull-downgraded'. hull_union is audited at every step: {'0': [...], '1': [...]}
  while the family is supported before the forecast, else None; with hull_unknown > 0 the recorded union must be a
  superset.
Report = COUNT of mismatching (case, arm) traces, plus a mutation test (20 traces, random.Random(20261026), >= 4 in
J9 certificate/hull fields and >= 4 SP8/J9 action choices).
"""
from __future__ import annotations
import copy,random
from math import log
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor
from experiments.brute_common import check,load,VerificationError
from experiments.v90_independent_reference import ref_initial,ref_support,ref_observe,bit_compatible
from experiments.v011_independent_reference import RefSuffix1,ref_reason,expected_decision,_close
from experiments.v030_independent_reference import y1k_union,score,compatible_codes,full
from experiments.v040_reference import ref_world,_window_tier
from experiments.v050_reference import _Alarm12,plan006_view
from experiments.v060_reference import recent_union
from experiments.v080_reference import (audit_2x2 as audit_2x2_080,_rule,calm_after,score_c,jump_rows,plan_choice,_fr,
    _flip_hull,MUTATIONS)
from bgr89.worlds import actions
from bgr90.worlds import step as new_step

ROOT=Path(__file__).resolve().parents[1]
PLAN=ROOT/'experiments/BRUTE_PLAN_011.json'
PLAN007=ROOT/'experiments/BRUTE_PLAN_007.json'
DRIFT=(12,23,34)
ARMS_2X2=('J9','SP8')


def plan_view(plan):
    """Plan 011 (as plans 009/010) inherits learner bounds, epsilon, row budget (160000) and window tier from the
    frozen BRUTE_PLAN_007; every key plan 011 defines overrides it."""
    v=dict(load(PLAN007));v.update(plan);v.update(plan['rule_constants_frozen'])
    v['actions_per_case_2x2']=plan['actions_per_case_2x2']
    check(v['row_budget_enumeration']==160000,'row budget');check(v['jump_window_K']==4,'K');return v


def window_positions(T,K):
    """J(T) = {max(1, T-K+1), ..., T-1}: observations whose incoming transition may be a free jump."""
    return list(range(max(1,T-K+1),T))


def window_rows(hist,obsl,acts,T,k4,b4,K):
    """(rows, ok): the no-jump rows hist[T] UNION every jump branch; ok False iff a branch hit the row budget."""
    H=set(hist[T]);ok=True
    for t in window_positions(T,K):
        rows=jump_rows(hist[t-1],compatible_codes(obsl[t]),k4)
        for u in range(t+1,T+1):
            if not rows:break
            rows,st=ref_observe(rows,acts[u-1],obsl[u],k4,b4)
            if st=='budget_exhausted':ok=False;rows=None;break
            if st!='supported':rows=None;break
        if rows:H|=set(rows)
    return frozenset(H),ok


def window_hull(hist,obsl,acts,T,k4,b4,K):
    """({b: y1k_union(window rows, b, codes of observation T)}, ok)."""
    H,ok=window_rows(hist,obsl,acts,T,k4,b4,K);codes=compatible_codes(obsl[T])
    return {b:y1k_union(H,b,codes,k4) for b in (0,1)},ok


# ------------------------------------------------------------------ J9 audit (copy of the v080 SP8 path + window hull)
def audit_j9(c,plan,tau6,K):
    arm='J9'
    p6=plan006_view(plan);fam=c['family'];seed=c['seed'];rate=c['mask_rate'];where=f'{fam} {seed} {rate} {arm}'
    k4=p6['family_state_cap'];k5=p6['margin_state_cap'];b4=b5=p6['row_budget_family'];rule='CTR'
    W_=plan['window_W'];eps=plan['open_world_reserve_epsilon'];wt=_window_tier();frac=plan['surprise_fraction'];rw=plan['recency_window'];burn=plan['burn_in']
    A=c['arms'][arm];trace=A['trace']
    truth=ref_world(seed,fam);hidden=truth.start;initial=truth.observed(hidden,rate,-1)
    check(list(initial)==c['initial_visible'],'initial '+where)
    attested=fam in plan['in_family_2x2'];check(c['attested']==attested,'attested flag '+where)
    r4=ref_initial(initial);s4='supported';r5=ref_initial(initial);s5='supported';last=initial
    win=None;restarts=0;suffix=RefSuffix1(0.7,initial);al=_Alarm12(tau6,W_,True)
    issued=[];retracted=None;acts=[];events=[];trig=[];prev=None;pol='LU-C';hist=[r4];obsl=[tuple(initial)];K_=K
    t={'steps':0,'certs':0,'cf_certs':0,'resumes':0,'unknown_forecasts':0,'applicable':0,'planned':0,'hull_steps':0,'hull_downgrades':0,'hull_unauditable':0,'hull_nonvacuous':0}
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
        if s4=='supported':
            H,ok=window_hull(hist,obsl,acts,i,k4,b4,K_);hu=rec['hull_unknown'];check(isinstance(hu,int) and hu>=0,'hull_unknown '+where)
            ru=rec['hull_union'];check(isinstance(ru,dict) and set(ru)=={'0','1'},'hull_union keys '+where);t['hull_steps']+=1
            if not ok:
                t['hull_unauditable']+=1;H={b:frozenset(ru[str(b)]) if ru[str(b)] is not None else frozenset(range(4)) for b in (0,1)}
            for b in (0,1):
                if hu==0:check(ru[str(b)]==sorted(H[b]),f'hull_union {where} {i} {b}')
                else:check(ru[str(b)] is None or set(H[b])<=set(ru[str(b)]),f'hull_union superset {where} {i} {b}')
            t['hull_nonvacuous']+=any(len(H[b])<4 for b in (0,1))
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
                    if cert is not None:
                        if H[b]==frozenset((cert,)):path=path+'+whull'
                        else:s_,rs,cert,path='ABSTAIN','RESYNC_AMBIGUOUS',None,'whull-downgraded';t['hull_downgrades']+=1
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
        hist.append(r4);obsl.append(tuple(obs))
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


# ------------------------------------------------------------------ count / mutate
def audit_trace(c,arm,plan,tau6):
    """(ok, message, counts). Never raises on a mismatch."""
    try:
        if arm=='J9':t=audit_j9(c,plan,tau6,plan['jump_window_K'])
        elif arm=='SP8':t=audit_2x2_080(c,'SP8',plan,tau6)
        else:return True,'not audited',None
        return True,None,t
    except (VerificationError,KeyError,IndexError,TypeError,ValueError,AssertionError,ZeroDivisionError) as exc:
        return False,f'{type(exc).__name__}: {exc}',None


def _job(x):
    i,c,plan,tau6,arms=x
    return i,{arm:audit_trace(c,arm,plan,tau6) for arm in arms if arm in c['arms']}


def count(cases,plan,tau6,arms=ARMS_2X2,workers=4,on_result=None):
    jobs=[(i,c,plan,tau6,arms) for i,c in enumerate(cases)]
    if workers<=1:outs=[];[outs.append(_job(j)) or (on_result and on_result(outs[-1])) for j in jobs]
    else:
        outs=[]
        with ProcessPoolExecutor(workers) as ex:
            for o in ex.map(_job,jobs,chunksize=1):
                outs.append(o)
                if on_result:on_result(o)
    checked=0;bad=[];hull={'hull_steps':0,'hull_downgrades':0,'hull_unauditable':0,'hull_nonvacuous':0}
    for i,o in sorted(outs,key=lambda x:x[0]):
        for arm,(ok,msg,t) in o.items():
            if msg=='not audited':continue
            checked+=1
            if not ok:bad.append({'case':i,'family':cases[i]['family'],'seed':cases[i]['seed'],'mask_rate':cases[i]['mask_rate'],'arm':arm,'first_difference':msg})
            elif arm=='J9':
                for k in hull:hull[k]+=t[k]
    return checked,bad,hull


def mutate(cases,k,rng_seed=20261026,arms=ARMS_2X2,max_step=8,j9=4,act=4):
    """Inject one single-field error into k distinct (case, arm) traces: the first `j9` go to J9 traces (alternately a
    toggled code in hull_union at a supported step, and a changed certificate), the next `act` flip the recorded
    action of an SP8 or J9 step (alternating), the rest are the v070 kinds. Returns (cases, keys)."""
    rng=random.Random(rng_seed);cases=copy.deepcopy(cases);inj=[]
    pj=[(i,'J9') for i,c in enumerate(cases) if 'J9' in c['arms'] and 'J9' in arms]
    rng.shuffle(pj)
    for n,(i,a) in enumerate(pj[:j9]):
        tr=cases[i]['arms'][a]['trace']
        if n%2==0:
            st=[r for r in tr if r.get('hull_union') is not None]
            if st:_flip_hull(rng.choice(st),rng);inj.append((i,a));continue
        rec=tr[rng.randrange(min(len(tr),max_step))]
        rec['certificate']=(rec['certificate']+1)%4 if rec['certificate'] is not None else 0;inj.append((i,a))
    sp=[(i,'SP8') for i,c in enumerate(cases) if 'SP8' in c['arms'] and 'SP8' in arms]
    jj=[(i,'J9') for i,c in enumerate(cases) if 'J9' in c['arms'] and 'J9' in arms and (i,'J9') not in inj]
    rng.shuffle(sp);rng.shuffle(jj);pick=[]
    while len(pick)<act and (sp or jj):
        src=sp if (len(pick)%2==0 and sp) or not jj else jj;pick.append(src.pop(0))
    for i,a in pick:
        tr=cases[i]['arms'][a]['trace'];rec=tr[rng.randrange(min(len(tr),max_step))];rec['action']=1-rec['action'];inj.append((i,a))
    keys=[(i,a) for i,c in enumerate(cases) for a in arms if a in c['arms'] and (i,a) not in inj];rng.shuffle(keys)
    for n,(i,a) in enumerate(keys[:k-len(inj)]):
        tr=cases[i]['arms'][a]['trace'];rec=tr[rng.randrange(min(len(tr),max_step or len(tr)))];kind=MUTATIONS[n%len(MUTATIONS)]
        r=rec
        if kind=='certificate':r['certificate']=(r['certificate']+1)%len(r['probabilities']) if r['certificate'] is not None else 0
        elif kind=='status':r['status']='CERTIFIED' if r['status']!='CERTIFIED' else 'ABSTAIN'
        elif kind=='logloss':rec['logloss']=rec['logloss']+1e-6
        else:rec['action']=1-rec['action']
        inj.append((i,a))
    return cases,set(inj)


def run(cases,plan,workers=4,mutate_k=0,arms=None,source_sha=None,on_result=None):
    check(plan==load(PLAN),'plan mismatch');tau6=plan['tau6']['value'];arms=arms or ARMS_2X2
    view=plan_view(plan);checked,bad,hull=count(cases,view,tau6,arms,workers=workers,on_result=on_result)
    rep={'schema':'brute.second-implementation-count.v6','study':plan['study'],
         'wording':'second implementation by the same author, no brute import; not an independent or third-party audit',
         'arm_traces_checked':checked,'mismatching_arm_traces':len(bad),'mismatches':bad,'tau6':tau6,'jump_window_K':view['jump_window_K'],
         'j9_hull':hull,'row_budget':view['row_budget_enumeration'],
         'granularity':'one count per (case, arm) trace; the first differing field inside a trace is recorded',
         'scope':'J9 (v080 SP8 audit path + window-hull row enumeration), SP8 (frozen v080 audit)','source_sha256':source_sha}
    if mutate_k:
        mc,inj=mutate(cases,mutate_k,arms=arms);_,mbad,_=count(mc,view,tau6,arms,workers=workers)
        flagged={(b['case'],b['arm']) for b in mbad};base={(b['case'],b['arm']) for b in bad}
        rep['mutation_test']={'injected':len(inj),'injected_j9':sum(a=='J9' for _,a in inj),'injected_sp8':sum(a=='SP8' for _,a in inj),
                              'detected_injected':len(inj&flagged),'flagged_not_injected':len(flagged-inj-base),
                              'rng':'random.Random(20261026)','passed':inj<=flagged and not (flagged-inj-base)}
    return rep
