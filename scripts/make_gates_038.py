"""Gates for study-038 (BRUTE_PLAN_038; deviation #148 definitions), LEAN process.
Committed in the source freeze before run_start_038; nothing is tuned after results are seen. New file; built from
scripts/make_gates_037.py (frozen, unchanged).
Inputs (D = results/study-038): D/main/{RESULTS,SCIENTIFIC,SEAL}.json (42 cases: noisy_scale12 12, clean_scale12 12,
noisy_scale8 12, control 6), D/main/RECOUNT_038.json, D/main/REFERENCE_038.json, D/TEST_SUITE_038.json,
experiments/COMMIT_ORDER_038.json, results/RESEARCH_LEDGER.jsonl. Missing or partial input => every data gate FAIL
INCOMPLETE_INPUT. Case records are accepted only if sha256(RESULTS) equals the seal and no_time(RESULTS) equals SCIENTIFIC.
Definitions (deviation #148):
  label(arm, case) as recounted by RECOUNT_038; clean = clean_scale12, control; within(arm, case) = the recounted truth flips
  over the arm's fused trace <= that arm's B_max (A13_r5 / A12_r5 2, A13_r3 / A12_r3 / A11_r3 6, S7 27);
  capped confirmation (arm, case): at least one B_max confirmation of the arm on the case ended 'unknown' (a capped query);
  GR13 a: recounted WRONG = 0 for A13_r5 and A13_r3 on every clean case and every within-budget noisy case, and every arm's
     stored label equals its recount (other arms' WRONG reported, not gated);
     b: paired over the 12 noisy_scale12 seeds, mean IDU(A12_r3) - IDU(A13_r3) >= 0.25 and seed-bootstrap 95% CI lower end > 0
     (10000 resamples, random.Random(34) via make_gates_034.boot_mean);
     c: ID + IDF (A13_r5, noisy_scale12) >= 5 of 12;  d: capped confirmations of A13_r5 on clean_scale12 <= 2 of 12;
  GSAFE13: TEST_SUITE_038 module test_scalesearch13_0350 returncode 0 with test_GSAFE13_sealed_036_trace 'ok';
  GINC13: the same module with test_GINC13_sealed_037_reference_set 'ok' (both Exact, inside GTI);
  GNR13: on every clean_scale12 and control case each A13 arm has B_final 0 and the same recounted label as A11_r3;
  GQB13: every arm's max query wall <= 10.5 s on every case;
  G_sound: separating words of the five active arms, as in 037;
  G10: every arm (A13_r5, A13_r3, A12_r5, A12_r3, A11_r3, S7) ID on every control case (6/6);
  GS_ref: REFERENCE_038 audits A13_r3 on the 12 noisy_scale8 cases incl. the confirmation verdicts: 0 mismatches, decided > 0,
     mutations 20/20 and at least one decided item at B > 0 (else 'raised-B not exercised');
  G_RT: total elapsed <= 1800 s; G_recount: RECOUNT_038 PASS on the sealed RESULTS; GTI: TEST_SUITE_038 all modules 0;
  G_PROC: ledger events preregistration, build_authorization, seedcheck, source_freeze, run_start, run_end, recount, reference,
     tests (038) present, in order, parseable non-decreasing times, the commit-order file present and the main block sealed.
  GH2 (secondary; not in all_gated_pass): capped confirmations (A12_r5 + A12_r3, all 42 cases) - (A13_r5 + A13_r3) >= 6;
  GPR13 (secondary): capped least-B probes A13_r3 <= A12_r3 on noisy_scale12.
Reports (not gated): labels with Wilson CIs per (arm, key); B_final, capped, confirmations_capped, steps, reads per (arm, key)
  with bootstrap CIs; confirmation verdict counts; B histories; within-budget counts; paired contrasts; query max; stops.
  PYTHONPATH=. python scripts/make_gates_038.py [--study-dir D] [--check]"""
from __future__ import annotations
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common_038 import STUDY_DIR,load,dumps,write_new,check,sha,wilson
from scripts.make_gates_034 import opt,boot_mean

