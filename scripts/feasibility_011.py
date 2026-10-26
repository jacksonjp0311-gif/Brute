"""7-8 state feasibility block of study-011 (BRUTE_PLAN_011 feasibility_7_8; ungated, optional stream "feas").

Per seed of feasibility_seeds (n6, n7, n8): a random.Random(seed) Moore machine with n states, 2 actions, 4 codes
(2 bits), transitions and outputs uniform, regenerated until every state is reachable from state 0; 32 uniform random
actions; each observation bit hidden with probability 0.35. At T in {8, 16, 24, 32}: build brute.region.RegionK(n, 2, 4,
masks[0..T], actions[0..T-1], conf_budget=100000, symmetry=True) with state bound n and time the build, feasible,
support(0), support(1), saturated(), y1k(0, mask_T), y1k(1, mask_T); record variables, clauses and unknowns.
Every measurement is appended to --checkpoint (fsync), so a budget stop leaves partial evidence; a restart skips
measured (seed, T). --summarize-only writes the report from the checkpoint. Seeds are asserted by
scripts/check_seeds_011.check_run_seeds('feas', ...) before any machine is generated.
"""
from __future__ import annotations
import argparse,json,os,random,statistics,time
from pathlib import Path
from bgr90.symbolic import mask_for_observation
from brute.region import RegionK
from experiments.brute_common import load,check
from experiments.brute_common_009 import repair_torn_tail
from scripts.check_seeds_011 import check_run_seeds

ROOT=Path(__file__).resolve().parents[1]
PLAN=ROOT/'experiments/BRUTE_PLAN_011.json'
TS=(8,16,24,32);STEPS=32;MASK=0.35;CONF=100000;K=2;M=4


def machine(seed,n):
    """(delta, out, actions, observations) of the seed's reachable random Moore machine and walk."""
    rng=random.Random(seed)
    while True:
        d=[[rng.randrange(n) for _ in range(K)] for _ in range(n)];e=[rng.randrange(M) for _ in range(n)]
        seen={0};st=[0]
        while st:
            q=st.pop()
            for r in d[q]:
                if r not in seen:seen.add(r);st.append(r)
        if len(seen)==n:break
    def ob(q):return tuple(None if rng.random()<MASK else (e[q]>>j)&1 for j in (0,1))
    q=0;obs=[ob(q)];acts=[]
    for _ in range(STEPS):a=rng.randrange(K);q=d[q][a];acts.append(a);obs.append(ob(q))
    return d,e,acts,obs


def measure(seed,n,T):
    d,e,acts,obs=machine(seed,n);masks=[mask_for_observation(o) for o in obs[:T+1]];W={}
    t=time.perf_counter();R=RegionK(n,K,M,masks,acts[:T],CONF,symmetry=True);W['build']=time.perf_counter()-t
    t=time.perf_counter();f=R.feasible;W['feasible']=time.perf_counter()-t;out={'feasible':f}
    for name,fn in (('support0',lambda:R.support(0)),('support1',lambda:R.support(1)),('saturated',R.saturated),
                    ('y1k0',lambda:R.y1k(0,masks[-1])),('y1k1',lambda:R.y1k(1,masks[-1]))):
        t=time.perf_counter();r,u=fn();W[name]=time.perf_counter()-t
        out[name]=list(r) if isinstance(r,tuple) else r;out[name+'_unknown']=u
    rec={'seed':seed,'n':n,'T':T,'variables':R.base_vars,'clauses':R.base_clauses,'solver_calls':R.calls,'unknown':R.unknown,
         **out,'wall_informational':{k:round(v,6) for k,v in W.items()},'total_wall_informational':round(sum(W.values()),6)}
    R.close();return rec


