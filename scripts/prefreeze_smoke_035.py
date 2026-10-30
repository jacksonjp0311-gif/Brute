"""Pre-freeze smoke-gates test for study-035 (plan 035 process: "pre-freeze gates test on a sealed smoke block"; the #129
lesson). New file; built from scripts/prefreeze_smoke_034.py (frozen). Input: a sealed smoke block written by
experiments/brute_study_035.py --block smoke (outside results/study-035). Runs recount_035 and run_reference_035 on it, builds
make_gates_035 on it, then relabels the same cases block 'main' (seeds unchanged, so no plan seed is touched), re-seals them
with the runner's _write (stand-in freeze hash), recounts, gates and runs make_gates_035 --check in a subprocess. Also records
the runtime projection for the 48-case main block (Inferred). Writes results/diag-035/PREFREEZE_SMOKE_GATES_035.json
(refuses overwrite). Observed only: no gate decision, no tuning.
  PYTHONPATH=. python scripts/prefreeze_smoke_035.py /tmp/smoke"""
import json,subprocess,sys,tempfile
from pathlib import Path
from unittest import mock
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments import brute_study_035 as ST
from experiments.brute_common_035 import load,write_new,PLAN
from scripts import make_gates_035 as MG
from scripts.recount_035 import main as recount
from scripts.run_reference_035 import main as reference
OUT=ROOT/'results/diag-035/PREFREEZE_SMOKE_GATES_035.json'
MAIN_COUNTS={'scale16_clean':6,'noisy_scale12':12,'clean_scale12':12,'noisy_scale8':12,'control':6}


def status(g):return {k:{'pass':v['pass'],**({'reason':v['reason']} if 'reason' in v else {})} for k,v in g['gates'].items()}


def projection(res,workers=8):
    """Inferred: mean smoke case wall per key times the main counts, divided by the worker count (no contention model)."""
    per={}
    for c in res['cases']:per.setdefault(c['key'],[]).append(c['case_wall_informational'])
    mean={k:sum(v)/len(v) for k,v in per.items()};tot=sum(mean.get(k,max(mean.values()))*n for k,n in MAIN_COUNTS.items())
    lpt=sorted([mean.get(k,max(mean.values())) for k,n in MAIN_COUNTS.items() for _ in range(n)],reverse=True);bins=[0.0]*workers
    for x in lpt:bins[bins.index(min(bins))]+=x
    return {'label':'Inferred','mean_case_wall_by_key':{k:round(v,1) for k,v in mean.items()},'serial_s':round(tot,1),
            'ideal_parallel_s':round(tot/workers,1),'greedy_makespan_s':round(max(bins),1),'workers':workers,
            'smoke_total_elapsed_s':res.get('total_elapsed_informational'),'cap_s':1800}


def main(argv=None):
    argv=sys.argv[1:] if argv is None else argv;S=Path(argv[0]);out={'label':'Observed','purpose':__doc__.split('\n')[0]}
    res=load(S/'RESULTS.json');out['smoke_cases']=[(c['key'],c['seed'],{a:c['arms'][a]['label'] for a in ST.ORDER},
        c['arms']['A10']['used'],c['arms']['A10']['stop'],c['arms']['A10']['B_final'],round(c['case_wall_informational'],1)) for c in res['cases']]
    out['runtime_projection']=projection(res)
    out['recount_rc']=recount([str(S)]);rc=load(S/'RECOUNT_035.json');out['recount']={k:rc[k] for k in ('cases','labels','words_checked','words_unsound','mismatching_cases','PASS')}
    out['reference_rc']=reference([str(S),'--workers','2']);rf=load(S/'REFERENCE_035.json')
    out['reference_on_smoke_noisy8']={k:rf.get(k) for k in ('cases','decided_items','undecided_items','labels_checked','mismatch_count','PASS')}|{'mutations':rf['mutation_test']['detected'],'of':rf['mutation_test']['mutations']}
    with tempfile.TemporaryDirectory() as d:
        sd=Path(d)/'smoke_as_study';(sd/'main').mkdir(parents=True)
        for nm in ('RESULTS.json','SCIENTIFIC.json','SEAL.json','RECOUNT_035.json','REFERENCE_035.json'):(sd/'main'/nm).write_bytes((S/nm).read_bytes())
        g=MG.build(sd);out['smoke_gate_status']=status(g);out['smoke_sealed_input_verified']=g['sealed_input_verified']
        D=Path(d)/'relabelled';(D/'main').mkdir(parents=True);fz=Path(d)/'FREEZE_STANDIN.json';fz.write_text('{}')
        cases=[dict(c,block='main') for c in res['cases']];P=load(PLAN)
        with mock.patch.object(ST,'FREEZE',fz):ST._write(D/'main',P,'main',[f"main:{c['key']}:{c['seed']}" for c in cases],cases,True,{'total_elapsed_informational':res.get('total_elapsed_informational')})
        rr=recount([str(D/'main')]);g=MG.build(D);(D/'GATES_035.json').write_bytes(MG.dumps(g))
        r=subprocess.run([sys.executable,'scripts/make_gates_035.py','--study-dir',str(D),'--check'],cwd=ROOT,capture_output=True,text=True,env={'PYTHONPATH':str(ROOT),'PATH':'/usr/bin:/bin'})
        out['relabelled']={'recount_rc':rr,'crashed':False,'gate_status':status(g),'secondary':{k:v['pass'] for k,v in g['secondary'].items()},
                           'sealed_input_verified':g['sealed_input_verified'],'check_returncode':r.returncode,'check_stdout':r.stdout.strip(),'reports_keys':sorted(g['reports'])}
    out['PASS']=out['recount_rc']==0 and out['relabelled']['recount_rc']==0 and out['relabelled']['check_returncode']==0 and out['relabelled']['sealed_input_verified']
    out['note']='PASS here means the tooling ran end to end on a sealed block (recount reproduces, gates reproduce); the reference result is recorded, not required (it may be undecided on smoke)'
    write_new(OUT,out);print(json.dumps(out,default=str)[:4000]);return 0 if out['PASS'] else 1


if __name__=='__main__':sys.exit(main())
