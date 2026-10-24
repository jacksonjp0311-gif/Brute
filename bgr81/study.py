import json,hashlib,sys
from pathlib import Path
from bgr81.epistemic import run
from bgr81.reachability import analyze
ROOT=Path(__file__).resolve().parents[1]
def execute():
    out=ROOT/'results';out.mkdir(exist_ok=True)
    if (out/'CASES.json').exists():raise RuntimeError('study cannot overwrite evidence')
    cases=[];reach=[]
    for family in ('logic','switching','navigation','mixed'):
        for seed in range(99101,99113):
            reach.append(analyze(seed,family))
            for policy in ('epistemic','active','random','cyclic'):
                cases.append(run(seed,family,policy,steps=120))
    (out/'CASES.json').write_text(json.dumps(cases,sort_keys=True,separators=(',',':'))+'\n')
    (out/'REACHABILITY.json').write_text(json.dumps(reach,sort_keys=True,indent=2)+'\n')
    stats={p:{'identified':sum(x['identified'] for x in cases if x['policy']==p),
              'certified':sum(x['certified'] for x in cases if x['policy']==p),
              'incorrect':sum(x['incorrect'] for x in cases if x['policy']==p)}
           for p in ('epistemic','active','random','cyclic')}
    summary={'schema':'bgr81.study.v1','worlds':48,'policy_runs':192,'actions':23040,
             'summary':stats,'oracle_reachable_identifiable':sum(x['reachable_oracle_identified'] for x in reach),
             'reachable_state_fraction_mean':sum(x['reachable_states']/x['total_states'] for x in reach)/48,
             'cases_sha256':hashlib.sha256((out/'CASES.json').read_bytes()).hexdigest(),
             'reachability_sha256':hashlib.sha256((out/'REACHABILITY.json').read_bytes()).hexdigest()}
    (out/'SUMMARY.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))
if __name__=='__main__':execute()
