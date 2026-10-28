"""Gates for study-020 (BRUTE_PLAN_020 criteria; docs/research/BRUTE_DEVIATIONS_020.md #103; adapted from make_gates_019,
frozen). Committed and ledgered (scoring_freeze_020) before the held-out run_start; nothing is tuned after results are seen.

Inputs (study dir D = results/study-020): D/transfer/{SCIENTIFIC,SEAL}.json (480 cases = 360 main + 120 stress, 88 steps),
D/PAIRED_ANALYSIS_020.json, D/REPRODUCIBILITY_020.json, D/SECOND_IMPLEMENTATION_020.json, D/TEST_SUITE_020.json,
D/RUN_STATE_020.json, D/RUN_T0, D/HEARTBEAT_020.jsonl, D/KILL_DRILL_020.json (or results/smoke-020/ under --smoke),
optional D/STOP_020*.json, D/RUN_DONE_020.json, D/HEARTBEAT_ATTRIBUTION_020.json, D/transfer/RESULTS.json (timing only).

Gated (plan criteria, one entry each):
  GLH_horizon             (a) RGNB4 0 false certificates (recorded and recomputed) on every noisy main case (eps 0.01, 0.02;
                          240), unconditional: crossings included; (b) CP95 upper of the RGNB4 case-false rate over those
                          cases <= 0.05; (c) C_late(RGNB4, eps 0.02) mean >= 0.10; (d) its 95% CI lower > 0.05 (PAIRED_ANALYSIS_020).
  GLH_early_control       C_early28(RGNB4, eps 0.02) mean inside the study-019 CI [0.04053, 0.065436] (#103 item 6; inclusive).
  GS_a8_soundness         RGNB4 0 false at eps 0 on the 120 eps-0 main cases over 88 steps.
  G_recount               every arm's false count recomputed from its trace against the SP8 trace truth; wrong flags;
                          certificate counts; summary (certificates, false, case_false, coverage, late / early28 / per-step
                          windows); RGNB4_bit recomputed from the RGNB4 supports (bits, wrong flags, all four counts, summary);
                          realized_flips == |flip positions|; crossing == (crossing_bit is not None).
  GS_ref8_reference_audit SECOND_IMPLEMENTATION_020 results sha == transfer seal, all 360 main cases audited (gated), 0 gated
                          mismatches, mutation 20/20.
  GAPI8                   brute/api/certify7.py byte-identical to its study-019 source-freeze hash; test_api_certify7_0170.py
                          ok inside GTI (>= 4 tests); certify7 soundness probe unchanged; no brute/api/certify8.py.
  G10_compute             480 cases, seal complete, every trace 88 steps, unknown > 0 fraction <= 1% for every support kind.
  G12_reproducibility     REPRODUCIBILITY_020 G12_pass, 120 expected, main sha == transfer seal.
  G13_frozen_controls_reproduce freeze chain holds; tau6; RG4 recomputed by the frozen v0.12.0 rg_arm and RGN4 / RGNB4 /
                          RGN4_or certificates recomputed from the recorded supports by the frozen study-018 rgn_arm on every
                          case; frozen study-014 / 018 / 019 sources unchanged; seal binds the current plan and freeze.
  GTI_test_isolation      TEST_SUITE_020 verdict passed (declared K_0170) and tracked tree clean at GTI start.
  G_RT_study_runtime      as study-019 (streams inside the 7,200 s cap, not stopped; watchdog whole run; kill drill <= 15 s).
  G_HB_heartbeat_gap      max heartbeat gap <= 10 s (plan criterion; study-019 used 30 s).
A gate whose inputs are missing or incomplete FAILS with reason INCOMPLETE_INPUT (STUDY_BUDGET if a stop fired).
Reports (non-gated): R_C_curve, R_perbit, R_stress, R_coverage_RG4_RGN4or_SP8, R_boundary, R_first_cert (informational;
CENSOR = 45 inherited, #103 addendum), R_rates (projected vs observed), R_heartbeat_attribution.
  PYTHONPATH=. python scripts/make_gates_020.py [--study-dir D] [--check] [--smoke]"""
