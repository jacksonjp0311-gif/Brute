"""Pre-freeze smoke-gates, runtime projection and cut check for study-062 (plan 062 runtime_estimate; pre-run deviation #198).
New file; built from scripts/prefreeze_smoke_061.py (frozen). Input: the sealed smoke block written by experiments/brute_study_062.py
--block smoke (outside results/study-062; smoke seeds 12620301-02 on all three arms, 6 jobs on one 8-worker pool, B 2000000 for
smoke only, conflict-only stop; 12620303 is used only by the api_checks no-network run, 12620304-06 unused). Smoke is never gated
and never sets C, B or K. It
  1. lists stops, labels, smoke determinism (canon62 of W2 vs W2b), wall_guard firings and per-record fields;
  2. runs recount_062 and run_reference_062 (block smoke) on copies and scripts/api_checks_062.py (no --study) into a temp file;
  3. builds a synthetic complete block (smoke cases relabelled 'main'), re-sealed with the runner's _write (stand-in freeze),
     recounted, referenced, self-replayed (GFID62 fidelity, must be exact) and gated twice with the smoke case counts (dumps must be
     identical); exercises verify_release_0590.release_ok;
  4. runs verify_release_0590.chain on the repository (ledger since preregistration_062; HEAD stands in for freeze and seal);
  5. runtime projection (Inferred), plan 062 runtime_estimate: smoke runs at B 2M, so the per-job worst comes from the exploratory
     budget probe (results/diag-062/BUDGET_PROBE_062.json, same code path, 8 workers): worst(arm) = 1.25 * the probe's max wall of
     that policy at B62 (W2 for W2 and W2b, B2 for B2; a probe job stopped by the probe's 2400 s guard counts at 2400 s, a lower
     bound); the run = LPT of the declared main jobs on 8 workers. Declared cut rule (plan, #198): candidates in order
     (N_W2B, N_SEEDS) = (6, 12), (2, 12), (2, 8), then the #198 step (2, 3); the first whose run is <= 3300 s is required (cut_exhausted if none); the runner's
     N_W2B and N_SEEDS must equal it (cut_consistent).
Writes results/diag-062/PREFREEZE_SMOKE_GATES_062.json (refuses overwrite) or --output. Observed only: no gate decision, no tuning.
  PYTHONPATH=. python scripts/prefreeze_smoke_062.py /tmp/s62/smoke [--output PATH]"""
import copy,json,shutil,subprocess,sys,tempfile
from pathlib import Path
from unittest import mock
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments import brute_study_062 as ST
from experiments.brute_common_062 import load,write_new,PLAN,B62,WORKERS,ALL_ARMS
from experiments.brute_common import dumps
from scripts import make_gates_062 as MG
from scripts import make_freeze_062 as MF
from scripts import verify_release_0590 as V
from scripts import api_checks_062 as AC
from scripts.recount_062 import main as recount
from scripts.run_reference_062 import main as reference
OUT=ROOT/'results/diag-062/PREFREEZE_SMOKE_GATES_062.json';CAP=3300.0;STEPS=((6,12),(2,12),(2,8),(2,3));SAFETY=1.25;PROBE=ROOT/'results/diag-062/BUDGET_PROBE_062.json'
BY_DESIGN=('GHOST62','GTEST','G_PROC','GW62')
FIELDS=('label','stop','n_min','used','n_rounds','conflicts_spent','wall_guard','clique_prefix','clique_final')


def status(g):return {k:{'pass':v['pass'],**({'reason':v['reason']} if 'reason' in v else {})} for k,v in g['gates'].items()}


def _lpt(walls,workers):
    bins=[0.0]*workers
    for x in sorted(walls,reverse=True):bins[bins.index(min(bins))]+=x
    return max(bins)


def _jobs(nb,ns):
    with mock.patch.object(ST,'N_W2B',nb),mock.patch.object(ST,'N_SEEDS',ns):return ST.jobs_for(load(PLAN),'main')


