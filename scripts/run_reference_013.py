"""G11 + GS_ref driver for study-013 (2x2 via the frozen v0100_reference audit; GS_ref via experiments/v0110_reference.audit_transfer_case) (BRUTE_PLAN_013 samples.g11_*, criteria.G11_second_implementation, GS_ref).

One stream (g11: arms J10, SP8). Order: every trace of the mandatory sample (scripts/check_seeds_013.g11_mandatory,
216 cases, all masks) first, then the mutation test, then the event mandatory_done (G_RT: the mandatory part ends
here), then the GS_ref transfer audit of every transfer case (--transfer-results; implementation reading, disclosed in
BRUTE_DEVIATIONS_013: GS_ref runs inside the g11 stream), then the FIXED optional list (g11_optional, 54 cases), then
the stamp optional_done (all optional traces audited) or stopped_own_budget (written by --summarize-only when the
budget stop came first). Every audited (case, arm) trace is appended to --checkpoint (fsync), so a budget stop leaves partial
evidence; a restart skips audited traces. --summarize-only writes the report from the checkpoint (unreached traces are
reported, not failed).

Mutation test (2x2 stream): experiments/v0100_reference.mutate(mandatory cases, 20, random.Random(20261026),
j10=4, act=4) and an audit of the 20 injected traces only. Implementation reading (disclosed): a trace that was not
injected is byte-identical to the original (asserted), so its audit result equals the unmutated audit result (Exact) and
is not recomputed; flagged_not_injected is therefore 0 by construction and the original mismatches are carried over.
"""
from __future__ import annotations
import argparse,hashlib,json,os,time,copy
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor,as_completed
from experiments import v0100_reference as R
from experiments import v0110_reference as R1
from experiments.brute_common import load,check
from experiments.brute_common_009 import repair_torn_tail
from scripts.check_seeds_013 import g11_mandatory,g11_optional

ROOT=Path(__file__).resolve().parents[1]
ARMS={'2x2':('J10','SP8')}
MUTATE=20


def ckey(c):return f"{c['family']}/{c['seed']}/{c['mask_rate']}"


def mandatory_keys(plan,block):
    M=g11_mandatory(plan);return {f'{f}/{s}/{m}' for f,ss in M.items() for s in ss for m in plan['mask_rates']}


def optional_keys(plan,block):
    M=g11_optional(plan);return {f'{f}/{s}/{m}' for f,ss in M.items() for s in ss for m in plan['mask_rates']}


def read_ck(path):
    traces={};events={}
    if Path(path).exists():
        for line in Path(path).read_text().split('\n'):
            if not line.strip():continue
            r=json.loads(line)
            if 'event' in r:events[r['event']]=r
            else:traces[(r['case'],r['arm'])]=r
    return traces,events


def _audit(x):
    key,c,arms,view,tau6=x;out=[]
    for a in arms:
        if a not in c['arms']:continue
        t0=time.time();ok,msg,t=R.audit_trace(c,a,view,tau6)
        out.append({'case':key,'arm':a,'ok':ok,'first_difference':msg,'counts':t,
                    'steps':len(c['arms'][a]['trace']),'wall_informational':round(time.time()-t0,3)})
    return out


def _append(fh,rec):fh.write(json.dumps(rec,sort_keys=True)+'\n');fh.flush();os.fsync(fh.fileno())


def audit_many(cases,arms,view,tau6,workers,fh,done,log):
    jobs=[(ckey(c),c,tuple(a for a in arms if (ckey(c),a) not in done),view,tau6) for c in cases]
    jobs=[j for j in jobs if j[2]]
    if workers<=1:it=(_audit(j) for j in jobs)
    else:
        ex=ProcessPoolExecutor(workers);futs=[ex.submit(_audit,j) for j in jobs];it=(f.result() for f in as_completed(futs))
    n=0
    for out in it:
        for r in out:_append(fh,r);done[(r['case'],r['arm'])]=r
        n+=1
        if n%10==0 or n==len(jobs):log(f'audited {n}/{len(jobs)} cases')
    if workers>1:ex.shutdown()


def _taudit(x):
    key,c,plan=x;t0=time.time();ok,msg=R1.audit_transfer_case(c,plan)
    return [{'case':key,'arm':'TRANSFER','ok':ok,'first_difference':msg,'counts':None,'steps':c['steps'],'wall_informational':round(time.time()-t0,3)}]


def audit_transfer(tcases,plan,workers,fh,done,log):
    jobs=[(ckey(c),c,plan) for c in tcases if (ckey(c),'TRANSFER') not in done]
    if workers<=1:it=(_taudit(j) for j in jobs)
    else:
        ex=ProcessPoolExecutor(workers);futs=[ex.submit(_taudit,j) for j in jobs];it=(f.result() for f in as_completed(futs))
    n=0
    for out in it:
        for r in out:_append(fh,r);done[(r['case'],r['arm'])]=r
        n+=1
        if n%24==0 or n==len(jobs):log(f'transfer audited {n}/{len(jobs)} cases')
    if workers>1:ex.shutdown()


