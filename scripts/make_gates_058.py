"""Gates for study-058 (BRUTE_PLAN_058 criteria; pre-run deviation #190 definitions), LEAN process. Committed in the source freeze
before main_run_058; nothing is tuned after results are seen. New file; built from scripts/make_gates_057.py (frozen).
HONEST FRAMING (plan step_back): this study changes the TARGET (wider readings); 2-bit readings at 20 states stay Open whatever it shows.
Inputs (D = results/study-058): D/main/{RESULTS,SCIENTIFIC,SEAL}.json, D/main/RECOUNT_058.json, D/main/REFERENCE_058.json,
D/API_CHECKS_058.json, D/TEST_SUITE_058.json, results/diag-058/SEEDCHECK_058.json, experiments/COMMIT_ORDER_058.json,
results/RESEARCH_LEDGER.jsonl. Missing or partial input => every data gate FAIL INCOMPLETE_INPUT. Records are accepted only if
sha256(RESULTS) equals the seal and no_time(RESULTS) equals SCIENTIFIC. Labels: recounted if G_recount passes, else the study's.
Arms (certify/20b at bound 20): B2 (scale20, 2-bit), B2R (random 2-bit), B3 (random 3-bit), B4 (random 4-bit), B4_b (B4 again).
  GS58_sound: WRONG 0 on every record (60 at N58 12);
  GB_gain58: B4 ID+IDF >= 6 of 12 AND B4 - B2R >= 4 on the same seeds (Wilson CIs; exact McNemar reported);
  GB3_58: B3 ID+IDF >= 4 of 12 AND B3 > B2R;
  GDET58: canon58(B4) == canon58(B4_b) on every seed, 0 wall-guard firings on every record;
  GFID58: API_CHECKS_058 equiv (bits 2 == 16e on 6 small worlds, malformed refused), the no-network run (0 socket attempts) and fidelity exact on every decided record,
     bound to the sealed RESULTS sha;
  GHOST58: API_CHECKS_058 ghost PASS58, bound to certify20b.py's sha in BRUTE_SOURCE_FREEZE_058;
  GS_ref: REFERENCE_058 on block main: sha bound, 0 mismatches, complete within 1800 s on 8 workers, 20/20 mutations (vacuous only if
     nothing is decided);
  G_recount: RECOUNT_058 bound and PASS; GTEST: gated modules of TEST_SUITE_058 pass;
  G_PROC: preregistration, build_authorization, seedcheck, prefreeze_smoke_058, deviation_190, freeze_058, main_run_058
     (plan G_PROC names) as a subsequence, parseable non-decreasing note times, commit-order file, main sealed;
  G_RT: verify_release_0550 is the release-time check (recorded at release, not gated here; plan G_RT); this file records the
     main elapsed for the record.
  certified_readbits_N20: every gate passes (for read_bits 3 and 4 at N <= 20); sound_not_certified_readbits: every gate except
  GB_gain58 and/or GB3_58 passes. status_phrase: derived from the two flags.
  Secondary (reported): PER_ARM58, MCNEMAR58, COST58, SEEDCHECK58.
  PYTHONPATH=. python scripts/make_gates_058.py [--study-dir D] [--check]"""
from __future__ import annotations
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common import load,dumps,write_new,check,sha
from experiments.brute_common_026 import wilson
from scripts.make_gates_034 import opt
from scripts.make_gates_043 import subseq
from scripts.make_gates_057 import mcnemar

STUDY_DIR=ROOT/'results/study-058';ARMS=('B2','B2R','B3','B4','B4_b')
LABELS=('ID','IDF','AMB','WRONG','IDU');MIN_B4=6;DIFF_B4=4;MIN_B3=4;SOFT=('GB_gain58','GB3_58')
PROC_ORDER=('preregistration_058','build_authorization_058','seedcheck_058','prefreeze_smoke_058','deviation_190','freeze_058',
            'main_run_058')


def ckey(c):return f"{c['block']}/{c['key']}/{c['seed']}"


def ledger():
    from datetime import datetime
    L=[json.loads(x) for x in (ROOT/'results/RESEARCH_LEDGER.jsonl').read_text().splitlines() if x.strip()]
    i0=next((i for i,e in enumerate(L) if e.get('event')=='preregistration_058'),None);out=[]
    for e in (L[i0:] if i0 is not None else []):
        try:t=datetime.fromisoformat(str(e.get('note',''))[:25])
        except ValueError:t=None
        out.append((e['event'],t))
        if e['event']==PROC_ORDER[-1]:break
    return out


