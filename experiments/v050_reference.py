"""Second implementation (same author, no `brute` import) for study BRUTE-050-REGION-007 (G11, GX2).

Written from experiments/BRUTE_PLAN_007.json and committed before any v0.5.0 learner code (brute/region*.py,
brute/breadth.py) existed. NOT an independent or third-party audit: same author, same machine.

* 2x2 arms A5 and M5: the frozen v0.4.0 reference rules (experiments/v040_reference.py and the frozen pieces it imports)
  re-applied with rows fields null (the SAT backend enumerates nothing), the SOLVER_BUDGET overlay, and the M
  projection-volume tie-break written here from the plan text. The A4 arm is audited by the frozen v040_reference.audit_full.
* Breadth arms B5, BM5, BP5: an enumeration of canonical rows generalised to k actions and m=2**s codes, the breadth
  worlds and the breadth learner rules, all written here from the plan text. The audit of a breadth trace stops (and
  counts the steps checked) the first time any enumerated set would exceed the row budget (plan row_budget_enumeration).
Report = COUNT of mismatching (case, arm) traces, plus a mutation test.
"""
from __future__ import annotations
import argparse,copy,json,random
from math import log,log2,inf
from pathlib import Path
from dataclasses import dataclass
from concurrent.futures import ProcessPoolExecutor
from experiments.brute_common import check,load,sha,VerificationError
from experiments.v90_independent_reference import ref_initial,ref_support,ref_observe,bit_compatible
from experiments.v011_independent_reference import RefSuffix1,ref_reason,expected_decision,_close
from experiments.v030_independent_reference import y1k_union,score,full,compatible_codes
import experiments.v040_reference as V40
from experiments.v040_reference import ref_world,_Alarm,_window_tier
from bgr89.worlds import actions
from bgr90.worlds import step as new_step

ROOT=Path(__file__).resolve().parents[1]
PLAN=ROOT/'experiments/BRUTE_PLAN_007.json'
STUDY_DIR=ROOT/'results/study-007'
DRIFT=(12,23,34)
ARMS_2X2_NEW=('A5','M5')
ARMS_BREADTH=('B5','BM5','BP5')


class _Alarm12(_Alarm):
    """Pre-freeze fix (found on smoke seeds, PROCESS_NOTES): BRUTE_PLAN_007 defines residual = mean of the last W
    surprises ROUNDED to 12 d.p. and 'alarm set when residual > tau'; the frozen v040_reference._Alarm compares the
    unrounded mean, which differs from the plan exactly when the residual ties tau at 12 d.p. (residuals are discrete,
    and tau7 is itself a rounded residual). The frozen A4 audit (audit_full) keeps _Alarm unchanged."""
    def push(self,step,surprise,s4,s5):
        self.s.append(surprise)
        if len(self.s)<self.W:return None
        R=round(sum(self.s[-self.W:])/self.W,12)
        if self.tau is None:return R
        if not self.on:
            if R>self.tau:
                self.on=True;self.ever=True;self.run=0;self.sets.append(step)
                if self.first is None:self.first=step
        elif self.resume:
            self.run=self.run+1 if R<=self.tau else 0
            if self.run>=self.W and s4=='supported' and s5=='supported':
                self.on=False;self.run=0;self.resumes.append(step)
        return R


def plan006_view(plan):
    """The BRUTE_PLAN_006 keys the frozen v0.4.0 reference reads, filled from plan 007 (2x2 block)."""
    return {'family_state_cap':plan['family_state_cap_2x2'],'margin_state_cap':plan['margin_state_cap_2x2'],
            'row_budget_family':plan['row_budget_enumeration'],'row_budget_margin':plan['row_budget_enumeration'],
            'residual_surprise':{'window_W':plan['window_W'],'tau_v030':plan['tau_v030']},
            'open_world_reserve_epsilon':plan['open_world_reserve_epsilon'],'in_family':plan['in_family_2x2'],
            'actions_per_case':plan['actions_per_case_2x2']}


