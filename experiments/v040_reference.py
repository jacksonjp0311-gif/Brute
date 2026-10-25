"""Second implementation (same author, no `brute` import) for study BRUTE-040-GEOMETRY-006 (G11).

Written from experiments/BRUTE_PLAN_006.json and committed before any v0.4.0 learner code (brute/resume.py) existed.
It is NOT an independent or third-party audit: same author, same machine, and it reuses the frozen v0.3.0 second
implementation (experiments/v030_independent_reference.py) for the parts the plan declares unchanged (supports,
Y1k union, LU-R scores, v0.1.1 decision/probability rules). New here, from the plan text: the perm4 world generator
(written independently of experiments/worlds_006.py), the tau6 alarm with the resume rule, the never-re-attest rule,
and a mismatch COUNT over every arm trace (a failing trace is recorded and the scan continues) with a mutation test.
"""
from __future__ import annotations
import argparse,json,copy,random
from math import log
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor
from experiments.brute_common import check,load,sha,VerificationError
from experiments.v90_independent_reference import ref_initial,ref_support,ref_observe,bit_compatible
from experiments.v011_independent_reference import RefSuffix1,ref_reason,expected_decision,_close
import experiments.v030_independent_reference as _v030
from experiments.v030_independent_reference import y1k_union,score,full,compatible_codes,audit_arm as audit_arm_030
from bgr89.worlds import world as old_world,actions,HiddenWorld
from bgr90.worlds import world as new_world,step as new_step

ROOT=Path(__file__).resolve().parents[1]
PLAN=ROOT/'experiments/BRUTE_PLAN_006.json'
STUDY_DIR=ROOT/'results/study-006'
DRIFT=(12,23,34)
FULL_ARMS=('A4','P4')
SLIM_030=('A3','A2','E2')   # checked with the frozen v0.3.0 second implementation (slim mode, alarm read from trace)


def ref_perm4(seed):
    """perm4 generator from the plan text (new_family_perm4.generator)."""
    rng=random.Random(seed*104729+211)
    p0=list(range(4));rng.shuffle(p0);p1=list(range(4));rng.shuffle(p1)
    codes=rng.sample(range(4),3);em=[codes[0],codes[0],codes[1],codes[2]];rng.shuffle(em)
    start=rng.randrange(4)
    return HiddenWorld(4,tuple((p0[s],p1[s]) for s in range(4)),tuple(em),start,seed,'perm4')


def ref_world(seed,fam):
    if fam=='perm4':return ref_perm4(seed)
    return (new_world if fam in ('ood5','drift4') else old_world)(seed,fam)


def _old_or_perm4(seed,fam):return ref_perm4(seed) if fam=='perm4' else old_world(seed,fam)
_v030.old_world=_old_or_perm4   # in this process only: lets the frozen v0.3.0 slim audit replay perm4 worlds


def _window_tier():
    return load(ROOT/'experiments/BRUTE_PLAN_004.json')['window_tier']


class _Alarm:
    """tau6 alarm with the plan's resume rule. `on` is the state used by the next predict."""
    def __init__(self,tau,W,resume):
        self.tau=tau;self.W=W;self.resume=resume;self.s=[];self.on=False;self.run=0;self.ever=False
        self.first=None;self.sets=[];self.resumes=[]
    def push(self,step,surprise,s4,s5):
        self.s.append(surprise)
        if len(self.s)<self.W:return None
        R=sum(self.s[-self.W:])/self.W
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


