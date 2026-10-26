"""Second implementation (same author, no `brute` import) for study BRUTE-0100-SUPPORT-TRANSFER-012 (G11, GLV, GT_ref).

Written from experiments/BRUTE_PLAN_012.json (J10_definition, transfer_definition, second_implementation) and committed
before brute/supportwindow.py and brute/transfer.py existed. NOT an independent or third-party audit: same author.

* SP8: the frozen experiments/v080_reference.audit_2x2(c, 'SP8', ...) imported unchanged.
* J10: a copy of the v090_reference J9 audit path (rule CTR, LU-C, every other field as SP8) in which the window test
  is the SUPPORT PROJECTION over the window rows: rows = the no-jump rows UNION every jump branch (the frozen
  v090_reference.window_rows, row enumeration), supW(b) = ref_support(rows, b, k4); a kept SP8 certificate c survives iff
  supW(b) == {c} (cert_rule <SP8 path> + '+wsupp'), else ABSTAIN / RESYNC_AMBIGUOUS, 'wsupp-downgraded'. hull_union is
  audited as supW (unauditable branches as v090).
* Transfer (GT_ref): an independent motif learner (itertools enumeration of complete machines for n <= 3, a separate
  recursive DFS for n = 4, both restricted to the traversed transitions and renumbered by first visit), an independent
  hypothesis expansion (action relabelling x injective class->code maps x start x open-transition completions, reachable
  canonical form) and an independent re-computation of every TRp / TRn decision from the learner-visible SP8 trace.
"""
from __future__ import annotations
import copy,random,itertools
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
from experiments.v090_reference import window_positions,window_rows
from bgr89.worlds import actions
from bgr90.worlds import step as new_step

ROOT=Path(__file__).resolve().parents[1]
PLAN=ROOT/'experiments/BRUTE_PLAN_012.json'
PLAN007=ROOT/'experiments/BRUTE_PLAN_007.json'
DRIFT=(12,23,34)
ARMS_2X2=('J10','SP8')


def plan_view(plan):
    """Plan 012 (as 009-011) inherits learner bounds, epsilon, row budget (160000) and window tier from BRUTE_PLAN_007."""
    v=dict(load(PLAN007));v.update(plan);v.update(plan['rule_constants_frozen'])
    v['actions_per_case_2x2']=plan['actions_per_case_2x2']
    check(v['row_budget_enumeration']==160000,'row budget');check(v['jump_window_K']==4,'K');return v


def window_supp(hist,obsl,acts,T,k4,b4,K):
    """({b: ref_support(window rows, b)}, ok): the exact support projection over (machine, <= 1 window jump)."""
    H,ok=window_rows(hist,obsl,acts,T,k4,b4,K)
    return {b:frozenset(ref_support(H,b,k4)) for b in (0,1)},ok


# ------------------------------------------------------------------ J10 audit (copy of the v090 J9 path, support test)
def audit_j10(c,plan,tau6,K):
    arm='J10'
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
            H,ok=window_supp(hist,obsl,acts,i,k4,b4,K_);hu=rec['hull_unknown'];check(isinstance(hu,int) and hu>=0,'hull_unknown '+where)
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
                        if H[b]==frozenset((cert,)):path=path+'+wsupp'
                        else:s_,rs,cert,path='ABSTAIN','RESYNC_AMBIGUOUS',None,'wsupp-downgraded';t['hull_downgrades']+=1
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
        if arm=='J10':t=audit_j10(c,plan,tau6,plan['jump_window_K'])
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
            elif arm=='J10':
                for k in hull:hull[k]+=t[k]
    return checked,bad,hull


