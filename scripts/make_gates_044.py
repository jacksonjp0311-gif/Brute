"""Gates for study-044 (BRUTE_PLAN_044; pre-run deviation #161 definitions), LEAN process. Committed in the source freeze before
run_start_044; nothing is tuned after results are seen. New file; built from scripts/make_gates_043.py (frozen).
Inputs (D = results/study-044): D/main/{RESULTS,SCIENTIFIC,SEAL}.json (18 fresh cases: lowobs12 12, control 6; arms A16_c9 /
A16_c30 / A16_xf merged per case; under the A16_c30 cut only the first 8 lowobs12 cases carry A16_c30), D/main/RECOUNT_044.json,
D/main/REFERENCE_044.json, D/TEST_SUITE_044.json, experiments/COMMIT_ORDER_044.json, results/RESEARCH_LEDGER.jsonl.
Missing or partial input => every data gate FAIL INCOMPLETE_INPUT. Records are accepted only if sha256(RESULTS) equals the seal and
no_time(RESULTS) equals SCIENTIFIC. Each gate is scored from its own counts (plan gate_dependency_rule):
  labels: recounted labels if G_recount passes, else the study's stored labels (the fallback is stated in the gate);
  GLO_cap: lowobs12, A16_c30 ID+IDF >= 3 of 12 AND (A16_c30 - A16_c9) ID+IDF >= 2; under the cut (RESULTS cut_c30 true; plan
     runtime_estimate) both counts are taken on the first 8 lowobs12 seeds and the bar is >= 2 of 8 with gain >= 2;
  GLO_pol: lowobs12, A16_xf ID+IDF >= 3 of 12 AND (A16_xf - A16_c9) ID+IDF >= 2; Wilson 95% CIs reported for every count;
  GLO_sem: WRONG 0 in every arm on every fresh case (recount labels where present, study labels otherwise, both read); for every
     pair of arms on a case: both ID / IDF => same n_min, both ID => same canonical model. ID-vs-IDF pairs reported;
  GQB19: per arm, every logged SAT-call wall and every query wall <= that arm's cap + 1.5 s (10.5 s c9 / xf, 31.5 s c30);
  G_sound: study words_unsound 0, recount words_unsound 0 and words_checked equal to the study's, recount truth_inconsistent 0;
  G10: every arm ID on each of the 6 controls;
  GS_ref: REFERENCE_044 on block main, all three arms, key lowobs12: records equal the lowobs12 records of all arms, 0 mismatches,
     sha bound; if decided > 0 then mutations 20/20; if decided == 0 the gate passes VACUOUSLY and says so ('vacuous': true);
  GTI: TEST_SUITE_044 passed (gated modules returncode 0);
  G_PROC: preregistration_044, build_authorization_044, seedcheck_044, seedcheck_044b (#161 item 2), source_freeze_044,
     run_start_044, run_end_044 present in this order (other events allowed between), parseable non-decreasing note times;
     commit-order file; main sealed;
  G_RT: total elapsed <= 3600 s (plan G_RT); G_recount: RECOUNT_044 PASS on the sealed RESULTS with 0 mismatches.
  Secondary (reported only): GC9 = A16_c9 lowobs12 ID+IDF with Wilson CI beside the 043 A16 0/12; GPH19 = calls / capped calls by
     (arm, key, phase); GLO_cause2 = per lowobs12 case and arm: stop, label, n_min, used, xf_used, rounds, capped calls, last phase,
     query max, run wall (informational).
  PYTHONPATH=. python scripts/make_gates_044.py [--study-dir D] [--check]"""
from __future__ import annotations
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common import load,dumps,write_new,check,sha
from experiments.brute_common_026 import wilson
from scripts.make_gates_034 import opt
from scripts.make_gates_043 import subseq
from scripts.recount_033 import canon

