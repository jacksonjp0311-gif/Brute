import sys,time,random
from brute.scalesearch14 import active14
from experiments import worlds_050 as W50
from experiments.brute_study_033 import passive,StepWorld
seed=int(sys.argv[1]);m=int(sys.argv[2]);T=int(sys.argv[3]);dl=float(sys.argv[4])
w=W50.world(seed,'scale20');rng=random.Random(seed)
em=[rng.randrange(m) for _ in range(w.n)] if m!=4 else list(w.emissions)
_,acts,_=passive(StepWorld(w),seed);acts=acts[:T]
q=w.start;codes=[em[q]]
for a in acts:q=w.transitions[q][a];codes.append(em[q])
st={'q':q}
def observe(a):st['q']=w.transitions[st['q']][a];return 1<<em[st['q']]
t=time.time();r=active14([1<<c for c in codes],acts,3,m,20,observe,time.perf_counter()+dl,K=400,query_s=dl)
M=r['final']['model'];
print(seed,m,T,r['stop'],r['final']['n_min'],r['used'],len(r['rounds']),round(time.time()-t,1),flush=True)