def mutate(cases,k,rng_seed=20261026,arms=ARMS_2X2,max_step=8,j10=4,act=4):
    """Inject one single-field error into k distinct (case, arm) traces: the first `j9` go to J10 traces (alternately a
    toggled code in hull_union at a supported step, and a changed certificate), the next `act` flip the recorded
    action of an SP8 or J10 step (alternating), the rest are the v070 kinds. Returns (cases, keys)."""
    rng=random.Random(rng_seed);cases=copy.deepcopy(cases);inj=[]
    pj=[(i,'J10') for i,c in enumerate(cases) if 'J10' in c['arms'] and 'J10' in arms]
    rng.shuffle(pj)
    for n,(i,a) in enumerate(pj[:j10]):
        tr=cases[i]['arms'][a]['trace']
        if n%2==0:
            st=[r for r in tr if r.get('hull_union') is not None]
            if st:_flip_hull(rng.choice(st),rng);inj.append((i,a));continue
        rec=tr[rng.randrange(min(len(tr),max_step))]
        rec['certificate']=(rec['certificate']+1)%4 if rec['certificate'] is not None else 0;inj.append((i,a))
    sp=[(i,'SP8') for i,c in enumerate(cases) if 'SP8' in c['arms'] and 'SP8' in arms]
    jj=[(i,'J10') for i,c in enumerate(cases) if 'J10' in c['arms'] and 'J10' in arms and (i,'J10') not in inj]
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
    rep={'schema':'brute.second-implementation-count.v7','study':plan['study'],
         'wording':'second implementation by the same author, no brute import; not an independent or third-party audit',
         'arm_traces_checked':checked,'mismatching_arm_traces':len(bad),'mismatches':bad,'tau6':tau6,'jump_window_K':view['jump_window_K'],
         'j10_hull':hull,'row_budget':view['row_budget_enumeration'],
         'granularity':'one count per (case, arm) trace; the first differing field inside a trace is recorded',
         'scope':'J10 (v090 J9 audit path, window SUPPORT by row enumeration), SP8 (frozen v080 audit)','source_sha256':source_sha}
    if mutate_k:
        mc,inj=mutate(cases,mutate_k,arms=arms);_,mbad,_=count(mc,view,tau6,arms,workers=workers)
        flagged={(b['case'],b['arm']) for b in mbad};base={(b['case'],b['arm']) for b in bad}
        rep['mutation_test']={'injected':len(inj),'injected_j10':sum(a=='J10' for _,a in inj),'injected_sp8':sum(a=='SP8' for _,a in inj),
                              'detected_injected':len(inj&flagged),'flagged_not_injected':len(flagged-inj-base),
                              'rng':'random.Random(20261026)','passed':inj<=flagged and not (flagged-inj-base)}
    return rep


# ------------------------------------------------------------------ transfer (GT_ref): independent re-implementation
from bgr89.worlds import world as bgr89_world
from scripts.check_seeds_012 import source_seed as _source_seed
SOURCE_STEPS=60;LIB_CAP=64;HYP_CAP=200000;TRANSFER_FAMILIES=('cycle3','switch3','unaliased2','ood4')


def ref_source_obs(seed,family):
    """(codes, acts): fully observed source (mask 0.0) under the frozen passive actions bgr89.worlds.actions(seed, 60)."""
    w=bgr89_world(seed,family);h=w.start;codes=[w.emission(h)];acts=list(actions(seed,SOURCE_STEPS))
    for a in acts:h=w.next(h,a);codes.append(w.emission(h))
    return codes,acts


def _classes(codes):
    m={}
    for c in codes:m.setdefault(c,len(m))
    return m


def _relabel(trans,used,n,acts):
    """First-visit renumbering of a complete machine run from state 0; None unless all n states are visited."""
    order={0:0};s=0
    for a in acts:
        s=trans[s][a]
        if s not in order:order[s]=len(order)
    if len(order)!=n:return None
    T=[[None,None] for _ in range(n)]
    for (q,a) in used:T[order[q]][a]=order[trans[q][a]]
    return order,tuple(tuple(r) for r in T)


