"""Pre-freeze smoke-gates, runtime projection and cut check for study-065 (plan 065 runtime_projection; pre-run deviation #204).
New file; built from scripts/prefreeze_smoke_064.py (frozen). Input: the sealed smoke block written by experiments/brute_study_065.py
--block smoke (outside results/study-065; smoke seed 12650301 on every arm C20, S10, S20, S30, S30b, 5 jobs on one 6-worker pool,
B 2000000 for smoke only, conflict-only stop; 12650303 is used only by the api_checks no-network run, 12650302 by the equivalence
check, 12650304-06 unused). Smoke is never gated and never sets C, B, K, eps_bar or delta. It
  1. lists stops, labels, read counts, smoke determinism (canon65 of S30 vs S30b), the read-free equality of every noisy arm with
     C20 (canon_inner), wall_guard firings and per-record fields;
  2. runs recount_065 and run_reference_065 (block smoke) on copies and scripts/api_checks_065.py (no --study) into a temp file;
  3. builds a synthetic complete block (smoke cases relabelled 'main'), re-sealed with the runner's _write (stand-in freeze),
     recounted, referenced, self-replayed (GFID65 fidelity, must be exact) and gated twice with the smoke case counts (dumps must be
     identical); exercises verify_release_0620.release_ok;
  4. runs verify_release_0620.chain on the repository (ledger since preregistration_065, the v0.61.0 release-closing entries
     excluded as declared in #204; HEAD stands in for freeze and seal);
  5. runtime projection (Inferred), plan 065 runtime_projection: every arm repeats the C20 SAT work (GEQ65), so each arm's n jobs
     are assigned the n largest of the six sealed study-064 P20 case walls (frozen certify/20p, B 8M, 6 workers, same scale20
     generator) times SAFETY 1.25; the run = LPT of the declared main jobs on 6 workers. Declared cut rule (plan): candidates
     (N_S20, N_S10) = (6, 6), (3, 6), (3, 3); the first whose projection is <= CUT_AT 2000 s is required, else the last
     (cut_exhausted, disclosed); the runner's N_S20 and N_S10 must equal it (cut_consistent).
Writes results/diag-065/PREFREEZE_SMOKE_GATES_065.json (refuses overwrite) or --output. Observed only: no gate decision, no tuning.
  PYTHONPATH=. python scripts/prefreeze_smoke_065.py /tmp/s65/smoke [--output PATH]"""
import copy,json,shutil,subprocess,sys,tempfile
from pathlib import Path
from unittest import mock
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments import brute_study_065 as ST
from experiments.brute_common_065 import load,write_new,PLAN,B65,WORKERS,ALL_ARMS,NOISY,MAIN_CAP_S
from experiments.brute_common import dumps
from scripts import make_gates_065 as MG
from scripts import make_freeze_065 as MF
from scripts import verify_release_0620 as V
from scripts import api_checks_065 as AC
from scripts.recount_065 import main as recount
from scripts.run_reference_065 import main as reference
OUT=ROOT/'results/diag-065/PREFREEZE_SMOKE_GATES_065.json';CUT_AT=2000.0;CAP=MAIN_CAP_S;STEPS=((6,6),(3,6),(3,3));SAFETY=1.25
P20REF='results/study-064/main'
BY_DESIGN=('GHOST65','GTEST65','G_PROC65','GN65','GN_low65')
REQUIRED=('G_recount65','GDET65','GFID65','GS65_sound','GS_ref65','GMAJ65','GEQ65')
FIELDS=('label','stop','n_min','used','n_rounds','conflicts_spent','wall_guard','observations','reads_total','fixed_reads_total','settled_bit_errors')


def status(g):return {k:{'pass':v['pass'],**({'reason':v['reason']} if 'reason' in v else {})} for k,v in g['gates'].items()}


def _lpt(walls,workers):
    bins=[0.0]*workers
    for x in sorted(walls,reverse=True):bins[bins.index(min(bins))]+=x
    return max(bins)


def _jobs(n20,n10):
    with mock.patch.object(ST,'N_S20',n20),mock.patch.object(ST,'N_S10',n10):return ST.jobs_for(load(PLAN),'main')


def _p20_walls():
    from scripts.study064_storage import ensure_raw
    ensure_raw();R=load(ROOT/P20REF/'RESULTS.json')
    return sorted((x['case_wall_informational'] for c in R['cases'] for g,x in c['arms'].items() if g=='P20'),reverse=True)


