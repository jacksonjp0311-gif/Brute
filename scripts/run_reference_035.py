"""GS_ref audit for study-035 (BRUTE_PLAN_035 GS_ref; deviation #142; built from scripts/run_reference_034.py, frozen):
experiments/v0320_reference.py (plain CNF with a totalizer flip budget, CaDiCaL 1.9.5, no shared code with brute/) on arm
A10 of every noisy_scale8 case of a sealed study directory, 8 processes. Per case it rebuilds A10's trace (the seeded
noisy prefix of worlds_026.trajectory plus the stored fused extra readings, which recount_035 checks independently) and,
for every round under that round's B: a 'none' check -> no machine <= N fits (exists_machine at N UNSAT); n_min -> n_min
fits and n_min - 1 does not; a raise to B' -> N fits at B' and not at B' - 1; a raise ending 'none' -> N does not fit at
B_max; every stored future / start verdict (n, SAT or UNSAT) with exists_different (L = N + n_min - 1). Then the final
label (stop unknown -> IDU; future SAT -> AMB; start SAT -> IDF; no rival -> ID if M1 equals the truth from the start, else
WRONG; 'none' -> WRONG) and the separating words (shortest by v0300_reference's BFS, separating, both machines within the
round's B, executed words concatenating to the extra actions). A reference query not decided within 30 s is counted as
undecided (not a mismatch). Then 20 seeded mutations of audited records (label, n_min, one verdict, one raise B) must each
be detected. Writes <study>/REFERENCE_035.json (refuses overwrite). Pass: 0 mismatches, decided items > 0, mutations 20/20.
  PYTHONPATH=. python scripts/run_reference_035.py results/study-035/main [--workers 8]"""
import argparse,copy,json,random,sys
from pathlib import Path
from time import perf_counter
from concurrent.futures import ProcessPoolExecutor
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common_035 import load,write_new,sha
from experiments import worlds_026 as W
from experiments.v0300_reference import shortest_word_len
from experiments.v0320_reference import exists_machine,exists_different
MUTATIONS=20;KEY='noisy_scale8';ARM='A10';N=8;M=4;B_MAX=27;LIMIT=30.0


def _same(d1,e1,s1,d2,e2,s2):
    k=len(d1[0]);seen={(s1,s2)};st=[(s1,s2)]
    while st:
        p,q=st.pop()
        if e1[p]!=e2[q]:return False
        for a in range(k):
            x=(d1[p][a],d2[q][a])
            if x not in seen:seen.add(x);st.append(x)
    return True


def _cur(D,acts):
    q=0
    for a in acts:q=D[q][a]
    return q


def _flips(D,E,acts,rd):
    b=lambda c:((c>>1)&1,c&1);q=0;f=sum(x!=y for x,y in zip(b(E[0]),rd[0]))
    for a,o in zip(acts,rd[1:]):q=D[q][a];f+=sum(x!=y for x,y in zip(b(E[q]),o))
    return f


def audit(case,cache=None):
    w=W.world(case['seed'],case['family']);a=case['arms'][ARM];eps=case['eps']
    acts=list(W.actions(case['seed'],eps,w.k))+list(a['extra_acts'])
    rd=[tuple(o) for o in W.trajectory(w,case['seed'],eps)['readings']]+[tuple(o) for o in a['extra_readings']]
    mm=[];cache={} if cache is None else cache;cnt={'decided':0,'undecided':0}
    def q(key,f):
        if key not in cache:cache[key]=f()
        r=cache[key];cnt['decided' if r is not None else 'undecided']+=1;return r
    def expect(tag,i,key,f,want):
        r=q(key,f)
        if r is not None and r!=want:mm.append([tag,i,want,r])
    for i,r in enumerate(a['rounds']):
        T=r['T'];B=r['B'];ac=acts[:T];rr=rd[:T+1]
        if r['check']=='none':expect('none_but_fits',i,('m',T,N,B),lambda:exists_machine(ac,rr,N,w.k,M,B,LIMIT),False)
        if r['n_min'] is not None:
            nm=r['n_min'];expect('n_min_unfit',i,('m',T,nm,B),lambda:exists_machine(ac,rr,nm,w.k,M,B,LIMIT),True)
            if nm>1:expect('n_min_not_least',i,('m',T,nm-1,B),lambda:exists_machine(ac,rr,nm-1,w.k,M,B,LIMIT),False)
        if r.get('raise_status')=='ok':
            Bn=r['raise_to'];expect('raise_unfit',i,('m',T,N,Bn),lambda:exists_machine(ac,rr,N,w.k,M,Bn,LIMIT),True)
            expect('raise_not_least',i,('m',T,N,Bn-1),lambda:exists_machine(ac,rr,N,w.k,M,Bn-1,LIMIT),False)
        if r.get('raise_status')=='none':expect('raise_none_but_fits',i,('m',T,N,B_MAX),lambda:exists_machine(ac,rr,N,w.k,M,B_MAX,LIMIT),False)
        if r['M1'] is not None:
            M1=r['M1'];s1=_cur(M1[0],ac);L=N+len(M1[0])-1
            if s1!=r['s1']:mm.append(['s1',i])
            if _flips(M1[0],M1[1],ac,rr)>B:mm.append(['M1_over_B',i])
            for mode in ('future','start'):
                S=r.get(mode)
                if S is None:continue
                for n,v in S['verdicts']:
                    if v=='UNKNOWN':continue
                    expect('verdict_'+mode,i,(mode,T,n,B,json.dumps(M1)),lambda:exists_different(ac,rr,n,w.k,M,B,M1,s1,mode,L,LIMIT),v=='SAT')
    last=a['rounds'][-1];st=a['stop']
    if st=='unknown':ref='IDU'
    elif st=='none':ref='WRONG'
    else:
        F=last.get('future');S=last.get('start');fsat=bool(F) and any(v=='SAT' for _,v in F['verdicts']);ssat=bool(S) and any(v=='SAT' for _,v in S['verdicts'])
        M1=last['M1'];ref='AMB' if fsat else ('IDF' if ssat else ('ID' if M1 and _same(M1[0],M1[1],0,w.transitions,w.emissions,w.start) else 'WRONG'))
    if ref!=a['label']:mm.append(['label',a['label'],ref])
    ex=[]
    for i,r in enumerate(a['rounds']):
        if not r.get('word'):continue
        T=r['T'];(D1,E1),(D2,E2)=r['M1'],r['M2']
        if shortest_word_len(D1,E1,r['s1'],D2,E2,r['s2'])!=len(r['word']):mm.append(['word_not_shortest',i])
        if _flips(D1,E1,acts[:T],rd[:T+1])>r['B'] or _flips(D2,E2,acts[:T],rd[:T+1])>r['B']:mm.append(['word_machines_over_B',i])
        q1,q2=r['s1'],r['s2'];p1=[];p2=[]
        for b in r['word']:q1=D1[q1][b];q2=D2[q2][b];p1.append(E1[q1]);p2.append(E2[q2])
        if not (p1[:-1]==p2[:-1] and p1[-1]!=p2[-1]):mm.append(['word_not_separating',i])
        if r.get('executed'):ex+=list(r['word'])
    if ex!=list(a['extra_acts']):mm.append(['executed_words_vs_extra_acts'])
    return {'mismatches':mm,'label':ref,**cnt},cache


