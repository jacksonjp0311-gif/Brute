"""Gates for study-040 (BRUTE_PLAN_040; deviation #152 definitions), LEAN process.
Committed in the source freeze before run_start_040; nothing is tuned after results are seen. New file; built from
scripts/make_gates_039.py (frozen, unchanged).
Inputs (D = results/study-040): D/main/{RESULTS,SCIENTIFIC,SEAL}.json (42 cases: scale16 12, scale14 12, lowobs12 12,
control 6), D/main/RECOUNT_040.json, D/main/REFERENCE_040.json, D/TEST_SUITE_040.json, experiments/COMMIT_ORDER_040.json,
results/RESEARCH_LEDGER.jsonl. Missing or partial input => every data gate FAIL INCOMPLETE_INPUT. Case records are accepted
only if sha256(RESULTS) equals the seal and no_time(RESULTS) equals SCIENTIFIC, and every case carries exactly the arms its
key is run with (experiments.brute_study_040.plan_groups).
Definitions (deviation #152):
  label(arm, case) as recounted by RECOUNT_040; IDF is not ID;
  GC15 a: recounted WRONG = 0 for A15 and A15_cube on every case, and every arm's stored label equals its recount;
       b: ID + IDF (A15_cube, scale16) >= 4 of 12;
       c: paired over the 12 scale16 seeds, mean ID(A15_cube) - ID(A14) >= 0.25 and seed-bootstrap 95% CI lower end > 0
          (10000 resamples, random.Random(34) via make_gates_034.boot_mean);
       d: capped cases of A15_cube on scale16 <= 6 of 12 (literal reading: a case counts as capped if any of its SAT calls
          hit the 9 s cap, including an initial call that a cube split then resolved; cube counts reported in GCAP15);
  GREP15: ID + IDF (A15_cube, scale14) >= ID + IDF (A14, scale14) - 1;
  GFAM15: ID + IDF (A15_cube, lowobs12) >= 6 of 12 and recounted WRONG 0 for A15 and A15_cube on lowobs12; not exercised
     (pass null) if A15_cube's mean extra actions on lowobs12 < 3;
  GINC15: TEST_SUITE_040 module test_scalesearch15_0370 returncode 0 with test_GINC15_sealed_039_traces 'ok' (Exact, inside GTI);
  GQB15: max query wall <= 10.5 s for A15 and A15_cube on every case (A14 reported, not gated);
  G_sound: study and recount words_unsound 0 over every arm, recount words_checked equal to the study's, 0 truth
     inconsistencies in the recount;
  G10: every arm run on a control case is ID on it (6/6 each);
  GS_ref: REFERENCE_040 audits A15_cube on the 12 scale14 cases: 0 mismatches, decided > 0, mutations 20/20;
  G_RT: total elapsed <= 1800 s; G_recount: RECOUNT_040 PASS on the sealed RESULTS; GTI: TEST_SUITE_040 all modules 0;
  G_PROC: ledger events preregistration, build_authorization, seedcheck, source_freeze, run_start, run_end, recount,
     reference, tests (040) present, in order, parseable non-decreasing times, the commit-order file present and main sealed.
  GSYM15 (secondary, reported): paired ID(A15) - ID(A14) and ID(A15_cube) - ID(A15) per family.
  GCAP15 (secondary, reported): capped cases and calls, IDU last phase, cube counts, extra actions used and K_spent per arm
     and family.
Reports (not gated): labels with Wilson CIs per (arm, key); used, rounds, capped, queries, query max, wall per (arm, key)
  with bootstrap CIs; stops; paired contrasts; clique sizes; incremental-instance guards and sizes.
  PYTHONPATH=. python scripts/make_gates_040.py [--study-dir D] [--check]"""
from __future__ import annotations
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common_040 import STUDY_DIR,PLAN,load,dumps,write_new,check,sha,wilson
from experiments.brute_study_040 import plan_groups,ORDER
from scripts.make_gates_034 import opt,boot_mean

EXPECTED={'scale16':12,'scale14':12,'lowobs12':12,'control':6}
CAP=1800;QB=10.5;C_DIFF=0.25;B_MIN=4;D_MAX=6;FAM_MIN=6;FAM_ACT=3
ARMS=ORDER;NO_WRONG=('A15','A15_cube');QB_ARMS=('A15','A15_cube');ACTIVE=ORDER;HEAD='A15_cube'
LABELS=('ID','IDF','AMB','WRONG','IDU')
PROC_ORDER=('preregistration_040','build_authorization_040','seedcheck_040','source_freeze_040','run_start_040','run_end_040','recount_040',
            'reference_040','tests_040')
