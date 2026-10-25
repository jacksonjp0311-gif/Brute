"""Design probe for v0.2.0 (scratch, NOT product code). Runs on study-003 seeds (design data)."""
import sys,json,math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from bgr89.worlds import world as old_world,actions
from bgr90.worlds import world as new_world,step as new_step
from bgr90.symbolic import SymbolicLearner,ALL
from brute.fallback import FallbackBruteLearner
from brute.core.learner import ScopeAttestation
from brute.evaluation import loss
from bgr89.baselines import SuffixFrequency
PLAN=json.load(open(ROOT/'experiments/BRUTE_PLAN_003.json'))
TAU=PLAN['residual_surprise']['tau']

def row_mask(p,a,cap):
    d=p.trans[p.current*2+a]
    if d>=0:return p.masks[d]
    u=0
    for j in range(p.used):u|=p.masks[j]
    if p.used<cap:u|=ALL
    return u

def entropy(learner,a):
    if learner.status!='supported' or not learner.belief:return 0.
    w=[0.]*4
    for p in learner.belief:
        m=row_mask(p,a,learner.max_states);cs=[c for c in range(4) if m>>c&1];
        for c in cs:w[c]+=1/len(cs)
    z=sum(w);return -sum(x/z*math.log(x/z) for x in w if x>0)

def supsize(learner,a):
    s=learner.predict_support(a);return len(s) if s else 0

def choose(L,policy,passive_a):
    if policy=='passive':return passive_a
    if policy=='H':
        sc=[round(entropy(L.support,a)+entropy(L.margin,a),12) for a in (0,1)]
    elif policy=='S':
        sc=[supsize(L.support,a)+supsize(L.margin,a) for a in (0,1)]
    if sc[0]==sc[1]:return passive_a
    return 0 if sc[0]>sc[1] else 1

class Win:
    """window rebuild after contradiction: fresh <=cap learner restarted at each contradiction"""
    def __init__(self,cap):self.cap=cap;self.l=None;self.restarts=0
    def start(self,obs):self.l=SymbolicLearner(self.cap,160000);self.l.initialize(obs);self.restarts+=1
    def observe(self,a,obs):
        self.l.observe(a,obs)
        if self.l.status!='supported':self.start(obs)

def run(seed,fam,rate,policy,wincap=4):
    truth=(new_world if fam in('ood5','drift4') else old_world)(seed,fam)
    att=ScopeAttestation(PLAN['declared_family'],'e','e') if fam in PLAN['in_family'] else None
    L=FallbackBruteLearner(4,5,160000,160000,.08,.02,8,TAU,att)
    h=truth.start;init=truth.observed(h,rate,-1);L.initialize(init)
    W=Win(wincap);sfx=SuffixFrequency(1,.7);sfx.initialize(init)
    pas=actions(seed,44);out=[]
    for i in range(44):
        a=choose(L,policy,pas[i])
        f0=L.predict(0);f1=L.predict(1);f=(f0,f1)[a]
        # window tier probabilities
        pw=None;src=f.forecast_source
        if L.support.status=='grammar_contradicted' and not (L.margin.status=='supported' and f.margin_support):
            s=W.l.predict_support(a) if W.l and W.l.status=='supported' else None
            q=sfx.predict(a)
            if s:
                z=sum(q[c] for c in s);r=[q[c]/z if c in s else 0 for c in range(4)]
                pw=tuple(.98*x+.005 for x in r)
            else:pw=tuple(.98*x+.005 for x in q)
        h=new_step(truth,h,a,i) if fam=='drift4' else truth.next(h,a)
        act=truth.emission(h);obs=truth.observed(h,rate,i)
        was=L.support.status
        L.observe(a,obs);sfx.observe(a,obs)
        if was=='supported' and L.support.status=='grammar_contradicted':W.start(obs)
        elif W.l is not None:W.observe(a,obs)
        out.append(dict(step=i+1,a=a,cert=f.certificate,wrong=f.certificate is not None and f.certificate!=act,
          dual=(f0.certificate is not None)+(f1.certificate is not None),
          dual_wrong=sum(g.certificate is not None and g.certificate!=act for g in ()),
          ll=loss(f.probabilities,act),llw=loss(pw,act) if pw else loss(f.probabilities,act),
          status=f.status.value,reason=f.reason.value if f.reason else None,alarm=L.alarm_step is not None,
          drift=fam=='drift4' and (i+1) in (12,23,34)))
    return out,max(L.support.max_rows_seen,0),L.margin.max_rows_seen,L.alarm_step is not None

if __name__=='__main__':
    fam=sys.argv[1];pols=sys.argv[2].split(',')
    lo,hi=PLAN['heldout_ranges'][fam];res={}
    for pol in pols:
        recs=[];peak=[0,0];alarms=0;n=0
        for seed in range(lo,hi+1):
            for rate in PLAN['mask_rates']:
                o,pf,pm,al=run(seed,fam,rate,pol);n+=1
                recs+= [dict(r,seed=seed,rate=rate) for r in o];peak=[max(peak[0],pf),max(peak[1],pm)];alarms+=al
        post=[r for r in recs if r['step']>8]
        res[pol]=dict(on_policy_cov=round(sum(r['cert'] is not None for r in post)/len(post),4),
          dual_cov=round(sum(r['dual'] for r in post)/(2*len(post)),4),
          false_certs=sum(r['wrong'] for r in recs),false_nondrift=sum(r['wrong'] and not r['drift'] for r in recs),
          ll=round(sum(r['ll'] for r in post)/len(post),4),llw=round(sum(r['llw'] for r in post)/len(post),4),
          peak=peak,alarm_cases=alarms,cases=n,
          margin_dis=sum(r['reason']=='MARGIN_DISAGREES' for r in post),possible=sum(r['status']=='POSSIBLE_SET' for r in post))
    print(fam,json.dumps(res))
