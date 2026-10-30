"""Gates for study-034 (BRUTE_PLAN_034; deviation #140 definitions), LEAN process.
Committed in the source freeze before run_start_034; nothing is tuned after results are seen. New file; built from
scripts/make_gates_033.py (frozen, unchanged).
Inputs (D = results/study-034): D/main/{RESULTS,SCIENTIFIC,SEAL}.json (36 cases: scale8 12, scale12 12, scale16 6,
control_cycle3 6), D/main/RECOUNT_034.json, D/main/REFERENCE_034.json, D/TEST_SUITE_034.json,
experiments/COMMIT_ORDER_034.json, results/RESEARCH_LEDGER.jsonl. Missing or partial input => every data gate FAIL
INCOMPLETE_INPUT. Case records are accepted only if sha256(RESULTS) equals the seal and no_time(RESULTS) equals SCIENTIFIC.
Gated (plan criteria): GA9_headline a-d, GDIAG8, GIDF9, GCH9, G_sound, G10, GS_ref, GQB9, G_RT, G_recount, GTI, G_PROC.
Definitions (deviation #140):
  label(arm, case) in ID / IDF / AMB / WRONG / IDU (recounted by RECOUNT_034; IDF is not ID); ID(arm, fam) = ID / cases;
  GA9 a: recounted WRONG = 0 for A9, A9_random, S5 and S1 on every case, and every arm's stored label equals its recount;
     b: paired over the 12 scale12 seeds, mean d = ID(A9) - ID(S5) (per seed 1/0) >= 0.33 and the seed-bootstrap 95% CI
     (BOOT resamples, random.Random(BOOT_SEED)) lower end > 0; c: ID(A9, scale12) >= 5 of 12; d: IDU(A9, scale12) <= 2 of 12;
  GDIAG8: every recounted A8 WRONG (36 cases) has n_min < truth_reachable; 0 A8 WRONG => pass None, status 'not exercised'
     (neither pass nor fail; excluded from all_gated_pass and from failed);
  GIDF9: ID + IDF (A9, scale12) >= 8 of 12; GCH9: paired mean A9 - A9_random >= 0.17 and CI lower > 0;
  G_sound: every A9 and A8 separating word rechecked (study and recount words_unsound 0, counts equal), both machines
     consistent with their round's trace, the truth consistent with every A9 / A8 round prefix and every arm's final trace;
  G10: every control case ID by A9 and by S5 (6/6); GQB9: A9 max SAT query wall <= 10.5 s on every case;
  GS_ref: REFERENCE_034 audits arm A9 on every scale8 case: 0 mismatches, decided > 0, mutations 20/20;
  G_PROC: ledger events preregistration, build_authorization, seedcheck, source_freeze, run_start, run_end (034) all
     present, in order, parseable and non-decreasing times, the commit-order file present and the main block sealed.
Reports (not gated): labels with Wilson CIs per (arm, family); actions used (mean, per ID); A9 rounds and stops; IDF
  M1_future_match; paired contrasts; query max; n_min vs truth; A8 WRONG detail.
  PYTHONPATH=. python scripts/make_gates_034.py [--study-dir D] [--check]"""
from __future__ import annotations
import argparse,json,random,sys
from datetime import datetime
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common_034 import STUDY_DIR,load,dumps,write_new,check,sha,wilson

EXPECTED={'scale8':12,'scale12':12,'scale16':6,'control_cycle3':6}
CAP=1800;QB=10.5;B_S5=0.33;B_R=0.17;ID_MIN=5;IDU_MAX=2;IDF_MIN=8;BOOT=10000;BOOT_SEED=34
ARMS=('A9','A9_random','A8','S5','S1');LABELS=('ID','IDF','AMB','WRONG','IDU');NO_WRONG=('A9','A9_random','S5','S1')
PROC_ORDER=('preregistration_034','build_authorization_034','seedcheck_034','source_freeze_034','run_start_034','run_end_034')


def opt(p):
    p=Path(p)
    try:return load(p) if p.exists() else None
    except Exception:return None


