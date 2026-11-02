"""Pre-freeze smoke-gates, runtime projection and cut check for study-060 (plan 060 runtime_estimate; pre-run deviation #194).
New file; built from scripts/prefreeze_smoke_059.py (frozen). Input: the sealed smoke block written by experiments/brute_study_060.py
--block smoke (outside results/study-060; smoke seeds 12600301-02 on all three arms, 6 jobs on one 8-worker pool, B 2000000 for
smoke only, conflict-only stop; 12600303 is used only by the api_checks no-network run, 12600304-06 unused). Smoke is never gated
and never sets C, B or K. It
  1. lists stops, labels, smoke determinism (canon60 of S24 vs S24b), wall_guard firings and per-record fields;
  2. runs recount_060 and run_reference_060 (block smoke) on copies and scripts/api_checks_060.py (no --study) into a temp file;
  3. builds a synthetic complete block (smoke cases relabelled 'main'), re-sealed with the runner's _write (stand-in freeze),
     recounted, referenced, self-replayed (GFID60 fidelity, must be exact) and gated twice with the smoke case counts (dumps must be
     identical); exercises verify_release_0570.release_ok;
  4. runs verify_release_0570.chain on the repository (ledger since preregistration_060; HEAD stands in for freeze and seal);
  5. runtime projection (Inferred), plan 060 runtime_estimate: smoke runs at B 2M, so the per-job worst comes from the exploratory
     budget probe (results/diag-060/BUDGET_PROBE_060.json, same code path at B 8M, 8 workers): worst(n) = 1.25 * the probe's max
     wall at n and B 8M; the run = LPT of the declared main jobs on 8 workers. Load check (reported): smoke walls at B 2M against
     1.5 * the probe's max walls at B 2M. Declared cut rule: N32 = 6 if that run <= 3300 s else 0 (cut_exhausted if still > 3300 s);
     the runner's N32 must equal it (cut_consistent). S24 / S24b are never cut.
Writes results/diag-060/PREFREEZE_SMOKE_GATES_060.json (refuses overwrite) or --output. Observed only: no gate decision, no tuning.
  PYTHONPATH=. python scripts/prefreeze_smoke_060.py /tmp/s60/smoke [--output PATH]"""
import copy,json,shutil,subprocess,sys,tempfile
from pathlib import Path
from unittest import mock
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments import brute_study_060 as ST
from experiments.brute_common_060 import load,write_new,PLAN,B60,WORKERS,ALL_ARMS
from experiments.brute_common import dumps
from scripts import make_gates_060 as MG
from scripts import make_freeze_060 as MF
from scripts import verify_release_0570 as V
from scripts import api_checks_060 as AC
from scripts.recount_060 import main as recount
from scripts.run_reference_060 import main as reference
OUT=ROOT/'results/diag-060/PREFREEZE_SMOKE_GATES_060.json';CAP=3300.0;STEPS=(6,0);SAFETY=1.25;PROBE=ROOT/'results/diag-060/BUDGET_PROBE_060.json'
BY_DESIGN=('GHOST60','GTEST','G_PROC','GN24_60')
FIELDS=('label','stop','n_min','true_size','used','n_rounds','conflicts_spent','wall_guard')


def status(g):return {k:{'pass':v['pass'],**({'reason':v['reason']} if 'reason' in v else {})} for k,v in g['gates'].items()}


def _lpt(walls,workers):
    bins=[0.0]*workers
    for x in sorted(walls,reverse=True):bins[bins.index(min(bins))]+=x
    return max(bins)


def _jobs(n):
    with mock.patch.object(ST,'N32',n):return ST.jobs_for(load(PLAN),'main')


