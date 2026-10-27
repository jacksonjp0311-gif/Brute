"""Evaluate the pre-registered study-018 criteria (BRUTE_PLAN_018: headline GNS_noise_soundness, GN0_control, GS_a6,
G_recount, GS_ref6, GAPI6, G10, G12, G13, GTI, G_RT, G_HB gated; non_gated_reports reported) from sealed artifacts only.
Committed and ledgered (scoring_freeze_018) before the held-out run_start; thresholds are copied from the plan, nothing is
tuned. Adapted from make_gates_017 (frozen, not edited).

Inputs in results/study-018 (D): transfer/{SCIENTIFIC,SEAL}.json (360 main cases at eps 0 / 0.01 / 0.02 then 120 stress
cases at eps 0.05), repro/main/SEAL.json, PAIRED_ANALYSIS_018.json, REPRODUCIBILITY_018.json, SECOND_IMPLEMENTATION_018.json,
TEST_SUITE_018.json, RUN_STATE_018.json, RUN_T0, RUN_DONE_018.json / STOP_018.json / STOP_018_ORCHESTRATOR.json,
HEARTBEAT_018.jsonl, KILL_DRILL_018.json, HEARTBEAT_ATTRIBUTION_018.json (reported only); experiments/BRUTE_SOURCE_FREEZE_018.json.

Scoring choices fixed here, before data:
- Every arm (SP8, RG4, RGN4, RGN4_0, RGN4_or) is scored on the SP8 trajectory. Certificate[b] at step i is false iff
  non-null and different from the evaluator-only latent (noise-free) code (#97 item 2).
- "main" = the 360 cases at eps in {0, 0.01, 0.02}; "noisy" = main at eps in {0.01, 0.02} (240); "stress" = eps 0.05 (120).
- G_recount: every arm of every case: recorded false == recount; recorded 'wrong' flags == recount; certificate counts
  equal trace counts and the summary; summary case_false == (false > 0).
- GNS (headline): (a) RGN4 recorded == recomputed == 0 false on every noisy case with realized_flips <= m;
  (b) exact one-sided 95% Clopper-Pearson upper bound (plan metrics.clopper_pearson) of the RGN4 case-false rate over the
  240 noisy cases (recomputed case-false) <= 0.05; (c) PAIRED C_RGN4_eps2 mean >= 0.10 and ci95 lower > 0.05.
- GN0: on the eps = 0 main cases, RGN4_0 certificate list == RG4 certificate list at every step, AND RGN4 recorded ==
  recomputed == 0 false. Predicted FAIL (#97 item 3). Reported alongside: R_gn0_support (RGN4_0 supports == bounded['4']
  supports at every step of every case, all eps) and R_gn0_post_burn (equality at every step t > burn_in, eps 0).
- GS_a6: RG4 recorded == recomputed == 0 false on the eps = 0 main cases.
- GS_ref6: SECOND_IMPLEMENTATION_018 results_sha256 == transfer SEAL results_sha256; every gated case (main, eps 0 or
  0.02: 240) audited, 0 not reached, 0 gated mismatching; mutation 20 / 20 distinct detected, flagged_not_injected 0;
  g11 not stopped. Mismatches on ungated cases (eps 0.01, stress) are reported only.
- GAPI6: TEST_SUITE_018 per_module['test_api_certify6_0160.py'] returncode 0, >= 4 results, all 'ok';
  brute/api/certify6.py in BRUTE_SOURCE_FREEZE_018; brute.api.certify6.certify6([0, 1], [0, 1], [[0, 1], [1, None]], 8) soundness dict has kind
  'probabilistic', delta 0.01 and conditional_on 'flips <= m and n* <= family_bound'.
- G10: 480 cases, transfer SEAL complete; every trace 44 steps; the fraction of recorded support queries (bounded['4'],
  noisy RGN4 / RGN4_0 / RGN4_or) with unknown > 0 is <= 1% per support kind.
- G12: REPRODUCIBILITY_018 G12_pass, 120 expected, main sha equal to the transfer SEAL.
- G13: check_freeze (018 chain), case tau6 == plan-013 tau6, SEAL of the current plan and freeze, rg_arm / sp8_steps are
  the frozen brute_study_014 functions (sha equal to BRUTE_SOURCE_FREEZE_014), and on every eps = 0 case the recorded
  RG4 arm equals frozen rg_arm recomputed from the recorded SP8 trace and bounded['4'] supports.
- GTI as study-017 (verdict.passed of scripts/run_tests_0160.py). G_RT (i) streams transfer, repro, gti, g11 completed
  <= t0 + 7200 and not stopped; (ii) heartbeat first beat <= t0 + 60 and last >= end - 10; (iii) KILL_DRILL_018 latency
  <= 15 s, no survivors. G_HB: largest gap <= 30 s.
- STUDY_BUDGET: a gate whose inputs are incomplete is FAIL; reason 'STUDY_BUDGET' when a STOP file exists, else
  'INCOMPLETE_INPUT (...)'."""
