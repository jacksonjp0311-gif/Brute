"""GS_ref audit for study-045 (BRUTE_PLAN_045 GS_ref / GNF_bound; pre-run deviation #163 item 4 fixes the scope; new file, the
scripts/run_reference_044.py logic with the frozen scripts/run_reference_041.py audit() imported unchanged): experiments/
v0310_reference.py and v0300_reference.py (plain CNF, CaDiCaL, no shared code with brute/) on the decided records of one block
(default main). Per record it rebuilds the final trace (worlds_043 dispatch, eps 0, plus the recorded extra actions; readings by
simulating the true machine) and recomputes n_min, the model's consistency and s1, every stored future / start verdict,
completeness at the record's bound and the stop label. Bound: A16_N N = the family size; A16_nf1 / A16_nf2 N = n_min + delta
(the bounded claim; a reference ID / IDF there certifies uniqueness among machines with at most n_min + delta states only).
A K_spent stop is audited as the AMB it ended on. Unknown records are 'not_reached'. Each record also gets future_match_ref
(the model from s1 versus the true machine from its true final state).
SCOPE (#163 item 4, declared before the freeze): one total wall budget BUDGET_S = 1800 s for the audits, 8 worker processes
(multiprocessing.Pool, apply_async, FIFO); audit order A16_nf2, A16_nf1, A16_N; within an arm control first, then scale16, each by
seed. At the budget the pool is terminated; records not finished are 'not_audited' and listed. Bucketing: on an nf arm a stop
mismatch [stop, ID, WRONG] (reference says the model is not the truth) is a MISFIRE (counted for GNF_misfire), not a reference
mismatch; every other mismatch counts. Then 20 seeded mutations (stop, n_min, one verdict, s1; random.Random(450)) over the audited
decided records must each be detected.
PASS iff 0 counted mismatches on audited records, every decided A16_nf2 record of the block audited, and 20/20 mutations detected
(vacuous pass stated if 0 decided). 'complete' says whether every decided record of every arm was audited.
Writes <study>/REFERENCE_045.json (refuses overwrite).
  PYTHONPATH=. python scripts/run_reference_045.py results/study-045/main [--workers 8] [--block main] [--budget 1800]"""
import argparse,copy,json,random,sys,time
from multiprocessing import Pool
from pathlib import Path
from time import perf_counter
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common import load,write_new,sha
from experiments import worlds_043 as W43
from scripts.run_reference_033 import _truth
from scripts.run_reference_041 import audit
from scripts.run_reference_040 import _same
MUTATIONS=20;SEED=450;BUDGET_S=1800.0;WORKERS=8
ORDER=('A16_nf2','A16_nf1','A16_N');DELTA={'A16_N':None,'A16_nf1':1,'A16_nf2':2};KEYS=('control','scale16')


def view(c,arm):
    a=c['arms'][arm];stop='AMB' if a['stop']=='K_spent' else a['stop']
    N=c['N'] if DELTA[arm] is None else (None if a['n_min'] is None else a['n_min']+DELTA[arm])
    return {'id':f"{c['block']}/{c['key']}/{c['seed']}/{arm}",'arm':arm,'key':c['key'],'seed':c['seed'],'family':c['family'],
            'extra_acts':list(a['extra_acts']),'stop':stop,'stop_recorded':a['stop'],'n_min':a['n_min'],'model':a['model'],'s1':a['s1'],
            'future':a['future'],'start':a['start'],'N':N}


def trace(r):
    w=W43.world(r['seed'],r['family']);acts=list(W43.actions(r['seed'],0.0,w.k))+r['extra_acts'];return w,acts,_truth(w,acts)


def _audit(r):
    t=perf_counter();w,acts,codes=trace(r);cache={};x=audit(r,w,acts,codes,cache);x['id']=r['id'];x['stop_recorded']=r['stop_recorded']
    q=w.start
    for a in acts:q=w.transitions[q][a]
    m=r['model'];x['future_match_ref']=bool(m is not None and r['s1'] is not None and _same(m[0],m[1],r['s1'],w.transitions,w.emissions,q))
    x['N_audited']=r['N'];return x,cache,perf_counter()-t


def bucket(r,x):
    """Split mismatches into counted mismatches and misfires (nf arms only: [stop, ID, WRONG])."""
    mis=[];fire=[]
    for m in x['mismatches']:
        (fire if DELTA[r['arm']] is not None and m==['stop','ID','WRONG'] else mis).append(m)
    return mis,fire


