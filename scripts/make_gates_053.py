"""Gates for study-053 (BRUTE_PLAN_053 criteria; pre-run deviation #179 definitions), LEAN process. Committed in the source freeze
before run_start_053; nothing is tuned after results are seen. New file; built from scripts/make_gates_052.py (frozen).
Inputs (D = results/study-053): D/main/{RESULTS,SCIENTIFIC,SEAL}.json, D/main/RECOUNT_053.json, D/main/REFERENCE_053.json,
D/API_CHECKS_053.json, D/TEST_SUITE_053.json, results/diag-053/SEEDCHECK_053.json, experiments/COMMIT_ORDER_053.json,
results/RESEARCH_LEDGER.jsonl. Missing or partial input => every data gate FAIL INCOMPLETE_INPUT. Records are accepted only if
sha256(RESULTS) equals the seal and no_time(RESULTS) equals SCIENTIFIC. Labels: recounted if G_recount passes, else the study's.
Part A = noise16 (API16N16 / API16N16_b, eps 0.05), noise16_bar (API16N16_bar, eps 0.10), compat16 (API16N16_c eps 0 / API16E,
bound 16); part B = scale20c (API16E20 / API16E20_b, certify/16e at bound 20, conflict-only stop, 900 s hard kill; non-blocking).
  GDET53: canon16n(API16N16) == canon16n(API16N16_b) on 12/12 noise16 cases AND wall_guard 0 on every part A record;
  GFID53: API_CHECKS_053 fidelity exact on every part A record (#179 widening of the plan's 18 + 6: 24 noise16 + N16BAR
     noise16_bar + 6 API16N16_c + 6 API16E = 42 with no cut), bound to the sealed RESULTS sha;
  GN16_sound53: WRONG 0 on every noise16 (both passes) and noise16_bar record AND API16N16 ID+IDF >= 4/12 (non-vacuity);
  GCOMPAT16N53: 6/6 compat16 seeds equal under the plan 052 rule (RECOUNT_053 compat);
  GHOST53: API_CHECKS_053 ghost PASS53, bound to certify16n.py's sha in the 050 freeze and the 053 freeze;
  GQB27: max chunk wall <= 30 s and max case wall <= 600 s on every part A record (part B maxima reported in GS20C_rate53);
  GS_ref: REFERENCE_053 on block main (part A, bound 16): sha bound, 0 mismatches, complete within 2400 s on 8 workers, 20/20;
  G_sound: 0 unsound words on every record of parts A and B (study and recount), recount checked the same words, 0 WRONG on compat16;
  G_recount;  GTI: SEEDCHECK_053 PASS and its sha frozen in BRUTE_SOURCE_FREEZE_053;
  GTEST: the gated test modules of TEST_SUITE_053 pass;
  G_PROC: preregistration, build_authorization, seedcheck, prefreeze_smoke, source_freeze, run_start, run_end, recount, reference,
     api_checks, tests (all _053) as a subsequence, parseable non-decreasing note times, commit-order file, main sealed;
  G_RT: main elapsed <= 3600 s.
  Non-blocking (scored, not in all_gated_pass): GS20C_det53: canon16e(API16E20) == canon16e(API16E20_b) on every scale20c case
  and 0 hard kills; GS20C_sound53: WRONG 0 on every scale20c record, decided (ID+IDF) count with a Wilson CI.
  certified_16n_N16: true iff every gated gate passes (the GS20C gates are excluded by the plan).
  Secondary (reported): GN16_rate53, GS20C_rate53 (conflicts/s, max chunk wall, max case wall), GCOST53.
  PYTHONPATH=. python scripts/make_gates_053.py [--study-dir D] [--check]"""
from __future__ import annotations
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common import load,dumps,write_new,check,sha
from experiments.brute_common_026 import wilson
from scripts.make_gates_034 import opt
from scripts.make_gates_043 import subseq

