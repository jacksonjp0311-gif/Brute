"""Build experiments/truth_076.json (refuses overwrite): the minimal Moore machine of each study-076 target, derived by an ORACLE that is
independent of Brute: a breadth-first search over real CPython incremental decoder states (identified by decoder.getstate() plus the
last reading), then Moore partition refinement. getstate() is used ONLY here (the runner's adapter never touches it). Moore view as in
experiments/truth_069: state = decoder state, emission code 2*(non-empty)+(has U+FFFD), start 0 = a fresh decoder.
  PYTHONPATH=. python scripts/make_truth_076.py [--check]"""
import codecs,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common import write_new,load,check
from experiments import targets_076 as TG
OUT=ROOT/'experiments/truth_076.json';CAP=400


def code(s):return 2*(1 if len(s)>0 else 0)+(1 if '\ufffd' in s else 0)


def oracle(codec,bs):
    def mk(hist):
        d=codecs.getincrementaldecoder(codec)('replace');r=0
        for b in hist:r=code(d.decode(bytes([b])))
        return d,r
    d0,r0=mk(());idx={(d0.getstate(),r0):0};E=[r0];H=[()];T=[[None]*len(bs)];Q=[0];i=0
    while i<len(Q):
        s=Q[i];i+=1
        for a,b in enumerate(bs):
            d,_=mk(H[s]);r=code(d.decode(bytes([b])));k=(d.getstate(),r)
            if k not in idx:
                check(len(idx)<CAP,'oracle cap');idx[k]=len(idx);E.append(r);H.append(H[s]+(b,));T.append([None]*len(bs));Q.append(idx[k])
            T[s][a]=idx[k]
    n=len(T);part=list(E)
    while True:
        sig={};new=[sig.setdefault((part[s],tuple(part[T[s][a]] for a in range(len(bs)))),len(sig)) for s in range(n)]
        if len(set(new))==len(set(part)):break
        part=new
    cls={};order=[]
    for s in range(n):                                   # renumber classes by first reachable state; class of state 0 is 0
        if part[s] not in cls:cls[part[s]]=len(cls);order.append(s)
    Tm=[[cls[part[T[s][a]]] for a in range(len(bs))] for s in order];Em=[E[s] for s in order]
    return {'codec':codec,'bytes':list(bs),'reachable_states':n,'n':len(order),'transitions':Tm,'emissions':Em}


def build():return {'schema':'brute.truth.v76','oracle':'BFS over CPython decoder getstate()+last reading, then Moore minimisation','python':sys.version.split()[0],
                    'targets':{name:oracle(*TG.TARGETS[name]) for name in TG.TARGETS}}


if __name__=='__main__':
    r=build()
    if '--check' in sys.argv:check(load(OUT)==r,'truth_076 differs');print('truth_076 --check ok')
    else:write_new(OUT,r);print('wrote',OUT)
    print({k:(v['n'],v['reachable_states']) for k,v in r['targets'].items()})
