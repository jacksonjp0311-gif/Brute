"""Pre-freeze smoke-gates test for study-033 (plan 033 process: "pre-freeze gates test on a sealed smoke block"; the #129
lesson). New file. Input: a sealed smoke block written by experiments/brute_study_033.py --block smoke (outside
results/study-033). Runs recount_033 and run_reference_033 on it, builds make_gates_033 on it, then relabels the same cases
block 'main' (seeds unchanged, so no plan seed is touched), re-seals them with the runner's _write (stand-in freeze hash),
recounts, gates and runs make_gates_033 --check in a subprocess. Writes results/diag-033/PREFREEZE_SMOKE_GATES_033.json
(refuses overwrite). Observed only: no gate decision, no tuning.
  PYTHONPATH=. python scripts/prefreeze_smoke_033.py /tmp/smoke"""
import json,subprocess,sys,tempfile
from pathlib import Path
from unittest import mock
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments import brute_study_033 as ST
from experiments.brute_common_033 import load,write_new,PLAN
from scripts import make_gates_033 as MG
from scripts.recount_033 import main as recount
from scripts.run_reference_033 import main as reference
OUT=ROOT/'results/diag-033/PREFREEZE_SMOKE_GATES_033.json'


def status(g):return {k:{'pass':v['pass'],**({'reason':v['reason']} if 'reason' in v else {})} for k,v in g['gates'].items()}


def main(argv=None):
    argv=sys.argv[1:] if argv is None else argv;S=Path(argv[0]);out={'label':'Observed','purpose':__doc__.split('\n')[0]}
    res=load(S/'RESULTS.json');out['smoke_cases']=[(c['family'],c['seed'],{a:c['arms'][a]['label'] for a in ST.ORDER},
        c['arms']['A8']['used'],c['arms']['A8']['stop']) for c in res['cases']]
    out['recount_rc']=recount([str(S)]);rc=load(S/'RECOUNT_033.json');out['recount']={k:rc[k] for k in ('cases','labels','words_checked','words_unsound','mismatching_cases','PASS')}
    out['reference_rc']=reference([str(S),'--workers','2']);rf=load(S/'REFERENCE_033.json')
    out['reference_on_smoke_scale8']={k:rf.get(k) for k in ('cases','decided','not_reached','words_checked','mismatch_count','PASS')}|{'mutations':rf['mutation_test']['detected'],'of':rf['mutation_test']['mutations']}
    with tempfile.TemporaryDirectory() as d:
        sd=Path(d)/'smoke_as_study';(sd/'main').mkdir(parents=True)
        for nm in ('RESULTS.json','SCIENTIFIC.json','SEAL.json','RECOUNT_033.json','REFERENCE_033.json'):(sd/'main'/nm).write_bytes((S/nm).read_bytes())
        g=MG.build(sd);out['smoke_gate_status']=status(g);out['smoke_sealed_input_verified']=g['sealed_input_verified']
        D=Path(d)/'relabelled';(D/'main').mkdir(parents=True);fz=Path(d)/'FREEZE_STANDIN.json';fz.write_text('{}')
        cases=[dict(c,block='main') for c in res['cases']];P=load(PLAN)
        with mock.patch.object(ST,'FREEZE',fz):ST._write(D/'main',P,'main',[f"main/{c['family']}/{c['seed']}" for c in cases],cases,True,{'total_elapsed_informational':res.get('total_elapsed_informational')})
        rr=recount([str(D/'main')]);g=MG.build(D);(D/'GATES_033.json').write_bytes(MG.dumps(g))
        r=subprocess.run([sys.executable,'scripts/make_gates_033.py','--study-dir',str(D),'--check'],cwd=ROOT,capture_output=True,text=True,env={'PYTHONPATH':str(ROOT),'PATH':'/usr/bin:/bin'})
        out['relabelled']={'recount_rc':rr,'crashed':False,'gate_status':status(g),'sealed_input_verified':g['sealed_input_verified'],
                           'check_returncode':r.returncode,'check_stdout':r.stdout.strip(),'reports_keys':sorted(g['reports'])}
    out['PASS']=out['recount_rc']==0 and out['reference_rc']==0 and out['relabelled']['check_returncode']==0 and out['relabelled']['sealed_input_verified']
    write_new(OUT,out);print(json.dumps(out,default=str)[:3000]);return 0 if out['PASS'] else 1


if __name__=='__main__':sys.exit(main())
