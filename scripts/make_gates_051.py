"""Gates for study-051 (BRUTE_PLAN_051 criteria; pre-run deviation #175 definitions), LEAN process. Committed in the source freeze
before run_start_051; nothing is tuned after results are seen. New file; built from scripts/make_gates_050.py (frozen).
Inputs (D = results/study-051): D/main/{RESULTS,SCIENTIFIC,SEAL}.json, D/main/RECOUNT_051.json, D/main/REFERENCE_051.json,
D/API_CHECKS_051.json, D/TEST_SUITE_051.json, results/diag-051/SEEDCHECK_051.json, experiments/COMMIT_ORDER_051.json,
results/RESEARCH_LEDGER.jsonl. Missing or partial input => every data gate FAIL INCOMPLETE_INPUT. Records are accepted only if
sha256(RESULTS) equals the seal and no_time(RESULTS) equals SCIENTIFIC. Labels: recounted if G_recount passes, else the study's.
  GDET51: canon16s(API16S) == canon16s(API16S_b) on 12/12 scale20, canon16e(API16E) == canon16e(API16E_b) on 6/6 controls,
     canon16n(API16N) == canon16n(API16N_b) on the N12B doubly-run noise12 cases, AND wall_guard 0 on every record;
  GFID51: API_CHECKS_051 fidelity exact on 12 API16S + 6 API16E + 12 API16N records, bound to the sealed RESULTS sha;
  GS20_sound51: scale20 WRONG 0 (both arms), every decided scale20 record audited at bound 20 by REFERENCE_051 with 0 mismatches,
     AND >= 1/12 API16S scale20 records decided (0 decided FAILS);
  GN12_sound51: noise12 WRONG 0 on both passes (labels against the clean truth);
  GCOMPAT16S: part c (API16S_c, certify/16s at bound 12) equals the part-k API16E record on label and, for ID / IDF, on the
     canonical (BFS-numbered) machine, on NCOMPAT/NCOMPAT (RECOUNT_051 comparison);
  GHOST51: API_CHECKS_051 ghost PASS51, bound to certify16s.py's sha in the 051 freeze;  G10: 6/6 controls ID on both passes;
  GQB25: max chunk wall <= 30 s and max case wall <= 600 s on every record;
  GS_ref: REFERENCE_051 on block main: sha bound, 0 mismatches, complete (12-state records within 2400 s; each decided scale20
     record within its own 1800 s), 20/20 mutations; G_sound; G_recount;
  GTI: SEEDCHECK_051 PASS and its sha frozen in BRUTE_SOURCE_FREEZE_051;  GTEST: the gated test modules of TEST_SUITE_051 pass;
  G_PROC: preregistration, build_authorization, seedcheck, prefreeze_smoke, source_freeze, run_start, run_end, recount, reference,
     api_checks, tests (all _051) as a subsequence, parseable non-decreasing note times, commit-order file, main sealed;
  G_RT: main elapsed <= 3600 s.
  Secondary (reported): GS20_rate51, GS20_vs50, GRATE51, GN12_rate, GCOST51.
  PYTHONPATH=. python scripts/make_gates_051.py [--study-dir D] [--check]"""
from __future__ import annotations
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common import load,dumps,write_new,check,sha
from experiments.brute_common_026 import wilson
from scripts.make_gates_034 import opt
from scripts.make_gates_043 import subseq

STUDY_DIR=ROOT/'results/study-051';S2=('API16S','API16S_b');E2=('API16E','API16E_b');N2=('API16N','API16N_b')
LABELS=('ID','IDF','AMB','WRONG','IDU');CAP_RT=3600;QB=30.0;CASE_B=600.0;PRIOR_050_S20=(1,24)
PROC_ORDER=tuple(e+'_051' for e in ('preregistration','build_authorization','seedcheck','prefreeze_smoke','source_freeze','run_start','run_end',
                                    'recount','reference','api_checks','tests'))


def ckey(c):return f"{c['block']}/{c['key']}/{c['seed']}"


def ledger():
    from datetime import datetime
    L=[json.loads(x) for x in (ROOT/'results/RESEARCH_LEDGER.jsonl').read_text().splitlines() if x.strip()]
    i0=next((i for i,e in enumerate(L) if e.get('event')=='preregistration_051'),None);out=[]
    for e in (L[i0:] if i0 is not None else []):
        try:t=datetime.fromisoformat(str(e.get('note',''))[:25])
        except ValueError:t=None
        out.append((e['event'],t))
        if e['event']==PROC_ORDER[-1]:break
    return out


