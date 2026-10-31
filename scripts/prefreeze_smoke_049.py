"""Pre-freeze smoke-gates, runtime projection and cut order for study-049 (plan 049 runtime_estimate; pre-run deviation #171).
New file; built from scripts/prefreeze_smoke_048.py (frozen). Input: the sealed smoke block written by
experiments/brute_study_049.py --block smoke (outside results/study-049; seeds 11690001-11690006 by API16E and API16E_b, plus part r
and part c on sealed 048 scale16 11510002 and control 11530001). Smoke is never gated and never sets C or B. It
  1. lists the stops present, smoke determinism (canon16e API16E vs API16E_b), wall_guard firings, chunk counts and part c
     canon16d equality;
  2. runs recount_049 and run_reference_049 (block smoke) on copies; runs scripts/api_checks_049.py into a temp file;
  3. builds a synthetic complete block (smoke fresh cases relabelled 'main', the smoke replays kept as parts r and c, expected
     counts patched in this process only), re-sealed with the runner's _write (stand-in freeze), recounted, referenced,
     self-replayed (GFID49 fidelity) and gated twice (dumps must be identical); exercises verify_release_0460.release_ok;
  4. runs verify_release_0460.chain on the repository (ledger since preregistration_049; HEAD stands in for freeze and seal);
  5. runtime projection (Inferred), plan 049 runtime_estimate: r_min(key) = min(slowest smoke conflict rate over that key's
     certify/16e fresh or part-r records with case wall >= 1 s, the declared rates scale16 6716/s, scale20 3528/s); every
     fresh or part-r scale16 / scale20 job worst min(600 s, B / r_min + 10 s); controls and part c at their smoke mean (part c
     scale20, absent from smoke, at the largest part c smoke mean); LPT on 8 workers.
     Cut order: the first of (R20 True, N20 8), (R20 False, 8), (False, 6), (False, 4) whose worst-case LPT <= 3600 s, else
     (False, 0); the runner's (R20, N20) must equal it (cut_consistent).
Writes results/diag-049/PREFREEZE_SMOKE_GATES_049.json (refuses overwrite). Observed only: no gate decision, no tuning.
  PYTHONPATH=. python scripts/prefreeze_smoke_049.py /tmp/s49/smoke"""
import copy,json,shutil,subprocess,sys,tempfile
from pathlib import Path
from unittest import mock
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments import brute_study_049 as ST
from experiments.brute_common_049 import load,write_new,PLAN,budget_for
from experiments.brute_common import dumps
from scripts import make_gates_049 as MG
from scripts import make_freeze_049 as MF
from scripts import verify_release_0460 as V
from scripts import api_checks_049 as AC
from scripts.recount_049 import main as recount
from scripts.run_reference_049 import main as reference
OUT=ROOT/'results/diag-049/PREFREEZE_SMOKE_GATES_049.json';CAP=3600;GUARD=600.0;RATE_DECL={'scale16':6716.0,'scale20':3528.0}
STEPS=((True,8),(False,8),(False,6),(False,4))


def status(g):return {k:{'pass':v['pass'],**({'reason':v['reason']} if 'reason' in v else {})} for k,v in g['gates'].items()}


def _lpt(walls,workers):
    bins=[0.0]*workers
    for x in sorted(walls,reverse=True):bins[bins.index(min(bins))]+=x
    return max(bins)


def _jobs(r20,n20):
    with mock.patch.object(ST,'N20',n20),mock.patch.object(ST,'R20',r20):return ST.jobs_for(load(PLAN),'main')


