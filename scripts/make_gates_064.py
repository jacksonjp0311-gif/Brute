"""Gates for study-064 (BRUTE_PLAN_064 criteria; the pre-run deviation fixes the definitions), LEAN process. Committed in the
source freeze before main_run_064; nothing is tuned after results are seen. New file; built from scripts/make_gates_063.py (frozen).
HONEST FRAMING (plan honest_framing): a SIZE test of the v0.60.0 method (certify/32p = certify/20p with the declared bound raised to
24, no other change) on 2-bit 24-state worlds, plus a replication of certify/20p at 20 states with an audit that can finish.
Inputs (D = results/study-064): D/main/{RESULTS,SCIENTIFIC,SEAL}.json, D/main/RECOUNT_064.json, D/main/REFERENCE_064.json,
D/API_CHECKS_064.json, D/TEST_SUITE_064.json, results/diag-064/SEEDCHECK_064.json, experiments/COMMIT_ORDER_064.json,
results/RESEARCH_LEDGER.jsonl. Missing or partial input => every data gate FAIL INCOMPLETE_INPUT. Records are accepted only if
sha256(RESULTS) equals the seal and no_time(RESULTS) equals SCIENTIFIC. Labels: recounted if G_recount64 passes, else the study's.
Arms: P24 (certify/32p, N 24, scale24), B24 (frozen certify/32b, N 24, first n_b24 scale24 seeds; reported), P20 (frozen
certify/20p, N 20, scale20), P20b (P20 on the first n_p20b scale20 seeds). n = n_seeds per size.
  GS64_sound: WRONG 0 on every record;
  GP24_64 (headline): P24 ID+IDF >= ceil(2 n / 6) (plan 2 of 6); Wilson 95% CI; B24 on its seeds reported with exact McNemar p;
  GP20_64: P20 ID+IDF >= ceil(3 n / 6) (plan 3 of 6); Wilson 95% CI;
  GDET64: canon64(P20) == canon64(P20b) on every P20b seed and 0 wall-guard firings in P24, P20, P20b (B24 firings reported);
  GFID64: API_CHECKS_064 equiv PASS (certify/32p == certify/20p at bound <= 20 incl. the smoke world; sound at bound n+5; bounds),
     the no-network run and replay fidelity exact on every decided record, bound to the sealed RESULTS sha;
  GXREF64: API_CHECKS_064 xref PASS (pinned reference == frozen plain reference on 150 small traces and the 2 study-063 records);
  GHOST64: API_CHECKS_064 ghost PASS64 with certify32p.py's sha equal to its sha in BRUTE_SOURCE_FREEZE_064;
  GS_ref64: REFERENCE_064 on block main: sha bound, 0 mismatches, complete within 1800 s on 6 workers, 20/20 mutations (vacuous only
     if nothing is decided);
  G_recount64: RECOUNT_064 bound and PASS; GTEST64: gated modules of TEST_SUITE_064 pass;
  G_PROC64: preregistration_064, build_authorization_064, seedcheck_064, prefreeze_smoke_064, deviation_202, freeze_064,
     main_run_064 as a subsequence, parseable non-decreasing note times, commit-order file, main sealed;
  G_RT: verify_release_0610 at release (not gated here).
  certified_readbits2_N24_clique: every gate passes; certified_readbits2_N20_clique: every gate except GP24_64 passes.
  status_phrase: 'certified (read_bits 2, N <= 24, clique-anchored)' / 'certified (read_bits 2, N <= 20, clique-anchored); 24 states
  at 2 bits stay Open' / 'not certified, no certification status (failing gates: ...)'.
  Secondary (reported): CLIQUE64, GCOST64, GSTATS64, B24_64, SEEDCHECK64, PROBE64.
  PYTHONPATH=. python scripts/make_gates_064.py [--study-dir D] [--check]"""
from __future__ import annotations
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common import load,dumps,write_new,check,sha
from experiments.brute_common_026 import wilson
from scripts.make_gates_034 import opt
from scripts.make_gates_043 import subseq
from scripts.make_gates_063 import mcnemar_exact

