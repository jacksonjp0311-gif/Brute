"""GS_ref audit for study-039 (BRUTE_PLAN_039 GS_ref; deviation #150; built from scripts/run_reference_034.py, frozen):
experiments/v0310_reference.py (plain CNF, CaDiCaL, no shared code with brute/) on arm A14 of every scale14 case of a sealed
study directory (N = 14, K = 128), 8 processes. Per case it rebuilds A14's final trace (seeded passive actions + stored extra
actions, readings by simulating the true machine from experiments.worlds_039) and, for every round, recomputes n_min
(n_min-1 UNSAT) on that round's prefix and every stored future / start verdict (n, SAT or UNSAT) with the reference
'exists_different' query (L = N + n_min - 1); then the final label (reference stop: future SAT -> AMB; else start SAT -> IDF;
else ID if M1 equals the truth from the start, WRONG otherwise), the separating words (shortest by v0300_reference's
independent BFS, separating, executed words concatenating to the extra actions). IDU records are 'not_reached'. Then 20
seeded mutations of the audited record (label, n_min, one verdict, one action of an executed word) must each be detected.
Writes <study>/REFERENCE_039.json (refuses overwrite). Pass: 0 mismatches, decided > 0, mutations 20/20.
  PYTHONPATH=. python scripts/run_reference_039.py results/study-039/main [--workers 8]"""
import argparse,copy,json,random,sys
from pathlib import Path
from time import perf_counter
from concurrent.futures import ProcessPoolExecutor
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common_039 import load,write_new,sha
from experiments import worlds_039 as W
from experiments.v0300_reference import shortest_word_len,solve
from experiments.v0310_reference import exists_different
from scripts.run_reference_033 import _truth,_cons
MUTATIONS=20;FAMILY='scale14';ARM='A14';N=14;M=4;K=128


def _same(d1,e1,s1,d2,e2,s2):
    k=len(d1[0]);seen={(s1,s2)};st=[(s1,s2)]
    while st:
        p,q=st.pop()
        if e1[p]!=e2[q]:return False
        for a in range(k):
            x=(d1[p][a],d2[q][a])
            if x not in seen:seen.add(x);st.append(x)
    return True


def _cur(D,E,acts):
    q=0
    for a in acts:q=D[q][a]
    return q


def _nmin(acts,codes,k):
    for n in range(1,N+1):
        if solve(acts,codes,n,k,M)[0] is not None:return n
    return None


def audit(case,cache=None):
    """Mismatch list for the A9 record of one case; cache (query answers) is reused by the mutation test."""
    w=W.world(case['seed'],case['family']);a=case['arms'][ARM];acts=list(W.actions(case['seed'],0.0,w.k))+list(a['extra_acts'])
    codes=_truth(w,acts);mm=[];cache={} if cache is None else cache
    if a['label']=='IDU':return {'decided':False,'mismatches':[]},cache
    def q(key,f):
        if key not in cache:cache[key]=f()
        return cache[key]
    ref_stop=None;verdicts=0
    for i,r in enumerate(a['rounds']):
        T=r['T'];ac=acts[:T];co=codes[:T+1]
        nm=q(('nmin',T),lambda:_nmin(ac,co,w.k))
        if nm!=r['n_min']:mm.append(['n_min',i,r['n_min'],nm]);continue
        if r['M1'] is None:continue
        M1=r['M1'];s1=_cur(M1[0],M1[1],ac);L=N+len(M1[0])-1
        if not _cons(M1[0],M1[1],ac,co):mm.append(['M1_inconsistent',i])
        if s1!=r['s1']:mm.append(['s1',i])
        for mode in ('future','start'):
            S=r.get(mode)
            if S is None:continue
            for n,v in S['verdicts']:
                if v=='UNKNOWN':continue
                ans=q((mode,T,n,json.dumps(M1)),lambda:exists_different(ac,co,n,w.k,M,M1,s1,mode,L));verdicts+=1
                if ans!=(v=='SAT'):mm.append(['verdict',i,mode,n,v,ans])
        if i==len(a['rounds'])-1:
            F=r.get('future');S=r.get('start')
            fsat=bool(F) and any(v=='SAT' for _,v in F['verdicts']);ssat=bool(S) and any(v=='SAT' for _,v in S['verdicts'])
            # completeness of the final verdict lists: the reference checks size N directly (covers every n <= N)
            if not fsat:
                if q(('future',T,N,json.dumps(M1)),lambda:exists_different(ac,co,N,w.k,M,M1,s1,'future',L)):mm.append(['future_N_sat',i])
                if not ssat and q(('start',T,N,json.dumps(M1)),lambda:exists_different(ac,co,N,w.k,M,M1,s1,'start',L)):mm.append(['start_N_sat',i])
            ref_stop='AMB' if fsat else ('IDF' if ssat else ('ID' if _same(M1[0],M1[1],0,w.transitions,w.emissions,w.start) else 'WRONG'))
    if ref_stop is not None and ref_stop!=a['label']:mm.append(['label',a['label'],ref_stop])
    ex=[]
    for i,r in enumerate(a['rounds']):
        if not r.get('word'):continue
        T=r['T'];(D1,E1),(D2,E2)=r['M1'],r['M2']
        Lw=shortest_word_len(D1,E1,r['s1'],D2,E2,r['s2'])
        if Lw!=len(r['word']):mm.append(['word_not_shortest',i,len(r['word']),Lw])
        if not (_cons(D1,E1,acts[:T],codes[:T+1]) and _cons(D2,E2,acts[:T],codes[:T+1])):mm.append(['word_machines_inconsistent',i])
        q1,q2=r['s1'],r['s2'];p1=[];p2=[]
        for b in r['word']:q1=D1[q1][b];q2=D2[q2][b];p1.append(E1[q1]);p2.append(E2[q2])
        if not (p1[:-1]==p2[:-1] and p1[-1]!=p2[-1]):mm.append(['word_not_separating',i])
        if r.get('executed'):ex+=list(r['word'])
    if ex!=list(a['extra_acts']):mm.append(['executed_words_vs_extra_acts'])
    return {'decided':True,'mismatches':mm,'label':ref_stop,'verdicts_checked':verdicts},cache


