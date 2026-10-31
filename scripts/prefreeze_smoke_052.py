"""Pre-freeze smoke-gates, runtime projection and cut order for study-052 (plan 052 runtime_estimate; pre-run deviation #177).
New file; built from scripts/prefreeze_smoke_051.py (frozen). Input: the sealed smoke block written by
experiments/brute_study_052.py --block smoke (outside results/study-052; seeds 12030001-12030006: two noise12 cases by API16N /
API16N_b, two noise12_bar cases by API16N_bar, two compat cases by API16N_c / API16E; one phase, 8 workers). Smoke is never gated
and never sets C, B, eps, eps_bar, delta or k. It
  1. lists stops, smoke determinism (canon16n of the two noise12 passes), wall_guard firings, majority errors and the compat rule
     of recount_052 (label; ID same machine from state 0; IDF future_match and same machine from s1);
  2. runs recount_052 and run_reference_052 (block smoke) on copies; runs scripts/api_checks_052.py (ghost only) into a temp file;
  3. builds a synthetic complete block (smoke cases relabelled 'main'), re-sealed with the runner's _write (stand-in freeze),
     recounted, referenced, self-replayed (GFID52 fidelity) and gated twice with the smoke case counts (dumps must be identical);
     exercises verify_release_0490.release_ok;
  4. runs verify_release_0490.chain on the repository (ledger since preregistration_052; HEAD stands in for freeze and seal);
  5. runtime projection (Inferred), plan 052 runtime_estimate (worst case, every job spends its whole B):
     r_min = min(slowest smoke conflict rate over records with case wall >= 1 s, the declared 29194/s);
     every job worst min(600 s, B / r_min + 10 s); total = LPT of all jobs on 8 workers. Declared cut order (never noise12, never
     compat): the first of N12BAR 12, 6 whose worst-case total <= 3600 s, else 6 with cut_exhausted true; the runner's N12BAR must
     equal it (cut_consistent).
Writes results/diag-052/PREFREEZE_SMOKE_GATES_052.json (refuses overwrite). Observed only: no gate decision, no tuning.
  PYTHONPATH=. python scripts/prefreeze_smoke_052.py /tmp/s52/smoke"""
import copy,json,shutil,subprocess,sys,tempfile
from pathlib import Path
from unittest import mock
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments import brute_study_052 as ST
from experiments.brute_common_052 import load,write_new,PLAN,caps_for,WORKERS
from experiments.brute_common import dumps
from scripts import make_gates_052 as MG
from scripts import make_freeze_052 as MF
from scripts import verify_release_0490 as V
from scripts import api_checks_052 as AC
from scripts.recount_052 import main as recount,compat_rule
from scripts.run_reference_052 import main as reference
OUT=ROOT/'results/diag-052/PREFREEZE_SMOKE_GATES_052.json';CAP=3600;GUARD=600.0;RATE_DECL=29194.0
STEPS=(12,6)
budget_for=lambda k:caps_for(k)[1]
BY_DESIGN=('GHOST52','GTI','GTEST','G_PROC','G_RT')


def status(g):return {k:{'pass':v['pass'],**({'reason':v['reason']} if 'reason' in v else {})} for k,v in g['gates'].items()}


def _lpt(walls,workers):
    bins=[0.0]*workers
    for x in sorted(walls,reverse=True):bins[bins.index(min(bins))]+=x
    return max(bins)


def _jobs(n):
    with mock.patch.object(ST,'N12BAR',n):return ST.jobs_for(load(PLAN),'main')


def projection(res):
    fv={};rate=[]
    for c in res['cases']:
        for g,w in c['group_walls_informational'].items():fv.setdefault(c['key'],[]).append(w)
        for a,x in c['arms'].items():
            w=x.get('case_wall_informational')
            if w and w>=1.0:rate.append(x['conflicts_spent']/w)
    fm={k:sum(x)/len(x) for k,x in fv.items()};smin=min(rate) if rate else None
    rmin=min(v for v in (smin,RATE_DECL) if v is not None)
    worst=lambda j:min(GUARD,budget_for(j[1])/rmin+10.0);mean=lambda j:fm.get(j[1],0.0)
    out={'label':'Inferred','mean_wall_by_key':{k:round(v,2) for k,v in sorted(fm.items())},'smoke_slowest_rate':None if smin is None else round(smin,1),
         'rate_declared':RATE_DECL,'r_min':round(rmin,1),'worst_per_job_s':{k:round(worst(('main',k,0,'')),1) for k in ('noise12','noise12_bar','compat')},
         'workers':WORKERS,'cap_s':CAP,'candidates':{}}
    for n in STEPS:
        J=_jobs(n)
        out['candidates'][f'N12BAR={n}']={'jobs':len(J),'mean_total_s':round(_lpt([mean(j) for j in J],WORKERS),1),
            'worst_serial_s':round(sum(worst(j) for j in J),1),'worst_case_total_s':round(_lpt([worst(j) for j in J],WORKERS),1)}
    ok=[n for n in STEPS if out['candidates'][f'N12BAR={n}']['worst_case_total_s']<=CAP];req=ok[0] if ok else STEPS[-1]
    out['required']={'N12BAR':req};out['cut_exhausted']=not ok;out['runner']={'N12BAR':ST.N12BAR}
    out['cut_consistent']=req==ST.N12BAR;out['cut_applied']=req!=STEPS[0]
    out['caveat']='two smoke seeds per key; the worst case assumes every job spends its whole B at r_min (or hits the 600 s case guard)'
    return out


