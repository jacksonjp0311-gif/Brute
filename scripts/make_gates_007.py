"""Evaluate the pre-registered study-007 criteria (BRUTE_PLAN_007: GX1-GX3, G1-G5, G6b (M5), G7, G9-G13 gated; GM,
GR2', R_breadth reported) from sealed artifacts only. Committed (process step 5) before any study-007 run; thresholds
are copied from the plan, nothing is tuned.

Inputs in results/study-007: SCIENTIFIC.json + SEAL.json, RESULTS.json (timing only), CALIBRATION_007.json,
PAIRED_ANALYSIS.json, REPRODUCIBILITY.json, SECOND_IMPLEMENTATION_COUNT.json, SCALING_007.json.

Scoring choices fixed here, before data:
- "every action": 2x2 = taken + counterfactual forecast of each step; breadth/stress = all k forecasts of each step.
- GX1: compared per step (A5 vs A4): action; experiment scores/score/tied/proposal; for taken and counterfactual:
  status, reason, certificate, public_certificate, support, margin_support, saturated, probabilities, forecast_source;
  surprise, residual_after, alarm_after. Arm level: issued, retractions, alarm_steps and resume_steps restricted to
  compared steps (one mismatch each if they differ). Exclusion: from the first step whose A4 family/margin/window
  status_after is budget_exhausted (inclusive); the frozen A4 trace records lookahead budget hits only per case
  (diagnostics.lookahead_budget_hits), so a case with any hit is excluded from step 1 (conservative for the 1% clause);
  plus each step where A5 has solver_unknown > 0 on either forecast.
- GX2: mismatching breadth traces of the count (B5/BM5/BP5) must be 0, and sens3/act3/ood6s3 steps_checked/steps
  >= 0.90 for every breadth arm; big6 unchecked share reported.
- GX3: OPEN (gate not passed) if the stress block has no forecast with solver_unknown > 0. (c) = the unit tests
  test_tiny_budget_abstains_with_reason and test_feasibility_unknown_is_budget_exhausted pass when gates are made.
- G3': taken-action false certificates of A5 and M5 on drift4; v0.90 control = v090_wrong of the A4 full trace.
- G4(c): a public certificate on any forecast of a step > diagnostics.first_alarm_step is a violation.
- G5: a case counts if diagnostics.first_alarm_step is set (any step).
- G7: mean post-burn-in taken-action log-loss rounded to 6 d.p. <= round(ln 4, 6) / round(ln 8, 6); min probability
  >= round(eps / 2**s, 12) for every step of every case of the arm (eps = open_world_reserve_epsilon).
- G9: resume rule as study-006 with tau6 (2x2) or tau7 (breadth); no forecast with a certificate and reason
  RESYNC_AMBIGUOUS, and no issued pair whose taken forecast has reason RESYNC_AMBIGUOUS; "retractions only at
  contradiction" = every retraction reason equals the reference reason for its observation (2x2:
  v011_independent_reference.ref_reason; breadth: v050_reference.k_reason) and no duplicate issued/retraction pairs.
- G10: case counts equal the plan job counts and every arm trace has the plan step count; production arms (A5, M5,
  B5, BM5, BP5; stress excluded) forecasts with solver_unknown > 0 <= 1% per block.
- G11: count of the sealed RESULTS.json, mismatching == 0, traces checked == 3 x 2x2 cases + 3 x breadth cases,
  mutation 20/20 detected with 0 false flags.
"""
from __future__ import annotations
import argparse,io,math,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common_007 import STUDY_DIR,PLAN,FREEZE,load,dumps,write_new,check,sha
from experiments.v011_independent_reference import ref_reason
from experiments.v050_reference import k_reason

LN4,LN8=round(math.log(4),6),round(math.log(8),6)
NEW2=('A5','M5');NEWB=('B5','BM5','BP5')
F_STEP=('surprise','residual_after','alarm_after')
F_FC=('status','reason','certificate','public_certificate','support','margin_support','saturated','probabilities','forecast_source')


