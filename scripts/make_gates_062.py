"""Gates for study-062 (BRUTE_PLAN_062 criteria; pre-run deviation #198 definitions), LEAN process. Committed in the source freeze
before main_run_062; nothing is tuned after results are seen. New file; built from scripts/make_gates_061.py (frozen).
HONEST FRAMING (plan honest_framing): BACK ON THE HARD PROBLEM (2-bit readings at 20 states). A POLICY change (which actions are
taken: probe-word windows), not a new solver or encoding; B2 is the budget-matched control at the same B62.
Inputs (D = results/study-062): D/main/{RESULTS,SCIENTIFIC,SEAL}.json, D/main/RECOUNT_062.json, D/main/REFERENCE_062.json,
D/API_CHECKS_062.json, D/TEST_SUITE_062.json, results/diag-062/SEEDCHECK_062.json, experiments/COMMIT_ORDER_062.json,
results/RESEARCH_LEDGER.jsonl. Missing or partial input => every data gate FAIL INCOMPLETE_INPUT. Records are accepted only if
sha256(RESULTS) equals the seal and no_time(RESULTS) equals SCIENTIFIC. Labels: recounted if G_recount passes, else the study's.
Arms (worlds_058 scale20, read_bits 2, bound 20, noise-free, B62): B2 (certify/20b, usual policy), W2 (certify/20w, probe (0, 1)),
W2b (W2 on the first n_w2b seeds, reversed order). n = n_seeds.
  GS62_sound: WRONG 0 on every record of B2, W2 and W2b;
  GW62 (headline): W2 ID+IDF >= ceil(4 n / 12) AND (W2 - B2) >= ceil(3 n / 12) on the same seeds (plan 4 and 3 at n = 12; scaled
     by #198 only if the seed cut fires); Wilson 95% CIs and the exact two-sided McNemar p on the discordant pairs reported;
  GDET62: canon62(W2) == canon62(W2b) on every W2b seed (n_w2b of n_w2b), 0 wall-guard firings in W2 and W2b (B2 reported);
  GFID62: API_CHECKS_062 equiv (empty probe word == certify/20b record-for-record; refusals), the no-network run (0 socket
     attempts) and fidelity exact on every decided record, bound to the sealed RESULTS sha;
  GHOST62: API_CHECKS_062 ghost PASS62 (closure scan, AST scan of certify20w, frozen api shas vs FREEZE_061, certify16d bound
     unpatched, no network), with certify20w.py's sha equal to its sha in BRUTE_SOURCE_FREEZE_062;
  GS_ref: REFERENCE_062 on block main: sha bound, 0 mismatches, complete within 1800 s on 8 workers, 20/20 mutations (vacuous only if
     nothing is decided);
  G_recount: RECOUNT_062 bound and PASS; GTEST: gated modules of TEST_SUITE_062 pass;
  G_PROC: preregistration_062, budget_probe_062, build_authorization_062, seedcheck_062, prefreeze_smoke_062, deviation_198,
     freeze_062, main_run_062 as a subsequence, parseable non-decreasing note times, commit-order file, main sealed;
  G_RT: verify_release_0590 at release (not gated here).
  certified_readbits2_N20_windows: every gate passes; sound_no_2bit_gain: every gate except GW62 passes.
  status_phrase (plan status_wording_rule): 'certified (read_bits 2, N <= 20, windows)' / 'sound but no 2-bit gain' /
  'not certified, no certification status (failing gates: ...)'. Secondary (reported): CLIQUE62, GCOST62, GSTATS62, SEEDCHECK62, PROBE62.
  PYTHONPATH=. python scripts/make_gates_062.py [--study-dir D] [--check]"""
from __future__ import annotations
import argparse,json,sys
from math import comb
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common import load,dumps,write_new,check,sha
from experiments.brute_common_026 import wilson
from scripts.make_gates_034 import opt
from scripts.make_gates_043 import subseq

