"""Pre-freeze smoke-gates, runtime projection and cut check for study-059 (plan 059 runtime_estimate; pre-run deviation #192).
New file; built from scripts/prefreeze_smoke_058.py (frozen). Input: the sealed smoke block written by experiments/brute_study_059.py
--block smoke (outside results/study-059; smoke seeds 12590051-52, all five arms, 10 jobs on one 8-worker pool, conflict-only stop;
12590053 is used only by the api_checks no-network run, 12590054-56 unused). Smoke is never gated and never sets C, B or K. It
  1. lists stops, labels, smoke determinism (canon59 of N4_10 vs N4_10b), wall_guard firings and per-record fields;
  2. runs recount_059 and run_reference_059 (block smoke) on copies and scripts/api_checks_059.py (no --study) into a temp file;
  3. builds a synthetic complete block (smoke cases relabelled 'main'), re-sealed with the runner's _write (stand-in freeze),
     recounted, referenced, self-replayed (GFID59 fidelity, must be exact) and gated twice with the smoke case count (dumps must be
     identical); exercises verify_release_0560.release_ok;
  4. runs verify_release_0560.chain on the repository (ledger since preregistration_059; HEAD stands in for freeze and seal);
  5. runtime projection (Inferred), plan 059 runtime_estimate "at its slowest rate": r_slow = the slowest smoke conflict rate over
     records with case wall >= 1 s; every main job worst = B / r_slow + 10 s (it spends its whole B); the run = LPT of the 5*N59 jobs
     on 8 workers. Declared cut rule: N59 = 12 if that run <= 3300 s else 8 (cut_exhausted if still > 3300 s); the runner's N59 must
     equal it (cut_consistent).
Writes results/diag-059/PREFREEZE_SMOKE_GATES_059.json (refuses overwrite) or --output. Observed only: no gate decision, no tuning.
  PYTHONPATH=. python scripts/prefreeze_smoke_059.py /tmp/s59/smoke [--output PATH]"""
import copy,json,shutil,subprocess,sys,tempfile
from pathlib import Path
from unittest import mock
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments import brute_study_059 as ST
from experiments.brute_common_059 import load,write_new,PLAN,B59,WORKERS,ALL_ARMS
from experiments.brute_common import dumps
from scripts import make_gates_059 as MG
from scripts import make_freeze_059 as MF
from scripts import verify_release_0560 as V
from scripts import api_checks_059 as AC
from scripts.recount_059 import main as recount
from scripts.run_reference_059 import main as reference
OUT=ROOT/'results/diag-059/PREFREEZE_SMOKE_GATES_059.json';CAP=3300.0;STEPS=(12,8)
BY_DESIGN=('GHOST59','GTEST','G_PROC','GN_keep59','GN05_59')
FIELDS=('label','stop','n_min','used','n_rounds','conflicts_spent','wall_guard','reads_total','maj_errors')


def status(g):return {k:{'pass':v['pass'],**({'reason':v['reason']} if 'reason' in v else {})} for k,v in g['gates'].items()}


def _lpt(walls,workers):
    bins=[0.0]*workers
    for x in sorted(walls,reverse=True):bins[bins.index(min(bins))]+=x
    return max(bins)


def _jobs(n):
    with mock.patch.object(ST,'N59',n):return ST.jobs_for(load(PLAN),'main')


