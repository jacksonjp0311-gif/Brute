"""Seen-data diagnostic of the study-015 DLFn / RSXn false certificate (BRUTE_PLAN_016 process_controls step 3,
non_gated_reports.R_diag_license). Run BEFORE any v0.14.0 code; reads only sealed, already-scored data (studies 014 and
015); changes no criterion. Observed on SEEN data.

Questions:
  Q1  the failing case (study-015, ood4 seed 8140016, mask 0.35): step, action, library, license bound, the bounded
      supports at n = 1..5 at that step, the true reading, SP8 support, and when the license region is first empty;
  Q2  every license certificate issued by DLFp / DLFn / RSXp / RSXn (015) and DLFp / DLFn (014), by license bound
      n_L + 1 versus the evaluator-only true state count n*; the BRUTE_PLAN_014 Exact guarantee covers only n* <= n_L + 1;
  Q3  how many RG_{n_L+1} (RG3 when n_L = 2) false certificates the library-agreement filter removed on the same cases.

  PYTHONPATH=. python scripts/diag_license_016.py   -> results/diag-016/DIAG_LICENSE_016.json
"""
import json,sys,collections
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
OUT=ROOT/'results/diag-016/DIAG_LICENSE_016.json'
RES={'015':ROOT/'results/study-015/transfer/RESULTS.json','014':ROOT/'results/study-014/transfer/RESULTS.json'}
CASE=(8140016,0.35)


def _cases(study):
    return [c for c in json.load(open(RES[study]))['cases'] if c['family']!='ood5']


def q1(cases):
    c=[c for c in cases if c['seed']==CASE[0] and abs(c['mask_rate']-CASE[1])<1e-9][0]
    t=c['transfer']['DLFn'];row=[r for r in t['trace'] if 'license' in r['rule']][0];i=row['step']-1
    b=row['rule'].index('license');sp=c['arms']['SP8']['trace'][i];B=c['bounded']['SP8']
    taken=sp['action'];actual=sp['actual_emission_EVALUATOR_ONLY'] if b==taken else sp['counterfactual_actual_EVALUATOR_ONLY']
    sp_support=sp['support'] if b==taken else sp['counterfactual']['support']
    lb=t['license_bound'];empty=None
    for j,s in enumerate(B[str(lb)]['support']):
        if s is None or any(x is None or len(x)==0 for x in s):empty=j+1;break  # None: region status not supported (refuted)
    return {'seed':c['seed'],'mask_rate':c['mask_rate'],'family':c['family'],'true_n_EVALUATOR_ONLY':c['true_hidden_state_count_EVALUATOR_ONLY'],
            'step':row['step'],'action':b,'certificate':row['certificate'][b],'true_reading_EVALUATOR_ONLY':actual,
            'library':{k:c['libraries']['neg'][k] for k in ('source_family','source_seed','min_n','motifs')},
            'library_hypotheses_alive_before':row['alive'],'license_bound':lb,'disabled_step':t['disabled_step'],
            'sp8_support':sp_support,'bounded_support_at_step':{n:B[n]['support'][i][b] for n in sorted(B)},
            'first_step_license_region_empty':empty,
            'same_step_rg':{a:c['transfer'][a]['trace'][i]['certificate'][b] for a in ('RG2','RG3','RG4','RG5')},
            'rsxn_same':[r for r in c['transfer']['RSXn']['trace'] if 'license' in r['rule']][0]['step']==row['step']}


def q2(study,cases):
    arms=('DLFp','DLFn','RSXp','RSXn') if study=='015' else ('DLFp','DLFn')
    st=collections.Counter()
    for c in cases:
        n=c['true_hidden_state_count_EVALUATOR_ONLY']
        for a in arms:
            if a not in c['transfer']:continue
            t=c['transfer'][a]
            for r in t['trace']:
                for b in (0,1):
                    if r['rule'][b]=='license':
                        st[(a,'inside' if n<=t['license_bound'] else 'outside',bool(r['wrong'][b]))]+=1
    out={}
    for (a,g,w),v in sorted(st.items()):out.setdefault(a,{}).setdefault(g,{'certificates':0,'false':0});out[a][g]['certificates']+=v;out[a][g]['false']+=v*w
    return out


def q3(cases):
    out={'cases_with_license_bound_below_true_n':0,'rg_at_bound_false':0,'dlfn_false':0}
    for c in cases:
        t=c['transfer'].get('DLFn')
        if not t or c['true_hidden_state_count_EVALUATOR_ONLY']<=t['license_bound']:continue
        out['cases_with_license_bound_below_true_n']+=1;arm='RG%d'%t['license_bound']
        if arm in c['transfer']:out['rg_at_bound_false']+=c['transfer'][arm]['false_certificates']
        out['dlfn_false']+=t['false_certificates']
    return out


def main():
    r={'schema':'brute.diag-license.v16','label':'Observed on SEEN data (studies 014 and 015, sealed); changes no v0.14.0 criterion'}
    c15=_cases('015');r['Q1_case']=q1(c15);r['Q2_license_by_guarantee']={'015':q2('015',c15)}
    r['Q3_filter_015']=q3(c15)
    if RES['014'].exists():c14=_cases('014');r['Q2_license_by_guarantee']['014']=q2('014',c14);r['Q3_filter_014']=q3(c14)
    OUT.parent.mkdir(parents=True,exist_ok=True);txt=json.dumps(r,indent=1,default=str)
    with open(OUT,'x') as fh:fh.write(txt+'\n')
    print(txt);return 0


if __name__=='__main__':sys.exit(main())
