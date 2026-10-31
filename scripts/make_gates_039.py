"""Gates for study-039 (BRUTE_PLAN_039; deviation #150 definitions), LEAN process.
Committed in the source freeze before run_start_039; nothing is tuned after results are seen. New file; built from
scripts/make_gates_038.py (frozen, unchanged).
Inputs (D = results/study-039): D/main/{RESULTS,SCIENTIFIC,SEAL}.json (54 cases: scale16 12, scale14 12, scale12 12,
perm12 12, control 6), D/main/RECOUNT_039.json, D/main/REFERENCE_039.json, D/TEST_SUITE_039.json,
experiments/COMMIT_ORDER_039.json, results/RESEARCH_LEDGER.jsonl. Missing or partial input => every data gate FAIL
INCOMPLETE_INPUT. Case records are accepted only if sha256(RESULTS) equals the seal and no_time(RESULTS) equals SCIENTIFIC,
and every case carries exactly the arms its key is run with (experiments.brute_study_039.plan_groups).
Definitions (deviation #150):
  label(arm, case) as recounted by RECOUNT_039; IDF is not ID;
  GC14 a: recounted WRONG = 0 for A14 and A14_k64 on every case, and every arm's stored label equals its recount;
       b: ID + IDF (A14, scale16) >= 4 of 12;
       c: paired over the 12 scale16 seeds, mean ID(A14) - ID(A9) >= 0.25 and seed-bootstrap 95% CI lower end > 0
          (10000 resamples, random.Random(34) via make_gates_034.boot_mean);
       d: ID + IDF (A14, scale14) >= 6 of 12;
  GFAM14: ID + IDF (A14, perm12) >= 6 of 12 and recounted WRONG 0 for A14 and A14_k64 on perm12;
  GREP14: ID + IDF (A14, scale12) >= ID + IDF (A9, scale12) - 1;
  GCH14: paired ID(A14) - ID(A14_random) over the 24 scale14 + scale16 seeds >= 0.17 and bootstrap CI lower end > 0;
  GINC14: TEST_SUITE_039 module test_scalesearch14_0360 returncode 0 with test_GINC14_sealed_034_traces 'ok' (Exact, inside GTI);
  GQB14: max query wall <= 10.5 s for A14, A14_k64 and A14_random on every case (A9 reported, not gated);
  G_sound: study and recount words_unsound 0 over A14, A14_k64 and A9, recount words_checked equal to the study's, 0 truth
     inconsistencies in the recount;
  G10: every arm run on a control case is ID on it (6/6 each);
  GS_ref: REFERENCE_039 audits A14 on the 12 scale14 cases: 0 mismatches, decided > 0, mutations 20/20;
  G_RT: total elapsed <= 1800 s; G_recount: RECOUNT_039 PASS on the sealed RESULTS; GTI: TEST_SUITE_039 all modules 0;
  G_PROC: ledger events preregistration, build_authorization, seedcheck, source_freeze, run_start, run_end, recount,
     reference, tests (039) present, in order, parseable non-decreasing times, the commit-order file present and main sealed.
  GK14 (secondary, reported): paired ID(A14) - ID(A14_k64) and ID(A14_k64) - ID(A9) on scale16 (and every key run).
  GACT14 (secondary, reported): extra actions used and K_spent counts per arm and key.
Reports (not gated): labels with Wilson CIs per (arm, key); used, rounds, capped, queries, query max, wall per (arm, key)
  with bootstrap CIs; stops; paired contrasts; incremental-instance guards and sizes.
  PYTHONPATH=. python scripts/make_gates_039.py [--study-dir D] [--check]"""
from __future__ import annotations
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common_039 import STUDY_DIR,PLAN,load,dumps,write_new,check,sha,wilson
from experiments.brute_study_039 import plan_groups,GROUP_ARMS,ORDER
from scripts.make_gates_034 import opt,boot_mean

EXPECTED={'scale16':12,'scale14':12,'scale12':12,'perm12':12,'control':6}
CAP=1800;QB=10.5;C_DIFF=0.25;CH_DIFF=0.17;B_MIN=4;D_MIN=6;FAM_MIN=6
ARMS=ORDER;NO_WRONG=('A14','A14_k64');QB_ARMS=('A14','A14_k64','A14_random');ACTIVE=('A14','A14_k64','A9')
LABELS=('ID','IDF','AMB','WRONG','IDU')
PROC_ORDER=('preregistration_039','build_authorization_039','seedcheck_039','source_freeze_039','run_start_039','run_end_039','recount_039',
            'reference_039','tests_039')
