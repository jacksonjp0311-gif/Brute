"""Evaluate the pre-registered study-015 criteria (BRUTE_PLAN_015: headline GRS_region_split, GS_a3, GS_b3, GS_c3, GEB,
G_alias3_stress, G_recount, GS_ref3, GAPI3, G10, G12, G13, GTI, G_RT, G_HB gated; non_gated_reports reported) from sealed
artifacts only. Committed and ledgered (scoring_freeze_015) before the held-out run_start; thresholds are copied from the
plan, nothing is tuned. Adapted from make_gates_014 (frozen, not edited).

Inputs in results/study-015 (D): transfer/{SCIENTIFIC,SEAL}.json, repro/transfer/SEAL.json, PAIRED_ANALYSIS_015.json,
REPRODUCIBILITY_015.json, SECOND_IMPLEMENTATION_015.json, TEST_SUITE_015.json, RUN_STATE_015.json, RUN_T0,
RUN_DONE_015.json / STOP_015.json / STOP_015_ORCHESTRATOR.json, HEARTBEAT_015.jsonl, KILL_DRILL_015.json;
experiments/BRUTE_SOURCE_FREEZE_015.json.

Scoring choices fixed here, before data:
- Own trajectory (metrics.false_certificates): SP8, RG2-5, EB, EB2, DLFp, DLFn -> the SP8 trajectory actuals
  (brute_study_014.sp8_steps); RSX4, RSXp, RSXn and the SP8 learner run on the RSX trajectory (case.rsx) -> the RSX
  trajectory actuals (brute_study_014.lx_steps(case.rsx)); an arm's own 'trajectory' field, when recorded, must agree.
  Certificate[b] at step i is false iff it is non-null and differs from the evaluator-only actual of action b at step i.
- G_recount: for every arm of arms_by_block (transfer: SP8, RG2-5, RSX4, RSXp, RSXn, DLFp, DLFn, EB, EB2, stress; ood5:
  SP8, RG4, RG5) the recount equals the recorded count, per case: SP8 vs summary.false.SP8, arms vs
  transfer[arm].false_certificates, the RSX-trajectory SP8 learner vs rsx.false_certificates, stress DLF_certs vs
  DLF_false (SP8 trajectory) and RSX_certs vs RSX_false (RSX trajectory).
- GS_a3: per arm (RG4, RSX4, RSXp, RSXn, DLFp, DLFn) recorded == 0 and recomputed == 0 on the 288 main cases.
- GS_b3: (1) SP8 trajectory: SP8 cert (taken / counterfactual) non-null -> RG4 cert equal; (2) RSX4 cert non-null ->
  RSXp and RSXn cert equal; (3) every rule 'rg' certificate c has bounded support [c] at n = the arm's n (RG2-5, RSX4) or
  n = 4 (DLF*, RSXp/n, EB*), every 'license' certificate at n = license_bound, every 'eb' certificate at n = the row's
  recorded bound, on the arm's own trajectory. Main and ood5 cases.
- GRS: GS_a3 RSX4 pass AND PAIRED TV_RSX4 mean >= 1.0 AND ci95 lower > 0. GS_c3: RSXn pass AND RSXn_minus_RSX4 ci95
  lower <= 0. GEB: EB recorded == recomputed == 0; TV_EB / EB2 reported.
- G_alias3_stress: stress pair = stress record with AT6_transfer >= 1; PASS iff >= 20 pairs and RSX_false == 0 and the
  recount of RSX_certs == 0 on every pair.
- GS_ref3: SECOND_IMPLEMENTATION_015 results_sha256 equals the transfer SEAL results_sha256, 360 audited (288 + 72),
  0 not reached, 0 mismatching, mutation_test passed with injected 20, distinct 20, detected 20, flagged_not_injected 0,
  kinds exactly bounded 5 / rsx 4 / dlf 3 / stress 3 / rg 2 / eb 3; g11 stream not stopped.
- GAPI3: TEST_SUITE_015 per_module['test_api_certify3_0130.py'] returncode 0, >= 4 results, all 'ok'; brute/api/certify3.py
  in BRUTE_SOURCE_FREEZE_015.
- G10: 360 cases, transfer SEAL complete; every recorded trace 44 steps; 72 stress records per main case; per trajectory
  (SP8, RSX) the fraction of recorded bounded-support queries (n = 1..5, both actions) with unknown > 0 is <= 1%.
- G13: check_freeze (015 freeze chain incl. 002-014 and release freezes), plan tau6, cases tau6, SEAL of the current plan
  and freeze, and the study runner's rg_arm / dlf_arm are the frozen v0.12.0 functions (brute_study_014, sha equal to
  BRUTE_SOURCE_FREEZE_014).
- G_RT (i) streams transfer, repro, gti, g11 completed_at <= t0 + 7200 and not stopped; (ii) heartbeat first beat <=
  t0 + 60 and last >= end - 10; (iii) KILL_DRILL_015 latency <= 15 s, no survivors. G_HB: largest gap <= 30 s.
- STUDY_BUDGET: a gate whose inputs are incomplete is FAIL; reason 'STUDY_BUDGET' when a STOP file exists, else
  'INCOMPLETE_INPUT (...)'.
- R_coverage (metrics.coverage_proxy): certificates per arm / (cases x 44 x 2), main and ood5 separately."""
from __future__ import annotations
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common_015 import STUDY_DIR,PLAN,FREEZE,load,dumps,write_new,check,sha,check_freeze
from experiments.brute_study_014 import sp8_steps,lx_steps
import experiments.brute_study_014 as S14
import experiments.brute_study_015 as S15

