"""Gates for study-065 (BRUTE_PLAN_065 criteria; the pre-run deviation #204 fixes the definitions), LEAN process. Committed in the
source freeze before main_run_065; nothing is tuned after results are seen. New file; built from scripts/make_gates_064.py (frozen).
HONEST FRAMING (plan honest_framing): a NOISE test of the v0.60.0 clique-anchored method on 2-bit 20-state worlds through a new
sequential (random-walk / SPRT) per-bit re-read front end, certify/20s, at eps 0.10 / 0.20 / 0.30.
Inputs (D = results/study-065): D/main/{RESULTS,SCIENTIFIC,SEAL}.json, D/main/RECOUNT_065.json, D/main/REFERENCE_065.json,
D/API_CHECKS_065.json, D/TEST_SUITE_065.json, results/diag-065/SEEDCHECK_065.json, experiments/COMMIT_ORDER_065.json,
results/RESEARCH_LEDGER.jsonl. Missing or partial input => every data gate FAIL INCOMPLETE_INPUT. Records are accepted only if
sha256(RESULTS) equals the seal and no_time(RESULTS) equals SCIENTIFIC. Labels: recounted if G_recount65 passes, else the study's.
Arms: C20 (n seeds), S30 (n), S20 (first n_s20), S10 (first n_s10), S30b (first n_s30b). Decided = ID or IDF.
  GS65_sound: WRONG 0 on every record;
  GMAJ65: 0 settled-bit errors over every observation of every noisy record (the recounted numbers if G_recount65 passes);
  GEQ65: canon_inner(noisy arm) == canon_inner(C20) for every noisy record on its seed;
  GN65 (headline): S30 decided >= ceil(3 n / 6) and >= C20 decided - 1; Wilson 95% CI;
  GN_low65: S10 decided >= C20 decided on the same seeds - 1 and the same for S20;
  GREAD65: in each of S10, S20, S30: sum reads_total <= 0.35 x sum fixed_reads_total (certify20n.reads_for on the same observations);
  GDET65: canon65(S30) == canon65(S30b) on every S30b seed; 0 wall-guard firings in every arm;
  GFID65: API_CHECKS_065 fidelity exact on every decided noisy record (bound to the sealed RESULTS sha), equiv PASS (certify/20s at
     eps_bar 0 == certify/20p on the smoke worlds) and threshold PASS (exact fractions, t 1..500, each eps_bar);
  GHOST65: API_CHECKS_065 ghost: the no-network run made 0 socket attempts and certify20s.py's sha equals its freeze sha;
  GS_ref65: REFERENCE_065 on block main: sha bound, 0 mismatches, complete (every decided record audited) within 1800 s on 6 workers,
     20/20 mutations (vacuous only if nothing is decided);
  G_recount65: RECOUNT_065 bound and PASS; GTEST65: gated modules of TEST_SUITE_065 pass;
  G_PROC65: preregistration_065, build_authorization_065, seedcheck_065, prefreeze_smoke_065, deviation_204, freeze_065,
     main_run_065 as a subsequence, parseable non-decreasing note times, commit-order file, main sealed.
  Certification (plan certification_rule): every gate passes -> 'certified (read_bits 2, N <= 20, iid bit noise eps <= 0.30, delta
  0.001, sequential re-reads)'; every gate except GN65 -> the same with eps <= 0.20; if GMAJ65, GEQ65, GS_ref65 or GS65_sound fails, or
  any other gate fails: no certification.
  Secondary (reported): READS65 (per arm and per record), MC65 (API_CHECKS Monte-Carlo per-bit error), GCOST65, GSTATS65, SEEDCHECK65.
  PYTHONPATH=. python scripts/make_gates_065.py [--study-dir D] [--check]"""
from __future__ import annotations
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common import load,dumps,write_new,check,sha
from experiments.brute_common_026 import wilson
from scripts.make_gates_034 import opt
from scripts.make_gates_043 import subseq

