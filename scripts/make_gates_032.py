"""Gates for study-032 (BRUTE_PLAN_032; deviation #136 definitions), LEAN process.
Committed in the source freeze before run_start_032; nothing is tuned after results are seen. New file; built from
scripts/make_gates_031.py (frozen, unchanged).
Inputs (D = results/study-032): D/main/{RESULTS,SCIENTIFIC,SEAL}.json (48 cases: 30 noisy, 12 clean, 6 control),
D/main/RECOUNT_032.json, D/main/REFERENCE_032.json, D/TEST_SUITE_032.json, experiments/COMMIT_ORDER_032.json,
results/RESEARCH_LEDGER.jsonl. Missing or partial input => every data gate FAIL INCOMPLETE_INPUT. Case records are read
from RESULTS.json and accepted only if sha256(RESULTS) equals the seal and no_time(RESULTS) equals SCIENTIFIC.json.
Gated (plan criteria): GRP7_headline a-e, GNR7, GQB7, G10, GS_ref, GTI, G_PROC, G_RT, G_recount.
Definitions (deviation #136):
  U(arm, case) = UNKNOWN queries / planned (an unrun query counts UNKNOWN); U_inf = U, except a case whose arm ends
  grammar_contradicted counts every planned query UNKNOWN; X_inf = cases with U_inf count 0;
  within_B(case) = realised prefix flips <= B(sensor readings so far) at every reading (B(t) = ceil(0.05 t + 2 sqrt(0.05 t)));
  F_truth(arm, case) = exact supports that exclude the true next code (recounted from the seed);
  GRP7 a: recounted F_truth(S7) = 0 on every noisy within_B case and on every clean and control case;
  b: paired over the 12 noisy_scale12 seeds, mean d = U_inf(S7) - U_inf(S5) <= -0.10 and the seed-bootstrap 95% CI
     (BOOT resamples, random.Random(BOOT_SEED)) upper end < 0; c: the same against S1 with -0.05;
  d: X_inf(S7, noisy_scale12) >= 3 (of 12); e: S7 grammar_contradicted on 0 noisy within_B cases;
  GNR7: paired over the 6 clean (eps 0) scale12 seeds, mean U(S7) - U(S5) <= +0.05 and CI upper <= +0.08, and 0
     S5_in_S7 mismatches (S5's exact support not a subset of S7's) over every eps-0 case, with > 0 compared;
  GQB7: S7 max(query_max, observe_max) <= 10.5 s on every case; G10: every control case has S7 U_count 0 and F_truth 0;
  GS_ref: REFERENCE_032 audits arm S7 on every noisy_scale8 case: 0 mismatches, decided > 0, mutations 20/20.
Reports (not gated): coverage of B; U, U_inf, X_inf with CIs per (arm, block/family); F and F_truth per arm; contradiction
verdicts per arm (S7_contra vacuity vs S1); S5_in_S7 equal/compared; contrasts; TP ratios; counters; query max.
  PYTHONPATH=. python scripts/make_gates_032.py [--study-dir D] [--check]"""
from __future__ import annotations
import argparse,json,random,sys
from datetime import datetime
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common_032 import STUDY_DIR,load,dumps,write_new,check,sha,wilson

EXPECTED={('noisy','noisy_scale8'):12,('noisy','noisy_scale12'):12,('noisy','noisy_scale16'):6,('clean','noisy_scale12'):6,
          ('clean','noisy_scale16'):6,('control','control_cycle3'):6}
CAP=1800;QB=10.5;B_S5=-0.10;B_S1=-0.05;X_MIN=3;NR_D=0.05;NR_CI=0.08;BOOT=10000;BOOT_SEED=32
ARMS=('S7','S7_contra','S5','S1');EXACT=('S7','S7_contra','S5')
PROC_ORDER=('preregistration_032','build_authorization_032','seedcheck_032','source_freeze_032','run_start_032')


def opt(p):
    p=Path(p)
    try:return load(p) if p.exists() else None
    except Exception:return None


def uf(c,arm,inf=True):a=c['arms'][arm];return (a['U_inf_count'] if inf else a['U_count'])/a['planned']


