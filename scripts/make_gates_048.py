"""Gates for study-048 (BRUTE_PLAN_048 criteria; pre-run deviation #169 definitions), LEAN process. Committed in the source freeze
before run_start_048; nothing is tuned after results are seen. New file; built from scripts/make_gates_047.py (frozen).
Inputs (D = results/study-048): D/main/{RESULTS,SCIENTIFIC,SEAL}.json (18 part-r replays: scale16 12, control 6, arm API16D; fresh
cases scale16 12, control 6, scale20 N20, arms API16D and API16D_b), D/main/RECOUNT_048.json, D/main/REFERENCE_048.json,
D/API_CHECKS_048.json, D/TEST_SUITE_048.json, experiments/COMMIT_ORDER_048.json, results/RESEARCH_LEDGER.jsonl. Missing or partial
input => every data gate FAIL INCOMPLETE_INPUT. Records are accepted only if sha256(RESULTS) equals the seal and no_time(RESULTS)
equals SCIENTIFIC. Labels: recounted if G_recount passes, else the study's (stated).
  GDET48: canon16d(API16D) == canon16d(API16D_b) on 18/18 fresh scale16+control and N20/N20 scale20, AND wall_guard false on every
     certify/16d record (parts a, r, d);  GWALL_r: wall_guard false on all 18 part-r replays;
  GFID48: API_CHECKS_048 fidelity exact on 18 + N20 records, bound to the sealed RESULTS sha;
  GAPI16D_fresh48: scale16 API16D WRONG 0 (either arm) and API16D ID+IDF >= 7/12 (Wilson 95% CI);
  GS20_sound: scale20 WRONG 0 (both arms) and every decided scale20 record audited at bound 20 by REFERENCE_048 with 0 mismatches;
     'vacuous' stated if 0 decided; pass None ('not run') if part d is dropped (N20 = 0);
  GHOST48: API_CHECKS_048 ghost PASS48 (closure unchanged since the 047 freeze, certify16d.py sha = the 047 and 048 freeze sha,
     no flagged import, 0 socket attempts);  G10: API16D and API16D_b ID on the 6 fresh controls;
  GQB23: every logged certify/16d call wall <= 30 s (fresh and replay), conflicts reported per part;
  GS_ref: REFERENCE_048 on block main: sha bound, 0 mismatches, complete within 2400 s, 20/20 mutations; G_sound; G_recount; GTI;
  G_PROC: preregistration, build_authorization, seedcheck, source_freeze, run_start, run_end (all _048) as a subsequence,
     parseable non-decreasing note times, commit-order file, main sealed;  G_RT: main elapsed <= 3600 s.
  Secondary (reported): GS20_rate, GREP16e, GR_class, GCOST48.
  PYTHONPATH=. python scripts/make_gates_048.py [--study-dir D] [--check]"""
from __future__ import annotations
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common import load,dumps,write_new,check,sha
from experiments.brute_common_026 import wilson
from scripts.make_gates_034 import opt
from scripts.make_gates_043 import subseq

STUDY_DIR=ROOT/'results/study-048';D_ARMS=('API16D','API16D_b')
LABELS=('ID','IDF','AMB','WRONG','IDU');CLASSES=('none','cap-timing','word-divergence','infidelity')
CAP_RT=3600;QB=30.0;FRESH_BAR=7;GREP_047=(10,12);NAMED=(11230004,11230008,11230009)
PROC_ORDER=tuple(e+'_048' for e in ('preregistration','build_authorization','seedcheck','source_freeze','run_start','run_end'))


def ckey(c):return f"{c['block']}/{c['key']}/{c['seed']}"


def ledger():
    from datetime import datetime
    L=[json.loads(x) for x in (ROOT/'results/RESEARCH_LEDGER.jsonl').read_text().splitlines() if x.strip()]
    i0=next((i for i,e in enumerate(L) if e.get('event')=='preregistration_048'),None);out=[]
    for e in (L[i0:] if i0 is not None else []):
        try:t=datetime.fromisoformat(str(e.get('note',''))[:25])
        except ValueError:t=None
        out.append((e['event'],t))
        if e['event']==PROC_ORDER[-1]:break
    return out


