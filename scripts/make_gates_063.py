"""Gates for study-063 (BRUTE_PLAN_063 criteria; pre-run deviation #200 definitions), LEAN process. Committed in the source freeze
before main_run_063; nothing is tuned after results are seen. New file; built from scripts/make_gates_062.py (frozen).
HONEST FRAMING (plan honest_framing): BACK ON THE HARD PROBLEM (2-bit readings at 20 states). A POOL change (certify/20p anchors the
symmetry-breaking clique on an exact max apartness clique and re-pins when it grows), not a new action policy; B2 is the
budget-matched frozen certify/20b control at the same B 8M.
Inputs (D = results/study-063): D/main/{RESULTS,SCIENTIFIC,SEAL}.json, D/main/RECOUNT_063.json, D/main/REFERENCE_063.json,
D/API_CHECKS_063.json, D/TEST_SUITE_063.json, results/diag-063/SEEDCHECK_063.json, experiments/COMMIT_ORDER_063.json,
results/RESEARCH_LEDGER.jsonl. Missing or partial input => every data gate FAIL INCOMPLETE_INPUT. Records are accepted only if
sha256(RESULTS) equals the seal and no_time(RESULTS) equals SCIENTIFIC. Labels: recounted if G_recount63 passes, else the study's.
Arms (worlds_058 scale20, read_bits 2, bound 20, noise-free, B 8M): B2 (certify/20b), P2 (certify/20p, node cap 200000),
P2b (P2 on the first n_p2b seeds, reversed order). n = n_seeds.
  GS63_sound: WRONG 0 on every record of B2, P2 and P2b;
  GP63 (headline): P2 ID+IDF >= ceil(3 n / 8) AND (P2 - B2) >= ceil(2 n / 8) on the same seeds (plan 3 of 8 and 2; 3 and 2 at
     n = 6 too, if the #200 seed cut fires); Wilson 95% CIs and the exact two-sided McNemar p reported;
  GDET63: canon63(P2) == canon63(P2b) on every P2b seed (n_p2b of n_p2b), 0 wall-guard firings in P2 and P2b (B2 reported);
  GFID63: API_CHECKS_063 equiv (certify/20p sound against the true machine and agreeing with certify/20b where both decide, on small
     worlds; refusals), the no-network run (0 socket attempts) and replay fidelity exact on every decided record, bound to the
     sealed RESULTS sha;
  GHOST63: API_CHECKS_063 ghost PASS63 (closure scan, AST scan of certify20p, frozen api shas vs FREEZE_062, certify16d bound
     unpatched, no network), with certify20p.py's sha equal to its sha in BRUTE_SOURCE_FREEZE_063;
  GS_ref63: REFERENCE_063 on block main: sha bound, 0 mismatches, complete within 1800 s on 8 workers, 20/20 mutations (vacuous only
     if nothing is decided);
  G_recount63: RECOUNT_063 bound and PASS; GTEST63: gated modules of TEST_SUITE_063 pass;
  G_PROC63: preregistration_063, build_authorization_063, seedcheck_063, prefreeze_smoke_063, deviation_200, freeze_063,
     main_run_063 as a subsequence, parseable non-decreasing note times, commit-order file, main sealed;
  G_RT: verify_release_0600 at release (not gated here).
  certified_readbits2_N20_clique: every gate passes; sound_no_2bit_gain: every gate except GP63 passes.
  status_phrase (plan status_wording_rule): 'certified (read_bits 2, N <= 20, clique-anchored)' / 'sound but no 2-bit gain' /
  'not certified, no certification status (failing gates: ...)'. Secondary (reported): CLIQUE63, GCOST63, GSTATS63, SEEDCHECK63, PROBE63.
  PYTHONPATH=. python scripts/make_gates_063.py [--study-dir D] [--check]"""
from __future__ import annotations
import argparse,json,sys
from math import comb
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common import load,dumps,write_new,check,sha
from experiments.brute_common_026 import wilson
from scripts.make_gates_034 import opt
from scripts.make_gates_043 import subseq

