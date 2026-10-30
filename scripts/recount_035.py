"""G_recount for study-035 (deviation #142; new file, independent of the runner): regenerates every world from its seed
(experiments.worlds_026.world) and the flip stream from its own copy of the plan's flip rule (random.Random((seed*1000003 +
round(1000 eps)*7919 + 26) mod 2^64), two draws per reading, flip iff < eps), rebuilds each arm's readings by direct
simulation of the true machine over the seeded passive actions plus the stored extra actions (A10 / A10_fixed: r = 3 reads
per action once B > 0, fused by per-bit majority; A9: single reads), checks the stored raw and fused readings, recounts the
truth's flips and within_budget (flips <= 27), rechecks each model (exact for A9 / S5, <= B flips for A10 / S7) and
re-derives every label:
  S7, S5: the 033 rule from (unknown, second_found, unique, canonical match);
  A10, A10_fixed, A9: 'ID' needs the final future and start searches UNSAT at every n = n_min..N and the model
  behaviourally equal to the truth from the start (own product BFS); 'IDF' needs the future search UNSAT at every n and the
  start search ending SAT; 'K_spent' needs a future SAT and a word whose cost (length * reps) exceeds the actions left;
  'unknown' an UNKNOWN verdict, a capped raise or no M1; 'none' -> WRONG.
Every separating word is re-simulated on the stored M1 and M2 (equal codes before the last action, different after) and
both machines rechecked on the round's trace under the round's B. Writes <study>/RECOUNT_035.json (refuses overwrite).
  PYTHONPATH=. python scripts/recount_035.py results/study-035/main"""
import json,random,sys
from math import ceil,sqrt
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common_035 import load,write_new,sha
from experiments import worlds_026 as W
from scripts.recount_033 import canon,run,lab
ARMS=('A10','A10_fixed','A9','S7','S5');ADAPT=('A10','A10_fixed');LABELS=('ID','IDF','AMB','WRONG','IDU')
N_DECLARED={'scale8':8,'scale12':12,'scale16':16,'control_cycle3':3};SB=2;H=176
B_MAX=int(ceil(0.05*(H+1)*SB+2*sqrt(0.05*(H+1)*SB)-1e-12));K={8:64,12:64,16:128,3:64};K9=64;R=3


def flip_rows(seed,eps,n):
    if eps==0:return [(False,False)]*n
    g=random.Random((seed*1000003+int(round(eps*1000))*7919+26)%(2**64));return [tuple(g.random()<eps for _ in range(SB)) for _ in range(n)]


def bits(c):return tuple((c>>(SB-1-j))&1 for j in range(SB))
def code(b):return b[0]*2+b[1]


def same(d1,e1,s1,d2,e2,s2):
    k=len(d1[0]);seen={(s1,s2)};st=[(s1,s2)]
    while st:
        p,q=st.pop()
        if e1[p]!=e2[q]:return False
        for a in range(k):
            x=(d1[p][a],d2[q][a])
            if x not in seen:seen.add(x);st.append(x)
    return True


def flips_of(d,e,s,acts,rd):
    q=s;f=sum(x!=y for x,y in zip(bits(e[q]),rd[0]))
    for a,o in zip(acts,rd[1:]):q=d[q][a];f+=sum(x!=y for x,y in zip(bits(e[q]),o))
    return f


def fits(M,acts,rd,B):return flips_of(M[0],M[1],0,acts,rd)<=B


def _all_unsat(S,n,N):return S is not None and not S['found'] and not S['unknown'] and S['verdicts']==[[x,'UNSAT'] for x in range(n,N+1)]


def _ends_sat(S,n):
    v=S and S['verdicts'];return bool(v) and S['found'] and v[-1][1]=='SAT' and all(x[1]=='UNSAT' for x in v[:-1]) and v[0][0]==n


def lab_active(a,w,N,Kc,reps_of):
    m=a['model'];st=a['stop'];F=a.get('future');S=a.get('start')
    if st=='unknown':
        last=(a.get('rounds') or [{}])[-1]
        ok=m is None or last.get('raise_status')=='unknown' or any(x[1]=='UNKNOWN' for y in (F,S) if y for x in y['verdicts'])
        return 'IDU' if ok else 'BAD_unknown'
    if st=='none':return 'WRONG'
    n=a['n_min']
    if st=='ID':
        if not (_all_unsat(F,n,N) and _all_unsat(S,n,N)):return 'BAD_ID_verdicts'
        return 'ID' if same(m[0],m[1],0,w.transitions,w.emissions,w.start) else 'WRONG'
    if st=='IDF':return 'IDF' if _all_unsat(F,n,N) and _ends_sat(S,n) else 'BAD_IDF_verdicts'
    if st=='K_spent':
        if 'rounds' not in a:return 'AMB' if _ends_sat(F,n) else 'BAD_K_spent'
        r=a['rounds'][-1];return 'AMB' if _ends_sat(F,n) and r.get('word') and len(r['word'])*reps_of(r)>Kc-a['used'] else 'BAD_K_spent'
    return 'BAD_stop'


def maj(rs):return tuple(int(2*sum(o[j] for o in rs)>len(rs)) for j in range(SB))


