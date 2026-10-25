import time,sys
sys.path.insert(0,'.')
from experiments.worlds_006 import world,next_hidden
from bgr89.worlds import actions
from bgr90.symbolic import mask_for_observation
from brute.geometry import ConstraintRegion,lookahead_score
def case(seed,fam,rate):
    w=world(seed,fam);h=w.start;init=w.observed(h,rate,-1)
    masks=[mask_for_observation(init)];acts=[]
    t0=time.perf_counter()
    for i,pa in enumerate(actions(seed,44)):
        r4=ConstraintRegion(4,masks,acts);r5=ConstraintRegion(5,masks,acts)
        if r4.feasible and r5.feasible:
            for b in (0,1):r4.support(b);r5.support(b);r4.fibre_support(b,[masks[-1]])
            r4.saturated()
            sc=[lookahead_score(r4,r5,a) for a in (0,1)]
        r4.close();r5.close()
        h=next_hidden(w,h,pa,i);o=w.observed(h,rate,i);masks.append(mask_for_observation(o));acts.append(pa)
    return time.perf_counter()-t0
for fam in ('cycle3','perm4','ood5'):
    print(fam,[round(case(1600001+k,fam,0.35),2) for k in range(2)])
