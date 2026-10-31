"""Gates for study-041 (BRUTE_PLAN_041; deviation #154 definitions), LEAN process. Committed in the source freeze before
run_start_041; nothing is tuned after results are seen. New file; built from scripts/make_gates_040.py (frozen).
Inputs (D = results/study-041): D/main/{RESULTS,SCIENTIFIC,SEAL}.json (240 replays: part c 60, b 30, a 150; 18 fresh cases:
perm12 12, control 6, arms A14 / A15 / A15_cube), D/main/RECOUNT_041.json, D/main/REFERENCE_041.json, D/TEST_SUITE_041.json,
experiments/COMMIT_ORDER_041.json, results/RESEARCH_LEDGER.jsonl. Missing or partial input => every data gate FAIL INCOMPLETE_INPUT.
Records are accepted only if sha256(RESULTS) equals the seal and no_time(RESULTS) equals SCIENTIFIC.
Definitions (deviation #154):
  decided = stop not 'unknown'; a replay's partner is the E0 record of the same (part, study, key, seed, repeat);
  GAUD_sem: no decided replay has (stop, n_min) different from its decided E0 partner; no decided A15 / A15_cube fresh record has
     (stop, n_min) different from a decided A14 on the same case; recounted WRONG 0 for every replay and every arm; stored fresh
     labels equal the recount. Decided-where-E0-unknown records are reported (gains), not failures;
  GAUD_loc: GINC15 cells (10540007,E3), (10540008,E3), (10540008,E4). For V in E1, E2: V reproduces the loss if, in >= 2 of the 3
     repeats, V is unknown on >= 1 of the 2 part-b traces where E0 decided (same repeat); V matches E0 if, in >= 2 of the 3 repeats,
     V's stop equals E0's on both traces. Pass iff exactly one of E1 / E2 reproduces the loss and the other matches E0 (names the
     component: E1 = apartness clauses, E2 = fixed-colour clique);
  GAUD_time: over the 42 traces of parts a and c, r = median(call wall E3) / median(call wall E0) on the same trace (traces where
     either has no call are dropped and listed); statistic mean(r); seed-bootstrap 95% CI (10000 resamples, random.Random(41),
     percentile); pass if the CI lower end > 1. E1, E2, E4 ratios reported;
  GAUD_stab: part b, the stop is identical across the 3 repeats in >= 9 of the 10 (trace, variant) cells;
  GPERM16: fresh perm12, on every case where A14 is decided, A15 and A15_cube give A14's stop and n_min (unknown fails);
  GQB16: every logged SAT-call wall and every query wall <= 10.5 s over every replay and arm; overruns listed with phase;
  G_sound: study and recount words_unsound 0, recount words_checked equal to the study's, recount truth_inconsistent 0;
  G10: every arm ID on each of the 6 fresh controls (recounted label);
  GS_ref: REFERENCE_041 on part c, E1 and E2: 24 records over 12 traces, 0 mismatches, decided > 0, mutations 20/20, sha bound;
  GTI: TEST_SUITE_041 passed (gated 041 modules returncode 0; frozen modules reported only);
  G_PROC: ledger events preregistration_041, seedcheck_041, build_authorization_041 (user-specified order, deviation #154),
     source_freeze_041, run_start_041, run_end_041, recount_041, reference_041, tests_041 present, in order, parseable
     non-decreasing times; commit-order file; main sealed;
  G_RT: total elapsed <= 1800 s; G_recount: RECOUNT_041 PASS on the sealed RESULTS with 0 mismatches.
  GCLS16 (secondary): clause and variable counts per variant and size; GPH16 (secondary): calls and capped calls by phase
     (least, rival = future + start at call level, cube) per variant and arm.
  PYTHONPATH=. python scripts/make_gates_041.py [--study-dir D] [--check]"""
from __future__ import annotations
import argparse,json,random,sys
from pathlib import Path
from statistics import median
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common import load,dumps,write_new,check,sha
from experiments.brute_common_026 import wilson
from scripts.make_gates_034 import opt

