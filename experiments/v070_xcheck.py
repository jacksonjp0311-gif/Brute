"""GX2'' driver (BRUTE_PLAN_009 xcheck_backend): re-derive every decision-level field of the breadth arms B5, BS7, BSC7
with the ADOPTED incremental CaDiCaL second encoding (brute/xcheck_sat_incremental.IncSolver through the adopted
experiments/v060_xcheck_incremental.IncOracle, both byte-identical to c2bf07e) - no row enumeration, no import of
brute/region.py, brute/geometry.py or any enumeration code.

Same author as the learners: "second encoding by the same author", never an independent audit.
B5 is audited by the frozen experiments/v060_xcheck.audit (unchanged). BS7/BSC7 use audit_sync below: the same flow with
the plan-009 events (E1 contradiction or R > tau x fraction; E2 the acted certificate is not compatible with the
observation; E3 one-step surprise > tau) and rules (RO: Y1k-recent while an event is recent, else Y1k; CTR: as RO, and
outside recency 'tracked-calm' when Y1k fails and t >= burn_in), recomputed from the re-derived support sets and
recomputed probabilities.
Budget: 2,000,000 conflicts per solve call; a query over budget makes the step UNCHECKED (counted, never a mismatch).
At an unchecked step the recorded action, decision and statuses are adopted (as v060_xcheck, disclosed there).
Wall caps are enforced by the study runner (scripts/run_study_009.sh, `timeout`); cases not finished at the cap are
UNCHECKED in the summary (every step), so the checked-fraction clause decides.
"""
from __future__ import annotations
import argparse,json,os,time
from math import log
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor,as_completed
from experiments.brute_common import check,load,VerificationError
from experiments.v011_independent_reference import expected_decision
from experiments.v050_reference import _Alarm12,codes_of,choose,k_reason,breadth_world,passive_actions
from experiments.v060_xcheck import audit as audit_b5,x_score,Unchecked,load_cases
from experiments.v060_xcheck_incremental import IncOracle
from brute.xcheck_sat import mask_of,CONF_BUDGET

ROOT=Path(__file__).resolve().parents[1]
PLAN=ROOT/'experiments/BRUTE_PLAN_009.json'
PLAN007=ROOT/'experiments/BRUTE_PLAN_007.json'
RULE={'BS7':'RO','BSC7':'CTR'}
ARMS=('B5','BS7','BSC7')
FAMILIES=('big6','sens3','act3','ood6s3')


def plan_view(plan):
    v=dict(load(PLAN007));v.update(plan);v.update(plan['rule_constants_frozen']);return v


def x_rule9(rule,o,N4,e4,b,lmask,cert,s_,rs,events,i,rw,burn):
    ss=events[-1] if events else None
    if ss is not None and i-ss<rw:
        if o.q(N4,*e4,'y1k',b,lmask,max(0,ss-1))==(cert,):return s_,rs,cert,'Y1k-recent'
        return 'ABSTAIN','RESYNC_AMBIGUOUS',None,'downgraded'
    if o.q(N4,*e4,'y1k',b,lmask,None)==(cert,):return s_,rs,cert,'Y1k'
    if rule=='CTR' and i>=burn:return s_,rs,cert,'tracked-calm'
    return 'ABSTAIN','RESYNC_AMBIGUOUS',None,'downgraded'