from __future__ import annotations
import argparse,json,math,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common_020 import STUDY_DIR,PLAN,FREEZE,load,dumps,write_new,check,sha,check_freeze,TAU6
from experiments.brute_study_014 import sp8_steps
import experiments.brute_study_014 as S14
import experiments.brute_study_018 as S18
import experiments.brute_study_020 as S20
from scripts.make_gates_015 import wrong,opt
from scripts.make_gates_018 import cp_upper,p_exceed
from scripts.run_study_020 import STREAMS as RUN_STREAMS,CAP

STEPS=88;FB=4;SLOTS=176;LATE=(45,88);EARLY=28;EXPECTED={'main':360,'stress':120};REPRO_EXPECTED=120
EARLY_CI=(0.04053,0.065436)
ARMS=('RG4','RGN4','RGNB4','RGN4_or');NOISY=('RGN4','RGNB4','RGN4_or');ALL_ARMS=('SP8',)+ARMS
STREAMS=('transfer','repro','gti','g11');BUDGETS={k:v[1] for k,v in RUN_STREAMS.items()}
EPS=(0.0,0.01,0.02,0.05)
API_EXPECT={'kind':'probabilistic','delta':0.01,'conditional_on':'running flips <= m(b) and n* <= family_bound'}


def ck(c):return f"{c['block']}/{c['family']}/{c['seed']}/{c['eps']}"
def is_main(c):return c['eps'] in (0.0,0.01,0.02) and c['block']!='stress'
def is_noisy(c):return c['eps'] in (0.01,0.02)


def beats(d,t0):
    p=Path(d)/'HEARTBEAT_020.jsonl'
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


def actual(c):return [s[5] for s in sp8_steps(c)]


def recount(c,act):
    """[(arm, recorded, recomputed, wrong_flags_ok)] for one case, every arm."""
    S=sp8_steps(c)
    out=[('SP8',c['summary']['false']['SP8'],sum(cert[b] is not None and cert[b]!=act[i][b] for i,(t,a,cert,_,_,_) in enumerate(S) for b in (0,1)),True)]
    for arm in ARMS:
        A=c['certifiers'][arm]
        flags=all(len(r['certificate'])==2 and r['wrong'][b]==(r['certificate'][b] is not None and r['certificate'][b]!=act[i][b]) for i,r in enumerate(A['trace']) for b in (0,1)) if A['trace'] and 'wrong' in A['trace'][0] else True
        out.append((arm,A['false_certificates'],wrong(A['trace'],act),flags))
    return out


def _bit(code,j):return (code>>(1-j))&1


def perbit_recount(c,act):
    """RGNB4_bit recomputed from the recorded RGNB4 supports (independent of brute.perbit); list of mismatches."""
    bad=[];P=c['perbit'];sp=sup(c,'RGNB4')['support'];n=f=nl=fl=0
    for i,r in enumerate(c['certifiers']['RGNB4']['trace']):
        t=r['step'];row=P['trace'][i]
        if row['step']!=t:bad.append(('perbit','step',i));continue
        for b in (0,1):
            s=sp[i][b];want=[None,None]
            if t>c['burn_in'] and s:
                for j in (0,1):
                    v={_bit(x,j) for x in s};want[j]=v.pop() if len(v)==1 else None
            if row['bits'][b]!=want:bad.append(('perbit','bits',t,b,row['bits'][b],want))
            w=[want[j] is not None and want[j]!=_bit(act[i][b],j) for j in (0,1)]
            if row['wrong'][b]!=w:bad.append(('perbit','wrong',t,b))
            k=sum(v is not None for v in want);n+=k;f+=sum(w)
            if LATE[0]<=t<=LATE[1]:nl+=k;fl+=sum(w)
    got=(P['certified_bits'],P['false_bits'],P['late_certified_bits'],P['late_false_bits'])
    if got!=(n,f,nl,fl):bad.append(('perbit','counts',got,(n,f,nl,fl)))
    Sb=c['summary']['perbit']
    if (Sb['certified_bits'],Sb['false_bits'],Sb['late_certified_bits'],Sb['late_false_bits'],Sb['case_false'])!=(n,f,nl,fl,f>0):bad.append(('perbit','summary'))
    if Sb['coverage']!=round(n/(2*SLOTS),6) or Sb['coverage_late']!=round(nl/(4*(LATE[1]-LATE[0]+1)),6):bad.append(('perbit','summary_coverage'))
    return bad


