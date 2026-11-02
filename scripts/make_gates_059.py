"""Gates for study-059 (BRUTE_PLAN_059 criteria; pre-run deviation #192 definitions), LEAN process. Committed in the source freeze
before main_run_059; nothing is tuned after results are seen. New file; built from scripts/make_gates_058.py (frozen).
HONEST FRAMING (plan honest_framing): this study changes the TARGET (wide 4-bit readings, now with iid reading noise); 2-bit readings
at 20 states stay Open whatever it shows.
Inputs (D = results/study-059): D/main/{RESULTS,SCIENTIFIC,SEAL}.json, D/main/RECOUNT_059.json, D/main/REFERENCE_059.json,
D/API_CHECKS_059.json, D/TEST_SUITE_059.json, results/diag-059/SEEDCHECK_059.json, experiments/COMMIT_ORDER_059.json,
results/RESEARCH_LEDGER.jsonl. Missing or partial input => every data gate FAIL INCOMPLETE_INPUT. Records are accepted only if
sha256(RESULTS) equals the seal and no_time(RESULTS) equals SCIENTIFIC. Labels: recounted if G_recount passes, else the study's.
Arms (bound 20, read_bits 4, scale20r4): C4 (certify/20b, eps 0), N4_05 (certify/20n, eps 0.05, eps_bar 0.10), N4_10 and N4_10b
(eps 0.10, eps_bar 0.15; N4_10b in reversed seed order), NEG4 (eps 0.25 > eps_bar 0.10: noise model violated; reported, never gated).
  GS59_sound: WRONG 0 on the 48 gated records (C4, N4_05, N4_10, N4_10b) against the clean truth (NOFIT is a refusal, not WRONG);
  GN_keep59: N4_10 ID+IDF >= 6 of 12 AND N4_10 >= C4 - 2 (Wilson CIs; exact McNemar N4_10 vs C4 reported);
  GN05_59: N4_05 ID+IDF >= 6 of 12;
  GMAJ59: total majority errors 0 over every observation of N4_05, N4_10, N4_10b (recounted values if G_recount passes);
  GDET59: canon59(N4_10) == canon59(N4_10b) on every seed, 0 wall-guard firings on every record;
  GFID59: API_CHECKS_059 equiv (a: 20n reads=1 == 20b; b: 20n read_bits 2 == 16n; c: malformed refused), the no-network run
     (0 socket attempts) and fidelity exact on every decided record, bound to the sealed RESULTS sha;
  GHOST59: API_CHECKS_059 ghost PASS59, bound to certify20n.py's sha in BRUTE_SOURCE_FREEZE_059;
  GS_ref: REFERENCE_059 on block main: sha bound, 0 counted mismatches, complete within 1800 s on 8 workers, 20/20 mutations
     (vacuous only if nothing is decided);
  G_recount: RECOUNT_059 bound and PASS; GTEST: gated modules of TEST_SUITE_059 pass;
  G_PROC: preregistration_059, build_authorization_059, seedcheck_059, prefreeze_smoke_059, deviation_192, freeze_059, main_run_059
     as a subsequence, parseable non-decreasing note times, commit-order file, main sealed;
  G_RT: verify_release_0560 at release (not gated here).
  certified_noisy_readbits4_N20: every gate passes; sound_not_certified_noisy: every gate except GN_keep59 and/or GN05_59 passes.
  status_phrase: derived from the two flags. Secondary (reported): GCOST59, GSTATS59, NEG4_report, MCNEMAR59, SEEDCHECK59.
  PYTHONPATH=. python scripts/make_gates_059.py [--study-dir D] [--check]"""
from __future__ import annotations
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common import load,dumps,write_new,check,sha
from experiments.brute_common_026 import wilson
from scripts.make_gates_034 import opt
from scripts.make_gates_043 import subseq
from scripts.make_gates_057 import mcnemar