CAP=7200;EXPECTED_MAIN=288;EXPECTED_OOD5=72;STEPS=44;STRESS=72;FB=4;TAU6=1.645215321642
MAIN=('RG2','RG3','RG4','RG5','RSX4','RSXp','RSXn','DLFp','DLFn','EB','EB2');OOD5=('RG4','RG5')
RSX_TRAJ=('RSX4','RSXp','RSXn');GS_A3=('RG4','RSX4','RSXp','RSXn','DLFp','DLFn')
STREAMS=('transfer','repro','gti','g11');BUDGETS={'transfer':3000,'gti':3600,'repro':1500,'g11':2400}
FAMILIES=('cycle3','switch3','unaliased2','ood4');KINDS={'bounded':5,'rsx':4,'dlf':3,'stress':3,'rg':2,'eb':3}
def opt(p):return load(p) if Path(p).exists() else None
def ck(c):return f"{c['family']}/{c['seed']}/{c['mask_rate']}"


def beats(d,t0):
    p=d/'HEARTBEAT_015.jsonl'
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
    return {'beats':len(R),'first_wall':R[0]['wall'],'last_wall':R[-1]['wall'],'max_gap_s':max(gaps) if gaps else None,
            'gaps_over_10s':att}


def actuals(c):
    out={'SP8':[s[5] for s in sp8_steps(c)]}
    if 'rsx' in c:out['RSX']=[s[5] for s in lx_steps(c['rsx'])]
    return out


def traj_of(c,arm):
    t='RSX' if arm in RSX_TRAJ else 'SP8';rec=c['transfer'][arm].get('trajectory')
    check(rec is None or rec==t,f'{ck(c)} {arm}: recorded trajectory {rec} != {t}');return t


def wrong(tr,A):return sum(1 for i,r in enumerate(tr) for b in (0,1) if r['certificate'][b] is not None and r['certificate'][b]!=A[i][b])
def wrong_certs(cs,A):return sum(1 for t,b,code in cs if code!=A[t-1][b])


def recount(c,act):
    """[(arm, recorded, recomputed)] for one case, every arm of arms_by_block."""
    S=sp8_steps(c);out=[('SP8',c['summary']['false']['SP8'],sum(cert[b] is not None and cert[b]!=act['SP8'][i][b] for i,(t,a,cert,_,_,_) in enumerate(S) for b in (0,1)))]
    for arm in c['transfer']:out.append((arm,c['transfer'][arm]['false_certificates'],wrong(c['transfer'][arm]['trace'],act[traj_of(c,arm)])))
    if 'rsx' in c:out.append(('RSX_trajectory_SP8',c['rsx']['false_certificates'],wrong(c['rsx']['trace'],act['RSX'])))
    for s in c.get('stress',[]):
        out.append(('stress_DLF_SP8',s['DLF_false'],wrong_certs(s['DLF_certs'],act['SP8'])))
        out.append(('stress_DLF_RSX',s['RSX_false'],wrong_certs(s['RSX_certs'],act['RSX'])))
    return out