def audit_full(c,arm,plan,tau6,tau_c):
    """Full check of an A4 or P4 trace. Raises VerificationError at the first differing field of this trace."""
    active=arm=='A4';fam=c['family'];seed=c['seed'];rate=c['mask_rate'];where=f'{fam} {seed} {rate} {arm}'
    k4=plan['family_state_cap'];k5=plan['margin_state_cap'];b4=plan['row_budget_family'];b5=plan['row_budget_margin']
    W_=plan['residual_surprise']['window_W'];eps=plan['open_world_reserve_epsilon'];wt=_window_tier()
    A=c['arms'][arm];trace=A['trace'];B=c['burn_in']
    truth=ref_world(seed,fam);hidden=truth.start;initial=truth.observed(hidden,rate,-1)
    check(list(initial)==c['initial_visible'],'initial '+where)
    attested=fam in plan['in_family'];check(c['attested']==attested,'attested flag '+where)
    r4=ref_initial(initial);s4='supported';r5=ref_initial(initial);s5='supported';last=initial
    win=None;restarts=0;suffix=RefSuffix1(0.7,initial);al=_Alarm(tau6,W_,True);ctl=_Alarm(tau_c,W_,False)
    issued=[];retracted=None;diverged=False;t={'steps':0,'certs':0,'cf_certs':0,'resumes':0}
    for i,pa in enumerate(actions(seed,plan['actions_per_case'])):
        rec=trace[i];step=i+1;alarm=al.on
        check(rec['step']==step and rec['passive_action']==pa,'step '+where)
        if active:
            sc=[score(r4,s4,r5,s5,alarm,b,k4,k5,b4,b5,True) for b in (0,1)]
            a=pa if sc[0]==sc[1] else (0 if sc[0]>sc[1] else 1);e=rec['experiment']
            check(e['scores']==sc and e['score']==sc[a] and e['tied']==(sc[0]==sc[1]) and e['check'] is False,f'experiment {where} {i}')
            want='PROPOSED' if (s4=='supported' and s5=='supported' and not alarm) else 'NO_PROPOSAL'
            check(e['proposal']==want,f'proposal {where} {i}')
        else:
            a=pa;check('experiment' not in rec,'passive experiment '+where)
        check(rec['action']==a,f'action {where} {i}')
        sat=all(len(m.outputs)==k4 for m in r4) if s4=='supported' else None
        nxt=[new_step(truth,hidden,b,i) if fam=='drift4' else truth.next(hidden,b) for b in (0,1)]
        act=[truth.emission(h) for h in nxt];dec={}
        for b,r in ((a,rec),(1-a,rec['counterfactual'])):
            sup=ref_support(r4,b,k4) if s4=='supported' else None
            msup=ref_support(r5,b,k5) if s5=='supported' else None
            check((list(sup) if sup is not None else None)==r['support'],f'support {where} {i} {b}')
            check((list(msup) if msup is not None else None)==r['margin_support'],f'margin {where} {i} {b}')
            check(sat==r['saturated'],f'saturation {where} {i}')
            s_,rs,cert=expected_decision(s4,alarm,sup,s5,msup,sat);v020=cert
            if cert is not None and y1k_union(r4,b,compatible_codes(last),k4)!=frozenset((cert,)):s_,rs,cert='ABSTAIN','RESYNC_AMBIGUOUS',None
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
            dec[b]=(cert,pub,v020)
        check(rec['actual_emission_EVALUATOR_ONLY']==act[a] and rec['counterfactual_actual_EVALUATOR_ONLY']==act[1-a],'truth '+where)
        check(rec['drift_step']==(fam=='drift4' and step in DRIFT),'drift flag')
        if arm=='P4':
            q=A['control_trace'][i]
            if not diverged:
                if rec['reason']=='RESYNC_AMBIGUOUS':check(q['status']=='CERTIFIED' and q['certificate']==dec[a][2],f'G8a resync {where} {i}')
                else:
                    for k in ('status','reason','certificate','public_certificate'):check(q[k]==rec[k],f'G8a {k} {where} {i}')
            if rec['forecast_source']!='window_n4':check(q['probabilities']==rec['probabilities'] and q['forecast_source']==rec['forecast_source'],f'G8a probabilities {where} {i}')
            else:check(q['forecast_source']=='suffix1','window replaced non-suffix1')
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
        if arm=='P4':
            q=A['control_trace'][i];check(abs(q['surprise']-(-log(sum(p for x,p in enumerate(q['probabilities']) if bit_compatible(x,obs)))))<1e-8,'control surprise')
            Rc=ctl.push(step,q['surprise'],s4,s5);check((Rc is None and q['residual_after'] is None) or (Rc is not None and abs(Rc-q['residual_after'])<1e-8),'control residual')
            check(q['alarm_after']==ctl.on,f'control alarm {where} {i}')
            if al.on!=ctl.on:diverged=True
        check(rec['family_status_after']==s4 and rec['margin_status_after']==s5,'status after '+where)
        check(rec['family_rows_after']==len(r4) and rec['margin_rows_after']==len(r5),'rows after '+where)
        check(rec['window_status_after']==(None if win is None else 'supported') and rec['window_rows_after']==(None if win is None else len(win)),'window '+where)
        t['steps']+=1;t['certs']+=cert is not None;t['cf_certs']+=dec[1-a][0] is not None
    check(A['issued']==[[s_,k] for s_,k,_ in issued],'issued '+where)
    acts={r['step']:r['actual_emission_EVALUATOR_ONLY'] for r in trace}
    exp=[{'step':s_,'certificate':k,'observed':list(o),'reason':ref_reason(k,o),'actual_EVALUATOR_ONLY':acts[s_],'wrong':k!=acts[s_]} for s_,k,o in (retracted or [])]
    check(A['retractions']==exp,'retractions '+where)
    d=A['diagnostics']
    check(d['window_restarts']==restarts and d['first_alarm_step']==al.first and d['alarm_steps']==al.sets and d['resume_steps']==al.resumes,'diagnostics '+where)
    check(d['certificates_issued']==len(issued) and d['certificates_retracted']==len(exp),'issued/retracted counts '+where)
    if arm=='P4':check(A['control_diagnostics']['alarm_step']==ctl.first,'control alarm step '+where)
    t['resumes']=len(al.resumes);return t


