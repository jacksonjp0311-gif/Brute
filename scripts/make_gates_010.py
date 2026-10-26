"""Evaluate the pre-registered study-010 criteria (BRUTE_PLAN_010: GA1_010, G1, G2, G3', G6b, GD, G4, G5, G7, G9, G10,
G11, GX2_010, G12, G13, GTI, G_RT gated; the non_gated_reports reported) from sealed artifacts only. Committed and
ledgered (scoring_freeze_010) before the held-out run_start; thresholds are copied from the plan, nothing is tuned.

Inputs in results/study-010 (D): <block>/{SCIENTIFIC,SEAL,RESULTS}.json for 2x2, breadth; repro/<block>;
PAIRED_ANALYSIS_010.json, REPRODUCIBILITY_010.json, SECOND_IMPLEMENTATION_010_{2x2,breadth}.json, XCHECK_010.json,
XCHECK_SPOT_010.json, TEST_SUITE_010.json, RUN_STATE_010.json, RUN_T0, RUN_DONE_010.json / STOP_010.json /
STOP_010_ORCHESTRATOR.json, HEARTBEAT_010.jsonl, KILL_DRILL_010.json (copy of the smoke-3 drill STOP record), SEAL.json,
DIAG_REPLAY_009.json.

Scoring choices fixed here, before data (as make_gates_009 unless stated):
- "every action": 2x2 = taken + counterfactual forecast of each step; breadth = all k forecasts.
- G1: J8, SP8, SC7 on each in_family_2x2 family; B5, BSC7, BSP8 on each in_family_breadth family; 0 false and 0 public
  false certificates; all steps incl. burn-in. A public certificate is also a conditional certificate.
- G2: J8, SP8, SC7 on ood5; B5, BSC7, BSP8 on ood6s3; 0 false certificates.
- G3': taken action, drift_definition (NON-DRIFT iff step > 12 and step not in {12,23,34}); limit = 0.5 x sum of A4
  v090_wrong (taken) on the same drift4 cases; gated for J8 and SP8 separately (both must pass for the G3' row; the
  per-arm results feed GA1_010); SC7 reported.
- G6b: PAIRED_ANALYSIS_010 G6b_dual_coverage_{J8,SP8}_minus_A2; both must pass for the G6b row; per arm feeds GA1_010.
- GA1_010: PASS iff for at least one X in {SP8, J8}: G1(X) (its in-family 2x2 tallies), G2(X) (ood5), G3'(X), G6b(X).
- GD: scripts/diag_stale_010.run on the 2x2 SCIENTIFIC.json with arms SC7, SP8 and hull arm J8 (fixed before data):
  (i) evaluable iff >= 3 non-drift false certificates, PASS iff stale fraction >= 0.8 (else FAIL, reason
  INSUFFICIENT_EVENTS when < 3); (ii) 0 hull-containment exceptions (missing hull_union = exception). Non-vacuity reported.
- G4: arms J8, SP8, SC7, B5, BSC7, BSP8: (a) 0 public certificates on ood5, drift4, ood6s3; (b) 0 wrong public anywhere;
  (c) no public certificate on any forecast of a step > diagnostics.first_alarm_step.
- G5: a case counts if diagnostics.first_alarm_step is set; J8, SP8 on each in_family_2x2 family; BSP8 on each
  in_family_breadth family; fraction <= 0.05.
- G7: mean post-burn-in taken-action log-loss rounded to 6 d.p. <= round(ln 4, 6) for J8, SP8 on ood5 and drift4;
  <= round(ln 8, 6) for BSP8 on ood6s3; min probability >= round(eps / 2**s, 12) (0.005 2x2, 0.0025 breadth) on every
  step of every case for J8, SP8, BSP8 (other arms reported).
- G9: as make_gates_009 for J8, SP8 (tau6, ref_reason) and BSP8 (tau7, k_reason).
- G10: case counts 2x2 648, breadth 288, both sealed complete, every trace has the plan step count; production arms J8,
  SP8 (2x2), BSP8 (breadth): forecasts with solver_unknown > 0 <= 1% per block.
- G11: for each block report SECOND_IMPLEMENTATION_010_<block>: (i) mandatory_complete, mandatory_samples_present and 0
  mandatory mismatching traces; (ii) 0 rest mismatching traces; (iii) 2x2 mutation_test.passed (20 injected in 20
  distinct traces, 20 detected, >= 4 J8 certificate/hull fields, >= 4 SP8 actions, 0 flagged not injected); (iv) the
  'mandatory_done' event exists with wall_since_start <= the g11 stream budget (1500 s) and the stream was not stopped by
  the cap or an error before writing the report; the audited RESULTS.json sha256 equals the block SEAL results_sha256.
  A stop of a g11 stream by its own budget AFTER mandatory_done leaves rest traces unaudited (allowed).
- G12: REPRODUCIBILITY_010.G12_pass and its main hashes equal the seals.
- G13: check_freeze() holds; every block SEAL plan/freeze sha equal the current files; tau6/tau7; every case's tau.
- GX2_010: (i) XCHECK_010 0 mismatching traces, 0 witness replay failures, covers every breadth case; (ii) checked_fraction
  >= 0.99 for each of big6/sens3/act3/ood6s3 x B5/BSC7 (missing = fail); (iii) gx2_sym finished inside its budget (not
  stopped for any reason); (iv) XCHECK_SPOT_010 0 mismatching, 0 replay failures, checked_steps_per_family >= 64 for act3
  and sens3.
- GTI: TEST_SUITE_010 verdict.passed (in-cap run).
- G_RT: (i) every stream of the plan list has a completed_at stamp <= RUN_T0 + 7200 in RUN_STATE_010 and no stream was
  stopped for any reason; (ii) HEARTBEAT_010.jsonl first wall <= RUN_T0 + 60 and last wall >= (end - 10 s), end =
  RUN_T0 + RUN_DONE elapsed_s, or the deadline if no RUN_DONE; (iii) KILL_DRILL_010.json kill_latency_s <= 15 and no
  survivors. Max heartbeat gap and every gap > 10 s are reported.
- STUDY_BUDGET: a gate whose inputs are incomplete is FAIL; reason 'STUDY_BUDGET' when a STOP file exists, else
  'INCOMPLETE_INPUT (...)'."""
