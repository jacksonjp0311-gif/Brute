"""G_recount for study-038 (deviation #148; new file built from the frozen scripts/recount_037.py, independent of the runner): regenerates every world from its seed
(experiments.worlds_026.world) and the raw read stream from its own copy of the plan's flip rule (random.Random((seed*1000003
+ round(1000 eps)*7919 + 26) mod 2^64), two draws per raw read, flip iff < eps), rebuilds each arm's readings by direct
simulation of the true machine:
  A13_r5 / A13_r3 / A12_r5 / A12_r3 / A11_r3: r raw reads per base position (the step read, then r - 1 re-reads),
  per-bit majority; every executed word likewise r reads per action; S7: the single-read prefix.
It checks the stored fused base, raw and fused word readings, steps and reads, recounts the truth's flips and within_budget
(flips <= the arm's B_max: 2 / 6 / 2 / 6 / 6 / 27, recomputed here from the binomial majority rate), rechecks each model
(<= B_final flips) and re-derives every label: the 035 recount rule (scripts/recount_035.lab_active) for the a11-stop arm
and S7 (033 rule); for the sound-stop arms the last round's B_max confirmation verdicts must support the stop (ID: ordinary
check all UNSAT and, when B < B_max, confirmation future and start all UNSAT for n = c..N, where c = 1 for A12 and c = N for
A13, whose confirmation is one query at n = N (an N-state region contains every machine of <= N states; deviation #148); IDF: confirmation future all
UNSAT and the start search ends SAT; K_spent: the last word's search ends SAT and the word does not fit in K; unknown: an
UNKNOWN verdict or capped raise). Every separating word is re-simulated on the stored M1 and M2; M1 is rechecked under the
round's B and M2 under B_max when the word came from the confirmation, else under B. Writes <study>/RECOUNT_038.json
(refuses overwrite).
  PYTHONPATH=. python scripts/recount_038.py results/study-038/main"""
import json,random,sys
from math import ceil,sqrt,comb
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common_038 import load,write_new,sha
from experiments import worlds_026 as W
from scripts.recount_033 import canon,run,lab
from scripts.recount_035 import same,flips_of,fits,lab_active,maj,bits,SB,H,_all_unsat,_ends_sat
ARMS=('A13_r5','A13_r3','A12_r5','A12_r3','A11_r3','S7')
REPS={'A13_r5':5,'A13_r3':3,'A12_r5':5,'A12_r3':3,'A11_r3':3};SOUND=('A13_r5','A13_r3','A12_r5','A12_r3');INC=('A13_r5','A13_r3');LABELS=('ID','IDF','AMB','WRONG','IDU')
N_DECLARED={'scale8':8,'scale12':12,'control_cycle3':3};K=64


