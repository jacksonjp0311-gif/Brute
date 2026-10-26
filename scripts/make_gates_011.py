"""Evaluate the pre-registered study-011 criteria (BRUTE_PLAN_011: GA1_011, G1, G2, G3L, G3' strict, G6b, GH, G4, G5,
G7, G9, G10, G12, G13, G11, GTI, G_RT gated; the non_gated_reports reported) from sealed artifacts only. Committed and
ledgered (scoring_freeze_011) before the held-out run_start; thresholds are copied from the plan, nothing is tuned.

Inputs in results/study-011 (D): 2x2/{SCIENTIFIC,SEAL,RESULTS}.json, repro/2x2; PAIRED_ANALYSIS_011.json,
REPRODUCIBILITY_011.json, SECOND_IMPLEMENTATION_011_2x2.json, TEST_SUITE_011.json, FEASIBILITY_011.json,
RUN_STATE_011.json, RUN_T0, RUN_DONE_011.json / STOP_011.json / STOP_011_ORCHESTRATOR.json, HEARTBEAT_011.jsonl,
KILL_DRILL_011.json (copy of the smoke kill-drill STOP record), SEAL.json; results/diag-011/LAG_DIAG_SEEN.json.

Scoring choices fixed here, before data (as make_gates_010 unless stated):
- "every action" = taken + counterfactual forecast of each step. A public certificate is also a conditional certificate.
- lag of a forecast at step s = s - d, d = max drift step (12, 23, 34) < s; NON-DRIFT as drift_definition
  (s > 12 and s not in {12, 23, 34}).
- G1: J9 and SP8 on each in_family_2x2 family: 0 false and 0 public false certificates, all steps, both actions.
- G2: J9 and SP8 on ood5: 0 false certificates, both actions.
- G3L: J9 on drift4: (a) 0 non-drift false certificates with lag >= 2, taken AND counterfactual; (b) taken-action false
  certificates <= 0.5 x sum of A4 v090_wrong (taken) on the same cases. SP8 lag >= 2 count reported; if it is 0 the
  observed record carries power='UNINFORMATIVE' (still scored).
- G3' strict: J9, taken action: non-drift false (any lag) == 0 AND total <= the same limit.
- G6b: PAIRED_ANALYSIS_011 G6b_dual_coverage_J9_minus_A2 pooled >= -0.03 AND CI lower >= -0.05.
- GA1_011: J9 passes G1(J9), G2(J9), G3L, G6b.
- GH: J9 on drift4, steps s in {14, 15, 16}: if trace[s-2].family_status_after == 'supported' and the step-s record's
  hull_unknown == 0, then hull_union[str(a)] must contain the realised code of a for both actions (taken:
  actual_emission_EVALUATOR_ONLY, other: counterfactual_actual_EVALUATOR_ONLY); missing hull_union = exception.
  Non-vacuity (some hull_union entry with < 4 codes) reported.
- G4: J9, SP8: (a) 0 public certificates on ood5 and drift4; (b) 0 wrong public anywhere; (c) none on a step >
  diagnostics.first_alarm_step.
- G5: a case counts if diagnostics.first_alarm_step is set; J9, SP8 on each in_family_2x2 family; fraction <= 0.05.
- G7: mean post-burn-in taken-action log-loss (6 d.p.) <= round(ln 4, 6) for J9, SP8 on ood5 and drift4; min
  probability >= 0.005 on every step of every case for J9, SP8.
- G9: J9, SP8 with tau6 and ref_reason, as make_gates_010.
- G10: 792 cases, block sealed complete, every trace 44 steps; J9, SP8 forecasts with solver_unknown > 0 <= 1%.
- G11: SECOND_IMPLEMENTATION_011_2x2: (i) mandatory_complete, mandatory_samples_present, 0 mandatory mismatching;
  (ii) 0 rest mismatching (audited rest); (iii) mutation passed, 20 injected, 20 detected, 0 flagged not injected,
  injected_j9_cert_or_hull_fields >= 4, injected_action >= 4; (iv) mandatory_done exists with wall_since_start <= 1500,
  the g11 stream was not stopped by the cap or an error, and results_sha256 equals the 2x2 SEAL results_sha256.
- G12: REPRODUCIBILITY_011.G12_pass and its main hash equals the seal. G13: check_freeze(), tau6, seals of current plan.
- GTI: TEST_SUITE_011 verdict.passed (in-cap run).
- G_RT (NEW semantics, plan 011): (i) 2x2, repro_2x2, gti have completed_at <= RUN_T0 + 7200 and are not stopped;
  g11_2x2 has mandatory_done at wall t <= RUN_T0 + 7200 with wall_since_start <= 1500 and was not stopped by the cap
  or an error; (ii) heartbeat first wall <= RUN_T0 + 60, last wall >= end - 10 s (end = RUN_T0 + RUN_DONE elapsed_s,
  else the deadline); (iii) KILL_DRILL_011 kill_latency_s <= 15 and no survivors. Optional phases (g11 rest, feas)
  reported in R_optional_phases. R_G_RT_strict = the v0.8.0 clause (i) reading on all streams incl. feas.
- STUDY_BUDGET: a gate whose inputs are incomplete is FAIL; reason 'STUDY_BUDGET' when a STOP file exists, else
  'INCOMPLETE_INPUT (...)'."""
