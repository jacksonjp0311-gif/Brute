"""GS_ref audit for study-033 (BRUTE_PLAN_033 GS_ref; deviation #138; built from scripts/run_reference_032.py, frozen):
experiments/v0300_reference.py (plain CNF, CaDiCaL, no shared code) on arm A8 of every scale8 case of a sealed study
directory, 8 processes. Per case it rebuilds A8's final trace (seeded passive actions + stored extra actions, readings by
simulating the true machine), recomputes n_min (n_min-1 UNSAT), uniqueness at n_min and the label against the truth, and
checks every distinguishing word: shortest by an independent product BFS, both machines consistent with the round's
prefix, executed words concatenating to the extra actions. IDU records are 'not_reached'. Then 20 seeded mutations of the
audited record (label, n_min +1/-1, one action of an executed word) must each be detected.
Writes <study>/REFERENCE_033.json (refuses overwrite). Pass: 0 mismatches, decided > 0, mutations 20/20.
  PYTHONPATH=. python scripts/run_reference_033.py results/study-033/main [--workers 8]"""
import argparse,copy,json,random,sys
from pathlib import Path
from time import perf_counter
from concurrent.futures import ProcessPoolExecutor
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common_033 import load,write_new,sha
from experiments import worlds_026 as W
from experiments.v0300_reference import reference_identify,shortest_word_len,solve
MUTATIONS=20;FAMILY='scale8';ARM='A8';N_MAX=16;M=4


def _truth(w,acts):
    q=w.start;out=[w.emissions[q]]
    for a in acts:q=w.transitions[q][a];out.append(w.emissions[q])
    return out


def _canon(d,e,s):
    k=len(d[0]);order=[s];idx={s:0};i=0
    while i<len(order):
        q=order[i];i+=1
        for a in range(k):
            if d[q][a] not in idx:idx[d[q][a]]=len(order);order.append(d[q][a])
    return [[idx[d[q][a]] for a in range(k)] for q in order],[e[q] for q in order]


def _cons(D,E,acts,codes):
    q=0
    if E[q]!=codes[0]:return False
    for a,c in zip(acts,codes[1:]):
        q=D[q][a]
        if E[q]!=c:return False
    return True


def audit(case,ref=None):
    """Mismatch list for the A8 record of one case; ref (the reference identify result) is reused by the mutation test."""
    w=W.world(case['seed'],case['family']);a=case['arms'][ARM];acts=list(W.actions(case['seed'],0.0,w.k))+list(a['extra_acts'])
    codes=_truth(w,acts);mm=[]
    if a['label']=='IDU':return {'decided':False,'mismatches':[]},ref
    if ref is None:ref=reference_identify(acts,codes,w.k,M,N_MAX)
    if ref['n_min']!=a['n_min']:mm.append(['n_min',a['n_min'],ref['n_min']])
    if ref['n_min'] is not None and ref['n_min']>1 and solve(acts,codes,ref['n_min']-1,w.k,M)[0] is not None:mm.append(['n_min_minus_1_sat'])
    match=ref['M1'] is not None and _canon(ref['M1'][0],ref['M1'][1],0)==_canon(w.transitions,w.emissions,w.start)
    lab='AMB' if not ref['unique'] else ('ID' if match else 'WRONG')
    if lab!=a['label']:mm.append(['label',a['label'],lab])
    if a['model'] is not None and not _cons(a['model'][0],a['model'][1],acts,codes):mm.append(['model_inconsistent'])
    ex=[]
    for i,r in enumerate(a['rounds']):
        if not r.get('word'):continue
        T=r['T'];(D1,E1),(D2,E2)=r['M1'],r['M2']
        L=shortest_word_len(D1,E1,r['s1'],D2,E2,r['s2'])
        if L!=len(r['word']):mm.append(['word_not_shortest',i,len(r['word']),L])
        if not (_cons(D1,E1,acts[:T],codes[:T+1]) and _cons(D2,E2,acts[:T],codes[:T+1])):mm.append(['word_machines_inconsistent',i])
        q1,q2=r['s1'],r['s2'];p1=[];p2=[]
        for b in r['word']:q1=D1[q1][b];q2=D2[q2][b];p1.append(E1[q1]);p2.append(E2[q2])
        if not (p1[:-1]==p2[:-1] and p1[-1]!=p2[-1]):mm.append(['word_not_separating',i])
        if r.get('executed'):ex+=list(r['word'])
    if ex!=list(a['extra_acts']):mm.append(['executed_words_vs_extra_acts'])
    return {'decided':True,'mismatches':mm,'n_min':ref['n_min'],'unique':ref['unique'],'label':lab},ref