STUDY_DIR=ROOT/'results/study-044'
EXP_CASES={'lowobs12':12,'control':6};ARMS=('A16_c9','A16_c30','A16_xf');LABELS=('ID','IDF','AMB','WRONG','IDU')
CAP_RT=3600;CAP={'A16_c9':9.0,'A16_c30':30.0,'A16_xf':9.0};QB={a:CAP[a]+1.5 for a in ARMS}
BAR=3;GAIN=2;CUT_N=8;CUT_BAR=2;CUT_GAIN=2;GC9_043=(0,12)
PROC_ORDER=('preregistration_044','build_authorization_044','seedcheck_044','seedcheck_044b','source_freeze_044','run_start_044','run_end_044')


def ckey(c):return f"{c['block']}/{c['key']}/{c['seed']}"
def sn(x):return [x['stop'],x['n_min']]


def ledger():
    from datetime import datetime
    L=[json.loads(x) for x in (ROOT/'results/RESEARCH_LEDGER.jsonl').read_text().splitlines() if x.strip()]
    i0=next((i for i,e in enumerate(L) if e.get('event')=='preregistration_044'),None);out=[]
    for e in (L[i0:] if i0 is not None else []):
        try:t=datetime.fromisoformat(str(e.get('note',''))[:25])
        except ValueError:t=None
        out.append((e['event'],t))
        if e['event']==PROC_ORDER[-1]:break
    return out