def jobs(plan,smoke=False):
    """Held-out feasibility jobs; smoke: seeds 4190028 / 4190029 / 4190030 for n = 6 / 7 / 8 (smoke range only)."""
    J=[]
    if smoke:
        lo,hi=plan['smoke_seeds']['range'];S=[(hi-2,6),(hi-1,7),(hi,8)];check_run_seeds('smoke',[s for s,_ in S],plan)
        return [(s,n,T) for s,n in S for T in TS]
    for name,n in (('n6',6),('n7',7),('n8',8)):
        lo,hi=plan['feasibility_seeds'][name];seeds=list(range(lo,hi+1));check_run_seeds('feas',seeds,plan)
        for s in seeds:
            for T in TS:J.append((s,n,T))
    return J


def summarize(recs,plan,smoke=False):
    rep={'schema':'brute.feasibility-011.v1','study':plan['study'],'gated':False,
         'labels':'per-case timings Observed (shared 8-CPU box, informational); projections Inferred',
         'smoke':smoke,'expected_measurements':len(jobs(plan,smoke)),'measurements':len(recs),'cells':{}}
    for n in (6,7,8):
        for T in TS:
            R=[r for r in recs if r['n']==n and r['T']==T]
            if not R:continue
            w=sorted(r['total_wall_informational'] for r in R)
            rep['cells'][f'n{n}/T{T}']={'cases':len(R),'feasible_true':sum(r['feasible'] is True for r in R),
                'unknown_queries':sum(r['unknown'] for r in R),'solver_calls':sum(r['solver_calls'] for r in R),
                'unknown_fraction':round(sum(r['unknown'] for r in R)/max(1,sum(r['solver_calls'] for r in R)),6),
                'wall_median_s':round(statistics.median(w),6),'wall_p95_s':round(w[min(len(w)-1,int(0.95*len(w)))],6),'wall_max_s':round(w[-1],6),
                'variables_median':statistics.median(r['variables'] for r in R),'clauses_median':statistics.median(r['clauses'] for r in R)}
    rep['all_feasible']=all(r['feasible'] is True for r in recs)
    proj={}
    for n in (7,8):
        c=rep['cells'].get(f'n{n}/T32')
        if c:per_q=c['wall_median_s']/7;proj[f'n{n}']={'per_case_s_44_steps_14_queries_per_step':round(per_q*14*44,1),
                                                    'per_792_cases_s':round(per_q*14*44*792,0),'basis':'Inferred: median T=32 query wall / 7 x 14 queries x 44 steps'}
    rep['projection_inferred']=proj;return rep


def main(argv=None):
    ap=argparse.ArgumentParser();ap.add_argument('--checkpoint',required=True);ap.add_argument('--output',required=True)
    ap.add_argument('--summarize-only',action='store_true');ap.add_argument('--limit',type=int);ap.add_argument('--smoke',action='store_true')
    a=ap.parse_args(argv);out=Path(a.output)
    if out.exists():raise SystemExit(f'refusing to overwrite {out}')
    plan=load(PLAN);J=jobs(plan,a.smoke)
    if a.limit:J=J[:a.limit]
    ck=Path(a.checkpoint);ck.parent.mkdir(parents=True,exist_ok=True);ck.touch();repair_torn_tail(ck)
    recs={(r['seed'],r['T']):r for r in (json.loads(l) for l in ck.read_text().split('\n') if l.strip())}
    if not a.summarize_only:
        with open(ck,'a') as fh:
            for s,n,T in J:
                if (s,T) in recs:continue
                r=measure(s,n,T);recs[(s,T)]=r;fh.write(json.dumps(r,sort_keys=True)+'\n');fh.flush();os.fsync(fh.fileno())
                print(f"[{time.strftime('%H:%M:%S')}] feas n{n} seed {s} T{T} {r['total_wall_informational']:.3f}s unk {r['unknown']}",flush=True)
    rep=summarize(list(recs.values()),plan,a.smoke);out.write_text(json.dumps(rep,indent=1,sort_keys=True)+'\n');print(json.dumps(rep['cells'].get('n8/T32')))


if __name__=='__main__':main()