# ------------------------------------------------------------------ 2x2: A5 / M5
def volume_2x2(r4,a,k4,b4):
    """M tie-break V(a), plan experiment_rules['M ...'], 2 actions x 4 codes."""
    S=ref_support(r4,a,k4);tot=0.
    for c in S:
        f,st=ref_observe(r4,a,full(c),k4,b4)
        if st!='supported':tot+=2*log2(4);continue
        tot+=sum(log2(len(y1k_union(f,b,frozenset((c,)),k4))) for b in (0,1))
    return round(tot/len(S),12)


def audit_region_2x2(c,arm,plan,tau6):
    """Full check of an A5 or M5 trace (v0.4.0 A4 rules; rows null; SOLVER_BUDGET overlay; M tie-break for M5)."""
    p6=plan006_view(plan);fam=c['family'];seed=c['seed'];rate=c['mask_rate'];where=f'{fam} {seed} {rate} {arm}'
    k4=p6['family_state_cap'];k5=p6['margin_state_cap'];b4=b5=p6['row_budget_family']
    W_=plan['window_W'];eps=plan['open_world_reserve_epsilon'];wt=_window_tier();M=arm=='M5'
    A=c['arms'][arm];trace=A['trace']
    truth=ref_world(seed,fam);hidden=truth.start;initial=truth.observed(hidden,rate,-1)
    check(list(initial)==c['initial_visible'],'initial '+where)
    attested=fam in plan['in_family_2x2'];check(c['attested']==attested,'attested flag '+where)
    r4=ref_initial(initial);s4='supported';r5=ref_initial(initial);s5='supported';last=initial
    win=None;restarts=0;suffix=RefSuffix1(0.7,initial);al=_Alarm12(tau6,W_,True)
    issued=[];retracted=None;t={'steps':0,'certs':0,'cf_certs':0,'resumes':0,'unknown_forecasts':0}
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
            if cert is not None and y1k_union(r4,b,compatible_codes(last),k4)!=frozenset((cert,)):s_,rs,cert='ABSTAIN','RESYNC_AMBIGUOUS',None
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
        suffix.observe(a,obs);last=obs;was=s4
        if s4=='supported':r4,s4=ref_observe(r4,a,obs,k4,b4);r4=r4 or frozenset()
        if s5=='supported':r5,s5=ref_observe(r5,a,obs,k5,b5);r5=r5 or frozenset()
        if s4=='grammar_contradicted':
            if was=='supported':win=ref_initial(obs);restarts+=1;retracted=list(issued)
            else:
                w,ws=ref_observe(win,a,obs,wt['state_cap'],wt['row_budget'])
                if ws!='supported':win=ref_initial(obs);restarts+=1
                else:win=w
        R=al.push(step,rec['surprise'],s4,s5)
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
    check(d['window_restarts']==restarts and d['first_alarm_step']==al.first and d['alarm_steps']==al.sets and d['resume_steps']==al.resumes,'diagnostics '+where)
    check(d['certificates_issued']==len(issued) and d['certificates_retracted']==len(exp),'issued/retracted counts '+where)
    t['resumes']=len(al.resumes);return t


# ------------------------------------------------------------------ breadth: worlds
@dataclass(frozen=True)
class WorldK:
    n:int;k:int;s:int;transitions:tuple;emissions:tuple;start:int;seed:int;family:str
    def emission(self,h):return self.emissions[h]
    def next(self,h,a):return self.transitions[h][a]
    def observed(self,h,rate,step):
        c=self.emissions[h];bits=[(c>>(self.s-1-j))&1 for j in range(self.s)]
        rng=random.Random((self.seed*1299709+step*23011+701)%(2**64))
        return tuple(b if rng.random()>=rate else None for b in bits)


def _reach(rng,n,k):
    for _ in range(10000):
        T=[[rng.randrange(n) for a in range(k)] for q in range(n)];start=rng.randrange(n)
        seen={start};todo=[start]
        while todo:
            q=todo.pop()
            for x in T[q]:
                if x not in seen:seen.add(x);todo.append(x)
        if len(seen)==n:return tuple(tuple(r) for r in T),start
    raise ValueError('no reachable machine')


_GEN={'big6':(307,6,2,2,3,(0,0,1,1,2,2)),'sens3':(311,4,2,3,3,(0,0,1,2)),'act3':(313,4,3,2,3,(0,0,1,2)),'ood6s3':(317,6,2,3,4,(0,0,1,1,2,3))}