STUDY_DIR=ROOT/'results/study-059';ARMS=('C4','N4_05','N4_10','N4_10b','NEG4');GATED=('C4','N4_05','N4_10','N4_10b');NOISY=('N4_05','N4_10','N4_10b')
LABELS=('ID','IDF','AMB','WRONG','IDU','NOFIT');MIN_N=6;SLACK=2;SOFT=('GN_keep59','GN05_59')
PROC_ORDER=('preregistration_059','build_authorization_059','seedcheck_059','prefreeze_smoke_059','deviation_192','freeze_059','main_run_059')


def ckey(c):return f"{c['block']}/{c['key']}/{c['seed']}"


def ledger():
    from datetime import datetime
    L=[json.loads(x) for x in (ROOT/'results/RESEARCH_LEDGER.jsonl').read_text().splitlines() if x.strip()]
    i0=next((i for i,e in enumerate(L) if e.get('event')=='preregistration_059'),None);out=[]
    for e in (L[i0:] if i0 is not None else []):
        try:t=datetime.fromisoformat(str(e.get('note',''))[:25])
        except ValueError:t=None
        out.append((e['event'],t))
        if e['event']==PROC_ORDER[-1]:break
    return out


def status_phrase(certified,sound_only,failed):
    if certified:return 'certified (read_bits 4, iid bit noise eps <= eps_bar <= 0.15, N <= 20)'
    if sound_only:return 'sound but not certified'
    return 'not certified, no certification status (failing gates: '+', '.join(failed)+')'


