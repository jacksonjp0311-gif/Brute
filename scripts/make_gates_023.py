"""Gates for study-023 (BRUTE_PLAN_023 criteria; adapted from make_gates_021). Committed and ledgered (scoring_freeze_023)
before the held-out run_start; nothing is tuned after results are seen.

Inputs (study dir D = results/study-023): D/transfer/{SCIENTIFIC,SEAL}.json (390 cases = 360 main + 30 stress (deviation #110), 88 steps;
120 prefix28 records on the eps-0.02 main cases), D/PAIRED_ANALYSIS_023.json, D/REPRODUCIBILITY_023.json,
D/SECOND_IMPLEMENTATION_023.json, D/TEST_SUITE_023.json, D/RUN_STATE_023.json, D/RUN_T0, D/HEARTBEAT_023.jsonl,
results/smoke-023/{KILL_DRILL_023,RESUME_DRILL_023,API_CHECK_023}.json, results/diag-023/HN_RECOUNT_023.json, optional
D/STOP_023*.json, D/RUN_DONE_023.json, D/HEARTBEAT_ATTRIBUTION_023.json, D/transfer/RESULTS.json (timing only).
Arms per case: RG4, RGL4, RGNA4, RGN4_or, plus RGNB4 at eps 0.02 (plan arms; deviation #109); SP8 always.

Gated (plan criteria, one entry each):
  GLR                 (a) RGL4 0 false certificates (recorded and recomputed) on all 240 noisy main cases; (b) CP95 upper of
                      the RGL4 case-false rate <= 0.05; (c) C_late(RGL4, eps 0.02) >= 0.35 and CI lower > 0.30;
                      (d) dC_late(RGL4 - RGNA4, eps 0.02) paired mean >= 0.08 and CI lower > 0.05; (e) RGL4_prefix28 identical
                      (supports, unknown, bounds, certificates, LR record) to steps 1-28 of the full RGL4 run on all 120
                      eps-0.02 main cases.
  GLR_lemma           LR_LEMMA_023.md committed in a commit that is an ancestor of every commit touching brute/lrregion.py;
                      v0200_reference.ref_D() == [3, 4, 5, 7] (exact integers); HN_RECOUNT_023 passed.
  GAS_frozen_control  95% CI of C_late(RGNA4, eps 0.02) intersects [0.214962, 0.317332] (inclusive).
  GS_a10              RGL4 0 false at eps 0 on the 120 eps-0 main cases.
  GS_ref10            SECOND_IMPLEMENTATION_023 results sha == transfer seal, all 360 main cases audited, 0 gated
                      mismatches, mutation 20/20.
  GAPI10              certify9.py present, METHODS == ('lr', 'anytime'), default 'lr'; certify9(method='anytime') answers as
                      certify8 on a probe; certify8 / anytimemargin byte-identical to BRUTE_SOURCE_FREEZE_021, certify7 to
                      019; host-agnostic source scan of certify9 + lrregion; API_CHECK_023 passed (4 smoke-api cases);
                      test_certify9_0200.py and test_lrregion_0200.py all ok inside GTI.
  G_recount           every arm's false / certificate counts, windows and summaries recounted from the traces; RGL4
                      bound rule T = min(m_a(b; 0.02, 0.005), witness w + D_n - 1) recomputed from the records; T == RGL4 m;
                      realized flips; crossings; anytime boundary == brute.anytimemargin.anytime_boundary.
  G10                 390 cases + 120 prefix28 records, seal complete, traces 88 steps (prefix 28), unknown > 0 fraction
                      <= 1% for every support kind.
  G12                 REPRODUCIBILITY_023 G12_pass, 60 expected, main sha == transfer seal (reproset byte-identical).
  G13                 freeze chain holds; tau6; RG4 by the frozen v0.12.0 rg_arm; RGL4 / RGNA4 / RGNB4 / RGN4_or certificates
                      by the frozen study-019 cert_arm from the recorded supports; frozen sources unchanged; seal binds plan
                      and freeze.
  GTI                 TEST_SUITE_023 verdict passed (declared K_0190, clause vi tooling order) and tracked tree clean at start.
  G_RT                streams inside the 7,200 s cap, not stopped; watchdog whole run; kill drill <= 15 s.
  G_HB                max heartbeat gap <= 10 s.
A gate whose inputs are missing or incomplete FAILS with reason INCOMPLETE_INPUT (STUDY_BUDGET if a stop fired).
Reports (non-gated, plan non_gated_reports): R_ratio_RGL4_RGNB4, R_eps_compare (RGL4 vs RGNA4 at eps 0 / 0.01), R_early28,
R_attain (which n attains T per step), R_stress, R_step_wall, R_C_curve, R_coverage, R_boundary, R_first_cert,
R_resume_drill, R_rates, R_heartbeat_attribution.
  PYTHONPATH=. python scripts/make_gates_023.py [--study-dir D] [--check] [--smoke]"""
from __future__ import annotations
import argparse,json,math,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common_023 import STUDY_DIR,PLAN,FREEZE,load,dumps,write_new,check,sha,check_freeze,TAU6
from experiments.brute_study_014 import sp8_steps
import experiments.brute_study_014 as S14
import experiments.brute_study_019 as S19
import subprocess
import experiments.brute_study_023 as S20
from brute.anytimemargin import anytime_boundary
from experiments import v0200_reference as REF
from scripts.make_gates_015 import wrong,opt
from scripts.make_gates_018 import cp_upper,p_exceed
from scripts.run_study_023 import STREAMS as RUN_STREAMS,CAP

