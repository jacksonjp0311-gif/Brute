"""Pre-freeze smoke-gates, runtime projection and cut check for study-061 (plan 061 runtime_estimate; pre-run deviation #196).
New file; built from scripts/prefreeze_smoke_060.py (frozen). Input: the sealed smoke block written by experiments/brute_study_061.py
--block smoke (outside results/study-061; smoke seeds 12610301-02 on all three arms, 6 jobs on one 8-worker pool, B 2000000 for
smoke only, conflict-only stop; 12610303 is used only by the api_checks no-network run, 12610304-06 unused). Smoke is never gated
and never sets C, B or K. It
  1. lists stops, labels, smoke determinism (canon61 of S24 vs S24b), wall_guard firings and per-record fields;
  2. runs recount_061 and run_reference_061 (block smoke) on copies and scripts/api_checks_061.py (no --study) into a temp file;
  3. builds a synthetic complete block (smoke cases relabelled 'main'), re-sealed with the runner's _write (stand-in freeze),
     recounted, referenced, self-replayed (GFID61 fidelity, must be exact) and gated twice with the smoke case counts (dumps must be
     identical); exercises verify_release_0580.release_ok;
  4. runs verify_release_0580.chain on the repository (ledger since preregistration_061; HEAD stands in for freeze and seal);
  5. runtime projection (Inferred), plan 061 runtime_estimate: smoke runs at B 2M, so the per-job worst comes from the exploratory
     budget probe (results/diag-061/BUDGET_PROBE_061.json, same code path, 8 workers): worst(arm) = 1.25 * the probe's max wall at
     (n, B61) (a probe job stopped by the probe's 2100 s guard counts at 2100 s, a lower bound); the run = LPT of the declared main
     jobs on 8 workers. Declared cut rule (#196): candidates in order (N32, N24B, N24) = (4, 6, 12), (0, 6, 12), (0, 3, 12), (0, 2, 6); the
     plan's three steps, then the #196 step (fewer S24 seeds, user instruction); the first whose run is <= 3300 s is required
     (cut_exhausted if none); the runner's N32, N24B and N24 must equal it (cut_consistent).
Writes results/diag-061/PREFREEZE_SMOKE_GATES_061.json (refuses overwrite) or --output. Observed only: no gate decision, no tuning.
  PYTHONPATH=. python scripts/prefreeze_smoke_061.py /tmp/s61/smoke [--output PATH]"""
import copy,json,shutil,subprocess,sys,tempfile
from pathlib import Path
from unittest import mock
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments import brute_study_061 as ST
from experiments.brute_common_061 import load,write_new,PLAN,B61,WORKERS,ALL_ARMS
from experiments.brute_common import dumps
from scripts import make_gates_061 as MG
from scripts import make_freeze_061 as MF
from scripts import verify_release_0580 as V
from scripts import api_checks_061 as AC
from scripts.recount_061 import main as recount
from scripts.run_reference_061 import main as reference
OUT=ROOT/'results/diag-061/PREFREEZE_SMOKE_GATES_061.json';CAP=3300.0;STEPS=((4,6,12),(0,6,12),(0,3,12),(0,2,6));SAFETY=1.25;PROBE=ROOT/'results/diag-061/BUDGET_PROBE_061.json'
BY_DESIGN=('GHOST61','GTEST','G_PROC','GN24_61')
FIELDS=('label','stop','n_min','true_size','used','n_rounds','conflicts_spent','wall_guard')


def status(g):return {k:{'pass':v['pass'],**({'reason':v['reason']} if 'reason' in v else {})} for k,v in g['gates'].items()}


def _lpt(walls,workers):
    bins=[0.0]*workers
    for x in sorted(walls,reverse=True):bins[bins.index(min(bins))]+=x
    return max(bins)


def _jobs(n32,n24b,n24):
    with mock.patch.object(ST,'N32',n32),mock.patch.object(ST,'N24B',n24b),mock.patch.object(ST,'N24',n24):return ST.jobs_for(load(PLAN),'main')


