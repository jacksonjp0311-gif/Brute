"""Pre-freeze smoke-gates, runtime projection and step-down for study-048 (plan 048 runtime_estimate; pre-run deviation #169).
New file; built from scripts/prefreeze_smoke_047.py (frozen). Input: the sealed smoke block written by
experiments/brute_study_048.py --block smoke (outside results/study-048; seeds 11590001-11590006 and one part-r replay of 11230004).
Smoke is never gated and never sets C or B. It
  1. lists the stops present, smoke determinism (canon16d API16D vs API16D_b) and wall_guard firings;
  2. runs recount_048 and run_reference_048 (block smoke) on copies; runs scripts/api_checks_048.py into a temp file;
  3. builds a synthetic complete block (smoke fresh cases relabelled 'main', the smoke replay kept as part r, expected counts
     patched in this process only), re-sealed with the runner's _write (stand-in freeze), recounted, referenced, self-replayed
     (GFID48 fidelity) and gated twice (dumps must be identical); exercises verify_release_0450.release_ok;
  4. runs verify_release_0450.chain on the repository (ledger since preregistration_048; HEAD stands in for freeze and seal);
  5. runtime projection (Inferred), plan 048 runtime_estimate: r_min(key) = min(slowest smoke conflict rate over that key's
     certify/16d records with arm wall >= 1 s, the 047 loaded rate: scale16 6716/s, scale20 3528/s); per job worst
     min(600 s, B / r_min + 10 s); controls (and any key with no rate) at their smoke mean; LPT on 8 workers.
     Step-down: N20 = the first of 8, 6, 4 whose worst-case LPT <= 3600 s, else 0 (part d dropped); the runner's N20 must equal
     it (step_down_consistent).
Writes results/diag-048/PREFREEZE_SMOKE_GATES_048.json (refuses overwrite). Observed only: no gate decision, no tuning.
  PYTHONPATH=. python scripts/prefreeze_smoke_048.py /tmp/s48/smoke"""
import copy,json,shutil,subprocess,sys,tempfile
from pathlib import Path
from unittest import mock
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments import brute_study_048 as ST
from experiments.brute_common_048 import load,write_new,PLAN,budget_for
from experiments.brute_common import dumps
from scripts import make_gates_048 as MG
from scripts import make_freeze_048 as MF
from scripts import verify_release_0450 as V
from scripts import api_checks_048 as AC
from scripts.recount_048 import main as recount
from scripts.run_reference_048 import main as reference
OUT=ROOT/'results/diag-048/PREFREEZE_SMOKE_GATES_048.json';CAP=3600;GUARD=600.0;RATE_047={'scale16':6716.0,'scale20':3528.0}
STEPS=(8,6,4)


def status(g):return {k:{'pass':v['pass'],**({'reason':v['reason']} if 'reason' in v else {})} for k,v in g['gates'].items()}


def _lpt(walls,workers):
    bins=[0.0]*workers
    for x in sorted(walls,reverse=True):bins[bins.index(min(bins))]+=x
    return max(bins)


def _jobs(n20):
    with mock.patch.object(ST,'N20',n20):return ST.jobs_for(load(PLAN),'main')