STEPS=88;FB=4;SLOTS=176;LATE=(45,88);EARLY=28;PREFIX=28;EXPECTED={'main':360,'stress':30};REPRO_EXPECTED=60
FROZEN_CI=(0.214962,0.317332)
ARMS=('RG4','RGL4','RGNA4','RGNB4','RGN4_or');ALL_ARMS=('SP8',)+ARMS
D_TABLE=[3,4,5,7];DELTA_A=0.005
def arms(c):return ('RG4','RGL4','RGNA4')+(('RGNB4',) if c['eps']==0.02 else ())+('RGN4_or',)
def noisy_arms(c):return arms(c)[1:]
def all_arms(c):return ('SP8',)+arms(c)
STREAMS=('transfer','repro','gti','g11');BUDGETS={k:v[1] for k,v in RUN_STREAMS.items()}
EPS=(0.0,0.01,0.02,0.05)
API_EXPECT={'kind':'probabilistic','delta':0.01,'conditional_on':'running flips <= m(b) and n* <= family_bound'}
API8_EXPECT={'kind':'probabilistic','delta':0.01,'conditional_on':'running flips <= m_a(b) and n* <= family_bound','anytime':True}
API9_METHODS=('lr','anytime')
HOST_BANNED=('import os','socket','threading','subprocess','open(','multiprocessing')


def ck(c):return f"{c['block']}/{c['family']}/{c['seed']}/{c['eps']}"
def is_main(c):return c['eps'] in (0.0,0.01,0.02) and c['block']!='stress'
def is_noisy(c):return c['eps'] in (0.01,0.02)


def beats(d,t0):
    p=Path(d)/'HEARTBEAT_023.jsonl'
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
    for arm in arms(c):
        A=c['certifiers'][arm]
        flags=all(len(r['certificate'])==2 and r['wrong'][b]==(r['certificate'][b] is not None and r['certificate'][b]!=act[i][b]) for i,r in enumerate(A['trace']) for b in (0,1)) if A['trace'] and 'wrong' in A['trace'][0] else True
        out.append((arm,A['false_certificates'],wrong(A['trace'],act),flags))
    return out


def _dlist(d):
    """HN_RECOUNT stores D as {'1':3,'2':4,...}; normalise to [D_1..D_4] (a list passes through)."""
    if isinstance(d,dict):
        try:return [d[k] for k in sorted(d,key=int)]
        except (ValueError,TypeError):return None
    return d


def lr_check(c,lr,steps,where='lr'):
    """RGL4 bound rule recomputed from the record: T[i] = min(m_a[bits_i], min over witnesses (w + D_n - 1)); attain; D."""
    bad=[]
    if lr.get('D')!=D_TABLE:bad.append((where,'D',lr.get('D')))
    if lr.get('delta_L')!=0.005 or lr.get('delta_a')!=DELTA_A:bad.append((where,'deltas'))
    if lr.get('anytime_boundary')!=anytime_boundary(c['B'],0.02,DELTA_A):bad.append((where,'anytime_boundary'))
    T=lr.get('T') or [];bits=c['prefix_bits'];ba=lr.get('anytime_boundary') or []
    if len(T)!=steps or any(len(lr.get(k) or [])!=steps for k in ('attain','witnesses','witness_unknowns','witness_calls')):return bad+[(where,'lengths')]
    for i in range(steps):
        W=lr['witnesses'][i];ma=ba[bits[i]]
        want=min([ma]+[w['w']+D_TABLE[w['n']-1]-1 for w in W])
        if T[i]!=want:bad.append((where,'T',i+1,T[i],want))
        if lr['attain'][i]!=(W[-1]['n'] if W else None):bad.append((where,'attain',i+1))
        if i and T[i]<T[i-1]:bad.append((where,'T_monotone',i+1))
    return bad


def cert_counts(c):
    bad=[];Sm=c['summary']
    tr={a:c['certifiers'][a]['trace'] for a in arms(c)}|{'SP8':[{'step':t,'certificate':cert} for t,a,cert,_,_,_ in sp8_steps(c)]}
    for arm in arms(c):
        A=c['certifiers'][arm];n=sum(x is not None for r in A['trace'] for x in r['certificate'])
        if A['certificates']!=n:bad.append((arm,'trace',A['certificates'],n))
        if Sm['false'].get(arm)!=A['false_certificates']:bad.append((arm,'summary_false',Sm['false'].get(arm),A['false_certificates']))
    if set(c['certifiers'])!=set(arms(c)) or set(Sm['certificates'])!=set(all_arms(c)):bad.append(('arms','set',sorted(c['certifiers']),sorted(Sm['certificates'])))
    for arm in all_arms(c):
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
    if c['anytime_crossing']!=(c['anytime_crossing_bit'] is not None):bad.append(('noise','anytime_crossing',c['anytime_crossing'],c['anytime_crossing_bit']))
    if c['anytime_boundary']!=anytime_boundary(c['B'],c['eps_bar'],c['delta']):bad.append(('noise','anytime_boundary'))
    bad+=lr_check(c,c['lr'],STEPS)
    if c['lr'].get('T')!=c['noisy']['RGL4']['m']:bad.append(('lr','T_is_RGL4_m'))
    return bad