def bend(p):x=p*(H+1)*SB;return int(ceil(x+2*sqrt(x)-1e-12))
def prate(r,e=0.05):return sum(comb(r,i)*e**i*(1-e)**(r-i) for i in range(r//2+1,r+1))
BMAX={**{a:bend(prate(r)) for a,r in REPS.items()},'S7':bend(0.05)}


def flip_rows(seed,eps,n):
    if eps==0:return [(False,False)]*n
    g=random.Random((seed*1000003+int(round(eps*1000))*7919+26)%(2**64));return [tuple(g.random()<eps for _ in range(SB)) for _ in range(n)]


def lab_sound(a,w,N,Kc,Bmax,c=1):
    """Label for a sound-stop arm, re-derived from the stored verdicts (BAD_* on any inconsistency); c: first confirmation n."""
    r=(a.get('rounds') or [{}])[-1];C=r.get('confirm');st=a['stop'];m=a['model']
    if C is None:return lab_active(a,w,N,Kc,lambda x:1) if not (st in ('ID','IDF') and a['B_final']<Bmax) else 'BAD_no_confirm'
    if C['B_max']!=Bmax:return 'BAD_confirm_Bmax'
    F,S=C['future'],C['start'];chk=r.get('check');n=a['n_min']
    if chk not in ('ID','IDF'):return 'BAD_confirm_after_'+str(chk)
    if chk=='ID' and not (_all_unsat(a.get('future'),n,N) and _all_unsat(a.get('start'),n,N)):return 'BAD_check_verdicts'
    if chk=='IDF' and not (_all_unsat(a.get('future'),n,N) and _ends_sat(a.get('start'),n)):return 'BAD_check_verdicts'
    if st=='unknown':return 'IDU' if any(x[1]=='UNKNOWN' for y in (F,S) if y for x in y['verdicts']) else 'BAD_unknown'
    if st=='K_spent':return 'AMB' if _ends_sat(F,c) and r.get('word') and len(r['word'])>Kc-a['used'] else 'BAD_K_spent'
    if not _all_unsat(F,c,N):return 'BAD_confirm_future'
    if st=='IDF':return 'IDF' if (chk=='IDF' and S is None) or (chk=='ID' and _ends_sat(S,c)) else 'BAD_IDF_verdicts'
    if st=='ID':
        if chk!='ID' or not _all_unsat(S,c,N):return 'BAD_ID_verdicts'
        return 'ID' if same(m[0],m[1],0,w.transitions,w.emissions,w.start) else 'WRONG'
    return 'BAD_stop'


def recount_case(c):
    seed=c['seed'];eps=c['eps'];w=W.world(seed,c['family']);bad=[];out={};N=N_DECLARED[c['family']]
    if (w.n,w.k)!=(c['n'],c['k']) or c.get('N')!=N or c.get('B_max')!=BMAX:bad.append('world_shape_N_or_Bmax')
    pa=list(W.actions(seed,eps,w.k));fl=flip_rows(seed,eps,H+1+3000);tc=canon(w.transitions,w.emissions,w.start)
    rd1=lambda q,i:tuple(b^f for b,f in zip(bits(w.emissions[q]),fl[i]))
    for arm in ARMS:
        a=c['arms'][arm];ex=list(a.get('extra_acts') or []);acts=pa+ex;rec={}
        r0=REPS.get(arm,1);ri=0;q=w.start;base=[]
        for t in range(H+1):
            if t:q=w.transitions[q][pa[t-1]]
            rs=[rd1(q,ri+j) for j in range(r0)];ri+=r0;base.append(maj(rs) if r0>1 else rs[0])
        trd=list(base)
        if arm in REPS:
            if [list(o) for o in base]!=[list(o) for o in a['base_readings']]:bad.append((arm,'base_readings'))
            ws=wu=0;used=0
            for x in a['rounds']:
                T=x['T'];sub_a,sub_r=acts[:T],trd[:T+1]
                if x.get('word'):
                    B2=BMAX[arm] if x.get('word_from_confirm') else x['B']
                    if x.get('word_from_confirm') and arm not in SOUND:bad.append((arm,'confirm_word_in_a11_arm',T))
                    (d1,e1),(d2,e2)=x['M1'],x['M2'];p1=run(d1,e1,x['s1'],x['word']);p2=run(d2,e2,x['s2'],x['word']);ws+=1
                    wu+=not (p1[:-1]==p2[:-1] and p1[-1]!=p2[-1] and fits(x['M1'],sub_a,sub_r,x['B']) and fits(x['M2'],sub_a,sub_r,B2))
                if x.get('executed'):
                    raw=[];fused=[]
                    for y in x['word']:
                        q=w.transitions[q][y];rs=[rd1(q,ri+j) for j in range(r0)];ri+=r0
                        raw.append(rs);fused.append(maj(rs) if r0>1 else rs[0]);trd.append(fused[-1])
                    used+=len(x['word'])
                    if [[list(o) for o in rs] for rs in raw]!=[[list(o) for o in rs] for rs in x['raw']] or [list(o) for o in fused]!=[list(o) for o in x['obs']]:bad.append((arm,'raw_or_fused_readings',T))
            if [list(o) for o in trd[H+1:]]!=[list(o) for o in a['extra_readings']]:bad.append((arm,'extra_readings'))
            if used!=a['used'] or ri!=a['reads'] or len(acts)!=a['steps']:bad.append((arm,'used_steps_or_reads',used,ri,len(acts)))
            m=a['model'];mc=m is not None and fits(m,acts,trd,a['B_final'])
            L=lab_sound(a,w,N,K,BMAX[arm],N if arm in INC else 1) if arm in SOUND else lab_active(a,w,N,K,lambda r:1)
            rec.update(label=L,words_checked=ws,words_unsound=wu)
            if m is not None and not mc:bad.append((arm,'model_inconsistent'))
        else:
            if ri!=a['reads'] or a['steps']!=H:bad.append((arm,'steps_or_reads'))
            m=a['model'];match=m is not None and canon(m[0],m[1],0)==tc;rec.update(label=lab(a,match))
            if m is not None:
                f=flips_of(m[0],m[1],0,acts,trd)
                if f>BMAX['S7']:bad.append((arm,'model_inconsistent',f))
        tf=flips_of(w.transitions,w.emissions,w.start,acts,trd);rec.update(truth_flips_trace=tf,within_budget=tf<=BMAX[arm],T_final=len(acts),B_max=BMAX[arm])
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
    act=[a for a in ARMS if a in REPS]
    out={'schema':'brute.recount.v35_0','results_sha256':sha(d/'RESULTS.json'),'cases':len(per),'labels':labels,'B_max':BMAX,
         'words_unsound':sum(v[a]['words_unsound'] for v in per.values() for a in act),
         'words_checked':sum(v[a]['words_checked'] for v in per.values() for a in act),
         'mismatching_cases':len(bad),'mismatches':{k:v for k,v in list(bad.items())[:50]},'per_case':per,'PASS':not bad and len(per)>0}
    write_new(d/'RECOUNT_038.json',out);print(json.dumps({k:v for k,v in out.items() if k!='per_case'},default=str));return 0 if out['PASS'] else 1


if __name__=='__main__':sys.exit(main())