def _audit(case):
    t=perf_counter();r,cache=audit(case);r['key']=f"{case['key']}/{case['seed']}";r['wall_informational']=perf_counter()-t;return r,cache


def mutation_test(cases,caches,n=MUTATIONS):
    pool=list(zip(cases,caches))
    if not pool:return {'mutations':0,'detected':0,'pass':False,'note':'no case'}
    rng=random.Random(320);out=[]
    for j in range(n):
        c,ch=rng.choice(pool);c=copy.deepcopy(c);a=c['arms'][ARM];kind=['label','n_min','verdict','raise'][j%4]
        vr=[r for r in a['rounds'] if any(r.get(md) and any(v!='UNKNOWN' for _,v in r[md]['verdicts']) for md in ('future','start'))]
        nr=[r for r in a['rounds'] if r['n_min'] is not None];rr=[r for r in a['rounds'] if r.get('raise_status')=='ok']
        if kind=='raise' and not rr:kind='verdict'
        if kind=='verdict' and not vr:kind='n_min'
        if kind=='n_min' and not nr:kind='label'
        if kind=='label':a['label']={'ID':'IDF','IDF':'ID','AMB':'ID','WRONG':'ID','IDU':'ID'}[a['label']]
        elif kind=='n_min':r=rng.choice(nr);r['n_min']+=1
        elif kind=='raise':r=rng.choice(rr);r['raise_to']+=1
        else:
            r=rng.choice(vr);md=rng.choice([md for md in ('future','start') if r.get(md) and any(v!='UNKNOWN' for _,v in r[md]['verdicts'])])
            x=rng.choice([x for x in r[md]['verdicts'] if x[1]!='UNKNOWN']);x[1]={'SAT':'UNSAT','UNSAT':'SAT'}[x[1]]
        rep,_=audit(c,dict(ch));out.append({'key':f"{c['key']}/{c['seed']}",'kind':kind,'detected':bool(rep['mismatches'])})
    d=sum(x['detected'] for x in out);return {'mutations':n,'detected':d,'pass':d==n,'items':out}


def main(argv=None):
    ap=argparse.ArgumentParser();ap.add_argument('study');ap.add_argument('--workers',type=int,default=8);a=ap.parse_args(argv)
    d=Path(a.study);res=load(d/'RESULTS.json');cases=[c for c in res['cases'] if c['key']==KEY];t=perf_counter()
    with ProcessPoolExecutor(a.workers) as ex:pairs=list(ex.map(_audit,cases))
    reports=[p[0] for p in pairs];caches=[p[1] for p in pairs];mt=mutation_test(cases,caches)
    mism=[[r['key']]+m for r in reports for m in r['mismatches']]
    out={'schema':'brute.reference.v32_0','study_results_sha256':sha(d/'RESULTS.json'),'key':KEY,'arm_audited':ARM,'N':N,
         'cases':len(cases),'decided_items':sum(r['decided'] for r in reports),'undecided_items':sum(r['undecided'] for r in reports),
         'labels_checked':len(reports),'mismatches':mism,'mismatch_count':len(mism),'mutation_test':mt,'per_case':reports,
         'elapsed_informational':perf_counter()-t}
    out['PASS']=out['mismatch_count']==0 and out['decided_items']>0 and mt['pass']
    write_new(d/'REFERENCE_035.json',out)
    print(json.dumps({k:v for k,v in out.items() if k not in ('per_case','mutation_test','mismatches')},indent=1),'\nmutations',mt['detected'],'/',mt['mutations'])
    return 0 if out['PASS'] else 1


if __name__=='__main__':sys.exit(main())