GINC_MOD='test_scalesearch14_0360';GINC_TEST='test_GINC14_sealed_034_traces'


def _key(c):return f"{c['block']}/{c['key']}/{c['seed']}"
def rec(c,arm,pc):return (pc.get(_key(c)) or {}).get(arm) or {}
def lab(c,arm,pc):return rec(c,arm,pc).get('label')
def arms_of(k):G=plan_groups(load(PLAN))[k];return tuple(a for a in ARMS if any(a in GROUP_ARMS[g] for g in G))
def has(cases,arm):return [c for c in cases if arm in c['arms']]


def counts(cases,arm,pc):
    cases=has(cases,arm);n=len(cases);out={'n':n}
    for L in LABELS:x=sum(1 for c in cases if lab(c,arm,pc)==L);out[L]={'x':x,'rate':x/n if n else None,'ci95':wilson(x,n) if n else None}
    x=out['ID']['x']+out['IDF']['x'] if n else 0;out['ID+IDF']={'x':x,'ci95':wilson(x,n) if n else None};return out


def paired(cases,x,y,pc,L='ID'):
    cs=sorted([c for c in cases if x in c['arms'] and y in c['arms']],key=lambda c:(c['key'],c['seed']))
    d=[int(lab(c,x,pc)==L)-int(lab(c,y,pc)==L) for c in cs]
    return d,(sum(d)/len(d) if d else None),boot_mean(d)


def _mean(v):v=[x for x in v if x is not None];return None if not v else round(sum(v)/len(v),3)
def _stat(v):v=[x for x in v if x is not None];return {'mean':_mean(v),'ci95_bootstrap':boot_mean(v) if v else None,'n':len(v)}
def idf(cases,arm,pc):return sum(1 for c in has(cases,arm) if lab(c,arm,pc) in ('ID','IDF'))


def ledger():
    from datetime import datetime
    L=[json.loads(x) for x in (ROOT/'results/RESEARCH_LEDGER.jsonl').read_text().splitlines() if x.strip()]
    i0=next((i for i,e in enumerate(L) if e.get('event')=='preregistration_039'),None);out=[]
    for e in (L[i0:] if i0 is not None else []):
        try:t=datetime.fromisoformat(str(e.get('note',''))[:25])
        except ValueError:t=None
        out.append((e['event'],t))
        if e['event']==PROC_ORDER[-1]:break
    return out


def act_stats(cases,arm):
    cs=sorted(has(cases,arm),key=lambda c:c['seed'])
    return {'used':_stat([c['arms'][arm].get('used') for c in cs]),'used_per_seed':[c['arms'][arm].get('used') for c in cs],
            'K_spent':sum(1 for c in cs if c['arms'][arm]['stop']=='K_spent'),'cases':len(cs)}


def reports(allc,res,pc):
    G=lambda k:[c for c in allc if c['key']==k];S=lambda k:sorted(G(k),key=lambda c:c['seed']);r={}
    AK=[(a,k) for a in ARMS for k in EXPECTED if has(G(k),a)]
    r['labels']={f'{a}/{k}':counts(G(k),a,pc) for a,k in AK}
    r['cost']={f'{a}/{k}':{f:_stat([c['arms'][a].get(f) for c in has(G(k),a)]) for f in ('used','n_rounds','capped','queries','query_max_s','arm_wall_informational','T_final')}
               for a,k in AK}
    r['labels_per_seed']={f'{a}/{k}':[lab(c,a,pc) for c in has(S(k),a)] for a,k in AK}
    r['stops']={f'{a}/{k}':{s:sum(1 for c in has(G(k),a) if c['arms'][a]['stop']==s) for s in sorted({c['arms'][a]['stop'] for c in has(G(k),a)})} for a,k in AK}
    r['n_min']={f'{a}/{k}':[c['arms'][a].get('n_min') for c in has(S(k),a)] for a,k in AK}
    r['truth_reachable']={k:[c['truth_reachable'] for c in S(k)] for k in EXPECTED}
    con={}
    for x,y in (('A14','A9'),('A14','A14_random'),('A14','A14_k64'),('A14_k64','A9')):
        for k in EXPECTED:
            d,m,ci=paired(G(k),x,y,pc,'ID')
            if d:con[f'ID({x})-ID({y})/{k}']={'mean':round(m,4),'ci95_seed_bootstrap':ci,'per_seed':d}
    r['contrasts']=con
    r['query_max_s']={f'{a}/{k}':max([c['arms'][a]['query_max_s'] or 0 for c in has(G(k),a)],default=None) for a,k in AK}
    r['inc_guards']={f'{a}/{k}':_stat([c['arms'][a].get('inc_guards') for c in has(G(k),a)]) for a,k in AK if a in NO_WRONG}
    r['group_wall_mean_s']={f'{g}/{k}':_mean([c['group_walls_informational'].get(g) for c in G(k)]) for g in GROUP_ARMS for k in EXPECTED}
    return r


