"""Pre-freeze smoke-gates, runtime projection and cut order for study-056 (plan 056 runtime_estimate; pre-run
deviation #185). New file; built from scripts/prefreeze_smoke_055.py (frozen). Input: the sealed smoke block written by
experiments/brute_study_056.py --block smoke (outside results/study-056; smoke seeds 01-02 scale20t by API20L / API20L_b / API16E20,
03-04 compat20t by API20L / API16E, 05-06 unused; two concurrent 4-worker pools, conflict-only stop). Smoke is never gated and never
sets C or B. It
  1. lists stops, smoke determinism (canon20l and conflicts_spent of the two certify/20l passes), wall_guard firings, hook arms (must
     be 0 everywhere), table sizes per record;
  2. runs recount_056 and run_reference_056 (block smoke) on copies, records compat_rule_056 per smoke compat pair (from the
     recount, which holds the recounted future_match), runs scripts/api_checks_056.py (ghost only) into a temp file;
  3. builds a synthetic complete block (smoke cases relabelled 'main'), re-sealed with the runner's _write (stand-in freeze),
     recounted, referenced, self-replayed (GFID56 fidelity: API20L gated, API16E reported, all must be exact) and gated twice with
     the smoke case counts (dumps must be identical); exercises verify_release_0530.release_ok;
  4. runs verify_release_0530.chain on the repository (ledger since preregistration_056; HEAD stands in for freeze and seal);
  5. runtime projection (Inferred), plan 056 runtime_estimate (worst case, every job spends its whole B): r_min = min(slowest smoke
     conflict rate over records with case wall >= 1 s, the declared 4503/s); every job worst B / r_min + 10 s; each pool total = LPT of
     its jobs on 4 workers; the run = max over the two concurrent pools. Declared cut rule: N20L = 6 if the run <= 3300 s else 4;
     then NC20L = 6 if the run (with that N20L) <= 3300 s else 4 (cut_exhausted if still > 3300 s); the runner's N20L and NC20L
     must equal them (cut_consistent). Table bookkeeping is pure Python and is inside each record's case wall.
Writes results/diag-056/PREFREEZE_SMOKE_GATES_056.json (refuses overwrite). Observed only: no gate decision, no tuning.
  PYTHONPATH=. python scripts/prefreeze_smoke_056.py /tmp/s56/smoke"""
import copy,json,shutil,subprocess,sys,tempfile
from pathlib import Path
from unittest import mock
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments import brute_study_056 as ST
from experiments.brute_common_056 import load,write_new,PLAN,caps_for,WORKERS_S,WORKERS_C
from experiments.brute_common import dumps
from scripts import make_gates_056 as MG
from scripts import make_freeze_056 as MF
from scripts import verify_release_0530 as V
from scripts import api_checks_056 as AC
from scripts.recount_056 import main as recount
from scripts.run_reference_056 import main as reference
OUT=ROOT/'results/diag-056/PREFREEZE_SMOKE_GATES_056.json';CAP=3300.0;RATE_DECL=4503.0
STEPS=(6,4);KEYS=('scale20t','compat20t');POOL={'scale20t':WORKERS_S,'compat20t':WORKERS_C}
budget_for=lambda k:caps_for(k)[1]
BY_DESIGN=('GHOST56','GTI','GTEST','G_PROC')


def status(g):return {k:{'pass':v['pass'],**({'reason':v['reason']} if 'reason' in v else {})} for k,v in g['gates'].items()}


def _lpt(walls,workers):
    bins=[0.0]*workers
    for x in sorted(walls,reverse=True):bins[bins.index(min(bins))]+=x
    return max(bins)


def _jobs(n20,nc):
    with mock.patch.object(ST,'N20L',n20),mock.patch.object(ST,'NC20L',nc):return ST.jobs_for(load(PLAN),'main')


