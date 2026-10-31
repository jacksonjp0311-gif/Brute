"""Gates for study-043 (BRUTE_PLAN_043; pre-run deviation #159 definitions), LEAN process. Committed in the source freeze before
run_start_043; nothing is tuned after results are seen. New file; built from scripts/make_gates_042.py (frozen).
Inputs (D = results/study-043): D/main/{RESULTS,SCIENTIFIC,SEAL}.json (30 fresh cases: lowobs12 12, scale16_rep 12, control 6;
arms A16 / A14 merged per case), D/main/RECOUNT_043.json, D/main/REFERENCE_043.json, D/TEST_SUITE_043.json,
experiments/COMMIT_ORDER_043.json, results/RESEARCH_LEDGER.jsonl.
Missing or partial input => every data gate FAIL INCOMPLETE_INPUT. Records are accepted only if sha256(RESULTS) equals the seal and
no_time(RESULTS) equals SCIENTIFIC. Each gate is scored from its own counts (plan gate_dependency_rule):
  labels: recounted labels if G_recount passes, else the study's stored labels (the fallback is stated in the gate);
  GLO: lowobs12, A16 ID+IDF >= 4 of 12 AND (A16 ID+IDF) - (A14 ID+IDF) >= 3; Wilson 95% CIs reported;
  GREP16: scale16_rep, A16 ID >= 6 of 12 (Wilson CI; A14 reported);
  GLO_sem: WRONG 0 in both arms on every fresh case (recount labels where present, study labels otherwise, both listed); no case
     where both arms are ID / IDF with different n_min, or both ID with canonical models that differ. ID-vs-IDF reported;
  GQB18: every logged SAT-call wall and every query wall <= 10.5 s over every arm (cube calls included);
  G_sound: study words_unsound 0, recount words_unsound 0 and words_checked equal to the study's, recount truth_inconsistent 0;
  G10: every arm ID on each of the 6 controls (recount labels where present, study labels otherwise);
  GS_ref: REFERENCE_043 on block main, arm A16, keys lowobs12 + scale16_rep (#159 item 3): records equal the lowobs12 +
     scale16_rep case count, 0 mismatches, decided > 0, mutations 20/20, sha bound; decided lowobs12 records reported;
  GTI: TEST_SUITE_043 passed (gated modules returncode 0);
  G_PROC: preregistration_043, build_authorization_043, seedcheck_043, seedcheck_043b (#159 item 1), source_freeze_043,
     run_start_043, run_end_043 present in this order (other events allowed between), parseable non-decreasing note times;
     commit-order file; main sealed;
  G_RT: total elapsed <= 1800 s; G_recount: RECOUNT_043 PASS on the sealed RESULTS with 0 mismatches.
  Secondary: GT17 = mean over main cases (calls in both arms) of mean call wall A16 / A14 on the same case, seed-bootstrap 95% CI
     (10000 resamples, random.Random(42), percentile); GPH18 = calls / capped calls by (arm, key, phase); GLO_cause = per lowobs12
     case and arm: stop, label, n_min, used, rounds, capped calls, last phase, query max (reported, read only by plan 043 next_if_fail).
  PYTHONPATH=. python scripts/make_gates_043.py [--study-dir D] [--check]"""
from __future__ import annotations
import argparse,json,random,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common import load,dumps,write_new,check,sha
from experiments.brute_common_026 import wilson
from scripts.make_gates_034 import opt
from scripts.recount_033 import canon

STUDY_DIR=ROOT/'results/study-043'
EXP_CASES={'lowobs12':12,'scale16_rep':12,'control':6};ARMS=('A16','A14');LABELS=('ID','IDF','AMB','WRONG','IDU')
CAP=1800;QB=10.5;BOOT=10000;BOOT_SEED=42;GLO_MIN=4;GLO_GAIN=3;GREP_MIN=6
PROC_ORDER=('preregistration_043','build_authorization_043','seedcheck_043','seedcheck_043b','source_freeze_043','run_start_043','run_end_043')


def boot(v,n=BOOT,seed=BOOT_SEED):
    if not v:return None
    rng=random.Random(seed);m=len(v);s=sorted(sum(v[rng.randrange(m)] for _ in range(m))/m for _ in range(n))
    return [round(s[int(0.025*n)],4),round(s[int(0.975*n)-1],4)]


def ckey(c):return f"{c['block']}/{c['key']}/{c['seed']}"
def dec(x):return x['stop']!='unknown'
def sn(x):return [x['stop'],x['n_min']]


