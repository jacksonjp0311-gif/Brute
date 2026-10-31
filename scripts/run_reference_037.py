"""GS_ref audit for study-037 (BRUTE_PLAN_037 GS_ref; deviation #146; built from scripts/run_reference_036.py, frozen):
the frozen independent reference experiments/v0320_reference.py (plain CNF, totalizer flip budget, CaDiCaL 1.9.5, no shared
code with brute/) on arm A12_r3 of every noisy_scale8 case of a sealed study directory, 8 processes. Per case it rebuilds
A12_r3's majority trace from its own raw reads (worlds_026.flips rows, 3 reads per base position, per-bit majority) plus the
stored fused extra readings (which recount_037 checks independently), and, for every round under that round's B: a 'none'
check -> no machine <= N fits; n_min -> n_min fits and n_min - 1 does not; every bisection probe [B', SAT/UNSAT] -> N fits at
B' iff SAT; a raise to B' (the least B) -> N fits at B' and not at B' - 1; a raise ending 'none' -> N does not fit at
B_max(3) = 6; every stored future / start verdict with exists_different (L = N + n_min - 1); every B_max confirmation
verdict (future and start, n = 1..N, at B_max 6) the same way. Then the final label (a confirmation verdict overrides the
ordinary check: future SAT -> AMB, start SAT -> IDF, UNKNOWN -> IDU) and the separating words (M2 under B_max when the word
came from the confirmation). Undecided reference queries (30 s) are counted, not mismatches. 20 seeded mutations (label,
n_min, one verdict, one raise B, one probe, one confirmation verdict) must each be detected. GS_ref also needs at least 1 decided verdict or probe at
B > 0 (raised_B_decided), else it fails as 'raised-B not exercised'. Writes <study>/REFERENCE_037.json (refuses overwrite).
  PYTHONPATH=. python scripts/run_reference_037.py results/study-037/main [--workers 8]"""
