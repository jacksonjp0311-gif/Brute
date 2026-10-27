"""Gates for study-019 (BRUTE_PLAN_019 criteria; adapted from make_gates_018, frozen). Committed and ledgered
(scoring_freeze_019) before the held-out run_start; nothing is tuned after results are seen.

Inputs (study dir D = results/study-019): D/transfer/{SCIENTIFIC,SEAL}.json (576 cases = 360 main + 120 stress + 96
alphabet3), D/PAIRED_ANALYSIS_019.json, D/REPRODUCIBILITY_019.json, D/SECOND_IMPLEMENTATION_019.json, D/TEST_SUITE_019.json,
D/RUN_STATE_019.json, D/RUN_T0, D/HEARTBEAT_019.jsonl, D/KILL_DRILL_019.json (or results/smoke-019/ under --smoke),
optional D/STOP_019*.json, D/RUN_DONE_019.json, D/HEARTBEAT_ATTRIBUTION_019.json, D/transfer/RESULTS.json (timing only).

Gated (plan criteria, one entry each):
  GNB_sequential_margin   (a) RGNB4 0 false (recorded and recomputed) on every noisy main case without a crossing;
                          (b) CP95 upper of RGNB4 case-false over the noisy main cases <= 0.05; (c) dC_RGNB4_RGN4_eps2 CI lower > 0;
                          (d) C_RGNB4_eps2 mean >= 0.10 and CI lower > 0.05 (both from PAIRED_ANALYSIS_019).
  GNB_post_burn_control   eps-0 main cases: RGNB4_0 certificates == RG4 certificates at every step > burn_in, and RGNB4 0 false.
  GA3_alphabet3_soundness RG4_3 0 false on the eps-0 alphabet3 cases; RGNB4_3 0 false on every eps-0.02 alphabet3 case without a
                          crossing; CP95 upper of RGNB4_3 case-false at eps 0.02 <= 0.10.
  GS_a7_soundness         RG4 0 false on the eps-0 main cases.
  G_recount               every arm's false count recomputed from its trace against the evaluator truth (main: SP8 trace truth;
                          alphabet3: truth_EVALUATOR_ONLY), wrong flags, certificate counts, summary, case_false, coverage; plus
                          realized_flips == |flip positions| and crossing == (crossing_bit is not None).
  GS_ref7_reference_audit SECOND_IMPLEMENTATION_019 results sha == transfer seal, every gated case audited (main eps 0 and 0.02 +
                          every alphabet3 case), 0 gated mismatches, mutation 20/20.
  GAPI7_certify7          test_api_certify7_0170.py ok inside GTI (>= 4 tests), brute/api/certify7.py in the source freeze,
                          soundness probe == {'kind': 'probabilistic', 'delta': 0.01, 'conditional_on': 'running flips <= m(b) and n* <= family_bound'}.
  G10_compute             576 cases, seal complete, every trace 44 steps, unknown > 0 fraction <= 1% for every support kind.
  G12_reproducibility     REPRODUCIBILITY_019 G12_pass, 152 expected, main sha == transfer seal.
  G13_frozen_controls_reproduce freeze chain holds; tau6; RG4 recomputed by the frozen v0.12.0 rg_arm on every main and stress
                          case; RGN4 certificates recomputed from the recorded RGN4 supports by the frozen study-018 rgn_arm on every
                          main and stress case; seal binds the current plan and freeze.
  GTI_test_isolation      TEST_SUITE_019 verdict passed and tracked tree clean at GTI start (deviation #100 item 1).
  G_RT_study_runtime      as study-018 (streams inside the 7,200 s cap, not stopped; watchdog whole run; kill drill <= 15 s).
  G_HB_heartbeat_gap      max heartbeat gap <= 30 s.
A gate whose inputs are missing or incomplete FAILS with reason INCOMPLETE_INPUT (STUDY_BUDGET if a stop fired).
Reports (non-gated): R_gn0_full, R_boundary, R_RG4_noise, R_stress, R_oracle, R_bound, R_alphabet3_coverage, R_rates,
R_heartbeat_attribution.
  PYTHONPATH=. python scripts/make_gates_019.py [--study-dir D] [--check] [--smoke]"""
from __future__ import annotations
import argparse,json,math,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common_019 import STUDY_DIR,PLAN,FREEZE,load,dumps,write_new,check,sha,check_freeze,TAU6
from experiments.brute_study_014 import sp8_steps
import experiments.brute_study_014 as S14
import experiments.brute_study_018 as S18
import experiments.brute_study_019 as S19
from scripts.make_gates_015 import wrong,opt
from scripts.make_gates_018 import cp_upper,p_exceed
from scripts.run_study_019 import STREAMS as RUN_STREAMS,CAP

