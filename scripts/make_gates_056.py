"""Gates for study-056 (BRUTE_PLAN_056 criteria; pre-run deviation #185 definitions), LEAN process. Committed in
the source freeze before run_start_056; nothing is tuned after results are seen. New file; built from scripts/make_gates_055.py (frozen).
Inputs (D = results/study-056): D/main/{RESULTS,SCIENTIFIC,SEAL}.json, D/main/RECOUNT_056.json, D/main/REFERENCE_056.json,
D/API_CHECKS_056.json, D/TEST_SUITE_056.json, results/diag-056/SEEDCHECK_056.json, experiments/COMMIT_ORDER_056.json,
results/RESEARCH_LEDGER.jsonl. Missing or partial input => every data gate FAIL INCOMPLETE_INPUT. Records are accepted only if
sha256(RESULTS) equals the seal and no_time(RESULTS) equals SCIENTIFIC. Labels: recounted if G_recount passes, else the study's.
scale20t = API20L / API20L_b (certify/20l, bound 20) and API16E20 (certify/16e, bound 20); compat20t = API20L vs API16E (bound 16);
conflict-only stop everywhere, 900 s hard kill.
  GDET56: canon20l(API20L) == canon20l(API20L_b) (canon16e plus the table, #185) and identical conflicts_spent on every scale20t case
     (6/6 at full size), 0 hard kills (wall_guard) on every record;
  GFID56: API_CHECKS_056 fidelity exact on every API20L / API20L_b record (12 + 6 at full size), bound to the sealed RESULTS sha;
  GS20L_sound56: WRONG 0 on every scale20t record (API20L, API20L_b, API16E20) and every compat20t record;
  GS20L_gain56: API20L (pass 1) ID+IDF >= 2 of the scale20t cases AND > API16E20 ID+IDF on the same seeds (Wilson CIs reported);
  GCOMPAT20L56: every compat20t seed equal under compat_rule_056 (RECOUNT_056 compat). compat_rule_056 was introduced after the 055
     compat failure and is not retroactive: it is applied to 055 only in the reported, never gated RECHECK_055;
  GTABLE56: REFERENCE_056 table_audit (scripts/table_audit_056) bound to the sealed RESULTS sha, covering every API20L / API20L_b record
     (2 x scale20t + compat20t), PASS: the table, every hypothesis and every proposed word reproduce from the trace alone, and every
     counterexample word distinguishes H from the SAT rival;
  GHOST56: API_CHECKS_056 ghost PASS56 (no network; frozen API files and 16e / 16n / 16s / 20t / 20c closures unchanged), bound to
     certify20l.py's sha in BRUTE_SOURCE_FREEZE_056;
  GS_ref: REFERENCE_056 on block main: sha bound, 0 mismatches, complete within 2400 s on 8 workers, 20/20 mutations (vacuous only if
     no API20L record is decided; then mutations are not required and this is reported);
  G_sound: 0 unsound words on every record (study and recount), recount checked the same words, 0 WRONG anywhere;
  G_recount;  GTI: SEEDCHECK_056 PASS and its sha frozen in BRUTE_SOURCE_FREEZE_056;  GTEST: gated modules of TEST_SUITE_056 pass;
  G_PROC: preregistration, build_authorization, seedcheck, prefreeze_smoke, source_freeze, run_start, run_end, recount, reference,
     api_checks, tests (all _056, exact names) as a subsequence, parseable non-decreasing note times, commit-order file, main sealed;
  G_RT: main elapsed <= 3600 s.
  certified_20l_N20: true iff every gated gate passes, GS20L_gain56 included; sound_not_certified_20l: every gate except
  GS20L_gain56 passes (plan certification_rule). status_phrase: derived from the two flags (plan status_wording_rule).
  Secondary (reported): GS20L_rate56, GS20L_paired56, GTABLE_stats56, GCOST56, RECHECK_055 (recheck_12270005: compat_rule_056 on the
  sealed 055 compat pairs 12270003 and 12270005, read-only, no solver, never gated).
  PYTHONPATH=. python scripts/make_gates_056.py [--study-dir D] [--check]"""
from __future__ import annotations
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common import load,dumps,write_new,check,sha
from experiments.brute_common_026 import wilson
from scripts.make_gates_034 import opt
from scripts.make_gates_043 import subseq

