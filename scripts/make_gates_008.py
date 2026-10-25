"""Evaluate the pre-registered study-008 criteria (BRUTE_PLAN_008: GA1, G1-G5, G6b, G7, G9-G13, GX2', GMC gated; GT1 is
evaluated at release step (10) by tests/test_release_060.py and recorded in GT1_008.json; R_dev_xcheck_007,
R_counts_breadth, R_coverage_all, R_drift_detail reported) from sealed artifacts only. Committed (process step 6) before the
held-out run_start; thresholds are copied from the plan, nothing is tuned.

Inputs in results/study-008: SCIENTIFIC.json + SEAL.json, RESULTS.json (timing only), PAIRED_ANALYSIS.json,
REPRODUCIBILITY.json, SECOND_IMPLEMENTATION_COUNT.json, ENUM_B5_008.json, XCHECK_008.json, GMC_COUNT_008.json,
GMC_BREADTH_008.json, R_DEV_XCHECK_007.json (and GT1_008.json when present).

Scoring choices fixed here, before data:
- "every action": 2x2 = taken + counterfactual forecast of each step; breadth = all k forecasts of each step.
- G1/G2/G4 tallies: all steps incl. burn-in; a public certificate is also a conditional certificate.
- G3': plan drift_definition, taken action: a false certificate is NON-DRIFT iff step > 12 and step not in {12,23,34};
  total = all taken-action false certificates on drift4; limit = 0.5 x sum of A4 v090_wrong (taken) on the same cases.
  Also reported (not gated): counterfactual false certificates and the count with study-007's coding (not a drift step).
- G4(c): a public certificate on any forecast of a step > diagnostics.first_alarm_step is a violation.
- G5: a case counts if diagnostics.first_alarm_step is set (any step).
- G6b: PAIRED_ANALYSIS G6b_dual_coverage_{R6,C6}_minus_A2 (pooled in_family_original_2x2, default_rng(20261026)).
- G7: mean post-burn-in taken-action log-loss rounded to 6 d.p. <= round(ln 4, 6) / round(ln 8, 6); min probability
  >= round(eps / 2**s, 12) on every step of every case for R6, C6, BR6, BC6 (eps = open_world_reserve_epsilon).
- G9: as study-007 for R6, C6 (tau6) and BR6, BC6 (tau7).
- G10: case counts equal the plan job counts, every arm trace has the plan step count; production arms = R6, C6, A5
  (2x2) and B5, BR6, BC6 (breadth): forecasts with solver_unknown > 0 <= 1% per block.
- G11: SECOND_IMPLEMENTATION_COUNT of the sealed RESULTS.json; mismatching == 0; traces checked == 2 x 2x2 cases +
  2 x breadth cases; mutation 20/20 detected, 0 false flags.
- G12: REPRODUCIBILITY.G12_pass (byte-identical repro cases AND GMC recount identical up to timeout-only UNKNOWNs).
- G13: check_freeze() (002-007 source freezes, v0.5.0 release freeze, 008 source freeze) holds now; SEAL plan/freeze
  sha equal; tau6/tau7 in the plan equal 1.645215321642 / 2.07944154168 and every case's recorded tau equals them.
- GX2': (i) XCHECK_008 mismatching traces == 0 (a mismatching trace contains >= 1 mismatching checked step);
  (ii) witness_replay_failures == 0; (iii) checked_fraction >= 0.99 for each of big6/sens3/act3/ood6s3 x B5/BR6/BC6
  (missing entry = fail); xcheck must cover every breadth case. (iv) enumeration verdicts = ENUM_B5_008 (B5, frozen
  v050_reference) and SECOND_IMPLEMENTATION_COUNT (BR6/BC6, v060_reference), both up to the row budget; a trace is a
  disagreement iff exactly one of xcheck / enumeration flags it (conservative: counted even if the flagged step lies
  outside the other's checked range). Both pass on a trace => every commonly checked step agrees with the sealed trace
  and hence with each other.
- GMC: on GMC_COUNT_008.json of the sealed RESULTS: coverage = R counted / EXPECTED sampled steps (360 cases x 9 steps;
  missing cases count as UNKNOWN); (ii) 0 disagreements; (iii) 0 sum-check violations.
- GA1: PASS iff for at least one X in {R6, C6}: G1(X), G2(X), G3'(X) and G6b(X) all pass (per-arm clauses below).
"""
from __future__ import annotations
import argparse,math,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common_008 import STUDY_DIR,PLAN,FREEZE,load,dumps,write_new,check,sha,plan_view,check_freeze
from experiments.v011_independent_reference import ref_reason
from experiments.v050_reference import k_reason

