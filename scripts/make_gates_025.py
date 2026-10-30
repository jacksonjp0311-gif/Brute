"""Gates for study-025, LEAN process (BRUTE_PLAN_025 + A1 + A2 effective criteria). Committed in the source freeze before
the held-out run_start (A2: no separate scoring-freeze wait); nothing is tuned after results are seen.
Inputs (D = results/study-025): D/transfer/{RESULTS,SCIENTIFIC,SEAL}.json (lean block, 90 cases), D/PAIRED_ANALYSIS_025.json,
D/SECOND_IMPLEMENTATION_025.json, D/API_CHECK_025.json, D/TEST_SUITE_025.json, results/diag-025/HN_RECOUNT_025.json,
experiments/COMMIT_ORDER_025.json, results/RESEARCH_LEDGER.jsonl, results/study-024/PAIRED_ANALYSIS_024.json (frozen controls).
Gated: GBC a-e, GBC_lemma, GAS_frozen_control, GS_a11, GS_ref11, GAPI11, G_recount, G10, G13, GTI, G_PROC (c, d), G_RT.
Dropped under A2 (listed in the output, not gated): G12, G_HB, G_PROC a/b. Missing input => FAIL INCOMPLETE_INPUT.
  PYTHONPATH=. python scripts/make_gates_025.py [--study-dir D] [--check]"""
from __future__ import annotations
import argparse,inspect,json,sys
from datetime import datetime
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common_025 import STUDY_DIR,PLAN,FREEZE,load,dumps,write_new,check,sha,check_freeze,TAU6
import scripts.make_gates_024 as G24
from scripts.make_gates_018 import cp_upper
from scripts.make_gates_015 import opt
import experiments.brute_study_014 as S14
import experiments.brute_study_019 as S19

PLAN_A1=ROOT/'experiments/BRUTE_PLAN_025_A1.json';PLAN_A2=ROOT/'experiments/BRUTE_PLAN_025_A2.json'
STEPS=88;PREFIX=28;EXPECTED={'main':60,'stress':30,'noisy':40,'eps2':20};CAP=1800
CTRL_024={'RGL5':[0.37822,0.461742],'RGL4':[0.371591,0.452654]}
HOST_BANNED=G24.HOST_BANNED


def arms(c):return ('RG4','RGB6','RGL4','RGL5')+(('RGNB4',) if c['eps']==0.02 else ())+('RGN4_or',)
def noisy_arms(c):return arms(c)[1:]
G24.arms=arms;G24.noisy_arms=noisy_arms;G24.all_arms=lambda c:('SP8',)+arms(c)   # the 024 recount helpers, with the 025 arm set
def ck(c):return f"{c['block']}/{c['family']}/{c['seed']}/{c['eps']}"


def b6_check(c):
    b=c['b6'];bad=[];T=b.get('T') or []
    if T!=c['noisy']['RGB6']['m']:bad.append('T_is_RGB6_m')
    if len(T)!=STEPS:return bad+['lengths']
    for i in range(STEPS):
        if i and T[i]<T[i-1]:bad.append(('T_monotone',i+1))
        if T[i]>b['T0'][i]:bad.append(('T_le_T0',i+1))
        if not b['active'][i] and T[i]!=b['T0'][i]:bad.append(('inactive_T_is_T0',i+1))
    for j in ('1','2'):
        act=[int(j) in a for a in b['active']];K=b['K'][j]
        if any(a and not x for a,x in zip(act,act[1:])):bad.append(('sticky',j))
    return bad


def api11_probe():
    try:
        from brute.api import certify11 as C11
        from brute.api.certify10 import certify10
        from brute.api.certify9 import certify9
        init,acts,obs=(0,1),[0,1,0,1,1,0,0,1,1,1,0],[(0,1),(1,None),(0,1),(1,0),(None,1),(0,1),(1,0),(0,0),(1,1),(0,1),(1,None)]
        K=('supports','unknown','certificates','status','m','steps')
        d=C11.certify11(init,acts,obs);s=C11.certify11(init,acts,obs,method='stitched');l=C11.certify11(init,acts,obs,method='lr');a=C11.certify11(init,acts,obs,method='anytime')
        s10=certify10(init,acts,obs);r9=certify9(init,acts,obs);a9=certify9(init,acts,obs,method='anytime')
        return {'api':d.get('api'),'methods':list(C11.METHODS),'default_method':inspect.signature(C11.certify11).parameters['method'].default,
                'default_answer_method':d.get('method'),'stitched_equals_certify10':all(s.get(k)==s10.get(k) for k in K),
                'lr_equals_certify9':all(l.get(k)==r9.get(k) for k in K),'anytime_equals_certify9_anytime':all(a.get(k)==a9.get(k) for k in K),'error':None}
    except Exception as e:return {'error':f'{type(e).__name__}: {e}'}


