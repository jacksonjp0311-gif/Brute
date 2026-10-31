"""GS_ref audit for study-041 (BRUTE_PLAN_041 GS_ref; deviation #154; built from the frozen scripts/run_reference_040.py):
experiments/v0310_reference.py and v0300_reference.py (plain CNF, CaDiCaL, no shared code with brute/) on the replay records of
variants E1 and E2 on the 12 sealed study-040 scale16 traces (part c; N = 16). Per trace it rebuilds the sealed final A14 trace
(worlds_040.actions, eps 0, plus the sealed extra actions; readings by simulating the true machine) and, for each decided E1 / E2
record, recomputes n_min (n_min - 1 UNSAT), the returned model's consistency and current state s1, every stored future / start
verdict (n, SAT or UNSAT) with the reference 'exists_different' query (L = N + n_min - 1), the completeness of the final lists
at size N, and the stop label (future SAT -> AMB; else start SAT -> IDF; else ID if the model equals the truth from the start,
WRONG otherwise). Unknown records are 'not_reached'. Then 20 seeded mutations (stop, n_min, one verdict, s1) of the audited
records must each be detected. Writes <study>/REFERENCE_041.json (refuses overwrite). Pass: 0 mismatches, decided > 0, 20/20.
  PYTHONPATH=. python scripts/run_reference_041.py results/study-041/main [--workers 8] [--part c]"""
import argparse,copy,json,random,sys
from pathlib import Path
from time import perf_counter
from concurrent.futures import ProcessPoolExecutor
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common import load,write_new,sha
from experiments.v0300_reference import solve
from experiments.v0310_reference import exists_different
from scripts.run_reference_033 import _truth,_cons
from scripts.run_reference_040 import _same,_cur
from scripts.recount_041 import sealed,WM
MUTATIONS=20;VARS=('E1','E2');M=4


def _nmin(acts,codes,k,N):
    for n in range(1,N+1):
        if solve(acts,codes,n,k,M)[0] is not None:return n
    return None


def trace(r):
    c=sealed(r['study'])[(r['key'],r['seed'])];Wm=WM[r['study']];w=Wm.world(c['seed'],c['family']);a=c['arms']['A14']
    acts=list(Wm.actions(c['seed'],0.0,w.k))+list(a['extra_acts']);return w,acts,_truth(w,acts)


def audit(r,w,acts,codes,cache):
    if r['stop']=='unknown':return {'decided':False,'mismatches':[]}
    mm=[];N=r['N'];k=w.k
    def q(key,f):
        if key not in cache:cache[key]=f()
        return cache[key]
    nm=q(('nmin',),lambda:_nmin(acts,codes,k,N))
    if nm!=r['n_min']:return {'decided':True,'mismatches':[['n_min',r['n_min'],nm]],'verdicts_checked':0}
    M1=r['model'];verd=0
    if M1 is None:return {'decided':True,'mismatches':[['no_model']],'verdicts_checked':0}
    s1=_cur(M1[0],M1[1],acts);L=N+len(M1[0])-1
    if not _cons(M1[0],M1[1],acts,codes):mm.append(['M1_inconsistent'])
    if s1!=r['s1']:mm.append(['s1',r['s1'],s1])
    key=json.dumps(M1)
    for mode in ('future','start'):
        S=r.get(mode)
        if S is None:continue
        if S['L']!=L:mm.append(['L',mode,S['L'],L])
        for n,v in S['verdicts']:
            if v=='UNKNOWN':continue
            ans=q((mode,n,key,s1),lambda:exists_different(acts,codes,n,k,M,M1,s1,mode,L));verd+=1
            if ans!=(v=='SAT'):mm.append(['verdict',mode,n,v,ans])
    F=r.get('future');S=r.get('start')
    fsat=bool(F) and any(v=='SAT' for _,v in F['verdicts']);ssat=bool(S) and any(v=='SAT' for _,v in S['verdicts'])
    if not fsat:
        if q(('future',N,key,s1),lambda:exists_different(acts,codes,N,k,M,M1,s1,'future',L)):mm.append(['future_N_sat'])
        if not ssat and q(('start',N,key,s1),lambda:exists_different(acts,codes,N,k,M,M1,s1,'start',L)):mm.append(['start_N_sat'])
    ref='AMB' if fsat else ('IDF' if ssat else ('ID' if _same(M1[0],M1[1],0,w.transitions,w.emissions,w.start) else 'WRONG'))
    if ref!=r['stop']:mm.append(['stop',r['stop'],ref])
    return {'decided':True,'mismatches':mm,'label':ref,'verdicts_checked':verd}


