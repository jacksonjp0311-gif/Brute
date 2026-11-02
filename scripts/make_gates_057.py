"""Gates for study-057 (BRUTE_PLAN_057 criteria; pre-run deviation #188 definitions), LEAN process. Committed in the source freeze
before run_start_057; nothing is tuned after results are seen. New file; built from scripts/make_gates_056.py (frozen).
Inputs (D = results/study-057): D/main/{RESULTS,SCIENTIFIC,SEAL}.json, D/main/RECOUNT_057.json, D/main/REFERENCE_057.json,
D/API_CHECKS_057.json, D/TEST_SUITE_057.json, results/diag-057/SEEDCHECK_057.json, experiments/COMMIT_ORDER_057.json,
results/RESEARCH_LEDGER.jsonl. Missing or partial input => every data gate FAIL INCOMPLETE_INPUT. Records are accepted only if
sha256(RESULTS) equals the seal and no_time(RESULTS) equals SCIENTIFIC. Labels: recounted if G_recount passes, else the study's.
Arms (scale20v, certify/16e at bound 20): API16E20, COV_O (oracle-planned, not deployable), LEN_R, COV_X, COV_X_b.
  GS57_sound: WRONG 0 on every record;
  GMATCH57: per seed (n57/n57): COV_O hand-off has 0 unexercised truth pairs reachable from the post-prefix state and LEN_R ext_len ==
     COV_O ext_len (RECOUNT_057 coverage, recomputed from the world, and both extensions reproduce their declared rules);
  GPRE57: COV_O ID+IDF >= 3 AND COV_O ID+IDF - LEN_R ID+IDF >= 2 on the same seeds (Wilson CIs; exact McNemar reported);
  GX_gain57: COV_X (pass 1) ID+IDF >= 2 AND > API16E20 ID+IDF on the same seeds;
  GDET57: canon57(COV_X) == canon57(COV_X_b) (canon16e plus extension and api result) and identical conflicts_spent and ext_acts on
     every seed, 0 hard kills (wall_guard) on every record;
  GFID57: API_CHECKS_057 fidelity exact on every COV_X record, bound to the sealed RESULTS sha;
  GHOST57: API_CHECKS_057 ghost PASS57, bound to cover20.py's sha in BRUTE_SOURCE_FREEZE_057;
  G_sound: 0 unsound words (study and recount), recount checked the same words, 0 WRONG;
  GS_ref: REFERENCE_057 on block main: sha bound, 0 mismatches, complete within 2400 s on 8 workers, 20/20 mutations (vacuous only if
     nothing is decided);
  G_recount; GTI57: RECOUNT_057 truth_inconsistent == 0 (bound); GTEST: gated modules of TEST_SUITE_057 pass;
  G_PROC: preregistration, build_authorization, seedcheck, prefreeze_smoke, deviation_188, source_freeze, run_start, run_end, recount,
     reference, api_checks, tests (_057) as a subsequence, parseable non-decreasing note times, commit-order file, main sealed;
  G_RT: main elapsed <= 3600 s.
  certified_20v_N20: every gate passes; sound_not_certified_20v: every gate except GPRE57 and/or GX_gain57 passes (plan certification_rule;
  the oracle walk is never certified). status_phrase: derived from the two flags (plan status_wording_rule).
  Secondary (reported): GPRE_stats57, GCOVX57, GCOST57, MCNEMAR57, SEEDCHECK57.
  PYTHONPATH=. python scripts/make_gates_057.py [--study-dir D] [--check]"""
from __future__ import annotations
import argparse,json,sys
from math import comb
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common import load,dumps,write_new,check,sha
from experiments.brute_common_026 import wilson
from scripts.make_gates_034 import opt
from scripts.make_gates_043 import subseq

STUDY_DIR=ROOT/'results/study-057';ARMS=('API16E20','COV_O','LEN_R','COV_X','COV_X_b')
LABELS=('ID','IDF','AMB','WRONG','IDU');CAP_RT=3600;MIN_PRE=3;MIN_DIFF=2;MIN_X=2;SOFT=('GPRE57','GX_gain57')
PROC_ORDER=('preregistration_057','build_authorization_057','seedcheck_057','prefreeze_smoke_057','deviation_188','source_freeze_057',
            'run_start_057','run_end_057','recount_057','reference_057','api_checks_057','tests_057')


def ckey(c):return f"{c['block']}/{c['key']}/{c['seed']}"


