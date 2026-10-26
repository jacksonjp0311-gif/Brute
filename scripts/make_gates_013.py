"""Evaluate the pre-registered study-013 criteria (BRUTE_PLAN_013: headline GST_sound_transfer, GS_a..GS_e, GS_ref,
GAPI, G1, G2, G3L, G3' strict, GH, G4, G5, G7, G9, G6b (SP8 vs A2 only), G10, G11, G12, G13, GTI, G_RT, G78_soundness,
G78_containment gated; the non_gated_reports reported) from sealed artifacts only. Committed and ledgered
(scoring_freeze_013) before the held-out run_start; thresholds are copied from the plan, nothing is tuned.
Adapted from make_gates_012 (frozen, not edited); unchanged gates keep the make_gates_012 scoring choices verbatim.

Inputs in results/study-013 (D): {2x2,big78,transfer}/{SCIENTIFIC,SEAL,RESULTS}.json, repro/{2x2,transfer};
PAIRED_ANALYSIS_013.json, REPRODUCIBILITY_013.json, SECOND_IMPLEMENTATION_013_2x2.json, TEST_SUITE_013.json,
RUN_STATE_013.json, RUN_T0, RUN_DONE_013.json / STOP_013.json / STOP_013_ORCHESTRATOR.json, HEARTBEAT_013.jsonl,
KILL_DRILL_013.json, SEAL.json; results/diag-013/APPLICABILITY_DIAG_SEEN.json; experiments/BRUTE_SOURCE_FREEZE_013.json.

Scoring choices fixed here, before data (new or changed versus make_gates_012):
- G6b: PAIRED_ANALYSIS_013 G6b_dual_coverage_SP8_minus_A2 pooled >= -0.03 AND CI lower >= -0.05 (window hulls off G6b);
  J10 - A2 and J9 - A2 reported (R_window_G6b). GA1_012 and GJ10 retired (R_J10_minus_J9 reported).
- G78_soundness: SP8_78 only: 0 false and 0 public false certificates, all steps, both actions, AND >= 150 conditional
  certificates (taken + counterfactual, all steps). G78_containment as make_gates_012 on SP8_78.
- G10: 2x2 792, big78 288, transfer 288 cases; every trace incl. every transfer arm (TR/DR/AT/AT4/LX) 44 steps.
- G11 (iv) / G_RT: the g11 stream budget is 1800 s (plan stream_budgets).
- GS_a: false certificates recomputed: for post-hoc arms (TR, DR, AT, AT4) from the arm trace certificate[b] against the
  SP8 *_EVALUATOR_ONLY actual of action b at the same step; for LX from its own trace certificate[b] vs
  actual_EVALUATOR_ONLY[b]. Must equal the recorded false_certificates. Pass iff DRp, DRn, ATp, ATn, LXp, LXn all 0.
- GS_b: every non-null DR certificate equals the SP8 conditional certificate at (case, step, action) (taken ->
  certificate, other -> counterfactual.certificate); per case and arm DR certificate count <= SP8 count; S(DR) <= 0 on
  every case (S = tcert(SP8 trace) - DR first_cert_step).
- GS_c: per arm in DRn, ATn, LXn: (i) 0 false (as GS_a) AND (ii) PAIRED_ANALYSIS_013 S_<arm> ci95[0] <= 0.
- GS_d / GS_e: PAIRED_ANALYSIS_013 S_ATp / S_LXp mean_S >= 1.0 AND ci95[0] > 0.
- GS_ref: SECOND_IMPLEMENTATION_013_2x2.transfer_audit as GT_ref in make_gates_012.
- GST: PASS iff for X in (AT, LX): GS_a per-arm pass for X_p and X_n, GS_c per-arm pass for X_n, and GS_d (AT) / GS_e (LX).
- GAPI: TEST_SUITE_013 per_module['test_api_certify_0110.py'] returncode 0, >= 1 result, every result 'ok';
  brute/api/certify.py present in BRUTE_SOURCE_FREEZE_013 sha256_files.
- G13 adds: plan tau7 equals BRUTE_PLAN_012 tau7.
- STUDY_BUDGET: a gate whose inputs are incomplete is FAIL; reason 'STUDY_BUDGET' when a STOP file exists, else
  'INCOMPLETE_INPUT (...)'."""
from __future__ import annotations
import argparse,json,math,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common_013 import STUDY_DIR,PLAN,FREEZE,load,dumps,write_new,check,sha,plan_view,check_freeze
from experiments.v011_independent_reference import ref_reason
from scripts.make_paired_009 import tcert

LN4=round(math.log(4),6)
NEW=('J10','J9','SP8');GA='J10';DRIFT=(12,23,34);TAU6=1.645215321642;ALL=('J10','J9','SP8','A4','A2')
BIG_ARMS=('SP8_78',);TR_ARMS=('TRp','TRn','DRp','DRn','ATp','ATn','AT4p','AT4n','LXp','LXn');POSTHOC=('TRp','TRn','DRp','DRn','ATp','ATn','AT4p','AT4n')
GS_A_ARMS=('DRp','DRn','ATp','ATn','LXp','LXn');GS_C_ARMS=('DRn','ATn','LXn');G78_MIN_CERTS=150
EXPECTED={'2x2':792,'big78':288,'transfer':288};CAP=7200;G11_BUDGET=1800;GH_STEPS=(14,15,16)
MANDATORY=('2x2','big78','transfer','repro','gti');STREAMS=MANDATORY+('g11',)
BUDGETS={'2x2':2400,'big78':2700,'transfer':1800,'gti':2700,'repro':1500,'g11':1800}
BAD_STOP=('STUDY_BUDGET','exit code','input stream')
def fcs(r):return [r,r['counterfactual']]
def nondrift(s):return s>12 and s not in DRIFT
def lag(s):
    d=max([x for x in DRIFT if x<s],default=None);return None if d is None else s-d
