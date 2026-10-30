"""Gates for study-036 (BRUTE_PLAN_036; deviation #144 definitions), LEAN process.
Committed in the source freeze before run_start_036; nothing is tuned after results are seen. New file; built from
scripts/make_gates_035.py (frozen, unchanged).
Inputs (D = results/study-036): D/main/{RESULTS,SCIENTIFIC,SEAL}.json (48 cases: noisy_scale12 12, noisy_scale12_extra 6,
clean_scale12 12, noisy_scale8 12, control 6), D/main/RECOUNT_036.json, D/main/REFERENCE_036.json, D/TEST_SUITE_036.json,
experiments/COMMIT_ORDER_036.json, results/RESEARCH_LEDGER.jsonl. Missing or partial input => every data gate FAIL
INCOMPLETE_INPUT. Case records are accepted only if sha256(RESULTS) equals the seal and no_time(RESULTS) equals SCIENTIFIC.
Definitions (deviation #144):
  label(arm, case) as recounted by RECOUNT_036; clean = clean_scale12, control; within(arm, case) = the recounted truth flips
  over the trace that arm's solver saw <= that arm's B_max (A11_r3 / A11_r3_up 6, A11_r5 2, A10 / S7 27, S5 0);
  GR11 a: recounted WRONG = 0 for A11_r3, A11_r5 and S7 on clean and within-budget noisy cases and for S5 on clean cases,
     and every arm's stored label equals its recount; b: paired over the 12 noisy_scale12 seeds, mean ID(A11_r3) - ID(A10)
     >= 0.25 and seed-bootstrap 95% CI lower end > 0 (10000 resamples, random.Random(34) via make_gates_034.boot_mean);
     c: ID + IDF (A11_r3, noisy_scale12) >= 4 of 12; d: IDU (A11_r3, noisy_scale12) <= 3 of 12;
  GBIS11: IDU(A11_r3, noisy_scale12) <= IDU(A11_r3_up, noisy_scale12) (paired IDU difference and CI reported);
  GRB11 (secondary; not in all_gated_pass): mean B_final and mean capped queries non-increasing over A10, A11_r3, A11_r5 on
     the 18 pooled noisy_scale12 + noisy_scale12_extra cases; reads per case with bootstrap CIs reported;
  GNR11: A11_r3 and A11_r5 labels = the in-run A10 label on every clean_scale12 and control case, and their B_final = 0 on
     every clean case;
  GQB11: every arm's max SAT query wall <= 10.5 s on every case;
  G_sound: A11_r3 / A11_r5 / A11_r3_up / A10 separating words: study and recount words_unsound 0 with equal counts, both
     machines of every word fit the round's trace under its B, every stored model fits (recount PASS); truth_over_Bmax rounds
     reported;
  G10: A11_r3, A11_r5 and S5 ID on every control case (6/6);
  GS_ref: REFERENCE_036 audits A11_r3 on the 12 noisy_scale8 cases: 0 mismatches, decided > 0, mutations 20/20 and at least
     one decided item at B > 0; otherwise FAIL (with reason 'raised-B not exercised' when only that clause fails);
  G_RT: total elapsed <= 1800 s; G_recount: RECOUNT_036 PASS on the sealed RESULTS; GTI: TEST_SUITE_036 all modules 0;
  G_PROC: ledger events preregistration, build_authorization, seedcheck, source_freeze, run_start, run_end (036) present,
     in order, parseable non-decreasing times, the commit-order file present and the main block sealed.
Reports (not gated): labels with Wilson CIs per (arm, key); B_final, capped, steps, reads and reads per step per (arm, key)
  with bootstrap CIs; B histories; within-budget counts; paired contrasts; query max; stops.
  PYTHONPATH=. python scripts/make_gates_036.py [--study-dir D] [--check]"""
from __future__ import annotations
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common_036 import STUDY_DIR,load,dumps,write_new,check,sha,wilson
from scripts.make_gates_034 import opt,boot_mean

EXPECTED={'noisy_scale12':12,'noisy_scale12_extra':6,'clean_scale12':12,'noisy_scale8':12,'control':6}
CLEAN=('clean_scale12','control');POOL12=('noisy_scale12','noisy_scale12_extra')
CAP=1800;QB=10.5;B_A10=0.25;IDF_MIN=4;IDU_MAX=3
ARMS=('A11_r3','A11_r5','A11_r3_up','A10','S7','S5');ACTIVE=('A11_r3','A11_r5','A11_r3_up','A10');LABELS=('ID','IDF','AMB','WRONG','IDU')
NO_WRONG=('A11_r3','A11_r5','S7');CLEAN_ONLY=('S5',)
PROC_ORDER=('preregistration_036','build_authorization_036','seedcheck_036','source_freeze_036','run_start_036','run_end_036')


