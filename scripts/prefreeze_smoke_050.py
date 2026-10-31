"""Pre-freeze smoke-gates, runtime projection and cut order for study-050 (plan 050 runtime_estimate; pre-run deviation #173).
New file; built from scripts/prefreeze_smoke_049.py (frozen). Input: the sealed smoke block written by
experiments/brute_study_050.py --block smoke (outside results/study-050; seeds 11810001-11810006: two scale20, two control and
two noise12 cases by both arms, plus part c (API16N_c) on the two smoke controls). Smoke is never gated and never sets C, B, eps,
eps_bar, delta or k. It
  1. lists stops, smoke determinism (canon16e / canon16n of the two arms), wall_guard firings, majority errors and part c compat;
  2. runs recount_050 and run_reference_050 (block smoke) on copies; runs scripts/api_checks_050.py (ghost only) into a temp file;
  3. builds a synthetic complete block (smoke cases relabelled 'main', part c kept), re-sealed with the runner's _write (stand-in
     freeze), recounted, referenced, self-replayed (GFID50 fidelity) and gated twice with the smoke case counts (dumps must be
     identical); exercises verify_release_0470.release_ok;
  4. runs verify_release_0470.chain on the repository (ledger since preregistration_050; HEAD stands in for freeze and seal);
  5. runtime projection (Inferred), plan 050 runtime_estimate: r_min(scale20) = min(slowest smoke scale20 conflict rate over records
     with case wall >= 1 s, the declared 3528/s); every scale20 job worst min(600 s, B20 / r_min + 10 s); control, noise12 and part c
     jobs at max(10 x their smoke mean, 60 s) (12 states at B12: smoke cases decide in seconds; the factor is a declared margin, not
     a fit); LPT on 8 workers. Declared cut order: the first of (N12B 12, N20B 12), (6, 12), (6, 6) whose worst-case LPT <= 3600 s,
     else (6, 6) with cut_exhausted; the runner's (N12B, N20B) must equal it (cut_consistent).
Writes results/diag-050/PREFREEZE_SMOKE_GATES_050.json (refuses overwrite). Observed only: no gate decision, no tuning.
  PYTHONPATH=. python scripts/prefreeze_smoke_050.py /tmp/s50/smoke"""
import copy,json,shutil,subprocess,sys,tempfile
from pathlib import Path
from unittest import mock
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments import brute_study_050 as ST
from experiments.brute_common_050 import load,write_new,PLAN,budget_for,N_ARMS
from experiments.brute_common import dumps
from scripts import make_gates_050 as MG
from scripts import make_freeze_050 as MF
from scripts import verify_release_0470 as V
from scripts import api_checks_050 as AC
from scripts.recount_050 import main as recount
from scripts.run_reference_050 import main as reference
OUT=ROOT/'results/diag-050/PREFREEZE_SMOKE_GATES_050.json';CAP=3600;GUARD=600.0;RATE_DECL=3528.0;MARGIN=10.0;FLOOR=60.0
STEPS=((12,12),(6,12),(6,6))


def status(g):return {k:{'pass':v['pass'],**({'reason':v['reason']} if 'reason' in v else {})} for k,v in g['gates'].items()}


def _lpt(walls,workers):
    bins=[0.0]*workers
    for x in sorted(walls,reverse=True):bins[bins.index(min(bins))]+=x
    return max(bins)


def _jobs(n12b,n20b):
    with mock.patch.object(ST,'N12B',n12b),mock.patch.object(ST,'N20B',n20b):return ST.jobs_for(load(PLAN),'main')