def breadth_world(seed,fam):
    off,n,k,s,nc,pat=_GEN[fam];rng=random.Random(seed*130363+off)
    T,start=_reach(rng,n,k);codes=rng.sample(range(2**s),nc);em=[codes[j] for j in pat];rng.shuffle(em)
    return WorldK(n,k,s,T,tuple(em),start,seed,fam)


def passive_actions(seed,steps,k):
    rng=random.Random(seed*72031+37);return tuple(rng.randrange(k) for _ in range(steps))


# ------------------------------------------------------------------ breadth: enumeration of canonical rows
class RefBudget(Exception):pass


@dataclass(frozen=True)
class Row:
    paths:tuple;outputs:tuple;current:int


def codes_of(obs,s):
    return frozenset(c for c in range(2**s) if all(b is None or ((c>>(s-1-j))&1)==b for j,b in enumerate(obs)))


def k_initial(codes,k):return frozenset((Row((-1,)*k,(frozenset(codes),),0),))


def k_observe(rows,a,codes,N,k,budget):
    """returns (rows, status); status 'supported' | 'grammar_contradicted'; raises RefBudget above the budget."""
    new=set()
    for r in rows:
        n=len(r.outputs);e=r.current*k+a;old=r.paths[e]
        for tg in ((old,) if old>=0 else range(min(N,n+1))):
            if tg==n:v=frozenset(codes);outs=r.outputs+(v,);paths=list(r.paths)+[-1]*k
            else:v=r.outputs[tg]&codes;outs=r.outputs[:tg]+(v,)+r.outputs[tg+1:];paths=list(r.paths)
            if not v:continue
            if old<0:paths[e]=tg
            new.add(Row(tuple(paths),outs,tg))
            if len(new)>budget:raise RefBudget()
    return (frozenset(new),'supported') if new else (frozenset(),'grammar_contradicted')


def k_support(rows,b,N,k,m):
    U=set()
    for r in rows:
        d=r.paths[r.current*k+b]
        if d>=0:U|=r.outputs[d]
        else:
            for o in r.outputs:U|=o
            if len(r.outputs)<N:U|=set(range(m))
    return tuple(sorted(U))


def k_saturated(rows,N):return all(len(r.outputs)==N for r in rows)


def k_y1k(rows,b,codes,N,k,m):
    U=set()
    for r in rows:
        for j,out in enumerate(r.outputs):
            if not (out&codes):continue
            d=r.paths[j*k+b]
            if d>=0:U|=r.outputs[d]
            elif j==r.current:
                for o in r.outputs:U|=o
                if len(r.outputs)<N:U|=set(range(m))
    return frozenset(U)


def k_score(r4,s4,r5,s5,alarm,a,N4,N5,k,m,budget):
    if s4!='supported' or s5!='supported' or alarm:return 0.
    S=k_support(r4,a,N4,k,m);tot=0
    for c in S:
        f,st=k_observe(r4,a,frozenset((c,)),N4,k,budget)
        if st!='supported' or k_saturated(f,N4):continue
        singles=[]
        for b in range(k):
            sb=k_support(f,b,N4,k,m)
            if len(sb)==1 and k_y1k(f,b,frozenset((c,)),N4,k,m)==frozenset(sb):singles.append((b,sb))
        if not singles:continue
        g,gs=k_observe(r5,a,frozenset((c,)),N5,k,budget)
        if gs!='supported':continue
        tot+=sum(k_support(g,b,N5,k,m)==sb for b,sb in singles)
    return round(tot/len(S),12)


def k_volume(r4,a,N4,k,m,budget):
    S=k_support(r4,a,N4,k,m);tot=0.
    for c in S:
        f,st=k_observe(r4,a,frozenset((c,)),N4,k,budget)
        if st!='supported':tot+=k*log2(m);continue
        tot+=sum(log2(len(k_y1k(f,b,frozenset((c,)),N4,k,m))) for b in range(k))
    return round(tot/len(S),12)


def choose(scores,default,vols=None):
    best=max(scores);tied=[b for b,x in enumerate(scores) if x==best]
    if vols is not None and len(tied)>1:
        v=min(vols[b] for b in tied);tied=[b for b in tied if vols[b]==v]
    return default if default in tied else min(tied)