def projection(res):
    P=load(PROBE)['summary'];size={'S24':24,'S24b':24,'S32':32}
    worst={a:round(SAFETY*P[f'n{size[a]}_B8M']['max_wall_s'],1) for a in size}
    sm={a:[round(x['case_wall_informational'],1) for c in res['cases'] for g,x in c['arms'].items() if g==a] for a in size}
    p2={a:P[f'n{size[a]}_B2M']['max_wall_s'] for a in size}
    out={'label':'Inferred','source':'results/diag-060/BUDGET_PROBE_060.json (exploratory, non-fresh seeds) max walls at B 8M times '+str(SAFETY),
         'worst_per_job_s':worst,'probe_max_wall_B2M_s':p2,'smoke_walls_B2M_s':sm,
         'load_check_reported':{a:bool(sm[a]) and max(sm[a])<=1.5*p2[a] for a in size},'workers':WORKERS,'cap_s':CAP,'candidates':{}}
    for n in STEPS:
        J=_jobs(n);out['candidates'][f'N32={n}']={'jobs':len(J),'worst_run_s':round(_lpt([worst[j[3]] for j in J],WORKERS),1)}
    w0=out['candidates'][f'N32={STEPS[0]}']['worst_run_s']
    req=STEPS[0] if w0<=CAP else STEPS[1];ch=out['candidates'][f'N32={req}']
    out.update(required={'N32':req},chosen_projection=ch,cut_exhausted=ch['worst_run_s']>CAP,
               runner={'N32':ST.N32,'N24':ST.N24},cut_consistent=req==ST.N32 and ST.N24==12,cut_applied=req!=STEPS[0],projected_main_worst_s=ch['worst_run_s'],
               caveat='4 probe seeds per size; every job is assumed to take 1.25 times the slowest probe job of its size; S32 jobs may also stop at the 3600 s case kill')
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
    det=[(c['seed'],ST.canon60(c['arms']['S24'])==ST.canon60(c['arms']['S24b'])) for c in allr if c['key']=='scale24w'];out['smoke_determinism']=det
    out['all_arms_present']=sorted(a for c in allr for a in c['arms'])==sorted(['S24','S24','S24b','S24b','S32','S32']) and len(allr)==4 and len(det)==2
    out['runtime_projection']=projection(res)
    with tempfile.TemporaryDirectory() as d:
        C=Path(d)/'copy';C.mkdir()
        for nm in ('RESULTS.json','SCIENTIFIC.json','SEAL.json'):shutil.copy(S/nm,C/nm)
        out['recount_rc']=recount([str(C)]);rc=load(C/'RECOUNT_060.json')
        out['recount']={k:rc.get(k) for k in ('cases','records','decided_by_arm','study_decided_by_arm','wrong_by_arm','mismatches','PASS')}
        out['reference_rc']=reference([str(C),'--block','smoke','--workers','8']);rf=load(C/'REFERENCE_060.json')
        out['reference_smoke']={k:rf.get(k) for k in ('records','decided','audited','complete','per_arm','mismatch_count','vacuous','PASS','elapsed_informational','scope')}|{'mutations':rf['mutation_test']['detected'],'of':rf['mutation_test']['mutations']}
        ac=Path(d)/'API_CHECKS_060.json';p=subprocess.run([sys.executable,str(ROOT/'scripts/api_checks_060.py'),'--output',str(ac)],
            cwd=ROOT,capture_output=True,text=True,timeout=1500,env={'PYTHONPATH':str(ROOT),'PATH':'/usr/bin:/bin'});out['api_checks_rc']=p.returncode
        if p.returncode and not ac.exists():raise SystemExit('api_checks_060 failed: '+p.stderr[-2000:])
        A=load(ac);out['api_checks']={'PASS':A.get('PASS'),'equiv':A.get('equiv'),'ghost':{k:A['ghost'].get(k) for k in A['ghost'] if k not in ('certify32b_closure',)}}
        D=Path(d)/'synthetic';(D/'main').mkdir(parents=True);fz=Path(d)/'FREEZE_STANDIN.json';fz.write_text('{}')
        cases=[dict(copy.deepcopy(c),block='main') for c in res['cases']];P=load(PLAN)
        with mock.patch.object(ST,'FREEZE',fz):
            ST._write(D/'main',P,'main',[f'synthetic:{i}' for i in range(sum(len(c['arms']) for c in cases))],cases,True,{'total_elapsed_informational':res.get('total_elapsed_informational')})
        rr=recount([str(D/'main')]);rf2=reference([str(D/'main'),'--workers','8'])
        n=(sum(c['key']=='scale24w' for c in cases),sum(c['key']=='scale32w' for c in cases));fi=AC.fidelity(D/'main');A2=dict(A,fidelity=fi);(D/'API_CHECKS_060.json').write_text(json.dumps(A2))
        g1=MG.build(D,n);g2=MG.build(D,n)
        out['synthetic']={'cases':n,'recount_rc':rr,'reference_rc':rf2,'gate_status':status(g1),'secondary':{k:v.get('observed') for k,v in g1['secondary'].items() if k!='GSTATS60'},
                          'fidelity_self_replay':{k:v for k,v in fi.items() if k!='per_case'},'fidelity_failures':{k:v for k,v in fi['per_case'].items() if not v['exact']},
                          **{nm:g1['gates'][nm].get('observed') for nm in ('GDET60','GFID60','GN24_60','GS60_sound','GS_ref')},
                          'certified_readbits4_N24':g1['certified_readbits4_N24'],'sound_not_certified_N24':g1['sound_not_certified_N24'],'status_phrase':g1['status_phrase'],
                          'sealed_input_verified':g1.get('sealed_input_verified'),'reproduces':dumps(g1)==dumps(g2),'label_source':g1.get('label_source'),
                          'note':('synthetic: smoke cases as main with the smoke case count; GHOST60 (no 060 freeze yet), GTEST and G_PROC fail by design; '
                                  'GN24_60 on 2 smoke seeds at B 2M is recorded, not required')}
        Rd=Path(d)/'rel';(Rd/V.STUDY).mkdir(parents=True);(Rd/V.STUDY/'GATES_060.json').write_bytes(dumps(g1))
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
                 and gs['G_recount']['pass'] is True and gs['GDET60']['pass'] is True and gs['GFID60']['pass'] is True and gs['GS60_sound']['pass'] is True
                 and gs['GS_ref']['pass'] is True and sy['label_source']=='recount' and fs.get('PASS') is True
                 and out['api_checks_rc']==0 and out['api_checks']['ghost'].get('PASS60') is True and out['api_checks']['equiv']['PASS'] is True
                 and pj['cut_consistent'] and all(x[1] for x in det) and not out['smoke_wall_guard_records'] and out['all_arms_present']
                 and out['release_ok_synthetic'] is True and vc['passed'] and vc.get('authorization_exceptions')==0)
    out['note']=('PASS here means the tooling ran end to end on a sealed block, gates reproduce, the self-replay is exact, the cut rule was '
                 'applied as declared and the real commit-order check passes; GN24_60 outcome on smoke are recorded, not required')
    write_new(outp,out);print(json.dumps({k:v for k,v in out.items() if k not in ('smoke_records','synthetic','recount')},default=str)[:6000])
    print(json.dumps(gs));return 0 if out['PASS'] else 1


if __name__=='__main__':sys.exit(main())
