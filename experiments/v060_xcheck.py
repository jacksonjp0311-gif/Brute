"""GX2' driver (BRUTE_PLAN_008): re-derive every decision-level field of the breadth arms B5, BR6, BC6 (and, for the
non-gated R_dev_xcheck_007 report, the sealed study-007 B5/BM5/BP5 traces) with the CaDiCaL second encoding in
brute/xcheck_sat.py - no row enumeration.

Same author as the learners and as v050_reference/v060_reference: a second implementation, never an independent one.
The flow mirrors v050_reference.audit_breadth / v060_reference.audit_drift_breadth; every region query (feasibility,
support, margin support, saturation, Y1k and the recent union, and the LU-R/M scores built from them) is answered by
brute.xcheck_sat.XRegion re-derived from the raw (action, mask) evidence. World generation, passive actions, the
residual alarm, the tie-break `choose`, `codes_of`, `k_reason` and `expected_decision` are imported from the frozen
reference modules; no enumeration function (k_initial/k_observe/k_support/k_y1k/k_score/k_volume) is called.

Budget (plan): a query hitting the 2,000,000-conflict budget makes the step UNCHECKED (counted, never a mismatch, never a
pass). Implementation note (disclosed in BRUTE_DEVIATIONS_008.md): at an unchecked step the recorded action, decision and
statuses are adopted so that the rest of the trace can still be checked.
Witness failures: every SAT answer is decoded and replayed in plain Python by xcheck_sat; failures are counted.
"""
from __future__ import annotations
import argparse,gzip,json,os,time
from math import log,log2
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor,as_completed
from experiments.brute_common import check,load,VerificationError
from experiments.v011_independent_reference import expected_decision
from experiments.v050_reference import _Alarm12,codes_of,choose,k_reason,breadth_world,passive_actions
from brute.xcheck_sat import XRegion,mask_of,CONF_BUDGET

ROOT=Path(__file__).resolve().parents[1]
PLAN=ROOT/'experiments/BRUTE_PLAN_008.json'
PLAN007=ROOT/'experiments/BRUTE_PLAN_007.json'
RULE={'BR6':'RO','BC6':'CT'}
ARMS_008=('B5','BR6','BC6')
ARMS_007=('B5','BM5','BP5')


class Unchecked(Exception):pass


def plan_view(plan):
    v=dict(load(PLAN007));v.update(plan);v.update(plan.get('rule_constants_frozen',{}));return v


class Oracle:
    """Per-case memo of XRegion answers keyed by (bound, evidence, query). Raises Unchecked on a budget hit."""
    def __init__(self,k,m,budget=CONF_BUDGET):
        self.k=k;self.m=m;self.budget=budget;self.res={};self.live={}
        self.queries=0;self.unknown_queries=0;self.witness_failures=0;self.regions=0

    def _reg(self,N,masks,acts):
        key=(N,masks,acts)
        if key not in self.live:self.live[key]=XRegion(N,self.k,self.m,masks,acts,self.budget);self.regions+=1
        return self.live[key]

    def q(self,N,masks,acts,name,*args):
        key=(N,masks,acts,name,args)
        if key not in self.res:
            X=self._reg(N,masks,acts)
            if name=='feasible':r=X.feasible();u=int(r is None)
            elif name=='support':r,u=X.support(*args)
            elif name=='saturated':r,u=X.saturated()
            elif name=='y1k':r,u=X.y1k(*args)
            else:raise ValueError(name)
            self.res[key]=(r,u)
        r,u=self.res[key]
        if u:raise Unchecked(name)
        return r

    def flush(self):
        for X in self.live.values():
            self.queries+=X.queries;self.unknown_queries+=X.unknown;self.witness_failures+=X.witness_failures;X.close()
        self.live={}

    def status(self,N,masks,acts):
        return 'supported' if self.q(N,masks,acts,'feasible') else 'grammar_contradicted'


def x_score(o,N4,N5,e4,e5,s4,s5,alarm,a):
    if s4!='supported' or s5!='supported' or alarm:return 0.
    (m4,a4),(m5,a5)=e4,e5;k=o.k
    S=o.q(N4,m4,a4,'support',a);tot=0
    for c in S:
        f=(m4+(1<<c,),a4+(a,))
        if not o.q(N4,*f,'feasible') or o.q(N4,*f,'saturated'):continue
        singles=[]
        for b in range(k):
            sb=o.q(N4,*f,'support',b)
            if len(sb)==1 and o.q(N4,*f,'y1k',b,1<<c,None)==sb:singles.append((b,sb))
        if not singles:continue
        g=(m5+(1<<c,),a5+(a,))
        if not o.q(N5,*g,'feasible'):continue
        tot+=sum(o.q(N5,*g,'support',b)==sb for b,sb in singles)
    return round(tot/len(S),12)