def audit_sync(c,arm,plan,tau7,o):
    """Re-derive one BS7/BSC7 trace. Returns counts; raises VerificationError at the first mismatching checked step."""
    fam=c['family'];seed=c['seed'];rate=c['mask_rate'];where=f'{fam} {seed} {rate} {arm}';rule=RULE[arm]
    lb=plan['breadth_worlds']['learner_bounds'][fam];N4=lb['family'];N5=lb['margin']
    eps=plan['open_world_reserve_epsilon'];W_=plan['window_W'];steps=plan['actions_per_case_breadth']
    A=c['arms'][arm];trace=A['trace'];frac=plan['surprise_fraction'];rw=plan['recency_window'];burn=plan['burn_in']
    w=breadth_world(seed,fam);k=w.k;s=w.s;m=2**s
    check(c['k']==k and c['s']==s and c['attested']==lb['attested'],'case header '+where)
    hidden=w.start;initial=w.observed(hidden,rate,-1);check(list(initial)==c['initial_visible'],'initial '+where)
    tau=tau7;al=_Alarm12(tau,W_,True);issued=[];retracted=None;events=[];trig=[]
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
            sc=[x_score(o,N4,N5,e4,e5,s4,s5,alarm,b) for b in range(k)]
            tiedn=sum(x==max(sc) for x in sc);a=choose(sc,pa,None);e=rec['experiment']
            check(e['scores']==sc and e['score']==sc[a] and e['tied']==(tiedn>1) and e['volumes'] is None
                  and e['rule']=='LU-R' and e['proposal']==('PROPOSED' if live else 'NO_PROPOSAL'),f'experiment {where} {i}')
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
                if cert is not None:s_,rs,cert,path=x_rule9(rule,o,N4,e4,b,mask_of(last,s),cert,s_,rs,events,i,rw,burn)
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
                t['unknown_forecasts']+=unk>0;dec[b]=cert
            checked=True
        except Unchecked:
            checked=False;a=rec['action'];dec={a:fc[a]['certificate']}
        hidden=nxt[a];obs=w.observed(hidden,rate,i)
        check(rec['observed']==list(obs),'observation '+where)
        P=fc[a]['probabilities'];cs=codes_of(obs,s)
        sp=-log(sum(P[x] for x in cs))
        if checked:
            check(abs(rec['logloss']+log(max(1e-12,P[act[a]])))<1e-8,'logloss '+where)
            check(abs(rec['min_probability']-min(min(f['probabilities']) for f in fc))<1e-12,'min prob '+where)
            check(abs(sp-rec['surprise'])<1e-8,f'surprise {where} {i}')
        cert=dec[a]
        if cert is not None and (step,cert) not in [(x[0],x[1]) for x in issued]:issued.append((step,cert,tuple(obs)))
        last=obs;was=s4;mk=mask_of(obs,s)
        try:
            if s4=='supported':m4=m4+(mk,);a4=a4+(a,);s4=o.status(N4,m4,a4)
            if s5=='supported':m5=m5+(mk,);a5=a5+(a,);s5=o.status(N5,m5,a5)
        except Unchecked:
            checked=False;s4=rec['family_status_after'];s5=rec['margin_status_after']
        if s4=='grammar_contradicted' and was=='supported':retracted=list(issued)
        R=al.push(step,rec['surprise'],s4,s5);f=[]
        if (s4=='grammar_contradicted' and was=='supported') or (R is not None and R>tau*frac):f.append('E1')
        if cert is not None and cert not in cs:f.append('E2')
        if sp>tau:f.append('E3')
        if f:events.append(step);trig.append([step,f])
        if checked:
            check((R is None and rec['residual_after'] is None) or (R is not None and abs(R-rec['residual_after'])<1e-8),f'residual {where} {i}')
            check(rec['alarm_after']==al.on,f'alarm {where} {i}')
            check(rec['family_status_after']==s4 and rec['margin_status_after']==s5,'status after '+where)
            t['steps_checked']+=1;t['certs']+=cert is not None
        else:t['steps_unchecked']+=1;t['unchecked_steps'].append(i)
        o.flush()
    check(A['issued']==[[s_,x] for s_,x,_ in issued],'issued '+where)
    actsE={r['step']:r['forecasts'][r['action']]['actual_EVALUATOR_ONLY'] for r in trace}
    exp=[{'step':s_,'certificate':x,'observed':list(o_),'reason':k_reason(x,o_,s),'actual_EVALUATOR_ONLY':actsE[s_],'wrong':x!=actsE[s_]} for s_,x,o_ in (retracted or [])]
    check(A['retractions']==exp,'retractions '+where)
    d=A['diagnostics']
    check(d['drift_events']==events and d['event_triggers']==trig,'events '+where)
    check(d['first_alarm_step']==al.first and d['alarm_steps']==al.sets and d['resume_steps']==al.resumes,'diagnostics '+where)
    check(d['certificates_issued']==len(issued) and d['certificates_retracted']==len(exp),'issued/retracted counts '+where)
    return t


def case_job(x):
    idx,c,plan,tau7,arms,budget,sym=x;t0=time.time()
    w=breadth_world(c['seed'],c['family']);o=IncOracle(w.k,2**w.s,budget,symmetry=sym);out={};wall={}
    for arm in arms:
        if arm not in c['arms']:continue
        ta=time.time()
        try:out[arm]={'ok':True,'counts':(audit_b5 if arm=='B5' else audit_sync)(c,arm,plan,tau7,o)}
        except (VerificationError,KeyError,IndexError,TypeError,ValueError,AssertionError) as exc:
            out[arm]={'ok':False,'first_difference':f'{type(exc).__name__}: {exc}'}
        wall[arm]=round(time.time()-ta,3)
    o.close()
    return idx,{'family':c['family'],'seed':c['seed'],'mask_rate':c['mask_rate'],'arms':out,
                'queries':o.queries,'unknown_queries':o.unknown_queries,'witness_failures':o.witness_failures,
                'regions':o.regions,'layers':o.layers,'wall_per_arm_informational':wall,'wall_informational':round(time.time()-t0,3)}


def select(cases,spot=None):
    """[(index, case)] of breadth cases; spot = list of [family, seed, mask] restricts to those (spot check)."""
    out=[(i,c) for i,c in enumerate(cases) if 'k' in c]
    if spot is not None:
        S={(f,s,m) for f,s,m in spot};out=[(i,c) for i,c in out if (c['family'],c['seed'],c['mask_rate']) in S]
        check(len(out)==len(S),'spot sample cases missing from results')
    return out


def read_checkpoint(path):
    done={}
    if path and Path(path).exists():
        lines=Path(path).read_text().split('\n')
        for j,line in enumerate(lines):
            if not line.strip():continue
            try:r=json.loads(line)
            except json.JSONDecodeError:
                if j==len(lines)-1:continue
                raise
            done[r['case']]=r['out']
    return done


