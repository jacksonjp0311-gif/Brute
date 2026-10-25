"""Evaluate pre-registered gates G1..G13 (+ reported R1..R4) for study-004 from sealed artifacts only.

Thresholds are those in experiments/BRUTE_PLAN_004.json (frozen at c0ac594 / source freeze 004). Failed gates are
published as failed; nothing here is tuned. Written before the study-004 results were inspected.
"""
from __future__ import annotations
import argparse,math,sys,unittest,io
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common_004 import STUDY_DIR,PLAN,FREEZE,load,dumps,write_new,check,sha
from experiments.v011_independent_reference import ref_reason

OUT=STUDY_DIR/'GATES.json'
LN4=round(math.log(4),6)
ARMS=('A','P')


def _dedup_tests_pass():
    sys.path.insert(0,str(ROOT/'tests'))
    import test_brute_active as T
    names=[n for n in ('test_record_twice_once','test_retraction_listed_once')]
    suite=unittest.TestSuite()
    for cls in [v for v in vars(T).values() if isinstance(v,type) and issubclass(v,unittest.TestCase)]:
        for n in names:
            if hasattr(cls,n):suite.addTest(cls(n))
    r=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(suite)
    return {'tests':sorted(names),'run':r.testsRun,'passed':r.wasSuccessful() and r.testsRun==len(names)}


