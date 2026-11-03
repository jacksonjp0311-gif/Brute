"""Pre-freeze smoke-gates and runtime report for study-066 (plan 066 runtime_projection; pre-run deviation #206). New file; built
from scripts/prefreeze_smoke_065.py (frozen). Input: the sealed smoke block written by experiments/brute_study_066.py --block smoke
(outside results/study-066; smoke seed 12660301 on every arm C20, S30, S30b (scale20) and C24, S24 (scale24), 5 jobs, one process
per job, 7 at a time, runner kill 600 s, B 2000000 for smoke only; 12660302 is used by the api_checks equivalence checks, 12660303 by
the no-network run, 12660304-06 unused). Smoke is never gated and never sets C, B, K, eps_bar, delta or the case counts. It
  1. lists stops, labels, read counts, smoke determinism (canon66 of S30 vs S30b), the read-free equality of every noisy arm with
     its control (canon_inner), wall_guard firings and per-record fields;
  2. runs recount_066 and run_reference_066 (block smoke) on copies and scripts/api_checks_066.py (no --study) into a temp file;
  3. builds a synthetic complete block (smoke cases relabelled 'main'), re-sealed with the runner's _write (stand-in freeze),
     recounted, referenced, self-replayed (GFID66 fidelity, must be exact) and gated twice with the smoke case counts (dumps must be
     identical); then a second synthetic block in which the S24 record is replaced by the runner's kill_record (KILL path: recount,
     reference and gates must accept it as a complete undecided outcome); exercises verify_release_0630.release_ok;
  4. runs verify_release_0630.chain on the repository (ledger since preregistration_066; HEAD stands in for freeze and seal);
  5. runtime (plan 066 runtime_projection): no cut rule; smoke walls are reported, and a 20-state smoke record above 300 s is
     reported, not acted on.
Writes results/diag-066/PREFREEZE_SMOKE_GATES_066.json (refuses overwrite) or --output. Observed only: no gate decision, no tuning.
  PYTHONPATH=. python scripts/prefreeze_smoke_066.py /tmp/s66/smoke [--output PATH]"""
import copy,json,shutil,subprocess,sys,tempfile
from pathlib import Path
from unittest import mock
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments import brute_study_066 as ST
from experiments.brute_common_066 import load,write_new,PLAN,WORKERS,ALL_ARMS,NOISY,MAIN_CAP_S,CONTROL
from experiments.brute_common import dumps
from scripts import make_gates_066 as MG
from scripts import make_freeze_066 as MF
from scripts import verify_release_0630 as V
from scripts import api_checks_066 as AC
from scripts.recount_066 import main as recount
from scripts.run_reference_066 import main as reference
OUT=ROOT/'results/diag-066/PREFREEZE_SMOKE_GATES_066.json'
BY_DESIGN=('GHOST66','GTEST66','G_PROC66','GN66','GN24_66','GEQ66')
REQUIRED=('G_recount66','GDET66','GFID66','GS66_sound','GS_ref66','GMAJ66','GLIVE66','GREAD66')
REQUIRED_KILL=('G_recount66','GS66_sound','GLIVE66','GMAJ66','GS_ref66')
FIELDS=('label','stop','n_min','used','n_rounds','conflicts_spent','wall_guard','observations','reads_total','fixed_reads_total','settled_bit_errors')


def status(g):return {k:{'pass':v['pass'],**({'reason':v['reason']} if 'reason' in v else {})} for k,v in g['gates'].items()}


def runtime(res):
    sm={a:[round(x['case_wall_informational'],1) for c in res['cases'] for g,x in c['arms'].items() if g==a] for a in ALL_ARMS}
    slow=[[a,w] for a in ('C20','S30','S30b') for w in sm[a] if w>300]
    return {'label':'Observed','rule':'plan 066 runtime_projection: no cut rule; a 20-state smoke record above 300 s is reported, not acted on',
            'smoke_walls_B2M_s':sm,'smoke_total_elapsed_s':res.get('total_elapsed_informational'),'twenty_state_above_300s':slow,
            'jobs_main':len(ST.jobs_for(load(PLAN),'main')),'workers':WORKERS,'job_kill_s':ST.JOB_KILL_S,'main_cap_s':MAIN_CAP_S}


