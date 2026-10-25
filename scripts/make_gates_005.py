"""Evaluate pre-registered gates G1..G13 (+ G14 decision, R1..R4 reported) for study-005 from sealed artifacts only.

Thresholds are those in experiments/BRUTE_PLAN_005.json (pre-registered at 25fa47b; source freeze f7f3bd3). Failed gates
are published as failed; nothing here is tuned. Written before the study-005 results were inspected.
"""
from __future__ import annotations
import argparse,math,sys,unittest,io
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common_005 import STUDY_DIR,PLAN,FREEZE,load,dumps,write_new,check,sha,is_stale
from experiments.v011_independent_reference import ref_reason

OUT=STUDY_DIR/'GATES.json'
LN4=round(math.log(4),6)
ARMS=('A3','P3')
ALL_ARMS=('A3','P3','A2','P2','E2')
K=('certs_all','false_certs_all','counterfactual_certs_all','counterfactual_false_certs_all','public_certs_all','public_false_certs_all')


def _dedup_tests_pass():
    sys.path.insert(0,str(ROOT/'tests'))
    import test_brute_active as T
    names=('test_record_twice_once','test_retraction_listed_once')
    suite=unittest.TestSuite()
    for cls in [v for v in vars(T).values() if isinstance(v,type) and issubclass(v,unittest.TestCase)]:
        for n in names:
            if hasattr(cls,n):suite.addTest(cls(n))
    r=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(suite)
    return {'tests':sorted(names),'run':r.testsRun,'passed':r.wasSuccessful() and r.testsRun==len(names)}


def _pooled(S,fams,arm,key,den='steps_post_burn_in'):
    return round(sum(S[f][arm][key] for f in fams)/sum(S[f][den] for f in fams),6)


