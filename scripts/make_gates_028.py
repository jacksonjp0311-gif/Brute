"""Gates for study-028 (BRUTE_PLAN_028 criteria; deviation #128 definitions), LEAN process. Committed in the source freeze
before run_start_028; nothing is tuned after results are seen. New file.
Inputs (D = results/study-028): D/main/{RESULTS,SCIENTIFIC,SEAL}.json (51 cases), D/main/RECOUNT_028.json,
D/main/REFERENCE_028.json, D/main/API_CHECK_028.json, D/TEST_SUITE_028.json, experiments/COMMIT_ORDER_028.json,
results/RESEARCH_LEDGER.jsonl. Missing or partial input => every data gate FAIL INCOMPLETE_INPUT.
Gated: GQB, GSC3_headline a-d (e descriptive), G10, GAPI13, GS_ref13, GTI, G_PROC, G_RT, G_recount.
Definitions (deviation #128):
  U(arm, case) = UNKNOWN queries / planned queries (an unrun query counts UNKNOWN); X = cases with U_count 0;
  GQB: S3 max(query_max, observe_max) <= 10.5 s on every main case;
  b: paired over the 12 scale12 eps-0 seeds, mean of d = U(S3) - U(S2) <= -0.15 AND the bootstrap 95% percentile CI
     of mean d (BOOT resamples of seeds, random.Random(BOOT_SEED)) has upper end < 0;
  G10: every control eps-0 case has S3 U_count 0 (no solver UNKNOWN and no unrun query) and clause a mismatches 0.
Reports: X with Wilson 95% CIs, U with seed-bootstrap 95% CIs, per (arm, family); query / observe max; ID; F;
certificates; UNKNOWN split; per-phase S3 timing; solver wins.
  PYTHONPATH=. python scripts/make_gates_028.py [--study-dir D] [--check]"""
from __future__ import annotations
import argparse,json,random,sys
from datetime import datetime
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common_028 import STUDY_DIR,PLAN,FREEZE,load,dumps,write_new,check,sha,wilson

EXPECTED_MAIN={'scale8':12,'scale12':12,'scale16':12,'control_cycle3':6};EXPECTED_STRESS=9;CAP=1800;STEPS=176
QB=10.5;B_DELTA=0.15;X_MIN=3;BOOT=10000;BOOT_SEED=28
ARMS=('S3','S3_tight','S2','S1');EXACT=('S3','S3_tight','S2')
HOST_BANNED=('import os','socket','threading','subprocess','open(','multiprocessing','import signal')
PROC_ORDER=('preregistration_028','build_authorization_028','seedcheck_028','source_freeze_028','run_start_028')


def opt(p):
    p=Path(p)
    try:return load(p) if p.exists() else None
    except Exception:return None


def clause_a(c,other):
    a,b=c['arms']['S3'],c['arms'][other];cmpd=mis=exc=0
    for i in range(STEPS):
        for j in range(c['k']):
            if a['unk'][i][j]==0 and b['unk'][i][j]==0:cmpd+=1;mis+=a['sup'][i][j]!=b['sup'][i][j]
            else:exc+=1
    return cmpd,mis,exc


def truth_missing(c):
    """Exact S3 supports at eps 0 that miss the latent next code (regenerated from the seed)."""
    from experiments import worlds_026 as W
    w=W.world(c['seed'],c['family']);tr=W.trajectory(w,c['seed'],c['eps'])
    T=[[w.emissions[w.transitions[q][b]] for b in range(w.k)] for q in tr['states'][:STEPS]];a=c['arms']['S3'];chk=mis=0
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


def _mean(v):return None if not v else round(sum(v)/len(v),3)


def api_probe():
    try:
        from brute.api import certify13 as C13
        from brute.api.certify12 import certify12
        init,acts,obs=(0,1),[0,1,0,1,1,0,0,1,1,1,0],[(0,1),(1,None),(0,1),(1,0),(None,1),(0,1),(1,0),(0,0),(1,1),(0,1),(1,None)]
        K=('supports','unknown','certificates','status','m','steps')
        d=C13.certify13(init,acts,obs);d12=certify12(init,acts,obs)
        s2=C13.certify13(init,acts,obs,family_bound=3,search='s2');s2b=certify12(init,acts,obs,family_bound=3,search='s2')
        s3=C13.certify13(init,acts,obs,family_bound=3,search='s3')
        return {'api':d.get('api'),'searches':list(C13.SEARCHES),'region_equals_certify12':all(d.get(k)==d12.get(k) for k in K),
                's2_equals_certify12':all(s2.get(k)==s2b.get(k) for k in K),'s3_api':s3.get('api'),'s3_search':s3.get('search'),
                's3_equals_s2_small':all(s3.get(k)==s2b.get(k) for k in ('supports','unknown','certificates','status')),'error':None}
    except Exception as e:return {'error':f'{type(e).__name__}: {e}'}