def _audit(case):
    t=perf_counter();r,cache=audit(case);r['key']=f"{case['family']}/{case['seed']}";r['wall_informational']=perf_counter()-t
    return r,cache


def mutation_test(cases,caches,n=MUTATIONS):
    pool=[(c,ch) for c,ch,r in zip(cases,caches,[None]*len(cases)) if c['arms'][ARM]['label']!='IDU']
    if not pool:return {'mutations':0,'detected':0,'pass':False,'note':'no decided case'}
    rng=random.Random(310);out=[]
    for j in range(n):
        c,ch=rng.choice(pool);c=copy.deepcopy(c);a=c['arms'][ARM];kind=['label','n_min','verdict','word'][j%4]
        if kind=='word' and not any(r.get('word') and r.get('executed') for r in a['rounds']):kind='verdict'
        vr=[r for r in a['rounds'] if any(r.get(md) and any(v!='UNKNOWN' for _,v in r[md]['verdicts']) for md in ('future','start'))]
        if kind=='verdict' and not vr:kind='label'
        if kind=='label':a['label']={'ID':'IDF','IDF':'ID','AMB':'ID','WRONG':'ID'}[a['label']]
        elif kind=='n_min':r=rng.choice(a['rounds']);r['n_min']=(r['n_min'] or 0)+1
        elif kind=='verdict':
            r=rng.choice(vr);md=rng.choice([md for md in ('future','start') if r.get(md) and any(v!='UNKNOWN' for _,v in r[md]['verdicts'])])
            vs=[x for x in r[md]['verdicts'] if x[1]!='UNKNOWN'];x=rng.choice(vs);x[1]={'SAT':'UNSAT','UNSAT':'SAT'}[x[1]]
        else:
            r=rng.choice([r for r in a['rounds'] if r.get('word') and r.get('executed')]);i=rng.randrange(len(r['word']))
            r['word'][i]=(r['word'][i]+1+rng.randrange(c['k']-1))%c['k']
        rep,_=audit(c,dict(ch));out.append({'key':f"{c['family']}/{c['seed']}",'kind':kind,'detected':bool(rep['mismatches'])})
    d=sum(x['detected'] for x in out);return {'mutations':n,'detected':d,'pass':d==n,'items':out}


def main(argv=None):
    ap=argparse.ArgumentParser();ap.add_argument('study');ap.add_argument('--workers',type=int,default=8);a=ap.parse_args(argv)
    d=Path(a.study);res=load(d/'RESULTS.json');cases=[c for c in res['cases'] if c['key']==FAMILY and ARM in c['arms']];t=perf_counter()
    with ProcessPoolExecutor(a.workers) as ex:pairs=list(ex.map(_audit,cases))
    reports=[p[0] for p in pairs];caches=[p[1] for p in pairs];mt=mutation_test(cases,caches)
    mism=[[r['key']]+m for r in reports for m in r['mismatches']]
    out={'schema':'brute.reference.v36_0','study_results_sha256':sha(d/'RESULTS.json'),'family':FAMILY,'arm_audited':ARM,'N':N,
         'cases':len(cases),'decided':sum(r['decided'] for r in reports),'not_reached':sum(not r['decided'] for r in reports),
         'verdicts_checked':sum(r.get('verdicts_checked',0) for r in reports),
         'words_checked':sum(len([x for x in c['arms'][ARM]['rounds'] if x.get('word')]) for c in cases),
         'mismatches':mism,'mismatch_count':len(mism),'mutation_test':mt,'per_case':reports,'elapsed_informational':perf_counter()-t}
    out['PASS']=out['mismatch_count']==0 and out['decided']>0 and mt['pass']
    write_new(d/'REFERENCE_039.json',out)
    print(json.dumps({k:v for k,v in out.items() if k not in ('per_case','mutation_test','mismatches')},indent=1),'\nmutations',mt['detected'],'/',mt['mutations'])
    return 0 if out['PASS'] else 1


if __name__=='__main__':sys.exit(main())