def _key(c):return f"{c['block']}/{c['key']}/{c['seed']}"
def rec(c,arm,pc):return (pc.get(_key(c)) or {}).get(arm) or {}
def lab(c,arm,pc):return rec(c,arm,pc).get('label')


def counts(cases,arm,pc):
    n=len(cases);out={'n':n}
    for L in LABELS:x=sum(1 for c in cases if lab(c,arm,pc)==L);out[L]={'x':x,'rate':x/n if n else None,'ci95':wilson(x,n)}
    return out


def paired(cases,x,y,pc,L='ID'):
    cs=sorted(cases,key=lambda c:c['seed']);d=[int(lab(c,x,pc)==L)-int(lab(c,y,pc)==L) for c in cs]
    return d,(sum(d)/len(d) if d else None),boot_mean(d)


def _mean(v):v=[x for x in v if x is not None];return None if not v else round(sum(v)/len(v),3)
def _stat(v):v=[x for x in v if x is not None];return {'mean':_mean(v),'ci95_bootstrap':boot_mean(v) if v else None,'n':len(v)}


def ledger():
    from datetime import datetime
    L=[json.loads(x) for x in (ROOT/'results/RESEARCH_LEDGER.jsonl').read_text().splitlines() if x.strip()]
    i0=next((i for i,e in enumerate(L) if e.get('event')=='preregistration_036'),None);out=[]
    for e in (L[i0:] if i0 is not None else []):
        try:t=datetime.fromisoformat(str(e.get('note',''))[:25])
        except ValueError:t=None
        out.append((e['event'],t))
        if e['event']=='run_end_036':break
    return out