def ledger(upto='run_start_028'):
    L=[json.loads(x) for x in (ROOT/'results/RESEARCH_LEDGER.jsonl').read_text().splitlines() if x.strip()]
    i0=next((i for i,e in enumerate(L) if e.get('event')=='preregistration_028'),None);out=[]
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
    r['X_stress']={f'{a}/{f}':X(fam(f,stress),a) for a in ('S3','S2','S1') for f in ('scale8','scale12','scale16')}
    r['U_stress']={f'{a}/{f}':U(fam(f,stress),a) for a in ('S3','S2','S1') for f in ('scale8','scale12','scale16')}
    r['U_split']={f'{a}/{f}':{'not_run':sum(1 for c in fam(f) for row in c['arms'][a]['unk'] for u in row if u==-1),
                              'solver_unknown':sum(1 for c in fam(f) for row in c['arms'][a]['unk'] for u in row if u>=1)} for a in ARMS for f in F}
    r['query_max_s']={f'{a}/{f}':{'max':max([c['arms'][a]['query_max_informational'] for c in fam(f)],default=None),
                                  'mean_case_max':_mean([c['arms'][a]['query_max_informational'] for c in fam(f)])} for a in ARMS for f in F}
    r['observe_max_s']={f'{a}/{f}':max([c['arms'][a].get('observe_max_informational',0) for c in fam(f)],default=None) for a in EXACT for f in F}
    r['steps_done']={f'{a}/{f}':{'mean':_mean([c['arms'][a]['steps_done'] for c in fam(f)]),'full':sum(1 for c in fam(f) if c['arms'][a]['steps_done']==STEPS)} for a in ARMS for f in F}
    r['ID']={f'{a}/{f}':(lambda cs:{'ID':sum(c['arms'][a]['identify']['ID'] for c in cs),'n':len(cs),'ci95':wilson(sum(c['arms'][a]['identify']['ID'] for c in cs),len(cs)),
             'ran':sum(1 for c in cs if c['arms'][a]['identify']['ran'])})(fam(f)) for a in EXACT for f in F}
    r['n_lo']={f'{a}/{f}':{'mean':_mean([c['arms'][a]['n_lo'] for c in fam(f)]),'equals_n':sum(1 for c in fam(f) if c['arms'][a]['n_lo']==c['n'])} for a in EXACT for f in F}
    r['certificates']={f'{a}/{f}':sum(c['arms'][a]['certificates'] for c in fam(f)) for a in ARMS for f in F}
    r['F_by_arm_block']={a:{blk:sum(c['arms'][a]['F'] for c in allc if c['block']==blk and a in c['arms']) for blk in ('main','stress')} for a in ARMS}
    r['S3_timing_mean_s']={f:{k:_mean([c['arms']['S3'].get('timing_informational',{}).get(k,0) for c in fam(f)]) for k in ('repair','add_step','feasible','chain','solve_support')} for f in F}
    r['S3_solver_wins']={f:{s:sum(c['arms']['S3'].get('solver_wins',{}).get(s,0) for c in fam(f)) for s in ('m22','mcb')} for f in F}
    r['mean_case_wall']=None if not res or not res['cases'] else round(sum(c['case_wall_informational'] for c in res['cases'])/len(res['cases']),1)
    return r