def _enum_small(codes,acts,n,cls):
    """itertools enumeration of every complete n-state machine (start 0); keep those reproducing the codes."""
    out=set()
    for flat in itertools.product(range(n),repeat=2*n):
        trans=[(flat[2*q],flat[2*q+1]) for q in range(n)];emit={0:codes[0]};s=0;used=set();ok=True
        for t,a in enumerate(acts):
            used.add((s,a));s=trans[s][a]
            if emit.setdefault(s,codes[t+1])!=codes[t+1]:ok=False;break
        if not ok or len(emit)!=n:continue
        rl=_relabel(trans,used,n,acts)
        if rl is None:continue
        order,T=rl;C=[None]*n
        for q,c in emit.items():C[order[q]]=cls[c]
        out.add((n,T,tuple(C)))
    return out


def _dfs4(codes,acts,cls,n=4):
    """Recursive DFS over partial n-state machines (states numbered at first visit)."""
    out=set()
    def go(t,s,T,E,k):
        if t==len(acts):
            if k==n:out.add((n,tuple(tuple(r) for r in T),tuple(E)))
            return
        a=acts[t];c=cls[codes[t+1]]
        if T[s][a] is not None:
            q=T[s][a]
            if E[q]==c:go(t+1,q,T,E,k)
            return
        for q in range(k+1 if k<n else k):
            if q<k and E[q]!=c:continue
            T2=[list(r) for r in T];T2[s][a]=q;E2=list(E)
            if q==k:E2[q]=c
            go(t+1,q,T2,E2,k+1 if q==k else k)
    E0=[None]*n;E0[0]=cls[codes[0]];go(0,0,[[None,None] for _ in range(n)],E0,1)
    return out


def ref_library(family,seed):
    codes,acts=ref_source_obs(seed,family);cls=_classes(codes)
    for n in range(1,5):
        sols=_enum_small(codes,acts,n,cls) if n<=3 else _dfs4(codes,acts,cls)
        if sols:
            sols=sorted(sols)
            if len(sols)>LIB_CAP:return {'source_family':family,'source_seed':seed,'min_n':n,'status':'over_cap','motif_count':len(sols),'motifs':[]}
            return {'source_family':family,'source_seed':seed,'min_n':n,'status':'ok','motif_count':len(sols),
                    'motifs':[{'n':m[0],'trans':[list(r) for r in m[1]],'classes':list(m[2])} for m in sols]}
    return {'source_family':family,'source_seed':seed,'min_n':None,'status':'none','motif_count':0,'motifs':[]}


def _canon(trans,emis,start):
    """Reachable part from start, renumbered by BFS (action 0 before 1)."""
    order={start:0};queue=[start]
    while queue:
        q=queue.pop(0)
        for a in (0,1):
            r=trans[q][a]
            if r not in order:order[r]=len(order);queue.append(r)
    inv=sorted(order,key=order.get)
    return (tuple((order[trans[q][0]],order[trans[q][1]]) for q in inv),tuple(emis[q] for q in inv))


def ref_hypotheses(lib):
    """(sorted list of canonical (trans, emis), status)."""
    if lib['status']!='ok':return [],lib['status']
    H=set()
    for m in lib['motifs']:
        n=m['n'];K=max(m['classes'])+1;open_=[(q,a) for q in range(n) for a in (0,1) if m['trans'][q][a] is None]
        for swap in (0,1):
            for perm in itertools.permutations(range(4),K):
                emis=tuple(perm[k] for k in m['classes'])
                for fill in itertools.product(range(n),repeat=len(open_)):
                    T=[list(r) for r in m['trans']]
                    for (q,a),v in zip(open_,fill):T[q][a]=v
                    if swap:T=[[r[1],r[0]] for r in T]
                    for st in range(n):
                        H.add(_canon(T,emis,st))
                        if len(H)>HYP_CAP:return [],'over_cap'
    return sorted(H),'ok'


