"""Scratch diagnosis for study-029 (amendment BRUTE_PLAN_029_A1): what in S2 / S3 costs more than S1?
Smoke seeds 9590001-9590030 only (declared smoke range of study-029; disjoint from targets); never a gate input.
Runs whole arms (55 s, eps 0, the study-028 per-step protocol) with per-mechanism variants and solver timing by result.
Variants:
  S1          frozen RegionSpace(16): one fresh RegionK (g3, first-visit symmetry, 100000-conflict budget) per step
  S1_nosym    S1 with RegionK(symmetry=False)
  S1_g4       S1 on glucose 4
  S2          ScaleRegion(16) (incremental, BFS-canonical symmetry, deepening, pool + chain witnesses, dist clauses, g4)
  S2_g3       S2 on glucose 3
  S2_fresh    S2 with a fresh solver per step (kept clauses only)
  S2_nobfs    S2 without the BFS-canonical clauses (u-chain and unused-state fixing kept)
  S2_nodist   S2 without distinguishability clauses
  S3          ScaleRegion3(16) (v0.25.0)
  PYTHONPATH=. python scripts/diag_029.py --out results/diag-029/S1_COST_029.json --workers 8
"""
import argparse,json,sys,time
from pathlib import Path
from time import perf_counter
from concurrent.futures import ProcessPoolExecutor
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
SMOKE=(9590001,9590030)
VARIANTS=('S1','S1_nosym','S1_g4','S2','S2_g3','S2_fresh','S2_nobfs','S2_nodist','S3')


def _instrument(T):
    """Wrap solver entry points to time solves by result (scratch only, inside the worker process)."""
    import brute.region as R,brute.scalesearch as SS
    o1=R.RegionK._solve
    def s1(self,assume):
        t=perf_counter();r=o1(self,assume);T['solve_'+{True:'sat',False:'unsat',None:'unk'}[r]].append(perf_counter()-t);return r
    R.RegionK._solve=s1
    o2=SS._Skeleton.solve
    def s2(self,assume,deadline):
        t=perf_counter();r=o2(self,assume,deadline);T['solve_'+{True:'sat',False:'unsat',None:'unk'}[r]].append(perf_counter()-t);return r
    SS._Skeleton.solve=s2
    ob=R.RegionK.__init__
    def b(self,*a,**k):
        t=perf_counter();ob(self,*a,**k);T['build'].append(perf_counter()-t)
    R.RegionK.__init__=b


def make(v,k):
    import brute.region as R,brute.scalesearch as SS
    from experiments import brute_study_026 as S26
    from experiments import worlds_026 as W
    if v.startswith('S1'):
        A=S26._S1(k)
        if v=='S1_nosym':
            orig=R.RegionK.__init__
            def nos(self,*a,**kw):kw['symmetry']=False;orig(self,*a,**kw)
            R.RegionK.__init__=nos
        if v=='S1_g4':
            orig=R.RegionK.__init__
            def g4(self,*a,**kw):kw['solver']='g4';orig(self,*a,**kw)
            R.RegionK.__init__=g4
        return A
    A=S26._S2.__new__(S26._S2)
    if v=='S3':
        from brute.scalesearch3 import ScaleRegion3;A.R=ScaleRegion3(16,k,W.S_BITS,10.0);return A
    kw={}
    if v=='S2_g3':kw['solver']='g3'
    if v=='S2_fresh':kw['fresh']=True
    if v=='S2_nodist':kw['distinct']=False
    if v=='S2_nobfs':
        orig=SS._Skeleton.__init__
        def nobfs(self,n,kk,m,solver=SS.SOLVER):
            from pysat.solvers import Solver
            self.n=n;self.k=kk;self.m=m;self.nv=0;cl=[];v_=self._v;N=range(n);K=range(kk);M=range(m)
            self.d=[[[v_() for _ in N] for _ in K] for _ in N];self.e=[[v_() for _ in M] for _ in N];self.u=[v_() for _ in N]
            for q in N:
                for a in K:cl+=self._one(self.d[q][a])
                cl+=self._one(self.e[q])
            cl.append([self.u[0]])
            for q in range(1,n):
                cl.append([-self.u[q],self.u[q-1]])
                for a in K:cl.append([self.u[q],self.d[q][a][0]])
                cl.append([self.u[q],self.e[q][0]])
                for i in N:
                    for a in K:cl.append([-self.d[i][a][q],self.u[q]])
            self.solver_name=solver;self.base=cl;self.s=Solver(name=solver,bootstrap_with=cl);self.clauses=len(cl)
        SS._Skeleton.__init__=nobfs
    A.R=SS.ScaleRegion(16,k,W.S_BITS,10.0,**kw);return A


