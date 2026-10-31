"""Gates for study-045 (BRUTE_PLAN_045 criteria; pre-run deviation #163 definitions), LEAN process. Committed in the source freeze
before run_start_045; nothing is tuned after results are seen. New file; built from scripts/make_gates_044.py (frozen).
Inputs (D = results/study-045): D/main/{RESULTS,SCIENTIFIC,SEAL}.json (18 fresh cases: scale16 12, control 6; arms A16_N /
A16_nf1 / A16_nf2 merged per case), D/main/RECOUNT_045.json, D/main/REFERENCE_045.json, D/TEST_SUITE_045.json,
experiments/COMMIT_ORDER_045.json, results/RESEARCH_LEDGER.jsonl. Missing or partial input => every data gate FAIL
INCOMPLETE_INPUT. Records are accepted only if sha256(RESULTS) equals the seal and no_time(RESULTS) equals SCIENTIFIC.
Labels: recounted labels if G_recount passes, else the study's stored labels (stated). A nf ID / IDF is the bounded claim ID_d /
IDF_d (unique among machines with at most n_min+delta states; not full N-freedom).
  GNF_bound: every A16_nf1 / A16_nf2 decided record audited by REFERENCE_045 at bound n_min+delta, 0 counted mismatches on the nf
     arms (a [stop, ID, WRONG] misfire is bucketed to GNF_misfire, #163 item 4), mutations 20/20, sha bound;
  GNF_agree: scale16: A16_nf2 ID+IDF >= 8/12 AND on the cases where A16_N is ID or IDF, A16_nf2 has the same stop kind and an
     equivalent model (ID: equal canonical model from state 0; IDF: equal behaviour from the current states, i.e. both
     future_match true) in >= 90% of those cases (#163 item 5); vacuous agreement stated if A16_N decides none; Wilson 95% CIs;
  GNF_misfire: A16_nf2 misfires = 0 on fresh scale16 and controls (misfire = WRONG label, or IDF with future_match false; recount
     values, reference misfire bucket also read); A16_nf1 misfires reported with a Wilson CI over its ID+IDF, not gated;
  G10: every arm ID on each of the 6 controls (as written; an IDF is not ID);
  GLO_sem: A16_N WRONG 0 on every fresh case; any two arms both ID/IDF on a case => same n_min;
  GQB20: per arm, every logged SAT-call wall and every query wall <= 10.5 s;
  GS_ref: REFERENCE_045 on block main (scope #163 item 4): sha bound, 0 counted mismatches on audited records, every decided
     A16_nf2 record audited, mutations 20/20 (vacuous pass stated if 0 decided); 'complete' and the not_audited list are reported;
  GTI: TEST_SUITE_045 passed (gated modules returncode 0);
  G_PROC: preregistration_045, build_authorization_045, seedcheck_045, source_freeze_045, run_start_045, run_end_045 in this order
     (others allowed between), parseable non-decreasing note times; commit-order file; main sealed;
  G_RT: total elapsed <= 3600 s; G_recount: RECOUNT_045 PASS on the sealed RESULTS, 0 mismatches;
  G_sound: study and recount words_unsound 0, words_checked equal, recount truth_inconsistent 0.
  Secondary (reported only): GNF_cost = per arm and key: calls, capped calls and summed call wall by phase, arm wall; GREP16b =
     A16_N scale16 ID+IDF with Wilson CI beside 043 GREP16 9/12.
  PYTHONPATH=. python scripts/make_gates_045.py [--study-dir D] [--check]"""
from __future__ import annotations
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common import load,dumps,write_new,check,sha
from experiments.brute_common_026 import wilson
from scripts.make_gates_034 import opt
from scripts.make_gates_043 import subseq
from scripts.recount_033 import canon