from __future__ import annotations
import argparse,json,math,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common_010 import STUDY_DIR,PLAN,FREEZE,load,dumps,write_new,check,sha,plan_view,check_freeze
from experiments.v011_independent_reference import ref_reason
from experiments.v050_reference import k_reason
from scripts import diag_stale_010 as GDS

LN4,LN8=round(math.log(4),6),round(math.log(8),6)
NEW2=('J8','SP8');SOUND2=('J8','SP8','SC7');SOUND_B=('B5','BSC7','BSP8');DRIFT=(12,23,34);TAU6,TAU7=1.645215321642,2.07944154168
XFAM=('big6','sens3','act3','ood6s3');XARMS=('B5','BSC7');ALL2=('J8','SP8','SC7','A4','A2')
EXPECTED={'2x2':648,'breadth':288};CAP=7200;G11_BUDGET=1500
STREAMS=('2x2','breadth','gx2_sym','gx2_spot','g11_2x2','g11_breadth','repro_2x2','repro_breadth','gti')
def fcs(r):return [r,r['counterfactual']] if 'counterfactual' in r else r['forecasts']
def nondrift(s):return s>12 and s not in DRIFT
def opt(p):return load(p) if Path(p).exists() else None


def heartbeat(d):
    p=d/'HEARTBEAT_010.jsonl'
    if not p.exists():return None
    R=[json.loads(l) for l in p.read_text().splitlines() if l.strip()]
    if not R:return None
    g=[r['gap_s'] for r in R if r.get('gap_s') is not None]
    return {'beats':len(R),'first_wall':R[0]['wall'],'last_wall':R[-1]['wall'],'max_gap_s':max(g) if g else None,
            'gaps_over_10s':[{'wall':r['wall'],'gap_s':r['gap_s']} for r in R if (r.get('gap_s') or 0)>10]}


