"""Replay from independent simulator ground truth; learner itself is shared with run."""
import json,hashlib
from pathlib import Path
from random import Random
from bgr60.worlds import factory
from bgr81.reachability import analyze
ROOT=Path(__file__).resolve().parents[1]
def execute():
 out=ROOT/'results';cases=json.loads((out/'CASES.json').read_text());bounds=json.loads((out/'REACHABILITY.json').read_text())
 assert len(cases)==192 and len(bounds)==48
 checked=0
 for case in cases:
  w=factory(case['seed'],case['family']);schema,_=w.public();rng=Random(case['seed']*931+73)
  state=tuple(rng.choice(d) for d in schema.domains)
  for event in case['trace']:
   assert tuple(event['before'])==state
   state=w.transition(event['action'],state)
   assert tuple(event['after'])==state
   checked+=1
  assert case['incorrect']==0
 for entry in bounds:
  assert entry==analyze(entry['seed'],entry['family'])
 result={'status':'passed','replayed_actions':checked,'reachable_oracle_worlds_checked':len(bounds),
         'limitations':'transition replay and reachable oracle recomputation; not independent posterior implementation',
         'cases_sha256':hashlib.sha256((out/'CASES.json').read_bytes()).hexdigest()}
 (out/'AUDIT.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
if __name__=='__main__':execute()