def prefix_check(c):
    """GLR (e) for one eps-0.02 main case: [] if the prefix28 record equals steps 1..28 of the 88-step RGL4 run."""
    p=c.get('prefix28')
    if not p:return ['prefix28 missing']
    full=sup(c,'RGL4');tr=c['certifiers']['RGL4']['trace'];bad=[]
    if p.get('actions')!=PREFIX:bad.append('actions')
    if p['support']!=full['support'][:PREFIX]:bad.append('support')
    if p['unknown']!=full['unknown'][:PREFIX]:bad.append('unknown')
    if p['m']!=full['m'][:PREFIX]:bad.append('m')
    pc=[x['certificate'] for x in p['certifier']['trace']]
    if len(pc)!=PREFIX or pc!=[x['certificate'] for x in tr[:PREFIX]]:bad.append('certificates')
    if p.get('identical') is not True:bad.append('recorded flag')
    pl=p.get('lr') or {}
    for k in ('T','attain','witnesses','witness_unknowns','witness_calls'):
        if pl.get(k)!=c['lr'][k][:PREFIX]:bad.append('lr '+k)
    if p['m']!=pl.get('T'):bad.append('lr T is m')
    return bad


def sup(c,arm):
    x=c['noisy'][arm]
    return c['noisy'][x['shared_with']] if x.get('shared_with') and x.get('support') is None else x


def api9_probe():
    """certify9 default method, METHODS, and method='anytime' == certify8 on a small probe."""
    try:
        import inspect
        from brute.api import certify9 as C9
        from brute.api.certify8 import certify8
        init,acts,obs=(0,1),[0,1,0,1,1,0,0,1,1,1,0],[(0,1),(1,None),(0,1),(1,0),(None,1),(0,1),(1,0),(0,0),(1,1),(0,1),(1,None)]
        d=C9.certify9(init,acts,obs);a=C9.certify9(init,acts,obs,method='anytime');r8=certify8(init,acts,obs)
        same=all(a.get(k)==r8.get(k) for k in ('supports','unknown','certificates','status','m','steps'))
        dm=inspect.signature(C9.certify9).parameters['method'].default
        return {'api':d.get('api'),'methods':list(C9.METHODS),'default_method':dm,'default_answer_method':d.get('method'),
                'anytime_equals_certify8':same,'soundness_lr':d.get('soundness'),'error':None}
    except Exception as e:return {'error':f'{type(e).__name__}: {e}'}


