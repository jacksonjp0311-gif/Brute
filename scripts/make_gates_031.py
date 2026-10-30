"""Gates for study-031 (BRUTE_PLAN_031; deviation #134 definitions), LEAN process.
Committed in the source freeze before run_start_031; nothing is tuned after results are seen. New file; built from
scripts/make_gates_030.py (frozen, unchanged).
Inputs (D = results/study-031): D/main/{RESULTS,SCIENTIFIC,SEAL}.json (54 cases), D/main/RECOUNT_031.json,
D/main/REFERENCE_031.json, D/TEST_SUITE_031.json, experiments/COMMIT_ORDER_031.json, results/RESEARCH_LEDGER.jsonl.
Missing or partial input => every data gate FAIL INCOMPLETE_INPUT. Case records are read from RESULTS.json and accepted
only if sha256(RESULTS) equals the seal and no_time(RESULTS) equals SCIENTIFIC.json.
Gated (plan criteria): GSC6_headline a-d, GID6 a-c, GQB6, G10, GS_ref, GTI, G_PROC, G_RT, G_recount.
Definitions (deviation #134):
  U(arm, case) = UNKNOWN queries / planned queries (an unrun query counts UNKNOWN); X = cases with U_count 0;
  TP(arm, case) = exact answers / arm wall seconds (identify excluded);
  GSC6 a: 0 mismatches of S6 vs S1 and vs S5 on queries both answered exactly (main and stress) and 0 exact eps-0 S6
     supports missing the latent next code, with > 0 compared;
  b: paired over the 18 scale16 eps-0 seeds, mean of d = U(S6) - U(S5) <= -0.06 AND the bootstrap 95% percentile CI
     of mean d (BOOT resamples of seeds, random.Random(BOOT_SEED)) has upper end < 0;
  c: X(S6, scale16) >= 4 (of 18); d: recounted F(S6) = 0 over main and stress (strict);
  GID6 a: no eps-0 main case has label WRONG for any arm; b: ID(S6, scale12) >= 4 (of 12);
     c: IDU(S6, scale12) <= 2, where IDU counts labels IDU and NR (identify not run: arm did not finish; conservative);
  GQB6: S6 max(query_max, observe_max) <= 10.5 s on every main and stress case;
  G10: every control eps-0 case has S6 U_count 0, S6 label ID and clause a mismatches 0 (vs S1 and S5);
  GS_ref: REFERENCE_031 audits arm S6 on every scale8 case: 0 mismatches, decided > 0, mutations detected 20/20.
Reports (not gated): X with Wilson 95% CIs, U with seed-bootstrap 95% CIs, TP, per (arm, family); stress X/U for every arm;
ID/AMB/WRONG/IDU/NR per (arm, family) with Wilson CIs; identify diagnostics (n_min vs n, unexercised truth pairs);
query / observe max; F; certificates; UNKNOWN split; counters; contrasts U(S6)-U(S6_noorder), U(S6)-U(S5), U(S6)-U(S1),
U(S5)-U(S1); TP ratios.
  PYTHONPATH=. python scripts/make_gates_031.py [--study-dir D] [--check]"""
from __future__ import annotations
import argparse,json,random,sys
from datetime import datetime
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common_031 import STUDY_DIR,PLAN,FREEZE,load,dumps,write_new,check,sha,wilson

EXPECTED_MAIN={'scale8':12,'scale12':12,'scale16':18,'control_cycle3':6};EXPECTED_STRESS=6;CAP=1800;STEPS=176
QB=10.5;B_DELTA=0.06;X_MIN=4;ID_MIN=4;IDU_MAX=2;BOOT=10000;BOOT_SEED=31
ARMS=('S6','S6_noorder','S5','S1');EXACT=('S6','S6_noorder','S5');LABELS=('ID','AMB','WRONG','IDU','NR')
STRESS_F=('scale12','scale16')
PROC_ORDER=('preregistration_031','build_authorization_031','seedcheck_031','scratch_diag_031','source_freeze_031','run_start_031')


def opt(p):
    p=Path(p)
    try:return load(p) if p.exists() else None
    except Exception:return None