import argparse,copy,json,random,sys
from pathlib import Path
from time import perf_counter
from concurrent.futures import ProcessPoolExecutor
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common_037 import load,write_new,sha
from experiments import worlds_026 as W
from experiments.v0300_reference import shortest_word_len
from experiments.v0320_reference import exists_machine,exists_different
MUTATIONS=20;KEY='noisy_scale8';ARM='A12_r3';N=8;M=4;B_MAX=6;LIMIT=30.0;R=3;H=176


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
    fl=W.flips(case['seed'],eps,H+3000);b=lambda c:((c>>1)&1,c&1);q=w.start;base=[]
    for t in range(H+1):
        if t:q=w.transitions[q][acts[t-1]]
        rs=[tuple(x^int(f) for x,f in zip(b(w.emissions[q]),fl[R*t+j])) for j in range(R)]
        base.append(tuple(int(2*sum(o[j] for o in rs)>R) for j in range(2)))
    rd=base+[tuple(o) for o in a['extra_readings']]
    mm=[];cache={} if cache is None else cache;cnt={'decided':0,'undecided':0,'raised_B_decided':0,'confirm_items':0}
    def q(key,f):
        if key not in cache:cache[key]=f()
        r=cache[key];cnt['decided' if r is not None else 'undecided']+=1
        if r is not None and key[3]>0:cnt['raised_B_decided']+=1
        return r
    def expect(tag,i,key,f,want):
        r=q(key,f)
        if r is not None and r!=want:mm.append([tag,i,want,r])
    for i,r in enumerate(a['rounds']):
        T=r['T'];B=r['B'];ac=acts[:T];rr=rd[:T+1]
        if r['check']=='none':expect('none_but_fits',i,('m',T,N,B),lambda:exists_machine(ac,rr,N,w.k,M,B,LIMIT),False)
        if r['n_min'] is not None:
            nm=r['n_min'];expect('n_min_unfit',i,('m',T,nm,B),lambda:exists_machine(ac,rr,nm,w.k,M,B,LIMIT),True)
            if nm>1:expect('n_min_not_least',i,('m',T,nm-1,B),lambda:exists_machine(ac,rr,nm-1,w.k,M,B,LIMIT),False)
        for j,(Bp,v) in enumerate(r.get('probes') or []):
            if v is None:continue
            expect('probe',i,('m',T,N,Bp),lambda:exists_machine(ac,rr,N,w.k,M,Bp,LIMIT),bool(v))
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
            C=r.get('confirm')
            if C is not None:
                if C['B_max']!=B_MAX:mm.append(['confirm_Bmax',i])
                for mode in ('future','start'):
                    S=C.get(mode)
                    if S is None:continue
                    if [n for n,_ in S['verdicts']]!=list(range(1,len(S['verdicts'])+1)):mm.append(['confirm_n_range_'+mode,i])
                    for n,v in S['verdicts']:
                        if v=='UNKNOWN':continue
                        expect('confirm_'+mode,i,(mode,T,n,B_MAX,json.dumps(M1)),lambda:exists_different(ac,rr,n,w.k,M,B_MAX,M1,s1,mode,L,LIMIT),v=='SAT');cnt['confirm_items']+=1
    last=a['rounds'][-1];st=a['stop']
    if st=='unknown':ref='IDU'
    elif st=='none':ref='WRONG'
    elif last.get('confirm') is not None:
        C=last['confirm'];cv=[v for md in ('future','start') if C.get(md) for _,v in C[md]['verdicts']]
        fsat=bool(C.get('future')) and any(v=='SAT' for _,v in C['future']['verdicts']);ssat=bool(C.get('start')) and any(v=='SAT' for _,v in C['start']['verdicts'])
        M1=last['M1']
        if fsat:ref='AMB'
        elif 'UNKNOWN' in cv:ref='IDU'
        elif ssat or last['check']=='IDF':ref='IDF'
        else:ref='ID' if M1 and _same(M1[0],M1[1],0,w.transitions,w.emissions,w.start) else 'WRONG'
    else:
        F=last.get('future');S=last.get('start');fsat=bool(F) and any(v=='SAT' for _,v in F['verdicts']);ssat=bool(S) and any(v=='SAT' for _,v in S['verdicts'])
        M1=last['M1'];ref='AMB' if fsat else ('IDF' if ssat else ('ID' if M1 and _same(M1[0],M1[1],0,w.transitions,w.emissions,w.start) else 'WRONG'))
    if ref!=a['label']:mm.append(['label',a['label'],ref])
    ex=[]
    for i,r in enumerate(a['rounds']):
        if not r.get('word'):continue
        T=r['T'];(D1,E1),(D2,E2)=r['M1'],r['M2']
        if shortest_word_len(D1,E1,r['s1'],D2,E2,r['s2'])!=len(r['word']):mm.append(['word_not_shortest',i])
        if _flips(D1,E1,acts[:T],rd[:T+1])>r['B'] or _flips(D2,E2,acts[:T],rd[:T+1])>(B_MAX if r.get('word_from_confirm') else r['B']):mm.append(['word_machines_over_B',i])
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
    rng=random.Random(340);out=[]
    for j in range(n):
        c,ch=rng.choice(pool);c=copy.deepcopy(c);a=c['arms'][ARM];kind=['label','n_min','verdict','raise','probe','confirm'][j%6]
        vr=[r for r in a['rounds'] if any(r.get(md) and any(v!='UNKNOWN' for _,v in r[md]['verdicts']) for md in ('future','start'))]
        nr=[r for r in a['rounds'] if r['n_min'] is not None];rr=[r for r in a['rounds'] if r.get('raise_status')=='ok']
        pr=[r for r in a['rounds'] if any(v is not None for _,v in (r.get('probes') or []))]
        cr=[r for r in a['rounds'] if r.get('confirm') and any(r['confirm'].get(md) and any(v!='UNKNOWN' for _,v in r['confirm'][md]['verdicts']) for md in ('future','start'))]
        if kind=='confirm' and not cr:kind='probe'
        if kind=='probe' and not pr:kind='raise'
        if kind=='raise' and not rr:kind='verdict'
        if kind=='verdict' and not vr:kind='n_min'
        if kind=='n_min' and not nr:kind='label'
        if kind=='label':a['label']={'ID':'IDF','IDF':'ID','AMB':'ID','WRONG':'ID','IDU':'ID'}[a['label']]
        elif kind=='n_min':r=rng.choice(nr);r['n_min']+=1
        elif kind=='raise':r=rng.choice(rr);r['raise_to']+=1
        elif kind=='confirm':
            r=rng.choice(cr);C=r['confirm'];md=rng.choice([md for md in ('future','start') if C.get(md) and any(v!='UNKNOWN' for _,v in C[md]['verdicts'])])
            x=rng.choice([x for x in C[md]['verdicts'] if x[1]!='UNKNOWN']);x[1]={'SAT':'UNSAT','UNSAT':'SAT'}[x[1]]
        elif kind=='probe':r=rng.choice(pr);x=rng.choice([x for x in r['probes'] if x[1] is not None]);x[1]=not x[1]
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
    out={'schema':'brute.reference.v34_0','study_results_sha256':sha(d/'RESULTS.json'),'key':KEY,'arm_audited':ARM,'N':N,
         'cases':len(cases),'decided_items':sum(r['decided'] for r in reports),'undecided_items':sum(r['undecided'] for r in reports),
         'raised_B_decided':sum(r['raised_B_decided'] for r in reports),
         'labels_checked':len(reports),'mismatches':mism,'mismatch_count':len(mism),'mutation_test':mt,'per_case':reports,
         'elapsed_informational':perf_counter()-t}
    out['raised_B_exercised']=out['raised_B_decided']>0
    out['confirm_items']=sum(r.get('confirm_items',0) for r in reports)
    out['PASS']=out['mismatch_count']==0 and out['decided_items']>0 and mt['pass'] and out['raised_B_exercised']
    write_new(d/'REFERENCE_037.json',out)
    print(json.dumps({k:v for k,v in out.items() if k not in ('per_case','mutation_test','mismatches')},indent=1),'\nmutations',mt['detected'],'/',mt['mutations'])
    return 0 if out['PASS'] else 1


if __name__=='__main__':sys.exit(main())
