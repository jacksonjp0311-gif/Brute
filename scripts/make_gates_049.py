"""Gates for study-049 (BRUTE_PLAN_049 criteria; pre-run deviation #171 definitions), LEAN process. Committed in the source freeze
before run_start_049; nothing is tuned after results are seen. New file; built from scripts/make_gates_048.py (frozen).
Inputs (D = results/study-049): D/main/{RESULTS,SCIENTIFIC,SEAL}.json (part r: API16E on 26 sealed 048 traces, 18 if the cut drops
r scale20; part c: API16E_c1 on the 26 sealed 048 traces; fresh cases scale16 12, control 6, scale20 N20, arms API16E and
API16E_b), D/main/RECOUNT_049.json, D/main/REFERENCE_049.json, D/API_CHECKS_049.json, D/TEST_SUITE_049.json,
experiments/COMMIT_ORDER_049.json, results/RESEARCH_LEDGER.jsonl. Missing or partial input => every data gate FAIL
INCOMPLETE_INPUT. Records are accepted only if sha256(RESULTS) equals the seal and no_time(RESULTS) equals SCIENTIFIC. Labels:
recounted if G_recount passes, else the study's (stated).
  GDET49: canon16e(API16E) == canon16e(API16E_b) on 18/18 fresh scale16+control and N20/N20 scale20, AND wall_guard 0 on every
     certify/16e record (parts a, d, r and c);
  GFID49: API_CHECKS_049 fidelity exact on 18 + N20 API16E records, bound to the sealed RESULTS sha;
  GCOMPAT16D: part c canon16d equal to the sealed 048 API16D record on 26/26 (recount comparison);
  GAPI16E_fresh49: scale16 WRONG 0 (either arm) and API16E ID+IDF >= 7/12 (Wilson 95% CI); a budget-spent IDU is not WRONG;
  GS20_sound49: scale20 WRONG 0 (both arms) and every decided scale20 record audited at bound 20 by REFERENCE_049 with 0
     mismatches; 'vacuous' if 0 decided (a vacuous pass carries no N <= 20 claim); pass None ('not run') if N20 = 0;
  GR49_sound: part r: 0 contradictions with the sealed 048 decided records (recount_049 rule) and WRONG 0;
  GHOST49: API_CHECKS_049 ghost PASS49, bound to certify16e.py's sha in the 049 freeze;  G10: both arms ID on the 6 controls;
  GQB24: max chunk wall <= 30 s and max case wall <= 600 s on every certify/16e record; chunks and capped calls reported;
  GS_ref: REFERENCE_049 on block main: sha bound, 0 mismatches, complete within 2400 s, 20/20 mutations; G_sound; G_recount; GTI;
  G_PROC: preregistration, build_authorization, seedcheck, source_freeze, run_start, run_end (all _049) as a subsequence,
     parseable non-decreasing note times, commit-order file, main sealed;  G_RT: main elapsed <= 3600 s.
  Secondary (reported): GS20_rate49, GREP16f, GR_gain, GCOST49.
  PYTHONPATH=. python scripts/make_gates_049.py [--study-dir D] [--check]"""
from __future__ import annotations
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common import load,dumps,write_new,check,sha
from experiments.brute_common_026 import wilson
from scripts.make_gates_034 import opt
from scripts.make_gates_043 import subseq

STUDY_DIR=ROOT/'results/study-049';D_ARMS=('API16E','API16E_b')
LABELS=('ID','IDF','AMB','WRONG','IDU');CLASSES=('none','cap-timing','word-divergence','infidelity')
CAP_RT=3600;QB=30.0;CASE_B=600.0;FRESH_BAR=7;GREP_047=(10,12);GREP_048=(0,12)
PROC_ORDER=tuple(e+'_049' for e in ('preregistration','build_authorization','seedcheck','source_freeze','run_start','run_end'))


def ckey(c):return f"{c['block']}/{c['key']}/{c['seed']}"


def ledger():
    from datetime import datetime
    L=[json.loads(x) for x in (ROOT/'results/RESEARCH_LEDGER.jsonl').read_text().splitlines() if x.strip()]
    i0=next((i for i,e in enumerate(L) if e.get('event')=='preregistration_049'),None);out=[]
    for e in (L[i0:] if i0 is not None else []):
        try:t=datetime.fromisoformat(str(e.get('note',''))[:25])
        except ValueError:t=None
        out.append((e['event'],t))
        if e['event']==PROC_ORDER[-1]:break
    return out