def x_volume(o,N4,e4,a):
    m4,a4=e4;k=o.k;m=o.m;S=o.q(N4,m4,a4,'support',a);tot=0.
    for c in S:
        f=(m4+(1<<c,),a4+(a,))
        if not o.q(N4,*f,'feasible'):tot+=k*log2(m);continue
        tot+=sum(log2(len(o.q(N4,*f,'y1k',b,1<<c,None))) for b in range(k))
    return round(tot/len(S),12)


def x_rule(arm,o,N4,e4,b,lmask,cert,s_,rs,events,i,rw,burn):
    plain=lambda:o.q(N4,*e4,'y1k',b,lmask,None)
    if arm not in RULE:
        if plain()!=(cert,):return 'ABSTAIN','RESYNC_AMBIGUOUS',None,None
        return s_,rs,cert,None
    if RULE[arm]=='RO':
        ss=events[-1] if events else None
        if ss is not None and i-ss<rw:U=o.q(N4,*e4,'y1k',b,lmask,max(0,ss-1));path='Y1k-recent'
        else:U=plain();path='Y1k'
        if U==(cert,):return s_,rs,cert,path
        return 'ABSTAIN','RESYNC_AMBIGUOUS',None,'downgraded'
    if plain()==(cert,):return s_,rs,cert,'Y1k'
    if not events and i>=burn:return s_,rs,cert,'tracked-calm'
    return 'ABSTAIN','RESYNC_AMBIGUOUS',None,'downgraded'


