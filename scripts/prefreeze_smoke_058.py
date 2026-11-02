"""Pre-freeze smoke-gates, runtime projection and cut check for study-058 (plan 058 runtime_estimate; pre-run deviation #190).
New file; built from scripts/prefreeze_smoke_057.py (frozen). Input: the sealed smoke block written by experiments/brute_study_058.py
--block smoke (outside results/study-058; smoke seeds 12550001-02, all five arms, 10 jobs on one 8-worker pool, conflict-only stop;
12550003 is used only by the api_checks no-network run, 12550004-06 unused). Smoke is never gated and never sets C, B or K. It
  1. lists stops, labels, smoke determinism (canon58 of B4 vs B4_b), wall_guard firings and per-record fields;
  2. runs recount_058 and run_reference_058 (block smoke) on copies and scripts/api_checks_058.py (no --study) into a temp file;
  3. builds a synthetic complete block (smoke cases relabelled 'main'), re-sealed with the runner's _write (stand-in freeze),
     recounted, referenced, self-replayed (GFID58 fidelity, must be exact) and gated twice with the smoke case count (dumps must be
     identical); exercises verify_release_0550.release_ok;
  4. runs verify_release_0550.chain on the repository (ledger since preregistration_058; HEAD stands in for freeze and seal);
  5. runtime projection (Inferred), plan 058 runtime_estimate "at its slowest rate": r_slow = the slowest smoke conflict rate over
     records with case wall >= 1 s; every main job worst = B / r_slow + 10 s (it spends its whole B); the run = LPT of the 5*N58 jobs
     on 8 workers. Declared cut rule: N58 = 12 if that run <= 3300 s else 8 (cut_exhausted if still > 3300 s); the runner's N58 must
     equal it (cut_consistent).
Writes results/diag-058/PREFREEZE_SMOKE_GATES_058.json (refuses overwrite) or --output. Observed only: no gate decision, no tuning.
  PYTHONPATH=. python scripts/prefreeze_smoke_058.py /tmp/s58/smoke [--output PATH]"""
import copy,json,shutil,subprocess,sys,tempfile
from pathlib import Path
from unittest import mock
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments import brute_study_058 as ST
from experiments.brute_common_058 import load,write_new,PLAN,B58,WORKERS,ALL_ARMS
from experiments.brute_common import dumps
from scripts import make_gates_058 as MG
from scripts import make_freeze_058 as MF
from scripts import verify_release_0550 as V
from scripts import api_checks_058 as AC
from scripts.recount_058 import main as recount
from scripts.run_reference_058 import main as reference
OUT=ROOT/'results/diag-058/PREFREEZE_SMOKE_GATES_058.json';CAP=3300.0;STEPS=(12,8)
BY_DESIGN=('GHOST58','GTEST','G_PROC','GB_gain58','GB3_58')
FIELDS=('label','stop','n_min','used','n_rounds','conflicts_spent','wall_guard','distinct_codes')


def status(g):return {k:{'pass':v['pass'],**({'reason':v['reason']} if 'reason' in v else {})} for k,v in g['gates'].items()}


def _lpt(walls,workers):
    bins=[0.0]*workers
    for x in sorted(walls,reverse=True):bins[bins.index(min(bins))]+=x
    return max(bins)


def _jobs(n):
    with mock.patch.object(ST,'N58',n):return ST.jobs_for(load(PLAN),'main')