STUDY_DIR=ROOT/'results/study-045'
EXP_CASES={'scale16':12,'control':6};ARMS=('A16_N','A16_nf1','A16_nf2');NF=('A16_nf1','A16_nf2');LABELS=('ID','IDF','AMB','WRONG','IDU')
CAP_RT=3600;QB={a:10.5 for a in ARMS};AGREE_BAR=8;AGREE_FRAC=0.9;GREP16_043=(9,12)
PROC_ORDER=('preregistration_045','build_authorization_045','seedcheck_045','source_freeze_045','run_start_045','run_end_045')


def ckey(c):return f"{c['block']}/{c['key']}/{c['seed']}"


def ledger():
    from datetime import datetime
    L=[json.loads(x) for x in (ROOT/'results/RESEARCH_LEDGER.jsonl').read_text().splitlines() if x.strip()]
    i0=next((i for i,e in enumerate(L) if e.get('event')=='preregistration_045'),None);out=[]
    for e in (L[i0:] if i0 is not None else []):
        try:t=datetime.fromisoformat(str(e.get('note',''))[:25])
        except ValueError:t=None
        out.append((e['event'],t))
        if e['event']==PROC_ORDER[-1]:break
    return out


def build(study=STUDY_DIR,exp=None):
    from brute.evaluation import no_time
    exp=exp or EXP_CASES;study=Path(study);D=study/'main';Gt={};sec={}
    seal=opt(D/'SEAL.json');sci=opt(D/'SCIENTIFIC.json');res=opt(D/'RESULTS.json');rc=opt(D/'RECOUNT_045.json')
    ref=opt(D/'REFERENCE_045.json');ts=opt(study/'TEST_SUITE_045.json');order=opt(ROOT/'experiments/COMMIT_ORDER_045.json')
    rsha=sha(D/'RESULTS.json') if (D/'RESULTS.json').exists() else None
    sealed=(bool(seal) and res is not None and sci is not None and rsha==seal.get('results_sha256')
            and sha(D/'SCIENTIFIC.json')==seal.get('scientific_sha256') and no_time(res)==sci)
    allc=[c for c in (res or {}).get('cases',[]) if c['block']=='main'] if sealed else []
    G=lambda k:sorted([c for c in allc if c['key']==k],key=lambda c:c['seed'])
    sc16=G('scale16');n16=len(sc16)
    complete=(sealed and seal.get('complete') is True and all(len(G(k))==n for k,n in exp.items()) and len(allc)==sum(exp.values())
              and all(sorted(c['arms'])==sorted(ARMS) for c in allc))
    wb=None if complete else 'INCOMPLETE_INPUT (main missing, partial, missing arms or not matching its seal)'
    def gate(name,ok,obs,why=None):Gt[name]={'pass':bool(ok) and why is None,'observed':obs,**({'reason':why} if why else {})}
    pc=(rc or {}).get('per_case') or {}
    rc_bound=bool(rc) and rc.get('results_sha256')==rsha and rc.get('cases')==len((res or {}).get('cases',[]))
    rc_ok=rc_bound and rc.get('PASS') is True and rc.get('mismatching_cases')==0
    rrec=lambda c,a:((pc.get(ckey(c)) or {}).get(a) or {}) if rc_bound else {}
    rlab=lambda c,a:rrec(c,a).get('label')
    lab=(lambda c,a:rlab(c,a)) if rc_ok else (lambda c,a:c['arms'][a]['label'])
    fmatch=(lambda c,a:rrec(c,a).get('future_match')) if rc_ok else (lambda c,a:c['arms'][a].get('future_match'))
    lsrc='recount' if rc_ok else 'study labels (G_recount did not pass)'
    dd=lambda c,a:a in c['arms'] and lab(c,a) in ('ID','IDF')
    misfire=lambda c,a:lab(c,a)=='WRONG' or (lab(c,a)=='IDF' and not fmatch(c,a))
    ci=lambda x,n:wilson(x,n) if n else None
    mt=(ref or {}).get('mutation_test') or {};rb=bool(ref) and ref.get('study_results_sha256')==rsha and ref.get('block')=='main'
    rpa=(ref or {}).get('per_arm') or {}
    # GNF_bound
    nf_dec=[f"{ckey(c)}/{a}" for c in allc for a in NF if c['arms'][a]['stop']!='unknown']
    na=set((ref or {}).get('not_audited') or [])
    nf_cnt=[m for m in (ref or {}).get('mismatches',[]) if m[0].rsplit('/',1)[-1] in NF]
    gnb=rb and not (set(nf_dec)&na) and not nf_cnt and mt.get('detected')==mt.get('mutations')==20
    gate('GNF_bound',complete and gnb,None if not ref else {'nf_decided':len(nf_dec),'nf_not_audited':sorted(set(nf_dec)&na),'nf_counted_mismatches':nf_cnt,
         'per_arm':{a:rpa.get(a) for a in NF},'mutations':mt.get('detected'),'of':mt.get('mutations'),
         'claim':'bounded: unique among machines with at most n_min+delta states; not full N-freedom'},
         why=wb or (None if ref else 'INCOMPLETE_INPUT (REFERENCE_045 missing)'))
    # GNF_agree
    nf2=sum(dd(c,'A16_nf2') for c in sc16);base=[c for c in sc16 if dd(c,'A16_N')]
    def agree(c):
        if lab(c,'A16_nf2')!=lab(c,'A16_N'):return False
        mN=c['arms']['A16_N']['model'];m2=c['arms']['A16_nf2']['model']
        if lab(c,'A16_N')=='ID':return canon(mN[0],mN[1],0)==canon(m2[0],m2[1],0)
        return bool(fmatch(c,'A16_N') and fmatch(c,'A16_nf2'))
    ag=sum(agree(c) for c in base);nb=len(base);frac=(ag/nb) if nb else None
    gate('GNF_agree',complete and nf2>=AGREE_BAR and (nb==0 or frac>=AGREE_FRAC),{'A16_nf2_ID_IDF':nf2,'of':n16,'ci95':ci(nf2,n16),
         'A16_N_ID_IDF':nb,'agree':ag,'agree_frac':frac,'agree_ci95':ci(ag,nb),'vacuous_agreement':nb==0,'label_source':lsrc,
         'per_case':[[c['seed'],lab(c,'A16_N'),lab(c,'A16_nf1'),lab(c,'A16_nf2'),agree(c) if dd(c,'A16_N') else None] for c in sc16],
         'rule':f'A16_nf2 ID+IDF >= {AGREE_BAR}/12 and same stop kind + equivalent model on >= 90% of A16_N ID/IDF cases'},why=wb)
    # GNF_misfire
    mf={a:[[ckey(c),lab(c,a)] for c in allc if dd(c,a) and misfire(c,a)] for a in NF}
    nd={a:sum(dd(c,a) for c in allc) for a in NF}
    gate('GNF_misfire',complete and not mf['A16_nf2'],{'A16_nf2_misfires':mf['A16_nf2'],'A16_nf2_decided':nd['A16_nf2'],
         'A16_nf2_ci95':ci(len(mf['A16_nf2']),nd['A16_nf2']),'A16_nf1_misfires_reported':mf['A16_nf1'],'A16_nf1_decided':nd['A16_nf1'],
         'A16_nf1_ci95':ci(len(mf['A16_nf1']),nd['A16_nf1']),'reference_misfire_bucket':(ref or {}).get('misfires'),
         'rule':'misfire = WRONG, or IDF whose model from s1 is not equivalent to the truth from its true state; A16_nf2 = 0 gated'},why=wb)
    # G10
    g10=[(c['seed'],{a:lab(c,a) for a in ARMS}) for c in G('control')]
    gate('G10',complete and len(g10)==exp['control'] and all(all(L=='ID' for L in x[1].values()) for x in g10),
         {'cases':g10,'rule':'every arm ID on every control (IDF is not ID)'},why=wb)
    # GLO_sem
    wrong=[ckey(c) for c in allc if lab(c,'A16_N')=='WRONG' or c['arms']['A16_N']['label']=='WRONG']
    pairs=[(a,b) for i,a in enumerate(ARMS) for b in ARMS[i+1:]]
    nm=[[ckey(c),a,b,c['arms'][a]['n_min'],c['arms'][b]['n_min']] for c in allc for a,b in pairs
        if c['arms'][a]['stop'] in ('ID','IDF') and c['arms'][b]['stop'] in ('ID','IDF') and c['arms'][a]['n_min']!=c['arms'][b]['n_min']]
    gate('GLO_sem',complete and not wrong and not nm,{'A16_N_WRONG':wrong,'n_min_differs':nm,'rule':'A16_N WRONG 0; decided arms agree on n_min'},why=wb)
    # GQB20
    per={};over=[];kills=0;ncalls=0
    for c in allc:
        for a,ar in c['arms'].items():
            kills+=ar['kills']
            for x in ar['calls']:
                ncalls+=1;per[a]=max(per.get(a,0),x['wall'])
                if x['wall']>QB[a]:over.append([f'{ckey(c)}/{a}',x['phase'],x['n'],round(x['wall'],3)])
            q=ar['query_max_s']
            if q is not None:
                per[a]=max(per.get(a,0),q)
                if q>QB[a]:over.append([f'{ckey(c)}/{a}','query',None,round(q,3)])
    gate('GQB20',complete and bool(per) and not over,{'max_s_by_arm':{a:round(v,3) for a,v in sorted(per.items())},'bound_s':10.5,'over':over,
         'hard_kills':kills,'calls_logged':ncalls},why=wb)
    # GS_ref
    vac=bool(ref) and ref.get('decided')==0
    robs=None if not ref else {k:ref.get(k) for k in ('block','scope','records','decided','audited','not_audited','complete','nf2_all_audited','per_arm','not_reached',
                               'k_spent_as_amb','verdicts_checked','mismatch_count','vacuous','PASS','elapsed_informational')}|{'mutations':mt.get('detected'),'of':mt.get('mutations')}
    gate('GS_ref',rb and ref.get('mismatch_count')==0 and ref.get('nf2_all_audited') is True and (vac or mt.get('detected')==mt.get('mutations')==20) and ref.get('PASS') is True,
         robs,why=wb or (None if ref else 'INCOMPLETE_INPUT (REFERENCE_045 missing)'))
    # GTI
    mods=(ts or {}).get('per_module') or {};gm=(ts or {}).get('gated_modules') or []
    gate('GTI',bool(gm) and ts.get('passed') is True and all(mods[m].get('returncode')==0 for m in gm),
         None if not ts else {'gated':{m:{'returncode':mods[m].get('returncode'),'tests':mods[m].get('tests')} for m in gm},
                              'reported':{m:{'returncode':v.get('returncode'),'tests':v.get('tests')} for m,v in mods.items() if m not in gm}},
         why=None if ts else 'INCOMPLETE_INPUT (TEST_SUITE_045 missing)')
    # G_PROC
    lt=ledger();ev=[e for e,_ in lt];times=[t for _,t in lt]
    proc={'order':subseq(ev,PROC_ORDER),'ledger_times_parse':bool(lt) and all(t is not None for t in times),
          'ledger_times_non_decreasing':all(a<=b for a,b in zip(times,times[1:]) if a and b),'commit_order_file':order is not None,'main_sealed':bool(sealed)}
    sc=opt(ROOT/'results/diag-045/SEEDCHECK_045.json')
    gate('G_PROC',all(proc.values()),{'clauses':proc,'events':ev,'required_order':list(PROC_ORDER),'reported_seedcheck_045_PASS':(sc or {}).get('PASS')})
    el=(res or {}).get('total_elapsed_informational')
    gate('G_RT',complete and el is not None and el<=CAP_RT,{'elapsed_s':el,'cap_s':CAP_RT,'cases':len(allc)},why=wb)
    gate('G_recount',complete and rc_ok,None if not rc else {k:rc.get(k) for k in ('cases','labels_main','misfires_main','amb_rule_applied','words_checked','words_unsound','truth_inconsistent','mismatching_cases','PASS')},
         why=wb or (None if rc else 'INCOMPLETE_INPUT (RECOUNT_045 missing)'))
    snd={'words_checked':sum(ar.get('words_checked',0) for c in allc for ar in c['arms'].values()),
         'words_unsound':sum(ar.get('words_unsound',0) for c in allc for ar in c['arms'].values()),
         'recount_bound':rc_bound,'recount_words_checked':(rc or {}).get('words_checked'),'recount_words_unsound':(rc or {}).get('words_unsound'),
         'recount_truth_inconsistent':(rc or {}).get('truth_inconsistent')}
    gate('G_sound',complete and rc_bound and snd['words_unsound']==0 and snd['recount_words_unsound']==0 and snd['recount_truth_inconsistent']==0
         and snd['recount_words_checked']==snd['words_checked'],snd,why=wb or (None if rc_bound else 'INCOMPLETE_INPUT (RECOUNT_045 missing or unbound)'))
    # secondary
    cost={}
    for c in allc:
        for a,ar in c['arms'].items():
            x=cost.setdefault(f"{a}/{c['key']}",{'arm_wall_s':0.0,'phases':{}});x['arm_wall_s']+=ar.get('arm_wall_informational') or 0.0
            for cl in ar['calls']:
                p=x['phases'].setdefault(cl['phase'],{'calls':0,'capped':0,'wall_s':0.0});p['calls']+=1;p['capped']+=bool(cl['capped']);p['wall_s']+=cl['wall']
    for x in cost.values():
        x['arm_wall_s']=round(x['arm_wall_s'],1)
        for p in x['phases'].values():p['wall_s']=round(p['wall_s'],1)
    sec['GNF_cost']={'pass':None,'observed':dict(sorted(cost.items())),'rule':'reported: calls, capped and call wall by phase; arm wall (informational)'}
    rN=sum(dd(c,'A16_N') for c in sc16)
    sec['GREP16b']={'pass':None,'observed':{'A16_N_ID_IDF':rN,'of':n16,'ci95':ci(rN,n16),'study_043_GREP16':list(GREP16_043),'study_043_ci95':wilson(*GREP16_043)},
                    'rule':'reported: A16_N replicates 043 GREP16 (9/12)'}
    cnt=lambda k,a,L:sum(lab(c,a)==L for c in G(k));nk=lambda k:len(G(k))
    fl={f'{a}/{k}':{L:{'x':cnt(k,a,L),'n':nk(k),'ci95':ci(cnt(k,a,L),nk(k))} for L in LABELS} for a in ARMS for k in exp}
    return {'schema':'brute.gates.v42_0','study':'BRUTE-0420-A16-NFREE-STOP-045','process':'lean','sealed_input_verified':sealed,'label_source':lsrc,'gates':Gt,
            'secondary':sec,'all_gated_pass':all(g['pass'] for g in Gt.values() if g['pass'] is not None),
            'failed':[k for k,g in Gt.items() if g['pass'] is False],'not_exercised':[k for k,g in Gt.items() if g['pass'] is None],
            'bounded_claim':'A16_nf ID/IDF = unique among machines with at most n_min+delta states (bounded claim; not full N-freedom)',
            'reports':{'fresh_labels':fl} if allc else {}}


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--study-dir',default=str(STUDY_DIR));ap.add_argument('--check',action='store_true');a=ap.parse_args()
    obj=build(Path(a.study_dir));out=Path(a.study_dir)/'GATES_045.json'
    if a.check:check(out.read_bytes()==dumps(obj),'GATES_045.json does not reproduce');print('GATES_045 reproduces')
    else:write_new(out,obj);print(json.dumps({k:v['pass'] for k,v in obj['gates'].items()}),obj['failed'])