def k_reason(cert,obs,s):
    bits=[(cert>>(s-1-j))&1 for j in range(s)]
    if any(o is not None and o!=b for o,b in zip(obs,bits)):return 'falsified_by_observation'
    if all(o is not None for o in obs):return 'scope_withdrawn'
    return 'unverifiable_masked'


def audit_breadth(c,arm,plan,tau7):
    """Check a B5/BM5/BP5 trace step by step until the enumeration exceeds its row budget.
    Returns counts incl. steps_checked and budget_stop (step index or None)."""
    fam=c['family'];seed=c['seed'];rate=c['mask_rate'];where=f'{fam} {seed} {rate} {arm}'
    lb=plan['breadth_worlds']['learner_bounds'][fam];N4=lb['family'];N5=lb['margin'];budget=plan['row_budget_enumeration']
    eps=plan['open_world_reserve_epsilon'];W_=plan['window_W'];steps=plan['actions_per_case_breadth']
    A=c['arms'][arm];trace=A['trace'];active=arm in ('B5','BM5');M=arm=='BM5'
    w=breadth_world(seed,fam);k=w.k;s=w.s;m=2**s
    check(c['k']==k and c['s']==s and c['attested']==lb['attested'],'case header '+where)
    hidden=w.start;initial=w.observed(hidden,rate,-1);check(list(initial)==c['initial_visible'],'initial '+where)
    tau=None if arm=='BP5' and c.get('calibration') else tau7
    al=_Alarm12(tau,W_,True);issued=[];retracted=None
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
                if cert is not None and k_y1k(r4,b,codes_of(last,s),N4,k,m)!=frozenset((cert,)):s_,rs,cert='ABSTAIN','RESYNC_AMBIGUOUS',None
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
            last=obs;was=s4
            if s4=='supported':r4,s4=k_observe(r4,a,cs,N4,k,budget)
            if s5=='supported':r5,s5=k_observe(r5,a,cs,N5,k,budget)
            if s4=='grammar_contradicted' and was=='supported':retracted=list(issued)
            R=al.push(step,rec['surprise'],s4,s5)
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
    check(d['first_alarm_step']==al.first and d['alarm_steps']==al.sets and d['resume_steps']==al.resumes,'diagnostics '+where)
    check(d['certificates_issued']==len(issued) and d['certificates_retracted']==len(exp),'issued/retracted counts '+where)
    return t


# ------------------------------------------------------------------ count / mutate
def audit_trace(c,arm,plan,tau6,tau7):
    """(ok, message, counts). Never raises on a mismatch."""
    try:
        if arm=='A4':t=V40.audit_full(c,arm,plan006_view(plan),tau6,plan['tau_v030'])
        elif arm in ARMS_2X2_NEW:t=audit_region_2x2(c,arm,plan,tau6)
        elif arm in ARMS_BREADTH:t=audit_breadth(c,arm,plan,tau7)
        else:return True,'not audited',None
        return True,None,t
    except (VerificationError,KeyError,IndexError,TypeError,ValueError,AssertionError) as exc:
        return False,f'{type(exc).__name__}: {exc}',None


def _job(x):
    i,c,plan,tau6,tau7,arms=x
    return i,{arm:audit_trace(c,arm,plan,tau6,tau7) for arm in arms if arm in c['arms']}


def count(cases,plan,tau6,tau7,arms=('A4',)+ARMS_2X2_NEW+ARMS_BREADTH,workers=4):
    jobs=[(i,c,plan,tau6,tau7,arms) for i,c in enumerate(cases)]
    if workers<=1:outs=[_job(j) for j in jobs]
    else:
        with ProcessPoolExecutor(workers) as ex:outs=list(ex.map(_job,jobs,chunksize=1))
    checked=0;bad=[];coverage={}
    for i,o in sorted(outs):
        for arm,(ok,msg,t) in o.items():
            if msg=='not audited':continue
            checked+=1
            if not ok:bad.append({'case':i,'family':cases[i]['family'],'seed':cases[i]['seed'],'mask_rate':cases[i]['mask_rate'],'arm':arm,'first_difference':msg})
            elif arm in ARMS_BREADTH:
                g=coverage.setdefault(f"{cases[i]['family']}/{arm}",{'steps':0,'steps_checked':0,'traces_budget_stopped':0})
                g['steps']+=t['steps'];g['steps_checked']+=t['steps_checked'];g['traces_budget_stopped']+=t['budget_stop'] is not None
    return checked,bad,coverage


