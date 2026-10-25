"""GMC runner for BRUTE_PLAN_008 (reporting only; counts never feed any decision).

Sample (plan modelcount_sample_block): the A5 trace of every 2x2 in_family_original case in the given RESULTS file,
every step with step % 4 == 0 and step > burn_in (8); breadth (--breadth): the B5 trace, step % 8 == 0 and step > 8,
reported only (R_counts_breadth). The evidence at sampled step t is the initial mask plus the first t (action, mask)
pairs of the trace (the region before the step-t action is taken).

Per sampled step: pyganak counts |R_t|, pairs(a), fibre(a, c) (brute/modelcount.py) under the budget rule
(10 s per count, 120 s of counter time per case, study-wide counter wall-clock cap 6 h measured from the start of the
run); the blocking-clause count (CaDiCaL, cap 10^4) is always run as the independent check; pyapproxmc (Inferred) is
run only where |R_t| is UNKNOWN. UNKNOWN is recorded with its reason and never imputed.
Checkpoint: JSONL, one line per case, fsync'd; a rerun with the same --checkpoint resumes.
"""
from __future__ import annotations
import argparse, gzip, json, multiprocessing as mp, os, sys, time
from collections import Counter as _C
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from brute.modelcount import count_jobs, ganak_counts, blocking_count, approx_count, PER_COUNT_S, PER_CASE_S, BLOCK_CAP
from brute.xcheck_sat import mask_of
PLAN=Path(__file__).with_name('BRUTE_PLAN_008.json')
PLAN7=Path(__file__).with_name('BRUTE_PLAN_007.json')
TOTAL_S=6*3600.0
APPROX_TIMEOUT_S=30.0
SCHEMA='brute.modelcount-report.v1'


def _approx_child(conn,nv,cl,proj):
    try:conn.send((approx_count(nv,cl,proj),None))
    except Exception as exc:conn.send((None,f'error: {type(exc).__name__}: {exc}'))


def approx_guarded(nv,cl,proj,timeout=APPROX_TIMEOUT_S):
    a,b=mp.get_context('fork').Pipe(duplex=False);p=mp.get_context('fork').Process(target=_approx_child,args=(b,nv,cl,proj),daemon=True)
    p.start();b.close()
    try:
        if a.poll(timeout):return a.recv()
        return None,f'timeout ({timeout:g} s)'
    finally:
        if p.is_alive():p.kill()
        p.join()


def load_cases(path):
    op=gzip.open if str(path).endswith('.gz') else open
    with op(path,'rt') as f:return json.load(f)['cases']


def sample_steps(trace,every,burn_in):
    return [r['step'] for r in trace if r['step']%every==0 and r['step']>burn_in]


def case_job(args):
    """Two phases inside the per-case counter budget (fixed on smoke data before the source freeze, disclosed):
    phase 1 counts |R_t| at every sampled step (the gated quantity), phase 2 the pairs/fibre counts step by step."""
    c,arm,n,k,m,every,burn_in,global_deadline=args
    tr=c['arms'][arm]['trace'];s=len(c['initial_visible'])
    masks=[mask_of(c['initial_visible'],s)];acts=[];want=set(sample_steps(tr,every,burn_in));ev=[]
    for rec in tr:
        if rec['step'] in want:ev.append((rec['step'],list(masks),list(acts)))
        acts.append(rec['action']);masks.append(mask_of(rec['observed'],s))
    spent=0.;rows=[];jobs_by=[]
    def counted(jobs):
        nonlocal spent
        deadline=min(time.time()+max(0.,PER_CASE_S-spent),global_deadline)
        t0=time.time();res=ganak_counts(jobs,PER_COUNT_S,deadline);spent+=time.time()-t0;return res
    for st,mk,ac in ev:
        jobs=count_jobs(n,k,m,mk,ac);jobs_by.append(jobs);res=counted(jobs[:1]);R=res[('R',)]
        row={'step':st,'evidence_pairs':len(ac),'R':R['count'],'R_reason':R['reason'],'R_seconds_informational':R['seconds']}
        bc,cens,why=blocking_count(n,k,m,mk,ac,BLOCK_CAP)
        row['blocking']=bc;row['blocking_censored']=cens;row['blocking_reason']=why
        row['agree']=None if (bc is None or R['count'] is None) else (int(R['count'])==bc)
        if R['count'] is None:
            est,err=approx_guarded(jobs[0][1],jobs[0][2],jobs[0][3]);row['approx_R_Inferred']=est;row['approx_reason']=err
        rows.append(row)
    for row,jobs in zip(rows,jobs_by):
        res=counted(jobs[1:])
        row['pairs']={str(a):res[('pairs',a)]['count'] for a in range(k)}
        row['fibre']={f'{a},{cc}':res[('fibre',a,cc)]['count'] for a in range(k) for cc in range(m)}
        unk=[v['reason'] for v in res.values() if v['count'] is None]
        row['unknown_fibre_counts']=len(unk);row['unknown_fibre_reasons']=sorted(_C(unk).items())
        sums={}
        for a in range(k):
            fs=[row['fibre'][f'{a},{cc}'] for cc in range(m)];pr=row['pairs'][str(a)]
            if row['R'] is None or pr is None or any(x is None for x in fs):sums[str(a)]=None
            else:
                tot=sum(int(x) for x in fs);sums[str(a)]={'sum':str(tot),'ok':tot>=int(row['R']) and tot==int(pr)}
        row['sum_check']=sums
    return {'key':f"{c['block']}/{c['family']}/{c['seed']}/{c['mask_rate']}",'family':c['family'],'seed':c['seed'],
            'mask_rate':c['mask_rate'],'arm':arm,'n':n,'k':k,'m':m,'steps':rows,'counter_seconds_informational':round(spent,3)}