def head():return subprocess.run(['git','-C',str(ROOT),'rev-parse','--short','HEAD'],capture_output=True,text=True).stdout.strip()


def main(argv=None):
    argv=sys.argv[1:] if argv is None else argv;S=Path(argv[0]);out={'label':'Observed','purpose':__doc__.split('\n')[0]}
    res=load(S/'RESULTS.json');st={};allr=res['cases']
    for c in allr:
        for a,x in c['arms'].items():st.setdefault(x['stop'],[]).append(f"{c['block']}/{c['key']}/{c['seed']}/{a}")
    out['stops_present']={k:len(v) for k,v in sorted(st.items())}
    out['smoke_records']=[(c['block'],c['key'],c['seed'],{a:[x['label'],x['stop'],x['conflicts_spent'],x.get('chunks_total'),round(x.get('case_wall_informational') or 0,2),
                           round(x.get('chunk_wall_max') or 0,3),x['wall_guard'],x.get('majority_errors'),x.get('reads_total')] for a,x in c['arms'].items()}) for c in allr]
    out['smoke_record_columns']=['block','key','seed','arm: label, stop, conflicts, chunks, case wall s, max chunk wall s, wall_guard, majority_errors, reads_total']
    out['smoke_wall_guard_records']=[f"{c['block']}/{c['key']}/{c['seed']}/{a}" for c in allr for a,x in c['arms'].items() if x.get('wall_guard')]
    det=[(c['key'],c['seed'],ST.canon16n(c['arms']['API16N'])==ST.canon16n(c['arms']['API16N_b'])) for c in allr if c['key']=='noise12']
    out['smoke_determinism']=det
    out['smoke_compat']=[(c['seed'],compat_rule(c['arms']['API16N_c'],c['arms']['API16E'],c['arms']['API16N_c']['label'],c['arms']['API16E']['label'])) for c in allr if c['key']=='compat']
    out['runtime_projection']=projection(res)
    with tempfile.TemporaryDirectory() as d:
        C=Path(d)/'copy';C.mkdir()
        for nm in ('RESULTS.json','SCIENTIFIC.json','SEAL.json'):shutil.copy(S/nm,C/nm)
        out['recount_rc']=recount([str(C)]);rc=load(C/'RECOUNT_052.json')
        out['recount']={k:rc.get(k) for k in ('labels','compat_equal','majority_errors','misfires','words_checked','words_unsound','truth_inconsistent','mismatching_cases','PASS')}
        out['reference_rc']=reference([str(C),'--block','smoke','--workers','8']);rf=load(C/'REFERENCE_052.json')
        out['reference_smoke']={k:rf.get(k) for k in ('records','decided','audited','complete','per_key','mismatch_count','vacuous','PASS','elapsed_informational','scope')}|{'mutations':rf['mutation_test']['detected'],'of':rf['mutation_test']['mutations']}
        ac=Path(d)/'API_CHECKS_052.json';p=subprocess.run([sys.executable,str(ROOT/'scripts/api_checks_052.py'),'--output',str(ac)],
            cwd=ROOT,capture_output=True,text=True,timeout=900,env={'PYTHONPATH':str(ROOT),'PATH':'/usr/bin:/bin'});out['api_checks_rc']=p.returncode
        if p.returncode and not ac.exists():raise SystemExit('api_checks_052 failed: '+p.stderr[-2000:])
        A=load(ac);out['api_checks']={'PASS':A.get('PASS'),'ghost':{k:A['ghost'].get(k) for k in A['ghost'] if k not in ('closures',)}}
        D=Path(d)/'synthetic';(D/'main').mkdir(parents=True);fz=Path(d)/'FREEZE_STANDIN.json';fz.write_text('{}')
        cases=[dict(copy.deepcopy(c),block='main') for c in res['cases']];P=load(PLAN)
        with mock.patch.object(ST,'FREEZE',fz):
            ST._write(D/'main',P,'main',[f'synthetic:{i}' for i in range(sum(len(c['arms']) for c in cases))],cases,True,{'total_elapsed_informational':res.get('total_elapsed_informational')})
        rr=recount([str(D/'main')]);rf2=reference([str(D/'main'),'--workers','8'])
        exp={k:sum(c['key']==k for c in cases) for k in ('noise12','noise12_bar','compat')};nrec=sum(len(c['arms']) for c in cases)
        fi=AC.fidelity(D/'main',nrec);A2=dict(A,fidelity=fi);(D/'API_CHECKS_052.json').write_text(json.dumps(A2))
        g1=MG.build(D,exp);g2=MG.build(D,exp)
        out['synthetic']={'cases':exp,'records':nrec,'recount_rc':rr,'reference_rc':rf2,'gate_status':status(g1),'secondary':sorted(g1['secondary']),
                          'fidelity_self_replay':{k:v for k,v in fi.items() if k!='per_case'},
                          **{nm:g1['gates'][nm].get('observed') for nm in ('GDET52','GFID52','GCOMPAT16N52','GN12_sound52','GQB26','GS_ref','G_sound')},
                          'GN12_pool':g1['secondary']['GN12_pool']['observed'],
                          'sealed_input_verified':g1.get('sealed_input_verified'),'reproduces':dumps(g1)==dumps(g2),'label_source':g1.get('label_source'),
                          'note':('synthetic: smoke cases as main with the smoke case counts; GHOST52 fails by design (no 052 freeze yet), GTI, GTEST, G_PROC and G_RT by design; '
                                  'GN12_sound52 non-vacuity (>= 8/24) cannot hold on 2 smoke cases')}
        Rd=Path(d)/'rel';(Rd/V.STUDY).mkdir(parents=True);(Rd/V.STUDY/'GATES_052.json').write_bytes(dumps(g1))
        Rel={k:'x' for k in V.RELEASE_KEYS};Rel.update(version=V.VERSION,gates_passed=sorted(k for k,v in g1['gates'].items() if v['pass'] is True),
             gates_failed=sorted(k for k,v in g1['gates'].items() if v['pass'] is False),gates_not_exercised=sorted(k for k,v in g1['gates'].items() if v['pass'] is None),
             secondary={k:v['pass'] for k,v in g1['secondary'].items()})
        (Rd/'RELEASE.json').write_text(json.dumps(Rel))
        try:V.release_ok(Rd);out['release_ok_synthetic']=True
        except Exception as e:out['release_ok_synthetic']=f'error: {e}'
    E=MF.entries();h=head();R={'preregistration_commit':E[0]['commit'],'source_freeze_commit':h,'seal_commit':h}
    try:out['verifier_chain']={'passed':True,'entries':[[e['event'],e['commit']] for e in E],'head':h,**V.chain(ROOT,R,E)}
    except Exception as e:out['verifier_chain']={'passed':False,'error':str(e),'entries':[[e['event'],e['commit']] for e in E]}
    vc=out['verifier_chain'];pj=out['runtime_projection'];sy=out['synthetic']
    out['PASS']=(out['recount_rc']==0 and out['reference_rc']==0 and sy['recount_rc']==0 and sy['reference_rc']==0 and sy['reproduces']
                 and sy['sealed_input_verified'] and not any('INCOMPLETE_INPUT' in v.get('reason','') for k,v in sy['gate_status'].items() if k not in BY_DESIGN)
                 and sy['gate_status']['G_recount']['pass'] is True and sy['label_source']=='recount'
                 and sy['fidelity_self_replay'].get('exact')==sy['fidelity_self_replay'].get('cases')==nrec
                 and out['api_checks_rc']==0 and pj['cut_consistent'] and all(x[2] for x in det) and all(x[1]['equal'] for x in out['smoke_compat'])
                 and out['release_ok_synthetic'] is True and vc['passed'] and vc.get('authorization_exceptions')==0)
    out['note']='PASS here means the tooling ran end to end on a sealed block, gates reproduce, the self-replay is exact, the cut order was applied as declared and the real commit-order check passes; gate outcomes on smoke are recorded, not required'
    write_new(OUT,out);print(json.dumps({k:v for k,v in out.items() if k not in ('smoke_records','synthetic')},default=str)[:6000])
    print(json.dumps(sy['gate_status']));return 0 if out['PASS'] else 1


if __name__=='__main__':sys.exit(main())