def boot_mean(v,n=BOOT,seed=BOOT_SEED):
    if not v:return None
    rng=random.Random(seed);m=len(v);s=sorted(sum(v[rng.randrange(m)] for _ in range(m))/m for _ in range(n))
    return [round(s[int(0.025*n)],4),round(s[int(0.975*n)-1],4)]


def X(cases,arm,inf=True):
    n=len(cases);k='U_inf_count' if inf else 'U_count';x=sum(1 for c in cases if c['arms'][arm][k]==0)
    return {'x':x,'n':n,'X':x/n if n else None,'ci95':wilson(x,n)}


def U(cases,arm,inf=True):
    k='U_inf_count' if inf else 'U_count';u=sum(c['arms'][arm][k] for c in cases);p=sum(c['arms'][arm]['planned'] for c in cases)
    return {'unknown':u,'planned':p,'U':u/p if p else None,'ci95_seed_bootstrap':boot_mean([uf(c,arm,inf) for c in cases])}


def paired(cs,x,y,inf=True):
    cs=sorted(cs,key=lambda c:c['seed']);d=[uf(c,x,inf)-uf(c,y,inf) for c in cs]
    return d,(sum(d)/len(d) if d else None),boot_mean(d)


def tp(c,arm):a=c['arms'][arm];w=a.get('arm_wall_informational');return None if not w else a['exact_answers']/w


def _mean(v):return None if not v else round(sum(v)/len(v),3)