def ref_tr_arm(case,lib,label):
    """Independent recomputation of one TR arm (dict as the learner side writes it, minus timing)."""
    H,st=ref_hypotheses(lib);burn=case['burn_in']
    init=tuple(case['initial_visible'])
    alive=[(T,E,0) for T,E in H if bit_compatible(E[0],init)]
    out={'library':label,'hypotheses_initial':len(H),'hypothesis_status':st,'alive_after_initial':len(alive),'disabled_step':0 if not alive else None,'trace':[]}
    sp=case['arms']['SP8']['trace'];first=45;false=0
    for r in sp:
        t=r['step'];a=r['action'];recs={a:r,1-a:r['counterfactual']};act={a:r['actual_emission_EVALUATOR_ONLY'],1-a:r['counterfactual_actual_EVALUATOR_ONLY']}
        cert=[None,None];rule=[None,None];wrong=[False,False]
        for b in (0,1):
            R=recs[b]
            if R['certificate'] is not None:cert[b]=R['certificate'];rule[b]='sp8'
            elif alive and t>burn and R['support'] is not None:
                P={E[T[s][b]] for T,E,s in alive}
                if len(P)==1:
                    c=next(iter(P))
                    if c in R['support']:cert[b]=c;rule[b]='transfer'
            wrong[b]=cert[b] is not None and cert[b]!=act[b];false+=wrong[b]
        if cert[a] is not None and first==45:first=t
        out['trace'].append({'step':t,'alive':len(alive),'certificate':cert,'rule':rule,'wrong':wrong})
        obs=tuple(r['observed'])
        if alive:
            alive=[(T,E,T[s][a]) for T,E,s in alive if bit_compatible(E[T[s][a]],obs)]
            if not alive and out['disabled_step'] is None:out['disabled_step']=t
    out['first_cert_step']=first;out['false_certificates']=false
    out['transfer_certificates']=sum(x=='transfer' for s in out['trace'] for x in s['rule'])
    return out


def audit_transfer_case(c,plan):
    """(ok, message). Recomputes both libraries and both TR arms; any differing field is a mismatch."""
    try:
        fam=c['family'];off=c['seed']-plan['heldout_ranges_transfer']['targets'][fam][0]+1 if c.get('smoke') is not True else c['offset']
        for key,neg in (('pos',False),('neg',True)):
            sf,ss=(c['libraries'][key]['source_family'],c['libraries'][key]['source_seed']) if c.get('smoke') else _source_seed(fam,off,plan,neg)
            lib=ref_library(sf,ss);got=c['libraries'][key]
            for k in ('source_family','source_seed','min_n','status','motif_count','motifs'):check(got[k]==lib[k],f'library {key} {k}')
            arm='TRp' if key=='pos' else 'TRn';exp=ref_tr_arm(c,lib,key);g=c['transfer'][arm]
            for k in exp:check(g[k]==exp[k],f'{arm} {k}')
        return True,None
    except (VerificationError,KeyError,IndexError,TypeError,ValueError,AssertionError) as exc:
        return False,f'{type(exc).__name__}: {exc}'


def _tjob(x):
    i,c,plan=x;return i,audit_transfer_case(c,plan)


def run_transfer(cases,plan,workers=1):
    jobs=[(i,c,plan) for i,c in enumerate(cases)]
    if workers<=1:outs=[_tjob(j) for j in jobs]
    else:
        with ProcessPoolExecutor(workers) as ex:outs=list(ex.map(_tjob,jobs,chunksize=4))
    bad=[{'case':i,'family':cases[i]['family'],'seed':cases[i]['seed'],'mask_rate':cases[i]['mask_rate'],'first_difference':m} for i,(ok,m) in sorted(outs) if not ok]
    return {'schema':'brute.transfer-reference.v1','study':plan['study'],'cases_checked':len(cases),'mismatching_cases':len(bad),'mismatches':bad,
            'wording':'second implementation by the same author, no brute import'}
