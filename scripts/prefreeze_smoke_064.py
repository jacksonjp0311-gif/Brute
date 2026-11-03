"""Pre-freeze smoke-gates, runtime projection and cut check for study-064 (plan 064 runtime_estimate; pre-run deviation #202).
New file; built from scripts/prefreeze_smoke_063.py (frozen). Input: the sealed smoke block written by experiments/brute_study_064.py
--block smoke (outside results/study-064; smoke seed 12640301 on B24 and P24, 12640302 on P20 and P20b, 4 jobs on one 6-worker
pool, B 2000000 for smoke only, conflict-only stop; 12640303 is used only by the api_checks no-network run, 12640304-06 unused).
Smoke is never gated and never sets C, B or K. It
  1. lists stops, labels, smoke determinism (canon64 of P20 vs P20b), wall_guard firings and per-record fields;
  2. runs recount_064 and run_reference_064 (block smoke) on copies and scripts/api_checks_064.py (no --study, xref included) into
     a temp file;
  3. builds a synthetic complete block (smoke cases relabelled 'main'), re-sealed with the runner's _write (stand-in freeze),
     recounted, referenced, self-replayed (GFID64 fidelity, must be exact) and gated twice with the smoke case counts (dumps must be
     identical); exercises verify_release_0610.release_ok;
  4. runs verify_release_0610.chain on the repository (ledger since preregistration_064; HEAD stands in for freeze and seal);
  5. runtime projection (Inferred), plan 064 runtime_estimate: per-job worst = SAFETY 1.25 times the slowest observed wall of the
     same arm at B 8M (P24, B24: results/diag-064/CAPABILITY_PROBE_064.json, 6 concurrent workers; P20, P20b: the P2 case walls of
     the sealed study-063 main block, frozen certify/20p, 6 workers), with B24 capped at the 1800 s case kill plus one 30 s guarded
     call; the run = LPT of the declared main jobs on 6 workers. Declared cut rule (plan): candidates in order (N_P20B, N_B24) =
     (2, 3), (1, 3), (1, 2); the first whose run is <= MAIN_CAP_S 2400 s is required, else the last (cut_exhausted, disclosed);
     the runner's N_P20B and N_B24 must equal it (cut_consistent).
Writes results/diag-064/PREFREEZE_SMOKE_GATES_064.json (refuses overwrite) or --output. Observed only: no gate decision, no tuning.
  PYTHONPATH=. python scripts/prefreeze_smoke_064.py /tmp/s64/smoke [--output PATH]"""
import copy,json,shutil,subprocess,sys,tempfile
from pathlib import Path
from unittest import mock
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments import brute_study_064 as ST
from experiments.brute_common_064 import load,write_new,PLAN,B64,WORKERS,ALL_ARMS,MAIN_CAP_S,HARD_KILL_S,GUARD_CALL_S
from experiments.brute_common import dumps
from scripts import make_gates_064 as MG
from scripts import make_freeze_064 as MF
from scripts import verify_release_0610 as V
from scripts import api_checks_064 as AC
from scripts.recount_064 import main as recount
from scripts.run_reference_064 import main as reference
OUT=ROOT/'results/diag-064/PREFREEZE_SMOKE_GATES_064.json';CAP=MAIN_CAP_S;STEPS=((2,3),(1,3),(1,2));SAFETY=1.25
PROBE=ROOT/'results/diag-064/CAPABILITY_PROBE_064.json';P20REF='results/study-063/main'
BY_DESIGN=('GHOST64','GTEST64','G_PROC64','GP24_64','GP20_64')
FIELDS=('label','stop','n_min','used','n_rounds','conflicts_spent','wall_guard','clique_prefix','clique_final','clique_size','final_clique')


def status(g):return {k:{'pass':v['pass'],**({'reason':v['reason']} if 'reason' in v else {})} for k,v in g['gates'].items()}


def _lpt(walls,workers):
    bins=[0.0]*workers
    for x in sorted(walls,reverse=True):bins[bins.index(min(bins))]+=x
    return max(bins)