def _part(c):return c['block'] if c['block'] in ('r','c') else ('d' if c['key']=='scale20' else 'a')


def build(study=STUDY_DIR,fresh=None,n_rep=None,n_compat=None):
    from brute.evaluation import no_time
    from experiments.brute_study_049 import canon16e,N20,R20
    study=Path(study);D=study/'main';Gt={};sec={}
    seal=opt(D/'SEAL.json');sci=opt(D/'SCIENTIFIC.json');res=opt(D/'RESULTS.json');rc=opt(D/'RECOUNT_049.json')
    ref=opt(D/'REFERENCE_049.json');ts=opt(study/'TEST_SUITE_049.json');order=opt(ROOT/'experiments/COMMIT_ORDER_049.json')
    api=opt(study/'API_CHECKS_049.json');fz=opt(ROOT/'experiments/BRUTE_SOURCE_FREEZE_049.json')
    rsha=sha(D/'RESULTS.json') if (D/'RESULTS.json').exists() else None
    sealed=(bool(seal) and res is not None and sci is not None and rsha==seal.get('results_sha256')
            and sha(D/'SCIENTIFIC.json')==seal.get('scientific_sha256') and no_time(res)==sci)
    n20=(res or {}).get('n_scale20',N20);r20=(res or {}).get('r_scale20',R20)
    fresh=dict(fresh or {'scale16':12,'control':6,'scale20':n20});n_rep=(26 if r20 else 18) if n_rep is None else n_rep
    n_compat=26 if n_compat is None else n_compat
    if not fresh.get('scale20'):fresh.pop('scale20',None)
    allc=[c for c in (res or {}).get('cases',[]) if c['block']=='main'] if sealed else []
    reps=[r for r in (res or {}).get('replays',[]) if r['block']=='r'] if sealed else []
    comp=[r for r in (res or {}).get('replays',[]) if r['block']=='c'] if sealed else []
    G=lambda k:sorted([c for c in allc if c['key']==k],key=lambda c:c['seed'])
    sc16=G('scale16');s20=G('scale20')
    complete=(sealed and seal.get('complete') is True and all(len(G(k))==n for k,n in fresh.items()) and len(allc)==sum(fresh.values())
              and all(list(c['arms'])==list(D_ARMS) for c in allc) and len(reps)==n_rep and all(list(c['arms'])==['API16E'] for c in reps)
              and len(comp)==n_compat and all(list(c['arms'])==['API16E_c1'] for c in comp))
    wb=None if complete else 'INCOMPLETE_INPUT (main missing, partial, missing arms or not matching its seal)'
    def gate(name,ok,obs,why=None,na=False):Gt[name]={'pass':None if na else (bool(ok) and why is None),'observed':obs,**({'reason':why} if why else {})}
    pc=(rc or {}).get('per_case') or {};rcmp=(rc or {}).get('replay_compare') or {}
    rc_bound=bool(rc) and rc.get('results_sha256')==rsha and rc.get('cases')==len((res or {}).get('cases',[])) and rc.get('replays')==len((res or {}).get('replays',[]))
    rc_ok=rc_bound and rc.get('PASS') is True and rc.get('mismatching_cases')==0
    rrec=lambda c,a:((pc.get(ckey(c)) or {}).get(a) or {}) if rc_bound else {}
    prc=(rc or {}).get('per_replay') or {}
    lab=(lambda c,a:(rrec(c,a) if c['block']=='main' else ((prc.get(ckey(c)) or {}).get(a) or {})).get('label')) if rc_ok else (lambda c,a:c['arms'][a]['label'])
    lsrc='recount' if rc_ok else 'study labels (G_recount did not pass)'
    dd=lambda c,a:a in c['arms'] and lab(c,a) in ('ID','IDF')
    ci=lambda x,n:wilson(x,n) if n else None
    cmp_=(lambda c:rcmp.get(ckey(c)) or {}) if rc_ok else (lambda c:c.get('replay') or {})
    every=allc+reps+comp
    # GDET49
    det=[[c['key'],c['seed'],canon16e(c['arms']['API16E'])==canon16e(c['arms']['API16E_b']),c['arms']['API16E']['label'],c['arms']['API16E_b']['label']]
         for c in sc16+G('control')+s20]
    guards=[[ckey(c),an,ar.get('guard_events')] for c in every for an,ar in c['arms'].items() if ar.get('wall_guard')]
    nd=sum(x[2] for x in det);ndet=18+fresh.get('scale20',0)
    d16=sum(x[2] for x in det if x[0]!='scale20');d20=sum(x[2] for x in det if x[0]=='scale20')
    gate('GDET49',complete and len(det)==ndet and nd==ndet and not guards,{'identical':nd,'of':len(det),'ci95':ci(nd,len(det)),
         'scale16_control':[d16,18],'scale20':[d20,fresh.get('scale20',0)],'wall_guard_fired':guards,'records_checked_for_guard':sum(len(c['arms']) for c in every),
         'per_case':det,'columns':['key','seed','canon16e_equal','API16E','API16E_b'],
         'rule':'canon16e identical on 18/18 and N20/N20; wall_guard 0 on every certify/16e record (a, d, r, c)'},why=wb)
    # GFID49
    fi=(api or {}).get('fidelity') or {}
    fi_ok=bool(fi) and fi.get('study_results_sha256')==rsha and fi.get('PASS') is True and fi.get('exact')==fi.get('cases')==ndet
    gate('GFID49',complete and fi_ok,{'exact':fi.get('exact'),'of':fi.get('cases'),'expected':ndet,'ci95':ci(fi.get('exact') or 0,fi.get('cases') or 0),
         'per_key':fi.get('per_key'),'bound':bool(fi) and fi.get('study_results_sha256')==rsha,'failures':{k:v for k,v in (fi.get('per_case') or {}).items() if not v['exact']}},
         why=wb or (None if fi else 'INCOMPLETE_INPUT (API_CHECKS_049 fidelity missing)'))
    # GCOMPAT16D
    ce=[[c['key'],c['seed'],bool(cmp_(c).get('canon16d_equal')),cmp_(c).get('label')] for c in comp];nce=sum(x[2] for x in ce)
    gate('GCOMPAT16D',complete and rc_ok and nce==len(ce)==n_compat,{'equal':nce,'of':len(ce),'ci95':ci(nce,len(ce)),'per_case':ce,
         'rule':'part c (max_chunks 1) canon16d byte-identical to the sealed 048 API16D record on 26/26; comparison from RECOUNT_049'},
         why=wb or (None if rc_ok else 'G_recount did not pass (comparison not independently confirmed)'))
    # GAPI16E_fresh49
    wrong=[[ckey(c),a] for c in every for a in c['arms'] if lab(c,a)=='WRONG' or c['arms'][a]['label']=='WRONG']
    w16=[x for x in wrong if x[0].startswith('main/scale16/')];x16=sum(dd(c,'API16E') for c in sc16)
    gate('GAPI16E_fresh49',complete and len(sc16)==12 and not w16 and x16>=FRESH_BAR,{'WRONG':w16,'ID_IDF':x16,'of':len(sc16),'bar':FRESH_BAR,'ci95':ci(x16,len(sc16)),
         'API16E_b_ID_IDF':sum(dd(c,'API16E_b') for c in sc16),
         'per_case':[[c['seed'],lab(c,'API16E'),c['arms']['API16E']['stop'],c['arms']['API16E']['conflicts_spent'],c['arms']['API16E'].get('chunks_total')] for c in sc16],
         'budget_spent_cases':sum((c['arms']['API16E'].get('conflicts_spent') or 0)>=c['arms']['API16E']['budget_conflicts'] for c in sc16),
         'label_source':lsrc},why=wb)
    # GS20_sound49
    if not fresh.get('scale20'):gate('GS20_sound49',False,{'n_scale20':0,'note':'part d dropped under the declared cut rule'},na=True)
    else:
        w20=[x for x in wrong if x[0].startswith('main/scale20/')];dec=[(c,a) for c in s20 for a in D_ARMS if c['arms'][a]['stop']!='unknown']
        ab=((ref or {}).get('per_key') or {}).get('scale20') or {};rb=bool(ref) and ref.get('study_results_sha256')==rsha
        ok20=rb and ref.get('complete') is True and ab.get('audited')==ab.get('decided')==len(dec) and not ab.get('mismatches')
        x20=sum(dd(c,'API16E') for c in s20)
        gate('GS20_sound49',complete and len(s20)==fresh['scale20'] and not w20 and ok20,{'WRONG':w20,'decided_records':len(dec),'vacuous':len(dec)==0,
             'API16E_ID_IDF':x20,'of':len(s20),'ci95':ci(x20,len(s20)),'reference_scale20':ab,'reference_bound':rb,
             'per_case':[[c['seed'],lab(c,'API16E'),c['arms']['API16E']['stop'],lab(c,'API16E_b')] for c in s20],
             'rule':'scale20 WRONG 0; every decided scale20 record audited at bound 20 with 0 mismatches; a pass with 0 decided is vacuous and carries no N <= 20 claim'},
             why=wb or (None if ref else 'INCOMPLETE_INPUT (REFERENCE_049 missing)'))
    # GR49_sound
    wr=[x for x in wrong if x[0].startswith('r/')];con=[[c['key'],c['seed'],cmp_(c).get('label')] for c in reps if cmp_(c).get('contradiction')]
    gate('GR49_sound',complete and rc_ok and not wr and not con,{'WRONG':wr,'contradictions':con,'n':len(reps),
         'per_case':[[c['key'],c['seed'],cmp_(c).get('label'),cmp_(c).get('class'),cmp_(c).get('contradiction')] for c in reps],
         'rule':'no part-r decided record contradicts a sealed 048 decided record (recount_049 rule); WRONG 0'},
         why=wb or (None if rc_ok else 'G_recount did not pass'))
    # GHOST49
    ce_sha=(fz or {}).get('sha256_files',{}).get('brute/api/certify16e.py')
    abound=bool(api) and ce_sha is not None and api.get('certify16e_sha256')==ce_sha==sha(ROOT/'brute/api/certify16e.py')
    ag=(api or {}).get('ghost') or {}
    gate('GHOST49',abound and ag.get('PASS49') is True,None if not api else {'bound_to_freeze_049':abound,'frozen_api_unchanged':ag.get('frozen_api_unchanged'),
         'certify16d_closure_unchanged':ag.get('certify16d_closure_unchanged'),'newly_imported_vs_certify16d':ag.get('newly_imported'),'new_flagged':ag.get('new_flagged'),
         'socket_attempts':ag.get('socket_attempts'),'no_network_run':ag.get('no_network_run')},why=None if api else 'INCOMPLETE_INPUT (API_CHECKS_049 missing)')
    # G10
    g10=[(c['seed'],{a:lab(c,a) for a in D_ARMS}) for c in G('control')]
    gate('G10',complete and len(g10)==6 and all(all(L=='ID' for L in x[1].values()) for x in g10),{'cases':g10},why=wb)
    # GQB24
    mx={};mxc={};over=[];over_c=[];conf={}
    for c in every:
        part=_part(c)
        for a,ar in c['arms'].items():
            cw=[t for r in ar['rounds'] for x in r.get('chunk_walls_informational',[]) for t in x];cs=ar.get('case_wall_informational')
            if cw:mx[part]=max(mx.get(part,0),max(cw))
            if cs is not None:mxc[part]=max(mxc.get(part,0),cs)
            over+=[[f'{ckey(c)}/{a}',round(t,3)] for t in cw if t>QB]
            if cs is None or cs>CASE_B:over_c.append([f'{ckey(c)}/{a}',cs])
            ch=[v for r in ar['rounds'] for v in r.get('call_chunks',[])];cc=[v for r in ar['rounds'] for v in r.get('call_conflicts',[])]
            y=conf.setdefault(part,{'records':0,'calls':0,'chunks':0,'max_chunks_per_call':0,'max_call_conflicts':0,'capped_calls':0,'spent':0,'budget_spent_records':0})
            y['records']+=1;y['calls']+=len(cc);y['chunks']+=sum(ch);y['max_chunks_per_call']=max([y['max_chunks_per_call']]+ch);y['max_call_conflicts']=max([y['max_call_conflicts']]+cc)
            y['capped_calls']+=sum(bool(v) for r in ar['rounds'] for v in r.get('call_capped',[]));y['spent']+=ar.get('conflicts_spent') or 0
            y['budget_spent_records']+=(ar.get('conflicts_spent') or 0)>=ar['budget_conflicts']
    gate('GQB24',complete and bool(mx) and not over and not over_c,{'max_chunk_wall_s_by_part':{k:round(v,3) for k,v in sorted(mx.items())},
         'max_case_wall_s_by_part':{k:round(v,3) for k,v in sorted(mxc.items())},'chunk_bound_s':QB,'case_bound_s':CASE_B,'over_chunk':over,'over_case':over_c,
         'chunks_by_part':conf},why=wb)
    # GS_ref
    mt=(ref or {}).get('mutation_test') or {};rb=bool(ref) and ref.get('study_results_sha256')==rsha and ref.get('block')=='main'
    robs=None if not ref else {k:ref.get(k) for k in ('block','scope','records','decided','audited','not_audited','complete','per_arm','per_key','not_reached',
                               'k_spent_as_amb','verdicts_checked','mismatch_count','vacuous','PASS','elapsed_informational')}|{'mutations':mt.get('detected'),'of':mt.get('mutations')}
    gate('GS_ref',rb and ref.get('mismatch_count')==0 and ref.get('complete') is True and (ref.get('scope') or {}).get('budget_s')==2400.0
         and mt.get('detected')==mt.get('mutations')==20 and ref.get('PASS') is True,robs,why=wb or (None if ref else 'INCOMPLETE_INPUT (REFERENCE_049 missing)'))
    # G_sound / G_recount
    snd={'words_checked':sum(ar.get('words_checked',0) for c in every for ar in c['arms'].values()),
         'words_unsound':sum(ar.get('words_unsound',0) for c in every for ar in c['arms'].values()),
         'recount_bound':rc_bound,'recount_words_checked':(rc or {}).get('words_checked'),'recount_words_unsound':(rc or {}).get('words_unsound'),
         'recount_truth_inconsistent':(rc or {}).get('truth_inconsistent')}
    gate('G_sound',complete and rc_bound and snd['words_unsound']==0 and snd['recount_words_unsound']==0 and snd['recount_truth_inconsistent']==0
         and snd['recount_words_checked']==snd['words_checked'],snd,why=wb or (None if rc_bound else 'INCOMPLETE_INPUT (RECOUNT_049 missing or unbound)'))
    gate('G_recount',complete and rc_ok,None if not rc else {k:rc.get(k) for k in ('cases','replays','labels_main','labels_scale16_main','labels_control_main',
         'labels_scale20_main','labels_r','labels_c','part_r','part_c','misfires_main','replay_wrong','amb_rule_applied','words_checked','words_unsound','truth_inconsistent','mismatching_cases','PASS')},
         why=wb or (None if rc else 'INCOMPLETE_INPUT (RECOUNT_049 missing)'))
    mods=(ts or {}).get('per_module') or {};gm=(ts or {}).get('gated_modules') or []
    gate('GTI',bool(gm) and ts.get('passed') is True and all(mods[m].get('returncode')==0 for m in gm),
         None if not ts else {'gated':{m:{'returncode':mods[m].get('returncode'),'tests':mods[m].get('tests')} for m in gm},
                              'reported':{m:{'returncode':v.get('returncode'),'tests':v.get('tests')} for m,v in mods.items() if m not in gm}},
         why=None if ts else 'INCOMPLETE_INPUT (TEST_SUITE_049 missing)')
    lt=ledger();ev=[e for e,_ in lt];times=[t for _,t in lt]
    proc={'order':subseq(ev,PROC_ORDER),'ledger_times_parse':bool(lt) and all(t is not None for t in times),
          'ledger_times_non_decreasing':all(a<=b for a,b in zip(times,times[1:]) if a and b),'commit_order_file':order is not None,'main_sealed':bool(sealed)}
    gate('G_PROC',all(proc.values()),{'clauses':proc,'events':ev,'required_order':list(PROC_ORDER)})
    el=(res or {}).get('total_elapsed_informational')
    gate('G_RT',complete and el is not None and el<=CAP_RT,{'elapsed_s':el,'cap_s':CAP_RT,'cases':len(allc),'replays':len(reps),'compat':len(comp),'n_scale20':fresh.get('scale20',0),'r_scale20':r20},why=wb)
    # secondary
    cost={}
    for c in every:
        part=_part(c)
        for a,ar in c['arms'].items():
            x=cost.setdefault(f"{a}/{part}/{c['key']}",{'records':0,'arm_wall_s':0.0,'calls':0,'chunks':0,'capped_calls':0,'conflicts':0,'budget_spent':0})
            x['records']+=1;x['arm_wall_s']+=ar.get('arm_wall_informational') or ar.get('case_wall_informational') or 0.0;x['conflicts']+=ar.get('conflicts_spent') or 0
            x['calls']+=sum(len(r.get('call_conflicts',[])) for r in ar['rounds']);x['chunks']+=ar.get('chunks_total') or 0
            x['capped_calls']+=sum(bool(v) for r in ar['rounds'] for v in r.get('call_capped',[]))
            x['budget_spent']+=(ar.get('conflicts_spent') or 0)>=ar['budget_conflicts']
    for x in cost.values():x['arm_wall_s']=round(x['arm_wall_s'],1)
    sec['GCOST49']={'pass':None,'observed':dict(sorted(cost.items())),'rule':'reported: wall, calls, chunks, capped calls, conflicts, budget-spent records per arm/part/key'}
    sec['GREP16f']={'pass':None,'observed':{'API16E_ID_IDF':x16,'of':len(sc16),'ci95':ci(x16,len(sc16)),'prior_048_C50000_no_resume':list(GREP_048),
                    'prior_048_ci95':wilson(*GREP_048),'prior_047_C294000':list(GREP_047),'prior_047_ci95':wilson(*GREP_047)},
                    'rule':'reported: API16E scale16 ID+IDF beside 048 (0/12) and 047 (10/12)'}
    gk=lambda k:[c for c in reps if c['key']==k and cmp_(c).get('gain')]
    sec['GR_gain']={'pass':None,'observed':{'gain_by_key':{k:len(gk(k)) for k in ('scale16','control','scale20')},
                    'classes':{q:sum(cmp_(c).get('class')==q for c in reps) for q in CLASSES},'same':sum(bool(cmp_(c).get('same')) for c in reps),'n':len(reps),
                    'per_case':[[c['key'],c['seed'],cmp_(c).get('label'),cmp_(c).get('class'),cmp_(c).get('gain')] for c in reps]},
                    'rule':'reported: part r cases certify/16e decided where the sealed certify/16d record was IDU'}
    if fresh.get('scale20'):
        x20=sum(dd(c,'API16E') for c in s20)
        sec['GS20_rate49']={'pass':None,'observed':{'ID_IDF':x20,'of':len(s20),'ci95':ci(x20,len(s20)),'cost':{k:v for k,v in cost.items() if '/d/' in k}},'rule':'reported'}
    cnt=lambda k,a,L:sum(lab(c,a)==L for c in G(k));nk=lambda k:len(G(k))
    fl={f'{a}/{k}':{L:{'x':cnt(k,a,L),'n':nk(k),'ci95':ci(cnt(k,a,L),nk(k))} for L in LABELS} for k in fresh for a in D_ARMS}
    return {'schema':'brute.gates.v46_0','study':(res or {}).get('plan',{}).get('study'),'process':'lean','sealed_input_verified':sealed,'label_source':lsrc,
            'n_scale20':fresh.get('scale20',0),'r_scale20':r20,'conflict_cap':(res or {}).get('conflict_cap'),'budget_conflicts':(res or {}).get('budget_conflicts'),
            'max_chunks':(res or {}).get('max_chunks'),'gates':Gt,'secondary':sec,
            'all_gated_pass':all(g['pass'] for g in Gt.values() if g['pass'] is not None),
            'failed':[k for k,g in Gt.items() if g['pass'] is False],'not_exercised':[k for k,g in Gt.items() if g['pass'] is None],
            'claim':'certify/16e ID/IDF is exact conditional on noise-free readings and true size <= the declared N (family_bound)',
            'reports':{'fresh_labels':fl} if allc else {}}


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--study-dir',default=str(STUDY_DIR));ap.add_argument('--check',action='store_true');a=ap.parse_args()
    obj=build(Path(a.study_dir));out=Path(a.study_dir)/'GATES_049.json'
    if a.check:check(out.read_bytes()==dumps(obj),'GATES_049.json does not reproduce');print('GATES_049 reproduces')
    else:write_new(out,obj);print(json.dumps({k:v['pass'] for k,v in obj['gates'].items()}),obj['failed'])