from __future__ import annotations
import argparse,json,math,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common_011 import STUDY_DIR,PLAN,FREEZE,load,dumps,write_new,check,sha,plan_view,check_freeze
from experiments.v011_independent_reference import ref_reason

LN4=round(math.log(4),6)
NEW=('J9','SP8');DRIFT=(12,23,34);TAU6=1.645215321642;ALL=('J9','SP8','A4','A2')
EXPECTED=792;CAP=7200;G11_BUDGET=1500;GH_STEPS=(14,15,16)
MANDATORY=('2x2','gti','repro_2x2','g11_2x2');STREAMS=MANDATORY+('feas',)
BUDGETS={'2x2':1800,'gti':2400,'repro_2x2':900,'g11_2x2':1500,'feas':1200}
def fcs(r):return [r,r['counterfactual']]
def nondrift(s):return s>12 and s not in DRIFT
def lag(s):
    d=max([x for x in DRIFT if x<s],default=None);return None if d is None else s-d
def opt(p):return load(p) if Path(p).exists() else None


def heartbeat(d):
    p=d/'HEARTBEAT_011.jsonl'
    if not p.exists():return None
    R=[json.loads(l) for l in p.read_text().splitlines() if l.strip()]
    if not R:return None
    g=[r['gap_s'] for r in R if r.get('gap_s') is not None]
    return {'beats':len(R),'first_wall':R[0]['wall'],'last_wall':R[-1]['wall'],'max_gap_s':max(g) if g else None,
            'gaps_over_10s':[{'wall':r['wall'],'gap_s':r['gap_s']} for r in R if (r.get('gap_s') or 0)>10]}