def boot_mean(v,n=BOOT,seed=BOOT_SEED):
    if not v:return None
    rng=random.Random(seed);m=len(v);s=sorted(sum(v[rng.randrange(m)] for _ in range(m))/m for _ in range(n))
    return [round(s[int(0.025*n)],4),round(s[int(0.975*n)-1],4)]


def _key(c):return f"{c['block']}/{c['family']}/{c['seed']}"


def lab(c,arm,pc):
    r=(pc.get(_key(c)) or {}).get(arm)
    return r['label'] if r else None


def counts(cases,arm,pc):
    n=len(cases);out={'n':n}
    for L in LABELS:x=sum(1 for c in cases if lab(c,arm,pc)==L);out[L]={'x':x,'rate':x/n if n else None,'ci95':wilson(x,n)}
    return out


def paired(cases,x,y,pc):
    cs=sorted(cases,key=lambda c:c['seed']);d=[int(lab(c,x,pc)=='ID')-int(lab(c,y,pc)=='ID') for c in cs]
    return d,(sum(d)/len(d) if d else None),boot_mean(d)


def _mean(v):return None if not v else round(sum(v)/len(v),3)


def ledger(upto='run_end_034'):
    L=[json.loads(x) for x in (ROOT/'results/RESEARCH_LEDGER.jsonl').read_text().splitlines() if x.strip()]
    i0=next((i for i,e in enumerate(L) if e.get('event')=='preregistration_034'),None);out=[]
    for e in (L[i0:] if i0 is not None else []):
        try:t=datetime.fromisoformat(str(e.get('note',''))[:25])
        except ValueError:t=None
        out.append((e['event'],t))
        if e['event']==upto:break
    return out


def reports(allc,res,pc):
    G=lambda f:[c for c in allc if c['family']==f];r={}
    r['N_declared']={f:(G(f)[0]['N'] if G(f) else None) for f in EXPECTED}
    r['labels']={f'{a}/{f}':counts(G(f),a,pc) for a in ARMS for f in EXPECTED}
    r['actions_used']={f'{a}/{f}':{'mean':_mean([c['arms'][a]['used'] for c in G(f)]),'per_seed':[c['arms'][a]['used'] for c in sorted(G(f),key=lambda c:c['seed'])],
        'mean_on_ID':_mean([c['arms'][a]['used'] for c in G(f) if lab(c,a,pc)=='ID'])} for a in ('A9','A9_random','A8') for f in EXPECTED}
    r['A9_rounds']={f:{'mean':_mean([c['arms']['A9']['n_rounds'] for c in G(f)]),'max':max([c['arms']['A9']['n_rounds'] for c in G(f)],default=None)} for f in EXPECTED}
    r['A9_stop']={f:{s:sum(1 for c in G(f) if c['arms']['A9']['stop']==s) for s in ('ID','IDF','K_spent','unknown','none')} for f in EXPECTED}
    r['A9_random_stop']={f:{s:sum(1 for c in G(f) if c['arms']['A9_random']['stop']==s) for s in ('ID','IDF','AMB','unknown','none')} for f in EXPECTED}
    r['A8_stop']={f:{s:sum(1 for c in G(f) if c['arms']['A8']['stop']==s) for s in ('unique','unknown','none','indistinguishable','K_spent')} for f in EXPECTED}
    r['IDF_diagnosis']={f'{a}/{f}':{'IDF':sum(1 for c in G(f) if c['arms'][a]['stop']=='IDF'),
        'M1_future_match':sum(1 for c in G(f) if c['arms'][a]['stop']=='IDF' and c['arms'][a].get('M1_future_match'))} for a in ('A9','A9_random') for f in EXPECTED}
    r['A8_WRONG_detail']=[{'key':_key(c),'n_min':c['arms']['A8']['n_min'],'truth_reachable':c['truth_reachable'],'stop':c['arms']['A8']['stop']}
                          for c in allc if lab(c,'A8',pc)=='WRONG']
    con={}
    for x,y in (('A9','S5'),('A9','A9_random'),('A9','A8'),('A9','S1'),('A8','S5'),('A9_random','S5'),('S5','S1')):
        for f in EXPECTED:
            d,m,ci=paired(G(f),x,y,pc);con[f'ID({x})-ID({y})/{f}']={'mean':None if m is None else round(m,4),'ci95_seed_bootstrap':ci,'per_seed':d}
    r['contrasts']=con
    r['query_max_s']={f'{a}/{f}':max([c['arms'][a]['query_max_s'] or 0 for c in G(f)],default=None) for a in ARMS for f in EXPECTED}
    r['arm_wall_mean_s']={f'{a}/{f}':_mean([c['arms'][a]['arm_wall_informational'] for c in G(f)]) for a in ARMS for f in EXPECTED}
    r['capped_queries']={a:sum(c['arms'][a].get('capped') or 0 for c in allc) for a in ('A9','A9_random','A8')}
    r['n_min_vs_truth']={f'{a}/{f}':{'equal':sum(1 for c in G(f) if c['arms'][a]['n_min']==c['truth_reachable']),
        'below':sum(1 for c in G(f) if c['arms'][a]['n_min'] is not None and c['arms'][a]['n_min']<c['truth_reachable'])} for a in ARMS for f in EXPECTED}
    r['truth_reachable']={f:[c['truth_reachable'] for c in sorted(G(f),key=lambda c:c['seed'])] for f in EXPECTED}
    r['mean_case_wall']=None if not res or not res['cases'] else round(sum(c['case_wall_informational'] for c in res['cases'])/len(res['cases']),1)
    return r