def audit(c,arm,plan,tau7,o):
    """Re-derive one breadth trace. Returns counts; raises VerificationError at the first mismatching checked step."""
    fam=c['family'];seed=c['seed'];rate=c['mask_rate'];where=f'{fam} {seed} {rate} {arm}'
    lb=plan['breadth_worlds']['learner_bounds'][fam];N4=lb['family'];N5=lb['margin']
    eps=plan['open_world_reserve_epsilon'];W_=plan['window_W'];steps=plan['actions_per_case_breadth']
    A=c['arms'][arm];trace=A['trace'];active=arm!='BP5';M=arm=='BM5'
    drift=arm in RULE;frac=plan.get('surprise_fraction');rw=plan.get('recency_window');burn=plan.get('burn_in')
    w=breadth_world(seed,fam);k=w.k;s=w.s;m=2**s
    check(c['k']==k and c['s']==s and c['attested']==lb['attested'],'case header '+where)
    hidden=w.start;initial=w.observed(hidden,rate,-1);check(list(initial)==c['initial_visible'],'initial '+where)
    tau=None if arm=='BP5' and c.get('calibration') else tau7
    al=_Alarm12(tau,W_,True);issued=[];retracted=None;events=[]
    t={'steps':len(trace),'steps_checked':0,'steps_unchecked':0,'unchecked_steps':[],'certs':0,'unknown_forecasts':0}
    m4=(mask_of(initial,s),);a4=();m5=m4;a5=();s4='supported';s5='supported';last=initial
    pas=passive_actions(seed,steps,k);check(len(trace)==steps,'trace length '+where)
    for i,pa in enumerate(pas):
        rec=trace[i];step=i+1;alarm=al.on;fc=rec['forecasts']
        check(rec['step']==step and rec['passive_action']==pa,'step '+where)
        nxt=[w.next(hidden,b) for b in range(k)];act=[w.emission(h) for h in nxt]
        try:
            e4=(m4,a4);e5=(m5,a5)
            live=s4=='supported' and s5=='supported' and not alarm
            if active:
                sc=[x_score(o,N4,N5,e4,e5,s4,s5,alarm,b) for b in range(k)]
                tiedn=sum(x==max(sc) for x in sc)
                vol=[x_volume(o,N4,e4,b) for b in range(k)] if (M and live and tiedn>1) else None
                a=choose(sc,pa,vol);e=rec['experiment']
                check(e['scores']==sc and e['score']==sc[a] and e['tied']==(tiedn>1) and e['volumes']==vol
                      and e['rule']==('M' if M else 'LU-R') and e['proposal']==('PROPOSED' if live else 'NO_PROPOSAL'),f'experiment {where} {i}')
            else:
                a=pa;check('experiment' not in rec,'passive experiment '+where)
            check(rec['action']==a,f'action {where} {i}')
            sat=o.q(N4,*e4,'saturated') if s4=='supported' else None
            check(len(fc)==k,'forecasts '+where);dec={}
            for b in range(k):
                r=fc[b];sup=o.q(N4,*e4,'support',b) if s4=='supported' else None
                msup=o.q(N5,*e5,'support',b) if s5=='supported' else None
                unk=r['solver_unknown'];check(isinstance(unk,int) and unk>=0,'solver_unknown '+where)
                if unk==0:
                    check((list(sup) if sup is not None else None)==r['support'],f'support {where} {i} {b}')
                    check((list(msup) if msup is not None else None)==r['margin_support'],f'margin {where} {i} {b}')
                    check(sat==r['saturated'],f'saturation {where} {i}')
                else:check(sup is None or set(sup)<=set(r['support'] or ()),f'unknown support superset {where} {i}')
                s_,rs,cert=expected_decision(s4,alarm,sup,s5,msup,sat);path=None
                if cert is not None:s_,rs,cert,path=x_rule(arm,o,N4,e4,b,mask_of(last,s),cert,s_,rs,events,i,rw,burn)
                if drift:check(unk>0 or r['cert_rule']==path,f'cert_rule {where} {i} {b}')
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
                t['unknown_forecasts']+=unk>0;dec[b]=cert
            checked=True
        except Unchecked:
            # adopt the recorded action and decision of this step (disclosed implementation note)
            checked=False;a=rec['action'];dec={a:fc[a]['certificate']}
        hidden=nxt[a];obs=w.observed(hidden,rate,i)
        check(rec['observed']==list(obs),'observation '+where)
        P=fc[a]['probabilities']
        if checked:
            check(abs(rec['logloss']+log(max(1e-12,P[act[a]])))<1e-8,'logloss '+where)
            check(abs(rec['min_probability']-min(min(f['probabilities']) for f in fc))<1e-12,'min prob '+where)
            sp=-log(sum(P[x] for x in codes_of(obs,s)));check(abs(sp-rec['surprise'])<1e-8,f'surprise {where} {i}')
        cert=dec[a]
        if cert is not None and (step,cert) not in [(x[0],x[1]) for x in issued]:issued.append((step,cert,tuple(obs)))
        last=obs;was=s4;mk=mask_of(obs,s)
        try:
            if s4=='supported':
                m4=m4+(mk,);a4=a4+(a,);s4=o.status(N4,m4,a4)
            if s5=='supported':
                m5=m5+(mk,);a5=a5+(a,);s5=o.status(N5,m5,a5)
        except Unchecked:
            checked=False;s4=rec['family_status_after'];s5=rec['margin_status_after']
        if s4=='grammar_contradicted' and was=='supported':retracted=list(issued)
        R=al.push(step,rec['surprise'],s4,s5)
        if drift and ((s4=='grammar_contradicted' and was=='supported') or (R is not None and R>tau*frac)):events.append(step)
        if checked:
            check((R is None and rec['residual_after'] is None) or (R is not None and abs(R-rec['residual_after'])<1e-8),f'residual {where} {i}')
            check(rec['alarm_after']==al.on,f'alarm {where} {i}')
            check(rec['family_status_after']==s4 and rec['margin_status_after']==s5,'status after '+where)
            t['steps_checked']+=1;t['certs']+=cert is not None
        else:
            t['steps_unchecked']+=1;t['unchecked_steps'].append(i)
        o.flush()
    check(A['issued']==[[s_,x] for s_,x,_ in issued],'issued '+where)
    acts={r['step']:r['forecasts'][r['action']]['actual_EVALUATOR_ONLY'] for r in trace}
    exp=[{'step':s_,'certificate':x,'observed':list(o_),'reason':k_reason(x,o_,s),'actual_EVALUATOR_ONLY':acts[s_],'wrong':x!=acts[s_]} for s_,x,o_ in (retracted or [])]
    check(A['retractions']==exp,'retractions '+where)
    d=A['diagnostics']
    if drift:check(d['drift_events']==events,'drift events '+where)
    check(d['first_alarm_step']==al.first and d['alarm_steps']==al.sets and d['resume_steps']==al.resumes,'diagnostics '+where)
    check(d['certificates_issued']==len(issued) and d['certificates_retracted']==len(exp),'issued/retracted counts '+where)
    return t