def projection(res,workers=8):
    fv={};rate=[]
    for c in res['cases']:
        for g,w in c['group_walls_informational'].items():fv.setdefault(('c/' if c['block']=='c' else '')+c['key'],[]).append(w)
        if c['key']=='scale20':
            for a,x in c['arms'].items():
                w=x.get('case_wall_informational')
                if w and w>=1.0:rate.append(x['conflicts_spent']/w)
    fm={k:sum(x)/len(x) for k,x in fv.items()};smin=min(rate) if rate else None;rmin=min(v for v in (smin,RATE_DECL) if v is not None)
    def mean(j):return fm.get(('c/' if j[0]=='c' else '')+j[1],0.0)
    def worst(j):return min(GUARD,budget_for(j[1])/rmin+10.0) if j[1]=='scale20' else max(MARGIN*mean(j),FLOOR)
    out={'label':'Inferred','mean_wall_by_key':{k:round(v,2) for k,v in sorted(fm.items())},'smoke_slowest_scale20_rate':None if smin is None else round(smin,1),
         'rate_declared_scale20':RATE_DECL,'r_min_scale20':round(rmin,1),'small_job_rule':f'max({MARGIN} x smoke mean, {FLOOR} s)','workers':workers,'cap_s':CAP,'candidates':{}}
    for n12b,n20b in STEPS:
        J=_jobs(n12b,n20b);w=[mean(j) for j in J];x=[worst(j) for j in J]
        out['candidates'][f'N12B={n12b},N20B={n20b}']={'jobs':len(J),'mean_lpt_s':round(_lpt(w,workers),1),'worst_serial_s':round(sum(x),1),'worst_case_lpt_s':round(_lpt(x,workers),1)}
    ok=[s for s in STEPS if out['candidates'][f'N12B={s[0]},N20B={s[1]}']['worst_case_lpt_s']<=CAP];req=ok[0] if ok else STEPS[-1]
    out['required']={'N12B':req[0],'N20B':req[1]};out['cut_exhausted']=not ok;out['runner']={'N12B':ST.N12B,'N20B':ST.N20B}
    out['cut_consistent']=req==(ST.N12B,ST.N20B);out['cut_applied']=req!=STEPS[0]
    out['caveat']='two smoke seeds per key; the worst case assumes every scale20 job exhausts B20 at r_min (or hits the 600 s case guard); 12-state jobs use a declared margin over smoke'
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
    det=[]
    for c in allr:
        if c['block']=='c':continue
        A=ST.ARMS_OF[c['key']];f=ST.canon16n if A[0] in N_ARMS else ST.canon16e;det.append((c['key'],c['seed'],f(c['arms'][A[0]])==f(c['arms'][A[1]])))
    out['smoke_determinism']=det
    K={c['seed']:c for c in allr if c['block']=='smoke' and c['key']=='control'}
    out['smoke_part_c_compat']=[(c['seed'],ST.canon16e(c['arms']['API16N_c'])==ST.canon16e(K[c['seed']]['arms']['API16E'])) for c in allr if c['block']=='c']
    out['runtime_projection']=projection(res)
    with tempfile.TemporaryDirectory() as d:
        C=Path(d)/'copy';C.mkdir()
        for nm in ('RESULTS.json','SCIENTIFIC.json','SEAL.json'):shutil.copy(S/nm,C/nm)
        out['recount_rc']=recount([str(C)]);rc=load(C/'RECOUNT_050.json')
        out['recount']={k:rc.get(k) for k in ('labels','labels_c','compat_equal','majority_errors','misfires','words_checked','words_unsound','truth_inconsistent','mismatching_cases','PASS')}
        out['reference_rc']=reference([str(C),'--block','smoke','--workers','8']);rf=load(C/'REFERENCE_050.json')
        out['reference_smoke']={k:rf.get(k) for k in ('records','decided','audited','complete','per_key','mismatch_count','vacuous','PASS','elapsed_informational','scope')}|{'mutations':rf['mutation_test']['detected'],'of':rf['mutation_test']['mutations']}
        ac=Path(d)/'API_CHECKS_050.json';p=subprocess.run([sys.executable,str(ROOT/'scripts/api_checks_050.py'),'--output',str(ac)],
            cwd=ROOT,capture_output=True,text=True,timeout=900,env={'PYTHONPATH':str(ROOT),'PATH':'/usr/bin:/bin'});out['api_checks_rc']=p.returncode
        if p.returncode and not ac.exists():raise SystemExit('api_checks_050 failed: '+p.stderr[-2000:])
        A=load(ac);out['api_checks']={'PASS':A.get('PASS'),'ghost':{k:A['ghost'].get(k) for k in A['ghost'] if k not in ('closures',)}}
        D=Path(d)/'synthetic';(D/'main').mkdir(parents=True);fz=Path(d)/'FREEZE_STANDIN.json';fz.write_text('{}')
        cases=[dict(copy.deepcopy(c),block='c' if c['block']=='c' else 'main') for c in res['cases']];P=load(PLAN)
        with mock.patch.object(ST,'FREEZE',fz):
            ST._write(D/'main',P,'main',[f'synthetic:{i}' for i in range(sum(len(c['arms']) for c in cases))],cases,True,{'total_elapsed_informational':res.get('total_elapsed_informational')})
        rr=recount([str(D/'main')]);rf2=reference([str(D/'main'),'--workers','8'])
        mc=[c for c in cases if c['block']=='main'];exp={k:sum(c['key']==k for c in mc) for k in ('scale20','noise12','control')};exp['compat']=sum(c['block']=='c' for c in cases)
        fi=AC.fidelity(D/'main',len(mc));A2=dict(A,fidelity=fi);(D/'API_CHECKS_050.json').write_text(json.dumps(A2))
        g1=MG.build(D,exp);g2=MG.build(D,exp)
        out['synthetic']={'cases':exp,'recount_rc':rr,'reference_rc':rf2,'gate_status':status(g1),'secondary':sorted(g1['secondary']),
                          'fidelity_self_replay':{k:v for k,v in fi.items() if k!='per_case'},
                          **{nm:g1['gates'][nm].get('observed') for nm in ('GDET50','GFID50','GCOMPAT16N','GS20_sound50','GN12_sound','G10','GQB25','GS_ref')},
                          'sealed_input_verified':g1.get('sealed_input_verified'),'reproduces':dumps(g1)==dumps(g2),'label_source':g1.get('label_source'),
                          'note':'synthetic: smoke cases as main with the smoke case counts; GHOST50 fails by design (no 050 freeze yet and no study API_CHECKS), GTI, GTEST, G_PROC and G_RT by design'}
        Rd=Path(d)/'rel';(Rd/V.STUDY).mkdir(parents=True);(Rd/V.STUDY/'GATES_050.json').write_bytes(dumps(g1))
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
                 and sy['sealed_input_verified'] and not any('INCOMPLETE_INPUT' in v.get('reason','') for k,v in sy['gate_status'].items() if k not in ('GHOST50','GTI','GTEST','G_PROC','G_RT'))
                 and sy['gate_status']['G_recount']['pass'] is True and sy['label_source']=='recount'
                 and sy['fidelity_self_replay'].get('exact')==sy['fidelity_self_replay'].get('cases')>0
                 and out['api_checks_rc']==0 and pj['cut_consistent'] and all(x[2] for x in det) and all(x[1] for x in out['smoke_part_c_compat'])
                 and out['release_ok_synthetic'] is True and vc['passed'] and vc.get('authorization_exceptions')==0)
    out['note']='PASS here means the tooling ran end to end on a sealed block, gates reproduce, the self-replay is exact, the cut order was applied as declared and the real commit-order check passes; gate outcomes on smoke are recorded, not required'
    write_new(OUT,out);print(json.dumps({k:v for k,v in out.items() if k not in ('smoke_records','synthetic')},default=str)[:6000])
    print(json.dumps(sy['gate_status']));return 0 if out['PASS'] else 1


if __name__=='__main__':sys.exit(main())