def build(study=STUDY_DIR):
    study=Path(study);D=study/'main';G={}
    seal=opt(D/'SEAL.json');sci=opt(D/'SCIENTIFIC.json');res=opt(D/'RESULTS.json');rc=opt(D/'RECOUNT_028.json')
    ref=opt(D/'REFERENCE_028.json');apck=opt(D/'API_CHECK_028.json');ts=opt(study/'TEST_SUITE_028.json');order=opt(ROOT/'experiments/COMMIT_ORDER_028.json')
    allc=(sci or {}).get('cases',[]);main=[c for c in allc if c['block']=='main'];stress=[c for c in allc if c['block']=='stress']
    fam=lambda f,cs=main:[c for c in cs if c['family']==f]
    complete=(bool(seal) and seal.get('complete') is True and sha(D/'SCIENTIFIC.json')==seal.get('scientific_sha256')
              and all(len(fam(f))==n for f,n in EXPECTED_MAIN.items()) and len(stress)==EXPECTED_STRESS)
    wb=None if complete else 'INCOMPLETE_INPUT (main missing, partial or not matching its seal)'
    def gate(name,ok,obs,why=None):G[name]={'pass':bool(ok) and why is None,'observed':obs,**({'reason':why} if why else {})}
    rsha=sha(D/'RESULTS.json') if (D/'RESULTS.json').exists() else None
    # GQB
    qb=[(f"{c['family']}/{c['seed']}",round(c['arms']['S3']['query_max_informational'],3),round(c['arms']['S3'].get('observe_max_informational',0),3)) for c in main]
    worst=max([max(q,o) for _,q,o in qb],default=None)
    gate('GQB',complete and worst is not None and worst<=QB,{'max_s':worst,'bound_s':QB,'over':[x for x in qb if max(x[1],x[2])>QB]},why=wb)
    # GSC3 a: S3 vs S2, S1 and truth (eps 0 main)
    A={o:dict(zip(('compared','mismatches','excluded'),map(sum,zip(*[clause_a(c,o) for c in allc] or [(0,0,0)])))) for o in ('S2','S1')}
    tm=[truth_missing(c) for c in main];A['truth']={'checked':sum(x[0] for x in tm),'missing':sum(x[1] for x in tm)}
    a_ok=complete and A['S2']['mismatches']==0 and A['S1']['mismatches']==0 and A['truth']['missing']==0 and A['S2']['compared']>0
    s12=sorted(fam('scale12'),key=lambda c:c['seed']);d=[ufrac(c,'S3')-ufrac(c,'S2') for c in s12];md=sum(d)/len(d) if d else None;ci=boot_mean(d)
    b_ok=complete and md is not None and md<=-B_DELTA and ci[1]<0
    x12=X(s12,'S3');c_ok=complete and x12['x']>=X_MIN
    F_rc=(rc or {}).get('F_total') or {};rc_ok=bool(rc) and rc.get('PASS') is True and rc.get('results_sha256')==rsha and rc.get('cases')==len(allc)
    d_ok=complete and rc_ok and F_rc.get('S3')==0
    gate('GSC3_headline',a_ok and b_ok and c_ok and d_ok,{
        'a':{'pass':a_ok,**A},
        'b':{'pass':b_ok,'mean_diff_U_S3_minus_S2':None if md is None else round(md,4),'ci95_seed_bootstrap':ci,'per_seed':[round(x,4) for x in d],
             'U_S3_scale12':U(s12,'S3'),'U_S2_scale12':U(s12,'S2'),'rule':'mean(U_S3 - U_S2) <= -0.15 and bootstrap CI upper < 0'},
        'c':{'pass':c_ok,**x12,'rule':'X(S3, scale12) >= 3/12'},
        'd':{'pass':d_ok,'F_recount':F_rc,'recount_pass':rc_ok,'strict':True},
        'e':{'descriptive':True,'ID_S3':{f:sum(c['arms']['S3']['identify']['ID'] for c in fam(f)) for f in EXPECTED_MAIN},
             'certificates_S3':{f:sum(c['arms']['S3']['certificates'] for c in fam(f)) for f in EXPECTED_MAIN}}},why=wb)
    ctrl=fam('control_cycle3');g10=[(c['seed'],c['arms']['S3']['U_count'],clause_a(c,'S2')[1],clause_a(c,'S1')[1]) for c in ctrl]
    gate('G10',complete and all(x[1]==0 and x[2]==0 and x[3]==0 for x in g10),{'cases':g10,'rule':'S3 U_count 0 and clause a 0 on every control eps-0 case'},why=wb)
    # GAPI13
    p=api_probe();old={}
    for rel in ['brute/api/certify.py']+[f'brute/api/certify{n}.py' for n in range(2,13)]:
        fz=next((f for f in sorted(ROOT.glob('experiments/BRUTE_SOURCE_FREEZE_0*.json')) if f!=FREEZE and rel in (load(f).get('sha256_files') or {})),None)
        old[rel]=fz is not None and load(fz)['sha256_files'][rel]==sha(ROOT/rel)
    src=''.join((ROOT/f).read_text() for f in ('brute/api/certify13.py','brute/scalesearch3.py'))
    api={'probe_api':p.get('api')=='brute.certify/13' and p.get('s3_api')=='brute.certify/13' and p.get('s3_search')=='s3',
         'searches':p.get('searches')==['region','s2','s3'],'region_equals_certify12':p.get('region_equals_certify12') is True,
         's2_equals_certify12':p.get('s2_equals_certify12') is True,'certify_to_certify12_unchanged':all(old.values()),
         'host_agnostic_source_scan':not any(x in src for x in HOST_BANNED),
         'stream_check':bool(apck) and apck.get('passed') is True and apck.get('results_sha256')==rsha}
    gate('GAPI13',all(api.values()),{'clauses':api,'probe':p,'older':old,'stream':None if not apck else {k:v for k,v in apck.items() if k!='cases'}},
         why=None if apck else 'INCOMPLETE_INPUT (API_CHECK_028 missing)')
    gate('GS_ref13',bool(ref) and ref.get('PASS') is True and ref.get('study_results_sha256')==rsha and ref.get('cases')==len(fam('scale8',allc)),
         None if not ref else {k:ref.get(k) for k in ('arm_audited','cases','queries','exact_s2','decided','undecided','not_reached','coverage_of_exact',
         'decided_possible_codes','decided_impossible_codes','mismatch_count','PASS')}|{'mutations':(ref.get('mutation_test') or {}).get('detected'),'of':(ref.get('mutation_test') or {}).get('mutations')},
         why=wb or (None if ref else 'INCOMPLETE_INPUT (REFERENCE_028 missing)'))
    mods=(ts or {}).get('per_module') or {}
    gate('GTI',bool(mods) and ts.get('passed') is True and all(v.get('returncode')==0 for v in mods.values()),
         None if not ts else {k:{'returncode':v.get('returncode'),'tests':v.get('tests')} for k,v in mods.items()},why=None if ts else 'INCOMPLETE_INPUT (TEST_SUITE_028 missing)')
    lt=ledger();ev=[e for e,_ in lt];times=[t for _,t in lt];pos={e:ev.index(e) for e in PROC_ORDER if e in ev}
    proc={'all_events':len(pos)==len(PROC_ORDER),'order':len(pos)==len(PROC_ORDER) and all(pos[a]<pos[b] for a,b in zip(PROC_ORDER,PROC_ORDER[1:])),
          'ledger_times_parse':bool(lt) and all(t is not None for t in times),'ledger_times_non_decreasing':all(a<=b for a,b in zip(times,times[1:]) if a and b),
          'commit_order_file':order is not None}
    gate('G_PROC',all(proc.values()),{'clauses':proc,'events':ev})
    el=(res or {}).get('total_elapsed_informational')
    gate('G_RT',complete and el is not None and el<=CAP,{'elapsed_s':el,'cap_s':CAP,'cases':len(allc)},why=wb)
    gate('G_recount',complete and rc_ok,None if not rc else {k:rc.get(k) for k in ('cases','F_total','mismatching_cases','PASS')},why=wb or (None if rc else 'INCOMPLETE_INPUT (RECOUNT_028 missing)'))
    return {'schema':'brute.gates.v25_0','study':'BRUTE-0250-SOLVER-COST-028','process':'lean','gates':G,
            'all_gated_pass':all(g['pass'] for g in G.values()),'failed':[k for k,g in G.items() if not g['pass']],
            'reports':reports(main,stress,allc,res) if allc else {}}


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--study-dir',default=str(STUDY_DIR));ap.add_argument('--check',action='store_true');a=ap.parse_args()
    obj=build(Path(a.study_dir));out=Path(a.study_dir)/'GATES_028.json'
    if a.check:check(out.read_bytes()==dumps(obj),'GATES_028.json does not reproduce');print('GATES_028 reproduces')
    else:write_new(out,obj);print(json.dumps({k:v['pass'] for k,v in obj['gates'].items()}),obj['failed'])