def _rid(r):return f"{r['study']}/{r['key']}/{r['seed']}/{r['variant']}/{r['repeat']}"


def _audit_trace(recs):
    t=perf_counter();w,acts,codes=trace(recs[0]);cache={};out=[]
    for r in recs:
        x=audit(r,w,acts,codes,cache);x['id']=_rid(r);out.append(x)
    return out,cache,perf_counter()-t


def mutation_test(recs,caches,n=MUTATIONS):
    pool=[r for r in recs if r['stop']!='unknown']
    if not pool:return {'mutations':0,'detected':0,'pass':False,'note':'no decided record'}
    rng=random.Random(410);out=[]
    for j in range(n):
        r=copy.deepcopy(rng.choice(pool));kind=['stop','n_min','verdict','s1'][j%4]
        vr=[md for md in ('future','start') if r.get(md) and any(v!='UNKNOWN' for _,v in r[md]['verdicts'])]
        if kind=='verdict' and not vr:kind='stop'
        if kind=='stop':r['stop']={'ID':'IDF','IDF':'ID','AMB':'ID','WRONG':'ID'}[r['stop']]
        elif kind=='n_min':r['n_min']=(r['n_min'] or 0)+1
        elif kind=='verdict':
            md=rng.choice(vr);x=rng.choice([x for x in r[md]['verdicts'] if x[1]!='UNKNOWN']);x[1]={'SAT':'UNSAT','UNSAT':'SAT'}[x[1]]
        else:r['s1']=(r['s1']+1+rng.randrange(len(r['model'][0])-1))%len(r['model'][0])
        w,acts,codes=trace(r);rep=audit(r,w,acts,codes,dict(caches[(r['study'],r['key'],r['seed'])]))
        out.append({'id':_rid(r),'kind':kind,'detected':bool(rep['mismatches'])})
    d=sum(x['detected'] for x in out);return {'mutations':n,'detected':d,'pass':d==n,'items':out}


def main(argv=None):
    ap=argparse.ArgumentParser();ap.add_argument('study');ap.add_argument('--workers',type=int,default=8);ap.add_argument('--part',default='c')
    a=ap.parse_args(argv);d=Path(a.study);res=load(d/'RESULTS.json');t=perf_counter()
    recs=[r for r in res['replays'] if r['part']==a.part and r['variant'] in VARS];groups={}
    for r in recs:groups.setdefault((r['study'],r['key'],r['seed']),[]).append(r)
    keys=sorted(groups)
    with ProcessPoolExecutor(a.workers) as ex:outs=list(ex.map(_audit_trace,[groups[k] for k in keys]))
    reports=[x for o in outs for x in o[0]];caches={k:o[1] for k,o in zip(keys,outs)}
    mt=mutation_test(recs,caches);mism=[[r['id']]+m for r in reports for m in r['mismatches']]
    out={'schema':'brute.reference.v38_0','study_results_sha256':sha(d/'RESULTS.json'),'part':a.part,'variants_audited':list(VARS),
         'traces':len(keys),'records':len(recs),'decided':sum(r['decided'] for r in reports),'not_reached':sum(not r['decided'] for r in reports),
         'decided_by_variant':{v:sum(r['decided'] for r in reports if r['id'].split('/')[3]==v) for v in VARS},
         'verdicts_checked':sum(r.get('verdicts_checked',0) for r in reports),'mismatches':mism,'mismatch_count':len(mism),
         'mutation_test':mt,'per_record':reports,'trace_walls_informational':{'/'.join(map(str,k)):round(o[2],1) for k,o in zip(keys,outs)},
         'elapsed_informational':perf_counter()-t}
    out['PASS']=out['mismatch_count']==0 and out['decided']>0 and mt['pass']
    write_new(d/'REFERENCE_041.json',out)
    print(json.dumps({k:v for k,v in out.items() if k not in ('per_record','mutation_test','mismatches')},indent=1),'\nmutations',mt['detected'],'/',mt['mutations'])
    return 0 if out['PASS'] else 1


if __name__=='__main__':sys.exit(main())