EXPECTED={'noisy_scale12':12,'clean_scale12':12,'noisy_scale8':12,'control':6}
CLEAN=('clean_scale12','control')
CAP=1800;QB=10.5;IDU_DIFF=0.25;IDF_MIN=5
ARMS=('A13_r5','A13_r3','A12_r5','A12_r3','A11_r3','S7');ACTIVE=ARMS[:5];A13=('A13_r5','A13_r3');SOUND=ARMS[:4]
LABELS=('ID','IDF','AMB','WRONG','IDU');NO_WRONG=A13;CAPC_MAX=2;H2_MIN=6
PROC_ORDER=('preregistration_038','build_authorization_038','seedcheck_038','source_freeze_038','run_start_038','run_end_038','recount_038',
            'reference_038','tests_038')
GSAFE_MOD='test_scalesearch13_0350';GSAFE_TEST='test_GSAFE13_sealed_036_trace';GINC_TEST='test_GINC13_sealed_037_reference_set'


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
    i0=next((i for i,e in enumerate(L) if e.get('event')=='preregistration_038'),None);out=[]
    for e in (L[i0:] if i0 is not None else []):
        try:t=datetime.fromisoformat(str(e.get('note',''))[:25])
        except ValueError:t=None
        out.append((e['event'],t))
        if e['event']==PROC_ORDER[-1]:break
    return out


def probe_stats(cases,arm):
    """Least-B searches, probes per search and capped probes for one arm over cases (GPR12)."""
    srch=sum(c['arms'][arm].get('least_B_searches') or 0 for c in cases);pr=sum(c['arms'][arm].get('probes_total') or 0 for c in cases)
    cap=sum(c['arms'][arm].get('probes_capped') or 0 for c in cases)
    first=[x['probes'][0] for c in cases for x in c['arms'][arm]['rounds'] if x.get('probes')]
    return {'least_B_searches':srch,'probes':pr,'probes_per_search':None if not srch else round(pr/srch,3),'capped_probes':cap,
            'first_probe_capped':sum(1 for p in first if p[1] is None),'first_probes':len(first),
            'per_seed_probes':[c['arms'][arm].get('probes_total') for c in sorted(cases,key=lambda c:c['seed'])]}


def capc(c,arm):return int((c['arms'][arm].get('confirmations_capped') or 0)>0)


def capc_stats(cases,arm):
    v=[capc(c,arm) for c in sorted(cases,key=lambda c:c['seed'])];x=sum(v)
    return {'cases_capped':x,'of':len(v),'ci95':wilson(x,len(v)) if v else None,'per_seed':v,
            'confirmations':sum(len(c['arms'][arm].get('confirmations') or []) for c in cases),
            'confirmations_capped_total':sum(c['arms'][arm].get('confirmations_capped') or 0 for c in cases)}