def build(study=STUDY_DIR,smoke=False):
    study=Path(study);plan=load(PLAN);C=plan['criteria']
    blk=opt(study/'transfer'/'SCIENTIFIC.json');seal=opt(study/'transfer'/'SEAL.json')
    if blk is not None:check(seal['scientific_sha256']==sha(study/'transfer'/'SCIENTIFIC.json'),'transfer: SCIENTIFIC does not match SEAL')
    stop=opt(study/'STOP_023.json');stop_o=opt(study/'STOP_023_ORCHESTRATOR.json');done=opt(study/'RUN_DONE_023.json')
    state=opt(study/'RUN_STATE_023.json') or {'stopped':{},'spent':{},'completed_at':{}}
    t0=float((study/'RUN_T0').read_text().split()[0]) if (study/'RUN_T0').exists() else None
    paired=opt(study/'PAIRED_ANALYSIS_023.json');repro=opt(study/'REPRODUCIBILITY_023.json')
    aud=opt(study/'SECOND_IMPLEMENTATION_023.json');ts=opt(study/'TEST_SUITE_023.json');drill=opt(study/'KILL_DRILL_023.json')
    if drill is None:drill=opt(ROOT/'results/smoke-023/KILL_DRILL_023.json')
    resume=opt(ROOT/'results/smoke-023/RESUME_DRILL_023.json');apick=opt(ROOT/'results/smoke-023/API_CHECK_023.json')
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
    tot={};bad_rc=[];bad_cc=[];bad_fl=[]
    for c in allc:
        sub='stress' if c['eps']==0.05 else 'main'
        for arm,rec,re,fl in recount(c,ACT[id(c)]):
            RC[(id(c),arm)]=re
            x=tot.setdefault(sub,{}).setdefault(arm,{'recorded_false':0,'recomputed_false':0,'records':0,'mismatching_records':0})
            x['recorded_false']+=rec;x['recomputed_false']+=re;x['records']+=1
            if rec!=re:x['mismatching_records']+=1;bad_rc.append((ck(c),arm,rec,re))
            if not fl:bad_fl.append((ck(c),arm))
        bad_cc+=[(ck(c),)+tuple(b) for b in cert_counts(c)]
    cover=sorted(set(ALL_ARMS)-set(tot.get('main',{})))
    bad_pf=[(ck(c),b) for c in allc if 'prefix28' in c and c['eps']!=0.02 for b in ['prefix28 on a non-0.02 case']]
    gate('G_recount',not bad_rc and not bad_cc and not bad_fl and not bad_pf and bool(allc) and not cover,{'misplaced_prefix_records':bad_pf[:20],'per_subset_arm':tot,'mismatches':bad_rc[:50],
         'wrong_flag_mismatches':bad_fl[:50],'certificate_and_lr_mismatches':bad_cc[:50],'arms_not_recounted':cover},why=wb)
    zero=lambda cs,arm:all(c['certifiers'][arm]['false_certificates']==0 and RC[(id(c),arm)]==0 for c in cs)
    casefalse=lambda c,arm:RC[(id(c),arm)]>0
    P=paired or {}
    def pv(k):x=P.get(k) or {};return x.get('mean'),x.get('ci95')
    wp=wb+incomplete(False,files=(('PAIRED_ANALYSIS_023.json',paired),))
    # GLR (headline)
    k=sum(casefalse(c,'RGL4') for c in noisy);ub=cp_upper(k,len(noisy));m2,ci2=pv('C_late_RGL4_eps2');dm,dci=pv('dC_late_RGL4_RGNA4_eps2')
    pfb=[(ck(c),pb_) for c in e2 for pb_ in prefix_check(c)];exp_pref=len(e2) if smoke else 120
    glr={'a_zero_false_all_noisy_main':(bool(noisy) if smoke else len(noisy)==240) and zero(noisy,'RGL4'),
         'b_cp_upper_le_0.05':ub is not None and ub<=0.05,
         'c_C_late_eps2_mean_ge_0.35_and_ci_lower_gt_0.30':m2 is not None and ci2 is not None and m2>=0.35 and ci2[0]>0.30,
         'd_dC_late_RGL4_RGNA4_eps2_mean_ge_0.08_and_ci_lower_gt_0.05':dm is not None and dci is not None and dm>=0.08 and dci[0]>0.05,
         'e_prefix28_identical_all_eps2':len(e2)==exp_pref and sum('prefix28' in c for c in e2)==exp_pref and not pfb}
    gate('GLR',all(glr.values()),{'clauses':glr,'noisy_cases':len(noisy),'case_false':k,'case_false_examples':[ck(c) for c in noisy if casefalse(c,'RGL4')][:20],
         'false_certificates_RGL4':sum(RC[(id(c),'RGL4')] for c in noisy),'cp_upper_95_one_sided':ub,
         'C_late_RGL4_eps2':(m2,ci2),'dC_late_RGL4_RGNA4_eps2':(dm,dci),'C_late_RGNA4_eps2':pv('C_late_RGNA4_eps2'),
         'C_late_RGNB4_eps2':pv('C_late_RGNB4_eps2'),'C_late_RGN4_or_eps2':pv('C_late_RGN4_or_eps2'),
         'prefix28':{'eps2_cases':len(e2),'records':sum('prefix28' in c for c in e2),'mismatches':pfb[:30]}},why=wp)
    # GLR_lemma
    def _git(*a):return subprocess.run(['git',*a],cwd=ROOT,capture_output=True,text=True)
    lem=_git('log','--format=%H','--diff-filter=A','--','docs/research/v0.20.0/LR_LEMMA_023.md').stdout.split()
    lrc=_git('log','--format=%H','--','brute/lrregion.py').stdout.split()
    first_lr=lrc[-1] if lrc else None
    before=bool(lem) and first_lr is not None and lem[-1]!=first_lr and _git('merge-base','--is-ancestor',lem[-1],first_lr).returncode==0
    try:rd=REF.ref_D()
    except Exception as e_:rd=f'{type(e_).__name__}: {e_}'
    hn=opt(ROOT/'results/diag-023/HN_RECOUNT_023.json')
    lm={'lemma_committed_before_rgl4_code':before,'D_table_exact_3_4_5_7':rd==D_TABLE,'hn_recount_passed':bool(hn) and hn.get('PASS') is True and _dlist(hn.get('D'))==D_TABLE}
    gate('GLR_lemma',all(lm.values()),{'clauses':lm,'lemma_commit':lem[-1] if lem else None,'first_lrregion_commit':first_lr,'ref_D':rd,
         'hn_recount':None if hn is None else {k_:v for k_,v in hn.items() if k_ in ('PASS','H','D')}})
    me,cie=pv('C_late_RGNA4_eps2')
    gate('GAS_frozen_control',cie is not None and cie[0]<=FROZEN_CI[1] and cie[1]>=FROZEN_CI[0],{'C_late_RGNA4_eps2':(me,cie),'study021_ci':list(FROZEN_CI),
         'rule':'95% CI intersects the study-021 CI (inclusive)'},why=wp)
    gate('GS_a10',bool(e0) and zero(e0,'RGL4'),{'eps0_cases':len(e0),'RGL4_recorded_false':sum(c['certifiers']['RGL4']['false_certificates'] for c in e0),
         'RGL4_recomputed_false':sum(RC[(id(c),'RGL4')] for c in e0),'RGNA4_false_eps0':sum(RC[(id(c),'RGNA4')] for c in e0),'RG4_false_eps0':sum(RC[(id(c),'RG4')] for c in e0)},why=wb)
    # GS_ref10
    md=(aud or {}).get('mutation_test') or {};ngated=len(main)
    ref={'results_sha_matches_seal':bool(aud) and bool(seal) and aud.get('results_sha256')==seal.get('results_sha256'),
         'all_gated_cases_audited':bool(aud) and aud.get('gated_cases_expected')==ngated and aud.get('gated_cases_audited')==ngated and ngated>0,
         'zero_gated_mismatching':bool(aud) and aud.get('gated_mismatching_cases')==0,
         'mutation_20_of_20':md.get('passed') is True and md.get('injected')==20 and md.get('distinct_cases')==20 and md.get('detected_injected')==20 and md.get('flagged_not_injected')==0}
    gate('GS_ref10',all(ref.values()),{'clauses':ref,'gated_expected':ngated,'report':None if aud is None else {k:aud[k] for k in aud if k not in ('mismatches','mutation_test','events')},
         'mutation':{k:v for k,v in md.items() if k!='details'},'wording':'second implementation by the same author'},
         why=wb+incomplete(False,files=(('SECOND_IMPLEMENTATION_023.json',aud),),streams=('g11',)))
    # GAPI10
    PM=(ts or {}).get('per_module') or {};mods_={m:PM.get(m) or {} for m in ('test_certify9_0200.py','test_lrregion_0200.py')}
    f19=(opt(ROOT/'experiments/BRUTE_SOURCE_FREEZE_019.json') or {}).get('sha256_files',{})
    f21=(opt(ROOT/'experiments/BRUTE_SOURCE_FREEZE_021.json') or {}).get('sha256_files',{});p9=api9_probe()
    c9=ROOT/'brute/api/certify9.py';src9=(c9.read_text() if c9.exists() else '')+((ROOT/'brute/lrregion.py').read_text() if (ROOT/'brute/lrregion.py').exists() else '')
    fr=lambda f,rel:f.get(rel) is not None and f.get(rel)==sha(ROOT/rel)
    api={'certify9_present':c9.exists() and p9.get('api')=='brute.certify/9','methods_lr_anytime':p9.get('methods')==list(API9_METHODS),
         'default_method_lr':p9.get('default_method')=='lr' and p9.get('default_answer_method')=='lr','anytime_equals_certify8':p9.get('anytime_equals_certify8') is True,
         'certify8_unchanged':fr(f21,'brute/api/certify8.py') and fr(f21,'brute/anytimemargin.py'),'certify7_unchanged':fr(f19,'brute/api/certify7.py'),
'host_agnostic_source_scan':bool(src9) and not any(x in src9 for x in HOST_BANNED),
         'smoke_api_supports_equal':bool(apick) and apick.get('passed') is True and apick.get('cases_checked')==4,
         'tests_ok_inside_gti':all(m.get('returncode')==0 and len(m.get('results') or {})>=3 and all(v[0]=='ok' for v in m['results'].values()) for m in mods_.values())}
    gate('GAPI10',all(api.values()),{'clauses':api,'results':{k:v.get('results') for k,v in mods_.items()},'certify9_probe':p9,
         'api_check':None if apick is None else {k:v for k,v in apick.items() if k!='cases'}},why=incomplete(False,files=(('TEST_SUITE_023.json',ts),),streams=('gti',)))
    # G10
    tl={'SP8':all(len(c['arms']['SP8']['trace'])==STEPS for c in allc),**{a:all(len(c['certifiers'][a]['trace'])==STEPS for c in allc if a in arms(c)) for a in ARMS},
        'prefix28':all(len(c['prefix28']['support'])==PREFIX and len(c['prefix28']['certifier']['trace'])==PREFIX for c in e2 if 'prefix28' in c)}
    npref=sum('prefix28' in c for c in e2)
    unk={}
    for c in allc:
        for kind,X in (('bounded4',c['bounded']['4']),)+tuple((a,sup(c,a)) for a in noisy_arms(c))+((('prefix28',c['prefix28']),) if 'prefix28' in c else ()):
            u=unk.setdefault(kind,[0,0])
            for row in X['unknown']:
                for x in row:u[0]+=1;u[1]+=x>0
    frac={k:(b/a if a else None) for k,(a,b) in unk.items()}
    g10ok=bool(allc) and len(allc)==expected and npref==exp_pref and bool(seal) and seal.get('complete') and all(tl.values()) and all(f is not None and f<=0.01 for f in frac.values())
    gate('G10',g10ok,{'prefix28_records':npref,'prefix28_expected':exp_pref,'cases':len(allc),'expected':expected,'by_part':{'main':len(main),'stress':len(stress)},'traces_88_steps':tl,
         'unknown_gt0_fraction':{k:None if f is None else round(f,6) for k,f in frac.items()},'queries':{k:{'queries':a,'unknown_gt0':b} for k,(a,b) in unk.items()}},why=wb)
    # G12
    R0=(repro or {}).get('blocks',{}).get('transfer',{})
    g12ok=bool(repro) and repro['G12_pass'] and bool(seal) and R0.get('main_scientific_sha256')==seal['scientific_sha256'] and R0.get('expected')==(11 if smoke else REPRO_EXPECTED)
    gate('G12',g12ok,None if repro is None else repro['blocks'],why=wb+incomplete(False,files=(('REPRODUCIBILITY_023.json',repro),),streams=('repro',)))
    # G13
    try:check_freeze();fz=True;fz_err=None
    except Exception as exc_:fz=False;fz_err=f'{type(exc_).__name__}: {exc_}'
    F={n:(opt(ROOT/f'experiments/BRUTE_SOURCE_FREEZE_0{n}.json') or {}).get('sha256_files',{}) for n in (14,18,19,20,21)}
    rg_bad=[ck(c) for c in allc if S14.rg_arm(sp8_steps(c),{'4':c['bounded']['4']},FB,c['burn_in'])!=c['certifiers']['RG4']]
    rgn_bad=[(ck(c),a) for c in allc for a in noisy_arms(c) if S19.cert_arm([(s_[0],s_[1]) for s_ in sp8_steps(c)],[s_[5] for s_ in sp8_steps(c)],sup(c,a)['support'],c['noisy'][a]['m'],c['burn_in'],2)!=c['certifiers'][a]]
    g13={'freeze_chain_holds':fz,'cases_use_plan013_tau6':bool(allc) and all(c.get('tau6')==TAU6 for c in allc),
         'rg_sp8_are_frozen_v0120':S20.rg_arm is S14.rg_arm and S20.sp8_steps is S14.sp8_steps and F[14].get('experiments/brute_study_014.py')==sha(ROOT/'experiments/brute_study_014.py'),
         'cert_arm_is_frozen_v0170':S20.cert_arm is S19.cert_arm and F[19].get('experiments/brute_study_019.py')==sha(ROOT/'experiments/brute_study_019.py'),
         'v0170_sources_frozen':all(F[19].get(p)==sha(ROOT/p) for p in ('experiments/brute_study_019.py','brute/seqmargin.py')),
         'v0180_sources_frozen':all(F[20].get(p)==sha(ROOT/p) for p in ('experiments/brute_study_020.py','brute/perbit.py')),
         'v0190_sources_frozen':all(F[21].get(p)==sha(ROOT/p) for p in ('experiments/brute_study_021.py','brute/anytimemargin.py','brute/api/certify8.py')),
         'rg4_reproduces':bool(allc) and not rg_bad,'cert_rule_reproduces_RGL4_RGNA4_RGNB4_RGN4_or':bool(allc) and not rgn_bad,
         'seal_of_current_plan_and_freeze':bool(seal) and seal['plan_sha256']==sha(PLAN) and FREEZE.exists() and seal.get('freeze_sha256')==sha(FREEZE)}
    g13ok=all(g13.values()) if not smoke else all(v for k,v in g13.items() if k not in ('freeze_chain_holds','seal_of_current_plan_and_freeze'))
    gate('G13',g13ok,{'clauses':g13,'rg4_not_reproduced':rg_bad[:20],'rgn_not_reproduced':rgn_bad[:20],'freeze_error':fz_err,'smoke_dry_run_relaxed':smoke},why=wb)
    # GTI
    V=(ts or {}).get('verdict');gti={'verdict_passed':bool(V) and V['passed'],'clause_vi_tooling_order':bool(V) and V['clauses'].get('vi_tooling_order') is True,
         'K_0190_declared':bool(V) and '0190' in (V.get('k_rules') or {}),'tracked_tree_clean_at_start':bool(ts) and ts.get('tracked_tree_dirty') is False}
    gate('GTI',all(gti.values()),None if ts is None else {'clauses':gti,'verdict':V,'head':ts.get('head'),'tracked_tree_dirty':ts.get('tracked_tree_dirty'),
         'dirty_tracked_files':ts.get('dirty_tracked_files'),'workers':ts.get('workers'),
         'clean_tag_runs':{k:(None if v is None else v.get('results')) for k,v in (ts.get('clean_tag_runs') or {}).items()},'run':'in-cap'},
         why=incomplete(False,files=(('TEST_SUITE_023.json',ts),),streams=('gti',)))
    # G_RD
    rcl=(resume or {}).get('clauses') or {}
    g['R_resume_drill']={'gated':False,'pass':None,'observed':{'drill_passed':bool(resume) and resume.get('passed') is True and len(rcl)==4 and all(rcl.values()),
         'report':None if resume is None else {k:v for k,v in resume.items() if k not in ('per_case',)},'label':'process control (not a plan criterion in 023)'}}
    # G_RT / G_HB
    hb=heartbeat(study,t0);comp=state.get('completed_at',{})
    end=(t0+done['elapsed_s']) if (t0 is not None and done) else (t0+CAP if t0 is not None else None)
    late={s:(round(comp[s]-t0,1) if s in comp and t0 is not None else None) for s in STREAMS}
    i_streams={s:late[s] is not None and late[s]<=CAP and s not in stopped for s in STREAMS}
    rt={'i_streams_inside_cap_not_stopped':t0 is not None and all(i_streams.values()),
        'ii_watchdog_whole_run':bool(hb) and t0 is not None and hb['first_wall']<=t0+60 and hb['last_wall']>=end-10,
        'iii_kill_drill_latency_le_15s':bool(drill) and drill.get('kill_latency_s') is not None and drill['kill_latency_s']<=15 and not drill.get('survivors')}
    g['G_RT']={'gated':True,'pass':all(rt.values()),'observed':{'clauses':rt,'streams':i_streams,'completion_s_after_t0':late,
         'stopped_streams':stopped,'stop_watchdog':stop,'stop_orchestrator':stop_o,'run_done':done,
         'kill_drill':None if drill is None else {k:drill.get(k) for k in ('kill_latency_s','survivors','sigkill_used','fire_delay_s','label')},
         'spent_s':{k:round(v) for k,v in state.get('spent',{}).items()},'cap_s':CAP},
         **({} if all(rt.values()) else {'reason':'STUDY_BUDGET' if fired else 'clauses failed: '+', '.join(k for k,v in rt.items() if not v)})}
    g['G_HB']={'gated':True,'pass':bool(hb) and hb['max_gap_s'] is not None and hb['max_gap_s']<=10,
         'observed':{'max_gap_s':None if not hb else hb['max_gap_s'],'beats':None if not hb else hb['beats'],'gaps_over_10s_attributed':None if not hb else hb['gaps_over_10s']}}
    # ---- reports (non_gated_reports)
    def per_eps(arm,cs,eps=EPS):
        o={}
        for e in eps:
            x=[c for c in cs if c['eps']==e and (arm=='SP8' or arm in arms(c))]
            if not x:continue
            kf=sum(casefalse(c,arm) for c in x)
            o[str(e)]={'cases':len(x),'false_certificates':sum(RC[(id(c),arm)] for c in x),'case_false':kf,'case_false_rate':round(kf/len(x),6),
                       'cp_upper_95_one_sided':cp_upper(kf,len(x)),'anytime_crossings':sum(c['anytime_crossing'] for c in x),'coverage_full':round(sum(c['summary']['certificates'][arm] for c in x)/(len(x)*SLOTS),6),
                       'coverage_late':round(sum(c['summary']['certificates_late'][arm] for c in x)/(len(x)*88),6),
                       'coverage_early28':round(sum(c['summary']['certificates_early28'][arm] for c in x)/(len(x)*56),6),'crossings':sum(c['crossing'] for c in x)}
        return o
    subs=('eps0','eps1','eps2','noisy','stress')
    gate('R_C_curve',None,{s:P.get('C_curve_'+s) for s in subs}|{'label':'per step t = 1..88: mean certificates / 2 (PAIRED_ANALYSIS_023)'},gated=False)
    gate('R_stress',None,{'cases':len(stress),**{a:per_eps(a,stress).get('0.05') for a in ('RG4','RGL4','RGNA4','RGN4_or')},'cases_with_anytime_crossing':sum(c['anytime_crossing'] for c in stress),
         'RGL4_false_certificates':sum(RC[(id(c),'RGL4')] for c in stress),'RGL4_case_false':sum(casefalse(c,'RGL4') for c in stress),
         'RGL4_case_false_with_lr_anytime_crossing':sum(casefalse(c,'RGL4') for c in stress if c['lr']['anytime_crossing_bit'] is not None),
         'RGNA4_case_false':sum(casefalse(c,'RGNA4') for c in stress),'label':'outside the attestation; no guarantee'},gated=False)
    gate('R_ratio_RGL4_RGNB4',None,{'C_late_RGL4_eps2':pv('C_late_RGL4_eps2'),'C_late_RGNB4_eps2':pv('C_late_RGNB4_eps2'),'ratio_late':P.get('ratio_late_RGL4_RGNB4_eps2'),
         'dC_late_RGL4_RGNB4_eps2':pv('dC_late_RGL4_RGNB4_eps2'),'dC_early28_RGL4_RGNB4_eps2':pv('dC_early28_RGL4_RGNB4_eps2'),
         'label':'RGNB4 is planned-B (not anytime); comparison only'},gated=False)
    gate('R_eps_compare',None,{s_:{'C_late_RGL4':pv('C_late_RGL4_'+s_),'C_late_RGNA4':pv('C_late_RGNA4_'+s_),'dC_late_RGL4_RGNA4':pv('dC_late_RGL4_RGNA4_'+s_),
         'dC_early28_RGL4_RGNA4':pv('dC_early28_RGL4_RGNA4_'+s_)} for s_ in ('eps0','eps1','eps2','noisy','stress')},gated=False)
    gate('R_early28',None,{a:{s_:pv(f'C_early28_{a}_{s_}') for s_ in subs} for a in ARMS+('SP8',)},gated=False)
    att={}
    for e in EPS:
        x=[c for c in allc if c['eps']==e]
        if not x:continue
        h={};ps=[0]*STEPS
        for c in x:
            for i,n_ in enumerate(c['lr']['attain']):
                h[str(n_)]=h.get(str(n_),0)+1;ps[i]+=n_ is not None
        att[str(e)]={'cases':len(x),'attain_n_histogram_over_steps':h,'fraction_steps_witness_lowered':round(sum(ps)/(STEPS*len(x)),6),
                     'per_step_cases_with_witness':ps,'witness_unknowns':sum(sum(c['lr']['witness_unknowns']) for c in x),
                     'witness_calls':sum(sum(c['lr']['witness_calls']) for c in x)}
    gate('R_attain',None,att|{'label':'which n attains T; None = the anytime bound m_a(b) was the minimum'},gated=False)
    sw=[c['lr'].get('step_wall_informational') for c in allc]
    gate('R_step_wall',None,{'RGL4_step_wall_s':None if not sw or any(w is None for w in sw) else {'mean':round(sum(sw)/len(sw),6),'max':max(sw),'cases':len(sw)},
         'label':'informational wall clock, unsealed'},gated=False)
    gate('R_coverage',None,{a:per_eps(a,allc) for a in ('RG4','RGL4','RGN4_or','SP8','RGNA4','RGNB4')}|
         {'C_late':{a:{s:pv(f'C_late_{a}_{s}') for s in subs} for a in ('RG4','RGL4','RGN4_or','SP8','RGNA4','RGNB4')},
          'C_full':{a:{s:pv(f'C_full_{a}_{s}') for s in subs} for a in ARMS},
          'labels':{'RG4':'expected > 0 false under noise','RGN4_or':'oracle m = realized flips, evaluator-only'}},gated=False)
    bd={}
    for e in EPS:
        x=[c for c in allc if c['eps']==e]
        if not x:continue
        ma=[mb for c in x for mb in c['noisy']['RGNA4']['m']];tl=[t_ for c in x for t_ in c['lr']['T']];mp=[mb for c in x if 'RGNB4' in c['noisy'] for mb in c['noisy']['RGNB4']['m']]
        bd[str(e)]={'cases':len(x),'mean_m_a_b':round(sum(ma)/len(ma),6),'mean_T_RGL4':round(sum(tl)/len(tl),6),'T_below_m_a_rate':round(sum(t_<m_ for t_,m_ in zip(tl,ma))/len(tl),6),'mean_planned_m_b':round(sum(mp)/len(mp),6) if mp else None,
                    'mean_fixed_m':round(sum(c['m'] for c in x)/len(x),6),'anytime_crossing_rate':round(sum(c['anytime_crossing'] for c in x)/len(x),6),
                    'planned_crossing_rate':round(sum(c['crossing'] for c in x)/len(x),6),
                    'observed_flips_gt_m_rate':round(sum(c['realized_flips']>c['m'] for c in x)/len(x),6),
                    'mean_bound_P_flips_gt_m':round(sum(p_exceed(c['B'],e,c['m']) for c in x)/len(x),8),'B_range':[min(c['B'] for c in x),max(c['B'] for c in x)]}
    gate('R_boundary',None,bd,gated=False)
    gate('R_first_cert',None,{'label':'informational, ungated; SP8 censored at the inherited CENSOR = 45 (ambiguous at 88 steps; deviation addendum)',
         'mean_first_cert_step':{a:{str(e):(lambda x:None if not x else round(sum(x)/len(x),3))([c['summary']['first_cert_step'][a] for c in allc if c['eps']==e and a in c['summary']['first_cert_step']]) for e in EPS} for a in ALL_ARMS}},gated=False)
    hba=opt(study/'HEARTBEAT_ATTRIBUTION_023.json')
    gate('R_heartbeat_attribution',None,{'watchdog_gaps_over_10s':None if not hb else hb['gaps_over_10s'],
         'sentinel_attribution':None if hba is None else {k:hba.get(k) for k in ('max_watchdog_gap_s','max_sentinel_tick_gap_s','class_counts','gaps_over_10s','sentinel_records')},
         'label':'Inferred; diagnostic, changes no verdict'},gated=False)
    raw=opt(study/'transfer'/'RESULTS.json');RW={ck(c):c for c in raw['cases']} if raw else {}
    def solver_cost():
        W=[RW.get(ck(c),{}).get('region_wall_informational') for c in allc]
        if not W or any(w is None for w in W):return 'RESULTS.json absent or incomplete: timing not reported'
        return {a:{'cases':sum(a in w for w in W),'total_s':round(sum(w[a] for w in W if a in w),3),'ms_per_step':round(1000*sum(w[a] for w in W if a in w)/(max(1,sum(a in w for w in W))*STEPS),4)} for a in ARMS+('prefix28',)}|{'timing_source':'transfer/RESULTS.json (informational, unsealed)'}
    rm=opt(ROOT/'docs/research/v0.20.0/RATE_MATH_023.json');proj=(rm or {}).get('streams') or {}
    gate('R_rates',None,{s_:{'spent_s':round(state.get('spent',{}).get(s_,0),1),'budget_s':BUDGETS[s_],'projected_s':(proj.get(s_) or {}).get('projected_s'),
         'raw_projection_s':(proj.get(s_) or {}).get('raw_s'),'fraction_of_budget':round(state.get('spent',{}).get(s_,0)/BUDGETS[s_],3)} for s_ in STREAMS}|
         {'solver_cost':solver_cost() if allc else None,'rate_math':None if rm is None else {'file':'docs/research/v0.20.0/RATE_MATH_023.json','sha256':sha(ROOT/'docs/research/v0.20.0/RATE_MATH_023.json'),'fits':rm.get('fits')}},gated=False)
    gated=[k for k,v in g.items() if v['gated']]
    return {'schema':'brute.gates.v20_0','study':plan['study'],'plan_sha256':sha(PLAN),'smoke_dry_run':smoke,'criteria_registered':sorted(C),
            'criteria_scored':sorted(gated),'scientific_sha256':None if seal is None else seal['scientific_sha256'],'stop_rule_fired':fired,'gates':g,
            'passed':[k for k in gated if g[k]['pass']],'failed':[k for k in gated if g[k]['pass'] is False],
            'pending':[k for k in gated if g[k]['pass'] is None],'all_gated_pass':all(g[k]['pass'] for k in gated),
            'GLR':g['GLR']['pass'],'G_RT':g['G_RT']['pass'],'G_HB':g['G_HB']['pass']}


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--study-dir',default=str(STUDY_DIR));ap.add_argument('--check',action='store_true')
    ap.add_argument('--output',default='GATES_023.json');ap.add_argument('--smoke',action='store_true',help='dry run on a smoke directory; prints only')
    a=ap.parse_args()
    if a.smoke:
        obj=build(Path(a.study_dir),smoke=True)
        print({k:obj[k] for k in ('passed','failed','pending')});print({k:v.get('reason') for k,v in obj['gates'].items() if v.get('reason')});raise SystemExit
    obj=build(Path(a.study_dir));out=Path(a.study_dir)/a.output
    if a.check:check(out.read_bytes()==dumps(obj),out.name+' does not reproduce');print(out.name,'reproduces')
    else:write_new(out,obj);print({k:obj[k] for k in ('passed','failed','pending','all_gated_pass')})
