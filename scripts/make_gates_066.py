"""Gates for study-066 (BRUTE_PLAN_066 criteria; the pre-run deviation #206 fixes the definitions), LEAN process. Committed in the
source freeze before main_run_066; nothing is tuned after results are seen. New file; built from scripts/make_gates_065.py (frozen).
HONEST FRAMING (plan honest_framing): noise AND size together: the certify/20s sequential re-read front end at eps 0.30 on 2-bit
20-state worlds (on certify/20p) and on 2-bit 24-state worlds (new certify/32s on certify/32p), with a runner-level per-job kill.
Inputs (D = results/study-066): D/main/{RESULTS,SCIENTIFIC,SEAL}.json, D/main/RECOUNT_066.json, D/main/REFERENCE_066.json,
D/API_CHECKS_066.json, D/TEST_SUITE_066.json, results/diag-066/SEEDCHECK_066.json, experiments/COMMIT_ORDER_066.json,
results/RESEARCH_LEDGER.jsonl. A main block with a missing job (sealed partial) or not matching its seal => GLIVE66 and every data
gate FAIL INCOMPLETE_INPUT. A KILL record (runner SIGKILL at 600 s) is a complete, undecided outcome. Records are accepted only if
sha256(RESULTS) equals the seal and no_time(RESULTS) equals SCIENTIFIC. Labels: recounted if G_recount66 passes, else the study's.
Arms: C20, S30 (n20 scale20 seeds), S30b (first n_s30b), C24, S24 (n24 scale24 seeds). Decided = ID or IDF; finished = not KILL.
  GS66_sound: WRONG 0 on every finished record;
  GLIVE66: main sealed complete, every job has a record (finished or KILL) and total elapsed < MAIN_CAP_S 2400 s;
  GMAJ66: 0 settled-bit errors over every observation of every finished noisy record (recounted numbers if G_recount66 passes);
  GEQ66: canon_inner(noisy) == canon_inner(control) on every seed where both finished (S30, S30b vs C20; S24 vs C24); at least 4
     S30/C20 pairs and at least 2 S24/C24 pairs;
  GN66 (headline): S30 decided >= 3 of 6 and >= C20 decided - 1; Wilson 95% CI;
  GN24_66: S24 decided >= C24 decided - 1 and >= 1;
  GREAD66: in each of S30 and S24 (finished records): sum reads_total <= 0.35 x sum fixed_reads_total;
  GDET66: canon66(S30) == canon66(S30b) on every S30b seed, both finished (wall-guard firings reported);
  GFID66: API_CHECKS_066 fidelity exact on every decided noisy record (bound to the sealed RESULTS sha), equiv PASS (certify/32s at
     eps_bar 0 == certify/32p), equiv20 PASS (certify/32s at N 20 == certify/20s) and threshold PASS;
  GHOST66: API_CHECKS_066 ghost: the no-network run made 0 socket attempts and certify32s.py's sha equals its freeze sha;
  GS_ref66: REFERENCE_066 on block main: sha bound, 0 mismatches, complete within 1800 s on 6 workers, 20/20 mutations;
  G_recount66: RECOUNT_066 bound and PASS; GTEST66: gated modules of TEST_SUITE_066 pass;
  G_PROC66: preregistration_066 .. main_run_066 as a subsequence, parseable non-decreasing note times, commit-order file, main sealed.
  Certification (plan certification_rule): every gate passes -> PHRASE24; every gate except GN24_66 -> PHRASE20; otherwise none.
  Secondary (reported): KILLS66, READS66, MC66, GCOST66, GSTATS66, SEEDCHECK66.
  PYTHONPATH=. python scripts/make_gates_066.py [--study-dir D] [--check]"""
from __future__ import annotations
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common import load,dumps,write_new,check,sha
from experiments.brute_common_026 import wilson
from scripts.make_gates_034 import opt
from scripts.make_gates_043 import subseq