STUDY_DIR=ROOT/'results/study-053';N2=('API16N16','API16N16_b');BAR='API16N16_bar';CP=('API16N16_c','API16E');B2=('API16E20','API16E20_b')
A_KEYS=('noise16','noise16_bar','compat16');LABELS=('ID','IDF','AMB','WRONG','IDU');CAP_RT=3600;QB=30.0;CASE_B=600.0;MIN_ID=4
PROC_ORDER=tuple(e+'_053' for e in ('preregistration','build_authorization','seedcheck','prefreeze_smoke','source_freeze','run_start','run_end',
                                    'recount','reference','api_checks','tests'))


def ckey(c):return f"{c['block']}/{c['key']}/{c['seed']}"


def ledger():
    from datetime import datetime
    L=[json.loads(x) for x in (ROOT/'results/RESEARCH_LEDGER.jsonl').read_text().splitlines() if x.strip()]
    i0=next((i for i,e in enumerate(L) if e.get('event')=='preregistration_053'),None);out=[]
    for e in (L[i0:] if i0 is not None else []):
        try:t=datetime.fromisoformat(str(e.get('note',''))[:25])
        except ValueError:t=None
        out.append((e['event'],t))
        if e['event']==PROC_ORDER[-1]:break
    return out


def build(study=STUDY_DIR,expect=None):
    """expect: case counts {noise16, noise16_bar, compat16, scale20c}; the plan's 12 / N16BAR / 6 / N20C unless a pre-freeze synthetic check patches it."""
    from brute.evaluation import no_time
    from experiments.brute_study_053 import canon16n,canon16e,N16BAR,N20C
    study=Path(study);D=study/'main';Gt={};sec={}
    seal=opt(D/'SEAL.json');sci=opt(D/'SCIENTIFIC.json');res=opt(D/'RESULTS.json');rc=opt(D/'RECOUNT_053.json')
    ref=opt(D/'REFERENCE_053.json');ts=opt(study/'TEST_SUITE_053.json');order=opt(ROOT/'experiments/COMMIT_ORDER_053.json')
    api=opt(study/'API_CHECKS_053.json');fz=opt(ROOT/'experiments/BRUTE_SOURCE_FREEZE_053.json');fz50=opt(ROOT/'experiments/BRUTE_SOURCE_FREEZE_050.json')
    sc=opt(ROOT/'results/diag-053/SEEDCHECK_053.json')
    rsha=sha(D/'RESULTS.json') if (D/'RESULTS.json').exists() else None
    sealed=(bool(seal) and res is not None and sci is not None and rsha==seal.get('results_sha256')
            and sha(D/'SCIENTIFIC.json')==seal.get('scientific_sha256') and no_time(res)==sci)
    E=dict(expect or {'noise16':12,'noise16_bar':(res or {}).get('n_noise16_bar',N16BAR),'compat16':6,'scale20c':(res or {}).get('n_scale20c',N20C)})
    nfid=2*E['noise16']+E['noise16_bar']+2*E['compat16']
    allc=[c for c in (res or {}).get('cases',[]) if c['block']=='main'] if sealed else []
    G=lambda k:sorted([c for c in allc if c['key']==k],key=lambda c:c['seed'])
    n12=G('noise16');nb=G('noise16_bar');cp=G('compat16');s20=G('scale20c')
    arms_ok=(all(sorted(c['arms'])==sorted(N2) for c in n12) and all(sorted(c['arms'])==[BAR] for c in nb)
             and all(sorted(c['arms'])==sorted(CP) for c in cp) and all(sorted(c['arms'])==sorted(B2) for c in s20))  # arm sets; the runner's dict order is job order
    complete=(sealed and seal.get('complete') is True and len(n12)==E['noise16'] and len(nb)==E['noise16_bar'] and len(cp)==E['compat16']
              and len(s20)==E['scale20c'] and len(allc)==E['noise16']+E['noise16_bar']+E['compat16']+E['scale20c'] and arms_ok)
    wb=None if complete else 'INCOMPLETE_INPUT (main missing, partial, missing arms or not matching its seal)'
    def gate(name,ok,obs,why=None):Gt[name]={'pass':bool(ok) and why is None,'observed':obs,**({'reason':why} if why else {})}
    pc=(rc or {}).get('per_case') or {}
    rc_bound=bool(rc) and rc.get('results_sha256')==rsha and rc.get('cases')==len((res or {}).get('cases',[]))
    rc_ok=rc_bound and rc.get('PASS') is True and rc.get('mismatching_cases')==0
    lab=(lambda c,a:((pc.get(ckey(c)) or {}).get(a) or {}).get('label')) if rc_ok else (lambda c,a:c['arms'][a]['label'])
    lsrc='recount' if rc_ok else 'study labels (G_recount did not pass)'
    dd=lambda c,a:a in c['arms'] and lab(c,a) in ('ID','IDF')
    ci=lambda x,n:wilson(x,n) if n else None
    every=allc;everyA=[c for c in allc if c['key'] in A_KEYS]
    # GDET53
    det=[[c['seed'],canon16n(c['arms']['API16N16'])==canon16n(c['arms']['API16N16_b']),c['arms']['API16N16']['label'],c['arms']['API16N16_b']['label']]
         for c in n12 if 'API16N16_b' in c['arms']]
    guards=[[ckey(c),an,ar.get('guard_events')] for c in everyA for an,ar in c['arms'].items() if ar.get('wall_guard')]
    nd=sum(x[1] for x in det)
    gate('GDET53',complete and len(det)==E['noise16'] and nd==E['noise16'] and not guards,{'identical':nd,'of':len(det),'ci95':ci(nd,len(det)),
         'wall_guard_fired':guards,'records_checked_for_guard':sum(len(c['arms']) for c in everyA),'per_case':det,'columns':['seed','canon16n_equal','pass1','pass2'],
         'rule':'canon16n identical on 12/12 noise16 cases; wall_guard 0 on every part A record'},why=wb)
    # GFID53
    fi=(api or {}).get('fidelity') or {};fa=fi.get('part_a') or {}
    fi_ok=bool(fi) and fi.get('study_results_sha256')==rsha and fi.get('PASS') is True and fa.get('exact')==fa.get('cases')==nfid
    gate('GFID53',complete and fi_ok,{'exact':fa.get('exact'),'of':fa.get('cases'),'expected':nfid,'ci95':ci(fa.get('exact') or 0,fa.get('cases') or 0),'part_b_reported':fi.get('part_b'),
         'per_key':fi.get('per_key'),'exact_per_arm':fi.get('exact_per_arm'),'bound':bool(fi) and fi.get('study_results_sha256')==rsha,
         'failures':{k:v for k,v in (fi.get('per_case') or {}).items() if not v['exact']}},
         why=wb or (None if fi else 'INCOMPLETE_INPUT (API_CHECKS_053 fidelity missing)'))
    wrong=[[ckey(c),a] for c in every for a in c['arms'] if lab(c,a)=='WRONG' or c['arms'][a]['label']=='WRONG']
    # GN16_sound53
    wn=[x for x in wrong if x[0].startswith(('main/noise16/','main/noise16_bar/'))];xn=sum(dd(c,'API16N16') for c in n12);xb=sum(dd(c,BAR) for c in nb)
    pk=(ref or {}).get('per_key') or {}
    gate('GN16_sound53',complete and not wn and xn>=MIN_ID,{'WRONG':wn,'records':sum(len(c['arms']) for c in n12+nb),
         'API16N16_ID_IDF':xn,'of':len(n12),'ci95':ci(xn,len(n12)),'non_vacuous':xn>=MIN_ID,'min_ID_IDF':MIN_ID,
         'API16N16_bar_ID_IDF':xb,'bar_of':len(nb),'bar_ci95':ci(xb,len(nb)),
         'majority_errors':(rc or {}).get('majority_errors'),'reference_noise16':pk.get('noise16'),'reference_noise16_bar':pk.get('noise16_bar'),
         'per_case':[[c['seed'],lab(c,'API16N16'),c['arms']['API16N16']['stop'],c['arms']['API16N16'].get('reads_total'),c['arms']['API16N16'].get('majority_errors'),
                      lab(c,'API16N16_b') if 'API16N16_b' in c['arms'] else None] for c in n12],
         'per_case_bar':[[c['seed'],lab(c,BAR),c['arms'][BAR]['stop'],c['arms'][BAR].get('reads_total'),c['arms'][BAR].get('majority_errors')] for c in nb],
         'model_bound':f'P(any WRONG over {sum(len(c["arms"]) for c in n12+nb)} records) <= that count x 0.001 (Exact, conditional on the iid model)','label_source':lsrc},why=wb)
    # GCOMPAT16N53
    cq=(rc or {}).get('compat') or {};ce=[[c['seed'],bool((cq.get(ckey(c)) or {}).get('equal')),(cq.get(ckey(c)) or {}).get('label'),(cq.get(ckey(c)) or {}).get('control_label'),
        (cq.get(ckey(c)) or {}).get('machine_equal'),(cq.get(ckey(c)) or {}).get('canon16e_equal')] for c in cp];nce=sum(x[1] for x in ce)
    gate('GCOMPAT16N53',complete and rc_ok and nce==len(ce)==E['compat16'],{'equal':nce,'of':len(ce),'ci95':ci(nce,len(ce)),'per_case':ce,
         'columns':['seed','equal','label_16n16_eps0','label_16e','machine_equal','canon16e_equal (H4, informational)'],
         'canon16e_equal':sum(bool(x[5]) for x in ce),
         'rule':('plan 052 rule, reused by plan 053: same label; ID: same machine from start state 0; IDF: future_match on both and the same machine '
                 'from the current state s1'),'source':'RECOUNT_053'},
         why=wb or (None if rc_ok else 'G_recount did not pass'))
    # GHOST53
    cn=sha(ROOT/'brute/api/certify16n.py');f53=(fz or {}).get('sha256_files',{}).get('brute/api/certify16n.py');f50=(fz50 or {}).get('sha256_files',{}).get('brute/api/certify16n.py')
    abound=bool(api) and api.get('certify16n_sha256')==cn==f50 and f53 in (None,cn)
    ag=(api or {}).get('ghost') or {}
    gate('GHOST53',abound and ag.get('PASS53') is True,None if not api else {'bound_to_freeze_050':abound,'in_freeze_053':f53==cn,'frozen_api_unchanged':ag.get('frozen_api_unchanged'),
         'closures_unchanged':ag.get('closures_unchanged'),'socket_attempts':ag.get('socket_attempts'),'no_network_run':ag.get('no_network_run')},
         why=None if api else 'INCOMPLETE_INPUT (API_CHECKS_053 missing)')
    # GQB27 + cost (bounds on part A; part B maxima reported)
    mx={};mxc={};over=[];over_c=[];cost={}
    for c in every:
        pa=c['key'] in A_KEYS
        for a,ar in c['arms'].items():
            p=f"{a}/{c['key']}"
            cw=[t for r in ar['rounds'] for x in r.get('chunk_walls_informational',[]) for t in x];cs=ar.get('case_wall_informational')
            if cw:mx[p]=max(mx.get(p,0),max(cw))
            if cs is not None:mxc[p]=max(mxc.get(p,0),cs)
            if pa:
                over+=[[f'{ckey(c)}/{a}',round(t,3)] for t in cw if t>QB]
                if cs is None or cs>CASE_B:over_c.append([f'{ckey(c)}/{a}',cs])
            x=cost.setdefault(p,{'records':0,'arm_wall_s':0.0,'calls':0,'chunks':0,'capped_calls':0,'conflicts':0,'budget_spent':0,'reads':0})
            x['records']+=1;x['arm_wall_s']+=ar.get('arm_wall_informational') or 0.0;x['conflicts']+=ar.get('conflicts_spent') or 0
            x['calls']+=sum(len(r.get('call_conflicts',[])) for r in ar['rounds']);x['chunks']+=ar.get('chunks_total') or 0
            x['capped_calls']+=sum(bool(v) for r in ar['rounds'] for v in r.get('call_capped',[]))
            x['budget_spent']+=(ar.get('conflicts_spent') or 0)>=ar['budget_conflicts'];x['reads']+=ar.get('reads_total') or 0
    for x in cost.values():x['arm_wall_s']=round(x['arm_wall_s'],1)
    mxA={p:v for p,v in mx.items() if p.split('/')[1] in A_KEYS};mxcA={p:v for p,v in mxc.items() if p.split('/')[1] in A_KEYS}
    gate('GQB27',complete and bool(mxA) and not over and not over_c,{'max_chunk_wall_s':{k:round(v,3) for k,v in sorted(mxA.items())},
         'max_case_wall_s':{k:round(v,3) for k,v in sorted(mxcA.items())},'scope':'part A records','chunk_bound_s':QB,'case_bound_s':CASE_B,'over_chunk':over,'over_case':over_c},why=wb)
    # GS_ref
    mt=(ref or {}).get('mutation_test') or {};rb=bool(ref) and ref.get('study_results_sha256')==rsha and ref.get('block')=='main'
    robs=None if not ref else {k:ref.get(k) for k in ('block','scope','records','decided','audited','not_audited','complete','per_arm','per_key','not_reached',
                               'k_spent_as_amb','verdicts_checked','mismatch_count','vacuous','PASS','elapsed_informational')}|{'mutations':mt.get('detected'),'of':mt.get('mutations')}
    gate('GS_ref',rb and ref.get('mismatch_count')==0 and ref.get('complete') is True and (ref.get('scope') or {}).get('budget_12_s')==2400.0
         and mt.get('detected')==mt.get('mutations')==20 and ref.get('PASS') is True,robs,why=wb or (None if ref else 'INCOMPLETE_INPUT (REFERENCE_053 missing)'))
    # G_sound / G_recount
    wc=[x for x in wrong if x[0].startswith('main/compat16/')]
    snd={'words_checked':sum(ar.get('words_checked',0) for c in every for ar in c['arms'].values()),
         'words_unsound':sum(ar.get('words_unsound',0) for c in every for ar in c['arms'].values()),
         'recount_bound':rc_bound,'recount_words_checked':(rc or {}).get('words_checked'),'recount_words_unsound':(rc or {}).get('words_unsound'),
         'recount_truth_inconsistent':(rc or {}).get('truth_inconsistent'),'compat_WRONG':wc}
    gate('G_sound',complete and rc_bound and snd['words_unsound']==0 and snd['recount_words_unsound']==0 and snd['recount_words_checked']==snd['words_checked'] and not wc,
         snd,why=wb or (None if rc_bound else 'INCOMPLETE_INPUT (RECOUNT_053 missing or unbound)'))
    gate('G_recount',complete and rc_ok,None if not rc else {k:rc.get(k) for k in ('cases','recounted','labels','compat_equal','majority_errors','misfires',
         'amb_rule_applied','words_checked','words_unsound','truth_inconsistent','mismatching_cases','mismatches','PASS')},
         why=wb or (None if rc else 'INCOMPLETE_INPUT (RECOUNT_053 missing)'))
    # GTI / GTEST
    sc_frozen=bool(sc) and (fz or {}).get('sha256_files',{}).get('results/diag-053/SEEDCHECK_053.json')==sha(ROOT/'results/diag-053/SEEDCHECK_053.json')
    gate('GTI',bool(sc) and sc.get('PASS') is True and sc_frozen,None if not sc else {'seedcheck_pass':sc.get('PASS'),'frozen_in_053':sc_frozen,
         'total_cases':sc.get('total_cases'),'prior_range_count':sc.get('prior_range_count'),'all_tokens_allowed':sc.get('all_tokens_allowed')},
         why=None if sc else 'INCOMPLETE_INPUT (SEEDCHECK_053 missing)')
    mods=(ts or {}).get('per_module') or {};gm=(ts or {}).get('gated_modules') or []
    gate('GTEST',bool(gm) and ts.get('passed') is True and all(mods[m].get('returncode')==0 for m in gm),
         None if not ts else {'gated':{m:{'returncode':mods[m].get('returncode'),'tests':mods[m].get('tests')} for m in gm},
                              'reported':{m:{'returncode':v.get('returncode'),'tests':v.get('tests')} for m,v in mods.items() if m not in gm}},
         why=None if ts else 'INCOMPLETE_INPUT (TEST_SUITE_053 missing)')
    lt=ledger();ev=[e for e,_ in lt];times=[t for _,t in lt]
    proc={'order':subseq(ev,PROC_ORDER),'ledger_times_parse':bool(lt) and all(t is not None for t in times),
          'ledger_times_non_decreasing':all(a<=b for a,b in zip(times,times[1:]) if a and b),'commit_order_file':order is not None,'main_sealed':bool(sealed)}
    gate('G_PROC',all(proc.values()),{'clauses':proc,'events':ev,'required_order':list(PROC_ORDER)})
    el=(res or {}).get('total_elapsed_informational')
    gate('G_RT',complete and el is not None and el<=CAP_RT,{'elapsed_s':el,'cap_s':CAP_RT,'cases':len(allc),'n_noise16_bar':E['noise16_bar'],'n_scale20c':E['scale20c']},why=wb)
    # non-blocking part B gates (scored; excluded from all_gated_pass and from the certification by the plan)
    nb_g={}
    def ngate(name,ok,obs,why=None):nb_g[name]={'pass':bool(ok) and why is None,'observed':obs,'blocking':False,**({'reason':why} if why else {})}
    d20=[[c['seed'],canon16e(c['arms']['API16E20'])==canon16e(c['arms']['API16E20_b']),c['arms']['API16E20']['label'],c['arms']['API16E20_b']['label'],
          c['arms']['API16E20'].get('conflicts_spent'),c['arms']['API16E20_b'].get('conflicts_spent')] for c in s20 if 'API16E20_b' in c['arms']]
    kills=[[ckey(c),an,ar.get('guard_events')] for c in s20 for an,ar in c['arms'].items() if ar.get('wall_guard')]
    n20=sum(x[1] for x in d20)
    ngate('GS20C_det53',complete and len(d20)==E['scale20c'] and n20==E['scale20c'] and not kills,{'identical':n20,'of':len(d20),'ci95':ci(n20,len(d20)),
          'hard_kills':kills,'per_case':d20,'columns':['seed','canon16e_equal','pass1','pass2','conflicts_pass1','conflicts_pass2'],
          'rule':'canon16e identical on every scale20c case (plan: 6/6, cut rule applied) and 0 hard kills at 900 s'},why=wb)
    w20=[x for x in wrong if x[0].startswith('main/scale20c/')];x20=sum(dd(c,a) for c in s20 for a in B2);r20=sum(len(c['arms']) for c in s20)
    ngate('GS20C_sound53',complete and not w20,{'WRONG':w20,'records':r20,'decided_ID_IDF':x20,'of':r20,'ci95':ci(x20,r20),
          'per_case':[[c['seed'],lab(c,'API16E20'),c['arms']['API16E20']['stop'],lab(c,'API16E20_b'),c['arms']['API16E20_b']['stop']] for c in s20],
          'label_source':lsrc},why=wb)
    # secondary
    sec['GCOST53']={'pass':None,'observed':dict(sorted(cost.items())),'rule':'reported: wall, calls, chunks, capped calls, conflicts, budget-spent records, reads per arm/key'}
    def rd(cs,a):
        rp=[c['arms'][a].get('reads_total') or 0 for c in cs];ob=[len(c['arms'][a].get('reads_per_obs') or []) for c in cs]
        return {'reads_total':sum(rp),'observations':sum(ob),'reads_per_observation':round(sum(rp)/sum(ob),2) if sum(ob) else None,
                'k_range':[min((min(c['arms'][a]['reads_per_obs']) for c in cs if c['arms'][a].get('reads_per_obs')),default=None),max((c['arms'][a].get('reads_max') or 0 for c in cs),default=None)]}
    sec['GN16_rate53']={'pass':None,'observed':{'eps_0.05':{'ID_IDF':xn,'of':len(n12),'ci95':ci(xn,len(n12)),**(rd(n12,'API16N16') if n12 else {})},
                        'eps_0.10':{'ID_IDF':xb,'of':len(nb),'ci95':ci(xb,len(nb)),**(rd(nb,BAR) if nb else {})}},'rule':'reported'}
    rate={}
    for a in B2:
        cf=sum(c['arms'][a].get('conflicts_spent') or 0 for c in s20);wl=sum(c['arms'][a].get('arm_wall_informational') or 0.0 for c in s20)
        rate[a]={'conflicts':cf,'arm_wall_s':round(wl,1),'conflicts_per_s':round(cf/wl,1) if wl else None,
                 'max_chunk_wall_s':round(mx.get(f'{a}/scale20c',0.0),3),'max_case_wall_s':round(mxc.get(f'{a}/scale20c',0.0),3)}
    sec['GS20C_rate53']={'pass':None,'observed':rate,'rule':'reported: part B conflicts per second (informational wall), max chunk and case wall'}
    cnt=lambda k,a,L:sum(lab(c,a)==L for c in G(k) if a in c['arms']);nk=lambda k,a:sum(a in c['arms'] for c in G(k))
    fl={f'{a}/{k}':{L:{'x':cnt(k,a,L),'n':nk(k,a),'ci95':ci(cnt(k,a,L),nk(k,a))} for L in LABELS}
        for k,arms in (('noise16',N2),('noise16_bar',(BAR,)),('compat16',CP),('scale20c',B2)) for a in arms}
    ok=all(g['pass'] for g in Gt.values())
    return {'schema':'brute.gates.v50_0','study':(res or {}).get('plan',{}).get('study'),'process':'lean','sealed_input_verified':sealed,'label_source':lsrc,
            'n_noise16_bar':E['noise16_bar'],'n_scale20c':E['scale20c'],'caps':(res or {}).get('caps'),'workers':(res or {}).get('workers'),
            'noise':(res or {}).get('noise'),'part_b':(res or {}).get('part_b'),'gates':Gt,'nonblocking':nb_g,'secondary':sec,
            'all_gated_pass':ok,'failed':[k for k,g in Gt.items() if g['pass'] is False],'nonblocking_failed':[k for k,g in nb_g.items() if g['pass'] is False],
            'not_exercised':[],'certified_16n_N16':ok,
            'claim':('certify/16n ID/IDF is exact conditional on every majority being correct (probability >= 1 - delta per record under iid flips with '
                     'eps <= eps_bar) and true size <= the declared N (here N <= 16); IDF identifies the machine from the current state, not the start. '
                     'Inferred reason the condition is needed: a larger machine can copy the true machine on every visited state'),
            'reports':{'labels':fl} if allc else {}}


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--study-dir',default=str(STUDY_DIR));ap.add_argument('--check',action='store_true');a=ap.parse_args()
    obj=build(Path(a.study_dir));out=Path(a.study_dir)/'GATES_053.json'
    if a.check:check(out.read_bytes()==dumps(obj),'GATES_053.json does not reproduce');print('GATES_053 reproduces')
    else:write_new(out,obj);print(json.dumps({k:v['pass'] for k,v in obj['gates'].items()}),json.dumps({k:v['pass'] for k,v in obj['nonblocking'].items()}),obj['failed'])