def _synth(d,name,cases,res,P):
    D=Path(d)/name;(D/'main').mkdir(parents=True);fz=Path(d)/'FREEZE_STANDIN.json';fz.write_text('{}')
    with mock.patch.object(ST,'FREEZE',fz):
        ST._write(D/'main',P,'main',[f'synthetic:{i}' for i in range(sum(len(c['arms']) for c in cases))],cases,True,{'total_elapsed_informational':res.get('total_elapsed_informational')})
    return D


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
    det=[(c['seed'],ST.canon66(c['arms']['S30'])==ST.canon66(c['arms']['S30b'])) for c in allr if 'S30b' in c['arms']];out['smoke_determinism']=det
    eq=[(c['key'],c['seed'],a,ST.canon_inner(c['arms'][a])==ST.canon_inner(c['arms'][CONTROL[a]])) for c in allr for a in NOISY if a in c['arms'] and CONTROL[a] in c['arms']]
    out['smoke_inner_equal_control']=eq
    out['smoke_reads']={a:[x.get('reads_total'),x.get('fixed_reads_total'),x.get('settled_bit_errors')] for c in allr for a,x in c['arms'].items() if a in NOISY}
    out['all_arms_present']=sorted(a for c in allr for a in c['arms'])==sorted(ALL_ARMS) and len(allr)==2 and len(det)==1 and len(eq)==len(NOISY)
    out['runtime']=runtime(res)
    with tempfile.TemporaryDirectory() as d:
        C=Path(d)/'copy';C.mkdir()
        for nm in ('RESULTS.json','SCIENTIFIC.json','SEAL.json'):shutil.copy(S/nm,C/nm)
        out['recount_rc']=recount([str(C)]);rc=load(C/'RECOUNT_066.json')
        out['recount']={k:rc.get(k) for k in ('cases','records','decided_by_arm','study_decided_by_arm','wrong','killed','settled_bit_errors','mismatches','PASS')}
        out['reference_rc']=reference([str(C),'--block','smoke','--workers','6']);rf=load(C/'REFERENCE_066.json')
        out['reference_smoke']={k:rf.get(k) for k in ('records','decided','audited','complete','per_arm','mismatch_count','vacuous','PASS','elapsed_informational','scope')}|{'mutations':rf['mutation_test']['detected'],'of':rf['mutation_test']['mutations']}
        ac=Path(d)/'API_CHECKS_066.json';p=subprocess.run([sys.executable,str(ROOT/'scripts/api_checks_066.py'),'--output',str(ac)],
            cwd=ROOT,capture_output=True,text=True,timeout=2400,env={'PYTHONPATH':str(ROOT),'PATH':'/usr/bin:/bin'});out['api_checks_rc']=p.returncode
        if p.returncode and not ac.exists():raise SystemExit('api_checks_066 failed: '+p.stderr[-2000:])
        A=load(ac);out['api_checks']={'PASS':A.get('PASS'),'equiv':{k:v for k,v in A['equiv'].items() if k!='cases'},'equiv20':A.get('equiv20'),'threshold':A.get('threshold'),
                                      'montecarlo':A.get('montecarlo'),'ghost':{k:A['ghost'].get(k) for k in A['ghost'] if not k.endswith('_closure')}}
        cases=[dict(copy.deepcopy(c),block='main') for c in res['cases']];P=load(PLAN)
        D=_synth(d,'synthetic',cases,res,P)
        rr=recount([str(D/'main')]);rf2=reference([str(D/'main'),'--workers','6'])
        n=(sum(c['key']=='scale20' for c in cases),sum(c['key']=='scale24' for c in cases),sum('S30b' in c['arms'] for c in cases))
        fi=AC.fidelity(D/'main');A2=dict(A,fidelity=fi);(D/'API_CHECKS_066.json').write_text(json.dumps(A2))
        g1=MG.build(D,n);g2=MG.build(D,n)
        out['synthetic']={'cases':n,'recount_rc':rr,'reference_rc':rf2,'gate_status':status(g1),'secondary':{k:v.get('observed') for k,v in g1['secondary'].items() if k!='GSTATS66'},
                          'fidelity_self_replay':{k:v for k,v in fi.items() if k!='per_case'},'fidelity_failures':{k:v for k,v in fi['per_case'].items() if not v['exact']},
                          **{nm:g1['gates'][nm].get('observed') for nm in ('GDET66','GFID66','GN66','GN24_66','GMAJ66','GEQ66','GREAD66','GS66_sound','GS_ref66','GLIVE66')},
                          **{f:g1[f] for f in V.FLAGS},
                          'status_phrase':g1['status_phrase'],'sealed_input_verified':g1.get('sealed_input_verified'),'reproduces':dumps(g1)==dumps(g2),
                          'label_source':g1.get('label_source'),
                          'note':('synthetic: smoke cases as main with the smoke case counts (1 seed per family); GHOST66 (bound to FREEZE_066, absent before the freeze), '
                                  'GTEST66 and G_PROC66 fail by design; GEQ66 (needs 4 + 2 pairs), GN66 and GN24_66 on 1 smoke seed at B 2M are recorded, not required')}
        kc=copy.deepcopy(cases);c24=next(c for c in kc if 'S24' in c['arms'])
        kr=ST.kill_record(('main',c24['key'],c24['seed'],'S24'),600.0);c24['arms']['S24']=kr['arms']['S24']
        c24['killed_arms']=['S24'];c24['killed']=True
        DK=_synth(d,'synthetic_kill',kc,res,P)
        rk=recount([str(DK/'main')]);rfk=reference([str(DK/'main'),'--workers','6'])
        fik=AC.fidelity(DK/'main');(DK/'API_CHECKS_066.json').write_text(json.dumps(dict(A,fidelity=fik)))
        gk=MG.build(DK,n)
        out['synthetic_kill']={'recount_rc':rk,'reference_rc':rfk,'gate_status':status(gk),'KILLS66':gk['secondary']['KILLS66']['observed'],
                               'recount_killed':load(DK/'main'/'RECOUNT_066.json').get('killed'),'fidelity_PASS':fik.get('PASS'),
                               'GLIVE66':gk['gates']['GLIVE66']['observed'],'GN24_66':gk['gates']['GN24_66']['observed']}
        Rd=Path(d)/'rel';(Rd/V.STUDY).mkdir(parents=True);(Rd/V.STUDY/'GATES_066.json').write_bytes(dumps(g1))
        Rel={k:'x' for k in V.RELEASE_KEYS};Rel.update(version=V.VERSION,gates_passed=sorted(k for k,v in g1['gates'].items() if v['pass'] is True),
             gates_failed=sorted(k for k,v in g1['gates'].items() if v['pass'] is False),gates_not_exercised=sorted(k for k,v in g1['gates'].items() if v['pass'] is None),
             secondary={k:v['pass'] for k,v in g1['secondary'].items()},status_phrase=g1['status_phrase'],**{f:g1[f] for f in V.FLAGS})
        (Rd/'RELEASE.json').write_text(json.dumps(Rel))
        try:V.release_ok(Rd);out['release_ok_synthetic']=True
        except Exception as e:out['release_ok_synthetic']=f'error: {e}'
    E=MF.entries();h=head();R={'preregistration_commit':E[0]['commit'],'source_freeze_commit':h,'seal_commit':h}
    try:out['verifier_chain']={'passed':True,'entries':[[e['event'],e['commit']] for e in E],'head':h,**V.chain(ROOT,R,E)}
    except Exception as e:out['verifier_chain']={'passed':False,'error':str(e),'entries':[[e['event'],e['commit']] for e in E]}
    vc=out['verifier_chain'];sy=out['synthetic'];fs=sy['fidelity_self_replay'];gs=sy['gate_status'];sk=out['synthetic_kill'];gk=sk['gate_status']
    out['PASS']=(out['recount_rc']==0 and out['reference_rc']==0 and sy['recount_rc']==0 and sy['reference_rc']==0 and sy['reproduces']
                 and sy['sealed_input_verified'] and not any('INCOMPLETE_INPUT' in v.get('reason','') for k,v in gs.items() if k not in BY_DESIGN)
                 and all(gs[k]['pass'] is True for k in REQUIRED) and sy['label_source']=='recount' and fs.get('PASS') is True
                 and out['api_checks_rc']==0 and out['api_checks']['ghost'].get('PASS') is True and out['api_checks']['equiv']['PASS'] is True
                 and out['api_checks']['threshold']['PASS'] is True and (out['api_checks']['equiv20'] or {}).get('PASS') is True
                 and sk['recount_rc']==0 and sk['reference_rc']==0 and all(gk[k]['pass'] is True for k in REQUIRED_KILL) and sk['recount_killed']==1
                 and all(x[1] for x in det) and all(x[3] for x in eq) and not out['smoke_wall_guard_records'] and out['all_arms_present']
                 and out['release_ok_synthetic'] is True and vc['passed'] and vc.get('authorization_exceptions')==0)
    out['note']=('PASS here means the tooling ran end to end on a sealed block, gates reproduce, the self-replay is exact, every noisy smoke '
                 'record equals its control read-free, the KILL path is accepted end to end and the real commit-order check passes; GEQ66 / GN66 / GN24_66 '
                 'outcomes on smoke are recorded, not required')
    write_new(outp,out);print(json.dumps({k:v for k,v in out.items() if k not in ('smoke_records','synthetic','synthetic_kill','recount')},default=str)[:6000])
    print(json.dumps(gs));print(json.dumps(gk));return 0 if out['PASS'] else 1


if __name__=='__main__':sys.exit(main())