def mutation_test(recs,caches,n=MUTATIONS):
    pool=[r for r in recs if r['stop']!='unknown' and r['id'] in caches]
    if not pool:return {'mutations':0,'detected':0,'pass':False,'note':'no audited decided record'}
    rng=random.Random(SEED);out=[]
    for j in range(n):
        r=copy.deepcopy(rng.choice(pool));kind=['stop','n_min','verdict','s1'][j%4]
        vr=[md for md in ('future','start') if r.get(md) and any(v!='UNKNOWN' for _,v in r[md]['verdicts'])]
        if kind=='verdict' and not vr:kind='stop'
        if kind=='s1' and len(r['model'][0])<2:kind='stop'
        if kind=='stop':r['stop']={'ID':'IDF','IDF':'ID','AMB':'ID','WRONG':'ID'}[r['stop']]
        elif kind=='n_min':r['n_min']=(r['n_min'] or 0)+1
        elif kind=='verdict':
            md=rng.choice(vr);x=rng.choice([x for x in r[md]['verdicts'] if x[1]!='UNKNOWN']);x[1]={'SAT':'UNSAT','UNSAT':'SAT'}[x[1]]
        else:r['s1']=(r['s1']+1+rng.randrange(len(r['model'][0])-1))%len(r['model'][0])
        w,acts,codes=trace(r);rep=audit(r,w,acts,codes,dict(caches[r['id']]))
        out.append({'id':r['id'],'kind':kind,'detected':bool(rep['mismatches'])})
    d=sum(x['detected'] for x in out);return {'mutations':n,'detected':d,'pass':d==n,'items':out}


def ordered(recs):
    return sorted(recs,key=lambda r:(ORDER.index(r['arm']),KEYS.index(r['key']) if r['key'] in KEYS else 9,r['seed']))


def run_pool(todo,workers,budget):
    t0=time.monotonic();done={};pool=Pool(workers)
    try:
        hs=[(r,pool.apply_async(_audit,(r,))) for r in todo]
        while time.monotonic()-t0<budget and not all(h.ready() for _,h in hs):time.sleep(1.0)
        for r,h in hs:
            if h.ready():done[r['id']]=h.get()
    finally:pool.terminate();pool.join()
    return done,time.monotonic()-t0


def main(argv=None):
    ap=argparse.ArgumentParser();ap.add_argument('study');ap.add_argument('--workers',type=int,default=WORKERS)
    ap.add_argument('--block',default='main');ap.add_argument('--budget',type=float,default=BUDGET_S);ap.add_argument('--output-name',default='REFERENCE_045.json')
    a=ap.parse_args(argv);d=Path(a.study);res=load(d/'RESULTS.json')
    recs=ordered([view(c,g) for c in res['cases'] if c['block']==a.block for g in ORDER if g in c['arms']])
    todo=[r for r in recs if r['stop']!='unknown'];done,el=run_pool(todo,a.workers,a.budget)
    reports=[];mism=[];fires=[]
    for r in recs:
        if r['stop']=='unknown':reports.append({'id':r['id'],'decided':False,'audited':False,'mismatches':[],'stop_recorded':r['stop_recorded']});continue
        if r['id'] not in done:reports.append({'id':r['id'],'decided':True,'audited':False,'mismatches':[],'stop_recorded':r['stop_recorded']});continue
        x=dict(done[r['id']][0]);x['audited']=True;m,f=bucket(r,x);x['counted']=m;x['misfire']=f
        mism+=[[r['id']]+y for y in m];fires+=[[r['id']]+y for y in f];reports.append(x)
    caches={k:v[1] for k,v in done.items()};mt=mutation_test(todo,caches)
    na=[x['id'] for x in reports if x['decided'] and not x['audited']]
    nf2_all=all(x['audited'] for x in reports if x['decided'] and x['id'].endswith('/A16_nf2'))
    per_arm={g:{'records':sum(1 for r in recs if r['arm']==g),'decided':sum(1 for r in todo if r['arm']==g),
                'audited':sum(1 for x in reports if x.get('audited') and x['id'].endswith('/'+g)),
                'mismatches':sum(1 for m in mism if m[0].endswith('/'+g)),'misfires':sum(1 for m in fires if m[0].endswith('/'+g)),
                'idf_future_mismatch':sum(1 for x in reports if x.get('audited') and x['id'].endswith('/'+g) and x.get('label')=='IDF' and not x['future_match_ref'])}
             for g in ORDER}
    out={'schema':'brute.reference.v42_0','study_results_sha256':sha(d/'RESULTS.json'),'block':a.block,'scope':{'budget_s':a.budget,
         'workers':a.workers,'order':list(ORDER),'key_order':list(KEYS)},'records':len(recs),'decided':len(todo),'audited':len(done),
         'not_audited':na,'not_reached':sum(not x['decided'] for x in reports),'complete':not na,'nf2_all_audited':nf2_all,'per_arm':per_arm,
         'k_spent_as_amb':sum(r['stop_recorded']=='K_spent' for r in todo),
         'verdicts_checked':sum(x.get('verdicts_checked',0) for x in reports),'mismatches':mism,'mismatch_count':len(mism),'misfires':fires,
         'mutation_test':mt,'per_record':reports,'walls_informational':{k:round(v[2],1) for k,v in done.items()},'elapsed_informational':el}
    out['vacuous']=out['decided']==0
    out['PASS']=out['mismatch_count']==0 and nf2_all and (out['vacuous'] or mt['pass'])
    write_new(d/a.output_name,out)
    print(json.dumps({k:v for k,v in out.items() if k not in ('per_record','mutation_test','mismatches')},indent=1),'\nmutations',mt['detected'],'/',mt['mutations'])
    return 0 if out['PASS'] else 1


if __name__=='__main__':sys.exit(main())