def projection(res):
    fv={};rate=[]
    for c in res['cases']:
        for g,w in c['group_walls_informational'].items():fv.setdefault(c['key'],[]).append(w)
        for a,x in c['arms'].items():
            w=x.get('case_wall_informational')
            if w and w>=1.0:rate.append(x['conflicts_spent']/w)
    fm={k:sum(x)/len(x) for k,x in fv.items()};smin=min(rate) if rate else None
    rmin=min(v for v in (smin,RATE_DECL) if v is not None)
    worst=lambda j:budget_for(j[1])/rmin+10.0;mean=lambda j:fm.get(j[1],0.0)
    out={'label':'Inferred','mean_wall_by_key':{k:round(v,2) for k,v in sorted(fm.items())},'smoke_slowest_rate':None if smin is None else round(smin,1),
         'rate_declared':RATE_DECL,'r_min':round(rmin,1),'worst_per_job_s':{k:round(worst(('main',k,0,'')),1) for k in KEYS},
         'workers':POOL,'cap_s':CAP,'candidates':{}}
    def tot(J):
        o={}
        for k in KEYS:
            P=[j for j in J if j[1]==k]
            o[k]={'jobs':len(P),'worst_s':round(_lpt([worst(j) for j in P],POOL[k]),1),'mean_s':round(_lpt([mean(j) for j in P],POOL[k]),1)}
        o['worst_run_s']=max(o[k]['worst_s'] for k in KEYS);o['mean_run_s']=max(o[k]['mean_s'] for k in KEYS);return o
    for n20 in STEPS:
        for nc in STEPS:out['candidates'][f'N20L={n20},NC20L={nc}']=tot(_jobs(n20,nc))
    C=lambda a,b:out['candidates'][f'N20L={a},NC20L={b}']
    r20=STEPS[0] if C(STEPS[0],STEPS[0])['worst_run_s']<=CAP else STEPS[1]
    rc=STEPS[0] if C(r20,STEPS[0])['worst_run_s']<=CAP else STEPS[1]
    ch=C(r20,rc)
    out['required']={'N20L':r20,'NC20L':rc};out['chosen_projection']=ch
    out['cut_exhausted']=ch['worst_run_s']>CAP;out['runner']={'N20L':ST.N20L,'NC20L':ST.NC20L}
    out['cut_consistent']=(r20,rc)==(ST.N20L,ST.NC20L);out['cut_applied']={'scale20t':r20!=STEPS[0],'compat20t':rc!=STEPS[0]}
    out['projected_main_worst_s']=ch['worst_run_s']
    out['caveat']='two smoke seeds per key; the worst case assumes every job spends its whole B at r_min; the two pools run concurrently'
    return out


def head():return subprocess.run(['git','-C',str(ROOT),'rev-parse','--short','HEAD'],capture_output=True,text=True).stdout.strip()


