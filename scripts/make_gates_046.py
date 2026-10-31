"""Gates for study-046 (BRUTE_PLAN_046 criteria; pre-run deviation #165 definitions), LEAN process. Committed in the source freeze
before run_start_046; nothing is tuned after results are seen. New file; built from scripts/make_gates_045.py (frozen).
Inputs (D = results/study-046): D/main/{RESULTS,SCIENTIFIC,SEAL}.json (18 replay records of the sealed 045 A16_N cases, arm API16;
18 fresh cases: scale16 12, control 6, arms API16 / A16_N merged per case), D/main/RECOUNT_046.json, D/main/REFERENCE_046.json,
D/API_CHECKS_046.json, D/TEST_SUITE_046.json, experiments/COMMIT_ORDER_046.json, results/RESEARCH_LEDGER.jsonl. Missing or partial
input => every data gate FAIL INCOMPLETE_INPUT. Records are accepted only if sha256(RESULTS) equals the seal and no_time(RESULTS)
equals SCIENTIFIC. Labels: recounted labels if G_recount passes, else the study's stored labels (stated).
  GAPI16_replay: 18/18 replay records (12 scale16, 6 control) with the same label as the sealed 045 A16_N record, the same n_min and
     an equal canonical model from state 0 (recount replay comparison if G_recount passes, else the study's); T_final equality
     ('same step') and word equality are reported, not gated (#165 item 1);
  GAPI16_fresh: fresh scale16: API16 WRONG 0 (labels on all 18 fresh cases), API16 ID+IDF >= 8/12 (Wilson 95% CI), and API16 and
     A16_N the same label on >= 11/12 scale16 cases; a disagreement where one side is IDU and that side had a capped call is
     reported as 'capped_unknown', still counted as a disagreement (plan: reported, not WRONG);
  GAPI14_compat: API_CHECKS_046 compat PASS (frozen certify/14 test module passes; sample reproduced byte for byte, s4 cases
     included); GHOST16: API_CHECKS_046 ghost PASS (static closure check on the newly imported modules; no-network run); both
     bound to the certify16.py sha in the source freeze;
  G10: API16 and A16_N ID on each of the 6 fresh controls;
  GQB21: per arm, every logged SAT-call wall and every query wall <= 10.5 s (fresh and replay records);
  GS_ref: REFERENCE_046 on block main: sha bound, 0 mismatches, complete (every decided fresh record audited), mutations 20/20;
  G_sound: study and recount words_unsound 0, words_checked equal, recount truth_inconsistent 0 (fresh and replay);
  G_recount: RECOUNT_046 PASS on the sealed RESULTS, 0 mismatches; GTI: TEST_SUITE_046 passed (gated modules returncode 0);
  G_PROC: preregistration_046, build_authorization_046, seedcheck_046, source_freeze_046, run_start_046, run_end_046 in this order
     (others allowed between), parseable non-decreasing note times; commit-order file; main sealed;
  G_RT: main run total elapsed <= 3600 s.
  Secondary (reported only): GREP16c = API16 and A16_N scale16 ID+IDF with Wilson CI beside 043 (9/12) and 045 (10/12);
     GAPI_cost = per arm and key: arm wall, calls and call wall (wrapper overhead, informational walls).
  PYTHONPATH=. python scripts/make_gates_046.py [--study-dir D] [--check]"""
from __future__ import annotations
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common import load,dumps,write_new,check,sha
from experiments.brute_common_026 import wilson
from scripts.make_gates_034 import opt
from scripts.make_gates_043 import subseq

STUDY_DIR=ROOT/'results/study-046'
EXP_CASES={'scale16':12,'control':6};EXP_REPLAY={'scale16':12,'control':6};ARMS=('API16','A16_N');LABELS=('ID','IDF','AMB','WRONG','IDU')
CAP_RT=3600;QB=10.5;FRESH_BAR=8;AGREE_BAR=11;GREP=((9,12),(10,12))
PROC_ORDER=('preregistration_046','build_authorization_046','seedcheck_046','source_freeze_046','run_start_046','run_end_046')