def cert_counts(c):
    bad=[];Sm=c['summary']
    tr={a:c['certifiers'][a]['trace'] for a in ARMS}|{'SP8':[{'step':t,'certificate':cert} for t,a,cert,_,_,_ in sp8_steps(c)]}
    for arm in ARMS:
        A=c['certifiers'][arm];n=sum(x is not None for r in A['trace'] for x in r['certificate'])
        if A['certificates']!=n:bad.append((arm,'trace',A['certificates'],n))
        if Sm['false'].get(arm)!=A['false_certificates']:bad.append((arm,'summary_false',Sm['false'].get(arm),A['false_certificates']))
    for arm in ALL_ARMS:
        per=[sum(x is not None for x in r['certificate']) for r in tr[arm]];n=sum(per)
        late=sum(p for r,p in zip(tr[arm],per) if LATE[0]<=r['step']<=LATE[1]);early=sum(p for r,p in zip(tr[arm],per) if r['step']<=EARLY)
        if Sm['certificates'].get(arm)!=n:bad.append((arm,'summary',Sm['certificates'].get(arm),n))
        if Sm['coverage'].get(arm)!=round(n/SLOTS,6):bad.append((arm,'coverage',Sm['coverage'].get(arm),n))
        if Sm['per_step'].get(arm)!=per:bad.append((arm,'per_step'))
        if Sm['certificates_late'].get(arm)!=late or Sm['coverage_late'].get(arm)!=round(late/88,6):bad.append((arm,'late',Sm['certificates_late'].get(arm),late))
        if Sm['certificates_early28'].get(arm)!=early or Sm['coverage_early28'].get(arm)!=round(early/56,6):bad.append((arm,'early28',Sm['certificates_early28'].get(arm),early))
        if Sm['case_false'].get(arm)!=(Sm['false'].get(arm,0)>0):bad.append((arm,'case_false',Sm['case_false'].get(arm),Sm['false'].get(arm)))
    if c['realized_flips']!=len(c['flip_positions_EVALUATOR_ONLY']):bad.append(('noise','realized_flips',c['realized_flips'],len(c['flip_positions_EVALUATOR_ONLY'])))
    if c['crossing']!=(c['crossing_bit'] is not None):bad.append(('noise','crossing',c['crossing'],c['crossing_bit']))
    return bad


