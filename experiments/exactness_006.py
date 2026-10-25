"""GR1 / GR1b / GR2 for study BRUTE-040-GEOMETRY-006 (experiments/BRUTE_PLAN_006.json, representation).

GR1  (gated): brute.geometry.ConstraintRegion rebuilt from each recorded evidence prefix reproduces, on every step of
     the sealed study-004 A/P and study-005 A3/P3 traces (taken AND counterfactual action): family/margin feasibility,
     support (n=4), margin_support (n=5), saturated, the Y1k decision (005), and the LU / LU-R experiment scores
     (active arms). Report = COUNT of mismatching (trace, step, field) items over everything; PASS iff 0.
GR1b (gated): the same on study-006 A4/P4, plus D2 (LU2-R scores) and F2 (2-step fibre decision, F2 LU-R scores) on
     the pre-registered subsample (first 4 seeds per family, all masks).
GR2  (reported): enumeration (bgr90 SymbolicLearner, n=2..6) vs ConstraintRegion (n=2..6, 8, 10, 12) on the passive
     sequences of 84 study-006 cases: per-step time, rows vs variables/clauses, agreement, log-log slopes.

Exclusions (pre-registered): steps where the enumeration's family or margin learner was budget_exhausted, and score
items in traces whose lookahead copies hit the row budget, are not compared and are counted separately.
The region is rebuilt from scratch at every step (no incremental solving), which is unfavourable to the region in GR2.
"""
from __future__ import annotations
import argparse,gzip,json,math,statistics
from time import perf_counter
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor
from bgr90.symbolic import SymbolicLearner,mask_for_observation
from brute.geometry import ConstraintRegion,lookahead_score
from experiments.brute_common import load,check

ROOT=Path(__file__).resolve().parents[1]
# arm -> (score rule or None, decision rule or None); score rule = (resync, fibre_w, depth)
SPEC={('004','A'):((False,0,1),None),('004','P'):(None,None),
      ('005','A3'):((True,0,1),'Y1k'),('005','P3'):(None,'Y1k'),
      ('006','A4'):((True,0,1),'Y1k'),('006','P4'):(None,'Y1k'),
      ('006','D2'):((True,0,2),'Y1k'),('006','F2'):((True,2,1),'F2')}
SUBSAMPLE_ARMS=('D2','F2')


def _cases(path):
    p=Path(path)
    if p.suffix=='.gz' or not p.exists():
        g=p if p.suffix=='.gz' else p.with_name(p.name+'.gz');return json.load(gzip.open(g))['cases']
    return load(p)['cases']


def _t(x):return None if x is None else tuple(x)