def build(study=STUDY_DIR,expect=None):
    """expect: case counts {scale20, noise12, control, compat}; the plan's 12 / 12 / 6 / NCOMPAT unless a pre-freeze synthetic check patches it."""
    from brute.evaluation import no_time
    from experiments.brute_study_051 import canon16s,canon16e,canon16n,N12B,NCOMPAT
    study=Path(study);D=study/'main';Gt={};sec={}
    seal=opt(D/'SEAL.json');sci=opt(D/'SCIENTIFIC.json');res=opt(D/'RESULTS.json');rc=opt(D/'RECOUNT_051.json')
    ref=opt(D/'REFERENCE_051.json');ts=opt(study/'TEST_SUITE_051.json');order=opt(ROOT/'experiments/COMMIT_ORDER_051.json')
    api=opt(study/'API_CHECKS_051.json');fz=opt(ROOT/'experiments/BRUTE_SOURCE_FREEZE_051.json');sc=opt(ROOT/'results/diag-051/SEEDCHECK_051.json')
    rsha=sha(D/'RESULTS.json') if (D/'RESULTS.json').exists() else None
    sealed=(bool(seal) and res is not None and sci is not None and rsha==seal.get('results_sha256')
            and sha(D/'SCIENTIFIC.json')==seal.get('scientific_sha256') and no_time(res)==sci)
    E=dict(expect or {'scale20':12,'noise12':12,'control':6,'compat':NCOMPAT});nfid=E['scale20']+E['control']+E['noise12']
    n12b=(res or {}).get('n_noise12_b',N12B)
    allc=[c for c in (res or {}).get('cases',[]) if c['block']=='main'] if sealed else []
    comp=[c for c in (res or {}).get('cases',[]) if c['block']=='c'] if sealed else []
    G=lambda k:sorted([c for c in allc if c['key']==k],key=lambda c:c['seed'])
    s20=G('scale20');n12=G('noise12');ctl=G('control')
    arms_ok=(all(list(c['arms'])==list(S2) for c in s20)
             and all(list(c['arms'])==(list(N2) if i<n12b else ['API16N']) for i,c in enumerate(n12))
             and all(list(c['arms'])==list(E2) for c in ctl) and all(list(c['arms'])==['API16S_c'] for c in comp))
    complete=sealed and seal.get('complete') is True and len(s20)==E['scale20'] and len(n12)==E['noise12'] and len(ctl)==E['control'] and len(comp)==E['compat'] and len(allc)==nfid and arms_ok
    wb=None if complete else 'INCOMPLETE_INPUT (main missing, partial, missing arms or not matching its seal)'
    def gate(name,ok,obs,why=None):Gt[name]={'pass':bool(ok) and why is None,'observed':obs,**({'reason':why} if why else {})}
    pc=(rc or {}).get('per_case') or {}
    rc_bound=bool(rc) and rc.get('results_sha256')==rsha and rc.get('cases')==len((res or {}).get('cases',[]))
    rc_ok=rc_bound and rc.get('PASS') is True and rc.get('mismatching_cases')==0
    lab=(lambda c,a:((pc.get(ckey(c)) or {}).get(a) or {}).get('label')) if rc_ok else (lambda c,a:c['arms'][a]['label'])
    lsrc='recount' if rc_ok else 'study labels (G_recount did not pass)'
    dd=lambda c,a:a in c['arms'] and lab(c,a) in ('ID','IDF')
    ci=lambda x,n:wilson(x,n) if n else None
    every=allc+comp
    # GDET51
    det=[[c['key'],c['seed'],canon16s(c['arms']['API16S'])==canon16s(c['arms']['API16S_b']),c['arms']['API16S']['label'],c['arms']['API16S_b']['label']]
         for c in s20 if 'API16S_b' in c['arms']]
    det+=[[c['key'],c['seed'],canon16e(c['arms']['API16E'])==canon16e(c['arms']['API16E_b']),c['arms']['API16E']['label'],c['arms']['API16E_b']['label']]
         for c in ctl if 'API16E_b' in c['arms']]
    det+=[[c['key'],c['seed'],canon16n(c['arms']['API16N'])==canon16n(c['arms']['API16N_b']),c['arms']['API16N']['label'],c['arms']['API16N_b']['label']]
          for c in n12[:n12b] if 'API16N_b' in c['arms']]
    guards=[[ckey(c),an,ar.get('guard_events')] for c in every for an,ar in c['arms'].items() if ar.get('wall_guard')]
    nd=sum(x[2] for x in det);ndet=E['scale20']+E['control']+min(n12b,E['noise12'])
    gate('GDET51',complete and len(det)==ndet and nd==ndet and not guards,{'identical':nd,'of':len(det),'ci95':ci(nd,len(det)),
         'scale20':[sum(x[2] for x in det if x[0]=='scale20'),E['scale20']],'control':[sum(x[2] for x in det if x[0]=='control'),E['control']],
         'noise12':[sum(x[2] for x in det if x[0]=='noise12'),n12b],'wall_guard_fired':guards,'records_checked_for_guard':sum(len(c['arms']) for c in every),
         'per_case':det,'columns':['key','seed','canon_equal','pass1','pass2'],
         'rule':'canon16s identical (scale20 12), canon16e identical (control 6), canon16n identical (noise12 N12B); wall_guard 0 on every record'},why=wb)
    # GFID51
    fi=(api or {}).get('fidelity') or {}
    fi_ok=bool(fi) and fi.get('study_results_sha256')==rsha and fi.get('PASS') is True and fi.get('exact')==fi.get('cases')==nfid
    gate('GFID51',complete and fi_ok,{'exact':fi.get('exact'),'of':fi.get('cases'),'expected':nfid,'ci95':ci(fi.get('exact') or 0,fi.get('cases') or 0),
         'per_key':fi.get('per_key'),'exact_per_arm':fi.get('exact_per_arm'),'bound':bool(fi) and fi.get('study_results_sha256')==rsha,
         'failures':{k:v for k,v in (fi.get('per_case') or {}).items() if not v['exact']}},
         why=wb or (None if fi else 'INCOMPLETE_INPUT (API_CHECKS_051 fidelity missing)'))
    wrong=[[ckey(c),a] for c in every for a in c['arms'] if lab(c,a)=='WRONG' or c['arms'][a]['label']=='WRONG']
    # GS20_sound51
    w20=[x for x in wrong if x[0].startswith('main/scale20/')];dec=[(c,a) for c in s20 for a in S2 if a in c['arms'] and c['arms'][a]['stop']!='unknown']
    ab=((ref or {}).get('per_key') or {}).get('scale20') or {};rb=bool(ref) and ref.get('study_results_sha256')==rsha
    ok20=rb and ref.get('complete') is True and ab.get('audited')==ab.get('decided')==len(dec) and not ab.get('mismatches')
    x20=sum(dd(c,'API16S') for c in s20)
    gate('GS20_sound51',complete and not w20 and ok20 and x20>=1,{'WRONG':w20,'decided_records':len(dec),'API16S_ID_IDF':x20,'of':len(s20),
         'ci95':ci(x20,len(s20)),'non_vacuous':x20>=1,'reference_scale20':ab,'reference_bound':rb,
         'per_case':[[c['seed'],lab(c,'API16S'),c['arms']['API16S']['stop'],c['arms']['API16S']['conflicts_spent'],lab(c,'API16S_b') if 'API16S_b' in c['arms'] else None] for c in s20],
         'rule':'scale20 WRONG 0; every decided scale20 record audited at bound 20 with 0 mismatches; >= 1/12 API16S decided (0 decided FAILS)',
         'label_source':lsrc},why=wb or (None if ref else 'INCOMPLETE_INPUT (REFERENCE_051 missing)'))
    # GN12_sound51
    wn=[x for x in wrong if x[0].startswith('main/noise12/')];xn=sum(dd(c,'API16N') for c in n12)
    an=((ref or {}).get('per_key') or {}).get('noise12') or {}
    gate('GN12_sound51',complete and not wn,{'WRONG':wn,'records':sum(len(c['arms']) for c in n12),'API16N_ID_IDF':xn,'of':len(n12),'ci95':ci(xn,len(n12)),
         'majority_errors':(rc or {}).get('majority_errors'),'reference_noise12':an,
         'per_case':[[c['seed'],lab(c,'API16N'),c['arms']['API16N']['stop'],c['arms']['API16N'].get('reads_total'),c['arms']['API16N'].get('majority_errors'),
                      lab(c,'API16N_b') if 'API16N_b' in c['arms'] else None] for c in n12],
         'model_bound':'P(any WRONG over 24 records) <= 24 x 0.001 = 0.024 (Exact, conditional on the iid model)','label_source':lsrc},why=wb)
    # GCOMPAT16S
    cp=(rc or {}).get('compat') or {};ce=[[c['seed'],bool((cp.get(ckey(c)) or {}).get('equal')),(cp.get(ckey(c)) or {}).get('label'),(cp.get(ckey(c)) or {}).get('control_label'),
        (cp.get(ckey(c)) or {}).get('machine_equal')] for c in comp];nce=sum(x[1] for x in ce)
    gate('GCOMPAT16S',complete and rc_ok and nce==len(ce)==E['compat'],{'equal':nce,'of':len(ce),'ci95':ci(nce,len(ce)),'per_case':ce,
         'columns':['seed','equal','label_16s_c','label_16e_k','machine_equal'],
         'rule':'part c (certify/16s at bound 12) label equal to the part-k API16E record and, for ID / IDF, the same machine in canonical BFS form; from RECOUNT_051'},
         why=wb or (None if rc_ok else 'G_recount did not pass'))
    # GHOST51
    cs_sha=(fz or {}).get('sha256_files',{}).get('brute/api/certify16s.py')
    abound=bool(api) and cs_sha is not None and api.get('certify16s_sha256')==cs_sha==sha(ROOT/'brute/api/certify16s.py')
    ag=(api or {}).get('ghost') or {}
    gate('GHOST51',abound and ag.get('PASS51') is True,None if not api else {'bound_to_freeze_051':abound,'frozen_api_unchanged':ag.get('frozen_api_unchanged'),
         'closures_unchanged':ag.get('closures_unchanged'),'newly_imported_vs_certify16e':ag.get('newly_imported'),'new_flagged':ag.get('new_flagged'),
         'socket_attempts':ag.get('socket_attempts'),'no_network_run':ag.get('no_network_run')},why=None if api else 'INCOMPLETE_INPUT (API_CHECKS_051 missing)')
    # G10
    g10=[(c['seed'],{a:lab(c,a) for a in E2}) for c in ctl]
    gate('G10',complete and len(g10)==E['control'] and all(all(L=='ID' for L in x[1].values()) for x in g10),{'cases':g10},why=wb)
    # GQB25 + cost
    mx={};mxc={};over=[];over_c=[];cost={};rate={}
    for c in every:
        for a,ar in c['arms'].items():
            p=f"{a}/{c['block']}/{c['key']}"
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
            cc=[t for r in ar['rounds'] for y in r.get('chunk_conflicts',[]) for t in y];aw=ar.get('arm_wall_informational') or 0.0
            y=rate.setdefault(p,{'records':0,'conflicts':0,'arm_wall_s':0.0,'chunk_conflicts':0,'chunk_wall_s':0.0,'per_record':[]})
            y['records']+=1;y['conflicts']+=ar.get('conflicts_spent') or 0;y['arm_wall_s']+=aw;y['chunk_conflicts']+=sum(cc);y['chunk_wall_s']+=sum(cw)
            y['per_record'].append([ckey(c),round((ar.get('conflicts_spent') or 0)/aw,1) if aw else None])
    for x in cost.values():x['arm_wall_s']=round(x['arm_wall_s'],1)
    gate('GQB25',complete and bool(mx) and not over and not over_c,{'max_chunk_wall_s':{k:round(v,3) for k,v in sorted(mx.items())},
         'max_case_wall_s':{k:round(v,3) for k,v in sorted(mxc.items())},'chunk_bound_s':QB,'case_bound_s':CASE_B,'over_chunk':over,'over_case':over_c},why=wb)
    # GS_ref
    mt=(ref or {}).get('mutation_test') or {};rb=bool(ref) and ref.get('study_results_sha256')==rsha and ref.get('block')=='main'
    robs=None if not ref else {k:ref.get(k) for k in ('block','scope','records','decided','audited','not_audited','complete','per_arm','per_key','not_reached',
                               'k_spent_as_amb','verdicts_checked','mismatch_count','vacuous','PASS','elapsed_informational')}|{'mutations':mt.get('detected'),'of':mt.get('mutations')}
    gate('GS_ref',rb and ref.get('mismatch_count')==0 and ref.get('complete') is True and (ref.get('scope') or {}).get('budget_12_s')==2400.0 and (ref.get('scope') or {}).get('budget_20_s_per_record')==1800.0
         and mt.get('detected')==mt.get('mutations')==20 and ref.get('PASS') is True,robs,why=wb or (None if ref else 'INCOMPLETE_INPUT (REFERENCE_051 missing)'))
    # G_sound / G_recount
    snd={'words_checked':sum(ar.get('words_checked',0) for c in every for ar in c['arms'].values()),
         'words_unsound':sum(ar.get('words_unsound',0) for c in every for ar in c['arms'].values()),
         'recount_bound':rc_bound,'recount_words_checked':(rc or {}).get('words_checked'),'recount_words_unsound':(rc or {}).get('words_unsound'),
         'recount_truth_inconsistent':(rc or {}).get('truth_inconsistent')}
    gate('G_sound',complete and rc_bound and snd['words_unsound']==0 and snd['recount_words_unsound']==0 and snd['recount_words_checked']==snd['words_checked'],
         snd,why=wb or (None if rc_bound else 'INCOMPLETE_INPUT (RECOUNT_051 missing or unbound)'))
    gate('G_recount',complete and rc_ok,None if not rc else {k:rc.get(k) for k in ('cases','recounted','labels','labels_c','compat_equal','majority_errors','misfires',
         'amb_rule_applied','words_checked','words_unsound','truth_inconsistent','mismatching_cases','mismatches','PASS')},
         why=wb or (None if rc else 'INCOMPLETE_INPUT (RECOUNT_051 missing)'))
    # GTI (plan wording) and GTEST (#173)
    sc_frozen=bool(sc) and (fz or {}).get('sha256_files',{}).get('results/diag-051/SEEDCHECK_051.json')==sha(ROOT/'results/diag-051/SEEDCHECK_051.json')
    gate('GTI',bool(sc) and sc.get('PASS') is True and sc_frozen,None if not sc else {'seedcheck_pass':sc.get('PASS'),'frozen_in_051':sc_frozen,
         'total_cases':sc.get('total_cases'),'prior_range_count':sc.get('prior_range_count'),'all_tokens_allowed':sc.get('all_tokens_allowed')},
         why=None if sc else 'INCOMPLETE_INPUT (SEEDCHECK_051 missing)')
    mods=(ts or {}).get('per_module') or {};gm=(ts or {}).get('gated_modules') or []
    gate('GTEST',bool(gm) and ts.get('passed') is True and all(mods[m].get('returncode')==0 for m in gm),
         None if not ts else {'gated':{m:{'returncode':mods[m].get('returncode'),'tests':mods[m].get('tests')} for m in gm},
                              'reported':{m:{'returncode':v.get('returncode'),'tests':v.get('tests')} for m,v in mods.items() if m not in gm}},
         why=None if ts else 'INCOMPLETE_INPUT (TEST_SUITE_051 missing)')
    lt=ledger();ev=[e for e,_ in lt];times=[t for _,t in lt]
    proc={'order':subseq(ev,PROC_ORDER),'ledger_times_parse':bool(lt) and all(t is not None for t in times),
          'ledger_times_non_decreasing':all(a<=b for a,b in zip(times,times[1:]) if a and b),'commit_order_file':order is not None,'main_sealed':bool(sealed)}
    gate('G_PROC',all(proc.values()),{'clauses':proc,'events':ev,'required_order':list(PROC_ORDER)})
    el=(res or {}).get('total_elapsed_informational')
    gate('G_RT',complete and el is not None and el<=CAP_RT,{'elapsed_s':el,'cap_s':CAP_RT,'cases':len(allc),'compat':len(comp),'n_noise12_b':n12b,'phase_a_elapsed_informational':(res or {}).get('phase_a_elapsed_informational'),'phase_b_elapsed_informational':(res or {}).get('phase_b_elapsed_informational')},why=wb)
    # secondary
    sec['GCOST51']={'pass':None,'observed':dict(sorted(cost.items())),'rule':'reported: wall, calls, chunks, capped calls, conflicts, budget-spent records, reads per arm/block/key'}
    for y in rate.values():
        y['conflicts_per_s_record']=round(y['conflicts']/y['arm_wall_s'],1) if y['arm_wall_s'] else None
        y['conflicts_per_s_chunk']=round(y['chunk_conflicts']/y['chunk_wall_s'],1) if y['chunk_wall_s'] else None
        y['arm_wall_s']=round(y['arm_wall_s'],1);y['chunk_wall_s']=round(y['chunk_wall_s'],1)
    sec['GRATE51']={'pass':None,'observed':dict(sorted(rate.items())),'rule':'reported: conflicts per second per record (arm wall) and per chunk (chunk walls), per arm/block/key; informational timing'}
    sec['GS20_rate51']={'pass':None,'observed':{'ID_IDF':x20,'of':len(s20),'ci95':ci(x20,len(s20)),'cost':{k:v for k,v in cost.items() if k.endswith('/main/scale20')}},'rule':'reported'}
    rp=[c['arms']['API16N'].get('reads_total') or 0 for c in n12];ob=[len(c['arms']['API16N'].get('reads_per_obs') or []) for c in n12]
    sec['GN12_rate']={'pass':None,'observed':{'ID_IDF':xn,'of':len(n12),'ci95':ci(xn,len(n12)),'reads_total':sum(rp),'observations':sum(ob),
                      'reads_per_observation':round(sum(rp)/sum(ob),2) if sum(ob) else None,
                      'k_range':[min((min(c['arms']['API16N']['reads_per_obs']) for c in n12),default=None),max((c['arms']['API16N'].get('reads_max') or 0 for c in n12),default=None)]},'rule':'reported'}
    sec['GS20_vs50']={'pass':None,'observed':{'051_API16S_ID_IDF':[x20,len(s20)],'051_ci95':ci(x20,len(s20)),'050_API16E_B20_4000000':list(PRIOR_050_S20),'050_ci95':wilson(*PRIOR_050_S20)},
                      'rule':'reported: certify/16s scale20 decided rate at C20 12000 / B20 2000000 beside 050 certify/16e (1/24 at 4000000)'}
    cnt=lambda k,a,L:sum(lab(c,a)==L for c in G(k) if a in c['arms']);nk=lambda k,a:sum(a in c['arms'] for c in G(k))
    fl={f'{a}/{k}':{L:{'x':cnt(k,a,L),'n':nk(k,a),'ci95':ci(cnt(k,a,L),nk(k,a))} for L in LABELS} for k,arms in (('scale20',S2),('control',E2),('noise12',N2),) for a in arms}
    return {'schema':'brute.gates.v48_0','study':(res or {}).get('plan',{}).get('study'),'process':'lean','sealed_input_verified':sealed,'label_source':lsrc,
            'n_noise12_b':n12b,'n_compat':len(comp),'caps':(res or {}).get('caps'),'workers':(res or {}).get('workers'),'conflict_cap':(res or {}).get('conflict_cap'),'budget_conflicts':(res or {}).get('budget_conflicts'),
            'noise':(res or {}).get('noise'),'gates':Gt,'secondary':sec,
            'all_gated_pass':all(g['pass'] for g in Gt.values()),'failed':[k for k,g in Gt.items() if g['pass'] is False],'not_exercised':[],
            'claim':('certify/16s and certify/16e ID/IDF is exact conditional on noise-free readings and true size <= the declared N (family_bound); certify/16n ID/IDF is exact '
                     'conditional on every majority being correct (probability >= 1 - delta under iid flips with eps <= eps_bar) and true size <= N'),
            'reports':{'labels':fl} if allc else {}}


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--study-dir',default=str(STUDY_DIR));ap.add_argument('--check',action='store_true');a=ap.parse_args()
    obj=build(Path(a.study_dir));out=Path(a.study_dir)/'GATES_051.json'
    if a.check:check(out.read_bytes()==dumps(obj),'GATES_051.json does not reproduce');print('GATES_051 reproduces')
    else:write_new(out,obj);print(json.dumps({k:v['pass'] for k,v in obj['gates'].items()}),obj['failed'])
