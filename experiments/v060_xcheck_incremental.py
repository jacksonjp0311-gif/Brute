"""Post-release verification re-run of GX2' (v0.6.0) with the incremental second encoding.

NOT a frozen v0.6.0 artifact and cannot change the frozen GX2' verdict (FAIL, incomplete coverage, BRUTE_PLAN_008).
The decision logic is the frozen one: `audit`, `x_score`, `x_volume`, `x_rule`, `summarize`, `load_cases`, `plan_view`
are imported unchanged from experiments/v060_xcheck.py. Only the oracle is replaced: instead of building a new
brute.xcheck_sat.XRegion (full re-encoding) for every evidence prefix at every step, IncOracle keeps one
brute.xcheck_sat_incremental.IncSolver per (case, bound N) alive across steps and arms and adds only the new layer.

The memo semantics are identical to the frozen Oracle (answers keyed by (bound, evidence, query, args), kept for the
whole case, a budget hit raises Unchecked).
"""
from __future__ import annotations
import argparse,json,os,time
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor,as_completed
from experiments.brute_common import load,VerificationError
from experiments.v060_xcheck import (audit,summarize,load_cases,plan_view,Unchecked,ARMS_008,PLAN)
from experiments.v050_reference import breadth_world
from brute.xcheck_sat import CONF_BUDGET
from brute.xcheck_sat_incremental import IncSolver


class IncOracle:
    def __init__(self,k,m,budget=CONF_BUDGET,log=None,symmetry=False):
        self.k=k;self.m=m;self.budget=budget;self.res={};self.solvers={};self.log=log;self.symmetry=symmetry
        self.queries=0;self.unknown_queries=0;self.witness_failures=0;self.regions=0

    def _sol(self,N):
        if N not in self.solvers:self.solvers[N]=IncSolver(N,self.k,self.m,self.budget,self.symmetry)
        return self.solvers[N]

    def q(self,N,masks,acts,name,*args):
        key=(N,masks,acts,name,args)
        if key not in self.res:
            X=self._sol(N);L=X.layer(masks,acts)
            if name=='feasible':r=X.feasible(L);u=int(r is None)
            elif name=='support':r,u=X.support(L,*args)
            elif name=='saturated':r,u=X.saturated(L)
            elif name=='y1k':r,u=X.y1k(L,*args)
            else:raise ValueError(name)
            self.res[key]=(r,u)
            if self.log is not None:self.log.append((key,r,u))
        r,u=self.res[key]
        if u:raise Unchecked(name)
        return r

    def status(self,N,masks,acts):
        return 'supported' if self.q(N,masks,acts,'feasible') else 'grammar_contradicted'

    def flush(self):
        pass  # solvers stay alive for the whole case (that is the point)

    def close(self):
        for X in self.solvers.values():
            self.queries+=X.queries;self.unknown_queries+=X.unknown;self.witness_failures+=X.witness_failures
            self.regions+=X.rebuilds;X.close()
        self.layers=sum(X.layers_built for X in self.solvers.values());self.solvers={}


def case_job(x):
    idx,c,plan,tau7,arms,budget,sym=x;t0=time.time()
    w=breadth_world(c['seed'],c['family']);o=IncOracle(w.k,2**w.s,budget,symmetry=sym);out={};wall={}
    for arm in arms:
        if arm not in c['arms']:continue
        ta=time.time()
        try:out[arm]={'ok':True,'counts':audit(c,arm,plan,tau7,o)}
        except (VerificationError,KeyError,IndexError,TypeError,ValueError,AssertionError) as exc:
            out[arm]={'ok':False,'first_difference':f'{type(exc).__name__}: {exc}'}
        wall[arm]=round(time.time()-ta,3)
    o.close()
    return idx,{'family':c['family'],'seed':c['seed'],'mask_rate':c['mask_rate'],'arms':out,
                'queries':o.queries,'unknown_queries':o.unknown_queries,'witness_failures':o.witness_failures,
                'regions':o.regions,'layers':o.layers,'wall_per_arm_informational':wall,
                'wall_informational':round(time.time()-t0,3)}


def run(results,plan,arms,workers=4,checkpoint=None,budget=CONF_BUDGET,limit=None,cases_only=None,progress=None,symmetry=False):
    cases=[(i,c) for i,c in enumerate(load_cases(results)) if 'k' in c and any(a in c['arms'] for a in arms)]
    if cases_only is not None:cases=[(i,c) for i,c in cases if i in cases_only]
    if limit:cases=cases[:limit]
    view=plan_view(plan);tau7=view['tau7']['value']
    done={}
    if checkpoint and Path(checkpoint).exists():
        for line in open(checkpoint):
            if line.strip():r=json.loads(line);done[r['case']]=r['out']
    todo=[(i,c,view,tau7,arms,budget,symmetry) for i,c in cases if i not in done]
    # hardest first (big6, high mask rate) so the long tail starts early
    todo.sort(key=lambda j:(j[1]['family']!='big6',-j[1]['mask_rate'],j[0]))
    ck=open(checkpoint,'a') if checkpoint else None
    def save(i,out):
        done[i]=out
        if ck:ck.write(json.dumps({'case':i,'out':out})+'\n');ck.flush();os.fsync(ck.fileno())
        if progress:print(f"[{time.strftime('%H:%M:%S')}] case {i} {out['family']} {out['mask_rate']} wall {out['wall_informational']}s "
                          f"unk {out['unknown_queries']} ok {[v['ok'] for v in out['arms'].values()]} done {len(done)}",flush=True)
    if workers<=1:
        for j in todo:save(*case_job(j))
    else:
        with ProcessPoolExecutor(workers) as ex:
            fs=[ex.submit(case_job,j) for j in todo];todo=None
            for f in as_completed(fs):save(*f.result())
    if ck:ck.close()
    return summarize(done,arms,budget),done


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--results',required=True);ap.add_argument('--output',required=True)
    ap.add_argument('--arms',default=','.join(ARMS_008));ap.add_argument('--workers',type=int,default=4)
    ap.add_argument('--checkpoint');ap.add_argument('--limit',type=int);ap.add_argument('--plan',default=str(PLAN))
    ap.add_argument('--cases',help='comma-separated case indices (subset)')
    ap.add_argument('--symmetry',action='store_true',help='first-visit state naming in the incremental encoding (answers unchanged)')
    a=ap.parse_args();out=Path(a.output)
    if out.exists():raise SystemExit(f'refusing to overwrite {out}')
    plan=load(a.plan);t0=time.time()
    only=set(int(x) for x in a.cases.split(',')) if a.cases else None
    rep,_=run(a.results,plan,tuple(a.arms.split(',')),a.workers,a.checkpoint,limit=a.limit,cases_only=only,progress=True,symmetry=a.symmetry)
    rep['schema']='brute.xcheck-sat-incremental-report.v1'
    rep['wording']=('post-release verification re-run with the incremental second encoding (brute/xcheck_sat_incremental.py), '
                    'same author, no enumeration; not an independent audit; cannot change the frozen GX2\' verdict')
    rep['symmetry_breaking']=a.symmetry;rep['results_file']=a.results;rep['cases_subset']=sorted(only) if only else None;rep['wall_informational']=round(time.time()-t0,1)
    out.write_text(json.dumps(rep,indent=1,sort_keys=True)+'\n');print(json.dumps({k:v for k,v in rep.items() if k!='mismatches'},indent=1)[:3000])


if __name__=='__main__':main()
