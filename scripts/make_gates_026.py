"""Gates for study-026 (BRUTE_PLAN_026 criteria; deviation #123 definitions), LEAN process. Committed in the source freeze
before run_start_026; nothing is tuned after results are seen. New file.
Inputs (D = results/study-026): D/main/{RESULTS,SCIENTIFIC,SEAL}.json (93 cases), D/main/RECOUNT_026.json,
D/main/REFERENCE_026.json, D/main/API_CHECK_026.json, D/TEST_SUITE_026.json, experiments/COMMIT_ORDER_026.json,
results/RESEARCH_LEDGER.jsonl. Missing or partial input => every data gate FAIL INCOMPLETE_INPUT.
Gated: GSC_headline a-e, G10, GAPI12, GS_ref12, GTI, G_PROC, G_RT, G_recount. Reports: X per (arm, family) with Wilson 95%
CIs (also per eps), U fractions, clause a counts, F, ID, C_late.
  PYTHONPATH=. python scripts/make_gates_026.py [--study-dir D] [--check]"""
from __future__ import annotations
import argparse,json,sys
from datetime import datetime
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common_026 import STUDY_DIR,PLAN,FREEZE,load,dumps,write_new,check,sha,wilson

EXPECTED_MAIN={'scale8':24,'scale12':24,'scale16':24,'control_cycle3':12};EXPECTED_STRESS=9;CAP=1800;STEPS=176
HOST_BANNED=('import os','socket','threading','subprocess','open(','multiprocessing','import signal')
PROC_ORDER=('preregistration_026','build_authorization_026','seedcheck_026','s2_code_026','source_freeze_026','run_start_026')


def opt(p):
    p=Path(p)
    try:return load(p) if p.exists() else None
    except Exception:return None


def clause_a(c):
    a,b=c['arms']['S2'],c['arms']['S1'];cmpd=mis=exc=0
    for i in range(STEPS):
        for j in range(c['k']):
            if a['unk'][i][j]==0 and b['unk'][i][j]==0:cmpd+=1;mis+=a['sup'][i][j]!=b['sup'][i][j]
            else:exc+=1
    return cmpd,mis,exc


def X(cases,arm):
    n=len(cases);x=sum(1 for c in cases if c['arms'][arm]['U_count']==0);return {'x':x,'n':n,'X':x/n if n else None,'ci95':wilson(x,n)}


def U(cases,arm):
    u=sum(c['arms'][arm]['U_count'] for c in cases);p=sum(c['arms'][arm]['planned'] for c in cases)
    return {'unknown':u,'planned':p,'U':u/p if p else None}


def api_probe():
    try:
        from brute.api import certify12 as C12
        from brute.api.certify11 import certify11
        init,acts,obs=(0,1),[0,1,0,1,1,0,0,1,1,1,0],[(0,1),(1,None),(0,1),(1,0),(None,1),(0,1),(1,0),(0,0),(1,1),(0,1),(1,None)]
        K=('supports','unknown','certificates','status','m','steps');d=C12.certify12(init,acts,obs);d11=certify11(init,acts,obs)
        s=C12.certify12(init,acts,obs,family_bound=3,search='s2')
        return {'api':d.get('api'),'searches':list(C12.SEARCHES),'region_equals_certify11':all(d.get(k)==d11.get(k) for k in K),
                's2_api':s.get('api'),'s2_search':s.get('search'),'error':None}
    except Exception as e:return {'error':f'{type(e).__name__}: {e}'}


def ledger(upto='run_start_026'):
    L=[json.loads(x) for x in (ROOT/'results/RESEARCH_LEDGER.jsonl').read_text().splitlines() if x.strip()]
    i0=next((i for i,e in enumerate(L) if e.get('event')=='preregistration_026'),None);out=[]
    for e in (L[i0:] if i0 is not None else []):
        try:t=datetime.fromisoformat(str(e.get('note',''))[:25])
        except ValueError:t=None
        out.append((e['event'],t))
        if e['event']==upto:break
    return out