GINC_MOD='test_scalesearch15_0370';GINC_TEST='test_GINC15_sealed_039_traces'
GROUP_ARMS={a:(a,) for a in ORDER}


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
    i0=next((i for i,e in enumerate(L) if e.get('event')=='preregistration_040'),None);out=[]
    for e in (L[i0:] if i0 is not None else []):
        try:t=datetime.fromisoformat(str(e.get('note',''))[:25])
        except ValueError:t=None
        out.append((e['event'],t))
        if e['event']==PROC_ORDER[-1]:break
    return out


def act_stats(cases,arm):
    cs=sorted(has(cases,arm),key=lambda c:c['seed'])
    return {'used':_stat([c['arms'][arm].get('used') for c in cs]),'used_per_seed':[c['arms'][arm].get('used') for c in cs],
            'K_spent':sum(1 for c in cs if c['arms'][arm]['stop']=='K_spent'),'cases':len(cs),
            'capped_cases':sum(1 for c in cs if c['arms'][arm].get('capped_case')),'capped_calls':sum(c['arms'][arm].get('capped') or 0 for c in cs),
            'IDU_last_phase':{str(p):sum(1 for c in cs if c['arms'][arm]['stop']=='unknown' and c['arms'][arm].get('last_phase')==p) for p in ('least','future','start',None)},
            'cube':{f:sum(((c['arms'][arm].get('cube') or {}).get(f) or 0) for c in cs) for f in ('cubes','cube_sat','cube_unsat')}}


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
    for x,y in (('A15_cube','A14'),('A15','A14'),('A15_cube','A15')):
        for k in EXPECTED:
            d,m,ci=paired(G(k),x,y,pc,'ID')
            if d:con[f'ID({x})-ID({y})/{k}']={'mean':round(m,4),'ci95_seed_bootstrap':ci,'per_seed':d}
    r['contrasts']=con
    r['query_max_s']={f'{a}/{k}':max([c['arms'][a]['query_max_s'] or 0 for c in has(G(k),a)],default=None) for a,k in AK}
    r['clique']={f'{a}/{k}':[c['arms'][a].get('clique') for c in has(S(k),a)] for a,k in AK if a!='A14'}
    r['inc_guards']={f'{a}/{k}':_stat([c['arms'][a].get('inc_guards') for c in has(G(k),a)]) for a,k in AK if a in NO_WRONG}
    r['group_wall_mean_s']={f'{g}/{k}':_mean([c['group_walls_informational'].get(g) for c in G(k)]) for g in GROUP_ARMS for k in EXPECTED}
    return r


