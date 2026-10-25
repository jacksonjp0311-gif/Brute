"""Compare the incremental re-run checkpoint with the frozen (stopped) study-008 GX2' checkpoint on the cases both did.

Per case and arm: both 'ok'; steps equal; every step unchecked in the incremental run is also unchecked in the original;
on steps checked by both, the audit passed in both (a mismatch would have made ok False). When the unchecked sets are
equal the counts (steps_checked, certs, unknown_forecasts) must be identical. Also per-case wall-clock speedup.
"""
import json,statistics,sys
orig_p,new_p,out_p=sys.argv[1:4]
rd=lambda p:{(r:=json.loads(l))['case']:r['out'] for l in open(p) if l.strip()}
O=rd(orig_p);N=rd(new_p);rows=[];bad=[]
for i in sorted(O):
    o=O[i];n=N.get(i)
    if n is None:bad.append({'case':i,'why':'missing in re-run'});continue
    for arm,oa in o['arms'].items():
        na=n['arms'].get(arm)
        r={'case':i,'family':o['family'],'seed':o['seed'],'mask_rate':o['mask_rate'],'arm':arm,'ok_orig':oa['ok'],'ok_new':na and na['ok']}
        if not(oa['ok'] and na and na['ok']):bad.append(dict(r,why='ok differs or failed'));rows.append(r);continue
        oc,nc=oa['counts'],na['counts'];ou,nu=set(oc['unchecked_steps']),set(nc['unchecked_steps'])
        r.update(unchecked_orig=sorted(ou),unchecked_new=sorted(nu),steps=oc['steps'])
        if oc['steps']!=nc['steps'] or not nu<=ou:bad.append(dict(r,why='new unchecked not subset of original'))
        if ou==nu and oc!=nc:bad.append(dict(r,why='counts differ with equal unchecked sets',orig=oc,new=nc))
        r['identical_counts']=oc==nc;rows.append(r)
sp=[O[i]['wall_informational']/max(N[i]['wall_informational'],1e-3) for i in O if i in N]
rep={'schema':'brute.xcheck-incremental-equivalence.v1','cases_compared':len(O),'arm_traces_compared':len(rows),
     'differences':bad,'arm_traces_identical_counts':sum(r.get('identical_counts',False) for r in rows),
     'arm_traces_more_checked_in_rerun':sum(1 for r in rows if 'unchecked_new' in r and len(r['unchecked_new'])<len(r['unchecked_orig'])),
     'original_wall_sum_s':round(sum(O[i]['wall_informational'] for i in O),1),'rerun_wall_sum_s_same_cases':round(sum(N[i]['wall_informational'] for i in O if i in N),1),
     'per_case_speedup_median':round(statistics.median(sp),1),'per_case_speedup_min':round(min(sp),1),'per_case_speedup_max':round(max(sp),1),
     'rows':rows}
json.dump(rep,open(out_p,'w'),indent=1,sort_keys=True)
print(json.dumps({k:v for k,v in rep.items() if k!='rows'},indent=1))