def replay(study,ci,c,arm):
    """Return (items_compared, mismatches[list], excluded_steps, excluded_score_items)."""
    score_rule,dec=SPEC[(study,arm)]
    t=c['arms'][arm];recs=t['trace'];full='support' in recs[0]
    diag=t['diagnostics']
    skip_scores=diag.get('lookahead_budget_hits',0)>0
    if not full and 'budget_exhausted' in (diag.get('family_status'),diag.get('margin_status')):
        return 0,[],len(recs),0
    masks=[mask_for_observation(c['initial_visible'])];acts=[]
    n=0;bad=[];ex_steps=0;ex_scores=0;fs=ms='supported';alarm=False
    for i,rec in enumerate(recs):
        a=rec['action']
        if fs=='budget_exhausted' or ms=='budget_exhausted':ex_steps+=1
        else:
            r4=ConstraintRegion(4,masks,acts);r5=ConstraintRegion(5,masks,acts)
            def miss(field,got,want):
                bad.append({'study':study,'case':ci,'seed':c['seed'],'family':c['family'],'mask_rate':c['mask_rate'],
                            'arm':arm,'step':rec['step'],'field':field,'region':got,'enumeration':want})
            if full:
                n+=2
                if r4.feasible!=(fs=='supported'):miss('family_feasible',r4.feasible,fs)
                if r5.feasible!=(ms=='supported'):miss('margin_feasible',r5.feasible,ms)
            sup={b:r4.support(b) for b in (0,1)}
            for b,f in ((a,rec),(1-a,rec['counterfactual'])):
                tag='' if b==a else 'counterfactual.'
                if full:
                    n+=2
                    if sup[b]!=_t(f['support']):miss(tag+'support',sup[b],f['support'])
                    ms_=r5.support(b)
                    if ms_!=_t(f['margin_support']):miss(tag+'margin_support',ms_,f['margin_support'])
                    if r4.feasible:
                        n+=1;sat=r4.saturated()
                        if sat!=f['saturated']:miss(tag+'saturated',sat,f['saturated'])
                if dec and (f['certificate'] is not None or f['reason']=='RESYNC_AMBIGUOUS'):
                    s=sup[b]
                    if s is None or len(s)!=1:
                        n+=1;miss(tag+'decision_support_not_single',s,f['certificate'])
                    else:
                        h=_hist(masks,acts,0 if dec=='Y1k' else 2)
                        n+=1;ok=r4.fibre_support(b,*h)==s
                        if ok!=(f['certificate'] is not None):miss(tag+dec+'_decision',ok,f['certificate'])
            if score_rule and 'experiment' in rec:
                if skip_scores:ex_scores+=2
                else:
                    resync,w,depth=score_rule
                    if not (r4.feasible and r5.feasible) or alarm:want=[0.,0.]
                    else:want=[lookahead_score(r4,r5,b,resync,w,depth) for b in (0,1)]
                    n+=2
                    for b in (0,1):
                        if want[b]!=rec['experiment']['scores'][b]:miss(f'score[{b}]',want[b],rec['experiment']['scores'][b])
            r4.close();r5.close()
        obs=rec['observed'];masks.append(mask_for_observation(obs));acts.append(a)
        if full:fs,ms=rec['family_status_after'],rec['margin_status_after']
        alarm=rec['alarm_after']
    return n,bad,ex_steps,ex_scores


def _hist(masks,acts,w):
    m=masks[-(w+1):];k=len(m)-1
    return m,(acts[len(acts)-k:] if k else [])


def _job(x):
    study,ci,c,arm=x;t0=perf_counter();r=replay(study,ci,c,arm);return (study,arm)+r+(perf_counter()-t0,)


def _subsample(cases):
    out=[];seen={}
    for ci,c in enumerate(cases):
        k=(c['family'],c['mask_rate']);seen.setdefault(k,[])
        if len(seen[k])<4:seen[k].append(ci);out.append(ci)
    return out


def exactness(jobs,workers):
    tot={};mism=[];t0=perf_counter()
    with ProcessPoolExecutor(workers) as ex:
        for study,arm,n,bad,es,esc,dt in ex.map(_job,jobs,chunksize=4):
            d=tot.setdefault(f'{study}/{arm}',{'traces':0,'items':0,'mismatches':0,'excluded_budget_steps':0,
                                               'excluded_score_items':0,'elapsed_informational_s':0.})
            d['traces']+=1;d['items']+=n;d['mismatches']+=len(bad);d['excluded_budget_steps']+=es
            d['excluded_score_items']+=esc;d['elapsed_informational_s']=round(d['elapsed_informational_s']+dt,3)
            mism+=bad
    return {'per_arm':tot,'items_compared':sum(d['items'] for d in tot.values()),'mismatch_count':len(mism),
            'mismatches':mism[:200],'mismatches_truncated':len(mism)>200,'passed':len(mism)==0,
            'elapsed_informational_s':round(perf_counter()-t0,1)}


