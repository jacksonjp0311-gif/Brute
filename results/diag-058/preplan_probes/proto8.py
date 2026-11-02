import sys,time,random
from brute.scalesearch14 import stop_check14
from experiments import worlds_050 as W50
from experiments.worlds_026 import trajectory
from experiments.brute_study_033 import passive,StepWorld
seed=int(sys.argv[1]);m=int(sys.argv[2]);T=int(sys.argv[3])
w=W50.world(seed,'scale20');rng=random.Random(seed)
em=[rng.randrange(m) for _ in range(w.n)]
_,acts,_=passive(StepWorld(w),seed)
r2=random.Random(seed+1);acts=(acts+[r2.randrange(3) for _ in range(1000)])[:T]
q=w.start;codes=[em[q]]
for a in acts:q=w.transitions[q][a];codes.append(em[q])
masks=[1<<c for c in codes]
t=time.time();r=stop_check14(masks,acts,3,m,20,time.perf_counter()+float(sys.argv[4]),query_s=float(sys.argv[4]))
print(seed,m,T,r['stop'],r['n_min'],round(time.time()-t,1),flush=True)
