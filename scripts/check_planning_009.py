"""GP1 (iv) certification isolation and GP1 (v) count audit for study BRUTE-070-SYNCPLAN-009.

(iv) every planning case: P7's recorded (action, observation) sequence is replayed through the FROZEN A5 learner
     (brute.region_learner.RegionBruteLearner, the study-007 A5 constructor, policy LU-R, production conf budget); at each
     step the replayed learner's forecasts for BOTH actions are compared with the recorded taken and counterfactual
     forecasts on status, reason, certificate, public certificate and probabilities (12 d.p., the recorded rounding).
     The replayed learner's own experiment() is called each step (as in the A5 trajectory) and its action ignored.
(v)  random.Random(20261028).sample over all planned decisions (cases in RESULTS order, steps in order), 200 decisions;
     each is recounted by the OTHER source on its recorded region (n, masks, actions): enumeration-sourced -> the frozen
     modelcount ganak fibre counts (per-count limit = 30 s, deadline 30 s); ganak-sourced -> exhaustive enumeration with
     NO machine cap and a 30 s limit. Both one-step count matrices are compared exactly; a recount that does not
     complete in 30 s is 'not both complete'. Each recount runs in its own forked non-daemonic child (hard kill at 35 s).
Writes results/study-009/PLANNING_AUDIT_009.json (refuses to overwrite)."""
from __future__ import annotations
import argparse,json,multiprocessing as mp,random,time
from pathlib import Path
from brute.region_learner import RegionBruteLearner
from brute.core.learner import ScopeAttestation
from brute.planner import enumerate_pairs,ganak_fibres
import experiments.brute_study_007 as S7
from bgr89.worlds import actions
from experiments.brute_common_009 import PLAN,load,plan_view,plan006_keys
from experiments.brute_study_009 import _base
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results/study-009/PLANNING_AUDIT_009.json'
FIELDS=('status','reason','certificate','public_certificate','probabilities')
LIMIT=30.0
SAMPLE=200
RNG=20261028


def replay(c,plan):
    v=plan_view(plan);p6=plan006_keys(v);tau6=plan['tau6']['value']
    att=ScopeAttestation(p6['declared_family'],'evaluator','synthetic world built inside the family') if c['attested'] else None
    L=RegionBruteLearner(*_base(p6),tau6,att,policy='LU-R');L.initialize(tuple(c['initial_visible']))
    tr=c['arms']['P7']['trace'];bad=[]
    pas=actions(c['seed'],p6['actions_per_case'])
    for i,rec in enumerate(tr):
        check_pa=pas[i]==rec['passive_action']
        L.experiment(rec['passive_action']);a=rec['action'];fs=(L.predict(0),L.predict(1))
        for which,f,r in (('taken',fs[a],rec),('counterfactual',fs[1-a],rec['counterfactual'])):
            d=S7._fc(f,None)
            for k in FIELDS:
                if d[k]!=r[k]:bad.append({'step':rec['step'],'forecast':which,'field':k,'recorded':r[k],'replayed':d[k]})
        if not check_pa:bad.append({'step':rec['step'],'field':'passive_action'})
        L.record_issued(fs[a]);L.observe(a,tuple(rec['observed']))
        if bad:break
    L.close();return bad


def _child(conn,src,n,masks,acts):
    try:
        if src=='enumeration':
            c,r=ganak_fibres(n,masks,acts,time.time()+LIMIT,per_count=LIMIT);conn.send(('ganak',c,r))
        else:
            c,_,info=enumerate_pairs(n,masks,acts,cap=10**12,seconds=LIMIT);conn.send(('enumeration',c,None if c is not None else info))
    except Exception as exc:conn.send((None,None,f'error: {type(exc).__name__}: {exc}'))
    finally:conn.close()


def recount_all(items,workers):
    ctx=mp.get_context('fork');todo=list(enumerate(items));live={};out={}
    while todo or live:
        while todo and len(live)<workers:
            j,it=todo.pop(0);a,b=ctx.Pipe(duplex=False)
            p=ctx.Process(target=_child,args=(b,it['source'],it['region']['n'],it['region']['masks'],it['region']['actions']),daemon=False)
            p.start();b.close();live[j]=(p,a,time.time())
        for j,(p,a,t0) in list(live.items()):
            got=None
            if a.poll(0.05):
                try:got=a.recv()
                except EOFError:got=(None,None,'error: recount child died')
            elif time.time()-t0>LIMIT+5:got=(None,None,f'recount exceeded {LIMIT:g} s (killed)')
            if got is not None:
                if p.is_alive():p.kill()
                p.join();a.close();out[j]=got+(round(time.time()-t0,2),);del live[j]
    return [out[j] for j in range(len(items))]


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--results',required=True);ap.add_argument('--output',default=str(OUT))
    ap.add_argument('--workers',type=int,default=2);ap.add_argument('--sample',type=int,default=SAMPLE);a=ap.parse_args()
    out=Path(a.output)
    if out.exists():raise SystemExit(f'refusing to overwrite {out}')
    plan=load(PLAN);cases=json.loads(Path(a.results).read_text())['cases'];t0=time.time()
    rep={'schema':'brute.planning-audit.v1','study':plan['study'],'results_file':a.results,'cases':len(cases)}
    mism=[]
    for c in cases:
        b=replay(c,plan)
        if b:mism.append({'family':c['family'],'seed':c['seed'],'mask_rate':c['mask_rate'],'first':b[0]})
    rep['iv_replay']={'cases_replayed':len(cases),'mismatching_cases':len(mism),'mismatches':mism,'fields':list(FIELDS),
                      'passed':not mism and len(cases)>0}
    planned=[]
    for ci,c in enumerate(cases):
        for rec in c['arms']['P7']['trace']:
            P=rec.get('planner')
            if P and P.get('planned'):planned.append({'case':ci,'family':c['family'],'seed':c['seed'],'mask_rate':c['mask_rate'],
                                                      'step':rec['step'],'source':P['source'],'region':P['region'],'counts':P['counts']})
    idx=random.Random(RNG).sample(range(len(planned)),min(a.sample,len(planned)));items=[planned[i] for i in idx]
    res=recount_all(items,a.workers);rows=[];both=dis=0
    for it,(src2,c2,why,dt) in zip(items,res):
        ok=c2 is not None;agree=ok and c2==it['counts'];both+=ok;dis+=ok and not agree
        rows.append({k:it[k] for k in ('family','seed','mask_rate','step','source')}|{'other_source':src2,'both_complete':ok,
                    'agree':agree if ok else None,'other_counts':c2,'recorded_counts':it['counts'],'reason':why,'seconds_informational':dt})
    rep['v_count_audit']={'planned_decisions':len(planned),'sampled':len(items),'rng':f'random.Random({RNG}).sample','limit_s':LIMIT,
                          'both_complete':both,'disagreements':dis,'passed':len(items)==a.sample and dis==0 and both>=100,
                          'by_source':{s:sum(r['source']==s for r in rows) for s in ('enumeration','ganak')},'rows':rows}
    rep['wall_informational']=round(time.time()-t0,1)
    out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(rep,indent=1,sort_keys=True)+'\n')
    print(json.dumps({'iv':{k:v for k,v in rep['iv_replay'].items() if k!='mismatches'}|{'first':mism[:2]},
                      'v':{k:v for k,v in rep['v_count_audit'].items() if k!='rows'}}))
if __name__=='__main__':main()
