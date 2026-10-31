"""Pre-plan diagnosis for BRUTE_PLAN_040: why did the study-039 scale16 / scale14 cases end IDU? Reads the sealed
results/study-039/main/RESULTS.json (seal-checked) only; writes results/diag-040/DIAG_039_IDU.json. New file.
Per IDU case and arm: actions used vs K, case wall vs budget, capped queries, and which query was unknown in the last
round ('least' = least consistent machine, 'future' / 'start' = rival search). A cause is 'query_cap' if the last round
has a capped query, 'case_budget' if the arm wall reached the budget without a capped query, 'actions' if stop is K_spent.
  PYTHONPATH=. python scripts/diag_039_idu.py"""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common import sha,load,write_new,check

D=ROOT/'results/study-039/main';OUT=ROOT/'results/diag-040/DIAG_039_IDU.json'
BUDGET={'A14':240.0,'A14_k64':120.0,'A9':120.0,'A14_random':240.0};K={'A14':128,'A14_k64':64,'A9':64}


def phase(a):
    rs=a.get('rounds')
    if not rs:return 'stop_check'
    x=rs[-1]
    if x.get('n_min') is None:return 'least'
    f=x.get('future') or {}
    if f.get('unknown'):return 'future'
    return 'start'


def main():
    seal=load(D/'SEAL.json');check(sha(D/'RESULTS.json')==seal['results_sha256'],'RESULTS does not match its seal')
    R=load(D/'RESULTS.json');out={'source_results_sha256':seal['results_sha256'],'per_arm_key':{},'cases':[]}
    for c in R['cases']:
        if c['key'] not in ('scale16','scale14'):continue
        for arm,a in c['arms'].items():
            if a['label']!='IDU':continue
            last_capped=(a['rounds'][-1]['capped']>0) if a.get('rounds') else a.get('capped',0)>0
            wall=a['arm_wall_informational'];bud=BUDGET[arm]
            cause='actions' if a['stop']=='K_spent' else ('query_cap' if last_capped else ('case_budget' if wall>=bud-1 else 'other'))
            row={'key':c['key'],'seed':c['seed'],'arm':arm,'stop':a['stop'],'used':a['used'],'K':K.get(arm),'wall_s':round(wall,1),
                 'budget_s':bud,'capped_queries':a.get('capped'),'query_max_s':round(a['query_max_s'],3),'last_phase':phase(a),
                 'rounds':a.get('n_rounds'),'cause':cause}
            out['cases'].append(row);g=out['per_arm_key'].setdefault(f"{arm}/{c['key']}",{'IDU':0,'cause':{},'last_phase':{},'max_used':0,'max_wall_s':0})
            g['IDU']+=1;g['cause'][cause]=g['cause'].get(cause,0)+1;g['last_phase'][row['last_phase']]=g['last_phase'].get(row['last_phase'],0)+1
            g['max_used']=max(g['max_used'],a['used']);g['max_wall_s']=max(g['max_wall_s'],row['wall_s'])
            g['zero_action_cases']=g.get('zero_action_cases',0)+(a['used']==0)
    OUT.parent.mkdir(parents=True,exist_ok=True);write_new(OUT,out);print(json.dumps(out['per_arm_key'],indent=1))


if __name__=='__main__':main()
