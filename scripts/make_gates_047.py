"""Gates for study-047 (BRUTE_PLAN_047 criteria; pre-run deviation #167 definitions), LEAN process. Committed in the source freeze
before run_start_047; nothing is tuned after results are seen. New file; built from scripts/make_gates_046.py (frozen).
Inputs (D = results/study-047): D/main/{RESULTS,SCIENTIFIC,SEAL}.json (72 replay records: a1 18, a2 18, a3_045 18, a3_046 18;
fresh cases: scale16 12 and control 6 with arms API16D / API16D_b / A16_N, scale20 12 with API16D, unless part d is cut),
D/main/RECOUNT_047.json, D/main/REFERENCE_047.json, D/API_CHECKS_047.json, D/TEST_SUITE_047.json, experiments/COMMIT_ORDER_047.json,
results/RESEARCH_LEDGER.jsonl. Missing or partial input => every data gate FAIL INCOMPLETE_INPUT. Records are accepted only if
sha256(RESULTS) equals the seal and no_time(RESULTS) equals SCIENTIFIC. Labels: recounted if G_recount passes, else the study's (stated).
  GDET: canon16d(API16D) == canon16d(API16D_b) byte for byte on 18/18 fresh scale16+control cases, and wall_guard false on every
     API16D / API16D_b record of the run (parts a3, b and d; #167: 'a wall_guard firing is a GDET failure');
  GFID16D: (i) API_CHECKS_047 fidelity 18/18 exact, bound to the sealed RESULTS sha; (ii) a3 (both sources): every replay with no
     capped call on either side has the same label, n_min and canonical model as the sealed record (recount comparison if
     G_recount passes); the a3 class counts are reported;
  GFID_wall: a1 and a2: 0 replays in the 'infidelity' class (#167 classify; cap-timing / word-divergence counted, not failed);
  GAPI16D_fresh: scale16: API16D WRONG 0 and API16D ID+IDF >= 7/12 (Wilson 95% CI); agreement with A16_N reported (capped unknowns);
  GS20_sound: scale20: API16D WRONG 0 on 12/12 and every decided scale20 record audited by REFERENCE_047 at bound 20 with 0
     mismatches; ID+IDF with CI reported; pass None ('not run') if part d is cut;
  GAPI16_compat / GHOST16D: API_CHECKS_047 compat / ghost PASS, bound to the certify16d.py sha in the source freeze;
  G10: API16D, API16D_b and A16_N ID on each of the 6 fresh controls;
  GQB22: A16_N max logged call / query wall <= 10.5 s and API16D(+_b) max logged call wall <= 30 s, fresh and replay records
     (API16 replays reported against 10.5 s, not gated), conflict counts reported;
  GS_ref: REFERENCE_047 on block main: sha bound, 0 mismatches, complete, 20/20 mutations; G_sound; G_recount; GTI;
  G_PROC: preregistration, build_authorization, seedcheck, cap_calibration, source_freeze, run_start, run_end (all _047) as a
     subsequence, parseable non-decreasing note times, commit-order file, main sealed; G_RT: main elapsed <= 3600 s.
  Secondary (reported): GREP16d, GCAP_class, GS20_rate, GAPI_cost.
  PYTHONPATH=. python scripts/make_gates_047.py [--study-dir D] [--check]"""
from __future__ import annotations
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common import load,dumps,write_new,check,sha
from experiments.brute_common_026 import wilson
from scripts.make_gates_034 import opt
from scripts.make_gates_043 import subseq

STUDY_DIR=ROOT/'results/study-047'
FRESH={'scale16':12,'control':6,'scale20':12};ARMS_OF={'scale16':('API16D','API16D_b','A16_N'),'control':('API16D','API16D_b','A16_N'),'scale20':('API16D',)}
PARTS={'a1':18,'a2':18,'a3_045':18,'a3_046':18};PART_ARM={'a1':'A16_N','a2':'API16','a3_045':'API16D','a3_046':'API16D'}
LABELS=('ID','IDF','AMB','WRONG','IDU');CLASSES=('none','cap-timing','word-divergence','infidelity')
CAP_RT=3600;QB={'A16_N':10.5,'API16D':30.0,'API16D_b':30.0};QB_REPORT={'API16':10.5};FRESH_BAR=7
GREP=((9,12),(10,12),(7,12))
PROC_ORDER=tuple(e+'_047' for e in ('preregistration','build_authorization','seedcheck','cap_calibration','source_freeze','run_start','run_end'))


