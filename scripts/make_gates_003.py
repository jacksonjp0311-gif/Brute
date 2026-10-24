"""Evaluate pre-registered gates G1..G11 (+ reported R1..R6) for study-003 from sealed artifacts only.

Thresholds are those in experiments/BRUTE_PLAN_003.json (frozen at 1585a77 / freeze 003). Failed gates
are published as failed; nothing here is tuned.
"""
from __future__ import annotations
import argparse,math,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common_003 import STUDY_DIR,PLAN,FREEZE,load,dumps,write_new,check,sha
from experiments.v011_independent_reference import ref_reason

OUT=STUDY_DIR/'GATES.json'
LN4=round(math.log(4),6)


def build():
    plan=load(PLAN);d=load(STUDY_DIR/'SCIENTIFIC.json');S=d['summary'];seal=load(STUDY_DIR/'SEAL.json')
    check(seal['scientific_sha256']==sha(STUDY_DIR/'SCIENTIFIC.json'),'SCIENTIFIC does not match SEAL')
    check(seal['plan_sha256']==sha(PLAN) and seal['freeze_sha256']==sha(FREEZE),'seal plan/freeze mismatch')
    cal=load(STUDY_DIR/'CALIBRATION_CHECK.json');audit=load(STUDY_DIR/'INDEPENDENT_AUDIT.json')
    repro=load(STUDY_DIR/'REPRODUCIBILITY.json');paired=load(STUDY_DIR/'PAIRED_ANALYSIS.json')
    witness=load(STUDY_DIR/'WITNESS_AUDIT.json');r4=load(STUDY_DIR/'DRIFT_STRESS_R4.json')
    results=load(STUDY_DIR/'RESULTS.json')
    check(paired['scientific_sha256']==seal['scientific_sha256'],'paired analysis is of another SCIENTIFIC')
    inf,oof=plan['in_family'],plan['out_of_family'];cases=d['cases'];g={}
    def gate(name,ok,obs,gated=True):g[name]={'gated':gated,'pass':bool(ok) if gated else None,'observed':obs}
    A=lambda f,arm='v0.1.1':S[f][arm]
    gate('G1_in_family_soundness',all(A(f)['false_certs_all']==0 and A(f)['public_false_certs_all']==0 for f in inf),
         {f:{'certs':A(f)['certs_all'],'false':A(f)['false_certs_all'],'public_false':A(f)['public_false_certs_all']} for f in inf})
    gate('G2_ood5_false_certs_zero',A('ood5')['false_certs_all']==0,
         {arm:{'certs':S['ood5'][arm]['certs_all'],'false':S['ood5'][arm]['false_certs_all']} for arm in ('v0.1.1','v0.1.0','v0.90')})
    D=S['drift4'];limit=0.5*D['v0.90']['false_certs_all']
    gate('G3_prime_drift4',A('drift4')['false_certs_non_drift_steps']==0 and A('drift4')['false_certs_all']<=limit,
         {'v0.1.1':{k:A('drift4')[k] for k in ('certs_all','false_certs_all','false_certs_drift_steps','false_certs_non_drift_steps')},
          'v0.1.0':{k:A('drift4','v0.1.0')[k] for k in ('certs_all','false_certs_all','false_certs_drift_steps','false_certs_non_drift_steps')},
          'v0.90':{k:D['v0.90'][k] for k in ('certs_all','false_certs_all','false_certs_drift_steps')},
          'limit_total_false_certs':limit,'drift_steps_all':D['drift_steps_all'],
          'wrong_certificates':[{'seed':c['seed'],'mask_rate':c['mask_rate'],'step':r['step'],'drift_step':r['drift_step'],
                                 'certificate':r['certificate'],'actual':r['actual_emission_EVALUATOR_ONLY']}
                                for c in cases if c['family']=='drift4' for r in c['trace'] if r['brute_wrong']]})
    gate('G3_original_drift4_zero',None,{'false_certs_all':A('drift4')['false_certs_all'],'would_pass':A('drift4')['false_certs_all']==0},gated=False)
    gate('G4_public_safety',all(A(f)['public_certs_all']==0 for f in oof) and all(A(f)['public_false_certs_all']==0 for f in S),
         {f:{'public_certs':A(f)['public_certs_all'],'public_false':A(f)['public_false_certs_all']} for f in S})
    alarm={f:{'cases_with_alarm':A(f)['cases_with_alarm'],'cases':S[f]['cases'],'fraction':round(A(f)['cases_with_alarm']/S[f]['cases'],6),
              'alarm_steps_post':A(f)['alarm_steps_post'],'step_rate_post':round(A(f)['alarm_steps_post']/S[f]['steps_post_burn_in'],6)} for f in S}
    gate('G5_false_alarm_limit',all(alarm[f]['fraction']<=0.05 for f in inf),alarm)
    minp=min(A(f)['min_probability_any_step'] for f in S)
    lo=A('ood5')['logloss_post'];ld=A('drift4')['logloss_post'];ld0=A('drift4','v0.1.0')['logloss_post']
    gate('G6_open_world_logloss',lo<=LN4 and ld<=LN4 and ld<=ld0 and minp>=0.005,
         {'ln4':LN4,'ood5':{'v0.1.1':lo,'v0.1.0':A('ood5','v0.1.0')['logloss_post'],'v0.90':S['ood5']['v0.90']['logloss_post'],
                            **S['ood5']['baselines_logloss_post'],'ablation':S['ood5']['ablation_logloss_post']},
          'drift4':{'v0.1.1':ld,'v0.1.0':ld0,'v0.90':S['drift4']['v0.90']['logloss_post'],**S['drift4']['baselines_logloss_post'],
                    'ablation':S['drift4']['ablation_logloss_post']},
          'min_probability_any_step':minp,
          'reported_targets':{'ood5_le_1.0':lo<=1.0,'drift4_le_suffix1':ld<=S['drift4']['baselines_logloss_post']['suffix1'],
                              'per_mask':{f:S[f]['logloss_post_per_mask'] for f in oof},
                              'paired_bootstrap':{f:paired['families'][f] for f in oof}}})
    def prefix_identical(fam):
        steps=diff=0
        for c in cases:
            if c['family']!=fam:continue
            k=c['diagnostics']['contradiction_step'];n=len(c['trace']) if k is None else k
            for r,q in zip(c['trace'][:n],c['control_trace'][:n]):
                steps+=1;diff+=any(r[x]!=q[x] for x in ('probabilities','status','reason','certificate'))
        return {'steps_before_contradiction':steps,'differing_steps':diff}
    g7a={f:{'v0.1.1':A(f)['logloss_post'],'v0.90':S[f]['v0.90']['logloss_post'],'limit':round(S[f]['v0.90']['logloss_post']+0.05,6)} for f in inf}
    g7b={f:prefix_identical(f) for f in S}
    gate('G7_in_family_no_change',all(g7a[f]['v0.1.1']<=g7a[f]['limit'] for f in inf) and all(g7b[f]['differing_steps']==0 for f in inf)
         and cal['tau_reproduced'] is True,
         {'a_logloss':g7a,'b_prefix_identity_gated_in_family':{f:g7b[f] for f in inf},'b_reported_open_world':{f:g7b[f] for f in oof},
          'c_tau':{'tau':cal['tau'],'reproduced':cal['tau_reproduced']}})
    reasons_ok=True;falsified=0;falsified_truth=0;totals={}
    for c in cases:
        for e in c['retractions']:
            obs=c['trace'][e['step']-1]['observed'];want=ref_reason(e['certificate'],obs)
            reasons_ok&=e['reason']==want;totals[e['reason']]=totals.get(e['reason'],0)+1
            falsified+=e['reason']=='falsified_by_observation'
            falsified_truth+=e['wrong'] and any(o is not None and o!=b for o,b in zip(obs,((e['certificate']>>1)&1,e['certificate']&1)))
    gate('G8_retraction_semantics',reasons_ok and falsified==falsified_truth and audit.get('status')=='passed',
         {'retraction_reasons_total':totals,'falsified':falsified,'retracted_wrong_with_contradicting_bit':falsified_truth,
          'retracted_wrong':sum(S[f]['retracted_wrong'] for f in S),
          'per_family':{f:{'reasons':S[f]['retraction_reasons'],'retracted_wrong':S[f]['retracted_wrong'],
                           'wrong_certs_in_never_contradicted_cases':S[f]['wrong_certs_in_never_contradicted_cases']} for f in S}})
    peak=max(max(A(f,arm)['peak_rows_family'],A(f,arm)['peak_rows_margin']) for f in S for arm in ('v0.1.1','v0.1.0'))
    new_exh=0;bad_exh=0
    for c in cases:
        L,C=c['diagnostics'],c['control_diagnostics']
        lex='budget_exhausted' in (L['family_status'],L['margin_status']) or any('budget_exhausted' in (r['family_status_after'],r['margin_status_after']) for r in c['trace'])
        cex='budget_exhausted' in (C['family_status'],C['margin_status'])
        new_exh+=lex and not cex
        for prev,r in zip(c['trace'],c['trace'][1:]):
            k=(r['status'],r['reason'])
            if prev['family_status_after']=='budget_exhausted' and k not in (('ABSTAIN','BUDGET_EXHAUSTED'),('OUT_OF_FAMILY','RESIDUAL_SURPRISE')):bad_exh+=1
            elif prev['margin_status_after']=='budget_exhausted' and r['status']=='CERTIFIED':bad_exh+=1
    tv=sum(results['summary'][f]['time_v011_informational_seconds'] for f in S);tc=sum(results['summary'][f]['time_v010_informational_seconds'] for f in S)
    gate('G9_compute_budget',peak<=160000 and new_exh==0 and bad_exh==0,
         {'peak_rows_any_arm':peak,'limit':160000,'new_exhaustion_cases':new_exh,'exhaustion_steps_not_budget_abstain':bad_exh,
          'per_family':{f:{arm:[A(f,arm)['peak_rows_family'],A(f,arm)['peak_rows_margin']] for arm in ('v0.1.1','v0.1.0')} for f in S},
          'wall_clock_informational':{'v0.1.1_seconds':round(tv,2),'v0.1.0_seconds':round(tc,2),'ratio':round(tv/tc,3),'target_ratio_le':2.0}})
    gate('G10_independent_audit',audit.get('status')=='passed' and audit.get('cases')==len(cases) and audit.get('scientific_sha256')==seal['scientific_sha256'],
         {k:audit[k] for k in audit if k!='per_family'})
    gate('G11_reproducibility',repro['all_byte_identical'],repro['files'])
    gate('R1_coverage',None,{f:{'v0.1.1':A(f)['coverage_post'],'v0.1.0':A(f,'v0.1.0')['coverage_post'],'v0.90':S[f]['v0.90']['coverage_post'],
                               'v0.89':S[f]['v0.89']['coverage_post'],'selective_risk_v0.1.1':A(f)['selective_risk_post'],
                               'status_breakdown_v0.1.1':A(f)['status_breakdown_post']} for f in S},gated=False)
    gate('R2_loss_decomposition',None,{f:{'loss_decomposition_post':S[f]['loss_decomposition_post'],
                                          'forecast_source_steps_post':S[f]['forecast_source_steps_post']} for f in oof},gated=False)
    gate('R3_witness_audit_F14',None,{'totals':witness['totals'],'families':{f:{k:v for k,v in t.items() if k!='witness_examples'} for f,t in witness['families'].items()}},gated=False)
    gate('R4_drift_stress_replay',None,{'v0.1.1':{k:r4['summary']['v0.1.1'][k] for k in
        ('certs_all','false_certs_all','false_certs_drift_steps','false_certs_non_drift_steps')},
        'v0.1.0':{k:r4['summary']['v0.1.0'][k] for k in ('certs_all','false_certs_all','false_certs_drift_steps','false_certs_non_drift_steps')},
        'retraction_reasons':r4['summary']['retraction_reasons'],'logloss_v0.1.1':r4['summary']['v0.1.1']['logloss_post'],
        'logloss_v0.1.0':r4['summary']['v0.1.0']['logloss_post']},gated=False)
    gate('R5_out_of_scope_margin',None,{f:{'margin_fallback_steps_post':S[f]['margin_fallback_steps_post'],
        'actual_outside_margin_support':S[f]['margin_fallback_actual_outside_support_post']} for f in S},gated=False)
    gate('R6_v089_paired',None,{f:{'valid_steps_post':S[f]['v0.89']['valid_steps_post'],'v0.89':S[f]['v0.89']['logloss_valid_steps'],
        'v0.1.1':S[f]['v0.89']['v011_logloss_on_v089_valid_steps']} for f in S},gated=False)
    gated=[k for k,v in g.items() if v['gated']]
    return {'schema':'brute.gates.v1_1','study':plan['study'],'plan_sha256':sha(PLAN),'scientific_sha256':seal['scientific_sha256'],
            'gates':g,'passed':[k for k in gated if g[k]['pass']],'failed':[k for k in gated if not g[k]['pass']],
            'all_gated_pass':all(g[k]['pass'] for k in gated)}


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--check',action='store_true');a=ap.parse_args();obj=build()
    if a.check:check(OUT.read_bytes()==dumps(obj),'GATES.json does not reproduce');print('GATES reproduces')
    else:write_new(OUT,obj);print(dumps(obj).decode())