def build(study=STUDY_DIR):
    from brute.evaluation import no_time
    study=Path(study);D=study/'main';Gt={};sec={}
    seal=opt(D/'SEAL.json');sci=opt(D/'SCIENTIFIC.json');res=opt(D/'RESULTS.json');rc=opt(D/'RECOUNT_040.json')
    ref=opt(D/'REFERENCE_040.json');ts=opt(study/'TEST_SUITE_040.json');order=opt(ROOT/'experiments/COMMIT_ORDER_040.json')
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
    s16=G('scale16');s14=G('scale14');b=idf(s16,HEAD,pc);b_ok=complete and rc_ok and b>=B_MIN
    dc,mc,cic=paired(s16,HEAD,'A14',pc);c_ok=complete and rc_ok and mc is not None and mc>=C_DIFF and cic[0]>0
    cap=[c['seed'] for c in has(s16,HEAD) if c['arms'][HEAD].get('capped_case')];d_ok=complete and len(cap)<=D_MAX
    gate('GC15_headline',a_ok and b_ok and c_ok and d_ok,{
        'a':{'pass':a_ok,'WRONG_gated':wrong,'WRONG_other_arms_reported':wrong_out,'label_mismatch':mism,'recount_pass':rc_ok,
             'rule':'recounted WRONG = 0 for A15 and A15_cube on every case, no recount label mismatch'},
        'b':{'pass':b_ok,'ID_plus_IDF_A15_cube_scale16':b,'of':len(s16),'ci95':wilson(b,len(s16)) if s16 else None,'rule':'>= 4/12'},
        'c':{'pass':c_ok,'mean_diff_ID_A15_cube_minus_A14_scale16':None if mc is None else round(mc,4),'ci95_seed_bootstrap':cic,'per_seed':dc,
             **{f'labels_{a}_scale16':counts(s16,a,pc) for a in ARMS},'rule':'mean(ID A15_cube - ID A14, scale16) >= 0.25 and CI lower > 0'},
        'd':{'pass':d_ok,'capped_cases_A15_cube_scale16':len(cap),'seeds':cap,'of':len(s16),'ci95':wilson(len(cap),len(s16)) if s16 else None,
             'rule':'<= 6/12 (any capped call)'}},why=wb)
    r15=idf(s14,HEAD,pc);r14=idf(s14,'A14',pc)
    gate('GREP15',complete and rc_ok and r15>=r14-1,{'ID_plus_IDF_A15_cube_scale14':r15,'ID_plus_IDF_A14_scale14':r14,'of':len(s14),
         **{f'labels_{a}_scale14':counts(s14,a,pc) for a in ARMS},'rule':'ID+IDF(A15_cube) >= ID+IDF(A14) - 1 on scale14'},why=wb)
    lo=G('lowobs12');fp=idf(lo,HEAD,pc);fw=[(_key(c),a) for c in lo for a in NO_WRONG if a in c['arms'] and lab(c,a,pc)=='WRONG']
    ua=_mean([c['arms'][HEAD].get('used') for c in has(lo,HEAD)])
    fobs={'ID_plus_IDF_A15_cube_lowobs12':fp,'of':len(lo),'ci95':wilson(fp,len(lo)) if lo else None,'WRONG':fw,'mean_extra_actions_A15_cube':ua,
          **{f'labels_{a}_lowobs12':counts(lo,a,pc) for a in ARMS},
          'rule':'ID+IDF(A15_cube, lowobs12) >= 6/12 and WRONG 0 for A15, A15_cube; not exercised if mean extra actions < 3'}
    if complete and rc_ok and ua is not None and ua<FAM_ACT:Gt['GFAM15']={'pass':None,'observed':fobs,'reason':'NOT_EXERCISED (mean extra actions < 3)'}
    else:gate('GFAM15',complete and rc_ok and fp>=FAM_MIN and not fw,fobs,why=wb)
    mods=(ts or {}).get('per_module') or {};gm=mods.get(GINC_MOD) or {}
    gate('GINC15',bool(gm) and gm.get('returncode')==0 and (gm.get('results') or {}).get(GINC_TEST)=='ok',
         None if not gm else {'module':GINC_MOD,'test':GINC_TEST,'result':(gm.get('results') or {}).get(GINC_TEST),'stdout_tail':gm.get('stdout_tail')},
         why=None if ts else 'INCOMPLETE_INPUT (TEST_SUITE_040 missing)')
    qb=[(_key(c),a,round(c['arms'][a]['query_max_s'] or 0,3)) for c in allc for a in QB_ARMS if a in c['arms']];worst=max([q for *_,q in qb],default=None)
    gate('GQB15',complete and worst is not None and worst<=QB,{'max_s':worst,'bound_s':QB,'over':[x for x in qb if x[2]>QB],
         **{f'{a}_max_s':max([c['arms'][a]['query_max_s'] or 0 for c in has(allc,a)],default=None) for a in ARMS}},why=wb)
    snd={'words_checked':sum(c['arms'][a].get('words_checked',0) for c in allc for a in ACTIVE if a in c['arms']),
         'words_unsound':sum(c['arms'][a].get('words_unsound',0) for c in allc for a in ACTIVE if a in c['arms']),
         'recount_words_checked':(rc or {}).get('words_checked'),'recount_words_unsound':(rc or {}).get('words_unsound'),
         'recount_truth_inconsistent':(rc or {}).get('truth_inconsistent')}
    gate('G_sound',complete and rc_ok and snd['words_unsound']==0 and snd['recount_words_unsound']==0 and snd['recount_truth_inconsistent']==0
         and snd['recount_words_checked']==snd['words_checked'],snd,why=wb)
    g10=[(c['seed'],{a:lab(c,a,pc) for a in c['arms']}) for c in G('control')]
    gate('G10',complete and rc_ok and len(g10)==6 and all(all(L=='ID' for L in x[1].values()) for x in g10),{'cases':g10,'rule':'every arm ID on every control'},why=wb)
    mt=(ref or {}).get('mutation_test') or {}
    robs=None if not ref else {k:ref.get(k) for k in ('arm_audited','family','N','cases','decided','not_reached','verdicts_checked','words_checked','mismatch_count','PASS')}|{'mutations':mt.get('detected'),'of':mt.get('mutations')}
    rbase=(bool(ref) and ref.get('study_results_sha256')==rsha and ref.get('cases')==len(s14) and ref.get('arm_audited')==HEAD and ref.get('family')=='scale14'
           and mt.get('detected')==mt.get('mutations')==20 and ref.get('mismatch_count')==0 and (ref.get('decided') or 0)>0)
    gate('GS_ref',rbase and ref.get('PASS') is True,robs,why=wb or (None if ref else 'INCOMPLETE_INPUT (REFERENCE_040 missing)'))
    gate('GTI',bool(mods) and ts.get('passed') is True and all(v.get('returncode')==0 for v in mods.values()),
         None if not ts else {k:{'returncode':v.get('returncode'),'tests':v.get('tests')} for k,v in mods.items()},why=None if ts else 'INCOMPLETE_INPUT (TEST_SUITE_040 missing)')
    lt=ledger();ev=[e for e,_ in lt];times=[t for _,t in lt];pos={e:ev.index(e) for e in PROC_ORDER if e in ev}
    proc={'all_events':len(pos)==len(PROC_ORDER),'order':len(pos)==len(PROC_ORDER) and all(pos[a]<pos[b] for a,b in zip(PROC_ORDER,PROC_ORDER[1:])),
          'ledger_times_parse':bool(lt) and all(t is not None for t in times),'ledger_times_non_decreasing':all(a<=b for a,b in zip(times,times[1:]) if a and b),
          'commit_order_file':order is not None,'main_sealed':bool(sealed)}
    gate('G_PROC',all(proc.values()),{'clauses':proc,'events':ev})
    el=(res or {}).get('total_elapsed_informational')
    gate('G_RT',complete and el is not None and el<=CAP,{'elapsed_s':el,'cap_s':CAP,'cases':len(allc)},why=wb)
    gate('G_recount',complete and rc_ok,None if not rc else {k:rc.get(k) for k in ('cases','labels','words_checked','words_unsound','mismatching_cases','PASS')},
         why=wb or (None if rc else 'INCOMPLETE_INPUT (RECOUNT_040 missing)'))
    gk={}
    for x,y in (('A15','A14'),('A15_cube','A15')):
        for k in EXPECTED:
            dd,m,ci=paired(G(k),x,y,pc)
            if dd:gk[f'ID({x})-ID({y})/{k}']={'mean':round(m,4),'ci95_seed_bootstrap':ci,'per_seed':dd}
    sec['GSYM15']={'pass':None,'observed':gk,'rule':'reported, not gated: encoding effect A15 - A14, cube effect A15_cube - A15'}
    sec['GCAP15']={'pass':None,'observed':{f'{a}/{k}':act_stats(G(k),a) for a in ARMS for k in EXPECTED if has(G(k),a)},
                   'rule':'reported: capped cases and calls, IDU last phase, cube counts, extra actions used and K_spent per arm and family'}
    return {'schema':'brute.gates.v37_0','study':'BRUTE-0370-APART-CUBE-040','process':'lean','sealed_input_verified':sealed,'gates':Gt,
            'secondary':sec,'all_gated_pass':all(g['pass'] for g in Gt.values() if g['pass'] is not None),
            'failed':[k for k,g in Gt.items() if g['pass'] is False],'not_exercised':[k for k,g in Gt.items() if g['pass'] is None],
            'reports':reports(allc,res,pc) if allc else {}}


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--study-dir',default=str(STUDY_DIR));ap.add_argument('--check',action='store_true');a=ap.parse_args()
    obj=build(Path(a.study_dir));out=Path(a.study_dir)/'GATES_040.json'
    if a.check:check(out.read_bytes()==dumps(obj),'GATES_040.json does not reproduce');print('GATES_040 reproduces')
    else:write_new(out,obj);print(json.dumps({k:v['pass'] for k,v in obj['gates'].items()}),obj['failed'])