def _jobs(nb20,nb24):
    with mock.patch.object(ST,'N_P20B',nb20),mock.patch.object(ST,'N_B24',nb24):return ST.jobs_for(load(PLAN),'main')


def _p20_walls():
    from scripts.study063_storage import ensure_raw
    ensure_raw();R=load(ROOT/P20REF/'RESULTS.json')
    return [x['case_wall_informational'] for c in R['cases'] for g,x in c['arms'].items() if g=='P2']


def projection(res):
    PB=load(PROBE);w24={a:[r['wall_s_informational'] for r in PB['records'] if r['arm']==a] for a in ('P24','B24')};w20=_p20_walls()
    kill=HARD_KILL_S+GUARD_CALL_S
    worst={'P24':round(SAFETY*max(w24['P24']),1),'B24':round(min(SAFETY*max(w24['B24']),kill),1),
           'P20':round(SAFETY*max(w20),1),'P20b':round(SAFETY*max(w20),1)}
    sm={a:[round(x['case_wall_informational'],1) for c in res['cases'] for g,x in c['arms'].items() if g==a] for a in worst}
    out={'label':'Inferred','source':(f'P24/B24: results/diag-064/CAPABILITY_PROBE_064.json at B {PB["B"]} (exploratory, non-fresh seeds); '
                                      f'P20/P20b: sealed {P20REF} P2 case walls (frozen certify/20p, B 8M, 6 workers); times {SAFETY}; B24 capped at {kill} s'),
         'B64':B64,'probe_walls_s':w24,'sealed_063_P2_walls_s':[round(x,1) for x in w20],'worst_per_job_s':worst,
         'smoke_walls_B2M_s':sm,'workers':WORKERS,'cap_s':CAP,'candidates':{}}
    for nb20,nb24 in STEPS:
        J=_jobs(nb20,nb24);out['candidates'][f'N_P20B={nb20},N_B24={nb24}']={'jobs':len(J),'worst_run_s':round(_lpt([worst[j[3]] for j in J],WORKERS),1)}
    req=next((x for x in STEPS if out['candidates'][f'N_P20B={x[0]},N_B24={x[1]}']['worst_run_s']<=CAP),STEPS[-1])
    ch=out['candidates'][f'N_P20B={req[0]},N_B24={req[1]}']
    out.update(required={'N_P20B':req[0],'N_B24':req[1]},chosen_projection=ch,cut_exhausted=ch['worst_run_s']>CAP,
               runner={'N_P20B':ST.N_P20B,'N_B24':ST.N_B24,'N_SEEDS':ST.N_SEEDS},cut_consistent=req==(ST.N_P20B,ST.N_B24),cut_applied=req!=STEPS[0],
               projected_main_worst_s=ch['worst_run_s'],
               caveat=('every job is assumed to take 1.25 times the slowest of its arm (pessimistic: decided P20 records took about 45-70 s in '
                       'study-063); the realistic makespan is about 1850-2100 s (the B24 case kill dominates)'))
    return out


def head():return subprocess.run(['git','-C',str(ROOT),'rev-parse','--short','HEAD'],capture_output=True,text=True).stdout.strip()