STEPS=44;FB=4;CENSOR=45;SLOTS=88;SLOTS3=132;K3=3;EXPECTED={'main':360,'stress':120,'alphabet3':96};REPRO_EXPECTED=152
ARMS=('RG4','RGN4','RGNB4','RGNB4_0','RGN4_or');ALL_ARMS=('SP8',)+ARMS;A3_ARMS=('RG4_3','RGN4_3','RGNB4_3')
STREAMS=('transfer','repro','gti','g11');BUDGETS={k:v[1] for k,v in RUN_STREAMS.items()}
FAMILIES=('cycle3','switch3','unaliased2','ood4');EPS=(0.0,0.01,0.02,0.05);EPS_A3=(0.0,0.02)
API_EXPECT={'kind':'probabilistic','delta':0.01,'conditional_on':'running flips <= m(b) and n* <= family_bound'}


def ck(c):return f"{c['block']}/{c['family']}/{c['seed']}/{c['eps']}"
def is_a3(c):return c.get('schema')=='brute.case3.v17_0'
def is_main(c):return not is_a3(c) and c['eps'] in (0.0,0.01,0.02)
def is_noisy(c):return c['eps'] in (0.01,0.02)


def beats(d,t0):
    p=Path(d)/'HEARTBEAT_019.jsonl'
    if not p.exists():return []
    R=[json.loads(l) for l in p.read_text().splitlines() if l.strip()]
    return [r for r in R if t0 is None or r['wall']>=t0]


def heartbeat(d,t0):
    R=beats(d,t0)
    if not R:return None
    gaps=[];att=[]
    for a,b in zip(R,R[1:]):
        g=round(b['wall']-a['wall'],3);gaps.append(g)
        if g>10:
            dl=lambda k:None if a.get(k) is None or b.get(k) is None else round(b[k]-a[k],3)
            att.append({'wall_from':a['wall'],'gap_s':g,'d_monotonic':dl('monotonic'),'d_boottime':dl('boottime'),'d_cpu_s':dl('cpu_s'),
                        'd_psi_io_some_us':dl('psi_io_some_us'),'d_psi_io_full_us':dl('psi_io_full_us')})
    return {'beats':len(R),'first_wall':R[0]['wall'],'last_wall':R[-1]['wall'],'max_gap_s':max(gaps) if gaps else None,'gaps_over_10s':att}


def actual(c):return c['truth_EVALUATOR_ONLY'] if is_a3(c) else [s[5] for s in sp8_steps(c)]
def arms_of(c):return A3_ARMS if is_a3(c) else ARMS
def k_of(c):return K3 if is_a3(c) else 2


def _wrong(tr,act,k):return sum(1 for i,r in enumerate(tr) for b in range(k) if r['certificate'][b] is not None and r['certificate'][b]!=act[i][b])


def recount(c,act):
    """[(arm, recorded, recomputed, wrong_flags_ok)] for one case, every arm."""
    k=k_of(c);out=[]
    if not is_a3(c):
        S=sp8_steps(c)
        out.append(('SP8',c['summary']['false']['SP8'],sum(cert[b] is not None and cert[b]!=act[i][b] for i,(t,a,cert,_,_,_) in enumerate(S) for b in (0,1)),True))
    for arm in arms_of(c):
        A=c['certifiers'][arm]
        flags=all(len(r['certificate'])==k and r['wrong'][b]==(r['certificate'][b] is not None and r['certificate'][b]!=act[i][b]) for i,r in enumerate(A['trace']) for b in range(k)) if A['trace'] and 'wrong' in A['trace'][0] else True
        re=wrong(A['trace'],act) if k==2 else _wrong(A['trace'],act,k)
        out.append((arm,A['false_certificates'],re,flags))
    return out


def cert_counts(c):
    bad=[];Sm=c['summary'];slots=SLOTS3 if is_a3(c) else SLOTS
    for arm in arms_of(c):
        A=c['certifiers'][arm];n=sum(x is not None for r in A['trace'] for x in r['certificate'])
        if A['certificates']!=n:bad.append((arm,'trace',A['certificates'],n))
        if Sm['certificates'].get(arm)!=A['certificates']:bad.append((arm,'summary',Sm['certificates'].get(arm),A['certificates']))
        if Sm['false'].get(arm)!=A['false_certificates']:bad.append((arm,'summary_false',Sm['false'].get(arm),A['false_certificates']))
        if Sm['coverage'].get(arm)!=round(A['certificates']/slots,6):bad.append((arm,'coverage',Sm['coverage'].get(arm),A['certificates']))
    if not is_a3(c):
        sp=sum(cert[b] is not None for t,a,cert,_,_,_ in sp8_steps(c) for b in (0,1))
        if Sm['certificates'].get('SP8')!=sp:bad.append(('SP8','summary',Sm['certificates'].get('SP8'),sp))
    for arm in ((() if is_a3(c) else ('SP8',))+arms_of(c)):
        if Sm['case_false'].get(arm)!=(Sm['false'].get(arm,0)>0):bad.append((arm,'case_false',Sm['case_false'].get(arm),Sm['false'].get(arm)))
    if c['realized_flips']!=len(c['flip_positions_EVALUATOR_ONLY']):bad.append(('noise','realized_flips',c['realized_flips'],len(c['flip_positions_EVALUATOR_ONLY'])))
    if c['crossing']!=(c['crossing_bit'] is not None):bad.append(('noise','crossing',c['crossing'],c['crossing_bit']))
    return bad


