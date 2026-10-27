"""Evaluate the pre-registered study-017 criteria (BRUTE_PLAN_017: headline GRL_bounded_lookahead, GDS2, GS_a5, GS_b5,
G_recount, GS_ref5, GAPI5, G10, G12, G13, GTI, G_RT, G_HB gated; non_gated_reports reported) from sealed artifacts only.
Committed and ledgered (scoring_freeze_017) before the held-out run_start; thresholds are copied from the plan, nothing is
tuned. Adapted from make_gates_016 (frozen, not edited).

Inputs in results/study-017 (D): transfer/{SCIENTIFIC,SEAL}.json, repro/transfer/SEAL.json, PAIRED_ANALYSIS_017.json,
REPRODUCIBILITY_017.json, SECOND_IMPLEMENTATION_017.json, TEST_SUITE_017.json, RUN_STATE_017.json, RUN_T0,
RUN_DONE_017.json / STOP_017.json / STOP_017_ORCHESTRATOR.json, HEARTBEAT_017.jsonl, KILL_DRILL_017.json,
HEARTBEAT_ATTRIBUTION_017.json (reported only); experiments/BRUTE_SOURCE_FREEZE_017.json.

Scoring choices fixed here, before data:
- Own trajectory: SP8, RG4, RG5, EB, DLF*, DLF2*, DLFa_* -> the SP8 trajectory actuals; RSX4 -> RSX; RSXL4, RSXLp,
  RSXLn -> RSXL; RGLX4 -> RGLX; RGL4 -> RGL; RSXL5 (ood5) -> RSXL5. An arm's recorded 'trajectory' field, when present,
  must agree. Certificate[b] at step i is false iff non-null and different from the evaluator-only actual.
- G_recount: every arm of every case (arms_by_block is covered): recorded false == recount; the trajectory SP8 learners
  (rsx, rsxl, rglx, rgl, rsxl5) likewise; stress DLF_certs / RSXL_certs; certificate counts equal trace counts and the
  summary.
- GS_a5: RG4, RGLX4, RGL4, RSXL4, DLFa_p, DLFa_n recorded == recomputed == 0 on the main cases; RG5, RSXL5 on ood5.
- GS_b5: (1) SP8 cert non-null -> RG4 cert equal (SP8 trajectory); (2) DLFa_p and DLFa_n certificate lists equal RG4's at
  every step; (3) on the RGLX trajectory, at every step t >= switch_step (RG4's first certificate + 1) the recorded
  (action, rule) equals brute.regionsplit.rsx_choose(t, burn_in, bounded_sizes, sp8_action) and lookahead is None;
  (4) every rule 'rg' / 'license' / 'eb' certificate c has recorded bounded support [c] at the arm's n / license_bound /
  row bound on the arm's own trajectory. Main and ood5 cases ((2), (3) main only).
- GRL: (i) RGLX4 0 false (GS_a5 clause); (ii) PAIRED TV_RGLX4 mean >= 1.0; (iii) TV_RGLX4 ci95 lower > 0.
- GDS2: (i) RSXL4 0 false; (ii) S(RSXL4) == S(RG4) on every main case (summary and recomputed first taken-action
  certificate steps); (iii) PAIRED dC_RSXL4 mean >= 0.03; (iv) dC_RSXL4 ci95 lower > 0.
- GS_ref5: SECOND_IMPLEMENTATION_017 results_sha256 equals the transfer SEAL results_sha256, 432 audited, 0 not reached,
  0 mismatching, mutation 20 / 20 distinct detected, flagged_not_injected 0, kinds exactly v0150_reference.KINDS; g11
  not stopped.
- GAPI5: TEST_SUITE_017 per_module['test_api_certify5_0150.py'] returncode 0, >= 4 results, all 'ok';
  brute/api/certify5.py in BRUTE_SOURCE_FREEZE_017.
- G10: 432 cases, transfer SEAL complete; every trace 44 steps; 72 stress records per main case; per trajectory (SP8,
  RSX, RSXL, RGLX, RGL; ood5 SP8, RSXL5) the fraction of recorded bounded-support queries with unknown > 0 is <= 1%.
- G12: REPRODUCIBILITY_017 G12_pass, 144 expected (120 main + 24 ood5).
- G13: check_freeze (017 chain), plan tau6, case tau6, SEAL of the current plan and freeze, and rg_arm / dlf_arm /
  sp8_steps are the frozen brute_study_014 functions (sha equal to BRUTE_SOURCE_FREEZE_014).
- G_RT (i) streams transfer, repro, gti, g11 completed_at <= t0 + 7200 and not stopped; (ii) heartbeat first beat <=
  t0 + 60 and last >= end - 10; (iii) KILL_DRILL_017 latency <= 15 s, no survivors. G_HB: largest gap <= 30 s
  (unchanged; the deviation #90 sentinel attribution is reported in R_heartbeat_attribution and changes no verdict).
- STUDY_BUDGET: a gate whose inputs are incomplete is FAIL; reason 'STUDY_BUDGET' when a STOP file exists, else
  'INCOMPLETE_INPUT (...)'."""
