import json,hashlib
from pathlib import Path
from bgr83.frontier import run
ROOT=Path(__file__).resolve().parents[1]
FAMILIES=('logic','switching','navigation','mixed','incompatible')
POLICIES=('frontier','random','active')
def study():
 records=[run(83000+i+1000*j,f,p,120) for j,f in enumerate(FAMILIES) for i in range(10) for p in POLICIES]
 summary={}
 for p in POLICIES:
  group=[r for r in records if r['policy']==p]
  summary[p]={'worlds':len(group),'reachable_complete':sum(r['reachable_complete'] for r in group),'certified':sum(r['certified'] for r in group),'reachable_total':sum(r['reachable_total'] for r in group),'incorrect':sum(r['incorrect'] for r in group),'candidate_checks':sum(r['candidate_checks'] for r in group)}
 result={'study':'BGR-083-NORESET-001','design':'50 unseen synthetic worlds; three policies; 120 no-reset actions per run','summary':summary,'records':records,'limitations':['worlds share supplied typed schema and local-function grammar','reachable set is evaluator-only oracle','same-world policy runs are paired, not independent worlds','no positive transfer or AGI established']}
 out=ROOT/'results';out.mkdir(exist_ok=True)
 payload=json.dumps(result,sort_keys=True,separators=(',',':')).encode();(out/'STUDY.json').write_bytes(payload)
 (out/'SEAL.json').write_text(json.dumps({'study_sha256':hashlib.sha256(payload).hexdigest(),'cases':len(records)},indent=2)+'\n')
 print(json.dumps(summary,indent=2))
if __name__=='__main__':study()