STUDY_DIR=ROOT/'results/study-041'
EXP_REPLAYS={'c':60,'b':30,'a':150};EXP_CASES={'perm12':12,'control':6}
VARIANTS=('E0','E1','E2','E3','E4');ARMS=('A14','A15','A15_cube');LABELS=('ID','IDF','AMB','WRONG','IDU')
CAP=1800;QB=10.5;BOOT=10000;BOOT_SEED=41
GINC=(10540007,10540008);GINC_CELLS=((10540007,'E3'),(10540008,'E3'),(10540008,'E4'));COMPONENT={'E1':'apartness clauses','E2':'fixed-colour clique'}
PROC_ORDER=('preregistration_041','seedcheck_041','build_authorization_041','source_freeze_041','run_start_041','run_end_041','recount_041',
            'reference_041','tests_041')


def boot(v,n=BOOT,seed=BOOT_SEED):
    if not v:return None
    rng=random.Random(seed);m=len(v);s=sorted(sum(v[rng.randrange(m)] for _ in range(m))/m for _ in range(n))
    return [round(s[int(0.025*n)],4),round(s[int(0.975*n)-1],4)]


def tkey(r):return (r['part'],r['study'],r['key'],r['seed'],r['repeat'])
def rid(r):return '/'.join(map(str,tkey(r)+(r['variant'],)))
def ckey(c):return f"{c['block']}/{c['key']}/{c['seed']}"
def dec(x):return x['stop']!='unknown'
def sn(x):return [x['stop'],x['n_min']]


def ledger():
    from datetime import datetime
    L=[json.loads(x) for x in (ROOT/'results/RESEARCH_LEDGER.jsonl').read_text().splitlines() if x.strip()]
    i0=next((i for i,e in enumerate(L) if e.get('event')=='preregistration_041'),None);out=[]
    for e in (L[i0:] if i0 is not None else []):
        try:t=datetime.fromisoformat(str(e.get('note',''))[:25])
        except ValueError:t=None
        out.append((e['event'],t))
        if e['event']==PROC_ORDER[-1]:break
    return out


def ratios(reps,v,parts=('a','c')):
    idx={(tkey(r),r['variant']):r for r in reps};out=[];dropped=[]
    for r in reps:
        if r['part'] not in parts or r['variant']!='E0':continue
        x=idx.get((tkey(r),v))
        a=[c['wall'] for c in r['calls']];b=[c['wall'] for c in (x or {}).get('calls',[])]
        if not a or not b or median(a)<=0:dropped.append('/'.join(map(str,tkey(r))));continue
        out.append(('/'.join(map(str,tkey(r))),median(b)/median(a)))
    return out,dropped