def ckey(c):return f"{c['block']}/{c['key']}/{c['seed']}"


def ledger():
    from datetime import datetime
    L=[json.loads(x) for x in (ROOT/'results/RESEARCH_LEDGER.jsonl').read_text().splitlines() if x.strip()]
    i0=next((i for i,e in enumerate(L) if e.get('event')=='preregistration_047'),None);out=[]
    for e in (L[i0:] if i0 is not None else []):
        try:t=datetime.fromisoformat(str(e.get('note',''))[:25])
        except ValueError:t=None
        out.append((e['event'],t))
        if e['event']==PROC_ORDER[-1]:break
    return out


def build(study=STUDY_DIR,fresh=None,parts=None):
    from brute.evaluation import no_time
    from experiments.brute_study_047 import canon16d
    study=Path(study);D=study/'main';Gt={};sec={}
    seal=opt(D/'SEAL.json');sci=opt(D/'SCIENTIFIC.json');res=opt(D/'RESULTS.json');rc=opt(D/'RECOUNT_047.json')
    ref=opt(D/'REFERENCE_047.json');ts=opt(study/'TEST_SUITE_047.json');order=opt(ROOT/'experiments/COMMIT_ORDER_047.json')
    api=opt(study/'API_CHECKS_047.json');fz=opt(ROOT/'experiments/BRUTE_SOURCE_FREEZE_047.json')
    rsha=sha(D/'RESULTS.json') if (D/'RESULTS.json').exists() else None
    sealed=(bool(seal) and res is not None and sci is not None and rsha==seal.get('results_sha256')
            and sha(D/'SCIENTIFIC.json')==seal.get('scientific_sha256') and no_time(res)==sci)
    cut=bool((res or {}).get('cut_d'))
    fresh=dict(fresh or FRESH);parts=PARTS if parts is None else parts
    if cut:fresh.pop('scale20',None)
    allc=[c for c in (res or {}).get('cases',[]) if c['block']=='main'] if sealed else []
    reps=(res or {}).get('replays',[]) if sealed else []
    G=lambda k:sorted([c for c in allc if c['key']==k],key=lambda c:c['seed'])
    P=lambda p:sorted([c for c in reps if c['block']==p],key=lambda c:(c['key'],c['seed']))
    sc16=G('scale16');n16=len(sc16);s20=G('scale20')
    complete=(sealed and seal.get('complete') is True and all(len(G(k))==n for k,n in fresh.items()) and len(allc)==sum(fresh.values())
              and all(sorted(c['arms'])==sorted(ARMS_OF[c['key']]) for c in allc) and all(len(P(p))==n for p,n in parts.items())
              and len(reps)==sum(parts.values()) and all(list(c['arms'])==[PART_ARM[c['block']]] for c in reps))
    wb=None if complete else 'INCOMPLETE_INPUT (main missing, partial, missing arms or not matching its seal)'
    def gate(name,ok,obs,why=None,na=False):Gt[name]={'pass':None if na else (bool(ok) and why is None),'observed':obs,**({'reason':why} if why else {})}
    pc=(rc or {}).get('per_case') or {};rcmp=(rc or {}).get('replay_compare') or {}
    rc_bound=bool(rc) and rc.get('results_sha256')==rsha and rc.get('cases')==len((res or {}).get('cases',[])) and rc.get('replays')==len(reps or (res or {}).get('replays',[]))
    rc_ok=rc_bound and rc.get('PASS') is True and rc.get('mismatching_cases')==0
    rrec=lambda c,a:((pc.get(ckey(c)) or {}).get(a) or {}) if rc_bound else {}
    lab=(lambda c,a:rrec(c,a).get('label')) if rc_ok else (lambda c,a:c['arms'][a]['label'])
    lsrc='recount' if rc_ok else 'study labels (G_recount did not pass)'
    dd=lambda c,a:a in c['arms'] and lab(c,a) in ('ID','IDF')
    ci=lambda x,n:wilson(x,n) if n else None
    cmp_=(lambda c:rcmp.get(ckey(c)) or {}) if rc_ok else (lambda c:c.get('replay') or {})
    # GDET
    det=[];guards=[]
    for c in G('scale16')+G('control'):
        a,b=c['arms']['API16D'],c['arms']['API16D_b'];det.append([c['key'],c['seed'],canon16d(a)==canon16d(b),a['label'],b['label']])
    for c in allc+reps:
        for an,ar in c['arms'].items():
            if an in ('API16D','API16D_b') and ar.get('wall_guard'):guards.append([ckey(c),an,ar.get('guard_events')])
    nd=sum(x[2] for x in det)
    gate('GDET',complete and len(det)==18 and nd==18 and not guards,{'identical':nd,'of':len(det),'ci95':ci(nd,len(det)),'wall_guard_fired':guards,
         'per_case':det,'columns':['key','seed','canon16d_equal','API16D','API16D_b'],
         'rule':'canon16d byte-identical on 18/18 fresh scale16+control; wall_guard 0 on every API16D/API16D_b record (a3, b, d)'},why=wb)
    # GFID16D
    fi=(api or {}).get('fidelity') or {};fi_ok=bool(fi) and fi.get('study_results_sha256')==rsha and fi.get('PASS') is True and fi.get('exact')==fi.get('cases')==18
    a3=[[c['block'],c['key'],c['seed'],cmp_(c).get('label'),cmp_(c).get('n_min'),cmp_(c).get('canonical_model_equal'),cmp_(c).get('same'),
         cmp_(c).get('sealed_capped_any'),cmp_(c).get('replay_capped_any'),cmp_(c).get('class')] for p in ('a3_045','a3_046') for c in P(p)]
    unc=[x for x in a3 if not x[7] and not x[8]];bad3=[x for x in unc if not x[6]]
    gate('GFID16D',complete and fi_ok and len(a3)==36 and not bad3,
         {'i_self_replay':{'exact':fi.get('exact'),'of':fi.get('cases'),'ci95':ci(fi.get('exact') or 0,fi.get('cases') or 0),'bound':bool(fi) and fi.get('study_results_sha256')==rsha},
          'ii_uncapped':len(unc),'ii_uncapped_same':len(unc)-len(bad3),'ii_ci95':ci(len(unc)-len(bad3),len(unc)),'ii_failures':bad3,
          'a3_classes':{q:sum(x[9]==q for x in a3) for q in CLASSES},'per_case':a3,
          'columns':['part','key','seed','label[api,sealed]','n_min[api,sealed]','canonical_model_equal','same','sealed_capped_any','replay_capped_any','class'],
          'source':'recount' if rc_ok else 'study'},why=wb or (None if fi else 'INCOMPLETE_INPUT (API_CHECKS_047 fidelity missing)'))
    # GFID_wall
    aw={p:{q:sum(cmp_(c).get('class')==q for c in P(p)) for q in CLASSES}|{'n':len(P(p)),'same':sum(bool(cmp_(c).get('same')) for c in P(p))} for p in ('a1','a2')}
    inf=[[c['block'],c['key'],c['seed']] for p in ('a1','a2') for c in P(p) if cmp_(c).get('class')=='infidelity']
    gate('GFID_wall',complete and not inf,{'by_part':aw,'same_ci95':{p:ci(v['same'],v['n']) for p,v in aw.items()},'infidelity':inf,
         'rule':'a1 and a2: 0 infidelity-class differences (cap-timing and word-divergence published, not failed)'},why=wb)
    # GAPI16D_fresh
    wrong=[[ckey(c),a] for c in allc for a in c['arms'] if lab(c,a)=='WRONG' or c['arms'][a]['label']=='WRONG']
    w16=[x for x in wrong if x[0].startswith('main/scale16/') and x[1]=='API16D'];nA=sum(dd(c,'API16D') for c in sc16)
    agree=0;dis=[]
    for c in sc16:
        la,ln=lab(c,'API16D'),lab(c,'A16_N')
        if la==ln:agree+=1;continue
        dis.append({'seed':c['seed'],'API16D':la,'A16_N':ln,'capped_unknown':[a for a in ('API16D','A16_N') if lab(c,a)=='IDU' and c['arms'][a]['capped']>0]})
    gate('GAPI16D_fresh',complete and not w16 and nA>=FRESH_BAR,{'API16D_WRONG':w16,'all_WRONG':wrong,'API16D_ID_IDF':nA,'of':n16,'ci95':ci(nA,n16),
         'agree_A16_N':agree,'agree_ci95':ci(agree,n16),'disagreements':dis,'label_source':lsrc,
         'per_case':[[c['seed'],lab(c,'API16D'),lab(c,'A16_N')] for c in sc16],'rule':f'API16D WRONG 0; API16D ID+IDF >= {FRESH_BAR}/12'},why=wb)
    # GS20_sound
    if cut:gate('GS20_sound',False,{'cut_d':True},why='not run: part d cut under the declared runtime rule',na=True)
    else:
        w20=[x for x in wrong if x[0].startswith('main/scale20/')];dec=[c for c in s20 if dd(c,'API16D')]
        ab=((ref or {}).get('per_key') or {}).get('scale20') or {}
        rb=bool(ref) and ref.get('study_results_sha256')==rsha
        ok20=rb and ref.get('mismatch_count')==0 and ref.get('complete') is True and ab.get('audited')==ab.get('decided') and (ab.get('decided') or 0)>=len(dec) and not ab.get('mismatches')
        n20=sum(dd(c,'API16D') for c in s20)
        gate('GS20_sound',complete and len(s20)==12 and not w20 and ok20,{'WRONG':w20,'decided':len(dec),'ID_IDF':n20,'of':len(s20),'ci95':ci(n20,len(s20)),
             'reference_scale20':ab,'reference_bound':rb,'per_case':[[c['seed'],lab(c,'API16D'),c['arms']['API16D']['stop']] for c in s20],
             'rule':'scale20 API16D WRONG 0; every decided scale20 record audited at bound 20 with 0 mismatches'},
             why=wb or (None if ref else 'INCOMPLETE_INPUT (REFERENCE_047 missing)'))
    # GAPI16_compat / GHOST16D
    cd=(fz or {}).get('sha256_files',{}).get('brute/api/certify16d.py');abound=bool(api) and cd is not None and api.get('certify16d_sha256')==cd==sha(ROOT/'brute/api/certify16d.py')
    ac=(api or {}).get('compat') or {};ag=(api or {}).get('ghost') or {};nw=None if api else 'INCOMPLETE_INPUT (API_CHECKS_047 missing)'
    gate('GAPI16_compat',abound and ac.get('PASS') is True,None if not api else {'bound_to_freeze':abound,'tests':ac.get('tests'),
         'sample_046':{k:(ac.get('sample_046') or {}).get(k) for k in ('cases','s4_cases','sample_sha256','PASS')}},why=nw)
    gate('GHOST16D',abound and ag.get('PASS') is True,None if not api else {'bound_to_freeze':abound,'newly_imported':ag.get('newly_imported'),
         'new_flagged':ag.get('new_flagged'),'closure_flagged_reported':ag.get('closure_flagged_reported'),'no_network_run':ag.get('no_network_run'),
         'static_pass':ag.get('static_pass'),'network_pass':ag.get('network_pass')},why=nw)
    # G10
    g10=[(c['seed'],{a:lab(c,a) for a in ARMS_OF['control']}) for c in G('control')]
    gate('G10',complete and len(g10)==6 and all(all(L=='ID' for L in x[1].values()) for x in g10),{'cases':g10,'rule':'API16D, API16D_b and A16_N ID on every fresh control'},why=wb)
    # GQB22
    per={};over=[];rep_over=[];ncalls=0;conf={}
    for c in allc+reps:
        for a,ar in c['arms'].items():
            bound=QB.get(a,QB_REPORT.get(a));sink=over if a in QB else rep_over
            for x in ar['calls']:
                ncalls+=1;per[a]=max(per.get(a,0),x['wall'])
                if x['wall']>bound:sink.append([f'{ckey(c)}/{a}',x.get('phase'),x.get('n'),round(x['wall'],3)])
            q=ar.get('query_max_s')
            if q is not None:
                per[a]=max(per.get(a,0),q)
                if q>bound:sink.append([f'{ckey(c)}/{a}','query',None,round(q,3)])
            if a in ('API16D','API16D_b'):
                cc=[v for r in ar['rounds'] for v in r.get('call_conflicts',[])];y=conf.setdefault(a,{'calls':0,'max':0,'capped':0,'spent':0})
                y['calls']+=len(cc);y['max']=max([y['max']]+cc);y['capped']+=sum(v is not None for r in ar['rounds'] for v in r.get('call_capped',[]));y['spent']+=ar.get('conflicts_spent') or 0
    gate('GQB22',complete and bool(per) and not over,{'max_s_by_arm':{a:round(v,3) for a,v in sorted(per.items())},'bound_s':QB,'over':over,
         'API16_replay_over_10_5_reported':rep_over,'calls_logged':ncalls,'conflicts':conf},why=wb)
    # GS_ref
    mt=(ref or {}).get('mutation_test') or {};rb=bool(ref) and ref.get('study_results_sha256')==rsha and ref.get('block')=='main'
    robs=None if not ref else {k:ref.get(k) for k in ('block','scope','records','decided','audited','not_audited','complete','per_arm','per_key','not_reached',
                               'k_spent_as_amb','verdicts_checked','mismatch_count','vacuous','PASS','elapsed_informational')}|{'mutations':mt.get('detected'),'of':mt.get('mutations')}
    gate('GS_ref',rb and ref.get('mismatch_count')==0 and ref.get('complete') is True and mt.get('detected')==mt.get('mutations')==20 and ref.get('PASS') is True,
         robs,why=wb or (None if ref else 'INCOMPLETE_INPUT (REFERENCE_047 missing)'))
    # G_sound / G_recount
    snd={'words_checked':sum(ar.get('words_checked',0) for c in allc+reps for ar in c['arms'].values()),
         'words_unsound':sum(ar.get('words_unsound',0) for c in allc+reps for ar in c['arms'].values()),
         'recount_bound':rc_bound,'recount_words_checked':(rc or {}).get('words_checked'),'recount_words_unsound':(rc or {}).get('words_unsound'),
         'recount_truth_inconsistent':(rc or {}).get('truth_inconsistent')}
    gate('G_sound',complete and rc_bound and snd['words_unsound']==0 and snd['recount_words_unsound']==0 and snd['recount_truth_inconsistent']==0
         and snd['recount_words_checked']==snd['words_checked'],snd,why=wb or (None if rc_bound else 'INCOMPLETE_INPUT (RECOUNT_047 missing or unbound)'))
    gate('G_recount',complete and rc_ok,None if not rc else {k:rc.get(k) for k in ('cases','replays','labels_main','labels_scale16_main','labels_scale20_main',
         'replay_by_part','misfires_main','amb_rule_applied','words_checked','words_unsound','truth_inconsistent','mismatching_cases','PASS')},
         why=wb or (None if rc else 'INCOMPLETE_INPUT (RECOUNT_047 missing)'))
    mods=(ts or {}).get('per_module') or {};gm=(ts or {}).get('gated_modules') or []
    gate('GTI',bool(gm) and ts.get('passed') is True and all(mods[m].get('returncode')==0 for m in gm),
         None if not ts else {'gated':{m:{'returncode':mods[m].get('returncode'),'tests':mods[m].get('tests')} for m in gm},
                              'reported':{m:{'returncode':v.get('returncode'),'tests':v.get('tests')} for m,v in mods.items() if m not in gm}},
         why=None if ts else 'INCOMPLETE_INPUT (TEST_SUITE_047 missing)')
    lt=ledger();ev=[e for e,_ in lt];times=[t for _,t in lt]
    proc={'order':subseq(ev,PROC_ORDER),'ledger_times_parse':bool(lt) and all(t is not None for t in times),
          'ledger_times_non_decreasing':all(a<=b for a,b in zip(times,times[1:]) if a and b),'commit_order_file':order is not None,'main_sealed':bool(sealed)}
    sc=opt(ROOT/'results/diag-047/SEEDCHECK_047.json')
    gate('G_PROC',all(proc.values()),{'clauses':proc,'events':ev,'required_order':list(PROC_ORDER),'reported_seedcheck_047_PASS':(sc or {}).get('PASS')})
    el=(res or {}).get('total_elapsed_informational')
    gate('G_RT',complete and el is not None and el<=CAP_RT,{'elapsed_s':el,'cap_s':CAP_RT,'cases':len(allc),'replays':len(reps),'cut_d':cut},why=wb)
    # secondary
    cost={}
    for c in allc+reps:
        for a,ar in c['arms'].items():
            x=cost.setdefault(f"{a}/{c['block']}/{c['key']}",{'records':0,'arm_wall_s':0.0,'calls':0,'capped_calls':0,'call_wall_s':0.0,'conflicts':0})
            x['records']+=1;x['arm_wall_s']+=ar.get('arm_wall_informational') or 0.0;x['conflicts']+=ar.get('conflicts_spent') or 0
            for cl in ar['calls']:x['calls']+=1;x['capped_calls']+=bool(cl['capped']);x['call_wall_s']+=cl['wall']
    for x in cost.values():x['arm_wall_s']=round(x['arm_wall_s'],1);x['call_wall_s']=round(x['call_wall_s'],1)
    sec['GAPI_cost']={'pass':None,'observed':dict(sorted(cost.items())),'rule':'reported: wall, calls, capped calls, call wall, conflicts per arm/block/key'}
    rr={a:sum(dd(c,a) for c in sc16) for a in ('API16D','A16_N')}
    sec['GREP16d']={'pass':None,'observed':{**{f'{a}_ID_IDF':rr[a] for a in rr},'of':n16,'ci95':{a:ci(rr[a],n16) for a in rr},
                    'prior':{'043':list(GREP[0]),'045':list(GREP[1]),'046':list(GREP[2])},'prior_ci95':{k:wilson(*v) for k,v in zip(('043','045','046'),GREP)}},
                    'rule':'reported: A16_N scale16 ID+IDF beside 043 (9/12), 045 (10/12), 046 (7/12)'}
    sec['GCAP_class']={'pass':None,'observed':{p:{q:sum(cmp_(c).get('class')==q for c in P(p)) for q in CLASSES} for p in PARTS},'rule':'reported: class counts a1-a3'}
    if not cut:
        n20=sum(dd(c,'API16D') for c in s20)
        sec['GS20_rate']={'pass':None,'observed':{'ID_IDF':n20,'of':len(s20),'ci95':ci(n20,len(s20)),'cost':{k:v for k,v in cost.items() if k.endswith('/main/scale20')}},'rule':'reported'}
    cnt=lambda k,a,L:sum(lab(c,a)==L for c in G(k));nk=lambda k:len(G(k))
    fl={f'{a}/{k}':{L:{'x':cnt(k,a,L),'n':nk(k),'ci95':ci(cnt(k,a,L),nk(k))} for L in LABELS} for k in fresh for a in ARMS_OF[k]}
    return {'schema':'brute.gates.v44_0','study':(res or {}).get('plan',{}).get('study'),'process':'lean','sealed_input_verified':sealed,'label_source':lsrc,
            'cut_d':cut,'conflict_cap':(res or {}).get('conflict_cap'),'budget_conflicts':(res or {}).get('budget_conflicts'),'gates':Gt,'secondary':sec,
            'all_gated_pass':all(g['pass'] for g in Gt.values() if g['pass'] is not None),
            'failed':[k for k,g in Gt.items() if g['pass'] is False],'not_exercised':[k for k,g in Gt.items() if g['pass'] is None],
            'claim':'certify/16d ID/IDF is exact conditional on noise-free readings and true size <= the declared N (family_bound)',
            'reports':{'fresh_labels':fl} if allc else {}}


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--study-dir',default=str(STUDY_DIR));ap.add_argument('--check',action='store_true');a=ap.parse_args()
    obj=build(Path(a.study_dir));out=Path(a.study_dir)/'GATES_047.json'
    if a.check:check(out.read_bytes()==dumps(obj),'GATES_047.json does not reproduce');print('GATES_047 reproduces')
    else:write_new(out,obj);print(json.dumps({k:v['pass'] for k,v in obj['gates'].items()}),obj['failed'])