def case_job(x):
    """All requested breadth arms of one case with a shared oracle (arms with identical evidence reuse answers)."""
    idx,c,plan,tau7,arms,budget=x;t0=time.time()
    w=breadth_world(c['seed'],c['family']);o=Oracle(w.k,2**w.s,budget);out={}
    for arm in arms:
        if arm not in c['arms']:continue
        try:out[arm]={'ok':True,'counts':audit(c,arm,plan,tau7,o)}
        except (VerificationError,KeyError,IndexError,TypeError,ValueError,AssertionError) as exc:
            out[arm]={'ok':False,'first_difference':f'{type(exc).__name__}: {exc}'}
        o.flush()
    return idx,{'family':c['family'],'seed':c['seed'],'mask_rate':c['mask_rate'],'arms':out,
                'queries':o.queries,'unknown_queries':o.unknown_queries,'witness_failures':o.witness_failures,
                'regions':o.regions,'wall_informational':round(time.time()-t0,3)}


def load_cases(path):
    op=gzip.open if str(path).endswith('.gz') else open
    with op(path,'rt') as f:d=json.load(f)
    return d['cases'] if isinstance(d,dict) else d


def run(results,plan,arms,workers=4,checkpoint=None,budget=CONF_BUDGET,limit=None):
    cases=[(i,c) for i,c in enumerate(load_cases(results)) if 'k' in c and any(a in c['arms'] for a in arms)]
    if limit:cases=cases[:limit]
    view=plan_view(plan);tau7=plan['tau7']['value'] if 'tau7' in plan else view['tau7']['value']
    done={}
    if checkpoint and Path(checkpoint).exists():
        for line in open(checkpoint):
            if line.strip():r=json.loads(line);done[r['case']]=r['out']
    todo=[(i,c,view,tau7,arms,budget) for i,c in cases if i not in done]
    ck=open(checkpoint,'a') if checkpoint else None
    def save(i,out):
        done[i]=out
        if ck:ck.write(json.dumps({'case':i,'out':out})+'\n');ck.flush();os.fsync(ck.fileno())
    if workers<=1:
        for j in todo:save(*case_job(j))
    else:
        with ProcessPoolExecutor(workers) as ex:
            for f in as_completed([ex.submit(case_job,j) for j in todo]):save(*f.result())
    if ck:ck.close()
    return summarize(done,arms,budget)


def summarize(done,arms,budget):
    fams={};mism=[];wf=0;q=0;uq=0
    for i in sorted(done):
        r=done[i];wf+=r['witness_failures'];q+=r['queries'];uq+=r['unknown_queries']
        for arm,o in r['arms'].items():
            g=fams.setdefault(f"{r['family']}/{arm}",{'traces':0,'steps':0,'steps_checked':0,'steps_unchecked':0,'mismatching_traces':0,'certs':0})
            g['traces']+=1
            if not o['ok']:
                g['mismatching_traces']+=1;mism.append({'case':i,'family':r['family'],'seed':r['seed'],'mask_rate':r['mask_rate'],'arm':arm,'first_difference':o['first_difference']})
                continue
            t=o['counts'];g['steps']+=t['steps'];g['steps_checked']+=t['steps_checked'];g['steps_unchecked']+=t['steps_unchecked'];g['certs']+=t['certs']
    for g in fams.values():g['checked_fraction']=round(g['steps_checked']/g['steps'],6) if g['steps'] else None
    return {'schema':'brute.xcheck-sat-report.v1','solver':'cadical195','conf_budget_per_query':budget,'arms':list(arms),
            'wording':'second encoding by the same author (brute/xcheck_sat.py), no enumeration; not an independent audit',
            'cases':len(done),'per_family_arm':fams,'mismatching_traces':len(mism),'mismatches':mism,
            'witness_replay_failures':wf,'queries':q,'unknown_queries':uq,
            'note':'a mismatching trace stops at its first differing field; its steps are not counted as checked'}


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--results',required=True);ap.add_argument('--output',required=True)
    ap.add_argument('--arms',default=','.join(ARMS_008));ap.add_argument('--workers',type=int,default=4)
    ap.add_argument('--checkpoint');ap.add_argument('--limit',type=int);ap.add_argument('--plan',default=str(PLAN))
    a=ap.parse_args();out=Path(a.output)
    if out.exists():raise SystemExit(f'refusing to overwrite {out}')
    plan=load(a.plan);t0=time.time()
    rep=run(a.results,plan,tuple(a.arms.split(',')),a.workers,a.checkpoint,limit=a.limit)
    rep['results_file']=a.results;rep['wall_informational']=round(time.time()-t0,1)
    out.write_text(json.dumps(rep,indent=1,sort_keys=True)+'\n');print(json.dumps({k:v for k,v in rep.items() if k!='mismatches'},indent=1)[:3000])


if __name__=='__main__':main()