def ckey(c):return f"{c['block']}/{c['key']}/{c['seed']}"


def ledger():
    from datetime import datetime
    L=[json.loads(x) for x in (ROOT/'results/RESEARCH_LEDGER.jsonl').read_text().splitlines() if x.strip()]
    i0=next((i for i,e in enumerate(L) if e.get('event')=='preregistration_046'),None);out=[]
    for e in (L[i0:] if i0 is not None else []):
        try:t=datetime.fromisoformat(str(e.get('note',''))[:25])
        except ValueError:t=None
        out.append((e['event'],t))
        if e['event']==PROC_ORDER[-1]:break
    return out


def build(study=STUDY_DIR,exp=None,exp_replay=None):
    from brute.evaluation import no_time
    exp=exp or EXP_CASES;exp_replay=EXP_REPLAY if exp_replay is None else exp_replay;study=Path(study);D=study/'main';Gt={};sec={}
    seal=opt(D/'SEAL.json');sci=opt(D/'SCIENTIFIC.json');res=opt(D/'RESULTS.json');rc=opt(D/'RECOUNT_046.json')
    ref=opt(D/'REFERENCE_046.json');ts=opt(study/'TEST_SUITE_046.json');order=opt(ROOT/'experiments/COMMIT_ORDER_046.json')
    api=opt(study/'API_CHECKS_046.json');fz=opt(ROOT/'experiments/BRUTE_SOURCE_FREEZE_046.json')
    rsha=sha(D/'RESULTS.json') if (D/'RESULTS.json').exists() else None
    sealed=(bool(seal) and res is not None and sci is not None and rsha==seal.get('results_sha256')
            and sha(D/'SCIENTIFIC.json')==seal.get('scientific_sha256') and no_time(res)==sci)
    allc=[c for c in (res or {}).get('cases',[]) if c['block']=='main'] if sealed else []
    reps=[c for c in (res or {}).get('replays',[]) if c['block']=='replay'] if sealed else []
    G=lambda k:sorted([c for c in allc if c['key']==k],key=lambda c:c['seed'])
    R=lambda k:sorted([c for c in reps if c['key']==k],key=lambda c:c['seed'])
    sc16=G('scale16');n16=len(sc16)
    complete=(sealed and seal.get('complete') is True and all(len(G(k))==n for k,n in exp.items()) and len(allc)==sum(exp.values())
              and all(sorted(c['arms'])==sorted(ARMS) for c in allc) and all(len(R(k))==n for k,n in exp_replay.items())
              and len(reps)==sum(exp_replay.values()) and all(list(c['arms'])==['API16'] for c in reps))
    wb=None if complete else 'INCOMPLETE_INPUT (main missing, partial, missing arms or not matching its seal)'
    def gate(name,ok,obs,why=None):Gt[name]={'pass':bool(ok) and why is None,'observed':obs,**({'reason':why} if why else {})}
    pc=(rc or {}).get('per_case') or {};pr=(rc or {}).get('per_replay') or {};rcmp=(rc or {}).get('replay_compare') or {}
    rc_bound=bool(rc) and rc.get('results_sha256')==rsha and rc.get('cases')==len((res or {}).get('cases',[])) and rc.get('replays')==len((res or {}).get('replays',[]))
    rc_ok=rc_bound and rc.get('PASS') is True and rc.get('mismatching_cases')==0
    rrec=lambda c,a:((pc.get(ckey(c)) or {}).get(a) or {}) if rc_bound else {}
    lab=(lambda c,a:rrec(c,a).get('label')) if rc_ok else (lambda c,a:c['arms'][a]['label'])
    lsrc='recount' if rc_ok else 'study labels (G_recount did not pass)'
    dd=lambda c,a:a in c['arms'] and lab(c,a) in ('ID','IDF')
    ci=lambda x,n:wilson(x,n) if n else None
    # GAPI16_replay
    cmp_=(lambda c:rcmp.get(ckey(c)) or {}) if rc_ok else (lambda c:c.get('replay') or {})
    rp=[[c['key'],c['seed'],cmp_(c).get('label'),cmp_(c).get('n_min'),cmp_(c).get('canonical_model_equal'),cmp_(c).get('same'),
         cmp_(c).get('same_step'),(c.get('replay') or {}).get('words_equal'),(c.get('replay') or {}).get('first_word_divergence'),
         (c.get('replay') or {}).get('capped')] for k in EXP_REPLAY for c in R(k)]
    same=sum(bool(x[5]) for x in rp);nrep=len(rp)
    gate('GAPI16_replay',complete and nrep==sum(exp_replay.values()) and same==nrep,{'same':same,'of':nrep,'ci95':ci(same,nrep),
         'same_step':sum(bool(x[6]) for x in rp),'words_equal':sum(bool(x[7]) for x in rp),'source':'recount' if rc_ok else 'study',
         'per_case':rp,'columns':['key','seed','label[api,sealed]','n_min[api,sealed]','canonical_model_equal','same','same_step',
                                  'words_equal','first_word_divergence','capped[api,sealed]'],
         'rule':'same label, same n_min and equal canonical model as the sealed 045 A16_N record, 18/18'},why=wb)
    # GAPI16_fresh
    wrong=[[ckey(c),a] for c in allc for a in ARMS if lab(c,a)=='WRONG' or c['arms'][a]['label']=='WRONG']
    wrong_api=[x for x in wrong if x[1]=='API16'];nA=sum(dd(c,'API16') for c in sc16)
    agree=[];dis=[]
    for c in sc16:
        la,ln=lab(c,'API16'),lab(c,'A16_N')
        if la==ln:agree.append(c['seed']);continue
        capu=[a for a in ARMS if lab(c,a)=='IDU' and c['arms'][a]['capped']>0]
        dis.append({'seed':c['seed'],'API16':la,'A16_N':ln,'capped_unknown':capu})
    gate('GAPI16_fresh',complete and not wrong_api and nA>=FRESH_BAR and len(agree)>=AGREE_BAR,
         {'API16_WRONG':wrong_api,'all_WRONG':wrong,'API16_ID_IDF':nA,'of':n16,'ci95':ci(nA,n16),'agree':len(agree),'agree_ci95':ci(len(agree),n16),
          'disagreements':dis,'label_source':lsrc,'per_case':[[c['seed'],lab(c,'API16'),lab(c,'A16_N')] for c in sc16],
          'rule':f'API16 WRONG 0; API16 ID+IDF >= {FRESH_BAR}/12; same label as A16_N on >= {AGREE_BAR}/12 (capped unknowns reported)'},why=wb)
    # GAPI14_compat / GHOST16
    c16=(fz or {}).get('sha256_files',{}).get('brute/api/certify16.py');abound=bool(api) and c16 is not None and api.get('certify16_sha256')==c16==sha(ROOT/'brute/api/certify16.py')
    ac=(api or {}).get('compat') or {};ag=(api or {}).get('ghost') or {}
    gate('GAPI14_compat',abound and ac.get('PASS') is True,None if not api else {'bound_to_freeze':abound,'cases':ac.get('cases'),'s4_cases':ac.get('s4_cases'),
         'tests':ac.get('tests'),'sample_sha256':ac.get('sample_sha256')},why=None if api else 'INCOMPLETE_INPUT (API_CHECKS_046 missing)')
    gate('GHOST16',abound and ag.get('PASS') is True,None if not api else {'bound_to_freeze':abound,'newly_imported':ag.get('newly_imported'),
         'new_flagged':ag.get('new_flagged'),'closure_flagged_reported':ag.get('closure_flagged_reported'),'no_network_run':ag.get('no_network_run'),
         'static_pass':ag.get('static_pass'),'network_pass':ag.get('network_pass')},why=None if api else 'INCOMPLETE_INPUT (API_CHECKS_046 missing)')
    # G10
    g10=[(c['seed'],{a:lab(c,a) for a in ARMS}) for c in G('control')]
    gate('G10',complete and len(g10)==exp['control'] and all(all(L=='ID' for L in x[1].values()) for x in g10),
         {'cases':g10,'rule':'API16 and A16_N ID on every fresh control (IDF is not ID)'},why=wb)
    # GQB21
    per={};over=[];kills=0;ncalls=0
    for c in allc+reps:
        for a,ar in c['arms'].items():
            kills+=ar['kills']
            for x in ar['calls']:
                ncalls+=1;per[a]=max(per.get(a,0),x['wall'])
                if x['wall']>QB:over.append([f'{ckey(c)}/{a}',x['phase'],x['n'],round(x['wall'],3)])
            q=ar['query_max_s']
            if q is not None:
                per[a]=max(per.get(a,0),q)
                if q>QB:over.append([f'{ckey(c)}/{a}','query',None,round(q,3)])
    gate('GQB21',complete and bool(per) and not over,{'max_s_by_arm':{a:round(v,3) for a,v in sorted(per.items())},'bound_s':QB,'over':over,
         'hard_kills':kills,'calls_logged':ncalls},why=wb)
    # GS_ref
    mt=(ref or {}).get('mutation_test') or {};rb=bool(ref) and ref.get('study_results_sha256')==rsha and ref.get('block')=='main'
    vac=bool(ref) and ref.get('decided')==0
    robs=None if not ref else {k:ref.get(k) for k in ('block','scope','records','decided','audited','not_audited','complete','per_arm','not_reached',
                               'k_spent_as_amb','verdicts_checked','mismatch_count','vacuous','PASS','elapsed_informational')}|{'mutations':mt.get('detected'),'of':mt.get('mutations')}
    gate('GS_ref',rb and ref.get('mismatch_count')==0 and ref.get('complete') is True and (vac or mt.get('detected')==mt.get('mutations')==20) and ref.get('PASS') is True,
         robs,why=wb or (None if ref else 'INCOMPLETE_INPUT (REFERENCE_046 missing)'))
    # G_sound
    snd={'words_checked':sum(ar.get('words_checked',0) for c in allc+reps for ar in c['arms'].values()),
         'words_unsound':sum(ar.get('words_unsound',0) for c in allc+reps for ar in c['arms'].values()),
         'recount_bound':rc_bound,'recount_words_checked':(rc or {}).get('words_checked'),'recount_words_unsound':(rc or {}).get('words_unsound'),
         'recount_truth_inconsistent':(rc or {}).get('truth_inconsistent')}
    gate('G_sound',complete and rc_bound and snd['words_unsound']==0 and snd['recount_words_unsound']==0 and snd['recount_truth_inconsistent']==0
         and snd['recount_words_checked']==snd['words_checked'],snd,why=wb or (None if rc_bound else 'INCOMPLETE_INPUT (RECOUNT_046 missing or unbound)'))
    gate('G_recount',complete and rc_ok,None if not rc else {k:rc.get(k) for k in ('cases','replays','labels_main','labels_scale16_main','replay_labels','replay_same',
         'replay_same_step','misfires_main','amb_rule_applied','words_checked','words_unsound','truth_inconsistent','mismatching_cases','PASS')},
         why=wb or (None if rc else 'INCOMPLETE_INPUT (RECOUNT_046 missing)'))
    # GTI
    mods=(ts or {}).get('per_module') or {};gm=(ts or {}).get('gated_modules') or []
    gate('GTI',bool(gm) and ts.get('passed') is True and all(mods[m].get('returncode')==0 for m in gm),
         None if not ts else {'gated':{m:{'returncode':mods[m].get('returncode'),'tests':mods[m].get('tests')} for m in gm},
                              'reported':{m:{'returncode':v.get('returncode'),'tests':v.get('tests')} for m,v in mods.items() if m not in gm}},
         why=None if ts else 'INCOMPLETE_INPUT (TEST_SUITE_046 missing)')
    # G_PROC
    lt=ledger();ev=[e for e,_ in lt];times=[t for _,t in lt]
    proc={'order':subseq(ev,PROC_ORDER),'ledger_times_parse':bool(lt) and all(t is not None for t in times),
          'ledger_times_non_decreasing':all(a<=b for a,b in zip(times,times[1:]) if a and b),'commit_order_file':order is not None,'main_sealed':bool(sealed)}
    sc=opt(ROOT/'results/diag-046/SEEDCHECK_046.json')
    gate('G_PROC',all(proc.values()),{'clauses':proc,'events':ev,'required_order':list(PROC_ORDER),'reported_seedcheck_046_PASS':(sc or {}).get('PASS')})
    el=(res or {}).get('total_elapsed_informational')
    gate('G_RT',complete and el is not None and el<=CAP_RT,{'elapsed_s':el,'cap_s':CAP_RT,'cases':len(allc),'replays':len(reps)},why=wb)
    # secondary
    cost={}
    for c in allc+reps:
        for a,ar in c['arms'].items():
            x=cost.setdefault(f"{a}/{c['block']}/{c['key']}",{'records':0,'arm_wall_s':0.0,'calls':0,'capped_calls':0,'call_wall_s':0.0})
            x['records']+=1;x['arm_wall_s']+=ar.get('arm_wall_informational') or 0.0
            for cl in ar['calls']:x['calls']+=1;x['capped_calls']+=bool(cl['capped']);x['call_wall_s']+=cl['wall']
    for x in cost.values():x['arm_wall_s']=round(x['arm_wall_s'],1);x['call_wall_s']=round(x['call_wall_s'],1)
    sec['GAPI_cost']={'pass':None,'observed':dict(sorted(cost.items())),'rule':'reported: arm wall, calls, capped calls, call wall per arm/block/key (informational walls)'}
    rr={a:sum(dd(c,a) for c in sc16) for a in ARMS}
    sec['GREP16c']={'pass':None,'observed':{**{f'{a}_ID_IDF':rr[a] for a in ARMS},'of':n16,'ci95':{a:ci(rr[a],n16) for a in ARMS},
                    'study_043':list(GREP[0]),'study_043_ci95':wilson(*GREP[0]),'study_045_A16_N':list(GREP[1]),'study_045_ci95':wilson(*GREP[1])},
                    'rule':'reported: scale16 ID+IDF beside 043 (9/12) and 045 (10/12)'}
    cnt=lambda k,a,L:sum(lab(c,a)==L for c in G(k));nk=lambda k:len(G(k))
    fl={f'{a}/{k}':{L:{'x':cnt(k,a,L),'n':nk(k),'ci95':ci(cnt(k,a,L),nk(k))} for L in LABELS} for a in ARMS for k in exp}
    return {'schema':'brute.gates.v43_0','study':'BRUTE-0430-CERTIFY16-046','process':'lean','sealed_input_verified':sealed,'label_source':lsrc,'gates':Gt,
            'secondary':sec,'all_gated_pass':all(g['pass'] for g in Gt.values() if g['pass'] is not None),
            'failed':[k for k,g in Gt.items() if g['pass'] is False],'not_exercised':[k for k,g in Gt.items() if g['pass'] is None],
            'claim':'certify/16 ID/IDF is exact conditional on noise-free readings and true size <= the declared N (family_bound)',
            'reports':{'fresh_labels':fl} if allc else {}}


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--study-dir',default=str(STUDY_DIR));ap.add_argument('--check',action='store_true');a=ap.parse_args()
    obj=build(Path(a.study_dir));out=Path(a.study_dir)/'GATES_046.json'
    if a.check:check(out.read_bytes()==dumps(obj),'GATES_046.json does not reproduce');print('GATES_046 reproduces')
    else:write_new(out,obj);print(json.dumps({k:v['pass'] for k,v in obj['gates'].items()}),obj['failed'])