def clause_a(c,other,arm='S6'):
    a,b=c['arms'][arm],c['arms'][other];cmpd=mis=exc=0
    for i in range(STEPS):
        for j in range(c['k']):
            if a['unk'][i][j]==0 and b['unk'][i][j]==0:cmpd+=1;mis+=a['sup'][i][j]!=b['sup'][i][j]
            else:exc+=1
    return cmpd,mis,exc


def truth_missing(c,arm='S6'):
    """Exact supports of the arm at eps 0 that miss the latent next code (regenerated from the seed)."""
    from experiments import worlds_026 as W
    w=W.world(c['seed'],c['family']);tr=W.trajectory(w,c['seed'],c['eps'])
    T=[[w.emissions[w.transitions[q][b]] for b in range(w.k)] for q in tr['states'][:STEPS]];a=c['arms'][arm];chk=mis=0
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


def labels(cases,arm):
    n=len(cases);out={'n':n}
    for L in LABELS:
        x=sum(1 for c in cases if c['arms'][arm]['identify']['label']==L);out[L]={'x':x,'ci95':wilson(x,n)}
    x=out['IDU']['x']+out['NR']['x'];out['IDU_incl_NR']={'x':x,'ci95':wilson(x,n)}
    return out


def tp(c,arm):a=c['arms'][arm];w=a.get('arm_wall_informational');return None if not w else a['exact_answers']/w


def _mean(v):return None if not v else round(sum(v)/len(v),3)


