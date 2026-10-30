"""Gates for study-035 (BRUTE_PLAN_035; deviation #142 definitions), LEAN process.
Committed in the source freeze before run_start_035; nothing is tuned after results are seen. New file; built from
scripts/make_gates_034.py (frozen, unchanged).
Inputs (D = results/study-035): D/main/{RESULTS,SCIENTIFIC,SEAL}.json (48 cases: noisy_scale8 12, noisy_scale12 12,
clean_scale12 12, scale16_clean 6, control 6), D/main/RECOUNT_035.json, D/main/REFERENCE_035.json, D/TEST_SUITE_035.json,
experiments/COMMIT_ORDER_035.json, results/RESEARCH_LEDGER.jsonl. Missing or partial input => every data gate FAIL
INCOMPLETE_INPUT. Case records are accepted only if sha256(RESULTS) equals the seal and no_time(RESULTS) equals SCIENTIFIC.
Definitions (deviation #142):
  label(arm, case) in ID / IDF / AMB / WRONG / IDU as recounted by RECOUNT_035; clean cases = clean_scale12, scale16_clean,
  control; within(arm, case) = the recounted truth flips over that arm's final trace <= B_max (27);
  GA10 a: for each of A10, S7 and S5, recounted WRONG = 0 on every clean case and every noisy case within(arm), and every
     arm's stored label equals its recount; b: paired over the 12 noisy_scale12 seeds, mean ID(A10) - ID(S7) >= 0.25 and
     the seed-bootstrap 95% CI (BOOT resamples, random.Random(BOOT_SEED)) lower end > 0; c: ID + IDF (A10, noisy_scale12)
     >= 4 of 12; d: IDU (A10, noisy_scale12) <= 3 of 12;
  GNR10: A10 label = A9 label on every clean_scale12 and control case, and A10 B_final = 0 on every clean case;
  GAD10: paired mean ID(A10) - ID(A10_fixed) >= 0 on noisy_scale12, and >= 0.17 with CI lower > 0 on clean_scale12;
  G16 (secondary; not in all_gated_pass and not in failed, reported under secondary): ID(A10, scale16_clean) >= 2 of 6
     and WRONG 0, Wilson CI;
  GQB10: every arm's max SAT query wall <= 10.5 s on every case;
  G_sound: A10 / A10_fixed separating words: study and recount words_unsound 0 with equal counts, both machines of every
     word fit the round's trace under its B (M1_fits, M2_fits), every stored model fits its trace (recount PASS);
  G10: A10 and S5 ID on every control case (6/6);
  GS_ref: REFERENCE_035 audits A10 on the 12 noisy_scale8 cases: PASS (0 mismatches, decided > 0, mutations 20/20); if
     there are 0 mismatches and 20/20 mutations but 0 decided items, status 'not exercised' (pass None);
  G_RT: total elapsed <= 1800 s; G_recount: RECOUNT_035 PASS on the sealed RESULTS; GTI: TEST_SUITE_035 all modules 0;
  G_PROC: ledger events preregistration, build_authorization, seedcheck, source_freeze, run_start, run_end (035) present,
     in order, parseable non-decreasing times, the commit-order file present and the main block sealed.
Reports (not gated): labels with Wilson CIs per (arm, key); budget used (extra actions, reads); A10 B_final and B
  histories; within-budget counts; paired contrasts; query max; stops.
  PYTHONPATH=. python scripts/make_gates_035.py [--study-dir D] [--check]"""
from __future__ import annotations
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common_035 import STUDY_DIR,load,dumps,write_new,check,sha,wilson
from scripts.make_gates_034 import opt,boot_mean