def run(results,plan,arms,workers,checkpoint,symmetry,spot=None,budget=CONF_BUDGET,progress=True):
    cases=select(load_cases(results),spot);view=plan_view(plan);tau7=plan['tau7']['value']
    done=read_checkpoint(checkpoint)
    todo=[(i,c,view,tau7,arms,budget,symmetry) for i,c in cases if i not in done]
    todo.sort(key=lambda j:(j[1]['family']!='big6',-j[1]['mask_rate'],j[0]))   # hardest first
    with open(checkpoint,'a') as ck:
        def save(i,out):
            done[i]=out;ck.write(json.dumps({'case':i,'out':out})+'\n');ck.flush();os.fsync(ck.fileno())
            if progress:print(f"[{time.strftime('%H:%M:%S')}] case {i} {out['family']} {out['mask_rate']} wall {out['wall_informational']}s "
                              f"unk {out['unknown_queries']} ok {[v['ok'] for v in out['arms'].values()]} done {len(done)}",flush=True)
        if workers<=1:
            for j in todo:save(*case_job(j))
        else:
            with ProcessPoolExecutor(workers) as ex:
                for f in as_completed([ex.submit(case_job,j) for j in todo]):save(*f.result())


def summarize(results,plan,arms,checkpoint,spot=None,budget=CONF_BUDGET):
    """Report over ALL expected cases: a case absent from the checkpoint (not reached by the wall cap) counts every step
    of every arm as UNCHECKED."""
    cases=select(load_cases(results),spot);done=read_checkpoint(checkpoint)
    fams={};mism=[];wf=q=uq=0;missing=[]
    for i,c in cases:
        r=done.get(i)
        if r is None:missing.append(i)
        else:wf+=r['witness_failures'];q+=r['queries'];uq+=r['unknown_queries']
        for arm in arms:
            if arm not in c['arms']:continue
            g=fams.setdefault(f"{c['family']}/{arm}",{'traces':0,'steps':0,'steps_checked':0,'steps_unchecked':0,'mismatching_traces':0,'certs':0,'traces_not_reached':0})
            g['traces']+=1;n=len(c['arms'][arm]['trace'])
            if r is None:g['traces_not_reached']+=1;g['steps']+=n;g['steps_unchecked']+=n;continue
            o=r['arms'][arm]
            if not o['ok']:
                g['mismatching_traces']+=1;g['steps']+=n
                mism.append({'case':i,'family':c['family'],'seed':c['seed'],'mask_rate':c['mask_rate'],'arm':arm,'first_difference':o['first_difference']});continue
            t=o['counts'];g['steps']+=t['steps'];g['steps_checked']+=t['steps_checked'];g['steps_unchecked']+=t['steps_unchecked'];g['certs']+=t['certs']
    for g in fams.values():g['checked_fraction']=round(g['steps_checked']/g['steps'],6) if g['steps'] else None
    per_family={f:sum(g['steps_checked'] for k_,g in fams.items() if k_.startswith(f+'/')) for f in FAMILIES}
    return {'schema':'brute.xcheck-sat-incremental-report.v2','solver':'cadical195','conf_budget_per_query':budget,'arms':list(arms),
            'wording':'second encoding by the same author (brute/xcheck_sat_incremental.py, adopted), no enumeration; not an independent audit',
            'cases_expected':len(cases),'cases_done':len(cases)-len(missing),'cases_not_reached':missing,'per_family_arm':fams,
            'checked_steps_per_family':per_family,'mismatching_traces':len(mism),'mismatches':mism,'witness_replay_failures':wf,
            'queries':q,'unknown_queries':uq,'note':'a mismatching trace stops at its first differing field; its steps are not counted as checked'}


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--results',required=True);ap.add_argument('--checkpoint',required=True)
    ap.add_argument('--output');ap.add_argument('--arms',default=','.join(ARMS));ap.add_argument('--workers',type=int,default=4)
    ap.add_argument('--no-symmetry',action='store_true');ap.add_argument('--spot',help='SPOT_SAMPLE_009.json: restrict to the drawn cases')
    ap.add_argument('--summarize-only',action='store_true');ap.add_argument('--plan',default=str(PLAN))
    a=ap.parse_args();plan=load(a.plan);arms=tuple(a.arms.split(','));sym=not a.no_symmetry
    spot=None
    if a.spot:
        S=load(a.spot);spot=[[f,s_,m_] for f,lst in S['cases'].items() for s_,m_ in lst] if 'cases' in S else S['spot']
    if not a.summarize_only:run(a.results,plan,arms,a.workers,a.checkpoint,sym,spot)
    if a.output:
        out=Path(a.output)
        if out.exists():raise SystemExit(f'refusing to overwrite {out}')
        rep=summarize(a.results,plan,arms,a.checkpoint,spot);rep['symmetry_breaking']=sym;rep['spot_sample']=a.spot;rep['results_file']=a.results
        out.write_text(json.dumps(rep,indent=1,sort_keys=True)+'\n')
        print(json.dumps({k:v for k,v in rep.items() if k not in ('mismatches','per_family_arm')},indent=1)[:3000])


if __name__=='__main__':main()
