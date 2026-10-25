"""GR2-prime scaling block for study-007 (BRUTE_PLAN_007 scaling_block; reported, not gated).

For each alphabet (2a2s = big6 generator, 3a2s = act3 generator, 2a3s = sens3 generator), seed in scaling_block.seeds and
family bound n in family_bounds: 44 passive steps at mask 0.35; at every step a RegionK over the whole history answers
feasibility, support(b) for every action, saturated() and y1k(b, last mask) for every action (no lookahead; margin not
built). Timing fields are *_informational (wall clock; noisy, non-monotone). For n<=6 the second implementation's row
enumeration (experiments/v050_reference.py, row budget 160000) runs on the same steps; when it has not exhausted its
budget, its support / saturation / Y1k answers are compared with the SAT answers (exact agreement count).
Checkpointed per job (SCALING_CHECKPOINT.jsonl); SCALING_007.json refuses to overwrite."""
import argparse,math,statistics
from pathlib import Path
from time import perf_counter
from concurrent.futures import ProcessPoolExecutor,as_completed
from brute.region import RegionK,codes_mask
from brute.evaluation import no_time
from experiments.worlds_007 import breadth_world,passive_actions
from experiments import v050_reference as R
from experiments.brute_common_007 import PLAN,FREEZE,STUDY_DIR,load,sha,write_new,check_freeze,check,Checkpoint

ALPHA={'2a2s':'big6','3a2s':'act3','2a3s':'sens3'}


def _job(args):
    alpha,seed,n,plan=args;S=plan['scaling_block'];w=breadth_world(seed,ALPHA[alpha]);k,s,m=w.k,w.s,w.m
    rate=S['mask_rate'];acts=passive_actions(seed,S['steps'],k);h=w.start;obs=[w.observed(h,rate,-1)]
    for i,a in enumerate(acts):h=w.next(h,a);obs.append(w.observed(h,rate,i))
    masks=[codes_mask(o,s) for o in obs];enum=n<=6;rows=R.k_initial(R.codes_of(obs[0],s),k) if enum else None
    exhausted_at=None;steps=[];t_case=perf_counter();truncated=False;agree=disagree=0
    for t in range(len(acts)+1):
        if t>0 and enum and exhausted_at is None and rows is not None:
            try:
                rows,st=R.k_observe(rows,acts[t-1],R.codes_of(obs[t],s),n,k,S.get('enumeration_row_budget',160000))
                if st!='supported':rows=None
            except R.RefBudget:exhausted_at=t;rows=None
        t0=perf_counter();g=RegionK(n,k,m,masks[:t+1],list(acts[:t]),conf_budget=S['conf_budget'])
        unk=0;feas=g.feasible;sup={};y={}
        if feas is True:
            for b in range(k):
                sup[b],u=g.support(b);unk+=u
                y[b],u=g.y1k(b,masks[t]);unk+=u
            sat,u=g.saturated();unk+=u
        else:sat=None
        dt=perf_counter()-t0;size=g.size;calls=g.calls;g.close()
        rec={'t':t,'feasible':feas,'unknown_answers':unk+(feas is None),'solve_calls':calls,'variables':size['variables'],
             'clauses':size['clauses'],'seconds_informational':dt}
        if enum:
            rec['enum_rows']=None if rows is None else len(rows);rec['enum_exhausted']=exhausted_at is not None
            if rows is not None and feas is True and unk==0:
                ok=all(tuple(R.k_support(rows,b,n,k,m))==tuple(sup[b]) and tuple(sorted(R.k_y1k(rows,b,R.codes_of(obs[t],s),n,k,m)))==tuple(y[b]) for b in range(k))
                ok=ok and R.k_saturated(rows,n)==sat;agree+=ok;disagree+=not ok;rec['enum_agrees']=ok
        steps.append(rec)
        if perf_counter()-t_case>S['case_wall_cap_seconds']:truncated=True;break
    return f'{alpha}/{seed}/{n}',{'alphabet':alpha,'seed':seed,'n':n,'k':k,'s':s,'steps':steps,'truncated_by_wall_cap':truncated,
        'enumeration':{'run':enum,'exhausted_at_step':exhausted_at,'agree_steps':agree,'disagree_steps':disagree},
        'case_seconds_informational':perf_counter()-t_case}