def build(study=STUDY_DIR,smoke=False):
    study=Path(study);plan=load(PLAN);view=plan_view(plan);C=plan['criteria']
    EXP={b:None for b in EXPECTED} if smoke else dict(EXPECTED)
    blk={};seal={};res={}
    for b in ('2x2','breadth'):
        blk[b]=opt(study/b/'SCIENTIFIC.json');seal[b]=opt(study/b/'SEAL.json');res[b]=opt(study/b/'RESULTS.json')
        if blk[b] is not None:check(seal[b]['scientific_sha256']==sha(study/b/'SCIENTIFIC.json'),f'{b}: SCIENTIFIC does not match SEAL')
    stop=opt(study/'STOP_010.json');stop_o=opt(study/'STOP_010_ORCHESTRATOR.json');done=opt(study/'RUN_DONE_010.json')
    state=opt(study/'RUN_STATE_010.json') or {'stopped':{},'spent':{},'completed_at':{}}
    t0=float((study/'RUN_T0').read_text().split()[0]) if (study/'RUN_T0').exists() else None
    paired=opt(study/'PAIRED_ANALYSIS_010.json');repro=opt(study/'REPRODUCIBILITY_010.json')
    aud={b:opt(study/f'SECOND_IMPLEMENTATION_010_{b}.json') for b in ('2x2','breadth')}
    xc=opt(study/'XCHECK_010.json');xs=opt(study/'XCHECK_SPOT_010.json');ts=opt(study/'TEST_SUITE_010.json')
    top=opt(study/'SEAL.json');drill=opt(study/'KILL_DRILL_010.json');replay=opt(ROOT/'results/study-010/DIAG_REPLAY_009.json')
    stopped=state.get('stopped',{});fired=stop is not None or stop_o is not None
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
    def reason(why):return None if not why else ('STUDY_BUDGET' if fired else 'INCOMPLETE_INPUT')+' ('+'; '.join(why)+')'
    tau6,tau7=plan['tau6']['value'],plan['tau7']['value'];eps=view['open_world_reserve_epsilon'];W=view['window_W']
    two=blk['2x2']['cases'] if blk['2x2'] else [];br=blk['breadth']['cases'] if blk['breadth'] else []
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
    blocks=[(two,IF,OOF,SOUND2),(br,IB,OB,SOUND_B)]
    w_all=incomplete(('2x2','breadth'));w2=incomplete(('2x2',))
    # G1
    g1={}
    for cs,inf,_,arms in blocks:
        for f in inf:
            if fam(cs,f):g1[f]={a:tally(fam(cs,f),a) for a in arms}
    g1arm={a:all(g1[f][a]['false_certs']==0 and g1[f][a]['public_false_certs']==0 for f in g1 if a in g1[f]) for a in SOUND2+SOUND_B}
    gate('G1_in_family_soundness',all(g1arm.values()),{'per_arm_pass':g1arm,'per_family':g1},why=w_all)
    # G2
    g2={'ood5':{a:tally(fam(two,'ood5'),a) for a in SOUND2},'ood6s3':{a:tally(fam(br,'ood6s3'),a) for a in SOUND_B}}
    g2arm={a:g2['ood5'][a]['false_certs']==0 for a in SOUND2};g2arm.update({a:g2['ood6s3'][a]['false_certs']==0 for a in SOUND_B})
    gate('G2_ood_soundness',all(g2arm.values()),{'per_arm_pass':g2arm,**g2,'prediction':C['G2_ood_soundness']['prediction']},why=w_all)
    # G3'
    D=fam(two,'drift4');v090=sum(bool(r['v090_wrong']) for c in D for r in c['arms']['A4']['trace']);limit=0.5*v090;g3={}
    for a in SOUND2:
        tr=[(c,r) for c in D for r in c['arms'][a]['trace']]
        tot=sum(bool(r['wrong']) for _,r in tr);nd=sum(bool(r['wrong']) and nondrift(r['step']) for _,r in tr)
        g3[a]={'false_certs_taken':tot,'false_certs_non_drift':nd,'non_drift_zero':nd==0,'total_within_limit':tot<=limit,
               'reported_counterfactual_false':sum(bool(r['counterfactual']['wrong']) for _,r in tr),
               'reported_counterfactual_false_non_drift':sum(bool(r['counterfactual']['wrong']) and nondrift(r['step']) for _,r in tr)}
        g3[a]['pass']=g3[a]['non_drift_zero'] and g3[a]['total_within_limit']
    g3['SC7']['role']='reported (comparator), not gated'
    gate('G3_prime_drift4',all(g3[a]['pass'] for a in NEW2),{'v090_control_false_certs':v090,'limit':limit,'drift_cases':len(D),**g3,
         'per_arm_pass':{a:g3[a]['pass'] for a in NEW2},'definition':plan['drift_definition'],'prediction':C['G3_prime_drift4']['prediction']},why=w2)
    # G6b
    g6={}
    if paired:
        for a in NEW2:
            P=paired[f'G6b_dual_coverage_{a}_minus_A2'];g6[a]={'pooled_gain':P['pooled_gain'],'pooled_ci95':P['pooled_ci95'],
                'a_pooled_ge_-0.03':P['pooled_gain']>=-0.03,'b_ci_lower_ge_-0.05':P['pooled_ci95'][0]>=-0.05,'families':P['families']}
            g6[a]['pass']=g6[a]['a_pooled_ge_-0.03'] and g6[a]['b_ci_lower_ge_-0.05']
    gate('G6b_coverage_vs_v020',bool(g6) and all(v['pass'] for v in g6.values()),{**g6,'per_arm_pass':{a:v['pass'] for a,v in g6.items()},
         'reported_SC7_minus_A2':paired and paired['R_dual_coverage_SC7_minus_A2']['pooled_gain'],
         'reported_SP8_minus_SC7':paired and {k:paired['R_SP8_minus_SC7_in_family_original'][k] for k in ('pooled_gain','pooled_ci95')},
         'prediction':C['G6b_coverage_vs_v020']['prediction']},why=w2+incomplete(files=(('PAIRED_ANALYSIS_010.json',paired),)))
    # GA1_010
    ga={a:{'G1':all(g1[f][a]['false_certs']==0 and g1[f][a]['public_false_certs']==0 for f in g1 if a in g1[f]),'G2':g2arm[a],
           'G3_prime':g3[a]['pass'],'G6b':bool(g6) and g6[a]['pass']} for a in NEW2}
    for a in NEW2:ga[a]['all']=all(ga[a].values())
    gate('GA1_010_align_drift_and_coverage',any(ga[a]['all'] for a in NEW2),{'per_arm':ga,'passing_arms':[a for a in NEW2 if ga[a]['all']],
         'note':'FAIL means the drift-and-coverage target is NOT met even if G3-prime and G6b are each passed by a DIFFERENT arm',
         'prediction':C['GA1_010_align_drift_and_coverage']['prediction']},why=w2+incomplete(files=(('PAIRED_ANALYSIS_010.json',paired),)))
    # GD
    gd=GDS.run([study/'2x2'/'SCIENTIFIC.json'],['SC7','SP8'],'J8') if blk['2x2'] else None
    gdr=None
    if gd and not gd['clause_i']['evaluable']:gdr='INSUFFICIENT_EVENTS'
    gd_obs=None if gd is None else {'clause_i':gd['clause_i'],'nd_false_total':gd['nd_false_total'],'stale_class':gd['stale_class'],
        'fraction':gd['fraction'],'by_arm':gd['by_arm'],'clause_ii':gd['clause_ii'],'false_certificates':gd['false_certificates'],
        'scored_fail_reason':gdr,'prediction':C['GD_stale_cause_diagnostic']['prediction']}
    gate('GD_stale_cause_diagnostic',bool(gd) and gd['GD_pass'],gd_obs,why=w2)
    # G4
    pub_oof={}
    for cs,_,oof,arms in blocks:
        for f in oof:pub_oof[f]={a:tally(fam(cs,f),a)['public_certs'] for a in arms}
    pub_wrong=sum(tally(cs,a)['public_false_certs'] for cs,_,_,arms in blocks for a in arms)
    after=sum(1 for cs,_,_,arms in blocks for c in cs for a in arms for r in c['arms'][a]['trace']
              if c['arms'][a]['diagnostics'].get('first_alarm_step') is not None and r['step']>c['arms'][a]['diagnostics']['first_alarm_step']
              for q in fcs(r) if q['public_certificate'] is not None)
    g4={'a_no_public_on_ood5_drift4_ood6s3':all(v==0 for f in pub_oof for v in pub_oof[f].values()),'b_no_wrong_public':pub_wrong==0,'c_no_public_after_first_alarm':after==0}
    gate('G4_public_safety',all(g4.values()),{'clauses':g4,'public_certs_out_of_family':pub_oof,'public_false_certs':pub_wrong,'public_after_first_alarm':after},why=w_all)
    # G5
    g5={}
    for cs,inf,arms in ((two,IF,NEW2),(br,IB,('BSP8',))):
        for f in inf:
            cc=fam(cs,f)
            if not cc:continue
            g5[f]={a:{'cases':len(cc),'cases_with_alarm':sum(c['arms'][a]['diagnostics'].get('first_alarm_step') is not None for c in cc)} for a in arms}
            for v in g5[f].values():v['fraction']=round(v['cases_with_alarm']/v['cases'],6)
    gate('G5_false_alarm_limit',bool(g5) and all(v['fraction']<=0.05 for f in g5 for v in g5[f].values()),{'tau6':tau6,'tau7':tau7,'per_family':g5,
         'prediction':C['G5_false_alarm_limit']['prediction']},why=w_all)
    # G7
    def mean_ll(cs,a):
        v=[r['logloss'] for c in cs for r in c['arms'][a]['trace'][c['burn_in']:]];return round(sum(v)/len(v),6) if v else None
    ll={'ood5':{a:mean_ll(fam(two,'ood5'),a) for a in NEW2},'drift4':{a:mean_ll(fam(two,'drift4'),a) for a in NEW2},
        'ood6s3':{'BSP8':mean_ll(fam(br,'ood6s3'),'BSP8')}}
    minp_bad=[];minp={}
    for cs,arms in ((two,('J8','SP8','SC7','A4')),(br,SOUND_B)):
        for c in cs:
            thr=round(eps/2**c.get('s',2),12)
            for a in arms:
                if a not in c['arms'] or not c['arms'][a]['trace'] or 'min_probability' not in c['arms'][a]['trace'][0]:continue
                mp=min(r['min_probability'] for r in c['arms'][a]['trace']);k=f"{c['block']}/{c['family']}/{a}";minp[k]=min(minp.get(k,1),mp)
                if mp<thr-1e-12 and a in NEW2+('BSP8',):minp_bad.append({'family':c['family'],'seed':c['seed'],'mask_rate':c['mask_rate'],'arm':a,'min':mp,'threshold':thr})
    g7={'logloss_2x2_le_ln4':all(ll[f][a] is not None and ll[f][a]<=LN4 for f in ('ood5','drift4') for a in ll[f]),
        'logloss_ood6s3_le_ln8':ll['ood6s3']['BSP8'] is not None and ll['ood6s3']['BSP8']<=LN8,'min_probability':not minp_bad}
    gate('G7_open_world',all(g7.values()),{'clauses':g7,'logloss_post':ll,'ln4':LN4,'ln8':LN8,'eps':eps,'min_probability_by_block_family_arm':minp,'violations':minp_bad[:20]},why=w_all)
    # G9
    resumes=0;resume_bad=[];resync=0;reasons_ok=True;totals={};dups=0;bad_reason=[]
    for cs,arms,tau,breadth in ((two,NEW2,tau6,False),(br,('BSP8',),tau7,True)):
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
    have={'2x2':len(two),'breadth':len(br)};steps={'2x2':plan['actions_per_case_2x2'],'breadth':plan['actions_per_case_breadth']}
    short=[f"{c['block']}/{c['family']}/{c['seed']}/{c['mask_rate']}/{a}" for b,cs in (('2x2',two),('breadth',br)) for c in cs
           for a in c['arms'] if len(c['arms'][a]['trace'])!=steps[b]]
    unk_rate={}
    for name,cs,arms in (('2x2',two,NEW2),('breadth',br,('BSP8',))):
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
    g11={};g11_why=[]
    for b in ('2x2','breadth'):
        A=aud[b];sn=f'g11_{b}'
        if A is None:g11_why.append(f'SECOND_IMPLEMENTATION_010_{b}.json missing');continue
        st=str(stopped.get(sn,''))
        if st.startswith(('STUDY_BUDGET','exit code')):g11_why.append(f'{sn} stream stopped: {st}')
        md=A.get('events',{}).get('mandatory_done')
        g11[b]={'i_mandatory_complete_zero_mismatch':bool(A.get('mandatory_complete')) and bool(A.get('mandatory_samples_present')) and A['mandatory']['mismatching_traces']==0,
                'ii_rest_zero_mismatch':A.get('rest',{}).get('mismatching_traces',0)==0,
                'iv_mandatory_inside_budget':md is not None and md['wall_since_start']<=G11_BUDGET,
                'of_sealed_results':seal[b] is not None and A.get('results_sha256')==seal[b]['results_sha256']}
        if b=='2x2':
            mt=A.get('mutation_test') or {}
            g11[b]['iii_mutation_20_of_20']=bool(mt.get('passed')) and mt.get('injected')==20 and mt.get('detected_injected')==20 and mt.get('flagged_not_injected')==0 \
                and (mt.get('injected_j8_cert_or_hull_fields') or 0)>=4 and (mt.get('injected_sp8_action') or 0)>=4
    gate('G11_second_implementation',len(g11)==2 and all(all(v.values()) for v in g11.values()),{'clauses':g11,
         'reports':{b:None if aud[b] is None else {k:aud[b][k] for k in aud[b] if k not in ('mismatches',)} for b in aud},
         'wording':'second implementation by the same author'},why=g11_why+incomplete(('2x2','breadth')))
    # G12
    g12ok=bool(repro) and repro['G12_pass'] and all(repro['blocks'][b]['main_scientific_sha256']==seal[b]['scientific_sha256'] for b in repro['blocks'])
    gate('G12_reproducibility',g12ok,None if repro is None else repro['blocks'],
         why=w_all+incomplete(files=(('REPRODUCIBILITY_010.json',repro),),streams=('repro_2x2','repro_breadth')))
    # G13
    try:check_freeze();fz=True;fz_err=None
    except Exception as exc:fz=False;fz_err=f'{type(exc).__name__}: {exc}'
    taus=sorted({c.get('tau6') for c in two})+sorted({c.get('tau') for c in br})
    g13={'freeze_chain_holds':fz,'plan_tau_values':tau6==TAU6 and tau7==TAU7,
         'cases_use_plan_tau':all(c.get('tau6')==tau6 for c in two) and all(c.get('tau')==tau7 for c in br),
         'seals_of_current_plan_and_freeze':all(s['plan_sha256']==sha(PLAN) and FREEZE.exists() and s['freeze_sha256']==sha(FREEZE) for s in seal.values() if s)}
    g13ok=all(g13.values()) if not smoke else (g13['plan_tau_values'] and g13['cases_use_plan_tau'])
    gate('G13_frozen_controls_reproduce',g13ok,{'clauses':g13,'freeze_error':fz_err,'recorded_taus':taus,'smoke_dry_run_relaxed':smoke},
         why=incomplete(('2x2','breadth')) if any(s is None for s in seal.values()) else None)
    # GX2_010
    fr={f'{f}/{a}':((xc or {}).get('per_family_arm',{}).get(f'{f}/{a}') or {}).get('checked_fraction') for f in XFAM for a in XARMS}
    spot_steps=(xs or {}).get('checked_steps_per_family',{})
    gx_why=incomplete(('breadth',),files=(('XCHECK_010.json',xc),('XCHECK_SPOT_010.json',xs)),streams=('gx2_spot',))
    gx={}
    if xc:
        gx={'i_zero_mismatching_and_witness':xc['mismatching_traces']==0 and xc['witness_replay_failures']==0,
            'i_covers_every_breadth_case':xc['cases_expected']==len(br) and xc['cases_done']==len(br),
            'ii_checked_ge_0.99_each':all(v is not None and v>=0.99 for v in fr.values()),
            'iii_symmetric_inside_budget':'gx2_sym' not in stopped and 'gx2_sym' in state.get('completed_at',{})}
    if xs:
        gx['iv_spot_zero_mismatching_and_witness']=xs['mismatching_traces']==0 and xs['witness_replay_failures']==0
        gx['iv_spot_ge_64_steps_act3_sens3']=all((spot_steps.get(f) or 0)>=64 for f in ('act3','sens3'))
    gate('GX2_010_incremental_xcheck',len(gx)==6 and all(gx.values()),{'clauses':gx,'checked_fraction':fr,
         'per_family_arm':(xc or {}).get('per_family_arm'),'symmetric_spent_s':state.get('spent',{}).get('gx2_sym'),
         'symmetric_stop':stopped.get('gx2_sym'),'mismatches':(xc or {}).get('mismatches',[])[:50],'queries':(xc or {}).get('queries'),
         'unknown_queries':(xc or {}).get('unknown_queries'),'witness_replay_failures':(xc or {}).get('witness_replay_failures'),
         'spot':None if xs is None else {k:xs[k] for k in xs if k not in ('mismatches',)},'wording':(xc or {}).get('wording'),
         'prediction':C['GX2_010_incremental_xcheck']['prediction']},why=gx_why)
    # GTI (in-cap)
    V=(ts or {}).get('verdict')
    gate('GTI_test_isolation',bool(V) and V['passed'],None if ts is None else {'verdict':V,'head':ts.get('head'),'tracked_tree_dirty':ts.get('tracked_tree_dirty'),
         'clean_tag_runs':ts.get('clean_tag_runs'),'run':'in-cap'},why=incomplete(files=(('TEST_SUITE_010.json',ts),),streams=('gti',)))
    # G_RT
    hb=heartbeat(study);comp=state.get('completed_at',{})
    end=(t0+done['elapsed_s']) if (t0 is not None and done) else (t0+CAP if t0 is not None else None)
    late={s:(round(comp[s]-t0,1) if s in comp else None) for s in STREAMS} if t0 is not None else {}
    rt={'i_every_stream_completed_inside_cap':t0 is not None and all(v is not None and v<=CAP for v in late.values()) and not stopped,
        'ii_watchdog_whole_run':bool(hb) and t0 is not None and hb['first_wall']<=t0+60 and hb['last_wall']>=end-10,
        'iii_kill_drill_latency_le_15s':bool(drill) and drill.get('kill_latency_s') is not None and drill['kill_latency_s']<=15 and not drill.get('survivors')}
    g['G_RT_study_runtime']={'gated':True,'pass':all(rt.values()),'observed':{'clauses':rt,'completion_s_after_t0':late,'stopped_streams':stopped,
         'stop_watchdog':stop,'stop_orchestrator':stop_o,'run_done':done,'heartbeat':hb,'kill_drill':drill,
         'spent_s':{k:round(v) for k,v in state.get('spent',{}).items()},'cap_s':CAP},
         **({} if all(rt.values()) else {'reason':'STUDY_BUDGET' if fired else 'clauses failed: '+', '.join(k for k,v in rt.items() if not v)})}
    # ---- non-gated reports
    gate('R_diag_replay_009',None,None if replay is None else {k:v for k,v in replay.items() if k not in ('false_certificates',)},gated=False)
    vs={}
    if paired:vs={k:{x:paired[k][x] for x in ('pooled_gain','pooled_ci95')} for k in ('R_SP8_minus_SC7_in_family_original','R_SP8_minus_SC7_in_family')}
    vs['drift4_taken_false']={a:sum(bool(r['wrong']) for c in D for r in c['arms'][a]['trace']) for a in ALL2 if D}
    vs['drift4_taken_false_non_drift']={a:sum(bool(r['wrong']) and nondrift(r['step']) for c in D for r in c['arms'][a]['trace']) for a in ALL2 if D}
    gate('R_SP8_vs_SC7',None,vs,gated=False)
    gate('R_BSP8_vs_BSC7',None,None if not paired else {x:paired['R_BSP8_minus_BSC7'][x] for x in ('pooled_gain','pooled_ci95','families')},gated=False)
    jc={}
    for c in two:
        x=jc.setdefault(c['family'],{'cases':0,'post_forecasts':0,'post_certs':0,'hull_steps':0,'hull_all_codes':0,'hull_downgrades':0})
        x['cases']+=1;x['hull_downgrades']+=c['arms']['J8']['diagnostics'].get('hull_downgrades') or 0
        for r in c['arms']['J8']['trace'][c['burn_in']:]:x['post_forecasts']+=2;x['post_certs']+=(r['certificate'] is not None)+(r['counterfactual']['certificate'] is not None)
        for r in c['arms']['J8']['trace']:
            H=r.get('hull_union')
            if H is not None:x['hull_steps']+=1;x['hull_all_codes']+=all(len(v)>=4 for v in H.values())
    for x in jc.values():
        x['coverage']=round(x['post_certs']/x['post_forecasts'],6) if x['post_forecasts'] else None
        x['fraction_hull_all_codes']=round(x['hull_all_codes']/x['hull_steps'],6) if x['hull_steps'] else None
    gate('R_J8_coverage',None,jc,gated=False)
    det=[]
    for c in D:
        for a in ALL2:
            ev=set(c['arms'][a]['diagnostics'].get('drift_events') or [])
            for r in c['arms'][a]['trace']:
                for side,q in (('taken',r),('counterfactual',r.get('counterfactual'))):
                    if q and q.get('wrong'):
                        last=max([x for x in DRIFT if x<=r['step']],default=None);d=max([x for x in DRIFT if x<r['step']],default=None)
                        det.append({'arm':a,'seed':c['seed'],'mask_rate':c['mask_rate'],'step':r['step'],'action':side,'public':bool(q.get('public_wrong')),
                                    'steps_after_last_drift':None if last is None else r['step']-last,'non_drift':nondrift(r['step']),
                                    'event_at_d':None if d is None or a in ('A2','A4') else d in ev})
    gate('R_drift_detail',None,{'false_certificates':det,'count_by_arm':{a:sum(x['arm']==a for x in det) for a in ALL2}},gated=False)
    gate('R_heartbeat',None,hb,gated=False)
    budgets={'2x2':1500,'breadth':2400,'gti':2400,'g11_2x2':1500,'repro_2x2':900,'gx2_sym':1200,'gx2_spot':1200,'g11_breadth':1500,'repro_breadth':1500}
    gate('R_rates',None,{s:{'spent_s':round(state.get('spent',{}).get(s,0),1),'budget_s':budgets[s],'fraction_of_budget':round(state.get('spent',{}).get(s,0)/budgets[s],3)} for s in budgets},gated=False)
    gate('R_tests_plain',None,None if ts is None else ts.get('plain_discover'),gated=False)
    gated=[k for k,v in g.items() if v['gated']]
    return {'schema':'brute.gates.v8_0','study':plan['study'],'plan_sha256':sha(PLAN),'smoke_dry_run':smoke,
            'scientific_sha256':{b:s['scientific_sha256'] for b,s in seal.items() if s},'study_seal_present':top is not None,
            'stop_rule_fired':fired,'gates':g,
            'passed':[k for k in gated if g[k]['pass']],'failed':[k for k in gated if g[k]['pass'] is False],
            'pending':[k for k in gated if g[k]['pass'] is None],'all_gated_pass':all(g[k]['pass'] for k in gated),
            'GA1_010':g['GA1_010_align_drift_and_coverage']['pass'],'GD':g['GD_stale_cause_diagnostic']['pass'],
            'GX2_010':g['GX2_010_incremental_xcheck']['pass'],'GTI_in_cap':g['GTI_test_isolation']['pass'],'G_RT':g['G_RT_study_runtime']['pass']}


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--study-dir',default=str(STUDY_DIR));ap.add_argument('--check',action='store_true')
    ap.add_argument('--output',default='GATES_010.json');ap.add_argument('--smoke',action='store_true',help='dry run on a smoke directory; prints only')
    a=ap.parse_args()
    if a.smoke:
        obj=build(Path(a.study_dir),smoke=True)
        print({k:obj[k] for k in ('passed','failed','pending')});print({k:v.get('reason') for k,v in obj['gates'].items() if v.get('reason')});raise SystemExit
    obj=build(Path(a.study_dir));out=Path(a.study_dir)/a.output
    if a.check:check(out.read_bytes()==dumps(obj),out.name+' does not reproduce');print(out.name,'reproduces')
    else:write_new(out,obj);print({k:obj[k] for k in ('passed','failed','pending','all_gated_pass')})