def projection(res):
    PB=load(PROBE);P=PB['summary'];size={'S24':24,'S24b':24,'S32':32};bm=PB['B61']//1000000
    worst={a:round(SAFETY*P[f'n{size[a]}_B{bm}M']['max_wall_s'],1) for a in size}
    sm={a:[round(x['case_wall_informational'],1) for c in res['cases'] for g,x in c['arms'].items() if g==a] for a in size}
    out={'label':'Inferred','source':f'results/diag-061/BUDGET_PROBE_061.json (exploratory, non-fresh seeds) max walls at B61 = {bm}M times '+str(SAFETY),
         'B61':PB['B61'],'worst_per_job_s':worst,'probe_guard_firings_at_B61':{a:P[f'n{size[a]}_B{bm}M']['guard'] for a in size},
         'smoke_walls_B2M_s':sm,'workers':WORKERS,'cap_s':CAP,'candidates':{}}
    for n32,n24b,n24 in STEPS:
        J=_jobs(n32,n24b,n24);out['candidates'][f'N32={n32},N24B={n24b},N24={n24}']={'jobs':len(J),'worst_run_s':round(_lpt([worst[j[3]] for j in J],WORKERS),1)}
    req=next((x for x in STEPS if out['candidates'][f'N32={x[0]},N24B={x[1]},N24={x[2]}']['worst_run_s']<=CAP),STEPS[-1])
    ch=out['candidates'][f'N32={req[0]},N24B={req[1]},N24={req[2]}']
    out.update(required={'N32':req[0],'N24B':req[1],'N24':req[2]},chosen_projection=ch,cut_exhausted=ch['worst_run_s']>CAP,
               runner={'N32':ST.N32,'N24B':ST.N24B,'N24':ST.N24},cut_consistent=req==(ST.N32,ST.N24B,ST.N24),cut_applied=req!=STEPS[0],
               projected_main_worst_s=ch['worst_run_s'],
               caveat='4 (n24) or 2 (n32) probe seeds; every job is assumed to take 1.25 times the slowest probe job of its size at B61; a probe job stopped by its 2100 s guard is a lower bound')
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
    out['smoke_records']=[(c['seed'],{a:[x.get(f) for f in FIELDS]+[round(x.get('case_wall_informational') or 0,1)] for a,x in c['arms'].items()}) for c in allr]
    out['smoke_record_columns']=['seed','arm: '+', '.join(FIELDS)+', case wall s']
    out['smoke_wall_guard_records']=[f"{c['seed']}/{a}" for c in allr for a,x in c['arms'].items() if x.get('wall_guard')]
    det=[(c['seed'],ST.canon61(c['arms']['S24'])==ST.canon61(c['arms']['S24b'])) for c in allr if c['key']=='scale24w'];out['smoke_determinism']=det
    out['all_arms_present']=sorted(a for c in allr for a in c['arms'])==sorted(['S24','S24','S24b','S24b','S32','S32']) and len(allr)==4 and len(det)==2
    out['runtime_projection']=projection(res)
    with tempfile.TemporaryDirectory() as d:
        C=Path(d)/'copy';C.mkdir()
        for nm in ('RESULTS.json','SCIENTIFIC.json','SEAL.json'):shutil.copy(S/nm,C/nm)
        out['recount_rc']=recount([str(C)]);rc=load(C/'RECOUNT_061.json')
        out['recount']={k:rc.get(k) for k in ('cases','records','decided_by_arm','study_decided_by_arm','wrong_by_arm','mismatches','PASS')}
        out['reference_rc']=reference([str(C),'--block','smoke','--workers','8']);rf=load(C/'REFERENCE_061.json')
        out['reference_smoke']={k:rf.get(k) for k in ('records','decided','audited','complete','per_arm','mismatch_count','vacuous','PASS','elapsed_informational','scope')}|{'mutations':rf['mutation_test']['detected'],'of':rf['mutation_test']['mutations']}
        ac=Path(d)/'API_CHECKS_061.json';p=subprocess.run([sys.executable,str(ROOT/'scripts/api_checks_061.py'),'--output',str(ac)],
            cwd=ROOT,capture_output=True,text=True,timeout=1500,env={'PYTHONPATH':str(ROOT),'PATH':'/usr/bin:/bin'});out['api_checks_rc']=p.returncode
        if p.returncode and not ac.exists():raise SystemExit('api_checks_061 failed: '+p.stderr[-2000:])
        A=load(ac);out['api_checks']={'PASS':A.get('PASS'),'equiv':A.get('equiv'),'ghost':{k:A['ghost'].get(k) for k in A['ghost'] if k not in ('certify32b_closure',)}}
        D=Path(d)/'synthetic';(D/'main').mkdir(parents=True);fz=Path(d)/'FREEZE_STANDIN.json';fz.write_text('{}')
        cases=[dict(copy.deepcopy(c),block='main') for c in res['cases']];P=load(PLAN)
        with mock.patch.object(ST,'FREEZE',fz):
            ST._write(D/'main',P,'main',[f'synthetic:{i}' for i in range(sum(len(c['arms']) for c in cases))],cases,True,{'total_elapsed_informational':res.get('total_elapsed_informational')})
        rr=recount([str(D/'main')]);rf2=reference([str(D/'main'),'--workers','8'])
        n=(sum(c['key']=='scale24w' for c in cases),sum(c['key']=='scale24w' and 'S24b' in c['arms'] for c in cases),sum(c['key']=='scale32w' for c in cases));fi=AC.fidelity(D/'main');A2=dict(A,fidelity=fi);(D/'API_CHECKS_061.json').write_text(json.dumps(A2))
        g1=MG.build(D,n);g2=MG.build(D,n)
        out['synthetic']={'cases':n,'recount_rc':rr,'reference_rc':rf2,'gate_status':status(g1),'secondary':{k:v.get('observed') for k,v in g1['secondary'].items() if k!='GSTATS61'},
                          'fidelity_self_replay':{k:v for k,v in fi.items() if k!='per_case'},'fidelity_failures':{k:v for k,v in fi['per_case'].items() if not v['exact']},
                          **{nm:g1['gates'][nm].get('observed') for nm in ('GDET61','GFID61','GN24_61','GS61_sound','GS_ref')},
                          'certified_readbits4_N24':g1['certified_readbits4_N24'],'sound_not_certified_N24':g1['sound_not_certified_N24'],'status_phrase':g1['status_phrase'],
                          'sealed_input_verified':g1.get('sealed_input_verified'),'reproduces':dumps(g1)==dumps(g2),'label_source':g1.get('label_source'),
                          'note':('synthetic: smoke cases as main with the smoke case count; GHOST61 (bound to FREEZE_060; may pass), GTEST and G_PROC fail by design; '
                                  'GN24_61 on 2 smoke seeds at B 2M is recorded, not required')}
        Rd=Path(d)/'rel';(Rd/V.STUDY).mkdir(parents=True);(Rd/V.STUDY/'GATES_061.json').write_bytes(dumps(g1))
        Rel={k:'x' for k in V.RELEASE_KEYS};Rel.update(version=V.VERSION,gates_passed=sorted(k for k,v in g1['gates'].items() if v['pass'] is True),
             gates_failed=sorted(k for k,v in g1['gates'].items() if v['pass'] is False),gates_not_exercised=sorted(k for k,v in g1['gates'].items() if v['pass'] is None),
             secondary={k:v['pass'] for k,v in g1['secondary'].items()},certified_readbits4_N24=g1['certified_readbits4_N24'],
             sound_not_certified_N24=g1['sound_not_certified_N24'],status_phrase=g1['status_phrase'])
        (Rd/'RELEASE.json').write_text(json.dumps(Rel))
        try:V.release_ok(Rd);out['release_ok_synthetic']=True
        except Exception as e:out['release_ok_synthetic']=f'error: {e}'
    E=MF.entries();h=head();R={'preregistration_commit':E[0]['commit'],'source_freeze_commit':h,'seal_commit':h}
    try:out['verifier_chain']={'passed':True,'entries':[[e['event'],e['commit']] for e in E],'head':h,**V.chain(ROOT,R,E)}
    except Exception as e:out['verifier_chain']={'passed':False,'error':str(e),'entries':[[e['event'],e['commit']] for e in E]}
    vc=out['verifier_chain'];pj=out['runtime_projection'];sy=out['synthetic'];fs=sy['fidelity_self_replay'];gs=sy['gate_status']
    out['PASS']=(out['recount_rc']==0 and out['reference_rc']==0 and sy['recount_rc']==0 and sy['reference_rc']==0 and sy['reproduces']
                 and sy['sealed_input_verified'] and not any('INCOMPLETE_INPUT' in v.get('reason','') for k,v in gs.items() if k not in BY_DESIGN)
                 and gs['G_recount']['pass'] is True and gs['GDET61']['pass'] is True and gs['GFID61']['pass'] is True and gs['GS61_sound']['pass'] is True
                 and gs['GS_ref']['pass'] is True and sy['label_source']=='recount' and fs.get('PASS') is True
                 and out['api_checks_rc']==0 and out['api_checks']['ghost'].get('PASS61') is True and out['api_checks']['equiv']['PASS'] is True
                 and pj['cut_consistent'] and all(x[1] for x in det) and not out['smoke_wall_guard_records'] and out['all_arms_present']
                 and out['release_ok_synthetic'] is True and vc['passed'] and vc.get('authorization_exceptions')==0)
    out['note']=('PASS here means the tooling ran end to end on a sealed block, gates reproduce, the self-replay is exact, the cut rule was '
                 'applied as declared and the real commit-order check passes; GN24_61 outcome on smoke are recorded, not required')
    write_new(outp,out);print(json.dumps({k:v for k,v in out.items() if k not in ('smoke_records','synthetic','recount')},default=str)[:6000])
    print(json.dumps(gs));return 0 if out['PASS'] else 1


if __name__=='__main__':sys.exit(main())
