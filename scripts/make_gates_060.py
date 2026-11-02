"""Gates for study-060 (BRUTE_PLAN_060 criteria; pre-run deviation #194 definitions), LEAN process. Committed in the source freeze
before main_run_060; nothing is tuned after results are seen. New file; built from scripts/make_gates_059.py (frozen).
HONEST FRAMING (plan honest_framing): this study keeps the TARGET CHANGE (wide 4-bit readings on random emissions) and raises the
declared size to 24 (gated) and 32 (reported); 2-bit readings at 20 states stay Open whatever it shows.
Inputs (D = results/study-060): D/main/{RESULTS,SCIENTIFIC,SEAL}.json, D/main/RECOUNT_060.json, D/main/REFERENCE_060.json,
D/API_CHECKS_060.json, D/TEST_SUITE_060.json, results/diag-060/SEEDCHECK_060.json, experiments/COMMIT_ORDER_060.json,
results/RESEARCH_LEDGER.jsonl. Missing or partial input => every data gate FAIL INCOMPLETE_INPUT. Records are accepted only if
sha256(RESULTS) equals the seal and no_time(RESULTS) equals SCIENTIFIC. Labels: recounted if G_recount passes, else the study's.
Arms (certify/32b, read_bits 4, noise-free): S24 and S24b (scale24r4, bound 24; S24b in reversed seed order), S32 (scale32r4,
bound 32; decisions reported only).
  GS60_sound: WRONG 0 on every record of S24, S24b and S32 (NOFIT is a refusal, not WRONG);
  GN24_60 (soft): S24 ID+IDF >= 6 of n24 (Wilson CI);
  GDET60: canon60(S24) == canon60(S24b) on every scale24w seed, 0 wall-guard firings in S24 and S24b (S32 firings reported);
  GFID60: API_CHECKS_060 equiv (32b == 20b at bounds <= 20 on 18 small worlds, one-shot equal, bounds 21..32 accepted, bad bounds
     refused), the no-network run (0 socket attempts) and fidelity exact on every decided record, bound to the sealed RESULTS sha;
  GHOST60: API_CHECKS_060 ghost PASS60 (closure scan, frozen api shas vs FREEZE_059, certify16d bound unpatched, no network), bound
     to certify32b.py's sha in BRUTE_SOURCE_FREEZE_060;
  GS_ref: REFERENCE_060 on block main: sha bound, 0 mismatches, complete within 3600 s on 8 workers, 20/20 mutations (vacuous only if
     nothing is decided);
  G_recount: RECOUNT_060 bound and PASS; GTEST: gated modules of TEST_SUITE_060 pass;
  G_PROC: preregistration_060, build_authorization_060, seedcheck_060, prefreeze_smoke_060, deviation_194, freeze_060, main_run_060
     as a subsequence, parseable non-decreasing note times, commit-order file, main sealed;
  G_RT: verify_release_0570 at release (not gated here).
  certified_readbits4_N24: every gate passes; sound_not_certified_N24: every gate except GN24_60 passes.
  status_phrase: derived from the two flags. Secondary (reported): S32_report, GCOST60, GSTATS60, SEEDCHECK60.
  PYTHONPATH=. python scripts/make_gates_060.py [--study-dir D] [--check]"""
from __future__ import annotations
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common import load,dumps,write_new,check,sha
from experiments.brute_common_026 import wilson
from scripts.make_gates_034 import opt
from scripts.make_gates_043 import subseq

STUDY_DIR=ROOT/'results/study-060';ARMS=('S24','S24b','S32');ARMS_OF={'scale24w':('S24','S24b'),'scale32w':('S32',)}
LABELS=('ID','IDF','AMB','WRONG','IDU','NOFIT');MIN_N=6;SOFT=('GN24_60',);REF_BUDGET=3600.0
PROC_ORDER=('preregistration_060','build_authorization_060','seedcheck_060','prefreeze_smoke_060','deviation_194','freeze_060','main_run_060')


def ckey(c):return f"{c['block']}/{c['key']}/{c['seed']}"


def ledger():
    from datetime import datetime
    L=[json.loads(x) for x in (ROOT/'results/RESEARCH_LEDGER.jsonl').read_text().splitlines() if x.strip()]
    i0=next((i for i,e in enumerate(L) if e.get('event')=='preregistration_060'),None);out=[]
    for e in (L[i0:] if i0 is not None else []):
        try:t=datetime.fromisoformat(str(e.get('note',''))[:25])
        except ValueError:t=None
        out.append((e['event'],t))
        if e['event']==PROC_ORDER[-1]:break
    return out


