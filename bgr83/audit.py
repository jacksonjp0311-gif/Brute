"""Independent teacher transition replay and learner certificate check."""
import json,hashlib
from pathlib import Path
from collections import deque
from bgr60.worlds import factory
from bgr60.generalist import GeneralLearner
ROOT=Path(__file__).resolve().parents[1]
def audit():
 p=ROOT/'results/STUDY.json';seal=json.loads((ROOT/'results/SEAL.json').read_text())
 assert hashlib.sha256(p.read_bytes()).hexdigest()==seal['study_sha256']
 data=json.loads(p.read_text());summary={}
 for r in data['records']:
  w=factory(r['seed'],r['family']);schema,actions=w.public();l=GeneralLearner(schema,actions)
  assert len(r['trace'])==r['steps']
  for i,e in enumerate(r['trace']):
   b=tuple(e['before']);n=tuple(e['after']);a=e['action']
   if i:assert b==tuple(r['trace'][i-1]['after'])
   assert n==w.transition(a,b)
   l.observe(a,b,n)
  visited={tuple(r['trace'][0]['before'])};q=deque(visited)
  while q:
   s=q.popleft()
   for a in range(len(actions)):
    t=w.transition(a,s)
    if t not in visited:visited.add(t);q.append(t)
  correct=wrong=0
  for s in visited:
   for a in range(len(actions)):
    pred=l.certified(a,s)
    if pred is not None:correct+=1;wrong+=pred!=w.transition(a,s)
  assert (correct,wrong,len(visited)*len(actions))==(r['certified'],r['incorrect'],r['reachable_total'])
  assert l.identified()==r['global_identified']
  s=summary.setdefault(r['policy'],{'worlds':0,'reachable_complete':0,'certified':0,'reachable_total':0,'incorrect':0,'candidate_checks':0})
  s['worlds']+=1;s['reachable_complete']+=int(correct==len(visited)*len(actions));s['certified']+=correct;s['reachable_total']+=len(visited)*len(actions);s['incorrect']+=wrong;s['candidate_checks']+=l.candidate_checks
 assert summary==data['summary']
 report={'status':'passed','cases':len(data['records']),'actions_replayed':sum(len(x['trace']) for x in data['records']),'summary':summary,'scope':'teacher replay and same-implementation learner reconstruction, not an independent learner algorithm'}
 (ROOT/'results/AUDIT.json').write_text(json.dumps(report,indent=2)+'\n')
 print('audit passed:',report['cases'],'cases',report['actions_replayed'],'actions')
if __name__=='__main__':audit()