EXPECTED={'noisy_scale8':12,'noisy_scale12':12,'clean_scale12':12,'scale16_clean':6,'control':6}
CLEAN=('clean_scale12','scale16_clean','control');NOISY=('noisy_scale8','noisy_scale12')
CAP=1800;QB=10.5;B_S7=0.25;B_FIX=0.17;IDF_MIN=4;IDU_MAX=3;ID16=2;B_MAX=27
ARMS=('A10','A10_fixed','A9','S7','S5');LABELS=('ID','IDF','AMB','WRONG','IDU');NO_WRONG=('A10','S7','S5')
PROC_ORDER=('preregistration_035','build_authorization_035','seedcheck_035','source_freeze_035','run_start_035','run_end_035')


def _key(c):return f"{c['block']}/{c['key']}/{c['seed']}"
def rec(c,arm,pc):return (pc.get(_key(c)) or {}).get(arm) or {}
def lab(c,arm,pc):return rec(c,arm,pc).get('label')


def counts(cases,arm,pc):
    n=len(cases);out={'n':n}
    for L in LABELS:x=sum(1 for c in cases if lab(c,arm,pc)==L);out[L]={'x':x,'rate':x/n if n else None,'ci95':wilson(x,n)}
    return out


def paired(cases,x,y,pc):
    cs=sorted(cases,key=lambda c:c['seed']);d=[int(lab(c,x,pc)=='ID')-int(lab(c,y,pc)=='ID') for c in cs]
    return d,(sum(d)/len(d) if d else None),boot_mean(d)


def _mean(v):return None if not v else round(sum(v)/len(v),3)


def ledger():
    from datetime import datetime
    L=[json.loads(x) for x in (ROOT/'results/RESEARCH_LEDGER.jsonl').read_text().splitlines() if x.strip()]
    i0=next((i for i,e in enumerate(L) if e.get('event')=='preregistration_035'),None);out=[]
    for e in (L[i0:] if i0 is not None else []):
        try:t=datetime.fromisoformat(str(e.get('note',''))[:25])
        except ValueError:t=None
        out.append((e['event'],t))
        if e['event']=='run_end_035':break
    return out


def reports(allc,res,pc):
    G=lambda k:[c for c in allc if c['key']==k];r={}
    r['labels']={f'{a}/{k}':counts(G(k),a,pc) for a in ARMS for k in EXPECTED}
    r['budget_used']={f'{a}/{k}':{'extra_actions_mean':_mean([c['arms'][a]['used'] for c in G(k)]),
        'reads_mean':_mean([c['arms'][a].get('reads') for c in G(k)]) if a in ('A10','A10_fixed') else None,
        'per_seed':[c['arms'][a]['used'] for c in sorted(G(k),key=lambda c:c['seed'])]} for a in ('A10','A10_fixed','A9') for k in EXPECTED}
    r['A10_B_final']={k:[c['arms']['A10']['B_final'] for c in sorted(G(k),key=lambda c:c['seed'])] for k in EXPECTED}
    r['A10_B_history']={k:[c['arms']['A10']['B_history'] for c in sorted(G(k),key=lambda c:c['seed'])] for k in EXPECTED}
    r['prefix_truth_flips']={k:[c['prefix_truth_flips'] for c in sorted(G(k),key=lambda c:c['seed'])] for k in EXPECTED}
    r['within_budget']={f'{a}/{k}':sum(1 for c in G(k) if rec(c,a,pc).get('within_budget')) for a in ARMS for k in EXPECTED}
    r['stops']={f'{a}/{k}':{s:sum(1 for c in G(k) if c['arms'][a]['stop']==s) for s in sorted({c['arms'][a]['stop'] for c in G(k)})} for a in ARMS for k in EXPECTED}
    con={}
    for x,y in (('A10','S7'),('A10','A10_fixed'),('A10','A9'),('A10','S5'),('A9','S5'),('A10_fixed','S7')):
        for k in EXPECTED:
            d,m,ci=paired(G(k),x,y,pc);con[f'ID({x})-ID({y})/{k}']={'mean':None if m is None else round(m,4),'ci95_seed_bootstrap':ci,'per_seed':d}
    r['contrasts']=con
    r['query_max_s']={f'{a}/{k}':max([c['arms'][a]['query_max_s'] or 0 for c in G(k)],default=None) for a in ARMS for k in EXPECTED}
    r['arm_wall_mean_s']={f'{a}/{k}':_mean([c['arms'][a]['arm_wall_informational'] for c in G(k)]) for a in ARMS for k in EXPECTED}
    r['mean_case_wall']=None if not res or not res['cases'] else round(sum(c['case_wall_informational'] for c in res['cases'])/len(res['cases']),1)
    return r