def mutation(mand,arms,view,tau6,base,k=MUTATE):
    mc,inj=R.mutate(mand,k,arms=arms)
    check(len(inj)==k,'mutation count')
    for i,c in enumerate(mand):
        for a in arms:
            if a in c['arms'] and (i,a) not in inj:check(mc[i]['arms'][a]==c['arms'][a],'uninjected trace changed')
            if (i,a) in inj:check(mc[i]['arms'][a]!=c['arms'][a],'injection did not change the trace')
    det=[]
    for i,a in sorted(inj):
        ok,msg,_=R.audit_trace(mc[i],a,view,tau6)
        fields=sorted({k for r0,r1 in zip(c_tr(mand[i],a),c_tr(mc[i],a)) for k in set(r0)|set(r1) if r0.get(k)!=r1.get(k)})
        det.append({'case':ckey(mc[i]),'arm':a,'detected':not ok,'first_difference':msg,'injected_fields':fields})
    j9ch=sum(1 for d in det if d['arm']=='J10' and set(d['injected_fields'])&{'hull_union','hull_unknown','certificate'})
    acta=sum(1 for d in det if 'action' in d['injected_fields'])
    base_bad={(ckey(mand[i]),a) for i,a in inj if not base[(ckey(mand[i]),a)]['ok']}
    return {'event':'mutation','injected':len(inj),'injected_j10':sum(a=='J10' for _,a in inj),'injected_sp8':sum(a=='SP8' for _,a in inj),
            'detected_injected':sum(d['detected'] for d in det),'injected_on_already_mismatching_trace':len(base_bad),
            'flagged_not_injected':0,'flagged_not_injected_basis':'Exact: uninjected traces asserted byte-identical',
            'injected_j10_cert_or_hull_fields':j9ch,'injected_action':acta,
            'rng':'random.Random(20261026)','details':det,
            'passed':all(d['detected'] for d in det) and len(inj)==k and len({d['case']+d['arm'] for d in det})==k and j9ch>=4 and acta>=4}


def c_tr(c,a):
    """flattened per-step records of one arm (forecast dicts merged so a nested certificate change is visible)."""
    out=[]
    for r in c['arms'][a]['trace']:
        f=dict(r)
        if 'forecasts' in r and r.get('action') is not None and isinstance(r['forecasts'],list):
            f.update({k:v for k,v in r['forecasts'][r['action']].items() if k in ('certificate','status')})
        out.append(f)
    return out


def summarize(block,cases,plan,traces,events,results,src,M,O,tcases=None,tresults=None):
    """mandatory = the 216-case sample; G_RT reads events.mandatory_done (after the mutation test); 'rest' = the FIXED
    optional list (54 cases); transfer = GS_ref over every transfer case."""
    arms=ARMS[block];exp={'mandatory':[],'rest':[]}
    for c in cases:
        for a in arms:
            if a in c['arms'] and (ckey(c) in M or ckey(c) in O):exp['mandatory' if ckey(c) in M else 'rest'].append((ckey(c),a))
    rep={'schema':'brute.second-implementation-013.v1','study':plan['study'],'block':block,'arms':list(arms),
         'wording':'second implementation by the same author, no brute import; not an independent or third-party audit',
         'source_sha256':src,'results_file':str(results),'results_sha256':hashlib.sha256(Path(results).read_bytes()).hexdigest(),
         'tau6':plan['tau6']['value'],'jump_window_K':R.plan_view(plan)['jump_window_K']}
    for part,keys in exp.items():
        got=[traces[k] for k in keys if k in traces];bad=[g for g in got if not g['ok']]
        rep[part]={'traces_expected':len(keys),'traces_audited':len(got),'traces_not_reached':len(keys)-len(got),
                   'mismatching_traces':len(bad),'mismatches':bad,'per_arm':{a:{'expected':sum(k[1]==a for k in keys),
                   'audited':sum(g['arm']==a for g in got),'mismatching':sum(g['arm']==a and not g['ok'] for g in bad)} for a in arms}}
    rep['mandatory_complete']=rep['mandatory']['traces_not_reached']==0
    rep['mandatory_samples_present']=sorted({k[0] for k in exp['mandatory']})==sorted(M)
    rep['events']={k:{x:y for x,y in v.items() if x!='details'} for k,v in events.items()}
    if 'mutation' in events:rep['mutation_test']=events['mutation']
    hull={'steps':0,'hull_steps':0,'hull_downgrades':0,'hull_unauditable':0,'hull_nonvacuous':0}
    for (ck,a),g in traces.items():
        if a=='J10' and g['counts'] and isinstance(g['counts'],dict):
            for k in hull:hull[k]+=g['counts'].get(k,0)
    rep['j10_support']=hull
    rep['rest_mismatch_fails_g11']=True;rep['optional_fixed_expected_cases']=len(O)
    rep['optional_stamp']='optional_done' if 'optional_done' in events else 'stopped_own_budget'
    if tcases is not None:
        keys=[ckey(c) for c in tcases];got=[traces[(k,'TRANSFER')] for k in keys if (k,'TRANSFER') in traces];bad=[g for g in got if not g['ok']]
        rep['transfer_audit']={'results_file':str(tresults),'results_sha256':hashlib.sha256(Path(tresults).read_bytes()).hexdigest(),
            'cases_expected':len(keys),'cases_audited':len(got),'cases_not_reached':len(keys)-len(got),'mismatching_cases':len(bad),'mismatches':bad,
            'done_event':'transfer_done' in events}
    return rep


