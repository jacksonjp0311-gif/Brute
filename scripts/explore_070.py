"""EXPLORATORY, NOT GATED (post-hoc, written after the study-070 seal; see docs/research/BRUTE_DEVIATIONS_070_210.md).
The frozen gates (scripts/make_gates_070.py) correctly mark every data gate INCOMPLETE_INPUT because 7 of 51 main-run jobs were
SIGKILLed by the kernel OOM killer (exit -9) and are absent from RESULTS.json. This script re-evaluates the SAME frozen gate code on
the 44 sealed records only, by restricting the job list to the records present and treating the run as complete. It does not change
any label, record or gate; its output is evidence label Observed (exploratory) and can never certify anything.
  PYTHONPATH=. python scripts/explore_070.py   -> results/study-070/EXPLORATORY_070.json (refuses overwrite)"""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import scripts.make_gates_070 as MG
from experiments.brute_common import load as _load,write_new
OUT=ROOT/'results/study-070/EXPLORATORY_070.json'
R0=_load(MG.M/'RESULTS.json');present=[tuple(x) for x in ((r['target'],r['seed'],r['arm']) for r in R0['records'])]
def load(p):
    d=_load(p)
    if Path(p).name=='RESULTS.json':d=dict(d,complete=True)
    return d
MG.load=load;MG.jobs_for=lambda block:present
r=MG.compute()
out={'EXPLORATORY_NOT_GATED':True,'why':'7 of 51 jobs OOM-killed (exit -9), not retried; frozen gates say not certified',
     'missing_jobs':R0['errors'],'records_used':len(present),
     'gates_on_sealed_records':{k:v for k,v in r['gates'].items() if k not in ('GLIVE70',)},
     'would_fail_on_sealed_records':[k for k in r['failed'] if k!='GLIVE70'],'official_status':'see results/study-070/GATES_070.json'}
if __name__=='__main__':
    write_new(OUT,out);print(json.dumps({k:out[k] for k in ('records_used','would_fail_on_sealed_records')}))
    print(json.dumps(r['gates']['GDEC70']));print(json.dumps(r['gates']['GS70_sound']))