def projection(res):
    rate=[];walls=[]
    for c in res['cases']:
        walls+=list(c['group_walls_informational'].values())
        for x in c['arms'].values():
            w=x.get('case_wall_informational')
            if w and w>=1.0:rate.append(x['conflicts_spent']/w)
    r=min(rate) if rate else None;worst=B58/r+10.0 if r else None
    out={'label':'Inferred','smoke_slowest_rate':None if r is None else round(r,1),'smoke_rate_max':round(max(rate),1) if rate else None,
         'smoke_job_walls_s':sorted(round(x,1) for x in walls),'worst_per_job_s':None if worst is None else round(worst,1),'workers':WORKERS,'cap_s':CAP,'candidates':{}}
    for n in STEPS:
        J=_jobs(n);out['candidates'][f'N58={n}']={'jobs':len(J),'worst_run_s':None if worst is None else round(_lpt([worst]*len(J),WORKERS),1),
                                                  'smoke_mean_run_s':round(_lpt([sum(walls)/len(walls)]*len(J),WORKERS),1) if walls else None}
    w0=out['candidates'][f'N58={STEPS[0]}']['worst_run_s']
    req=STEPS[0] if w0 is not None and w0<=CAP else STEPS[1];ch=out['candidates'][f'N58={req}']
    out.update(required={'N58':req},chosen_projection=ch,cut_exhausted=ch['worst_run_s'] is None or ch['worst_run_s']>CAP,
               runner={'N58':ST.N58},cut_consistent=req==ST.N58,cut_applied=req!=STEPS[0],projected_main_worst_s=ch['worst_run_s'],
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
    det=[(c['seed'],ST.canon58(c['arms']['B4'])==ST.canon58(c['arms']['B4_b'])) for c in allr];out['smoke_determinism']=det
    out['all_arms_present']=all(sorted(c['arms'])==sorted(ALL_ARMS) for c in allr) and len(allr)==2
    out['runtime_projection']=projection(res)
    with tempfile.TemporaryDirectory() as d:
        C=Path(d)/'copy';C.mkdir()
        for nm in ('RESULTS.json','SCIENTIFIC.json','SEAL.json'):shutil.copy(S/nm,C/nm)
        out['recount_rc']=recount([str(C)]);rc=load(C/'RECOUNT_058.json')
        out['recount']={k:rc.get(k) for k in ('cases','records','decided_by_arm','study_decided_by_arm','wrong','mismatches','PASS')}
        out['reference_rc']=reference([str(C),'--block','smoke','--workers','8']);rf=load(C/'REFERENCE_058.json')
        out['reference_smoke']={k:rf.get(k) for k in ('records','decided','audited','complete','per_arm','mismatch_count','vacuous','PASS','elapsed_informational','scope')}|{'mutations':rf['mutation_test']['detected'],'of':rf['mutation_test']['mutations']}
        ac=Path(d)/'API_CHECKS_058.json';p=subprocess.run([sys.executable,str(ROOT/'scripts/api_checks_058.py'),'--output',str(ac)],
            cwd=ROOT,capture_output=True,text=True,timeout=1500,env={'PYTHONPATH':str(ROOT),'PATH':'/usr/bin:/bin'});out['api_checks_rc']=p.returncode
        if p.returncode and not ac.exists():raise SystemExit('api_checks_058 failed: '+p.stderr[-2000:])
        A=load(ac);out['api_checks']={'PASS':A.get('PASS'),'equiv':A.get('equiv'),'ghost':{k:A['ghost'].get(k) for k in A['ghost'] if k not in ('certify20b_closure',)}}
        D=Path(d)/'synthetic';(D/'main').mkdir(parents=True);fz=Path(d)/'FREEZE_STANDIN.json';fz.write_text('{}')
        cases=[dict(copy.deepcopy(c),block='main') for c in res['cases']];P=load(PLAN)
        with mock.patch.object(ST,'FREEZE',fz):
            ST._write(D/'main',P,'main',[f'synthetic:{i}' for i in range(sum(len(c['arms']) for c in cases))],cases,True,{'total_elapsed_informational':res.get('total_elapsed_informational')})
        rr=recount([str(D/'main')]);rf2=reference([str(D/'main'),'--workers','8'])
        n=len(cases);fi=AC.fidelity(D/'main');A2=dict(A,fidelity=fi);(D/'API_CHECKS_058.json').write_text(json.dumps(A2))
        g1=MG.build(D,n);g2=MG.build(D,n)
        out['synthetic']={'cases':n,'recount_rc':rr,'reference_rc':rf2,'gate_status':status(g1),'secondary':{k:v.get('observed') for k,v in g1['secondary'].items() if k!='PER_ARM58'},
                          'fidelity_self_replay':{k:v for k,v in fi.items() if k!='per_case'},'fidelity_failures':{k:v for k,v in fi['per_case'].items() if not v['exact']},
                          **{nm:g1['gates'][nm].get('observed') for nm in ('GDET58','GFID58','GB_gain58','GB3_58','GS58_sound','GS_ref')},
                          'certified_readbits_N20':g1['certified_readbits_N20'],'sound_not_certified_readbits':g1['sound_not_certified_readbits'],'status_phrase':g1['status_phrase'],
                          'sealed_input_verified':g1.get('sealed_input_verified'),'reproduces':dumps(g1)==dumps(g2),'label_source':g1.get('label_source'),
                          'note':('synthetic: smoke cases as main with the smoke case count; GHOST58 (no 058 freeze yet), GTEST and G_PROC fail by design; '
                                  'GB_gain58 / GB3_58 on 2 smoke seeds are recorded, not required')}
        Rd=Path(d)/'rel';(Rd/V.STUDY).mkdir(parents=True);(Rd/V.STUDY/'GATES_058.json').write_bytes(dumps(g1))
        Rel={k:'x' for k in V.RELEASE_KEYS};Rel.update(version=V.VERSION,gates_passed=sorted(k for k,v in g1['gates'].items() if v['pass'] is True),
             gates_failed=sorted(k for k,v in g1['gates'].items() if v['pass'] is False),gates_not_exercised=sorted(k for k,v in g1['gates'].items() if v['pass'] is None),
             secondary={k:v['pass'] for k,v in g1['secondary'].items()},certified_readbits_N20=g1['certified_readbits_N20'],
             sound_not_certified_readbits=g1['sound_not_certified_readbits'],status_phrase=g1['status_phrase'])
        (Rd/'RELEASE.json').write_text(json.dumps(Rel))
        try:V.release_ok(Rd);out['release_ok_synthetic']=True
        except Exception as e:out['release_ok_synthetic']=f'error: {e}'
    E=MF.entries();h=head();R={'preregistration_commit':E[0]['commit'],'source_freeze_commit':h,'seal_commit':h}
    try:out['verifier_chain']={'passed':True,'entries':[[e['event'],e['commit']] for e in E],'head':h,**V.chain(ROOT,R,E)}
    except Exception as e:out['verifier_chain']={'passed':False,'error':str(e),'entries':[[e['event'],e['commit']] for e in E]}
    vc=out['verifier_chain'];pj=out['runtime_projection'];sy=out['synthetic'];fs=sy['fidelity_self_replay'];gs=sy['gate_status']
    out['PASS']=(out['recount_rc']==0 and out['reference_rc']==0 and sy['recount_rc']==0 and sy['reference_rc']==0 and sy['reproduces']
                 and sy['sealed_input_verified'] and not any('INCOMPLETE_INPUT' in v.get('reason','') for k,v in gs.items() if k not in BY_DESIGN)
                 and gs['G_recount']['pass'] is True and gs['GDET58']['pass'] is True and gs['GFID58']['pass'] is True and gs['GS58_sound']['pass'] is True
                 and gs['GS_ref']['pass'] is True and sy['label_source']=='recount' and fs.get('PASS') is True
                 and out['api_checks_rc']==0 and out['api_checks']['ghost'].get('PASS58') is True and out['api_checks']['equiv']['PASS'] is True
                 and pj['cut_consistent'] and all(x[1] for x in det) and not out['smoke_wall_guard_records'] and out['all_arms_present']
                 and out['release_ok_synthetic'] is True and vc['passed'] and vc.get('authorization_exceptions')==0)
    out['note']=('PASS here means the tooling ran end to end on a sealed block, gates reproduce, the self-replay is exact, the cut rule was '
                 'applied as declared and the real commit-order check passes; GB_gain58 / GB3_58 outcomes on smoke are recorded, not required')
    write_new(outp,out);print(json.dumps({k:v for k,v in out.items() if k not in ('smoke_records','synthetic','recount')},default=str)[:6000])
    print(json.dumps(gs));return 0 if out['PASS'] else 1


if __name__=='__main__':sys.exit(main())