def projection(res,workers=8):
    fv={};rate={}
    for c in res['cases']:
        for g,w in c['group_walls_informational'].items():fv.setdefault(c['key'],[]).append(w)
    for r in res['replays']:fv.setdefault(r['block']+'/'+r['key'],[]).append(r['job_wall_informational'])
    for c in res['replays']+res['cases']:
        if c['block']=='c':continue
        for a,x in c['arms'].items():
            w=x.get('case_wall_informational')
            if w and w>=1.0:rate.setdefault(c['key'],[]).append(x['conflicts_spent']/w)
    fm={k:sum(x)/len(x) for k,x in fv.items()};smin={k:min(v) for k,v in rate.items()}
    rmin={k:min([v for v in (smin.get(k),RATE_DECL.get(k)) if v is not None]) for k in set(smin)|set(RATE_DECL)}
    cmax=max([v for k,v in fm.items() if k.startswith('c/')] or [0.0])
    def mean(j):
        if j[0]=='c':return fm.get('c/'+j[1],cmax)
        return fm.get(('r/' if j[0]=='r' else '')+j[1],fm.get(j[1],0.0))
    def worst(j):return min(GUARD,budget_for(j[1])/rmin[j[1]]+10.0) if (j[0]!='c' and j[1] in RATE_DECL) else mean(j)
    out={'label':'Inferred','mean_wall_by_key':{k:round(v,2) for k,v in sorted(fm.items())},'smoke_slowest_rate_by_key':{k:round(v,1) for k,v in sorted(smin.items())},
         'rate_declared':RATE_DECL,'r_min_by_key':{k:round(v,1) for k,v in sorted(rmin.items())},'workers':workers,'cap_s':CAP,'candidates':{}}
    for r20,n in STEPS+((False,0),):
        J=_jobs(r20,n);w=[mean(j) for j in J];x=[worst(j) for j in J]
        out['candidates'][f'R20={r20},N20={n}']={'jobs':len(J),'mean_lpt_s':round(_lpt(w,workers),1),'worst_serial_s':round(sum(x),1),'worst_case_lpt_s':round(_lpt(x,workers),1)}
    req=next((s for s in STEPS if out['candidates'][f'R20={s[0]},N20={s[1]}']['worst_case_lpt_s']<=CAP),(False,0))
    out['required']={'R20':req[0],'N20':req[1]};out['runner']={'R20':ST.R20,'N20':ST.N20}
    out['cut_consistent']=req==(ST.R20,ST.N20);out['cut_applied']=req!=(True,8)
    out['caveat']='two scale16, two scale20, two control smoke seeds and two sealed traces per part r / c; the worst case assumes every long job exhausts its budget at r_min'
    return out


def head():return subprocess.run(['git','-C',str(ROOT),'rev-parse','--short','HEAD'],capture_output=True,text=True).stdout.strip()