STUDY_DIR=ROOT/'results/study-056';S3=('API20L','API20L_b','API16E20');CP=('API20L','API16E')
LABELS=('ID','IDF','AMB','WRONG','IDU');CAP_RT=3600;MIN_ID=2
PROC_ORDER=tuple(e+'_056' for e in ('preregistration','build_authorization','seedcheck','prefreeze_smoke','source_freeze','run_start','run_end',
                                    'recount','reference','api_checks','tests'))


def ckey(c):return f"{c['block']}/{c['key']}/{c['seed']}"


def ledger():
    from datetime import datetime
    L=[json.loads(x) for x in (ROOT/'results/RESEARCH_LEDGER.jsonl').read_text().splitlines() if x.strip()]
    i0=next((i for i,e in enumerate(L) if e.get('event')=='preregistration_056'),None);out=[]
    for e in (L[i0:] if i0 is not None else []):
        try:t=datetime.fromisoformat(str(e.get('note',''))[:25])
        except ValueError:t=None
        out.append((e['event'],t))
        if e['event']==PROC_ORDER[-1]:break
    return out


R055=ROOT/'results/study-055/main';R055_SHA='aaab8ab2';RECHECK_SEEDS=(12270003,12270005)


def status_phrase(certified,sound_only,failed):
    """Plan 056 status_wording_rule: the only status phrases, derived from the two flags."""
    if certified:return 'certified'
    if sound_only:return 'sound but not certified'
    return 'not certified, no certification status (failing gates: '+', '.join(failed)+')'


def recheck_055():
    """recheck_12270005 (plan 056): compat_rule_056 on the sealed 055 compat pairs, read-only (no solver, no new seed), never gated.
    Labels and future_match are RECOUNT_055's (055 recount, at each arm's own stop step); machines are the 055 records'."""
    from scripts.recount_056 import compat_rule_056
    try:
        from scripts.study055_storage import ensure_raw;ensure_raw()
        res=load(R055/'RESULTS.json');rc=load(R055/'RECOUNT_055.json');rsha=sha(R055/'RESULTS.json')
    except Exception as e:return {'pass':None,'observed':None,'reason':'055 inputs unavailable: '+str(e)[:200]}
    out={}
    for c in res['cases']:
        if c['key']!='compat20t' or c['seed'] not in RECHECK_SEEDS:continue
        k=f"{c['block']}/{c['key']}/{c['seed']}";px=rc['per_case'][k]['API20C'];py=rc['per_case'][k]['API16E']
        r=compat_rule_056(c['arms']['API20C'],c['arms']['API16E'],px['label'],py['label'],px.get('future_match'),py.get('future_match'))
        out[str(c['seed'])]={x:r.get(x) for x in ('equal','label','control_label','rule','machine_equal','future_match','unpointed_iso')}
    return {'pass':None,'observed':out,'results_sha256':rsha,'bound_to_055_seal':rsha.startswith(R055_SHA),
            'rule':'reported only: compat_rule_056 applied read-only to sealed 055 compat pairs 12270003 and 12270005; never gated; changes no 055 file'}


