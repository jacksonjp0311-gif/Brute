"""Evaluate the pre-registered study-009 criteria (BRUTE_PLAN_009: GA1', G1, G2, G3', G4, G5, G6b, G7, G9, G10, G11, G12,
G13, GX2'', GP1, GTI, G_RT gated; the non_gated_reports reported) from sealed artifacts only. Committed and ledgered
(scoring_freeze_009) before the held-out run_start; thresholds are copied from the plan, nothing is tuned.

Inputs in results/study-009 (D): <block>/{SCIENTIFIC,SEAL,RESULTS}.json for 2x2, breadth, planning; repro/<block>;
PAIRED_ANALYSIS_009.json (make_paired_009), REPRODUCIBILITY_009.json (make_reproducibility_009),
SECOND_IMPLEMENTATION_009.json, XCHECK_009.json, XCHECK_SPOT_009.json, PLANNING_AUDIT_009.json, TEST_SUITE_009.json,
RUN_STATE_009.json, RUN_DONE_009.json / STOP_009.json, SEAL.json (seal_009), DIAG_LAG_009.json.

Scoring choices fixed here, before data (as make_gates_008 unless stated):
- "every action": 2x2 and planning = taken + counterfactual forecast of each step; breadth = all k forecasts.
- G1/G2/G4 tallies: all steps incl. burn-in; a public certificate is also a conditional certificate.
  P7 in-family = its 120 in_family_original planning cases; P7 OOD = its 24 ood5 planning cases.
- G3': taken action, plan drift_definition (NON-DRIFT iff step > 12 and step not in {12,23,34}); limit = 0.5 x sum of
  A4 v090_wrong (taken) on the same drift4 cases.
- G4(c): a public certificate on any forecast of a step > diagnostics.first_alarm_step is a violation.
- G5: a case counts if diagnostics.first_alarm_step is set; arms S7, SC7 (6 in-family 2x2 families), P7 (5 in-family
  planning families), BS7, BSC7 (3 in-family breadth families).
- G6b: PAIRED_ANALYSIS_009 G6b_dual_coverage_{S7,SC7}_minus_A2.
- G7: mean post-burn-in taken-action log-loss rounded to 6 d.p. <= round(ln 4, 6) (S7, SC7 on ood5 and drift4; P7 on
  ood5) / round(ln 8, 6) (BS7, BSC7 on ood6s3); min probability >= round(eps / 2**s, 12) on every step of every case for
  S7, SC7, P7, BS7, BSC7.
- G9: as study-008 for S7, SC7, P7 (tau6) and BS7, BSC7 (tau7); retraction reasons vs ref_reason / k_reason.
- G10: case counts equal the plan job counts (2x2 648, breadth 288, planning 144), every block sealed complete, every
  trace has the plan step count; production arms S7, SC7, A5 (2x2), P7 (planning), B5, BS7, BSC7 (breadth): forecasts
  with solver_unknown > 0 <= 1% per block.
- G11: SECOND_IMPLEMENTATION_009 mismatching traces == 0; traces checked == 2 x 2x2 + 2 x breadth + planning cases;
  each RESULTS.json sha256 it audited equals the block SEAL results_sha256; mutation 20/20 detected, 0 false flags,
  >= 4 injected in P7 action choices.
- G12: REPRODUCIBILITY_009.G12_pass and its main-block hashes equal the seals.
- G13: check_freeze() holds; every block SEAL plan/freeze sha equal the current files; tau6/tau7 values; every case's
  recorded tau equals them.
- GX2'': (i) XCHECK_009 mismatching_traces == 0 and witness_replay_failures == 0 and it covers every breadth case;
  (ii) checked_fraction >= 0.99 for each of big6/sens3/act3/ood6s3 x B5/BS7/BSC7 (missing entry = fail);
  (iii) the gx2_sym stream was not stopped by the 3 h cap or an error (a stop by its own 30 min budget leaves unreached
  steps unchecked and (ii) decides); (iv) XCHECK_SPOT_009 mismatching_traces == 0, witness_replay_failures == 0 and
  checked_steps_per_family >= 64 for each of the 4 families.
- GP1: (i) PAIRED_ANALYSIS_009 GP1 route_coverage.pass OR route_tcert.pass (97.5% CIs, one resample set, 40 seeds);
  (ii) P7 tallies above + 0 public certificates on ood5; (iii) planned / applicable over all P7 planner records with
  applicable == true >= 0.80; (iv) PLANNING_AUDIT iv_replay.passed and cases_replayed == 144; (v) v_count_audit.passed
  (200 sampled, 0 disagreements, >= 100 both complete); (vi) the planning block is sealed complete with 144 cases and the
  planning stream was not stopped.
- GTI: TEST_SUITE_009 verdict.passed (in-cap run, process step 8). The final-tree run is recorded separately in
  GATES_009_FINAL.json; both must pass for the release statement "GTI PASS".
- G_RT: PASS iff STOP_009.json is absent, RUN_DONE_009.json exists with elapsed_s <= 10800 and NO stream was stopped
  for any reason (stream budget, error or cap). (Conservative reading of "every held-out stream finishes".)
- STUDY_BUDGET: a gate whose inputs are incomplete is FAIL. reason = 'STUDY_BUDGET' when STOP_009.json exists (the cap
  fired), else 'INCOMPLETE_INPUT (<stream stop reason or missing file>)'. Inputs: G1/G2/G4/G5/G7/G9/G10 all three
  blocks; G3', G6b the 2x2 block; GA1' 2x2 (G1/G2 per arm read only the 2x2 part for S7/SC7); GX2'' breadth + both
  xcheck reports; G11 all blocks + its report; G12 all blocks + repro + its report; GP1 planning + 2x2 + audit;
  GTI its report; G13 the blocks' seals.
- GA1': PASS iff for at least one X in {S7, SC7}: G1(X), G2(X), G3'(X), G6b(X) all pass."""
from __future__ import annotations
import argparse,math,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common_009 import STUDY_DIR,PLAN,FREEZE,load,dumps,write_new,check,sha,plan_view,check_freeze
from experiments.v011_independent_reference import ref_reason
from experiments.v050_reference import k_reason