def recount_case(c):
    seed=c['seed'];eps=c['eps'];w=W.world(seed,c['family']);bad=[];out={};N=N_DECLARED[c['family']]
    if (w.n,w.k)!=(c['n'],c['k']) or c.get('N')!=N or c.get('B_max')!=B_MAX:bad.append('world_shape_N_or_Bmax')
    pa=list(W.actions(seed,eps,w.k));fl=flip_rows(seed,eps,H+1+3*K[N]+10);tc=canon(w.transitions,w.emissions,w.start)
    q=w.start;rd=[tuple(b^f for b,f in zip(bits(w.emissions[q]),fl[0]))]
    for t,a in enumerate(pa):q=w.transitions[q][a];rd.append(tuple(b^f for b,f in zip(bits(w.emissions[q]),fl[t+1])))
    qend=q
    for arm in ARMS:
        a=c['arms'][arm];ex=list(a.get('extra_acts') or []);acts=pa+ex;trd=list(rd);q=qend;ri=H+1;rec={}
        if arm in ADAPT:
            ws=wu=0;used=0
            for r in a['rounds']:
                T=r['T'];sub_a,sub_r=acts[:T],trd[:T+1]
                if r.get('word'):
                    (d1,e1),(d2,e2)=r['M1'],r['M2'];p1=run(d1,e1,r['s1'],r['word']);p2=run(d2,e2,r['s2'],r['word']);ws+=1
                    wu+=not (p1[:-1]==p2[:-1] and p1[-1]!=p2[-1] and fits(r['M1'],sub_a,sub_r,r['B']) and fits(r['M2'],sub_a,sub_r,r['B']))
                if r.get('executed'):
                    reps=3 if r['B']>0 else 1;raw=[];fused=[]
                    for x in r['word']:
                        q=w.transitions[q][x];rs=[]
                        for _ in range(reps):rs.append(tuple(b^f for b,f in zip(bits(w.emissions[q]),fl[ri])));ri+=1
                        raw.append(rs);fused.append(maj(rs) if reps>1 else rs[0]);trd.append(fused[-1])
                    used+=len(r['word'])*reps
                    if [[list(o) for o in rs] for rs in raw]!=[[list(o) for o in rs] for rs in r['raw']] or [list(o) for o in fused]!=[list(o) for o in r['obs']]:bad.append((arm,'raw_or_fused_readings',T))
            if [list(o) for o in trd[H+1:]]!=[list(o) for o in a['extra_readings']]:bad.append((arm,'extra_readings'))
            if used!=a['used'] or ri!=a['reads']:bad.append((arm,'used_or_reads',used,ri))
            Bf=a['B_final'];m=a['model'];mc=m is not None and fits(m,acts,trd,Bf)
            rec.update(label=lab_active(a,w,N,K[N],lambda r:3 if r['B']>0 else 1),words_checked=ws,words_unsound=wu,model_consistent_B=mc)
            if m is not None and not mc:bad.append((arm,'model_inconsistent'))
        elif arm=='A9':
            for x in ex:q=w.transitions[q][x];trd.append(tuple(b^f for b,f in zip(bits(w.emissions[q]),fl[ri])));ri+=1
            m=a['model'];rec['label']=lab_active(a,w,N,K9,lambda r:1)
            if m is not None and flips_of(m[0],m[1],0,acts,trd)!=0:bad.append((arm,'model_inconsistent'))
        else:
            m=a['model'];match=m is not None and canon(m[0],m[1],0)==tc;rec.update(label=lab(a,match))
            if m is not None:
                f=flips_of(m[0],m[1],0,acts,trd)
                if f>(B_MAX if arm=='S7' else 0):bad.append((arm,'model_inconsistent',f))
        tf=flips_of(w.transitions,w.emissions,w.start,acts,trd);rec.update(truth_flips_trace=tf,within_budget=tf<=B_MAX,T_final=len(acts))
        if rec['label'].startswith('BAD'):bad.append((arm,rec['label']))
        for kk,v in rec.items():
            if kk in a and a[kk]!=v:bad.append((arm,kk,a[kk],v))
        out[arm]=rec
    return out,bad


def main(argv=None):
    argv=sys.argv[1:] if argv is None else argv;d=Path(argv[0]);res=load(d/'RESULTS.json');per={};bad={}
    for c in res['cases']:
        k=f"{c['block']}/{c['key']}/{c['seed']}";per[k],b=recount_case(c)
        if b:bad[k]=b
    labels={arm:{L:sum(1 for v in per.values() if v[arm]['label']==L) for L in LABELS} for arm in ARMS}
    out={'schema':'brute.recount.v32_0','results_sha256':sha(d/'RESULTS.json'),'cases':len(per),'labels':labels,
         'words_unsound':sum(v[a]['words_unsound'] for v in per.values() for a in ADAPT),
         'words_checked':sum(v[a]['words_checked'] for v in per.values() for a in ADAPT),
         'mismatching_cases':len(bad),'mismatches':{k:v for k,v in list(bad.items())[:50]},'per_case':per,'PASS':not bad and len(per)>0}
    write_new(d/'RECOUNT_035.json',out);print(json.dumps({k:v for k,v in out.items() if k!='per_case'},default=str));return 0 if out['PASS'] else 1


if __name__=='__main__':sys.exit(main())