def build(study=STUDY_DIR):
    from brute.evaluation import no_time
    study=Path(study);D=study/'main';Gt={};sec={}
    seal=opt(D/'SEAL.json');sci=opt(D/'SCIENTIFIC.json');res=opt(D/'RESULTS.json');rc=opt(D/'RECOUNT_041.json')
    ref=opt(D/'REFERENCE_041.json');ts=opt(study/'TEST_SUITE_041.json');order=opt(ROOT/'experiments/COMMIT_ORDER_041.json')
    rsha=sha(D/'RESULTS.json') if (D/'RESULTS.json').exists() else None
    sealed=(bool(seal) and res is not None and sci is not None and rsha==seal.get('results_sha256')
            and sha(D/'SCIENTIFIC.json')==seal.get('scientific_sha256') and no_time(res)==sci)
    reps=(res or {}).get('replays',[]) if sealed else [];allc=(res or {}).get('cases',[]) if sealed else []
    P=lambda p:[r for r in reps if r['part']==p];G=lambda k:sorted([c for c in allc if c['key']==k and c['block']=='main'],key=lambda c:c['seed'])
    complete=(sealed and seal.get('complete') is True and all(len(P(p))==n for p,n in EXP_REPLAYS.items()) and len(reps)==sum(EXP_REPLAYS.values())
              and all(len(G(k))==n for k,n in EXP_CASES.items()) and len(allc)==sum(EXP_CASES.values()) and all(set(c['arms'])==set(ARMS) for c in allc))
    wb=None if complete else 'INCOMPLETE_INPUT (main missing, partial, missing arms or not matching its seal)'
    def gate(name,ok,obs,why=None):Gt[name]={'pass':bool(ok) and why is None,'observed':obs,**({'reason':why} if why else {})}
    pc=(rc or {}).get('per_case') or {};pr=(rc or {}).get('per_replay') or {}
    rc_ok=bool(rc) and rc.get('PASS') is True and rc.get('results_sha256')==rsha and rc.get('cases')==len(allc) and rc.get('replays')==len(reps) and rc.get('mismatching_cases')==0
    lab=lambda c,a:((pc.get(ckey(c)) or {}).get(a) or {}).get('label')
    rlab=lambda r:(pr.get(f"replay/{r['part']}/{r['study']}/{r['key']}/{r['seed']}/{r['variant']}/{r['repeat']}") or {}).get('label')
    E0={tkey(r):r for r in reps if r['variant']=='E0'}
    # GAUD_sem
    contra=[[rid(r),sn(r),sn(E0[tkey(r)])] for r in reps if r['variant']!='E0' and dec(r) and tkey(r) in E0 and dec(E0[tkey(r)]) and sn(r)!=sn(E0[tkey(r)])]
    gains=[rid(r) for r in reps if r['variant']!='E0' and dec(r) and tkey(r) in E0 and not dec(E0[tkey(r)])]
    losses={v:[rid(r) for r in reps if r['variant']==v and not dec(r) and tkey(r) in E0 and dec(E0[tkey(r)])] for v in VARIANTS[1:]}
    fcontra=[[ckey(c),a,sn(c['arms'][a]),sn(c['arms']['A14'])] for c in allc for a in ARMS[1:] if dec(c['arms'][a]) and dec(c['arms']['A14']) and sn(c['arms'][a])!=sn(c['arms']['A14'])]
    rwrong=[rid(r) for r in reps if rlab(r)=='WRONG'];fwrong=[(ckey(c),a) for c in allc for a in c['arms'] if lab(c,a)=='WRONG']
    lmis=[(ckey(c),a) for c in allc for a in c['arms'] if lab(c,a)!=c['arms'][a]['label']]
    vs_sealed=[rid(r) for r in reps if dec(r) and r['sealed'][0]!='unknown' and sn(r)!=r['sealed']]
    gate('GAUD_sem',complete and rc_ok and not contra and not fcontra and not rwrong and not fwrong and not lmis,
         {'replay_contradictions':contra,'fresh_contradictions':fcontra,'replay_WRONG':rwrong,'fresh_WRONG':fwrong,'fresh_label_mismatch':lmis,
          'decided_where_E0_unknown_reported':gains,'unknown_where_E0_decided_reported':losses,'decided_differs_from_sealed_reported':vs_sealed,
          'rule':'decided (stop, n_min) equals decided E0 (replay) / A14 (fresh); WRONG 0; unknown allowed'},why=wb)
    # GAUD_loc
    B={(r['seed'],r['variant'],r['repeat']):r for r in P('b')};loc={}
    for v in ('E1','E2'):
        rep_loss=0;rep_match=0;per=[]
        for k in range(3):
            e0=[B.get((s,'E0',k)) for s in GINC];x=[B.get((s,v,k)) for s in GINC]
            ok=all(e0) and all(x)
            loss=ok and any(dec(a) and not dec(b) for a,b in zip(e0,x));match=ok and all(a['stop']==b['stop'] for a,b in zip(e0,x))
            rep_loss+=loss;rep_match+=match;per.append({'repeat':k,'E0':[a and a['stop'] for a in e0],v:[b and b['stop'] for b in x],'loss':loss,'match':match})
        loc[v]={'reproduces_loss':rep_loss>=2,'matches_E0':rep_match>=2,'repeats_loss':rep_loss,'repeats_match':rep_match,'per_repeat':per}
    cells={f'{s}/{v}':[(B.get((s,v,k)) or {}).get('stop') for k in range(3)] for s,v in GINC_CELLS}
    one=[v for v in ('E1','E2') if loc[v]['reproduces_loss'] and not loc[v]['matches_E0']]
    other={'E1':'E2','E2':'E1'}
    lp=len(one)==1 and loc[other[one[0]]]['matches_E0'] and not loc[other[one[0]]]['reproduces_loss']
    gate('GAUD_loc',complete and lp,{'variants':loc,'ginc15_cells_E3_E4_by_repeat':cells,'component':COMPONENT[one[0]] if lp else None,
         'reading':'both' if all(loc[v]['reproduces_loss'] for v in ('E1','E2')) else ('neither' if not any(loc[v]['reproduces_loss'] for v in ('E1','E2')) else 'one'),
         'rule':'exactly one of E1, E2 reproduces the loss (>=2/3 repeats) and the other matches E0 (>=2/3 repeats)'},why=wb)
    # GAUD_time
    tm={}
    for v in ('E1','E2','E3','E4'):
        rr,dr=ratios(reps,v);vals=[x for _,x in rr]
        tm[v]={'traces':len(rr),'dropped':dr,'mean_ratio':round(sum(vals)/len(vals),4) if vals else None,'median_ratio':round(median(vals),4) if vals else None,
               'ci95_seed_bootstrap':boot(vals),'per_trace':[[k,round(x,4)] for k,x in rr]}
    t3=tm['E3'];gate('GAUD_time',complete and t3['ci95_seed_bootstrap'] is not None and t3['ci95_seed_bootstrap'][0]>1,
                     {'E3_over_E0':{k:t3[k] for k in t3},'reported':{v:{k:tm[v][k] for k in ('traces','mean_ratio','median_ratio','ci95_seed_bootstrap','dropped')} for v in ('E1','E2','E4')},
                      'rule':'mean over traces (parts a, c) of median call wall E3 / E0; 95% CI lower > 1'},why=wb)
    # GAUD_stab
    st={f'{s}/{v}':[(B.get((s,v,k)) or {}).get('stop') for k in range(3)] for s in GINC for v in VARIANTS}
    same=sum(1 for x in st.values() if None not in x and len(set(x))==1)
    gate('GAUD_stab',complete and same>=9,{'cells_identical':same,'of':len(st),'cells':st,'ci95':wilson(same,len(st)),'rule':'>= 9/10'},why=wb)
    # GPERM16
    pm=G('perm12');pd=[c for c in pm if dec(c['arms']['A14'])]
    bad=[[c['seed'],a,sn(c['arms'][a]),sn(c['arms']['A14'])] for c in pd for a in ARMS[1:] if sn(c['arms'][a])!=sn(c['arms']['A14'])]
    gate('GPERM16',complete and bool(pd) and not bad,{'A14_decided':len(pd),'of':len(pm),'differ':bad,
         'agree':{a:sum(1 for c in pd if sn(c['arms'][a])==sn(c['arms']['A14'])) for a in ARMS[1:]},
         'agree_ci95':{a:wilson(sum(1 for c in pd if sn(c['arms'][a])==sn(c['arms']['A14'])),len(pd)) if pd else None for a in ARMS[1:]},
         'labels':{a:[c['arms'][a]['label'] for c in pm] for a in ARMS},'rule':'A15 and A15_cube equal A14 (stop, n_min) wherever A14 decides'},why=wb)
    # GQB16
    calls=[(rid(r),c['phase'],c['n'],c['wall']) for r in reps for c in r['calls']]+[(f'{ckey(c)}/{a}',x['phase'],x['n'],x['wall']) for c in allc for a,ar in c['arms'].items() for x in ar['calls']]
    qmax=[(rid(r),r['query_max_s']) for r in reps if r['query_max_s'] is not None]+[(f'{ckey(c)}/{a}',ar['query_max_s']) for c in allc for a,ar in c['arms'].items() if ar['query_max_s'] is not None]
    over=[[i,p,n,round(w,3)] for i,p,n,w in calls if w>QB];qover=[[i,round(w,3)] for i,w in qmax if w>QB]
    worst=max([w for *_,w in calls]+[w for _,w in qmax],default=None)
    by={};kills=0
    for i,p,n,w in calls:
        v=i.split('/')[-1];by[v]=max(by.get(v,0),w)
    kills=sum(r['kills'] for r in reps)+sum(ar['kills'] for c in allc for ar in c['arms'].values())
    gate('GQB16',complete and worst is not None and worst<=QB and not over and not qover,{'max_s':worst,'bound_s':QB,'over_calls':over,'over_queries':qover,
         'max_by_variant_or_arm':{k:round(v,3) for k,v in sorted(by.items())},'hard_kills':kills,'calls_logged':len(calls)},why=wb)
    snd={'words_checked':sum(ar.get('words_checked',0) for c in allc for ar in c['arms'].values()),
         'words_unsound':sum(ar.get('words_unsound',0) for c in allc for ar in c['arms'].values()),
         'recount_words_checked':(rc or {}).get('words_checked'),'recount_words_unsound':(rc or {}).get('words_unsound'),
         'recount_truth_inconsistent':(rc or {}).get('truth_inconsistent')}
    gate('G_sound',complete and rc_ok and snd['words_unsound']==0 and snd['recount_words_unsound']==0 and snd['recount_truth_inconsistent']==0
         and snd['recount_words_checked']==snd['words_checked'],snd,why=wb)
    g10=[(c['seed'],{a:lab(c,a) for a in c['arms']}) for c in G('control')]
    gate('G10',complete and rc_ok and len(g10)==6 and all(all(L=='ID' for L in x[1].values()) for x in g10),{'cases':g10,'rule':'every arm ID on every control'},why=wb)
    mt=(ref or {}).get('mutation_test') or {}
    robs=None if not ref else {k:ref.get(k) for k in ('part','variants_audited','traces','records','decided','decided_by_variant','not_reached','verdicts_checked','mismatch_count','PASS')}|{'mutations':mt.get('detected'),'of':mt.get('mutations')}
    rbase=(bool(ref) and ref.get('study_results_sha256')==rsha and ref.get('part')=='c' and ref.get('records')==24 and ref.get('traces')==12
           and mt.get('detected')==mt.get('mutations')==20 and ref.get('mismatch_count')==0 and (ref.get('decided') or 0)>0)
    gate('GS_ref',rbase and ref.get('PASS') is True,robs,why=wb or (None if ref else 'INCOMPLETE_INPUT (REFERENCE_041 missing)'))
    mods=(ts or {}).get('per_module') or {};gm=(ts or {}).get('gated_modules') or []
    gate('GTI',bool(gm) and ts.get('passed') is True and all(mods[m].get('returncode')==0 for m in gm),
         None if not ts else {'gated':{m:{'returncode':mods[m].get('returncode'),'tests':mods[m].get('tests')} for m in gm},
                              'reported':{m:{'returncode':v.get('returncode'),'tests':v.get('tests')} for m,v in mods.items() if m not in gm}},
         why=None if ts else 'INCOMPLETE_INPUT (TEST_SUITE_041 missing)')
    lt=ledger();ev=[e for e,_ in lt];times=[t for _,t in lt];pos={e:ev.index(e) for e in PROC_ORDER if e in ev}
    proc={'all_events':len(pos)==len(PROC_ORDER),'order':len(pos)==len(PROC_ORDER) and all(pos[a]<pos[b] for a,b in zip(PROC_ORDER,PROC_ORDER[1:])),
          'ledger_times_parse':bool(lt) and all(t is not None for t in times),'ledger_times_non_decreasing':all(a<=b for a,b in zip(times,times[1:]) if a and b),
          'commit_order_file':order is not None,'main_sealed':bool(sealed)}
    gate('G_PROC',all(proc.values()),{'clauses':proc,'events':ev})
    el=(res or {}).get('total_elapsed_informational')
    gate('G_RT',complete and el is not None and el<=CAP,{'elapsed_s':el,'cap_s':CAP,'replays':len(reps),'cases':len(allc)},why=wb)
    gate('G_recount',complete and rc_ok,None if not rc else {k:rc.get(k) for k in ('replays','cases','labels','replay_labels','replay_wrong','words_checked','words_unsound','mismatching_cases','PASS')},
         why=wb or (None if rc else 'INCOMPLETE_INPUT (RECOUNT_041 missing)'))
    cls={}
    for r in reps:
        for c in r['calls']:x=cls.setdefault(f"{r['variant']}/n{c['n']}",[]);x.append((c['clauses'],c['vars']))
    sec['GCLS16']={'pass':None,'observed':{k:{'calls':len(v),'clauses_max':max(a for a,_ in v),'clauses_mean':round(sum(a for a,_ in v)/len(v),1),
                   'vars_max':max(b for _,b in v)} for k,v in sorted(cls.items())},'rule':'reported: clause and variable counts per variant and size (replays)'}
    ph={}
    for r in reps:
        for p,b in r['by_phase'].items():x=ph.setdefault(f"replay/{r['variant']}/{p}",[0,0]);x[0]+=b['calls'];x[1]+=b['capped']
    for c in allc:
        for a,ar in c['arms'].items():
            for p,b in ar['by_phase'].items():x=ph.setdefault(f"fresh/{a}/{p}",[0,0]);x[0]+=b['calls'];x[1]+=b['capped']
    sec['GPH16']={'pass':None,'observed':{k:{'calls':v[0],'capped':v[1]} for k,v in sorted(ph.items())},
                  'rule':'reported: calls and capped calls by phase (least, rival = future + start, cube) per variant / arm'}
    rp={}
    for p in EXP_REPLAYS:
        for v in VARIANTS:
            xs=[r for r in P(p) if r['variant']==v];d=sum(dec(r) for r in xs)
            rp[f'{p}/{v}']={'n':len(xs),'decided':d,'ci95':wilson(d,len(xs)) if xs else None,'stops':{s:sum(r['stop']==s for r in xs) for s in sorted({r['stop'] for r in xs})},
                            'capped_records':sum(r['capped']>0 for r in xs),'hard_kills':sum(r['kills'] for r in xs)}
    fl={f'{a}/{k}':{L:{'x':sum(lab(c,a)==L for c in G(k)),'ci95':wilson(sum(lab(c,a)==L for c in G(k)),len(G(k))) if G(k) else None} for L in LABELS} for a in ARMS for k in EXP_CASES}
    return {'schema':'brute.gates.v38_0','study':'BRUTE-0380-ENCODING-AUDIT-041','process':'lean','sealed_input_verified':sealed,'gates':Gt,
            'secondary':sec,'all_gated_pass':all(g['pass'] for g in Gt.values() if g['pass'] is not None),
            'failed':[k for k,g in Gt.items() if g['pass'] is False],'not_exercised':[k for k,g in Gt.items() if g['pass'] is None],
            'reports':{'replay_decided':rp,'fresh_labels':fl,'time_ratios':tm} if reps else {}}


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--study-dir',default=str(STUDY_DIR));ap.add_argument('--check',action='store_true');a=ap.parse_args()
    obj=build(Path(a.study_dir));out=Path(a.study_dir)/'GATES_041.json'
    if a.check:check(out.read_bytes()==dumps(obj),'GATES_041.json does not reproduce');print('GATES_041 reproduces')
    else:write_new(out,obj);print(json.dumps({k:v['pass'] for k,v in obj['gates'].items()}),obj['failed'])