def fcs(c,r):return [r,r['counterfactual']] if c['block']=='2x2' else r['forecasts']


def _unit_tests():
    sys.path.insert(0,str(ROOT/'tests'));import test_v050_impl as T
    names=('test_tiny_budget_abstains_with_reason','test_feasibility_unknown_is_budget_exhausted');suite=unittest.TestSuite()
    for cls in [v for v in vars(T).values() if isinstance(v,type) and issubclass(v,unittest.TestCase)]:
        for n in names:
            if hasattr(cls,n):suite.addTest(cls(n))
    r=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(suite)
    return {'tests':list(names),'run':r.testsRun,'passed':r.wasSuccessful() and r.testsRun==len(names)}


def gx1_case(c):
    a5,a4=c['arms']['A5'],c['arms']['A4'];t5,t4=a5['trace'],a4['trace'];n=len(t4);e=n+1
    if a4['diagnostics'].get('lookahead_budget_hits',0):e=1
    else:
        for r in t4:
            if 'budget_exhausted' in (r.get('family_status_after'),r.get('margin_status_after'),r.get('window_status_after')):e=r['step'];break
    excl=set(range(e,n+1))|{r['step'] for r in t5 if r['solver_unknown'] or r['counterfactual']['solver_unknown']}
    mism=[]
    for r5,r4 in zip(t5,t4):
        s=r4['step']
        if s in excl:continue
        bad=[k for k in ('action',)+F_STEP if r5[k]!=r4[k]]
        bad+=['experiment.'+k for k in ('scores','score','tied','proposal') if r5['experiment'][k]!=r4['experiment'][k]]
        bad+=[f'{w}.{k}' for w,(x,y) in (('taken',(r5,r4)),('counterfactual',(r5['counterfactual'],r4['counterfactual']))) for k in F_FC if x[k]!=y[k]]
        if bad:mism.append({'step':s,'fields':bad})
    keep=lambda st:st not in excl
    arm=[]
    if [x for x in a5['issued'] if keep(x[0])]!=[x for x in a4['issued'] if keep(x[0])]:arm.append('issued')
    if [x for x in a5['retractions'] if keep(x['step'])]!=[x for x in a4['retractions'] if keep(x['step'])]:arm.append('retractions')
    for k in ('alarm_steps','resume_steps'):
        if [x for x in a5['diagnostics'].get(k,[]) if keep(x)]!=[x for x in a4['diagnostics'].get(k,[]) if keep(x)]:arm.append(k)
    return n,len(excl),mism,arm