def main(argv=None):
    argv=list(sys.argv[1:] if argv is None else argv);outp=OUT
    if '--output' in argv:i=argv.index('--output');outp=Path(argv[i+1]);del argv[i:i+2]
    S=Path(argv[0]);out={'label':'Observed','purpose':__doc__.split('\n')[0]}
    res=load(S/'RESULTS.json');st={};allr=res['cases']
    for c in allr:
        for a,x in c['arms'].items():st.setdefault(x['stop'],[]).append(f"{c['block']}/{c['key']}/{c['seed']}/{a}")
    out['stops_present']={k:len(v) for k,v in sorted(st.items())}
    out['smoke_records']=[(c['key'],c['seed'],{a:[x.get(f) for f in FIELDS]+[round(x.get('case_wall_informational') or 0,1)] for a,x in c['arms'].items()}) for c in allr]
    out['smoke_record_columns']=['key','seed','arm: '+', '.join(FIELDS)+', case wall s']
    out['smoke_wall_guard_records']=[f"{c['seed']}/{a}" for c in allr for a,x in c['arms'].items() if x.get('wall_guard')]
    det=[(c['seed'],ST.canon64(c['arms']['P20'])==ST.canon64(c['arms']['P20b'])) for c in allr if 'P20b' in c['arms']];out['smoke_determinism']=det
    out['all_arms_present']=sorted(a for c in allr for a in c['arms'])==sorted(ALL_ARMS) and len(allr)==2 and len(det)==1
    out['runtime_projection']=projection(res)
    with tempfile.TemporaryDirectory() as d:
        C=Path(d)/'copy';C.mkdir()
        for nm in ('RESULTS.json','SCIENTIFIC.json','SEAL.json'):shutil.copy(S/nm,C/nm)
        out['recount_rc']=recount([str(C)]);rc=load(C/'RECOUNT_064.json')
        out['recount']={k:rc.get(k) for k in ('cases','records','decided_by_arm','study_decided_by_arm','wrong','mismatches','PASS')}
        out['reference_rc']=reference([str(C),'--block','smoke','--workers','6']);rf=load(C/'REFERENCE_064.json')
        out['reference_smoke']={k:rf.get(k) for k in ('records','decided','audited','complete','per_arm','mismatch_count','vacuous','PASS','elapsed_informational','scope')}|{'mutations':rf['mutation_test']['detected'],'of':rf['mutation_test']['mutations']}
        ac=Path(d)/'API_CHECKS_064.json';p=subprocess.run([sys.executable,str(ROOT/'scripts/api_checks_064.py'),'--output',str(ac)],
            cwd=ROOT,capture_output=True,text=True,timeout=2400,env={'PYTHONPATH':str(ROOT),'PATH':'/usr/bin:/bin'});out['api_checks_rc']=p.returncode
        if p.returncode and not ac.exists():raise SystemExit('api_checks_064 failed: '+p.stderr[-2000:])
        A=load(ac);out['api_checks']={'PASS':A.get('PASS'),'equiv':A.get('equiv'),'xref':A.get('xref'),
                                      'ghost':{k:A['ghost'].get(k) for k in A['ghost'] if k not in ('certify32p_closure',)}}
        D=Path(d)/'synthetic';(D/'main').mkdir(parents=True);fz=Path(d)/'FREEZE_STANDIN.json';fz.write_text('{}')
        cases=[dict(copy.deepcopy(c),block='main') for c in res['cases']];P=load(PLAN)
        with mock.patch.object(ST,'FREEZE',fz):
            ST._write(D/'main',P,'main',[f'synthetic:{i}' for i in range(sum(len(c['arms']) for c in cases))],cases,True,{'total_elapsed_informational':res.get('total_elapsed_informational')})
        rr=recount([str(D/'main')]);rf2=reference([str(D/'main'),'--workers','6'])
        n=(1,sum('B24' in c['arms'] for c in cases),sum('P20b' in c['arms'] for c in cases))
        fi=AC.fidelity(D/'main');A2=dict(A,fidelity=fi);(D/'API_CHECKS_064.json').write_text(json.dumps(A2))
        g1=MG.build(D,n);g2=MG.build(D,n)
        out['synthetic']={'cases':n,'recount_rc':rr,'reference_rc':rf2,'gate_status':status(g1),'secondary':{k:v.get('observed') for k,v in g1['secondary'].items() if k!='GSTATS64'},
                          'fidelity_self_replay':{k:v for k,v in fi.items() if k!='per_case'},'fidelity_failures':{k:v for k,v in fi['per_case'].items() if not v['exact']},
                          **{nm:g1['gates'][nm].get('observed') for nm in ('GDET64','GFID64','GXREF64','GP24_64','GP20_64','GS64_sound','GS_ref64')},
                          'certified_readbits2_N24_clique':g1['certified_readbits2_N24_clique'],'certified_readbits2_N20_clique':g1['certified_readbits2_N20_clique'],
                          'status_phrase':g1['status_phrase'],'sealed_input_verified':g1.get('sealed_input_verified'),'reproduces':dumps(g1)==dumps(g2),
                          'label_source':g1.get('label_source'),
                          'note':('synthetic: smoke cases as main with the smoke case counts (1 per size); GHOST64 (bound to FREEZE_064, absent before the freeze), '
                                  'GTEST64 and G_PROC64 fail by design; GP24_64 / GP20_64 on 1 smoke seed each at B 2M are recorded, not required')}
        Rd=Path(d)/'rel';(Rd/V.STUDY).mkdir(parents=True);(Rd/V.STUDY/'GATES_064.json').write_bytes(dumps(g1))
        Rel={k:'x' for k in V.RELEASE_KEYS};Rel.update(version=V.VERSION,gates_passed=sorted(k for k,v in g1['gates'].items() if v['pass'] is True),
             gates_failed=sorted(k for k,v in g1['gates'].items() if v['pass'] is False),gates_not_exercised=sorted(k for k,v in g1['gates'].items() if v['pass'] is None),
             secondary={k:v['pass'] for k,v in g1['secondary'].items()},certified_readbits2_N24_clique=g1['certified_readbits2_N24_clique'],
             certified_readbits2_N20_clique=g1['certified_readbits2_N20_clique'],status_phrase=g1['status_phrase'])
        (Rd/'RELEASE.json').write_text(json.dumps(Rel))
        try:V.release_ok(Rd);out['release_ok_synthetic']=True
        except Exception as e:out['release_ok_synthetic']=f'error: {e}'
    E=MF.entries();h=head();R={'preregistration_commit':E[0]['commit'],'source_freeze_commit':h,'seal_commit':h}
    try:out['verifier_chain']={'passed':True,'entries':[[e['event'],e['commit']] for e in E],'head':h,**V.chain(ROOT,R,E)}
    except Exception as e:out['verifier_chain']={'passed':False,'error':str(e),'entries':[[e['event'],e['commit']] for e in E]}
    vc=out['verifier_chain'];pj=out['runtime_projection'];sy=out['synthetic'];fs=sy['fidelity_self_replay'];gs=sy['gate_status']
    out['PASS']=(out['recount_rc']==0 and out['reference_rc']==0 and sy['recount_rc']==0 and sy['reference_rc']==0 and sy['reproduces']
                 and sy['sealed_input_verified'] and not any('INCOMPLETE_INPUT' in v.get('reason','') for k,v in gs.items() if k not in BY_DESIGN)
                 and gs['G_recount64']['pass'] is True and gs['GDET64']['pass'] is True and gs['GFID64']['pass'] is True and gs['GS64_sound']['pass'] is True
                 and gs['GS_ref64']['pass'] is True and gs['GXREF64']['pass'] is True and sy['label_source']=='recount' and fs.get('PASS') is True
                 and out['api_checks_rc']==0 and out['api_checks']['ghost'].get('PASS64') is True and out['api_checks']['equiv']['PASS'] is True
                 and pj['cut_consistent'] and all(x[1] for x in det) and not out['smoke_wall_guard_records'] and out['all_arms_present']
                 and out['release_ok_synthetic'] is True and vc['passed'] and vc.get('authorization_exceptions')==0)
    out['note']=('PASS here means the tooling ran end to end on a sealed block, gates reproduce, the self-replay is exact, the cut rule was '
                 'applied as declared and the real commit-order check passes; GP24_64 / GP20_64 outcomes on smoke are recorded, not required')
    write_new(outp,out);print(json.dumps({k:v for k,v in out.items() if k not in ('smoke_records','synthetic','recount')},default=str)[:6000])
    print(json.dumps(gs));return 0 if out['PASS'] else 1


if __name__=='__main__':sys.exit(main())