STUDY_DIR=ROOT/'results/study-062';ARMS=('B2','W2','W2b')
LABELS=('ID','IDF','AMB','WRONG','IDU','NOFIT');SOFT=('GW62',);REF_BUDGET=1800.0
min_w=lambda n:-(-4*n//12);min_d=lambda n:-(-3*n//12)
PROC_ORDER=('preregistration_062','budget_probe_062','build_authorization_062','seedcheck_062','prefreeze_smoke_062','deviation_198','freeze_062','main_run_062')


def ckey(c):return f"{c['block']}/{c['key']}/{c['seed']}"


def mcnemar_exact(b,c):
    """Two-sided exact McNemar p (binomial, p = 1/2, on the b + c discordant pairs); 1.0 if there are none."""
    n=b+c
    if n==0:return 1.0
    return min(1.0,2*sum(comb(n,i) for i in range(min(b,c)+1))/2**n)


def ledger():
    from datetime import datetime
    L=[json.loads(x) for x in (ROOT/'results/RESEARCH_LEDGER.jsonl').read_text().splitlines() if x.strip()]
    i0=next((i for i,e in enumerate(L) if e.get('event')=='preregistration_062'),None);out=[]
    for e in (L[i0:] if i0 is not None else []):
        try:t=datetime.fromisoformat(str(e.get('note',''))[:25])
        except ValueError:t=None
        out.append((e['event'],t))
        if e['event']==PROC_ORDER[-1]:break
    return out


def status_phrase(certified,sound_only,failed):
    if certified:return 'certified (read_bits 2, N <= 20, windows)'
    if sound_only:return 'sound but no 2-bit gain'
    return 'not certified, no certification status (failing gates: '+', '.join(failed)+')'


def build(study=STUDY_DIR,expect=None):
    from brute.evaluation import no_time
    from experiments.brute_study_062 import canon62,N_SEEDS,N_W2B
    study=Path(study);D=study/'main';Gt={};sec={}
    seal=opt(D/'SEAL.json');sci=opt(D/'SCIENTIFIC.json');res=opt(D/'RESULTS.json');rc=opt(D/'RECOUNT_062.json')
    ref=opt(D/'REFERENCE_062.json');ts=opt(study/'TEST_SUITE_062.json');order=opt(ROOT/'experiments/COMMIT_ORDER_062.json')
    api=opt(study/'API_CHECKS_062.json');fz=opt(ROOT/'experiments/BRUTE_SOURCE_FREEZE_062.json')
    sc=opt(ROOT/'results/diag-062/SEEDCHECK_062.json')
    rsha=sha(D/'RESULTS.json') if (D/'RESULTS.json').exists() else None
    sealed=(bool(seal) and res is not None and sci is not None and rsha==seal.get('results_sha256')
            and sha(D/'SCIENTIFIC.json')==seal.get('scientific_sha256') and no_time(res)==sci)
    if expect is not None:n,nb=expect
    else:n=int((res or {}).get('n_seeds',N_SEEDS));nb=int((res or {}).get('n_w2b',N_W2B))
    cs=sorted([c for c in (res or {}).get('cases',[]) if c['block']=='main' and c['key']=='scale20w2'],key=lambda c:c['seed']) if sealed else []
    bseeds={c['seed'] for c in cs[:nb]}
    want=lambda c:('B2','W2','W2b') if c['seed'] in bseeds else ('B2','W2')
    arms_ok=all(sorted(c['arms'])==sorted(want(c)) for c in cs)
    nall=len([c for c in (res or {}).get('cases',[]) if c['block']=='main']) if sealed else 0
    complete=sealed and seal.get('complete') is True and len(cs)==n==nall and arms_ok and sum('W2b' in c['arms'] for c in cs)==nb
    wb=None if complete else 'INCOMPLETE_INPUT (main missing, partial, missing arms or not matching its seal)'
    def gate(name,ok,obs,why=None):Gt[name]={'pass':bool(ok) and why is None,'observed':obs,**({'reason':why} if why else {})}
    pc=(rc or {}).get('per_case') or {}
    rc_bound=bool(rc) and rc.get('results_sha256')==rsha and rc.get('cases')==len((res or {}).get('cases',[]))
    rc_ok=rc_bound and rc.get('PASS') is True and not rc.get('mismatches')
    rget=lambda c,a,f:((pc.get(str(c['seed'])) or {}).get(a) or {}).get(f)
    lab=(lambda c,a:rget(c,a,'label')) if rc_ok else (lambda c,a:c['arms'][a]['label'])
    lsrc='recount' if rc_ok else 'study labels (G_recount did not pass)'
    dd=lambda c,a:a in c['arms'] and lab(c,a) in ('ID','IDF')
    ci=lambda x,m:wilson(x,m) if m else None
    wrong=[[ckey(c),a] for c in cs for a in c['arms'] if lab(c,a)=='WRONG' or c['arms'][a]['label']=='WRONG']
    gate('GS62_sound',complete and not wrong,{'WRONG':wrong,'records':sum(len(c['arms']) for c in cs),
         'per_case':[[c['seed']]+[lab(c,a) if a in c['arms'] else None for a in ARMS] for c in cs],'columns':['seed']+list(ARMS),
         'label_source':lsrc},why=wb)
    xw=sum(dd(c,'W2') for c in cs);xb=sum(dd(c,'B2') for c in cs);xwb=sum(dd(c,'W2b') for c in cs if 'W2b' in c['arms']);m=len(cs)
    b_=sum(dd(c,'W2') and not dd(c,'B2') for c in cs);c_=sum(dd(c,'B2') and not dd(c,'W2') for c in cs)
    gate('GW62',complete and xw>=min_w(n) and xw-xb>=min_d(n),{'W2_ID_IDF':xw,'B2_ID_IDF':xb,'of':m,'ci95_W2':ci(xw,m),'ci95_B2':ci(xb,m),
         'W2_minus_B2':xw-xb,'discordant_W2_only':b_,'discordant_B2_only':c_,'mcnemar_exact_p':mcnemar_exact(b_,c_),'W2b_ID_IDF_reported':xwb,
         'rule':f'W2 ID+IDF >= {min_w(n)} of {n} AND W2 - B2 >= {min_d(n)} (plan 4 of 12 and 3; scaled ceil(4n/12), ceil(3n/12) by #198)','label_source':lsrc},why=wb)
    det=[[c['seed'],canon62(c['arms']['W2'])==canon62(c['arms']['W2b']),c['arms']['W2']['label'],c['arms']['W2b']['label']] for c in cs if 'W2b' in c['arms']]
    kills=[[ckey(c),an,ar.get('guard_events')] for c in cs for an,ar in c['arms'].items() if an in ('W2','W2b') and ar.get('wall_guard')]
    killsB=[[ckey(c),'B2',c['arms']['B2'].get('guard_events')] for c in cs if c['arms']['B2'].get('wall_guard')]
    ndt=sum(x[1] for x in det)
    gate('GDET62',complete and ndt==nb and len(det)==nb and not kills,{'identical':ndt,'of':len(det),'ci95':ci(ndt,len(det)),'wall_guard_firings_W2_W2b':kills,
         'wall_guard_firings_B2_reported':killsB,'per_case':det,'columns':['seed','canon62_equal','W2','W2b']},why=wb)
    fi=(api or {}).get('fidelity') or {};eq=(api or {}).get('equiv') or {}
    ndec=sum(dd(c,a) for c in cs for a in c['arms'])
    fi_ok=bool(fi) and fi.get('study_results_sha256')==rsha and fi.get('PASS') is True and fi.get('exact')==fi.get('decided_records')==ndec
    gh=(api or {}).get('ghost') or {}
    gate('GFID62',complete and fi_ok and eq.get('PASS') is True and gh.get('network_pass') is True,{'no_network_run':gh.get('no_network_run'),
         'equiv_cases':eq.get('cases'),'refusals':eq.get('refusals'),'windows_appended_total':eq.get('windows_appended_total'),'fidelity_exact':fi.get('exact'),
         'of_decided':fi.get('decided_records'),'decided_in_gates':ndec,'vacuous':fi.get('vacuous'),'bound':bool(fi) and fi.get('study_results_sha256')==rsha,
         'failures':{k:v for k,v in (fi.get('per_case') or {}).items() if not v['exact']}},
         why=wb or (None if fi else 'INCOMPLETE_INPUT (API_CHECKS_062 fidelity missing)'))
    ct=sha(ROOT/'brute/api/certify20w.py');f62=(fz or {}).get('sha256_files',{}).get('brute/api/certify20w.py')
    abound=bool(api) and api.get('certify20w_sha256')==ct==f62
    gate('GHOST62',abound and gh.get('PASS62') is True,None if not api else {'bound_to_freeze_062':abound,'static_ok':gh.get('certify20w_static_ok'),
         'ast_scan':gh.get('certify20w_ast_scan'),'frozen_api_unchanged':gh.get('frozen_api_unchanged'),'a16d_max_bound_unpatched':gh.get('a16d_max_bound_unpatched'),
         'socket_attempts':gh.get('socket_attempts'),'no_network_run':gh.get('no_network_run')},
         why=None if api else 'INCOMPLETE_INPUT (API_CHECKS_062 missing)')
    mt=(ref or {}).get('mutation_test') or {};rb=bool(ref) and ref.get('study_results_sha256')==rsha and ref.get('block')=='main'
    robs=None if not ref else {k:ref.get(k) for k in ('block','scope','records','decided','audited','not_audited','complete','per_arm','not_reached',
                               'k_spent_as_amb','verdicts_checked','mismatch_count','misfires','vacuous','PASS','elapsed_informational')}|{'mutations':mt.get('detected'),'of':mt.get('mutations')}
    gate('GS_ref',rb and ref.get('mismatch_count')==0 and ref.get('complete') is True and (ref.get('scope') or {}).get('budget_s')==REF_BUDGET
         and (ref.get('vacuous') is True or mt.get('detected')==mt.get('mutations')==20) and ref.get('PASS') is True,robs,
         why=wb or (None if ref else 'INCOMPLETE_INPUT (REFERENCE_062 missing)'))
    gate('G_recount',complete and rc_ok,None if not rc else {k:rc.get(k) for k in ('cases','records','decided_by_arm','study_decided_by_arm','wrong','mismatches','PASS')},
         why=wb or (None if rc else 'INCOMPLETE_INPUT (RECOUNT_062 missing)'))
    mods=(ts or {}).get('per_module') or {};gm=(ts or {}).get('gated_modules') or []
    gate('GTEST',bool(gm) and ts.get('passed') is True and all(mods[x].get('returncode')==0 for x in gm),
         None if not ts else {'gated':{x:{'returncode':mods[x].get('returncode'),'tests':mods[x].get('tests')} for x in gm},
                              'reported':{x:{'returncode':v.get('returncode'),'tests':v.get('tests')} for x,v in mods.items() if x not in gm}},
         why=None if ts else 'INCOMPLETE_INPUT (TEST_SUITE_062 missing)')
    lt=ledger();ev=[e for e,_ in lt];times=[t for _,t in lt]
    proc={'order':subseq(ev,PROC_ORDER),'ledger_times_parse':bool(lt) and all(t is not None for t in times),
          'ledger_times_non_decreasing':all(a<=b for a,b in zip(times,times[1:]) if a and b),'commit_order_file':order is not None,'main_sealed':bool(sealed)}
    gate('G_PROC',all(proc.values()),{'clauses':proc,'events':ev,'required_order':list(PROC_ORDER)})
    row=lambda c,a:[lab(c,a),c['arms'][a]['n_min'],len(c['arms'][a]['extra_acts']),c['arms'][a]['n_rounds'],c['arms'][a]['conflicts_spent']]
    sec['GSTATS62']={'pass':None,'observed':[[c['seed']]+[row(c,a) for a in c['arms']] for c in cs],
                     'columns':['seed','per arm [label, n_min, extra_actions, rounds, conflicts]'],'rule':'reported'}
    cl=[[c['seed'],c['arms']['B2']['clique_prefix'],c['arms']['B2']['clique_final'],c['arms']['W2']['clique_final']] for c in cs]
    sec['CLIQUE62']={'pass':None,'observed':{'per_case':cl,'columns':['seed','prefix','B2_final','W2_final'],
                     'W2_gt_B2':sum(x[3]>x[2] for x in cl),'W2_eq_B2':sum(x[3]==x[2] for x in cl),'of':len(cl)},
                     'rule':'reported (H5): greedy apartness clique of the final trace, frozen apart_matrix / greedy_clique'}
    cost={}
    for c in cs:
        for a,ar in c['arms'].items():
            x=cost.setdefault(a,{'records':0,'wall_s':0.0,'conflicts':0,'chunks':0,'steps':0,'budget_spent':0,'decided_conflicts':[]})
            x['records']+=1;x['wall_s']+=ar.get('case_wall_informational') or 0.0;x['conflicts']+=ar.get('conflicts_spent') or 0
            x['chunks']+=ar.get('chunks_total') or 0;x['steps']+=len(ar.get('extra_acts') or []);x['budget_spent']+=(ar.get('conflicts_spent') or 0)>=ar['budget_conflicts']
            if dd(c,a):x['decided_conflicts'].append(ar.get('conflicts_spent'))
    for x in cost.values():x['wall_s']=round(x['wall_s'],1);x['decided_conflicts'].sort()
    sec['GCOST62']={'pass':None,'observed':cost,'elapsed_s':(res or {}).get('total_elapsed_informational'),'rule':'reported (walls informational)'}
    sc_frozen=bool(sc) and (fz or {}).get('sha256_files',{}).get('results/diag-062/SEEDCHECK_062.json')==sha(ROOT/'results/diag-062/SEEDCHECK_062.json')
    sec['SEEDCHECK62']={'pass':None,'observed':None if not sc else {'seedcheck_pass':sc.get('PASS'),'frozen_in_062':sc_frozen}}
    pr=opt(ROOT/'results/diag-062/BUDGET_PROBE_062.json')
    sec['PROBE62']={'pass':None,'observed':None if not pr else {'B62':pr.get('B62'),'B62_rule_met':pr.get('B62_rule_met'),'summary':pr.get('summary')},'rule':'exploratory, non-fresh seeds; not gate evidence'}
    fl={}
    for a in ARMS:
        cc=[c for c in cs if a in c['arms']];fl[a]={L:{'x':sum(lab(c,a)==L for c in cc),'n':len(cc),'ci95':ci(sum(lab(c,a)==L for c in cc),len(cc))} for L in LABELS}
    ok=all(g['pass'] for g in Gt.values())
    sound_only=not ok and all(g['pass'] for k,g in Gt.items() if k not in SOFT)
    failed=[k for k,g in Gt.items() if g['pass'] is False]
    return {'schema':'brute.gates.v59_0','study':(res or {}).get('plan',{}).get('study'),'process':'lean',
            'sealed_input_verified':sealed,'label_source':lsrc,'n_seeds':n,'n_w2b':nb,'caps':(res or {}).get('caps'),
            'workers':(res or {}).get('workers'),'stop':(res or {}).get('stop'),'arm_spec':(res or {}).get('arm_spec'),'probe_word':(res or {}).get('probe_word'),
            'gates':Gt,'secondary':sec,'all_gated_pass':ok,'failed':failed,'not_exercised':[],
            'certified_readbits2_N20_windows':ok,'sound_no_2bit_gain':sound_only,'status_phrase':status_phrase(ok,sound_only,failed),
            'framing':'BACK ON THE HARD PROBLEM: 2-bit readings at 20 states; a policy change (probe-word windows, certify/20w) against the budget-matched frozen certify/20b, declared N 20',
            'claim':('certify/20w and certify/20b ID/IDF are exact conditional on noise-free readings and on true size <= the declared N (here N <= 20). IDF identifies the '
                     'machine from the current state, not the start. Inferred reason the size condition is needed: a larger machine can copy the true machine on every visited state'),
            'reports':{'labels':fl} if cs else {}}


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--study-dir',default=str(STUDY_DIR));ap.add_argument('--check',action='store_true');a=ap.parse_args()
    obj=build(Path(a.study_dir));out=Path(a.study_dir)/'GATES_062.json'
    if a.check:check(out.read_bytes()==dumps(obj),'GATES_062.json does not reproduce');print('GATES_062 reproduces')
    else:write_new(out,obj);print(json.dumps({k:v['pass'] for k,v in obj['gates'].items()}),obj['failed'])