def build(study=STUDY_DIR,expect=None):
    """expect: case counts {scale20t, compat20t}; the sealed n_scale20t / n_compat20t (plan 6 / 6 unless the declared cut applies)."""
    from brute.evaluation import no_time
    from experiments.brute_study_056 import canon20l,N20L,NC20L
    study=Path(study);D=study/'main';Gt={};sec={}
    seal=opt(D/'SEAL.json');sci=opt(D/'SCIENTIFIC.json');res=opt(D/'RESULTS.json');rc=opt(D/'RECOUNT_056.json')
    ref=opt(D/'REFERENCE_056.json');ts=opt(study/'TEST_SUITE_056.json');order=opt(ROOT/'experiments/COMMIT_ORDER_056.json')
    api=opt(study/'API_CHECKS_056.json');fz=opt(ROOT/'experiments/BRUTE_SOURCE_FREEZE_056.json')
    sc=opt(ROOT/'results/diag-056/SEEDCHECK_056.json')
    rsha=sha(D/'RESULTS.json') if (D/'RESULTS.json').exists() else None
    sealed=(bool(seal) and res is not None and sci is not None and rsha==seal.get('results_sha256')
            and sha(D/'SCIENTIFIC.json')==seal.get('scientific_sha256') and no_time(res)==sci)
    E=dict(expect or {'scale20t':(res or {}).get('n_scale20t',N20L),'compat20t':(res or {}).get('n_compat20t',NC20L)})
    nfid=2*E['scale20t']+E['compat20t']
    allc=[c for c in (res or {}).get('cases',[]) if c['block']=='main'] if sealed else []
    G=lambda k:sorted([c for c in allc if c['key']==k],key=lambda c:c['seed'])
    s20=G('scale20t');cp=G('compat20t')
    arms_ok=all(sorted(c['arms'])==sorted(S3) for c in s20) and all(sorted(c['arms'])==sorted(CP) for c in cp)
    complete=(sealed and seal.get('complete') is True and len(s20)==E['scale20t'] and len(cp)==E['compat20t']
              and len(allc)==E['scale20t']+E['compat20t'] and arms_ok)
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
    # GDET56
    det=[[c['seed'],canon20l(c['arms']['API20L'])==canon20l(c['arms']['API20L_b']),
          c['arms']['API20L'].get('conflicts_spent')==c['arms']['API20L_b'].get('conflicts_spent'),
          c['arms']['API20L']['label'],c['arms']['API20L_b']['label'],c['arms']['API20L'].get('conflicts_spent'),c['arms']['API20L_b'].get('conflicts_spent')]
         for c in s20 if 'API20L_b' in c['arms']]
    kills=[[ckey(c),an,ar.get('guard_events')] for c in every for an,ar in c['arms'].items() if ar.get('wall_guard')]
    nd=sum(x[1] and x[2] for x in det)
    gate('GDET56',complete and len(det)==E['scale20t'] and nd==E['scale20t'] and not kills,{'identical':nd,'of':len(det),'ci95':ci(nd,len(det)),
         'hard_kills':kills,'records_checked_for_kill':sum(len(c['arms']) for c in every),'per_case':det,
         'columns':['seed','canon20l_equal','conflicts_equal','pass1','pass2','conflicts_pass1','conflicts_pass2'],
         'rule':'canon20l (canon16e plus the table) and conflicts_spent identical on every scale20t case; 0 hard kills (wall_guard) on every record'},why=wb)
    # GFID56
    fi=(api or {}).get('fidelity') or {};fg=fi.get('gated') or {}
    fi_ok=bool(fi) and fi.get('study_results_sha256')==rsha and fi.get('PASS') is True and fg.get('exact')==fg.get('cases')==nfid
    gate('GFID56',complete and fi_ok,{'exact':fg.get('exact'),'of':fg.get('cases'),'expected':nfid,'ci95':ci(fg.get('exact') or 0,fg.get('cases') or 0),
         'reported_16e':fi.get('reported'),'per_key':fi.get('per_key'),'exact_per_arm':fi.get('exact_per_arm'),'bound':bool(fi) and fi.get('study_results_sha256')==rsha,
         'failures':{k:v for k,v in (fi.get('per_case') or {}).items() if not v['exact']}},
         why=wb or (None if fi else 'INCOMPLETE_INPUT (API_CHECKS_056 fidelity missing)'))
    wrong=[[ckey(c),a] for c in every for a in c['arms'] if lab(c,a)=='WRONG' or c['arms'][a]['label']=='WRONG']
    # GS20L_sound56
    gate('GS20L_sound56',complete and not wrong,{'WRONG':wrong,'records':sum(len(c['arms']) for c in every),
         'per_case':[[c['seed'],lab(c,'API20L'),lab(c,'API20L_b'),lab(c,'API16E20')] for c in s20],
         'per_case_compat':[[c['seed'],lab(c,'API20L'),lab(c,'API16E')] for c in cp],'label_source':lsrc},why=wb)
    # GS20L_gain56
    xt=sum(dd(c,'API20L') for c in s20);xe=sum(dd(c,'API16E20') for c in s20);xb=sum(dd(c,'API20L_b') for c in s20)
    gate('GS20L_gain56',complete and xt>=MIN_ID and xt>xe,{'API20L_ID_IDF':xt,'API16E20_ID_IDF':xe,'API20L_b_ID_IDF':xb,'of':len(s20),
         'ci95_API20L':ci(xt,len(s20)),'ci95_API16E20':ci(xe,len(s20)),'ci95_API20L_b':ci(xb,len(s20)),'min_ID_IDF':MIN_ID,
         'rule':'API20L (pass 1) ID+IDF >= 2 and strictly more than API16E20 on the same seeds','label_source':lsrc},why=wb)
    # GCOMPAT20L56
    cq=(rc or {}).get('compat') or {};ce=[[c['seed'],bool((cq.get(ckey(c)) or {}).get('equal')),(cq.get(ckey(c)) or {}).get('label'),(cq.get(ckey(c)) or {}).get('control_label'),
        (cq.get(ckey(c)) or {}).get('machine_equal'),(cq.get(ckey(c)) or {}).get('future_match'),(cq.get(ckey(c)) or {}).get('unpointed_iso')] for c in cp];nce=sum(x[1] for x in ce)
    gate('GCOMPAT20L56',complete and rc_ok and nce==len(ce)==E['compat20t'],{'equal':nce,'of':len(ce),'ci95':ci(nce,len(ce)),'per_case':ce,
         'columns':['seed','equal','label_20l','label_16e','machine_equal','future_match (IDF)','unpointed_iso (IDF)'],
         'rule':('compat_rule_056 (plan 056, introduced after the 055 compat failure, not retroactive): same label; ID: same machine from start '
                 'state 0; IDF: each arm future_matches the truth at its OWN stop step and the minimised parts reachable from each current '
                 'state are isomorphic as unpointed machines'),
         'source':'RECOUNT_056'},why=wb or (None if rc_ok else 'G_recount did not pass'))
    # GHOST56
    ct=sha(ROOT/'brute/api/certify20l.py');f56=(fz or {}).get('sha256_files',{}).get('brute/api/certify20l.py')
    abound=bool(api) and api.get('certify20l_sha256')==ct==f56
    ag=(api or {}).get('ghost') or {}
    gate('GHOST56',abound and ag.get('PASS56') is True,None if not api else {'bound_to_freeze_056':abound,'frozen_api_unchanged':ag.get('frozen_api_unchanged'),
         'closures_unchanged':ag.get('closures_unchanged'),'socket_attempts':ag.get('socket_attempts'),'no_network_run':ag.get('no_network_run')},
         why=None if api else 'INCOMPLETE_INPUT (API_CHECKS_056 missing)')
    # cost / rates (walls informational, never used for a decision)
    mx={};mxc={};cost={}
    for c in every:
        for a,ar in c['arms'].items():
            p=f"{a}/{c['key']}"
            cw=[t for r in ar['rounds'] for x in r.get('chunk_walls_informational',[]) for t in x];cs=ar.get('case_wall_informational')
            if cw:mx[p]=max(mx.get(p,0),max(cw))
            if cs is not None:mxc[p]=max(mxc.get(p,0),cs)
            x=cost.setdefault(p,{'records':0,'arm_wall_s':0.0,'calls':0,'chunks':0,'capped_calls':0,'conflicts':0,'budget_spent':0})
            x['records']+=1;x['arm_wall_s']+=ar.get('arm_wall_informational') or 0.0;x['conflicts']+=ar.get('conflicts_spent') or 0
            x['calls']+=sum(len(r.get('call_conflicts',[])) for r in ar['rounds']);x['chunks']+=ar.get('chunks_total') or 0
            x['capped_calls']+=sum(bool(v) for r in ar['rounds'] for v in r.get('call_capped',[]))
            x['budget_spent']+=(ar.get('conflicts_spent') or 0)>=ar['budget_conflicts']
    for x in cost.values():x['arm_wall_s']=round(x['arm_wall_s'],1)
    # GS_ref
    mt=(ref or {}).get('mutation_test') or {};rb=bool(ref) and ref.get('study_results_sha256')==rsha and ref.get('block')=='main'
    robs=None if not ref else {k:ref.get(k) for k in ('block','scope','records','decided','audited','not_audited','complete','per_arm','per_key','not_reached',
                               'k_spent_as_amb','verdicts_checked','mismatch_count','vacuous','PASS','elapsed_informational')}|{'mutations':mt.get('detected'),'of':mt.get('mutations')}
    gate('GS_ref',rb and ref.get('mismatch_count')==0 and ref.get('complete') is True and (ref.get('scope') or {}).get('budget_12_s')==2400.0
         and (ref.get('vacuous') is True or mt.get('detected')==mt.get('mutations')==20) and ref.get('PASS') is True,robs,
         why=wb or (None if ref else 'INCOMPLETE_INPUT (REFERENCE_056 missing)'))
    # GTABLE56
    tb=(ref or {}).get('table_audit') or {};ntb=2*E['scale20t']+E['compat20t']
    gate('GTABLE56',rb and tb.get('PASS') is True and tb.get('records')==ntb,None if not ref else {'records':tb.get('records'),'expected':ntb,
         'entries':tb.get('entries'),'counterexamples_checked':tb.get('counterexamples_checked'),'mismatch_records':tb.get('mismatch_records'),
         'bound':rb,'source':'REFERENCE_056 table_audit (scripts/table_audit_056)'},
         why=wb or (None if ref else 'INCOMPLETE_INPUT (REFERENCE_056 missing)'))
    # G_sound / G_recount
    snd={'words_checked':sum(ar.get('words_checked',0) for c in every for ar in c['arms'].values()),
         'words_unsound':sum(ar.get('words_unsound',0) for c in every for ar in c['arms'].values()),
         'recount_bound':rc_bound,'recount_words_checked':(rc or {}).get('words_checked'),'recount_words_unsound':(rc or {}).get('words_unsound'),
         'recount_truth_inconsistent':(rc or {}).get('truth_inconsistent'),'WRONG':wrong}
    gate('G_sound',complete and rc_bound and snd['words_unsound']==0 and snd['recount_words_unsound']==0 and snd['recount_words_checked']==snd['words_checked'] and not wrong,
         snd,why=wb or (None if rc_bound else 'INCOMPLETE_INPUT (RECOUNT_056 missing or unbound)'))
    gate('G_recount',complete and rc_ok,None if not rc else {k:rc.get(k) for k in ('cases','recounted','labels','compat_equal','misfires',
         'amb_rule_applied','words_checked','words_unsound','truth_inconsistent','mismatching_cases','mismatches','PASS')},
         why=wb or (None if rc else 'INCOMPLETE_INPUT (RECOUNT_056 missing)'))
    # GTI / GTEST
    sc_frozen=bool(sc) and (fz or {}).get('sha256_files',{}).get('results/diag-056/SEEDCHECK_056.json')==sha(ROOT/'results/diag-056/SEEDCHECK_056.json')
    gate('GTI',bool(sc) and sc.get('PASS') is True and sc_frozen,None if not sc else {'seedcheck_pass':sc.get('PASS'),'frozen_in_056':sc_frozen,
         'total_cases':sc.get('total_cases'),'prior_range_count':sc.get('prior_range_count'),'all_tokens_allowed':sc.get('all_tokens_allowed'),
         'gz_files_decompressed':sc.get('gz_files_decompressed')},why=None if sc else 'INCOMPLETE_INPUT (SEEDCHECK_056 missing)')
    mods=(ts or {}).get('per_module') or {};gm=(ts or {}).get('gated_modules') or []
    gate('GTEST',bool(gm) and ts.get('passed') is True and all(mods[m].get('returncode')==0 for m in gm),
         None if not ts else {'gated':{m:{'returncode':mods[m].get('returncode'),'tests':mods[m].get('tests')} for m in gm},
                              'reported':{m:{'returncode':v.get('returncode'),'tests':v.get('tests')} for m,v in mods.items() if m not in gm}},
         why=None if ts else 'INCOMPLETE_INPUT (TEST_SUITE_056 missing)')
    lt=ledger();ev=[e for e,_ in lt];times=[t for _,t in lt]
    proc={'order':subseq(ev,PROC_ORDER),'ledger_times_parse':bool(lt) and all(t is not None for t in times),
          'ledger_times_non_decreasing':all(a<=b for a,b in zip(times,times[1:]) if a and b),'commit_order_file':order is not None,'main_sealed':bool(sealed)}
    gate('G_PROC',all(proc.values()),{'clauses':proc,'events':ev,'required_order':list(PROC_ORDER)})
    el=(res or {}).get('total_elapsed_informational')
    gate('G_RT',complete and el is not None and el<=CAP_RT,{'elapsed_s':el,'cap_s':CAP_RT,'cases':len(allc),'n_scale20t':E['scale20t'],'n_compat20t':E['compat20t']},why=wb)
    # secondary
    cst={};TK=('entries','rows','columns','hypotheses','counterexamples','fill_steps')
    for x in tb.get('per_record') or []:cst[x['id']]={k:x[k] for k in TK}
    sec['GTABLE_stats56']={'pass':None,'observed':cst,'totals':{k:sum(v[k] for v in cst.values()) for k in TK},
                           'rule':'reported: table entries, rows, columns, hypotheses, counterexamples and fill steps per record'}
    for c in every:
        for a,ar in c['arms'].items():
            t=ar.get('table') or {};x=cost[f"{a}/{c['key']}"]
            x['hypotheses']=x.get('hypotheses',0)+(t.get('hypotheses') or 0);x['counterexamples']=x.get('counterexamples',0)+(t.get('counterexamples') or 0)
            x['steps']=x.get('steps',0)+len(ar.get('extra_acts') or [])
    sec['GCOST56']={'pass':None,'observed':dict(sorted(cost.items())),'rule':'reported: wall, calls, chunks, capped calls, conflicts, hypotheses, counterexamples, steps, budget-spent records per arm/key'}
    rate={}
    for a in S3:
        cf=sum(c['arms'][a].get('conflicts_spent') or 0 for c in s20);wl=sum(c['arms'][a].get('arm_wall_informational') or 0.0 for c in s20)
        x=sum(dd(c,a) for c in s20);cfd=sum(c['arms'][a].get('conflicts_spent') or 0 for c in s20 if dd(c,a))
        rate[a]={'ID_IDF':x,'of':len(s20),'ci95':ci(x,len(s20)),'conflicts':cf,'conflicts_per_decided_case':round(cfd/x,1) if x else None,
                 'arm_wall_s':round(wl,1),'conflicts_per_s':round(cf/wl,1) if wl else None,
                 'max_chunk_wall_s':round(mx.get(f'{a}/scale20t',0.0),3),'max_case_wall_s':round(mxc.get(f'{a}/scale20t',0.0),3)}
    sec['GS20L_rate56']={'pass':None,'observed':rate,'rule':'reported: ID+IDF with Wilson CIs, conflicts per decided case, conflicts/s, max chunk and case wall (informational)'}
    sec['GS20L_paired56']={'pass':None,'observed':[[c['seed'],lab(c,'API20L'),len(c['arms']['API20L'].get('extra_acts') or []),c['arms']['API20L'].get('conflicts_spent'),
                                                   lab(c,'API16E20'),len(c['arms']['API16E20'].get('extra_acts') or []),c['arms']['API16E20'].get('conflicts_spent')] for c in s20],
                           'columns':['seed','API20L_label','API20L_steps','API20L_conflicts','API16E20_label','API16E20_steps','API16E20_conflicts'],'rule':'reported'}
    sec['RECHECK_055']=recheck_055()
    cnt=lambda k,a,L:sum(lab(c,a)==L for c in G(k) if a in c['arms']);nk=lambda k,a:sum(a in c['arms'] for c in G(k))
    fl={f'{a}/{k}':{L:{'x':cnt(k,a,L),'n':nk(k,a),'ci95':ci(cnt(k,a,L),nk(k,a))} for L in LABELS}
        for k,arms in (('scale20t',S3),('compat20t',CP)) for a in arms}
    ok=all(g['pass'] for g in Gt.values())
    sound_only=not ok and all(g['pass'] for k,g in Gt.items() if k!='GS20L_gain56')
    phrase=status_phrase(ok,sound_only,[k for k,g in Gt.items() if g['pass'] is False])
    return {'schema':'brute.gates.v53_0','study':(res or {}).get('plan',{}).get('study'),'process':'lean',
            'sealed_input_verified':sealed,'label_source':lsrc,'n_scale20t':E['scale20t'],'n_compat20t':E['compat20t'],'caps':(res or {}).get('caps'),
            'workers':(res or {}).get('workers'),'stop':(res or {}).get('stop'),'gates':Gt,'secondary':sec,
            'all_gated_pass':ok,'failed':[k for k,g in Gt.items() if g['pass'] is False],'not_exercised':[],
            'certified_20l_N20':ok,'sound_not_certified_20l':sound_only,'status_phrase':phrase,
            'claim':('certify/20l ID/IDF is exact on noise-free traces conditional on true size <= the declared N (here N <= 20); IDF identifies the '
                     'machine from the current state, not the start. Inferred reason the condition is needed: a larger machine can copy the true '
                     'machine on every visited state'),
            'reports':{'labels':fl} if allc else {}}


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--study-dir',default=str(STUDY_DIR));ap.add_argument('--check',action='store_true');a=ap.parse_args()
    obj=build(Path(a.study_dir));out=Path(a.study_dir)/'GATES_056.json'
    if a.check:check(out.read_bytes()==dumps(obj),'GATES_056.json does not reproduce');print('GATES_056 reproduces')
    else:write_new(out,obj);print(json.dumps({k:v['pass'] for k,v in obj['gates'].items()}),obj['failed'])