def projection(res,workers=8):
    fv={};rate={}
    for c in res['cases']:
        for g,w in c['group_walls_informational'].items():fv.setdefault(c['key'],[]).append(w)
    for r in res['replays']:fv.setdefault('r/'+r['key'],[]).append(r['job_wall_informational'])
    for c in res['replays']+res['cases']:
        for a,x in c['arms'].items():
            w=x.get('arm_wall_informational')
            if w and w>=1.0:rate.setdefault(c['key'],[]).append(x['conflicts_spent']/w)
    fm={k:sum(x)/len(x) for k,x in fv.items()};smin={k:min(v) for k,v in rate.items()}
    rmin={k:min([v for v in (smin.get(k),RATE_047.get(k)) if v is not None]) for k in set(smin)|set(RATE_047)}
    def mean(j):return fm.get(('r/' if j[0]=='r' else '')+j[1],fm.get(j[1],0.0))
    def worst(j):return min(GUARD,budget_for(j[1])/rmin[j[1]]+10.0) if j[1] in rmin else mean(j)
    out={'label':'Inferred','mean_wall_by_key':{k:round(v,2) for k,v in sorted(fm.items())},'smoke_slowest_rate_by_key':{k:round(v,1) for k,v in sorted(smin.items())},
         'rate_047_loaded':RATE_047,'r_min_by_key':{k:round(v,1) for k,v in sorted(rmin.items())},'workers':workers,'cap_s':CAP,'candidates':{}}
    for n in STEPS+(0,):
        J=_jobs(n);w=[mean(j) for j in J];x=[worst(j) for j in J]
        out['candidates'][str(n)]={'jobs':len(J),'mean_lpt_s':round(_lpt(w,workers),1),'worst_serial_s':round(sum(x),1),'worst_case_lpt_s':round(_lpt(x,workers),1)}
    req=next((n for n in STEPS if out['candidates'][str(n)]['worst_case_lpt_s']<=CAP),0)
    out['n20_required']=req;out['runner_N20']=ST.N20;out['step_down_consistent']=req==ST.N20;out['step_down_applied']=req!=8
    out['caveat']='two scale16, two scale20, two control smoke seeds and one replay; the worst case assumes every long job exhausts its budget at r_min'
    return out


def head():return subprocess.run(['git','-C',str(ROOT),'rev-parse','--short','HEAD'],capture_output=True,text=True).stdout.strip()