def build(study=STUDY_DIR,fresh=None,n_rep=None):
    from brute.evaluation import no_time
    from experiments.brute_study_048 import canon16d,N20
    study=Path(study);D=study/'main';Gt={};sec={}
    seal=opt(D/'SEAL.json');sci=opt(D/'SCIENTIFIC.json');res=opt(D/'RESULTS.json');rc=opt(D/'RECOUNT_048.json')
    ref=opt(D/'REFERENCE_048.json');ts=opt(study/'TEST_SUITE_048.json');order=opt(ROOT/'experiments/COMMIT_ORDER_048.json')
    api=opt(study/'API_CHECKS_048.json');fz=opt(ROOT/'experiments/BRUTE_SOURCE_FREEZE_048.json');fz47=opt(ROOT/'experiments/BRUTE_SOURCE_FREEZE_047.json')
    rsha=sha(D/'RESULTS.json') if (D/'RESULTS.json').exists() else None
    sealed=(bool(seal) and res is not None and sci is not None and rsha==seal.get('results_sha256')
            and sha(D/'SCIENTIFIC.json')==seal.get('scientific_sha256') and no_time(res)==sci)
    n20=(res or {}).get('n_scale20',N20);fresh=dict(fresh or {'scale16':12,'control':6,'scale20':n20});n_rep=18 if n_rep is None else n_rep
    if not fresh.get('scale20'):fresh.pop('scale20',None)
    allc=[c for c in (res or {}).get('cases',[]) if c['block']=='main'] if sealed else []
    reps=[r for r in (res or {}).get('replays',[]) if r['block']=='r'] if sealed else []
    G=lambda k:sorted([c for c in allc if c['key']==k],key=lambda c:c['seed'])
    sc16=G('scale16');s20=G('scale20')
    complete=(sealed and seal.get('complete') is True and all(len(G(k))==n for k,n in fresh.items()) and len(allc)==sum(fresh.values())
              and all(list(c['arms'])==list(D_ARMS) for c in allc) and len(reps)==n_rep and all(list(c['arms'])==['API16D'] for c in reps))
    wb=None if complete else 'INCOMPLETE_INPUT (main missing, partial, missing arms or not matching its seal)'
    def gate(name,ok,obs,why=None,na=False):Gt[name]={'pass':None if na else (bool(ok) and why is None),'observed':obs,**({'reason':why} if why else {})}
    pc=(rc or {}).get('per_case') or {};rcmp=(rc or {}).get('replay_compare') or {}
    rc_bound=bool(rc) and rc.get('results_sha256')==rsha and rc.get('cases')==len((res or {}).get('cases',[])) and rc.get('replays')==len((res or {}).get('replays',[]))
    rc_ok=rc_bound and rc.get('PASS') is True and rc.get('mismatching_cases')==0
    rrec=lambda c,a:((pc.get(ckey(c)) or {}).get(a) or {}) if rc_bound else {}
    lab=(lambda c,a:rrec(c,a).get('label')) if rc_ok else (lambda c,a:c['arms'][a]['label'])
    lsrc='recount' if rc_ok else 'study labels (G_recount did not pass)'
    dd=lambda c,a:a in c['arms'] and lab(c,a) in ('ID','IDF')
    ci=lambda x,n:wilson(x,n) if n else None
    cmp_=(lambda c:rcmp.get(f"r/{c['key']}/{c['seed']}") or {}) if rc_ok else (lambda c:c.get('replay') or {})
    # GDET48 / GWALL_r
    det=[[c['key'],c['seed'],canon16d(c['arms']['API16D'])==canon16d(c['arms']['API16D_b']),c['arms']['API16D']['label'],c['arms']['API16D_b']['label']]
         for c in sc16+G('control')+s20]
    guards=[[ckey(c),an,ar.get('guard_events')] for c in allc+reps for an,ar in c['arms'].items() if ar.get('wall_guard')]
    rguard=[g for g in guards if g[0].startswith('r/')];nd=sum(x[2] for x in det);ndet=18+fresh.get('scale20',0)
    d16=sum(x[2] for x in det if x[0]!='scale20');d20=sum(x[2] for x in det if x[0]=='scale20')
    gate('GDET48',complete and len(det)==ndet and nd==ndet and not guards,{'identical':nd,'of':len(det),'ci95':ci(nd,len(det)),
         'scale16_control':[d16,18],'scale20':[d20,fresh.get('scale20',0)],'wall_guard_fired':guards,'per_case':det,
         'columns':['key','seed','canon16d_equal','API16D','API16D_b'],'rule':'canon16d identical on 18/18 and N20/N20; wall_guard 0 on every certify/16d record (a, r, d)'},why=wb)
    gate('GWALL_r',complete and not rguard,{'replays':len(reps),'fired':rguard,'named_047_firings':{s:[x for x in rguard if x[0].endswith(f'/{s}')]==[] for s in NAMED},
         'rule':'0 wall_guard firings on all 18 part-r replays'},why=wb)
    # GFID48
    fi=(api or {}).get('fidelity') or {}
    fi_ok=bool(fi) and fi.get('study_results_sha256')==rsha and fi.get('PASS') is True and fi.get('exact')==fi.get('cases')==ndet
    gate('GFID48',complete and fi_ok,{'exact':fi.get('exact'),'of':fi.get('cases'),'expected':ndet,'ci95':ci(fi.get('exact') or 0,fi.get('cases') or 0),
         'per_key':fi.get('per_key'),'bound':bool(fi) and fi.get('study_results_sha256')==rsha,'failures':{k:v for k,v in (fi.get('per_case') or {}).items() if not v['exact']}},
         why=wb or (None if fi else 'INCOMPLETE_INPUT (API_CHECKS_048 fidelity missing)'))
    # GAPI16D_fresh48
    wrong=[[ckey(c),a] for c in allc+reps for a in c['arms'] if lab(c,a)=='WRONG' or c['arms'][a]['label']=='WRONG']
    w16=[x for x in wrong if x[0].startswith('main/scale16/')];x16=sum(dd(c,'API16D') for c in sc16)
    gate('GAPI16D_fresh48',complete and len(sc16)==12 and not w16 and x16>=FRESH_BAR,{'WRONG':w16,'ID_IDF':x16,'of':len(sc16),'bar':FRESH_BAR,'ci95':ci(x16,len(sc16)),
         'API16D_b_ID_IDF':sum(dd(c,'API16D_b') for c in sc16),'per_case':[[c['seed'],lab(c,'API16D'),c['arms']['API16D']['stop'],c['arms']['API16D']['conflicts_spent']] for c in sc16],
         'label_source':lsrc},why=wb)
    # GS20_sound
    if not fresh.get('scale20'):gate('GS20_sound',False,{'n_scale20':0,'note':'part d dropped under the declared cut rule'},na=True)
    else:
        w20=[x for x in wrong if x[0].startswith('main/scale20/')];dec=[(c,a) for c in s20 for a in D_ARMS if c['arms'][a]['stop']!='unknown']
        ab=((ref or {}).get('per_key') or {}).get('scale20') or {};rb=bool(ref) and ref.get('study_results_sha256')==rsha
        ok20=rb and ref.get('complete') is True and ab.get('audited')==ab.get('decided')==len(dec) and not ab.get('mismatches')
        x20=sum(dd(c,'API16D') for c in s20)
        gate('GS20_sound',complete and len(s20)==fresh['scale20'] and not w20 and ok20,{'WRONG':w20,'decided_records':len(dec),'vacuous':len(dec)==0,
             'API16D_ID_IDF':x20,'of':len(s20),'ci95':ci(x20,len(s20)),'reference_scale20':ab,'reference_bound':rb,
             'per_case':[[c['seed'],lab(c,'API16D'),c['arms']['API16D']['stop'],lab(c,'API16D_b')] for c in s20],
             'rule':'scale20 WRONG 0; every decided scale20 record audited at bound 20 with 0 mismatches; a pass with 0 decided is vacuous'},
             why=wb or (None if ref else 'INCOMPLETE_INPUT (REFERENCE_048 missing)'))
    # GHOST48
    cd=(fz or {}).get('sha256_files',{}).get('brute/api/certify16d.py');cd47=(fz47 or {}).get('sha256_files',{}).get('brute/api/certify16d.py')
    abound=bool(api) and cd is not None and api.get('certify16d_sha256')==cd==cd47==sha(ROOT/'brute/api/certify16d.py')
    ag=(api or {}).get('ghost') or {}
    gate('GHOST48',abound and ag.get('PASS48') is True,None if not api else {'bound_to_freezes_047_048':abound,'closure_unchanged':ag.get('closure_unchanged'),
         'certify16d_unchanged':ag.get('certify16d_unchanged'),'newly_imported_vs_certify16':ag.get('newly_imported'),'new_flagged':ag.get('new_flagged'),
         'socket_attempts':ag.get('socket_attempts'),'no_network_run':ag.get('no_network_run')},why=None if api else 'INCOMPLETE_INPUT (API_CHECKS_048 missing)')
    # G10
    g10=[(c['seed'],{a:lab(c,a) for a in D_ARMS}) for c in G('control')]
    gate('G10',complete and len(g10)==6 and all(all(L=='ID' for L in x[1].values()) for x in g10),{'cases':g10},why=wb)
    # GQB23
    mx={};over=[];conf={}
    for c in allc+reps:
        part='r' if c['block']=='r' else ('d' if c['key']=='scale20' else 'a')
        for a,ar in c['arms'].items():
            for x in ar['calls']:
                mx[part]=max(mx.get(part,0),x['wall'])
                if x['wall']>QB:over.append([f'{ckey(c)}/{a}',x.get('phase'),x.get('n'),round(x['wall'],3)])
            cc=[v for r in ar['rounds'] for v in r.get('call_conflicts',[])];y=conf.setdefault(part,{'calls':0,'max':0,'capped':0,'spent':0})
            y['calls']+=len(cc);y['max']=max([y['max']]+cc);y['capped']+=sum(bool(v) for r in ar['rounds'] for v in r.get('call_capped',[]));y['spent']+=ar.get('conflicts_spent') or 0
    gate('GQB23',complete and bool(mx) and not over,{'max_call_wall_s_by_part':{k:round(v,3) for k,v in sorted(mx.items())},'bound_s':QB,'over':over,'conflicts_by_part':conf},why=wb)
    # GS_ref
    mt=(ref or {}).get('mutation_test') or {};rb=bool(ref) and ref.get('study_results_sha256')==rsha and ref.get('block')=='main'
    robs=None if not ref else {k:ref.get(k) for k in ('block','scope','records','decided','audited','not_audited','complete','per_arm','per_key','not_reached',
                               'k_spent_as_amb','verdicts_checked','mismatch_count','vacuous','PASS','elapsed_informational')}|{'mutations':mt.get('detected'),'of':mt.get('mutations')}
    gate('GS_ref',rb and ref.get('mismatch_count')==0 and ref.get('complete') is True and (ref.get('scope') or {}).get('budget_s')==2400.0
         and mt.get('detected')==mt.get('mutations')==20 and ref.get('PASS') is True,robs,why=wb or (None if ref else 'INCOMPLETE_INPUT (REFERENCE_048 missing)'))
    # G_sound / G_recount
    snd={'words_checked':sum(ar.get('words_checked',0) for c in allc+reps for ar in c['arms'].values()),
         'words_unsound':sum(ar.get('words_unsound',0) for c in allc+reps for ar in c['arms'].values()),
         'recount_bound':rc_bound,'recount_words_checked':(rc or {}).get('words_checked'),'recount_words_unsound':(rc or {}).get('words_unsound'),
         'recount_truth_inconsistent':(rc or {}).get('truth_inconsistent')}
    gate('G_sound',complete and rc_bound and snd['words_unsound']==0 and snd['recount_words_unsound']==0 and snd['recount_truth_inconsistent']==0
         and snd['recount_words_checked']==snd['words_checked'],snd,why=wb or (None if rc_bound else 'INCOMPLETE_INPUT (RECOUNT_048 missing or unbound)'))
    gate('G_recount',complete and rc_ok,None if not rc else {k:rc.get(k) for k in ('cases','replays','labels_main','labels_scale16_main','labels_control_main',
         'labels_scale20_main','replay_labels','replay_summary','misfires_main','amb_rule_applied','words_checked','words_unsound','truth_inconsistent','mismatching_cases','PASS')},
         why=wb or (None if rc else 'INCOMPLETE_INPUT (RECOUNT_048 missing)'))
    mods=(ts or {}).get('per_module') or {};gm=(ts or {}).get('gated_modules') or []
    gate('GTI',bool(gm) and ts.get('passed') is True and all(mods[m].get('returncode')==0 for m in gm),
         None if not ts else {'gated':{m:{'returncode':mods[m].get('returncode'),'tests':mods[m].get('tests')} for m in gm},
                              'reported':{m:{'returncode':v.get('returncode'),'tests':v.get('tests')} for m,v in mods.items() if m not in gm}},
         why=None if ts else 'INCOMPLETE_INPUT (TEST_SUITE_048 missing)')
    lt=ledger();ev=[e for e,_ in lt];times=[t for _,t in lt]
    proc={'order':subseq(ev,PROC_ORDER),'ledger_times_parse':bool(lt) and all(t is not None for t in times),
          'ledger_times_non_decreasing':all(a<=b for a,b in zip(times,times[1:]) if a and b),'commit_order_file':order is not None,'main_sealed':bool(sealed)}
    gate('G_PROC',all(proc.values()),{'clauses':proc,'events':ev,'required_order':list(PROC_ORDER)})
    el=(res or {}).get('total_elapsed_informational')
    gate('G_RT',complete and el is not None and el<=CAP_RT,{'elapsed_s':el,'cap_s':CAP_RT,'cases':len(allc),'replays':len(reps),'n_scale20':fresh.get('scale20',0)},why=wb)
    # secondary
    cost={}
    for c in allc+reps:
        part='r' if c['block']=='r' else ('d' if c['key']=='scale20' else 'a')
        for a,ar in c['arms'].items():
            x=cost.setdefault(f"{a}/{part}/{c['key']}",{'records':0,'arm_wall_s':0.0,'calls':0,'capped_calls':0,'call_wall_s':0.0,'conflicts':0})
            x['records']+=1;x['arm_wall_s']+=ar.get('arm_wall_informational') or 0.0;x['conflicts']+=ar.get('conflicts_spent') or 0
            for cl in ar['calls']:x['calls']+=1;x['capped_calls']+=bool(cl['capped']);x['call_wall_s']+=cl['wall']
    for x in cost.values():x['arm_wall_s']=round(x['arm_wall_s'],1);x['call_wall_s']=round(x['call_wall_s'],1)
    sec['GCOST48']={'pass':None,'observed':dict(sorted(cost.items())),'rule':'reported: wall, calls, capped calls, call wall, conflicts per arm/part/key'}
    sec['GREP16e']={'pass':None,'observed':{'API16D_ID_IDF':x16,'of':len(sc16),'ci95':ci(x16,len(sc16)),'prior_047_C294000':list(GREP_047),'prior_ci95':wilson(*GREP_047)},
                    'rule':'reported: API16D scale16 ID+IDF at C 50000 beside 047 at C 294000 (10/12)'}
    sec['GR_class']={'pass':None,'observed':{'classes':{q:sum(cmp_(c).get('class')==q for c in reps) for q in CLASSES},'same':sum(bool(cmp_(c).get('same')) for c in reps),
                     'n':len(reps),'per_case':[[c['key'],c['seed'],cmp_(c).get('label'),cmp_(c).get('class'),c['arms']['API16D'].get('wall_guard')] for c in reps]},
                     'rule':'reported: part r classes against the sealed 046 A16_N records'}
    if fresh.get('scale20'):
        x20=sum(dd(c,'API16D') for c in s20)
        sec['GS20_rate']={'pass':None,'observed':{'ID_IDF':x20,'of':len(s20),'ci95':ci(x20,len(s20)),'cost':{k:v for k,v in cost.items() if '/d/' in k}},'rule':'reported'}
    cnt=lambda k,a,L:sum(lab(c,a)==L for c in G(k));nk=lambda k:len(G(k))
    fl={f'{a}/{k}':{L:{'x':cnt(k,a,L),'n':nk(k),'ci95':ci(cnt(k,a,L),nk(k))} for L in LABELS} for k in fresh for a in D_ARMS}
    return {'schema':'brute.gates.v45_0','study':(res or {}).get('plan',{}).get('study'),'process':'lean','sealed_input_verified':sealed,'label_source':lsrc,
            'n_scale20':fresh.get('scale20',0),'conflict_cap':(res or {}).get('conflict_cap'),'budget_conflicts':(res or {}).get('budget_conflicts'),'gates':Gt,'secondary':sec,
            'all_gated_pass':all(g['pass'] for g in Gt.values() if g['pass'] is not None),
            'failed':[k for k,g in Gt.items() if g['pass'] is False],'not_exercised':[k for k,g in Gt.items() if g['pass'] is None],
            'claim':'certify/16d ID/IDF is exact conditional on noise-free readings and true size <= the declared N (family_bound)',
            'reports':{'fresh_labels':fl} if allc else {}}


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--study-dir',default=str(STUDY_DIR));ap.add_argument('--check',action='store_true');a=ap.parse_args()
    obj=build(Path(a.study_dir));out=Path(a.study_dir)/'GATES_048.json'
    if a.check:check(out.read_bytes()==dumps(obj),'GATES_048.json does not reproduce');print('GATES_048 reproduces')
    else:write_new(out,obj);print(json.dumps({k:v['pass'] for k,v in obj['gates'].items()}),obj['failed'])