def containment(c):
    bad=[];T=c['transfer'];S=sp8_steps(c);BS=c['bounded']
    for i,(t,a,cert,_,_,_) in enumerate(S):
        for b in (0,1):
            if cert[b] is not None and T['RG4']['trace'][i]['certificate'][b]!=cert[b]:bad.append(('sp8_not_rg4',t,b))
            if 'RSX4' in T:
                r=T['RSX4']['trace'][i]['certificate'][b]
                for arm in ('RSXp','RSXn'):
                    if r is not None and T[arm]['trace'][i]['certificate'][b]!=r:bad.append((arm+'_misses_rsx4',t,b))
    for arm,A in T.items():
        tj=traj_of(c,arm);nrg=A.get('n',FB);nl=A.get('license_bound')
        for i,r in enumerate(A['trace']):
            for b in (0,1):
                cc=r['certificate'][b];rule=r['rule'][b]
                n={'rg':nrg,'license':nl,'eb':r.get('bound')}.get(rule)
                if rule in ('rg','license','eb') and (n is None or list(BS[tj][str(n)]['support'][i][b] or [])!=[cc]):bad.append((f'{arm}_{rule}_not_singleton',r['step'],b))
    return bad


def build(study=STUDY_DIR,smoke=False):
    study=Path(study);plan=load(PLAN);C=plan['criteria']
    blk=opt(study/'transfer'/'SCIENTIFIC.json');seal=opt(study/'transfer'/'SEAL.json')
    if blk is not None:check(seal['scientific_sha256']==sha(study/'transfer'/'SCIENTIFIC.json'),'transfer: SCIENTIFIC does not match SEAL')
    stop=opt(study/'STOP_015.json');stop_o=opt(study/'STOP_015_ORCHESTRATOR.json');done=opt(study/'RUN_DONE_015.json')
    state=opt(study/'RUN_STATE_015.json') or {'stopped':{},'spent':{},'completed_at':{}}
    t0=float((study/'RUN_T0').read_text().split()[0]) if (study/'RUN_T0').exists() else None
    paired=opt(study/'PAIRED_ANALYSIS_015.json');repro=opt(study/'REPRODUCIBILITY_015.json')
    aud=opt(study/'SECOND_IMPLEMENTATION_015.json');ts=opt(study/'TEST_SUITE_015.json');drill=opt(study/'KILL_DRILL_015.json')
    if smoke and drill is None:drill=opt(ROOT/'results/study-015/KILL_DRILL_015.json')
    stopped=state.get('stopped',{});fired=stop is not None or stop_o is not None;g={}
    exp_main,exp_ood5=(8,2) if smoke else (EXPECTED_MAIN,EXPECTED_OOD5);expected=exp_main+exp_ood5
    allc=blk['cases'] if blk else [];cases=[c for c in allc if c['family']!='ood5'];c5=[c for c in allc if c['family']=='ood5']
    def incomplete(block=True,files=(),streams=()):
        why=[]
        if block:
            if blk is None:why.append('transfer block missing')
            elif not seal.get('complete') or seal.get('case_count')!=expected:why.append(f'transfer block incomplete ({seal.get("case_count")}/{expected})')
            elif len(cases)!=exp_main or len(c5)!=exp_ood5:why.append(f'block split {len(cases)}+{len(c5)} != {exp_main}+{exp_ood5}')
            if 'transfer' in stopped:why.append('transfer stream stopped: '+stopped['transfer'])
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
    wb=incomplete();ACT={id(c):actuals(c) for c in allc}
    # G_recount (+ per-arm totals for GS_a3 / GEB)
    tot={};bad_rc=[]
    for c in allc:
        blkname='ood5' if c['family']=='ood5' else 'transfer'
        for arm,rec,re in recount(c,ACT[id(c)]):
            x=tot.setdefault(blkname,{}).setdefault(arm,{'recorded_false':0,'recomputed_false':0,'records':0,'mismatching_records':0})
            x['recorded_false']+=rec;x['recomputed_false']+=re;x['records']+=1
            if rec!=re:x['mismatching_records']+=1;bad_rc.append((ck(c),arm,rec,re))
    want={b:set(v) for b,v in plan['arms_by_block'].items()}
    have={b:{('stress' if a.startswith('stress_') else 'SP8' if a=='RSX_trajectory_SP8' else a) for a in v} for b,v in tot.items()}
    cover={b:sorted(want[b]-have.get(b,set())) for b in want}
    gate('G_recount',not bad_rc and bool(allc) and not any(cover.values()),{'per_block_arm':tot,'mismatches':bad_rc[:50],
         'arms_by_block_not_recounted':cover},why=wb)
    T=tot.get('transfer',{})
    per={a:dict(T.get(a,{}),certificates=sum(c['transfer'][a]['certificates'] for c in cases),
                pass_=T.get(a,{}).get('recorded_false')==0 and T.get(a,{}).get('recomputed_false')==0) for a in MAIN}
    for a in per:per[a]['pass']=per[a].pop('pass_')
    gsa={a:per[a]['pass'] for a in GS_A3}
    gate('GS_a3_soundness',all(gsa.values()),{'per_arm_pass':gsa,'per_arm':per},why=wb)
    # GS_b3
    cb={};nbad=0
    for c in allc:
        b=containment(c)
        if b:cb[ck(c)]=b[:5];nbad+=1
    gate('GS_b3_containment',nbad==0 and bool(allc),{'cases_checked':len(allc),'cases_failing':nbad,'examples':dict(list(cb.items())[:10])},why=wb)
    P=paired or {}
    def pv(k):x=P.get(k) or {};return x.get('mean'),x.get('ci95')
    wp=wb+incomplete(False,files=(('PAIRED_ANALYSIS_015.json',paired),))
    m,ci=pv('TV_RSX4');grs={'i_RSX4_zero_false':per['RSX4']['pass'],'ii_TV_RSX_mean_ge_1':m is not None and m>=1.0,'iii_TV_RSX_ci_lower_gt_0':ci is not None and ci[0]>0}
    gate('GRS_region_split',all(grs.values()),{'clauses':grs,'TV_RSX4_mean':m,'TV_RSX4_ci95':ci,'S_RSX4':pv('S_RSX4'),'S_RG4':pv('S_RG4'),
         'per_family':(P.get('TV_RSX4') or {}).get('families'),'histogram':(P.get('TV_RSX4') or {}).get('histogram')},why=wp)
    m,ci=pv('RSXn_minus_RSX4');gsc={'i_RSXn_zero_false':per['RSXn']['pass'],'ii_RSXn_minus_RSX4_ci_lower_le_0':ci is not None and ci[0]<=0}
    gate('GS_c3_wrong_family',all(gsc.values()),{'clauses':gsc,'RSXn_minus_RSX4_mean':m,'ci95':ci,'RSXp_minus_RSX4':pv('RSXp_minus_RSX4')},why=wp)
    gate('GEB_evidence_bound_soundness',per['EB']['pass'],{'EB':per['EB'],'TV_EB':pv('TV_EB'),'EB2':per['EB2'],'TV_EB2':pv('TV_EB2'),
         'eb_certificates':sum(c['transfer']['EB']['eb_certificates'] for c in cases)},why=wb)
    # G_alias3
    allp=[s for c in cases for s in c['stress']];sp=[(c,s) for c in cases for s in c['stress'] if s['AT6_transfer']>=1]
    rre=[wrong_certs(s['RSX_certs'],ACT[id(c)]['RSX']) for c,s in sp]
    alias={'stress_pairs':len(sp),'RSX_false_on_stress_pairs':sum(s['RSX_false'] for _,s in sp),'RSX_false_recounted':sum(rre),
           'stress_pairs_with_RSX_false':sum(s['RSX_false']>0 or r>0 for (_,s),r in zip(sp,rre)),'RSX_license_on_stress_pairs':sum(s['RSX_license'] for _,s in sp),
           'DLF_SP8_false_on_stress_pairs':sum(s['DLF_false'] for _,s in sp),'AT6_false_on_stress_pairs':sum(s['AT6_false'] for _,s in sp)}
    gate('G_alias3_stress',len(sp)>=20 and alias['stress_pairs_with_RSX_false']==0,dict(alias,underpowered=len(sp)<20),why=wb)
    # GS_ref3
    md=(aud or {}).get('mutation_test') or {};kinds=md.get('kinds') or {}
    ref={'results_sha_matches_seal':bool(aud) and bool(seal) and aud.get('results_sha256')==seal.get('results_sha256'),
         'all_cases_audited':bool(aud) and aud.get('cases_audited')==expected and aud.get('cases_not_reached')==0,
         'zero_mismatching':bool(aud) and aud.get('mismatching_cases')==0,
         'mutation_20_of_20':md.get('passed') is True and md.get('injected')==20 and md.get('distinct_cases')==20 and md.get('detected_injected')==20 and md.get('flagged_not_injected')==0,
         'mutation_kinds':kinds==KINDS}
    gate('GS_ref3_reference_audit',all(ref.values()),{'clauses':ref,'report':None if aud is None else {k:aud[k] for k in aud if k not in ('mismatches','mutation_test')},
         'mutation':{k:v for k,v in md.items() if k!='details'},'wording':'second implementation by the same author'},
         why=wb+incomplete(False,files=(('SECOND_IMPLEMENTATION_015.json',aud),),streams=('g11',)))
    # GAPI3
    pm=((ts or {}).get('per_module') or {}).get('test_api_certify3_0130.py') or {}
    frz=opt(FREEZE) or {}
    api={'module_ok':pm.get('returncode')==0 and len(pm.get('results') or {})>=4 and all(v[0]=='ok' for v in pm.get('results',{}).values()),
         'certify3_in_freeze':'brute/api/certify3.py' in frz.get('sha256_files',{})}
    gate('GAPI3_certify3',all(api.values()),{'clauses':api,'results':pm.get('results')},why=incomplete(False,files=(('TEST_SUITE_015.json',ts),),streams=('gti',)))
    # G10
    tl={'SP8':all(len(c['arms']['SP8']['trace'])==STEPS for c in allc),'RSX':all(len(c['rsx']['trace'])==STEPS for c in cases),
        **{a:all(len(c['transfer'][a]['trace'])==STEPS for c in allc if a in c['transfer']) for a in MAIN}}
    unk={}
    for c in allc:
        for traj,Bn in c['bounded'].items():
            for n,B in Bn.items():
                x=unk.setdefault(traj,{}).setdefault(n,[0,0])
                for row in B['unknown']:
                    for u in row:x[0]+=1;x[1]+=u>0
    frac={t:(sum(v[1] for v in d.values())/sum(v[0] for v in d.values()) if sum(v[0] for v in d.values()) else None) for t,d in unk.items()}
    g10={'cases':len(allc)==expected and bool(seal) and bool(seal.get('complete')),'traces_44':all(tl.values()),
         'stress_72_per_main_case':bool(cases) and all(len(c['stress'])==(24 if smoke else STRESS) for c in cases),
         'unknown_le_1pct_every_trajectory':bool(frac) and set(frac)=={'SP8','RSX'} and all(f is not None and f<=0.01 for f in frac.values())}
    gate('G10_compute',all(g10.values()),{'clauses':g10,'trace_lengths_ok':tl,'unknown_fraction_per_trajectory':{t:None if f is None else round(f,6) for t,f in frac.items()},
         'unknown_per_trajectory_n':{t:{n:{'queries':a,'unknown_gt0':b} for n,(a,b) in sorted(d.items())} for t,d in unk.items()}},why=wb)
    # G12
    g12ok=bool(repro) and repro['G12_pass'] and bool(seal) and repro['blocks']['transfer']['main_scientific_sha256']==seal['scientific_sha256']
    gate('G12_reproducibility',g12ok,None if repro is None else repro['blocks'],why=wb+incomplete(False,files=(('REPRODUCIBILITY_015.json',repro),),streams=('repro',)))
    # G13
    try:check_freeze();fz=True;fz_err=None
    except Exception as exc_:fz=False;fz_err=f'{type(exc_).__name__}: {exc_}'
    f14=(opt(ROOT/'experiments/BRUTE_SOURCE_FREEZE_014.json') or {}).get('sha256_files',{})
    g13={'freeze_chain_holds':fz,'plan_tau6':plan['tau6']['value']==TAU6,
         'cases_use_plan_tau':bool(allc) and all(c.get('tau6')==TAU6 for c in allc),
         'rg_dlf_are_frozen_v0120':S15.rg_arm is S14.rg_arm and S15.dlf_arm is S14.dlf_arm and S15.sp8_steps is S14.sp8_steps
              and f14.get('experiments/brute_study_014.py')==sha(ROOT/'experiments/brute_study_014.py'),
         'seal_of_current_plan_and_freeze':bool(seal) and seal['plan_sha256']==sha(PLAN) and FREEZE.exists() and seal.get('freeze_sha256')==sha(FREEZE)}
    g13ok=all(g13.values()) if not smoke else (g13['plan_tau6'] and g13['cases_use_plan_tau'] and g13['rg_dlf_are_frozen_v0120'])
    gate('G13_frozen_controls_reproduce',g13ok,{'clauses':g13,'freeze_error':fz_err,'smoke_dry_run_relaxed':smoke},why=wb)
    # GTI
    V=(ts or {}).get('verdict')
    gate('GTI_test_isolation',bool(V) and V['passed'],None if ts is None else {'verdict':V,'head':ts.get('head'),'tracked_tree_dirty':ts.get('tracked_tree_dirty'),
         'clean_tag_runs':{k:(None if v is None else v.get('results')) for k,v in (ts.get('clean_tag_runs') or {}).items()},'run':'in-cap'},
         why=incomplete(False,files=(('TEST_SUITE_015.json',ts),),streams=('gti',)))
    # G_RT / G_HB
    hb=heartbeat(study,t0);comp=state.get('completed_at',{})
    end=(t0+done['elapsed_s']) if (t0 is not None and done) else (t0+CAP if t0 is not None else None)
    late={s:(round(comp[s]-t0,1) if s in comp and t0 is not None else None) for s in STREAMS}
    i_streams={s:late[s] is not None and late[s]<=CAP and s not in stopped for s in STREAMS if not (smoke and s=='gti')}
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
    # ---- reports
    fam=lambda f:[c for c in allc if c['family']==f]
    def arm_rep(a,fams=FAMILIES):
        return {f:{'cases':len(fam(f)),'false':sum(c['transfer'][a]['false_certificates'] for c in fam(f)),
                   'mean_S':round(sum(c['summary']['S'][a] for c in fam(f))/len(fam(f)),4) if fam(f) else None} for f in fams}
    gate('R_DLF_v0120',None,{a:{'per_arm':per[a],'per_family':arm_rep(a),'S':pv('S_'+a),'TV':pv('TV_'+a)} for a in ('DLFp','DLFn')},gated=False)
    nE={f:{} for f in FAMILIES}
    for c in cases:
        for r in c['transfer']['EB']['trace']:nE[c['family']][str(r['n_E'])]=nE[c['family']].get(str(r['n_E']),0)+1
    gate('R_EB',None,{'TV_EB':pv('TV_EB'),'TV_EB2':pv('TV_EB2'),'EB2':per['EB2'],'per_family':{a:arm_rep(a) for a in ('EB','EB2')},'n_E_steps_per_family':nE},gated=False)
    gate('R_rg_family',None,{a:arm_rep(a) for a in ('RG2','RG3','RG4','RG5')},gated=False)
    gate('R_B5',None,{'cases':len(c5),**{a:{'recorded_false':tot.get('ood5',{}).get(a,{}).get('recorded_false'),'certificates':sum(c['transfer'][a]['certificates'] for c in c5),
         'S':pv('ood5_S_'+a)} for a in OOD5},'SP8_false':tot.get('ood5',{}).get('SP8',{}).get('recorded_false'),
         'wall_informational_note':'per-case wall time is in RESULTS.json (timing stripped from SCIENTIFIC)'},gated=False)
    gate('R_rsx_family',None,{'TV_RSX4':(P.get('TV_RSX4') or {}).get('families'),'per_family':{a:arm_rep(a) for a in RSX_TRAJ},
         'rsx_rule_counts':{f:{k:sum(c['rsx']['rule_counts'][k] for c in fam(f)) for k in ('rsx','sp8')} for f in FAMILIES}},gated=False)
    cov={'main':{a:round(sum(c['transfer'][a]['certificates'] for c in cases)/(len(cases)*STEPS*2),6) if cases else None for a in MAIN},
         'ood5':{a:round(sum(c['transfer'][a]['certificates'] for c in c5)/(len(c5)*STEPS*2),6) if c5 else None for a in OOD5}}
    cov['main']['SP8']=round(sum(1 for c in cases for s in sp8_steps(c) for b in (0,1) if s[2][b] is not None)/(len(cases)*STEPS*2),6) if cases else None
    cov['main']['RSX_trajectory_SP8']=round(sum(c['rsx']['certificates'] for c in cases)/(len(cases)*STEPS*2),6) if cases else None
    gate('R_coverage',None,cov,gated=False)
    out_b=[s for s in allp if s['outside_exact_bound_EVALUATOR_ONLY']]
    gate('R_stress_sp8',None,{'pairs':len(allp),'DLF_false':sum(s['DLF_false'] for s in allp),'RSX_false':sum(s['RSX_false'] for s in allp),
         'AT6_false':sum(s['AT6_false'] for s in allp),'pairs_outside_exact_bound':len(out_b),'DLF_false_outside_bound':sum(s['DLF_false'] for s in out_b),
         'RSX_false_outside_bound':sum(s['RSX_false'] for s in out_b),'AT6_false_outside_bound':sum(s['AT6_false'] for s in out_b),
         'DLF_license_all':sum(s['DLF_license'] for s in allp),'RSX_license_all':sum(s['RSX_license'] for s in allp)},gated=False)
    gate('R_heartbeat_attribution',None,None if not hb else hb['gaps_over_10s'],gated=False)
    gate('R_rates',None,{s:{'spent_s':round(state.get('spent',{}).get(s,0),1),'budget_s':BUDGETS[s],
         'fraction_of_budget':round(state.get('spent',{}).get(s,0)/BUDGETS[s],3)} for s in STREAMS},gated=False)
    gate('R_K_after_release',None,{'note':'test_release_0110 / 0120 after the version bump: checked post-release, reported in RELEASE.json (not scored here)'},gated=False)
    gated=[k for k,v in g.items() if v['gated']]
    return {'schema':'brute.gates.v13_0','study':plan['study'],'plan_sha256':sha(PLAN),'smoke_dry_run':smoke,'criteria_registered':sorted(C),
            'criteria_scored':sorted(gated),'scientific_sha256':None if seal is None else seal['scientific_sha256'],'stop_rule_fired':fired,'gates':g,
            'passed':[k for k in gated if g[k]['pass']],'failed':[k for k in gated if g[k]['pass'] is False],
            'pending':[k for k in gated if g[k]['pass'] is None],'all_gated_pass':all(g[k]['pass'] for k in gated),
            'GRS':g['GRS_region_split']['pass'],'G_RT':g['G_RT_study_runtime']['pass'],'G_HB':g['G_HB_heartbeat_gap']['pass']}


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--study-dir',default=str(STUDY_DIR));ap.add_argument('--check',action='store_true')
    ap.add_argument('--output',default='GATES_015.json');ap.add_argument('--smoke',action='store_true',help='dry run on a smoke directory; prints only')
    a=ap.parse_args()
    if a.smoke:
        obj=build(Path(a.study_dir),smoke=True)
        print({k:obj[k] for k in ('passed','failed','pending')});print({k:v.get('reason') for k,v in obj['gates'].items() if v.get('reason')});raise SystemExit
    obj=build(Path(a.study_dir));out=Path(a.study_dir)/a.output
    if a.check:check(out.read_bytes()==dumps(obj),out.name+' does not reproduce');print(out.name,'reproduces')
    else:write_new(out,obj);print({k:obj[k] for k in ('passed','failed','pending','all_gated_pass')})
