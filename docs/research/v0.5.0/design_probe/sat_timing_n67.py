import time,sys
sys.path.insert(0,'.')
from experiments.worlds_006 import world,next_hidden
from bgr89.worlds import actions
from bgr90.symbolic import mask_for_observation
from brute.geometry import ConstraintRegion,lookahead_score
def case(seed,fam,rate,nf):
    w=world(seed,fam);h=w.start;init=w.observed(h,rate,-1)
    masks=[mask_for_observation(init)];acts=[];mx=0
    t0=time.perf_counter()
    for i,pa in enumerate(actions(seed,44)):
        t1=time.perf_counter()
        r4=ConstraintRegion(nf,masks,acts);r5=ConstraintRegion(nf+1,masks,acts)
        if r4.feasible and r5.feasible:
            for b in (0,1):r4.support(b);r5.support(b);r4.fibre_support(b,[masks[-1]])
            r4.saturated()
            sc=[lookahead_score(r4,r5,a) for a in (0,1)]
        r4.close();r5.close();mx=max(mx,time.perf_counter()-t1)
        h=next_hidden(w,h,pa,i);o=w.observed(h,rate,i);masks.append(mask_for_observation(o));acts.append(pa)
    return round(time.perf_counter()-t0,2),round(mx,2)
for nf in (6,7):
  for fam in ('perm4','ood5'):
    print(nf,fam,[case(1600001+k,fam,r,nf) for k in range(2) for r in (0.1,0.6)],flush=True)