STUDY_DIR=ROOT/'results/study-063';ARMS=('B2','P2','P2b')
LABELS=('ID','IDF','AMB','WRONG','IDU','NOFIT');SOFT=('GP63',);REF_BUDGET=1800.0
min_w=lambda n:-(-3*n//8);min_d=lambda n:-(-2*n//8)
PROC_ORDER=('preregistration_063','build_authorization_063','seedcheck_063','prefreeze_smoke_063','deviation_200','freeze_063','main_run_063')


def ckey(c):return f"{c['block']}/{c['key']}/{c['seed']}"


def mcnemar_exact(b,c):
    """Two-sided exact McNemar p (binomial, p = 1/2, on the b + c discordant pairs); 1.0 if there are none."""
    n=b+c
    if n==0:return 1.0
    return min(1.0,2*sum(comb(n,i) for i in range(min(b,c)+1))/2**n)


def ledger():
    from datetime import datetime
    L=[json.loads(x) for x in (ROOT/'results/RESEARCH_LEDGER.jsonl').read_text().splitlines() if x.strip()]
    i0=next((i for i,e in enumerate(L) if e.get('event')=='preregistration_063'),None);out=[]
    for e in (L[i0:] if i0 is not None else []):
        try:t=datetime.fromisoformat(str(e.get('note',''))[:25])
        except ValueError:t=None
        out.append((e['event'],t))
        if e['event']==PROC_ORDER[-1]:break
    return out


def status_phrase(certified,sound_only,failed):
    if certified:return 'certified (read_bits 2, N <= 20, clique-anchored)'
    if sound_only:return 'sound but no 2-bit gain'
    return 'not certified, no certification status (failing gates: '+', '.join(failed)+')'


def build(study=STUDY_DIR,expect=None):
    from brute.evaluation import no_time
    from experiments.brute_study_063 import canon63,N_SEEDS,N_P2B
    study=Path(study);D=study/'main';Gt={};sec={}
    seal=opt(D/'SEAL.json');sci=opt(D/'SCIENTIFIC.json');res=opt(D/'RESULTS.json');rc=opt(D/'RECOUNT_063.json')
    ref=opt(D/'REFERENCE_063.json');ts=opt(study/'TEST_SUITE_063.json');order=opt(ROOT/'experiments/COMMIT_ORDER_063.json')
    api=opt(study/'API_CHECKS_063.json');fz=opt(ROOT/'experiments/BRUTE_SOURCE_FREEZE_063.json')
    sc=opt(ROOT/'results/diag-063/SEEDCHECK_063.json')
    rsha=sha(D/'RESULTS.json') if (D/'RESULTS.json').exists() else None
    sealed=(bool(seal) and res is not None and sci is not None and rsha==seal.get('results_sha256')
            and sha(D/'SCIENTIFIC.json')==seal.get('scientific_sha256') and no_time(res)==sci)
    if expect is not None:n,nb=expect
    else:n=int((res or {}).get('n_seeds',N_SEEDS));nb=int((res or {}).get('n_p2b',N_P2B))
    cs=sorted([c for c in (res or {}).get('cases',[]) if c['block']=='main' and c['key']=='scale20p2'],key=lambda c:c['seed']) if sealed else []
    bseeds={c['seed'] for c in cs[:nb]}
    want=lambda c:('B2','P2','P2b') if c['seed'] in bseeds else ('B2','P2')
    arms_ok=all(sorted(c['arms'])==sorted(want(c)) for c in cs)
    nall=len([c for c in (res or {}).get('cases',[]) if c['block']=='main']) if sealed else 0
    complete=sealed and seal.get('complete') is True and len(cs)==n==nall and arms_ok and sum('P2b' in c['arms'] for c in cs)==nb
    wb=None if complete else 'INCOMPLETE_INPUT (main missing, partial, missing arms or not matching its seal)'
    def gate(name,ok,obs,why=None):Gt[name]={'pass':bool(ok) and why is None,'observed':obs,**({'reason':why} if why else {})}
    pc=(rc or {}).get('per_case') or {}
    rc_bound=bool(rc) and rc.get('results_sha256')==rsha and rc.get('cases')==len((res or {}).get('cases',[]))
    rc_ok=rc_bound and rc.get('PASS') is True and not rc.get('mismatches')
    rget=lambda c,a,f:((pc.get(str(c['seed'])) or {}).get(a) or {}).get(f)
    lab=(lambda c,a:rget(c,a,'label')) if rc_ok else (lambda c,a:c['arms'][a]['label'])
    lsrc='recount' if rc_ok else 'study labels (G_recount63 did not pass)'
    dd=lambda c,a:a in c['arms'] and lab(c,a) in ('ID','IDF')
    ci=lambda x,m:wilson(x,m) if m else None
    wrong=[[ckey(c),a] for c in cs for a in c['arms'] if lab(c,a)=='WRONG' or c['arms'][a]['label']=='WRONG']
    gate('GS63_sound',complete and not wrong,{'WRONG':wrong,'records':sum(len(c['arms']) for c in cs),
         'per_case':[[c['seed']]+[lab(c,a) if a in c['arms'] else None for a in ARMS] for c in cs],'columns':['seed']+list(ARMS),
         'label_source':lsrc},why=wb)
    xw=sum(dd(c,'P2') for c in cs);xb=sum(dd(c,'B2') for c in cs);xwb=sum(dd(c,'P2b') for c in cs if 'P2b' in c['arms']);m=len(cs)
    b_=sum(dd(c,'P2') and not dd(c,'B2') for c in cs);c_=sum(dd(c,'B2') and not dd(c,'P2') for c in cs)
    gate('GP63',complete and xw>=min_w(n) and xw-xb>=min_d(n),{'P2_ID_IDF':xw,'B2_ID_IDF':xb,'of':m,'ci95_P2':ci(xw,m),'ci95_B2':ci(xb,m),
         'P2_minus_B2':xw-xb,'discordant_P2_only':b_,'discordant_B2_only':c_,'mcnemar_exact_p':mcnemar_exact(b_,c_),'P2b_ID_IDF_reported':xwb,
         'rule':f'P2 ID+IDF >= {min_w(n)} of {n} AND P2 - B2 >= {min_d(n)} (plan 3 of 8 and 2; scaled ceil(3n/8), ceil(2n/8) by #200)','label_source':lsrc},why=wb)
    det=[[c['seed'],canon63(c['arms']['P2'])==canon63(c['arms']['P2b']),c['arms']['P2']['label'],c['arms']['P2b']['label']] for c in cs if 'P2b' in c['arms']]
    kills=[[ckey(c),an,ar.get('guard_events')] for c in cs for an,ar in c['arms'].items() if an in ('P2','P2b') and ar.get('wall_guard')]
    killsB=[[ckey(c),'B2',c['arms']['B2'].get('guard_events')] for c in cs if c['arms']['B2'].get('wall_guard')]
    ndt=sum(x[1] for x in det)
    gate('GDET63',complete and ndt==nb and len(det)==nb and not kills,{'identical':ndt,'of':len(det),'ci95':ci(ndt,len(det)),'wall_guard_firings_P2_P2b':kills,
         'wall_guard_firings_B2_reported':killsB,'per_case':det,'columns':['seed','canon63_equal','P2','P2b']},why=wb)
    fi=(api or {}).get('fidelity') or {};eq=(api or {}).get('equiv') or {}
    ndec=sum(dd(c,a) for c in cs for a in c['arms'])
    fi_ok=bool(fi) and fi.get('study_results_sha256')==rsha and fi.get('PASS') is True and fi.get('exact')==fi.get('decided_records')==ndec
    gh=(api or {}).get('ghost') or {}
    gate('GFID63',complete and fi_ok and eq.get('PASS') is True and gh.get('network_pass') is True,{'no_network_run':gh.get('no_network_run'),
         'equiv_cases':eq.get('cases'),'refusals':eq.get('refusals'),'agree_with_20b':eq.get('agree_with_20b'),'sound_vs_truth':eq.get('sound_vs_truth'),'fidelity_exact':fi.get('exact'),
         'of_decided':fi.get('decided_records'),'decided_in_gates':ndec,'vacuous':fi.get('vacuous'),'bound':bool(fi) and fi.get('study_results_sha256')==rsha,
         'failures':{k:v for k,v in (fi.get('per_case') or {}).items() if not v['exact']}},
         why=wb or (None if fi else 'INCOMPLETE_INPUT (API_CHECKS_063 fidelity missing)'))
    ct=sha(ROOT/'brute/api/certify20p.py');f63=(fz or {}).get('sha256_files',{}).get('brute/api/certify20p.py')
    abound=bool(api) and api.get('certify20p_sha256')==ct==f63
    gate('GHOST63',abound and gh.get('PASS63') is True,None if not api else {'bound_to_freeze_063':abound,'static_ok':gh.get('certify20p_static_ok'),
         'ast_scan':gh.get('certify20p_ast_scan'),'frozen_api_unchanged':gh.get('frozen_api_unchanged'),'a16d_max_bound_unpatched':gh.get('a16d_max_bound_unpatched'),
         'socket_attempts':gh.get('socket_attempts'),'no_network_run':gh.get('no_network_run')},
         why=None if api else 'INCOMPLETE_INPUT (API_CHECKS_063 missing)')
    mt=(ref or {}).get('mutation_test') or {};rb=bool(ref) and ref.get('study_results_sha256')==rsha and ref.get('block')=='main'
    robs=None if not ref else {k:ref.get(k) for k in ('block','scope','records','decided','audited','not_audited','complete','per_arm','not_reached',
                               'k_spent_as_amb','verdicts_checked','mismatch_count','misfires','vacuous','PASS','elapsed_informational')}|{'mutations':mt.get('detected'),'of':mt.get('mutations')}
    gate('GS_ref63',rb and ref.get('mismatch_count')==0 and ref.get('complete') is True and (ref.get('scope') or {}).get('budget_s')==REF_BUDGET
         and (ref.get('vacuous') is True or mt.get('detected')==mt.get('mutations')==20) and ref.get('PASS') is True,robs,
         why=wb or (None if ref else 'INCOMPLETE_INPUT (REFERENCE_063 missing)'))
    gate('G_recount63',complete and rc_ok,None if not rc else {k:rc.get(k) for k in ('cases','records','decided_by_arm','study_decided_by_arm','wrong','mismatches','PASS')},
         why=wb or (None if rc else 'INCOMPLETE_INPUT (RECOUNT_063 missing)'))
    mods=(ts or {}).get('per_module') or {};gm=(ts or {}).get('gated_modules') or []
    gate('GTEST63',bool(gm) and ts.get('passed') is True and all(mods[x].get('returncode')==0 for x in gm),
         None if not ts else {'gated':{x:{'returncode':mods[x].get('returncode'),'tests':mods[x].get('tests')} for x in gm},
                              'reported':{x:{'returncode':v.get('returncode'),'tests':v.get('tests')} for x,v in mods.items() if x not in gm}},
         why=None if ts else 'INCOMPLETE_INPUT (TEST_SUITE_063 missing)')
    lt=ledger();ev=[e for e,_ in lt];times=[t for _,t in lt]
    proc={'order':subseq(ev,PROC_ORDER),'ledger_times_parse':bool(lt) and all(t is not None for t in times),
          'ledger_times_non_decreasing':all(a<=b for a,b in zip(times,times[1:]) if a and b),'commit_order_file':order is not None,'main_sealed':bool(sealed)}
    gate('G_PROC63',all(proc.values()),{'clauses':proc,'events':ev,'required_order':list(PROC_ORDER)})
    row=lambda c,a:[lab(c,a),c['arms'][a]['n_min'],len(c['arms'][a]['extra_acts']),c['arms'][a]['n_rounds'],c['arms'][a]['conflicts_spent']]
    sec['GSTATS63']={'pass':None,'observed':[[c['seed']]+[row(c,a) for a in c['arms']] for c in cs],
                     'columns':['seed','per arm [label, n_min, extra_actions, rounds, conflicts]'],'rule':'reported'}
    cl=[[c['seed'],c['arms']['B2']['clique_prefix'],c['arms']['B2']['clique_final'],c['arms']['P2']['clique_final'],c['arms']['P2'].get('clique_size'),
         len(c['arms']['P2'].get('final_clique') or []),len(c['arms']['P2'].get('repins') or [])] for c in cs]
    sec['CLIQUE63']={'pass':None,'observed':{'per_case':cl,'columns':['seed','greedy_prefix','B2_greedy_final','P2_greedy_final','P2_anchor_clique_size',
                     'P2_final_clique_len','P2_pins'],'of':len(cl)},
                     'rule':'reported: exact anchor clique size and pin count from certify/20p; greedy apartness cliques from frozen apart_matrix / greedy_clique'}
    cost={}
    for c in cs:
        for a,ar in c['arms'].items():
            x=cost.setdefault(a,{'records':0,'wall_s':0.0,'conflicts':0,'chunks':0,'steps':0,'budget_spent':0,'decided_conflicts':[]})
            x['records']+=1;x['wall_s']+=ar.get('case_wall_informational') or 0.0;x['conflicts']+=ar.get('conflicts_spent') or 0
            x['chunks']+=ar.get('chunks_total') or 0;x['steps']+=len(ar.get('extra_acts') or []);x['budget_spent']+=(ar.get('conflicts_spent') or 0)>=ar['budget_conflicts']
            if dd(c,a):x['decided_conflicts'].append(ar.get('conflicts_spent'))
    for x in cost.values():x['wall_s']=round(x['wall_s'],1);x['decided_conflicts'].sort()
    sec['GCOST63']={'pass':None,'observed':cost,'elapsed_s':(res or {}).get('total_elapsed_informational'),'rule':'reported (walls informational)'}
    sc_frozen=bool(sc) and (fz or {}).get('sha256_files',{}).get('results/diag-063/SEEDCHECK_063.json')==sha(ROOT/'results/diag-063/SEEDCHECK_063.json')
    sec['SEEDCHECK63']={'pass':None,'observed':None if not sc else {'seedcheck_pass':sc.get('PASS'),'frozen_in_063':sc_frozen}}
    pr=opt(ROOT/'results/diag-063/CAPABILITY_PROBE_063.json')
    sec['PROBE63']={'pass':None,'observed':None if not pr else {k:pr.get(k) for k in ('summary','settings','seeds') if k in pr},'rule':'exploratory, sealed non-fresh seeds; not gate evidence'}
    fl={}
    for a in ARMS:
        cc=[c for c in cs if a in c['arms']];fl[a]={L:{'x':sum(lab(c,a)==L for c in cc),'n':len(cc),'ci95':ci(sum(lab(c,a)==L for c in cc),len(cc))} for L in LABELS}
    ok=all(g['pass'] for g in Gt.values())
    sound_only=not ok and all(g['pass'] for k,g in Gt.items() if k not in SOFT)
    failed=[k for k,g in Gt.items() if g['pass'] is False]
    return {'schema':'brute.gates.v60_0','study':(res or {}).get('plan',{}).get('study'),'process':'lean',
            'sealed_input_verified':sealed,'label_source':lsrc,'n_seeds':n,'n_p2b':nb,'caps':(res or {}).get('caps'),
            'workers':(res or {}).get('workers'),'stop':(res or {}).get('stop'),'arm_spec':(res or {}).get('arm_spec'),'node_cap':(res or {}).get('node_cap'),
            'gates':Gt,'secondary':sec,'all_gated_pass':ok,'failed':failed,'not_exercised':[],
            'certified_readbits2_N20_clique':ok,'sound_no_2bit_gain':sound_only,'status_phrase':status_phrase(ok,sound_only,failed),
            'framing':'BACK ON THE HARD PROBLEM: 2-bit readings at 20 states; a pool change (exact max-clique anchor, certify/20p) against the budget-matched frozen certify/20b, declared N 20',
            'claim':('certify/20p and certify/20b ID/IDF are exact conditional on noise-free readings and on true size <= the declared N (here N <= 20). IDF identifies the '
                     'machine from the current state, not the start. Inferred reason the size condition is needed: a larger machine can copy the true machine on every visited state'),
            'reports':{'labels':fl} if cs else {}}


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--study-dir',default=str(STUDY_DIR));ap.add_argument('--check',action='store_true');a=ap.parse_args()
    obj=build(Path(a.study_dir));out=Path(a.study_dir)/'GATES_063.json'
    if a.check:check(out.read_bytes()==dumps(obj),'GATES_063.json does not reproduce');print('GATES_063 reproduces')
    else:write_new(out,obj);print(json.dumps({k:v['pass'] for k,v in obj['gates'].items()}),obj['failed'])