def ledger_times(upto='run_start_025'):
    L=[json.loads(x) for x in (ROOT/'results/RESEARCH_LEDGER.jsonl').read_text().splitlines() if x.strip()]
    i0=next((i for i,e in enumerate(L) if e.get('event')=='build_authorization_025'),None);out=[]
    for e in L[i0:] if i0 is not None else []:
        try:out.append((e['event'],datetime.fromisoformat(str(e.get('note',''))[:25])))
        except ValueError:out.append((e['event'],None))
        if e['event']==upto:break
    return out


def build(study=STUDY_DIR):
    study=Path(study);G={};why_in=[]
    seal=opt(study/'transfer/SEAL.json');sci=opt(study/'transfer/SCIENTIFIC.json');res=opt(study/'transfer/RESULTS.json')
    P=opt(study/'PAIRED_ANALYSIS_025.json') or {};ref=opt(study/'SECOND_IMPLEMENTATION_025.json');apick=opt(study/'API_CHECK_025.json')
    ts=opt(study/'TEST_SUITE_025.json');hn=opt(ROOT/'results/diag-025/HN_RECOUNT_025.json');order=opt(ROOT/'experiments/COMMIT_ORDER_025.json')
    allc=(sci or {}).get('cases',[]);main=[c for c in allc if c['block']=='main'];stress=[c for c in allc if c['block']=='stress']
    noisy=[c for c in main if c['eps'] in (0.01,0.02)];e2=[c for c in main if c['eps']==0.02]
    complete=bool(seal) and seal.get('complete') is True and sha(study/'transfer/SCIENTIFIC.json')==seal.get('scientific_sha256') and len(main)==EXPECTED['main'] and len(stress)==EXPECTED['stress']
    wb=None if complete else 'INCOMPLETE_INPUT (transfer missing, partial or not matching its seal)'
    def gate(name,ok,obs,why=None):G[name]={'pass':bool(ok) and why is None,'observed':obs,**({'reason':why} if why else {})}
    def pv(k):x=P.get(k) or {};return x.get('mean'),x.get('ci95')
    # exact recount
    rec=[];F={'main':0,'noisy':0,'stress':0};Fc={}
    for c in allc:
        act=G24.actual(c)
        for arm,recd,recomp,flags in G24.recount(c,act):
            if recd!=recomp or not flags:rec.append((ck(c),arm,recd,recomp,flags))
            if arm=='RGB6':
                F['main' if c['block']=='main' else 'stress']+=recomp;F['noisy']+=recomp if c in noisy else 0
            Fc.setdefault(arm,{}).setdefault(c['block']+('_eps%s'%c['eps']),0);Fc[arm][c['block']+('_eps%s'%c['eps'])]+=recomp
    # GBC
    k_cases=sum(1 for c in noisy if c['summary']['false']['RGB6']>0)
    a_ok=complete and F['noisy']==0 and len(noisy)==EXPECTED['noisy']
    b_ok=complete and F['stress']==0
    m,ci=pv('dC_late_RGB6_RGL4_eps2');c_ok=complete and m is not None and m>=0.04 and ci[0]>0
    md,cid=pv('dC_late_RGB6_RGNB4_eps2');d_ok=complete and cid is not None and cid[0]>-0.06
    extra=[];extra_false=0
    for c in allc:
        act=G24.actual(c);B=c['certifiers']['RGB6']['trace'];L4=c['certifiers']['RGL4']['trace']
        for i,(rb,rl) in enumerate(zip(B,L4)):
            if rb['step']>PREFIX:break
            for b in (0,1):
                if rb['certificate'][b] is not None and rl['certificate'][b] is None:extra.append((ck(c),rb['step'],b));extra_false+=rb['certificate'][b]!=act[i][b]
    e_ok=complete and extra_false==0
    gate('GBC_headline',a_ok and b_ok and c_ok and d_ok and e_ok,{'a':{'pass':a_ok,'false_noisy':F['noisy'],'noisy_cases':len(noisy),'cases_with_false':k_cases,
         'cp95_upper_reported_not_gated':cp_upper(k_cases,len(noisy)) if noisy else None},'b':{'pass':b_ok,'false_stress':F['stress'],'stress_cases':len(stress),'strict':True},
         'c':{'pass':c_ok,'mean':m,'ci95':ci},'d':{'pass':d_ok,'mean':md,'ci95':cid},'e':{'pass':e_ok,'extra_certificates_steps_1_28':len(extra),'extra_false':extra_false,'first':extra[:10]},
         'false_by_arm_block_eps':Fc},why=wb)
    # GBC_lemma
    ordr=(order or {}).get('order') or [];pos={e:i for i,e in enumerate(ordr)}
    bf=lambda x,y:x in pos and y in pos and pos[x]<pos[y]
    lem={'commit_order_file':order is not None,'authorization_before_lemma':bf('build_authorization_025','betting_lemma_025'),
         'lemma_before_rgb6_code':bf('betting_lemma_025','rgb6_code_025'),'reference_before_rgb6_code':bf('reference_025','rgb6_code_025'),
         'hn_recount_passed':bool(hn) and hn.get('passed') is True}
    gate('GBC_lemma',all(lem.values()),lem)
    # GAS
    gas={a:{'ci95':pv(f'C_late_{a}_eps2')[1],'ctrl_024':CTRL_024[a]} for a in CTRL_024}
    for a,v in gas.items():v['intersects']=v['ci95'] is not None and v['ci95'][0]<=v['ctrl_024'][1] and v['ci95'][1]>=v['ctrl_024'][0]
    gate('GAS_frozen_control',all(v['intersects'] for v in gas.values()),gas,why=wb)
    gate('GS_a11',bool(apick) and apick.get('passed') is True and apick.get('cases_checked')==4 and apick.get('results_sha256')==sha(study/'transfer/RESULTS.json'),
         None if not apick else {k:v for k,v in apick.items() if k!='cases'},why=wb or (None if apick else 'INCOMPLETE_INPUT (API_CHECK_025 missing)'))
    rs=(ref or {});mt=rs.get('mutation_test') or {}
    gate('GS_ref11',bool(ref) and rs.get('passed') is True and rs.get('cases_audited')==len(allc)==90 and rs.get('gated_cases_audited')==90 and rs.get('mismatching_cases')==0
         and mt.get('detected_injected')==mt.get('injected')==20 and rs.get('results_sha256')==sha(study/'transfer/RESULTS.json'),
         None if not ref else {**{k:rs.get(k) for k in ('cases_audited','gated_cases_audited','mismatching_cases','gated_mismatching_cases','results_sha256','passed')},
                               'mutation':{k:mt.get(k) for k in ('injected','distinct_cases','detected_injected','passed')},'first_mismatches':rs.get('mismatches',[])[:5]},
         why=wb or (None if ref else 'INCOMPLETE_INPUT (SECOND_IMPLEMENTATION_025 missing)'))
    # GAPI11
    p=api11_probe();old={}
    for rel in ['brute/api/certify.py']+[f'brute/api/certify{n}.py' for n in range(2,11)]:
        fz=next((f for f in sorted(ROOT.glob('experiments/BRUTE_SOURCE_FREEZE_0*.json')) if rel in (load(f).get('sha256_files') or {})),None)
        old[rel]=fz is not None and load(fz)['sha256_files'][rel]==sha(ROOT/rel)
    src=(ROOT/'brute/api/certify11.py').read_text()+(ROOT/'brute/bettingregion.py').read_text()
    api={'api_certify11':p.get('api')=='brute.certify/11','methods':p.get('methods')==['betting','stitched','lr','anytime'],
         'default_betting':p.get('default_method')=='betting' and p.get('default_answer_method')=='betting','stitched_equals_certify10':p.get('stitched_equals_certify10') is True,
         'lr_equals_certify9':p.get('lr_equals_certify9') is True,'anytime_equals_certify9_anytime':p.get('anytime_equals_certify9_anytime') is True,
         'certify_to_certify10_unchanged':all(old.values()),'host_agnostic_source_scan':not any(x in src for x in HOST_BANNED)}
    gate('GAPI11',all(api.values()),{'clauses':api,'probe':p,'older':old})
    # G_recount
    b6bad={ck(c):b6_check(c) for c in allc};b6bad={k:v for k,v in b6bad.items() if v}
    cc={ck(c):G24.cert_counts(c) for c in allc};cc={k:v for k,v in cc.items() if v}
    gate('G_recount',not rec and not b6bad and not cc,{'recount_mismatch':rec[:20],'b6_rule':dict(list(b6bad.items())[:10]),'counts':dict(list(cc.items())[:10]),'cases':len(allc)},why=wb)
    # G10
    unk=[0,0]
    for c in allc:
        for a in noisy_arms(c):
            for row in G24.sup(c,a)['unknown']:
                for x in row:unk[0]+=1;unk[1]+=x>0
    tl=all(len(c['certifiers'][a]['trace'])==STEPS for c in allc for a in arms(c))
    npre=sum('prefix28_rgb6' in c for c in e2)
    gate('G10',complete and tl and unk[1]==0 and npre==EXPECTED['eps2'],{'cases':len(allc),'queries':unk[0],'unknown_gt0':unk[1],'traces_88':tl,'prefix28_rgb6_records':npre},why=wb)
    # G13
    try:fz=check_freeze();fe=None
    except Exception as e:fz=None;fe=f'{type(e).__name__}: {e}'
    rg_bad=[ck(c) for c in allc if S14.rg_arm(S14.sp8_steps(c),{'4':c['bounded']['4']},4,c['burn_in'])!=c['certifiers']['RG4']]
    rgn_bad=[(ck(c),a) for c in allc for a in noisy_arms(c) if S19.cert_arm([(s_[0],s_[1]) for s_ in S14.sp8_steps(c)],[s_[5] for s_ in S14.sp8_steps(c)],G24.sup(c,a)['support'],c['noisy'][a]['m'],c['burn_in'],2)!=c['certifiers'][a]]
    g13={'freeze_chain_holds':fz is not None,'a2_in_freeze':bool(fz) and fz.get('plan_a2_sha256')==sha(PLAN_A2),
         'seal_of_plan_and_freeze':bool(seal) and seal.get('plan_sha256')==sha(PLAN) and seal.get('freeze_sha256')==sha(FREEZE),
         'tau6':bool(allc) and all(c.get('tau6')==TAU6 for c in allc),'rg4_reproduces':not rg_bad,'cert_rule_reproduces':not rgn_bad}
    gate('G13',all(g13.values()),{'clauses':g13,'freeze_error':fe,'rg_bad':rg_bad[:10],'rgn_bad':rgn_bad[:10]},why=wb)
    # GTI (lean)
    mods=(ts or {}).get('per_module') or {}
    gate('GTI',bool(mods) and ts.get('passed') is True and all(v.get('returncode')==0 for v in mods.values()),
         None if not ts else {k:{'returncode':v.get('returncode'),'tests':v.get('tests')} for k,v in mods.items()},why=None if ts else 'INCOMPLETE_INPUT (TEST_SUITE_025 missing)')
    # G_PROC (c, d)
    lt=ledger_times();times=[t for _,t in lt]
    proc={'commit_order':lem['lemma_before_rgb6_code'] and lem['reference_before_rgb6_code'],'ledger_times_parse':bool(lt) and all(t is not None for t in times),
          'ledger_times_non_decreasing':all(a<=b for a,b in zip(times,times[1:]) if a and b),'run_start_ledgered':any(e=='run_start_025' for e,_ in lt)}
    gate('G_PROC',all(proc.values()),{'clauses':proc,'events':[e for e,_ in lt]})
    el=(res or {}).get('total_elapsed_informational')
    gate('G_RT',complete and el is not None and el<=CAP,{'elapsed_s':el,'cap_s':CAP,'complete':(seal or {}).get('complete')},why=wb)
    rep={'R_coverage':{k:pv(k) for k in sorted(P) if k.startswith(('C_late_','C_early28_','dC_late_','dC_early28_')) and ('eps2' in k or 'stress' in k or 'noisy' in k)},
         'R_ratio':{k:v for k,v in P.items() if k.startswith('ratio_')},
         'R_activation':{'cases_any_level_active':sum(any(c['b6']['active'][i] for i in range(STEPS)) for c in allc),'K_max':{j:max((max(c['b6']['K'][j]) for c in allc),default=None) for j in ('1','2')}},
         'R_stress_false_by_arm':{a:sum(c['summary']['false'][a] for c in stress) for a in ('RG4','RGB6','RGL4','RGL5','RGN4_or')},
         'R_case_wall':None if not res else round(sum(c['case_wall_informational'] for c in res['cases'])/max(1,len(res['cases'])),1)}
    return {'schema':'brute.gates.v22_0','study':'BRUTE-0220-BETTING-CS-025','process':'lean (BRUTE_PLAN_025_A2)','gates':G,
            'all_gated_pass':all(g['pass'] for g in G.values()),'failed':[k for k,g in G.items() if not g['pass']],
            'dropped_under_A2':['G12','G_HB','G_PROC a','G_PROC b'],'reports':rep}


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--study-dir',default=str(STUDY_DIR));ap.add_argument('--check',action='store_true');a=ap.parse_args()
    obj=build(Path(a.study_dir));out=Path(a.study_dir)/'GATES_025.json'
    if a.check:check(out.read_bytes()==dumps(obj),'GATES_025.json does not reproduce');print('GATES_025 reproduces')
    else:write_new(out,obj);print(json.dumps({k:v['pass'] for k,v in obj['gates'].items()}),obj['failed'])