def main(argv=None):
    argv=sys.argv[1:] if argv is None else argv;S=Path(argv[0]);out={'label':'Observed','purpose':__doc__.split('\n')[0]}
    res=load(S/'RESULTS.json');st={};allr=res['replays']+res['cases']
    for c in allr:
        for a,x in c['arms'].items():st.setdefault(x['stop'],[]).append(f"{c['block']}/{c['key']}/{c['seed']}/{a}")
    out['stops_present']={k:len(v) for k,v in sorted(st.items())}
    out['smoke_records']=[(c['block'],c['key'],c['seed'],{a:[x['label'],x['stop'],x['conflicts_spent'],x.get('chunks_total'),round(x.get('case_wall_informational') or 0,2),
                           round(x.get('chunk_wall_max') or 0,3),x['wall_guard']] for a,x in c['arms'].items()},
                           (c.get('replay') or {}).get('class'),(c.get('replay') or {}).get('canon16d_equal')) for c in allr]
    out['smoke_record_columns']=['block','key','seed','arm: label, stop, conflicts, chunks, case wall s, max chunk wall s, wall_guard','replay class','canon16d_equal']
    out['smoke_wall_guard_records']=[f"{c['block']}/{c['key']}/{c['seed']}/{a}" for c in allr for a,x in c['arms'].items() if x.get('wall_guard')]
    out['smoke_determinism']=[(c['key'],c['seed'],ST.canon16e(c['arms']['API16E'])==ST.canon16e(c['arms']['API16E_b'])) for c in res['cases']]
    out['smoke_part_c_canon16d_equal']=[(c['key'],c['seed'],c['replay']['canon16d_equal']) for c in res['replays'] if c['block']=='c']
    out['runtime_projection']=projection(res)
    with tempfile.TemporaryDirectory() as d:
        C=Path(d)/'copy';C.mkdir()
        for nm in ('RESULTS.json','SCIENTIFIC.json','SEAL.json'):shutil.copy(S/nm,C/nm)
        out['recount_rc']=recount([str(C)]);rc=load(C/'RECOUNT_049.json')
        out['recount']={k:rc.get(k) for k in ('replays','cases','labels_r','labels_c','part_r','part_c','replay_wrong','words_checked','mismatching_cases','mismatches','PASS')}
        out['reference_rc']=reference([str(C),'--block','smoke','--workers','8']);rf=load(C/'REFERENCE_049.json')
        out['reference_smoke']={k:rf.get(k) for k in ('records','decided','audited','complete','per_key','mismatch_count','vacuous','PASS','elapsed_informational','scope')}|{'mutations':rf['mutation_test']['detected'],'of':rf['mutation_test']['mutations']}
        ac=Path(d)/'API_CHECKS_049.json';p=subprocess.run([sys.executable,str(ROOT/'scripts/api_checks_049.py'),'--output',str(ac)],
            cwd=ROOT,capture_output=True,text=True,timeout=900,env={'PYTHONPATH':str(ROOT),'PATH':'/usr/bin:/bin'});out['api_checks_rc']=p.returncode
        if p.returncode and not ac.exists():raise SystemExit('api_checks_049 failed: '+p.stderr[-2000:])
        A=load(ac)
        out['api_checks']={'PASS':A['PASS'],'compat':A['compat']['PASS'],'ghost':{k:A['ghost'].get(k) for k in ('frozen_api_unchanged','certify16d_closure_unchanged','socket_attempts','new_flagged','newly_imported','PASS49')}}
        D=Path(d)/'synthetic';(D/'main').mkdir(parents=True);fz=Path(d)/'FREEZE_STANDIN.json';fz.write_text('{}')
        cases=[dict(copy.deepcopy(c),block='main') for c in res['cases']];reps=[copy.deepcopy(r) for r in res['replays']];P=load(PLAN)
        with mock.patch.object(ST,'FREEZE',fz):
            ST._write(D/'main',P,'main',[f'synthetic:{i}' for i in range(2*len(cases)+len(reps))],(reps,cases),True,{'total_elapsed_informational':res.get('total_elapsed_informational')})
        rr=recount([str(D/'main')]);rf2=reference([str(D/'main'),'--workers','8'])
        exp={k:sum(c['key']==k for c in cases) for k in ('scale16','control','scale20')}
        nr=sum(r['block']=='r' for r in reps);nc=sum(r['block']=='c' for r in reps)
        fi=AC.fidelity(D/'main',len(cases));A2=dict(A,fidelity=fi);(D/'API_CHECKS_049.json').write_text(json.dumps(A2))
        g1=MG.build(D,exp,nr,nc);g2=MG.build(D,exp,nr,nc)
        out['synthetic']={'cases':exp,'replays_r':nr,'replays_c':nc,'recount_rc':rr,'reference_rc':rf2,'gate_status':status(g1),'secondary':sorted(g1['secondary']),
                          'fidelity_self_replay':{k:v for k,v in fi.items() if k!='per_case'},
                          **{nm:g1['gates'][nm]['observed'] for nm in ('GDET49','GFID49','GCOMPAT16D','GS20_sound49','GR49_sound','G10','GQB24','GS_ref')},
                          'sealed_input_verified':g1['sealed_input_verified'],'reproduces':dumps(g1)==dumps(g2),'label_source':g1['label_source'],
                          'note':'synthetic: smoke fresh cases as main with expected counts patched; GDET49 and GFID49 fail here by their 18 + N20 count, GAPI16E_fresh49 by its 12-case count, G10 by its 6-control count, GHOST49 by design (no 049 freeze yet), GTI and G_PROC by design'}
        Rd=Path(d)/'rel';(Rd/V.STUDY).mkdir(parents=True);(Rd/V.STUDY/'GATES_049.json').write_bytes(dumps(g1))
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
                 and out['api_checks_rc']==0 and out['api_checks']['PASS'] is True and pj['cut_consistent']
                 and out['release_ok_synthetic'] is True and vc['passed'] and vc.get('authorization_exceptions')==0)
    out['note']='PASS here means the tooling ran end to end on a sealed block, gates reproduce, the self-replay is exact, the cut order was applied as declared and the real commit-order check passes; gate outcomes on smoke are recorded, not required'
    write_new(OUT,out);print(json.dumps({k:v for k,v in out.items() if k not in ('smoke_records','synthetic')},default=str)[:6000])
    print(json.dumps(sy['gate_status']));return 0 if out['PASS'] else 1


if __name__=='__main__':sys.exit(main())