LN4,LN8=round(math.log(4),6),round(math.log(8),6)
NEW2=('S7','SC7');NEWB=('BS7','BSC7');SOUND_B=('B5','BS7','BSC7');DRIFT=(12,23,34);TAU6,TAU7=1.645215321642,2.07944154168
XFAM=('big6','sens3','act3','ood6s3');ALL2=('S7','SC7','R6','C6','A5','A4','A2')
EXPECTED={'2x2':648,'breadth':288,'planning':144}
def fcs(r):return [r,r['counterfactual']] if 'counterfactual' in r else r['forecasts']
def nondrift(s):return s>12 and s not in DRIFT


def _tie(Q):
    """2-step use: the one-step objective E1 is tied at its minimum and E2 was computed (tie broken by E2)."""
    from fractions import Fraction as F
    if Q.get('E2') is None or not Q.get('E1'):return False
    e=[F(x) for x in Q['E1'] if x is not None];return bool(e) and e.count(min(e))>1


def opt(p):return load(p) if Path(p).exists() else None


def build(study=STUDY_DIR,smoke=False):
    study=Path(study);plan=load(PLAN);view=plan_view(plan);C=plan['criteria']
    if smoke:EXP={b:None for b in EXPECTED}
    else:EXP=dict(EXPECTED)
    blk={};seal={};res={}
    for b in ('2x2','breadth','planning'):
        blk[b]=opt(study/b/'SCIENTIFIC.json');seal[b]=opt(study/b/'SEAL.json');res[b]=opt(study/b/'RESULTS.json')
        if blk[b] is not None:check(seal[b]['scientific_sha256']==sha(study/b/'SCIENTIFIC.json'),f'{b}: SCIENTIFIC does not match SEAL')
    stop=opt(study/'STOP_009.json');done=opt(study/'RUN_DONE_009.json');state=opt(study/'RUN_STATE_009.json') or {'stopped':{},'spent':{}}
    paired=opt(study/'PAIRED_ANALYSIS_009.json');repro=opt(study/'REPRODUCIBILITY_009.json');audit=opt(study/'SECOND_IMPLEMENTATION_009.json')
    xc=opt(study/'XCHECK_009.json');xs=opt(study/'XCHECK_SPOT_009.json');pa=opt(study/'PLANNING_AUDIT_009.json');ts=opt(study/'TEST_SUITE_009.json')
    top=opt(study/'SEAL.json');diag=opt(study/'DIAG_LAG_009.json') or opt(ROOT/'results/study-009/DIAG_LAG_009.json')
    stopped=state.get('stopped',{})
    def incomplete(blocks=(),files=(),streams=()):
        why=[]
        for b in blocks:
            if blk[b] is None:why.append(f'{b} block missing')
            elif not seal[b].get('complete'):why.append(f'{b} block incomplete ({seal[b].get("case_count")}/{seal[b].get("expected_case_count")})')
            if b in stopped:why.append(f'{b} stream stopped: {stopped[b]}')
        for name,obj in files:
            if obj is None:why.append(f'{name} missing')
        for s in streams:
            if s in stopped:why.append(f'{s} stream stopped: {stopped[s]}')
        return why
    def reason(why):return None if not why else ('STUDY_BUDGET' if stop is not None else 'INCOMPLETE_INPUT')+' ('+'; '.join(why)+')'
    tau6,tau7=plan['tau6']['value'],plan['tau7']['value'];eps=view['open_world_reserve_epsilon'];W=view['window_W']
    two=blk['2x2']['cases'] if blk['2x2'] else [];br=blk['breadth']['cases'] if blk['breadth'] else [];pl=blk['planning']['cases'] if blk['planning'] else []
    IF,IFO,OOF=plan['in_family_2x2'],plan['in_family_original_2x2'],plan['out_of_family_2x2']
    IB,OB=plan['in_family_breadth'],plan['out_of_family_breadth'];g={}
    def gate(name,ok,obs,gated=True,why=None):
        r=reason(why or [])
        if r:g[name]={'gated':True,'pass':False,'reason':r,'observed_on_available_inputs':obs};return
        g[name]={'gated':gated,'pass':(bool(ok) if ok is not None else None) if gated else None,'observed':obs}
    fam=lambda cs,f:[c for c in cs if c['family']==f]
    def tally(cs,arm):
        t={'cases':len(cs),'forecasts':0,'certs':0,'false_certs':0,'public_certs':0,'public_false_certs':0}
        for c in cs:
            for r in c['arms'][arm]['trace']:
                for q in fcs(r):
                    t['forecasts']+=1;t['certs']+=q['certificate'] is not None;t['false_certs']+=bool(q['wrong'])
                    t['public_certs']+=q['public_certificate'] is not None;t['public_false_certs']+=bool(q['public_wrong'])
        t['rule_of_three_upper_false_rate']=round(3/t['certs'],6) if t['certs'] else None;return t
    PIF=[f for f in IFO];blocks=[(two,IF,OOF,NEW2),(pl,PIF,['ood5'],('P7',)),(br,IB,OB,SOUND_B)]
    w_all=incomplete(('2x2','breadth','planning'));w2=incomplete(('2x2',))
    # G1
    g1={}
    for cs,inf,_,arms in blocks:
        tag='planning/' if cs is pl else ''
        for f in inf:
            if fam(cs,f):g1[tag+f]={a:tally(fam(cs,f),a) for a in arms}
    g1arm={a:all(g1[f][a]['false_certs']==0 and g1[f][a]['public_false_certs']==0 for f in g1 if a in g1[f]) for a in NEW2+('P7',)+SOUND_B}
    gate('G1_in_family_soundness',all(g1arm.values()),{'per_arm_pass':g1arm,'per_family':g1},why=w_all)
    # G2
    g2={'ood5':{a:tally(fam(two,'ood5'),a) for a in NEW2},'planning/ood5':{'P7':tally(fam(pl,'ood5'),'P7')},'ood6s3':{a:tally(fam(br,'ood6s3'),a) for a in SOUND_B}}
    g2arm={a:g2['ood5'][a]['false_certs']==0 for a in NEW2};g2arm['P7']=g2['planning/ood5']['P7']['false_certs']==0
    g2arm.update({a:g2['ood6s3'][a]['false_certs']==0 for a in SOUND_B})
    gate('G2_ood_soundness',all(g2arm.values()),{'per_arm_pass':g2arm,**g2,'prediction':C['G2_ood_soundness']['prediction']},why=w_all)
    # G3'
    D=fam(two,'drift4');v090=sum(bool(r['v090_wrong']) for c in D for r in c['arms']['A4']['trace']);limit=0.5*v090;g3={}
    for a in NEW2:
        tr=[(c,r) for c in D for r in c['arms'][a]['trace']]
        tot=sum(bool(r['wrong']) for _,r in tr);nd=sum(bool(r['wrong']) and nondrift(r['step']) for _,r in tr)
        g3[a]={'false_certs_taken':tot,'false_certs_non_drift':nd,'non_drift_zero':nd==0,'total_within_limit':tot<=limit,
               'reported_counterfactual_false':sum(bool(r['counterfactual']['wrong']) for _,r in tr),
               'reported_counterfactual_false_non_drift':sum(bool(r['counterfactual']['wrong']) and nondrift(r['step']) for _,r in tr)}
        g3[a]['pass']=g3[a]['non_drift_zero'] and g3[a]['total_within_limit']
    gate('G3_prime_drift4',all(v['pass'] for v in g3.values()),{'v090_control_false_certs':v090,'limit':limit,'drift_cases':len(D),**g3,
         'definition':plan['drift_definition']},why=w2)
    # G4
    pub_oof={}
    for cs,_,oof,arms in blocks:
        for f in oof:pub_oof[('planning/' if cs is pl else '')+f]={a:tally(fam(cs,f),a)['public_certs'] for a in arms}
    pub_wrong=sum(tally(cs,a)['public_false_certs'] for cs,_,_,arms in blocks for a in arms)
    after=sum(1 for cs,_,_,arms in blocks for c in cs for a in arms for r in c['arms'][a]['trace']
              if c['arms'][a]['diagnostics'].get('first_alarm_step') is not None and r['step']>c['arms'][a]['diagnostics']['first_alarm_step']
              for q in fcs(r) if q['public_certificate'] is not None)
    g4={'a_no_public_on_ood5_drift4_ood6s3':all(v==0 for f in pub_oof for v in pub_oof[f].values()),'b_no_wrong_public':pub_wrong==0,'c_no_public_after_first_alarm':after==0}
    gate('G4_public_safety',all(g4.values()),{'clauses':g4,'public_certs_out_of_family':pub_oof,'public_false_certs':pub_wrong,'public_after_first_alarm':after},why=w_all)
    # G5
    g5={}
    for cs,inf,arms,tag in ((two,IF,NEW2,''),(pl,PIF,('P7',),'planning/'),(br,IB,NEWB,'')):
        for f in inf:
            cc=fam(cs,f)
            if not cc:continue
            g5[tag+f]={a:{'cases':len(cc),'cases_with_alarm':sum(c['arms'][a]['diagnostics'].get('first_alarm_step') is not None for c in cc)} for a in arms}
            for v in g5[tag+f].values():v['fraction']=round(v['cases_with_alarm']/v['cases'],6)
    gate('G5_false_alarm_limit',all(v['fraction']<=0.05 for f in g5 for v in g5[f].values()),{'tau6':tau6,'tau7':tau7,'per_family':g5,
         'prediction':C['G5_false_alarm_limit']['prediction']},why=w_all)
    # G6b
    g6={}
    if paired:
        for a in NEW2:
            P=paired[f'G6b_dual_coverage_{a}_minus_A2'];g6[a]={'pooled_gain':P['pooled_gain'],'pooled_ci95':P['pooled_ci95'],
                'a_pooled_ge_-0.03':P['pooled_gain']>=-0.03,'b_ci_lower_ge_-0.05':P['pooled_ci95'][0]>=-0.05,'families':P['families']}
            g6[a]['pass']=g6[a]['a_pooled_ge_-0.03'] and g6[a]['b_ci_lower_ge_-0.05']
    gate('G6b_coverage_vs_v020',all(v['pass'] for v in g6.values()) and bool(g6),{**g6,
         'reported_A5_minus_A2':paired and paired['R_dual_coverage_A5_minus_A2']['pooled_gain'],
         'reported_R6_minus_A2':paired and paired['R_dual_coverage_R6_minus_A2']['pooled_gain'],
         'reported_C6_minus_A2':paired and paired['R_dual_coverage_C6_minus_A2']['pooled_gain'],
         'prediction':C['G6b_coverage_vs_v020']['prediction']},why=w2+incomplete(files=(('PAIRED_ANALYSIS_009.json',paired),)))
    # GA1'
    ga={a:{'G1':all(g1[f][a]['false_certs']==0 and g1[f][a]['public_false_certs']==0 for f in g1 if a in g1[f]),'G2':g2arm[a],
           'G3_prime':g3[a]['pass'],'G6b':bool(g6) and g6[a]['pass']} for a in NEW2}
    for a in NEW2:ga[a]['all']=all(ga[a].values())
    gate('GA1_prime_sync_drift_and_coverage',any(ga[a]['all'] for a in NEW2),{'per_arm':ga,'passing_arms':[a for a in NEW2 if ga[a]['all']],
         'note':'FAIL means target (a) is NOT met even if G3-prime and G6b are each passed by a DIFFERENT arm',
         'prediction':C['GA1_prime_sync_drift_and_coverage']['prediction']},why=w2+incomplete(files=(('PAIRED_ANALYSIS_009.json',paired),)))
    # G7
    def mean_ll(cs,a):
        v=[r['logloss'] for c in cs for r in c['arms'][a]['trace'][c['burn_in']:]];return round(sum(v)/len(v),6) if v else None
    ll={'ood5':{a:mean_ll(fam(two,'ood5'),a) for a in NEW2},'drift4':{a:mean_ll(fam(two,'drift4'),a) for a in NEW2},
        'planning/ood5':{'P7':mean_ll(fam(pl,'ood5'),'P7')},'ood6s3':{a:mean_ll(fam(br,'ood6s3'),a) for a in NEWB}}
    minp_bad=[];minp={}
    for cs,arms in ((two,NEW2+('A5',)),(pl,('P7',)),(br,NEWB+('B5',))):
        for c in cs:
            thr=round(eps/2**c.get('s',2),12)
            for a in arms:
                mp=min(r['min_probability'] for r in c['arms'][a]['trace']);k=f"{c['block']}/{c['family']}/{a}";minp[k]=min(minp.get(k,1),mp)
                if mp<thr-1e-12 and a in NEW2+NEWB+('P7',):minp_bad.append({'family':c['family'],'seed':c['seed'],'mask_rate':c['mask_rate'],'arm':a,'min':mp,'threshold':thr})
    g7={'logloss_2x2_le_ln4':all(ll[f][a] is not None and ll[f][a]<=LN4 for f in ('ood5','drift4','planning/ood5') for a in ll[f]),
        'logloss_ood6s3_le_ln8':all(ll['ood6s3'][a] is not None and ll['ood6s3'][a]<=LN8 for a in NEWB),'min_probability':not minp_bad}
    gate('G7_open_world',all(g7.values()),{'clauses':g7,'logloss_post':ll,'ln4':LN4,'ln8':LN8,'eps':eps,'min_probability_by_block_family_arm':minp,'violations':minp_bad[:20]},why=w_all)
    # G9
    resumes=0;resume_bad=[];resync=0;reasons_ok=True;totals={};dups=0;bad_reason=[]
    for cs,arms,tau,breadth in ((two,NEW2,tau6,False),(pl,('P7',),tau6,False),(br,NEWB,tau7,True)):
        for c in cs:
            for a in arms:
                A=c['arms'][a];tr=A['trace']
                dups+=len(A['issued'])-len({tuple(x) for x in A['issued']})+len(A['retractions'])-len({(e['step'],e['certificate']) for e in A['retractions']})
                resync+=sum(1 for r in tr for q in fcs(r) if q['certificate'] is not None and q['reason']=='RESYNC_AMBIGUOUS')
                resync+=sum(1 for s_,_ in A['issued'] if fcs(tr[s_-1])[tr[s_-1]['action'] if breadth else 0]['reason']=='RESYNC_AMBIGUOUS')
                for e in A['retractions']:
                    want=k_reason(e['certificate'],e['observed'],c['s']) if breadth else ref_reason(e['certificate'],e['observed'])
                    if e['reason']!=want:reasons_ok=False;bad_reason.append({'family':c['family'],'seed':c['seed'],'arm':a,'step':e['step']})
                    totals[e['reason']]=totals.get(e['reason'],0)+1
                for s_ in A['diagnostics'].get('resume_steps',[]):
                    resumes+=1;win=tr[max(0,s_-W):s_]
                    ok=len(win)==W and all(r['residual_after'] is not None and r['residual_after']<=tau for r in win) \
                       and tr[s_-1]['family_status_after']=='supported' and tr[s_-1]['margin_status_after']=='supported'
                    if not ok:resume_bad.append({'family':c['family'],'seed':c['seed'],'mask_rate':c['mask_rate'],'arm':a,'resume_step':s_})
    gate('G9_retraction_resume',not resume_bad and resync==0 and reasons_ok and dups==0,
         {'resumes_checked':resumes,'resume_rule_violations':resume_bad[:50],'resync_ambiguous_certified_or_issued':resync,
          'retraction_reasons_match_reference':reasons_ok,'retraction_reason_mismatches':bad_reason[:50],'retraction_reasons_total':totals,'duplicate_pairs':dups},why=w_all)
    # G10
    have={'2x2':len(two),'breadth':len(br),'planning':len(pl)}
    steps={'2x2':plan['actions_per_case_2x2'],'planning':plan['actions_per_case_2x2'],'breadth':plan['actions_per_case_breadth']}
    short=[f"{c['block']}/{c['family']}/{c['seed']}/{c['mask_rate']}/{a}" for b,cs in (('2x2',two),('breadth',br),('planning',pl)) for c in cs
           for a in c['arms'] if len(c['arms'][a]['trace'])!=steps[b]]
    unk_rate={}
    for name,cs,arms in (('2x2',two,('S7','SC7','A5')),('planning',pl,('P7',)),('breadth',br,SOUND_B)):
        tot=u=0
        for c in cs:
            for a in arms:
                for r in c['arms'][a]['trace']:
                    for q in fcs(r):tot+=1;u+=(q.get('solver_unknown') or 0)>0
        unk_rate[name]={'arms':list(arms),'forecasts':tot,'with_unknown':u,'fraction':round(u/tot,6) if tot else None}
    wall={}
    for b in res:
        for c in (res[b] or {}).get('cases',[]):
            for a,A in c['arms'].items():k=f"{b}/{a}";wall[k]=round(wall.get(k,0)+A.get('elapsed_informational',0),2)
    counts_ok=all(EXP[b] is None or have[b]==EXP[b] for b in EXP) and all(seal[b] and seal[b].get('complete') for b in seal)
    gate('G10_compute',counts_ok and not short and all(v['fraction'] is not None and v['fraction']<=0.01 for v in unk_rate.values()),
         {'cases_expected':EXP,'cases_present':have,'sealed_complete':{b:seal[b] and seal[b].get('complete') for b in seal},'short_traces':short[:20],
          'production_unknown_forecasts':unk_rate,'wall_clock_informational_seconds':wall,'timing_note':'informational, shared 8-CPU box; not a gate input'},why=w_all)
    # G11
    g11={}
    if audit:
        mt=audit.get('mutation_test',{});rf=audit.get('results_files_sha256',{})
        g11={'zero_mismatching_traces':audit['mismatching_arm_traces']==0,
             'all_traces_counted':audit['arm_traces_checked']==2*len(two)+2*len(br)+len(pl),
             'of_sealed_results':all(any(Path(p).parent.name==b and v==seal[b]['results_sha256'] for p,v in rf.items()) for b in seal if seal[b]),
             'mutation_20_of_20':mt.get('injected')==20 and mt.get('detected_injected')==20 and mt.get('flagged_not_injected')==0 and (mt.get('injected_p7_actions') or 0)>=4}
    gate('G11_second_implementation',bool(g11) and all(g11.values()),{'clauses':g11,**({k:audit[k] for k in audit if k!='mismatches'} if audit else {}),
         'mismatches':(audit or {}).get('mismatches',[])[:50] if isinstance((audit or {}).get('mismatches'),list) else (audit or {}).get('mismatches')},
         why=w_all+incomplete(files=(('SECOND_IMPLEMENTATION_009.json',audit),),streams=('g11',)))
    # G12
    g12ok=bool(repro) and repro['G12_pass'] and all(repro['blocks'][b]['main_scientific_sha256']==seal[b]['scientific_sha256'] for b in repro['blocks'])
    rs=['repro_2x2','repro_breadth','repro_planning']
    gate('G12_reproducibility',g12ok,None if repro is None else repro['blocks'],
         why=w_all+incomplete(files=(('REPRODUCIBILITY_009.json',repro),),streams=rs))
    # G13
    try:check_freeze();fz=True;fz_err=None
    except Exception as exc:fz=False;fz_err=f'{type(exc).__name__}: {exc}'
    taus=sorted({c.get('tau6') for c in two+pl})+sorted({c.get('tau') for c in br})
    g13={'freeze_chain_holds':fz,'plan_tau_values':tau6==TAU6 and tau7==TAU7,
         'cases_use_plan_tau':all(c.get('tau6')==tau6 for c in two+pl) and all(c.get('tau')==tau7 for c in br),
         'seals_of_current_plan_and_freeze':all(s['plan_sha256']==sha(PLAN) and FREEZE.exists() and s['freeze_sha256']==sha(FREEZE) for s in seal.values() if s)}
    g13ok=all(g13.values()) if not smoke else (g13['plan_tau_values'] and g13['cases_use_plan_tau'])
    gate('G13_frozen_controls_reproduce',g13ok,{'clauses':g13,'freeze_error':fz_err,'recorded_taus':taus,'smoke_dry_run_relaxed':smoke},why=incomplete(('2x2','breadth','planning')) if any(s is None for s in seal.values()) else None)
    # GX2''
    fr={f'{f}/{a}':((xc or {}).get('per_family_arm',{}).get(f'{f}/{a}') or {}).get('checked_fraction') for f in XFAM for a in SOUND_B}
    spot_steps=(xs or {}).get('checked_steps_per_family',{})
    gx={}
    if xc:
        gx={'i_zero_mismatching_and_witness':xc['mismatching_traces']==0 and xc['witness_replay_failures']==0,
            'i_covers_every_breadth_case':xc['cases_expected']==len(br) and xc['cases_done']==len(br),
            'ii_checked_ge_0.99_each':all(v is not None and v>=0.99 for v in fr.values()),
            'iii_symmetric_not_stopped_by_cap_or_error':not str(stopped.get('gx2_sym','')).startswith(('STUDY_BUDGET','exit code'))}
    if xs:
        gx['iv_spot_zero_mismatching_and_witness']=xs['mismatching_traces']==0 and xs['witness_replay_failures']==0
        gx['iv_spot_ge_64_steps_each_family']=all((spot_steps.get(f) or 0)>=64 for f in XFAM)
    gate('GX2_dprime_incremental_xcheck',len(gx)==6 and all(gx.values()),{'clauses':gx,'checked_fraction':fr,
         'per_family_arm':(xc or {}).get('per_family_arm'),'symmetric_spent_s':state.get('spent',{}).get('gx2_sym'),
         'symmetric_stop':stopped.get('gx2_sym'),'mismatches':(xc or {}).get('mismatches',[])[:50],'queries':(xc or {}).get('queries'),
         'unknown_queries':(xc or {}).get('unknown_queries'),'witness_replay_failures':(xc or {}).get('witness_replay_failures'),
         'spot':None if xs is None else {k:xs[k] for k in xs if k not in ('mismatches',)},'wording':(xc or {}).get('wording'),
         'prediction':C['GX2_dprime_incremental_xcheck']['prediction']},
         why=incomplete(('breadth',),files=(('XCHECK_009.json',xc),('XCHECK_SPOT_009.json',xs)),streams=('gx2_sym','gx2_spot')) if not (xc and xs and not str(stopped.get('gx2_sym','')).startswith(('STUDY_BUDGET','exit code')) and not stopped.get('gx2_spot','').startswith(('STUDY_BUDGET','exit code'))) or incomplete(('breadth',)) else None)
    # GP1
    P=(paired or {}).get('GP1_i_P7_minus_A5') or {};rc,rt=P.get('route_coverage'),P.get('route_tcert')
    pin=[c for c in pl if c['family'] in IFO];pood=fam(pl,'ood5');tin=tally(pin,'P7');tood=tally(pood,'P7')
    app=pln=0;by_reason={};by_source={};two_step=0;by_fm={}
    for c in pl:
        for r in c['arms']['P7']['trace']:
            Q=r.get('planner')
            if not Q or not Q.get('applicable'):continue
            app+=1;pln+=bool(Q.get('planned'));k=(c['family'],str(c['mask_rate']));x=by_fm.setdefault(f'{k[0]}/{k[1]}',{'applicable':0,'planned':0})
            x['applicable']+=1;x['planned']+=bool(Q.get('planned'))
            if Q.get('planned'):by_source[Q.get('source')]=by_source.get(Q.get('source'),0)+1;two_step+=_tie(Q)
            else:rs_=str(Q.get('fallback_reason'));rs_=rs_.split(':')[0] if rs_.startswith('counter UNKNOWN') else rs_;by_reason[rs_]=by_reason.get(rs_,0)+1
    pf=round(pln/app,6) if app else None
    gp={'i_route_coverage_or_tcert':bool(rc and rt and (rc['pass'] or rt['pass'])),
        'ii_soundness':tin['false_certs']==0 and tin['public_false_certs']==0 and tood['false_certs']==0 and tood['public_certs']==0,
        'iii_planned_fraction_ge_0.80':pf is not None and pf>=0.80,
        'iv_replay_isolation':bool(pa) and pa['iv_replay']['passed'] and (smoke or pa['iv_replay']['cases_replayed']==144),
        'v_count_audit':bool(pa) and pa['v_count_audit']['passed'],
        'vi_all_cases_complete_in_budget':bool(seal['planning']) and bool(seal['planning'].get('complete')) and (smoke or len(pl)==144) and 'planning' not in stopped}
    gate('GP1_planning_vs_LUR',all(gp.values()),{'clauses':gp,'route_coverage':rc,'route_tcert':rt,'per_family':P.get('families'),
         'missing_comparator':P.get('missing_comparator'),'P7_in_family_tally':tin,'P7_ood5_tally':tood,
         'planned_fraction':pf,'applicable_decisions':app,'planned_decisions':pln,
         'iv':None if pa is None else {k:v for k,v in pa['iv_replay'].items() if k!='mismatches'}|{'mismatches':pa['iv_replay']['mismatches'][:20]},
         'v':None if pa is None else {k:v for k,v in pa['v_count_audit'].items() if k!='rows'},
         'prediction':C['GP1_planning_vs_LUR']['prediction']},
         why=incomplete(('planning','2x2'),files=(('PLANNING_AUDIT_009.json',pa),('PAIRED_ANALYSIS_009.json',paired)),streams=('gp1_audit',)))
    # GTI (in-cap)
    V=(ts or {}).get('verdict')
    gate('GTI_test_isolation',bool(V) and V['passed'],None if ts is None else {'verdict':V,'head':ts.get('head'),'tracked_tree_dirty':ts.get('tracked_tree_dirty'),
         'run':'in-cap (process step 8); the final-tree run is recorded in GATES_009_FINAL.json'},
         why=incomplete(files=(('TEST_SUITE_009.json',ts),),streams=('gti',)))
    # G_RT
    rt_ok=stop is None and done is not None and done['elapsed_s']<=10800 and not stopped
    g['G_RT_study_runtime']={'gated':True,'pass':bool(rt_ok),'observed':{'stop':stop,'run_done':done,'stopped_streams':stopped,
         'spent_s':{k:round(v) for k,v in state.get('spent',{}).items()},'cap_s':10800},
         **({} if rt_ok else {'reason':'STUDY_BUDGET' if stop is not None else ('streams stopped: '+', '.join(f'{k} ({v})' for k,v in stopped.items()) if stopped else 'RUN_DONE_009 missing')})}
    # ---- non-gated reports
    rep=plan['non_gated_reports']
    gate('R_diag_lag_008',None,None if diag is None else {'label':diag.get('label'),
         'summary':{a:{k:v for k,v in diag['arms'][a]['summary'].items() if k!='nondrift_classes'} for a in diag['arms']},'note':rep['R_diag_lag_008']},gated=False)
    gate('R_lag_heldout',None,lag_heldout(D,tau6),gated=False)
    ev={}
    for cs,arms in ((two,NEW2),(br,NEWB)):
        for c in cs:
            for a in arms:
                k=f"{c['family']}/{a}";e=ev.setdefault(k,{'cases':0,'E1':0,'E2':0,'E3':0})
                e['cases']+=1
                for _,types in c['arms'][a]['diagnostics'].get('event_triggers',[]):
                    for t in types:e[t]=e.get(t,0)+1
    gate('R_event_rates',None,ev,gated=False)
    vs={}
    if paired:vs={'S7_minus_R6':{k:paired['R_vs_v060_S7_minus_R6'][k] for k in ('pooled_gain','pooled_ci95')},
                  'SC7_minus_C6':{k:paired['R_vs_v060_SC7_minus_C6'][k] for k in ('pooled_gain','pooled_ci95')}}
    vs['drift4_taken_false']={a:sum(bool(r['wrong']) for c in D for r in c['arms'][a]['trace']) for a in ALL2 if D}
    gate('R_vs_v060',None,vs,gated=False)
    al=[]
    for c in fam(two,'perm4'):
        arms=[a for a in ALL2 if c['arms'][a]['diagnostics'].get('first_alarm_step') is not None]
        if arms:al.append({'seed':c['seed'],'mask_rate':c['mask_rate'],'steps':{a:c['arms'][a]['diagnostics']['first_alarm_step'] for a in arms},'arms':arms})
    gate('R_alarm_perm4',None,{'cases':al,'count':len(al)},gated=False)
    tc={}
    from scripts.make_paired_009 import tcert
    for c in pl:
        k=f"{c['family']}/{c['mask_rate']}";x=tc.setdefault(k,{'cases':0,'tcert_sum':0,'cov_num':0,'cov_den':0})
        x['cases']+=1;x['tcert_sum']+=tcert(c['arms']['P7']['trace'])
        for r in c['arms']['P7']['trace'][c['burn_in']:]:x['cov_num']+=(r['certificate'] is not None)+(r['counterfactual']['certificate'] is not None);x['cov_den']+=2
    for x in tc.values():x['mean_tcert']=round(x.pop('tcert_sum')/x['cases'],6);x['coverage']=round(x['cov_num']/x['cov_den'],6) if x['cov_den'] else None
    gate('R_planning_detail',None,{'fallback_by_reason':by_reason,'planned_by_source':by_source,'planned_decided_by_two_step_E2_tiebreak':two_step,
         'by_family_mask':by_fm,'coverage_and_tcert_by_family_mask':tc},gated=False)
    gate('R_xcheck_enum',None,None if not (audit and xc) else {'xcheck_mismatching_traces':xc['mismatching_traces'],
         'enumeration_mismatching_traces':audit['mismatching_arm_traces'],'enumeration_breadth_steps_checked':audit.get('breadth_steps_checked'),
         'note':'v070_reference enumerates BS7/BSC7 up to the 160000 row budget; both report 0 => every commonly checked step agrees'},gated=False)
    det=[]
    for c in D:
        for a in ALL2:
            for r in c['arms'][a]['trace']:
                for side,q in (('taken',r),('counterfactual',r.get('counterfactual'))):
                    if q and q.get('wrong'):
                        last=max([x for x in DRIFT if x<=r['step']],default=None)
                        det.append({'arm':a,'seed':c['seed'],'mask_rate':c['mask_rate'],'step':r['step'],'action':side,'public':bool(q.get('public_wrong')),
                                    'steps_after_last_drift':None if last is None else r['step']-last,'non_drift':nondrift(r['step'])})
    gate('R_drift_detail',None,{'false_certificates':det,'count_by_arm':{a:sum(x['arm']==a for x in det) for a in ALL2}},gated=False)
    gate('R_tests_plain',None,None if ts is None else ts.get('plain_discover'),gated=False)
    gated=[k for k,v in g.items() if v['gated']]
    return {'schema':'brute.gates.v7_0','study':plan['study'],'plan_sha256':sha(PLAN),'smoke_dry_run':smoke,
            'scientific_sha256':{b:s['scientific_sha256'] for b,s in seal.items() if s},'study_seal_present':top is not None,
            'stop_rule_fired':stop is not None,'gates':g,
            'passed':[k for k in gated if g[k]['pass']],'failed':[k for k in gated if g[k]['pass'] is False],
            'pending':[k for k in gated if g[k]['pass'] is None],'all_gated_pass':all(g[k]['pass'] for k in gated),
            'GA1_prime':g['GA1_prime_sync_drift_and_coverage']['pass'],'GX2_dprime':g['GX2_dprime_incremental_xcheck']['pass'],
            'GP1':g['GP1_planning_vs_LUR']['pass'],'GTI_in_cap':g['GTI_test_isolation']['pass'],'G_RT':g['G_RT_study_runtime']['pass']}