from __future__ import annotations
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common_017 import STUDY_DIR,PLAN,FREEZE,load,dumps,write_new,check,sha,check_freeze
from experiments.brute_study_014 import sp8_steps,lx_steps
import experiments.brute_study_014 as S14
import experiments.brute_study_017 as S16
from brute.regionsplit import rsx_choose
from experiments.v0150_reference import KINDS as REF_KINDS
from scripts.make_gates_015 import beats as _beats015,wrong,wrong_certs,opt,ck

CAP=7200;EXPECTED_MAIN=360;EXPECTED_OOD5=72;STEPS=44;STRESS=72;FB=4;TAU6=1.645215321642;CENSOR=45;SLOTS=88
MAIN=('RG4','RG5','RGLX4','RGL4','RSXL4','RSXLp','RSXLn','DLFp','DLFn','DLFa_p','DLFa_n','DLF2p','DLF2n','RSX4','EB');OOD5=('RG4','RG5','RSXL5')
TRAJ={'RSX4':'RSX','RSXL4':'RSXL','RSXLp':'RSXL','RSXLn':'RSXL','RGLX4':'RGLX','RGL4':'RGL','RSXL5':'RSXL5'}
GS_A5=('RG4','RGLX4','RGL4','RSXL4','DLFa_p','DLFa_n');GS_A5_OOD5=('RG5','RSXL5')
TRAJ_KEY={'RSX':'rsx','RSXL':'rsxl','RGLX':'rglx','RGL':'rgl','RSXL5':'rsxl5'}
STREAMS=('transfer','repro','gti','g11');BUDGETS={'transfer':3000,'gti':3600,'repro':1500,'g11':2400}
FAMILIES=('cycle3','switch3','unaliased2','ood4');KINDS={k:REF_KINDS.count(k) for k in sorted(set(REF_KINDS))}


def beats(d,t0):
    p=Path(d)/'HEARTBEAT_017.jsonl'
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
    for t,k in TRAJ_KEY.items():
        if k in c:out[t]=[s[5] for s in lx_steps(c[k])]
    return out


def traj_of(c,arm):
    t=TRAJ.get(arm,'SP8');rec=c['transfer'][arm].get('trajectory')
    check(rec is None or rec==t,f'{ck(c)} {arm}: recorded trajectory {rec} != {t}');return t


def recount(c,act):
    """[(arm, recorded, recomputed)] for one case, every arm of arms_by_block."""
    S=sp8_steps(c);out=[('SP8',c['summary']['false']['SP8'],sum(cert[b] is not None and cert[b]!=act['SP8'][i][b] for i,(t,a,cert,_,_,_) in enumerate(S) for b in (0,1)))]
    for arm in c['transfer']:out.append((arm,c['transfer'][arm]['false_certificates'],wrong(c['transfer'][arm]['trace'],act[traj_of(c,arm)])))
    for t,k in TRAJ_KEY.items():
        if k in c:out.append((t+'_trajectory_SP8',c[k]['false_certificates'],wrong(c[k]['trace'],act[t])))
    for s in c.get('stress',[]):
        out.append(('stress_DLF_SP8',s['DLF_false'],wrong_certs(s['DLF_certs'],act['SP8'])))
        out.append(('stress_DLF_RSXL',s['RSXL_false'],wrong_certs(s['RSXL_certs'],act['RSXL'])))
    return out