def build():
    plan=load(PLAN);d=load(STUDY_DIR/'SCIENTIFIC.json');S=d['summary'];seal=load(STUDY_DIR/'SEAL.json')
    check(seal['scientific_sha256']==sha(STUDY_DIR/'SCIENTIFIC.json'),'SCIENTIFIC does not match SEAL')
    check(seal['plan_sha256']==sha(PLAN) and seal['freeze_sha256']==sha(FREEZE),'seal plan/freeze mismatch')
    cal=load(STUDY_DIR/'CALIBRATION_CHECK.json');audit=load(STUDY_DIR/'INDEPENDENT_AUDIT.json')
    repro=load(STUDY_DIR/'REPRODUCIBILITY.json');paired=load(STUDY_DIR/'PAIRED_ANALYSIS.json')
    results=load(STUDY_DIR/'RESULTS.json')
    check(paired['scientific_sha256']==seal['scientific_sha256'],'paired analysis is of another SCIENTIFIC')
    inf,oof=plan['in_family'],plan['out_of_family'];cases=d['cases'];g={}
    def gate(name,ok,obs,gated=True):g[name]={'gated':gated,'pass':bool(ok) if gated else None,'observed':obs}
    X=lambda f,arm:S[f][arm]
    K=('certs_all','false_certs_all','counterfactual_certs_all','counterfactual_false_certs_all','public_certs_all','public_false_certs_all')
    gate('G1_in_family_soundness',all(X(f,a)['false_certs_all']==0 and X(f,a)['counterfactual_false_certs_all']==0
                                       and X(f,a)['public_false_certs_all']==0 for f in inf for a in ARMS),
         {f:{a:{k:X(f,a)[k] for k in K} for a in ARMS} for f in inf})
    gate('G2_ood5_soundness',all(X('ood5',a)['false_certs_all']==0 and X('ood5',a)['counterfactual_false_certs_all']==0 for a in ARMS),
         {**{a:{k:X('ood5',a)[k] for k in K} for a in ARMS},'C_v011':S['ood5']['C_v011'],'v0.90':S['ood5']['v0.90']})
    D=S['drift4'];limit=0.5*D['v0.90']['false_certs_all']
    def wrongs(arm,cf=False):
        out=[]
        for c in cases:
            if c['family']!='drift4':continue
            for r in c['arms'][arm]['trace']:
                q=r['counterfactual'] if cf else r
                if q['wrong']:out.append({'seed':c['seed'],'mask_rate':c['mask_rate'],'step':r['step'],'drift_step':r['drift_step'],
                    'certificate':q['certificate'],'actual':r['counterfactual_actual_EVALUATOR_ONLY' if cf else 'actual_emission_EVALUATOR_ONLY']})
        return out
    g3={a:{'non_drift_zero':X('drift4',a)['false_certs_non_drift_steps']==0,'total_within_limit':X('drift4',a)['false_certs_all']<=limit} for a in ARMS}
    KD=('certs_all','false_certs_all','false_certs_drift_steps','false_certs_non_drift_steps','counterfactual_certs_all',
        'counterfactual_false_certs_all','counterfactual_false_certs_drift_steps','counterfactual_false_certs_non_drift_steps')
    gate('G3_prime_drift4',all(all(v.values()) for v in g3.values()),
         {'clauses':g3,'limit_total_false_certs':limit,**{a:{k:X('drift4',a)[k] for k in KD} for a in ARMS},
          'C_v011':{k:D['C_v011'][k] for k in ('certs_all','false_certs_all')},
          'v0.90':{k:D['v0.90'][k] for k in ('certs_all','false_certs_all','false_certs_drift_steps')},
          'wrong_certificates':{a:wrongs(a) for a in ARMS},'counterfactual_wrong_certificates':{a:wrongs(a,True) for a in ARMS}})
    gate('G4_public_safety',all(X(f,a)['public_certs_all']==0 for f in oof for a in ARMS) and all(X(f,a)['public_false_certs_all']==0 for f in S for a in ARMS),
         {f:{a:{'public_certs':X(f,a)['public_certs_all'],'public_false':X(f,a)['public_false_certs_all']} for a in ARMS} for f in S})
    alarm={f:{a:{'cases_with_alarm':X(f,a)['cases_with_alarm'],'cases':S[f]['cases'],'fraction':round(X(f,a)['cases_with_alarm']/S[f]['cases'],6),
                 'alarm_steps_post':X(f,a)['alarm_steps_post']} for a in ARMS} for f in S}
    for f in S:alarm[f]['C_v011_cases_with_alarm']=S[f]['C_v011']['cases_with_alarm']
    gate('G5_false_alarm_limit',all(alarm[f][a]['fraction']<=0.05 for f in inf for a in ARMS),alarm)
    G6=paired['G6_dual_coverage_gain'];fams=G6['families']
    g6={'a_pooled_ge_0.05':G6['pooled_gain']>=0.05,'b_ci_lower_gt_0':G6['pooled_ci95'][0]>0,'c_every_family_ge_-0.01':all(fams[f]['gain']>=-0.01 for f in inf)}
    gate('G6_active_coverage_gain',all(g6.values()),
         {'clauses':g6,'pooled_gain':G6['pooled_gain'],'pooled_ci95':G6['pooled_ci95'],'families':fams,
          'dual_coverage_post':{f:{a:X(f,a)['dual_coverage_post'] for a in ARMS} for f in S},
          'on_policy_coverage_post':{f:{a:X(f,a)['on_policy_coverage_post'] for a in ARMS} for f in S},
          'C_v011_coverage_post':{f:S[f]['C_v011']['coverage_post'] for f in S},
          'selective_risk_post':{f:{a:X(f,a)['selective_risk_post'] for a in ARMS} for f in S},
          'per_mask_dual_coverage':{f:{a:{m:v['dual_coverage_post'] for m,v in X(f,a)['per_mask'].items()} for a in ARMS} for f in S},
          'design_estimate_Simulated':plan['criteria']['G6_active_coverage_gain']['design_estimate_Simulated']})
    ll={f:{'A':X(f,'A')['logloss_post'],'P':X(f,'P')['logloss_post'],'C_v011':S[f]['C_v011']['logloss_post'],
           'v0.90':S[f]['v0.90']['logloss_post'],'suffix':X(f,'P')['logloss_suffix_post'],'uniform':LN4} for f in S}
    minp={f:{'A':X(f,'A')['min_probability_any_step'],'P':X(f,'P')['min_probability_any_step'],'C_v011':S[f]['C_v011']['min_probability_any_step']} for f in S}
    g7={'a_P_le_C':all(ll[f]['P']<=ll[f]['C_v011'] for f in oof),'b_A_le_C':all(ll[f]['A']<=ll[f]['C_v011'] for f in oof),
        'c_le_ln4':all(ll[f][a]<=LN4 for f in oof for a in ('A','P','C_v011')),'c_min_probability_ge_0.005':all(v>=0.005 for f in S for v in minp[f].values())}
    LC=paired['logloss_contrasts']
    gate('G7_open_world_no_regression',all(g7.values()),
         {'clauses':g7,'logloss_post':{f:ll[f] for f in oof},'min_probability_any_step':minp,
          'reported_targets':{'drift4_P_minus_suffix1':LC['drift4']['logloss_P_minus_suffix1'],
                              'drift4_P_below_suffix1_ci_excludes_0':LC['drift4']['logloss_P_minus_suffix1']['ci95'][1]<0,
                              'paired_bootstrap':{f:LC[f] for f in oof},
                              'per_mask':{f:{'A':{m:v['logloss_post'] for m,v in X(f,'A')['per_mask'].items()},
                                             'P':{m:v['logloss_post'] for m,v in X(f,'P')['per_mask'].items()},
                                             'C_v011':S[f]['C_v011']['per_mask_logloss_post']} for f in oof}}})
    g8b={f:{'A':ll[f]['A'],'C_v011':ll[f]['C_v011'],'limit':round(ll[f]['C_v011']+0.05,6)} for f in inf}
    gate('G8_passive_equivalence',all(S[f]['G8a_passive_equivalence']['differing_steps']==0 for f in S) and all(g8b[f]['A']<=g8b[f]['limit'] for f in inf),
         {'a':{f:S[f]['G8a_passive_equivalence'] for f in S},'b':g8b,'reported_in_family_logloss':{f:ll[f] for f in inf}})
    reasons_ok=True;falsified=0;falsified_truth=0;totals={};dups=0
    for c in cases:
        for a in ARMS:
            A=c['arms'][a]
            dups+=len(A['issued'])-len({tuple(x) for x in A['issued']})
            dups+=len(A['retractions'])-len({(e['step'],e['certificate']) for e in A['retractions']})
            for e in A['retractions']:
                obs=A['trace'][e['step']-1]['observed'];want=ref_reason(e['certificate'],obs)
                reasons_ok&=e['reason']==want;totals[e['reason']]=totals.get(e['reason'],0)+1
                falsified+=e['reason']=='falsified_by_observation'
                falsified_truth+=e['wrong'] and any(o is not None and o!=b for o,b in zip(obs,((e['certificate']>>1)&1,e['certificate']&1)))
    dt=_dedup_tests_pass()
    gate('G9_retraction_semantics',reasons_ok and falsified==falsified_truth and audit.get('status')=='passed' and dups==0 and dt['passed'],
         {'reasons_match_reference':reasons_ok,'retraction_reasons_total':totals,'falsified':falsified,
          'retracted_wrong_with_contradicting_bit':falsified_truth,'duplicate_pairs':dups,'dedup_unit_tests':dt,
          'per_family':{f:{a:{'reasons':X(f,a)['retraction_reasons'],'retracted_wrong':X(f,a)['retracted_wrong'],
                              'certificates_retracted':X(f,a)['certificates_retracted']} for a in ARMS} for f in S}})
    peak=max(max(X(f,a)['peak_rows_family'],X(f,a)['peak_rows_margin'],X(f,a)['peak_rows_window']) for f in S for a in ARMS)
    bad_exh=0
    for c in cases:
        for a in ARMS:
            tr=c['arms'][a]['trace']
            for prev,r in zip(tr,tr[1:]):
                k=(r['status'],r['reason'])
                if prev['family_status_after']=='budget_exhausted' and k not in (('ABSTAIN','BUDGET_EXHAUSTED'),('OUT_OF_FAMILY','RESIDUAL_SURPRISE')):bad_exh+=1
                elif prev['margin_status_after']=='budget_exhausted' and r['status']=='CERTIFIED':bad_exh+=1
    RS=results['summary']
    tA=sum(RS[f]['A']['time_informational_seconds'] for f in RS);tP=sum(RS[f]['P']['time_informational_seconds'] for f in RS)
    tC=sum(RS[f]['C_v011']['time_informational_seconds'] for f in RS)
    gate('G10_compute_budget',peak<=160000 and bad_exh==0,
         {'peak_rows_any_arm':peak,'limit':160000,'exhaustion_steps_not_budget_abstain':bad_exh,
          'per_family':{f:{a:{k:X(f,a)[k] for k in ('peak_rows_family','peak_rows_margin','peak_rows_window','peak_rows_lookahead',
                               'lookahead_budget_hits','lookahead_copies','budget_exhausted_family','budget_exhausted_margin')} for a in ARMS} for f in S},
          'wall_clock_informational':{'A_seconds':round(tA,2),'P_seconds':round(tP,2),'C_seconds':round(tC,2),
                                      'A_over_C':round(tA/tC,3),'target_A_over_C_le':4.0}})
    gate('G11_independent_audit',audit.get('status')=='passed' and audit.get('mismatches')==0 and audit.get('cases')==len(cases)
         and audit.get('source_results_sha256')==seal['results_sha256'],{k:audit[k] for k in audit if k!='per_family'})
    gate('G12_reproducibility',repro['all_byte_identical'],repro['files'])
    gate('G13_tau_reproduces',cal['tau_reproduced'] is True and cal['tau']==plan['residual_surprise']['tau']==cal['tau_v011_control']
         and cal['per_family_max_R']==cal['per_family_max_R_study002']==cal['per_family_max_R_v011_control'],
         {k:cal[k] for k in ('tau','tau_v011_control','tau_study002','tau_reproduced','per_family_max_R','argmax')})
    gate('R1_geometry',None,{f:{a:{'mean_log_rows_post':X(f,a)['R1_mean_log_rows_post'],'peak_rows_lookahead':X(f,a)['peak_rows_lookahead'],
                                  'actions_differing_from_passive':X(f,a)['actions_differing_from_passive'],
                                  'forecast_source_steps_post':X(f,a)['forecast_source_steps_post'],
                                  'window_restarts':X(f,a)['window_restarts'],'family_contradicted_cases':X(f,a)['family_contradicted_cases'],
                                  'status_breakdown_post':X(f,a)['status_breakdown_post']} for a in ARMS} for f in S},gated=False)
    gate('R2_drift_post_jump',None,{a:X('drift4',a)['R2_post_jump'] for a in ARMS},gated=False)
    gate('R3_witness_audit',None,{'status':'not re-run (certification code unchanged); Open'},gated=False)
    gate('R4_five_state_certificates',None,{'status':'not attempted in v0.2.0; Open'},gated=False)
    gated=[k for k,v in g.items() if v['gated']]
    return {'schema':'brute.gates.v2_0','study':plan['study'],'plan_sha256':sha(PLAN),'scientific_sha256':seal['scientific_sha256'],
            'gates':g,'passed':[k for k in gated if g[k]['pass']],'failed':[k for k in gated if not g[k]['pass']],
            'all_gated_pass':all(g[k]['pass'] for k in gated)}


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--check',action='store_true');a=ap.parse_args();obj=build()
    if a.check:check(OUT.read_bytes()==dumps(obj),'GATES.json does not reproduce');print('GATES reproduces')
    else:write_new(OUT,obj);print(dumps(obj).decode())