def sup(c,arm):
    x=c['noisy'][arm]
    return c['noisy'][x['shared_with']] if x.get('shared_with') and x.get('support') is None else x


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
    stop=opt(study/'STOP_020.json');stop_o=opt(study/'STOP_020_ORCHESTRATOR.json');done=opt(study/'RUN_DONE_020.json')
    state=opt(study/'RUN_STATE_020.json') or {'stopped':{},'spent':{},'completed_at':{}}
    t0=float((study/'RUN_T0').read_text().split()[0]) if (study/'RUN_T0').exists() else None
    paired=opt(study/'PAIRED_ANALYSIS_020.json');repro=opt(study/'REPRODUCIBILITY_020.json')
    aud=opt(study/'SECOND_IMPLEMENTATION_020.json');ts=opt(study/'TEST_SUITE_020.json');drill=opt(study/'KILL_DRILL_020.json')
    if smoke and drill is None:drill=opt(ROOT/'results/smoke-020/KILL_DRILL_020.json')
    stopped=state.get('stopped',{});fired=stop is not None or stop_o is not None;g={}
    exp=({'main':24,'stress':8} if smoke else EXPECTED);expected=sum(exp.values())
    allc=blk['cases'] if blk else []
    main=[c for c in allc if is_main(c)];stress=[c for c in allc if c['eps']==0.05]
    noisy=[c for c in main if is_noisy(c)];e0=[c for c in main if c['eps']==0.0];e2=[c for c in main if c['eps']==0.02]
    def incomplete(block=True,files=(),streams=()):
        why=[]
        if block:
            if blk is None:why.append('transfer block missing')
            elif not blk.get('complete') or len(allc)!=expected or (len(main),len(stress))!=(exp['main'],exp['stress']):
                why.append(f'transfer block incomplete ({len(allc)}/{expected} cases: main {len(main)}, stress {len(stress)})')
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
    tot={};bad_rc=[];bad_cc=[];bad_fl=[];bad_pb=[]
    for c in allc:
        sub='stress' if c['eps']==0.05 else 'main'
        for arm,rec,re,fl in recount(c,ACT[id(c)]):
            RC[(id(c),arm)]=re
            x=tot.setdefault(sub,{}).setdefault(arm,{'recorded_false':0,'recomputed_false':0,'records':0,'mismatching_records':0})
            x['recorded_false']+=rec;x['recomputed_false']+=re;x['records']+=1
            if rec!=re:x['mismatching_records']+=1;bad_rc.append((ck(c),arm,rec,re))
            if not fl:bad_fl.append((ck(c),arm))
        bad_cc+=[(ck(c),)+b for b in cert_counts(c)];bad_pb+=[(ck(c),)+b for b in perbit_recount(c,ACT[id(c)])]
    cover=sorted(set(ALL_ARMS)-set(tot.get('main',{})))
    gate('G_recount',not bad_rc and not bad_cc and not bad_fl and not bad_pb and bool(allc) and not cover,{'per_subset_arm':tot,'mismatches':bad_rc[:50],
         'wrong_flag_mismatches':bad_fl[:50],'certificate_count_mismatches':bad_cc[:50],'perbit_mismatches':bad_pb[:50],'arms_not_recounted':cover},why=wb)
    zero=lambda cs,arm:all(c['certifiers'][arm]['false_certificates']==0 and RC[(id(c),arm)]==0 for c in cs)
    casefalse=lambda c,arm:RC[(id(c),arm)]>0
    P=paired or {}
    def pv(k):x=P.get(k) or {};return x.get('mean'),x.get('ci95')
    wp=wb+incomplete(False,files=(('PAIRED_ANALYSIS_020.json',paired),))
    # GLH_horizon (headline)
    k=sum(casefalse(c,'RGNB4') for c in noisy);ub=cp_upper(k,len(noisy));m2,ci2=pv('C_late_RGNB4_eps2')
    glh={'a_zero_false_all_noisy_main':bool(noisy) and zero(noisy,'RGNB4'),'b_cp_upper_le_0.05':ub is not None and ub<=0.05,
         'c_C_late_eps2_mean_ge_0.10':m2 is not None and m2>=0.10,'d_C_late_eps2_ci_lower_gt_0.05':ci2 is not None and ci2[0]>0.05}
    gate('GLH_horizon',all(glh.values()),{'clauses':glh,'noisy_cases':len(noisy),'cases_with_crossing':sum(c['crossing'] for c in noisy),
         'case_false':k,'case_false_examples':[ck(c) for c in noisy if casefalse(c,'RGNB4')][:20],
         'case_false_with_crossing':sum(casefalse(c,'RGNB4') for c in noisy if c['crossing']),
         'false_certificates_RGNB4':sum(RC[(id(c),'RGNB4')] for c in noisy),'cp_upper_95_one_sided':ub,
         'C_late_RGNB4_eps2':(m2,ci2),'C_late_RGNB4_eps1':pv('C_late_RGNB4_eps1'),'C_late_RGNB4_eps0':pv('C_late_RGNB4_eps0'),
         'C_late_RGN4_eps2':pv('C_late_RGN4_eps2'),'dC_late_RGNB4_RGN4_eps2':pv('dC_late_RGNB4_RGN4_eps2'),
         'C_full_RGNB4_eps2':pv('C_full_RGNB4_eps2')},why=wp)
    me,cie=pv('C_early28_RGNB4_eps2')
    gate('GLH_early_control',me is not None and EARLY_CI[0]<=me<=EARLY_CI[1],{'C_early28_RGNB4_eps2':(me,cie),'study019_ci':list(EARLY_CI),
         'rule':'mean inside the study-019 CI (inclusive)'},why=wp)
    gate('GS_a8_soundness',bool(e0) and zero(e0,'RGNB4'),{'eps0_cases':len(e0),'RGNB4_recorded_false':sum(c['certifiers']['RGNB4']['false_certificates'] for c in e0),
         'RGNB4_recomputed_false':sum(RC[(id(c),'RGNB4')] for c in e0),'RG4_false_eps0':sum(RC[(id(c),'RG4')] for c in e0)},why=wb)
    # GS_ref8
    md=(aud or {}).get('mutation_test') or {};ngated=len(main)
    ref={'results_sha_matches_seal':bool(aud) and bool(seal) and aud.get('results_sha256')==seal.get('results_sha256'),
         'all_gated_cases_audited':bool(aud) and aud.get('gated_cases_expected')==ngated and aud.get('gated_cases_audited')==ngated and ngated>0,
         'zero_gated_mismatching':bool(aud) and aud.get('gated_mismatching_cases')==0,
         'mutation_20_of_20':md.get('passed') is True and md.get('injected')==20 and md.get('distinct_cases')==20 and md.get('detected_injected')==20 and md.get('flagged_not_injected')==0}
    gate('GS_ref8_reference_audit',all(ref.values()),{'clauses':ref,'gated_expected':ngated,'report':None if aud is None else {k:aud[k] for k in aud if k not in ('mismatches','mutation_test','events')},
         'mutation':{k:v for k,v in md.items() if k!='details'},'wording':'second implementation by the same author'},
         why=wb+incomplete(False,files=(('SECOND_IMPLEMENTATION_020.json',aud),),streams=('g11',)))
    # GAPI8
    pm=((ts or {}).get('per_module') or {}).get('test_api_certify7_0170.py') or {};f19=(opt(ROOT/'experiments/BRUTE_SOURCE_FREEZE_019.json') or {}).get('sha256_files',{});asd=api_soundness()
    api={'certify7_unchanged':f19.get('brute/api/certify7.py') is not None and f19.get('brute/api/certify7.py')==sha(ROOT/'brute/api/certify7.py'),
         'module_ok':pm.get('returncode')==0 and len(pm.get('results') or {})>=4 and all(v[0]=='ok' for v in pm.get('results',{}).values()),
         'soundness_dict':asd['matches'],'no_certify8':not (ROOT/'brute/api/certify8.py').exists()}
    gate('GAPI8',all(api.values()),{'clauses':api,'results':pm.get('results'),'soundness_probe':asd},why=incomplete(False,files=(('TEST_SUITE_020.json',ts),),streams=('gti',)))
    # G10
    tl={'SP8':all(len(c['arms']['SP8']['trace'])==STEPS for c in allc),**{a:all(len(c['certifiers'][a]['trace'])==STEPS for c in allc) for a in ARMS},
        'perbit':all(len(c['perbit']['trace'])==STEPS for c in allc)}
    unk={}
    for c in allc:
        for kind,X in (('bounded4',c['bounded']['4']),)+tuple((a,sup(c,a)) for a in NOISY):
            u=unk.setdefault(kind,[0,0])
            for row in X['unknown']:
                for x in row:u[0]+=1;u[1]+=x>0
    frac={k:(b/a if a else None) for k,(a,b) in unk.items()}
    g10ok=bool(allc) and len(allc)==expected and bool(seal) and seal.get('complete') and all(tl.values()) and all(f is not None and f<=0.01 for f in frac.values())
    gate('G10_compute',g10ok,{'cases':len(allc),'expected':expected,'by_part':{'main':len(main),'stress':len(stress)},'traces_88_steps':tl,
         'unknown_gt0_fraction':{k:None if f is None else round(f,6) for k,f in frac.items()},'queries':{k:{'queries':a,'unknown_gt0':b} for k,(a,b) in unk.items()}},why=wb)
    # G12
    R0=(repro or {}).get('blocks',{}).get('transfer',{})
    g12ok=bool(repro) and repro['G12_pass'] and bool(seal) and R0.get('main_scientific_sha256')==seal['scientific_sha256'] and R0.get('expected')==(11 if smoke else REPRO_EXPECTED)
    gate('G12_reproducibility',g12ok,None if repro is None else repro['blocks'],why=wb+incomplete(False,files=(('REPRODUCIBILITY_020.json',repro),),streams=('repro',)))
    # G13
    try:check_freeze();fz=True;fz_err=None
    except Exception as exc_:fz=False;fz_err=f'{type(exc_).__name__}: {exc_}'
    F={n:(opt(ROOT/f'experiments/BRUTE_SOURCE_FREEZE_0{n}.json') or {}).get('sha256_files',{}) for n in (14,18,19)}
    rg_bad=[ck(c) for c in allc if S14.rg_arm(sp8_steps(c),{'4':c['bounded']['4']},FB,c['burn_in'])!=c['certifiers']['RG4']]
    rgn_bad=[(ck(c),a) for c in allc for a in NOISY if S18.rgn_arm(sp8_steps(c),sup(c,a)['support'],c['noisy'][a]['m'],c['burn_in'])!=c['certifiers'][a]]
    g13={'freeze_chain_holds':fz,'cases_use_plan013_tau6':bool(allc) and all(c.get('tau6')==TAU6 for c in allc),
         'rg_sp8_are_frozen_v0120':S20.rg_arm is S14.rg_arm and S20.sp8_steps is S14.sp8_steps and F[14].get('experiments/brute_study_014.py')==sha(ROOT/'experiments/brute_study_014.py'),
         'rgn_arm_is_frozen_v0160':F[18].get('experiments/brute_study_018.py')==sha(ROOT/'experiments/brute_study_018.py'),
         'v0170_sources_frozen':all(F[19].get(p)==sha(ROOT/p) for p in ('experiments/brute_study_019.py','brute/seqmargin.py')),
         'rg4_reproduces':bool(allc) and not rg_bad,'rgn_rule_reproduces_RGN4_RGNB4_RGN4_or':bool(allc) and not rgn_bad,
         'seal_of_current_plan_and_freeze':bool(seal) and seal['plan_sha256']==sha(PLAN) and FREEZE.exists() and seal.get('freeze_sha256')==sha(FREEZE)}
    g13ok=all(g13.values()) if not smoke else all(v for k,v in g13.items() if k not in ('freeze_chain_holds','seal_of_current_plan_and_freeze'))
    gate('G13_frozen_controls_reproduce',g13ok,{'clauses':g13,'rg4_not_reproduced':rg_bad[:20],'rgn_not_reproduced':rgn_bad[:20],'freeze_error':fz_err,'smoke_dry_run_relaxed':smoke},why=wb)
    # GTI
    V=(ts or {}).get('verdict');gti={'verdict_passed':bool(V) and V['passed'],'tracked_tree_clean_at_start':bool(ts) and ts.get('tracked_tree_dirty') is False}
    gate('GTI_test_isolation',all(gti.values()),None if ts is None else {'clauses':gti,'verdict':V,'head':ts.get('head'),'tracked_tree_dirty':ts.get('tracked_tree_dirty'),
         'dirty_tracked_files':ts.get('dirty_tracked_files'),'workers':ts.get('workers'),
         'clean_tag_runs':{k:(None if v is None else v.get('results')) for k,v in (ts.get('clean_tag_runs') or {}).items()},'run':'in-cap'},
         why=incomplete(False,files=(('TEST_SUITE_020.json',ts),),streams=('gti',)))
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
    g['G_HB_heartbeat_gap']={'gated':True,'pass':bool(hb) and hb['max_gap_s'] is not None and hb['max_gap_s']<=10,
         'observed':{'max_gap_s':None if not hb else hb['max_gap_s'],'beats':None if not hb else hb['beats'],'gaps_over_10s_attributed':None if not hb else hb['gaps_over_10s']}}
    # ---- reports (non_gated_reports)
    def per_eps(arm,cs,eps=EPS):
        o={}
        for e in eps:
            x=[c for c in cs if c['eps']==e]
            if not x:continue
            kf=sum(casefalse(c,arm) for c in x)
            o[str(e)]={'cases':len(x),'false_certificates':sum(RC[(id(c),arm)] for c in x),'case_false':kf,'case_false_rate':round(kf/len(x),6),
                       'cp_upper_95_one_sided':cp_upper(kf,len(x)),'coverage_full':round(sum(c['summary']['certificates'][arm] for c in x)/(len(x)*SLOTS),6),
                       'coverage_late':round(sum(c['summary']['certificates_late'][arm] for c in x)/(len(x)*88),6),
                       'coverage_early28':round(sum(c['summary']['certificates_early28'][arm] for c in x)/(len(x)*56),6),'crossings':sum(c['crossing'] for c in x)}
        return o
    subs=('eps0','eps1','eps2','noisy','stress')
    gate('R_C_curve',None,{s:P.get('C_curve_'+s) for s in subs}|{'label':'per step t = 1..88: mean certificates / 2 (PAIRED_ANALYSIS_020)'},gated=False)
    pbr={}
    for e in EPS:
        x=[c for c in allc if c['eps']==e]
        if x:pbr[str(e)]={'cases':len(x),'certified_bits':sum(c['perbit']['certified_bits'] for c in x),'false_bits':sum(c['perbit']['false_bits'] for c in x),
                          'late_certified_bits':sum(c['perbit']['late_certified_bits'] for c in x),'late_false_bits':sum(c['perbit']['late_false_bits'] for c in x),
                          'cases_with_false_bit':sum(c['perbit']['false_bits']>0 for c in x),'coverage_full':round(sum(c['perbit']['certified_bits'] for c in x)/(352*len(x)),6),
                          'coverage_late':round(sum(c['perbit']['late_certified_bits'] for c in x)/(176*len(x)),6)}
    gate('R_perbit',None,{'per_eps':pbr,'ci':{s:{'late':pv('bit_late_RGNB4_'+s),'full':pv('bit_full_RGNB4_'+s),'case_false_bit':pv('bitfalse_RGNB4_'+s)} for s in subs}},gated=False)
    gate('R_stress',None,{'cases':len(stress),**{a:per_eps(a,stress).get('0.05') for a in ARMS},'cases_with_crossing':sum(c['crossing'] for c in stress),
         'RGNB4_case_false_without_crossing':sum(casefalse(c,'RGNB4') for c in stress if not c['crossing']),
         'RGNB4_case_false_with_crossing':sum(casefalse(c,'RGNB4') for c in stress if c['crossing']),'label':'outside the attestation; no guarantee'},gated=False)
    gate('R_coverage_RG4_RGN4or_SP8',None,{a:per_eps(a,allc) for a in ('RG4','RGN4_or','SP8','RGN4','RGNB4')}|
         {'C_late':{a:{s:pv(f'C_late_{a}_{s}') for s in subs} for a in ('RG4','RGN4_or','SP8','RGN4')},
          'labels':{'RG4':'expected > 0 false under noise','RGN4_or':'oracle m = realized flips, evaluator-only'}},gated=False)
    bd={}
    for e in EPS:
        x=[c for c in allc if c['eps']==e]
        if not x:continue
        ms=[(mb,c['m']) for c in x for mb in c['noisy']['RGNB4']['m']]
        bd[str(e)]={'cases':len(x),'mean_m_b':round(sum(a for a,_ in ms)/len(ms),6),'mean_fixed_m':round(sum(b for _,b in ms)/len(ms),6),
                    'step_fraction_m_b_lt_m':round(sum(a<b for a,b in ms)/len(ms),6),'step_fraction_m_b_gt_m':round(sum(a>b for a,b in ms)/len(ms),6),
                    'observed_flips_gt_m_rate':round(sum(c['realized_flips']>c['m'] for c in x)/len(x),6),
                    'mean_bound_P_flips_gt_m':round(sum(p_exceed(c['B'],e,c['m']) for c in x)/len(x),8),'B_range':[min(c['B'] for c in x),max(c['B'] for c in x)]}
    gate('R_boundary',None,bd,gated=False)
    gate('R_first_cert',None,{'label':'informational, ungated; SP8 censored at the inherited CENSOR = 45 (ambiguous at 88 steps; deviation addendum)',
         'mean_first_cert_step':{a:{str(e):(lambda x:None if not x else round(sum(x)/len(x),3))([c['summary']['first_cert_step'][a] for c in allc if c['eps']==e]) for e in EPS} for a in ALL_ARMS}},gated=False)
    hba=opt(study/'HEARTBEAT_ATTRIBUTION_020.json')
    gate('R_heartbeat_attribution',None,{'watchdog_gaps_over_10s':None if not hb else hb['gaps_over_10s'],
         'sentinel_attribution':None if hba is None else {k:hba.get(k) for k in ('max_watchdog_gap_s','max_sentinel_tick_gap_s','class_counts','gaps_over_10s','sentinel_records')},
         'label':'Inferred; diagnostic, changes no verdict'},gated=False)
    raw=opt(study/'transfer'/'RESULTS.json');RW={ck(c):c for c in raw['cases']} if raw else {}
    def solver_cost():
        W=[RW.get(ck(c),{}).get('region_wall_informational') for c in allc]
        if not W or any(w is None for w in W):return 'RESULTS.json absent or incomplete: timing not reported'
        return {a:{'total_s':round(sum(w[a] for w in W),3),'ms_per_step':round(1000*sum(w[a] for w in W)/(len(W)*STEPS),4)} for a in ARMS}|{'timing_source':'transfer/RESULTS.json (informational, unsealed)'}
    rm=opt(ROOT/'docs/research/v0.18.0/RATE_MATH_020.json');proj=(rm or {}).get('streams') or {}
    gate('R_rates',None,{s_:{'spent_s':round(state.get('spent',{}).get(s_,0),1),'budget_s':BUDGETS[s_],'projected_s':(proj.get(s_) or {}).get('projected_s'),
         'raw_projection_s':(proj.get(s_) or {}).get('raw_s'),'fraction_of_budget':round(state.get('spent',{}).get(s_,0)/BUDGETS[s_],3)} for s_ in STREAMS}|
         {'solver_cost':solver_cost() if allc else None,'rate_math':None if rm is None else {'file':'docs/research/v0.18.0/RATE_MATH_020.json','sha256':sha(ROOT/'docs/research/v0.18.0/RATE_MATH_020.json'),'fits':rm.get('fits')}},gated=False)
    gated=[k for k,v in g.items() if v['gated']]
    return {'schema':'brute.gates.v18_0','study':plan['study'],'plan_sha256':sha(PLAN),'smoke_dry_run':smoke,'criteria_registered':sorted(C),
            'criteria_scored':sorted(gated),'scientific_sha256':None if seal is None else seal['scientific_sha256'],'stop_rule_fired':fired,'gates':g,
            'passed':[k for k in gated if g[k]['pass']],'failed':[k for k in gated if g[k]['pass'] is False],
            'pending':[k for k in gated if g[k]['pass'] is None],'all_gated_pass':all(g[k]['pass'] for k in gated),
            'GLH':g['GLH_horizon']['pass'],'G_RT':g['G_RT_study_runtime']['pass'],'G_HB':g['G_HB_heartbeat_gap']['pass']}


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--study-dir',default=str(STUDY_DIR));ap.add_argument('--check',action='store_true')
    ap.add_argument('--output',default='GATES_020.json');ap.add_argument('--smoke',action='store_true',help='dry run on a smoke directory; prints only')
    a=ap.parse_args()
    if a.smoke:
        obj=build(Path(a.study_dir),smoke=True)
        print({k:obj[k] for k in ('passed','failed','pending')});print({k:v.get('reason') for k,v in obj['gates'].items() if v.get('reason')});raise SystemExit
    obj=build(Path(a.study_dir));out=Path(a.study_dir)/a.output
    if a.check:check(out.read_bytes()==dumps(obj),out.name+' does not reproduce');print(out.name,'reproduces')
    else:write_new(out,obj);print({k:obj[k] for k in ('passed','failed','pending','all_gated_pass')})