STUDY_DIR=ROOT/'results/study-064';ARMS=('P24','B24','P20','P20b')
LABELS=('ID','IDF','AMB','WRONG','IDU','NOFIT');SOFT=('GP24_64',);REF_BUDGET=1800.0;REF_WORKERS=6
min24=lambda n:-(-2*n//6);min20=lambda n:-(-3*n//6)
PROC_ORDER=('preregistration_064','build_authorization_064','seedcheck_064','prefreeze_smoke_064','deviation_202','freeze_064','main_run_064')


def ckey(c):return f"{c['block']}/{c['key']}/{c['seed']}"


def ledger():
    from datetime import datetime
    L=[json.loads(x) for x in (ROOT/'results/RESEARCH_LEDGER.jsonl').read_text().splitlines() if x.strip()]
    i0=next((i for i,e in enumerate(L) if e.get('event')=='preregistration_064'),None);out=[]
    for e in (L[i0:] if i0 is not None else []):
        try:t=datetime.fromisoformat(str(e.get('note',''))[:25])
        except ValueError:t=None
        out.append((e['event'],t))
        if e['event']==PROC_ORDER[-1]:break
    return out


def status_phrase(c24,c20,failed):
    if c24:return 'certified (read_bits 2, N <= 24, clique-anchored)'
    if c20:return 'certified (read_bits 2, N <= 20, clique-anchored); 24 states at 2 bits stay Open'
    return 'not certified, no certification status (failing gates: '+', '.join(failed)+')'


def build(study=STUDY_DIR,expect=None):
    from brute.evaluation import no_time
    from experiments.brute_study_064 import canon64,N_SEEDS,N_B24,N_P20B
    study=Path(study);D=study/'main';Gt={};sec={}
    seal=opt(D/'SEAL.json');sci=opt(D/'SCIENTIFIC.json');res=opt(D/'RESULTS.json');rc=opt(D/'RECOUNT_064.json')
    ref=opt(D/'REFERENCE_064.json');ts=opt(study/'TEST_SUITE_064.json');order=opt(ROOT/'experiments/COMMIT_ORDER_064.json')
    api=opt(study/'API_CHECKS_064.json');fz=opt(ROOT/'experiments/BRUTE_SOURCE_FREEZE_064.json')
    sc=opt(ROOT/'results/diag-064/SEEDCHECK_064.json')
    rsha=sha(D/'RESULTS.json') if (D/'RESULTS.json').exists() else None
    sealed=(bool(seal) and res is not None and sci is not None and rsha==seal.get('results_sha256')
            and sha(D/'SCIENTIFIC.json')==seal.get('scientific_sha256') and no_time(res)==sci)
    if expect is not None:n,nb24,nb20=expect
    else:n=int((res or {}).get('n_seeds',N_SEEDS));nb24=int((res or {}).get('n_b24',N_B24));nb20=int((res or {}).get('n_p20b',N_P20B))
    main=[c for c in (res or {}).get('cases',[]) if c['block']=='main'] if sealed else []
    c24=sorted([c for c in main if c['key']=='scale24p'],key=lambda c:c['seed']);c20=sorted([c for c in main if c['key']=='scale20p'],key=lambda c:c['seed'])
    s24={c['seed'] for c in c24[:nb24]};s20={c['seed'] for c in c20[:nb20]}
    arms_ok=(all(sorted(c['arms'])==sorted(('P24','B24') if c['seed'] in s24 else ('P24',)) for c in c24)
             and all(sorted(c['arms'])==sorted(('P20','P20b') if c['seed'] in s20 else ('P20',)) for c in c20))
    complete=(sealed and seal.get('complete') is True and len(c24)==len(c20)==n and len(main)==2*n and arms_ok
              and sum('B24' in c['arms'] for c in c24)==nb24 and sum('P20b' in c['arms'] for c in c20)==nb20)
    cs=c24+c20
    wb=None if complete else 'INCOMPLETE_INPUT (main missing, partial, missing arms or not matching its seal)'
    def gate(name,ok,obs,why=None):Gt[name]={'pass':bool(ok) and why is None,'observed':obs,**({'reason':why} if why else {})}
    pc=(rc or {}).get('per_case') or {}
    rc_bound=bool(rc) and rc.get('results_sha256')==rsha and rc.get('cases')==len((res or {}).get('cases',[]))
    rc_ok=rc_bound and rc.get('PASS') is True and not rc.get('mismatches')
    rget=lambda c,a,f:((pc.get(str(c['seed'])) or {}).get(a) or {}).get(f)
    lab=(lambda c,a:rget(c,a,'label')) if rc_ok else (lambda c,a:c['arms'][a]['label'])
    lsrc='recount' if rc_ok else 'study labels (G_recount64 did not pass)'
    dd=lambda c,a:a in c['arms'] and lab(c,a) in ('ID','IDF')
    ci=lambda x,m:wilson(x,m) if m else None
    wrong=[[ckey(c),a] for c in cs for a in c['arms'] if lab(c,a)=='WRONG' or c['arms'][a]['label']=='WRONG']
    gate('GS64_sound',complete and not wrong,{'WRONG':wrong,'records':sum(len(c['arms']) for c in cs),
         'per_case':[[c['key'],c['seed']]+[lab(c,a) if a in c['arms'] else None for a in ARMS] for c in cs],'columns':['key','seed']+list(ARMS),
         'label_source':lsrc},why=wb)
    x24=sum(dd(c,'P24') for c in c24);m24=len(c24)
    cb=[c for c in c24 if 'B24' in c['arms']];xb=sum(dd(c,'B24') for c in cb);xpb=sum(dd(c,'P24') for c in cb)
    b_=sum(dd(c,'P24') and not dd(c,'B24') for c in cb);c_=sum(dd(c,'B24') and not dd(c,'P24') for c in cb)
    gate('GP24_64',complete and x24>=min24(n),{'P24_ID_IDF':x24,'of':m24,'ci95_P24':ci(x24,m24),'rule':f'P24 ID+IDF >= {min24(n)} of {n} (plan 2 of 6)',
         'B24_reported':{'B24_ID_IDF':xb,'P24_on_same_seeds':xpb,'of':len(cb),'discordant_P24_only':b_,'discordant_B24_only':c_,
                         'mcnemar_exact_p':mcnemar_exact(b_,c_),'note':'time-capped control (1800 s case kill), not gated'},'label_source':lsrc},why=wb)
    x20=sum(dd(c,'P20') for c in c20);m20=len(c20)
    gate('GP20_64',complete and x20>=min20(n),{'P20_ID_IDF':x20,'of':m20,'ci95_P20':ci(x20,m20),'rule':f'P20 ID+IDF >= {min20(n)} of {n} (plan 3 of 6)',
         'P20b_ID_IDF_reported':sum(dd(c,'P20b') for c in c20),'label_source':lsrc},why=wb)
    det=[[c['seed'],canon64(c['arms']['P20'])==canon64(c['arms']['P20b']),c['arms']['P20']['label'],c['arms']['P20b']['label']] for c in c20 if 'P20b' in c['arms']]
    kills=[[ckey(c),an,ar.get('guard_events')] for c in cs for an,ar in c['arms'].items() if an!='B24' and ar.get('wall_guard')]
    killsB=[[ckey(c),'B24',c['arms']['B24'].get('guard_events')] for c in cb if c['arms']['B24'].get('wall_guard')]
    ndt=sum(x[1] for x in det)
    gate('GDET64',complete and ndt==nb20 and len(det)==nb20 and not kills,{'identical':ndt,'of':len(det),'wall_guard_firings_P':kills,
         'wall_guard_firings_B24_reported':killsB,'per_case':det,'columns':['seed','canon64_equal','P20','P20b']},why=wb)
    fi=(api or {}).get('fidelity') or {};eq=(api or {}).get('equiv') or {};xr=(api or {}).get('xref') or {}
    ndec=sum(dd(c,a) for c in cs for a in c['arms'])
    fi_ok=bool(fi) and fi.get('study_results_sha256')==rsha and fi.get('PASS') is True and fi.get('exact')==fi.get('decided_records')==ndec
    gh=(api or {}).get('ghost') or {}
    gate('GFID64',complete and fi_ok and eq.get('PASS') is True and gh.get('network_pass') is True,{'no_network_run':gh.get('no_network_run'),
         'equiv_cases':eq.get('cases'),'bounds':eq.get('bounds'),'smoke_world_identical':eq.get('smoke_world_identical'),'smoke_labels':eq.get('smoke_labels'),
         'fidelity_exact':fi.get('exact'),'of_decided':fi.get('decided_records'),'decided_in_gates':ndec,'vacuous':fi.get('vacuous'),
         'bound':bool(fi) and fi.get('study_results_sha256')==rsha,'failures':{k:v for k,v in (fi.get('per_case') or {}).items() if not v['exact']}},
         why=wb or (None if fi else 'INCOMPLETE_INPUT (API_CHECKS_064 fidelity missing)'))
    gate('GXREF64',xr.get('PASS') is True,None if not xr else {k:xr.get(k) for k in ('random_traces','checks','disagreements','study063','study063_match','PASS')},
         why=None if xr else 'INCOMPLETE_INPUT (API_CHECKS_064 xref missing)')
    ct=sha(ROOT/'brute/api/certify32p.py');f64=(fz or {}).get('sha256_files',{}).get('brute/api/certify32p.py')
    abound=bool(api) and api.get('certify32p_sha256')==ct==f64
    gate('GHOST64',abound and gh.get('PASS64') is True,None if not api else {'bound_to_freeze_064':abound,'static_ok':gh.get('certify32p_static_ok'),
         'ast_scan':gh.get('certify32p_ast_scan'),'frozen_api_unchanged':gh.get('frozen_api_unchanged'),'a16d_max_bound_unpatched':gh.get('a16d_max_bound_unpatched'),
         'socket_attempts':gh.get('socket_attempts'),'no_network_run':gh.get('no_network_run')},
         why=None if api else 'INCOMPLETE_INPUT (API_CHECKS_064 missing)')
    mt=(ref or {}).get('mutation_test') or {};rb=bool(ref) and ref.get('study_results_sha256')==rsha and ref.get('block')=='main'
    robs=None if not ref else {k:ref.get(k) for k in ('block','scope','records','decided','audited','not_audited','complete','per_arm','not_reached',
                               'k_spent_as_amb','verdicts_checked','mismatch_count','misfires','vacuous','PASS','elapsed_informational')}|{'mutations':mt.get('detected'),'of':mt.get('mutations')}
    sc_=(ref or {}).get('scope') or {}
    gate('GS_ref64',rb and ref.get('mismatch_count')==0 and ref.get('complete') is True and sc_.get('budget_s')==REF_BUDGET and sc_.get('workers')==REF_WORKERS
         and (ref.get('vacuous') is True or mt.get('detected')==mt.get('mutations')==20) and ref.get('PASS') is True,robs,
         why=wb or (None if ref else 'INCOMPLETE_INPUT (REFERENCE_064 missing)'))
    gate('G_recount64',complete and rc_ok,None if not rc else {k:rc.get(k) for k in ('cases','records','decided_by_arm','study_decided_by_arm','wrong','mismatches','PASS')},
         why=wb or (None if rc else 'INCOMPLETE_INPUT (RECOUNT_064 missing)'))
    mods=(ts or {}).get('per_module') or {};gm=(ts or {}).get('gated_modules') or []
    gate('GTEST64',bool(gm) and ts.get('passed') is True and all(mods[x].get('returncode')==0 for x in gm),
         None if not ts else {'gated':{x:{'returncode':mods[x].get('returncode'),'tests':mods[x].get('tests')} for x in gm},
                              'reported':{x:{'returncode':v.get('returncode'),'tests':v.get('tests')} for x,v in mods.items() if x not in gm}},
         why=None if ts else 'INCOMPLETE_INPUT (TEST_SUITE_064 missing)')
    lt=ledger();ev=[e for e,_ in lt];times=[t for _,t in lt]
    proc={'order':subseq(ev,PROC_ORDER),'ledger_times_parse':bool(lt) and all(t is not None for t in times),
          'ledger_times_non_decreasing':all(a<=b for a,b in zip(times,times[1:]) if a and b),'commit_order_file':order is not None,'main_sealed':bool(sealed)}
    gate('G_PROC64',all(proc.values()),{'clauses':proc,'events':ev,'required_order':list(PROC_ORDER)})
    row=lambda c,a:[a,lab(c,a),c['arms'][a]['n_min'],len(c['arms'][a]['extra_acts']),c['arms'][a]['n_rounds'],c['arms'][a]['conflicts_spent']]
    sec['GSTATS64']={'pass':None,'observed':[[c['key'],c['seed']]+[row(c,a) for a in c['arms']] for c in cs],
                     'columns':['key','seed','per arm [arm, label, n_min, extra_actions, rounds, conflicts]'],'rule':'reported'}
    cl=[[c['key'],c['seed'],a,c['arms'][a]['clique_prefix'],c['arms'][a]['clique_final'],c['arms'][a].get('clique_size'),
         len(c['arms'][a].get('final_clique') or []),len(c['arms'][a].get('repins') or [])] for c in cs for a in c['arms'] if a in ('P24','P20')]
    sec['CLIQUE64']={'pass':None,'observed':{'per_record':cl,'columns':['key','seed','arm','greedy_prefix','greedy_final','anchor_clique_size',
                     'final_clique_len','pins']},'rule':'reported'}
    cost={}
    for c in cs:
        for a,ar in c['arms'].items():
            x=cost.setdefault(a,{'records':0,'wall_s':0.0,'conflicts':0,'steps':0,'budget_spent':0,'wall_guard':0,'decided_conflicts':[],'decided_walls':[]})
            x['records']+=1;x['wall_s']+=ar.get('case_wall_informational') or 0.0;x['conflicts']+=ar.get('conflicts_spent') or 0
            x['steps']+=len(ar.get('extra_acts') or []);x['budget_spent']+=(ar.get('conflicts_spent') or 0)>=ar['budget_conflicts']
            x['wall_guard']+=bool(ar.get('wall_guard'))
            if dd(c,a):x['decided_conflicts'].append(ar.get('conflicts_spent'));x['decided_walls'].append(round(ar.get('case_wall_informational') or 0.0,1))
    for x in cost.values():x['wall_s']=round(x['wall_s'],1);x['decided_conflicts'].sort();x['decided_walls'].sort()
    sec['GCOST64']={'pass':None,'observed':cost,'elapsed_s':(res or {}).get('total_elapsed_informational'),'rule':'reported (walls informational)'}
    sc_frozen=bool(sc) and (fz or {}).get('sha256_files',{}).get('results/diag-064/SEEDCHECK_064.json')==sha(ROOT/'results/diag-064/SEEDCHECK_064.json')
    sec['SEEDCHECK64']={'pass':None,'observed':None if not sc else {'seedcheck_pass':sc.get('PASS'),'frozen_in_064':sc_frozen}}
    pr=opt(ROOT/'results/diag-064/CAPABILITY_PROBE_064.json')
    sec['PROBE64']={'pass':None,'observed':None if not pr else {k:pr.get(k) for k in ('summary','settings','seeds') if k in pr},'rule':'exploratory, sealed non-fresh seeds; not gate evidence'}
    fl={}
    for a in ARMS:
        cc=[c for c in cs if a in c['arms']];fl[a]={L:{'x':sum(lab(c,a)==L for c in cc),'n':len(cc),'ci95':ci(sum(lab(c,a)==L for c in cc),len(cc))} for L in LABELS}
    ok=all(g['pass'] for g in Gt.values())
    c20ok=not ok and all(g['pass'] for k,g in Gt.items() if k not in SOFT)
    failed=[k for k,g in Gt.items() if g['pass'] is False]
    return {'schema':'brute.gates.v61_0','study':(res or {}).get('plan',{}).get('study'),'process':'lean',
            'sealed_input_verified':sealed,'label_source':lsrc,'n_seeds':n,'n_b24':nb24,'n_p20b':nb20,'caps':(res or {}).get('caps'),
            'workers':(res or {}).get('workers'),'stop':(res or {}).get('stop'),'arm_spec':(res or {}).get('arm_spec'),'node_cap':(res or {}).get('node_cap'),
            'gates':Gt,'secondary':sec,'all_gated_pass':ok,'failed':failed,'not_exercised':[],
            'certified_readbits2_N24_clique':ok,'certified_readbits2_N20_clique':ok or c20ok,'status_phrase':status_phrase(ok,c20ok,failed),
            'framing':'SIZE TEST: the v0.60.0 clique-anchored method (certify/32p) on 2-bit 24-state worlds at declared N 24, plus a certify/20p replication at N 20 with a clique-pinned independent reference',
            'claim':('certify/32p, certify/32b and certify/20p ID/IDF are exact conditional on noise-free readings and on true size <= the declared N. IDF identifies the '
                     'machine from the current state, not the start. Inferred reason the size condition is needed: a larger machine can copy the true machine on every visited state'),
            'reports':{'labels':fl} if cs else {}}


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--study-dir',default=str(STUDY_DIR));ap.add_argument('--check',action='store_true');a=ap.parse_args()
    obj=build(Path(a.study_dir));out=Path(a.study_dir)/'GATES_064.json'
    if a.check:check(out.read_bytes()==dumps(obj),'GATES_064.json does not reproduce');print('GATES_064 reproduces')
    else:write_new(out,obj);print(json.dumps({k:v['pass'] for k,v in obj['gates'].items()}),obj['failed'])
