"""Study 069 pre-run truth check (BRUTE_PLAN_069 ground_truth.pre_run_check). No Brute involved: for every target and every action
sequence of length 0..7, a fresh public-interface decoder (experiments/targets_069.replay) and the hand truth machine
(experiments/truth_069) must give the same reading after every step. Also checks each truth machine is minimal (all states reachable
and pairwise distinguishable) with N_TRUE states. A disagreement is published and never changes the truth.
  PYTHONPATH=. python scripts/truthcheck_069.py --write   (writes results/study-069/TRUTHCHECK.json, refuses overwrite)
  PYTHONPATH=. python scripts/truthcheck_069.py --check   (recomputes and compares with the committed file)"""
import itertools,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments import targets_069 as TG
from experiments import truth_069 as TR
from experiments.brute_common import load,write_new,check
from brute.api.certify32r import equivalent
OUT=ROOT/'results/study-069/TRUTHCHECK.json';MAXLEN=7;NAMES=('U3','U4','W16','EJ','GB')


def truth_readings(w,acts):
    q=w.start;out=[w.emissions[q]]
    for a in acts:q=w.transitions[q][a];out.append(w.emissions[q])
    return [[c>>1&1,c&1] for c in out]


def minimal(w):
    T,E=w.transitions,w.emissions;n=len(T);seen={w.start};q=[w.start]
    while q:
        s=q.pop()
        for t in T[s]:
            if t not in seen:seen.add(t);q.append(t)
    dist=all(not equivalent(T,E,T,E,i,j)[0] for i in range(n) for j in range(i+1,n))
    return len(seen)==n and dist


def compute():
    per={}
    for name in NAMES:
        w=TR.world(name);check(tuple(TG.TARGETS[name][1])==tuple(w.bytes) and TG.TARGETS[name][0]==w.codec,'truth and adapter disagree on target '+name)
        n=0;nbad=0;ex=[]
        for L in range(MAXLEN+1):
            for acts in itertools.product(range(3),repeat=L):
                n+=1;live=[list(r) for r in TG.replay(name,list(acts))];tr=truth_readings(w,acts)
                if live!=tr:
                    nbad+=1
                    if len(ex)<20:ex.append({'acts':list(acts),'live':live,'truth':tr})
        per[name]={'sequences':n,'max_len':MAXLEN,'disagreements':nbad,'examples':ex,'states':len(w.transitions),
                   'n_true':TR.N_TRUE[name],'minimal':minimal(w) and len(w.transitions)==TR.N_TRUE[name]}
    return {'study':'BRUTE-0650-RESETDECODER-069','python':sys.version.split()[0],'targets':per,
            'agree':all(v['disagreements']==0 and v['minimal'] for v in per.values())}


if __name__=='__main__':
    r=compute()
    if '--write' in sys.argv:write_new(OUT,r);print('wrote',OUT)
    elif '--check' in sys.argv:check(load(OUT)==r,'truthcheck differs from the committed file');print('truthcheck --check ok')
    print('agree',r['agree'],{k:(v['sequences'],v['disagreements'],v['states'],v['minimal']) for k,v in r['targets'].items()})