def build():
    from scripts.study005_storage import ensure_raw;ensure_raw()
    plan=load(PLAN);d=load(STUDY_DIR/'SCIENTIFIC.json');S=d['summary'];XS=d['extended_summary'];seal=load(STUDY_DIR/'SEAL.json')
    check(seal['scientific_sha256']==sha(STUDY_DIR/'SCIENTIFIC.json'),'SCIENTIFIC does not match SEAL')
    check(seal['plan_sha256']==sha(PLAN) and seal['freeze_sha256']==sha(FREEZE),'seal plan/freeze mismatch')
    cal=load(STUDY_DIR/'CALIBRATION_CHECK.json');audit=load(STUDY_DIR/'INDEPENDENT_AUDIT.json')
    repro=load(STUDY_DIR/'REPRODUCIBILITY.json');paired=load(STUDY_DIR/'PAIRED_ANALYSIS.json')
    results=load(STUDY_DIR/'RESULTS.json')
    check(paired['scientific_sha256']==seal['scientific_sha256'],'paired analysis is of another SCIENTIFIC')
    inf,oof=plan['in_family'],plan['out_of_family'];cases=d['cases'];g={}
    def gate(name,ok,obs,gated=True):g[name]={'gated':gated,'pass':bool(ok) if gated else None,'observed':obs}
    X=lambda f,arm:S[f][arm]
    # G1
    gate('G1_in_family_soundness',all(X(f,a)['false_certs_all']==0 and X(f,a)['counterfactual_false_certs_all']==0
                                       and X(f,a)['public_false_certs_all']==0 for f in inf for a in ARMS),
         {f:{a:{k:X(f,a)[k] for k in K} for a in ALL_ARMS} for f in inf})
    # G2
    gate('G2_ood5_soundness',all(X('ood5',a)['false_certs_all']==0 and X('ood5',a)['counterfactual_false_certs_all']==0 for a in ARMS),
         {**{a:{k:X('ood5',a)[k] for k in K} for a in ALL_ARMS},'C_v011':S['ood5']['C_v011'],'v0.90':S['ood5']['v0.90']})
    # G3'
    D=S['drift4'];limit=0.5*D['v0.90']['false_certs_all']
    def wrongs(arm,cf=False):
        out=[]
        for c in cases:
            if c['family']!='drift4':continue
            for r in c['arms'][arm]['trace']:
                q=r['counterfactual'] if cf else r
                if q['wrong']:out.append({'seed':c['seed'],'mask_rate':c['mask_rate'],'step':r['step'],'drift_step':r['drift_step'],
                    'stale':is_stale(r['step']),'certificate':q['certificate'],
                    'actual':r['counterfactual_actual_EVALUATOR_ONLY' if cf else 'actual_emission_EVALUATOR_ONLY']})
        return out
    g3={a:{'non_drift_zero':X('drift4',a)['false_certs_non_drift_steps']==0,'total_within_limit':X('drift4',a)['false_certs_all']<=limit} for a in ARMS}
    KD=('certs_all','false_certs_all','false_certs_drift_steps','false_certs_non_drift_steps','counterfactual_certs_all',
        'counterfactual_false_certs_all','counterfactual_false_certs_drift_steps','counterfactual_false_certs_non_drift_steps','stale_false_certs')
    gate('G3_prime_drift4',all(all(v.values()) for v in g3.values()),
         {'clauses':g3,'limit_total_false_certs':limit,**{a:{k:X('drift4',a)[k] for k in KD} for a in ALL_ARMS},
          'C_v011':{k:D['C_v011'][k] for k in ('certs_all','false_certs_all')},
          'v0.90':{k:D['v0.90'][k] for k in ('certs_all','false_certs_all','false_certs_drift_steps')},
          'design_estimate_Simulated':plan['criteria']['G3_prime_drift4']['design_estimate_Simulated'],
          'wrong_certificates':{a:wrongs(a) for a in ALL_ARMS},'counterfactual_wrong_certificates':{a:wrongs(a,True) for a in ALL_ARMS}})
    # G4
    gate('G4_public_safety',all(X(f,a)['public_certs_all']==0 for f in oof for a in ARMS) and all(X(f,a)['public_false_certs_all']==0 for f in S for a in ARMS),
         {f:{a:{'public_certs':X(f,a)['public_certs_all'],'public_false':X(f,a)['public_false_certs_all']} for a in ALL_ARMS} for f in S})
    # G5
    alarm={f:{a:{'cases_with_alarm':X(f,a)['cases_with_alarm'],'cases':S[f]['cases'],'fraction':round(X(f,a)['cases_with_alarm']/S[f]['cases'],6),
                 'alarm_steps_post':X(f,a)['alarm_steps_post']} for a in ALL_ARMS} for f in S}
    for f in S:alarm[f]['C_v011_cases_with_alarm']=S[f]['C_v011']['cases_with_alarm']
    gate('G5_false_alarm_limit',all(alarm[f][a]['fraction']<=0.05 for f in inf for a in ARMS),alarm)
    # G6
    G6=paired['G6_dual_coverage_gain'];fams=G6['families']
    g6={'a_pooled_ge_0.05':G6['pooled_gain']>=0.05,'b_ci_lower_gt_0':G6['pooled_ci95'][0]>0,'c_every_family_ge_-0.01':all(fams[f]['gain']>=-0.01 for f in inf)}
    cov={f:{a:X(f,a)['dual_coverage_post'] for a in ALL_ARMS} for f in S}
    gate('G6_active_coverage_gain',all(g6.values()),
         {'clauses':g6,'pooled_gain':G6['pooled_gain'],'pooled_ci95':G6['pooled_ci95'],'families':fams,
          'dual_coverage_post':cov,
          'on_policy_coverage_post':{f:{a:X(f,a)['on_policy_coverage_post'] for a in ALL_ARMS} for f in S},
          'C_v011_coverage_post':{f:S[f]['C_v011']['coverage_post'] for f in S},
          'selective_risk_post':{f:{a:X(f,a)['selective_risk_post'] for a in ALL_ARMS} for f in S},
          'per_mask_dual_coverage':{f:{a:{m:v['dual_coverage_post'] for m,v in X(f,a)['per_mask'].items()} for a in ALL_ARMS} for f in S},
          'design_estimate_Simulated':plan['criteria']['G6_active_coverage_gain']['design_estimate_Simulated']})
    # G6b
    G6b=paired['G6b_dual_coverage_A3_minus_A2']
    g6b={'a_pooled_ge_-0.03':G6b['pooled_gain']>=-0.03,'b_ci_lower_ge_-0.05':G6b['pooled_ci95'][0]>=-0.05}
    gate('G6b_coverage_non_inferiority_vs_v020',all(g6b.values()),
         {'clauses':g6b,'pooled_A3_minus_A2':G6b['pooled_gain'],'pooled_ci95':G6b['pooled_ci95'],'families':G6b['families'],
          'pooled_dual_coverage_in_family':{a:round(sum(cov[f][a] for f in inf)/len(inf),6) for a in ALL_ARMS},
          'pre_registered_risk':plan['criteria']['G6b_coverage_non_inferiority_vs_v020']['pre_registered_risk']})
    # G7
    ll={f:{**{a:X(f,a)['logloss_post'] for a in ALL_ARMS},'C_v011':S[f]['C_v011']['logloss_post'],
           'v0.90':S[f]['v0.90']['logloss_post'],'suffix_P3':X(f,'P3')['logloss_suffix_post'],'uniform':LN4} for f in S}
    minp={f:{**{a:X(f,a)['min_probability_any_step'] for a in ALL_ARMS},'C_v011':S[f]['C_v011']['min_probability_any_step']} for f in S}
    g7={'a_P3_le_C':all(ll[f]['P3']<=ll[f]['C_v011'] for f in oof),'b_A3_le_C':all(ll[f]['A3']<=ll[f]['C_v011'] for f in oof),
        'c_every_arm_le_ln4':all(ll[f][a]<=LN4 for f in oof for a in ALL_ARMS+('C_v011',)),
        'c_min_probability_ge_0.005':all(v>=0.005 for f in S for v in minp[f].values()),
        'd_A3_le_A2_plus_0.05':all(ll[f]['A3']<=round(ll[f]['A2']+0.05,6) for f in oof)}
    gate('G7_open_world_no_regression',all(g7.values()),
         {'clauses':g7,'logloss_post':{f:ll[f] for f in oof},'min_probability_any_step':minp,
          'design_estimate_Simulated':plan['criteria']['G7_open_world_no_regression']['design_estimate_Simulated'],
          'paired_bootstrap':{f:paired['logloss_contrasts'][f] for f in oof},
          'per_mask':{f:{a:{m:v['logloss_post'] for m,v in X(f,a)['per_mask'].items()} for a in ALL_ARMS} for f in oof}})
    # G8
    pe={f:S[f]['G8a_passive_equivalence'] for f in S}
    g8a=all(v['probability_or_source_differences']==0 and v['certificate_differences']==0 and v['non_resync_differences']==0 for v in pe.values())
    g8b={f:{'A3':ll[f]['A3'],'C_v011':ll[f]['C_v011'],'limit':round(ll[f]['C_v011']+0.05,6)} for f in inf}
    gate('G8_passive_equivalence',g8a and all(g8b[f]['A3']<=g8b[f]['limit'] for f in inf),
         {'a_P3_vs_P2':pe,'a_holds':g8a,'reported_study004_G8a_P2_vs_C_differing_steps':{f:v['P2_vs_C']['differing_steps'] for f,v in pe.items()},
          'b':g8b,'reported_in_family_logloss':{f:ll[f] for f in inf}})
    # G9
    reasons_ok=True;falsified=0;falsified_truth=0;totals={};dups=0;resync_issued=0
    for c in cases:
        for a in ARMS:
            A=c['arms'][a]
            dups+=len(A['issued'])-len({tuple(x) for x in A['issued']})
            dups+=len(A['retractions'])-len({(e['step'],e['certificate']) for e in A['retractions']})
            resync_issued+=sum(A['trace'][st-1]['reason']=='RESYNC_AMBIGUOUS' for st,_ in A['issued'])
            for e in A['retractions']:
                obs=A['trace'][e['step']-1]['observed'];want=ref_reason(e['certificate'],obs)
                reasons_ok&=e['reason']==want;totals[e['reason']]=totals.get(e['reason'],0)+1
                falsified+=e['reason']=='falsified_by_observation'
                falsified_truth+=e['wrong'] and any(o is not None and o!=b for o,b in zip(obs,((e['certificate']>>1)&1,e['certificate']&1)))
    dt=_dedup_tests_pass()
    gate('G9_retraction_semantics',reasons_ok and falsified==falsified_truth and audit.get('status')=='passed' and dups==0 and dt['passed'] and resync_issued==0,
         {'reasons_match_reference':reasons_ok,'retraction_reasons_total':totals,'falsified':falsified,
          'retracted_wrong_with_contradicting_bit':falsified_truth,'duplicate_pairs':dups,'dedup_unit_tests':dt,
          'resync_ambiguous_in_issued':resync_issued,
          'per_family':{f:{a:{'reasons':X(f,a)['retraction_reasons'],'retracted_wrong':X(f,a)['retracted_wrong'],
                              'certificates_retracted':X(f,a)['certificates_retracted'],'resync_issued':X(f,a)['resync_issued']} for a in ARMS} for f in S}})
    # G10
    peak=max(max(X(f,a)['peak_rows_family'],X(f,a)['peak_rows_margin'],X(f,a)['peak_rows_window'],X(f,a)['peak_rows_lookahead']) for f in S for a in ARMS)
    bad_exh=0
    for c in cases:
        for a in ARMS:
            tr=c['arms'][a]['trace']
            for prev,r in zip(tr,tr[1:]):
                k=(r['status'],r['reason'])
                if prev['family_status_after']=='budget_exhausted' and k not in (('ABSTAIN','BUDGET_EXHAUSTED'),('OUT_OF_FAMILY','RESIDUAL_SURPRISE')):bad_exh+=1
                elif prev['margin_status_after']=='budget_exhausted' and r['status']=='CERTIFIED':bad_exh+=1
    RS=results['summary'];t={a:sum(RS[f][a]['time_informational_seconds'] for f in RS) for a in ALL_ARMS}
    tC=sum(RS[f]['C_v011']['time_informational_seconds'] for f in RS)
    gate('G10_compute_budget',peak<=160000 and bad_exh==0,
         {'peak_rows_A3_P3_incl_lookahead':peak,'limit':160000,'exhaustion_steps_not_budget_abstain':bad_exh,
          'per_family':{f:{a:{k:X(f,a)[k] for k in ('peak_rows_family','peak_rows_margin','peak_rows_window','peak_rows_lookahead',
                               'lookahead_budget_hits','lookahead_copies','budget_exhausted_family','budget_exhausted_margin')} for a in ARMS} for f in S},
          'wall_clock_informational':{**{a+'_seconds':round(v,2) for a,v in t.items()},'C_seconds':round(tC,2),
                                      'A3_over_C':round(t['A3']/tC,3),'target_A3_over_C_le':6.0}})
    # G11..G13
    gate('G11_independent_audit',audit.get('status')=='passed' and audit.get('mismatches')==0 and audit.get('cases')==len(cases)
         and audit.get('extended_cases')==len(d['extended_cases']) and audit.get('source_results_sha256')==seal['results_sha256'],
         {k:audit[k] for k in audit if k not in ('per_family','extended_per_family')})
    gate('G12_reproducibility',repro['all_byte_identical'],repro['files'])
    gate('G13_tau_reproduces',cal['tau_reproduced'] is True and cal['tau']==plan['residual_surprise']['tau']==cal['tau_v011_control']
         and cal['per_family_max_R']==cal['per_family_max_R_study002']==cal['per_family_max_R_v011_control'],
         {k:cal[k] for k in ('tau','tau_v011_control','tau_study002','tau_reproduced','per_family_max_R','argmax')})
    # G14 (not gated): pre-registered decision rule
    steps_in=sum(S[f]['steps_post_burn_in'] for f in inf)
    chk={a:round(sum(X(f,a)['check_steps_post'] for f in inf)/steps_in,6) for a in ('A2','E2','A3')}
    sw={a:round(sum(X(f,a)['switch_rate_post']*S[f]['steps_post_burn_in'] for f in inf)/steps_in,6) for a in ('A2','E2','A3','P3')}
    M=chk['E2']>0 and sw['E2']>sw['A2']
    cfk={a:sum(X(f,a)['counterfactual_certs_all'] for f in inf) for a in ('A2','E2','A3')}
    P1=cfk['E2']>=1.10*cfk['A2']
    St={a:S['drift4'][a]['stale_false_certs']+XS['drift4'][a]['stale_false_certs'] for a in ('A2','E2','A3')}
    Sw={a:S['drift4'][a]['stale_window_certs']+XS['drift4'][a]['stale_window_certs'] for a in ('A2','E2','A3')}
    if M and P1 and St['A2']>=5 and St['E2']<=0.5*St['A2']:verdict='CONFIRMED'
    elif M and St['A2']>=5 and St['E2']>=St['A2']:verdict='FALSIFIED'
    else:verdict='OPEN'
    gate('G14_D7_D8_single_mechanism_test',None,
         {'verdict':verdict,'M_manipulation_check':{'holds':M,'check_rate_post_in_family':chk,'switch_rate_post_in_family':sw},
          'P1_counterfactual_knowledge':{'holds':P1,'in_family_counterfactual_certs':cfk,'ratio_E2_over_A2':round(cfk['E2']/cfk['A2'],6) if cfk['A2'] else None},
          'P2_stale_certainty':{'S_main_plus_extended':St,'S_main':{a:S['drift4'][a]['stale_false_certs'] for a in St},
                                'S_extended':{a:XS['drift4'][a]['stale_false_certs'] for a in St},
                                'stale_window_certificates':Sw,
                                'stale_false_per_certificate':{a:round(St[a]/Sw[a],6) if Sw[a] else None for a in St},
                                'S_A2_ge_5':St['A2']>=5,'bootstrap':paired['G14_stale_E2_minus_A2']},
          'alternative_mechanism':{'S_A3':St['A3'],'check_rate_A3':chk['A3'],
                                   'attribution_condition_S_A3_eq_0_and_check_rate_A3_eq_0':St['A3']==0 and chk['A3']==0},
          'decision_rule':plan['criteria']['G14_D7_D8_single_mechanism_test']['decision_rule']},gated=False)
    # R1..R4
    gate('R1_price_of_robustness',None,
         {'A2_minus_A3_dual_coverage':{f:round(cov[f]['A2']-cov[f]['A3'],6) for f in S},
          'A2_minus_A3_per_mask':{f:{m:round(X(f,'A2')['per_mask'][m]['dual_coverage_post']-X(f,'A3')['per_mask'][m]['dual_coverage_post'],6)
                                     for m in X(f,'A3')['per_mask']} for f in S},
          'P2_minus_P3_dual_coverage':{f:round(cov[f]['P2']-cov[f]['P3'],6) for f in S},
          'resync_abstentions_post':{f:{a:X(f,a)['resync_abstentions_post'] for a in ('A3','P3')} for f in S},
          'paired_P3_minus_P2':paired['R1_dual_coverage_P3_minus_P2'],'paired_E2_minus_A2':paired['R_dual_coverage_E2_minus_A2']},gated=False)
    gate('R2_drift_post_jump',None,{'main':{a:X('drift4',a)['R2_post_jump'] for a in ALL_ARMS},
                                    'extended':{a:XS['drift4'][a]['R2_post_jump'] for a in ('A3','A2','E2')}},gated=False)
    gate('R3_untied_experiments',None,{f:{a:X(f,a)['R3_untied_experiments_per_case'] for a in ('A3','A2','E2')} for f in S}|
         {'no_proposal_steps_A3':{f:X(f,'A3')['no_proposal_steps'] for f in S}},gated=False)
    RS4={f:{a:{'experiment_s':RS[f][a]['R4_mean_experiment_call_informational_seconds'],'observe_s':RS[f][a]['R4_mean_observe_call_informational_seconds']}
            for a in ALL_ARMS} for f in RS}
    gate('R4_call_cost',None,{'informational_not_reproducible':True,'mean_seconds_per_call':RS4},gated=False)
    gated=[k for k,v in g.items() if v['gated']]
    return {'schema':'brute.gates.v3_0','study':plan['study'],'plan_sha256':sha(PLAN),'scientific_sha256':seal['scientific_sha256'],
            'gates':g,'passed':[k for k in gated if g[k]['pass']],'failed':[k for k in gated if not g[k]['pass']],
            'all_gated_pass':all(g[k]['pass'] for k in gated),'G14_verdict':verdict}


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--check',action='store_true');a=ap.parse_args();obj=build()
    if a.check:check(OUT.read_bytes()==dumps(obj),'GATES.json does not reproduce');print('GATES reproduces')
    else:write_new(OUT,obj);print({k:obj[k] for k in ('passed','failed','all_gated_pass','G14_verdict')})