def reports(allc,res,pc):
    G=lambda k:[c for c in allc if c['key']==k];S=lambda k:sorted(G(k),key=lambda c:c['seed']);r={}
    r['labels']={f'{a}/{k}':counts(G(k),a,pc) for a in ARMS for k in EXPECTED}
    r['cost']={f'{a}/{k}':{f:_stat([c['arms'][a].get(f) for c in G(k)]) for f in ('B_final','capped','confirmations_capped','steps','reads','reads_per_step','used')}
               for a in ARMS for k in EXPECTED}
    r['B_final']={f'{a}/{k}':[c['arms'][a].get('B_final') for c in S(k)] for a in ACTIVE for k in EXPECTED}
    r['B_history']={f'{a}/{k}':[c['arms'][a].get('B_history') for c in S(k)] for a in ACTIVE for k in EXPECTED}
    r['confirmations']={f'{a}/{k}':[c['arms'][a].get('confirmations') for c in S(k)] for a in SOUND for k in EXPECTED}
    r['confirmations_capped']={f'{a}/{k}':capc_stats(G(k),a) for a in SOUND for k in EXPECTED}
    r['truth_flips_trace']={f'{a}/{k}':[c['arms'][a]['truth_flips_trace'] for c in S(k)] for a in ARMS for k in EXPECTED}
    r['within_budget']={f'{a}/{k}':sum(1 for c in G(k) if rec(c,a,pc).get('within_budget')) for a in ARMS for k in EXPECTED}
    r['stops']={f'{a}/{k}':{s:sum(1 for c in G(k) if c['arms'][a]['stop']==s) for s in sorted({c['arms'][a]['stop'] for c in G(k)})} for a in ARMS for k in EXPECTED}
    con={}
    for x,y in (('A12_r3','A13_r3'),('A12_r5','A13_r5'),('A13_r5','A11_r3'),('A13_r3','A11_r3'),('A13_r5','A13_r3'),('A13_r3','S7')):
        for k in EXPECTED:
            for L in ('ID','IDU'):
                d,m,ci=paired(G(k),x,y,pc,L);con[f'{L}({x})-{L}({y})/{k}']={'mean':None if m is None else round(m,4),'ci95_seed_bootstrap':ci,'per_seed':d}
    r['contrasts']=con
    r['query_max_s']={f'{a}/{k}':max([c['arms'][a]['query_max_s'] or 0 for c in G(k)],default=None) for a in ARMS for k in EXPECTED}
    r['arm_wall_mean_s']={f'{a}/{k}':_mean([c['arms'][a]['arm_wall_informational'] for c in G(k)]) for a in ARMS for k in EXPECTED}
    r['probes']={f'{a}/{k}':probe_stats(G(k),a) for a in ACTIVE for k in EXPECTED}
    r['mean_case_wall']=None if not res or not res['cases'] else round(sum(c['case_wall_informational'] for c in res['cases'])/len(res['cases']),1)
    return r


