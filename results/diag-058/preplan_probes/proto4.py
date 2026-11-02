import sys,time,json
from pysat.solvers import Solver
from brute.scalesearch14 import Inc14
from experiments import worlds_050 as W50
from experiments.brute_study_033 import StepWorld,passive
arm,idx,sol,n=sys.argv[1],int(sys.argv[2]),sys.argv[3],int(sys.argv[4])
D57=json.load(open('results/study-057/main/RESULTS.json'))
c=D57['cases'][idx];seed=c['seed'];a=c['arms'][arm];w=W50.world(seed,'scale20');masks,acts,rd=passive(StepWorld(w),seed)
acts=acts+list(a['extra_acts']);masks=masks+list(a['extra_masks'])
R=Inc14(n,3,4,sol).sync(masks,acts);t=time.time();r=R.s.solve();print(seed,sol,n,r,R.s.accum_stats(),round(time.time()-t,1),flush=True)
