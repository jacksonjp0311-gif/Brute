"""Evaluate pre-registered criteria C1..C11 of BRUTE-010-ABSTENTION-002 from sealed artifacts.

Thresholds come from experiments/BRUTE_PLAN_002.json as registered (commit d402c75). Nothing is tuned here.
"""
from __future__ import annotations
import argparse,math,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common import STUDY_DIR,PLAN,load,dumps,write_new,check,sha

OUT=STUDY_DIR/'GATES.json'
LN4=math.log(4)


def build():
    plan=load(PLAN);sci=load(STUDY_DIR/'SCIENTIFIC.json');S=sci['summary']
    audit=load(STUDY_DIR/'INDEPENDENT_AUDIT.json');repro=load(STUDY_DIR/'REPRODUCIBILITY.json')
    inf=plan['in_family'];eps=plan['open_world_reserve_epsilon'];g={}
    def gate(cid,passed,observed,gated=True):
        g[cid]={'criterion':plan['criteria'][cid],'gated':gated,'pass':bool(passed) if gated else None,'observed':observed}
    gate('C1_in_family_soundness',all(S[f]['brute_false_certs_all']==0 and S[f]['public_false_certs_all']==0 for f in inf),
         {f:{'brute_certs':S[f]['brute_certs_all'],'brute_false':S[f]['brute_false_certs_all'],
             'public_certs':S[f]['public_certs_all'],'public_false':S[f]['public_false_certs_all']} for f in inf})
    gate('C2_ood5_false_certs_zero',S['ood5']['brute_false_certs_all']==0,
         {'brute_certs':S['ood5']['brute_certs_all'],'brute_false':S['ood5']['brute_false_certs_all'],
          'v090_control_false':S['ood5']['v090_false_certs_all'],'v089_false':S['ood5']['v089_false_certs_all']})
    d=S['drift4']
    gate('C3_drift4_reduction',d['brute_false_certs_all']<=0.5*d['v090_false_certs_all'],
         {'brute_false':d['brute_false_certs_all'],'v090_control_false':d['v090_false_certs_all'],
          'limit':0.5*d['v090_false_certs_all'],'stretch_zero_met':d['brute_false_certs_all']==0})
    pub_oof=sum(S[f]['public_certs_all'] for f in plan['out_of_family'])
    pub_wrong=sum(S[f]['public_false_certs_all'] for f in S)
    gate('C4_public_safety',pub_oof==0 and pub_wrong==0,{'public_certs_out_of_family':pub_oof,'public_false_anywhere':pub_wrong})
    cases=sum(S[f]['cases'] for f in inf);alarmed=sum(S[f]['cases_with_alarm'] for f in inf)
    steps=sum(S[f]['steps_post_burn_in'] for f in inf);asteps=sum(S[f]['alarm_steps_post'] for f in inf)
    gate('C5_false_alarm_limit',alarmed/cases<=0.05,{'in_family_cases':cases,'cases_with_alarm':alarmed,'fraction':round(alarmed/cases,6),
         'step_level_alarm_rate':round(asteps/steps,6),'limit':0.05})
    minp=min(S[f]['min_probability_any_step'] for f in S)
    ll={f:S[f]['logloss_post']['brute'] for f in plan['out_of_family']}
    gate('C6_open_world_logloss',minp>=eps/4 and all(v<=round(LN4,6) for v in ll.values()),
         {'min_probability_any_step':minp,'floor':eps/4,'floor_pass':minp>=eps/4,
          'mean_post_logloss':ll,'limit_ln4':round(LN4,6),'per_family_pass':{f:v<=round(LN4,6) for f,v in ll.items()}})
    c7={f:{'brute':S[f]['logloss_post']['brute'],'v090':S[f]['logloss_post']['v090'],
           'limit':round(S[f]['logloss_post']['v090']+0.05,6),'pass':S[f]['logloss_post']['brute']<=S[f]['logloss_post']['v090']+0.05} for f in inf}
    gate('C7_in_family_logloss_cost',all(v['pass'] for v in c7.values()),c7)
    gate('C8_coverage_reported',None,{f:{'coverage_post':S[f]['coverage_post'],'selective_risk_post':S[f]['selective_risk_post'],
         'status_breakdown_post':S[f]['status_breakdown_post']} for f in S},gated=False)
    exhausted=sum(S[f]['budget_exhausted_family']+S[f]['budget_exhausted_margin'] for f in S)
    gate('C9_row_budgets_reported',None,{'peak_rows_family':max(S[f]['peak_rows_family'] for f in S),
         'peak_rows_margin':max(S[f]['peak_rows_margin'] for f in S),'budget':plan['row_budget_margin'],'exhaustions':exhausted,
         'per_family':{f:[S[f]['peak_rows_family'],S[f]['peak_rows_margin']] for f in S}},gated=False)
    gate('C10_independent_audit',audit.get('status')=='passed' and audit.get('cases')==504,dict(audit))
    gate('C11_reproducibility',repro['all_byte_identical'],repro['files'])
    gated=[k for k,v in g.items() if v['gated']]
    return {'schema':'brute.gates.v1','study':plan['study'],'plan_sha256':sha(PLAN),'scientific_sha256':sha(STUDY_DIR/'SCIENTIFIC.json'),
            'gates':g,'passed':[k for k in gated if g[k]['pass']],'failed':[k for k in gated if not g[k]['pass']],
            'all_gated_pass':all(g[k]['pass'] for k in gated)}


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--check',action='store_true');a=ap.parse_args()
    obj=build()
    if a.check:check(OUT.read_bytes()==dumps(obj),'GATES.json does not reproduce');print('GATES reproduces')
    else:write_new(OUT,obj);print(dumps(obj).decode())