def main(argv=None):
    argv=sys.argv[1:] if argv is None else argv;S=Path(argv[0]);out={'label':'Observed','purpose':__doc__.split('\n')[0]}
    res=load(S/'RESULTS.json');st={};allr=res['cases']
    for c in allr:
        for a,x in c['arms'].items():st.setdefault(x['stop'],[]).append(f"{c['block']}/{c['key']}/{c['seed']}/{a}")
    out['stops_present']={k:len(v) for k,v in sorted(st.items())}
    out['smoke_records']=[(c['block'],c['key'],c['seed'],{a:[x['label'],x['stop'],x['conflicts_spent'],x.get('chunks_total'),round(x.get('case_wall_informational') or 0,2),
                           round(x.get('chunk_wall_max') or 0,3),x['wall_guard'],x.get('n_min'),x.get('api')['api'] if isinstance(x.get('api'),dict) else None] for a,x in c['arms'].items()}) for c in allr]
    out['smoke_record_columns']=['block','key','seed','arm: label, stop, conflicts, chunks, case wall s, max chunk wall s, wall_guard, n_min, api']
    out['smoke_wall_guard_records']=[f"{c['block']}/{c['key']}/{c['seed']}/{a}" for c in allr for a,x in c['arms'].items() if x.get('wall_guard')]
    det=[(c['key'],c['seed'],ST.canon20l(c['arms']['API20L'])==ST.canon20l(c['arms']['API20L_b'])
          and c['arms']['API20L']['conflicts_spent']==c['arms']['API20L_b']['conflicts_spent']) for c in allr if c['key']=='scale20t']
    out['smoke_determinism']=det
    out['hook_arms']={f"{c['key']}/{c['seed']}/{a}":x.get('hook_arms') for c in allr for a,x in c['arms'].items()}
    out['smoke_table']={f"{c['key']}/{c['seed']}/{a}":{k:(x.get('table') or {}).get(k) for k in ('rows','n_columns','hypotheses','counterexamples','fill_steps')}
                        for c in allr for a,x in c['arms'].items() if a in AC.T_ARMS}
    out['runtime_projection']=projection(res)
    with tempfile.TemporaryDirectory() as d:
        C=Path(d)/'copy';C.mkdir()
        for nm in ('RESULTS.json','SCIENTIFIC.json','SEAL.json'):shutil.copy(S/nm,C/nm)
        out['recount_rc']=recount([str(C)]);rc=load(C/'RECOUNT_056.json')
        out['smoke_compat']=[(c['seed'],(rc.get('compat') or {}).get(f"{c['block']}/{c['key']}/{c['seed']}") or {'equal':False,'missing':True}) for c in allr if c['key']=='compat20t']
        out['recount']={k:rc.get(k) for k in ('labels','compat_equal','misfires','words_checked','words_unsound','truth_inconsistent','mismatching_cases','PASS')}
        out['reference_rc']=reference([str(C),'--block','smoke','--workers','8']);rf=load(C/'REFERENCE_056.json')
        out['reference_smoke']={k:rf.get(k) for k in ('records','decided','audited','complete','per_key','mismatch_count','vacuous','PASS','elapsed_informational','scope')}|{'mutations':rf['mutation_test']['detected'],'of':rf['mutation_test']['mutations']}
        ac=Path(d)/'API_CHECKS_056.json';p=subprocess.run([sys.executable,str(ROOT/'scripts/api_checks_056.py'),'--output',str(ac)],
            cwd=ROOT,capture_output=True,text=True,timeout=900,env={'PYTHONPATH':str(ROOT),'PATH':'/usr/bin:/bin'});out['api_checks_rc']=p.returncode
        if p.returncode and not ac.exists():raise SystemExit('api_checks_056 failed: '+p.stderr[-2000:])
        A=load(ac);out['api_checks']={'PASS':A.get('PASS'),'ghost':{k:A['ghost'].get(k) for k in A['ghost'] if k not in ('closures',)}}
        D=Path(d)/'synthetic';(D/'main').mkdir(parents=True);fz=Path(d)/'FREEZE_STANDIN.json';fz.write_text('{}')
        cases=[dict(copy.deepcopy(c),block='main') for c in res['cases']];P=load(PLAN)
        with mock.patch.object(ST,'FREEZE',fz):
            ST._write(D/'main',P,'main',[f'synthetic:{i}' for i in range(sum(len(c['arms']) for c in cases))],cases,True,{'total_elapsed_informational':res.get('total_elapsed_informational')})
        rr=recount([str(D/'main')]);rf2=reference([str(D/'main'),'--workers','8'])
        exp={k:sum(c['key']==k for c in cases) for k in KEYS};nrec=sum(len(c['arms']) for c in cases)
        nT=sum(1 for c in cases for a in c['arms'] if a in AC.T_ARMS)
        fi=AC.fidelity(D/'main',nT);A2=dict(A,fidelity=fi);(D/'API_CHECKS_056.json').write_text(json.dumps(A2))
        g1=MG.build(D,exp);g2=MG.build(D,exp)
        out['synthetic']={'cases':exp,'records':nrec,'recount_rc':rr,'reference_rc':rf2,'gate_status':status(g1),'secondary':sorted(g1['secondary']),
                          'fidelity_self_replay':{k:v for k,v in fi.items() if k!='per_case'},
                          **{nm:g1['gates'][nm].get('observed') for nm in ('GDET56','GFID56','GTABLE56','GCOMPAT20L56','GS20L_sound56','GS20L_gain56','GS_ref','G_sound')},
                          'GS20L_rate56':g1['secondary']['GS20L_rate56']['observed'],'GS20L_paired56':g1['secondary']['GS20L_paired56']['observed'],
                          'GTABLE_stats56':g1['secondary']['GTABLE_stats56']['totals'],'RECHECK_055':g1['secondary']['RECHECK_055'],
                          'certified_20l_N20':g1['certified_20l_N20'],'sound_not_certified_20l':g1['sound_not_certified_20l'],'status_phrase':g1['status_phrase'],
                          'sealed_input_verified':g1.get('sealed_input_verified'),'reproduces':dumps(g1)==dumps(g2),'label_source':g1.get('label_source'),
                          'note':('synthetic: smoke cases as main with the smoke case counts; GHOST56, GTI, GTEST and G_PROC may fail by design (no 056 freeze, '
                                  'suite or sealed main yet); GS20L_gain56 on 2 smoke cases is recorded, not required')}
        Rd=Path(d)/'rel';(Rd/V.STUDY).mkdir(parents=True);(Rd/V.STUDY/'GATES_056.json').write_bytes(dumps(g1))
        Rel={k:'x' for k in V.RELEASE_KEYS};Rel.update(version=V.VERSION,gates_passed=sorted(k for k,v in g1['gates'].items() if v['pass'] is True),
             gates_failed=sorted(k for k,v in g1['gates'].items() if v['pass'] is False),gates_not_exercised=sorted(k for k,v in g1['gates'].items() if v['pass'] is None),
             secondary={k:v['pass'] for k,v in g1['secondary'].items()},certified_20l_N20=g1['certified_20l_N20'],sound_not_certified_20l=g1['sound_not_certified_20l'],status_phrase=g1['status_phrase'])
        (Rd/'RELEASE.json').write_text(json.dumps(Rel))
        try:V.release_ok(Rd);out['release_ok_synthetic']=True
        except Exception as e:out['release_ok_synthetic']=f'error: {e}'
    E=MF.entries();h=head();R={'preregistration_commit':E[0]['commit'],'source_freeze_commit':h,'seal_commit':h}
    try:out['verifier_chain']={'passed':True,'entries':[[e['event'],e['commit']] for e in E],'head':h,**V.chain(ROOT,R,E)}
    except Exception as e:out['verifier_chain']={'passed':False,'error':str(e),'entries':[[e['event'],e['commit']] for e in E]}
    vc=out['verifier_chain'];pj=out['runtime_projection'];sy=out['synthetic'];fs=sy['fidelity_self_replay']
    out['PASS']=(out['recount_rc']==0 and out['reference_rc']==0 and sy['recount_rc']==0 and sy['reference_rc']==0 and sy['reproduces']
                 and sy['sealed_input_verified'] and not any('INCOMPLETE_INPUT' in v.get('reason','') for k,v in sy['gate_status'].items() if k not in BY_DESIGN)
                 and sy['gate_status']['G_recount']['pass'] is True and sy['label_source']=='recount'
                 and (fs.get('gated') or {}).get('exact')==(fs.get('gated') or {}).get('cases')==nT
                 and (fs.get('reported') or {}).get('exact')==(fs.get('reported') or {}).get('cases')==nrec-nT
                 and out['api_checks_rc']==0 and pj['cut_consistent'] and all(x[2] for x in det) and all(v==0 for v in out['hook_arms'].values())
                 and len(out['smoke_compat'])>0 and all(x[1].get('rule_name')=='compat_rule_056' and x[1].get('label') and x[1].get('control_label') for x in out['smoke_compat'])
                 and out['release_ok_synthetic'] is True and vc['passed'] and vc.get('authorization_exceptions')==0)
    out['smoke_compat_equal']=sum(bool(x[1]['equal']) for x in out['smoke_compat'])  # recorded, not required (plan 056 smoke_range: never gated; #185 Fix E)
    out['note']='PASS here means the tooling ran end to end on a sealed block, gates reproduce, the self-replay is exact, the cut order was applied as declared and the real commit-order check passes; gate outcomes on smoke are recorded, not required'
    write_new(OUT,out);print(json.dumps({k:v for k,v in out.items() if k not in ('smoke_records','synthetic')},default=str)[:6000])
    print(json.dumps(sy['gate_status']));return 0 if out['PASS'] else 1


if __name__=='__main__':sys.exit(main())
