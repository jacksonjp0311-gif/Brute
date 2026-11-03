"""Study 068 pre-run truth check (BRUTE_PLAN_068 ground_truth.pre_run_check). No Brute involved: for every target and every action
sequence of length 0..7, a fresh public-interface decoder (experiments/targets_068.replay) and the hand truth machine
(experiments/truth_068) must give the same reading after every step. A disagreement is published and never changes the truth.
  PYTHONPATH=. python scripts/truthcheck_068.py --write   (writes results/study-068/TRUTHCHECK.json, refuses overwrite)
  PYTHONPATH=. python scripts/truthcheck_068.py --check   (recomputes and compares with the committed file)"""
import itertools,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments import targets_068 as TG
from experiments import truth_068 as TR
from experiments.brute_common import load,write_new,check
OUT=ROOT/'results/study-068/TRUTHCHECK.json';MAXLEN=7


def truth_readings(w,acts):
    q=w.start;out=[w.emissions[q]]
    for a in acts:q=w.transitions[q][a];out.append(w.emissions[q])
    return [[c>>1&1,c&1] for c in out]


def compute():
    per={}
    for name in TR.TARGETS:
        w=TR.world(name);check(tuple(TG.TARGETS[name][1])==tuple(w.bytes) and TG.TARGETS[name][0]==w.codec,'truth and adapter disagree on target '+name)
        n=0;bad=[]
        for L in range(MAXLEN+1):
            for acts in itertools.product(range(3),repeat=L):
                n+=1;live=[list(r) for r in TG.replay(name,list(acts))];tr=truth_readings(w,acts)
                if live!=tr and len(bad)<20:bad.append({'acts':list(acts),'live':live,'truth':tr})
        per[name]={'sequences':n,'max_len':MAXLEN,'disagreements':len(bad),'examples':bad}
    import sys as _s
    return {'study':'BRUTE-0640-REALDECODER-068','python':_s.version.split()[0],'targets':per,'agree':all(v['disagreements']==0 for v in per.values())}


if __name__=='__main__':
    r=compute()
    if '--write' in sys.argv:write_new(OUT,r);print('wrote',OUT)
    elif '--check' in sys.argv:check(load(OUT)==r,'truthcheck differs from the committed file');print('truthcheck --check ok')
    print('agree',r['agree'],{k:(v['sequences'],v['disagreements']) for k,v in r['targets'].items()})