def build(study=STUDY_DIR):
    from brute.evaluation import no_time
    study=Path(study);D=study/'main';Gt={};sec={}
    seal=opt(D/'SEAL.json');sci=opt(D/'SCIENTIFIC.json');res=opt(D/'RESULTS.json');rc=opt(D/'RECOUNT_038.json')
    ref=opt(D/'REFERENCE_038.json');ts=opt(study/'TEST_SUITE_038.json');order=opt(ROOT/'experiments/COMMIT_ORDER_038.json')
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
    wrong=[(_key(c),a) for a in gated for c in gated[a] if lab(c,a,pc)=='WRONG']
    wrong_out=[(_key(c),a) for c in allc for a in ARMS if lab(c,a,pc)=='WRONG' and not (a in gated and c in gated[a])]
    a_ok=complete and rc_ok and not wrong and not mism
    n12=G('noisy_scale12');db,mb,cib=paired(n12,'A12_r3','A13_r3',pc,'IDU')
    b_ok=complete and rc_ok and mb is not None and mb>=IDU_DIFF and cib[0]>0
    c5=counts(n12,'A13_r5',pc);idf=c5['ID']['x']+c5['IDF']['x']
    c_ok=complete and rc_ok and idf>=IDF_MIN;cc=capc_stats(G('clean_scale12'),'A13_r5');d_ok=complete and cc['cases_capped']<=CAPC_MAX
    gate('GR13_headline',a_ok and b_ok and c_ok and d_ok,{
        'a':{'pass':a_ok,'WRONG_gated':wrong,'WRONG_not_gated_reported':wrong_out,'label_mismatch':mism,'recount_pass':rc_ok,
             'gated_cases':{a:len(v) for a,v in gated.items()},'rule':'recounted WRONG = 0 for A13_r5 and A13_r3 on clean and within-budget noisy cases'},
        'b':{'pass':b_ok,'mean_diff_IDU_A12_r3_minus_A13_r3':None if mb is None else round(mb,4),'ci95_seed_bootstrap':cib,'per_seed':db,
             **{f'labels_{a}_noisy_scale12':counts(n12,a,pc) for a in ARMS},'rule':'mean(IDU A12_r3 - IDU A13_r3, noisy_scale12) >= 0.25 and CI lower > 0'},
        'c':{'pass':c_ok,'ID_plus_IDF_A13_r5_noisy_scale12':idf,'of':len(n12),'ci95':wilson(idf,len(n12)) if n12 else None,'rule':'>= 5/12'},
        'd':{'pass':d_ok,'A13_r5_clean_scale12':cc,'A12_r5_clean_scale12_reported':capc_stats(G('clean_scale12'),'A12_r5'),
             'rule':'capped confirmations (cases with a capped B_max confirmation) of A13_r5 on clean_scale12 <= 2 of 12'}},why=wb)
    mods=(ts or {}).get('per_module') or {};gm=mods.get(GSAFE_MOD) or {}
    for gn,tn in (('GSAFE13',GSAFE_TEST),('GINC13',GINC_TEST)):
        gate(gn,bool(gm) and gm.get('returncode')==0 and (gm.get('results') or {}).get(tn)=='ok',
             None if not gm else {'module':GSAFE_MOD,'test':tn,'result':(gm.get('results') or {}).get(tn),'stdout_tail':gm.get('stdout_tail')},
             why=None if ts else 'INCOMPLETE_INPUT (TEST_SUITE_038 missing)')
    nr=[(_key(c),a,lab(c,a,pc),lab(c,'A11_r3',pc)) for k in CLEAN for c in G(k) for a in A13]
    bf=[(_key(c),a,c['arms'][a]['B_final']) for k in CLEAN for c in G(k) for a in A13]
    gate('GNR13',complete and rc_ok and all(x[2]==x[3] for x in nr) and all(b==0 for *_,b in bf),
         {'label_differences':[x for x in nr if x[2]!=x[3]],'B_final_nonzero':[x for x in bf if x[2]!=0],'comparisons':len(nr)},why=wb)
    qb=[(_key(c),a,round(c['arms'][a]['query_max_s'] or 0,3)) for c in allc for a in ARMS];worst=max([q for *_,q in qb],default=None)
    gate('GQB13',complete and worst is not None and worst<=QB,{'max_s':worst,'bound_s':QB,'over':[x for x in qb if x[2]>QB],
         **{f'{a}_max_s':max([c['arms'][a]['query_max_s'] or 0 for c in allc],default=None) for a in ARMS}},why=wb)
    rounds=[x for c in allc for a in ACTIVE for x in c['arms'][a]['rounds']]
    snd={'words_checked':sum(c['arms'][a]['words_checked'] for c in allc for a in ACTIVE),
         'words_unsound':sum(c['arms'][a]['words_unsound'] for c in allc for a in ACTIVE),
         'words_from_confirmation':sum(1 for x in rounds if x.get('word') and x.get('word_from_confirm')),
         'word_machines_unfit':sum(1 for x in rounds if x.get('word') and not (x.get('M1_fits') and x.get('M2_fits'))),
         'recount_words_checked':(rc or {}).get('words_checked'),'recount_words_unsound':(rc or {}).get('words_unsound'),
         'truth_over_Bmax_rounds_reported':{a:sum(c['arms'][a]['truth_over_Bmax_rounds'] for c in allc) for a in ACTIVE}}
    gate('G_sound',complete and rc_ok and snd['words_unsound']==0 and snd['word_machines_unfit']==0 and snd['recount_words_unsound']==0
         and snd['recount_words_checked']==snd['words_checked'],snd,why=wb)
    g10=[(c['seed'],*[lab(c,a,pc) for a in ARMS]) for c in G('control')]
    gate('G10',complete and rc_ok and len(g10)==6 and all(all(L=='ID' for L in x[1:]) for x in g10),{'arms':ARMS,'cases':g10,'rule':'every arm ID on every control'},why=wb)
    mt=(ref or {}).get('mutation_test') or {}
    robs=None if not ref else {k:ref.get(k) for k in ('arm_audited','key','cases','decided_items','undecided_items','raised_B_decided','confirm_items','labels_checked','mismatch_count','PASS')}|{'mutations':mt.get('detected'),'of':mt.get('mutations')}
    rbase=bool(ref) and ref.get('study_results_sha256')==rsha and ref.get('cases')==len(G('noisy_scale8')) and ref.get('arm_audited')=='A13_r3' and mt.get('detected')==mt.get('mutations')==20 and ref.get('mismatch_count')==0 and (ref.get('decided_items') or 0)>0
    why=wb or (None if ref else 'INCOMPLETE_INPUT (REFERENCE_038 missing)')
    if why is None and rbase and not (ref.get('raised_B_decided') or 0)>0:why='raised-B not exercised'
    gate('GS_ref',rbase and ref.get('PASS') is True,robs,why=why)
    gate('GTI',bool(mods) and ts.get('passed') is True and all(v.get('returncode')==0 for v in mods.values()),
         None if not ts else {k:{'returncode':v.get('returncode'),'tests':v.get('tests')} for k,v in mods.items()},why=None if ts else 'INCOMPLETE_INPUT (TEST_SUITE_038 missing)')
    lt=ledger();ev=[e for e,_ in lt];times=[t for _,t in lt];pos={e:ev.index(e) for e in PROC_ORDER if e in ev}
    proc={'all_events':len(pos)==len(PROC_ORDER),'order':len(pos)==len(PROC_ORDER) and all(pos[a]<pos[b] for a,b in zip(PROC_ORDER,PROC_ORDER[1:])),
          'ledger_times_parse':bool(lt) and all(t is not None for t in times),'ledger_times_non_decreasing':all(a<=b for a,b in zip(times,times[1:]) if a and b),
          'commit_order_file':order is not None,'main_sealed':bool(sealed)}
    gate('G_PROC',all(proc.values()),{'clauses':proc,'events':ev})
    el=(res or {}).get('total_elapsed_informational')
    gate('G_RT',complete and el is not None and el<=CAP,{'elapsed_s':el,'cap_s':CAP,'cases':len(allc)},why=wb)
    gate('G_recount',complete and rc_ok,None if not rc else {k:rc.get(k) for k in ('cases','labels','words_checked','words_unsound','mismatching_cases','PASS')},
         why=wb or (None if rc else 'INCOMPLETE_INPUT (RECOUNT_038 missing)'))
    h12=sum(capc(c,a) for c in allc for a in ('A12_r5','A12_r3'));h13=sum(capc(c,a) for c in allc for a in A13)
    gate('GH2',complete and h12-h13>=H2_MIN,{'A12_capped_confirmation_cases':h12,'A13_capped_confirmation_cases':h13,'diff':h12-h13,
         'by_arm':{a:capc_stats(allc,a) for a in SOUND} if allc else None,'rule':'capped confirmations (A12_r5 + A12_r3) - (A13_r5 + A13_r3) >= 6, all cases (secondary, H2)'},why=wb,into=sec)
    p13=probe_stats(n12,'A13_r3') if n12 else None;p12=probe_stats(n12,'A12_r3') if n12 else None
    gate('GPR13',complete and p13['capped_probes']<=p12['capped_probes'],{'A13_r3':p13,'A12_r3':p12,
         'rule':'probe curve reported; direction: capped probes A13_r3 <= A12_r3 (secondary)'},why=wb,into=sec)
    return {'schema':'brute.gates.v35_0','study':'BRUTE-0350-INCREMENTAL-LEASTB-038','process':'lean','sealed_input_verified':sealed,'gates':Gt,
            'secondary':sec,'all_gated_pass':all(g['pass'] for g in Gt.values() if g['pass'] is not None),
            'failed':[k for k,g in Gt.items() if g['pass'] is False],'not_exercised':[k for k,g in Gt.items() if g['pass'] is None],
            'secondary_failed':[k for k,g in sec.items() if g['pass'] is False],'reports':reports(allc,res,pc) if allc else {}}


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--study-dir',default=str(STUDY_DIR));ap.add_argument('--check',action='store_true');a=ap.parse_args()
    obj=build(Path(a.study_dir));out=Path(a.study_dir)/'GATES_038.json'
    if a.check:check(out.read_bytes()==dumps(obj),'GATES_038.json does not reproduce');print('GATES_038 reproduces')
    else:write_new(out,obj);print(json.dumps({k:v['pass'] for k,v in obj['gates'].items()}),obj['failed'],obj['secondary_failed'])