MUTATIONS=('certificate','status','logloss','action')


def mutate(cases,k,rng_seed=20261025,arms=('A4',)+ARMS_2X2_NEW+ARMS_BREADTH,max_step=None):
    """Inject one single-field error into k distinct (case, arm) traces (at a step < max_step when given, so that budget-
    stopped breadth audits can still see it); returns (mutated cases, injected keys)."""
    rng=random.Random(rng_seed);cases=copy.deepcopy(cases)
    keys=[(i,a) for i,c in enumerate(cases) for a in arms if a in c['arms']];rng.shuffle(keys);inj=[]
    for n,(i,a) in enumerate(keys[:k]):
        tr=cases[i]['arms'][a]['trace'];rec=tr[rng.randrange(min(len(tr),max_step or len(tr)))];kind=MUTATIONS[n%len(MUTATIONS)]
        r=rec['forecasts'][rec['action']] if 'forecasts' in rec else rec
        if kind=='certificate':r['certificate']=(r['certificate']+1)%len(r['probabilities']) if r['certificate'] is not None else 0
        elif kind=='status':r['status']='CERTIFIED' if r['status']!='CERTIFIED' else 'ABSTAIN'
        elif kind=='logloss':rec['logloss']=rec['logloss']+1e-6
        else:rec['action']=(rec['action']+1)%len(rec['forecasts']) if 'forecasts' in rec else 1-rec['action']
        inj.append((i,a))
    return cases,set(inj)


def run(directory=STUDY_DIR,workers=4,limit=None,mutate_k=0,arms=None):
    directory=Path(directory);res=load(directory/'RESULTS.json');plan=res['plan']
    check(plan==load(PLAN),'plan mismatch');tau6=plan['tau6']['value'];tau7=res['calibration']['tau7']
    cases=res['cases'][:limit] if limit else res['cases'];arms=arms or ('A4',)+ARMS_2X2_NEW+ARMS_BREADTH
    checked,bad,cov=count(cases,plan,tau6,tau7,arms,workers=workers)
    rep={'schema':'brute.second-implementation-count.v2','study':plan['study'],
         'wording':'second implementation by the same author, no brute import; not an independent or third-party audit',
         'arm_traces_checked':checked,'mismatching_arm_traces':len(bad),'mismatches':bad,'tau6':tau6,'tau7':tau7,
         'breadth_steps_checked':cov,
         'granularity':'one count per (case, arm) trace; the first differing field inside a trace is recorded',
         'scope':'A4 with the frozen v040_reference.audit_full; A5/M5 with the v0.4.0 rules re-applied (rows null, SOLVER_BUDGET overlay, '
                 'M tie-break); B5/BM5/BP5 with a generalised enumeration up to the row budget',
         'source_results_sha256':sha(directory/'RESULTS.json')}
    if mutate_k:
        mc,inj=mutate(cases,mutate_k,arms=arms,max_step=8);_,mbad,_=count(mc,plan,tau6,tau7,arms,workers=workers)
        flagged={(b['case'],b['arm']) for b in mbad};base={(b['case'],b['arm']) for b in bad}
        rep['mutation_test']={'injected':len(inj),'detected_injected':len(inj&flagged),'flagged_not_injected':len(flagged-inj-base),
                              'passed':inj<=flagged and not (flagged-inj-base)}
    return rep


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--results-dir',default=str(STUDY_DIR));ap.add_argument('--workers',type=int,default=4)
    ap.add_argument('--limit',type=int);ap.add_argument('--mutate',type=int,default=0);ap.add_argument('--out')
    a=ap.parse_args();rep=run(a.results_dir,a.workers,a.limit,a.mutate)
    if a.out:
        p=Path(a.out);check(not p.exists(),'refusing to overwrite '+a.out);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(rep,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:v for k,v in rep.items() if k!='mismatches'},indent=2))