def gr1(workers,limit=None):
    jobs=[]
    for study,path,arms in (('004','results/study-004/RESULTS.json',('A','P')),('005','results/study-005/RESULTS.json',('A3','P3'))):
        cs=_cases(ROOT/path)
        if limit:cs=cs[::max(1,len(cs)//limit)][:limit]
        jobs+=[(study,ci,c,a) for ci,c in enumerate(cs) for a in arms]
    return exactness(jobs,workers)


def gr1b(results_dir,workers,limit=None):
    cs=_cases(Path(results_dir)/'RESULTS.json')
    if limit:cs=cs[::max(1,len(cs)//limit)][:limit]
    sub=set(_subsample(cs))
    jobs=[('006',ci,c,a) for ci,c in enumerate(cs) for a in ('A4','P4')]
    jobs+=[('006',ci,c,a) for ci,c in enumerate(cs) if ci in sub for a in SUBSAMPLE_ARMS]
    r=exactness(jobs,workers);r['subsample_cases']=len(sub);return r


# ------------------------------------------------------------------------------------------------------------- GR2
ENUM_N=(2,3,4,5,6);SAT_N=(2,3,4,5,6,8,10,12)


def _gr2_case(x):
    c,budget=x;t=c['arms']['P4']['trace'];init=c['initial_visible']
    ev=[(r['action'],r['observed']) for r in t];out={'seed':c['seed'],'family':c['family'],'mask_rate':c['mask_rate'],'enum':{},'sat':{}}
    for n in ENUM_N:
        L=SymbolicLearner(n,budget);t0=perf_counter();L.initialize(init);peak=L.count;res=[]
        for a,o in ev:
            if L.status=='supported':
                s=(L.predict_support(0),L.predict_support(1),all(p.used==n for p in L.belief))
            else:s=None
            res.append(s);L.observe(a,o);peak=max(peak,L.count)
        out['enum'][n]={'time_s':perf_counter()-t0,'peak_rows':peak,'final_status':L.status,'_res':res}
    for n in SAT_N:
        masks=[mask_for_observation(init)];acts=[];t0=perf_counter();res=[];vmax=cmax=0
        for a,o in ev:
            R=ConstraintRegion(n,masks,acts)
            res.append((R.support(0),R.support(1),R.saturated()) if R.feasible else None)
            vmax=max(vmax,R.size['variables']);cmax=max(cmax,R.size['clauses']);R.close()
            masks.append(mask_for_observation(o));acts.append(a)
        R=ConstraintRegion(n,masks,acts);fin=R.feasible;R.close()
        out['sat'][n]={'time_s':perf_counter()-t0,'max_variables':vmax,'max_clauses':cmax,'final_feasible':fin,'_res':res}
    for n in ENUM_N:
        e=out['enum'][n];s=out['sat'][n]
        agree=dis=excl=0
        for x,y in zip(e['_res'],s['_res']):
            if x is None and y is not None:excl+=1;continue   # enumeration over budget (region still feasible)
            if x==y:agree+=1
            else:dis+=1
        e['agree_steps']=agree;e['disagree_steps']=dis;e['excluded_steps']=excl
    for d in (out['enum'],out['sat']):
        for v in d.values():v.pop('_res')
    return out


def _slope(ns,ts):
    xs=[math.log(n) for n,t in zip(ns,ts) if t>0];ys=[math.log(t) for t in ts if t>0]
    if len(xs)<2:return None
    mx=statistics.mean(xs);my=statistics.mean(ys)
    return round(sum((x-mx)*(y-my) for x,y in zip(xs,ys))/sum((x-mx)**2 for x in xs),3)


def gr2(results_dir,workers,budget=160000,limit=None):
    cs=_cases(Path(results_dir)/'RESULTS.json')
    sel=[];seen={}
    for c in cs:
        k=(c['family'],c['mask_rate'])
        if c['family']=='perm4':continue
        seen.setdefault(k,0)
        if seen[k]<4:seen[k]+=1;sel.append(c)
    if limit:sel=sel[:limit]
    t0=perf_counter()
    with ProcessPoolExecutor(workers) as ex:rows=list(ex.map(_gr2_case,[(c,budget) for c in sel]))
    summ={'enum':{},'sat':{}}
    for kind,NS in (('enum',ENUM_N),('sat',SAT_N)):
        for n in NS:
            v=[r[kind][n] for r in rows];steps=44
            d={'median_case_time_s':round(statistics.median(x['time_s'] for x in v),6),
               'mean_case_time_s':round(statistics.mean(x['time_s'] for x in v),6),
               'max_case_time_s':round(max(x['time_s'] for x in v),6),
               'median_step_time_ms':round(1000*statistics.median(x['time_s'] for x in v)/steps,4)}
            if kind=='enum':
                d.update(mean_peak_rows=round(statistics.mean(x['peak_rows'] for x in v),1),max_peak_rows=max(x['peak_rows'] for x in v),
                         budget_exhausted_cases=sum(x['final_status']=='budget_exhausted' for x in v),
                         agree_steps=sum(x['agree_steps'] for x in v),disagree_steps=sum(x['disagree_steps'] for x in v),
                         excluded_steps=sum(x['excluded_steps'] for x in v))
            else:d.update(max_variables=max(x['max_variables'] for x in v),max_clauses=max(x['max_clauses'] for x in v))
            summ[kind][n]=d
    by_mask={}
    for m in sorted({r['mask_rate'] for r in rows}):
        rr=[r for r in rows if r['mask_rate']==m]
        by_mask[str(m)]={kind:{n:round(statistics.mean(r[kind][n]['time_s'] for r in rr),6) for n in NS}
                         for kind,NS in (('enum',ENUM_N),('sat',SAT_N))}
        by_mask[str(m)]['enum_mean_peak_rows']={n:round(statistics.mean(r['enum'][n]['peak_rows'] for r in rr),1) for n in ENUM_N}
    slopes={'enum_mean_time_vs_n_2_6':_slope(ENUM_N,[summ['enum'][n]['mean_case_time_s'] for n in ENUM_N]),
            'sat_mean_time_vs_n_2_6':_slope(ENUM_N,[summ['sat'][n]['mean_case_time_s'] for n in ENUM_N]),
            'sat_mean_time_vs_n_2_12':_slope(SAT_N,[summ['sat'][n]['mean_case_time_s'] for n in SAT_N]),
            'enum_mean_peak_rows_vs_n_2_6':_slope(ENUM_N,[summ['enum'][n]['mean_peak_rows'] for n in ENUM_N]),
            'sat_max_clauses_vs_n_2_12':_slope(SAT_N,[summ['sat'][n]['max_clauses'] for n in SAT_N])}
    return {'cases':len(rows),'budget_rows':budget,'summary':summ,'by_mask_mean_case_time_s':by_mask,'loglog_slopes':slopes,
            'per_case':rows,'elapsed_informational_s':round(perf_counter()-t0,1),
            'timing_note':'wall-clock on one shared 8-CPU box with parallel workers; informational, not gated'}


def main():
    ap=argparse.ArgumentParser();ap.add_argument('which',choices=('gr1','gr1b','gr2'))
    ap.add_argument('--results-dir',default=str(ROOT/'results/study-006'));ap.add_argument('--workers',type=int,default=6)
    ap.add_argument('--limit',type=int);ap.add_argument('--out')
    a=ap.parse_args()
    if a.which=='gr1':r=gr1(a.workers,a.limit)
    elif a.which=='gr1b':r=gr1b(a.results_dir,a.workers,a.limit)
    else:r=gr2(a.results_dir,a.workers,limit=a.limit)
    r={'schema':'brute.exactness.v1','check':a.which.upper(),'limit':a.limit,
       'representation':'brute.geometry.ConstraintRegion (CNF H-representation, pysat Glucose3, first-visit symmetry breaking)',**r}
    s=json.dumps(r,indent=1,sort_keys=True)+'\n'
    if a.out:Path(a.out).write_text(s)
    print(json.dumps({k:v for k,v in r.items() if k not in ('mismatches','per_case')},indent=1,sort_keys=True)[:4000])


if __name__=='__main__':main()