def run(job):
    fam,seed,v,budget=job
    from experiments import worlds_026 as W
    from experiments import brute_study_026 as S26
    T={'solve_sat':[],'solve_unsat':[],'solve_unk':[],'build':[]};_instrument(T)
    w=W.world(seed,fam);tr=W.trajectory(w,seed,0.0);truth=S26.truth(w,tr);A=make(v,w.k)
    t0=perf_counter();dl=t0+budget;U=0;planned=w.k*W.HORIZON;steps=0;qmax=0.0;omax=0.0;tq_sum=0.0;to_sum=0.0;miss=0;exact=0
    A.initialize(tr['readings'][0],dl)
    for i in range(W.HORIZON):
        if perf_counter()>=dl:break
        ok=True
        for b in range(w.k):
            if perf_counter()>=dl:ok=False;break
            tq=perf_counter();s,u=A.support(b,dl);d=perf_counter()-tq;qmax=max(qmax,d);tq_sum+=d
            if u==0 and s is not None:
                exact+=1;miss+=truth[i][b] not in s
        if not ok:break
        steps=i+1
        if i<W.HORIZON-1:
            to=perf_counter();A.observe(tr['actions'][i],tr['readings'][i+1],dl);d=perf_counter()-to;omax=max(omax,d);to_sum+=d
    wall=perf_counter()-t0;A.close()
    agg={k_:{'n':len(x),'s':round(sum(x),2),'max':round(max(x),2) if x else 0} for k_,x in T.items()}
    return {'fam':fam,'seed':seed,'v':v,'steps':steps,'exact':exact,'U':planned-exact,'U_frac':round((planned-exact)/planned,3),
            'truth_missing':miss,'wall':round(wall,1),'qmax':round(qmax,2),'omax':round(omax,2),'t_query':round(tq_sum,1),
            't_observe':round(to_sum,1),'solver':agg}


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--out',required=True);ap.add_argument('--workers',type=int,default=8)
    ap.add_argument('--fams',default='scale8,scale12');ap.add_argument('--seeds',default='9590001,9590002,9590003')
    ap.add_argument('--variants',default=','.join(VARIANTS));ap.add_argument('--budget',type=float,default=55.0)
    a=ap.parse_args();seeds=[int(s) for s in a.seeds.split(',')]
    assert all(SMOKE[0]<=s<=SMOKE[1] for s in seeds),'smoke seeds only'
    jobs=[(f,s,v,a.budget) for f in a.fams.split(',') for s in seeds for v in a.variants.split(',')]
    t0=time.time();out=[]
    with ProcessPoolExecutor(a.workers,max_tasks_per_child=1) as ex:   # one job per process: variant patches never leak
        for r in ex.map(run,jobs):out.append(r);print(json.dumps({k:r[k] for k in ('fam','seed','v','steps','U','wall','qmax','omax')}),flush=True)
    Path(a.out).parent.mkdir(parents=True,exist_ok=True)
    with open(a.out,'x') as fh:json.dump({'schema':'brute.diag/1','id':Path(a.out).stem,'phase':'scratch, before amendment 029_A1 and seedcheck_029; smoke seeds only',
        'label':'Observed (numbers)','workers':a.workers,'budget_s':a.budget,'runs':out,'elapsed_s':round(time.time()-t0,1)},fh,indent=1)
