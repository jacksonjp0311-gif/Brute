"""Evaluate the pre-registered study-006 criteria (BRUTE_PLAN_006: G1..G13, GR1, GR1b gated; G14', G15, G16, GR2, R1, R2,
R5, R6 reported) from sealed artifacts only.

Written and committed (process step 5) before any study-006 run; thresholds are copied from the plan, nothing is tuned.
Inputs in results/study-006: SCIENTIFIC.json + SEAL.json, RESULTS.json (timing, G10 only), CALIBRATION_006.json,
PAIRED_ANALYSIS.json, REPRODUCIBILITY.json, SECOND_IMPLEMENTATION_COUNT.json (experiments/v040_reference.py --mutate 20),
GR1.json, GR1B.json, GR2.json (experiments/exactness_006.py).

Scoring choices fixed here, before data:
- G5 counts a case if it has ANY alarm (first_alarm_step set, all steps); the post-burn-in count is reported next to it.
  The any-step count is a superset, so this is the stricter reading. The frozen 'cases_with_alarm' key reads the
  current alarm_step, which a resume clears, and is not used.
- G9 resume clause: for every resume step s of A4/P4, the 8 trace records ending at step s have residual_after <= tau6
  (not None) and the record at s has family_status_after and margin_status_after == 'supported'.
- G11: mismatching_arm_traces == 0, arm_traces_checked == 5 x main cases (A4, P4, A3, A2, E2), the count is of the
  sealed RESULTS.json, and the mutation test detects 20/20 with 0 false flags.
- G15/G16 coverage clause uses the PAIRED_ANALYSIS pooled point estimate (D2-A2, F2-A2) over in_family_original.
"""
from __future__ import annotations
import argparse,io,math,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common_006 import STUDY_DIR,PLAN,FREEZE,load,dumps,write_new,check,sha
from experiments.v011_independent_reference import ref_reason

OUT=STUDY_DIR/'GATES.json'
LN4=round(math.log(4),6)
ARMS=('A4','P4')
ALL_ARMS=('A4','P4','D2','F2','A3','A2','E2')
K=('certs_all','false_certs_all','counterfactual_certs_all','counterfactual_false_certs_all','public_certs_all','public_false_certs_all')
KD=('certs_all','false_certs_all','false_certs_drift_steps','false_certs_non_drift_steps','counterfactual_certs_all',
    'counterfactual_false_certs_all','counterfactual_false_certs_drift_steps','counterfactual_false_certs_non_drift_steps','stale_false_certs')


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


