"""Full design probe for policy LP on all study-003 seeds (design data). Checks counterfactual-action certificates."""
import sys,json,time
import probe,probe3
from probe import *
def run5(seed,fam,rate,policy):
    truth=(new_world if fam in('ood5','drift4') else old_world)(seed,fam)
    att=ScopeAttestation(PLAN['declared_family'],'e','e') if fam in PLAN['in_family'] else None
    L=FallbackBruteLearner(4,5,160000,160000,.08,.02,8,TAU,att)
    h=truth.start;L.initialize(truth.observed(h,rate,-1));pas=actions(seed,44);out=[]
    for i in range(44):
        a=probe.choose(L,policy,pas[i]);fs=(L.predict(0),L.predict(1))
        nxt=[(new_step(truth,h,b,i) if fam=='drift4' else truth.next(h,b)) for b in (0,1)]
        em=[truth.emission(x) for x in nxt]
        h=nxt[a];obs=truth.observed(h,rate,i);L.observe(a,obs)
        out.append(dict(step=i+1,a=a,agree=a==pas[i],cert=fs[a].certificate is not None,wrong=fs[a].certificate is not None and fs[a].certificate!=em[a],
            dual=sum(f.certificate is not None for f in fs),dual_wrong=sum(f.certificate is not None and f.certificate!=em[b] for b,f in enumerate(fs)),
            ll=loss(fs[a].probabilities,em[a]),drift=fam=='drift4' and (i+1) in (12,23,34),reason=fs[a].reason.value if fs[a].reason else None))
    return out,L.support.max_rows_seen,L.margin.max_rows_seen,L.alarm_step is not None
def _main():
  fam=sys.argv[1];pols=sys.argv[2].split(',');lo,hi=PLAN['heldout_ranges'][fam];res={}
  for pol in pols:
      t=time.time();recs=[];peak=[0,0];al=0;percase=[]
      for seed in range(lo,hi+1):
          for rate in PLAN['mask_rates']:
              o,pf,pm,a=run5(seed,fam,rate,pol);recs+=o;peak=[max(peak[0],pf),max(peak[1],pm)];al+=a
              post=[r for r in o if r['step']>8];percase.append(sum(r['dual'] for r in post)/2/len(post))
      post=[r for r in recs if r['step']>8]
      res[pol]=dict(on=round(sum(r['cert'] for r in post)/len(post),4),dual=round(sum(r['dual'] for r in post)/2/len(post),4),
        wrong=sum(r['wrong'] for r in recs),wrong_nondrift=sum(r['wrong'] and not r['drift'] for r in recs),
        dual_wrong=sum(r['dual_wrong'] for r in recs),dual_wrong_nondrift=sum(r['dual_wrong'] for r in recs if not r['drift']),
        ll=round(sum(r['ll'] for r in post)/len(post),4),peak=peak,alarm_cases=al,cases=len(percase),
        agree=round(sum(r['agree'] for r in post)/len(post),4),min_case_dual=round(min(percase),4),secs=round(time.time()-t,1))
  print(fam,json.dumps(res),flush=True)
if __name__=='__main__':_main()