def reports(allc,res,pc):
    G=lambda k:[c for c in allc if c['key']==k];S=lambda k:sorted(G(k),key=lambda c:c['seed']);r={}
    r['labels']={f'{a}/{k}':counts(G(k),a,pc) for a in ARMS for k in EXPECTED}
    r['labels_pooled_noisy12']={a:counts([c for k in POOL12 for c in G(k)],a,pc) for a in ARMS}
    r['cost']={f'{a}/{k}':{f:_stat([c['arms'][a].get(f) for c in G(k)]) for f in ('B_final','capped','steps','reads','reads_per_step','used')}
               for a in ARMS for k in EXPECTED}
    r['B_final']={f'{a}/{k}':[c['arms'][a].get('B_final') for c in S(k)] for a in ACTIVE for k in EXPECTED}
    r['B_history']={f'{a}/{k}':[c['arms'][a].get('B_history') for c in S(k)] for a in ACTIVE for k in EXPECTED}
    r['truth_flips_trace']={f'{a}/{k}':[c['arms'][a]['truth_flips_trace'] for c in S(k)] for a in ARMS for k in EXPECTED}
    r['within_budget']={f'{a}/{k}':sum(1 for c in G(k) if rec(c,a,pc).get('within_budget')) for a in ARMS for k in EXPECTED}
    r['stops']={f'{a}/{k}':{s:sum(1 for c in G(k) if c['arms'][a]['stop']==s) for s in sorted({c['arms'][a]['stop'] for c in G(k)})} for a in ARMS for k in EXPECTED}
    con={}
    for x,y in (('A11_r3','A10'),('A11_r5','A10'),('A11_r5','A11_r3'),('A11_r3','A11_r3_up'),('A11_r3','S7'),('A11_r3','S5')):
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
    seal=opt(D/'SEAL.json');sci=opt(D/'SCIENTIFIC.json');res=opt(D/'RESULTS.json');rc=opt(D/'RECOUNT_036.json')
    ref=opt(D/'REFERENCE_036.json');ts=opt(study/'TEST_SUITE_036.json');order=opt(ROOT/'experiments/COMMIT_ORDER_036.json')
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
    gated.update({a:[c for c in allc if c['key'] in CLEAN] for a in CLEAN_ONLY})
    wrong=[(_key(c),a) for a in gated for c in gated[a] if lab(c,a,pc)=='WRONG']
    wrong_out=[(_key(c),a) for c in allc for a in ARMS if lab(c,a,pc)=='WRONG' and not (a in gated and c in gated[a])]
    a_ok=complete and rc_ok and not wrong and not mism
    n12=G('noisy_scale12');d0,m0,ci0=paired(n12,'A11_r3','A10',pc)
    b_ok=complete and rc_ok and m0 is not None and m0>=B_A10 and ci0[0]>0
    c12=counts(n12,'A11_r3',pc);idf=c12['ID']['x']+c12['IDF']['x']
    c_ok=complete and rc_ok and idf>=IDF_MIN;d_ok=complete and rc_ok and c12['IDU']['x']<=IDU_MAX
    gate('GR11_headline',a_ok and b_ok and c_ok and d_ok,{
        'a':{'pass':a_ok,'WRONG_gated':wrong,'WRONG_not_gated_reported':wrong_out,'label_mismatch':mism,'recount_pass':rc_ok,
             'gated_cases':{a:len(v) for a,v in gated.items()},'rule':'recounted WRONG = 0 for A11_r3, A11_r5, S7 on clean and within-budget noisy cases, S5 on clean'},
        'b':{'pass':b_ok,'mean_diff_ID_A11_r3_minus_A10':None if m0 is None else round(m0,4),'ci95_seed_bootstrap':ci0,'per_seed':d0,
             **{f'labels_{a}_noisy_scale12':counts(n12,a,pc) for a in ARMS},'rule':'mean(ID A11_r3 - ID A10, noisy_scale12) >= 0.25 and CI lower > 0'},
        'c':{'pass':c_ok,'ID_plus_IDF_A11_r3_noisy_scale12':idf,'of':len(n12),'ci95':wilson(idf,len(n12)) if n12 else None,'rule':'>= 4/12'},
        'd':{'pass':d_ok,'IDU_A11_r3_noisy_scale12':c12['IDU'],'rule':'<= 3/12'}},why=wb)
    cu=counts(n12,'A11_r3_up',pc);du,mu,ciu=paired(n12,'A11_r3','A11_r3_up',pc,'IDU')
    gate('GBIS11',complete and rc_ok and c12['IDU']['x']<=cu['IDU']['x'],{'IDU_A11_r3':c12['IDU'],'IDU_A11_r3_up':cu['IDU'],
         'paired_IDU_diff_r3_minus_up':{'mean':None if mu is None else round(mu,4),'ci95_seed_bootstrap':ciu,'per_seed':du},'rule':'IDU(A11_r3) <= IDU(A11_r3_up), noisy_scale12'},why=wb)
    pool=[c for k in POOL12 for c in G(k)];seq=('A10','A11_r3','A11_r5')
    mb=[_mean([c['arms'][a]['B_final'] for c in pool]) for a in seq];mcq=[_mean([c['arms'][a]['capped'] for c in pool]) for a in seq]
    nonin=lambda v:all(x is not None for x in v) and all(x>=y for x,y in zip(v,v[1:]))
    gate('GRB11',complete and nonin(mb) and nonin(mcq),{'arms':seq,'mean_B_final':mb,'mean_capped':mcq,'cases':len(pool),
         'reads_per_case':{a:_stat([c['arms'][a]['reads'] for c in pool]) for a in seq},'rule':'non-increasing in r (secondary)'},why=wb,into=sec)
    nr=[(_key(c),a,lab(c,a,pc),lab(c,'A10',pc)) for k in CLEAN for c in G(k) for a in ('A11_r3','A11_r5')]
    bf=[(_key(c),a,c['arms'][a]['B_final']) for k in CLEAN for c in G(k) for a in ('A11_r3','A11_r5')]
    gate('GNR11',complete and rc_ok and all(x[2]==x[3] for x in nr) and all(b==0 for *_,b in bf),
         {'label_differences':[x for x in nr if x[2]!=x[3]],'B_final_nonzero':[x for x in bf if x[2]!=0],'comparisons':len(nr)},why=wb)
    qb=[(_key(c),a,round(c['arms'][a]['query_max_s'] or 0,3)) for c in allc for a in ARMS];worst=max([q for *_,q in qb],default=None)
    gate('GQB11',complete and worst is not None and worst<=QB,{'max_s':worst,'bound_s':QB,'over':[x for x in qb if x[2]>QB],
         **{f'{a}_max_s':max([c['arms'][a]['query_max_s'] or 0 for c in allc],default=None) for a in ARMS}},why=wb)
    rounds=[x for c in allc for a in ACTIVE for x in c['arms'][a]['rounds']]
    snd={'words_checked':sum(c['arms'][a]['words_checked'] for c in allc for a in ACTIVE),
         'words_unsound':sum(c['arms'][a]['words_unsound'] for c in allc for a in ACTIVE),
         'word_machines_unfit':sum(1 for x in rounds if x.get('word') and not (x.get('M1_fits') and x.get('M2_fits'))),
         'recount_words_checked':(rc or {}).get('words_checked'),'recount_words_unsound':(rc or {}).get('words_unsound'),
         'truth_over_Bmax_rounds_reported':{a:sum(c['arms'][a]['truth_over_Bmax_rounds'] for c in allc) for a in ACTIVE}}
    gate('G_sound',complete and rc_ok and snd['words_unsound']==0 and snd['word_machines_unfit']==0 and snd['recount_words_unsound']==0
         and snd['recount_words_checked']==snd['words_checked'],snd,why=wb)
    g10=[(c['seed'],lab(c,'A11_r3',pc),lab(c,'A11_r5',pc),lab(c,'S5',pc)) for c in G('control')]
    gate('G10',complete and rc_ok and len(g10)==6 and all(x[1:]==('ID','ID','ID') for x in g10),{'cases':g10,'rule':'A11_r3, A11_r5 and S5 ID on every control'},why=wb)
    mt=(ref or {}).get('mutation_test') or {}
    robs=None if not ref else {k:ref.get(k) for k in ('arm_audited','key','cases','decided_items','undecided_items','raised_B_decided','labels_checked','mismatch_count','PASS')}|{'mutations':mt.get('detected'),'of':mt.get('mutations')}
    rbase=bool(ref) and ref.get('study_results_sha256')==rsha and ref.get('cases')==len(G('noisy_scale8')) and ref.get('arm_audited')=='A11_r3' and mt.get('detected')==mt.get('mutations')==20 and ref.get('mismatch_count')==0 and (ref.get('decided_items') or 0)>0
    why=wb or (None if ref else 'INCOMPLETE_INPUT (REFERENCE_036 missing)')
    if why is None and rbase and not (ref.get('raised_B_decided') or 0)>0:why='raised-B not exercised'
    gate('GS_ref',rbase and ref.get('PASS') is True,robs,why=why)
    mods=(ts or {}).get('per_module') or {}
    gate('GTI',bool(mods) and ts.get('passed') is True and all(v.get('returncode')==0 for v in mods.values()),
         None if not ts else {k:{'returncode':v.get('returncode'),'tests':v.get('tests')} for k,v in mods.items()},why=None if ts else 'INCOMPLETE_INPUT (TEST_SUITE_036 missing)')
    lt=ledger();ev=[e for e,_ in lt];times=[t for _,t in lt];pos={e:ev.index(e) for e in PROC_ORDER if e in ev}
    proc={'all_events':len(pos)==len(PROC_ORDER),'order':len(pos)==len(PROC_ORDER) and all(pos[a]<pos[b] for a,b in zip(PROC_ORDER,PROC_ORDER[1:])),
          'ledger_times_parse':bool(lt) and all(t is not None for t in times),'ledger_times_non_decreasing':all(a<=b for a,b in zip(times,times[1:]) if a and b),
          'commit_order_file':order is not None,'main_sealed':bool(sealed)}
    gate('G_PROC',all(proc.values()),{'clauses':proc,'events':ev})
    el=(res or {}).get('total_elapsed_informational')
    gate('G_RT',complete and el is not None and el<=CAP,{'elapsed_s':el,'cap_s':CAP,'cases':len(allc)},why=wb)
    gate('G_recount',complete and rc_ok,None if not rc else {k:rc.get(k) for k in ('cases','labels','words_checked','words_unsound','mismatching_cases','PASS')},
         why=wb or (None if rc else 'INCOMPLETE_INPUT (RECOUNT_036 missing)'))
    return {'schema':'brute.gates.v33_0','study':'BRUTE-0330-REPEATED-READS-036','process':'lean','sealed_input_verified':sealed,'gates':Gt,
            'secondary':sec,'all_gated_pass':all(g['pass'] for g in Gt.values() if g['pass'] is not None),
            'failed':[k for k,g in Gt.items() if g['pass'] is False],'not_exercised':[k for k,g in Gt.items() if g['pass'] is None],
            'secondary_failed':[k for k,g in sec.items() if g['pass'] is False],'reports':reports(allc,res,pc) if allc else {}}


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--study-dir',default=str(STUDY_DIR));ap.add_argument('--check',action='store_true');a=ap.parse_args()
    obj=build(Path(a.study_dir));out=Path(a.study_dir)/'GATES_036.json'
    if a.check:check(out.read_bytes()==dumps(obj),'GATES_036.json does not reproduce');print('GATES_036 reproduces')
    else:write_new(out,obj);print(json.dumps({k:v['pass'] for k,v in obj['gates'].items()}),obj['failed'],obj['secondary_failed'])