def build(study=STUDY_DIR,smoke=False):
    study=Path(study);plan=load(PLAN);view=plan_view(plan);C=plan['criteria']
    blk=opt(study/'2x2'/'SCIENTIFIC.json');seal=opt(study/'2x2'/'SEAL.json');res=opt(study/'2x2'/'RESULTS.json')
    if blk is not None:check(seal['scientific_sha256']==sha(study/'2x2'/'SCIENTIFIC.json'),'2x2: SCIENTIFIC does not match SEAL')
    stop=opt(study/'STOP_011.json');stop_o=opt(study/'STOP_011_ORCHESTRATOR.json');done=opt(study/'RUN_DONE_011.json')
    state=opt(study/'RUN_STATE_011.json') or {'stopped':{},'spent':{},'completed_at':{}}
    t0=float((study/'RUN_T0').read_text().split()[0]) if (study/'RUN_T0').exists() else None
    paired=opt(study/'PAIRED_ANALYSIS_011.json');repro=opt(study/'REPRODUCIBILITY_011.json')
    aud=opt(study/'SECOND_IMPLEMENTATION_011_2x2.json');ts=opt(study/'TEST_SUITE_011.json');feas=opt(study/'FEASIBILITY_011.json')
    top=opt(study/'SEAL.json');drill=opt(study/'KILL_DRILL_011.json');lagseen=opt(ROOT/'results/diag-011/LAG_DIAG_SEEN.json')
    stopped=state.get('stopped',{});fired=stop is not None or stop_o is not None
    def incomplete(blocks=(),files=(),streams=()):
        why=[]
        if '2x2' in blocks:
            if blk is None:why.append('2x2 block missing')
            elif not seal.get('complete'):why.append(f'2x2 block incomplete ({seal.get("case_count")}/{seal.get("expected_case_count")})')
            if '2x2' in stopped:why.append(f'2x2 stream stopped: {stopped["2x2"]}')
        for name,obj in files:
            if obj is None:why.append(f'{name} missing')
        for s in streams:
            if s in stopped:why.append(f'{s} stream stopped: {stopped[s]}')
        return why
    def reason(why):return None if not why else ('STUDY_BUDGET' if fired else 'INCOMPLETE_INPUT')+' ('+'; '.join(why)+')'
    tau6=plan['tau6']['value'];eps=view['open_world_reserve_epsilon'];W=view['window_W']
    two=blk['cases'] if blk else [];IF,IFO,OOF=plan['in_family_2x2'],plan['in_family_original_2x2'],plan['out_of_family_2x2'];g={}
    def gate(name,ok,obs,gated=True,why=None):
        r=reason(why or [])
        if r:g[name]={'gated':True,'pass':False,'reason':r,'observed_on_available_inputs':obs};return
        g[name]={'gated':gated,'pass':(bool(ok) if ok is not None else None) if gated else None,'observed':obs}
    fam=lambda f:[c for c in two if c['family']==f]
    def tally(cs,arm):
        t={'cases':len(cs),'forecasts':0,'certs':0,'false_certs':0,'public_certs':0,'public_false_certs':0}
        for c in cs:
            for r in c['arms'][arm]['trace']:
                for q in fcs(r):
                    t['forecasts']+=1;t['certs']+=q['certificate'] is not None;t['false_certs']+=bool(q['wrong'])
                    t['public_certs']+=q['public_certificate'] is not None;t['public_false_certs']+=bool(q['public_wrong'])
        t['rule_of_three_upper_false_rate']=round(3/t['certs'],6) if t['certs'] else None;return t
    w2=incomplete(('2x2',))
    # G1
    g1={f:{a:tally(fam(f),a) for a in NEW} for f in IF if fam(f)}
    g1arm={a:all(g1[f][a]['false_certs']==0 and g1[f][a]['public_false_certs']==0 for f in g1) for a in NEW}
    gate('G1_in_family_soundness',bool(g1) and all(g1arm.values()),{'per_arm_pass':g1arm,'per_family':g1},why=w2)
    # G2
    g2={a:tally(fam('ood5'),a) for a in NEW};g2arm={a:g2[a]['false_certs']==0 for a in NEW}
    gate('G2_ood_soundness',all(g2arm.values()),{'per_arm_pass':g2arm,'ood5':g2,'prediction':C['G2_ood_soundness']['prediction']},why=w2)
    # G3L and G3' strict
    D=fam('drift4');v090=sum(bool(r['v090_wrong']) for c in D for r in c['arms']['A4']['trace']);limit=0.5*v090;g3={}
    for a in NEW:
        tr=[r for c in D for r in c['arms'][a]['trace']]
        both=[(side,r['step'],q) for r in tr for side,q in (('taken',r),('counterfactual',r['counterfactual'])) if q['wrong']]
        hist={}
        for side,s,q in both:
            if nondrift(s):hist[str(lag(s))]=hist.get(str(lag(s)),0)+1
        g3[a]={'false_certs_taken':sum(bool(r['wrong']) for r in tr),
               'false_certs_taken_non_drift':sum(bool(r['wrong']) and nondrift(r['step']) for r in tr),
               'false_certs_both_non_drift_lag_ge_2':sum(1 for side,s,q in both if nondrift(s) and lag(s)>=2),
               'false_certs_both_non_drift_lag_1':sum(1 for side,s,q in both if nondrift(s) and lag(s)==1),
               'false_certs_counterfactual':sum(bool(r['counterfactual']['wrong']) for r in tr),
               'non_drift_lag_histogram_both_actions':dict(sorted(hist.items(),key=lambda x:int(x[0])))}
        g3[a]['G3L_a_lag_ge_2_zero']=g3[a]['false_certs_both_non_drift_lag_ge_2']==0
        g3[a]['G3L_b_total_within_limit']=g3[a]['false_certs_taken']<=limit
        g3[a]['G3L_pass']=g3[a]['G3L_a_lag_ge_2_zero'] and g3[a]['G3L_b_total_within_limit']
        g3[a]['G3_strict_pass']=g3[a]['false_certs_taken_non_drift']==0 and g3[a]['G3L_b_total_within_limit']
    g3['SP8']['role']='reported (comparator / power check), not gated'
    power='UNINFORMATIVE' if D and g3['SP8']['false_certs_both_non_drift_lag_ge_2']==0 else 'informative'
    gate('G3L_drift4_lag_ge_2',g3['J9']['G3L_pass'],{'v090_control_false_certs':v090,'limit':limit,'drift_cases':len(D),**g3,
         'power':power,'power_note':'UNINFORMATIVE = SP8 also had 0 non-drift lag >= 2 false certificates (scored as is)',
         'definition':plan['drift_definition'],'prediction':C['G3L_drift4_lag_ge_2']['prediction']},why=w2)
    gate('G3_prime_strict_drift4',g3['J9']['G3_strict_pass'],{'v090_control_false_certs':v090,'limit':limit,
         'J9_false_certs_taken':g3['J9']['false_certs_taken'],'J9_false_certs_taken_non_drift':g3['J9']['false_certs_taken_non_drift'],
         'SP8_false_certs_taken_non_drift':g3['SP8']['false_certs_taken_non_drift'],'prediction':C['G3_prime_strict_drift4']['prediction']},why=w2)
    # G6b
    g6=None;pw=w2+incomplete(files=(('PAIRED_ANALYSIS_011.json',paired),))
    if paired:
        P=paired['G6b_dual_coverage_J9_minus_A2'];g6={'pooled_gain':P['pooled_gain'],'pooled_ci95':P['pooled_ci95'],
            'a_pooled_ge_-0.03':P['pooled_gain']>=-0.03,'b_ci_lower_ge_-0.05':P['pooled_ci95'][0]>=-0.05,'families':P['families']}
        g6['pass']=g6['a_pooled_ge_-0.03'] and g6['b_ci_lower_ge_-0.05']
    gate('G6b_coverage_vs_v020',bool(g6) and g6['pass'],{'J9_minus_A2':g6,
         'reported_J9_minus_SP8':paired and {k:paired['R_J9_minus_SP8_in_family_original'][k] for k in ('pooled_gain','pooled_ci95')},
         'reported_SP8_minus_A2':paired and {k:paired['R_SP8_minus_A2_in_family_original'][k] for k in ('pooled_gain','pooled_ci95')},
         'prediction':C['G6b_coverage_vs_v020']['prediction']},why=pw)
    # GA1_011
    ga={'G1':g1arm.get('J9',False),'G2':g2arm['J9'],'G3L':g3['J9']['G3L_pass'],'G6b':bool(g6) and g6['pass']}
    gate('GA1_011_window_drift_and_coverage',all(ga.values()),{'J9':ga,'G3L_power':power,
         'weakening_disclosed':C['GA1_011_window_drift_and_coverage']['weakening_disclosed'],
         'prediction':C['GA1_011_window_drift_and_coverage']['prediction']},why=pw)
    # GH
    exc=[];checked=0;nonvac=0;unknown_skipped=0;unsupported=0
    for c in D:
        tr=c['arms']['J9']['trace']
        for s in GH_STEPS:
            r=tr[s-1];check(r['step']==s,'trace order')
            if tr[s-2]['family_status_after']!='supported':unsupported+=1;continue
            if (r.get('hull_unknown') or 0)!=0:unknown_skipped+=1;continue
            checked+=1;H=r.get('hull_union');a=r['action']
            codes={a:r['actual_emission_EVALUATOR_ONLY'],1-a:r['counterfactual_actual_EVALUATOR_ONLY']}
            if H is None:exc.append({'seed':c['seed'],'mask_rate':c['mask_rate'],'step':s,'why':'missing hull_union'});continue
            nonvac+=any(len(v)<4 for v in H.values())
            for b in (0,1):
                if codes[b] not in H[str(b)]:exc.append({'seed':c['seed'],'mask_rate':c['mask_rate'],'step':s,'action':b,'realised':codes[b],'hull':H[str(b)]})
    gate('GH_window_hull_containment',not exc,{'steps':list(GH_STEPS),'checked':checked,'exceptions':len(exc),'exception_list':exc[:50],
         'skipped_family_not_supported':unsupported,'skipped_hull_unknown':unknown_skipped,'non_vacuous_checked_steps':nonvac,
         'prediction':C['GH_window_hull_containment']['prediction']},why=w2)
    # G4
    pub_oof={f:{a:tally(fam(f),a)['public_certs'] for a in NEW} for f in OOF}
    pub_wrong=sum(tally(two,a)['public_false_certs'] for a in NEW)
    after=sum(1 for c in two for a in NEW for r in c['arms'][a]['trace']
              if c['arms'][a]['diagnostics'].get('first_alarm_step') is not None and r['step']>c['arms'][a]['diagnostics']['first_alarm_step']
              for q in fcs(r) if q['public_certificate'] is not None)
    g4={'a_no_public_on_ood5_drift4':all(v==0 for f in pub_oof for v in pub_oof[f].values()),'b_no_wrong_public':pub_wrong==0,'c_no_public_after_first_alarm':after==0}
    gate('G4_public_safety',all(g4.values()),{'clauses':g4,'public_certs_out_of_family':pub_oof,'public_false_certs':pub_wrong,'public_after_first_alarm':after},why=w2)
    # G5
    g5={}
    for f in IF:
        cc=fam(f)
        if not cc:continue
        g5[f]={a:{'cases':len(cc),'cases_with_alarm':sum(c['arms'][a]['diagnostics'].get('first_alarm_step') is not None for c in cc)} for a in NEW}
        for v in g5[f].values():v['fraction']=round(v['cases_with_alarm']/v['cases'],6)
    gate('G5_false_alarm_limit',bool(g5) and all(v['fraction']<=0.05 for f in g5 for v in g5[f].values()),{'tau6':tau6,'per_family':g5,
         'prediction':C['G5_false_alarm_limit']['prediction']},why=w2)
    # G7
    def mean_ll(cs,a):
        v=[r['logloss'] for c in cs for r in c['arms'][a]['trace'][c['burn_in']:]];return round(sum(v)/len(v),6) if v else None
    ll={f:{a:mean_ll(fam(f),a) for a in NEW} for f in ('ood5','drift4')}
    thr=round(eps/4,12);minp={};minp_bad=[]
    for c in two:
        for a in ('J9','SP8','A4'):
            if a not in c['arms'] or not c['arms'][a]['trace'] or 'min_probability' not in c['arms'][a]['trace'][0]:continue
            mp=min(r['min_probability'] for r in c['arms'][a]['trace']);k=f"{c['family']}/{a}";minp[k]=min(minp.get(k,1),mp)
            if mp<thr-1e-12 and a in NEW:minp_bad.append({'family':c['family'],'seed':c['seed'],'mask_rate':c['mask_rate'],'arm':a,'min':mp,'threshold':thr})
    g7={'logloss_le_ln4':all(ll[f][a] is not None and ll[f][a]<=LN4 for f in ll for a in ll[f]),'min_probability':not minp_bad}
    gate('G7_open_world',all(g7.values()),{'clauses':g7,'logloss_post':ll,'ln4':LN4,'eps':eps,'min_probability_threshold':thr,
         'min_probability_by_family_arm':minp,'violations':minp_bad[:20]},why=w2)
    # G9
    resumes=0;resume_bad=[];resync=0;reasons_ok=True;totals={};dups=0;bad_reason=[]
    for c in two:
        for a in NEW:
            A=c['arms'][a];tr=A['trace']
            dups+=len(A['issued'])-len({tuple(x) for x in A['issued']})+len(A['retractions'])-len({(e['step'],e['certificate']) for e in A['retractions']})
            resync+=sum(1 for r in tr for q in fcs(r) if q['certificate'] is not None and q['reason']=='RESYNC_AMBIGUOUS')
            resync+=sum(1 for s_,_ in A['issued'] if tr[s_-1]['reason']=='RESYNC_AMBIGUOUS')
            for e in A['retractions']:
                if e['reason']!=ref_reason(e['certificate'],e['observed']):reasons_ok=False;bad_reason.append({'family':c['family'],'seed':c['seed'],'arm':a,'step':e['step']})
                totals[e['reason']]=totals.get(e['reason'],0)+1
            for s_ in A['diagnostics'].get('resume_steps',[]):
                resumes+=1;win=tr[max(0,s_-W):s_]
                ok=len(win)==W and all(r['residual_after'] is not None and r['residual_after']<=tau6 for r in win) \
                   and tr[s_-1]['family_status_after']=='supported' and tr[s_-1]['margin_status_after']=='supported'
                if not ok:resume_bad.append({'family':c['family'],'seed':c['seed'],'mask_rate':c['mask_rate'],'arm':a,'resume_step':s_})
    gate('G9_retraction_resume',not resume_bad and resync==0 and reasons_ok and dups==0,
         {'resumes_checked':resumes,'resume_rule_violations':resume_bad[:50],'resync_ambiguous_certified_or_issued':resync,
          'retraction_reasons_match_reference':reasons_ok,'retraction_reason_mismatches':bad_reason[:50],'retraction_reasons_total':totals,'duplicate_pairs':dups},why=w2)
    # G10
    steps=plan['actions_per_case_2x2']
    short=[f"{c['family']}/{c['seed']}/{c['mask_rate']}/{a}" for c in two for a in c['arms'] if len(c['arms'][a]['trace'])!=steps]
    tot=u=0
    for c in two:
        for a in NEW:
            for r in c['arms'][a]['trace']:
                for q in fcs(r):tot+=1;u+=(q.get('solver_unknown') or 0)>0
    unk={'arms':list(NEW),'forecasts':tot,'with_unknown':u,'fraction':round(u/tot,6) if tot else None}
    wall={}
    for c in (res or {}).get('cases',[]):
        for a,A in c['arms'].items():wall[a]=round(wall.get(a,0)+A.get('elapsed_informational',0),2)
    counts_ok=(smoke or len(two)==EXPECTED) and bool(seal) and bool(seal.get('complete'))
    gate('G10_compute',counts_ok and not short and unk['fraction'] is not None and unk['fraction']<=0.01,
         {'cases_expected':None if smoke else EXPECTED,'cases_present':len(two),'sealed_complete':bool(seal) and seal.get('complete'),'short_traces':short[:20],
          'production_unknown_forecasts':unk,'wall_clock_informational_seconds':wall,'timing_note':'informational, shared 8-CPU box; not a gate input'},why=w2)
    # G11
    g11=None;g11_why=[];sn='g11_2x2';st=str(stopped.get(sn,''))
    if aud is None:g11_why.append('SECOND_IMPLEMENTATION_011_2x2.json missing')
    if st.startswith(('STUDY_BUDGET','exit code','input stream')):g11_why.append(f'{sn} stream stopped: {st}')
    md=(aud or {}).get('events',{}).get('mandatory_done')
    if aud:
        mt=aud.get('mutation_test') or {}
        g11={'i_mandatory_complete_zero_mismatch':bool(aud.get('mandatory_complete')) and bool(aud.get('mandatory_samples_present')) and aud['mandatory']['mismatching_traces']==0,
             'ii_rest_zero_mismatch':aud.get('rest',{}).get('mismatching_traces',0)==0,
             'iii_mutation_20_of_20':bool(mt.get('passed')) and mt.get('injected')==20 and mt.get('detected_injected')==20 and mt.get('flagged_not_injected')==0
                and (mt.get('injected_j9_cert_or_hull_fields') or 0)>=4 and (mt.get('injected_action') or 0)>=4,
             'iv_mandatory_inside_budget':md is not None and md['wall_since_start']<=G11_BUDGET,
             'iv_of_sealed_results':seal is not None and aud.get('results_sha256')==seal['results_sha256']}
    gate('G11_second_implementation',bool(g11) and all(g11.values()),{'clauses':g11,
         'report':None if aud is None else {k:aud[k] for k in aud if k not in ('mismatches',)},
         'wording':'second implementation by the same author'},why=g11_why+w2)
    # G12
    g12ok=bool(repro) and repro['G12_pass'] and seal is not None and repro['blocks']['2x2']['main_scientific_sha256']==seal['scientific_sha256']
    gate('G12_reproducibility',g12ok,None if repro is None else repro['blocks'],
         why=w2+incomplete(files=(('REPRODUCIBILITY_011.json',repro),),streams=('repro_2x2',)))
    # G13
    try:check_freeze();fz=True;fz_err=None
    except Exception as exc_:fz=False;fz_err=f'{type(exc_).__name__}: {exc_}'
    g13={'freeze_chain_holds':fz,'plan_tau_value':tau6==TAU6,'cases_use_plan_tau':bool(two) and all(c.get('tau6')==tau6 for c in two),
         'seal_of_current_plan_and_freeze':bool(seal) and seal['plan_sha256']==sha(PLAN) and FREEZE.exists() and seal.get('freeze_sha256')==sha(FREEZE)}
    g13ok=all(g13.values()) if not smoke else (g13['plan_tau_value'] and g13['cases_use_plan_tau'])
    gate('G13_frozen_controls_reproduce',g13ok,{'clauses':g13,'freeze_error':fz_err,'recorded_taus':sorted({c.get('tau6') for c in two}),
         'smoke_dry_run_relaxed':smoke},why=w2 if seal is None else None)
    # GTI
    V=(ts or {}).get('verdict')
    gate('GTI_test_isolation',bool(V) and V['passed'],None if ts is None else {'verdict':V,'head':ts.get('head'),'tracked_tree_dirty':ts.get('tracked_tree_dirty'),
         'clean_tag_runs':ts.get('clean_tag_runs'),'run':'in-cap'},why=incomplete(files=(('TEST_SUITE_011.json',ts),),streams=('gti',)))
    # G_RT (plan 011 semantics)
    hb=heartbeat(study);comp=state.get('completed_at',{})
    end=(t0+done['elapsed_s']) if (t0 is not None and done) else (t0+CAP if t0 is not None else None)
    late={s:(round(comp[s]-t0,1) if s in comp and t0 is not None else None) for s in STREAMS}
    ev=(md if md is not None else (state.get('events',{}).get('g11_2x2',{}) or {}).get('mandatory_done'))
    md_at=None if ev is None or t0 is None or ev.get('t') is None else round(ev['t']-t0,1)
    i_streams={s:late[s] is not None and late[s]<=CAP and s not in stopped for s in ('2x2','repro_2x2','gti')}
    i_g11=md_at is not None and md_at<=CAP and ev['wall_since_start']<=G11_BUDGET and not st.startswith(('STUDY_BUDGET','exit code','input stream')) and aud is not None
    rt={'i_mandatory_inside_cap':t0 is not None and all(i_streams.values()) and i_g11,
        'ii_watchdog_whole_run':bool(hb) and t0 is not None and hb['first_wall']<=t0+60 and hb['last_wall']>=end-10,
        'iii_kill_drill_latency_le_15s':bool(drill) and drill.get('kill_latency_s') is not None and drill['kill_latency_s']<=15 and not drill.get('survivors')}
    g['G_RT_study_runtime']={'gated':True,'pass':all(rt.values()),'observed':{'clauses':rt,'mandatory_streams':i_streams,'g11_mandatory_ok':i_g11,
         'g11_mandatory_done_s_after_t0':md_at,'g11_mandatory_wall_since_start':None if ev is None else ev.get('wall_since_start'),
         'completion_s_after_t0':late,'stopped_streams':stopped,'stop_watchdog':stop,'stop_orchestrator':stop_o,'run_done':done,'heartbeat':hb,
         'kill_drill':drill,'spent_s':{k:round(v) for k,v in state.get('spent',{}).items()},'cap_s':CAP,
         'semantics':'plan 011 (mandatory vs optional; not retroactive)'},
         **({} if all(rt.values()) else {'reason':'STUDY_BUDGET' if fired else 'clauses failed: '+', '.join(k for k,v in rt.items() if not v)})}
    # ---- non-gated reports
    rj={}
    if paired:rj={k:{x:paired[k][x] for x in ('pooled_gain','pooled_ci95','families')} for k in ('R_J9_minus_SP8_in_family_original','R_J9_minus_SP8_in_family')}
    gate('R_J9_minus_SP8',None,rj,gated=False)
    det=[]
    for c in D:
        for a in ('J9','SP8','A4'):
            evs=set(c['arms'][a]['diagnostics'].get('drift_events') or [])
            for r in c['arms'][a]['trace']:
                for side,q in (('taken',r),('counterfactual',r.get('counterfactual'))):
                    wrong=q.get('v090_wrong') if a=='A4' and side=='taken' else q.get('wrong')
                    if q and wrong:
                        d=max([x for x in DRIFT if x<r['step']],default=None)
                        det.append({'arm':a,'seed':c['seed'],'mask_rate':c['mask_rate'],'step':r['step'],'action':side,'public':bool(q.get('public_wrong')),
                                    'lag':lag(r['step']),'non_drift':nondrift(r['step']),'rule':q.get('cert_rule'),
                                    'event_between':None if d is None or a=='A4' else any(d<=u<r['step'] for u in evs)})
    hist={a:{} for a in ('J9','SP8','A4')}
    for x in det:
        if x['non_drift']:hist[x['arm']][str(x['lag'])]=hist[x['arm']].get(str(x['lag']),0)+1
    gate('R_lag_detail',None,{'false_certificates':det,'non_drift_lag_histogram':hist,'count_by_arm':{a:sum(x['arm']==a for x in det) for a in hist},
         'note':'A4 rows use v090_wrong for the taken action (the G3 control)'},gated=False)
    jh={}
    for c in two:
        x=jh.setdefault(c['family'],{'cases':0,'post_forecasts':0,'post_certs':0,'hull_steps':0,'hull_all_codes':0,'hull_downgrades':0,'hull_queries':0})
        A=c['arms']['J9'];x['cases']+=1;x['hull_downgrades']+=A['diagnostics'].get('hull_downgrades') or 0;x['hull_queries']+=A['diagnostics'].get('hull_queries') or 0
        for r in A['trace'][c['burn_in']:]:x['post_forecasts']+=2;x['post_certs']+=(r['certificate'] is not None)+(r['counterfactual']['certificate'] is not None)
        for r in A['trace']:
            H=r.get('hull_union')
            if H is not None:x['hull_steps']+=1;x['hull_all_codes']+=all(len(v)>=4 for v in H.values())
    for x in jh.values():
        x['coverage']=round(x['post_certs']/x['post_forecasts'],6) if x['post_forecasts'] else None
        x['fraction_hull_all_codes']=round(x['hull_all_codes']/x['hull_steps'],6) if x['hull_steps'] else None
    gate('R_J9_hull',None,jh,gated=False)
    strict={s:late[s] is not None and late[s]<=CAP and s not in stopped for s in STREAMS}
    gate('R_G_RT_strict',None,{'every_stream_complete_inside_cap_none_stopped':all(strict.values()),'per_stream':strict,
         'note':'the v0.8.0 clause (i) reading, reported only'},gated=False)
    gate('R_optional_phases',None,{'g11_rest':None if aud is None else {k:aud['rest'][k] for k in ('traces_expected','traces_audited','traces_not_reached','mismatching_traces')},
         'g11_stream':{'stopped':stopped.get('g11_2x2'),'completed_s_after_t0':late.get('g11_2x2'),'spent_s':round(state.get('spent',{}).get('g11_2x2',0),1)},
         'feas_stream':{'stopped':stopped.get('feas'),'completed_s_after_t0':late.get('feas'),'spent_s':round(state.get('spent',{}).get('feas',0),1)}},gated=False)
    gate('R_feasibility_7_8',None,None if feas is None else {k:v for k,v in feas.items() if k!='records'},gated=False)
    gate('R_heartbeat',None,hb,gated=False)
    gate('R_rates',None,{s:{'spent_s':round(state.get('spent',{}).get(s,0),1),'budget_s':BUDGETS[s],
         'fraction_of_budget':round(state.get('spent',{}).get(s,0)/BUDGETS[s],3)} for s in STREAMS},gated=False)
    gate('R_tests_plain',None,None if ts is None else ts.get('plain_discover'),gated=False)
    gate('R_lag_diag_seen',None,None if lagseen is None else {'label':lagseen.get('label'),'summary':lagseen.get('summary'),
         'summary_taken_only':lagseen.get('summary_taken_only')},gated=False)
    gated=[k for k,v in g.items() if v['gated']]
    return {'schema':'brute.gates.v9_0','study':plan['study'],'plan_sha256':sha(PLAN),'smoke_dry_run':smoke,
            'scientific_sha256':None if seal is None else seal['scientific_sha256'],'study_seal_present':top is not None,
            'stop_rule_fired':fired,'gates':g,
            'passed':[k for k in gated if g[k]['pass']],'failed':[k for k in gated if g[k]['pass'] is False],
            'pending':[k for k in gated if g[k]['pass'] is None],'all_gated_pass':all(g[k]['pass'] for k in gated),
            'GA1_011':g['GA1_011_window_drift_and_coverage']['pass'],'G3L_power':power,'GTI_in_cap':g['GTI_test_isolation']['pass'],
            'G_RT':g['G_RT_study_runtime']['pass']}


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--study-dir',default=str(STUDY_DIR));ap.add_argument('--check',action='store_true')
    ap.add_argument('--output',default='GATES_011.json');ap.add_argument('--smoke',action='store_true',help='dry run on a smoke directory; prints only')
    a=ap.parse_args()
    if a.smoke:
        obj=build(Path(a.study_dir),smoke=True)
        print({k:obj[k] for k in ('passed','failed','pending')});print({k:v.get('reason') for k,v in obj['gates'].items() if v.get('reason')});raise SystemExit
    obj=build(Path(a.study_dir));out=Path(a.study_dir)/a.output
    if a.check:check(out.read_bytes()==dumps(obj),out.name+' does not reproduce');print(out.name,'reproduces')
    else:write_new(out,obj);print({k:obj[k] for k in ('passed','failed','pending','all_gated_pass')})