from __future__ import annotations
import argparse,json,math,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common_018 import STUDY_DIR,PLAN,FREEZE,load,dumps,write_new,check,sha,check_freeze,TAU6
from experiments.brute_study_014 import sp8_steps
import experiments.brute_study_014 as S14
import experiments.brute_study_018 as S18
from scripts.make_gates_015 import wrong,opt
from scripts.run_study_018 import STREAMS as RUN_STREAMS,CAP

STEPS=44;FB=4;CENSOR=45;SLOTS=88;EXPECTED={'main':360,'stress':120}
ARMS=('RG4','RGN4','RGN4_0','RGN4_or');ALL_ARMS=('SP8',)+ARMS
STREAMS=('transfer','repro','gti','g11');BUDGETS={k:v[1] for k,v in RUN_STREAMS.items()}
FAMILIES=('cycle3','switch3','unaliased2','ood4');EPS=(0.0,0.01,0.02,0.05)
API_EXPECT={'kind':'probabilistic','delta':0.01,'conditional_on':'flips <= m and n* <= family_bound'}


def ck(c):return f"{c['block']}/{c['family']}/{c['seed']}/{c['eps']}"
def is_main(c):return c['eps'] in (0.0,0.01,0.02)
def is_noisy(c):return c['eps'] in (0.01,0.02)


def cp_upper(k,n,alpha=0.05):
    """Exact one-sided (1 - alpha) Clopper-Pearson upper bound: p with P(Bin(n, p) <= k) = alpha (1 if k == n)."""
    if n==0:return None
    if k>=n:return 1.0
    def cdf(p):return sum(math.comb(n,i)*p**i*(1-p)**(n-i) for i in range(k+1))
    lo,hi=0.0,1.0
    for _ in range(200):
        mid=(lo+hi)/2
        if cdf(mid)>alpha:lo=mid
        else:hi=mid
    return round(hi,8)


def p_exceed(B,eps,m):
    """P(Bin(B, eps) > m), evaluator-side per-case bound (R_bound)."""
    return 1.0-sum(math.comb(B,i)*eps**i*(1-eps)**(B-i) for i in range(m+1))


def beats(d,t0):
    p=Path(d)/'HEARTBEAT_018.jsonl'
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
        flags=all(r['wrong'][b]==(r['certificate'][b] is not None and r['certificate'][b]!=act[i][b]) for i,r in enumerate(A['trace']) for b in (0,1)) if A['trace'] and 'wrong' in A['trace'][0] else True
        out.append((arm,A['false_certificates'],wrong(A['trace'],act),flags))
    return out