def build():
    from scripts.study006_storage import ensure_raw;ensure_raw()
    plan=load(PLAN);C=plan['criteria'];d=load(STUDY_DIR/'SCIENTIFIC.json');S=d['summary'];DS=d['d78_summary']
    seal=load(STUDY_DIR/'SEAL.json')
    check(seal['scientific_sha256']==sha(STUDY_DIR/'SCIENTIFIC.json'),'SCIENTIFIC does not match SEAL')
    check(seal['plan_sha256']==sha(PLAN) and seal['freeze_sha256']==sha(FREEZE),'seal plan/freeze mismatch')
    cal=load(STUDY_DIR/'CALIBRATION_006.json');check(seal['calibration_sha256']==sha(STUDY_DIR/'CALIBRATION_006.json'),'seal calibration mismatch')
    audit=load(STUDY_DIR/'SECOND_IMPLEMENTATION_COUNT.json');repro=load(STUDY_DIR/'REPRODUCIBILITY.json')
    paired=load(STUDY_DIR/'PAIRED_ANALYSIS.json');results=load(STUDY_DIR/'RESULTS.json')
    gr1=load(STUDY_DIR/'GR1.json');gr1b=load(STUDY_DIR/'GR1B.json');gr2=load(STUDY_DIR/'GR2.json')
    check(paired['scientific_sha256']==seal['scientific_sha256'],'paired analysis is of another SCIENTIFIC')
    inf,ifo,oof=plan['in_family'],plan['in_family_original'],plan['out_of_family'];cases=d['cases'];g={}
    tau6=cal['tau6']
    def gate(name,ok,obs,gated=True):g[name]={'gated':gated,'pass':bool(ok) if gated else None,'observed':obs}
    X=lambda f,arm:S[f][arm]
    # G1
    sound=lambda arms:all(X(f,a)['false_certs_all']==0 and X(f,a)['counterfactual_false_certs_all']==0 and X(f,a)['public_false_certs_all']==0
                         for f in inf for a in arms)
    gate('G1_in_family_soundness',sound(ARMS),{f:{a:{k:X(f,a)[k] for k in K} for a in ALL_ARMS} for f in inf})
    # G2
    ood=lambda arms:all(X('ood5',a)['false_certs_all']==0 and X('ood5',a)['counterfactual_false_certs_all']==0 for a in arms)
    gate('G2_ood5_soundness',ood(ARMS),
         {**{a:{k:X('ood5',a)[k] for k in K} for a in ALL_ARMS},'C_v011':S['ood5']['C_v011'],'v0.90':S['ood5']['v0.90']})
    # G3'
    D=S['drift4'];limit=0.5*D['v0.90']['false_certs_all']
    g3c=lambda a:{'non_drift_zero':X('drift4',a)['false_certs_non_drift_steps']==0,'total_within_limit':X('drift4',a)['false_certs_all']<=limit}
    def wrongs(arm,cf=False):
        out=[]
        for c in cases:
            if c['family']!='drift4':continue
            for r in c['arms'][arm]['trace']:
                q=r['counterfactual'] if cf else r
                if q['wrong']:out.append({'seed':c['seed'],'mask_rate':c['mask_rate'],'step':r['step'],'drift_step':r['drift_step'],
                    'certificate':q['certificate'],'actual':r['counterfactual_actual_EVALUATOR_ONLY' if cf else 'actual_emission_EVALUATOR_ONLY']})
        return out
    g3={a:g3c(a) for a in ARMS}
    gate('G3_prime_drift4',all(all(v.values()) for v in g3.values()),
         {'clauses':g3,'limit_total_false_certs':limit,**{a:{k:X('drift4',a)[k] for k in KD} for a in ALL_ARMS},
          'C_v011':{k:D['C_v011'][k] for k in ('certs_all','false_certs_all')},
          'v0.90':{k:D['v0.90'][k] for k in ('certs_all','false_certs_all','false_certs_drift_steps','false_certs_non_drift_steps')},
          'wrong_certificates':{a:wrongs(a) for a in ALL_ARMS},'counterfactual_wrong_certificates':{a:wrongs(a,True) for a in ALL_ARMS}})
    # G4
    g4={'a_no_public_on_ood5_drift4':all(X(f,a)['public_certs_all']==0 for f in oof for a in ARMS),
        'b_no_wrong_public_anywhere':all(X(f,a)['public_false_certs_all']==0 for f in S for a in ARMS),
        'c_no_public_after_first_alarm':all(X(f,a)['resume']['public_certs_after_first_alarm']==0 for f in S for a in ARMS)}
    gate('G4_public_safety',all(g4.values()),
         {'clauses':g4,**{f:{a:{'public_certs':X(f,a)['public_certs_all'],'public_false':X(f,a)['public_false_certs_all'],
                                'public_after_first_alarm':X(f,a)['resume']['public_certs_after_first_alarm'] if 'resume' in X(f,a) else None}
                             for a in ALL_ARMS} for f in S}})
    # G5
    alarm={f:{a:{'cases_with_any_alarm':X(f,a)['resume']['cases_with_any_alarm'],
                 'cases_with_any_alarm_post_burn_in':X(f,a)['resume']['cases_with_any_alarm_post_burn_in'],'cases':S[f]['cases'],
                 'fraction':round(X(f,a)['resume']['cases_with_any_alarm']/S[f]['cases'],6)} for a in ARMS} for f in S}
    for f in S:
        alarm[f]['A3_tau_v030_cases_with_alarm']=X(f,'A3')['cases_with_alarm'];alarm[f]['C_v011_cases_with_alarm']=S[f]['C_v011']['cases_with_alarm']
    gate('G5_false_alarm_limit',all(alarm[f][a]['fraction']<=0.05 for f in inf for a in ARMS),{'tau6':tau6,'per_family':alarm})
    # G6
    G6=paired['G6_dual_coverage_A4_minus_P4'];fams=G6['families']
    g6={'a_pooled_ge_0.05':G6['pooled_gain']>=0.05,'b_ci_lower_gt_0':G6['pooled_ci95'][0]>0,'c_every_family_ge_-0.01':all(fams[f]['gain']>=-0.01 for f in ifo)}
    cov={f:{a:X(f,a)['dual_coverage_post'] for a in ALL_ARMS} for f in S}
    gate('G6_active_coverage_gain',all(g6.values()),
         {'clauses':g6,'pooled_gain':G6['pooled_gain'],'pooled_ci95':G6['pooled_ci95'],'families':fams,
          'perm4_A4_minus_P4':paired['R6_perm4']['A4-P4'],'dual_coverage_post':cov,
          'on_policy_coverage_post':{f:{a:X(f,a)['on_policy_coverage_post'] for a in ALL_ARMS} for f in S},
          'C_v011_coverage_post':{f:S[f]['C_v011']['coverage_post'] for f in S},
          'selective_risk_post':{f:{a:X(f,a)['selective_risk_post'] for a in ALL_ARMS} for f in S},
          'per_mask_dual_coverage':{f:{a:{m:v['dual_coverage_post'] for m,v in X(f,a)['per_mask'].items()} for a in ALL_ARMS} for f in S}})
    # G6b'
    G6b=paired['G6b_prime_dual_coverage_A4_minus_A2']
    g6b={'a_pooled_ge_-0.03':G6b['pooled_gain']>=-0.03,'b_ci_lower_ge_-0.05':G6b['pooled_ci95'][0]>=-0.05}
    gate('G6b_prime_coverage_non_inferiority_vs_v020',all(g6b.values()),
         {'clauses':g6b,'pooled_A4_minus_A2':G6b['pooled_gain'],'pooled_ci95':G6b['pooled_ci95'],'families':G6b['families'],
          'reported_A3_minus_A2':paired['R_dual_coverage_A3_minus_A2']['pooled_gain'],
          'reported_A4_minus_A3':paired['R_dual_coverage_A4_minus_A3']['pooled_gain'],
          'pre_registered_risk':C['G6b_prime_coverage_non_inferiority_vs_v020']['pre_registered_risk']})
    # G7'
    ll={f:{**{a:X(f,a)['logloss_post'] for a in ALL_ARMS},'C_v011':S[f]['C_v011']['logloss_post'],'v0.90':S[f]['v0.90']['logloss_post'],'uniform':LN4} for f in S}
    minp={f:{**{a:X(f,a)['min_probability_any_step'] for a in ALL_ARMS},'C_v011':S[f]['C_v011']['min_probability_any_step']} for f in S}
    g7={'a_P4_le_C':all(ll[f]['P4']<=ll[f]['C_v011'] for f in oof),'a_A4_le_C':all(ll[f]['A4']<=ll[f]['C_v011'] for f in oof),
        'b_every_arm_le_ln4':all(ll[f][a]<=LN4 for f in oof for a in ALL_ARMS+('C_v011',)),
        'b_min_probability_ge_0.005':all(v>=0.005 for f in S for v in minp[f].values()),
        'c_A4_le_A3_plus_0.05':all(ll[f]['A4']<=round(ll[f]['A3']+0.05,6) for f in oof)}
    gate('G7_prime_open_world_no_regression',all(g7.values()),
         {'clauses':g7,'logloss_post':{f:ll[f] for f in oof},'min_probability_any_step':minp,
          'paired_bootstrap':{f:paired['logloss_contrasts'][f] for f in oof}})
    # G8
    pe={f:S[f]['G8a_passive_equivalence'] for f in S}
    g8a=all(v['probability_or_source_differences']==0 and v['non_resync_differences']==0 for v in pe.values())
    g8b={f:{'A4':ll[f]['A4'],'C_v011':ll[f]['C_v011'],'limit':round(ll[f]['C_v011']+0.05,6)} for f in inf}
    gate('G8_passive_equivalence',g8a and all(g8b[f]['A4']<=g8b[f]['limit'] for f in inf),
         {'a_P4_vs_C':pe,'a_holds':g8a,'b':g8b,'reported_in_family_logloss':{f:ll[f] for f in inf}})
    # G9
    reasons_ok=True;falsified=0;falsified_truth=0;totals={};dups=0;resync_issued=0;resume_bad=[];resumes=0
    W=plan['residual_surprise']['window_W']
    for c in cases:
        for a in ARMS:
            A=c['arms'][a];tr=A['trace']
            dups+=len(A['issued'])-len({tuple(x) for x in A['issued']})
            dups+=len(A['retractions'])-len({(e['step'],e['certificate']) for e in A['retractions']})
            resync_issued+=sum(tr[st-1]['reason']=='RESYNC_AMBIGUOUS' for st,_ in A['issued'])
            for e in A['retractions']:
                obs=tr[e['step']-1]['observed'];want=ref_reason(e['certificate'],obs)
                reasons_ok&=e['reason']==want;totals[e['reason']]=totals.get(e['reason'],0)+1
                falsified+=e['reason']=='falsified_by_observation'
                falsified_truth+=e['wrong'] and any(o is not None and o!=b for o,b in zip(obs,((e['certificate']>>1)&1,e['certificate']&1)))
            for s in A['diagnostics']['resume_steps']:
                resumes+=1;win=tr[max(0,s-W):s]
                ok=len(win)==W and all(r['residual_after'] is not None and r['residual_after']<=tau6 for r in win) \
                   and tr[s-1]['family_status_after']=='supported' and tr[s-1]['margin_status_after']=='supported'
                if not ok:resume_bad.append({'seed':c['seed'],'family':c['family'],'mask_rate':c['mask_rate'],'arm':a,'resume_step':s})
    dt=_dedup_tests_pass()
    gate('G9_retraction_semantics',reasons_ok and falsified==falsified_truth and dups==0 and dt['passed'] and resync_issued==0 and not resume_bad,
         {'reasons_match_reference':reasons_ok,'retraction_reasons_total':totals,'falsified':falsified,
          'retracted_wrong_with_contradicting_bit':falsified_truth,'duplicate_pairs':dups,'dedup_unit_tests':dt,
          'resync_ambiguous_in_issued':resync_issued,'resumes_checked':resumes,'resume_rule_violations':resume_bad,
          'per_family':{f:{a:{'reasons':X(f,a)['retraction_reasons'],'retracted_wrong':X(f,a)['retracted_wrong'],
                              'certificates_retracted':X(f,a)['certificates_retracted'],'resume':X(f,a)['resume']} for a in ARMS} for f in S}})
    # G10
    PK=('peak_rows_family','peak_rows_margin','peak_rows_window','peak_rows_lookahead')
    peak=max(X(f,a)[k] for f in S for a in ARMS for k in PK)
    bad_exh=0
    for c in cases:
        for a in ARMS:
            tr=c['arms'][a]['trace']
            for prev,r in zip(tr,tr[1:]):
                k=(r['status'],r['reason'])
                if prev['family_status_after']=='budget_exhausted' and k not in (('ABSTAIN','BUDGET_EXHAUSTED'),('OUT_OF_FAMILY','RESIDUAL_SURPRISE')):bad_exh+=1
                elif prev['margin_status_after']=='budget_exhausted' and r['status']=='CERTIFIED':bad_exh+=1
    RS=results['summary'];t={a:sum(RS[f][a]['time_informational_seconds'] for f in RS) for a in ALL_ARMS}
    gate('G10_compute_budget',peak<=160000 and bad_exh==0,
         {'peak_rows_A4_P4_incl_lookahead':peak,'limit':160000,'exhaustion_steps_not_budget_abstain':bad_exh,
          'per_family':{f:{a:{k:X(f,a)[k] for k in PK+('lookahead_budget_hits','lookahead_copies','budget_exhausted_family','budget_exhausted_margin')}
                           for a in ('A4','P4','D2','F2')} for f in S},
          'wall_clock_informational_seconds':{a:round(v,2) for a,v in t.items()},
          'D2_over_A4_informational':round(t['D2']/t['A4'],3) if t['A4'] else None})
    # G11
    mt=audit.get('mutation_test',{})
    g11={'zero_mismatching_traces':audit['mismatching_arm_traces']==0,'all_traces_counted':audit['arm_traces_checked']==5*len(cases),
         'of_sealed_results':audit['source_results_sha256']==seal['results_sha256'],
         'mutation_20_of_20':mt.get('injected')==20 and mt.get('detected_injected')==20 and mt.get('flagged_not_injected')==0}
    gate('G11_second_implementation',all(g11.values()),{'clauses':g11,**{k:audit[k] for k in audit if k not in ('mismatches',)}})
    # G12, G13
    gate('G12_reproducibility',repro['all_byte_identical'],repro['files'])
    g13={'calibration_byte_identical':repro['files']['CALIBRATION_006.json']['byte_identical'],
         'study_uses_that_tau6':d['calibration']==cal and d['cases'][0]['tau6']==cal['tau6'],
         'in_family_original_only':cal['out_of_family_data_used'] is False and set(cal['per_family_max_R'])==set(ifo)}
    gate('G13_tau6_reproduces',all(g13.values()),{'clauses':g13,**{k:cal[k] for k in ('tau6','per_family_max_R','argmax','calibration_cases')}})
    # GR1, GR1b
    for name,r in (('GR1_exactness_sealed',gr1),('GR1b_exactness_006',gr1b)):
        gate(name,r['mismatch_count']==0 and r['passed'] is True and r['limit'] is None and r['items_compared']>0,
             {k:v for k,v in r.items() if k!='mismatches'}|{'first_mismatches':r['mismatches'][:20]})
    # G14' (not gated)
    steps_in=sum(S[f]['steps_post_burn_in'] for f in ifo)
    chk={a:round(sum(X(f,a)['check_steps_post'] for f in ifo)/steps_in,6) for a in ('A2','E2','A3','A4')}
    sw={a:round(sum(X(f,a)['switch_rate_post']*S[f]['steps_post_burn_in'] for f in ifo)/steps_in,6) for a in ('A2','E2','A3','A4')}
    M=chk['E2']>0 and sw['E2']>sw['A2']
    cfk={a:sum(X(f,a)['counterfactual_certs_all'] for f in ifo) for a in ('A2','E2','A3','A4')}
    P1=cfk['E2']>=1.10*cfk['A2']
    R=paired['G14_prime_R_D78'];lo,hi=R['ci95'];SA2=R['S_Y']
    if M and P1 and SA2>=20 and hi is not None and hi<0.75:verdict='CONFIRMED'
    elif M and SA2>=20 and lo is not None and lo>0.5:verdict='FALSIFIED'
    else:verdict='OPEN'
    gate('G14_prime_D7_D8_powered',None,
         {'verdict':verdict,'M_manipulation_check':{'holds':M,'check_rate_post_in_family_original':chk,'switch_rate_post_in_family_original':sw},
          'P1_counterfactual_knowledge':{'holds':P1,'in_family_original_counterfactual_certs':cfk,
                                         'ratio_E2_over_A2':round(cfk['E2']/cfk['A2'],6) if cfk['A2'] else None},
          'S_D78':{a:DS['drift4'][a]['stale_false_certs'] for a in ('A2','E2')},'R_bootstrap':R,
          'S_A2_ge_20':SA2>=20,'reported_main_drift4':paired['G14_prime_R_main_drift4_reported'],
          'decision_rule':C['G14_prime_D7_D8_powered']['decision_rule'],'power':C['G14_prime_D7_D8_powered']['power']},gated=False)
    # G15, G16 (not gated candidate tests)
    for name,arm,key in (('G15_depth2_candidate','D2','G15_dual_coverage_D2_minus_A2'),('G16_fibre2_candidate','F2','G16_dual_coverage_F2_minus_A2')):
        cl={'G1':sound((arm,)),'G2':ood((arm,)),'G3_prime':all(g3c(arm).values()),'coverage_minus_A2_ge_-0.03':paired[key]['pooled_gain']>=-0.03}
        gate(name,None,{'candidate_passes':all(cl.values()),'clauses':cl,'coverage_minus_A2':paired[key],
                        'drift4':{k:X('drift4',arm)[k] for k in KD},'prediction_Simulated':C[name]['prediction_Simulated']},gated=False)
    # GR2 (not gated)
    gate('GR2_scaling',None,{k:gr2[k] for k in ('cases','budget_rows','sat_conf_budget_per_query','summary','by_mask_mean_case_time_s',
                                                'loglog_slopes','timing_note')},gated=False)
    # R1, R2, R5, R6
    gate('R1_price_of_robustness',None,
         {'A2_minus_A4_dual_coverage':{f:round(cov[f]['A2']-cov[f]['A4'],6) for f in S},
          'A2_minus_A4_per_mask':{f:{m:round(X(f,'A2')['per_mask'][m]['dual_coverage_post']-X(f,'A4')['per_mask'][m]['dual_coverage_post'],6)
                                     for m in X(f,'A4')['per_mask']} for f in S},
          'resync_abstentions_post':{f:{a:X(f,a)['resync_abstentions_post'] for a in ('A4','P4','D2','F2','A3')} for f in S}},gated=False)
    gate('R2_drift_post_jump',None,{a:X('drift4',a)['R2_post_jump'] for a in ('A4','P4','A3','A2','D2','F2')},gated=False)
    def first_alarm(f,arm,key='first_alarm_step'):
        v=[c['arms'][arm]['diagnostics'].get(key) for c in cases if c['family']==f]
        v=[x for x in v if x is not None];return {'cases_with_alarm':len(v),'mean_first_alarm_step':round(sum(v)/len(v),3) if v else None}
    after=[]
    for c in cases:
        for a in ('A4','P4'):
            rs=c['arms'][a]['diagnostics']['resume_steps']
            if rs:
                for r in c['arms'][a]['trace']:
                    for q,tag in ((r,'taken'),(r['counterfactual'],'counterfactual')):
                        if r['step']>rs[0] and q['wrong']:after.append({'seed':c['seed'],'family':c['family'],'mask_rate':c['mask_rate'],'arm':a,'step':r['step'],'which':tag})
    gate('R5_alarm_detection',None,
         {'detection':{f:{'A4_tau6':first_alarm(f,'A4'),'P4_tau6':first_alarm(f,'P4'),'A3_tau_v030':first_alarm(f,'A3','alarm_step')} for f in oof},
          'resumes':{f:{a:X(f,a)['resume'] for a in ARMS} for f in S},'false_certificates_after_a_resume':after},gated=False)
    gate('R6_perm4',None,{'dual_coverage_post':{a:cov['perm4'][a] for a in ('A4','P4','A2','A3')},'paired':paired['R6_perm4'],
                          'true_hidden_state_counts':S['perm4']['true_hidden_state_counts']},gated=False)
    gated=[k for k,v in g.items() if v['gated']]
    return {'schema':'brute.gates.v4_0','study':plan['study'],'plan_sha256':sha(PLAN),'scientific_sha256':seal['scientific_sha256'],
            'gates':g,'passed':[k for k in gated if g[k]['pass']],'failed':[k for k in gated if not g[k]['pass']],
            'all_gated_pass':all(g[k]['pass'] for k in gated),'G14_prime_verdict':verdict}


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--check',action='store_true');a=ap.parse_args();obj=build()
    if a.check:check(OUT.read_bytes()==dumps(obj),'GATES.json does not reproduce');print('GATES reproduces')
    else:write_new(OUT,obj);print({k:obj[k] for k in ('passed','failed','all_gated_pass','G14_prime_verdict')})
