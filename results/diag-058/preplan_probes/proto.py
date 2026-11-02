import sys,time,itertools
from pysat.solvers import Solver
from brute.scalesearch14 import Inc14
from brute.scalesearch import simulate
from brute.scalesearch8 import run_word
from brute.region import codes_mask
from experiments import worlds_050 as W50
from experiments.worlds_026 import trajectory
from experiments.brute_study_033 import StepWorld,passive
def solve(R,assume,B,C=50000):
    sp=0
    while sp<B:
        b0=int(R.s.accum_stats().get("conflicts",0));R.s.conf_budget(min(C,B-sp));r=R.s.solve_limited(assumptions=assume);sp+=int(R.s.accum_stats().get("conflicts",0))-b0
        if r is not None:return r,sp
    return None,sp
seed=int(sys.argv[1]);B=int(sys.argv[2])
w=W50.world(seed,'scale20');masks,acts,rd=passive(StepWorld(w),seed)
R=Inc14(20,3,4,'g3').sync(masks,acts)
t=time.time();r,sp=solve(R,[],B);print('base',r,sp,round(time.time()-t,1))
mod=set(x for x in R.s.get_model() if x>0);d,e=R.machine(mod);ok,s,_=simulate(d,e,acts,masks)
q=w.start
for a in acts:q=w.transitions[q][a]
def fc(word):
    p=run_word(d,e,s,word);v=R._v;g=v();cl=[];n=20;h=len(word)
    y=[[v() for _ in range(n)] for _ in range(h+1)];D=[v() for _ in range(h+1)]
    for q_ in range(n):cl+= [[-R.x[R.T][q_],y[0][q_]],[R.x[R.T][q_],-y[0][q_]]]
    for j in range(1,h+1):
        cl.append(y[j])
        for i in range(n):
            for i2 in range(i+1,n):cl.append([-y[j][i],-y[j][i2]])
        for q_ in range(n):
            for r_ in range(n):cl.append([-y[j-1][q_],-R.d[q_][word[j-1]][r_],y[j][r_]])
        for q_ in range(n):cl.append([-D[j],-y[j][q_],-R.e[q_][p[j-1]]])
    cl.append(D[1:])
    for c in cl:R.s.add_clause([-g]+c)
    t=time.time();res,sp=solve(R,[g],B);R.s.add_clause([-g])
    tru=run_word(w.transitions,w.emissions,q,word)
    return res,sp,round(time.time()-t,2),p==tru
for h in (1,2,4):
    for word in list(itertools.product(range(3),repeat=h))[:9]:
        print(h,word,fc(list(word)),flush=True)