def cert_counts(c):
    bad=[];Sm=c['summary']
    for arm in ARMS:
        A=c['certifiers'][arm];n=sum(x is not None for r in A['trace'] for x in r['certificate'])
        if A['certificates']!=n:bad.append((arm,'trace',A['certificates'],n))
        if Sm['certificates'].get(arm)!=A['certificates']:bad.append((arm,'summary',Sm['certificates'].get(arm),A['certificates']))
        if Sm['false'].get(arm)!=A['false_certificates']:bad.append((arm,'summary_false',Sm['false'].get(arm),A['false_certificates']))
    sp=sum(cert[b] is not None for t,a,cert,_,_,_ in sp8_steps(c) for b in (0,1))
    if Sm['certificates'].get('SP8')!=sp:bad.append(('SP8','summary',Sm['certificates'].get('SP8'),sp))
    for arm in ALL_ARMS:
        if Sm['case_false'].get(arm)!=(Sm['false'].get(arm,0)>0):bad.append((arm,'case_false',Sm['case_false'].get(arm),Sm['false'].get(arm)))
    return bad


def sup(c,arm):
    x=c['noisy'][arm]
    return c['noisy'][x['shared_with']] if x.get('shared_with') and x.get('support') is None else x


def certs(c,arm):return [r['certificate'] for r in c['certifiers'][arm]['trace']]


def api_soundness():
    try:
        from brute.api.certify6 import certify6
        r=certify6([0,1],[0,1],[[0,1],[1,None]],8);s=r.get('soundness')
        return {'soundness':s,'matches':s is not None and all(s.get(k)==v for k,v in API_EXPECT.items()),'error':None}
    except Exception as e:return {'soundness':None,'matches':False,'error':f'{type(e).__name__}: {e}'}


