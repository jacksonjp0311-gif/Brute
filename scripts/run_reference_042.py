"""GS_ref audit for study-042 (BRUTE_PLAN_042 GS_ref; pre-run deviation #157; built from the frozen scripts/run_reference_041.py,
whose audit() is imported unchanged): experiments/v0310_reference.py and v0300_reference.py (plain CNF, CaDiCaL, no shared code
with brute/) on every decided A16 record of the fresh scale16 cases of one block (default main). Per case it rebuilds the final
trace (worlds_039.actions, eps 0, plus the recorded extra actions; readings by simulating the true machine) and recomputes n_min,
the returned model's consistency and s1, every stored future / start verdict, completeness at size N, and the stop label.
Adapter (#157): a K_spent stop is audited as the AMB it ended on (its final stop check is the AMB round); s1 is the record's 's1'.
Unknown records are 'not_reached'. Then 20 seeded mutations (stop, n_min, one verdict, s1; random.Random(420)) must each be
detected. Writes <study>/REFERENCE_042.json (refuses overwrite). Pass: 0 mismatches, decided > 0, 20/20.
  PYTHONPATH=. python scripts/run_reference_042.py results/study-042/main [--workers 8] [--block main] [--arm A16]"""
import argparse,copy,json,random,sys
from pathlib import Path
from time import perf_counter
from concurrent.futures import ProcessPoolExecutor
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common import load,write_new,sha
from experiments import worlds_039 as W39
from scripts.run_reference_033 import _truth
from scripts.run_reference_041 import audit
MUTATIONS=20


def view(c,arm):
    a=c['arms'][arm];stop='AMB' if a['stop']=='K_spent' else a['stop']
    return {'id':f"{c['block']}/{c['key']}/{c['seed']}/{arm}",'seed':c['seed'],'family':c['family'],'extra_acts':list(a['extra_acts']),
            'stop':stop,'stop_recorded':a['stop'],'n_min':a['n_min'],'model':a['model'],'s1':a['s1'],'future':a['future'],'start':a['start'],'N':c['N']}


def trace(r):
    w=W39.world(r['seed'],r['family']);acts=list(W39.actions(r['seed'],0.0,w.k))+r['extra_acts'];return w,acts,_truth(w,acts)


def _audit(r):
    t=perf_counter();w,acts,codes=trace(r);cache={};x=audit(r,w,acts,codes,cache);x['id']=r['id'];x['stop_recorded']=r['stop_recorded']
    return x,cache,perf_counter()-t


def mutation_test(recs,caches,n=MUTATIONS):
    pool=[r for r in recs if r['stop']!='unknown']
    if not pool:return {'mutations':0,'detected':0,'pass':False,'note':'no decided record'}
    rng=random.Random(420);out=[]
    for j in range(n):
        r=copy.deepcopy(rng.choice(pool));kind=['stop','n_min','verdict','s1'][j%4]
        vr=[md for md in ('future','start') if r.get(md) and any(v!='UNKNOWN' for _,v in r[md]['verdicts'])]
        if kind=='verdict' and not vr:kind='stop'
        if kind=='stop':r['stop']={'ID':'IDF','IDF':'ID','AMB':'ID','WRONG':'ID'}[r['stop']]
        elif kind=='n_min':r['n_min']=(r['n_min'] or 0)+1
        elif kind=='verdict':
            md=rng.choice(vr);x=rng.choice([x for x in r[md]['verdicts'] if x[1]!='UNKNOWN']);x[1]={'SAT':'UNSAT','UNSAT':'SAT'}[x[1]]
        else:r['s1']=(r['s1']+1+rng.randrange(len(r['model'][0])-1))%len(r['model'][0])
        w,acts,codes=trace(r);rep=audit(r,w,acts,codes,dict(caches[r['id']]))
        out.append({'id':r['id'],'kind':kind,'detected':bool(rep['mismatches'])})
    d=sum(x['detected'] for x in out);return {'mutations':n,'detected':d,'pass':d==n,'items':out}


def main(argv=None):
    ap=argparse.ArgumentParser();ap.add_argument('study');ap.add_argument('--workers',type=int,default=8)
    ap.add_argument('--block',default='main');ap.add_argument('--arm',default='A16');ap.add_argument('--key',default='scale16')
    a=ap.parse_args(argv);d=Path(a.study);res=load(d/'RESULTS.json');t=perf_counter()
    recs=[view(c,a.arm) for c in res['cases'] if c['block']==a.block and c['key']==a.key and a.arm in c['arms']]
    todo=[r for r in recs if r['stop']!='unknown']
    with ProcessPoolExecutor(a.workers) as ex:outs=list(ex.map(_audit,todo)) if todo else []
    reports=[o[0] for o in outs]+[{'id':r['id'],'decided':False,'mismatches':[],'stop_recorded':r['stop_recorded']} for r in recs if r['stop']=='unknown']
    caches={o[0]['id']:o[1] for o in outs};mt=mutation_test(todo,caches);mism=[[r['id']]+m for r in reports for m in r['mismatches']]
    out={'schema':'brute.reference.v39_0','study_results_sha256':sha(d/'RESULTS.json'),'block':a.block,'arm':a.arm,'key':a.key,
         'records':len(recs),'decided':sum(r['decided'] for r in reports),'not_reached':sum(not r['decided'] for r in reports),
         'k_spent_as_amb':sum(r['stop_recorded']=='K_spent' for r in todo),
         'verdicts_checked':sum(r.get('verdicts_checked',0) for r in reports),'mismatches':mism,'mismatch_count':len(mism),
         'mutation_test':mt,'per_record':reports,'walls_informational':{o[0]['id']:round(o[2],1) for o in outs},
         'elapsed_informational':perf_counter()-t}
    out['PASS']=out['mismatch_count']==0 and out['decided']>0 and mt['pass']
    write_new(d/'REFERENCE_042.json',out)
    print(json.dumps({k:v for k,v in out.items() if k not in ('per_record','mutation_test','mismatches')},indent=1),'\nmutations',mt['detected'],'/',mt['mutations'])
    return 0 if out['PASS'] else 1


if __name__=='__main__':sys.exit(main())