def sup(c,arm):
    X=c['regions'] if is_a3(c) else c['noisy'];x=X[arm]
    return X[x['shared_with']] if x.get('shared_with') and x.get('support') is None else x


def certs(c,arm):return [r['certificate'] for r in c['certifiers'][arm]['trace']]


def api_soundness():
    try:
        from brute.api.certify7 import certify7
        r=certify7((0,1),[0,1],[(0,1),(1,None)],5);s=r.get('soundness')
        return {'soundness':s,'matches':s is not None and all(s.get(k)==v for k,v in API_EXPECT.items()),'error':None}
    except Exception as e:return {'soundness':None,'matches':False,'error':f'{type(e).__name__}: {e}'}


def build(study=STUDY_DIR,smoke=False):
    study=Path(study);plan=load(PLAN);C=plan['criteria']
    blk=opt(study/'transfer'/'SCIENTIFIC.json');seal=opt(study/'transfer'/'SEAL.json')
    if blk is not None:check(seal['scientific_sha256']==sha(study/'transfer'/'SCIENTIFIC.json'),'transfer: SCIENTIFIC does not match SEAL')
    stop=opt(study/'STOP_019.json');stop_o=opt(study/'STOP_019_ORCHESTRATOR.json');done=opt(study/'RUN_DONE_019.json')
    state=opt(study/'RUN_STATE_019.json') or {'stopped':{},'spent':{},'completed_at':{}}
    t0=float((study/'RUN_T0').read_text().split()[0]) if (study/'RUN_T0').exists() else None
    paired=opt(study/'PAIRED_ANALYSIS_019.json');repro=opt(study/'REPRODUCIBILITY_019.json')
    aud=opt(study/'SECOND_IMPLEMENTATION_019.json');ts=opt(study/'TEST_SUITE_019.json');drill=opt(study/'KILL_DRILL_019.json')
    if smoke and drill is None:drill=opt(ROOT/'results/smoke-019/KILL_DRILL_019.json')
    stopped=state.get('stopped',{});fired=stop is not None or stop_o is not None;g={}
    exp=({'main':24,'stress':8,'alphabet3':8} if smoke else EXPECTED);expected=sum(exp.values())
    allc=blk['cases'] if blk else [];a3=[c for c in allc if is_a3(c)];mc=[c for c in allc if not is_a3(c)]
    main=[c for c in mc if is_main(c)];stress=[c for c in mc if c['eps']==0.05];msx=main+stress
    noisy=[c for c in main if is_noisy(c)];e0=[c for c in main if c['eps']==0.0]
    a30=[c for c in a3 if c['eps']==0.0];a32=[c for c in a3 if c['eps']==0.02]
    def incomplete(block=True,files=(),streams=()):
        why=[]
        if block:
            if blk is None:why.append('transfer block missing')
            elif not blk.get('complete') or len(allc)!=expected or (len(main),len(stress),len(a3))!=(exp['main'],exp['stress'],exp['alphabet3']):
                why.append(f'transfer block incomplete ({len(allc)}/{expected} cases: main {len(main)}, stress {len(stress)}, alphabet3 {len(a3)})')
            if 'transfer' in stopped:why.append('transfer stream stopped: '+str(stopped['transfer']))
        for name,obj in files:
            if obj is None:why.append(name+' missing')
        for s in streams:
            if s in stopped:why.append(f'{s} stream stopped: {stopped[s]}')
        return why
    def reason(why):return None if not why else ('STUDY_BUDGET' if fired else 'INCOMPLETE_INPUT')+' ('+'; '.join(why)+')'
    def gate(name,ok,obs,gated=True,why=None):
        r=reason(why or [])
        if r:g[name]={'gated':True,'pass':False,'reason':r,'observed_on_available_inputs':obs};return
        g[name]={'gated':gated,'pass':(bool(ok) if ok is not None else None) if gated else None,'observed':obs}
    wb=incomplete();ACT={id(c):actual(c) for c in allc};RC={}
    # G_recount
    tot={};bad_rc=[];bad_cc=[];bad_fl=[]
    for c in allc:
        sub='alphabet3' if is_a3(c) else 'stress' if c['eps']==0.05 else 'main'
        for arm,rec,re,fl in recount(c,ACT[id(c)]):
            RC[(id(c),arm)]=re
            x=tot.setdefault(sub,{}).setdefault(arm,{'recorded_false':0,'recomputed_false':0,'records':0,'mismatching_records':0})
            x['recorded_false']+=rec;x['recomputed_false']+=re;x['records']+=1
            if rec!=re:x['mismatching_records']+=1;bad_rc.append((ck(c),arm,rec,re))
            if not fl:bad_fl.append((ck(c),arm))
        bad_cc+=[(ck(c),)+b for b in cert_counts(c)]
    cover=sorted(set(ALL_ARMS)-set(tot.get('main',{})))+sorted(set(A3_ARMS)-set(tot.get('alphabet3',{})))
    gate('G_recount',not bad_rc and not bad_cc and not bad_fl and bool(allc) and not cover,{'per_subset_arm':tot,'mismatches':bad_rc[:50],
         'wrong_flag_mismatches':bad_fl[:50],'certificate_count_mismatches':bad_cc[:50],'arms_not_recounted':cover},why=wb)
    zero=lambda cs,arm:all(c['certifiers'][arm]['false_certificates']==0 and RC[(id(c),arm)]==0 for c in cs)
    casefalse=lambda c,arm:RC[(id(c),arm)]>0
    P=paired or {}
    def pv(k):x=P.get(k) or {};return x.get('mean'),x.get('ci95')
    wp=wb+incomplete(False,files=(('PAIRED_ANALYSIS_019.json',paired),))
    # GNB (headline)
    nox=[c for c in noisy if not c['crossing']];k=sum(casefalse(c,'RGNB4') for c in noisy);ub=cp_upper(k,len(noisy))
    m2,ci2=pv('C_RGNB4_eps2');dm,dci=pv('dC_RGNB4_RGN4_eps2')
    gnb={'a_zero_false_without_crossing':bool(noisy) and zero(nox,'RGNB4'),'b_cp_upper_le_0.05':ub is not None and ub<=0.05,
         'c_dC_RGNB4_RGN4_eps2_ci_lower_gt_0':dci is not None and dci[0]>0,
         'd_C_eps2_mean_ge_0.10_ci_lower_gt_0.05':m2 is not None and m2>=0.10 and ci2 is not None and ci2[0]>0.05}
    gate('GNB_sequential_margin',all(gnb.values()),{'clauses':gnb,'noisy_cases':len(noisy),'cases_without_crossing':len(nox),
         'cases_with_crossing':len(noisy)-len(nox),'case_false':k,'case_false_examples':[ck(c) for c in noisy if casefalse(c,'RGNB4')][:20],
         'case_false_with_crossing':sum(casefalse(c,'RGNB4') for c in noisy if c['crossing']),
         'cp_upper_95_one_sided':ub,'C_RGNB4_eps2':(m2,ci2),'dC_RGNB4_RGN4_eps2':(dm,dci),'C_RGN4_eps2':pv('C_RGN4_eps2'),
         'C_RGNB4_eps1':pv('C_RGNB4_eps1'),'dC_RGNB4_RGN4_eps1':pv('dC_RGNB4_RGN4_eps1'),
         'false_certificates_RGNB4':sum(RC[(id(c),'RGNB4')] for c in noisy)},why=wp)
    # GNB_post_burn_control + R_gn0_full
    post=lambda c,arm:[x for r,x in zip(c['certifiers']['RG4']['trace'],certs(c,arm)) if r['step']>c['burn_in']]
    neq_post=[ck(c) for c in e0 if post(c,'RGNB4_0')!=post(c,'RG4')]
    steps_ok=all([r['step'] for r in c['certifiers']['RG4']['trace']]==[r['step'] for r in c['certifiers']['RGNB4_0']['trace']] for c in e0)
    gpb={'RGNB4_0_eq_RG4_after_burn_in':bool(e0) and steps_ok and not neq_post,'RGNB4_zero_false_eps0':bool(e0) and zero(e0,'RGNB4')}
    gate('GNB_post_burn_control',all(gpb.values()),{'clauses':gpb,'eps0_cases':len(e0),'cases_differing_after_burn_in':neq_post[:50],
         'RGNB4_false_eps0':sum(RC[(id(c),'RGNB4')] for c in e0)},why=wb)
    diff_slots=[(ck(c),r0['step'],b) for c in e0 for r0,r1 in zip(c['certifiers']['RG4']['trace'],c['certifiers']['RGNB4_0']['trace']) for b in (0,1) if r0['certificate'][b]!=r1['certificate'][b]]
    gate('R_gn0_full',None,{'eps0_cases':len(e0),'cases_differing_full_run':len({x[0] for x in diff_slots}),'differing_slots':diff_slots[:50],
         'differing_slots_in_burn_in':sum(1 for _,t,_ in diff_slots if t<=plan['burn_in']),'differing_slots_after_burn_in':sum(1 for _,t,_ in diff_slots if t>plan['burn_in']),
         'label':'expected to differ in burn-in by construction (#97 item 3)'},gated=False)
    # GA3
    a3x=[c for c in a32 if not c['crossing']];k3=sum(casefalse(c,'RGNB4_3') for c in a32);ub3=cp_upper(k3,len(a32))
    ga3={'RG4_3_zero_false_eps0':bool(a30) and zero(a30,'RG4_3'),'RGNB4_3_zero_false_without_crossing_eps2':bool(a32) and zero(a3x,'RGNB4_3'),
         'RGNB4_3_cp_upper_le_0.10':ub3 is not None and ub3<=0.10}
    gate('GA3_alphabet3_soundness',all(ga3.values()),{'clauses':ga3,'eps0_cases':len(a30),'eps2_cases':len(a32),'eps2_cases_without_crossing':len(a3x),
         'RGNB4_3_case_false_eps2':k3,'cp_upper_95_one_sided':ub3,'RG4_3_false_eps0':sum(RC[(id(c),'RG4_3')] for c in a30),
         'RG4_3_false_eps2_ungated':sum(RC[(id(c),'RG4_3')] for c in a32)},why=wb)
    # GS_a7
    gate('GS_a7_soundness',bool(e0) and zero(e0,'RG4'),{'eps0_cases':len(e0),'RG4_recorded_false':sum(c['certifiers']['RG4']['false_certificates'] for c in e0),
         'RG4_recomputed_false':sum(RC[(id(c),'RG4')] for c in e0)},why=wb)
    # GS_ref7
    md=(aud or {}).get('mutation_test') or {};ngated=sum(1 for c in main if c['eps'] in (0.0,0.02))+len(a3)
    ref={'results_sha_matches_seal':bool(aud) and bool(seal) and aud.get('results_sha256')==seal.get('results_sha256'),
         'all_gated_cases_audited':bool(aud) and aud.get('gated_cases_expected')==ngated and aud.get('gated_cases_audited')==ngated and ngated>0,
         'zero_gated_mismatching':bool(aud) and aud.get('gated_mismatching_cases')==0,
         'mutation_20_of_20':md.get('passed') is True and md.get('injected')==20 and md.get('distinct_cases')==20 and md.get('detected_injected')==20 and md.get('flagged_not_injected')==0}
    gate('GS_ref7_reference_audit',all(ref.values()),{'clauses':ref,'gated_expected':ngated,'report':None if aud is None else {k:aud[k] for k in aud if k not in ('mismatches','mutation_test','events')},
         'mutation':{k:v for k,v in md.items() if k!='details'},'wording':'second implementation by the same author'},
         why=wb+incomplete(False,files=(('SECOND_IMPLEMENTATION_019.json',aud),),streams=('g11',)))
    # GAPI7
    pm=((ts or {}).get('per_module') or {}).get('test_api_certify7_0170.py') or {};frz=opt(FREEZE) or {};asd=api_soundness()
    api={'module_ok':pm.get('returncode')==0 and len(pm.get('results') or {})>=4 and all(v[0]=='ok' for v in pm.get('results',{}).values()),
         'certify7_in_freeze':'brute/api/certify7.py' in frz.get('sha256_files',{}) or smoke,'soundness_dict':asd['matches']}
    gate('GAPI7_certify7',all(api.values()),{'clauses':api,'results':pm.get('results'),'soundness_probe':asd},why=incomplete(False,files=(('TEST_SUITE_019.json',ts),),streams=('gti',)))
    # G10
    tl={'SP8':all(len(c['arms']['SP8']['trace'])==STEPS for c in mc),**{a:all(len(c['certifiers'][a]['trace'])==STEPS for c in (a3 if a in A3_ARMS else mc)) for a in ARMS+A3_ARMS}}
    unk={}
    for c in allc:
        kinds=tuple((a,sup(c,a)) for a in A3_ARMS) if is_a3(c) else (('bounded4',c['bounded']['4']),)+tuple((a,sup(c,a)) for a in ('RGN4','RGNB4','RGNB4_0','RGN4_or'))
        for kind,X in kinds:
            u=unk.setdefault(kind,[0,0])
            for row in X['unknown']:
                for x in row:u[0]+=1;u[1]+=x>0
    frac={k:(b/a if a else None) for k,(a,b) in unk.items()}
    g10ok=bool(allc) and len(allc)==expected and bool(seal) and seal.get('complete') and all(tl.values()) and all(f is not None and f<=0.01 for f in frac.values())
    gate('G10_compute',g10ok,{'cases':len(allc),'expected':expected,'by_part':{'main':len(main),'stress':len(stress),'alphabet3':len(a3)},'traces_44_steps':tl,
         'unknown_gt0_fraction':{k:None if f is None else round(f,6) for k,f in frac.items()},'queries':{k:{'queries':a,'unknown_gt0':b} for k,(a,b) in unk.items()}},why=wb)
    # G12
    R0=(repro or {}).get('blocks',{}).get('transfer',{})
    g12ok=bool(repro) and repro['G12_pass'] and bool(seal) and R0.get('main_scientific_sha256')==seal['scientific_sha256'] and R0.get('expected')==(14 if smoke else REPRO_EXPECTED)
    gate('G12_reproducibility',g12ok,None if repro is None else repro['blocks'],why=wb+incomplete(False,files=(('REPRODUCIBILITY_019.json',repro),),streams=('repro',)))
    # G13
    try:check_freeze();fz=True;fz_err=None
    except Exception as exc_:fz=False;fz_err=f'{type(exc_).__name__}: {exc_}'
    f14=(opt(ROOT/'experiments/BRUTE_SOURCE_FREEZE_014.json') or {}).get('sha256_files',{})
    f18=(opt(ROOT/'experiments/BRUTE_SOURCE_FREEZE_018.json') or {}).get('sha256_files',{})
    rg_bad=[ck(c) for c in msx if S14.rg_arm(sp8_steps(c),{'4':c['bounded']['4']},FB,c['burn_in'])!=c['certifiers']['RG4']]
    rgn_bad=[ck(c) for c in msx if S18.rgn_arm(sp8_steps(c),sup(c,'RGN4')['support'],c['noisy']['RGN4']['m'],c['burn_in'])!=c['certifiers']['RGN4']]
    g13={'freeze_chain_holds':fz,'cases_use_plan013_tau6':bool(mc) and all(c.get('tau6')==TAU6 for c in mc),
         'rg_sp8_are_frozen_v0120':S19.rg_arm is S14.rg_arm and S19.sp8_steps is S14.sp8_steps and f14.get('experiments/brute_study_014.py')==sha(ROOT/'experiments/brute_study_014.py'),
         'rgn_arm_is_frozen_v0160':f18.get('experiments/brute_study_018.py')==sha(ROOT/'experiments/brute_study_018.py'),
         'rg4_reproduces_main_and_stress':bool(msx) and not rg_bad,'rgn4_reproduces_main_and_stress':bool(msx) and not rgn_bad,
         'seal_of_current_plan_and_freeze':bool(seal) and seal['plan_sha256']==sha(PLAN) and FREEZE.exists() and seal.get('freeze_sha256')==sha(FREEZE)}
    g13ok=all(g13.values()) if not smoke else all(v for k,v in g13.items() if k not in ('freeze_chain_holds','seal_of_current_plan_and_freeze'))
    gate('G13_frozen_controls_reproduce',g13ok,{'clauses':g13,'rg4_not_reproduced':rg_bad[:20],'rgn4_not_reproduced':rgn_bad[:20],'freeze_error':fz_err,'smoke_dry_run_relaxed':smoke},why=wb)
    # GTI
    V=(ts or {}).get('verdict');gti={'verdict_passed':bool(V) and V['passed'],'tracked_tree_clean_at_start':bool(ts) and ts.get('tracked_tree_dirty') is False}
    gate('GTI_test_isolation',all(gti.values()),None if ts is None else {'clauses':gti,'verdict':V,'head':ts.get('head'),'tracked_tree_dirty':ts.get('tracked_tree_dirty'),
         'dirty_tracked_files':ts.get('dirty_tracked_files'),'workers':ts.get('workers'),
         'clean_tag_runs':{k:(None if v is None else v.get('results')) for k,v in (ts.get('clean_tag_runs') or {}).items()},'run':'in-cap'},
         why=incomplete(False,files=(('TEST_SUITE_019.json',ts),),streams=('gti',)))
    # G_RT / G_HB
    hb=heartbeat(study,t0);comp=state.get('completed_at',{})
    end=(t0+done['elapsed_s']) if (t0 is not None and done) else (t0+CAP if t0 is not None else None)
    late={s:(round(comp[s]-t0,1) if s in comp and t0 is not None else None) for s in STREAMS}
    i_streams={s:late[s] is not None and late[s]<=CAP and s not in stopped for s in STREAMS}
    rt={'i_streams_inside_cap_not_stopped':t0 is not None and all(i_streams.values()),
        'ii_watchdog_whole_run':bool(hb) and t0 is not None and hb['first_wall']<=t0+60 and hb['last_wall']>=end-10,
        'iii_kill_drill_latency_le_15s':bool(drill) and drill.get('kill_latency_s') is not None and drill['kill_latency_s']<=15 and not drill.get('survivors')}
    g['G_RT_study_runtime']={'gated':True,'pass':all(rt.values()),'observed':{'clauses':rt,'streams':i_streams,'completion_s_after_t0':late,
         'stopped_streams':stopped,'stop_watchdog':stop,'stop_orchestrator':stop_o,'run_done':done,
         'kill_drill':None if drill is None else {k:drill.get(k) for k in ('kill_latency_s','survivors','sigkill_used','fire_delay_s','label')},
         'spent_s':{k:round(v) for k,v in state.get('spent',{}).items()},'cap_s':CAP},
         **({} if all(rt.values()) else {'reason':'STUDY_BUDGET' if fired else 'clauses failed: '+', '.join(k for k,v in rt.items() if not v)})}
    g['G_HB_heartbeat_gap']={'gated':True,'pass':bool(hb) and hb['max_gap_s'] is not None and hb['max_gap_s']<=30,
         'observed':{'max_gap_s':None if not hb else hb['max_gap_s'],'beats':None if not hb else hb['beats'],'gaps_over_10s_attributed':None if not hb else hb['gaps_over_10s']}}
    # ---- reports (non_gated_reports)
    def per_eps(arm,cs,eps=EPS,slots=SLOTS):
        o={}
        for e in eps:
            x=[c for c in cs if c['eps']==e]
            if not x:continue
            kf=sum(casefalse(c,arm) for c in x)
            o[str(e)]={'cases':len(x),'false_certificates':sum(RC[(id(c),arm)] for c in x),'case_false':kf,'case_false_rate':round(kf/len(x),6),
                       'cp_upper_95_one_sided':cp_upper(kf,len(x)),'coverage':round(sum(c['summary']['certificates'][arm] for c in x)/(len(x)*slots),6),
                       'crossings':sum(c['crossing'] for c in x)}
        return o
    bd={}
    for e in EPS[:3]:
        x=[c for c in main if c['eps']==e]
        if not x:continue
        ms=[(mb,c['m']) for c in x for mb in c['noisy']['RGNB4']['m']]
        st={}
        for c in x:
            for i in range(STEPS):
                s=st.setdefault(i+1,[0,0,0,0])
                for j,arm in enumerate(('RGNB4','RGN4')):s[j]+=sum(v is not None for v in c['certifiers'][arm]['trace'][i]['certificate'])
                s[2]+=c['noisy']['RGNB4']['m'][i];s[3]+=c['m']
        bd[str(e)]={'cases':len(x),'mean_m_b':round(sum(a for a,_ in ms)/len(ms),6),'mean_fixed_m':round(sum(b for _,b in ms)/len(ms),6),
                    'step_fraction_m_b_lt_m':round(sum(a<b for a,b in ms)/len(ms),6),'step_fraction_m_b_gt_m':round(sum(a>b for a,b in ms)/len(ms),6),
                    'per_step':{t:{'mean_m_b':round(v[2]/len(x),4),'mean_m':round(v[3]/len(x),4),'coverage_RGNB4':round(v[0]/(2*len(x)),4),'coverage_RGN4':round(v[1]/(2*len(x)),4)} for t,v in st.items()}}
    gate('R_boundary',None,bd,gated=False)
    gate('R_RG4_noise',None,{'RG4':per_eps('RG4',mc),'SP8':per_eps('SP8',mc),'C_RG4':{s:pv('C_RG4_'+s) for s in ('eps0','eps1','eps2','stress')},'label':'expected > 0 under noise'},gated=False)
    gate('R_stress',None,{'cases':len(stress),'RGNB4':per_eps('RGNB4',stress).get('0.05'),'RGN4':per_eps('RGN4',stress).get('0.05'),'RGN4_or':per_eps('RGN4_or',stress).get('0.05'),
         'cases_with_crossing':sum(c['crossing'] for c in stress),
         'RGNB4_case_false_without_crossing':sum(casefalse(c,'RGNB4') for c in stress if not c['crossing']),
         'RGNB4_case_false_with_crossing':sum(casefalse(c,'RGNB4') for c in stress if c['crossing']),'label':'outside the attestation; no guarantee'},gated=False)
    gate('R_oracle',None,{'RGN4_or':per_eps('RGN4_or',mc),'C_RGN4_or':{s:pv('C_RGN4_or_'+s) for s in ('eps0','eps1','eps2','noisy','stress')},
         'dC_RGN4_or_minus_RGNB4':{s:(lambda a,b:None if a is None or b is None else round(a-b,6))(pv('C_RGN4_or_'+s)[0],pv('C_RGNB4_'+s)[0]) for s in ('eps0','eps1','eps2','noisy','stress')}},gated=False)
    bnd={}
    for e in EPS:
        x=[c for c in mc if c['eps']==e]
        if x:bnd[str(e)]={'cases':len(x),'delta':sorted({c['delta'] for c in x}),
                          'observed_RGNB4_case_false_rate':round(sum(casefalse(c,'RGNB4') for c in x)/len(x),6),
                          'observed_RGN4_case_false_rate':round(sum(casefalse(c,'RGN4') for c in x)/len(x),6),
                          'observed_crossing_rate':round(sum(c['crossing'] for c in x)/len(x),6),
                          'observed_flips_gt_m_rate':round(sum(c['realized_flips']>c['m'] for c in x)/len(x),6),
                          'mean_bound_P_flips_gt_m':round(sum(p_exceed(c['B'],e,c['m']) for c in x)/len(x),8),
                          'm_values':sorted({c['m'] for c in x}),'B_range':[min(c['B'] for c in x),max(c['B'] for c in x)]}
    gate('R_bound',None,bnd,gated=False)
    gate('R_alphabet3_coverage',None,{a:per_eps(a,a3,EPS_A3,SLOTS3) for a in A3_ARMS}|{'C':{a:{s:pv(f'C_{a}_{s}') for s in ('a3_eps0','a3_eps2')} for a in A3_ARMS},
         'dC_RGNB4_3_RGN4_3':{s:pv('dC_RGNB4_3_RGN4_3_'+s) for s in ('a3_eps0','a3_eps2')},'label':'Open; reported only'},gated=False)
    hba=opt(study/'HEARTBEAT_ATTRIBUTION_019.json')
    gate('R_heartbeat_attribution',None,{'watchdog_gaps_over_10s':None if not hb else hb['gaps_over_10s'],
         'sentinel_attribution':None if hba is None else {k:hba.get(k) for k in ('max_watchdog_gap_s','max_sentinel_tick_gap_s','class_counts','gaps_over_10s','sentinel_records')},
         'label':'Inferred; deviation #90 diagnostic, changes no verdict'},gated=False)
    raw=opt(study/'transfer'/'RESULTS.json');RW={ck(c):c for c in raw['cases']} if raw else {}
    def solver_cost():
        out={}
        for arms,cs in ((('RG4','RGN4','RGNB4','RGNB4_0','RGN4_or'),mc),(A3_ARMS,a3)):
            W=[RW.get(ck(c),{}).get('region_wall_informational') for c in cs]
            if not W:continue
            if any(w is None for w in W):return 'RESULTS.json absent or incomplete: timing not reported'
            out|={a:{'total_s':round(sum(w[a] for w in W),3),'ms_per_step':round(1000*sum(w[a] for w in W)/(len(W)*STEPS),4)} for a in arms}
        return out|{'timing_source':'transfer/RESULTS.json (informational, unsealed)'}
    rm=opt(ROOT/'docs/research/v0.17.0/RATE_MATH_019.json')
    gate('R_rates',None,{s_:{'spent_s':round(state.get('spent',{}).get(s_,0),1),'budget_s':BUDGETS[s_],
         'fraction_of_budget':round(state.get('spent',{}).get(s_,0)/BUDGETS[s_],3)} for s_ in STREAMS}|{'solver_cost':solver_cost() if allc else None,
         'rate_math':None if rm is None else {'file':'docs/research/v0.17.0/RATE_MATH_019.json','sha256':sha(ROOT/'docs/research/v0.17.0/RATE_MATH_019.json'),
                                              'projections':rm.get('streams') or rm.get('projection')}},gated=False)
    gated=[k for k,v in g.items() if v['gated']]
    return {'schema':'brute.gates.v17_0','study':plan['study'],'plan_sha256':sha(PLAN),'smoke_dry_run':smoke,'criteria_registered':sorted(C),
            'criteria_scored':sorted(gated),'scientific_sha256':None if seal is None else seal['scientific_sha256'],'stop_rule_fired':fired,'gates':g,
            'passed':[k for k in gated if g[k]['pass']],'failed':[k for k in gated if g[k]['pass'] is False],
            'pending':[k for k in gated if g[k]['pass'] is None],'all_gated_pass':all(g[k]['pass'] for k in gated),
            'GNB':g['GNB_sequential_margin']['pass'],'GA3':g['GA3_alphabet3_soundness']['pass'],'G_RT':g['G_RT_study_runtime']['pass'],'G_HB':g['G_HB_heartbeat_gap']['pass']}


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--study-dir',default=str(STUDY_DIR));ap.add_argument('--check',action='store_true')
    ap.add_argument('--output',default='GATES_019.json');ap.add_argument('--smoke',action='store_true',help='dry run on a smoke directory; prints only')
    a=ap.parse_args()
    if a.smoke:
        obj=build(Path(a.study_dir),smoke=True)
        print({k:obj[k] for k in ('passed','failed','pending')});print({k:v.get('reason') for k,v in obj['gates'].items() if v.get('reason')});raise SystemExit
    obj=build(Path(a.study_dir));out=Path(a.study_dir)/a.output
    if a.check:check(out.read_bytes()==dumps(obj),out.name+' does not reproduce');print(out.name,'reproduces')
    else:write_new(out,obj);print({k:obj[k] for k in ('passed','failed','pending','all_gated_pass')})