def ledger():
    from datetime import datetime
    L=[json.loads(x) for x in (ROOT/'results/RESEARCH_LEDGER.jsonl').read_text().splitlines() if x.strip()]
    i0=next((i for i,e in enumerate(L) if e.get('event')=='preregistration_057'),None);out=[]
    for e in (L[i0:] if i0 is not None else []):
        try:t=datetime.fromisoformat(str(e.get('note',''))[:25])
        except ValueError:t=None
        out.append((e['event'],t))
        if e['event']==PROC_ORDER[-1]:break
    return out


def status_phrase(certified,sound_only,failed):
    """Plan 057 status_wording_rule: the only status phrases, derived from the two flags."""
    if certified:return 'certified'
    if sound_only:return 'sound but not certified'
    return 'not certified, no certification status (failing gates: '+', '.join(failed)+')'


def mcnemar(b,c):
    """Exact two-sided McNemar p on discordant counts b, c."""
    n=b+c
    if n==0:return 1.0
    k=min(b,c);return min(1.0,2*sum(comb(n,i) for i in range(k+1))/2**n)


def build(study=STUDY_DIR,expect=None):
    from brute.evaluation import no_time
    from experiments.brute_study_057 import canon57,N57
    study=Path(study);D=study/'main';Gt={};sec={}
    seal=opt(D/'SEAL.json');sci=opt(D/'SCIENTIFIC.json');res=opt(D/'RESULTS.json');rc=opt(D/'RECOUNT_057.json')
    ref=opt(D/'REFERENCE_057.json');ts=opt(study/'TEST_SUITE_057.json');order=opt(ROOT/'experiments/COMMIT_ORDER_057.json')
    api=opt(study/'API_CHECKS_057.json');fz=opt(ROOT/'experiments/BRUTE_SOURCE_FREEZE_057.json')
    sc=opt(ROOT/'results/diag-057/SEEDCHECK_057.json')
    rsha=sha(D/'RESULTS.json') if (D/'RESULTS.json').exists() else None
    sealed=(bool(seal) and res is not None and sci is not None and rsha==seal.get('results_sha256')
            and sha(D/'SCIENTIFIC.json')==seal.get('scientific_sha256') and no_time(res)==sci)
    n=int(expect if expect is not None else (res or {}).get('n57',N57))
    allc=sorted([c for c in (res or {}).get('cases',[]) if c['block']=='main'],key=lambda c:c['seed']) if sealed else []
    arms_ok=all(sorted(c['arms'])==sorted(ARMS) for c in allc)
    complete=sealed and seal.get('complete') is True and len(allc)==n and arms_ok
    wb=None if complete else 'INCOMPLETE_INPUT (main missing, partial, missing arms or not matching its seal)'
    def gate(name,ok,obs,why=None):Gt[name]={'pass':bool(ok) and why is None,'observed':obs,**({'reason':why} if why else {})}
    pc=(rc or {}).get('per_case') or {};cv=(rc or {}).get('coverage') or {}
    rc_bound=bool(rc) and rc.get('results_sha256')==rsha and rc.get('cases')==len((res or {}).get('cases',[]))
    rc_ok=rc_bound and rc.get('PASS') is True and rc.get('mismatching_cases')==0
    lab=(lambda c,a:((pc.get(ckey(c)) or {}).get(a) or {}).get('label')) if rc_ok else (lambda c,a:c['arms'][a]['label'])
    lsrc='recount' if rc_ok else 'study labels (G_recount did not pass)'
    dd=lambda c,a:a in c['arms'] and lab(c,a) in ('ID','IDF')
    ci=lambda x,m:wilson(x,m) if m else None
    nd_=lambda a:sum(dd(c,a) for c in allc)
    wrong=[[ckey(c),a] for c in allc for a in c['arms'] if lab(c,a)=='WRONG' or c['arms'][a]['label']=='WRONG']
    gate('GS57_sound',complete and not wrong,{'WRONG':wrong,'records':sum(len(c['arms']) for c in allc),
         'per_case':[[c['seed']]+[lab(c,a) for a in ARMS] for c in allc],'columns':['seed']+list(ARMS),'label_source':lsrc},why=wb)
    # GMATCH57
    mrow=[];nm=0
    for c in allc:
        v=cv.get(ckey(c)) or {};o=v.get('COV_O') or {};l=v.get('LEN_R') or {}
        ok=bool(rc_bound and o.get('handoff_reachable')==0 and o.get('ext_ok') and l.get('ext_ok') and o.get('ext_len')==l.get('ext_len'))
        nm+=ok;mrow.append([c['seed'],o.get('ext_len'),o.get('handoff_reachable'),l.get('ext_len'),l.get('handoff_reachable'),ok])
    gate('GMATCH57',complete and rc_bound and nm==n,{'valid':nm,'of':n,'per_case':mrow,
         'columns':['seed','COV_O_ext_len','COV_O_handoff_reachable_unexercised','LEN_R_ext_len','LEN_R_handoff_reachable_unexercised','valid'],
         'source':'RECOUNT_057 coverage (recomputed from the world)'},why=wb or (None if rc_bound else 'INCOMPLETE_INPUT (RECOUNT_057 missing or unbound)'))
    xo,xl,xe,xx,xb=(nd_(a) for a in ARMS[1:2]+ARMS[2:3]+ARMS[0:1]+ARMS[3:5])
    b1=sum(dd(c,'COV_O') and not dd(c,'LEN_R') for c in allc);c1=sum(dd(c,'LEN_R') and not dd(c,'COV_O') for c in allc)
    gate('GPRE57',complete and xo>=MIN_PRE and xo-xl>=MIN_DIFF,{'COV_O_ID_IDF':xo,'LEN_R_ID_IDF':xl,'of':len(allc),'ci95_COV_O':ci(xo,len(allc)),
         'ci95_LEN_R':ci(xl,len(allc)),'discordant':[b1,c1],'mcnemar_p_reported':mcnemar(b1,c1),
         'rule':'COV_O ID+IDF >= 3 and COV_O - LEN_R >= 2 on the same seeds (COV_O is oracle-planned, not deployable)','label_source':lsrc},why=wb)
    gate('GX_gain57',complete and xx>=MIN_X and xx>xe,{'COV_X_ID_IDF':xx,'API16E20_ID_IDF':xe,'COV_X_b_ID_IDF':xb,'of':len(allc),
         'ci95_COV_X':ci(xx,len(allc)),'ci95_API16E20':ci(xe,len(allc)),'ci95_COV_X_b':ci(xb,len(allc)),
         'rule':'COV_X (pass 1) ID+IDF >= 2 and strictly more than API16E20 on the same seeds','label_source':lsrc},why=wb)
    det=[[c['seed'],canon57(c['arms']['COV_X'])==canon57(c['arms']['COV_X_b']),
          c['arms']['COV_X'].get('conflicts_spent')==c['arms']['COV_X_b'].get('conflicts_spent'),
          c['arms']['COV_X'].get('ext_acts')==c['arms']['COV_X_b'].get('ext_acts'),
          c['arms']['COV_X']['label'],c['arms']['COV_X_b']['label']] for c in allc]
    kills=[[ckey(c),an,ar.get('guard_events')] for c in allc for an,ar in c['arms'].items() if ar.get('wall_guard')]
    ndt=sum(x[1] and x[2] and x[3] for x in det)
    gate('GDET57',complete and ndt==n and not kills,{'identical':ndt,'of':len(det),'ci95':ci(ndt,len(det)),'hard_kills':kills,
         'records_checked_for_kill':sum(len(c['arms']) for c in allc),'per_case':det,
         'columns':['seed','canon57_equal','conflicts_equal','ext_equal','pass1','pass2']},why=wb)
    fi=(api or {}).get('fidelity') or {};fg=fi.get('gated') or {}
    fi_ok=bool(fi) and fi.get('study_results_sha256')==rsha and fi.get('PASS') is True and fg.get('exact')==fg.get('cases')==n
    gate('GFID57',complete and fi_ok,{'exact':fg.get('exact'),'of':fg.get('cases'),'expected':n,'ci95':ci(fg.get('exact') or 0,fg.get('cases') or 0),
         'bound':bool(fi) and fi.get('study_results_sha256')==rsha,'failures':{k:v for k,v in (fi.get('per_case') or {}).items() if not v['exact']}},
         why=wb or (None if fi else 'INCOMPLETE_INPUT (API_CHECKS_057 fidelity missing)'))
    ct=sha(ROOT/'brute/api/cover20.py');f57=(fz or {}).get('sha256_files',{}).get('brute/api/cover20.py')
    abound=bool(api) and api.get('cover20_sha256')==ct==f57;ag=(api or {}).get('ghost') or {}
    gate('GHOST57',abound and ag.get('PASS57') is True,None if not api else {'bound_to_freeze_057':abound,'cover20_static_ok':ag.get('cover20_static_ok'),
         'frozen_api_unchanged':ag.get('frozen_api_unchanged'),'closures_unchanged':ag.get('closures_unchanged'),'socket_attempts':ag.get('socket_attempts'),
         'no_network_run':ag.get('no_network_run')},why=None if api else 'INCOMPLETE_INPUT (API_CHECKS_057 missing)')
    snd={'words_checked':sum(ar.get('words_checked',0) for c in allc for ar in c['arms'].values()),
         'words_unsound':sum(ar.get('words_unsound',0) for c in allc for ar in c['arms'].values()),
         'recount_bound':rc_bound,'recount_words_checked':(rc or {}).get('words_checked'),'recount_words_unsound':(rc or {}).get('words_unsound'),'WRONG':wrong}
    gate('G_sound',complete and rc_bound and snd['words_unsound']==0 and snd['recount_words_unsound']==0 and snd['recount_words_checked']==snd['words_checked'] and not wrong,
         snd,why=wb or (None if rc_bound else 'INCOMPLETE_INPUT (RECOUNT_057 missing or unbound)'))
    mt=(ref or {}).get('mutation_test') or {};rb=bool(ref) and ref.get('study_results_sha256')==rsha and ref.get('block')=='main'
    robs=None if not ref else {k:ref.get(k) for k in ('block','scope','records','decided','audited','not_audited','complete','per_arm','not_reached',
                               'k_spent_as_amb','verdicts_checked','mismatch_count','vacuous','PASS','elapsed_informational')}|{'mutations':mt.get('detected'),'of':mt.get('mutations')}
    gate('GS_ref',rb and ref.get('mismatch_count')==0 and ref.get('complete') is True and (ref.get('scope') or {}).get('budget_12_s')==2400.0
         and (ref.get('vacuous') is True or mt.get('detected')==mt.get('mutations')==20) and ref.get('PASS') is True,robs,
         why=wb or (None if ref else 'INCOMPLETE_INPUT (REFERENCE_057 missing)'))
    gate('G_recount',complete and rc_ok,None if not rc else {k:rc.get(k) for k in ('cases','recounted','labels','misfires',
         'amb_rule_applied','words_checked','words_unsound','truth_inconsistent','mismatching_cases','mismatches','PASS')},
         why=wb or (None if rc else 'INCOMPLETE_INPUT (RECOUNT_057 missing)'))
    gate('GTI57',complete and rc_bound and rc.get('truth_inconsistent')==0,None if not rc else {'truth_inconsistent':rc.get('truth_inconsistent'),'bound':rc_bound},
         why=wb or (None if rc else 'INCOMPLETE_INPUT (RECOUNT_057 missing)'))
    mods=(ts or {}).get('per_module') or {};gm=(ts or {}).get('gated_modules') or []
    gate('GTEST',bool(gm) and ts.get('passed') is True and all(mods[m].get('returncode')==0 for m in gm),
         None if not ts else {'gated':{m:{'returncode':mods[m].get('returncode'),'tests':mods[m].get('tests')} for m in gm},
                              'reported':{m:{'returncode':v.get('returncode'),'tests':v.get('tests')} for m,v in mods.items() if m not in gm}},
         why=None if ts else 'INCOMPLETE_INPUT (TEST_SUITE_057 missing)')
    lt=ledger();ev=[e for e,_ in lt];times=[t for _,t in lt]
    proc={'order':subseq(ev,PROC_ORDER),'ledger_times_parse':bool(lt) and all(t is not None for t in times),
          'ledger_times_non_decreasing':all(a<=b for a,b in zip(times,times[1:]) if a and b),'commit_order_file':order is not None,'main_sealed':bool(sealed)}
    gate('G_PROC',all(proc.values()),{'clauses':proc,'events':ev,'required_order':list(PROC_ORDER)})
    el=(res or {}).get('total_elapsed_informational')
    gate('G_RT',complete and el is not None and el<=CAP_RT,{'elapsed_s':el,'cap_s':CAP_RT,'cases':len(allc),'n57':n},why=wb)
    # secondary
    sec['GPRE_stats57']={'pass':None,'observed':[[c['seed']]+[[lab(c,a),c['arms'][a].get('ext_len'),c['arms'][a].get('truth_pairs_unexercised_handoff_reachable'),
                          c['arms'][a].get('truth_pairs_unexercised_final_reachable'),c['arms'][a].get('n_rounds'),c['arms'][a].get('conflicts_spent')] for a in ARMS[:4]] for c in allc],
                         'columns':['seed']+[a+' [label, ext_len, handoff_reach_unex, final_reach_unex, rounds, conflicts]' for a in ARMS[:4]],'rule':'reported'}
    hx=[c['arms']['COV_X'].get('truth_pairs_unexercised_handoff_reachable') for c in allc]
    sec['GCOVX57']={'pass':None,'observed':{'handoff_reachable_unexercised':hx,'full':sum(x==0 for x in hx if x is not None),'of':len(hx),
                    'mean':round(sum(hx)/len(hx),3) if hx and None not in hx else None},'rule':'reported: cover20 hand-off coverage'}
    cost={}
    for c in allc:
        for a,ar in c['arms'].items():
            x=cost.setdefault(a,{'records':0,'arm_wall_s':0.0,'conflicts':0,'calls':0,'chunks':0,'steps':0,'budget_spent':0})
            x['records']+=1;x['arm_wall_s']+=ar.get('arm_wall_informational') or 0.0;x['conflicts']+=ar.get('conflicts_spent') or 0
            x['calls']+=ar.get('calls_total') or 0;x['chunks']+=ar.get('chunks_total') or 0;x['steps']+=len(ar.get('extra_acts') or [])
            x['budget_spent']+=(ar.get('conflicts_spent') or 0)>=ar['budget_conflicts']
    for x in cost.values():x['arm_wall_s']=round(x['arm_wall_s'],1)
    sec['GCOST57']={'pass':None,'observed':cost,'rule':'reported (walls informational)'}
    b2=sum(dd(c,'COV_X') and not dd(c,'API16E20') for c in allc);c2=sum(dd(c,'API16E20') and not dd(c,'COV_X') for c in allc)
    sec['MCNEMAR57']={'pass':None,'observed':{'COV_O_vs_LEN_R':{'discordant':[b1,c1],'p':mcnemar(b1,c1)},'COV_X_vs_API16E20':{'discordant':[b2,c2],'p':mcnemar(b2,c2)}},
                      'rule':'reported: exact two-sided McNemar'}
    sc_frozen=bool(sc) and (fz or {}).get('sha256_files',{}).get('results/diag-057/SEEDCHECK_057.json')==sha(ROOT/'results/diag-057/SEEDCHECK_057.json')
    sec['SEEDCHECK57']={'pass':None,'observed':None if not sc else {'seedcheck_pass':sc.get('PASS'),'frozen_in_057':sc_frozen,'total_cases':sc.get('total_cases')}}
    cnt=lambda a,L:sum(lab(c,a)==L for c in allc)
    fl={a:{L:{'x':cnt(a,L),'n':len(allc),'ci95':ci(cnt(a,L),len(allc))} for L in LABELS} for a in ARMS}
    ok=all(g['pass'] for g in Gt.values())
    sound_only=not ok and all(g['pass'] for k,g in Gt.items() if k not in SOFT)
    failed=[k for k,g in Gt.items() if g['pass'] is False]
    return {'schema':'brute.gates.v54_0','study':(res or {}).get('plan',{}).get('study'),'process':'lean',
            'sealed_input_verified':sealed,'label_source':lsrc,'n57':n,'caps':(res or {}).get('caps'),
            'workers':(res or {}).get('workers'),'stop':(res or {}).get('stop'),'cover':(res or {}).get('cover'),'gates':Gt,'secondary':sec,
            'all_gated_pass':ok,'failed':failed,'not_exercised':[],
            'certified_20v_N20':ok,'sound_not_certified_20v':sound_only,'status_phrase':status_phrase(ok,sound_only,failed),
            'claim':('certify/20v (cover20 then certify/16e) ID/IDF is exact on noise-free traces conditional on true size <= the declared N (here '
                     'N <= 20); IDF identifies the machine from the current state, not the start. Inferred reason the condition is needed: a larger '
                     'machine can copy the true machine on every visited state. The oracle walk (COV_O) is never certified'),
            'reports':{'labels':fl} if allc else {}}


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--study-dir',default=str(STUDY_DIR));ap.add_argument('--check',action='store_true');a=ap.parse_args()
    obj=build(Path(a.study_dir));out=Path(a.study_dir)/'GATES_057.json'
    if a.check:check(out.read_bytes()==dumps(obj),'GATES_057.json does not reproduce');print('GATES_057 reproduces')
    else:write_new(out,obj);print(json.dumps({k:v['pass'] for k,v in obj['gates'].items()}),obj['failed'])