def status_phrase(certified,sound_only,failed):
    if certified:return 'certified (read_bits 4, N <= 24)'
    if sound_only:return 'sound but not certified'
    return 'not certified, no certification status (failing gates: '+', '.join(failed)+')'


def build(study=STUDY_DIR,expect=None):
    from brute.evaluation import no_time
    from experiments.brute_study_060 import canon60,N24,N32
    study=Path(study);D=study/'main';Gt={};sec={}
    seal=opt(D/'SEAL.json');sci=opt(D/'SCIENTIFIC.json');res=opt(D/'RESULTS.json');rc=opt(D/'RECOUNT_060.json')
    ref=opt(D/'REFERENCE_060.json');ts=opt(study/'TEST_SUITE_060.json');order=opt(ROOT/'experiments/COMMIT_ORDER_060.json')
    api=opt(study/'API_CHECKS_060.json');fz=opt(ROOT/'experiments/BRUTE_SOURCE_FREEZE_060.json')
    sc=opt(ROOT/'results/diag-060/SEEDCHECK_060.json')
    rsha=sha(D/'RESULTS.json') if (D/'RESULTS.json').exists() else None
    sealed=(bool(seal) and res is not None and sci is not None and rsha==seal.get('results_sha256')
            and sha(D/'SCIENTIFIC.json')==seal.get('scientific_sha256') and no_time(res)==sci)
    if expect is not None:n24,n32=expect
    else:n24=int((res or {}).get('n24',N24));n32=int((res or {}).get('n32',N32))
    allc=sorted([c for c in (res or {}).get('cases',[]) if c['block']=='main'],key=lambda c:(c['key'],c['seed'])) if sealed else []
    c24=[c for c in allc if c['key']=='scale24w'];c32=[c for c in allc if c['key']=='scale32w']
    arms_ok=all(c['key'] in ARMS_OF and sorted(c['arms'])==sorted(ARMS_OF[c['key']]) for c in allc)
    complete=sealed and seal.get('complete') is True and len(c24)==n24 and len(c32)==n32 and arms_ok
    wb=None if complete else 'INCOMPLETE_INPUT (main missing, partial, missing arms or not matching its seal)'
    def gate(name,ok,obs,why=None):Gt[name]={'pass':bool(ok) and why is None,'observed':obs,**({'reason':why} if why else {})}
    pc=(rc or {}).get('per_case') or {}
    rc_bound=bool(rc) and rc.get('results_sha256')==rsha and rc.get('cases')==len((res or {}).get('cases',[]))
    rc_ok=rc_bound and rc.get('PASS') is True and not rc.get('mismatches')
    rget=lambda c,a,f:((pc.get(f"{c['key']}/{c['seed']}") or {}).get(a) or {}).get(f)
    lab=(lambda c,a:rget(c,a,'label')) if rc_ok else (lambda c,a:c['arms'][a]['label'])
    lsrc='recount' if rc_ok else 'study labels (G_recount did not pass)'
    dd=lambda c,a:a in c['arms'] and lab(c,a) in ('ID','IDF')
    ci=lambda x,m:wilson(x,m) if m else None
    wrong=[[ckey(c),a] for c in allc for a in c['arms'] if lab(c,a)=='WRONG' or c['arms'][a]['label']=='WRONG']
    gate('GS60_sound',complete and not wrong,{'WRONG':wrong,'records':sum(len(c['arms']) for c in allc),
         'per_case':[[c['key'],c['seed']]+[lab(c,a) if a in c['arms'] else None for a in ARMS] for c in allc],'columns':['key','seed']+list(ARMS),
         'label_source':lsrc},why=wb)
    x24=sum(dd(c,'S24') for c in c24);x24b=sum(dd(c,'S24b') for c in c24);x32=sum(dd(c,'S32') for c in c32);m=len(c24);m32=len(c32)
    gate('GN24_60',complete and x24>=MIN_N,{'S24_ID_IDF':x24,'of':m,'ci95_S24':ci(x24,m),'S24b_ID_IDF_reported':x24b,
         'rule':'S24 ID+IDF >= 6 of 12','label_source':lsrc},why=wb)
    det=[[c['seed'],canon60(c['arms']['S24'])==canon60(c['arms']['S24b']),c['arms']['S24']['label'],c['arms']['S24b']['label']] for c in c24]
    kills=[[ckey(c),an,ar.get('guard_events')] for c in c24 for an,ar in c['arms'].items() if ar.get('wall_guard')]
    kills32=[[ckey(c),an,ar.get('guard_events')] for c in c32 for an,ar in c['arms'].items() if ar.get('wall_guard')]
    ndt=sum(x[1] for x in det)
    gate('GDET60',complete and ndt==n24 and not kills,{'identical':ndt,'of':len(det),'ci95':ci(ndt,len(det)),'wall_guard_firings_S24':kills,
         'wall_guard_firings_S32_reported':kills32,'per_case':det,'columns':['seed','canon60_equal','S24','S24b']},why=wb)
    fi=(api or {}).get('fidelity') or {};eq=(api or {}).get('equiv') or {}
    ndec=sum(dd(c,a) for c in allc for a in c['arms'])
    fi_ok=bool(fi) and fi.get('study_results_sha256')==rsha and fi.get('PASS') is True and fi.get('exact')==fi.get('decided_records')==ndec
    gh=(api or {}).get('ghost') or {}
    gate('GFID60',complete and fi_ok and eq.get('PASS') is True and gh.get('network_pass') is True,{'no_network_run':gh.get('no_network_run'),
         'equiv_cases':eq.get('cases'),'accepted_bounds':eq.get('accepted_bounds'),'refusals':eq.get('refusals'),'fidelity_exact':fi.get('exact'),
         'of_decided':fi.get('decided_records'),'decided_in_gates':ndec,'vacuous':fi.get('vacuous'),'bound':bool(fi) and fi.get('study_results_sha256')==rsha,
         'failures':{k:v for k,v in (fi.get('per_case') or {}).items() if not v['exact']}},
         why=wb or (None if fi else 'INCOMPLETE_INPUT (API_CHECKS_060 fidelity missing)'))
    ct=sha(ROOT/'brute/api/certify32b.py');f60=(fz or {}).get('sha256_files',{}).get('brute/api/certify32b.py')
    abound=bool(api) and api.get('certify32b_sha256')==ct==f60
    gate('GHOST60',abound and gh.get('PASS60') is True,None if not api else {'bound_to_freeze_060':abound,'static_ok':gh.get('certify32b_static_ok'),
         'frozen_api_unchanged':gh.get('frozen_api_unchanged'),'a16d_max_bound_unpatched':gh.get('a16d_max_bound_unpatched'),
         'socket_attempts':gh.get('socket_attempts'),'no_network_run':gh.get('no_network_run')},
         why=None if api else 'INCOMPLETE_INPUT (API_CHECKS_060 missing)')
    mt=(ref or {}).get('mutation_test') or {};rb=bool(ref) and ref.get('study_results_sha256')==rsha and ref.get('block')=='main'
    robs=None if not ref else {k:ref.get(k) for k in ('block','scope','records','decided','audited','not_audited','complete','per_arm','not_reached',
                               'k_spent_as_amb','verdicts_checked','mismatch_count','misfires','vacuous','PASS','elapsed_informational')}|{'mutations':mt.get('detected'),'of':mt.get('mutations')}
    gate('GS_ref',rb and ref.get('mismatch_count')==0 and ref.get('complete') is True and (ref.get('scope') or {}).get('budget_s')==REF_BUDGET
         and (ref.get('vacuous') is True or mt.get('detected')==mt.get('mutations')==20) and ref.get('PASS') is True,robs,
         why=wb or (None if ref else 'INCOMPLETE_INPUT (REFERENCE_060 missing)'))
    gate('G_recount',complete and rc_ok,None if not rc else {k:rc.get(k) for k in ('cases','records','decided_by_arm','study_decided_by_arm','wrong_by_arm','mismatches','PASS')},
         why=wb or (None if rc else 'INCOMPLETE_INPUT (RECOUNT_060 missing)'))
    mods=(ts or {}).get('per_module') or {};gm=(ts or {}).get('gated_modules') or []
    gate('GTEST',bool(gm) and ts.get('passed') is True and all(mods[x].get('returncode')==0 for x in gm),
         None if not ts else {'gated':{x:{'returncode':mods[x].get('returncode'),'tests':mods[x].get('tests')} for x in gm},
                              'reported':{x:{'returncode':v.get('returncode'),'tests':v.get('tests')} for x,v in mods.items() if x not in gm}},
         why=None if ts else 'INCOMPLETE_INPUT (TEST_SUITE_060 missing)')
    lt=ledger();ev=[e for e,_ in lt];times=[t for _,t in lt]
    proc={'order':subseq(ev,PROC_ORDER),'ledger_times_parse':bool(lt) and all(t is not None for t in times),
          'ledger_times_non_decreasing':all(a<=b for a,b in zip(times,times[1:]) if a and b),'commit_order_file':order is not None,'main_sealed':bool(sealed)}
    gate('G_PROC',all(proc.values()),{'clauses':proc,'events':ev,'required_order':list(PROC_ORDER)})
    row=lambda c,a:[lab(c,a),c['arms'][a]['n_min'],c['arms'][a]['true_size'],len(c['arms'][a]['extra_acts']),c['arms'][a]['n_rounds'],c['arms'][a]['conflicts_spent']]
    sec['GSTATS60']={'pass':None,'observed':[[c['key'],c['seed']]+[row(c,a) for a in c['arms']] for c in allc],
                     'columns':['key','seed','per arm [label, n_min, true_size, extra_actions, rounds, conflicts]'],'rule':'reported'}
    sec['S32_report']={'pass':None,'observed':{'labels':{L:sum(lab(c,'S32')==L for c in c32) for L in LABELS},'ID_IDF':x32,'of':m32,
                       'ci95':ci(x32,m32),'wall_guard_firings':kills32},'rule':'reported; S32 decisions are not gated (expected Open at this budget)'}
    cost={}
    for c in allc:
        for a,ar in c['arms'].items():
            x=cost.setdefault(a,{'records':0,'wall_s':0.0,'conflicts':0,'chunks':0,'steps':0,'budget_spent':0,'decided_conflicts':[]})
            x['records']+=1;x['wall_s']+=ar.get('case_wall_informational') or 0.0;x['conflicts']+=ar.get('conflicts_spent') or 0
            x['chunks']+=ar.get('chunks_total') or 0;x['steps']+=len(ar.get('extra_acts') or []);x['budget_spent']+=(ar.get('conflicts_spent') or 0)>=ar['budget_conflicts']
            if dd(c,a):x['decided_conflicts'].append(ar.get('conflicts_spent'))
    for x in cost.values():x['wall_s']=round(x['wall_s'],1);x['decided_conflicts'].sort()
    sec['GCOST60']={'pass':None,'observed':cost,'elapsed_s':(res or {}).get('total_elapsed_informational'),'rule':'reported (walls informational)'}
    sc_frozen=bool(sc) and (fz or {}).get('sha256_files',{}).get('results/diag-060/SEEDCHECK_060.json')==sha(ROOT/'results/diag-060/SEEDCHECK_060.json')
    sec['SEEDCHECK60']={'pass':None,'observed':None if not sc else {'seedcheck_pass':sc.get('PASS'),'frozen_in_060':sc_frozen}}
    fl={}
    for a,cs in (('S24',c24),('S24b',c24),('S32',c32)):
        fl[a]={L:{'x':sum(lab(c,a)==L for c in cs),'n':len(cs),'ci95':ci(sum(lab(c,a)==L for c in cs),len(cs))} for L in LABELS}
    ok=all(g['pass'] for g in Gt.values())
    sound_only=not ok and all(g['pass'] for k,g in Gt.items() if k not in SOFT)
    failed=[k for k,g in Gt.items() if g['pass'] is False]
    return {'schema':'brute.gates.v57_0','study':(res or {}).get('plan',{}).get('study'),'process':'lean',
            'sealed_input_verified':sealed,'label_source':lsrc,'n24':n24,'n32':n32,'caps':(res or {}).get('caps'),
            'workers':(res or {}).get('workers'),'stop':(res or {}).get('stop'),'arm_spec':(res or {}).get('arm_spec'),
            'gates':Gt,'secondary':sec,'all_gated_pass':ok,'failed':failed,'not_exercised':[],
            'certified_readbits4_N24':ok,'sound_not_certified_N24':sound_only,'status_phrase':status_phrase(ok,sound_only,failed),
            'framing':'TARGET CHANGE: wide 4-bit readings on random emissions, declared N raised to 24 (gated) and 32 (reported); 2-bit readings at 20 states stay Open',
            'claim':('certify/32b ID/IDF is exact conditional on noise-free readings and on true size <= the declared N (here N <= 24; S32 at N <= 32 '
                     'reported). IDF identifies the machine from the current state, not the start. Inferred reason the size condition is needed: a '
                     'larger machine can copy the true machine on every visited state'),
            'reports':{'labels':fl} if allc else {}}


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--study-dir',default=str(STUDY_DIR));ap.add_argument('--check',action='store_true');a=ap.parse_args()
    obj=build(Path(a.study_dir));out=Path(a.study_dir)/'GATES_060.json'
    if a.check:check(out.read_bytes()==dumps(obj),'GATES_060.json does not reproduce');print('GATES_060 reproduces')
    else:write_new(out,obj);print(json.dumps({k:v['pass'] for k,v in obj['gates'].items()}),obj['failed'])