def audit_trace(c,arm,plan,tau6,tau_c):
    """Returns (ok, message, counts). Never raises on a mismatch."""
    try:
        if arm in FULL_ARMS:t=audit_full(c,arm,plan,tau6,tau_c)
        elif arm in SLIM_030:
            p5=dict(load(ROOT/'experiments/BRUTE_PLAN_005.json'),in_family=plan['in_family']);t=audit_arm_030(c,arm,p5,tau_c,False)
        else:return True,'not audited',None
        return True,None,t
    except (VerificationError,KeyError,IndexError,TypeError,ValueError,AssertionError) as exc:
        return False,f'{type(exc).__name__}: {exc}',None


def _job(x):
    i,c,plan,tau6,tau_c,arms=x
    return i,{arm:audit_trace(c,arm,plan,tau6,tau_c)[:2] for arm in arms if arm in c['arms']}


def count(cases,plan,tau6,tau_c,arms=FULL_ARMS+SLIM_030,workers=4):
    jobs=[(i,c,plan,tau6,tau_c,arms) for i,c in enumerate(cases)]
    if workers<=1:outs=[_job(j) for j in jobs]
    else:
        with ProcessPoolExecutor(workers) as ex:outs=list(ex.map(_job,jobs,chunksize=1))
    checked=0;bad=[]
    for i,o in outs:
        for arm,(ok,msg) in o.items():
            if msg=='not audited':continue
            checked+=1
            if not ok:bad.append({'case':i,'family':cases[i]['family'],'seed':cases[i]['seed'],'mask_rate':cases[i]['mask_rate'],'arm':arm,'first_difference':msg})
    return checked,bad


MUTATIONS=('certificate','status','logloss','action')


def mutate(cases,k,rng_seed=20261025,arms=FULL_ARMS):
    """Inject one single-field error into k distinct (case, arm) traces; returns (mutated cases, injected keys)."""
    rng=random.Random(rng_seed);cases=copy.deepcopy(cases)
    keys=[(i,a) for i,c in enumerate(cases) for a in arms if a in c['arms']];rng.shuffle(keys);inj=[]
    for n,(i,a) in enumerate(keys[:k]):
        tr=cases[i]['arms'][a]['trace'];r=tr[rng.randrange(len(tr))];kind=MUTATIONS[n%len(MUTATIONS)]
        if kind=='certificate':r['certificate']=(r['certificate']+1)%4 if r['certificate'] is not None else 0
        elif kind=='status':r['status']='CERTIFIED' if r['status']!='CERTIFIED' else 'ABSTAIN'
        elif kind=='logloss':r['logloss']=r['logloss']+1e-6
        else:r['action']=1-r['action']
        inj.append((i,a))
    return cases,set(inj)


def run(directory=STUDY_DIR,workers=4,limit=None,mutate_k=0):
    directory=Path(directory);res=load(directory/'RESULTS.json');plan=res['plan']
    check(plan==load(PLAN),'plan mismatch');cal=res['calibration']
    tau6=cal['tau6'];tau_c=plan['residual_surprise']['tau_v030']
    cases=res['cases'][:limit] if limit else res['cases']
    checked,bad=count(cases,plan,tau6,tau_c,workers=workers)
    rep={'schema':'brute.second-implementation-count.v1','study':plan['study'],
         'wording':'second implementation by the same author, no brute import; not an independent or third-party audit',
         'arm_traces_checked':checked,'mismatching_arm_traces':len(bad),'mismatches':bad,'tau6':tau6,
         'granularity':'one count per (case, arm) trace; the first differing field inside a trace is recorded',
         'scope':'A4/P4 full (supports, saturation, Y1k, LU-R scores, actions, decisions, public certificates, probabilities, '
                 'surprise, residual, tau6 alarm and resume, G8a vs v0.1.1 control, issued/retractions); A3/A2/E2 with the frozen '
                 'v0.3.0 second implementation in slim mode; D2, F2 and C not audited here (D2/F2 geometry in GR1b)',
         'source_results_sha256':sha(directory/'RESULTS.json')}
    if mutate_k:
        mc,inj=mutate(cases,mutate_k);_,mbad=count(mc,plan,tau6,tau_c,arms=FULL_ARMS,workers=workers)
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