def build(study=STUDY_DIR,expect=None):
    from brute.evaluation import no_time
    from experiments.brute_study_059 import canon59,N59
    study=Path(study);D=study/'main';Gt={};sec={}
    seal=opt(D/'SEAL.json');sci=opt(D/'SCIENTIFIC.json');res=opt(D/'RESULTS.json');rc=opt(D/'RECOUNT_059.json')
    ref=opt(D/'REFERENCE_059.json');ts=opt(study/'TEST_SUITE_059.json');order=opt(ROOT/'experiments/COMMIT_ORDER_059.json')
    api=opt(study/'API_CHECKS_059.json');fz=opt(ROOT/'experiments/BRUTE_SOURCE_FREEZE_059.json')
    sc=opt(ROOT/'results/diag-059/SEEDCHECK_059.json')
    rsha=sha(D/'RESULTS.json') if (D/'RESULTS.json').exists() else None
    sealed=(bool(seal) and res is not None and sci is not None and rsha==seal.get('results_sha256')
            and sha(D/'SCIENTIFIC.json')==seal.get('scientific_sha256') and no_time(res)==sci)
    n=int(expect if expect is not None else (res or {}).get('n59',N59))
    allc=sorted([c for c in (res or {}).get('cases',[]) if c['block']=='main'],key=lambda c:c['seed']) if sealed else []
    arms_ok=all(sorted(c['arms'])==sorted(ARMS) for c in allc)
    complete=sealed and seal.get('complete') is True and len(allc)==n and arms_ok
    wb=None if complete else 'INCOMPLETE_INPUT (main missing, partial, missing arms or not matching its seal)'
    def gate(name,ok,obs,why=None):Gt[name]={'pass':bool(ok) and why is None,'observed':obs,**({'reason':why} if why else {})}
    pc=(rc or {}).get('per_case') or {}
    rc_bound=bool(rc) and rc.get('results_sha256')==rsha and rc.get('cases')==len((res or {}).get('cases',[]))
    rc_ok=rc_bound and rc.get('PASS') is True and not rc.get('mismatches')
    rget=lambda c,a,f:((pc.get(str(c['seed'])) or {}).get(a) or {}).get(f)
    lab=(lambda c,a:rget(c,a,'label')) if rc_ok else (lambda c,a:c['arms'][a]['label'])
    mer=(lambda c,a:rget(c,a,'maj_errors')) if rc_ok else (lambda c,a:c['arms'][a]['maj_errors'])
    lsrc='recount' if rc_ok else 'study labels (G_recount did not pass)'
    dd=lambda c,a:a in c['arms'] and lab(c,a) in ('ID','IDF')
    ci=lambda x,m:wilson(x,m) if m else None
    nd_=lambda a:sum(dd(c,a) for c in allc)
    wrong=[[ckey(c),a] for c in allc for a in GATED if lab(c,a)=='WRONG' or c['arms'][a]['label']=='WRONG']
    gate('GS59_sound',complete and not wrong,{'WRONG':wrong,'gated_records':sum(1 for c in allc for a in GATED if a in c['arms']),
         'per_case':[[c['seed']]+[lab(c,a) for a in ARMS] for c in allc],'columns':['seed']+list(ARMS),'label_source':lsrc},why=wb)
    xc,x05,x10,x10b,xneg=(nd_(a) for a in ARMS);m=len(allc)
    disc=lambda a,b:[sum(dd(c,a) and not dd(c,b) for c in allc),sum(dd(c,b) and not dd(c,a) for c in allc)]
    d10=disc('N4_10','C4');d05=disc('N4_05','C4')
    gate('GN_keep59',complete and x10>=MIN_N and x10>=xc-SLACK,{'N4_10_ID_IDF':x10,'C4_ID_IDF':xc,'of':m,'ci95_N4_10':ci(x10,m),'ci95_C4':ci(xc,m),
         'discordant':d10,'mcnemar_p_reported':mcnemar(*d10),'rule':'N4_10 ID+IDF >= 6 of 12 and N4_10 >= C4 - 2','label_source':lsrc},why=wb)
    gate('GN05_59',complete and x05>=MIN_N,{'N4_05_ID_IDF':x05,'of':m,'ci95_N4_05':ci(x05,m),'rule':'N4_05 ID+IDF >= 6 of 12','label_source':lsrc},why=wb)
    me={a:sum(mer(c,a) or 0 for c in allc) for a in ARMS};obs_n={a:sum(len(c['arms'][a]['reads_per_obs']) for c in allc) for a in ARMS}
    gate('GMAJ59',complete and all(me[a]==0 for a in NOISY),{'majority_errors':{a:me[a] for a in NOISY},'observations':{a:obs_n[a] for a in NOISY},
         'NEG4_majority_errors_reported':me['NEG4'],'source':'recount' if rc_ok else 'study'},why=wb)
    det=[[c['seed'],canon59(c['arms']['N4_10'])==canon59(c['arms']['N4_10b']),c['arms']['N4_10']['label'],c['arms']['N4_10b']['label']] for c in allc]
    kills=[[ckey(c),an,ar.get('guard_events')] for c in allc for an,ar in c['arms'].items() if ar.get('wall_guard')]
    ndt=sum(x[1] for x in det)
    gate('GDET59',complete and ndt==n and not kills,{'identical':ndt,'of':len(det),'ci95':ci(ndt,len(det)),'wall_guard_firings':kills,
         'records_checked':sum(len(c['arms']) for c in allc),'per_case':det,'columns':['seed','canon59_equal','N4_10','N4_10b']},why=wb)
    fi=(api or {}).get('fidelity') or {};eq=(api or {}).get('equiv') or {}
    ndec=sum(dd(c,a) for c in allc for a in c['arms'])
    fi_ok=bool(fi) and fi.get('study_results_sha256')==rsha and fi.get('PASS') is True and fi.get('exact')==fi.get('decided_records')
    gh=(api or {}).get('ghost') or {}
    gate('GFID59',complete and fi_ok and eq.get('PASS') is True and gh.get('network_pass') is True,{'no_network_run':gh.get('no_network_run'),
         'equiv_cases':eq.get('cases'),'refusals':eq.get('refusals'),'fidelity_exact':fi.get('exact'),'of_decided':fi.get('decided_records'),
         'decided_in_gates':ndec,'vacuous':fi.get('vacuous'),'bound':bool(fi) and fi.get('study_results_sha256')==rsha,
         'failures':{k:v for k,v in (fi.get('per_case') or {}).items() if not v['exact']}},
         why=wb or (None if fi else 'INCOMPLETE_INPUT (API_CHECKS_059 fidelity missing)'))
    ct=sha(ROOT/'brute/api/certify20n.py');f59=(fz or {}).get('sha256_files',{}).get('brute/api/certify20n.py')
    abound=bool(api) and api.get('certify20n_sha256')==ct==f59
    gate('GHOST59',abound and gh.get('PASS59') is True,None if not api else {'bound_to_freeze_059':abound,'static_ok':gh.get('certify20n_static_ok'),
         'frozen_api_unchanged':gh.get('frozen_api_unchanged'),'socket_attempts':gh.get('socket_attempts'),'no_network_run':gh.get('no_network_run')},
         why=None if api else 'INCOMPLETE_INPUT (API_CHECKS_059 missing)')
    mt=(ref or {}).get('mutation_test') or {};rb=bool(ref) and ref.get('study_results_sha256')==rsha and ref.get('block')=='main'
    robs=None if not ref else {k:ref.get(k) for k in ('block','scope','records','decided','audited','not_audited','complete','per_arm','not_reached',
                               'k_spent_as_amb','verdicts_checked','mismatch_count','misfires','vacuous','PASS','elapsed_informational')}|{'mutations':mt.get('detected'),'of':mt.get('mutations')}
    gate('GS_ref',rb and ref.get('mismatch_count')==0 and ref.get('complete') is True and (ref.get('scope') or {}).get('budget_s')==1800.0
         and (ref.get('vacuous') is True or mt.get('detected')==mt.get('mutations')==20) and ref.get('PASS') is True,robs,
         why=wb or (None if ref else 'INCOMPLETE_INPUT (REFERENCE_059 missing)'))
    gate('G_recount',complete and rc_ok,None if not rc else {k:rc.get(k) for k in ('cases','records','decided_by_arm','study_decided_by_arm','wrong_by_arm','mismatches','PASS')},
         why=wb or (None if rc else 'INCOMPLETE_INPUT (RECOUNT_059 missing)'))
    mods=(ts or {}).get('per_module') or {};gm=(ts or {}).get('gated_modules') or []
    gate('GTEST',bool(gm) and ts.get('passed') is True and all(mods[x].get('returncode')==0 for x in gm),
         None if not ts else {'gated':{x:{'returncode':mods[x].get('returncode'),'tests':mods[x].get('tests')} for x in gm},
                              'reported':{x:{'returncode':v.get('returncode'),'tests':v.get('tests')} for x,v in mods.items() if x not in gm}},
         why=None if ts else 'INCOMPLETE_INPUT (TEST_SUITE_059 missing)')
    lt=ledger();ev=[e for e,_ in lt];times=[t for _,t in lt]
    proc={'order':subseq(ev,PROC_ORDER),'ledger_times_parse':bool(lt) and all(t is not None for t in times),
          'ledger_times_non_decreasing':all(a<=b for a,b in zip(times,times[1:]) if a and b),'commit_order_file':order is not None,'main_sealed':bool(sealed)}
    gate('G_PROC',all(proc.values()),{'clauses':proc,'events':ev,'required_order':list(PROC_ORDER)})
    sec['GSTATS59']={'pass':None,'observed':[[c['seed']]+[[lab(c,a),c['arms'][a]['n_min'],len(c['arms'][a]['extra_acts']),c['arms'][a]['n_rounds'],
                       c['arms'][a]['conflicts_spent'],mer(c,a)] for a in ARMS] for c in allc],
                     'columns':['seed']+[a+' [label, n_min, extra_actions, rounds, conflicts, majority_errors]' for a in ARMS],'rule':'reported'}
    sec['MCNEMAR59']={'pass':None,'observed':{'N4_10_vs_C4':{'discordant':d10,'p':mcnemar(*d10)},'N4_05_vs_C4':{'discordant':d05,'p':mcnemar(*d05)}},
                      'rule':'reported: exact two-sided McNemar'}
    negw=[c['seed'] for c in allc if lab(c,'NEG4')=='WRONG']
    sec['NEG4_report']={'pass':None,'observed':{'labels':{L:sum(lab(c,'NEG4')==L for c in allc) for L in LABELS},'WRONG_seeds':negw,
                        'majority_errors':me['NEG4'],'ID_IDF':xneg},'rule':'reported; a WRONG here shows the noise assumption matters, not a soundness failure'}
    cost={}
    for c in allc:
        for a,ar in c['arms'].items():
            x=cost.setdefault(a,{'records':0,'wall_s':0.0,'conflicts':0,'chunks':0,'steps':0,'reads_total':0,'k_max':0,'budget_spent':0})
            x['records']+=1;x['wall_s']+=ar.get('case_wall_informational') or 0.0;x['conflicts']+=ar.get('conflicts_spent') or 0
            x['chunks']+=ar.get('chunks_total') or 0;x['steps']+=len(ar.get('extra_acts') or []);x['reads_total']+=ar.get('reads_total') or 0
            x['k_max']=max(x['k_max'],max(ar.get('reads_per_obs') or [1]));x['budget_spent']+=(ar.get('conflicts_spent') or 0)>=ar['budget_conflicts']
    for x in cost.values():x['wall_s']=round(x['wall_s'],1)
    sec['GCOST59']={'pass':None,'observed':cost,'elapsed_s':(res or {}).get('total_elapsed_informational'),'rule':'reported (walls informational)'}
    sc_frozen=bool(sc) and (fz or {}).get('sha256_files',{}).get('results/diag-059/SEEDCHECK_059.json')==sha(ROOT/'results/diag-059/SEEDCHECK_059.json')
    sec['SEEDCHECK59']={'pass':None,'observed':None if not sc else {'seedcheck_pass':sc.get('PASS'),'frozen_in_059':sc_frozen}}
    cnt=lambda a,L:sum(lab(c,a)==L for c in allc)
    fl={a:{L:{'x':cnt(a,L),'n':m,'ci95':ci(cnt(a,L),m)} for L in LABELS} for a in ARMS}
    ok=all(g['pass'] for g in Gt.values())
    sound_only=not ok and all(g['pass'] for k,g in Gt.items() if k not in SOFT)
    failed=[k for k,g in Gt.items() if g['pass'] is False]
    return {'schema':'brute.gates.v56_0','study':(res or {}).get('plan',{}).get('study'),'process':'lean',
            'sealed_input_verified':sealed,'label_source':lsrc,'n59':n,'caps':(res or {}).get('caps'),
            'workers':(res or {}).get('workers'),'stop':(res or {}).get('stop'),'arm_noise':(res or {}).get('arm_noise'),'delta':(res or {}).get('delta'),
            'gates':Gt,'secondary':sec,'all_gated_pass':ok,'failed':failed,'not_exercised':[],
            'certified_noisy_readbits4_N20':ok,'sound_not_certified_noisy':sound_only,'status_phrase':status_phrase(ok,sound_only,failed),
            'framing':'TARGET CHANGE: wide 4-bit readings on random emissions, now with iid reading noise; 2-bit readings at 20 states stay Open',
            'claim':('certify/20n ID/IDF is exact conditional on every majority reading being correct and on true size <= the declared N (here N <= 20); '
                     'under iid bit flips with eps <= eps_bar and state-preserving re-reads all majorities are correct with probability >= 1 - delta (0.001). '
                     'IDF identifies the machine from the current state, not the start. Inferred reason the size condition is needed: a larger machine '
                     'can copy the true machine on every visited state'),
            'reports':{'labels':fl} if allc else {}}


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--study-dir',default=str(STUDY_DIR));ap.add_argument('--check',action='store_true');a=ap.parse_args()
    obj=build(Path(a.study_dir));out=Path(a.study_dir)/'GATES_059.json'
    if a.check:check(out.read_bytes()==dumps(obj),'GATES_059.json does not reproduce');print('GATES_059 reproduces')
    else:write_new(out,obj);print(json.dumps({k:v['pass'] for k,v in obj['gates'].items()}),obj['failed'])