def summarize(recs,gated):
    S=[r for c in recs for r in c['steps']]
    counted=sum(r['R'] is not None for r in S);comp=[r for r in S if r['agree'] is not None]
    dis=[(c['key'],r['step']) for c in recs for r in c['steps'] if r['agree'] is False]
    sc=[v for r in S for v in r['sum_check'].values() if v is not None];viol=[v for v in sc if not v['ok']]
    unk=_C(r['R_reason'] for r in S if r['R'] is None)
    out={'cases':len(recs),'sampled_steps':len(S),'R_counted':counted,
         'R_coverage':round(counted/len(S),6) if S else None,
         'blocking_exact':sum(r['blocking'] is not None for r in S),
         'blocking_censored':sum(bool(r['blocking_censored']) for r in S),
         'compared_steps':len(comp),'disagreements':len(dis),'disagreement_list':dis,
         'sum_checks_evaluated':len(sc),'sum_check_violations':len(viol),
         'sum_checks_not_evaluable':sum(v is None for r in S for v in r['sum_check'].values()),
         'R_unknown_reasons':sorted(unk.items()),
         'approx_estimates_Inferred':sum(r.get('approx_R_Inferred') is not None for r in S)}
    if gated:
        out['GMC']={'i_coverage_ge_0.95':out['R_coverage'] is not None and out['R_coverage']>=0.95,
                    'ii_zero_disagreements':len(dis)==0,'iii_zero_sum_violations':len(viol)==0}
        out['GMC']['PASS']=all(out['GMC'].values())
    return out


def run(a):
    plan=json.load(open(PLAN));burn=plan['burn_in']
    if isinstance(burn,dict):burn=burn.get('value',8)
    cases=load_cases(a.results);args=[];gdl=(a.budget_start or time.time())+TOTAL_S
    if a.breadth:
        lb=json.load(open(PLAN7))['breadth_worlds']['learner_bounds']
        for c in cases:
            if 'k' in c and 'B5' in c['arms']:
                args.append((c,'B5',lb[c['family']]['family'],c['k'],2**c['s'],8,burn,gdl))
    else:
        fams=set(plan['in_family_original_2x2'])
        for c in cases:
            if 'k' not in c and c['family'] in fams and 'A5' in c['arms']:args.append((c,'A5',4,2,4,4,burn,gdl))
    if a.limit:args=args[:a.limit]
    ck=Path(a.checkpoint);done={}
    if ck.exists():
        for line in ck.read_text().splitlines():
            if line.strip():r=json.loads(line);done[r['key']]=r
    todo=[x for x in args if f"{x[0]['block']}/{x[0]['family']}/{x[0]['seed']}/{x[0]['mask_rate']}" not in done]
    print(f'cases {len(args)} done {len(done)} todo {len(todo)}',flush=True)
    with open(ck,'a') as f, ProcessPoolExecutor(a.workers,mp_context=mp.get_context('fork')) as ex:
        for i,fu in enumerate(as_completed([ex.submit(case_job,x) for x in todo])):
            r=fu.result();done[r['key']]=r;f.write(json.dumps(r,sort_keys=True)+'\n');f.flush();os.fsync(f.fileno())
            if i%10==0:print(i+1,r['key'],r['counter_seconds_informational'],flush=True)
    recs=[done[k] for k in sorted(done)]
    from experiments.brute_common import sha as _sha
    rep={'schema':SCHEMA,'results_file':str(a.results),'results_sha256':_sha(a.results),'mode':'breadth (reported only)' if a.breadth else '2x2 GMC sample',
         'counter':'pyganak==2.8.0 (Exact: documents itself as an exact model counter)',
         'independent_check':f'blocking-clause count on brute/xcheck_sat.XRegion (CaDiCaL), symmetry=True, cap {BLOCK_CAP}',
         'fallback':'pyapproxmc==4.4.0 eps 0.8 delta 0.2 (Inferred), only where |R_t| is UNKNOWN',
         'budget':{'per_count_s':PER_COUNT_S,'per_case_s':PER_CASE_S,'total_s':TOTAL_S,'budget_start_epoch':a.budget_start},
         'use':'reporting only; never used by any decision',
         'summary':summarize(recs,not a.breadth),'cases':recs}
    out=Path(a.output)
    if out.exists():raise SystemExit(f'refusing to overwrite {out}')
    out.write_text(json.dumps(rep,indent=1,sort_keys=True)+'\n');print(json.dumps(rep['summary'],indent=1))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--results',required=True);p.add_argument('--output',required=True)
    p.add_argument('--checkpoint',required=True);p.add_argument('--workers',type=int,default=4)
    p.add_argument('--breadth',action='store_true');p.add_argument('--limit',type=int)
    p.add_argument('--budget-start',type=float,help='epoch seconds at which the study-wide 6 h counting cap started (shared by the 2x2 and breadth invocations)')
    run(p.parse_args())
