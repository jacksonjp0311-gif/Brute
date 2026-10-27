"""Evaluate the pre-registered study-014 criteria (BRUTE_PLAN_014: headline GST2_bounded_transfer, GS_a, GS_b, GS_c,
GS_d, GS_rg, GS_x, G_alias_stress, GS_ref, GAPI2, G10, G12, G13, GTI, G_RT, G_HB gated; non_gated_reports reported)
from sealed artifacts only. Committed and ledgered (scoring_freeze_014) before the held-out run_start; thresholds are
copied from the plan, nothing is tuned. Adapted from make_gates_013 (frozen, not edited).

Inputs in results/study-014 (D): transfer/{SCIENTIFIC,SEAL}.json, repro/transfer/SEAL.json, PAIRED_ANALYSIS_014.json,
REPRODUCIBILITY_014.json, SECOND_IMPLEMENTATION_014.json, TEST_SUITE_014.json, RUN_STATE_014.json, RUN_T0,
RUN_DONE_014.json / STOP_014.json / STOP_014_ORCHESTRATOR.json, HEARTBEAT_014.jsonl, KILL_DRILL_014.json;
experiments/BRUTE_SOURCE_FREEZE_014.json; results/diag-014/LICENSE_DIAG_SEEN*.json.

Scoring choices fixed here, before data:
- false certificates (GS_a) are RECOMPUTED: for arms on the SP8 trajectory (RG*, DLF*, AT*) certificate[b] against the
  SP8 evaluator-only actual of action b at that step (brute_study_014.sp8_steps); for DXp / DXn against the LX<p|n>
  trajectory actuals (lx_steps). AT traces: certificate[b] as recorded by the frozen gated_arm. The recomputed count
  must equal the recorded false_certificates (else the arm fails). Per-arm pass for RG4, DLFp, DLFn, DXp, DXn.
- GS_b: (1) SP8 cert (taken / counterfactual) non-null -> RG4 cert equal; (2) RG4 cert non-null -> DLFp and DLFn cert
  equal (same SP8 trajectory); (3) every rule 'rg' certificate c of RG4 / DLF* / DX* has bounded support [c] at n = 4 of
  its trajectory, every rule 'license' certificate has [c] at n = license_bound; (4) S(DLFp), S(DLFn) >= S(RG4) >= 0.
- GS_c / GS_d / GS_rg / GS_x from PAIRED_ANALYSIS_014 (TV_DLFn, TV_DLFp, S_RG4, DX_minus_DLF_p): mean / ci95 thresholds.
- G_alias_stress: stress pair = stress record with AT6_transfer >= 1; PASS iff >= 20 pairs and DLF_false == 0 on all.
- GS_ref: SECOND_IMPLEMENTATION_014: results_sha256 equals the transfer SEAL results_sha256, 288 audited, 0 mismatching,
  mutation_test passed with injected 20, distinct 20, kinds bounded >= 6, dlf >= 6, stress >= 4, detected 20,
  flagged_not_injected 0; g11 stream not stopped.
- GAPI2: TEST_SUITE_014 per_module['test_api_certify2_0120.py'] returncode 0, >= 1 result, all 'ok'; brute/api/certify2.py
  in BRUTE_SOURCE_FREEZE_014.
- G10: 288 cases, transfer SEAL complete; SP8, LXp, LXn, DXp, DXn and every SP8-trajectory arm trace 44 steps; 72 stress
  records per case; pooled fraction of recorded bounded-support queries (all trajectories, all n, both actions) with
  unknown > 0 <= 1% (per n reported).
- G_RT (i) streams transfer, repro, gti, g11 completed_at <= t0 + 7200 and not stopped; (ii) heartbeat first beat <=
  t0 + 60 and last >= end - 10 (end = t0 + RUN_DONE elapsed_s, else t0 + 7200); (iii) KILL_DRILL_014 latency <= 15 s, no
  survivors. G_HB: largest gap between consecutive beat walls with wall >= t0 <= 30 s; gaps > 10 s attributed.
- STUDY_BUDGET: a gate whose inputs are incomplete is FAIL; reason 'STUDY_BUDGET' when a STOP file exists, else
  'INCOMPLETE_INPUT (...)'."""