def projection(res):
    PB=load(PROBE);P=PB['summary'];pol={'B2':'B2','W2':'W2','W2b':'W2'};bm=PB['B62']//1000000
    worst={a:round(SAFETY*P[f'{pol[a]}_B{bm}M']['max_wall_s'],1) for a in pol}
    sm={a:[round(x['case_wall_informational'],1) for c in res['cases'] for g,x in c['arms'].items() if g==a] for a in pol}
    out={'label':'Inferred','source':f'results/diag-062/BUDGET_PROBE_062.json (exploratory, non-fresh seeds) max walls at B62 = {bm}M times '+str(SAFETY),
         'B62':PB['B62'],'worst_per_job_s':worst,'probe_guard_firings_at_B62':{a:P[f'{pol[a]}_B{bm}M']['guard'] for a in pol},
         'smoke_walls_B2M_s':sm,'workers':WORKERS,'cap_s':CAP,'candidates':{}}
    for nb,ns in STEPS:
        J=_jobs(nb,ns);out['candidates'][f'N_W2B={nb},N_SEEDS={ns}']={'jobs':len(J),'worst_run_s':round(_lpt([worst[j[3]] for j in J],WORKERS),1)}
    req=next((x for x in STEPS if out['candidates'][f'N_W2B={x[0]},N_SEEDS={x[1]}']['worst_run_s']<=CAP),STEPS[-1])
    ch=out['candidates'][f'N_W2B={req[0]},N_SEEDS={req[1]}']
    out.update(required={'N_W2B':req[0],'N_SEEDS':req[1]},chosen_projection=ch,cut_exhausted=ch['worst_run_s']>CAP,
               runner={'N_W2B':ST.N_W2B,'N_SEEDS':ST.N_SEEDS},cut_consistent=req==(ST.N_W2B,ST.N_SEEDS),cut_applied=req!=STEPS[0],
               projected_main_worst_s=ch['worst_run_s'],
               caveat='4 probe seeds per policy; every job is assumed to take 1.25 times the slowest probe job of its policy at B62; a probe job stopped by its 2400 s guard is a lower bound')
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
    det=[(c['seed'],ST.canon62(c['arms']['W2'])==ST.canon62(c['arms']['W2b'])) for c in allr if 'W2b' in c['arms']];out['smoke_determinism']=det
    out['all_arms_present']=sorted(a for c in allr for a in c['arms'])==sorted(['B2','B2','W2','W2','W2b','W2b']) and len(allr)==2 and len(det)==2
    out['runtime_projection']=projection(res)
    with tempfile.TemporaryDirectory() as d:
        C=Path(d)/'copy';C.mkdir()
        for nm in ('RESULTS.json','SCIENTIFIC.json','SEAL.json'):shutil.copy(S/nm,C/nm)
        out['recount_rc']=recount([str(C)]);rc=load(C/'RECOUNT_062.json')
        out['recount']={k:rc.get(k) for k in ('cases','records','decided_by_arm','study_decided_by_arm','wrong','mismatches','PASS')}
        out['reference_rc']=reference([str(C),'--block','smoke','--workers','8']);rf=load(C/'REFERENCE_062.json')
        out['reference_smoke']={k:rf.get(k) for k in ('records','decided','audited','complete','per_arm','mismatch_count','vacuous','PASS','elapsed_informational','scope')}|{'mutations':rf['mutation_test']['detected'],'of':rf['mutation_test']['mutations']}
        ac=Path(d)/'API_CHECKS_062.json';p=subprocess.run([sys.executable,str(ROOT/'scripts/api_checks_062.py'),'--output',str(ac)],
            cwd=ROOT,capture_output=True,text=True,timeout=1500,env={'PYTHONPATH':str(ROOT),'PATH':'/usr/bin:/bin'});out['api_checks_rc']=p.returncode
        if p.returncode and not ac.exists():raise SystemExit('api_checks_062 failed: '+p.stderr[-2000:])
        A=load(ac);out['api_checks']={'PASS':A.get('PASS'),'equiv':A.get('equiv'),'ghost':{k:A['ghost'].get(k) for k in A['ghost'] if k not in ('certify20w_closure',)}}
        D=Path(d)/'synthetic';(D/'main').mkdir(parents=True);fz=Path(d)/'FREEZE_STANDIN.json';fz.write_text('{}')
        cases=[dict(copy.deepcopy(c),block='main') for c in res['cases']];P=load(PLAN)
        with mock.patch.object(ST,'FREEZE',fz):
            ST._write(D/'main',P,'main',[f'synthetic:{i}' for i in range(sum(len(c['arms']) for c in cases))],cases,True,{'total_elapsed_informational':res.get('total_elapsed_informational')})
        rr=recount([str(D/'main')]);rf2=reference([str(D/'main'),'--workers','8'])
        n=(len(cases),sum('W2b' in c['arms'] for c in cases));fi=AC.fidelity(D/'main');A2=dict(A,fidelity=fi);(D/'API_CHECKS_062.json').write_text(json.dumps(A2))
        g1=MG.build(D,n);g2=MG.build(D,n)
        out['synthetic']={'cases':n,'recount_rc':rr,'reference_rc':rf2,'gate_status':status(g1),'secondary':{k:v.get('observed') for k,v in g1['secondary'].items() if k!='GSTATS62'},
                          'fidelity_self_replay':{k:v for k,v in fi.items() if k!='per_case'},'fidelity_failures':{k:v for k,v in fi['per_case'].items() if not v['exact']},
                          **{nm:g1['gates'][nm].get('observed') for nm in ('GDET62','GFID62','GW62','GS62_sound','GS_ref')},
                          'certified_readbits2_N20_windows':g1['certified_readbits2_N20_windows'],'sound_no_2bit_gain':g1['sound_no_2bit_gain'],'status_phrase':g1['status_phrase'],
                          'sealed_input_verified':g1.get('sealed_input_verified'),'reproduces':dumps(g1)==dumps(g2),'label_source':g1.get('label_source'),
                          'note':('synthetic: smoke cases as main with the smoke case count; GHOST62 (bound to FREEZE_062, absent before the freeze), GTEST and G_PROC fail by design; '
                                  'GW62 on 2 smoke seeds at B 2M is recorded, not required')}
        Rd=Path(d)/'rel';(Rd/V.STUDY).mkdir(parents=True);(Rd/V.STUDY/'GATES_062.json').write_bytes(dumps(g1))
        Rel={k:'x' for k in V.RELEASE_KEYS};Rel.update(version=V.VERSION,gates_passed=sorted(k for k,v in g1['gates'].items() if v['pass'] is True),
             gates_failed=sorted(k for k,v in g1['gates'].items() if v['pass'] is False),gates_not_exercised=sorted(k for k,v in g1['gates'].items() if v['pass'] is None),
             secondary={k:v['pass'] for k,v in g1['secondary'].items()},certified_readbits2_N20_windows=g1['certified_readbits2_N20_windows'],
             sound_no_2bit_gain=g1['sound_no_2bit_gain'],status_phrase=g1['status_phrase'])
        (Rd/'RELEASE.json').write_text(json.dumps(Rel))
        try:V.release_ok(Rd);out['release_ok_synthetic']=True
        except Exception as e:out['release_ok_synthetic']=f'error: {e}'
    E=MF.entries();h=head();R={'preregistration_commit':E[0]['commit'],'source_freeze_commit':h,'seal_commit':h}
    try:out['verifier_chain']={'passed':True,'entries':[[e['event'],e['commit']] for e in E],'head':h,**V.chain(ROOT,R,E)}
    except Exception as e:out['verifier_chain']={'passed':False,'error':str(e),'entries':[[e['event'],e['commit']] for e in E]}
    vc=out['verifier_chain'];pj=out['runtime_projection'];sy=out['synthetic'];fs=sy['fidelity_self_replay'];gs=sy['gate_status']
    out['PASS']=(out['recount_rc']==0 and out['reference_rc']==0 and sy['recount_rc']==0 and sy['reference_rc']==0 and sy['reproduces']
                 and sy['sealed_input_verified'] and not any('INCOMPLETE_INPUT' in v.get('reason','') for k,v in gs.items() if k not in BY_DESIGN)
                 and gs['G_recount']['pass'] is True and gs['GDET62']['pass'] is True and gs['GFID62']['pass'] is True and gs['GS62_sound']['pass'] is True
                 and gs['GS_ref']['pass'] is True and sy['label_source']=='recount' and fs.get('PASS') is True
                 and out['api_checks_rc']==0 and out['api_checks']['ghost'].get('PASS62') is True and out['api_checks']['equiv']['PASS'] is True
                 and pj['cut_consistent'] and all(x[1] for x in det) and not out['smoke_wall_guard_records'] and out['all_arms_present']
                 and out['release_ok_synthetic'] is True and vc['passed'] and vc.get('authorization_exceptions')==0)
    out['note']=('PASS here means the tooling ran end to end on a sealed block, gates reproduce, the self-replay is exact, the cut rule was '
                 'applied as declared and the real commit-order check passes; GW62 outcome on smoke is recorded, not required')
    write_new(outp,out);print(json.dumps({k:v for k,v in out.items() if k not in ('smoke_records','synthetic','recount')},default=str)[:6000])
    print(json.dumps(gs));return 0 if out['PASS'] else 1


if __name__=='__main__':sys.exit(main())
