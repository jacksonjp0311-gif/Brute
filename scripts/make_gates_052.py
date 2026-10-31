"""Gates for study-052 (BRUTE_PLAN_052 criteria; pre-run deviation #177 definitions), LEAN process. Committed in the source freeze
before run_start_052; nothing is tuned after results are seen. New file; built from scripts/make_gates_051.py (frozen).
Inputs (D = results/study-052): D/main/{RESULTS,SCIENTIFIC,SEAL}.json, D/main/RECOUNT_052.json, D/main/REFERENCE_052.json,
D/API_CHECKS_052.json, D/TEST_SUITE_052.json, results/diag-052/SEEDCHECK_052.json, experiments/COMMIT_ORDER_052.json,
results/RESEARCH_LEDGER.jsonl. Missing or partial input => every data gate FAIL INCOMPLETE_INPUT. Records are accepted only if
sha256(RESULTS) equals the seal and no_time(RESULTS) equals SCIENTIFIC. Labels: recounted if G_recount passes, else the study's.
  GDET52: canon16n(API16N) == canon16n(API16N_b) on 24/24 noise12 cases AND wall_guard 0 on every record;
  GFID52: API_CHECKS_052 fidelity exact on every main record (#177 widening of the plan's 36 + 6: 48 noise12 + N12BAR
     noise12_bar + 6 API16N_c + 6 API16E = 72 with no cut), bound to the sealed RESULTS sha;
  GN12_sound52: WRONG 0 on every noise12 (both passes) and noise12_bar record (labels against the clean truth) AND
     API16N ID+IDF >= 8/24 at eps 0.05 (non-vacuity);
  GCOMPAT16N52: 6/6 compat seeds equal under the plan 052 rule (RECOUNT_052 compat: same label; ID same machine from start
     state 0; IDF future_match on both and same machine from the current state s1). Introduced after 051's GCOMPAT16S / G10 IDF
     failures and applied only to 052 data, never retroactively;
  GHOST52: API_CHECKS_052 ghost PASS52, bound to certify16n.py's sha in the 050 freeze and the 052 freeze;
  GQB26: max chunk wall <= 30 s and max case wall <= 600 s on every record;
  GS_ref: REFERENCE_052 on block main: sha bound, 0 mismatches, complete within 2400 s on 8 workers, 20/20 mutations;
  G_sound: 0 unsound words (study and recount), recount checked the same words, and 0 WRONG on the compat records (#177);
  G_recount;  GTI: SEEDCHECK_052 PASS and its sha frozen in BRUTE_SOURCE_FREEZE_052;
  GTEST: the gated test modules of TEST_SUITE_052 pass;
  G_PROC: preregistration, build_authorization, seedcheck, prefreeze_smoke, source_freeze, run_start, run_end, recount, reference,
     api_checks, tests (all _052) as a subsequence, parseable non-decreasing note times, commit-order file, main sealed;
  G_RT: main elapsed <= 3600 s.
  Secondary (reported): GN12_rate52, GN12_pool (050 + 051 + 052 eps-0.05 API16N records, read from GATES_050 / GATES_051),
  GCOST52.
  PYTHONPATH=. python scripts/make_gates_052.py [--study-dir D] [--check]"""
from __future__ import annotations
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common import load,dumps,write_new,check,sha
from experiments.brute_common_026 import wilson
from scripts.make_gates_034 import opt
from scripts.make_gates_043 import subseq

STUDY_DIR=ROOT/'results/study-052';N2=('API16N','API16N_b');CP=('API16N_c','API16E');ALL=('API16N','API16N_b','API16N_bar','API16N_c','API16E')
LABELS=('ID','IDF','AMB','WRONG','IDU');CAP_RT=3600;QB=30.0;CASE_B=600.0;MIN_ID=8
PROC_ORDER=tuple(e+'_052' for e in ('preregistration','build_authorization','seedcheck','prefreeze_smoke','source_freeze','run_start','run_end',
                                    'recount','reference','api_checks','tests'))
PRIOR=(('050','results/study-050/GATES_050.json','GN12_sound'),('051','results/study-051/GATES_051.json','GN12_sound51'))