def median(v):
    v=sorted(v);n=len(v)
    return None if not n else (v[n//2] if n%2 else (v[n//2-1]+v[n//2])/2)


def qmax(c,arm):a=c['arms'][arm];return max(a['query_max_informational'],a.get('observe_max_informational',0))


def ledger(upto='run_start_032'):
    L=[json.loads(x) for x in (ROOT/'results/RESEARCH_LEDGER.jsonl').read_text().splitlines() if x.strip()]
    i0=next((i for i,e in enumerate(L) if e.get('event')=='preregistration_032'),None);out=[]
    for e in (L[i0:] if i0 is not None else []):
        try:t=datetime.fromisoformat(str(e.get('note',''))[:25])
        except ValueError:t=None
        out.append((e['event'],t))
        if e['event']==upto:break
    return out


def reports(allc,res,rc):
    G=lambda b,f:[c for c in allc if c['block']==b and c['family']==f];r={}
    keys=[f'{b}/{f}' for b,f in EXPECTED]
    r['coverage_within_B']={f'noisy/{f}':{'x':sum(c['noise']['within_B'] for c in G('noisy',f)),'n':len(G('noisy',f)),
        'ci95':wilson(sum(c['noise']['within_B'] for c in G('noisy',f)),len(G('noisy',f))),
        'realised_flips':[c['noise']['realised_flips'] for c in sorted(G('noisy',f),key=lambda c:c['seed'])],
        'B_end':sorted({c['noise']['B_end'] for c in G('noisy',f)})} for f in ('noisy_scale8','noisy_scale12','noisy_scale16')}
    for nm,inf in (('U_inf',True),('U',False)):
        r[nm]={f'{a}/{k}':U(G(*k.split('/')),a,inf) for a in ARMS for k in keys}
        r['X'+nm[1:]]={f'{a}/{k}':X(G(*k.split('/')),a,inf) for a in ARMS for k in keys}
    r['grammar_contradicted']={f'{a}/{k}':{'x':sum(c['arms'][a]['grammar_contradicted'] for c in G(*k.split('/'))),
        'seeds':[c['seed'] for c in G(*k.split('/')) if c['arms'][a]['grammar_contradicted']]} for a in ARMS for k in keys}
    r['grammar_contradicted_within_B']={a:sum(c['arms'][a]['grammar_contradicted'] for c in allc if c['block']=='noisy' and c['noise']['within_B']) for a in ARMS}
    pc=(rc or {}).get('per_case') or {}
    def rcv(c,a,f):return (pc.get(f"{c['block']}/{c['family']}/{c['seed']}/{c['eps']}") or {}).get(a,{}).get(f)
    r['F_truth_recount']={f'{a}/{k}':{'total':sum(rcv(c,a,'F_truth') or 0 for c in G(*k.split('/'))),
        'within_B':sum(rcv(c,a,'F_truth') or 0 for c in G(*k.split('/')) if c['noise']['within_B']),
        'checked':sum(rcv(c,a,'F_truth_checked') or 0 for c in G(*k.split('/')))} for a in ARMS for k in keys}
    r['F_recount']={f'{a}/{k}':sum(rcv(c,a,'F') or 0 for c in G(*k.split('/'))) for a in ARMS for k in keys}
    r['certificates']={f'{a}/{k}':sum(c['arms'][a]['certificates'] for c in G(*k.split('/'))) for a in ARMS for k in keys}
    r['S5_in_S7']={k:{x:sum(c['S5_in_S7'][x] for c in G(*k.split('/'))) for x in ('compared','mismatches','equal')} for k in keys}
    con={}
    for x,y in (('S7','S5'),('S7','S1'),('S7_contra','S5'),('S7_contra','S1'),('S5','S1'),('S7','S7_contra')):
        for k in keys:
            for nm,inf in (('U_inf',True),('U',False)):
                d,m,ci=paired(G(*k.split('/')),x,y,inf);con[f'{nm}({x})-{nm}({y})/{k}']={'mean':None if m is None else round(m,4),'ci95_seed_bootstrap':ci}
    r['contrasts']=con
    r['exact_answers']={f'{a}/{k}':sum(c['arms'][a]['exact_answers'] for c in G(*k.split('/'))) for a in ARMS for k in keys}
    r['TP_mean_per_s']={f'{a}/{k}':_mean([tp(c,a) for c in G(*k.split('/')) if tp(c,a) is not None]) for a in ARMS for k in keys}
    tq={}
    for k in keys:
        for x,o in (('S7','S5'),('S7','S1')):
            v=[tp(c,x)/tp(c,o) for c in G(*k.split('/')) if tp(c,x) is not None and tp(c,o)]
            tq[f'{x}/{o}/{k}']={'median':None if not v else round(median(v),3),'ci95_seed_bootstrap':boot_mean(v)}
    r['TP_ratio']=tq
    r['U_split']={f'{a}/{k}':{'not_run':sum(1 for c in G(*k.split('/')) for row in c['arms'][a]['unk'] for u in row if u==-1),
        'solver_unknown':sum(1 for c in G(*k.split('/')) for row in c['arms'][a]['unk'] for u in row if u>=1)} for a in ARMS for k in keys}
    r['steps_done_mean']={f'{a}/{k}':_mean([c['arms'][a]['steps_done'] for c in G(*k.split('/'))]) for a in ARMS for k in keys}
    r['query_max_s']={f'{a}/{k}':max([qmax(c,a) for c in G(*k.split('/'))],default=None) for a in ARMS for k in keys}
    r['counters_mean']={f'{a}/{k}':{x:_mean([c['arms'][a].get(x,0) for c in G(*k.split('/'))]) for x in ('solves','solver_unknowns','chunks','builds',
        'cap_stops','build_skips','queries_by_witness','queries_by_solve','pool','contra_checks','contra_unknown','flip_budget_end')} for a in EXACT for k in keys}
    r['mean_case_wall']=None if not res or not res['cases'] else round(sum(c['case_wall_informational'] for c in res['cases'])/len(res['cases']),1)
    return r


def build(study=STUDY_DIR):
    from brute.evaluation import no_time
    study=Path(study);D=study/'main';Gt={}
    seal=opt(D/'SEAL.json');sci=opt(D/'SCIENTIFIC.json');res=opt(D/'RESULTS.json');rc=opt(D/'RECOUNT_032.json')
    ref=opt(D/'REFERENCE_032.json');ts=opt(study/'TEST_SUITE_032.json');order=opt(ROOT/'experiments/COMMIT_ORDER_032.json')
    rsha=sha(D/'RESULTS.json') if (D/'RESULTS.json').exists() else None
    sealed=(bool(seal) and res is not None and sci is not None and rsha==seal.get('results_sha256')
            and sha(D/'SCIENTIFIC.json')==seal.get('scientific_sha256') and no_time(res)==sci)
    allc=(res or {}).get('cases',[]) if sealed else []
    G=lambda b,f:[c for c in allc if c['block']==b and c['family']==f]
    complete=sealed and seal.get('complete') is True and all(len(G(b,f))==n for (b,f),n in EXPECTED.items()) and len(allc)==sum(EXPECTED.values())
    wb=None if complete else 'INCOMPLETE_INPUT (main missing, partial or not matching its seal)'
    def gate(name,ok,obs,why=None):Gt[name]={'pass':bool(ok) and why is None,'observed':obs,**({'reason':why} if why else {})}
    pc=(rc or {}).get('per_case') or {}
    rc_ok=bool(rc) and rc.get('PASS') is True and rc.get('results_sha256')==rsha and rc.get('cases')==len(allc)
    def rft(c):return (pc.get(f"{c['block']}/{c['family']}/{c['seed']}/{c['eps']}") or {}).get('S7',{}).get('F_truth')
    noisy=[c for c in allc if c['block']=='noisy'];inB=[c for c in noisy if c['noise']['within_B']];clean=[c for c in allc if c['block'] in ('clean','control')]
    fa=[(c['block'],c['family'],c['seed'],rft(c)) for c in inB+clean]
    a_ok=complete and rc_ok and all(x[3]==0 for x in fa)
    n12=G('noisy','noisy_scale12');d5,m5,ci5=paired(n12,'S7','S5');d1,m1,ci1=paired(n12,'S7','S1')
    b_ok=complete and m5 is not None and m5<=B_S5 and ci5[1]<0
    c_ok=complete and m1 is not None and m1<=B_S1 and ci1[1]<0
    x12=X(n12,'S7');d_ok=complete and x12['x']>=X_MIN
    gcB=[(c['family'],c['seed']) for c in inB if c['arms']['S7']['grammar_contradicted']];e_ok=complete and not gcB
    gate('GRP7_headline',a_ok and b_ok and c_ok and d_ok and e_ok,{
        'a':{'pass':a_ok,'cases_checked':len(fa),'noisy_within_B':len(inB),'noisy':len(noisy),'clean_and_control':len(clean),
             'F_truth_S7_nonzero':[x for x in fa if x[3]!=0],'F_truth_S7_total':sum(x[3] or 0 for x in fa),'recount_pass':rc_ok,
             'F_truth_S7_outside_B':[(c['family'],c['seed'],rft(c)) for c in noisy if not c['noise']['within_B']]},
        'b':{'pass':b_ok,'mean_diff_U_inf_S7_minus_S5':None if m5 is None else round(m5,4),'ci95_seed_bootstrap':ci5,'per_seed':[round(x,4) for x in d5],
             **{f'U_inf_{a}_noisy_scale12':U(n12,a) for a in ARMS},'rule':'mean(U_inf S7 - U_inf S5) <= -0.10 and CI upper < 0'},
        'c':{'pass':c_ok,'mean_diff_U_inf_S7_minus_S1':None if m1 is None else round(m1,4),'ci95_seed_bootstrap':ci1,'per_seed':[round(x,4) for x in d1],
             'rule':'mean(U_inf S7 - U_inf S1) <= -0.05 and CI upper < 0'},
        'd':{'pass':d_ok,**x12,**{f'X_inf_{a}_noisy_scale12':X(n12,a) for a in ARMS if a!='S7'},'rule':'X_inf(S7, noisy_scale12) >= 3/12'},
        'e':{'pass':e_ok,'S7_contradicted_within_B':gcB,'rule':'0 grammar_contradicted from S7 on within_B noisy cases'}},why=wb)
    c12=G('clean','noisy_scale12');dn,mn,cin=paired(c12,'S7','S5',False)
    s5s7={x:sum(c['S5_in_S7'][x] for c in clean) for x in ('compared','mismatches','equal')}
    nr_ok=complete and mn is not None and mn<=NR_D and cin[1]<=NR_CI and s5s7['mismatches']==0 and s5s7['compared']>0
    gate('GNR7',nr_ok,{'mean_diff_U_S7_minus_S5_clean12':None if mn is None else round(mn,4),'ci95_seed_bootstrap':cin,'per_seed':[round(x,4) for x in dn],
         **{f'U_{a}_clean12':U(c12,a,False) for a in ARMS},'S5_in_S7_eps0':s5s7,
         'mismatch_cases':[(c['block'],c['family'],c['seed']) for c in clean if c['S5_in_S7']['mismatches']],
         'rule':'mean(U S7 - U S5, clean scale12) <= +0.05, CI upper <= +0.08, 0 S5_in_S7 mismatches over eps-0 cases'},why=wb)
    qb=[(f"{c['block']}/{c['family']}/{c['seed']}",round(c['arms']['S7']['query_max_informational'],3),round(c['arms']['S7'].get('observe_max_informational',0),3)) for c in allc]
    worst=max([max(q,o) for _,q,o in qb],default=None)
    gate('GQB7',complete and worst is not None and worst<=QB,{'max_s':worst,'bound_s':QB,'over':[x for x in qb if max(x[1],x[2])>QB],
         **{f'{a}_max_s':max([qmax(c,a) for c in allc],default=None) for a in ARMS if a!='S7'}},why=wb)
    ctrl=G('control','control_cycle3');g10=[(c['seed'],c['arms']['S7']['U_count'],rft(c)) for c in ctrl]
    gate('G10',complete and rc_ok and len(g10)==6 and all(x[1]==0 and x[2]==0 for x in g10),{'cases':g10,'rule':'S7 U_count 0 and F_truth 0 on every control'},why=wb)
    mt=(ref or {}).get('mutation_test') or {}
    gate('GS_ref',bool(ref) and ref.get('PASS') is True and ref.get('study_results_sha256')==rsha and ref.get('cases')==len(G('noisy','noisy_scale8'))
         and ref.get('arm_audited')=='S7' and mt.get('detected')==mt.get('mutations')==20,
         None if not ref else {k:ref.get(k) for k in ('arm_audited','family','cases','queries','exact','decided','undecided','not_reached','coverage_of_exact',
         'checked_codes','decided_possible_codes','decided_impossible_codes','mismatch_count','PASS')}|{'mutations':mt.get('detected'),'of':mt.get('mutations')},
         why=wb or (None if ref else 'INCOMPLETE_INPUT (REFERENCE_032 missing)'))
    mods=(ts or {}).get('per_module') or {}
    gate('GTI',bool(mods) and ts.get('passed') is True and all(v.get('returncode')==0 for v in mods.values()),
         None if not ts else {k:{'returncode':v.get('returncode'),'tests':v.get('tests')} for k,v in mods.items()},why=None if ts else 'INCOMPLETE_INPUT (TEST_SUITE_032 missing)')
    lt=ledger();ev=[e for e,_ in lt];times=[t for _,t in lt];pos={e:ev.index(e) for e in PROC_ORDER if e in ev}
    proc={'all_events':len(pos)==len(PROC_ORDER),'order':len(pos)==len(PROC_ORDER) and all(pos[a]<pos[b] for a,b in zip(PROC_ORDER,PROC_ORDER[1:])),
          'ledger_times_parse':bool(lt) and all(t is not None for t in times),'ledger_times_non_decreasing':all(a<=b for a,b in zip(times,times[1:]) if a and b),
          'commit_order_file':order is not None}
    gate('G_PROC',all(proc.values()),{'clauses':proc,'events':ev})
    el=(res or {}).get('total_elapsed_informational')
    gate('G_RT',complete and el is not None and el<=CAP,{'elapsed_s':el,'cap_s':CAP,'cases':len(allc)},why=wb)
    gate('G_recount',complete and rc_ok,None if not rc else {k:rc.get(k) for k in ('cases','F_total','F_truth_total','mismatching_cases','PASS')},
         why=wb or (None if rc else 'INCOMPLETE_INPUT (RECOUNT_032 missing)'))
    return {'schema':'brute.gates.v29_0','study':'BRUTE-0290-ROBUST-PERCEPTION-032','process':'lean','sealed_input_verified':sealed,'gates':Gt,
            'all_gated_pass':all(g['pass'] for g in Gt.values()),'failed':[k for k,g in Gt.items() if not g['pass']],
            'reports':reports(allc,res,rc) if allc else {}}


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--study-dir',default=str(STUDY_DIR));ap.add_argument('--check',action='store_true');a=ap.parse_args()
    obj=build(Path(a.study_dir));out=Path(a.study_dir)/'GATES_032.json'
    if a.check:check(out.read_bytes()==dumps(obj),'GATES_032.json does not reproduce');print('GATES_032 reproduces')
    else:write_new(out,obj);print(json.dumps({k:v['pass'] for k,v in obj['gates'].items()}),obj['failed'])