STUDY_DIR=ROOT/'results/study-066';ARMS=('C20','S30','S30b','C24','S24');NOISY=('S30','S30b','S24')
CONTROL={'S30':'C20','S30b':'C20','S24':'C24'};MAIN_CAP_S=2400.0;JOBS=21
LABELS=('ID','IDF','AMB','WRONG','IDU','NOFIT','KILL');SOFT=('GN24_66',);HARD=('GS66_sound','GMAJ66','GEQ66','GS_ref66','GLIVE66');REF_BUDGET=1800.0;REF_WORKERS=6
READ_RATIO=0.35;min30=lambda n:-(-3*n//6)
PROC_ORDER=('preregistration_066','build_authorization_066','seedcheck_066','prefreeze_smoke_066','deviation_206','freeze_066','main_run_066')
PHRASE24='certified (read_bits 2, N <= 24, iid bit noise eps <= 0.30, delta 0.001, sequential re-reads)'
PHRASE20='certified (read_bits 2, N <= 20, iid bit noise eps <= 0.30, delta 0.001, sequential re-reads)'


def ckey(c):return f"{c['block']}/{c['key']}/{c['seed']}"


def ledger():
    from datetime import datetime
    L=[json.loads(x) for x in (ROOT/'results/RESEARCH_LEDGER.jsonl').read_text().splitlines() if x.strip()]
    i0=next((i for i,e in enumerate(L) if e.get('event')=='preregistration_066'),None);out=[]
    for e in (L[i0:] if i0 is not None else []):
        try:t=datetime.fromisoformat(str(e.get('note',''))[:25])
        except ValueError:t=None
        out.append((e['event'],t))
        if e['event']==PROC_ORDER[-1]:break
    return out


def status_phrase(c24,c20,failed):
    if c24:return PHRASE24
    if c20:return PHRASE20+'; noise at 24 states stays Open'
    return 'not certified, no certification status (failing gates: '+', '.join(failed)+')'


def build(study=STUDY_DIR,expect=None):
    from brute.evaluation import no_time
    from experiments.brute_study_066 import canon66,canon_inner,N20,N24,N_S30B
    study=Path(study);D=study/'main';Gt={};sec={}
    seal=opt(D/'SEAL.json');sci=opt(D/'SCIENTIFIC.json');res=opt(D/'RESULTS.json');rc=opt(D/'RECOUNT_066.json')
    ref=opt(D/'REFERENCE_066.json');ts=opt(study/'TEST_SUITE_066.json');order=opt(ROOT/'experiments/COMMIT_ORDER_066.json')
    api=opt(study/'API_CHECKS_066.json');fz=opt(ROOT/'experiments/BRUTE_SOURCE_FREEZE_066.json')
    sc=opt(ROOT/'results/diag-066/SEEDCHECK_066.json')
    rsha=sha(D/'RESULTS.json') if (D/'RESULTS.json').exists() else None
    sealed=(bool(seal) and res is not None and sci is not None and rsha==seal.get('results_sha256')
            and sha(D/'SCIENTIFIC.json')==seal.get('scientific_sha256') and no_time(res)==sci)
    if expect is not None:n20,n24,nb=expect
    else:r_=res or {};n20=int(r_.get('n20',N20));n24=int(r_.get('n24',N24));nb=int(r_.get('n_s30b',N_S30B))
    njobs=2*n20+2*n24+nb
    main=[c for c in (res or {}).get('cases',[]) if c['block']=='main'] if sealed else []
    cs20=sorted([c for c in main if c['key']=='scale20'],key=lambda c:c['seed']);cs24=sorted([c for c in main if c['key']=='scale24'],key=lambda c:c['seed'])
    cs=cs20+cs24
    arms_ok=(all(sorted(c['arms'])==sorted(['C20','S30']+(['S30b'] if i<nb else [])) for i,c in enumerate(cs20))
             and all(sorted(c['arms'])==['C24','S24'] for c in cs24))
    nrec=sum(len(c['arms']) for c in cs)
    complete=(sealed and seal.get('complete') is True and len(cs20)==n20 and len(cs24)==n24 and len(cs)==len(main) and arms_ok
              and nrec==njobs and len((res or {}).get('job_keys') or [])==njobs)
    wb=None if complete else 'INCOMPLETE_INPUT (main missing, partial, missing arms or not matching its seal)'
    def gate(name,ok,obs,why=None):Gt[name]={'pass':bool(ok) and why is None,'observed':obs,**({'reason':why} if why else {})}
    pc=(rc or {}).get('per_case') or {}
    rc_bound=bool(rc) and rc.get('results_sha256')==rsha and rc.get('cases')==len((res or {}).get('cases',[]))
    rc_ok=rc_bound and rc.get('PASS') is True and not rc.get('mismatches')
    rget=lambda c,a,f:((pc.get(f"{c['key']}:{c['seed']}") or {}).get(a) or {}).get(f)
    lab=(lambda c,a:rget(c,a,'label')) if rc_ok else (lambda c,a:c['arms'][a]['label'])
    lsrc='recount' if rc_ok else 'study labels (G_recount66 did not pass)'
    dd=lambda c,a:a in c['arms'] and lab(c,a) in ('ID','IDF')
    fin=lambda c,a:a in c['arms'] and c['arms'][a]['label']!='KILL' and c['arms'][a]['stop']!='KILL'
    ci=lambda x,m:wilson(x,m) if m else None
    kills=[[ckey(c),a] for c in cs for a in c['arms'] if not fin(c,a)]
    wrong=[[ckey(c),a] for c in cs for a in c['arms'] if fin(c,a) and (lab(c,a)=='WRONG' or c['arms'][a]['label']=='WRONG')]
    gate('GS66_sound',complete and not wrong,{'WRONG':wrong,'records':nrec,'finished':nrec-len(kills),'KILL':kills,
         'per_case':[[c['key'],c['seed']]+[lab(c,a) if a in c['arms'] else None for a in ARMS] for c in cs],'columns':['key','seed']+list(ARMS),'label_source':lsrc},why=wb)
    el=(res or {}).get('total_elapsed_informational')
    gate('GLIVE66',complete and isinstance(el,(int,float)) and el<MAIN_CAP_S,{'sealed_complete':bool(sealed and (seal or {}).get('complete') is True),
         'records':nrec,'jobs':njobs,'killed':len(kills),'total_elapsed_s':el,'cap_s':MAIN_CAP_S,
         'missing_job_keys':(seal or {}).get('missing_job_keys')},why=None if complete else 'INCOMPLETE_INPUT (sealed partial or missing jobs)')
    sbe=lambda c,a:(rget(c,a,'settled_bit_errors') if rc_ok else c['arms'][a].get('settled_bit_errors'))
    errs=[[ckey(c),a,sbe(c,a)] for c in cs for a in c['arms'] if a in NOISY and fin(c,a)]
    nobs=sum(c['arms'][a].get('observations') or 0 for c in cs for a in c['arms'] if a in NOISY and fin(c,a))
    gate('GMAJ66',complete and all(e[2]==0 for e in errs),{'settled_bit_errors_total':sum((e[2] or 0) for e in errs),'finished_noisy_records':len(errs),
         'noisy_observations':nobs,'nonzero':[e for e in errs if e[2]],'source':lsrc},why=wb)
    eqr=[[c['key'],c['seed'],a,canon_inner(c['arms'][a])==canon_inner(c['arms'][CONTROL[a]])] for c in cs for a in c['arms']
         if a in NOISY and fin(c,a) and fin(c,CONTROL[a])]
    p20=sum(1 for x in eqr if x[2]=='S30');p24=sum(1 for x in eqr if x[2]=='S24')
    gate('GEQ66',complete and all(x[3] for x in eqr) and p20>=4 and p24>=2,{'equal':sum(x[3] for x in eqr),'of':len(eqr),'pairs_S30_C20':p20,'pairs_S24_C24':p24,
         'rule':'all equal; >= 4 S30/C20 pairs and >= 2 S24/C24 pairs','per_record':eqr,'columns':['key','seed','arm','inner_equal_control']},why=wb)
    cnt={a:sum(dd(c,a) for c in cs) for a in ARMS};m_={a:sum(a in c['arms'] for c in cs) for a in ARMS}
    gate('GN66',complete and cnt['S30']>=min30(n20) and cnt['S30']>=cnt['C20']-1,{'S30_ID_IDF':cnt['S30'],'of':m_['S30'],'ci95_S30':ci(cnt['S30'],m_['S30']),
         'C20_ID_IDF':cnt['C20'],'ci95_C20':ci(cnt['C20'],m_['C20']),'rule':f'S30 >= {min30(n20)} of {n20} and >= C20 - 1','label_source':lsrc},why=wb)
    gate('GN24_66',complete and cnt['S24']>=cnt['C24']-1 and cnt['S24']>=1,{'S24_ID_IDF':cnt['S24'],'of':m_['S24'],'ci95_S24':ci(cnt['S24'],m_['S24']),
         'C24_ID_IDF':cnt['C24'],'ci95_C24':ci(cnt['C24'],m_['C24']),'rule':'S24 >= C24 - 1 and >= 1','label_source':lsrc},why=wb)
    rd={}
    for a in ('S30','S24'):
        rr=[c['arms'][a] for c in cs if fin(c,a)];R=sum(x.get('reads_total') or 0 for x in rr);F=sum(x.get('fixed_reads_total') or 0 for x in rr)
        rd[a]={'reads':R,'fixed_rule_reads':F,'ratio':(R/F if F else None),'ok':bool(F) and R<=READ_RATIO*F,'finished_records':len(rr)}
    gate('GREAD66',complete and all(v['ok'] for v in rd.values()),{'per_arm':rd,'rule':f'reads <= {READ_RATIO} x fixed rule, S30 and S24'},why=wb)
    det=[[c['seed'],fin(c,'S30') and fin(c,'S30b') and canon66(c['arms']['S30'])==canon66(c['arms']['S30b']),c['arms']['S30']['label'],c['arms']['S30b']['label']]
         for c in cs20 if 'S30b' in c['arms']]
    guards=[[ckey(c),an,ar.get('guard_events')] for c in cs for an,ar in c['arms'].items() if ar.get('wall_guard')]
    ndt=sum(bool(x[1]) for x in det)
    gate('GDET66',complete and ndt==nb==len(det),{'identical':ndt,'of':len(det),'wall_guard_firings_reported':guards,'per_case':det,
         'columns':['seed','canon66_equal_both_finished','S30','S30b']},why=wb)
    fi=(api or {}).get('fidelity') or {};eq=(api or {}).get('equiv') or {};e20=(api or {}).get('equiv20') or {};th=(api or {}).get('threshold') or {};gh=(api or {}).get('ghost') or {}
    ndec=sum(dd(c,a) for c in cs for a in c['arms'] if a in NOISY)
    fi_ok=bool(fi) and fi.get('study_results_sha256')==rsha and fi.get('PASS') is True and fi.get('exact')==fi.get('decided_records')==ndec
    gate('GFID66',complete and fi_ok and eq.get('PASS') is True and e20.get('PASS') is True and th.get('PASS') is True,{'fidelity_exact':fi.get('exact'),'of_decided':fi.get('decided_records'),
         'decided_noisy_in_gates':ndec,'vacuous':fi.get('vacuous'),'bound':bool(fi) and fi.get('study_results_sha256')==rsha,
         'failures':{k:v for k,v in (fi.get('per_case') or {}).items() if not v.get('exact')},'equiv':{k:eq.get(k) for k in ('cases','identical','PASS')},
         'equiv20':e20,'threshold':{k:th.get(k) for k in ('checked','disagreements','PASS')}},why=wb or (None if fi else 'INCOMPLETE_INPUT (API_CHECKS_066 fidelity missing)'))
    ct=sha(ROOT/'brute/api/certify32s.py');f66=(fz or {}).get('sha256_files',{}).get('brute/api/certify32s.py')
    abound=bool(api) and api.get('certify32s_sha256')==ct==f66
    gate('GHOST66',abound and gh.get('network_pass') is True,None if not api else {'bound_to_freeze_066':abound,'socket_attempts':gh.get('socket_attempts'),
         'no_network_run':gh.get('no_network_run'),'static_ok':gh.get('static_ok')},why=None if api else 'INCOMPLETE_INPUT (API_CHECKS_066 missing)')
    mt=(ref or {}).get('mutation_test') or {};rb=bool(ref) and ref.get('study_results_sha256')==rsha and ref.get('block')=='main'
    robs=None if not ref else {k:ref.get(k) for k in ('block','scope','records','decided','audited','not_audited','complete','per_arm','per_key','not_reached',
                               'k_spent_as_amb','verdicts_checked','mismatch_count','misfires','vacuous','PASS','elapsed_informational')}|{'mutations':mt.get('detected'),'of':mt.get('mutations')}
    sc_=(ref or {}).get('scope') or {}
    gate('GS_ref66',rb and ref.get('mismatch_count')==0 and ref.get('complete') is True and sc_.get('budget_s')==REF_BUDGET and sc_.get('workers')==REF_WORKERS
         and (ref.get('vacuous') is True or mt.get('detected')==mt.get('mutations')==20) and ref.get('PASS') is True,robs,
         why=wb or (None if ref else 'INCOMPLETE_INPUT (REFERENCE_066 missing)'))
    gate('G_recount66',complete and rc_ok,None if not rc else {k:rc.get(k) for k in ('cases','records','decided_by_arm','study_decided_by_arm','wrong','killed','settled_bit_errors','mismatches','PASS')},
         why=wb or (None if rc else 'INCOMPLETE_INPUT (RECOUNT_066 missing)'))
    mods=(ts or {}).get('per_module') or {};gm=(ts or {}).get('gated_modules') or []
    gate('GTEST66',bool(gm) and ts.get('passed') is True and all(mods[x].get('returncode')==0 for x in gm),
         None if not ts else {'gated':{x:{'returncode':mods[x].get('returncode'),'tests':mods[x].get('tests')} for x in gm},
                              'reported':{x:{'returncode':v.get('returncode'),'tests':v.get('tests')} for x,v in mods.items() if x not in gm}},
         why=None if ts else 'INCOMPLETE_INPUT (TEST_SUITE_066 missing)')
    lt=ledger();ev=[e for e,_ in lt];times=[t for _,t in lt]
    proc={'order':subseq(ev,PROC_ORDER),'ledger_times_parse':bool(lt) and all(t is not None for t in times),
          'ledger_times_non_decreasing':all(a<=b for a,b in zip(times,times[1:]) if a and b),'commit_order_file':order is not None,'main_sealed':bool(sealed)}
    gate('G_PROC66',all(proc.values()),{'clauses':proc,'events':ev,'required_order':list(PROC_ORDER)})
    sec['KILLS66']={'pass':None,'observed':{'killed':kills,'by_arm':{a:sum(1 for k in kills if k[1]==a) for a in ARMS},
                    'kill_walls':[[ckey(c),a,c['arms'][a].get('kill_wall_informational')] for c in cs for a in c['arms'] if not fin(c,a)]},'rule':'reported'}
    reads={a:[[c['seed'],c['arms'][a].get('observations'),c['arms'][a].get('reads_total'),c['arms'][a].get('fixed_reads_total'),c['arms'][a].get('reads_max'),
               (c['arms'][a].get('thresholds') or [None])[-1]] for c in cs if fin(c,a)] for a in NOISY}
    sec['READS66']={'pass':None,'observed':{'per_arm':rd,'per_record':reads,'columns':['seed','observations','reads','fixed_rule_reads','max_reads_one_obs','last_threshold']},'rule':'reported'}
    sec['MC66']={'pass':None,'observed':(api or {}).get('montecarlo'),'rule':'reported'}
    row=lambda c,a:[a,lab(c,a),c['arms'][a]['n_min'],len(c['arms'][a].get('extra_acts') or []),c['arms'][a].get('n_rounds'),c['arms'][a]['conflicts_spent']]
    sec['GSTATS66']={'pass':None,'observed':[[c['key'],c['seed']]+[row(c,a) for a in c['arms']] for c in cs],
                     'columns':['key','seed','per arm [arm, label, n_min, extra_actions, rounds, conflicts]'],'rule':'reported'}
    cost={}
    for c in cs:
        for a,ar in c['arms'].items():
            x=cost.setdefault(a,{'records':0,'killed':0,'wall_s':0.0,'conflicts':0,'steps':0,'budget_spent':0,'wall_guard':0})
            x['records']+=1;x['killed']+=not fin(c,a)
            x['wall_s']+=ar.get('case_wall_informational') or ar.get('kill_wall_informational') or 0.0;x['conflicts']+=ar.get('conflicts_spent') or 0
            x['steps']+=len(ar.get('extra_acts') or []);x['budget_spent']+=(ar.get('conflicts_spent') or 0)>=(ar.get('budget_conflicts') or 8000000);x['wall_guard']+=bool(ar.get('wall_guard'))
    for x in cost.values():x['wall_s']=round(x['wall_s'],1)
    sec['GCOST66']={'pass':None,'observed':cost,'elapsed_s':el,'rule':'reported (walls informational)'}
    sc_frozen=bool(sc) and (fz or {}).get('sha256_files',{}).get('results/diag-066/SEEDCHECK_066.json')==sha(ROOT/'results/diag-066/SEEDCHECK_066.json')
    sec['SEEDCHECK66']={'pass':None,'observed':None if not sc else {'seedcheck_pass':sc.get('PASS'),'frozen_in_066':sc_frozen}}
    fl={}
    for a in ARMS:
        cc=[c for c in cs if a in c['arms']];fl[a]={L:{'x':sum(lab(c,a)==L for c in cc),'n':len(cc),'ci95':ci(sum(lab(c,a)==L for c in cc),len(cc))} for L in LABELS}
    ok=all(g['pass'] for g in Gt.values())
    c20ok=not ok and all(g['pass'] for k,g in Gt.items() if k not in SOFT)
    failed=[k for k,g in Gt.items() if g['pass'] is False]
    return {'schema':'brute.gates.v63_0','study':(res or {}).get('plan',{}).get('study'),'process':'lean',
            'sealed_input_verified':sealed,'label_source':lsrc,'n20':n20,'n24':n24,'n_s30b':nb,'caps':(res or {}).get('caps'),
            'workers':(res or {}).get('workers'),'stop':(res or {}).get('stop'),'arm_noise':(res or {}).get('arm_noise'),'node_cap':(res or {}).get('node_cap'),
            'gates':Gt,'secondary':sec,'all_gated_pass':ok,'failed':failed,'not_exercised':[],
            'certified_readbits2_N24_eps030_seq':ok,'certified_readbits2_N20_eps030_seq':ok or c20ok,'status_phrase':status_phrase(ok,c20ok,failed),
            'framing':'NOISE x SIZE TEST: the sequential per-bit re-read front end at eps 0.30 on 2-bit 20-state worlds (certify/20s on certify/20p) and 24-state worlds (certify/32s on certify/32p), with a 600 s per-job process kill',
            'claim':('certify/20s and certify/32s ID/IDF are exact conditional on every settled reading being correct and on true size <= the declared bound (20 or 24); under iid bit flips with eps <= eps_bar and '
                     'state-preserving re-reads every settled reading is correct with probability >= 1 - delta (0.001) over the whole trace. IDF identifies the machine from '
                     'the current state, not the start. Inferred reason the size condition is needed: a larger machine can copy the true machine on every visited state'),
            'reports':{'labels':fl} if cs else {}}


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--study-dir',default=str(STUDY_DIR));ap.add_argument('--check',action='store_true');a=ap.parse_args()
    obj=build(Path(a.study_dir));out=Path(a.study_dir)/'GATES_066.json'
    if a.check:check(out.read_bytes()==dumps(obj),'GATES_066.json does not reproduce');print('GATES_066 reproduces')
    else:write_new(out,obj);print(json.dumps({k:v['pass'] for k,v in obj['gates'].items()}),obj['failed'])
