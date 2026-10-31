"""Pre-freeze smoke-gates test for study-039 (plan 039 process: "pre-freeze gates test on a sealed smoke block"; the #129
lesson). New file; built from scripts/prefreeze_smoke_038.py (frozen). Input: a sealed smoke block written by
experiments/brute_study_039.py --block smoke (outside results/study-039). Runs recount_039 and run_reference_039 on it (wall
recorded, task: measure the reference cost), builds make_gates_039 on it, then relabels the same cases block 'main' (seeds
unchanged, so no plan seed is touched), re-seals them with the runner's _write (stand-in freeze hash), recounts, gates and runs
make_gates_039 --check in a subprocess. Also records the runtime projection for the main block: an LPT makespan over the main
job list (group-major jobs) from the mean smoke group wall per (group, key), on 8 workers, for the full plan and for the
pre-declared reduction (A14_k64 on scale16 only); plan 039 runtime rule: over 1500 s, reduce A14_k64 to scale16 only by a
deviation before the freeze (Inferred). Writes results/diag-039/PREFREEZE_SMOKE_GATES_039.json (refuses overwrite).
Observed only: no gate decision, no tuning.
  PYTHONPATH=. python scripts/prefreeze_smoke_039.py /tmp/smoke"""
import json,subprocess,sys,tempfile
from pathlib import Path
from time import perf_counter
from unittest import mock
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments import brute_study_039 as ST
from experiments.brute_common_039 import load,write_new,PLAN
from scripts import make_gates_039 as MG
from scripts.recount_039 import main as recount
from scripts.run_reference_039 import main as reference
OUT=ROOT/'results/diag-039/PREFREEZE_SMOKE_GATES_039.json';THRESH=1500


def status(g):return {k:{'pass':v['pass'],**({'reason':v['reason']} if 'reason' in v else {})} for k,v in g['gates'].items()}


def _lpt(walls,workers):
    bins=[0.0]*workers
    for x in sorted(walls,reverse=True):bins[bins.index(min(bins))]+=x
    return max(bins)


def projection(res,workers=8):
    """Inferred: mean smoke group wall per (group, key), summed over the main job list; LPT makespan on `workers` (no contention model)."""
    per={}
    for c in res['cases']:
        for g,w in c['group_walls_informational'].items():per.setdefault((g,c['key']),[]).append(w)
    mean={k:sum(v)/len(v) for k,v in per.items()};P=load(PLAN)
    full={k:ST.GROUPS for k in ST.KEY_ORDER};red={k:(ST.GROUPS if k=='scale16' else tuple(g for g in ST.GROUPS if g!='A14_k64')) for k in ST.KEY_ORDER}
    def est(G):
        w=[mean[(j[3],j[1])] for j in ST.jobs_for(P,'main',G)];return {'jobs':len(w),'serial_s':round(sum(w),1),'ideal_parallel_s':round(sum(w)/workers,1),'lpt_makespan_s':round(_lpt(w,workers),1)}
    f=est(full);r=est(red)
    return {'label':'Inferred','mean_group_wall_by_group_key':{f'{g}/{k}':round(v,1) for (g,k),v in sorted(mean.items())},'workers':workers,
            'full_plan':f,'reduced_A14_k64_scale16_only':r,'smoke_total_elapsed_s':res.get('total_elapsed_informational'),'cap_s':1800,
            'threshold_s':THRESH,'reduce_A14_k64':f['lpt_makespan_s']>THRESH}


def main(argv=None):
    argv=sys.argv[1:] if argv is None else argv;S=Path(argv[0]);out={'label':'Observed','purpose':__doc__.split('\n')[0]}
    res=load(S/'RESULTS.json')
    out['smoke_cases']=[(c['key'],c['seed'],{a:c['arms'][a]['label'] for a in c['arms']},{a:c['arms'][a].get('used') for a in c['arms']},
                         {a:round(c['arms'][a].get('query_max_s') or 0,2) for a in c['arms']},{g:round(w,1) for g,w in c['group_walls_informational'].items()}) for c in res['cases']]
    out['runtime_projection']=projection(res)
    out['recount_rc']=recount([str(S)]);rc=load(S/'RECOUNT_039.json');out['recount']={k:rc.get(k) for k in ('cases','labels','words_checked','words_unsound','mismatching_cases','PASS')}
    t=perf_counter();out['reference_rc']=reference([str(S),'--workers','3']);rf=load(S/'REFERENCE_039.json')
    out['reference_on_smoke']={k:rf.get(k) for k in ('cases','decided','not_reached','verdicts_checked','words_checked','mismatch_count','PASS')}|{'mutations':rf['mutation_test']['detected'],'of':rf['mutation_test']['mutations'],'wall_s_informational':round(perf_counter()-t,1),'workers':3}
    with tempfile.TemporaryDirectory() as d:
        sd=Path(d)/'smoke_as_study';(sd/'main').mkdir(parents=True)
        for nm in ('RESULTS.json','SCIENTIFIC.json','SEAL.json','RECOUNT_039.json','REFERENCE_039.json'):(sd/'main'/nm).write_bytes((S/nm).read_bytes())
        g=MG.build(sd);out['smoke_gate_status']=status(g);out['smoke_sealed_input_verified']=g['sealed_input_verified']
        D=Path(d)/'relabelled';(D/'main').mkdir(parents=True);fz=Path(d)/'FREEZE_STANDIN.json';fz.write_text('{}')
        cases=[dict(c,block='main') for c in res['cases']];P=load(PLAN)
        with mock.patch.object(ST,'FREEZE',fz):ST._write(D/'main',P,'main',[f"main:{c['key']}:{c['seed']}:{g_}" for c in cases for g_ in c['group_walls_informational']],cases,True,{'total_elapsed_informational':res.get('total_elapsed_informational')})
        rr=recount([str(D/'main')]);g=MG.build(D);(D/'GATES_039.json').write_bytes(MG.dumps(g))
        r=subprocess.run([sys.executable,'scripts/make_gates_039.py','--study-dir',str(D),'--check'],cwd=ROOT,capture_output=True,text=True,env={'PYTHONPATH':str(ROOT),'PATH':'/usr/bin:/bin'})
        out['relabelled']={'recount_rc':rr,'crashed':False,'gate_status':status(g),'secondary':{k:v['pass'] for k,v in g['secondary'].items()},
                           'sealed_input_verified':g['sealed_input_verified'],'check_returncode':r.returncode,'check_stdout':r.stdout.strip(),'reports_keys':sorted(g['reports'])}
    out['PASS']=out['recount_rc']==0 and out['relabelled']['recount_rc']==0 and out['relabelled']['check_returncode']==0 and out['relabelled']['sealed_input_verified']
    out['note']='PASS here means the tooling ran end to end on a sealed block (recount reproduces, gates reproduce); the reference result is recorded, not required'
    write_new(OUT,out);print(json.dumps(out,default=str)[:4000]);return 0 if out['PASS'] else 1


if __name__=='__main__':sys.exit(main())