def _audit(case):
    t=perf_counter();r,ref=audit(case);r['key']=f"{case['family']}/{case['seed']}";r['wall_informational']=perf_counter()-t
    return r,ref


def mutation_test(cases,refs,n=MUTATIONS):
    pool=[(c,ref) for c,ref in zip(cases,refs) if ref is not None]
    if not pool:return {'mutations':0,'detected':0,'pass':False,'note':'no decided case'}
    rng=random.Random(300);out=[]
    for j in range(n):
        c,ref=rng.choice(pool);c=copy.deepcopy(c);a=c['arms'][ARM];kind=['label','n_min_plus','n_min_minus','word'][j%4]
        if kind=='word' and not any(r.get('word') and r.get('executed') for r in a['rounds']):kind='label'
        if kind=='n_min_minus' and not a['n_min'] or a['n_min']==1 and kind=='n_min_minus':kind='n_min_plus'
        if kind=='label':a['label']={'ID':'AMB','AMB':'ID','WRONG':'ID'}[a['label']]
        elif kind=='n_min_plus':a['n_min']=(a['n_min'] or 0)+1
        elif kind=='n_min_minus':a['n_min']-=1
        else:
            r=rng.choice([r for r in a['rounds'] if r.get('word') and r.get('executed')]);i=rng.randrange(len(r['word']))
            r['word'][i]=(r['word'][i]+1+rng.randrange(c['k']-1))%c['k']
        rep,_=audit(c,ref);out.append({'key':f"{c['family']}/{c['seed']}",'kind':kind,'detected':bool(rep['mismatches'])})
    d=sum(x['detected'] for x in out);return {'mutations':n,'detected':d,'pass':d==n,'items':out}


def main(argv=None):
    ap=argparse.ArgumentParser();ap.add_argument('study');ap.add_argument('--workers',type=int,default=8);a=ap.parse_args(argv)
    d=Path(a.study);res=load(d/'RESULTS.json');cases=[c for c in res['cases'] if c['family']==FAMILY];t=perf_counter()
    with ProcessPoolExecutor(a.workers) as ex:pairs=list(ex.map(_audit,cases))
    reports=[p[0] for p in pairs];refs=[p[1] for p in pairs];mt=mutation_test(cases,refs)
    mism=[[r['key']]+m for r in reports for m in r['mismatches']]
    out={'schema':'brute.reference.v30_0','study_results_sha256':sha(d/'RESULTS.json'),'family':FAMILY,'arm_audited':ARM,
         'cases':len(cases),'decided':sum(r['decided'] for r in reports),'not_reached':sum(not r['decided'] for r in reports),
         'words_checked':sum(len([x for x in c['arms'][ARM]['rounds'] if x.get('word')]) for c in cases),
         'mismatches':mism,'mismatch_count':len(mism),'mutation_test':mt,'per_case':reports,'elapsed_informational':perf_counter()-t}
    out['PASS']=out['mismatch_count']==0 and out['decided']>0 and mt['pass']
    write_new(d/'REFERENCE_033.json',out)
    print(json.dumps({k:v for k,v in out.items() if k not in ('per_case','mutation_test','mismatches')},indent=1),'\nmutations',mt['detected'],'/',mt['mutations'])
    return 0 if out['PASS'] else 1


if __name__=='__main__':sys.exit(main())