from __future__ import annotations
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common_014 import STUDY_DIR,PLAN,FREEZE,load,dumps,write_new,check,sha,check_freeze
from experiments.brute_study_014 import sp8_steps,lx_steps,ARMS,NS_SP8

CAP=7200;EXPECTED=288;STEPS=44;STRESS=72;FB=4;TAU6=1.645215321642;TAU7=2.07944154168
GS_A_ARMS=('RG4','DLFp','DLFn','DXp','DXn');SP8_TRAJ=('RG2','RG3','RG4','RG5','DLFp','DLFn','DLF0p','DLF0n','ATp','ATn')
STREAMS=('transfer','repro','gti','g11');BUDGETS={'transfer':2400,'gti':3600,'repro':1500,'g11':2400}
FAMILIES=('cycle3','switch3','unaliased2','ood4')
def opt(p):return load(p) if Path(p).exists() else None


def beats(d,t0):
    p=d/'HEARTBEAT_014.jsonl'
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
    for p in ('p','n'):out['DX'+p]=[s[5] for s in lx_steps(c['transfer']['LX'+p])]
    return out


def false_recount(c,arm,act):
    A=act['DX'+arm[-1]] if arm.startswith('DX') else act['SP8'];tr=c['transfer'][arm]['trace']
    return sum(1 for i,r in enumerate(tr) for b in (0,1) if r['certificate'][b] is not None and r['certificate'][b]!=A[i][b])


def containment(c):
    bad=[];T=c['transfer'];S=sp8_steps(c);BS=c['bounded']
    for i,(t,a,cert,_,_,_) in enumerate(S):
        for b in (0,1):
            r4=T['RG4']['trace'][i]['certificate'][b]
            if cert[b] is not None and r4!=cert[b]:bad.append(('sp8_not_rg4',t,b))
            for arm in ('DLFp','DLFn'):
                if r4 is not None and T[arm]['trace'][i]['certificate'][b]!=r4:bad.append((arm+'_misses_rg4',t,b))
    for arm in ('RG4','DLFp','DLFn','DLF0p','DLF0n','DXp','DXn'):
        traj='LX'+arm[-1] if arm.startswith('DX') else 'SP8';nb=T[arm].get('license_bound')
        for i,r in enumerate(T[arm]['trace']):
            for b in (0,1):
                cc=r['certificate'][b];rule=r['rule'][b]
                if rule=='rg' and list(BS[traj][str(FB)]['support'][i][b] or [])!=[cc]:bad.append((arm+'_rg_not_singleton',r['step'],b))
                if rule=='license' and list(BS[traj][str(nb)]['support'][i][b] or [])!=[cc]:bad.append((arm+'_license_not_singleton',r['step'],b))
    s=c['summary']['S']
    if not (s['DLFp']>=s['RG4']>=0 and s['DLFn']>=s['RG4']):bad.append(('S_order',s['DLFp'],s['DLFn'],s['RG4']))
    return bad