def ckey(c):return f"{c['block']}/{c['key']}/{c['seed']}"


def ledger():
    from datetime import datetime
    L=[json.loads(x) for x in (ROOT/'results/RESEARCH_LEDGER.jsonl').read_text().splitlines() if x.strip()]
    i0=next((i for i,e in enumerate(L) if e.get('event')=='preregistration_052'),None);out=[]
    for e in (L[i0:] if i0 is not None else []):
        try:t=datetime.fromisoformat(str(e.get('note',''))[:25])
        except ValueError:t=None
        out.append((e['event'],t))
        if e['event']==PROC_ORDER[-1]:break
    return out


def build(study=STUDY_DIR,expect=None):
    """expect: case counts {noise12, noise12_bar, compat}; the plan's 24 / N12BAR / 6 unless a pre-freeze synthetic check patches it."""
    from brute.evaluation import no_time
    from experiments.brute_study_052 import canon16n,N12BAR
    study=Path(study);D=study/'main';Gt={};sec={}
    seal=opt(D/'SEAL.json');sci=opt(D/'SCIENTIFIC.json');res=opt(D/'RESULTS.json');rc=opt(D/'RECOUNT_052.json')
    ref=opt(D/'REFERENCE_052.json');ts=opt(study/'TEST_SUITE_052.json');order=opt(ROOT/'experiments/COMMIT_ORDER_052.json')
    api=opt(study/'API_CHECKS_052.json');fz=opt(ROOT/'experiments/BRUTE_SOURCE_FREEZE_052.json');fz50=opt(ROOT/'experiments/BRUTE_SOURCE_FREEZE_050.json')
    sc=opt(ROOT/'results/diag-052/SEEDCHECK_052.json')
    rsha=sha(D/'RESULTS.json') if (D/'RESULTS.json').exists() else None
    sealed=(bool(seal) and res is not None and sci is not None and rsha==seal.get('results_sha256')
            and sha(D/'SCIENTIFIC.json')==seal.get('scientific_sha256') and no_time(res)==sci)
    E=dict(expect or {'noise12':24,'noise12_bar':(res or {}).get('n_noise12_bar',N12BAR),'compat':6});nfid=2*E['noise12']+E['noise12_bar']+2*E['compat']
    allc=[c for c in (res or {}).get('cases',[]) if c['block']=='main'] if sealed else []
    G=lambda k:sorted([c for c in allc if c['key']==k],key=lambda c:c['seed'])
    n12=G('noise12');nb=G('noise12_bar');cp=G('compat')
    arms_ok=(all(list(c['arms'])==list(N2) for c in n12) and all(list(c['arms'])==['API16N_bar'] for c in nb)
             and all(list(c['arms'])==list(CP) for c in cp))
    complete=(sealed and seal.get('complete') is True and len(n12)==E['noise12'] and len(nb)==E['noise12_bar'] and len(cp)==E['compat']
              and len(allc)==E['noise12']+E['noise12_bar']+E['compat'] and arms_ok)
    wb=None if complete else 'INCOMPLETE_INPUT (main missing, partial, missing arms or not matching its seal)'
    def gate(name,ok,obs,why=None):Gt[name]={'pass':bool(ok) and why is None,'observed':obs,**({'reason':why} if why else {})}
    pc=(rc or {}).get('per_case') or {}
    rc_bound=bool(rc) and rc.get('results_sha256')==rsha and rc.get('cases')==len((res or {}).get('cases',[]))
    rc_ok=rc_bound and rc.get('PASS') is True and rc.get('mismatching_cases')==0
    lab=(lambda c,a:((pc.get(ckey(c)) or {}).get(a) or {}).get('label')) if rc_ok else (lambda c,a:c['arms'][a]['label'])
    lsrc='recount' if rc_ok else 'study labels (G_recount did not pass)'
    dd=lambda c,a:a in c['arms'] and lab(c,a) in ('ID','IDF')
    ci=lambda x,n:wilson(x,n) if n else None
    every=allc
    # GDET52
    det=[[c['seed'],canon16n(c['arms']['API16N'])==canon16n(c['arms']['API16N_b']),c['arms']['API16N']['label'],c['arms']['API16N_b']['label']]
         for c in n12 if 'API16N_b' in c['arms']]
    guards=[[ckey(c),an,ar.get('guard_events')] for c in every for an,ar in c['arms'].items() if ar.get('wall_guard')]
    nd=sum(x[1] for x in det)
    gate('GDET52',complete and len(det)==E['noise12'] and nd==E['noise12'] and not guards,{'identical':nd,'of':len(det),'ci95':ci(nd,len(det)),
         'wall_guard_fired':guards,'records_checked_for_guard':sum(len(c['arms']) for c in every),'per_case':det,'columns':['seed','canon16n_equal','pass1','pass2'],
         'rule':'canon16n identical on 24/24 noise12 cases; wall_guard 0 on every record'},why=wb)
    # GFID52
    fi=(api or {}).get('fidelity') or {}
    fi_ok=bool(fi) and fi.get('study_results_sha256')==rsha and fi.get('PASS') is True and fi.get('exact')==fi.get('cases')==nfid
    gate('GFID52',complete and fi_ok,{'exact':fi.get('exact'),'of':fi.get('cases'),'expected':nfid,'ci95':ci(fi.get('exact') or 0,fi.get('cases') or 0),
         'per_key':fi.get('per_key'),'exact_per_arm':fi.get('exact_per_arm'),'bound':bool(fi) and fi.get('study_results_sha256')==rsha,
         'failures':{k:v for k,v in (fi.get('per_case') or {}).items() if not v['exact']}},
         why=wb or (None if fi else 'INCOMPLETE_INPUT (API_CHECKS_052 fidelity missing)'))
    wrong=[[ckey(c),a] for c in every for a in c['arms'] if lab(c,a)=='WRONG' or c['arms'][a]['label']=='WRONG']
    # GN12_sound52
    wn=[x for x in wrong if x[0].startswith(('main/noise12/','main/noise12_bar/'))];xn=sum(dd(c,'API16N') for c in n12);xb=sum(dd(c,'API16N_bar') for c in nb)
    pk=(ref or {}).get('per_key') or {}
    gate('GN12_sound52',complete and not wn and xn>=MIN_ID,{'WRONG':wn,'records':sum(len(c['arms']) for c in n12+nb),
         'API16N_ID_IDF':xn,'of':len(n12),'ci95':ci(xn,len(n12)),'non_vacuous':xn>=MIN_ID,'min_ID_IDF':MIN_ID,
         'API16N_bar_ID_IDF':xb,'bar_of':len(nb),'bar_ci95':ci(xb,len(nb)),
         'majority_errors':(rc or {}).get('majority_errors'),'reference_noise12':pk.get('noise12'),'reference_noise12_bar':pk.get('noise12_bar'),
         'per_case':[[c['seed'],lab(c,'API16N'),c['arms']['API16N']['stop'],c['arms']['API16N'].get('reads_total'),c['arms']['API16N'].get('majority_errors'),
                      lab(c,'API16N_b') if 'API16N_b' in c['arms'] else None] for c in n12],
         'per_case_bar':[[c['seed'],lab(c,'API16N_bar'),c['arms']['API16N_bar']['stop'],c['arms']['API16N_bar'].get('reads_total'),c['arms']['API16N_bar'].get('majority_errors')] for c in nb],
         'model_bound':f'P(any WRONG over {sum(len(c["arms"]) for c in n12+nb)} records) <= that count x 0.001 (Exact, conditional on the iid model)','label_source':lsrc},why=wb)
    # GCOMPAT16N52
    cq=(rc or {}).get('compat') or {};ce=[[c['seed'],bool((cq.get(ckey(c)) or {}).get('equal')),(cq.get(ckey(c)) or {}).get('label'),(cq.get(ckey(c)) or {}).get('control_label'),
        (cq.get(ckey(c)) or {}).get('machine_equal'),(cq.get(ckey(c)) or {}).get('canon16e_equal')] for c in cp];nce=sum(x[1] for x in ce)
    gate('GCOMPAT16N52',complete and rc_ok and nce==len(ce)==E['compat'],{'equal':nce,'of':len(ce),'ci95':ci(nce,len(ce)),'per_case':ce,
         'columns':['seed','equal','label_16n_eps0','label_16e','machine_equal','canon16e_equal (H4, informational)'],
         'canon16e_equal':sum(bool(x[5]) for x in ce),
         'rule':('plan 052: same label; ID: same machine from start state 0; IDF: future_match on both and the same machine from the current state s1. '
                 'Introduced after 051 GCOMPAT16S / G10 IDF failures; applied only to 052 data, not retroactively'),'source':'RECOUNT_052'},
         why=wb or (None if rc_ok else 'G_recount did not pass'))
    # GHOST52
    cn=sha(ROOT/'brute/api/certify16n.py');f52=(fz or {}).get('sha256_files',{}).get('brute/api/certify16n.py');f50=(fz50 or {}).get('sha256_files',{}).get('brute/api/certify16n.py')
    abound=bool(api) and api.get('certify16n_sha256')==cn==f50 and f52 in (None,cn)
    ag=(api or {}).get('ghost') or {}
    gate('GHOST52',abound and ag.get('PASS52') is True,None if not api else {'bound_to_freeze_050':abound,'in_freeze_052':f52==cn,'frozen_api_unchanged':ag.get('frozen_api_unchanged'),
         'closures_unchanged':ag.get('closures_unchanged'),'socket_attempts':ag.get('socket_attempts'),'no_network_run':ag.get('no_network_run')},
         why=None if api else 'INCOMPLETE_INPUT (API_CHECKS_052 missing)')
    # GQB26 + cost
    mx={};mxc={};over=[];over_c=[];cost={}
    for c in every:
        for a,ar in c['arms'].items():
            p=f"{a}/{c['key']}"
            cw=[t for r in ar['rounds'] for x in r.get('chunk_walls_informational',[]) for t in x];cs=ar.get('case_wall_informational')
            if cw:mx[p]=max(mx.get(p,0),max(cw))
            if cs is not None:mxc[p]=max(mxc.get(p,0),cs)
            over+=[[f'{ckey(c)}/{a}',round(t,3)] for t in cw if t>QB]
            if cs is None or cs>CASE_B:over_c.append([f'{ckey(c)}/{a}',cs])
            x=cost.setdefault(p,{'records':0,'arm_wall_s':0.0,'calls':0,'chunks':0,'capped_calls':0,'conflicts':0,'budget_spent':0,'reads':0})
            x['records']+=1;x['arm_wall_s']+=ar.get('arm_wall_informational') or 0.0;x['conflicts']+=ar.get('conflicts_spent') or 0
            x['calls']+=sum(len(r.get('call_conflicts',[])) for r in ar['rounds']);x['chunks']+=ar.get('chunks_total') or 0
            x['capped_calls']+=sum(bool(v) for r in ar['rounds'] for v in r.get('call_capped',[]))
            x['budget_spent']+=(ar.get('conflicts_spent') or 0)>=ar['budget_conflicts'];x['reads']+=ar.get('reads_total') or 0
    for x in cost.values():x['arm_wall_s']=round(x['arm_wall_s'],1)
    gate('GQB26',complete and bool(mx) and not over and not over_c,{'max_chunk_wall_s':{k:round(v,3) for k,v in sorted(mx.items())},
         'max_case_wall_s':{k:round(v,3) for k,v in sorted(mxc.items())},'chunk_bound_s':QB,'case_bound_s':CASE_B,'over_chunk':over,'over_case':over_c},why=wb)
    # GS_ref
    mt=(ref or {}).get('mutation_test') or {};rb=bool(ref) and ref.get('study_results_sha256')==rsha and ref.get('block')=='main'
    robs=None if not ref else {k:ref.get(k) for k in ('block','scope','records','decided','audited','not_audited','complete','per_arm','per_key','not_reached',
                               'k_spent_as_amb','verdicts_checked','mismatch_count','vacuous','PASS','elapsed_informational')}|{'mutations':mt.get('detected'),'of':mt.get('mutations')}
    gate('GS_ref',rb and ref.get('mismatch_count')==0 and ref.get('complete') is True and (ref.get('scope') or {}).get('budget_12_s')==2400.0
         and mt.get('detected')==mt.get('mutations')==20 and ref.get('PASS') is True,robs,why=wb or (None if ref else 'INCOMPLETE_INPUT (REFERENCE_052 missing)'))
    # G_sound / G_recount
    wc=[x for x in wrong if x[0].startswith('main/compat/')]
    snd={'words_checked':sum(ar.get('words_checked',0) for c in every for ar in c['arms'].values()),
         'words_unsound':sum(ar.get('words_unsound',0) for c in every for ar in c['arms'].values()),
         'recount_bound':rc_bound,'recount_words_checked':(rc or {}).get('words_checked'),'recount_words_unsound':(rc or {}).get('words_unsound'),
         'recount_truth_inconsistent':(rc or {}).get('truth_inconsistent'),'compat_WRONG':wc}
    gate('G_sound',complete and rc_bound and snd['words_unsound']==0 and snd['recount_words_unsound']==0 and snd['recount_words_checked']==snd['words_checked'] and not wc,
         snd,why=wb or (None if rc_bound else 'INCOMPLETE_INPUT (RECOUNT_052 missing or unbound)'))
    gate('G_recount',complete and rc_ok,None if not rc else {k:rc.get(k) for k in ('cases','recounted','labels','compat_equal','majority_errors','misfires',
         'amb_rule_applied','words_checked','words_unsound','truth_inconsistent','mismatching_cases','mismatches','PASS')},
         why=wb or (None if rc else 'INCOMPLETE_INPUT (RECOUNT_052 missing)'))
    # GTI / GTEST
    sc_frozen=bool(sc) and (fz or {}).get('sha256_files',{}).get('results/diag-052/SEEDCHECK_052.json')==sha(ROOT/'results/diag-052/SEEDCHECK_052.json')
    gate('GTI',bool(sc) and sc.get('PASS') is True and sc_frozen,None if not sc else {'seedcheck_pass':sc.get('PASS'),'frozen_in_052':sc_frozen,
         'total_cases':sc.get('total_cases'),'prior_range_count':sc.get('prior_range_count'),'all_tokens_allowed':sc.get('all_tokens_allowed')},
         why=None if sc else 'INCOMPLETE_INPUT (SEEDCHECK_052 missing)')
    mods=(ts or {}).get('per_module') or {};gm=(ts or {}).get('gated_modules') or []
    gate('GTEST',bool(gm) and ts.get('passed') is True and all(mods[m].get('returncode')==0 for m in gm),
         None if not ts else {'gated':{m:{'returncode':mods[m].get('returncode'),'tests':mods[m].get('tests')} for m in gm},
                              'reported':{m:{'returncode':v.get('returncode'),'tests':v.get('tests')} for m,v in mods.items() if m not in gm}},
         why=None if ts else 'INCOMPLETE_INPUT (TEST_SUITE_052 missing)')
    lt=ledger();ev=[e for e,_ in lt];times=[t for _,t in lt]
    proc={'order':subseq(ev,PROC_ORDER),'ledger_times_parse':bool(lt) and all(t is not None for t in times),
          'ledger_times_non_decreasing':all(a<=b for a,b in zip(times,times[1:]) if a and b),'commit_order_file':order is not None,'main_sealed':bool(sealed)}
    gate('G_PROC',all(proc.values()),{'clauses':proc,'events':ev,'required_order':list(PROC_ORDER)})
    el=(res or {}).get('total_elapsed_informational')
    gate('G_RT',complete and el is not None and el<=CAP_RT,{'elapsed_s':el,'cap_s':CAP_RT,'cases':len(allc),'n_noise12_bar':E['noise12_bar']},why=wb)
    # secondary
    sec['GCOST52']={'pass':None,'observed':dict(sorted(cost.items())),'rule':'reported: wall, calls, chunks, capped calls, conflicts, budget-spent records, reads per arm/key'}
    def rd(cs,a):
        rp=[c['arms'][a].get('reads_total') or 0 for c in cs];ob=[len(c['arms'][a].get('reads_per_obs') or []) for c in cs]
        return {'reads_total':sum(rp),'observations':sum(ob),'reads_per_observation':round(sum(rp)/sum(ob),2) if sum(ob) else None,
                'k_range':[min((min(c['arms'][a]['reads_per_obs']) for c in cs if c['arms'][a].get('reads_per_obs')),default=None),max((c['arms'][a].get('reads_max') or 0 for c in cs),default=None)]}
    sec['GN12_rate52']={'pass':None,'observed':{'eps_0.05':{'ID_IDF':xn,'of':len(n12),'ci95':ci(xn,len(n12)),**(rd(n12,'API16N') if n12 else {})},
                        'eps_0.10':{'ID_IDF':xb,'of':len(nb),'ci95':ci(xb,len(nb)),**(rd(nb,'API16N_bar') if nb else {})}},'rule':'reported'}
    pool={};px=xn;pn=len(n12);pw=len([x for x in wn if x[0].startswith('main/noise12/')]);pr=sum(len(c['arms']) for c in n12)
    for v,f,k in PRIOR:
        g=((opt(ROOT/f) or {}).get('gates') or {}).get(k) or {};o=g.get('observed') or {}
        pool[v]={'API16N_ID_IDF':o.get('API16N_ID_IDF'),'of':o.get('of'),'WRONG':len(o.get('WRONG') or []),'records':o.get('records'),'gate_pass':g.get('pass')}
        px+=o.get('API16N_ID_IDF') or 0;pn+=o.get('of') or 0;pw+=len(o.get('WRONG') or []);pr+=o.get('records') or 0
    pool['052']={'API16N_ID_IDF':xn,'of':len(n12),'WRONG':len([x for x in wn if x[0].startswith('main/noise12/')]),'records':sum(len(c['arms']) for c in n12)}
    sec['GN12_pool']={'pass':None,'observed':{'by_study':pool,'pooled_ID_IDF':px,'pooled_of':pn,'pooled_ci95':ci(px,pn),'pooled_WRONG':pw,'pooled_records':pr,
                      'pooled_WRONG_ci95':ci(pw,pr)},'rule':'reported only: eps-0.05 API16N records of 050, 051, 052; different cases, not a paired comparison'}
    cnt=lambda k,a,L:sum(lab(c,a)==L for c in G(k) if a in c['arms']);nk=lambda k,a:sum(a in c['arms'] for c in G(k))
    fl={f'{a}/{k}':{L:{'x':cnt(k,a,L),'n':nk(k,a),'ci95':ci(cnt(k,a,L),nk(k,a))} for L in LABELS} for k,arms in (('noise12',N2),('noise12_bar',('API16N_bar',)),('compat',CP)) for a in arms}
    return {'schema':'brute.gates.v49_0','study':(res or {}).get('plan',{}).get('study'),'process':'lean','sealed_input_verified':sealed,'label_source':lsrc,
            'n_noise12_bar':E['noise12_bar'],'caps':(res or {}).get('caps'),'workers':(res or {}).get('workers'),
            'noise':(res or {}).get('noise'),'gates':Gt,'secondary':sec,
            'all_gated_pass':all(g['pass'] for g in Gt.values()),'failed':[k for k,g in Gt.items() if g['pass'] is False],'not_exercised':[],
            'claim':('certify/16n ID/IDF is exact conditional on every majority being correct (probability >= 1 - delta per record under iid flips with '
                     'eps <= eps_bar) and true size <= the declared N; IDF identifies the machine from the current state, not the start'),
            'reports':{'labels':fl} if allc else {}}


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--study-dir',default=str(STUDY_DIR));ap.add_argument('--check',action='store_true');a=ap.parse_args()
    obj=build(Path(a.study_dir));out=Path(a.study_dir)/'GATES_052.json'
    if a.check:check(out.read_bytes()==dumps(obj),'GATES_052.json does not reproduce');print('GATES_052 reproduces')
    else:write_new(out,obj);print(json.dumps({k:v['pass'] for k,v in obj['gates'].items()}),obj['failed'])
