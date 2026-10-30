"""Gates for study-030 (BRUTE_PLAN_030; deviation #132 definitions), LEAN process.
Committed in the source freeze before run_start_030; nothing is tuned after results are seen. New file; built from
scripts/make_gates_029.py (frozen, unchanged).
Inputs (D = results/study-030): D/main/{RESULTS,SCIENTIFIC,SEAL}.json (51 cases), D/main/RECOUNT_030.json,
D/main/REFERENCE_030.json, D/TEST_SUITE_030.json, experiments/COMMIT_ORDER_030.json, results/RESEARCH_LEDGER.jsonl.
Missing or partial input => every data gate FAIL INCOMPLETE_INPUT. Case records are read from RESULTS.json and accepted
only if sha256(RESULTS) equals the seal and no_time(RESULTS) equals SCIENTIFIC.json.
Gated (plan criteria): GQB5, GSC5_headline a-d, G10, GS_ref, GTI, G_PROC, G_RT, G_recount.
Definitions (deviation #132):
  U(arm, case) = UNKNOWN queries / planned queries (an unrun query counts UNKNOWN); X = cases with U_count 0;
  TP(arm, case) = exact answers / arm wall seconds (identify excluded);
  GQB5: S5 max(query_max, observe_max) <= 10.5 s on every main case (as 029 GQB);
  a: 0 mismatches of S5 vs S1 and vs S4 on queries both answered exactly (main and stress) and 0 exact eps-0 S5 supports
     missing the latent next code, with > 0 compared;
  b: paired over the 12 scale12 eps-0 seeds, mean of d = U(S5) - U(S1) <= -0.08 AND the bootstrap 95% percentile CI
     of mean d (BOOT resamples of seeds, random.Random(BOOT_SEED)) has upper end < 0;
  c: X(S5, scale12) >= 5; d: recounted F(S5) = 0 over main and stress (strict);
  G10: every control eps-0 case has S5 U_count 0 and clause a mismatches 0 (vs S1 and S4);
  GS_ref: REFERENCE_030 audits arm S5 on every scale8 case: 0 mismatches, decided > 0, mutations detected 20/20.
Reports (not gated): X with Wilson 95% CIs, U with seed-bootstrap 95% CIs, TP, per (arm, family); query / observe max;
ID with Wilson CIs; F; certificates; UNKNOWN split; S5 cap counters; contrasts U(S5)-U(S5_softcap), U(S5)-U(S4),
U(S5)-U(S1), U(S5_softcap)-U(S1); TP ratios S5/S1.
  PYTHONPATH=. python scripts/make_gates_030.py [--study-dir D] [--check]"""
from __future__ import annotations
import argparse,json,random,sys
from datetime import datetime
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common_030 import STUDY_DIR,PLAN,FREEZE,load,dumps,write_new,check,sha,wilson

EXPECTED_MAIN={'scale8':12,'scale12':12,'scale16':12,'control_cycle3':6};EXPECTED_STRESS=9;CAP=1800;STEPS=176
QB=10.5;B_DELTA=0.08;X_MIN=5;BOOT=10000;BOOT_SEED=30
ARMS=('S5','S5_softcap','S4','S1');EXACT=('S5','S5_softcap','S4');STRESS_ARMS=('S5','S4','S1')
PROC_ORDER=('preregistration_030','build_authorization_030','seedcheck_030','scratch_diag_030','source_freeze_030','run_start_030')


def opt(p):
    p=Path(p)
    try:return load(p) if p.exists() else None
    except Exception:return None


def clause_a(c,other,arm='S5'):
    a,b=c['arms'][arm],c['arms'][other];cmpd=mis=exc=0
    for i in range(STEPS):
        for j in range(c['k']):
            if a['unk'][i][j]==0 and b['unk'][i][j]==0:cmpd+=1;mis+=a['sup'][i][j]!=b['sup'][i][j]
            else:exc+=1
    return cmpd,mis,exc