def build(study=STUDY_DIR):
    study=Path(study)
    if study==STUDY_DIR:
        from scripts.study007_storage import ensure_raw;ensure_raw()
    plan=load(PLAN);C=plan['criteria'];d=load(study/'SCIENTIFIC.json');seal=load(study/'SEAL.json')
    check(seal['scientific_sha256']==sha(study/'SCIENTIFIC.json'),'SCIENTIFIC does not match SEAL')
    check(seal['plan_sha256']==sha(PLAN) and seal['freeze_sha256']==sha(FREEZE),'seal plan/freeze mismatch')
    cal=load(study/'CALIBRATION_007.json');check(seal['calibration_sha256']==sha(study/'CALIBRATION_007.json'),'seal calibration mismatch')
    audit=load(study/'SECOND_IMPLEMENTATION_COUNT.json');repro=load(study/'REPRODUCIBILITY.json')
    paired=load(study/'PAIRED_ANALYSIS.json');scal=load(study/'SCALING_007.json');results=load(study/'RESULTS.json')
    check(paired['scientific_sha256']==seal['scientific_sha256'],'paired analysis is of another SCIENTIFIC')
    tau6,tau7=plan['tau6']['value'],cal['tau7'];eps=plan['open_world_reserve_epsilon'];W=plan['window_W']
    two=[c for c in d['cases'] if c['block']=='2x2'];br=[c for c in d['cases'] if c['block']=='breadth'];st=d['stress_cases']
    IF,IFO,OOF=plan['in_family_2x2'],plan['in_family_original_2x2'],plan['out_of_family_2x2']
    IB,OB=plan['in_family_breadth'],plan['out_of_family_breadth'];g={}
    def gate(name,ok,obs,gated=True):g[name]={'gated':gated,'pass':bool(ok) if gated else None,'observed':obs}
    fam=lambda cs,f:[c for c in cs if c['family']==f]
    def tally(cs,arm,pred=lambda c,r,q:True):
        t={'forecasts':0,'certs':0,'false_certs':0,'public_certs':0,'public_false_certs':0}
        for c in cs:
            for r in c['arms'][arm]['trace']:
                for q in fcs(c,r):
                    if not pred(c,r,q):continue
                    t['forecasts']+=1;t['certs']+=q['certificate'] is not None;t['false_certs']+=bool(q['wrong'])
                    t['public_certs']+=q['public_certificate'] is not None;t['public_false_certs']+=bool(q['public_wrong'])
        t['rule_of_three_upper_false_rate']=round(3/t['certs'],6) if t['certs'] else None;return t
    blocks=[(two,IF,OOF,NEW2),(br,IB,OB,NEWB)]
    # GX1
    n_steps=n_excl=0;mm=[];arm_mm=[]
    for c in two:
        n,x,m,a=gx1_case(c);n_steps+=n;n_excl+=x
        if m:mm.append({'family':c['family'],'seed':c['seed'],'mask_rate':c['mask_rate'],'steps':m[:5],'count':len(m)})
        if a:arm_mm.append({'family':c['family'],'seed':c['seed'],'mask_rate':c['mask_rate'],'fields':a})
    nm=sum(x['count'] for x in mm)+len(arm_mm)
    gate('GX1_backend_exactness_2x2',nm==0 and n_excl<=0.01*n_steps,
         {'steps':n_steps,'excluded_steps':n_excl,'excluded_fraction':round(n_excl/n_steps,6) if n_steps else None,
          'mismatching_steps_plus_arm_level':nm,'step_mismatches':mm[:50],'arm_level_mismatches':arm_mm[:50]})
    # GX2
    bm=[b for b in audit['mismatches'] if b['arm'] in NEWB];cov=audit['breadth_steps_checked']
    frac={k:round(v['steps_checked']/v['steps'],6) if v['steps'] else None for k,v in cov.items()}
    gx2c={f:all(frac[f'{f}/{a}'] is not None and frac[f'{f}/{a}']>=0.90 for a in NEWB) for f in ('sens3','act3','ood6s3')}
    gate('GX2_backend_exactness_breadth',not bm and all(gx2c.values()),
         {'mismatching_breadth_traces':len(bm),'mismatches':bm[:50],'checked_fraction':frac,'ge_0.90':gx2c,
          'big6_unchecked_share':{a:round(1-frac[f'big6/{a}'],6) for a in NEWB if frac.get(f'big6/{a}') is not None},'coverage':cov})
    # GX3
    unk=[];bad_unk=0;stress_false=0
    for c in st:
        for r in c['arms']['B5']['trace']:
            for q in r['forecasts']:
                stress_false+=bool(q['wrong'])
                if q['solver_unknown']:
                    unk.append(1)
                    ok=q['certificate'] is None and ((q['status']=='ABSTAIN' and q['reason'] in ('SOLVER_BUDGET','BUDGET_EXHAUSTED')) or q['status']=='OUT_OF_FAMILY')
                    bad_unk+=not ok
    prod_cert_unk=sum(1 for cs,_,_,arms in blocks for c in cs for a in arms for r in c['arms'][a]['trace'] for q in fcs(c,r)
                      if q['solver_unknown'] and q['certificate'] is not None)
    ut=_unit_tests();opened=len(unk)==0
    gate('GX3_budget_abstains',(not opened) and bad_unk==0 and stress_false==0 and prod_cert_unk==0 and ut['passed'],
         {'verdict':'OPEN' if opened else ('PASS' if bad_unk==0 and stress_false==0 and prod_cert_unk==0 and ut['passed'] else 'FAIL'),
          'a_stress_forecasts_with_unknown':len(unk),'a_unknown_forecasts_not_abstaining':bad_unk,'a_stress_false_certs':stress_false,
          'a_stress_tally':tally(st,'B5'),'b_production_certs_with_unknown':prod_cert_unk,'c_unit_tests':ut})
    # G1
    g1={f:{a:tally(fam(cs,f),a) for a in arms} for cs,inf,_,arms in blocks for f in inf}
    gate('G1_in_family_soundness',all(v['false_certs']==0 and v['public_false_certs']==0 for f in g1 for v in g1[f].values()),g1)
    # G2
    g2={f:{a:tally(fam(cs,f),a) for a in arms} for cs,_,oof,arms in blocks for f in oof if f!='drift4'}
    gate('G2_ood_soundness',all(v['false_certs']==0 for f in g2 for v in g2[f].values()),
         {**g2,'pre_registered_risk':C['G2_ood_soundness']['pre_registered_risk']})
    # G3'
    D=fam(two,'drift4');v090=sum(r['v090_wrong'] for c in D for r in c['arms']['A4']['trace']);limit=0.5*v090;g3={}
    for a in NEW2:
        tot=sum(bool(r['wrong']) for c in D for r in c['arms'][a]['trace']);nd=sum(bool(r['wrong']) and not r['drift_step'] for c in D for r in c['arms'][a]['trace'])
        cf=sum(bool(r['counterfactual']['wrong']) for c in D for r in c['arms'][a]['trace'])
        g3[a]={'false_certs_taken':tot,'false_certs_non_drift':nd,'counterfactual_false_reported':cf,'non_drift_zero':nd==0,'total_within_limit':tot<=limit}
    gate('G3_prime_drift4',all(v['non_drift_zero'] and v['total_within_limit'] for v in g3.values()),
         {'v090_control_false_certs':v090,'limit':limit,**g3})
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
    for cs,inf,_,arms in blocks:
        for f in inf:
            cc=fam(cs,f);g5[f]={a:{'cases':len(cc),'cases_with_alarm':sum(c['arms'][a]['diagnostics'].get('first_alarm_step') is not None for c in cc)} for a in arms}
            for v in g5[f].values():v['fraction']=round(v['cases_with_alarm']/v['cases'],6) if v['cases'] else None
    gate('G5_false_alarm_limit',all(v['fraction'] is not None and v['fraction']<=0.05 for f in g5 for v in g5[f].values()),{'tau6':tau6,'tau7':tau7,'per_family':g5})
    # G6b
    G6=paired['G6b_dual_coverage_M5_minus_A2'];g6={'a_pooled_ge_-0.03':G6['pooled_gain']>=-0.03,'b_ci_lower_ge_-0.05':G6['pooled_ci95'][0]>=-0.05}
    gate('G6b_M_coverage_vs_v020',all(g6.values()),{'clauses':g6,'M5_minus_A2':G6,'reported_A5_minus_A2':paired['R_dual_coverage_A5_minus_A2']['pooled_gain'],
         'reported_A4_minus_A2':paired['R_dual_coverage_A4_minus_A2']['pooled_gain'],'prediction':C['G6b_M_coverage_vs_v020']['prediction']})
    # G7
    def mean_ll(cs,a):
        v=[r['logloss'] for c in cs for r in c['arms'][a]['trace'][c['burn_in']:]];return round(sum(v)/len(v),6) if v else None
    ll={'ood5':{a:mean_ll(fam(two,'ood5'),a) for a in NEW2},'drift4':{a:mean_ll(fam(two,'drift4'),a) for a in NEW2},'ood6s3':{a:mean_ll(fam(br,'ood6s3'),a) for a in NEWB}}
    minp_bad=[];minp={}
    for cs,_,_,arms in blocks:
        for c in cs:
            thr=round(eps/2**c.get('s',2),12)
            for a in arms:
                mp=min(r['min_probability'] for r in c['arms'][a]['trace']);k=f"{c['family']}/{a}";minp[k]=min(minp.get(k,1),mp)
                if mp<thr-1e-12:minp_bad.append({'family':c['family'],'seed':c['seed'],'mask_rate':c['mask_rate'],'arm':a,'min':mp,'threshold':thr})
    g7={'logloss_2x2_le_ln4':all(ll[f][a]<=LN4 for f in ('ood5','drift4') for a in NEW2),'logloss_ood6s3_le_ln8':all(ll['ood6s3'][a]<=LN8 for a in NEWB),
        'min_probability':not minp_bad}
    gate('G7_open_world',all(g7.values()),{'clauses':g7,'logloss_post':ll,'ln4':LN4,'ln8':LN8,'min_probability_by_family_arm':minp,'violations':minp_bad[:20]})
    # G9
    resumes=0;resume_bad=[];resync=0;reasons_ok=True;totals={};dups=0
    for cs,_,_,arms in blocks:
        tau=tau6 if cs is two else tau7
        for c in cs:
            for a in arms:
                A=c['arms'][a];tr=A['trace']
                dups+=len(A['issued'])-len({tuple(x) for x in A['issued']})+len(A['retractions'])-len({(e['step'],e['certificate']) for e in A['retractions']})
                resync+=sum(1 for r in tr for q in fcs(c,r) if q['certificate'] is not None and q['reason']=='RESYNC_AMBIGUOUS')
                resync+=sum(1 for s_,_ in A['issued'] if fcs(c,tr[s_-1])[0 if cs is two else tr[s_-1]['action']]['reason']=='RESYNC_AMBIGUOUS')
                for e in A['retractions']:
                    want=ref_reason(e['certificate'],e['observed']) if cs is two else k_reason(e['certificate'],e['observed'],c['s'])
                    reasons_ok&=e['reason']==want;totals[e['reason']]=totals.get(e['reason'],0)+1
                for s_ in A['diagnostics'].get('resume_steps',[]):
                    resumes+=1;win=tr[max(0,s_-W):s_]
                    ok=len(win)==W and all(r['residual_after'] is not None and r['residual_after']<=tau for r in win) \
                       and tr[s_-1]['family_status_after']=='supported' and tr[s_-1]['margin_status_after']=='supported'
                    if not ok:resume_bad.append({'family':c['family'],'seed':c['seed'],'mask_rate':c['mask_rate'],'arm':a,'resume_step':s_})
    gate('G9_retraction_resume',not resume_bad and resync==0 and reasons_ok and dups==0,
         {'resumes_checked':resumes,'resume_rule_violations':resume_bad,'resync_ambiguous_certified_or_issued':resync,
          'retraction_reasons_match_reference':reasons_ok,'retraction_reasons_total':totals,'duplicate_pairs':dups})
    # G10
    nj={b:sum((hi-lo+1)*len(plan['mask_rates']) for lo,hi in plan[k].values()) for b,k in (('2x2','heldout_ranges_2x2'),('breadth','heldout_ranges_breadth'))}
    sb=plan['stress_block'];nj['stress']=(sb['range'][1]-sb['range'][0]+1)*len(sb['mask_rates'])
    have={'2x2':len(two),'breadth':len(br),'stress':len(st)}
    short=[f"{c['block']}/{c['family']}/{c['seed']}/{c['mask_rate']}/{a}" for c in two+br+st for a in c['arms']
           if len(c['arms'][a]['trace'])!=(plan['actions_per_case_2x2'] if c['block']=='2x2' else plan['actions_per_case_breadth'])]
    unk_rate={}
    for name,cs,arms in (('2x2',two,NEW2),('breadth',br,NEWB)):
        tot=u=0
        for c in cs:
            for a in arms:
                for r in c['arms'][a]['trace']:
                    for q in fcs(c,r):tot+=1;u+=q['solver_unknown']>0
        unk_rate[name]={'forecasts':tot,'with_unknown':u,'fraction':round(u/tot,6) if tot else None}
    RC={(c['block'],c['family'],c['seed'],c['mask_rate']):c for c in results['cases']+results['stress_cases']}
    wall={};maxstep={}
    for c in RC.values():
        for a,A in c['arms'].items():
            k=f"{c['block']}/{a}";wall[k]=wall.get(k,0)+A.get('elapsed_informational',0)
    wall={k:round(v,2) for k,v in wall.items()}
    gate('G10_compute',have==nj and not short and all(v['fraction'] is not None and v['fraction']<=0.01 for v in unk_rate.values()),
         {'cases_expected':nj,'cases_present':have,'short_traces':short[:20],'production_unknown_forecasts':unk_rate,
          'wall_clock_informational_seconds':wall,
          'A5_over_A4_wall_informational':round(wall['2x2/A5']/wall['2x2/A4'],3) if wall.get('2x2/A4') else None,
          'timing_note':'informational, shared 8-CPU box with other agents running; not a gate input'})
    # G11
    mt=audit.get('mutation_test',{})
    g11={'zero_mismatching_traces':audit['mismatching_arm_traces']==0,'all_traces_counted':audit['arm_traces_checked']==3*len(two)+3*len(br),
         'of_sealed_results':audit['source_results_sha256']==seal['results_sha256'],
         'mutation_20_of_20':mt.get('injected')==20 and mt.get('detected_injected')==20 and mt.get('flagged_not_injected')==0}
    gate('G11_second_implementation',all(g11.values()),{'clauses':g11,**{k:audit[k] for k in audit if k!='mismatches'},'mismatches':audit['mismatches'][:50]})
    # G12, G13
    gate('G12_reproducibility',repro['all_byte_identical'] and repro['scientific_sha256']==seal['scientific_sha256'],repro['files'])
    g13={'calibration_byte_identical':repro['files']['CALIBRATION_007.json']['byte_identical'],
         'study_uses_that_tau7':d['calibration']==cal and all(c['tau']==tau7 for c in br+st),
         'in_family_breadth_only':cal['out_of_family_data_used'] is False and set(cal['per_family_max_R'])==set(IB)}
    gate('G13_tau7_reproduces',all(g13.values()),{'clauses':g13,**{k:cal[k] for k in ('tau7','per_family_max_R','argmax','calibration_cases')}})
    # GM (reported)
    GM=paired['GM_dual_coverage_M5_minus_A5'];lo,hi=GM['pooled_ci95']
    m5ok=g1['cycle3']['M5']['false_certs']==0 and all(g1[f]['M5']['false_certs']==0 and g1[f]['M5']['public_false_certs']==0 for f in IF) \
         and all(v['M5']['false_certs']==0 for f,v in g2.items() if 'M5' in v) and g3['M5']['non_drift_zero'] and g3['M5']['total_within_limit']
    verdict='SUPPORTED' if lo>0 and m5ok else ('HARMFUL' if hi<0 else 'NOT DISTINGUISHED')
    def lur(scores,default):
        mx=max(scores);top=[i for i,v in enumerate(scores) if v==mx];return default if default in top else min(top)
    ties={};over={}
    for cs,arm in ((two,'M5'),(br,'BM5')):
        for c in cs:
            k=f"{c['block']}/{c['family']}";ties.setdefault(k,[0,0,0]);
            for r in c['arms'][arm]['trace']:
                e=r['experiment'];ties[k][0]+=1;ties[k][1]+=bool(e['tied'])
                ties[k][2]+=e.get('volumes') is not None and r['action']!=lur(e['scores'],r['passive_action'])
    gate('GM_projection_volume_mechanism',None,{'verdict':verdict,'decision_rule':C['GM_projection_volume_mechanism']['decision_rule'],
         'M5_minus_A5':GM,'M5_minus_A5_per_mask':paired['GM_dual_coverage_M5_minus_A5_per_mask'],
         'BM5_minus_B5':paired['GM_breadth_coverage_BM5_minus_B5'],'BP5_minus_B5':paired['R_breadth_coverage_BP5_minus_B5'],
         'steps_tied_overridden':{k:{'steps':v[0],'tied':v[1],'M_overrides_LU-R':v[2]} for k,v in ties.items()},
         'M5_soundness_holds':m5ok,'prediction':C['GM_projection_volume_mechanism']['prediction']},gated=False)
    gate('GR2_prime_scaling',None,{k:scal[k] for k in scal if k not in ('cases','records')},gated=False)
    # R_breadth (reported)
    rb={}
    for f in list(IB)+list(OB):
        cc=fam(br,f);rb[f]={}
        for a in NEWB:
            post=[q for c in cc for r in c['arms'][a]['trace'][c['burn_in']:] for q in r['forecasts']]
            sts={}
            for q in post:sts[q['status'] if q['status']!='ABSTAIN' else 'ABSTAIN/'+str(q['reason'])]=sts.get(q['status'] if q['status']!='ABSTAIN' else 'ABSTAIN/'+str(q['reason']),0)+1
            fa=[c['arms'][a]['diagnostics'].get('first_alarm_step') for c in cc];fa=[x for x in fa if x is not None]
            rb[f][a]={'all_action_coverage_post':round(sum(q['certificate'] is not None for q in post)/len(post),6) if post else None,
                      'per_mask':{str(m):round(sum(q['certificate'] is not None for c in cc if c['mask_rate']==m for r in c['arms'][a]['trace'][c['burn_in']:] for q in r['forecasts'])/
                                  max(1,sum(len(r['forecasts']) for c in cc if c['mask_rate']==m for r in c['arms'][a]['trace'][c['burn_in']:])),6) for m in plan['mask_rates']},
                      'status_breakdown_post':dict(sorted(sts.items())),'cases_with_alarm':len(fa),'cases':len(cc),
                      'mean_first_alarm_step':round(sum(fa)/len(fa),3) if fa else None}
        ms={};[ms.__setitem__(str(c.get('minimal_state_count_EVALUATOR_ONLY')),ms.get(str(c.get('minimal_state_count_EVALUATOR_ONLY')),0)+1) for c in cc]
        rb[f]['minimal_state_count_EVALUATOR_ONLY_histogram']=dict(sorted(ms.items()))
    gate('R_breadth',None,rb,gated=False)
    gated=[k for k,v in g.items() if v['gated']]
    return {'schema':'brute.gates.v5_0','study':plan['study'],'plan_sha256':sha(PLAN),'scientific_sha256':seal['scientific_sha256'],
            'gates':g,'passed':[k for k in gated if g[k]['pass']],'failed':[k for k in gated if not g[k]['pass']],
            'all_gated_pass':all(g[k]['pass'] for k in gated),'GM_verdict':verdict,'GX3_verdict':g['GX3_budget_abstains']['observed']['verdict']}


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--study-dir',default=str(STUDY_DIR));ap.add_argument('--check',action='store_true')
    a=ap.parse_args();obj=build(Path(a.study_dir));out=Path(a.study_dir)/'GATES.json'
    if a.check:check(out.read_bytes()==dumps(obj),'GATES.json does not reproduce');print('GATES reproduces')
    else:write_new(out,obj);print({k:obj[k] for k in ('passed','failed','all_gated_pass','GM_verdict','GX3_verdict')})