def build(study=STUDY_DIR):
    from brute.evaluation import no_time
    study=Path(study);D=study/'main';Gt={}
    seal=opt(D/'SEAL.json');sci=opt(D/'SCIENTIFIC.json');res=opt(D/'RESULTS.json');rc=opt(D/'RECOUNT_034.json')
    ref=opt(D/'REFERENCE_034.json');ts=opt(study/'TEST_SUITE_034.json');order=opt(ROOT/'experiments/COMMIT_ORDER_034.json')
    rsha=sha(D/'RESULTS.json') if (D/'RESULTS.json').exists() else None
    sealed=(bool(seal) and res is not None and sci is not None and rsha==seal.get('results_sha256')
            and sha(D/'SCIENTIFIC.json')==seal.get('scientific_sha256') and no_time(res)==sci)
    allc=(res or {}).get('cases',[]) if sealed else []
    G=lambda f:[c for c in allc if c['family']==f and c['block']=='main']
    complete=sealed and seal.get('complete') is True and all(len(G(f))==n for f,n in EXPECTED.items()) and len(allc)==sum(EXPECTED.values())
    wb=None if complete else 'INCOMPLETE_INPUT (main missing, partial or not matching its seal)'
    def gate(name,ok,obs,why=None):Gt[name]={'pass':bool(ok) and why is None,'observed':obs,**({'reason':why} if why else {})}
    pc=(rc or {}).get('per_case') or {}
    rc_ok=bool(rc) and rc.get('PASS') is True and rc.get('results_sha256')==rsha and rc.get('cases')==len(allc)
    mism=[(_key(c),a) for c in allc for a in ARMS if lab(c,a,pc)!=c['arms'][a]['label']]
    wrong=[(_key(c),a) for c in allc for a in NO_WRONG if lab(c,a,pc)=='WRONG']
    a_ok=complete and rc_ok and not wrong and not mism
    s12=G('scale12');d5,m5,ci5=paired(s12,'A9','S5',pc);dr,mr,cir=paired(s12,'A9','A9_random',pc)
    b_ok=complete and rc_ok and m5 is not None and m5>=B_S5 and ci5[0]>0
    c12=counts(s12,'A9',pc);c_ok=complete and rc_ok and c12['ID']['x']>=ID_MIN;d_ok=complete and rc_ok and c12['IDU']['x']<=IDU_MAX
    gate('GA9_headline',a_ok and b_ok and c_ok and d_ok,{
        'a':{'pass':a_ok,'WRONG':wrong,'label_mismatch':mism,'recount_pass':rc_ok,'cases':len(allc),'rule':'recounted WRONG = 0 for A9, A9_random, S5 and S1 on every case'},
        'b':{'pass':b_ok,'mean_diff_ID_A9_minus_S5':None if m5 is None else round(m5,4),'ci95_seed_bootstrap':ci5,'per_seed':d5,
             **{f'labels_{a}_scale12':counts(s12,a,pc) for a in ARMS},'rule':'mean(ID A9 - ID S5, scale12) >= 0.33 and CI lower > 0'},
        'c':{'pass':c_ok,'ID_A9_scale12':c12['ID'],'rule':'ID(A9, scale12) >= 5/12'},
        'd':{'pass':d_ok,'IDU_A9_scale12':c12['IDU'],'rule':'IDU(A9, scale12) <= 2/12'}},why=wb)
    a8w=[c for c in allc if lab(c,'A8',pc)=='WRONG'];det=[(_key(c),c['arms']['A8']['n_min'],c['truth_reachable']) for c in a8w]
    if wb:gate('GDIAG8',False,{'A8_WRONG':det},why=wb)
    elif not a8w:Gt['GDIAG8']={'pass':None,'status':'not exercised','observed':{'A8_WRONG':0,'rule':'every A8 WRONG has n_min < truth_reachable'}}
    else:
        ok=all(x[1] is not None and x[1]<x[2] for x in det)
        Gt['GDIAG8']={'pass':bool(ok and rc_ok),'status':'pass' if ok and rc_ok else 'fail','observed':{'A8_WRONG':det,'count':len(det),
                      'rule':'every A8 WRONG has n_min < truth_reachable'}}
    idf=sum(1 for c in s12 if lab(c,'A9',pc) in ('ID','IDF'))
    gate('GIDF9',complete and rc_ok and idf>=IDF_MIN,{'ID_plus_IDF_A9_scale12':idf,'of':len(s12),'ci95':wilson(idf,len(s12)) if s12 else None,'rule':'ID + IDF (A9, scale12) >= 8/12'},why=wb)
    gate('GCH9',complete and rc_ok and mr is not None and mr>=B_R and cir[0]>0,{'mean_diff_ID_A9_minus_A9_random':None if mr is None else round(mr,4),
         'ci95_seed_bootstrap':cir,'per_seed':dr,'actions_used_A9_scale12':[c['arms']['A9']['used'] for c in sorted(s12,key=lambda c:c['seed'])],
         'rule':'mean(ID A9 - ID A9_random, scale12) >= 0.17 and CI lower > 0'},why=wb)
    rounds=[(c,x) for c in allc for a in ('A9','A8') for x in c['arms'][a]['rounds']]
    snd={'words_checked':sum(c['arms'][a]['words_checked'] for c in allc for a in ('A9','A8')),'words_unsound':sum(c['arms'][a]['words_unsound'] for c in allc for a in ('A9','A8')),
         'words_checked_A9':sum(c['arms']['A9']['words_checked'] for c in allc),
         'word_machines_inconsistent':sum(1 for c,x in rounds if x.get('word') and not (x['M1_consistent'] and x['M2_consistent'])),
         'truth_inconsistent_rounds':sum(c['arms'][a]['truth_inconsistent_rounds'] for c in allc for a in ('A9','A8')),
         'truth_inconsistent_final':sum(1 for c in allc for a in ARMS if not c['arms'][a]['truth_consistent_final']),
         'recount_words_checked':(rc or {}).get('words_checked'),'recount_words_unsound':(rc or {}).get('words_unsound'),
         'recount_truth_inconsistent':(rc or {}).get('truth_inconsistent')}
    gate('G_sound',complete and rc_ok and snd['words_unsound']==0 and snd['word_machines_inconsistent']==0 and snd['truth_inconsistent_rounds']==0
         and snd['truth_inconsistent_final']==0 and snd['recount_words_unsound']==0 and snd['recount_truth_inconsistent']==0
         and snd['recount_words_checked']==snd['words_checked'],snd,why=wb)
    ctrl=G('control_cycle3');g10=[(c['seed'],lab(c,'A9',pc),lab(c,'S5',pc)) for c in ctrl]
    gate('G10',complete and rc_ok and len(g10)==6 and all(x[1]=='ID' and x[2]=='ID' for x in g10),{'cases':g10,'rule':'A9 and S5 ID on every control'},why=wb)
    mt=(ref or {}).get('mutation_test') or {}
    gate('GS_ref',bool(ref) and ref.get('PASS') is True and ref.get('study_results_sha256')==rsha and ref.get('cases')==len(G('scale8'))
         and ref.get('arm_audited')=='A9' and mt.get('detected')==mt.get('mutations')==20,
         None if not ref else {k:ref.get(k) for k in ('arm_audited','family','cases','decided','not_reached','verdicts_checked','words_checked','mismatch_count','PASS')}|{'mutations':mt.get('detected'),'of':mt.get('mutations')},
         why=wb or (None if ref else 'INCOMPLETE_INPUT (REFERENCE_034 missing)'))
    qb=[(_key(c),round(c['arms']['A9']['query_max_s'] or 0,3)) for c in allc];worst=max([q for _,q in qb],default=None)
    gate('GQB9',complete and worst is not None and worst<=QB,{'max_s':worst,'bound_s':QB,'over':[x for x in qb if x[1]>QB],
         **{f'{a}_max_s':max([c['arms'][a]['query_max_s'] or 0 for c in allc],default=None) for a in ARMS if a!='A9'}},why=wb)
    mods=(ts or {}).get('per_module') or {}
    gate('GTI',bool(mods) and ts.get('passed') is True and all(v.get('returncode')==0 for v in mods.values()),
         None if not ts else {k:{'returncode':v.get('returncode'),'tests':v.get('tests')} for k,v in mods.items()},why=None if ts else 'INCOMPLETE_INPUT (TEST_SUITE_034 missing)')
    lt=ledger();ev=[e for e,_ in lt];times=[t for _,t in lt];pos={e:ev.index(e) for e in PROC_ORDER if e in ev}
    proc={'all_events':len(pos)==len(PROC_ORDER),'order':len(pos)==len(PROC_ORDER) and all(pos[a]<pos[b] for a,b in zip(PROC_ORDER,PROC_ORDER[1:])),
          'ledger_times_parse':bool(lt) and all(t is not None for t in times),'ledger_times_non_decreasing':all(a<=b for a,b in zip(times,times[1:]) if a and b),
          'commit_order_file':order is not None,'main_sealed':bool(sealed)}
    gate('G_PROC',all(proc.values()),{'clauses':proc,'events':ev})
    el=(res or {}).get('total_elapsed_informational')
    gate('G_RT',complete and el is not None and el<=CAP,{'elapsed_s':el,'cap_s':CAP,'cases':len(allc)},why=wb)
    gate('G_recount',complete and rc_ok,None if not rc else {k:rc.get(k) for k in ('cases','labels','words_checked','words_unsound','mismatching_cases','PASS')},
         why=wb or (None if rc else 'INCOMPLETE_INPUT (RECOUNT_034 missing)'))
    return {'schema':'brute.gates.v31_0','study':'BRUTE-0310-SOUND-ACTIVE-ID-034','process':'lean','sealed_input_verified':sealed,'gates':Gt,
            'all_gated_pass':all(g['pass'] for g in Gt.values() if g['pass'] is not None),'failed':[k for k,g in Gt.items() if g['pass'] is False],
            'not_exercised':[k for k,g in Gt.items() if g['pass'] is None],
            'reports':reports(allc,res,pc) if allc else {}}


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--study-dir',default=str(STUDY_DIR));ap.add_argument('--check',action='store_true');a=ap.parse_args()
    obj=build(Path(a.study_dir));out=Path(a.study_dir)/'GATES_034.json'
    if a.check:check(out.read_bytes()==dumps(obj),'GATES_034.json does not reproduce');print('GATES_034 reproduces')
    else:write_new(out,obj);print(json.dumps({k:v['pass'] for k,v in obj['gates'].items()}),obj['failed'])