def truth_missing(c):
    """Exact S5 supports at eps 0 that miss the latent next code (regenerated from the seed)."""
    from experiments import worlds_026 as W
    w=W.world(c['seed'],c['family']);tr=W.trajectory(w,c['seed'],c['eps'])
    T=[[w.emissions[w.transitions[q][b]] for b in range(w.k)] for q in tr['states'][:STEPS]];a=c['arms']['S5'];chk=mis=0
    for i in range(STEPS):
        for j in range(c['k']):
            if a['unk'][i][j]==0 and a['sup'][i][j] is not None:chk+=1;mis+=T[i][j] not in a['sup'][i][j]
    return chk,mis


def ufrac(c,arm):a=c['arms'][arm];return a['U_count']/a['planned']


def boot_mean(v,n=BOOT,seed=BOOT_SEED):
    if not v:return None
    rng=random.Random(seed);m=len(v);s=sorted(sum(v[rng.randrange(m)] for _ in range(m))/m for _ in range(n))
    return [round(s[int(0.025*n)],4),round(s[int(0.975*n)-1],4)]


def X(cases,arm):
    n=len(cases);x=sum(1 for c in cases if c['arms'][arm]['U_count']==0);return {'x':x,'n':n,'X':x/n if n else None,'ci95':wilson(x,n)}


def U(cases,arm):
    u=sum(c['arms'][arm]['U_count'] for c in cases);p=sum(c['arms'][arm]['planned'] for c in cases);v=[ufrac(c,arm) for c in cases]
    return {'unknown':u,'planned':p,'U':u/p if p else None,'ci95_seed_bootstrap':boot_mean(v)}


def tp(c,arm):a=c['arms'][arm];w=a.get('arm_wall_informational');return None if not w else a['exact_answers']/w


def _mean(v):return None if not v else round(sum(v)/len(v),3)


def ledger(upto='run_start_030'):
    L=[json.loads(x) for x in (ROOT/'results/RESEARCH_LEDGER.jsonl').read_text().splitlines() if x.strip()]
    i0=next((i for i,e in enumerate(L) if e.get('event')=='preregistration_030'),None);out=[]
    for e in (L[i0:] if i0 is not None else []):
        try:t=datetime.fromisoformat(str(e.get('note',''))[:25])
        except ValueError:t=None
        out.append((e['event'],t))
        if e['event']==upto:break
    return out


