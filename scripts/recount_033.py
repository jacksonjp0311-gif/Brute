"""G_recount for study-033 (deviation #138; new file, independent of the runner): regenerates every world from its seed
(experiments.worlds_026), rebuilds each arm's trace from the seeded passive actions plus the stored extra actions by
direct simulation of the true machine (A8_random's extra actions are regenerated from random.Random(seed*91033+33)),
checks the stored extra readings, rechecks the stored final model's consistency with that trace, recomputes the match
against the truth (canonical BFS) and re-derives every label from (unknown, second_found, unique, match) with the 031 rule;
for A8 it re-simulates every distinguishing word on the stored M1 and M2 (equal codes before the last action, different
after it), rechecks both machines on the round's trace prefix and the truth on every prefix, and recounts actions used.
Writes <study>/RECOUNT_033.json (refuses overwrite); PASS iff every label, count and soundness field reproduces.
  PYTHONPATH=. python scripts/recount_033.py results/study-033/main"""
import json,random,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common_033 import load,write_new,sha
from experiments import worlds_026 as W
ARMS=('A8','A8_random','S5','S1');K=64


def canon(d,e,s):
    k=len(d[0]);order=[s];idx={s:0};i=0
    while i<len(order):
        q=order[i];i+=1
        for a in range(k):
            if d[q][a] not in idx:idx[d[q][a]]=len(order);order.append(d[q][a])
    return [[idx[d[q][a]] for a in range(k)] for q in order],[e[q] for q in order]


def consistent(d,e,s,acts,codes):
    """codes are exact codes (eps 0, single-code masks)."""
    q=s
    if e[q]!=codes[0]:return False
    for a,c in zip(acts,codes[1:]):
        q=d[q][a]
        if e[q]!=c:return False
    return True


def run(d,e,s,word):
    out=[]
    for a in word:s=d[s][a];out.append(e[s])
    return out


def truth_codes(w,acts):
    q=w.start;out=[w.emissions[q]]
    for a in acts:q=w.transitions[q][a];out.append(w.emissions[q])
    return out


def lab(a,match):
    if a['unknown']:return 'IDU'
    if a['second_found']:return 'AMB'
    return 'ID' if a['unique'] and match else 'WRONG'


def recount_case(c):
    w=W.world(c['seed'],c['family']);bad=[];out={}
    if (w.n,w.k)!=(c['n'],c['k']):bad.append('world_shape')
    pa=list(W.actions(c['seed'],0.0,w.k));tc=canon(w.transitions,w.emissions,w.start)
    for arm in ARMS:
        a=c['arms'][arm];ex=list(a.get('extra_acts') or [])
        if arm=='A8_random':
            rng=random.Random(c['seed']*91033+33);exp=[rng.randrange(w.k) for _ in range(min(c['arms']['A8']['used'],K))]
            if ex!=exp:bad.append((arm,'random_actions'))
        acts=pa+ex;codes=truth_codes(w,acts)
        if arm=='A8' and [1<<x for x in codes[len(pa)+1:]]!=list(a.get('extra_masks') or []):bad.append((arm,'extra_readings'))
        m=a['model'];mc=m is not None and consistent(m[0],m[1],0,acts,codes);match=m is not None and canon(m[0],m[1],0)==tc
        rec={'label':lab(a,match),'match':match,'model_consistent':mc,'used':len(ex),'T_final':len(acts)}
        if arm!='A8':rec['used']=a['used']
        if a.get('second_found') and a.get('model2') is not None:
            m2=a['model2'];rec['model2_consistent']=consistent(m2[0],m2[1],0,acts,codes) if arm!='A8' else None
        if arm=='A8':
            if a['stop']=='none':rec['label']='WRONG'
            ws=wu=ti=0
            for r in a['rounds']:
                T=r['T']
                if not consistent(w.transitions,w.emissions,w.start,acts[:T],codes[:T+1]):ti+=1
                if r.get('word'):
                    (d1,e1),(d2,e2)=r['M1'],r['M2'];p1=run(d1,e1,r['s1'],r['word']);p2=run(d2,e2,r['s2'],r['word']);ws+=1
                    ok=(p1[:-1]==p2[:-1] and p1[-1]!=p2[-1] and consistent(d1,e1,0,acts[:T],codes[:T+1]) and consistent(d2,e2,0,acts[:T],codes[:T+1]))
                    wu+=not ok
            rec.update(words_checked=ws,words_unsound=wu,truth_inconsistent_rounds=ti,
                       words_executed_length=sum(len(r['word']) for r in a['rounds'] if r.get('executed')))
            if rec['words_executed_length']!=a['used']:bad.append((arm,'used_vs_words'))
        rec['truth_consistent_final']=consistent(w.transitions,w.emissions,w.start,acts,codes)
        for kk,v in rec.items():
            if kk in a and a[kk]!=v:bad.append((arm,kk,a[kk],v))
        if a['model_consistent'] is not True and a['model'] is not None:bad.append((arm,'model_inconsistent'))
        out[arm]=rec
    return out,bad


def main(argv=None):
    argv=sys.argv[1:] if argv is None else argv;d=Path(argv[0]);res=load(d/'RESULTS.json');per={};bad={}
    for c in res['cases']:
        k=f"{c['block']}/{c['family']}/{c['seed']}";per[k],b=recount_case(c)
        if b:bad[k]=b
    labels={arm:{L:sum(1 for v in per.values() if v[arm]['label']==L) for L in ('ID','AMB','WRONG','IDU')} for arm in ARMS}
    out={'schema':'brute.recount.v30_0','results_sha256':sha(d/'RESULTS.json'),'cases':len(per),'labels':labels,
         'words_unsound':sum(v['A8']['words_unsound'] for v in per.values()),'words_checked':sum(v['A8']['words_checked'] for v in per.values()),
         'truth_inconsistent':sum(v['A8']['truth_inconsistent_rounds']+sum(not v[a]['truth_consistent_final'] for a in ARMS) for v in per.values()),
         'mismatching_cases':len(bad),'mismatches':{k:v for k,v in list(bad.items())[:50]},'per_case':per,'PASS':not bad and len(per)>0}
    write_new(d/'RECOUNT_033.json',out);print(json.dumps({k:v for k,v in out.items() if k!='per_case'},default=str));return 0 if out['PASS'] else 1


if __name__=='__main__':sys.exit(main())