def build(study=STUDY_DIR,smoke=False):
    study=Path(study);plan=load(PLAN);C=plan['criteria']
    blk=opt(study/'transfer'/'SCIENTIFIC.json');seal=opt(study/'transfer'/'SEAL.json');rseal=opt(study/'repro'/'transfer'/'SEAL.json')
    if blk is not None:check(seal['scientific_sha256']==sha(study/'transfer'/'SCIENTIFIC.json'),'transfer: SCIENTIFIC does not match SEAL')
    stop=opt(study/'STOP_014.json');stop_o=opt(study/'STOP_014_ORCHESTRATOR.json');done=opt(study/'RUN_DONE_014.json')
    state=opt(study/'RUN_STATE_014.json') or {'stopped':{},'spent':{},'completed_at':{}}
    t0=float((study/'RUN_T0').read_text().split()[0]) if (study/'RUN_T0').exists() else None
    paired=opt(study/'PAIRED_ANALYSIS_014.json');repro=opt(study/'REPRODUCIBILITY_014.json')
    aud=opt(study/'SECOND_IMPLEMENTATION_014.json');ts=opt(study/'TEST_SUITE_014.json');drill=opt(study/'KILL_DRILL_014.json')
    if smoke and drill is None:drill=opt(ROOT/'results/study-014/KILL_DRILL_014.json')
    seen=opt(ROOT/'results/diag-014/LICENSE_DIAG_SEEN.json');seenb=opt(ROOT/'results/diag-014/LICENSE_DIAG_SEEN_B.json')
    stopped=state.get('stopped',{});fired=stop is not None or stop_o is not None;g={}
    expected=8 if smoke else EXPECTED
    def incomplete(block=True,files=(),streams=()):
        why=[]
        if block:
            if blk is None:why.append('transfer block missing')
            elif not seal.get('complete') or seal.get('case_count')!=expected:why.append(f'transfer block incomplete ({seal.get("case_count")}/{expected})')
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
    cases=blk['cases'] if blk else [];wb=incomplete()
    ACT={id(c):actuals(c) for c in cases}
    # GS_a
    per={}
    for arm in ARMS:
        rec=sum(c['transfer'][arm]['false_certificates'] for c in cases);re=sum(false_recount(c,arm,ACT[id(c)]) for c in cases)
        certs=sum(c['transfer'][arm]['certificates'] for c in cases) if all('certificates' in c['transfer'][arm] for c in cases) else None
        per[arm]={'recorded_false':rec,'recomputed_false':re,'certificates':certs,'pass':rec==0 and re==0}
    gsa={a:per[a]['pass'] for a in GS_A_ARMS}
    gate('GS_a_soundness',all(gsa.values()),{'per_arm_pass':gsa,'per_arm':per},why=wb)
    # GS_b
    cb={};nbad=0
    for c in cases:
        b=containment(c)
        if b:cb[f"{c['family']}/{c['seed']}/{c['mask_rate']}"]=b[:5];nbad+=1
    gate('GS_b_containment',nbad==0 and bool(cases),{'cases_checked':len(cases),'cases_failing':nbad,'examples':dict(list(cb.items())[:10])},why=wb)
    P=paired or {}
    def pv(k):x=P.get(k) or {};return x.get('mean'),x.get('ci95')
    wp=wb+incomplete(False,files=(('PAIRED_ANALYSIS_014.json',paired),))
    m,ci=pv('TV_DLFn');gsc={'i_DLFn_zero_false':per['DLFn']['pass'],'ii_TV_DLFn_ci_lower_le_0':ci is not None and ci[0]<=0}
    gate('GS_c_wrong_family_control',all(gsc.values()),{'clauses':gsc,'TV_DLFn_mean':m,'TV_DLFn_ci95':ci},why=wp)
    m,ci=pv('TV_DLFp');gate('GS_d_transfer_value',m is not None and m>=1.0 and ci[0]>0,{'TV_DLFp_mean':m,'TV_DLFp_ci95':ci,
         'per_family':(P.get('TV_DLFp') or {}).get('families')},why=wp)
    m,ci=pv('S_RG4');gate('GS_rg_bounded_certification',per['RG4']['pass'] and m is not None and m>=1.0 and ci[0]>0,
         {'RG4_zero_false':per['RG4']['pass'],'S_RG4_mean':m,'S_RG4_ci95':ci,'per_family':(P.get('S_RG4') or {}).get('families')},why=wp)
    m,ci=pv('DX_minus_DLF_p');gate('GS_x_discriminating_experiments',m is not None and m>=1.0 and ci[0]>0,{'DXp_minus_DLFp_mean':m,'ci95':ci,
         'DXn_minus_DLFn':pv('DX_minus_DLF_n'),'per_family':(P.get('DX_minus_DLF_p') or {}).get('families')},why=wp)
    gate('GST2_bounded_transfer',g['GS_a_soundness']['pass'] is not None and per['DLFp']['pass'] and per['DLFn']['pass'] and g['GS_c_wrong_family_control']['pass'] and g['GS_d_transfer_value']['pass'],
         {'DLFp_zero_false':per['DLFp']['pass'],'DLFn_zero_false':per['DLFn']['pass'],'GS_c':g['GS_c_wrong_family_control']['pass'],'GS_d':g['GS_d_transfer_value']['pass']},why=wp)
    # G_alias_stress
    allp=[s for c in cases for s in c['stress']];sp=[s for s in allp if s['AT6_transfer']>=1]
    out_b=[s for s in allp if s['outside_exact_bound_EVALUATOR_ONLY']]
    alias={'stress_pairs':len(sp),'DLF_false_on_stress_pairs':sum(s['DLF_false'] for s in sp),'stress_pairs_with_DLF_false':sum(s['DLF_false']>0 for s in sp),
           'AT6_false_on_stress_pairs':sum(s['AT6_false'] for s in sp),'DLF_license_on_stress_pairs':sum(s['DLF_license'] for s in sp)}
    gate('G_alias_stress',len(sp)>=20 and alias['stress_pairs_with_DLF_false']==0,dict(alias,underpowered=len(sp)<20),why=wb)
    # GS_ref
    md=(aud or {}).get('mutation_test') or {};kinds=md.get('kinds') or {}
    ref={'results_sha_matches_seal':bool(aud) and bool(seal) and aud.get('results_sha256')==seal.get('results_sha256'),
         'all_cases_audited':bool(aud) and aud.get('cases_audited')==expected and aud.get('cases_not_reached')==0,
         'zero_mismatching':bool(aud) and aud.get('mismatching_cases')==0,
         'mutation_20_of_20':md.get('passed') is True and md.get('injected')==20 and md.get('distinct_cases')==20 and md.get('detected_injected')==20 and md.get('flagged_not_injected')==0,
         'mutation_kinds':kinds.get('bounded',0)>=6 and kinds.get('dlf',0)>=6 and kinds.get('stress',0)>=4}
    gate('GS_ref_reference_audit',all(ref.values()),{'clauses':ref,'report':None if aud is None else {k:aud[k] for k in aud if k not in ('mismatches','mutation_test')},
         'mutation':{k:v for k,v in md.items() if k!='details'},'wording':'second implementation by the same author'},
         why=wb+incomplete(False,files=(('SECOND_IMPLEMENTATION_014.json',aud),),streams=('g11',)))
    # GAPI2
    pm=((ts or {}).get('per_module') or {}).get('test_api_certify2_0120.py') or {}
    frz=opt(FREEZE) or {}
    api={'module_ok':pm.get('returncode')==0 and bool(pm.get('results')) and all(v[0]=='ok' for v in pm.get('results',{}).values()),
         'certify2_in_freeze':'brute/api/certify2.py' in frz.get('sha256_files',{})}
    gate('GAPI2_certify2',all(api.values()),{'clauses':api,'results':pm.get('results')},why=incomplete(False,files=(('TEST_SUITE_014.json',ts),),streams=('gti',)))
    # G10
    tl={'SP8':all(len(c['arms']['SP8']['trace'])==STEPS for c in cases),**{a:all(len(c['transfer'][a]['trace'])==STEPS for c in cases) for a in ('LXp','LXn')+SP8_TRAJ+('DXp','DXn')}}
    unk={};tot=0;pos=0
    for c in cases:
        for traj,Bn in c['bounded'].items():
            for n,B in Bn.items():
                x=unk.setdefault(n,[0,0])
                for row in B['unknown']:
                    for u in row:x[0]+=1;x[1]+=u>0
    for n,(a,b) in unk.items():tot+=a;pos+=b
    frac=pos/tot if tot else None
    g10={'cases':len(cases)==expected and bool(seal) and bool(seal.get('complete')),'traces_44':all(tl.values()),
         'stress_72_per_case':all(len(c['stress'])==(24 if smoke else STRESS) for c in cases),'unknown_le_1pct':frac is not None and frac<=0.01}
    gate('G10_compute',all(g10.values()),{'clauses':g10,'trace_lengths_ok':tl,'unknown_fraction_pooled':None if frac is None else round(frac,6),
         'unknown_per_n':{n:{'queries':a,'unknown_gt0':b,'fraction':round(b/a,6) if a else None} for n,(a,b) in sorted(unk.items())}},why=wb)
    # G12
    g12ok=bool(repro) and repro['G12_pass'] and bool(seal) and repro['blocks']['transfer']['main_scientific_sha256']==seal['scientific_sha256']
    gate('G12_reproducibility',g12ok,None if repro is None else repro['blocks'],why=wb+incomplete(False,files=(('REPRODUCIBILITY_014.json',repro),),streams=('repro',)))
    # G13
    try:check_freeze();fz=True;fz_err=None
    except Exception as exc_:fz=False;fz_err=f'{type(exc_).__name__}: {exc_}'
    g13={'freeze_chain_holds':fz,'plan_tau6':plan['tau6']['value']==TAU6,'plan_tau7':plan['tau7']['value']==TAU7,
         'cases_use_plan_tau':bool(cases) and all(c.get('tau6')==TAU6 for c in cases),
         'seal_of_current_plan_and_freeze':bool(seal) and seal['plan_sha256']==sha(PLAN) and FREEZE.exists() and seal.get('freeze_sha256')==sha(FREEZE)}
    g13ok=all(g13.values()) if not smoke else (g13['plan_tau6'] and g13['plan_tau7'] and g13['cases_use_plan_tau'])
    gate('G13_frozen_controls_reproduce',g13ok,{'clauses':g13,'freeze_error':fz_err,'smoke_dry_run_relaxed':smoke},why=wb)
    # GTI
    V=(ts or {}).get('verdict')
    gate('GTI_test_isolation',bool(V) and V['passed'],None if ts is None else {'verdict':V,'head':ts.get('head'),'tracked_tree_dirty':ts.get('tracked_tree_dirty'),
         'clean_tag_runs':{k:(None if v is None else v.get('results')) for k,v in (ts.get('clean_tag_runs') or {}).items()},'run':'in-cap'},
         why=incomplete(False,files=(('TEST_SUITE_014.json',ts),),streams=('gti',)))
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
    fam=lambda f:[c for c in cases if c['family']==f]
    def arm_rep(a):
        return {f:{'cases':len(fam(f)),'false':sum(c['transfer'][a]['false_certificates'] for c in fam(f)),
                   'mean_S':round(sum(c['summary']['S'][a] for c in fam(f))/len(fam(f)),4) if fam(f) else None} for f in FAMILIES}
    gate('R_rg_family',None,{a:arm_rep(a) for a in ('RG2','RG3','RG4','RG5')},gated=False)
    gate('R_DLF0',None,{a:{'per_arm':per[a],'per_family':arm_rep(a),'S':pv('S_'+a),'TV':pv('TV_'+a)} for a in ('DLF0p','DLF0n')},gated=False)
    gate('R_AT_v0110',None,{a:{'per_arm':per[a],'per_family':arm_rep(a),'S':pv('S_'+a)} for a in ('ATp','ATn')},gated=False)
    gate('R_DX_vs_SP8',None,{a:{'S':pv('S_'+a),'TV':pv('TV_'+a),'per_family':arm_rep(a)} for a in ('DXp','DXn','LXp','LXn')},gated=False)
    lic={a:{f:{'rg':sum(c['transfer'][a].get('rg_certificates',0) for c in fam(f)),'license':sum(c['transfer'][a].get('license_certificates',0) for c in fam(f))}
            for f in FAMILIES} for a in ('RG4','DLFp','DLFn','DLF0p','DLF0n','DXp','DXn')}
    gate('R_license_counts',None,lic,gated=False)
    gate('R_stress_all_pairs',None,{'pairs':len(allp),'DLF_false':sum(s['DLF_false'] for s in allp),'DLF0_false':sum(s['DLF0_false'] for s in allp),
         'AT6_false':sum(s['AT6_false'] for s in allp),'pairs_outside_exact_bound':len(out_b),'DLF_false_outside_bound':sum(s['DLF_false'] for s in out_b),
         'DLF0_false_outside_bound':sum(s['DLF0_false'] for s in out_b),'AT6_false_outside_bound':sum(s['AT6_false'] for s in out_b),
         'DLF_license_all':sum(s['DLF_license'] for s in allp),'DLF0_license_all':sum(s['DLF0_license'] for s in allp)},gated=False)
    gate('R_heartbeat_attribution',None,None if not hb else hb['gaps_over_10s'],gated=False)
    gate('R_rates',None,{s:{'spent_s':round(state.get('spent',{}).get(s,0),1),'budget_s':BUDGETS[s],
         'fraction_of_budget':round(state.get('spent',{}).get(s,0)/BUDGETS[s],3)} for s in STREAMS},gated=False)
    gate('R_diag_seen',None,{'label':'seen data, exploratory (diag-014), not held-out','diag_a_sha256':None if seen is None else sha(ROOT/'results/diag-014/LICENSE_DIAG_SEEN.json'),
         'diag_b_sha256':None if seenb is None else sha(ROOT/'results/diag-014/LICENSE_DIAG_SEEN_B.json')},gated=False)
    gate('R_K_after_release',None,{'note':'test_release_0110 / 0120 after the version bump: checked post-release, reported in RELEASE.json (not scored here)'},gated=False)
    gated=[k for k,v in g.items() if v['gated']]
    return {'schema':'brute.gates.v12_0','study':plan['study'],'plan_sha256':sha(PLAN),'smoke_dry_run':smoke,'criteria_registered':sorted(C),
            'scientific_sha256':None if seal is None else seal['scientific_sha256'],'stop_rule_fired':fired,'gates':g,
            'passed':[k for k in gated if g[k]['pass']],'failed':[k for k in gated if g[k]['pass'] is False],
            'pending':[k for k in gated if g[k]['pass'] is None],'all_gated_pass':all(g[k]['pass'] for k in gated),
            'GST2':g['GST2_bounded_transfer']['pass'],'G_RT':g['G_RT_study_runtime']['pass'],'G_HB':g['G_HB_heartbeat_gap']['pass']}


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--study-dir',default=str(STUDY_DIR));ap.add_argument('--check',action='store_true')
    ap.add_argument('--output',default='GATES_014.json');ap.add_argument('--smoke',action='store_true',help='dry run on a smoke directory; prints only')
    a=ap.parse_args()
    if a.smoke:
        obj=build(Path(a.study_dir),smoke=True)
        print({k:obj[k] for k in ('passed','failed','pending')});print({k:v.get('reason') for k,v in obj['gates'].items() if v.get('reason')});raise SystemExit
    obj=build(Path(a.study_dir));out=Path(a.study_dir)/a.output
    if a.check:check(out.read_bytes()==dumps(obj),out.name+' does not reproduce');print(out.name,'reproduces')
    else:write_new(out,obj);print({k:obj[k] for k in ('passed','failed','pending','all_gated_pass')})