def ledger():
    from datetime import datetime
    L=[json.loads(x) for x in (ROOT/'results/RESEARCH_LEDGER.jsonl').read_text().splitlines() if x.strip()]
    i0=next((i for i,e in enumerate(L) if e.get('event')=='preregistration_043'),None);out=[]
    for e in (L[i0:] if i0 is not None else []):
        try:t=datetime.fromisoformat(str(e.get('note',''))[:25])
        except ValueError:t=None
        out.append((e['event'],t))
        if e['event']==PROC_ORDER[-1]:break
    return out


def subseq(ev,order):
    i=0
    for e in ev:
        if i<len(order) and e==order[i]:i+=1
    return i==len(order)


def build(study=STUDY_DIR,exp=None):
    from brute.evaluation import no_time
    exp=exp or EXP_CASES;study=Path(study);D=study/'main';Gt={};sec={}
    seal=opt(D/'SEAL.json');sci=opt(D/'SCIENTIFIC.json');res=opt(D/'RESULTS.json');rc=opt(D/'RECOUNT_043.json')
    ref=opt(D/'REFERENCE_043.json');ts=opt(study/'TEST_SUITE_043.json');order=opt(ROOT/'experiments/COMMIT_ORDER_043.json')
    rsha=sha(D/'RESULTS.json') if (D/'RESULTS.json').exists() else None
    sealed=(bool(seal) and res is not None and sci is not None and rsha==seal.get('results_sha256')
            and sha(D/'SCIENTIFIC.json')==seal.get('scientific_sha256') and no_time(res)==sci)
    allc=[c for c in (res or {}).get('cases',[]) if c['block']=='main'] if sealed else []
    G=lambda k:sorted([c for c in allc if c['key']==k],key=lambda c:c['seed'])
    complete=(sealed and seal.get('complete') is True and all(len(G(k))==n for k,n in exp.items()) and len(allc)==sum(exp.values())
              and all(sorted(c['arms'])==sorted(ARMS) for c in allc))
    wb=None if complete else 'INCOMPLETE_INPUT (main missing, partial, missing arms or not matching its seal)'
    def gate(name,ok,obs,why=None):Gt[name]={'pass':bool(ok) and why is None,'observed':obs,**({'reason':why} if why else {})}
    pc=(rc or {}).get('per_case') or {}
    rc_bound=bool(rc) and rc.get('results_sha256')==rsha and rc.get('cases')==len((res or {}).get('cases',[]))
    rc_ok=rc_bound and rc.get('PASS') is True and rc.get('mismatching_cases')==0
    rlab=lambda c,a:((pc.get(ckey(c)) or {}).get(a) or {}).get('label') if rc_bound else None
    lab=(lambda c,a:rlab(c,a)) if rc_ok else (lambda c,a:c['arms'][a]['label'])
    lsrc='recount' if rc_ok else 'study labels (G_recount did not pass)'
    cnt=lambda k,a,L:sum(lab(c,a)==L for c in G(k))
    # GLO
    lo=G('lowobs12');nlo=len(lo);dd=lambda c,a:lab(c,a) in ('ID','IDF')
    l16=sum(dd(c,'A16') for c in lo);l14=sum(dd(c,'A14') for c in lo)
    gate('GLO',complete and l16>=GLO_MIN and l16-l14>=GLO_GAIN,{'A16_ID_IDF':l16,'A14_ID_IDF':l14,'of':nlo,'gain':l16-l14,
         'A16_ci95':wilson(l16,nlo) if nlo else None,'A14_ci95':wilson(l14,nlo) if nlo else None,'label_source':lsrc,
         'per_case':[[c['seed'],lab(c,'A16'),lab(c,'A14')] for c in lo],'rule':f'A16 ID+IDF >= {GLO_MIN}/12 and A16 - A14 (ID+IDF) >= {GLO_GAIN}'},why=wb)
    # GREP16
    s16=G('scale16_rep');n16=len(s16);i16=cnt('scale16_rep','A16','ID');i14=cnt('scale16_rep','A14','ID')
    gate('GREP16',complete and i16>=GREP_MIN,{'A16_ID':i16,'A14_ID':i14,'of':n16,'A16_ci95':wilson(i16,n16) if n16 else None,
         'A14_ci95':wilson(i14,n16) if n16 else None,'label_source':lsrc,'per_case':[[c['seed'],lab(c,'A16'),lab(c,'A14')] for c in s16],
         'rule':f'A16 ID >= {GREP_MIN}/12 on scale16_rep'},why=wb)
    # GLO_sem
    wrong=[(ckey(c),a,'recount' if rlab(c,a) is not None else 'study') for c in allc for a in ARMS
           if (rlab(c,a) if rlab(c,a) is not None else c['arms'][a]['label'])=='WRONG' or c['arms'][a]['label']=='WRONG']
    nm=[[ckey(c),sn(c['arms']['A16']),sn(c['arms']['A14'])] for c in allc
        if all(c['arms'][a]['stop'] in ('ID','IDF') for a in ARMS) and c['arms']['A16']['n_min']!=c['arms']['A14']['n_min']]
    cm=[ckey(c) for c in allc if all(c['arms'][a]['stop']=='ID' for a in ARMS)
        and canon(*c['arms']['A16']['model'],0)!=canon(*c['arms']['A14']['model'],0)]
    idf=[[ckey(c),c['arms']['A16']['stop'],c['arms']['A14']['stop']] for c in allc
         if {c['arms'][a]['stop'] for a in ARMS}=={'ID','IDF'}]
    gate('GLO_sem',complete and not wrong and not nm and not cm,{'WRONG':wrong,'n_min_differs':nm,'ID_models_differ':cm,
         'ID_vs_IDF_reported':idf,'rule':'WRONG 0 in both arms; both ID/IDF => same n_min; both ID => same canonical model'},why=wb)
    # GQB18
    calls=[(f'{ckey(c)}/{a}',x['phase'],x['n'],x['wall']) for c in allc for a,ar in c['arms'].items() for x in ar['calls']]
    qmax=[(f'{ckey(c)}/{a}',ar['query_max_s']) for c in allc for a,ar in c['arms'].items() if ar['query_max_s'] is not None]
    over=[[i,p,n,round(w,3)] for i,p,n,w in calls if w>QB];qover=[[i,round(w,3)] for i,w in qmax if w>QB]
    worst=max([w for *_,w in calls]+[w for _,w in qmax],default=None);by={}
    for i,p,n,w in calls:by[i.split('/')[-1]+'/'+p]=max(by.get(i.split('/')[-1]+'/'+p,0),w)
    kills=sum(ar['kills'] for c in allc for ar in c['arms'].values())
    gate('GQB18',complete and worst is not None and worst<=QB and not over and not qover,{'max_s':worst,'bound_s':QB,'over_calls':over,
         'over_queries':qover,'max_by_arm_phase':{k:round(v,3) for k,v in sorted(by.items())},'hard_kills':kills,'calls_logged':len(calls)},why=wb)
    # G_sound
    snd={'words_checked':sum(ar.get('words_checked',0) for c in allc for ar in c['arms'].values()),
         'words_unsound':sum(ar.get('words_unsound',0) for c in allc for ar in c['arms'].values()),
         'recount_bound':rc_bound,'recount_words_checked':(rc or {}).get('words_checked'),'recount_words_unsound':(rc or {}).get('words_unsound'),
         'recount_truth_inconsistent':(rc or {}).get('truth_inconsistent')}
    gate('G_sound',complete and rc_bound and snd['words_unsound']==0 and snd['recount_words_unsound']==0 and snd['recount_truth_inconsistent']==0
         and snd['recount_words_checked']==snd['words_checked'],snd,why=wb or (None if rc_bound else 'INCOMPLETE_INPUT (RECOUNT_043 missing or unbound)'))
    # G10
    g10=[(c['seed'],{a:(rlab(c,a) if rlab(c,a) is not None else c['arms'][a]['label']) for a in ARMS}) for c in G('control')]
    gate('G10',complete and len(g10)==exp['control'] and all(all(L=='ID' for L in x[1].values()) for x in g10),{'cases':g10,'rule':'every arm ID on every control'},why=wb)
    # GS_ref
    mt=(ref or {}).get('mutation_test') or {}
    robs=None if not ref else {k:ref.get(k) for k in ('block','arm','key','records','decided','decided_by_key','records_by_key','not_reached','k_spent_as_amb','verdicts_checked','mismatch_count','PASS')}|{'mutations':mt.get('detected'),'of':mt.get('mutations')}
    rbase=(bool(ref) and ref.get('study_results_sha256')==rsha and ref.get('block')=='main' and ref.get('arm')=='A16' and ref.get('key')==['lowobs12','scale16_rep']
           and ref.get('records')==nlo+n16 and mt.get('detected')==mt.get('mutations')==20 and ref.get('mismatch_count')==0 and (ref.get('decided') or 0)>0)
    gate('GS_ref',rbase and ref.get('PASS') is True,robs,why=wb or (None if ref else 'INCOMPLETE_INPUT (REFERENCE_043 missing)'))
    # GTI
    mods=(ts or {}).get('per_module') or {};gm=(ts or {}).get('gated_modules') or []
    gate('GTI',bool(gm) and ts.get('passed') is True and all(mods[m].get('returncode')==0 for m in gm),
         None if not ts else {'gated':{m:{'returncode':mods[m].get('returncode'),'tests':mods[m].get('tests')} for m in gm},
                              'reported':{m:{'returncode':v.get('returncode'),'tests':v.get('tests')} for m,v in mods.items() if m not in gm}},
         why=None if ts else 'INCOMPLETE_INPUT (TEST_SUITE_043 missing)')
    # G_PROC
    lt=ledger();ev=[e for e,_ in lt];times=[t for _,t in lt]
    proc={'order':subseq(ev,PROC_ORDER),'ledger_times_parse':bool(lt) and all(t is not None for t in times),
          'ledger_times_non_decreasing':all(a<=b for a,b in zip(times,times[1:]) if a and b),'commit_order_file':order is not None,'main_sealed':bool(sealed)}
    gate('G_PROC',all(proc.values()),{'clauses':proc,'events':ev,'required_order':list(PROC_ORDER)})
    el=(res or {}).get('total_elapsed_informational')
    gate('G_RT',complete and el is not None and el<=CAP,{'elapsed_s':el,'cap_s':CAP,'cases':len(allc)},why=wb)
    gate('G_recount',complete and rc_ok,None if not rc else {k:rc.get(k) for k in ('cases','labels_main','amb_rule_applied','words_checked','words_unsound','truth_inconsistent','mismatching_cases','PASS')},
         why=wb or (None if rc else 'INCOMPLETE_INPUT (RECOUNT_043 missing)'))
    # secondary
    rr=[];drop=[]
    for c in allc:
        a=[x['wall'] for x in c['arms']['A16']['calls']];b=[x['wall'] for x in c['arms']['A14']['calls']]
        if not a or not b or sum(b)<=0:drop.append(ckey(c));continue
        rr.append((ckey(c),c['key'],(sum(a)/len(a))/(sum(b)/len(b))))
    vals=[x for *_,x in rr];ci=boot(vals)
    sec['GT17']={'pass':None,'observed':{'cases':len(rr),'dropped':drop,'mean_ratio':round(sum(vals)/len(vals),4) if vals else None,'ci95_seed_bootstrap':ci,
                 'H3_upper_below_2':None if ci is None else ci[1]<2,
                 'by_key':{k:{'cases':len([1 for _,kk,_ in rr if kk==k]),'mean_ratio':round(sum(x for _,kk,x in rr if kk==k)/max(1,len([1 for _,kk,_ in rr if kk==k])),4),
                              'ci95':boot([x for _,kk,x in rr if kk==k])} for k in exp},'per_case':[[i,round(x,4)] for i,_,x in rr]},
                 'rule':'reported: per-case mean call wall A16 / A14, mean over cases, seed-bootstrap 95% CI'}
    ph={}
    for c in allc:
        for a,ar in c['arms'].items():
            for p,b in ar['by_phase'].items():x=ph.setdefault(f"{a}/{c['key']}/{p}",[0,0]);x[0]+=b['calls'];x[1]+=b['capped']
    sec['GPH18']={'pass':None,'observed':{k:{'calls':v[0],'capped':v[1]} for k,v in sorted(ph.items())},'rule':'reported: calls / capped calls by phase'}
    sec['GLO_cause']={'pass':None,'observed':{f"{c['seed']}/{a}":{'stop':x['stop'],'label':lab(c,a),'n_min':x['n_min'],'used':x['used'],
                      'n_rounds':x['n_rounds'],'capped_calls':sum(b['capped'] for b in x['by_phase'].values()),'last_phase':x['last_phase'],
                      'query_max_s':x['query_max_s']} for c in G('lowobs12') for a,x in c['arms'].items()},
                      'rule':'reported: per lowobs12 case and arm, the stop and what bound it (read by plan 043 next_if_fail only)'}
    fl={f'{a}/{k}':{L:{'x':cnt(k,a,L),'n':len(G(k)),'ci95':wilson(cnt(k,a,L),len(G(k))) if G(k) else None} for L in LABELS} for a in ARMS for k in exp}
    return {'schema':'brute.gates.v40_0','study':'BRUTE-0400-A16-LOWOBS-043','process':'lean','sealed_input_verified':sealed,'label_source':lsrc,'gates':Gt,
            'secondary':sec,'all_gated_pass':all(g['pass'] for g in Gt.values() if g['pass'] is not None),
            'failed':[k for k,g in Gt.items() if g['pass'] is False],'not_exercised':[k for k,g in Gt.items() if g['pass'] is None],
            'reports':{'fresh_labels':fl} if allc else {}}


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--study-dir',default=str(STUDY_DIR));ap.add_argument('--check',action='store_true');a=ap.parse_args()
    obj=build(Path(a.study_dir));out=Path(a.study_dir)/'GATES_043.json'
    if a.check:check(out.read_bytes()==dumps(obj),'GATES_043.json does not reproduce');print('GATES_043 reproduces')
    else:write_new(out,obj);print(json.dumps({k:v['pass'] for k,v in obj['gates'].items()}),obj['failed'])