def lag_heldout(D,tau):
    """R_lag_heldout: diag_lag_009.analyse on the held-out drift4 traces. S7/SC7: E1 = their recorded E1 event steps
    (diagnostics.event_triggers); R6/C6: recorded drift_events; A5/A4: the diagnostic's approximation; A2 slim."""
    from scripts.diag_lag_009 import analyse
    out={}
    for arm in ALL2:
        rows=[]
        for c in D:
            A=c['arms'][arm]
            if arm in NEW2:
                A=dict(A,diagnostics=dict(A['diagnostics'],drift_events=[s for s,t in A['diagnostics'].get('event_triggers',[]) if 'E1' in t]))
                rows.append(analyse({'seed':c['seed'],'mask_rate':c['mask_rate'],'arms':{'R6':A}},'R6',tau))
            else:rows.append(analyse(c,arm,tau))
        s={'cases':len(rows),'false_total':sum(len(r['false_steps']) for r in rows),
           'nondrift_false':[[r['seed'],r['mask_rate'],u] for r in rows for u in r['nondrift_false_steps']]}
        if rows and rows[0].get('full_trace'):
            Dd=[x for r in rows for x in r['drift']]
            for k in ('E1','E2','E3','E2E3'):
                det=[x['lag_'+k][0] for x in Dd if not x['lag_'+k][1]]
                s['lag_'+k]={'drift_steps':len(Dd),'detected':len(det),'censored':len(Dd)-len(det),'hist':{str(v):det.count(v) for v in sorted(set(det))}}
            cl=[dict(x,seed=r['seed'],mask_rate=r['mask_rate']) for r in rows for x in r['nondrift_classes']]
            s['nondrift_classes']=cl;s['class_counts']={k:sum(x['class']==k for x in cl) for k in ('i','ii','iii','not at d+1')}
        out[arm]=s
    return out


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--study-dir',default=str(STUDY_DIR));ap.add_argument('--check',action='store_true')
    ap.add_argument('--output',default='GATES_009.json');ap.add_argument('--smoke',action='store_true',help='dry run on a smoke directory; prints only')
    a=ap.parse_args()
    if a.smoke:
        obj=build(Path(a.study_dir),smoke=True)
        print({k:obj[k] for k in ('passed','failed','pending')});print({k:v.get('reason') for k,v in obj['gates'].items() if v.get('reason')});raise SystemExit
    obj=build(Path(a.study_dir));out=Path(a.study_dir)/a.output
    if a.check:check(out.read_bytes()==dumps(obj),out.name+' does not reproduce');print(out.name,'reproduces')
    else:write_new(out,obj);print({k:obj[k] for k in ('passed','failed','pending','all_gated_pass')})