def median(v):
    v=sorted(v);n=len(v)
    return None if not n else (v[n//2] if n%2 else (v[n//2-1]+v[n//2])/2)


def qmax(c,arm):a=c['arms'][arm];return max(a['query_max_informational'],a.get('observe_max_informational',0))


def ledger(upto='run_start_031'):
    L=[json.loads(x) for x in (ROOT/'results/RESEARCH_LEDGER.jsonl').read_text().splitlines() if x.strip()]
    i0=next((i for i,e in enumerate(L) if e.get('event')=='preregistration_031'),None);out=[]
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
    r['identify_labels']={f'{a}/{f}':labels(fam(f),a) for a in ARMS for f in F}
    r['identify_diagnostics']={f:{'n_min_lt_n':sum(1 for c in fam(f) if (c['identify_probe']['n_min'] or 99)<c['n']),
        'n_min_values':[c['identify_probe']['n_min'] for c in sorted(fam(f),key=lambda c:c['seed'])],
        'probe_labels':[c['identify_probe']['label'] for c in sorted(fam(f),key=lambda c:c['seed'])],
        'unexercised_truth_pairs':[c['identify_probe']['truth_pairs_unexercised'] for c in sorted(fam(f),key=lambda c:c['seed'])],
        'cases_with_unexercised_pairs':sum(1 for c in fam(f) if c['identify_probe']['truth_pairs_unexercised']>0),
        'WRONG_sound':sum(c['identify_probe']['WRONG_sound'] for c in fam(f)),
        'probe_wall_max_s':max([c['identify_probe']['wall_informational'] for c in fam(f)],default=None)} for f in F}
    r['TP_mean_per_s']={f'{a}/{f}':_mean([tp(c,a) for c in fam(f) if tp(c,a) is not None]) for a in ARMS for f in F}
    r['exact_answers']={f'{a}/{f}':sum(c['arms'][a]['exact_answers'] for c in fam(f)) for a in ARMS for f in F}
    r['X_stress']={f'{a}/{f}':X(fam(f,stress),a) for a in ARMS for f in STRESS_F}
    r['U_stress']={f'{a}/{f}':U(fam(f,stress),a) for a in ARMS for f in STRESS_F}
    r['U_stress_all']={a:U(stress,a) for a in ARMS}
    r['U_split']={f'{a}/{f}':{'not_run':sum(1 for c in fam(f) for row in c['arms'][a]['unk'] for u in row if u==-1),
                              'solver_unknown':sum(1 for c in fam(f) for row in c['arms'][a]['unk'] for u in row if u>=1)} for a in ARMS for f in F}
    r['query_max_s']={f'{a}/{f}':{'max':max([qmax(c,a) for c in fam(f)],default=None),
                                  'mean_case_max':_mean([qmax(c,a) for c in fam(f)])} for a in ARMS for f in F}
    r['query_max_s_stress']={a:max([qmax(c,a) for c in stress],default=None) for a in ARMS}
    r['steps_done']={f'{a}/{f}':{'mean':_mean([c['arms'][a]['steps_done'] for c in fam(f)]),'full':sum(1 for c in fam(f) if c['arms'][a]['steps_done']==STEPS)} for a in ARMS for f in F}
    r['certificates']={f'{a}/{f}':sum(c['arms'][a]['certificates'] for c in fam(f)) for a in ARMS for f in F}
    r['F_by_arm_block']={a:{blk:sum(c['arms'][a]['F'] for c in allc if c['block']==blk) for blk in ('main','stress')} for a in ARMS}
    r['counters_mean']={f'{a}/{f}':{k:_mean([c['arms'][a].get(k,0) for c in fam(f)]) for k in ('solves','solver_unknowns','chunks','builds','extends',
                        'cap_stops','build_skips','queries_by_witness','queries_by_solve','pool','reordered_steps')} for a in EXACT for f in F}
    r['timing_mean_s']={f'{a}/{f}':{k:_mean([c['arms'][a].get('timing_informational',{}).get(k,0) for c in fam(f)]) for k in ('build','solve','pool')}
                        for a in EXACT for f in F}
    con={}
    for x,y in (('S6','S6_noorder'),('S6','S5'),('S6','S1'),('S6_noorder','S5'),('S5','S1')):
        for f in F:
            cs=sorted(fam(f),key=lambda c:c['seed']);d=[ufrac(c,x)-ufrac(c,y) for c in cs]
            con[f'U({x})-U({y})/{f}']={'mean':None if not d else round(sum(d)/len(d),4),'ci95_seed_bootstrap':boot_mean(d)}
        cs=sorted(stress,key=lambda c:(c['family'],c['seed']));d=[ufrac(c,x)-ufrac(c,y) for c in cs]
        con[f'U({x})-U({y})/stress']={'mean':None if not d else round(sum(d)/len(d),4),'ci95_seed_bootstrap':boot_mean(d)}
    r['U_contrasts']=con
    tq={}
    for f in F:
        cs=sorted(fam(f),key=lambda c:c['seed'])
        for x,o in (('S6','S1'),('S6','S5'),('S6','S6_noorder')):
            v=[tp(c,x)/tp(c,o) for c in cs if tp(c,x) is not None and tp(c,o)]
            tq[f'{x}/{o}/{f}']={'median':None if not v else round(median(v),3),'mean':_mean(v),'ci95_seed_bootstrap':boot_mean(v)}
    r['TP_ratio']=tq
    r['mean_case_wall']=None if not res or not res['cases'] else round(sum(c['case_wall_informational'] for c in res['cases'])/len(res['cases']),1)
    return r


def build(study=STUDY_DIR):
    from brute.evaluation import no_time
    study=Path(study);D=study/'main';G={}
    seal=opt(D/'SEAL.json');sci=opt(D/'SCIENTIFIC.json');res=opt(D/'RESULTS.json');rc=opt(D/'RECOUNT_031.json')
    ref=opt(D/'REFERENCE_031.json');ts=opt(study/'TEST_SUITE_031.json');order=opt(ROOT/'experiments/COMMIT_ORDER_031.json')
    rsha=sha(D/'RESULTS.json') if (D/'RESULTS.json').exists() else None
    sealed=(bool(seal) and res is not None and sci is not None and rsha==seal.get('results_sha256')
            and sha(D/'SCIENTIFIC.json')==seal.get('scientific_sha256') and no_time(res)==sci)
    allc=(res or {}).get('cases',[]) if sealed else [];main=[c for c in allc if c['block']=='main'];stress=[c for c in allc if c['block']=='stress']
    fam=lambda f,cs=main:[c for c in cs if c['family']==f]
    complete=(sealed and seal.get('complete') is True and all(len(fam(f))==n for f,n in EXPECTED_MAIN.items()) and len(stress)==EXPECTED_STRESS)
    wb=None if complete else 'INCOMPLETE_INPUT (main missing, partial or not matching its seal)'
    def gate(name,ok,obs,why=None):G[name]={'pass':bool(ok) and why is None,'observed':obs,**({'reason':why} if why else {})}
    # GSC6
    A={o:dict(zip(('compared','mismatches','excluded'),map(sum,zip(*[clause_a(c,o) for c in allc] or [(0,0,0)])))) for o in ('S1','S5')}
    tm=[truth_missing(c) for c in main];A['truth']={'checked':sum(x[0] for x in tm),'missing':sum(x[1] for x in tm)}
    A['descriptive']={'S6_noorder_vs_S1':dict(zip(('compared','mismatches','excluded'),map(sum,zip(*[clause_a(c,'S1','S6_noorder') for c in allc] or [(0,0,0)])))),
                      'S6_noorder_vs_S6':dict(zip(('compared','mismatches','excluded'),map(sum,zip(*[clause_a(c,'S6','S6_noorder') for c in allc] or [(0,0,0)]))))}
    a_ok=complete and A['S1']['mismatches']==0 and A['S5']['mismatches']==0 and A['truth']['missing']==0 and A['S1']['compared']>0
    s16=sorted(fam('scale16'),key=lambda c:c['seed']);d=[ufrac(c,'S6')-ufrac(c,'S5') for c in s16];md=sum(d)/len(d) if d else None;ci=boot_mean(d)
    b_ok=complete and md is not None and md<=-B_DELTA and ci[1]<0
    x16=X(s16,'S6');c_ok=complete and x16['x']>=X_MIN
    F_rc=(rc or {}).get('F_total') or {};rc_ok=bool(rc) and rc.get('PASS') is True and rc.get('results_sha256')==rsha and rc.get('cases')==len(allc)
    d_ok=complete and rc_ok and F_rc.get('S6')==0
    gate('GSC6_headline',a_ok and b_ok and c_ok and d_ok,{
        'a':{'pass':a_ok,**A},
        'b':{'pass':b_ok,'mean_diff_U_S6_minus_S5':None if md is None else round(md,4),'ci95_seed_bootstrap':ci,'per_seed':[round(x,4) for x in d],
             **{f'U_{a}_scale16':U(s16,a) for a in ARMS},'rule':'mean(U_S6 - U_S5) <= -0.06 and bootstrap CI upper < 0'},
        'c':{'pass':c_ok,**x16,**{f'X_{a}_scale16':X(s16,a) for a in ARMS if a!='S6'},'rule':'X(S6, scale16) >= 4/18'},
        'd':{'pass':d_ok,'F_recount':F_rc,'recount_pass':rc_ok,'strict':True}},why=wb)
    # GID6
    wrong={a:[f"{c['family']}/{c['seed']}" for c in main if c['arms'][a]['identify']['label']=='WRONG'] for a in ARMS}
    ga=complete and all(not v for v in wrong.values())
    s12=fam('scale12');L12=labels(s12,'S6') if s12 else None
    gb=complete and L12['ID']['x']>=ID_MIN;gc=complete and L12['IDU_incl_NR']['x']<=IDU_MAX
    gate('GID6',ga and gb and gc,{'a':{'pass':ga,'WRONG_by_arm':wrong,
         'WRONG_sound_cases':sum(c['identify_probe']['WRONG_sound'] for c in main if 'identify_probe' in c),'rule':'WRONG = 0 for every arm'},
         'b':{'pass':gb,'S6_scale12':L12,'rule':'ID(S6, scale12) >= 4/12'},
         'c':{'pass':gc,'IDU_incl_NR':None if not L12 else L12['IDU_incl_NR'],'rule':'IDU + NR (S6, scale12) <= 2/12'}},why=wb)
    qb=[(f"{c['block']}/{c['family']}/{c['seed']}",round(c['arms']['S6']['query_max_informational'],3),round(c['arms']['S6'].get('observe_max_informational',0),3)) for c in allc]
    worst=max([max(q,o) for _,q,o in qb],default=None)
    gate('GQB6',complete and worst is not None and worst<=QB,{'max_s':worst,'bound_s':QB,'over':[x for x in qb if max(x[1],x[2])>QB],
         **{f'{a}_max_s':max([qmax(c,a) for c in allc],default=None) for a in ARMS if a!='S6'}},why=wb)
    ctrl=fam('control_cycle3');g10=[(c['seed'],c['arms']['S6']['U_count'],c['arms']['S6']['identify']['label'],clause_a(c,'S1')[1],clause_a(c,'S5')[1]) for c in ctrl]
    gate('G10',complete and len(g10)==6 and all(x[1]==0 and x[2]=='ID' and x[3]==0 and x[4]==0 for x in g10),
         {'cases':g10,'rule':'S6 U_count 0, label ID and clause a 0 on every control eps-0 case'},why=wb)
    gate('GS_ref',bool(ref) and ref.get('PASS') is True and ref.get('study_results_sha256')==rsha and ref.get('cases')==len(fam('scale8',allc))
         and ref.get('arm_audited')=='S6' and (ref.get('mutation_test') or {}).get('detected')==(ref.get('mutation_test') or {}).get('mutations')==20,
         None if not ref else {k:ref.get(k) for k in ('arm_audited','cases','queries','exact_s2','decided','undecided','not_reached','coverage_of_exact',
         'decided_possible_codes','decided_impossible_codes','mismatch_count','PASS')}|{'mutations':(ref.get('mutation_test') or {}).get('detected'),'of':(ref.get('mutation_test') or {}).get('mutations')},
         why=wb or (None if ref else 'INCOMPLETE_INPUT (REFERENCE_031 missing)'))
    mods=(ts or {}).get('per_module') or {}
    gate('GTI',bool(mods) and ts.get('passed') is True and all(v.get('returncode')==0 for v in mods.values()),
         None if not ts else {k:{'returncode':v.get('returncode'),'tests':v.get('tests')} for k,v in mods.items()},why=None if ts else 'INCOMPLETE_INPUT (TEST_SUITE_031 missing)')
    lt=ledger();ev=[e for e,_ in lt];times=[t for _,t in lt];pos={e:ev.index(e) for e in PROC_ORDER if e in ev}
    proc={'all_events':len(pos)==len(PROC_ORDER),'order':len(pos)==len(PROC_ORDER) and all(pos[a]<pos[b] for a,b in zip(PROC_ORDER,PROC_ORDER[1:])),
          'ledger_times_parse':bool(lt) and all(t is not None for t in times),'ledger_times_non_decreasing':all(a<=b for a,b in zip(times,times[1:]) if a and b),
          'commit_order_file':order is not None}
    gate('G_PROC',all(proc.values()),{'clauses':proc,'events':ev})
    el=(res or {}).get('total_elapsed_informational')
    gate('G_RT',complete and el is not None and el<=CAP,{'elapsed_s':el,'cap_s':CAP,'cases':len(allc)},why=wb)
    gate('G_recount',complete and rc_ok,None if not rc else {k:rc.get(k) for k in ('cases','F_total','mismatching_cases','PASS')},why=wb or (None if rc else 'INCOMPLETE_INPUT (RECOUNT_031 missing)'))
    return {'schema':'brute.gates.v28_0','study':'BRUTE-0280-SIXTEEN-STATE-ID-031','process':'lean','sealed_input_verified':sealed,'gates':G,
            'all_gated_pass':all(g['pass'] for g in G.values()),'failed':[k for k,g in G.items() if not g['pass']],
            'reports':reports(main,stress,allc,res) if allc else {}}


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--study-dir',default=str(STUDY_DIR));ap.add_argument('--check',action='store_true');a=ap.parse_args()
    obj=build(Path(a.study_dir));out=Path(a.study_dir)/'GATES_031.json'
    if a.check:check(out.read_bytes()==dumps(obj),'GATES_031.json does not reproduce');print('GATES_031 reproduces')
    else:write_new(out,obj);print(json.dumps({k:v['pass'] for k,v in obj['gates'].items()}),obj['failed'])