def main(argv=None):
    ap=argparse.ArgumentParser();ap.add_argument('--block',choices=ARMS,default='2x2');ap.add_argument('--results',required=True)
    ap.add_argument('--checkpoint',required=True);ap.add_argument('--output',required=True);ap.add_argument('--workers',type=int,default=2)
    ap.add_argument('--mutate',type=int,default=MUTATE);ap.add_argument('--summarize-only',action='store_true')
    ap.add_argument('--transfer-results',default=None,help='transfer block RESULTS.json (GS_ref audit after mandatory_done)')
    ap.add_argument('--no-rest',action='store_true',help='smoke only: stop after the mandatory sample')
    ap.add_argument('--smoke-all-mandatory',action='store_true',help='smoke only (seeds 6190001-6190030): treat every case as mandatory')
    a=ap.parse_args(argv);out=Path(a.output)
    if out.exists():raise SystemExit(f'refusing to overwrite {out}')
    plan=load(R1.PLAN);view=R.plan_view(plan);tau6=plan['tau6']['value'];arms=ARMS[a.block]
    src={f:hashlib.sha256((ROOT/'experiments'/f).read_bytes()).hexdigest() for f in ('v0100_reference.py','v0110_reference.py')}
    def log(m):print(f"[{time.strftime('%H:%M:%S')}] g11_{a.block}: {m}",flush=True)
    cases=json.loads(Path(a.results).read_text())['cases'];M=mandatory_keys(plan,a.block)
    if a.smoke_all_mandatory:
        lo,hi=plan['smoke_seeds']['range'];check(all(lo<=c['seed']<=hi for c in cases),'--smoke-all-mandatory on non-smoke seeds');M={ckey(c) for c in cases}
    O=optional_keys(plan,a.block)
    if a.smoke_all_mandatory:O=set()
    mand=[c for c in cases if ckey(c) in M];rest=[c for c in cases if ckey(c) in O]
    tcases=json.loads(Path(a.transfer_results).read_text())['cases'] if a.transfer_results else None
    Path(a.checkpoint).parent.mkdir(parents=True,exist_ok=True);repair_torn_tail(a.checkpoint)
    traces,events=read_ck(a.checkpoint)
    if not a.summarize_only:
        with open(a.checkpoint,'a') as fh:
            if 'start' not in events:events['start']={'event':'start','t':time.time()};_append(fh,events['start'])
            log(f'mandatory sample: {len(mand)} cases (expected {len(M)}), rest {len(rest)} cases')
            audit_many(mand,arms,view,tau6,a.workers,fh,traces,log)
            if a.mutate and 'mutation' not in events:
                events['mutation']=mutation(mand,arms,view,tau6,traces,a.mutate);_append(fh,events['mutation'])
                log(f"mutation {events['mutation']['detected_injected']}/{events['mutation']['injected']} passed={events['mutation']['passed']}")
            if 'mandatory_done' not in events:
                events['mandatory_done']={'event':'mandatory_done','t':time.time(),'wall_since_start':round(time.time()-events['start']['t'],1)}
                _append(fh,events['mandatory_done']);log(f"mandatory done ({events['mandatory_done']['wall_since_start']} s since first start)")
            if tcases is not None:
                audit_transfer(tcases,plan,a.workers,fh,traces,log)
                if 'transfer_done' not in events:events['transfer_done']={'event':'transfer_done','t':time.time()};_append(fh,events['transfer_done'])
            if not a.no_rest:
                audit_many(rest,arms,view,tau6,a.workers,fh,traces,log)
                if 'optional_done' not in events and all((ckey(c),x) in traces for c in rest for x in arms if x in c['arms']):
                    events['optional_done']={'event':'optional_done','t':time.time(),'optional_cases':len(rest)};_append(fh,events['optional_done'])
    rep=summarize(a.block,cases,plan,traces,events,a.results,src,M,O,tcases,a.transfer_results)
    out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(rep,indent=1,sort_keys=True)+'\n')
    log(json.dumps({'mandatory':{k:v for k,v in rep['mandatory'].items() if k!='mismatches'},'rest_audited':rep['rest']['traces_audited'],'optional_stamp':rep['optional_stamp'],'transfer':{k:v for k,v in rep.get('transfer_audit',{}).items() if k!='mismatches'},
                    'mutation':{k:v for k,v in rep.get('mutation_test',{}).items() if k!='details'}}))


if __name__=='__main__':main()