def summarise(cases,plan):
    S=plan['scaling_block'];out={}
    for alpha in ALPHA:
        rows=[];pts=[]
        for n in S['family_bounds']:
            cs=[c for c in cases if c['alphabet']==alpha and c['n']==n];st=[r for c in cs for r in c['steps']]
            secs=[r['seconds_informational'] for r in st]
            e={'n':n,'cases':len(cs),'steps':len(st),'mean_step_seconds_informational':statistics.mean(secs),
               'median_step_seconds_informational':statistics.median(secs),'max_step_seconds_informational':max(secs),
               'max_clauses':max(r['clauses'] for r in st),'max_variables':max(r['variables'] for r in st),
               'unknown_answers':sum(r['unknown_answers'] for r in st),'truncated_cases':sum(c['truncated_by_wall_cap'] for c in cs),
               'infeasible_steps':sum(r['feasible'] is False for r in st)}
            if n<=6:
                e['enumeration_exhausted_cases']=sum(c['enumeration']['exhausted_at_step'] is not None for c in cs)
                e['enumeration_max_rows']=max((r['enum_rows'] or 0) for r in st)
                e['enumeration_agree_steps']=sum(c['enumeration']['agree_steps'] for c in cs)
                e['enumeration_disagree_steps']=sum(c['enumeration']['disagree_steps'] for c in cs)
            rows.append(e);pts.append((math.log(n),math.log(e['mean_step_seconds_informational'])))
        mx=statistics.mean(p[0] for p in pts);my=statistics.mean(p[1] for p in pts)
        slope=sum((x-mx)*(y-my) for x,y in pts)/sum((x-mx)**2 for x,_ in pts)
        out[alpha]={'by_bound':rows,'loglog_slope_mean_time_vs_n_informational':slope,
                    'caveat':'SAT time is noisy and non-monotone; the slope rests on 5 points (one per bound) and is not a law'}
    return out


def main(output,workers=6,smoke=False,limit=None):
    output=Path(output);plan=load(PLAN)
    if not smoke:check_freeze()
    check(not output.exists(),'refusing overwrite '+str(output));S=plan['scaling_block']
    jobs=[(alpha,seed,n,plan) for alpha in ALPHA for seed in range(S['seeds'][0],S['seeds'][1]+1) for n in S['family_bounds']]
    if limit:jobs=jobs[:limit]
    ck=Checkpoint(output.parent/(output.stem+'_CHECKPOINT.jsonl'));todo=[j for j in jobs if f'{j[0]}/{j[1]}/{j[2]}' not in ck.done]
    todo.sort(key=lambda j:-j[2])
    with ProcessPoolExecutor(workers) as ex:
        for i,fu in enumerate(as_completed([ex.submit(_job,j) for j in todo])):
            k,c=fu.result();ck.add(k,c);print(f'scaling {i+1}/{len(todo)} {k} {c["case_seconds_informational"]:.1f}s',flush=True)
    cases=[ck.done[f'{a}/{s}/{n}'] for a,s,n,_ in jobs]
    out={'schema':'brute.scaling.v7','study':plan['study'],'use':S['use'],'summary':summarise(cases,plan),'cases':cases,
         'plan_sha256':sha(PLAN),'freeze_sha256':None if smoke else sha(FREEZE)}
    write_new(output,out);return out


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--output',default=str(STUDY_DIR/'SCALING_007.json'))
    ap.add_argument('--workers',type=int,default=6);ap.add_argument('--smoke',action='store_true');ap.add_argument('--limit',type=int)
    a=ap.parse_args();out=main(a.output,a.workers,a.smoke,a.limit)
    import json;print(json.dumps(no_time(out['summary']),indent=1))