def build(study=STUDY_DIR,smoke=False):
    study=Path(study);plan=load(PLAN);C=plan['criteria']
    blk=opt(study/'transfer'/'SCIENTIFIC.json');seal=opt(study/'transfer'/'SEAL.json')
    if blk is not None:check(seal['scientific_sha256']==sha(study/'transfer'/'SCIENTIFIC.json'),'transfer: SCIENTIFIC does not match SEAL')
    stop=opt(study/'STOP_018.json');stop_o=opt(study/'STOP_018_ORCHESTRATOR.json');done=opt(study/'RUN_DONE_018.json')
    state=opt(study/'RUN_STATE_018.json') or {'stopped':{},'spent':{},'completed_at':{}}
    t0=float((study/'RUN_T0').read_text().split()[0]) if (study/'RUN_T0').exists() else None
    paired=opt(study/'PAIRED_ANALYSIS_018.json');repro=opt(study/'REPRODUCIBILITY_018.json')
    aud=opt(study/'SECOND_IMPLEMENTATION_018.json');ts=opt(study/'TEST_SUITE_018.json');drill=opt(study/'KILL_DRILL_018.json')
    if smoke and drill is None:drill=opt(ROOT/'results/smoke-018/KILL_DRILL_018.json')
    stopped=state.get('stopped',{});fired=stop is not None or stop_o is not None;g={}
    exp_main,exp_stress=(24,8) if smoke else (EXPECTED['main'],EXPECTED['stress']);expected=exp_main+exp_stress
    allc=blk['cases'] if blk else [];main=[c for c in allc if is_main(c)];stress=[c for c in allc if c['eps']==0.05]
    noisy=[c for c in main if is_noisy(c)];e0=[c for c in main if c['eps']==0.0]
    def incomplete(block=True,files=(),streams=()):
        why=[]
        if block:
            if blk is None:why.append('transfer block missing')
            elif not blk.get('complete') or len(allc)!=expected:why.append(f'transfer block incomplete ({len(allc)}/{expected} cases)')
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
        bad_cc+=[(ck(c),)+b for b in cert_counts(c)]
    cover=sorted(set(ALL_ARMS)-set(tot.get('main',{})))
    gate('G_recount',not bad_rc and not bad_cc and not bad_fl and bool(allc) and not cover,{'per_subset_arm':tot,'mismatches':bad_rc[:50],
         'wrong_flag_mismatches':bad_fl[:50],'certificate_count_mismatches':bad_cc[:50],'arms_not_recounted':cover},why=wb)
    zero=lambda cs,arm:all(c['certifiers'][arm]['false_certificates']==0 and RC[(id(c),arm)]==0 for c in cs)
    casefalse=lambda c,arm:RC[(id(c),arm)]>0
    P=paired or {}
    def pv(k):x=P.get(k) or {};return x.get('mean'),x.get('ci95')
    wp=wb+incomplete(False,files=(('PAIRED_ANALYSIS_018.json',paired),))
    # GNS (headline)
    within=[c for c in noisy if c['realized_flips']<=c['m']];k=sum(casefalse(c,'RGN4') for c in noisy);ub=cp_upper(k,len(noisy))
    m2,ci2=pv('C_RGN4_eps2')
    gns={'a_zero_false_when_flips_le_m':bool(noisy) and zero(within,'RGN4'),'b_cp_upper_le_0.05':ub is not None and ub<=0.05,
         'c_C_eps2_mean_ge_0.10_ci_lower_gt_0.05':m2 is not None and m2>=0.10 and ci2 is not None and ci2[0]>0.05}
    gate('GNS_noise_soundness',all(gns.values()),{'clauses':gns,'noisy_cases':len(noisy),'cases_flips_le_m':len(within),
         'cases_flips_gt_m':len(noisy)-len(within),'case_false':k,'case_false_examples':[ck(c) for c in noisy if casefalse(c,'RGN4')][:20],
         'cp_upper_95_one_sided':ub,'C_RGN4_eps2':(m2,ci2),'C_RGN4_eps1':pv('C_RGN4_eps1'),'C_RG4_eps2':pv('C_RG4_eps2'),
         'false_certificates_RGN4':sum(RC[(id(c),'RGN4')] for c in noisy)},why=wp)
    # GN0 + R_gn0_*
    neq=[ck(c) for c in e0 if certs(c,'RGN4_0')!=certs(c,'RG4')]
    burn=lambda c:c['burn_in']
    neq_post=[ck(c) for c in e0 if [x for r,x in zip(c['certifiers']['RG4']['trace'],certs(c,'RGN4_0')) if r['step']>burn(c)]
              !=[r['certificate'] for r in c['certifiers']['RG4']['trace'] if r['step']>burn(c)]]
    diff_slots=[(ck(c),r0['step'],b) for c in e0 for r0,r1 in zip(c['certifiers']['RG4']['trace'],c['certifiers']['RGN4_0']['trace']) for b in (0,1) if r0['certificate'][b]!=r1['certificate'][b]]
    gn0={'RGN4_0_eq_RG4_every_eps0_case':bool(e0) and not neq,'RGN4_zero_false_eps0':bool(e0) and zero(e0,'RGN4')}
    gate('GN0_control',all(gn0.values()),{'clauses':gn0,'eps0_cases':len(e0),'cases_differing':neq[:50],'differing_slots':diff_slots[:50],
         'differing_slots_in_burn_in':sum(1 for _,t,_ in diff_slots if t<=8),'differing_slots_after_burn_in':sum(1 for _,t,_ in diff_slots if t>8),
         'prediction':'Inferred FAIL (#97 item 3: RG4 passes SP8 certificates through during burn-in)'},why=wb)
    sbad=[ck(c) for c in allc if sup(c,'RGN4_0')['support']!=c['bounded']['4']['support']]
    gate('R_gn0_support',None,{'cases':len(allc),'cases_supports_differ':len(sbad),'examples':sbad[:20],'pass':bool(allc) and not sbad,'label':'Exact check (reported, #97 item 3)'},gated=False)
    gate('R_gn0_post_burn',None,{'eps0_cases':len(e0),'cases_differing_after_burn_in':neq_post[:50],'pass':bool(e0) and not neq_post,'label':'reported, #97 item 3'},gated=False)
    # GS_a6
    gate('GS_a6_soundness',bool(e0) and zero(e0,'RG4'),{'eps0_cases':len(e0),'RG4_recorded_false':sum(c['certifiers']['RG4']['false_certificates'] for c in e0),
         'RG4_recomputed_false':sum(RC[(id(c),'RG4')] for c in e0)},why=wb)
    # GS_ref6
    md=(aud or {}).get('mutation_test') or {};ngated=sum(1 for c in main if c['eps'] in (0.0,0.02))
    ref={'results_sha_matches_seal':bool(aud) and bool(seal) and aud.get('results_sha256')==seal.get('results_sha256'),
         'all_gated_cases_audited':bool(aud) and aud.get('gated_cases_expected')==ngated and aud.get('gated_cases_audited')==ngated and ngated>0,
         'zero_gated_mismatching':bool(aud) and aud.get('gated_mismatching_cases')==0,
         'mutation_20_of_20':md.get('passed') is True and md.get('injected')==20 and md.get('distinct_cases')==20 and md.get('detected_injected')==20 and md.get('flagged_not_injected')==0}
    gate('GS_ref6_reference_audit',all(ref.values()),{'clauses':ref,'gated_expected':ngated,'report':None if aud is None else {k:aud[k] for k in aud if k not in ('mismatches','mutation_test')},
         'mutation':{k:v for k,v in md.items() if k!='details'},'wording':'second implementation by the same author'},
         why=wb+incomplete(False,files=(('SECOND_IMPLEMENTATION_018.json',aud),),streams=('g11',)))
    # GAPI6
    pm=((ts or {}).get('per_module') or {}).get('test_api_certify6_0160.py') or {};frz=opt(FREEZE) or {};asd=api_soundness()
    api={'module_ok':pm.get('returncode')==0 and len(pm.get('results') or {})>=4 and all(v[0]=='ok' for v in pm.get('results',{}).values()),
         'certify6_in_freeze':'brute/api/certify6.py' in frz.get('sha256_files',{}) or smoke,'soundness_dict':asd['matches']}
    gate('GAPI6_certify6',all(api.values()),{'clauses':api,'results':pm.get('results'),'soundness_probe':asd},why=incomplete(False,files=(('TEST_SUITE_018.json',ts),),streams=('gti',)))
    # G10
    tl={'SP8':all(len(c['arms']['SP8']['trace'])==STEPS for c in allc),**{a:all(len(c['certifiers'][a]['trace'])==STEPS for c in allc) for a in ARMS}}
    unk={}
    for c in allc:
        for kind,X in (('bounded4',c['bounded']['4']),)+tuple((a,sup(c,a)) for a in ('RGN4','RGN4_0','RGN4_or')):
            u=unk.setdefault(kind,[0,0])
            for row in X['unknown']:
                for x in row:u[0]+=1;u[1]+=x>0
    frac={k:(b/a if a else None) for k,(a,b) in unk.items()}
    g10ok=bool(allc) and len(allc)==expected and bool(seal) and seal.get('complete') and all(tl.values()) and all(f is not None and f<=0.01 for f in frac.values())
    gate('G10_compute',g10ok,{'cases':len(allc),'expected':expected,'traces_44_steps':tl,'unknown_gt0_fraction':{k:None if f is None else round(f,6) for k,f in frac.items()},
         'queries':{k:{'queries':a,'unknown_gt0':b} for k,(a,b) in unk.items()}},why=wb)
    # G12
    R0=(repro or {}).get('blocks',{}).get('transfer',{})
    g12ok=bool(repro) and repro['G12_pass'] and bool(seal) and R0.get('main_scientific_sha256')==seal['scientific_sha256'] and R0.get('expected')==(11 if smoke else 120)
    gate('G12_reproducibility',g12ok,None if repro is None else repro['blocks'],why=wb+incomplete(False,files=(('REPRODUCIBILITY_018.json',repro),),streams=('repro',)))
    # G13
    try:check_freeze();fz=True;fz_err=None
    except Exception as exc_:fz=False;fz_err=f'{type(exc_).__name__}: {exc_}'
    f14=(opt(ROOT/'experiments/BRUTE_SOURCE_FREEZE_014.json') or {}).get('sha256_files',{})
    rg_bad=[ck(c) for c in e0 if S14.rg_arm(sp8_steps(c),{'4':c['bounded']['4']},FB,c['burn_in'])!=c['certifiers']['RG4']]
    g13={'freeze_chain_holds':fz,'cases_use_plan013_tau6':bool(allc) and all(c.get('tau6')==TAU6 for c in allc),
         'rg_sp8_are_frozen_v0120':S18.rg_arm is S14.rg_arm and S18.sp8_steps is S14.sp8_steps and f14.get('experiments/brute_study_014.py')==sha(ROOT/'experiments/brute_study_014.py'),
         'rg4_reproduces_eps0':bool(e0) and not rg_bad,
         'seal_of_current_plan_and_freeze':bool(seal) and seal['plan_sha256']==sha(PLAN) and FREEZE.exists() and seal.get('freeze_sha256')==sha(FREEZE)}
    g13ok=all(g13.values()) if not smoke else all(v for k,v in g13.items() if k not in ('freeze_chain_holds','seal_of_current_plan_and_freeze'))
    gate('G13_frozen_controls_reproduce',g13ok,{'clauses':g13,'rg4_not_reproduced':rg_bad[:20],'freeze_error':fz_err,'smoke_dry_run_relaxed':smoke},why=wb)
    # GTI
    V=(ts or {}).get('verdict')
    gate('GTI_test_isolation',bool(V) and V['passed'],None if ts is None else {'verdict':V,'head':ts.get('head'),'tracked_tree_dirty':ts.get('tracked_tree_dirty'),
         'dirty_tracked_files':ts.get('dirty_tracked_files'),'workers':ts.get('workers'),
         'clean_tag_runs':{k:(None if v is None else v.get('results')) for k,v in (ts.get('clean_tag_runs') or {}).items()},'run':'in-cap'},
         why=incomplete(False,files=(('TEST_SUITE_018.json',ts),),streams=('gti',)))
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
    def per_eps(arm,cs=allc):
        o={}
        for e in EPS:
            x=[c for c in cs if c['eps']==e]
            if not x:continue
            kf=sum(casefalse(c,arm) for c in x)
            o[str(e)]={'cases':len(x),'false_certificates':sum(RC[(id(c),arm)] for c in x),'case_false':kf,'case_false_rate':round(kf/len(x),6),
                       'cp_upper_95_one_sided':cp_upper(kf,len(x)),'coverage':round(sum(c['summary']['certificates'][arm] for c in x)/(len(x)*SLOTS),6)}
        return o
    gate('R_RG4_noise',None,{'RG4':per_eps('RG4'),'SP8':per_eps('SP8'),'C_RG4':{s:pv('C_RG4_'+s) for s in ('eps0','eps1','eps2','stress')},'label':'expected > 0 under noise'},gated=False)
    gate('R_stress',None,{'cases':len(stress),'RGN4':per_eps('RGN4',stress).get('0.05'),'RGN4_or':per_eps('RGN4_or',stress).get('0.05'),
         'cases_flips_gt_m':sum(c['realized_flips']>c['m'] for c in stress),
         'RGN4_case_false_flips_le_m':sum(casefalse(c,'RGN4') for c in stress if c['realized_flips']<=c['m']),
         'RGN4_case_false_flips_gt_m':sum(casefalse(c,'RGN4') for c in stress if c['realized_flips']>c['m']),'label':'outside the attestation; no guarantee'},gated=False)
    gate('R_oracle',None,{'RGN4_or':per_eps('RGN4_or'),'C_RGN4_or':{s:pv('C_RGN4_or_'+s) for s in ('eps0','eps1','eps2','noisy','stress')},
         'dC_RGN4_or_minus_RGN4':{s:(lambda a,b:None if a is None or b is None else round(a-b,6))(pv('C_RGN4_or_'+s)[0],pv('C_RGN4_'+s)[0]) for s in ('eps0','eps1','eps2','noisy','stress')}},gated=False)
    bnd={}
    for e in EPS:
        x=[c for c in allc if c['eps']==e]
        if x:bnd[str(e)]={'cases':len(x),'observed_RGN4_case_false_rate':round(sum(casefalse(c,'RGN4') for c in x)/len(x),6),
                          'observed_flips_gt_m_rate':round(sum(c['realized_flips']>c['m'] for c in x)/len(x),6),
                          'mean_bound_P_flips_gt_m':round(sum(p_exceed(c['B'],e,c['m']) for c in x)/len(x),8),
                          'm_values':sorted({c['m'] for c in x}),'B_range':[min(c['B'] for c in x),max(c['B'] for c in x)]}
    gate('R_bound',None,bnd,gated=False)
    hba=opt(study/'HEARTBEAT_ATTRIBUTION_018.json')
    gate('R_heartbeat_attribution',None,{'watchdog_gaps_over_10s':None if not hb else hb['gaps_over_10s'],
         'sentinel_attribution':None if hba is None else {k:hba.get(k) for k in ('max_watchdog_gap_s','max_sentinel_tick_gap_s','class_counts','gaps_over_10s','sentinel_records')},
         'label':'Inferred; deviation #90 diagnostic, changes no verdict'},gated=False)
    raw=opt(study/'transfer'/'RESULTS.json');RW={ck(c):c for c in raw['cases']} if raw else {}
    def solver_cost():
        W=[RW.get(ck(c),{}).get('region_wall_informational') for c in allc]
        if not W or any(w is None for w in W):return 'RESULTS.json absent or incomplete: timing not reported'
        return {a:{'total_s':round(sum(w[a] for w in W),3),'ms_per_step':round(1000*sum(w[a] for w in W)/(len(W)*STEPS),4)} for a in ARMS}|{'timing_source':'transfer/RESULTS.json (informational, unsealed)'}
    gate('R_rates',None,{s_:{'spent_s':round(state.get('spent',{}).get(s_,0),1),'budget_s':BUDGETS[s_],
         'fraction_of_budget':round(state.get('spent',{}).get(s_,0)/BUDGETS[s_],3)} for s_ in STREAMS}|{'solver_cost':solver_cost() if allc else None},gated=False)
    gated=[k for k,v in g.items() if v['gated']]
    return {'schema':'brute.gates.v16_0','study':plan['study'],'plan_sha256':sha(PLAN),'smoke_dry_run':smoke,'criteria_registered':sorted(C),
            'criteria_scored':sorted(gated),'scientific_sha256':None if seal is None else seal['scientific_sha256'],'stop_rule_fired':fired,'gates':g,
            'passed':[k for k in gated if g[k]['pass']],'failed':[k for k in gated if g[k]['pass'] is False],
            'pending':[k for k in gated if g[k]['pass'] is None],'all_gated_pass':all(g[k]['pass'] for k in gated),
            'GNS':g['GNS_noise_soundness']['pass'],'GN0':g['GN0_control']['pass'],'G_RT':g['G_RT_study_runtime']['pass'],'G_HB':g['G_HB_heartbeat_gap']['pass']}


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--study-dir',default=str(STUDY_DIR));ap.add_argument('--check',action='store_true')
    ap.add_argument('--output',default='GATES_018.json');ap.add_argument('--smoke',action='store_true',help='dry run on a smoke directory; prints only')
    a=ap.parse_args()
    if a.smoke:
        obj=build(Path(a.study_dir),smoke=True)
        print({k:obj[k] for k in ('passed','failed','pending')});print({k:v.get('reason') for k,v in obj['gates'].items() if v.get('reason')});raise SystemExit
    obj=build(Path(a.study_dir));out=Path(a.study_dir)/a.output
    if a.check:check(out.read_bytes()==dumps(obj),out.name+' does not reproduce');print(out.name,'reproduces')
    else:write_new(out,obj);print({k:obj[k] for k in ('passed','failed','pending','all_gated_pass')})