STUDY_DIR=ROOT/'results/study-065';ARMS=('C20','S10','S20','S30','S30b');NOISY=('S10','S20','S30','S30b')
LABELS=('ID','IDF','AMB','WRONG','IDU','NOFIT');SOFT=('GN65',);HARD=('GMAJ65','GEQ65','GS_ref65','GS65_sound');REF_BUDGET=1800.0;REF_WORKERS=6
READ_RATIO=0.35;min30=lambda n:-(-3*n//6)
PROC_ORDER=('preregistration_065','build_authorization_065','seedcheck_065','prefreeze_smoke_065','deviation_204','freeze_065','main_run_065')
PHRASE30='certified (read_bits 2, N <= 20, iid bit noise eps <= 0.30, delta 0.001, sequential re-reads)'
PHRASE20='certified (read_bits 2, N <= 20, iid bit noise eps <= 0.20, delta 0.001, sequential re-reads)'


def ckey(c):return f"{c['block']}/{c['key']}/{c['seed']}"


def ledger():
    from datetime import datetime
    L=[json.loads(x) for x in (ROOT/'results/RESEARCH_LEDGER.jsonl').read_text().splitlines() if x.strip()]
    i0=next((i for i,e in enumerate(L) if e.get('event')=='preregistration_065'),None);out=[]
    for e in (L[i0:] if i0 is not None else []):
        try:t=datetime.fromisoformat(str(e.get('note',''))[:25])
        except ValueError:t=None
        out.append((e['event'],t))
        if e['event']==PROC_ORDER[-1]:break
    return out


def status_phrase(c30,c20,failed):
    if c30:return PHRASE30
    if c20:return PHRASE20+'; eps 0.30 stays Open'
    return 'not certified, no certification status (failing gates: '+', '.join(failed)+')'


def build(study=STUDY_DIR,expect=None):
    from brute.evaluation import no_time
    from experiments.brute_study_065 import canon65,canon_inner,N_SEEDS,N_S20,N_S10,N_S30B
    study=Path(study);D=study/'main';Gt={};sec={}
    seal=opt(D/'SEAL.json');sci=opt(D/'SCIENTIFIC.json');res=opt(D/'RESULTS.json');rc=opt(D/'RECOUNT_065.json')
    ref=opt(D/'REFERENCE_065.json');ts=opt(study/'TEST_SUITE_065.json');order=opt(ROOT/'experiments/COMMIT_ORDER_065.json')
    api=opt(study/'API_CHECKS_065.json');fz=opt(ROOT/'experiments/BRUTE_SOURCE_FREEZE_065.json')
    sc=opt(ROOT/'results/diag-065/SEEDCHECK_065.json')
    rsha=sha(D/'RESULTS.json') if (D/'RESULTS.json').exists() else None
    sealed=(bool(seal) and res is not None and sci is not None and rsha==seal.get('results_sha256')
            and sha(D/'SCIENTIFIC.json')==seal.get('scientific_sha256') and no_time(res)==sci)
    if expect is not None:n,n20,n10,nb=expect
    else:
        r_=res or {};n=int(r_.get('n_seeds',N_SEEDS));n20=int(r_.get('n_s20',N_S20));n10=int(r_.get('n_s10',N_S10));nb=int(r_.get('n_s30b',N_S30B))
    main=[c for c in (res or {}).get('cases',[]) if c['block']=='main'] if sealed else []
    cs=sorted([c for c in main if c['key']=='scale20'],key=lambda c:c['seed'])
    want=lambda i:sorted(['C20','S30']+(['S20'] if i<n20 else [])+(['S10'] if i<n10 else [])+(['S30b'] if i<nb else []))
    arms_ok=all(sorted(c['arms'])==want(i) for i,c in enumerate(cs))
    complete=sealed and seal.get('complete') is True and len(cs)==len(main)==n and arms_ok
    wb=None if complete else 'INCOMPLETE_INPUT (main missing, partial, missing arms or not matching its seal)'
    def gate(name,ok,obs,why=None):Gt[name]={'pass':bool(ok) and why is None,'observed':obs,**({'reason':why} if why else {})}
    pc=(rc or {}).get('per_case') or {}
    rc_bound=bool(rc) and rc.get('results_sha256')==rsha and rc.get('cases')==len((res or {}).get('cases',[]))
    rc_ok=rc_bound and rc.get('PASS') is True and not rc.get('mismatches')
    rget=lambda c,a,f:((pc.get(str(c['seed'])) or {}).get(a) or {}).get(f)
    lab=(lambda c,a:rget(c,a,'label')) if rc_ok else (lambda c,a:c['arms'][a]['label'])
    lsrc='recount' if rc_ok else 'study labels (G_recount65 did not pass)'
    dd=lambda c,a:a in c['arms'] and lab(c,a) in ('ID','IDF')
    ci=lambda x,m:wilson(x,m) if m else None
    wrong=[[ckey(c),a] for c in cs for a in c['arms'] if lab(c,a)=='WRONG' or c['arms'][a]['label']=='WRONG']
    gate('GS65_sound',complete and not wrong,{'WRONG':wrong,'records':sum(len(c['arms']) for c in cs),
         'per_case':[[c['seed']]+[lab(c,a) if a in c['arms'] else None for a in ARMS] for c in cs],'columns':['seed']+list(ARMS),'label_source':lsrc},why=wb)
    sbe=lambda c,a:(rget(c,a,'settled_bit_errors') if rc_ok else c['arms'][a].get('settled_bit_errors'))
    errs=[[ckey(c),a,sbe(c,a)] for c in cs for a in c['arms'] if a in NOISY]
    nobs=sum(c['arms'][a].get('observations') or 0 for c in cs for a in c['arms'] if a in NOISY)
    gate('GMAJ65',complete and all(e[2]==0 for e in errs),{'settled_bit_errors_total':sum((e[2] or 0) for e in errs),'noisy_records':len(errs),
         'noisy_observations':nobs,'nonzero':[e for e in errs if e[2]],'source':lsrc},why=wb)
    eqr=[[c['seed'],a,canon_inner(c['arms'][a])==canon_inner(c['arms']['C20'])] for c in cs for a in c['arms'] if a in NOISY]
    gate('GEQ65',complete and all(x[2] for x in eqr),{'equal':sum(x[2] for x in eqr),'of':len(eqr),'per_record':eqr,'columns':['seed','arm','inner_equal_C20']},why=wb)
    cnt={a:sum(dd(c,a) for c in cs) for a in ARMS};m_={a:sum(a in c['arms'] for c in cs) for a in ARMS}
    c20_on=lambda a:sum(dd(c,'C20') for c in cs if a in c['arms'])
    gate('GN65',complete and cnt['S30']>=min30(n) and cnt['S30']>=cnt['C20']-1,{'S30_ID_IDF':cnt['S30'],'of':m_['S30'],'ci95_S30':ci(cnt['S30'],m_['S30']),
         'C20_ID_IDF':cnt['C20'],'ci95_C20':ci(cnt['C20'],m_['C20']),'rule':f'S30 >= {min30(n)} of {n} and >= C20 - 1','label_source':lsrc},why=wb)
    low={a:{'decided':cnt[a],'of':m_[a],'C20_on_same_seeds':c20_on(a),'ci95':ci(cnt[a],m_[a]),'ok':cnt[a]>=c20_on(a)-1} for a in ('S10','S20')}
    gate('GN_low65',complete and all(v['ok'] for v in low.values()),low,why=wb)
    rd={}
    for a in ('S10','S20','S30'):
        rr=[c['arms'][a] for c in cs if a in c['arms']];R=sum(x.get('reads_total') or 0 for x in rr);F=sum(x.get('fixed_reads_total') or 0 for x in rr)
        rd[a]={'reads':R,'fixed_rule_reads':F,'ratio':(R/F if F else None),'ok':bool(F) and R<=READ_RATIO*F,'records':len(rr)}
    gate('GREAD65',complete and all(v['ok'] for v in rd.values()),{'per_arm':rd,'rule':f'reads <= {READ_RATIO} x fixed rule, each arm'},why=wb)
    det=[[c['seed'],canon65(c['arms']['S30'])==canon65(c['arms']['S30b']),c['arms']['S30']['label'],c['arms']['S30b']['label']] for c in cs if 'S30b' in c['arms']]
    kills=[[ckey(c),an,ar.get('guard_events')] for c in cs for an,ar in c['arms'].items() if ar.get('wall_guard')]
    ndt=sum(x[1] for x in det)
    gate('GDET65',complete and ndt==nb==len(det) and not kills,{'identical':ndt,'of':len(det),'wall_guard_firings':kills,'per_case':det,
         'columns':['seed','canon65_equal','S30','S30b']},why=wb)
    fi=(api or {}).get('fidelity') or {};eq=(api or {}).get('equiv') or {};th=(api or {}).get('threshold') or {};gh=(api or {}).get('ghost') or {}
    ndec=sum(dd(c,a) for c in cs for a in c['arms'] if a in NOISY)
    fi_ok=bool(fi) and fi.get('study_results_sha256')==rsha and fi.get('PASS') is True and fi.get('exact')==fi.get('decided_records')==ndec
    gate('GFID65',complete and fi_ok and eq.get('PASS') is True and th.get('PASS') is True,{'fidelity_exact':fi.get('exact'),'of_decided':fi.get('decided_records'),
         'decided_noisy_in_gates':ndec,'vacuous':fi.get('vacuous'),'bound':bool(fi) and fi.get('study_results_sha256')==rsha,
         'failures':{k:v for k,v in (fi.get('per_case') or {}).items() if not v.get('exact')},'equiv':{k:eq.get(k) for k in ('cases','identical','PASS')},
         'threshold':{k:th.get(k) for k in ('checked','disagreements','PASS')}},why=wb or (None if fi else 'INCOMPLETE_INPUT (API_CHECKS_065 fidelity missing)'))
    ct=sha(ROOT/'brute/api/certify20s.py');f65=(fz or {}).get('sha256_files',{}).get('brute/api/certify20s.py')
    abound=bool(api) and api.get('certify20s_sha256')==ct==f65
    gate('GHOST65',abound and gh.get('network_pass') is True,None if not api else {'bound_to_freeze_065':abound,'socket_attempts':gh.get('socket_attempts'),
         'no_network_run':gh.get('no_network_run'),'static_ok':gh.get('static_ok')},why=None if api else 'INCOMPLETE_INPUT (API_CHECKS_065 missing)')
    mt=(ref or {}).get('mutation_test') or {};rb=bool(ref) and ref.get('study_results_sha256')==rsha and ref.get('block')=='main'
    robs=None if not ref else {k:ref.get(k) for k in ('block','scope','records','decided','audited','not_audited','complete','per_arm','not_reached',
                               'k_spent_as_amb','verdicts_checked','mismatch_count','misfires','vacuous','PASS','elapsed_informational')}|{'mutations':mt.get('detected'),'of':mt.get('mutations')}
    sc_=(ref or {}).get('scope') or {}
    gate('GS_ref65',rb and ref.get('mismatch_count')==0 and ref.get('complete') is True and sc_.get('budget_s')==REF_BUDGET and sc_.get('workers')==REF_WORKERS
         and (ref.get('vacuous') is True or mt.get('detected')==mt.get('mutations')==20) and ref.get('PASS') is True,robs,
         why=wb or (None if ref else 'INCOMPLETE_INPUT (REFERENCE_065 missing)'))
    gate('G_recount65',complete and rc_ok,None if not rc else {k:rc.get(k) for k in ('cases','records','decided_by_arm','study_decided_by_arm','wrong','settled_bit_errors','mismatches','PASS')},
         why=wb or (None if rc else 'INCOMPLETE_INPUT (RECOUNT_065 missing)'))
    mods=(ts or {}).get('per_module') or {};gm=(ts or {}).get('gated_modules') or []
    gate('GTEST65',bool(gm) and ts.get('passed') is True and all(mods[x].get('returncode')==0 for x in gm),
         None if not ts else {'gated':{x:{'returncode':mods[x].get('returncode'),'tests':mods[x].get('tests')} for x in gm},
                              'reported':{x:{'returncode':v.get('returncode'),'tests':v.get('tests')} for x,v in mods.items() if x not in gm}},
         why=None if ts else 'INCOMPLETE_INPUT (TEST_SUITE_065 missing)')
    lt=ledger();ev=[e for e,_ in lt];times=[t for _,t in lt]
    proc={'order':subseq(ev,PROC_ORDER),'ledger_times_parse':bool(lt) and all(t is not None for t in times),
          'ledger_times_non_decreasing':all(a<=b for a,b in zip(times,times[1:]) if a and b),'commit_order_file':order is not None,'main_sealed':bool(sealed)}
    gate('G_PROC65',all(proc.values()),{'clauses':proc,'events':ev,'required_order':list(PROC_ORDER)})
    reads={a:[[c['seed'],c['arms'][a].get('observations'),c['arms'][a].get('reads_total'),c['arms'][a].get('fixed_reads_total'),c['arms'][a].get('reads_max'),
               (c['arms'][a].get('thresholds') or [None])[-1]] for c in cs if a in c['arms']] for a in NOISY}
    sec['READS65']={'pass':None,'observed':{'per_arm':rd,'per_record':reads,'columns':['seed','observations','reads','fixed_rule_reads','max_reads_one_obs','last_threshold']},'rule':'reported'}
    sec['MC65']={'pass':None,'observed':(api or {}).get('montecarlo'),'rule':'reported'}
    row=lambda c,a:[a,lab(c,a),c['arms'][a]['n_min'],len(c['arms'][a]['extra_acts']),c['arms'][a]['n_rounds'],c['arms'][a]['conflicts_spent']]
    sec['GSTATS65']={'pass':None,'observed':[[c['seed']]+[row(c,a) for a in c['arms']] for c in cs],
                     'columns':['seed','per arm [arm, label, n_min, extra_actions, rounds, conflicts]'],'rule':'reported'}
    cost={}
    for c in cs:
        for a,ar in c['arms'].items():
            x=cost.setdefault(a,{'records':0,'wall_s':0.0,'conflicts':0,'steps':0,'budget_spent':0,'wall_guard':0})
            x['records']+=1;x['wall_s']+=ar.get('case_wall_informational') or 0.0;x['conflicts']+=ar.get('conflicts_spent') or 0
            x['steps']+=len(ar.get('extra_acts') or []);x['budget_spent']+=(ar.get('conflicts_spent') or 0)>=ar['budget_conflicts'];x['wall_guard']+=bool(ar.get('wall_guard'))
    for x in cost.values():x['wall_s']=round(x['wall_s'],1)
    sec['GCOST65']={'pass':None,'observed':cost,'elapsed_s':(res or {}).get('total_elapsed_informational'),'rule':'reported (walls informational)'}
    sc_frozen=bool(sc) and (fz or {}).get('sha256_files',{}).get('results/diag-065/SEEDCHECK_065.json')==sha(ROOT/'results/diag-065/SEEDCHECK_065.json')
    sec['SEEDCHECK65']={'pass':None,'observed':None if not sc else {'seedcheck_pass':sc.get('PASS'),'frozen_in_065':sc_frozen}}
    fl={}
    for a in ARMS:
        cc=[c for c in cs if a in c['arms']];fl[a]={L:{'x':sum(lab(c,a)==L for c in cc),'n':len(cc),'ci95':ci(sum(lab(c,a)==L for c in cc),len(cc))} for L in LABELS}
    ok=all(g['pass'] for g in Gt.values())
    c20ok=not ok and all(g['pass'] for k,g in Gt.items() if k not in SOFT)
    failed=[k for k,g in Gt.items() if g['pass'] is False]
    return {'schema':'brute.gates.v62_0','study':(res or {}).get('plan',{}).get('study'),'process':'lean',
            'sealed_input_verified':sealed,'label_source':lsrc,'n_seeds':n,'n_s20':n20,'n_s10':n10,'n_s30b':nb,'caps':(res or {}).get('caps'),
            'workers':(res or {}).get('workers'),'stop':(res or {}).get('stop'),'arm_noise':(res or {}).get('arm_noise'),'node_cap':(res or {}).get('node_cap'),
            'gates':Gt,'secondary':sec,'all_gated_pass':ok,'failed':failed,'not_exercised':[],
            'certified_readbits2_N20_eps030_seq':ok,'certified_readbits2_N20_eps020_seq':ok or c20ok,'status_phrase':status_phrase(ok,c20ok,failed),
            'framing':'NOISE TEST: the v0.60.0 clique-anchored method (certify/20p) behind a new sequential per-bit re-read front end (certify/20s) on 2-bit 20-state worlds at eps 0.10 / 0.20 / 0.30',
            'claim':('certify/20s ID/IDF is exact conditional on every settled reading being correct and on true size <= 20; under iid bit flips with eps <= eps_bar and '
                     'state-preserving re-reads every settled reading is correct with probability >= 1 - delta (0.001) over the whole trace. IDF identifies the machine from '
                     'the current state, not the start. Inferred reason the size condition is needed: a larger machine can copy the true machine on every visited state'),
            'reports':{'labels':fl} if cs else {}}


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--study-dir',default=str(STUDY_DIR));ap.add_argument('--check',action='store_true');a=ap.parse_args()
    obj=build(Path(a.study_dir));out=Path(a.study_dir)/'GATES_065.json'
    if a.check:check(out.read_bytes()==dumps(obj),'GATES_065.json does not reproduce');print('GATES_065 reproduces')
    else:write_new(out,obj);print(json.dumps({k:v['pass'] for k,v in obj['gates'].items()}),obj['failed'])