def status_phrase(certified,sound_only,failed):
    if certified:return 'certified (read_bits 3 and 4, N <= 20)'
    if sound_only:return 'sound but not certified'
    return 'not certified, no certification status (failing gates: '+', '.join(failed)+')'


def build(study=STUDY_DIR,expect=None):
    from brute.evaluation import no_time
    from experiments.brute_study_058 import canon58,N58
    study=Path(study);D=study/'main';Gt={};sec={}
    seal=opt(D/'SEAL.json');sci=opt(D/'SCIENTIFIC.json');res=opt(D/'RESULTS.json');rc=opt(D/'RECOUNT_058.json')
    ref=opt(D/'REFERENCE_058.json');ts=opt(study/'TEST_SUITE_058.json');order=opt(ROOT/'experiments/COMMIT_ORDER_058.json')
    api=opt(study/'API_CHECKS_058.json');fz=opt(ROOT/'experiments/BRUTE_SOURCE_FREEZE_058.json')
    sc=opt(ROOT/'results/diag-058/SEEDCHECK_058.json')
    rsha=sha(D/'RESULTS.json') if (D/'RESULTS.json').exists() else None
    sealed=(bool(seal) and res is not None and sci is not None and rsha==seal.get('results_sha256')
            and sha(D/'SCIENTIFIC.json')==seal.get('scientific_sha256') and no_time(res)==sci)
    n=int(expect if expect is not None else (res or {}).get('n58',N58))
    allc=sorted([c for c in (res or {}).get('cases',[]) if c['block']=='main'],key=lambda c:c['seed']) if sealed else []
    arms_ok=all(sorted(c['arms'])==sorted(ARMS) for c in allc)
    complete=sealed and seal.get('complete') is True and len(allc)==n and arms_ok
    wb=None if complete else 'INCOMPLETE_INPUT (main missing, partial, missing arms or not matching its seal)'
    def gate(name,ok,obs,why=None):Gt[name]={'pass':bool(ok) and why is None,'observed':obs,**({'reason':why} if why else {})}
    pc=(rc or {}).get('per_case') or {}
    rc_bound=bool(rc) and rc.get('results_sha256')==rsha and rc.get('cases')==len((res or {}).get('cases',[]))
    rc_ok=rc_bound and rc.get('PASS') is True and not rc.get('mismatches')
    lab=(lambda c,a:((pc.get(str(c['seed'])) or {}).get(a) or {}).get('label')) if rc_ok else (lambda c,a:c['arms'][a]['label'])
    lsrc='recount' if rc_ok else 'study labels (G_recount did not pass)'
    dd=lambda c,a:a in c['arms'] and lab(c,a) in ('ID','IDF')
    ci=lambda x,m:wilson(x,m) if m else None
    nd_=lambda a:sum(dd(c,a) for c in allc)
    wrong=[[ckey(c),a] for c in allc for a in c['arms'] if lab(c,a)=='WRONG' or c['arms'][a]['label']=='WRONG']
    gate('GS58_sound',complete and not wrong,{'WRONG':wrong,'records':sum(len(c['arms']) for c in allc),
         'per_case':[[c['seed']]+[lab(c,a) for a in ARMS] for c in allc],'columns':['seed']+list(ARMS),'label_source':lsrc},why=wb)
    x2,x2r,x3,x4,x4b=(nd_(a) for a in ARMS);m=len(allc)
    disc=lambda a,b:[sum(dd(c,a) and not dd(c,b) for c in allc),sum(dd(c,b) and not dd(c,a) for c in allc)]
    d4=disc('B4','B2R');d3=disc('B3','B2R')
    gate('GB_gain58',complete and x4>=MIN_B4 and x4-x2r>=DIFF_B4,{'B4_ID_IDF':x4,'B2R_ID_IDF':x2r,'of':m,'ci95_B4':ci(x4,m),'ci95_B2R':ci(x2r,m),
         'discordant':d4,'mcnemar_p_reported':mcnemar(*d4),'rule':'B4 ID+IDF >= 6 of 12 and B4 - B2R >= 4 on the same seeds','label_source':lsrc},why=wb)
    gate('GB3_58',complete and x3>=MIN_B3 and x3>x2r,{'B3_ID_IDF':x3,'B2R_ID_IDF':x2r,'of':m,'ci95_B3':ci(x3,m),'ci95_B2R':ci(x2r,m),
         'discordant':d3,'mcnemar_p_reported':mcnemar(*d3),'rule':'B3 ID+IDF >= 4 of 12 and B3 > B2R','label_source':lsrc},why=wb)
    det=[[c['seed'],canon58(c['arms']['B4'])==canon58(c['arms']['B4_b']),c['arms']['B4']['label'],c['arms']['B4_b']['label']] for c in allc]
    kills=[[ckey(c),an,ar.get('guard_events')] for c in allc for an,ar in c['arms'].items() if ar.get('wall_guard')]
    ndt=sum(x[1] for x in det)
    gate('GDET58',complete and ndt==n and not kills,{'identical':ndt,'of':len(det),'ci95':ci(ndt,len(det)),'wall_guard_firings':kills,
         'records_checked':sum(len(c['arms']) for c in allc),'per_case':det,'columns':['seed','canon58_equal','pass1','pass2']},why=wb)
    fi=(api or {}).get('fidelity') or {};eq=(api or {}).get('equiv') or {}
    ndec=sum(dd(c,a) for c in allc for a in c['arms'])
    fi_ok=bool(fi) and fi.get('study_results_sha256')==rsha and fi.get('PASS') is True and fi.get('exact')==fi.get('decided_records')
    gate('GFID58',complete and fi_ok and eq.get('PASS') is True and ((api or {}).get('ghost') or {}).get('network_pass') is True,{'no_network_run':((api or {}).get('ghost') or {}).get('no_network_run'),'equiv_bits2_vs_16e':eq.get('cases'),'refusals':eq.get('refusals'),
         'fidelity_exact':fi.get('exact'),'of_decided':fi.get('decided_records'),'decided_in_gates':ndec,'vacuous':fi.get('vacuous'),
         'bound':bool(fi) and fi.get('study_results_sha256')==rsha,'failures':{k:v for k,v in (fi.get('per_case') or {}).items() if not v['exact']}},
         why=wb or (None if fi else 'INCOMPLETE_INPUT (API_CHECKS_058 fidelity missing)'))
    ct=sha(ROOT/'brute/api/certify20b.py');f58=(fz or {}).get('sha256_files',{}).get('brute/api/certify20b.py')
    abound=bool(api) and api.get('certify20b_sha256')==ct==f58;ag=(api or {}).get('ghost') or {}
    gate('GHOST58',abound and ag.get('PASS58') is True,None if not api else {'bound_to_freeze_058':abound,'static_ok':ag.get('certify20b_static_ok'),
         'frozen_api_unchanged':ag.get('frozen_api_unchanged'),'socket_attempts':ag.get('socket_attempts'),'no_network_run':ag.get('no_network_run')},
         why=None if api else 'INCOMPLETE_INPUT (API_CHECKS_058 missing)')
    mt=(ref or {}).get('mutation_test') or {};rb=bool(ref) and ref.get('study_results_sha256')==rsha and ref.get('block')=='main'
    robs=None if not ref else {k:ref.get(k) for k in ('block','scope','records','decided','audited','not_audited','complete','per_arm','not_reached',
                               'k_spent_as_amb','verdicts_checked','mismatch_count','vacuous','PASS','elapsed_informational')}|{'mutations':mt.get('detected'),'of':mt.get('mutations')}
    gate('GS_ref',rb and ref.get('mismatch_count')==0 and ref.get('complete') is True and (ref.get('scope') or {}).get('budget_s')==1800.0
         and (ref.get('vacuous') is True or mt.get('detected')==mt.get('mutations')==20) and ref.get('PASS') is True,robs,
         why=wb or (None if ref else 'INCOMPLETE_INPUT (REFERENCE_058 missing)'))
    gate('G_recount',complete and rc_ok,None if not rc else {k:rc.get(k) for k in ('cases','records','decided_by_arm','study_decided_by_arm','wrong','mismatches','PASS')},
         why=wb or (None if rc else 'INCOMPLETE_INPUT (RECOUNT_058 missing)'))
    mods=(ts or {}).get('per_module') or {};gm=(ts or {}).get('gated_modules') or []
    gate('GTEST',bool(gm) and ts.get('passed') is True and all(mods[x].get('returncode')==0 for x in gm),
         None if not ts else {'gated':{x:{'returncode':mods[x].get('returncode'),'tests':mods[x].get('tests')} for x in gm},
                              'reported':{x:{'returncode':v.get('returncode'),'tests':v.get('tests')} for x,v in mods.items() if x not in gm}},
         why=None if ts else 'INCOMPLETE_INPUT (TEST_SUITE_058 missing)')
    lt=ledger();ev=[e for e,_ in lt];times=[t for _,t in lt]
    proc={'order':subseq(ev,PROC_ORDER),'ledger_times_parse':bool(lt) and all(t is not None for t in times),
          'ledger_times_non_decreasing':all(a<=b for a,b in zip(times,times[1:]) if a and b),'commit_order_file':order is not None,'main_sealed':bool(sealed)}
    gate('G_PROC',all(proc.values()),{'clauses':proc,'events':ev,'required_order':list(PROC_ORDER)})
    sec['PER_ARM58']={'pass':None,'observed':[[c['seed']]+[[lab(c,a),c['arms'][a]['n_min'],c['arms'][a]['used'],c['arms'][a]['n_rounds'],
                       c['arms'][a]['conflicts_spent'],c['arms'][a]['distinct_codes']] for a in ARMS] for c in allc],
                      'columns':['seed']+[a+' [label, n_min, used, rounds, conflicts, distinct_codes]' for a in ARMS],'rule':'reported'}
    sec['MCNEMAR58']={'pass':None,'observed':{'B4_vs_B2R':{'discordant':d4,'p':mcnemar(*d4)},'B3_vs_B2R':{'discordant':d3,'p':mcnemar(*d3)},
                      'B2R_vs_B2':{'discordant':disc('B2R','B2'),'p':mcnemar(*disc('B2R','B2'))}},'rule':'reported: exact two-sided McNemar'}
    cost={}
    for c in allc:
        for a,ar in c['arms'].items():
            x=cost.setdefault(a,{'records':0,'wall_s':0.0,'conflicts':0,'chunks':0,'steps':0,'budget_spent':0})
            x['records']+=1;x['wall_s']+=ar.get('case_wall_informational') or 0.0;x['conflicts']+=ar.get('conflicts_spent') or 0
            x['chunks']+=ar.get('chunks_total') or 0;x['steps']+=len(ar.get('extra_acts') or [])
            x['budget_spent']+=(ar.get('conflicts_spent') or 0)>=ar['budget_conflicts']
    for x in cost.values():x['wall_s']=round(x['wall_s'],1)
    sec['COST58']={'pass':None,'observed':cost,'elapsed_s':(res or {}).get('total_elapsed_informational'),'rule':'reported (walls informational)'}
    sc_frozen=bool(sc) and (fz or {}).get('sha256_files',{}).get('results/diag-058/SEEDCHECK_058.json')==sha(ROOT/'results/diag-058/SEEDCHECK_058.json')
    sec['SEEDCHECK58']={'pass':None,'observed':None if not sc else {'seedcheck_pass':sc.get('PASS'),'frozen_in_058':sc_frozen}}
    cnt=lambda a,L:sum(lab(c,a)==L for c in allc)
    fl={a:{L:{'x':cnt(a,L),'n':m,'ci95':ci(cnt(a,L),m)} for L in LABELS} for a in ARMS}
    ok=all(g['pass'] for g in Gt.values())
    sound_only=not ok and all(g['pass'] for k,g in Gt.items() if k not in SOFT)
    failed=[k for k,g in Gt.items() if g['pass'] is False]
    return {'schema':'brute.gates.v55_0','study':(res or {}).get('plan',{}).get('study'),'process':'lean',
            'sealed_input_verified':sealed,'label_source':lsrc,'n58':n,'caps':(res or {}).get('caps'),
            'workers':(res or {}).get('workers'),'stop':(res or {}).get('stop'),'gates':Gt,'secondary':sec,
            'all_gated_pass':ok,'failed':failed,'not_exercised':[],
            'certified_readbits_N20':ok,'sound_not_certified_readbits':sound_only,'status_phrase':status_phrase(ok,sound_only,failed),
            'framing':'TARGET CHANGE: wider readings (3 or 4 bits) on random emissions; 2-bit readings at 20 states stay Open',
            'claim':('certify/20b ID/IDF is exact on noise-free traces conditional on true size <= the declared N (here N <= 20); IDF identifies '
                     'the machine from the current state, not the start. Inferred reason the condition is needed: a larger machine can copy the '
                     'true machine on every visited state'),
            'reports':{'labels':fl} if allc else {}}


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--study-dir',default=str(STUDY_DIR));ap.add_argument('--check',action='store_true');a=ap.parse_args()
    obj=build(Path(a.study_dir));out=Path(a.study_dir)/'GATES_058.json'
    if a.check:check(out.read_bytes()==dumps(obj),'GATES_058.json does not reproduce');print('GATES_058 reproduces')
    else:write_new(out,obj);print(json.dumps({k:v['pass'] for k,v in obj['gates'].items()}),obj['failed'])