def build(study=STUDY_DIR):
    from brute.evaluation import no_time
    study=Path(study);D=study/'main';Gt={};sec={}
    seal=opt(D/'SEAL.json');sci=opt(D/'SCIENTIFIC.json');res=opt(D/'RESULTS.json');rc=opt(D/'RECOUNT_039.json')
    ref=opt(D/'REFERENCE_039.json');ts=opt(study/'TEST_SUITE_039.json');order=opt(ROOT/'experiments/COMMIT_ORDER_039.json')
    rsha=sha(D/'RESULTS.json') if (D/'RESULTS.json').exists() else None
    sealed=(bool(seal) and res is not None and sci is not None and rsha==seal.get('results_sha256')
            and sha(D/'SCIENTIFIC.json')==seal.get('scientific_sha256') and no_time(res)==sci)
    allc=(res or {}).get('cases',[]) if sealed else []
    G=lambda k:[c for c in allc if c['key']==k and c['block']=='main']
    complete=(sealed and seal.get('complete') is True and all(len(G(k))==n for k,n in EXPECTED.items()) and len(allc)==sum(EXPECTED.values())
              and all(set(c['arms'])==set(arms_of(c['key'])) for c in allc))
    wb=None if complete else 'INCOMPLETE_INPUT (main missing, partial, missing arms or not matching its seal)'
    def gate(name,ok,obs,why=None,into=Gt):into[name]={'pass':bool(ok) and why is None,'observed':obs,**({'reason':why} if why else {})}
    pc=(rc or {}).get('per_case') or {}
    rc_ok=bool(rc) and rc.get('PASS') is True and rc.get('results_sha256')==rsha and rc.get('cases')==len(allc)
    mism=[(_key(c),a) for c in allc for a in c['arms'] if lab(c,a,pc)!=c['arms'][a]['label']]
    wrong=[(_key(c),a) for c in allc for a in NO_WRONG if a in c['arms'] and lab(c,a,pc)=='WRONG']
    wrong_out=[(_key(c),a) for c in allc for a in c['arms'] if a not in NO_WRONG and lab(c,a,pc)=='WRONG']
    a_ok=complete and rc_ok and not wrong and not mism
    s16=G('scale16');s14=G('scale14');b=idf(s16,'A14',pc);b_ok=complete and rc_ok and b>=B_MIN
    dc,mc,cic=paired(s16,'A14','A9',pc);c_ok=complete and rc_ok and mc is not None and mc>=C_DIFF and cic[0]>0
    d=idf(s14,'A14',pc);d_ok=complete and rc_ok and d>=D_MIN
    gate('GC14_headline',a_ok and b_ok and c_ok and d_ok,{
        'a':{'pass':a_ok,'WRONG_gated':wrong,'WRONG_other_arms_reported':wrong_out,'label_mismatch':mism,'recount_pass':rc_ok,
             'rule':'recounted WRONG = 0 for A14 and A14_k64 on every case, no recount label mismatch'},
        'b':{'pass':b_ok,'ID_plus_IDF_A14_scale16':b,'of':len(s16),'ci95':wilson(b,len(s16)) if s16 else None,'rule':'>= 4/12'},
        'c':{'pass':c_ok,'mean_diff_ID_A14_minus_A9_scale16':None if mc is None else round(mc,4),'ci95_seed_bootstrap':cic,'per_seed':dc,
             **{f'labels_{a}_scale16':counts(s16,a,pc) for a in ARMS},'rule':'mean(ID A14 - ID A9, scale16) >= 0.25 and CI lower > 0'},
        'd':{'pass':d_ok,'ID_plus_IDF_A14_scale14':d,'of':len(s14),'ci95':wilson(d,len(s14)) if s14 else None,'rule':'>= 6/12'}},why=wb)
    p12=G('perm12');fp=idf(p12,'A14',pc);fw=[(_key(c),a) for c in p12 for a in NO_WRONG if a in c['arms'] and lab(c,a,pc)=='WRONG']
    gate('GFAM14',complete and rc_ok and fp>=FAM_MIN and not fw,{'ID_plus_IDF_A14_perm12':fp,'of':len(p12),'ci95':wilson(fp,len(p12)) if p12 else None,
         'WRONG':fw,**{f'labels_{a}_perm12':counts(p12,a,pc) for a in ARMS},'rule':'ID+IDF(A14, perm12) >= 6/12 and WRONG 0 for A14, A14_k64'},why=wb)
    s12=G('scale12');r14=idf(s12,'A14',pc);r9=idf(s12,'A9',pc)
    gate('GREP14',complete and rc_ok and r14>=r9-1,{'ID_plus_IDF_A14_scale12':r14,'ID_plus_IDF_A9_scale12':r9,'of':len(s12),
         **{f'labels_{a}_scale12':counts(s12,a,pc) for a in ARMS},'rule':'ID+IDF(A14) >= ID+IDF(A9) - 1 on scale12'},why=wb)
    dh,mh,cih=paired(s14+s16,'A14','A14_random',pc)
    gate('GCH14',complete and rc_ok and mh is not None and mh>=CH_DIFF and cih[0]>0,{'mean_diff_ID_A14_minus_A14_random':None if mh is None else round(mh,4),
         'ci95_seed_bootstrap':cih,'n':len(dh),'per_seed':dh,'rule':'pooled scale14 + scale16 (n = 24) >= 0.17 and CI lower > 0'},why=wb)
    mods=(ts or {}).get('per_module') or {};gm=mods.get(GINC_MOD) or {}
    gate('GINC14',bool(gm) and gm.get('returncode')==0 and (gm.get('results') or {}).get(GINC_TEST)=='ok',
         None if not gm else {'module':GINC_MOD,'test':GINC_TEST,'result':(gm.get('results') or {}).get(GINC_TEST),'stdout_tail':gm.get('stdout_tail')},
         why=None if ts else 'INCOMPLETE_INPUT (TEST_SUITE_039 missing)')
    qb=[(_key(c),a,round(c['arms'][a]['query_max_s'] or 0,3)) for c in allc for a in QB_ARMS if a in c['arms']];worst=max([q for *_,q in qb],default=None)
    gate('GQB14',complete and worst is not None and worst<=QB,{'max_s':worst,'bound_s':QB,'over':[x for x in qb if x[2]>QB],
         **{f'{a}_max_s':max([c['arms'][a]['query_max_s'] or 0 for c in has(allc,a)],default=None) for a in ARMS}},why=wb)
    snd={'words_checked':sum(c['arms'][a].get('words_checked',0) if a!='A9' else sum(1 for x in c['arms'][a]['rounds'] if x.get('word'))
                             for c in allc for a in ACTIVE if a in c['arms']),
         'words_unsound':sum(c['arms'][a].get('words_unsound',0) if a!='A9' else sum(1 for x in c['arms'][a]['rounds'] if x.get('word') and not x.get('word_sound'))
                             for c in allc for a in ACTIVE if a in c['arms']),
         'recount_words_checked':(rc or {}).get('words_checked'),'recount_words_unsound':(rc or {}).get('words_unsound'),
         'recount_truth_inconsistent':(rc or {}).get('truth_inconsistent')}
    gate('G_sound',complete and rc_ok and snd['words_unsound']==0 and snd['recount_words_unsound']==0 and snd['recount_truth_inconsistent']==0
         and snd['recount_words_checked']==snd['words_checked'],snd,why=wb)
    g10=[(c['seed'],{a:lab(c,a,pc) for a in c['arms']}) for c in G('control')]
    gate('G10',complete and rc_ok and len(g10)==6 and all(all(L=='ID' for L in x[1].values()) for x in g10),{'cases':g10,'rule':'every arm ID on every control'},why=wb)
    mt=(ref or {}).get('mutation_test') or {}
    robs=None if not ref else {k:ref.get(k) for k in ('arm_audited','family','N','cases','decided','not_reached','verdicts_checked','words_checked','mismatch_count','PASS')}|{'mutations':mt.get('detected'),'of':mt.get('mutations')}
    rbase=(bool(ref) and ref.get('study_results_sha256')==rsha and ref.get('cases')==len(s14) and ref.get('arm_audited')=='A14' and ref.get('family')=='scale14'
           and mt.get('detected')==mt.get('mutations')==20 and ref.get('mismatch_count')==0 and (ref.get('decided') or 0)>0)
    gate('GS_ref',rbase and ref.get('PASS') is True,robs,why=wb or (None if ref else 'INCOMPLETE_INPUT (REFERENCE_039 missing)'))
    gate('GTI',bool(mods) and ts.get('passed') is True and all(v.get('returncode')==0 for v in mods.values()),
         None if not ts else {k:{'returncode':v.get('returncode'),'tests':v.get('tests')} for k,v in mods.items()},why=None if ts else 'INCOMPLETE_INPUT (TEST_SUITE_039 missing)')
    lt=ledger();ev=[e for e,_ in lt];times=[t for _,t in lt];pos={e:ev.index(e) for e in PROC_ORDER if e in ev}
    proc={'all_events':len(pos)==len(PROC_ORDER),'order':len(pos)==len(PROC_ORDER) and all(pos[a]<pos[b] for a,b in zip(PROC_ORDER,PROC_ORDER[1:])),
          'ledger_times_parse':bool(lt) and all(t is not None for t in times),'ledger_times_non_decreasing':all(a<=b for a,b in zip(times,times[1:]) if a and b),
          'commit_order_file':order is not None,'main_sealed':bool(sealed)}
    gate('G_PROC',all(proc.values()),{'clauses':proc,'events':ev})
    el=(res or {}).get('total_elapsed_informational')
    gate('G_RT',complete and el is not None and el<=CAP,{'elapsed_s':el,'cap_s':CAP,'cases':len(allc)},why=wb)
    gate('G_recount',complete and rc_ok,None if not rc else {k:rc.get(k) for k in ('cases','labels','words_checked','words_unsound','mismatching_cases','PASS')},
         why=wb or (None if rc else 'INCOMPLETE_INPUT (RECOUNT_039 missing)'))
    gk={}
    for x,y in (('A14','A14_k64'),('A14_k64','A9')):
        for k in EXPECTED:
            dd,m,ci=paired(G(k),x,y,pc)
            if dd:gk[f'ID({x})-ID({y})/{k}']={'mean':round(m,4),'ci95_seed_bootstrap':ci,'per_seed':dd}
    sec['GK14']={'pass':None,'observed':gk,'rule':'reported, not gated: budget effect A14 - A14_k64, incremental effect A14_k64 - A9'}
    sec['GACT14']={'pass':None,'observed':{f'{a}/{k}':act_stats(G(k),a) for a in ARMS for k in EXPECTED if has(G(k),a)},
                   'rule':'reported: extra actions used and K_spent counts per arm and family'}
    return {'schema':'brute.gates.v36_0','study':'BRUTE-0360-CLEAN-SCALE-039','process':'lean','sealed_input_verified':sealed,'gates':Gt,
            'secondary':sec,'all_gated_pass':all(g['pass'] for g in Gt.values() if g['pass'] is not None),
            'failed':[k for k,g in Gt.items() if g['pass'] is False],'not_exercised':[k for k,g in Gt.items() if g['pass'] is None],
            'reports':reports(allc,res,pc) if allc else {}}


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--study-dir',default=str(STUDY_DIR));ap.add_argument('--check',action='store_true');a=ap.parse_args()
    obj=build(Path(a.study_dir));out=Path(a.study_dir)/'GATES_039.json'
    if a.check:check(out.read_bytes()==dumps(obj),'GATES_039.json does not reproduce');print('GATES_039 reproduces')
    else:write_new(out,obj);print(json.dumps({k:v['pass'] for k,v in obj['gates'].items()}),obj['failed'])
