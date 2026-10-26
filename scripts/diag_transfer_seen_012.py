"""EXPLORATORY (seen data, not evidence): the frozen TR rule of BRUTE_PLAN_012 recomputed by experiments/v0100_reference
on the sealed study-011 SP8 traces of cycle3/switch3/unaliased2/ood4, libraries from smoke source seeds 5190021-5190030."""
import json,collections,statistics as S,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.v0100_reference import ref_tr_arm,ref_library
ROT={'cycle3':'switch3','switch3':'cycle3','unaliased2':'ood4','ood4':'unaliased2'}
d=json.load(open(ROOT/'results/study-011/2x2/RESULTS.json'));rows=collections.defaultdict(lambda:{'S':[],'false':0,'cases_with_false':0,'disabled':0})
for c in d['cases']:
    f=c['family']
    if f not in ROT:continue
    sp=next((r['step'] for r in c['arms']['SP8']['trace'] if r['certificate'] is not None),45)
    for lab,sf in (('TRp',f),('TRn',ROT[f])):
        o=ref_tr_arm(c,ref_library(sf,5190021+c['seed']%10),lab);x=rows[f'{f}/{lab}']
        x['S'].append(sp-o['first_cert_step']);x['false']+=o['false_certificates'];x['cases_with_false']+=o['false_certificates']>0;x['disabled']+=o['disabled_step'] is not None
out={'label':'EXPLORATORY seen data (study-011 sealed traces); not v0.10.0 evidence; frozen plan unchanged','rows':{}}
for k,x in sorted(rows.items()):out['rows'][k]={'cases':len(x['S']),'mean_S':round(S.mean(x['S']),3),'false_certificates':x['false'],'cases_with_false':x['cases_with_false'],'disabled_cases':x['disabled']}
Path(ROOT/'results/diag-012').mkdir(exist_ok=True);(ROOT/'results/diag-012/TRANSFER_DIAG_SEEN.json').write_text(json.dumps(out,indent=1)+'\n')
print(json.dumps(out,indent=1))