def projection(res):
    rate=[];walls=[]
    for c in res['cases']:
        walls+=list(c['group_walls_informational'].values())
        for x in c['arms'].values():
            w=x.get('case_wall_informational')
            if w and w>=1.0:rate.append(x['conflicts_spent']/w)
    r=min(rate) if rate else None;worst=B59/r+10.0 if r else None
    out={'label':'Inferred','smoke_slowest_rate':None if r is None else round(r,1),'smoke_rate_max':round(max(rate),1) if rate else None,
         'smoke_job_walls_s':sorted(round(x,1) for x in walls),'worst_per_job_s':None if worst is None else round(worst,1),'workers':WORKERS,'cap_s':CAP,'candidates':{}}
    for n in STEPS:
        J=_jobs(n);out['candidates'][f'N59={n}']={'jobs':len(J),'worst_run_s':None if worst is None else round(_lpt([worst]*len(J),WORKERS),1),
                                                  'smoke_mean_run_s':round(_lpt([sum(walls)/len(walls)]*len(J),WORKERS),1) if walls else None}
    w0=out['candidates'][f'N59={STEPS[0]}']['worst_run_s']
    req=STEPS[0] if w0 is not None and w0<=CAP else STEPS[1];ch=out['candidates'][f'N59={req}']
    out.update(required={'N59':req},chosen_projection=ch,cut_exhausted=ch['worst_run_s'] is None or ch['worst_run_s']>CAP,
               runner={'N59':ST.N59},cut_consistent=req==ST.N59,cut_applied=req!=STEPS[0],projected_main_worst_s=ch['worst_run_s'],
               caveat='two smoke seeds; the worst case assumes every job spends its whole B at the slowest smoke rate')
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
    det=[(c['seed'],ST.canon59(c['arms']['N4_10'])==ST.canon59(c['arms']['N4_10b'])) for c in allr];out['smoke_determinism']=det
    out['all_arms_present']=all(sorted(c['arms'])==sorted(ALL_ARMS) for c in allr) and len(allr)==2
    out['runtime_projection']=projection(res)
    with tempfile.TemporaryDirectory() as d:
        C=Path(d)/'copy';C.mkdir()
        for nm in ('RESULTS.json','SCIENTIFIC.json','SEAL.json'):shutil.copy(S/nm,C/nm)
        out['recount_rc']=recount([str(C)]);rc=load(C/'RECOUNT_059.json')
        out['recount']={k:rc.get(k) for k in ('cases','records','decided_by_arm','study_decided_by_arm','wrong_by_arm','mismatches','PASS')}
        out['reference_rc']=reference([str(C),'--block','smoke','--workers','8']);rf=load(C/'REFERENCE_059.json')
        out['reference_smoke']={k:rf.get(k) for k in ('records','decided','audited','complete','per_arm','mismatch_count','vacuous','PASS','elapsed_informational','scope')}|{'mutations':rf['mutation_test']['detected'],'of':rf['mutation_test']['mutations']}
        ac=Path(d)/'API_CHECKS_059.json';p=subprocess.run([sys.executable,str(ROOT/'scripts/api_checks_059.py'),'--output',str(ac)],
            cwd=ROOT,capture_output=True,text=True,timeout=1500,env={'PYTHONPATH':str(ROOT),'PATH':'/usr/bin:/bin'});out['api_checks_rc']=p.returncode
        if p.returncode and not ac.exists():raise SystemExit('api_checks_059 failed: '+p.stderr[-2000:])
        A=load(ac);out['api_checks']={'PASS':A.get('PASS'),'equiv':A.get('equiv'),'ghost':{k:A['ghost'].get(k) for k in A['ghost'] if k not in ('certify20n_closure',)}}
        D=Path(d)/'synthetic';(D/'main').mkdir(parents=True);fz=Path(d)/'FREEZE_STANDIN.json';fz.write_text('{}')
        cases=[dict(copy.deepcopy(c),block='main') for c in res['cases']];P=load(PLAN)
        with mock.patch.object(ST,'FREEZE',fz):
            ST._write(D/'main',P,'main',[f'synthetic:{i}' for i in range(sum(len(c['arms']) for c in cases))],cases,True,{'total_elapsed_informational':res.get('total_elapsed_informational')})
        rr=recount([str(D/'main')]);rf2=reference([str(D/'main'),'--workers','8'])
        n=len(cases);fi=AC.fidelity(D/'main');A2=dict(A,fidelity=fi);(D/'API_CHECKS_059.json').write_text(json.dumps(A2))
        g1=MG.build(D,n);g2=MG.build(D,n)
        out['synthetic']={'cases':n,'recount_rc':rr,'reference_rc':rf2,'gate_status':status(g1),'secondary':{k:v.get('observed') for k,v in g1['secondary'].items() if k!='GSTATS59'},
                          'fidelity_self_replay':{k:v for k,v in fi.items() if k!='per_case'},'fidelity_failures':{k:v for k,v in fi['per_case'].items() if not v['exact']},
                          **{nm:g1['gates'][nm].get('observed') for nm in ('GDET59','GFID59','GN_keep59','GN05_59','GMAJ59','GS59_sound','GS_ref')},
                          'certified_noisy_readbits4_N20':g1['certified_noisy_readbits4_N20'],'sound_not_certified_noisy':g1['sound_not_certified_noisy'],'status_phrase':g1['status_phrase'],
                          'sealed_input_verified':g1.get('sealed_input_verified'),'reproduces':dumps(g1)==dumps(g2),'label_source':g1.get('label_source'),
                          'note':('synthetic: smoke cases as main with the smoke case count; GHOST59 (no 059 freeze yet), GTEST and G_PROC fail by design; '
                                  'GN_keep59 / GN05_59 on 2 smoke seeds are recorded, not required')}
        Rd=Path(d)/'rel';(Rd/V.STUDY).mkdir(parents=True);(Rd/V.STUDY/'GATES_059.json').write_bytes(dumps(g1))
        Rel={k:'x' for k in V.RELEASE_KEYS};Rel.update(version=V.VERSION,gates_passed=sorted(k for k,v in g1['gates'].items() if v['pass'] is True),
             gates_failed=sorted(k for k,v in g1['gates'].items() if v['pass'] is False),gates_not_exercised=sorted(k for k,v in g1['gates'].items() if v['pass'] is None),
             secondary={k:v['pass'] for k,v in g1['secondary'].items()},certified_noisy_readbits4_N20=g1['certified_noisy_readbits4_N20'],
             sound_not_certified_noisy=g1['sound_not_certified_noisy'],status_phrase=g1['status_phrase'])
        (Rd/'RELEASE.json').write_text(json.dumps(Rel))
        try:V.release_ok(Rd);out['release_ok_synthetic']=True
        except Exception as e:out['release_ok_synthetic']=f'error: {e}'
    E=MF.entries();h=head();R={'preregistration_commit':E[0]['commit'],'source_freeze_commit':h,'seal_commit':h}
    try:out['verifier_chain']={'passed':True,'entries':[[e['event'],e['commit']] for e in E],'head':h,**V.chain(ROOT,R,E)}
    except Exception as e:out['verifier_chain']={'passed':False,'error':str(e),'entries':[[e['event'],e['commit']] for e in E]}
    vc=out['verifier_chain'];pj=out['runtime_projection'];sy=out['synthetic'];fs=sy['fidelity_self_replay'];gs=sy['gate_status']
    out['PASS']=(out['recount_rc']==0 and out['reference_rc']==0 and sy['recount_rc']==0 and sy['reference_rc']==0 and sy['reproduces']
                 and sy['sealed_input_verified'] and not any('INCOMPLETE_INPUT' in v.get('reason','') for k,v in gs.items() if k not in BY_DESIGN)
                 and gs['G_recount']['pass'] is True and gs['GDET59']['pass'] is True and gs['GFID59']['pass'] is True and gs['GS59_sound']['pass'] is True
                 and gs['GS_ref']['pass'] is True and sy['label_source']=='recount' and fs.get('PASS') is True
                 and out['api_checks_rc']==0 and out['api_checks']['ghost'].get('PASS59') is True and out['api_checks']['equiv']['PASS'] is True
                 and pj['cut_consistent'] and all(x[1] for x in det) and not out['smoke_wall_guard_records'] and out['all_arms_present']
                 and out['release_ok_synthetic'] is True and vc['passed'] and vc.get('authorization_exceptions')==0)
    out['note']=('PASS here means the tooling ran end to end on a sealed block, gates reproduce, the self-replay is exact, the cut rule was '
                 'applied as declared and the real commit-order check passes; GN_keep59 / GN05_59 / GMAJ59 outcomes on smoke are recorded, not required')
    write_new(outp,out);print(json.dumps({k:v for k,v in out.items() if k not in ('smoke_records','synthetic','recount')},default=str)[:6000])
    print(json.dumps(gs));return 0 if out['PASS'] else 1


if __name__=='__main__':sys.exit(main())
