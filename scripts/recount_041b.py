"""GRR041 (BRUTE_PLAN_042 part0_rerecount; pre-run deviation #157): the frozen 041 recount re-applied to the sealed 041 study with
one added rule, the AMB-at-stop rule of scripts/recount_042.py (an AMB stop is valid iff the stored future list ends SAT at n* and
the independent plain-CNF reference finds a rival of size n*, consistent with the trace, whose future differs from the returned
model's). Reported only; it changes no 041 gate and edits nothing under results/study-041.
Writes results/diag-042/RECOUNT_041B.json (refuses overwrite).
  PYTHONPATH=. python scripts/recount_041b.py [out.json]"""
import gzip,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common import write_new,sha
from scripts.recount_041 import recount_case
from scripts.recount_042 import recount_replay042
SRC=ROOT/'results/study-041/main/RESULTS.json.gz';OUT=ROOT/'results/diag-042/RECOUNT_041B.json'


def main(argv=None):
    argv=sys.argv[1:] if argv is None else argv;out_p=Path(argv[0]) if argv else OUT
    res=json.load(gzip.open(SRC));rp={};bad={};per={};before={};after={};changed=[]
    old=json.load(open(ROOT/'results/study-041/main/RECOUNT_041.json'))
    for r in res['replays']:
        k=f"replay/{r['part']}/{r['study']}/{r['key']}/{r['seed']}/{r['variant']}/{r['repeat']}";rp[k],b=recount_replay042(r)
        if b:bad[k]=b
        o=old['per_replay'].get(k,{}).get('label');before[o]=before.get(o,0)+1;after[rp[k]['label']]=after.get(rp[k]['label'],0)+1
        if o!=rp[k]['label']:changed.append([k,o,rp[k]['label']])
    for c in res.get('cases',[]):
        k=f"{c['block']}/{c['key']}/{c['seed']}";per[k],b=recount_case(c)
        if b:bad[k]=b
    out={'schema':'brute.recount041b.v39_0','source':str(SRC.relative_to(ROOT)),'source_sha256':sha(SRC),'replays':len(rp),'cases':len(per),
         'frozen_041_mismatching':old['mismatching_cases'],'mismatching_cases':len(bad),'mismatches':bad,
         'replay_labels_frozen_rule':before,'replay_labels_amb_rule':after,'relabelled':changed,
         'amb_rule_applied':sum('amb_rule' in v for v in rp.values()),
         'note':'GRR041 is reported only (secondary); it changes no 041 gate'}
    write_new(out_p,out);print(json.dumps({k:v for k,v in out.items() if k not in ('relabelled',)},default=str));return 0


if __name__=='__main__':sys.exit(main())