def build(study=STUDY_DIR):
    study=Path(study);D=study/'main';G={}
    seal=opt(D/'SEAL.json');sci=opt(D/'SCIENTIFIC.json');res=opt(D/'RESULTS.json');rc=opt(D/'RECOUNT_026.json')
    ref=opt(D/'REFERENCE_026.json');apck=opt(D/'API_CHECK_026.json');ts=opt(study/'TEST_SUITE_026.json');order=opt(ROOT/'experiments/COMMIT_ORDER_026.json')
    allc=(sci or {}).get('cases',[]);main=[c for c in allc if c['block']=='main'];stress=[c for c in allc if c['block']=='stress']
    fam=lambda f,cs=main:[c for c in cs if c['family']==f]
    complete=(bool(seal) and seal.get('complete') is True and sha(D/'SCIENTIFIC.json')==seal.get('scientific_sha256')
              and all(len(fam(f))==n for f,n in EXPECTED_MAIN.items()) and len(stress)==EXPECTED_STRESS)
    wb=None if complete else 'INCOMPLETE_INPUT (main missing, partial or not matching its seal)'
    def gate(name,ok,obs,why=None):G[name]={'pass':bool(ok) and why is None,'observed':obs,**({'reason':why} if why else {})}
    rsha=sha(D/'RESULTS.json') if (D/'RESULTS.json').exists() else None
    # clause a (recomputed from the records)
    ca=[clause_a(c) for c in allc];A={'compared':sum(x[0] for x in ca),'mismatches':sum(x[1] for x in ca),'excluded':sum(x[2] for x in ca)}
    a_ok=complete and A['mismatches']==0 and A['compared']>0
    Xs={(arm,f):X(fam(f),arm) for arm in ('S1','S2') for f in EXPECTED_MAIN}
    x2_12,x1_12,x2_8=Xs[('S2','scale12')]['X'],Xs[('S1','scale12')]['X'],Xs[('S2','scale8')]['X']
    b_ok=complete and None not in (x2_12,x1_12,x2_8) and x2_12>=x1_12+0.25 and x2_8>=0.9
    u16=U(fam('scale16'),'S2');c_ok=complete and u16['U'] is not None and u16['U']<=0.10
    F_rc=(rc or {}).get('F_total') or {};rc_ok=bool(rc) and rc.get('PASS') is True and rc.get('results_sha256')==rsha and rc.get('cases')==len(allc)
    d_ok=complete and rc_ok and F_rc.get('S2')==0 and F_rc.get('RGB6')==0
    s8e0=[c for c in fam('scale8') if c['eps']==0];idn=sum(c['arms']['S2']['identify']['ID'] for c in s8e0)
    e_ok=complete and len(s8e0)==12 and idn/12>=0.8
    gate('GSC_headline',a_ok and b_ok and c_ok and d_ok and e_ok,{
        'a':{'pass':a_ok,**A},
        'b':{'pass':b_ok,'X_S2_scale12':Xs[('S2','scale12')],'X_S1_scale12':Xs[('S1','scale12')],'X_S2_scale8':Xs[('S2','scale8')],
             'rule':'X(S2,scale12) >= X(S1,scale12) + 0.25 and X(S2,scale8) >= 0.9'},
        'c':{'pass':c_ok,**u16,'rule':'U(S2, scale16) <= 0.10'},
        'd':{'pass':d_ok,'F_recount':F_rc,'recount_pass':rc_ok,'strict':True},
        'e':{'pass':e_ok,'ID_count':idn,'cases':len(s8e0),'ID':idn/len(s8e0) if s8e0 else None,'ci95':wilson(idn,len(s8e0))}},why=wb)
    ctrl=fam('control_cycle3');g10=[(f"{c['seed']}/{c['eps']}",c['arms']['S1']['U_count'],c['arms']['S2']['U_count'],clause_a(c)[1]) for c in ctrl]
    gate('G10',complete and all(x[1]==0 and x[2]==0 and x[3]==0 for x in g10),{'cases':g10},why=wb)
    # GAPI12
    p=api_probe();old={}
    for rel in ['brute/api/certify.py']+[f'brute/api/certify{n}.py' for n in range(2,12)]:
        fz=next((f for f in sorted(ROOT.glob('experiments/BRUTE_SOURCE_FREEZE_0*.json')) if rel in (load(f).get('sha256_files') or {})),None)
        old[rel]=fz is not None and load(fz)['sha256_files'][rel]==sha(ROOT/rel)
    src=''.join((ROOT/f).read_text() for f in ('brute/api/certify12.py','brute/scalesearch.py','brute/scalebetting.py'))
    api={'probe_api':p.get('api')=='brute.certify/12' and p.get('s2_api')=='brute.certify/12','searches':p.get('searches')==['region','s2'],
         'region_equals_certify11':p.get('region_equals_certify11') is True,'certify_to_certify11_unchanged':all(old.values()),
         'host_agnostic_source_scan':not any(x in src for x in HOST_BANNED),
         'stream_check':bool(apck) and apck.get('passed') is True and apck.get('results_sha256')==rsha}
    gate('GAPI12',all(api.values()),{'clauses':api,'probe':p,'older':old,'stream':None if not apck else {k:v for k,v in apck.items() if k!='cases'}},
         why=None if apck else 'INCOMPLETE_INPUT (API_CHECK_026 missing)')
    gate('GS_ref12',bool(ref) and ref.get('PASS') is True and ref.get('study_results_sha256')==rsha and ref.get('cases')==len(fam('scale8',allc)),
         None if not ref else {k:ref.get(k) for k in ('cases','queries','exact_s2','decided','undecided','not_reached','coverage_of_exact',
         'decided_possible_codes','decided_impossible_codes','mismatch_count','PASS')}|{'mutations':(ref.get('mutation_test') or {}).get('detected'),'of':(ref.get('mutation_test') or {}).get('mutations')},
         why=wb or (None if ref else 'INCOMPLETE_INPUT (REFERENCE_026 missing)'))
    mods=(ts or {}).get('per_module') or {}
    gate('GTI',bool(mods) and ts.get('passed') is True and all(v.get('returncode')==0 for v in mods.values()),
         None if not ts else {k:{'returncode':v.get('returncode'),'tests':v.get('tests')} for k,v in mods.items()},why=None if ts else 'INCOMPLETE_INPUT (TEST_SUITE_026 missing)')
    lt=ledger();ev=[e for e,_ in lt];times=[t for _,t in lt];pos={e:ev.index(e) for e in PROC_ORDER if e in ev}
    proc={'all_events':len(pos)==len(PROC_ORDER),'order':len(pos)==len(PROC_ORDER) and all(pos[a]<pos[b] for a,b in zip(PROC_ORDER,PROC_ORDER[1:])),
          'ledger_times_parse':bool(lt) and all(t is not None for t in times),'ledger_times_non_decreasing':all(a<=b for a,b in zip(times,times[1:]) if a and b),
          'commit_order_file':order is not None}
    gate('G_PROC',all(proc.values()),{'clauses':proc,'events':ev})
    el=(res or {}).get('total_elapsed_informational')
    gate('G_RT',complete and el is not None and el<=CAP,{'elapsed_s':el,'cap_s':CAP,'cases':len(allc)},why=wb)
    gate('G_recount',complete and rc_ok,None if not rc else {k:rc.get(k) for k in ('cases','F_total','mismatching_cases','PASS')},why=wb or (None if rc else 'INCOMPLETE_INPUT (RECOUNT_026 missing)'))
    # reports (not gated)
    arms=('S1','S2','RGB6')
    rep={'X':{f'{a}/{f}':Xs[(a,f)] for a,f in Xs},
         'X_per_eps':{f'{a}/{f}/eps{e}':X([c for c in fam(f) if c['eps']==e],a) for a in ('S1','S2') for f in EXPECTED_MAIN for e in (0.0,0.02)},
         'X_RGB6':{f:X([c for c in fam(f) if c['eps']==0.02],'RGB6') for f in EXPECTED_MAIN},
         'X_stress':{f'{a}/{f}':X(fam(f,stress),a) for a in arms for f in ('scale8','scale12','scale16')},
         'U':{f'{a}/{f}':U([c for c in fam(f) if a in c['arms']],a) for a in arms for f in EXPECTED_MAIN},
         'U_per_eps':{f'{a}/{f}/eps{e}':U([c for c in fam(f) if c['eps']==e and a in c['arms']],a) for a in arms for f in EXPECTED_MAIN for e in (0.0,0.02) if not (a=='RGB6' and e==0)},
         'U_stress':{f'{a}/{f}':U(fam(f,stress),a) for a in arms for f in ('scale8','scale12','scale16')},
         'F_by_arm_block':{a:{blk:sum(c['arms'][a]['F'] for c in allc if c['block']==blk and a in c['arms']) for blk in ('main','stress')} for a in arms},
         'certificates_by_arm':{a:sum(c['arms'][a]['certificates'] for c in allc if a in c['arms']) for a in arms},
         'C_late_RGB6_eps002':(lambda cs:{'certificates':sum(c['arms']['RGB6']['late_certificates'] for c in cs),'queries':sum(c['arms']['RGB6']['late_queries'] for c in cs)})
                             ([c for c in main if c['eps']==0.02]),
         'ID_by_family_eps0':{f:{'ID':sum(c['arms']['S2']['identify']['ID'] for c in fam(f) if c['eps']==0),'n':len([c for c in fam(f) if c['eps']==0]),
                                 'n_min_equals_n':sum(1 for c in fam(f) if c['eps']==0 and c['arms']['S2']['identify']['n_min']==c['n'])} for f in EXPECTED_MAIN},
         'clause_a_by_family':{f:dict(zip(('compared','mismatches','excluded'),map(sum,zip(*[clause_a(c) for c in fam(f,allc)] or [(0,0,0)])))) for f in EXPECTED_MAIN},
         'mean_case_wall':None if not res or not res['cases'] else round(sum(c['case_wall_informational'] for c in res['cases'])/len(res['cases']),1)}
    cl=rep['C_late_RGB6_eps002'];cl['C_late']=cl['certificates']/cl['queries'] if cl['queries'] else None
    return {'schema':'brute.gates.v23_0','study':'BRUTE-0230-SCALE-026','process':'lean','gates':G,
            'all_gated_pass':all(g['pass'] for g in G.values()),'failed':[k for k,g in G.items() if not g['pass']],'reports':rep}


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--study-dir',default=str(STUDY_DIR));ap.add_argument('--check',action='store_true');a=ap.parse_args()
    obj=build(Path(a.study_dir));out=Path(a.study_dir)/'GATES_026.json'
    if a.check:check(out.read_bytes()==dumps(obj),'GATES_026.json does not reproduce');print('GATES_026 reproduces')
    else:write_new(out,obj);print(json.dumps({k:v['pass'] for k,v in obj['gates'].items()}),obj['failed'])