def projection(res):
    w=_p20_walls();worst=[round(SAFETY*x,1) for x in w]
    sm={a:[round(x['case_wall_informational'],1) for c in res['cases'] for g,x in c['arms'].items() if g==a] for a in ALL_ARMS}
    out={'label':'Inferred','source':(f'sealed {P20REF} P20 case walls (frozen certify/20p, B 8M, 6 workers, scale20 generator) times {SAFETY}; '
                                      'each arm\'s n jobs take the n largest (every arm repeats the C20 SAT work, GEQ65)'),
         'B65':B65,'sealed_064_P20_walls_s':[round(x,1) for x in w],'per_job_walls_s':worst,'smoke_walls_B2M_s':sm,'workers':WORKERS,'cut_at_s':CUT_AT,
         'main_cap_s':CAP,'candidates':{}}
    for n20,n10 in STEPS:
        J=_jobs(n20,n10);cnt={}
        for j in J:cnt[j[3]]=cnt.get(j[3],0)+1
        walls=[x for a,n in cnt.items() for x in worst[:n]]
        out['candidates'][f'N_S20={n20},N_S10={n10}']={'jobs':len(J),'per_arm':cnt,'projected_run_s':round(_lpt(walls,WORKERS),1),'cpu_s':round(sum(walls),1)}
    req=next((x for x in STEPS if out['candidates'][f'N_S20={x[0]},N_S10={x[1]}']['projected_run_s']<=CUT_AT),STEPS[-1])
    ch=out['candidates'][f'N_S20={req[0]},N_S10={req[1]}']
    out.update(required={'N_S20':req[0],'N_S10':req[1]},chosen_projection=ch,cut_exhausted=ch['projected_run_s']>CUT_AT,
               runner={'N_S20':ST.N_S20,'N_S10':ST.N_S10,'N_SEEDS':ST.N_SEEDS,'N_S30B':ST.N_S30B},cut_consistent=req==(ST.N_S20,ST.N_S10),cut_applied=req!=STEPS[0],
               projected_main_s=ch['projected_run_s'],
               caveat=('the 065 seeds are fresh, so their walls can differ from the 064 seeds; the 1800 s case kill and the 2400 s main cap '
                       '(seal-partial) still bound the run'))
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
    det=[(c['seed'],ST.canon65(c['arms']['S30'])==ST.canon65(c['arms']['S30b'])) for c in allr if 'S30b' in c['arms']];out['smoke_determinism']=det
    eq=[(c['seed'],a,ST.canon_inner(c['arms'][a])==ST.canon_inner(c['arms']['C20'])) for c in allr for a in NOISY if a in c['arms'] and 'C20' in c['arms']]
    out['smoke_inner_equal_C20']=eq
    out['smoke_reads']={a:[x.get('reads_total'),x.get('fixed_reads_total'),x.get('settled_bit_errors')] for c in allr for a,x in c['arms'].items() if a in NOISY}
    out['all_arms_present']=sorted(a for c in allr for a in c['arms'])==sorted(ALL_ARMS) and len(allr)==1 and len(det)==1 and len(eq)==len(NOISY)
    out['runtime_projection']=projection(res)
    with tempfile.TemporaryDirectory() as d:
        C=Path(d)/'copy';C.mkdir()
        for nm in ('RESULTS.json','SCIENTIFIC.json','SEAL.json'):shutil.copy(S/nm,C/nm)
        out['recount_rc']=recount([str(C)]);rc=load(C/'RECOUNT_065.json')
        out['recount']={k:rc.get(k) for k in ('cases','records','decided_by_arm','study_decided_by_arm','wrong','settled_bit_errors','mismatches','PASS')}
        out['reference_rc']=reference([str(C),'--block','smoke','--workers','6']);rf=load(C/'REFERENCE_065.json')
        out['reference_smoke']={k:rf.get(k) for k in ('records','decided','audited','complete','per_arm','mismatch_count','vacuous','PASS','elapsed_informational','scope')}|{'mutations':rf['mutation_test']['detected'],'of':rf['mutation_test']['mutations']}
        ac=Path(d)/'API_CHECKS_065.json';p=subprocess.run([sys.executable,str(ROOT/'scripts/api_checks_065.py'),'--output',str(ac)],
            cwd=ROOT,capture_output=True,text=True,timeout=2400,env={'PYTHONPATH':str(ROOT),'PATH':'/usr/bin:/bin'});out['api_checks_rc']=p.returncode
        if p.returncode and not ac.exists():raise SystemExit('api_checks_065 failed: '+p.stderr[-2000:])
        A=load(ac);out['api_checks']={'PASS':A.get('PASS'),'equiv':{k:v for k,v in A['equiv'].items() if k!='cases'},'threshold':A.get('threshold'),
                                      'montecarlo':A.get('montecarlo'),'ghost':{k:A['ghost'].get(k) for k in A['ghost'] if not k.endswith('_closure')}}
        D=Path(d)/'synthetic';(D/'main').mkdir(parents=True);fz=Path(d)/'FREEZE_STANDIN.json';fz.write_text('{}')
        cases=[dict(copy.deepcopy(c),block='main') for c in res['cases']];P=load(PLAN)
        with mock.patch.object(ST,'FREEZE',fz):
            ST._write(D/'main',P,'main',[f'synthetic:{i}' for i in range(sum(len(c['arms']) for c in cases))],cases,True,{'total_elapsed_informational':res.get('total_elapsed_informational')})
        rr=recount([str(D/'main')]);rf2=reference([str(D/'main'),'--workers','6'])
        n=(1,sum('S20' in c['arms'] for c in cases),sum('S10' in c['arms'] for c in cases),sum('S30b' in c['arms'] for c in cases))
        fi=AC.fidelity(D/'main');A2=dict(A,fidelity=fi);(D/'API_CHECKS_065.json').write_text(json.dumps(A2))
        g1=MG.build(D,n);g2=MG.build(D,n)
        out['synthetic']={'cases':n,'recount_rc':rr,'reference_rc':rf2,'gate_status':status(g1),'secondary':{k:v.get('observed') for k,v in g1['secondary'].items() if k!='GSTATS65'},
                          'fidelity_self_replay':{k:v for k,v in fi.items() if k!='per_case'},'fidelity_failures':{k:v for k,v in fi['per_case'].items() if not v['exact']},
                          **{nm:g1['gates'][nm].get('observed') for nm in ('GDET65','GFID65','GN65','GMAJ65','GEQ65','GREAD65','GS65_sound','GS_ref65')},
                          **{f:g1[f] for f in V.FLAGS},
                          'status_phrase':g1['status_phrase'],'sealed_input_verified':g1.get('sealed_input_verified'),'reproduces':dumps(g1)==dumps(g2),
                          'label_source':g1.get('label_source'),
                          'note':('synthetic: smoke cases as main with the smoke case counts (1 per arm); GHOST65 (bound to FREEZE_065, absent before the freeze), '
                                  'GTEST65 and G_PROC65 fail by design; GN65 / GN_low65 on 1 smoke seed at B 2M are recorded, not required')}
        Rd=Path(d)/'rel';(Rd/V.STUDY).mkdir(parents=True);(Rd/V.STUDY/'GATES_065.json').write_bytes(dumps(g1))
        Rel={k:'x' for k in V.RELEASE_KEYS};Rel.update(version=V.VERSION,gates_passed=sorted(k for k,v in g1['gates'].items() if v['pass'] is True),
             gates_failed=sorted(k for k,v in g1['gates'].items() if v['pass'] is False),gates_not_exercised=sorted(k for k,v in g1['gates'].items() if v['pass'] is None),
             secondary={k:v['pass'] for k,v in g1['secondary'].items()},status_phrase=g1['status_phrase'],**{f:g1[f] for f in V.FLAGS})
        (Rd/'RELEASE.json').write_text(json.dumps(Rel))
        try:V.release_ok(Rd);out['release_ok_synthetic']=True
        except Exception as e:out['release_ok_synthetic']=f'error: {e}'
    E=MF.entries();h=head();R={'preregistration_commit':E[0]['commit'],'source_freeze_commit':h,'seal_commit':h}
    try:out['verifier_chain']={'passed':True,'entries':[[e['event'],e['commit']] for e in E],'head':h,**V.chain(ROOT,R,E)}
    except Exception as e:out['verifier_chain']={'passed':False,'error':str(e),'entries':[[e['event'],e['commit']] for e in E]}
    vc=out['verifier_chain'];pj=out['runtime_projection'];sy=out['synthetic'];fs=sy['fidelity_self_replay'];gs=sy['gate_status']
    out['PASS']=(out['recount_rc']==0 and out['reference_rc']==0 and sy['recount_rc']==0 and sy['reference_rc']==0 and sy['reproduces']
                 and sy['sealed_input_verified'] and not any('INCOMPLETE_INPUT' in v.get('reason','') for k,v in gs.items() if k not in BY_DESIGN)
                 and all(gs[k]['pass'] is True for k in REQUIRED) and sy['label_source']=='recount' and fs.get('PASS') is True
                 and out['api_checks_rc']==0 and out['api_checks']['ghost'].get('PASS') is True and out['api_checks']['equiv']['PASS'] is True
                 and out['api_checks']['threshold']['PASS'] is True
                 and pj['cut_consistent'] and all(x[1] for x in det) and all(x[2] for x in eq) and not out['smoke_wall_guard_records'] and out['all_arms_present']
                 and out['release_ok_synthetic'] is True and vc['passed'] and vc.get('authorization_exceptions')==0)
    out['note']=('PASS here means the tooling ran end to end on a sealed block, gates reproduce, the self-replay is exact, every noisy smoke '
                 'record equals C20 read-free, the cut rule was applied as declared and the real commit-order check passes; GN65 / GN_low65 '
                 'outcomes on smoke are recorded, not required')
    write_new(outp,out);print(json.dumps({k:v for k,v in out.items() if k not in ('smoke_records','synthetic','recount')},default=str)[:6000])
    print(json.dumps(gs));return 0 if out['PASS'] else 1


if __name__=='__main__':sys.exit(main())