def opt(p):return load(p) if Path(p).exists() else None


def heartbeat(d):
    p=d/'HEARTBEAT_013.jsonl'
    if not p.exists():return None
    R=[json.loads(l) for l in p.read_text().splitlines() if l.strip()]
    if not R:return None
    g=[r['gap_s'] for r in R if r.get('gap_s') is not None]
    return {'beats':len(R),'first_wall':R[0]['wall'],'last_wall':R[-1]['wall'],'max_gap_s':max(g) if g else None,
            'gaps_over_10s':[{'wall':r['wall'],'gap_s':r['gap_s']} for r in R if (r.get('gap_s') or 0)>10]}


def build(study=STUDY_DIR,smoke=False):
    study=Path(study);plan=load(PLAN);view=plan_view(plan);C=plan['criteria']
    BLK={};SEALS={}
    for b in EXPECTED:
        BLK[b]=opt(study/b/'SCIENTIFIC.json');SEALS[b]=opt(study/b/'SEAL.json')
        if BLK[b] is not None:check(SEALS[b]['scientific_sha256']==sha(study/b/'SCIENTIFIC.json'),f'{b}: SCIENTIFIC does not match SEAL')
    blk=BLK['2x2'];seal=SEALS['2x2'];res=opt(study/'2x2'/'RESULTS.json')
    stop=opt(study/'STOP_013.json');stop_o=opt(study/'STOP_013_ORCHESTRATOR.json');done=opt(study/'RUN_DONE_013.json')
    state=opt(study/'RUN_STATE_013.json') or {'stopped':{},'spent':{},'completed_at':{}}
    t0=float((study/'RUN_T0').read_text().split()[0]) if (study/'RUN_T0').exists() else None
    paired=opt(study/'PAIRED_ANALYSIS_013.json');repro=opt(study/'REPRODUCIBILITY_013.json')
    aud=opt(study/'SECOND_IMPLEMENTATION_013_2x2.json');ts=opt(study/'TEST_SUITE_013.json')
    top=opt(study/'SEAL.json');drill=opt(study/'KILL_DRILL_013.json')
    apseen=opt(ROOT/'results/diag-013/APPLICABILITY_DIAG_SEEN.json')
    stopped=state.get('stopped',{});fired=stop is not None or stop_o is not None
    def incomplete(blocks=(),files=(),streams=()):
        why=[]
        for b in blocks:
            if BLK[b] is None:why.append(f'{b} block missing')
            elif not SEALS[b].get('complete'):why.append(f'{b} block incomplete ({SEALS[b].get("case_count")}/{SEALS[b].get("expected_case_count")})')
            if b in stopped:why.append(f'{b} stream stopped: {stopped[b]}')
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
            if arm not in c['arms']:continue
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
    g3['SP8']['role']='reported (comparator / power check), not gated';g3['J9']['role']='reported (frozen v0.9.0 arm), not gated'
    power='UNINFORMATIVE' if D and g3['SP8']['false_certs_both_non_drift_lag_ge_2']==0 else 'informative'
    gate('G3L_drift4_lag_ge_2',g3[GA]['G3L_pass'],{'v090_control_false_certs':v090,'limit':limit,'drift_cases':len(D),**g3,
         'power':power,'power_note':'UNINFORMATIVE = SP8 also had 0 non-drift lag >= 2 false certificates (scored as is)',
         'definition':plan['drift_definition'],'prediction':C['G3L_drift4_lag_ge_2']['prediction']},why=w2)
    gate('G3_prime_strict_drift4',g3[GA]['G3_strict_pass'],{'v090_control_false_certs':v090,'limit':limit,
         'J10_false_certs_taken':g3[GA]['false_certs_taken'],'J10_false_certs_taken_non_drift':g3[GA]['false_certs_taken_non_drift'],
         'J9_false_certs_taken_non_drift':g3['J9']['false_certs_taken_non_drift'],
         'SP8_false_certs_taken_non_drift':g3['SP8']['false_certs_taken_non_drift'],'prediction':C['G3_prime_strict_drift4']['prediction']},why=w2)
    # G6b (SP8 only; window hulls off G6b)
    g6=None;pw=w2+incomplete(files=(('PAIRED_ANALYSIS_013.json',paired),))
    if paired:
        P=paired['G6b_dual_coverage_SP8_minus_A2'];g6={'pooled_gain':P['pooled_gain'],'pooled_ci95':P['pooled_ci95'],
            'a_pooled_ge_-0.03':P['pooled_gain']>=-0.03,'b_ci_lower_ge_-0.05':P['pooled_ci95'][0]>=-0.05,'families':P['families']}
        g6['pass']=g6['a_pooled_ge_-0.03'] and g6['b_ci_lower_ge_-0.05']
    gate('G6b_coverage_vs_v020',bool(g6) and g6['pass'],{'SP8_minus_A2':g6,'prediction':C['G6b_coverage_vs_v020']['prediction']},why=pw)
    rw={}
    if paired:rw={k:{x:paired[k][x] for x in ('pooled_gain','pooled_ci95','families')} for k in ('R_window_G6b_J10_minus_A2','R_window_G6b_J9_minus_A2')}
    gate('R_window_G6b',None,rw,gated=False)
    gate('R_J10_minus_J9',None,None if not paired else {x:paired['R_J10_minus_J9_in_family_original'][x] for x in ('pooled_gain','pooled_ci95','families')},gated=False)
    # GH
    exc=[];checked=0;nonvac=0;unknown_skipped=0;unsupported=0
    for c in D:
        tr=c['arms'][GA]['trace']
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
    gate('GH_support_containment',not exc,{'steps':list(GH_STEPS),'checked':checked,'exceptions':len(exc),'exception_list':exc[:50],
         'skipped_family_not_supported':unsupported,'skipped_hull_unknown':unknown_skipped,'non_vacuous_checked_steps':nonvac,
         'prediction':C['GH_support_containment']['prediction']},why=w2)
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
        for a in ('J10','J9','SP8','A4'):
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
    steps=plan['actions_per_case_2x2'];short=[]
    for b,d_ in BLK.items():
        for c in (d_ or {}).get('cases',[]):
            short+=[f"{b}/{c['family']}/{c['seed']}/{c['mask_rate']}/{a}" for a in c['arms'] if len(c['arms'][a]['trace'])!=steps]
            short+=[f"{b}/{c['family']}/{c['seed']}/{c['mask_rate']}/{a}" for a in (c.get('transfer') or {}) if len(c['transfer'][a]['trace'])!=steps]
    tot=u=0
    for c in two:
        for a in NEW:
            for r in c['arms'][a]['trace']:
                for q in fcs(r):tot+=1;u+=(q.get('solver_unknown') or 0)>0
    unk={'arms':list(NEW),'forecasts':tot,'with_unknown':u,'fraction':round(u/tot,6) if tot else None}
    wall={}
    for c in (res or {}).get('cases',[]):
        for a,A in c['arms'].items():wall[a]=round(wall.get(a,0)+A.get('elapsed_informational',0),2)
    present={b:len((BLK[b] or {}).get('cases',[])) for b in EXPECTED}
    counts_ok=all((smoke or present[b]==EXPECTED[b]) and bool(SEALS[b]) and bool(SEALS[b].get('complete')) for b in EXPECTED)
    gate('G10_compute',counts_ok and not short and unk['fraction'] is not None and unk['fraction']<=0.01,
         {'cases_expected':None if smoke else EXPECTED,'cases_present':present,'sealed_complete':{b:bool(SEALS[b]) and SEALS[b].get('complete') for b in EXPECTED},'short_traces':short[:20],
          'production_unknown_forecasts':unk,'wall_clock_informational_seconds':wall,'timing_note':'informational, shared 8-CPU box; not a gate input'},why=incomplete(tuple(EXPECTED)))
    # G11
    g11=None;g11_why=[];sn='g11';st=str(stopped.get(sn,''))
    if aud is None:g11_why.append('SECOND_IMPLEMENTATION_013_2x2.json missing')
    if st.startswith(BAD_STOP):g11_why.append(f'{sn} stream stopped: {st}')
    md=(aud or {}).get('events',{}).get('mandatory_done')
    if aud:
        mt=aud.get('mutation_test') or {}
        g11={'i_mandatory_complete_zero_mismatch':bool(aud.get('mandatory_complete')) and bool(aud.get('mandatory_samples_present')) and aud['mandatory']['mismatching_traces']==0,
             'ii_optional_zero_mismatch':aud.get('rest',{}).get('mismatching_traces',0)==0,
             'iii_mutation_20_of_20':bool(mt.get('passed')) and mt.get('injected')==20 and mt.get('detected_injected')==20 and mt.get('flagged_not_injected')==0
                and (mt.get('injected_j10_cert_or_hull_fields') or 0)>=4 and (mt.get('injected_action') or 0)>=4,
             'iv_mandatory_inside_budget':md is not None and md['wall_since_start']<=G11_BUDGET,
             'iv_of_sealed_results':seal is not None and aud.get('results_sha256')==seal['results_sha256']}
    gate('G11_second_implementation',bool(g11) and all(g11.values()),{'clauses':g11,
         'report':None if aud is None else {k:aud[k] for k in aud if k not in ('mismatches',)},
         'wording':'second implementation by the same author'},why=g11_why+w2)
    # G12
    g12ok=bool(repro) and repro['G12_pass'] and all(SEALS[b] is not None and repro['blocks'][b]['main_scientific_sha256']==SEALS[b]['scientific_sha256'] for b in ('2x2','transfer'))
    gate('G12_reproducibility',g12ok,None if repro is None else repro['blocks'],
         why=incomplete(('2x2','transfer'),files=(('REPRODUCIBILITY_013.json',repro),),streams=('repro',)))
    # G13
    try:check_freeze();fz=True;fz_err=None
    except Exception as exc_:fz=False;fz_err=f'{type(exc_).__name__}: {exc_}'
    allc=[c for b in EXPECTED for c in (BLK[b] or {}).get('cases',[])]
    g13={'freeze_chain_holds':fz,'plan_tau_value':tau6==TAU6,'plan_tau7_equals_plan012':(plan.get('tau7') or {}).get('value')==(load(ROOT/'experiments/BRUTE_PLAN_012.json').get('tau7') or {}).get('value'),'cases_use_plan_tau':bool(allc) and all(c.get('tau6')==tau6 for c in allc),
         'seal_of_current_plan_and_freeze':all(bool(SEALS[b]) and SEALS[b]['plan_sha256']==sha(PLAN) and FREEZE.exists() and SEALS[b].get('freeze_sha256')==sha(FREEZE) for b in EXPECTED)}
    g13ok=all(g13.values()) if not smoke else (g13['plan_tau_value'] and g13['cases_use_plan_tau'] and g13['plan_tau7_equals_plan012'])
    gate('G13_frozen_controls_reproduce',g13ok,{'clauses':g13,'freeze_error':fz_err,'recorded_taus':sorted({c.get('tau6') for c in allc}),
         'smoke_dry_run_relaxed':smoke},why=w2 if seal is None else None)
    # GTI
    V=(ts or {}).get('verdict')
    gate('GTI_test_isolation',bool(V) and V['passed'],None if ts is None else {'verdict':V,'head':ts.get('head'),'tracked_tree_dirty':ts.get('tracked_tree_dirty'),
         'clean_tag_runs':ts.get('clean_tag_runs'),'run':'in-cap'},why=incomplete(files=(('TEST_SUITE_013.json',ts),),streams=('gti',)))
    # G_RT (plan 013 = plan 012 semantics)
    hb=heartbeat(study);comp=state.get('completed_at',{})
    end=(t0+done['elapsed_s']) if (t0 is not None and done) else (t0+CAP if t0 is not None else None)
    late={s:(round(comp[s]-t0,1) if s in comp and t0 is not None else None) for s in STREAMS}
    ev=(md if md is not None else (state.get('events',{}).get('g11',{}) or {}).get('mandatory_done'))
    md_at=None if ev is None or t0 is None or ev.get('t') is None else round(ev['t']-t0,1)
    i_streams={s:late[s] is not None and late[s]<=CAP and s not in stopped for s in MANDATORY}
    i_g11=md_at is not None and md_at<=CAP and ev['wall_since_start']<=G11_BUDGET and not st.startswith(BAD_STOP) and aud is not None
    rt={'i_mandatory_inside_cap':t0 is not None and all(i_streams.values()) and i_g11,
        'ii_watchdog_whole_run':bool(hb) and t0 is not None and hb['first_wall']<=t0+60 and hb['last_wall']>=end-10,
        'iii_kill_drill_latency_le_15s':bool(drill) and drill.get('kill_latency_s') is not None and drill['kill_latency_s']<=15 and not drill.get('survivors')}
    g['G_RT_study_runtime']={'gated':True,'pass':all(rt.values()),'observed':{'clauses':rt,'mandatory_streams':i_streams,'g11_mandatory_ok':i_g11,
         'g11_mandatory_done_s_after_t0':md_at,'g11_mandatory_wall_since_start':None if ev is None else ev.get('wall_since_start'),
         'completion_s_after_t0':late,'stopped_streams':stopped,'stop_watchdog':stop,'stop_orchestrator':stop_o,'run_done':done,'heartbeat':hb,
         'kill_drill':drill,'spent_s':{k:round(v) for k,v in state.get('spent',{}).items()},'cap_s':CAP,
         'semantics':'plan 013 = plan 012 (mandatory vs optional g11 phase)'},
         **({} if all(rt.values()) else {'reason':'STUDY_BUDGET' if fired else 'clauses failed: '+', '.join(k for k,v in rt.items() if not v)})}
    # ---- big78 (G78)
    BG=(BLK['big78'] or {}).get('cases',[]);wb=incomplete(('big78',))
    g78={a:tally(BG,a) for a in BIG_ARMS};g78ok={a:g78[a]['false_certs']==0 and g78[a]['public_false_certs']==0 for a in BIG_ARMS}
    pern={}
    for c in BG:
        n=str(c['true_hidden_state_count_EVALUATOR_ONLY'])
        for a in BIG_ARMS:
            x=pern.setdefault(a,{}).setdefault(n,{'cases':0,'post_forecasts':0,'post_certs':0,'tcert':[]})
            tr=c['arms'][a]['trace'];x['cases']+=1
            for r in tr[c['burn_in']:]:x['post_forecasts']+=2;x['post_certs']+=(r['certificate'] is not None)+(r['counterfactual']['certificate'] is not None)
            x['tcert'].append(next((r['step'] for r in tr if r['certificate'] is not None),45))
    for a in pern:
        for x in pern[a].values():
            x['coverage']=round(x['post_certs']/x['post_forecasts'],6) if x['post_forecasts'] else None
            x['mean_steps_to_first_cert']=round(sum(x['tcert'])/len(x['tcert']),6);x['censored']=sum(t==45 for t in x['tcert']);del x['tcert']
    certs78=sum(g78[a]['certs'] for a in BIG_ARMS)
    g78b={'a_zero_false':all(g78ok.values()),'b_power_ge_150_certificates':certs78>=G78_MIN_CERTS}
    gate('G78_soundness',bool(BG) and all(g78b.values()),{'clauses':g78b,'per_arm':g78,'per_arm_pass':g78ok,'certificates_total':certs78,
         'rule_of_three_upper':round(3/certs78,6) if certs78 else None,'power':'VACUOUS (no certificates issued)' if BG and certs78==0 else 'informative',
         'prediction':C['G78_soundness']['prediction']},why=wb)
    cexc=[];cchk=0;cnonvac=0
    for c in BG:
        for a in BIG_ARMS:
            for r in c['arms'][a]['trace']:
                for side,q,act in (('taken',r,r['actual_emission_EVALUATOR_ONLY']),('counterfactual',r['counterfactual'],r['counterfactual_actual_EVALUATOR_ONLY'])):
                    sp=q.get('support')
                    if sp is None or (q.get('solver_unknown') or 0)!=0:continue
                    cchk+=1;cnonvac+=len(sp)<4
                    if act not in sp:cexc.append({'seed':c['seed'],'mask_rate':c['mask_rate'],'arm':a,'step':r['step'],'action':side,'realised':act,'support':sp})
    gate('G78_containment',bool(BG) and not cexc,{'checked_forecasts':cchk,'non_vacuous_supports':cnonvac,'exceptions':len(cexc),'exception_list':cexc[:50],
         'prediction':C['G78_containment']['prediction']},why=wb)
    gate('R_big78_coverage',None,{'per_arm_per_n':pern},gated=False)
    # ---- transfer (GS)
    TC=(BLK['transfer'] or {}).get('cases',[]);wt=incomplete(('transfer',))
    gsa={};recorded_mismatch=[];sp8cert={}
    for c in TC:
        for r in c['arms']['SP8']['trace']:
            sp8cert[(c['family'],c['seed'],c['mask_rate'],r['step'],r['action'])]=r['certificate']
            sp8cert[(c['family'],c['seed'],c['mask_rate'],r['step'],1-r['action'])]=r['counterfactual']['certificate']
    for a in TR_ARMS:
        x={'cases':len(TC),'certificates':0,'transfer_rule_certificates':0,'false_certificates':0,'false_transfer_rule':0,'cases_with_false':0,
           'disabled_cases':0,'public_false_certificates':0,'certificate_forecasts':0}
        for c in TC:
            T_=c['transfer'][a];sp=c['arms']['SP8']['trace'];f=0
            if a in POSTHOC:
                for r,t in zip(sp,T_['trace']):
                    check(r['step']==t['step'],'TR trace order');act={r['action']:r['actual_emission_EVALUATOR_ONLY'],1-r['action']:r['counterfactual_actual_EVALUATOR_ONLY']}
                    for b_ in (0,1):
                        cb=t['certificate'][b_];x['certificate_forecasts']+=1
                        if cb is None:continue
                        x['certificates']+=1;x['transfer_rule_certificates']+=t['rule'][b_]=='transfer'
                        if cb!=act[b_]:f+=1;x['false_transfer_rule']+=t['rule'][b_]=='transfer'
            else:
                for t in T_['trace']:
                    for b_ in (0,1):
                        cb=t['certificate'][b_];x['certificate_forecasts']+=1
                        pc=t['public_certificate'][b_]
                        if pc is not None and pc!=t['actual_EVALUATOR_ONLY'][b_]:x['public_false_certificates']+=1
                        if cb is None:continue
                        x['certificates']+=1
                        if cb!=t['actual_EVALUATOR_ONLY'][b_]:f+=1
            x['false_certificates']+=f;x['cases_with_false']+=f>0;x['disabled_cases']+=T_.get('disabled_step') is not None
            if f!=T_['false_certificates']:recorded_mismatch.append({'arm':a,'family':c['family'],'seed':c['seed'],'mask_rate':c['mask_rate']})
        gsa[a]=x
    gsa_pass={a:bool(TC) and gsa[a]['false_certificates']==0 for a in GS_A_ARMS}
    gate('GS_a_transfer_soundness',bool(TC) and all(gsa_pass.values()) and not recorded_mismatch,
         {'per_arm_pass':gsa_pass,'per_arm':{a:gsa[a] for a in GS_A_ARMS},'recorded_false_count_mismatches':recorded_mismatch[:20],
          'rule_of_three_upper_per_arm':{a:(round(3/gsa[a]['certificates'],6) if gsa[a]['certificates'] else None) for a in GS_A_ARMS},
          'prediction':C['GS_a_transfer_soundness']['prediction']},why=wt)
    # GS_b: DR subset of SP8 (exact)
    sub_bad=[];cnt_bad=[];dr_pos=[]
    for c in TC:
        for a in ('DRp','DRn'):
            T_=c['transfer'][a];n_dr=0;n_sp=0
            for t in T_['trace']:
                for b_ in (0,1):
                    sc=sp8cert[(c['family'],c['seed'],c['mask_rate'],t['step'],b_)];n_sp+=sc is not None
                    if t['certificate'][b_] is not None:
                        n_dr+=1
                        if t['certificate'][b_]!=sc:sub_bad.append({'arm':a,'family':c['family'],'seed':c['seed'],'mask_rate':c['mask_rate'],'step':t['step'],'action':b_})
            if n_dr>n_sp:cnt_bad.append({'arm':a,'seed':c['seed'],'mask_rate':c['mask_rate'],'dr':n_dr,'sp8':n_sp})
            s_=tcert(c['arms']['SP8']['trace'])-T_['first_cert_step']
            if s_>0:dr_pos.append({'arm':a,'family':c['family'],'seed':c['seed'],'mask_rate':c['mask_rate'],'S':s_})
    gsb={'i_every_DR_certificate_equals_SP8':not sub_bad,'ii_counts_le_SP8':not cnt_bad,'iii_S_DR_le_0_every_case':not dr_pos}
    gate('GS_b_dual_region_subset',bool(TC) and all(gsb.values()),{'clauses':gsb,'violations_subset':sub_bad[:20],'violations_count':cnt_bad[:20],
         'violations_S':dr_pos[:20],'prediction':C['GS_b_dual_region_subset']['prediction']},why=wt)
    SP={a:(paired or {}).get('S_'+a) for a in TR_ARMS}
    def spd(a):
        p=SP[a]
        return None if not p or p.get('mean_S') is None else {'mean_S':p['mean_S'],'ci95':p['ci95'],'a_mean_ge_1':p['mean_S']>=1.0,'b_ci_lower_gt_0':p['ci95'][0]>0}
    wp=wt+incomplete(files=(('PAIRED_ANALYSIS_013.json',paired),))
    gsc={}
    for a in GS_C_ARMS:
        p=SP[a]
        gsc[a]=None if not p or p.get('mean_S') is None else {'i_zero_false':bool(TC) and gsa[a]['false_certificates']==0,
             'ii_no_significant_help_ci_lower_le_0':p['ci95'][0]<=0,'mean_S_n':p['mean_S'],'ci95':p['ci95']}
    gsc_pass={a:bool(gsc[a]) and gsc[a]['i_zero_false'] and gsc[a]['ii_no_significant_help_ci_lower_le_0'] for a in GS_C_ARMS}
    gate('GS_c_wrong_family_control',all(gsc_pass.values()),{'per_arm_pass':gsc_pass,'per_arm':gsc,'prediction':C['GS_c_wrong_family_control']['prediction']},why=wp)
    gsd=spd('ATp');gse=spd('LXp')
    gate('GS_d_AT_speedup',bool(gsd) and gsd['a_mean_ge_1'] and gsd['b_ci_lower_gt_0'],{'clauses':gsd,'detail':SP['ATp'],
         'prediction':C['GS_d_AT_speedup']['prediction']},why=wp)
    gate('GS_e_LX_speedup',bool(gse) and gse['a_mean_ge_1'] and gse['b_ci_lower_gt_0'],{'clauses':gse,'detail':SP['LXp'],
         'prediction':C['GS_e_LX_speedup']['prediction']},why=wp)
    ta=(aud or {}).get('transfer_audit');tseal=SEALS['transfer']
    gref=None if ta is None else {'done_event':bool(ta.get('done_event')),
         'all_cases_audited':ta.get('cases_audited')==ta.get('cases_expected') and (smoke or ta.get('cases_expected')==EXPECTED['transfer']),
         'zero_mismatching_cases':ta.get('mismatching_cases')==0,'of_sealed_results':tseal is not None and ta.get('results_sha256')==tseal['results_sha256']}
    gate('GS_ref_transfer_audit',bool(gref) and all(gref.values()),{'clauses':gref,'audit':None if ta is None else {k:v for k,v in ta.items() if k!='mismatches'},
         'mismatches':None if ta is None else ta.get('mismatches',[])[:20],'wording':'second implementation by the same author'},
         why=wt+(['transfer_audit missing'] if ta is None else [])+([f'g11 stream stopped: {st}'] if st.startswith(BAD_STOP) else []))
    # GST headline
    mech={}
    for X,sp_gate in (('AT','GS_d_AT_speedup'),('LX','GS_e_LX_speedup')):
        pa,na=X+'p',X+'n'
        mech[X]={'GS_a_both_zero_false':gsa_pass.get(pa,False) and gsa_pass.get(na,False),'GS_c_negative':gsc_pass.get(na,False),
                 'speedup':g[sp_gate]['pass'] is True}
        mech[X]['pass']=all(mech[X].values())
    gate('GST_sound_transfer',any(m['pass'] for m in mech.values()),{'per_mechanism':mech,'prediction':C['GST_sound_transfer']['prediction']},
         why=wp+incomplete(files=(('SECOND_IMPLEMENTATION_013_2x2.json',aud),)))
    lib={}
    for c in TC:
        for k_,L in c['libraries'].items():
            x=lib.setdefault(k_,{}).setdefault(L['source_family'],{'cases':0,'status':{},'min_n':{},'motif_count':{}})
            x['cases']+=1
            for fld in ('status','min_n','motif_count'):v=str(L.get(fld));x[fld][v]=x[fld].get(v,0)+1
    hyp={a:{'hypotheses_initial_mean':round(sum(c['transfer'][a]['hypotheses_initial'] for c in TC)/len(TC),3) if TC else None,
            'hypothesis_status':sorted({str(c['transfer'][a]['hypothesis_status']) for c in TC}),
            'disabled_steps':sorted(c['transfer'][a]['disabled_step'] for c in TC if c['transfer'][a].get('disabled_step') is not None)} for a in TR_ARMS}
    trcov={}
    for c in TC:
        for a in TR_ARMS+('SP8',):
            x=trcov.setdefault(c['family'],{}).setdefault(a,[0,0])
            if a=='SP8':
                for r in c['arms']['SP8']['trace'][c['burn_in']:]:x[0]+=(r['certificate'] is not None)+(r['counterfactual']['certificate'] is not None);x[1]+=2
            else:
                for t in c['transfer'][a]['trace'][c['burn_in']:]:x[0]+=sum(v is not None for v in t['certificate']);x[1]+=2
    trcov={f:{a:round(v[0]/v[1],6) if v[1] else None for a,v in d_.items()} for f,d_ in trcov.items()}
    gate('R_transfer_detail',None,{'libraries_by_role_and_source_family':lib,'hypotheses':hyp,'dual_coverage_post_burn_in':trcov,
         'S_per_arm':{a:None if SP[a] is None else {k:SP[a].get(k) for k in ('mean_S','ci95','histogram','families','cases_helped','cases_hurt','cases_equal')} for a in TR_ARMS}},gated=False)
    gate('R_TR_v0100',None,{a:{'false_certificates':gsa[a]['false_certificates'],'cases_with_false':gsa[a]['cases_with_false'],
         'S':None if not SP[a] else {k:SP[a].get(k) for k in ('mean_S','ci95','cases_helped','cases_hurt','cases_equal')}} for a in ('TRp','TRn')} if TC else None,gated=False)
    gate('R_AT4_sensitivity',None,{a:{'false_certificates':gsa[a]['false_certificates'],'transfer_rule_certificates':gsa[a]['transfer_rule_certificates'],
         'S':None if not SP[a] else {k:SP[a].get(k) for k in ('mean_S','ci95','cases_helped','cases_hurt','cases_equal')}} for a in ('AT4p','AT4n')} if TC else None,gated=False)
    gate('R_DR_disagreements',None,{a:{'disagreements':sum(c['transfer'][a]['disagreements'] for c in TC),
         'cases_with_disagreement':sum(c['transfer'][a]['disagreements']>0 for c in TC),'refuted_cases':sum(c['transfer'][a].get('disabled_step') is not None for c in TC),
         'S':None if not SP[a] else {k:SP[a].get(k) for k in ('mean_S','ci95')}} for a in ('DRp','DRn')} if TC else None,gated=False)
    lxr={}
    for a in ('LXp','LXn'):
        rc={}
        for c in TC:
            for k_,v in c['transfer'][a]['rule_counts'].items():rc[k_]=rc.get(k_,0)+v
        ref=[c['transfer'][a]['disabled_step'] for c in TC if c['transfer'][a].get('disabled_step') is not None]
        cov=[0,0];spc=[0,0]
        for c in TC:
            for t in c['transfer'][a]['trace'][c['burn_in']:]:cov[0]+=sum(v is not None for v in t['certificate']);cov[1]+=2
            for r in c['arms']['SP8']['trace'][c['burn_in']:]:spc[0]+=(r['certificate'] is not None)+(r['counterfactual']['certificate'] is not None);spc[1]+=2
        lxr[a]={'rule_counts':rc,'refuted_cases':len(ref),'mean_refutation_step':round(sum(ref)/len(ref),3) if ref else None,
                'dual_coverage_post_burn_in':round(cov[0]/cov[1],6) if cov[1] else None,'SP8_dual_coverage_post_burn_in':round(spc[0]/spc[1],6) if spc[1] else None,
                'public_false_certificates':gsa[a]['public_false_certificates'],
                'S':None if not SP[a] else {k:SP[a].get(k) for k in ('mean_S','ci95','cases_helped','cases_hurt','cases_equal','families')}}
    gate('R_LX_rules',None,lxr if TC else None,gated=False)
    # GAPI
    pm=((ts or {}).get('per_module') or {}).get('test_api_certify_0110.py')
    fzj=load(FREEZE) if FREEZE.exists() else None
    gapi={'i_module_ran_all_ok':bool(pm) and pm.get('returncode')==0 and bool(pm.get('results')) and all(v[0]=='ok' for v in pm['results'].values()),
          'ii_certify_in_source_freeze':bool(fzj) and 'brute/api/certify.py' in fzj.get('sha256_files',{}),
          'tests':None if not pm else len(pm.get('results') or {})}
    gate('GAPI_embeddable_certify',gapi['i_module_ran_all_ok'] and gapi['ii_certify_in_source_freeze'],{'clauses':gapi,
         'results':None if not pm else pm.get('results'),'prediction':C['GAPI_embeddable_certify']['prediction']},
         why=incomplete(files=(('TEST_SUITE_013.json',ts),),streams=('gti',)))
    # ---- non-gated reports
    rj={}
    if paired:rj={k:{x:paired[k][x] for x in ('pooled_gain','pooled_ci95','families')} for k in ('R_J10_minus_SP8_in_family_original',)}
    gate('R_J10_minus_SP8',None,rj,gated=False)
    det=[]
    for c in D:
        for a in ('J10','J9','SP8','A4'):
            evs=set(c['arms'][a]['diagnostics'].get('drift_events') or [])
            for r in c['arms'][a]['trace']:
                for side,q in (('taken',r),('counterfactual',r.get('counterfactual'))):
                    wrong=q.get('v090_wrong') if a=='A4' and side=='taken' else q.get('wrong')
                    if q and wrong:
                        d=max([x for x in DRIFT if x<r['step']],default=None)
                        det.append({'arm':a,'seed':c['seed'],'mask_rate':c['mask_rate'],'step':r['step'],'action':side,'public':bool(q.get('public_wrong')),
                                    'lag':lag(r['step']),'non_drift':nondrift(r['step']),'rule':q.get('cert_rule'),
                                    'event_between':None if d is None or a=='A4' else any(d<=u<r['step'] for u in evs)})
    hist={a:{} for a in ('J10','J9','SP8','A4')}
    for x in det:
        if x['non_drift']:hist[x['arm']][str(x['lag'])]=hist[x['arm']].get(str(x['lag']),0)+1
    gate('R_lag_detail',None,{'false_certificates':det,'non_drift_lag_histogram':hist,'count_by_arm':{a:sum(x['arm']==a for x in det) for a in hist},
         'note':'A4 rows use v090_wrong for the taken action (the G3 control)'},gated=False)
    jh={}
    for c in two:
        x=jh.setdefault(c['family'],{'cases':0,'post_forecasts':0,'post_certs':0,'hull_steps':0,'hull_all_codes':0,'hull_downgrades':0,'hull_queries':0})
        A=c['arms'][GA];x['cases']+=1;x['hull_downgrades']+=A['diagnostics'].get('hull_downgrades') or 0;x['hull_queries']+=A['diagnostics'].get('hull_queries') or 0
        for r in A['trace'][c['burn_in']:]:x['post_forecasts']+=2;x['post_certs']+=(r['certificate'] is not None)+(r['counterfactual']['certificate'] is not None)
        for r in A['trace']:
            H=r.get('hull_union')
            if H is not None:x['hull_steps']+=1;x['hull_all_codes']+=all(len(v)>=4 for v in H.values())
    for x in jh.values():
        x['coverage']=round(x['post_certs']/x['post_forecasts'],6) if x['post_forecasts'] else None
        x['fraction_supW_all_codes']=round(x['hull_all_codes']/x['hull_steps'],6) if x['hull_steps'] else None
    gate('R_J10_hull',None,jh,gated=False)
    strict={s:late[s] is not None and late[s]<=CAP and s not in stopped for s in STREAMS}
    stamp=(aud or {}).get('optional_stamp')
    gate('R_G_RT_strict',None,{'pass':all(strict.values()) and stamp=='optional_done','every_stream_complete_inside_cap_none_stopped':all(strict.values()),
         'per_stream':strict,'g11_optional_stamp':stamp},gated=False)
    gate('R_optional_phase',None,{'g11_optional_stamp':stamp,'g11_optional':None if aud is None else {k:aud['rest'][k] for k in ('traces_expected','traces_audited','traces_not_reached','mismatching_traces')},
         'optional_done_event':(aud or {}).get('events',{}).get('optional_done'),
         'g11_stream':{'stopped':stopped.get('g11'),'completed_s_after_t0':late.get('g11'),'spent_s':round(state.get('spent',{}).get('g11',0),1)}},gated=False)
    gate('R_heartbeat',None,hb,gated=False)
    gate('R_rates',None,{s:{'spent_s':round(state.get('spent',{}).get(s,0),1),'budget_s':BUDGETS[s],
         'fraction_of_budget':round(state.get('spent',{}).get(s,0)/BUDGETS[s],3)} for s in STREAMS},gated=False)
    gate('R_tests_plain',None,None if ts is None else ts.get('plain_discover'),gated=False)
    gate('R_diag_seen',None,{'applicability':None if apseen is None else {k:apseen.get(k) for k in ('label','summary')}},gated=False)
    gate('R_K0100_after_release',None,{'note':'checked post-release against tag v0.10.0 and reported in RELEASE.json (not gated, not scored here)'},gated=False)
    gated=[k for k,v in g.items() if v['gated']]
    return {'schema':'brute.gates.v11_0','retired_gates':sorted(plan['retired_gates']),'study':plan['study'],'plan_sha256':sha(PLAN),'smoke_dry_run':smoke,
            'scientific_sha256':{b:None if SEALS[b] is None else SEALS[b]['scientific_sha256'] for b in EXPECTED},'study_seal_present':top is not None,
            'stop_rule_fired':fired,'gates':g,
            'passed':[k for k in gated if g[k]['pass']],'failed':[k for k in gated if g[k]['pass'] is False],
            'pending':[k for k in gated if g[k]['pass'] is None],'all_gated_pass':all(g[k]['pass'] for k in gated),
            'GST':g['GST_sound_transfer']['pass'],'G3L_power':power,'GTI_in_cap':g['GTI_test_isolation']['pass'],
            'G_RT':g['G_RT_study_runtime']['pass'],
            'transfer':{k:g[k]['pass'] for k in ('GST_sound_transfer','GS_a_transfer_soundness','GS_b_dual_region_subset','GS_c_wrong_family_control',
                        'GS_d_AT_speedup','GS_e_LX_speedup','GS_ref_transfer_audit')}}

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--study-dir',default=str(STUDY_DIR));ap.add_argument('--check',action='store_true')
    ap.add_argument('--output',default='GATES_013.json');ap.add_argument('--smoke',action='store_true',help='dry run on a smoke directory; prints only')
    a=ap.parse_args()
    if a.smoke:
        obj=build(Path(a.study_dir),smoke=True)
        print({k:obj[k] for k in ('passed','failed','pending')});print({k:v.get('reason') for k,v in obj['gates'].items() if v.get('reason')});raise SystemExit
    obj=build(Path(a.study_dir));out=Path(a.study_dir)/a.output
    if a.check:check(out.read_bytes()==dumps(obj),out.name+' does not reproduce');print(out.name,'reproduces')
    else:write_new(out,obj);print({k:obj[k] for k in ('passed','failed','pending','all_gated_pass')})