def build(study=STUDY_DIR):
    from brute.evaluation import no_time
    study=Path(study);D=study/'main';Gt={};sec={}
    seal=opt(D/'SEAL.json');sci=opt(D/'SCIENTIFIC.json');res=opt(D/'RESULTS.json');rc=opt(D/'RECOUNT_035.json')
    ref=opt(D/'REFERENCE_035.json');ts=opt(study/'TEST_SUITE_035.json');order=opt(ROOT/'experiments/COMMIT_ORDER_035.json')
    rsha=sha(D/'RESULTS.json') if (D/'RESULTS.json').exists() else None
    sealed=(bool(seal) and res is not None and sci is not None and rsha==seal.get('results_sha256')
            and sha(D/'SCIENTIFIC.json')==seal.get('scientific_sha256') and no_time(res)==sci)
    allc=(res or {}).get('cases',[]) if sealed else []
    G=lambda k:[c for c in allc if c['key']==k and c['block']=='main']
    complete=sealed and seal.get('complete') is True and all(len(G(k))==n for k,n in EXPECTED.items()) and len(allc)==sum(EXPECTED.values())
    wb=None if complete else 'INCOMPLETE_INPUT (main missing, partial or not matching its seal)'
    def gate(name,ok,obs,why=None,into=Gt):into[name]={'pass':bool(ok) and why is None,'observed':obs,**({'reason':why} if why else {})}
    pc=(rc or {}).get('per_case') or {}
    rc_ok=bool(rc) and rc.get('PASS') is True and rc.get('results_sha256')==rsha and rc.get('cases')==len(allc)
    mism=[(_key(c),a) for c in allc for a in ARMS if lab(c,a,pc)!=c['arms'][a]['label']]
    gated={a:[c for c in allc if c['key'] in CLEAN or rec(c,a,pc).get('within_budget') is True] for a in NO_WRONG}
    wrong=[(_key(c),a) for a in NO_WRONG for c in gated[a] if lab(c,a,pc)=='WRONG']
    wrong_out=[(_key(c),a) for c in allc for a in ARMS if lab(c,a,pc)=='WRONG' and not (a in NO_WRONG and c in gated[a])]
    a_ok=complete and rc_ok and not wrong and not mism
    n12=G('noisy_scale12');d7,m7,ci7=paired(n12,'A10','S7',pc)
    b_ok=complete and rc_ok and m7 is not None and m7>=B_S7 and ci7[0]>0
    c12=counts(n12,'A10',pc);idf=c12['ID']['x']+c12['IDF']['x']
    c_ok=complete and rc_ok and idf>=IDF_MIN;d_ok=complete and rc_ok and c12['IDU']['x']<=IDU_MAX
    gate('GA10_headline',a_ok and b_ok and c_ok and d_ok,{
        'a':{'pass':a_ok,'WRONG_gated':wrong,'WRONG_not_gated_reported':wrong_out,'label_mismatch':mism,'recount_pass':rc_ok,
             'gated_cases':{a:len(v) for a,v in gated.items()},'rule':'recounted WRONG = 0 for A10, S7, S5 on clean and within-budget noisy cases'},
        'b':{'pass':b_ok,'mean_diff_ID_A10_minus_S7':None if m7 is None else round(m7,4),'ci95_seed_bootstrap':ci7,'per_seed':d7,
             **{f'labels_{a}_noisy_scale12':counts(n12,a,pc) for a in ARMS},'rule':'mean(ID A10 - ID S7, noisy_scale12) >= 0.25 and CI lower > 0'},
        'c':{'pass':c_ok,'ID_plus_IDF_A10_noisy_scale12':idf,'of':len(n12),'ci95':wilson(idf,len(n12)) if n12 else None,'rule':'>= 4/12'},
        'd':{'pass':d_ok,'IDU_A10_noisy_scale12':c12['IDU'],'rule':'<= 3/12'}},why=wb)
    nr=[(_key(c),lab(c,'A10',pc),lab(c,'A9',pc)) for k in ('clean_scale12','control') for c in G(k)]
    bf=[(_key(c),c['arms']['A10']['B_final']) for k in CLEAN for c in G(k)]
    gate('GNR10',complete and rc_ok and all(x[1]==x[2] for x in nr) and all(b==0 for _,b in bf),
         {'label_differences':[x for x in nr if x[1]!=x[2]],'B_final_nonzero':[x for x in bf if x[1]!=0],'cases_compared':len(nr),'clean_cases':len(bf)},why=wb)
    c12c=G('clean_scale12');dn,mn,cin=paired(n12,'A10','A10_fixed',pc);dc,mc,cic=paired(c12c,'A10','A10_fixed',pc)
    gate('GAD10',complete and rc_ok and mn is not None and mn>=0 and mc is not None and mc>=B_FIX and cic[0]>0,
         {'noisy_scale12':{'mean':None if mn is None else round(mn,4),'ci95_seed_bootstrap':cin,'per_seed':dn},
          'clean_scale12':{'mean':None if mc is None else round(mc,4),'ci95_seed_bootstrap':cic,'per_seed':dc},
          'rule':'noisy12 mean >= 0; clean12 mean >= 0.17 and CI lower > 0'},why=wb)
    s16=G('scale16_clean');c16=counts(s16,'A10',pc)
    gate('G16',complete and rc_ok and c16['ID']['x']>=ID16 and c16['WRONG']['x']==0,{'A10_scale16_clean':c16,'rule':'ID >= 2/6 and WRONG 0 (secondary)'},why=wb,into=sec)
    qb=[(_key(c),a,round(c['arms'][a]['query_max_s'] or 0,3)) for c in allc for a in ARMS];worst=max([q for *_,q in qb],default=None)
    gate('GQB10',complete and worst is not None and worst<=QB,{'max_s':worst,'bound_s':QB,'over':[x for x in qb if x[2]>QB],
         **{f'{a}_max_s':max([c['arms'][a]['query_max_s'] or 0 for c in allc],default=None) for a in ARMS}},why=wb)
    rounds=[x for c in allc for a in ('A10','A10_fixed') for x in c['arms'][a]['rounds']]
    snd={'words_checked':sum(c['arms'][a]['words_checked'] for c in allc for a in ('A10','A10_fixed')),
         'words_unsound':sum(c['arms'][a]['words_unsound'] for c in allc for a in ('A10','A10_fixed')),
         'word_machines_unfit':sum(1 for x in rounds if x.get('word') and not (x.get('M1_fits') and x.get('M2_fits'))),
         'recount_words_checked':(rc or {}).get('words_checked'),'recount_words_unsound':(rc or {}).get('words_unsound'),
         'truth_over_Bmax_rounds_reported':sum(c['arms'][a]['truth_over_Bmax_rounds'] for c in allc for a in ('A10','A10_fixed'))}
    gate('G_sound',complete and rc_ok and snd['words_unsound']==0 and snd['word_machines_unfit']==0 and snd['recount_words_unsound']==0
         and snd['recount_words_checked']==snd['words_checked'],snd,why=wb)
    g10=[(c['seed'],lab(c,'A10',pc),lab(c,'S5',pc)) for c in G('control')]
    gate('G10',complete and rc_ok and len(g10)==6 and all(x[1]=='ID' and x[2]=='ID' for x in g10),{'cases':g10,'rule':'A10 and S5 ID on every control'},why=wb)
    mt=(ref or {}).get('mutation_test') or {}
    robs=None if not ref else {k:ref.get(k) for k in ('arm_audited','key','cases','decided_items','undecided_items','labels_checked','mismatch_count','PASS')}|{'mutations':mt.get('detected'),'of':mt.get('mutations')}
    rbase=bool(ref) and ref.get('study_results_sha256')==rsha and ref.get('cases')==len(G('noisy_scale8')) and ref.get('arm_audited')=='A10' and mt.get('detected')==mt.get('mutations')==20 and ref.get('mismatch_count')==0
    if not wb and ref and rbase and ref.get('decided_items')==0:Gt['GS_ref']={'pass':None,'status':'not exercised','observed':robs}
    else:gate('GS_ref',rbase and ref.get('PASS') is True,robs,why=wb or (None if ref else 'INCOMPLETE_INPUT (REFERENCE_035 missing)'))
    mods=(ts or {}).get('per_module') or {}
    gate('GTI',bool(mods) and ts.get('passed') is True and all(v.get('returncode')==0 for v in mods.values()),
         None if not ts else {k:{'returncode':v.get('returncode'),'tests':v.get('tests')} for k,v in mods.items()},why=None if ts else 'INCOMPLETE_INPUT (TEST_SUITE_035 missing)')
    lt=ledger();ev=[e for e,_ in lt];times=[t for _,t in lt];pos={e:ev.index(e) for e in PROC_ORDER if e in ev}
    proc={'all_events':len(pos)==len(PROC_ORDER),'order':len(pos)==len(PROC_ORDER) and all(pos[a]<pos[b] for a,b in zip(PROC_ORDER,PROC_ORDER[1:])),
          'ledger_times_parse':bool(lt) and all(t is not None for t in times),'ledger_times_non_decreasing':all(a<=b for a,b in zip(times,times[1:]) if a and b),
          'commit_order_file':order is not None,'main_sealed':bool(sealed)}
    gate('G_PROC',all(proc.values()),{'clauses':proc,'events':ev})
    el=(res or {}).get('total_elapsed_informational')
    gate('G_RT',complete and el is not None and el<=CAP,{'elapsed_s':el,'cap_s':CAP,'cases':len(allc)},why=wb)
    gate('G_recount',complete and rc_ok,None if not rc else {k:rc.get(k) for k in ('cases','labels','words_checked','words_unsound','mismatching_cases','PASS')},
         why=wb or (None if rc else 'INCOMPLETE_INPUT (RECOUNT_035 missing)'))
    return {'schema':'brute.gates.v32_0','study':'BRUTE-0320-NOISY-ACTIVE-ID-035','process':'lean','sealed_input_verified':sealed,'gates':Gt,
            'secondary':sec,'all_gated_pass':all(g['pass'] for g in Gt.values() if g['pass'] is not None),
            'failed':[k for k,g in Gt.items() if g['pass'] is False],'not_exercised':[k for k,g in Gt.items() if g['pass'] is None],
            'secondary_failed':[k for k,g in sec.items() if g['pass'] is False],'reports':reports(allc,res,pc) if allc else {}}


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--study-dir',default=str(STUDY_DIR));ap.add_argument('--check',action='store_true');a=ap.parse_args()
    obj=build(Path(a.study_dir));out=Path(a.study_dir)/'GATES_035.json'
    if a.check:check(out.read_bytes()==dumps(obj),'GATES_035.json does not reproduce');print('GATES_035 reproduces')
    else:write_new(out,obj);print(json.dumps({k:v['pass'] for k,v in obj['gates'].items()}),obj['failed'],obj['secondary_failed'])