def reports(main,stress,allc,res):
    F=tuple(EXPECTED_MAIN);fam=lambda f,cs=main:[c for c in cs if c['family']==f];r={}
    r['X']={f'{a}/{f}':X(fam(f),a) for a in ARMS for f in F}
    r['U']={f'{a}/{f}':U(fam(f),a) for a in ARMS for f in F}
    r['TP_mean_per_s']={f'{a}/{f}':_mean([tp(c,a) for c in fam(f) if tp(c,a) is not None]) for a in ARMS for f in F}
    r['exact_answers']={f'{a}/{f}':sum(c['arms'][a]['exact_answers'] for c in fam(f)) for a in ARMS for f in F}
    r['X_stress']={f'{a}/{f}':X(fam(f,stress),a) for a in STRESS_ARMS for f in ('scale8','scale12','scale16')}
    r['U_stress']={f'{a}/{f}':U(fam(f,stress),a) for a in STRESS_ARMS for f in ('scale8','scale12','scale16')}
    r['U_split']={f'{a}/{f}':{'not_run':sum(1 for c in fam(f) for row in c['arms'][a]['unk'] for u in row if u==-1),
                              'solver_unknown':sum(1 for c in fam(f) for row in c['arms'][a]['unk'] for u in row if u>=1)} for a in ARMS for f in F}
    r['query_max_s']={f'{a}/{f}':{'max':max([c['arms'][a]['query_max_informational'] for c in fam(f)],default=None),
                                  'mean_case_max':_mean([c['arms'][a]['query_max_informational'] for c in fam(f)])} for a in ARMS for f in F}
    r['observe_max_s']={f'{a}/{f}':max([c['arms'][a].get('observe_max_informational',0) for c in fam(f)],default=None) for a in EXACT for f in F}
    r['steps_done']={f'{a}/{f}':{'mean':_mean([c['arms'][a]['steps_done'] for c in fam(f)]),'full':sum(1 for c in fam(f) if c['arms'][a]['steps_done']==STEPS)} for a in ARMS for f in F}
    r['ID']={f'{a}/{f}':(lambda cs:{'ID':sum(c['arms'][a]['identify']['ID'] for c in cs),'n':len(cs),'ci95':wilson(sum(c['arms'][a]['identify']['ID'] for c in cs),len(cs)),
             'ran':sum(1 for c in cs if c['arms'][a]['identify']['ran'])})(fam(f)) for a in ARMS for f in F}
    r['certificates']={f'{a}/{f}':sum(c['arms'][a]['certificates'] for c in fam(f)) for a in ARMS for f in F}
    r['F_by_arm_block']={a:{blk:sum(c['arms'][a]['F'] for c in allc if c['block']==blk and a in c['arms']) for blk in ('main','stress')} for a in ARMS}
    r['S5_counters_mean']={f'{a}/{f}':{k:_mean([c['arms'][a].get(k,0) for c in fam(f)]) for k in ('solves','solver_unknowns','chunks','builds','cap_stops','build_skips',
                           'queries_by_witness','queries_by_solve','pool')} for a in EXACT for f in F}
    r['S5_max_chunk_s']={f'S5/{f}':max([c['arms']['S5'].get('max_chunk_s_informational',0) for c in fam(f)],default=None) for f in F}
    r['timing_mean_s']={f'{a}/{f}':{k:_mean([c['arms'][a].get('timing_informational',{}).get(k,0) for c in fam(f)]) for k in ('build','solve','pool')}
                        for a in EXACT for f in F}
    con={}
    for x,y in (('S5','S5_softcap'),('S5','S4'),('S5','S1'),('S5_softcap','S1'),('S4','S1')):
        for f in F:
            cs=sorted(fam(f),key=lambda c:c['seed']);d=[ufrac(c,x)-ufrac(c,y) for c in cs]
            con[f'U({x})-U({y})/{f}']={'mean':None if not d else round(sum(d)/len(d),4),'ci95_seed_bootstrap':boot_mean(d)}
    r['U_contrasts']=con
    tq={}
    for f in F:
        cs=sorted(fam(f),key=lambda c:c['seed'])
        for x,o in (('S5','S1'),('S5','S4')):
            v=[tp(c,x)/tp(c,o) for c in cs if tp(c,x) is not None and tp(c,o)]
            tq[f'{x}/{o}/{f}']={'median':None if not v else round(median(v),3),'mean':_mean(v),'ci95_seed_bootstrap':boot_mean(v)}
    r['TP_ratio']=tq
    r['mean_case_wall']=None if not res or not res['cases'] else round(sum(c['case_wall_informational'] for c in res['cases'])/len(res['cases']),1)
    return r