def build(study=STUDY_DIR,exp=None):
    from brute.evaluation import no_time
    exp=exp or EXP_CASES;study=Path(study);D=study/'main';Gt={};sec={}
    seal=opt(D/'SEAL.json');sci=opt(D/'SCIENTIFIC.json');res=opt(D/'RESULTS.json');rc=opt(D/'RECOUNT_044.json')
    ref=opt(D/'REFERENCE_044.json');ts=opt(study/'TEST_SUITE_044.json');order=opt(ROOT/'experiments/COMMIT_ORDER_044.json')
    rsha=sha(D/'RESULTS.json') if (D/'RESULTS.json').exists() else None
    sealed=(bool(seal) and res is not None and sci is not None and rsha==seal.get('results_sha256')
            and sha(D/'SCIENTIFIC.json')==seal.get('scientific_sha256') and no_time(res)==sci)
    cut=bool((res or {}).get('cut_c30'))
    allc=[c for c in (res or {}).get('cases',[]) if c['block']=='main'] if sealed else []
    G=lambda k:sorted([c for c in allc if c['key']==k],key=lambda c:c['seed'])
    lo=G('lowobs12');nlo=len(lo)
    def arms_ok(c,i):
        want=[a for a in ARMS if not (cut and a=='A16_c30' and c['key']=='lowobs12' and i>=CUT_N)]
        return sorted(c['arms'])==sorted(want)
    complete=(sealed and seal.get('complete') is True and all(len(G(k))==n for k,n in exp.items()) and len(allc)==sum(exp.values())
              and all(arms_ok(c,i) for k in exp for i,c in enumerate(G(k))))
    wb=None if complete else 'INCOMPLETE_INPUT (main missing, partial, missing arms or not matching its seal)'
    def gate(name,ok,obs,why=None):Gt[name]={'pass':bool(ok) and why is None,'observed':obs,**({'reason':why} if why else {})}
    pc=(rc or {}).get('per_case') or {}
    rc_bound=bool(rc) and rc.get('results_sha256')==rsha and rc.get('cases')==len((res or {}).get('cases',[]))
    rc_ok=rc_bound and rc.get('PASS') is True and rc.get('mismatching_cases')==0
    rlab=lambda c,a:((pc.get(ckey(c)) or {}).get(a) or {}).get('label') if rc_bound else None
    lab=(lambda c,a:rlab(c,a)) if rc_ok else (lambda c,a:c['arms'][a]['label'])
    lsrc='recount' if rc_ok else 'study labels (G_recount did not pass)'
    dd=lambda c,a:a in c['arms'] and lab(c,a) in ('ID','IDF')
    ci=lambda x,n:wilson(x,n) if n else None
    # GLO_cap
    pool=lo[:CUT_N] if cut else lo;npool=len(pool);bar,gain=(CUT_BAR,CUT_GAIN) if cut else (BAR,GAIN)
    c30=sum(dd(c,'A16_c30') for c in pool);c9p=sum(dd(c,'A16_c9') for c in pool)
    gate('GLO_cap',complete and c30>=bar and c30-c9p>=gain,{'A16_c30_ID_IDF':c30,'A16_c9_ID_IDF':c9p,'of':npool,'gain':c30-c9p,'cut_applied':cut,
         'A16_c30_ci95':ci(c30,npool),'A16_c9_ci95':ci(c9p,npool),'label_source':lsrc,
         'per_case':[[c['seed'],lab(c,'A16_c30') if 'A16_c30' in c['arms'] else None,lab(c,'A16_c9')] for c in lo],
         'rule':f'A16_c30 ID+IDF >= {bar}/{CUT_N if cut else 12} and A16_c30 - A16_c9 (ID+IDF) >= {gain}'+(' on the first 8 lowobs12 seeds (cut)' if cut else '')},why=wb)
    # GLO_pol
    xf=sum(dd(c,'A16_xf') for c in lo);c9=sum(dd(c,'A16_c9') for c in lo)
    gate('GLO_pol',complete and xf>=BAR and xf-c9>=GAIN,{'A16_xf_ID_IDF':xf,'A16_c9_ID_IDF':c9,'of':nlo,'gain':xf-c9,
         'A16_xf_ci95':ci(xf,nlo),'A16_c9_ci95':ci(c9,nlo),'label_source':lsrc,
         'per_case':[[c['seed'],lab(c,'A16_xf'),lab(c,'A16_c9')] for c in lo],'rule':f'A16_xf ID+IDF >= {BAR}/12 and A16_xf - A16_c9 (ID+IDF) >= {GAIN}'},why=wb)
    # GLO_sem
    wrong=[(ckey(c),a,'recount' if rlab(c,a) is not None else 'study') for c in allc for a in c['arms']
           if (rlab(c,a) if rlab(c,a) is not None else c['arms'][a]['label'])=='WRONG' or c['arms'][a]['label']=='WRONG']
    pairs=lambda c:[(a,b) for i,a in enumerate(ARMS) for b in ARMS[i+1:] if a in c['arms'] and b in c['arms']]
    nm=[[ckey(c),a,b,sn(c['arms'][a]),sn(c['arms'][b])] for c in allc for a,b in pairs(c)
        if c['arms'][a]['stop'] in ('ID','IDF') and c['arms'][b]['stop'] in ('ID','IDF') and c['arms'][a]['n_min']!=c['arms'][b]['n_min']]
    cm=[[ckey(c),a,b] for c in allc for a,b in pairs(c) if c['arms'][a]['stop']=='ID' and c['arms'][b]['stop']=='ID'
        and canon(*c['arms'][a]['model'],0)!=canon(*c['arms'][b]['model'],0)]
    idf=[[ckey(c),a,b,c['arms'][a]['stop'],c['arms'][b]['stop']] for c in allc for a,b in pairs(c)
         if {c['arms'][a]['stop'],c['arms'][b]['stop']}=={'ID','IDF'}]
    gate('GLO_sem',complete and not wrong and not nm and not cm,{'WRONG':wrong,'n_min_differs':nm,'ID_models_differ':cm,
         'ID_vs_IDF_reported':idf,'rule':'WRONG 0 in every arm; any two arms both ID/IDF => same n_min; both ID => same canonical model'},why=wb)
    # GQB19
    per={};over=[];by={};kills=0;ncalls=0
    for c in allc:
        for a,ar in c['arms'].items():
            kills+=ar['kills']
            for x in ar['calls']:
                ncalls+=1;per[a]=max(per.get(a,0),x['wall']);k=a+'/'+x['phase'];by[k]=max(by.get(k,0),x['wall'])
                if x['wall']>QB[a]:over.append([f'{ckey(c)}/{a}',x['phase'],x['n'],round(x['wall'],3)])
            q=ar['query_max_s']
            if q is not None:
                per[a]=max(per.get(a,0),q)
                if q>QB[a]:over.append([f'{ckey(c)}/{a}','query',None,round(q,3)])
    gate('GQB19',complete and bool(per) and not over and all(per[a]<=QB[a] for a in per),{'max_s_by_arm':{a:round(v,3) for a,v in sorted(per.items())},
         'bound_s_by_arm':QB,'over':over,'max_by_arm_phase':{k:round(v,3) for k,v in sorted(by.items())},'hard_kills':kills,'calls_logged':ncalls},why=wb)
    # G_sound
    snd={'words_checked':sum(ar.get('words_checked',0) for c in allc for ar in c['arms'].values()),
         'words_unsound':sum(ar.get('words_unsound',0) for c in allc for ar in c['arms'].values()),
         'recount_bound':rc_bound,'recount_words_checked':(rc or {}).get('words_checked'),'recount_words_unsound':(rc or {}).get('words_unsound'),
         'recount_truth_inconsistent':(rc or {}).get('truth_inconsistent')}
    gate('G_sound',complete and rc_bound and snd['words_unsound']==0 and snd['recount_words_unsound']==0 and snd['recount_truth_inconsistent']==0
         and snd['recount_words_checked']==snd['words_checked'],snd,why=wb or (None if rc_bound else 'INCOMPLETE_INPUT (RECOUNT_044 missing or unbound)'))
    # G10
    g10=[(c['seed'],{a:(rlab(c,a) if rlab(c,a) is not None else c['arms'][a]['label']) for a in ARMS if a in c['arms']}) for c in G('control')]
    gate('G10',complete and len(g10)==exp['control'] and all(len(x[1])==3 and all(L=='ID' for L in x[1].values()) for x in g10),
         {'cases':g10,'rule':'every arm ID on every control'},why=wb)
    # GS_ref
    mt=(ref or {}).get('mutation_test') or {};nrec=sum(len(c['arms']) for c in lo)
    robs=None if not ref else {k:ref.get(k) for k in ('block','arm','key','records','decided','decided_by_arm','not_reached','k_spent_as_amb','verdicts_checked','mismatch_count','vacuous','PASS')}|{'mutations':mt.get('detected'),'of':mt.get('mutations')}
    vac=bool(ref) and ref.get('decided')==0
    rbase=(bool(ref) and ref.get('study_results_sha256')==rsha and ref.get('block')=='main' and ref.get('arm')==list(ARMS) and ref.get('key')==['lowobs12']
           and ref.get('records')==nrec and ref.get('mismatch_count')==0 and (vac or mt.get('detected')==mt.get('mutations')==20))
    if robs is not None:robs['vacuous_pass_stated']=('PASSES VACUOUSLY: 0 decided lowobs12 records in any arm, so nothing to audit and no mutation pool' if vac else None)
    gate('GS_ref',rbase and ref.get('PASS') is True,robs,why=wb or (None if ref else 'INCOMPLETE_INPUT (REFERENCE_044 missing)'))
    # GTI
    mods=(ts or {}).get('per_module') or {};gm=(ts or {}).get('gated_modules') or []
    gate('GTI',bool(gm) and ts.get('passed') is True and all(mods[m].get('returncode')==0 for m in gm),
         None if not ts else {'gated':{m:{'returncode':mods[m].get('returncode'),'tests':mods[m].get('tests')} for m in gm},
                              'reported':{m:{'returncode':v.get('returncode'),'tests':v.get('tests')} for m,v in mods.items() if m not in gm}},
         why=None if ts else 'INCOMPLETE_INPUT (TEST_SUITE_044 missing)')
    # G_PROC
    lt=ledger();ev=[e for e,_ in lt];times=[t for _,t in lt]
    proc={'order':subseq(ev,PROC_ORDER),'ledger_times_parse':bool(lt) and all(t is not None for t in times),
          'ledger_times_non_decreasing':all(a<=b for a,b in zip(times,times[1:]) if a and b),'commit_order_file':order is not None,'main_sealed':bool(sealed)}
    sc=opt(ROOT/'results/diag-044/SEEDCHECK_044.json');scb=opt(ROOT/'results/diag-044/SEEDCHECK_044B.json')
    gate('G_PROC',all(proc.values()),{'clauses':proc,'events':ev,'required_order':list(PROC_ORDER),
         'reported_seedcheck_044_PASS':(sc or {}).get('PASS'),'reported_seedcheck_044b_PASS':(scb or {}).get('PASS'),
         'note':'seedcheck_044 failed; seedcheck_044b is a post-scan adjudication (#161 item 2)'})
    el=(res or {}).get('total_elapsed_informational')
    gate('G_RT',complete and el is not None and el<=CAP_RT,{'elapsed_s':el,'cap_s':CAP_RT,'cases':len(allc),'cut_applied':cut},why=wb)
    gate('G_recount',complete and rc_ok,None if not rc else {k:rc.get(k) for k in ('cases','labels_main','amb_rule_applied','words_checked','words_unsound','truth_inconsistent','mismatching_cases','PASS')},
         why=wb or (None if rc else 'INCOMPLETE_INPUT (RECOUNT_044 missing)'))
    # secondary
    sec['GC9']={'pass':None,'observed':{'A16_c9_ID_IDF':c9,'of':nlo,'ci95':ci(c9,nlo),'study_043_A16':list(GC9_043),'study_043_ci95':wilson(*GC9_043)},
                'rule':'reported: A16_c9 replicates the 043 A16 baseline (0/12)'}
    ph={}
    for c in allc:
        for a,ar in c['arms'].items():
            for p,b in ar['by_phase'].items():x=ph.setdefault(f"{a}/{c['key']}/{p}",[0,0]);x[0]+=b['calls'];x[1]+=b['capped']
    sec['GPH19']={'pass':None,'observed':{k:{'calls':v[0],'capped':v[1]} for k,v in sorted(ph.items())},'rule':'reported: calls / capped calls by arm, key and phase'}
    sec['GLO_cause2']={'pass':None,'observed':{f"{c['seed']}/{a}":{'stop':x['stop'],'label':lab(c,a),'n_min':x['n_min'],'used':x['used'],'xf_used':x.get('xf_used',0),
                      'n_rounds':x['n_rounds'],'capped_calls':sum(b['capped'] for b in x['by_phase'].values()),'last_phase':x['last_phase'],
                      'query_max_s':x['query_max_s'],'run_wall_informational':x.get('arm_wall_informational')} for c in lo for a,x in c['arms'].items()},
                      'rule':'reported: per lowobs12 case and arm, the stop and what bound it'}
    cnt=lambda k,a,L:sum(a in c['arms'] and lab(c,a)==L for c in G(k));nk=lambda k,a:sum(a in c['arms'] for c in G(k))
    fl={f'{a}/{k}':{L:{'x':cnt(k,a,L),'n':nk(k,a),'ci95':ci(cnt(k,a,L),nk(k,a))} for L in LABELS} for a in ARMS for k in exp}
    return {'schema':'brute.gates.v41_0','study':'BRUTE-0410-A16-LOWOBS-AUDIT-044','process':'lean','sealed_input_verified':sealed,'label_source':lsrc,'cut_c30':cut,'gates':Gt,
            'secondary':sec,'all_gated_pass':all(g['pass'] for g in Gt.values() if g['pass'] is not None),
            'failed':[k for k,g in Gt.items() if g['pass'] is False],'not_exercised':[k for k,g in Gt.items() if g['pass'] is None],
            'reports':{'fresh_labels':fl} if allc else {}}


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--study-dir',default=str(STUDY_DIR));ap.add_argument('--check',action='store_true');a=ap.parse_args()
    obj=build(Path(a.study_dir));out=Path(a.study_dir)/'GATES_044.json'
    if a.check:check(out.read_bytes()==dumps(obj),'GATES_044.json does not reproduce');print('GATES_044 reproduces')
    else:write_new(out,obj);print(json.dumps({k:v['pass'] for k,v in obj['gates'].items()}),obj['failed'])