def cert_counts(c):
    """[(arm, problem)] where the recorded certificate count disagrees with its trace or with the summary."""
    bad=[]
    for arm,A in c['transfer'].items():
        n=sum(x is not None for r in A['trace'] for x in r['certificate'])
        if A['certificates']!=n:bad.append((arm,'trace',A['certificates'],n))
        if c['summary']['certificates'].get(arm)!=A['certificates']:bad.append((arm,'summary',c['summary']['certificates'].get(arm),A['certificates']))
    return bad


def taken_actions(c,traj):
    if traj=='SP8':return [s[1] for s in sp8_steps(c)]
    return [r['action'] for r in c[TRAJ_KEY[traj]]['trace']]


def first_cert(c,arm):
    A=taken_actions(c,traj_of(c,arm))
    for i,r in enumerate(c['transfer'][arm]['trace']):
        if r['certificate'][A[i]] is not None:return i+1
    return CENSOR


def containment(c):
    bad=[];T=c['transfer'];S=sp8_steps(c);BS=c['bounded']
    for i,(t,a,cert,_,_,_) in enumerate(S):
        for b in (0,1):
            if cert[b] is not None and T['RG4']['trace'][i]['certificate'][b]!=cert[b]:bad.append(('sp8_not_rg4',t,b))
    for arm in ('DLFa_p','DLFa_n'):
        if arm in T and [r['certificate'] for r in T[arm]['trace']]!=[r['certificate'] for r in T['RG4']['trace']]:bad.append((arm+'_differs_from_rg4',None,None))
    if 'rglx' in c:
        sw=c['rglx']['switch_step'];burn=c['burn_in'];f=T['RGLX4']['first_cert_step'];L=len(c['rglx']['trace'])
        if sw!=(f+1 if f<L else None):bad.append(('rglx_switch_not_after_rg4_first_certificate',sw,f))
        for r in c['rglx']['trace']:
            if sw is not None and r['step']>=sw:
                want=tuple(rsx_choose(r['step'],burn,r['bounded_sizes'],r['sp8_action']))
                if (r['action'],r['rule'])!=want or r['lookahead'] is not None:bad.append(('rglx_not_rsx_after_switch',r['step'],want));break
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
    stop=opt(study/'STOP_017.json');stop_o=opt(study/'STOP_017_ORCHESTRATOR.json');done=opt(study/'RUN_DONE_017.json')
    state=opt(study/'RUN_STATE_017.json') or {'stopped':{},'spent':{},'completed_at':{}}
    t0=float((study/'RUN_T0').read_text().split()[0]) if (study/'RUN_T0').exists() else None
    paired=opt(study/'PAIRED_ANALYSIS_017.json');repro=opt(study/'REPRODUCIBILITY_017.json')
    aud=opt(study/'SECOND_IMPLEMENTATION_017.json');ts=opt(study/'TEST_SUITE_017.json');drill=opt(study/'KILL_DRILL_017.json')
    if smoke and drill is None:drill=opt(ROOT/'results/study-017/KILL_DRILL_017.json')
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
    # G_recount
    tot={};bad_rc=[];bad_cc=[]
    for c in allc:
        blkname='ood5' if c['family']=='ood5' else 'transfer'
        for arm,rec,re in recount(c,ACT[id(c)]):
            x=tot.setdefault(blkname,{}).setdefault(arm,{'recorded_false':0,'recomputed_false':0,'records':0,'mismatching_records':0})
            x['recorded_false']+=rec;x['recomputed_false']+=re;x['records']+=1
            if rec!=re:x['mismatching_records']+=1;bad_rc.append((ck(c),arm,rec,re))
        bad_cc+=[(ck(c),)+b for b in cert_counts(c)]
    want={b:set(v) for b,v in plan['arms_by_block'].items()}
    have={b:{('stress' if a.startswith('stress_') else 'SP8' if a.endswith('_trajectory_SP8') else a) for a in v} for b,v in tot.items()}
    cover={b:sorted(want[b]-have.get(b,set())) for b in want}
    gate('G_recount',not bad_rc and not bad_cc and bool(allc) and not any(cover.values()),{'per_block_arm':tot,'mismatches':bad_rc[:50],
         'certificate_count_mismatches':bad_cc[:50],'arms_by_block_not_recounted':cover},why=wb)
    T=tot.get('transfer',{})
    per={a:dict(T.get(a,{}),certificates=sum(c['transfer'][a]['certificates'] for c in cases),
                pass_=T.get(a,{}).get('recorded_false')==0 and T.get(a,{}).get('recomputed_false')==0) for a in MAIN}
    for a in per:per[a]['pass']=per[a].pop('pass_')
    T5=tot.get('ood5',{})
    per5={a:dict(T5.get(a,{}),certificates=sum(c['transfer'][a]['certificates'] for c in c5),
                 pass_=T5.get(a,{}).get('recorded_false')==0 and T5.get(a,{}).get('recomputed_false')==0) for a in OOD5}
    for a in per5:per5[a]['pass']=per5[a].pop('pass_')
    gsa={a:per[a]['pass'] for a in GS_A5}|{'ood5_'+a:per5[a]['pass'] for a in GS_A5_OOD5}
    gate('GS_a5_soundness',all(gsa.values()),{'per_arm_pass':gsa,'per_arm':per,'per_arm_ood5':per5},why=wb)
    # GS_b5
    cb={};nbad=0
    for c in allc:
        b=containment(c)
        if b:cb[ck(c)]=b[:5];nbad+=1
    gate('GS_b5_containment',nbad==0 and bool(allc),{'cases_checked':len(allc),'cases_failing':nbad,'examples':dict(list(cb.items())[:10])},why=wb)
    P=paired or {}
    def pv(k):x=P.get(k) or {};return x.get('mean'),x.get('ci95')
    def fam_of(k):x=P.get(k) or {};return {q:x.get(q) for q in ('families','histogram','cases_positive','cases_negative','cases_zero')}
    wp=wb+incomplete(False,files=(('PAIRED_ANALYSIS_017.json',paired),))
    # GRL (headline)
    m,ci=pv('TV_RGLX4')
    grl={'i_RGLX4_zero_false':per['RGLX4']['pass'],'ii_TV_mean_ge_1.0':m is not None and m>=1.0,'iii_TV_ci_lower_gt_0':ci is not None and ci[0]>0}
    gate('GRL_bounded_lookahead',all(grl.values()),{'clauses':grl,'TV_RGLX4_mean':m,'TV_RGLX4_ci95':ci,'S_RGLX4':pv('S_RGLX4'),'S_RG4':pv('S_RG4'),
         'C_RGLX4':pv('C_RGLX4'),'dC_RGLX4':pv('dC_RGLX4'),'TV_RGL4':pv('TV_RGL4'),**fam_of('TV_RGLX4')},why=wp)
    # GDS2
    neq=[ck(c) for c in cases if c['summary']['S']['RSXL4']!=c['summary']['S']['RG4']
         or first_cert(c,'RSXL4')!=first_cert(c,'RG4') or first_cert(c,'RSXL4')!=c['transfer']['RSXL4']['first_cert_step']]
    m,ci=pv('dC_RSXL4')
    gds={'i_RSXL4_zero_false':per['RSXL4']['pass'],'ii_S_RSXL4_eq_S_RG4_every_case':bool(cases) and not neq,
         'iii_dC_mean_ge_0.03':m is not None and m>=0.03,'iv_dC_ci_lower_gt_0':ci is not None and ci[0]>0}
    gate('GDS2_deferred_split_replication',all(gds.values()),{'clauses':gds,'dC_RSXL4_mean':m,'dC_RSXL4_ci95':ci,'cases_S_differs':neq[:50],
         'C_RSXL4':pv('C_RSXL4'),'C_RG4':pv('C_RG4'),**fam_of('dC_RSXL4')},why=wp)
    allp=[s for c in cases for s in c['stress']]
    # GS_ref5
    md=(aud or {}).get('mutation_test') or {};kinds=md.get('kinds') or {}
    ref={'results_sha_matches_seal':bool(aud) and bool(seal) and aud.get('results_sha256')==seal.get('results_sha256'),
         'all_cases_audited':bool(aud) and aud.get('cases_audited')==expected and aud.get('cases_not_reached')==0,
         'zero_mismatching':bool(aud) and aud.get('mismatching_cases')==0,
         'mutation_20_of_20':md.get('passed') is True and md.get('injected')==20 and md.get('distinct_cases')==20 and md.get('detected_injected')==20 and md.get('flagged_not_injected')==0,
         'mutation_kinds':kinds==KINDS}
    gate('GS_ref5_reference_audit',all(ref.values()),{'clauses':ref,'report':None if aud is None else {k:aud[k] for k in aud if k not in ('mismatches','mutation_test')},
         'mutation':{k:v for k,v in md.items() if k!='details'},'wording':'second implementation by the same author'},
         why=wb+incomplete(False,files=(('SECOND_IMPLEMENTATION_017.json',aud),),streams=('g11',)))
    # GAPI5
    pm=((ts or {}).get('per_module') or {}).get('test_api_certify5_0150.py') or {}
    frz=opt(FREEZE) or {}
    api={'module_ok':pm.get('returncode')==0 and len(pm.get('results') or {})>=4 and all(v[0]=='ok' for v in pm.get('results',{}).values()),
         'certify5_in_freeze':'brute/api/certify5.py' in frz.get('sha256_files',{})}
    gate('GAPI5_certify5',all(api.values()),{'clauses':api,'results':pm.get('results')},why=incomplete(False,files=(('TEST_SUITE_017.json',ts),),streams=('gti',)))
    # G10
    tl={'SP8':all(len(c['arms']['SP8']['trace'])==STEPS for c in allc),'RSX':all(len(c['rsx']['trace'])==STEPS for c in cases),
        'RSXL':all(len(c['rsxl']['trace'])==STEPS for c in cases),'RGLX':all(len(c['rglx']['trace'])==STEPS for c in cases),
        'RGL':all(len(c['rgl']['trace'])==STEPS for c in cases),'RSXL5':all(len(c['rsxl5']['trace'])==STEPS for c in c5),
        **{a:all(len(c['transfer'][a]['trace'])==STEPS for c in allc if a in c['transfer']) for a in MAIN+OOD5}}
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
         'unknown_le_1pct_every_trajectory':bool(frac) and set(frac)=={'SP8','RSX','RSXL','RGLX','RGL','RSXL5'} and all(f is not None and f<=0.01 for f in frac.values())}
    gate('G10_compute',all(g10.values()),{'clauses':g10,'trace_lengths_ok':tl,'unknown_fraction_per_trajectory':{t:None if f is None else round(f,6) for t,f in frac.items()},
         'unknown_per_trajectory_n':{t:{n:{'queries':a,'unknown_gt0':b} for n,(a,b) in sorted(d.items())} for t,d in unk.items()}},why=wb)
    # G12
    g12ok=bool(repro) and repro['G12_pass'] and bool(seal) and repro['blocks']['transfer']['main_scientific_sha256']==seal['scientific_sha256'] \
          and repro['blocks']['transfer']['expected']==(4 if smoke else 144)
    gate('G12_reproducibility',g12ok,None if repro is None else repro['blocks'],why=wb+incomplete(False,files=(('REPRODUCIBILITY_017.json',repro),),streams=('repro',)))
    # G13
    try:check_freeze();fz=True;fz_err=None
    except Exception as exc_:fz=False;fz_err=f'{type(exc_).__name__}: {exc_}'
    f14=(opt(ROOT/'experiments/BRUTE_SOURCE_FREEZE_014.json') or {}).get('sha256_files',{})
    g13={'freeze_chain_holds':fz,'plan_tau6':plan['tau6']['value']==TAU6,
         'cases_use_plan_tau':bool(allc) and all(c.get('tau6')==TAU6 for c in allc),
         'rg_dlf_are_frozen_v0120':S16.rg_arm is S14.rg_arm and S16.dlf_arm is S14.dlf_arm and S16.sp8_steps is S14.sp8_steps
              and f14.get('experiments/brute_study_014.py')==sha(ROOT/'experiments/brute_study_014.py'),
         'seal_of_current_plan_and_freeze':bool(seal) and seal['plan_sha256']==sha(PLAN) and FREEZE.exists() and seal.get('freeze_sha256')==sha(FREEZE)}
    g13ok=all(g13.values()) if not smoke else (g13['plan_tau6'] and g13['cases_use_plan_tau'] and g13['rg_dlf_are_frozen_v0120'])
    gate('G13_frozen_controls_reproduce',g13ok,{'clauses':g13,'freeze_error':fz_err,'smoke_dry_run_relaxed':smoke},why=wb)
    # GTI
    V=(ts or {}).get('verdict')
    gate('GTI_test_isolation',bool(V) and V['passed'],None if ts is None else {'verdict':V,'head':ts.get('head'),'tracked_tree_dirty':ts.get('tracked_tree_dirty'),
         'dirty_tracked_files':ts.get('dirty_tracked_files'),
         'clean_tag_runs':{k:(None if v is None else v.get('results')) for k,v in (ts.get('clean_tag_runs') or {}).items()},'run':'in-cap'},
         why=incomplete(False,files=(('TEST_SUITE_017.json',ts),),streams=('gti',)))
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
    # ---- reports (non_gated_reports)
    fam=lambda f:[c for c in allc if c['family']==f]
    def arm_rep(a,fams=FAMILIES):
        return {f:{'cases':len(fam(f)),'false':sum(c['transfer'][a]['false_certificates'] for c in fam(f)),
                   'certificates':sum(c['transfer'][a]['certificates'] for c in fam(f)),
                   'mean_S':round(sum(c['summary']['S'][a] for c in fam(f))/len(fam(f)),4) if fam(f) else None} for f in fams}
    raw=opt(study/'transfer'/'RESULTS.json')   # timing keys live only in the unsealed RESULTS.json (SCIENTIFIC strips them)
    RW={(c['family'],c['seed'],c['mask_rate']):c for c in raw['cases']} if raw else {}
    def lk(k):
        L=[c[k] for c in cases];st=sum(x['lookahead_steps'] for x in L)
        W=[RW.get((c['family'],c['seed'],c['mask_rate']),{}).get(k,{}).get('lookahead_wall_informational') for c in cases]
        w=sum(W) if W and all(x is not None for x in W) else None
        return {'lookahead_steps':st,'lookahead_wall_s_informational':None if w is None else round(w,3),
                'wall_per_lookahead_step_ms':round(1000*w/st,4) if st and w is not None else None,
                'timing_source':'transfer/RESULTS.json (informational, unsealed)' if w is not None else 'RESULTS.json absent or incomplete: timing not reported',
                'rule_counts':{f:{r:sum(c[k]['rule_counts'].get(r,0) for c in fam(f)) for r in ('rgl','rsx','sp8')} for f in FAMILIES}}
    gate('R_RGL',None,{'per_arm':per['RGL4'],'S':pv('S_RGL4'),'TV':pv('TV_RGL4'),'C':pv('C_RGL4'),'dC':pv('dC_RGL4'),'per_family':arm_rep('RGL4'),
         'RGL_trajectory':lk('rgl') if cases else None,'RGLX_trajectory':lk('rglx') if cases else None,
         'cases_RGL4_S_eq_RGLX4_S':sum(c['summary']['S']['RGL4']==c['summary']['S']['RGLX4'] for c in cases)},gated=False)
    gate('R_coverage',None,{'C_main':{a:pv('C_'+a) for a in MAIN},'dC_RGLX4':{'mean_ci':pv('dC_RGLX4'),**fam_of('dC_RGLX4')},
         'per_family_C':{a:{f:(round(sum(c['transfer'][a]['certificates'] for c in fam(f))/(len(fam(f))*SLOTS),6) if fam(f) else None) for f in FAMILIES} for a in MAIN},
         'C_ood5':{a:round(sum(c['transfer'][a]['certificates'] for c in c5)/(len(c5)*SLOTS),6) if c5 else None for a in OOD5},
         'C_SP8_main':round(sum(1 for c in cases for s_ in sp8_steps(c) for b in (0,1) if s_[2][b] is not None)/(len(cases)*SLOTS),6) if cases else None},gated=False)
    gate('R_DLF',None,{**{a:{'per_arm':per[a],'per_family':arm_rep(a),'S':pv('S_'+a),'TV':pv('TV_'+a),'dC':pv('dC_'+a)} for a in ('DLFp','DLFn','RSXLp','RSXLn','DLF2p','DLF2n')},
         'DLFa_equal_RG4_cases':{a:sum([r['certificate'] for r in c['transfer'][a]['trace']]==[r['certificate'] for r in c['transfer']['RG4']['trace']] for c in cases) for a in ('DLFa_p','DLFa_n')},
         'DLFa_attested_cases':{a:sum(bool(c['transfer'][a].get('attested')) for c in cases) for a in ('DLFa_p','DLFa_n')},
         'DLFa':{a:per[a] for a in ('DLFa_p','DLFa_n')},'EB':{'per_arm':per['EB'],'S':pv('S_EB')},'RSX4':{'per_arm':per['RSX4'],'S':pv('S_RSX4'),'TV':pv('TV_RSX4')}},gated=False)
    gate('R_ood5',None,{'cases':len(c5),**{a:{'per_arm':per5[a],'S':pv('ood5_S_'+a),'C':round(per5[a]['certificates']/(len(c5)*SLOTS),6) if c5 else None,
         'cases_with_false':sum(c['transfer'][a]['false_certificates']>0 for c in c5)} for a in OOD5},
         'SP8_false':tot.get('ood5',{}).get('SP8',{}).get('recorded_false')},gated=False)
    out_b=[s_ for s_ in allp if s_['outside_exact_bound_EVALUATOR_ONLY']]
    gate('R_stress',None,{'pairs':len(allp),'DLF_false':sum(s_['DLF_false'] for s_ in allp),'RSXL_false':sum(s_['RSXL_false'] for s_ in allp),
         'AT6_false':sum(s_['AT6_false'] for s_ in allp),'pairs_outside_exact_bound':len(out_b),'DLF_false_outside_bound':sum(s_['DLF_false'] for s_ in out_b),
         'RSXL_false_outside_bound':sum(s_['RSXL_false'] for s_ in out_b)},gated=False)
    hba=opt(study/'HEARTBEAT_ATTRIBUTION_017.json')
    gate('R_heartbeat_attribution',None,{'watchdog_gaps_over_10s':None if not hb else hb['gaps_over_10s'],
         'sentinel_attribution':None if hba is None else {k:hba.get(k) for k in ('max_watchdog_gap_s','max_sentinel_tick_gap_s','class_counts','gaps_over_10s','sentinel_records')},
         'label':'Inferred; deviation #90 diagnostic, changes no verdict'},gated=False)
    gate('R_rates',None,{s_:{'spent_s':round(state.get('spent',{}).get(s_,0),1),'budget_s':BUDGETS[s_],
         'fraction_of_budget':round(state.get('spent',{}).get(s_,0)/BUDGETS[s_],3)} for s_ in STREAMS}|
         {'lookahead_cost':{k:lk(k) for k in ('rgl','rglx')} if cases else None},gated=False)
    gated=[k for k,v in g.items() if v['gated']]
    return {'schema':'brute.gates.v15_0','study':plan['study'],'plan_sha256':sha(PLAN),'smoke_dry_run':smoke,'criteria_registered':sorted(C),
            'criteria_scored':sorted(gated),'scientific_sha256':None if seal is None else seal['scientific_sha256'],'stop_rule_fired':fired,'gates':g,
            'passed':[k for k in gated if g[k]['pass']],'failed':[k for k in gated if g[k]['pass'] is False],
            'pending':[k for k in gated if g[k]['pass'] is None],'all_gated_pass':all(g[k]['pass'] for k in gated),
            'GRL':g['GRL_bounded_lookahead']['pass'],'GDS2':g['GDS2_deferred_split_replication']['pass'],'G_RT':g['G_RT_study_runtime']['pass'],'G_HB':g['G_HB_heartbeat_gap']['pass']}


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--study-dir',default=str(STUDY_DIR));ap.add_argument('--check',action='store_true')
    ap.add_argument('--output',default='GATES_017.json');ap.add_argument('--smoke',action='store_true',help='dry run on a smoke directory; prints only')
    a=ap.parse_args()
    if a.smoke:
        obj=build(Path(a.study_dir),smoke=True)
        print({k:obj[k] for k in ('passed','failed','pending')});print({k:v.get('reason') for k,v in obj['gates'].items() if v.get('reason')});raise SystemExit
    obj=build(Path(a.study_dir));out=Path(a.study_dir)/a.output
    if a.check:check(out.read_bytes()==dumps(obj),out.name+' does not reproduce');print(out.name,'reproduces')
    else:write_new(out,obj);print({k:obj[k] for k in ('passed','failed','pending','all_gated_pass')})