LN4,LN8=round(math.log(4),6),round(math.log(8),6)
NEW2=('R6','C6');NEWB=('BR6','BC6');SOUND_B=('B5','BR6','BC6');PROD2=('R6','C6','A5');PRODB=('B5','BR6','BC6')
DRIFT=(12,23,34);TAU6,TAU7=1.645215321642,2.07944154168
XFAM=('big6','sens3','act3','ood6s3')


def fcs(c,r):return [r,r['counterfactual']] if 'counterfactual' in r else r['forecasts']


def build(study=STUDY_DIR,block2='2x2',blockb='breadth',dry=False):
    study=Path(study)
    if study==STUDY_DIR:
        from scripts.study008_storage import ensure_raw;ensure_raw()
    plan=load(PLAN);view=plan_view(plan);C=plan['criteria'];d=load(study/'SCIENTIFIC.json');seal=load(study/'SEAL.json')
    check(seal['scientific_sha256']==sha(study/'SCIENTIFIC.json'),'SCIENTIFIC does not match SEAL')
    if not dry:check(seal['plan_sha256']==sha(PLAN) and seal['freeze_sha256']==sha(FREEZE),'seal plan/freeze mismatch')
    audit=load(study/'SECOND_IMPLEMENTATION_COUNT.json');enum=load(study/'ENUM_B5_008.json');xc=load(study/'XCHECK_008.json')
    repro=load(study/'REPRODUCIBILITY.json') if (study/'REPRODUCIBILITY.json').exists() or not dry else None
    paired=load(study/'PAIRED_ANALYSIS.json');gmc=load(study/'GMC_COUNT_008.json');results=load(study/'RESULTS.json')
    gmcb=load(study/'GMC_BREADTH_008.json') if (study/'GMC_BREADTH_008.json').exists() else None
    dev7=load(study/'R_DEV_XCHECK_007.json') if (study/'R_DEV_XCHECK_007.json').exists() else None
    check(paired['scientific_sha256']==seal['scientific_sha256'],'paired analysis is of another SCIENTIFIC')
    tau6,tau7=plan['tau6']['value'],plan['tau7']['value'];eps=view['open_world_reserve_epsilon'];W=view['window_W']
    two=[c for c in d['cases'] if c['block']==block2];br=[c for c in d['cases'] if c['block']==blockb]
    IF,IFO,OOF=plan['in_family_2x2'],plan['in_family_original_2x2'],plan['out_of_family_2x2']
    IB,OB=plan['in_family_breadth'],plan['out_of_family_breadth'];g={}
    def gate(name,ok,obs,gated=True):g[name]={'gated':gated,'pass':(bool(ok) if ok is not None else None) if gated else None,'observed':obs}
    fam=lambda cs,f:[c for c in cs if c['family']==f]
    def tally(cs,arm):
        t={'cases':len(cs),'forecasts':0,'certs':0,'false_certs':0,'public_certs':0,'public_false_certs':0}
        for c in cs:
            for r in c['arms'][arm]['trace']:
                for q in fcs(c,r):
                    t['forecasts']+=1;t['certs']+=q['certificate'] is not None;t['false_certs']+=bool(q['wrong'])
                    t['public_certs']+=q['public_certificate'] is not None;t['public_false_certs']+=bool(q['public_wrong'])
        t['rule_of_three_upper_false_rate']=round(3/t['certs'],6) if t['certs'] else None;return t
    blocks=[(two,IF,OOF,NEW2),(br,IB,OB,SOUND_B)]
    # G1
    g1={f:{a:tally(fam(cs,f),a) for a in arms} for cs,inf,_,arms in blocks for f in inf}
    ok1=lambda arms_:all(g1[f][a]['false_certs']==0 and g1[f][a]['public_false_certs']==0 for f in g1 for a in g1[f] if a in arms_)
    g1arm={a:ok1((a,)) for a in NEW2+SOUND_B}
    gate('G1_in_family_soundness',all(g1arm.values()),{'per_arm_pass':g1arm,'per_family':g1})
    # G2
    g2={'ood5':{a:tally(fam(two,'ood5'),a) for a in NEW2},'ood6s3':{a:tally(fam(br,'ood6s3'),a) for a in SOUND_B}}
    g2arm={a:g2['ood5'][a]['false_certs']==0 for a in NEW2};g2arm.update({a:g2['ood6s3'][a]['false_certs']==0 for a in SOUND_B})
    gate('G2_ood_soundness',all(g2arm.values()),{'per_arm_pass':g2arm,**g2,'prediction':C['G2_ood_soundness']['prediction']})
    # G3'
    D=fam(two,'drift4');v090=sum(bool(r['v090_wrong']) for c in D for r in c['arms']['A4']['trace']);limit=0.5*v090;g3={}
    nondrift=lambda s:s>12 and s not in DRIFT
    for a in NEW2:
        tr=[(c,r) for c in D for r in c['arms'][a]['trace']]
        tot=sum(bool(r['wrong']) for _,r in tr);nd=sum(bool(r['wrong']) and nondrift(r['step']) for _,r in tr)
        g3[a]={'false_certs_taken':tot,'false_certs_non_drift':nd,'non_drift_zero':nd==0,'total_within_limit':tot<=limit,
               'reported_counterfactual_false':sum(bool(r['counterfactual']['wrong']) for _,r in tr),
               'reported_counterfactual_false_non_drift':sum(bool(r['counterfactual']['wrong']) and nondrift(r['step']) for _,r in tr),
               'reported_taken_false_not_on_a_drift_step_study007_coding':sum(bool(r['wrong']) and not r['drift_step'] for _,r in tr)}
        g3[a]['pass']=g3[a]['non_drift_zero'] and g3[a]['total_within_limit']
    gate('G3_prime_drift4',all(v['pass'] for v in g3.values()),{'v090_control_false_certs':v090,'limit':limit,'drift_cases':len(D),**g3,
         'definition':plan['drift_definition']})
    # G4
    pub_oof={f:{a:tally(fam(cs,f),a)['public_certs'] for a in arms} for cs,_,oof,arms in blocks for f in oof}
    pub_wrong=sum(tally(cs,a)['public_false_certs'] for cs,_,_,arms in blocks for a in arms)
    after=sum(1 for cs,_,_,arms in blocks for c in cs for a in arms for r in c['arms'][a]['trace']
              if c['arms'][a]['diagnostics'].get('first_alarm_step') is not None and r['step']>c['arms'][a]['diagnostics']['first_alarm_step']
              for q in fcs(c,r) if q['public_certificate'] is not None)
    g4={'a_no_public_on_ood5_drift4_ood6s3':all(v==0 for f in pub_oof for v in pub_oof[f].values()),'b_no_wrong_public':pub_wrong==0,'c_no_public_after_first_alarm':after==0}
    gate('G4_public_safety',all(g4.values()),{'clauses':g4,'public_certs_out_of_family':pub_oof,'public_false_certs':pub_wrong,'public_after_first_alarm':after})
    # G5
    g5={}
    for cs,inf,arms in ((two,IF,NEW2),(br,IB,NEWB)):
        for f in inf:
            cc=fam(cs,f);g5[f]={a:{'cases':len(cc),'cases_with_alarm':sum(c['arms'][a]['diagnostics'].get('first_alarm_step') is not None for c in cc)} for a in arms}
            for v in g5[f].values():v['fraction']=round(v['cases_with_alarm']/v['cases'],6) if v['cases'] else None
    gate('G5_false_alarm_limit',all(v['fraction'] is not None and v['fraction']<=0.05 for f in g5 for v in g5[f].values()),{'tau6':tau6,'tau7':tau7,'per_family':g5})
    # G6b
    g6={}
    for a in NEW2:
        P=paired[f'G6b_dual_coverage_{a}_minus_A2'];g6[a]={'pooled_gain':P['pooled_gain'],'pooled_ci95':P['pooled_ci95'],
            'a_pooled_ge_-0.03':P['pooled_gain']>=-0.03,'b_ci_lower_ge_-0.05':P['pooled_ci95'][0]>=-0.05,'families':P['families']}
        g6[a]['pass']=g6[a]['a_pooled_ge_-0.03'] and g6[a]['b_ci_lower_ge_-0.05']
    gate('G6b_coverage_vs_v020',all(v['pass'] for v in g6.values()),{**g6,'reported_A5_minus_A2':paired['R_dual_coverage_A5_minus_A2']['pooled_gain'],
         'reported_A4_minus_A2':paired['R_dual_coverage_A4_minus_A2']['pooled_gain'],'prediction':C['G6b_coverage_vs_v020']['prediction']})
    # GA1
    ga={a:{'G1':g1arm[a],'G2':g2arm[a],'G3_prime':g3[a]['pass'],'G6b':g6[a]['pass']} for a in NEW2}
    for a in NEW2:ga[a]['all']=all(ga[a].values())
    gate('GA1_drift_sound_and_coverage',any(ga[a]['all'] for a in NEW2),{'per_arm':ga,'passing_arms':[a for a in NEW2 if ga[a]['all']],
         'note':'FAIL means target (a) is NOT met even if G3-prime and G6b are each passed by a DIFFERENT arm','prediction':C['GA1_drift_sound_and_coverage']['prediction']})
    # G7
    def mean_ll(cs,a):
        v=[r['logloss'] for c in cs for r in c['arms'][a]['trace'][c.get('burn_in',plan['burn_in']):]];return round(sum(v)/len(v),6) if v else None
    ll={'ood5':{a:mean_ll(fam(two,'ood5'),a) for a in NEW2},'drift4':{a:mean_ll(fam(two,'drift4'),a) for a in NEW2},'ood6s3':{a:mean_ll(fam(br,'ood6s3'),a) for a in NEWB}}
    minp_bad=[];minp={}
    for cs,arms in ((two,NEW2+('A5',)),(br,NEWB+('B5',))):
        for c in cs:
            thr=round(eps/2**c.get('s',2),12)
            for a in arms:
                mp=min(r['min_probability'] for r in c['arms'][a]['trace']);k=f"{c['family']}/{a}";minp[k]=min(minp.get(k,1),mp)
                if mp<thr-1e-12 and a in NEW2+NEWB:minp_bad.append({'family':c['family'],'seed':c['seed'],'mask_rate':c['mask_rate'],'arm':a,'min':mp,'threshold':thr})
    g7={'logloss_2x2_le_ln4':all(ll[f][a] is not None and ll[f][a]<=LN4 for f in ('ood5','drift4') for a in NEW2),
        'logloss_ood6s3_le_ln8':all(ll['ood6s3'][a] is not None and ll['ood6s3'][a]<=LN8 for a in NEWB),'min_probability':not minp_bad}
    gate('G7_open_world',all(g7.values()),{'clauses':g7,'logloss_post':ll,'ln4':LN4,'ln8':LN8,'eps':eps,'min_probability_by_family_arm':minp,'violations':minp_bad[:20]})
    # G9
    resumes=0;resume_bad=[];resync=0;reasons_ok=True;totals={};dups=0;bad_reason=[]
    for cs,arms,tau in ((two,NEW2,tau6),(br,NEWB,tau7)):
        for c in cs:
            for a in arms:
                A=c['arms'][a];tr=A['trace']
                dups+=len(A['issued'])-len({tuple(x) for x in A['issued']})+len(A['retractions'])-len({(e['step'],e['certificate']) for e in A['retractions']})
                resync+=sum(1 for r in tr for q in fcs(c,r) if q['certificate'] is not None and q['reason']=='RESYNC_AMBIGUOUS')
                resync+=sum(1 for s_,_ in A['issued'] if fcs(c,tr[s_-1])[0 if cs is two else tr[s_-1]['action']]['reason']=='RESYNC_AMBIGUOUS')
                for e in A['retractions']:
                    want=ref_reason(e['certificate'],e['observed']) if cs is two else k_reason(e['certificate'],e['observed'],c['s'])
                    if e['reason']!=want:reasons_ok=False;bad_reason.append({'family':c['family'],'seed':c['seed'],'arm':a,'step':e['step']})
                    totals[e['reason']]=totals.get(e['reason'],0)+1
                for s_ in A['diagnostics'].get('resume_steps',[]):
                    resumes+=1;win=tr[max(0,s_-W):s_]
                    ok=len(win)==W and all(r['residual_after'] is not None and r['residual_after']<=tau for r in win) \
                       and tr[s_-1]['family_status_after']=='supported' and tr[s_-1]['margin_status_after']=='supported'
                    if not ok:resume_bad.append({'family':c['family'],'seed':c['seed'],'mask_rate':c['mask_rate'],'arm':a,'resume_step':s_})
    gate('G9_retraction_resume',not resume_bad and resync==0 and reasons_ok and dups==0,
         {'resumes_checked':resumes,'resume_rule_violations':resume_bad[:50],'resync_ambiguous_certified_or_issued':resync,
          'retraction_reasons_match_reference':reasons_ok,'retraction_reason_mismatches':bad_reason[:50],'retraction_reasons_total':totals,'duplicate_pairs':dups})
    # G10
    nj={b:sum((hi-lo+1)*len(plan['mask_rates']) for lo,hi in plan[k].values()) for b,k in (('2x2','heldout_ranges_2x2'),('breadth','heldout_ranges_breadth'))}
    have={'2x2':len(two),'breadth':len(br)}
    short=[f"{c['block']}/{c['family']}/{c['seed']}/{c['mask_rate']}/{a}" for c in two+br for a in c['arms']
           if len(c['arms'][a]['trace'])!=(plan['actions_per_case_2x2'] if c in two else plan['actions_per_case_breadth'])]
    unk_rate={}
    for name,cs,arms in (('2x2',two,PROD2),('breadth',br,PRODB)):
        tot=u=0
        for c in cs:
            for a in arms:
                for r in c['arms'][a]['trace']:
                    for q in fcs(c,r):tot+=1;u+=(q.get('solver_unknown') or 0)>0
        unk_rate[name]={'arms':list(arms),'forecasts':tot,'with_unknown':u,'fraction':round(u/tot,6) if tot else None}
    wall={}
    for c in results['cases']:
        for a,A in c['arms'].items():k=f"{c['block']}/{a}";wall[k]=round(wall.get(k,0)+A.get('elapsed_informational',0),2)
    gate('G10_compute',(dry or have==nj) and not short and all(v['fraction'] is not None and v['fraction']<=0.01 for v in unk_rate.values()),
         {'cases_expected':nj,'cases_present':have,'short_traces':short[:20],'production_unknown_forecasts':unk_rate,
          'wall_clock_informational_seconds':wall,'timing_note':'informational, shared 8-CPU box; not a gate input'})
    # G11
    mt=audit.get('mutation_test',{})
    g11={'zero_mismatching_traces':audit['mismatching_arm_traces']==0,'all_traces_counted':audit['arm_traces_checked']==2*len(two)+2*len(br),
         'of_sealed_results':audit['source_sha256']==seal['results_sha256'],
         'mutation_20_of_20':mt.get('injected')==20 and mt.get('detected_injected')==20 and mt.get('flagged_not_injected')==0}
    gate('G11_second_implementation',all(g11.values()),{'clauses':g11,**{k:audit[k] for k in audit if k!='mismatches'},'mismatches':audit['mismatches'][:50]})
    # G12
    gate('G12_reproducibility',repro is not None and repro['G12_pass'] and repro['scientific_sha256']==seal['scientific_sha256'],
         None if repro is None else {'cases':repro['files'],'gmc_recount':repro['gmc_recount']})
    # G13
    try:check_freeze();fz=True;fz_err=None
    except Exception as exc:fz=False;fz_err=f'{type(exc).__name__}: {exc}'
    taus=sorted({c.get('tau6') for c in two})+sorted({c.get('tau') for c in br})
    g13={'freeze_chain_holds':fz,'plan_tau_values':tau6==TAU6 and tau7==TAU7,
         'cases_use_plan_tau':all(c.get('tau6')==tau6 for c in two) and all(c.get('tau')==tau7 for c in br)}
    gate('G13_frozen_controls_reproduce',all(g13.values()) and not dry or (dry and g13['plan_tau_values']),{'clauses':g13,'freeze_error':fz_err,'recorded_taus':taus})
    # GX2'
    fr={f'{f}/{a}':(xc['per_family_arm'].get(f'{f}/{a}') or {}).get('checked_fraction') for f in XFAM for a in SOUND_B}
    iii={k:v is not None and v>=0.99 for k,v in fr.items()}
    kx=lambda b:(b['family'],b['seed'],b['mask_rate'],b['arm'])
    xflag={kx(b) for b in xc['mismatches']};eflag={kx(b) for b in enum['mismatches']}|{kx(b) for b in audit['mismatches'] if b['arm'] in NEWB}
    dis=sorted(xflag^eflag)
    gx={'i_zero_mismatching':xc['mismatching_traces']==0,'ii_zero_witness_failures':xc['witness_replay_failures']==0,
        'iii_checked_ge_0.99_each':all(iii.values()),'covers_every_breadth_case':xc['cases']==len(br),
        'iv_zero_disagreements_with_enumeration':not dis}
    enum_cov={**enum['breadth_steps_checked'],**{k:v for k,v in audit['breadth_steps_checked'].items()}}
    gate('GX2_prime_breadth_exactness_nonenum',all(gx.values()),{'clauses':gx,'checked_fraction':fr,'per_family_arm':xc['per_family_arm'],
         'mismatches':xc['mismatches'][:50],'queries':xc['queries'],'unknown_queries':xc['unknown_queries'],'witness_replay_failures':xc['witness_replay_failures'],
         'disagreeing_traces':[list(x) for x in dis[:50]],'enumeration_coverage':enum_cov,'enumeration_B5_mismatching':enum['mismatching_arm_traces'],
         'wording':xc['wording'],'iv_scope':'trace-level: both pass => every commonly checked step agrees; one-sided flags counted as disagreements'})
    # GMC
    S=gmc['summary'];exp_cases=len([c for c in two if c['family'] in IFO]);exp_steps=exp_cases*len([s for s in range(1,plan['actions_per_case_2x2']+1) if s%4==0 and s>8])
    cov=round(S['R_counted']/exp_steps,6) if exp_steps else None
    gm={'i_coverage_ge_0.95':cov is not None and cov>=0.95,'ii_zero_disagreements':S['disagreements']==0,'iii_zero_sum_violations':S['sum_check_violations']==0,
        'of_sealed_results':gmc['results_sha256']==seal['results_sha256']}
    gate('GMC_model_counting_feasibility',all(gm.values()),{'clauses':gm,'coverage_over_expected':cov,'expected_cases':exp_cases,'expected_sampled_steps':exp_steps,
         'summary':S,'counter':gmc['counter'],'independent_check':gmc['independent_check'],'budget':gmc['budget'],'gated_separately':True,
         'prediction':C['GMC_model_counting_feasibility']['prediction']})
    # GT1 (evaluated at release step 10)
    gt=study/'GT1_008.json'
    gate('GT1_verifier_parse_errors',load(gt)['pass'] if gt.exists() else None,load(gt) if gt.exists() else
         {'status':'evaluated at process step (10) by tests/test_release_060.py; recorded in results/study-008/GT1_008.json'})
    # reported
    gate('R_dev_xcheck_007',None,None if dev7 is None else {k:v for k,v in dev7.items() if k!='mismatches'}|{'mismatches':dev7['mismatches'][:50],
         'note':plan['non_gated_reports']['R_dev_xcheck_007']},gated=False)
    gate('R_counts_breadth',None,None if gmcb is None else {'summary':gmcb['summary'],'budget':gmcb['budget']},gated=False)
    gate('R_coverage_all',None,{k:v for k,v in paired.items() if k.startswith('R_')},gated=False)
    det=[]
    for c in D:
        for a in ('R6','C6','A5','A4','A2'):
            for r in c['arms'][a]['trace']:
                for side,q in (('taken',r),('counterfactual',r['counterfactual'])):
                    if q['wrong']:
                        last=max([x for x in DRIFT if x<=r['step']],default=None)
                        det.append({'arm':a,'seed':c['seed'],'mask_rate':c['mask_rate'],'step':r['step'],'action':side,'public':bool(q['public_wrong']),
                                    'steps_after_last_drift':None if last is None else r['step']-last,'non_drift':nondrift(r['step'])})
    gate('R_drift_detail',None,{'false_certificates':det,'count_by_arm':{a:sum(x['arm']==a for x in det) for a in ('R6','C6','A5','A4','A2')}},gated=False)
    gated=[k for k,v in g.items() if v['gated'] and v['pass'] is not None]
    return {'schema':'brute.gates.v6_0','study':plan['study'],'plan_sha256':sha(PLAN),'scientific_sha256':seal['scientific_sha256'],
            'gates':g,'passed':[k for k in gated if g[k]['pass']],'failed':[k for k in gated if not g[k]['pass']],
            'pending':[k for k,v in g.items() if v['gated'] and v['pass'] is None],
            'all_gated_pass':all(g[k]['pass'] for k in gated) and not [k for k,v in g.items() if v['gated'] and v['pass'] is None],
            'GA1':g['GA1_drift_sound_and_coverage']['pass'],'GX2_prime':g['GX2_prime_breadth_exactness_nonenum']['pass'],'GMC':g['GMC_model_counting_feasibility']['pass']}


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--study-dir',default=str(STUDY_DIR));ap.add_argument('--check',action='store_true')
    ap.add_argument('--output',default='GATES_008.json');ap.add_argument('--smoke',action='store_true',help='dry run on smoke data; prints only')
    a=ap.parse_args()
    if a.smoke:
        obj=build(Path(a.study_dir),'smoke-2x2','smoke-breadth',dry=True);print({k:obj[k] for k in ('passed','failed','pending')});raise SystemExit
    obj=build(Path(a.study_dir));out=Path(a.study_dir)/a.output
    if a.check:check(out.read_bytes()==dumps(obj),out.name+' does not reproduce');print(out.name,'reproduces')
    else:write_new(out,obj);print({k:obj[k] for k in ('passed','failed','pending','all_gated_pass')})