def main(argv=None):
    argv=sys.argv[1:] if argv is None else argv;S=Path(argv[0]);out={'label':'Observed','purpose':__doc__.split('\n')[0]}
    res=load(S/'RESULTS.json');st={}
    for c in res['replays']+res['cases']:
        for a,x in c['arms'].items():st.setdefault(x['stop'],[]).append(f"{c['block']}/{c['key']}/{c['seed']}/{a}")
    out['stops_present']={k:len(v) for k,v in sorted(st.items())}
    out['smoke_records']=[(c['block'],c['key'],c['seed'],{a:[x['label'],x['stop'],x['conflicts_spent'],round(x['arm_wall_informational'],2),x['wall_guard']] for a,x in c['arms'].items()},
                           (c.get('replay') or {}).get('class')) for c in res['replays']+res['cases']]
    out['smoke_wall_guard_records']=[f"{c['block']}/{c['key']}/{c['seed']}/{a}" for c in res['replays']+res['cases'] for a,x in c['arms'].items() if x.get('wall_guard')]
    out['smoke_determinism']=[(c['key'],c['seed'],ST.canon16d(c['arms']['API16D'])==ST.canon16d(c['arms']['API16D_b'])) for c in res['cases']]
    out['runtime_projection']=projection(res)
    with tempfile.TemporaryDirectory() as d:
        C=Path(d)/'copy';C.mkdir()
        for nm in ('RESULTS.json','SCIENTIFIC.json','SEAL.json'):shutil.copy(S/nm,C/nm)
        out['recount_rc']=recount([str(C)]);rc=load(C/'RECOUNT_048.json')
        out['recount']={k:rc.get(k) for k in ('replays','cases','labels_all','replay_summary','words_checked','mismatching_cases','PASS')}
        out['reference_rc']=reference([str(C),'--block','smoke','--workers','8']);rf=load(C/'REFERENCE_048.json')
        out['reference_smoke']={k:rf.get(k) for k in ('records','decided','audited','complete','per_key','mismatch_count','vacuous','PASS','elapsed_informational','scope')}|{'mutations':rf['mutation_test']['detected'],'of':rf['mutation_test']['mutations']}
        ac=Path(d)/'API_CHECKS_048.json';p=subprocess.run([sys.executable,str(ROOT/'scripts/api_checks_048.py'),'--output',str(ac)],
            cwd=ROOT,capture_output=True,text=True,timeout=900,env={'PYTHONPATH':str(ROOT),'PATH':'/usr/bin:/bin'});out['api_checks_rc']=p.returncode
        if p.returncode and not ac.exists():raise SystemExit('api_checks_048 failed: '+p.stderr[-2000:])
        A=load(ac)
        out['api_checks']={'PASS':A['PASS'],'compat':A['compat']['PASS'],'ghost':{k:A['ghost'][k] for k in ('closure_unchanged','certify16d_unchanged','socket_attempts','new_flagged','PASS48')}}
        D=Path(d)/'synthetic';(D/'main').mkdir(parents=True);fz=Path(d)/'FREEZE_STANDIN.json';fz.write_text('{}')
        cases=[dict(copy.deepcopy(c),block='main') for c in res['cases']];reps=[copy.deepcopy(r) for r in res['replays']];P=load(PLAN)
        with mock.patch.object(ST,'FREEZE',fz):
            ST._write(D/'main',P,'main',[f'synthetic:{i}' for i in range(2*len(cases)+len(reps))],(reps,cases),True,{'total_elapsed_informational':res.get('total_elapsed_informational')})
        rr=recount([str(D/'main')]);rf2=reference([str(D/'main'),'--workers','8'])
        exp={k:sum(c['key']==k for c in cases) for k in ('scale16','control','scale20')}
        fi=AC.fidelity(D/'main',len(cases));A2=dict(A,fidelity=fi);(D/'API_CHECKS_048.json').write_text(json.dumps(A2))
        g1=MG.build(D,exp,len(reps));g2=MG.build(D,exp,len(reps))
        out['synthetic']={'cases':exp,'replays':len(reps),'recount_rc':rr,'reference_rc':rf2,'gate_status':status(g1),'secondary':sorted(g1['secondary']),
                          'fidelity_self_replay':{k:v for k,v in fi.items() if k!='per_case'},
                          **{nm:g1['gates'][nm]['observed'] for nm in ('GDET48','GWALL_r','GFID48','GS20_sound','G10','GQB23','GS_ref')},
                          'sealed_input_verified':g1['sealed_input_verified'],'reproduces':dumps(g1)==dumps(g2),'label_source':g1['label_source'],
                          'note':'synthetic: smoke fresh cases as main with expected counts patched; GDET48 fails here by its 18 + N20 count, GAPI16D_fresh48 by its 12-case count, GHOST48 by design (no 048 freeze yet), GTI and G_PROC by design'}
        Rd=Path(d)/'rel';(Rd/V.STUDY).mkdir(parents=True);(Rd/V.STUDY/'GATES_048.json').write_bytes(dumps(g1))
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
                 and sy['sealed_input_verified'] and not any('INCOMPLETE_INPUT (main' in v.get('reason','') for v in sy['gate_status'].values())
                 and sy['gate_status']['G_recount']['pass'] is True and sy['label_source']=='recount'
                 and sy['fidelity_self_replay']['exact']==sy['fidelity_self_replay']['cases']>0
                 and out['api_checks_rc']==0 and out['api_checks']['PASS'] is True and pj['step_down_consistent']
                 and out['release_ok_synthetic'] is True and vc['passed'] and vc.get('authorization_exceptions')==0)
    out['note']='PASS here means the tooling ran end to end on a sealed block, gates reproduce, the self-replay is exact, the step-down rule was applied as declared and the real commit-order check passes; gate outcomes on smoke are recorded, not required'
    write_new(OUT,out);print(json.dumps({k:v for k,v in out.items() if k not in ('smoke_records','synthetic')},default=str)[:5000])
    print(json.dumps(sy['gate_status']));return 0 if out['PASS'] else 1


if __name__=='__main__':sys.exit(main())