def median(v):
    v=sorted(v);n=len(v)
    return None if not n else (v[n//2] if n%2 else (v[n//2-1]+v[n//2])/2)


def build(study=STUDY_DIR):
    from brute.evaluation import no_time
    study=Path(study);D=study/'main';G={}
    seal=opt(D/'SEAL.json');sci=opt(D/'SCIENTIFIC.json');res=opt(D/'RESULTS.json');rc=opt(D/'RECOUNT_030.json')
    ref=opt(D/'REFERENCE_030.json');ts=opt(study/'TEST_SUITE_030.json');order=opt(ROOT/'experiments/COMMIT_ORDER_030.json')
    rsha=sha(D/'RESULTS.json') if (D/'RESULTS.json').exists() else None
    sealed=(bool(seal) and res is not None and sci is not None and rsha==seal.get('results_sha256')
            and sha(D/'SCIENTIFIC.json')==seal.get('scientific_sha256') and no_time(res)==sci)
    allc=(res or {}).get('cases',[]) if sealed else [];main=[c for c in allc if c['block']=='main'];stress=[c for c in allc if c['block']=='stress']
    fam=lambda f,cs=main:[c for c in cs if c['family']==f]
    complete=(sealed and seal.get('complete') is True and all(len(fam(f))==n for f,n in EXPECTED_MAIN.items()) and len(stress)==EXPECTED_STRESS)
    wb=None if complete else 'INCOMPLETE_INPUT (main missing, partial or not matching its seal)'
    def gate(name,ok,obs,why=None):G[name]={'pass':bool(ok) and why is None,'observed':obs,**({'reason':why} if why else {})}
    # GQB5
    qb=[(f"{c['family']}/{c['seed']}",round(c['arms']['S5']['query_max_informational'],3),round(c['arms']['S5'].get('observe_max_informational',0),3)) for c in main]
    worst=max([max(q,o) for _,q,o in qb],default=None)
    gate('GQB5',complete and worst is not None and worst<=QB,{'max_s':worst,'bound_s':QB,'over':[x for x in qb if max(x[1],x[2])>QB],
         'S5_softcap_max_s':max([max(c['arms']['S5_softcap']['query_max_informational'],c['arms']['S5_softcap'].get('observe_max_informational',0)) for c in main],default=None),
         'S4_max_s':max([max(c['arms']['S4']['query_max_informational'],c['arms']['S4'].get('observe_max_informational',0)) for c in main],default=None)},why=wb)
    # GSC5 a: S5 vs S1, S4 and truth
    A={o:dict(zip(('compared','mismatches','excluded'),map(sum,zip(*[clause_a(c,o) for c in allc] or [(0,0,0)])))) for o in ('S1','S4')}
    tm=[truth_missing(c) for c in main];A['truth']={'checked':sum(x[0] for x in tm),'missing':sum(x[1] for x in tm)}
    A['descriptive']={'S5_softcap_vs_S1':dict(zip(('compared','mismatches','excluded'),map(sum,zip(*[clause_a(c,'S1','S5_softcap') for c in main] or [(0,0,0)]))))}
    a_ok=complete and A['S1']['mismatches']==0 and A['S4']['mismatches']==0 and A['truth']['missing']==0 and A['S1']['compared']>0
    s12=sorted(fam('scale12'),key=lambda c:c['seed']);d=[ufrac(c,'S5')-ufrac(c,'S1') for c in s12];md=sum(d)/len(d) if d else None;ci=boot_mean(d)
    b_ok=complete and md is not None and md<=-B_DELTA and ci[1]<0
    x12=X(s12,'S5');c_ok=complete and x12['x']>=X_MIN
    F_rc=(rc or {}).get('F_total') or {};rc_ok=bool(rc) and rc.get('PASS') is True and rc.get('results_sha256')==rsha and rc.get('cases')==len(allc)
    d_ok=complete and rc_ok and F_rc.get('S5')==0
    gate('GSC5_headline',a_ok and b_ok and c_ok and d_ok,{
        'a':{'pass':a_ok,**A},
        'b':{'pass':b_ok,'mean_diff_U_S5_minus_S1':None if md is None else round(md,4),'ci95_seed_bootstrap':ci,'per_seed':[round(x,4) for x in d],
             'U_S5_scale12':U(s12,'S5'),'U_S1_scale12':U(s12,'S1'),'U_S4_scale12':U(s12,'S4'),'U_S5_softcap_scale12':U(s12,'S5_softcap'),
             'rule':'mean(U_S5 - U_S1) <= -0.08 and bootstrap CI upper < 0'},
        'c':{'pass':c_ok,**x12,'X_S1_scale12':X(s12,'S1'),'X_S4_scale12':X(s12,'S4'),'X_S5_softcap_scale12':X(s12,'S5_softcap'),'rule':'X(S5, scale12) >= 5/12'},
        'd':{'pass':d_ok,'F_recount':F_rc,'recount_pass':rc_ok,'strict':True}},why=wb)
    ctrl=fam('control_cycle3');g10=[(c['seed'],c['arms']['S5']['U_count'],clause_a(c,'S1')[1],clause_a(c,'S4')[1]) for c in ctrl]
    gate('G10',complete and len(g10)==6 and all(x[1]==0 and x[2]==0 and x[3]==0 for x in g10),{'cases':g10,'rule':'S5 U_count 0 and clause a 0 on every control eps-0 case'},why=wb)
    gate('GS_ref',bool(ref) and ref.get('PASS') is True and ref.get('study_results_sha256')==rsha and ref.get('cases')==len(fam('scale8',allc))
         and ref.get('arm_audited')=='S5' and (ref.get('mutation_test') or {}).get('detected')==(ref.get('mutation_test') or {}).get('mutations')==20,
         None if not ref else {k:ref.get(k) for k in ('arm_audited','cases','queries','exact_s2','decided','undecided','not_reached','coverage_of_exact',
         'decided_possible_codes','decided_impossible_codes','mismatch_count','PASS')}|{'mutations':(ref.get('mutation_test') or {}).get('detected'),'of':(ref.get('mutation_test') or {}).get('mutations')},
         why=wb or (None if ref else 'INCOMPLETE_INPUT (REFERENCE_030 missing)'))
    mods=(ts or {}).get('per_module') or {}
    gate('GTI',bool(mods) and ts.get('passed') is True and all(v.get('returncode')==0 for v in mods.values()),
         None if not ts else {k:{'returncode':v.get('returncode'),'tests':v.get('tests')} for k,v in mods.items()},why=None if ts else 'INCOMPLETE_INPUT (TEST_SUITE_030 missing)')
    lt=ledger();ev=[e for e,_ in lt];times=[t for _,t in lt];pos={e:ev.index(e) for e in PROC_ORDER if e in ev}
    proc={'all_events':len(pos)==len(PROC_ORDER),'order':len(pos)==len(PROC_ORDER) and all(pos[a]<pos[b] for a,b in zip(PROC_ORDER,PROC_ORDER[1:])),
          'ledger_times_parse':bool(lt) and all(t is not None for t in times),'ledger_times_non_decreasing':all(a<=b for a,b in zip(times,times[1:]) if a and b),
          'commit_order_file':order is not None}
    gate('G_PROC',all(proc.values()),{'clauses':proc,'events':ev})
    el=(res or {}).get('total_elapsed_informational')
    gate('G_RT',complete and el is not None and el<=CAP,{'elapsed_s':el,'cap_s':CAP,'cases':len(allc)},why=wb)
    gate('G_recount',complete and rc_ok,None if not rc else {k:rc.get(k) for k in ('cases','F_total','mismatching_cases','PASS')},why=wb or (None if rc else 'INCOMPLETE_INPUT (RECOUNT_030 missing)'))
    return {'schema':'brute.gates.v27_0','study':'BRUTE-0270-SYMMETRY-FREE-030','process':'lean','sealed_input_verified':sealed,'gates':G,
            'all_gated_pass':all(g['pass'] for g in G.values()),'failed':[k for k,g in G.items() if not g['pass']],
            'reports':reports(main,stress,allc,res) if allc else {}}


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--study-dir',default=str(STUDY_DIR));ap.add_argument('--check',action='store_true');a=ap.parse_args()
    obj=build(Path(a.study_dir));out=Path(a.study_dir)/'GATES_030.json'
    if a.check:check(out.read_bytes()==dumps(obj),'GATES_030.json does not reproduce');print('GATES_030 reproduces')
    else:write_new(out,obj);print(json.dumps({k:v['pass'] for k,v in obj['gates'].items()}),obj['failed'])
