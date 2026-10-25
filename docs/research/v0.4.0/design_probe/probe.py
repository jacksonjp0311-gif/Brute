"""Design probe for v0.4.0 on study-004 and study-005 seeds (DESIGN DATA; never used for a v0.4.0 claim).

Candidate rules: Fw = certificate constant on the fibre over the last w+1 observations (w=0 is v0.3.0 Y1k), and
lookahead depth 1 (LU-R with Fw) or 2 (LU2-R with Fw). Output: outputs/probe_<tag>.json, per step
(step, action, cert, actual, cf_cert, cf_actual, reason).
"""
import sys,json,argparse
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from dataclasses import replace
from bgr89.worlds import world as old_world,actions
from bgr90.worlds import world as new_world,step as new_step
from bgr90.symbolic import ALL,mask_for_observation
from brute.core.learner import Status
from brute.active import ActiveBruteLearner,_copy_update
from brute.changepoint import ChangePointBruteLearner,Reason030
P4=json.load(open(ROOT/'experiments/BRUTE_PLAN_004.json'));P5=json.load(open(ROOT/'experiments/BRUTE_PLAN_005.json'))


def fibre_union(learner,b,masks,acts,strict=False):
    """masks = last w+1 observation masks (oldest first), acts = the w actions between them."""
    if learner.status!='supported':return None
    u=0
    for p in learner.belief:
        F={j for j in range(p.used) if p.masks[j]&masks[0]}
        for a,m in zip(acts,masks[1:]):
            F={t for j in F for t in (p.trans[j*2+a],) if t>=0 and p.masks[t]&m}
        for j in F:
            d=p.trans[j*2+b]
            if d>=0:u|=p.masks[d]
            elif strict or j==p.current:
                for k in range(p.used):u|=p.masks[k]
                if p.used<learner.max_states:u|=ALL
        if u==ALL:return (0,1,2,3)
    return tuple(c for c in range(4) if u>>c&1)


class FwLearner(ChangePointBruteLearner):
    w=0;depth=1;resume=False;strict=False;_run=0;resumes=0
    def observe(self,action,obs):
        was=self.alarm_step
        s=super().observe(action,obs)
        if self.resume and was is not None and self.alarm_step is not None:
            self._run=self._run+1 if (self.residual is not None and self.residual<=self.tau) else 0
            if self._run>=self.window and self.support.status=='supported' and self.margin.status=='supported':
                self.alarm_step=None;self._run=0;self.resumes+=1
        return s
    def _hist(self,extra=None):
        ev=self.support.evidence;k=self.w
        tail=ev[-(k+1):] if len(ev)>=k+1 else ev
        masks=[mask_for_observation(o) for _,o in tail];acts=[a for a,_ in tail[1:]]
        if extra is not None:
            a,c=extra;masks=(masks+[1<<c])[-(k+1):];acts=(acts+[a])[-k:] if k else []
            if len(acts)>len(masks)-1:acts=acts[len(acts)-(len(masks)-1):]
        return masks,acts
    def predict(self,action):
        f=ActiveBruteLearner.predict(self,action)
        if f.certificate is not None:
            m,a=self._hist()
            if fibre_union(self.support,action,m,a,self.strict)!=(f.certificate,):
                return replace(f,status=Status.ABSTAIN,reason=Reason030.RESYNC_AMBIGUOUS,certificate=None,public_certificate=None,public_reason=None)
        return f
    def _N(self,fam,mar_src,a,c,hist):
        """certifiable count after the copy fam (already updated with (a,c)); hist=(masks,acts) incl. (a,c)."""
        if fam is None:return 0,None
        if all(p.used==fam.max_states for p in fam.belief):return 0,None
        singles={b:fam.predict_support(b) for b in (0,1)}
        singles={b:s for b,s in singles.items() if s and len(s)==1 and fibre_union(fam,b,*hist,self.strict)==s}
        mar,hit=_copy_update(mar_src,a,c);self.lookahead_budget_hits+=hit;self.lookahead_copies+=1
        if not singles or mar is None:return 0,mar
        return sum(mar.predict_support(b)==s for b,s in singles.items()),mar
    def _ext(self,hist,a,c):
        masks,acts=hist;k=self.w
        masks=(masks+[1<<c])[-(k+1):];acts=(acts+[a])
        acts=acts[len(acts)-(len(masks)-1):] if len(masks)>1 else []
        return masks,acts
    def experiment_score(self,action):
        if self.support.status!='supported' or self.margin.status!='supported' or self.alarm_step is not None:return 0.
        S=self.support.predict_support(action);h0=self._hist();tot=0.
        for c in S:
            fam,hit=_copy_update(self.support,action,c);self.lookahead_budget_hits+=hit;self.lookahead_copies+=1
            h1=self._ext(h0,action,c)
            n1,mar=self._N(fam,self.margin,action,c,h1)
            v=n1
            if self.depth==2 and fam is not None and mar is not None:
                best=0.
                for a2 in (0,1):
                    S2=fam.predict_support(a2);t=0.
                    for c2 in S2:
                        f2,hit=_copy_update(fam,a2,c2);self.lookahead_budget_hits+=hit;self.lookahead_copies+=1
                        n2,_=self._N(f2,mar,a2,c2,self._ext(h1,a2,c2));t+=n2
                    best=max(best,t/len(S2))
                v+=best
            tot+=v
        return round(tot/len(S),12)


def make(w,depth,tau=None,resume=False,strict=False):
    cls=type('L',(FwLearner,),{'w':w,'depth':depth,'resume':resume,'strict':strict})
    p=P5;return cls(p['family_state_cap'],p['margin_state_cap'],p['row_budget_family'],p['row_budget_margin'],
               p['prediction_smoothing'],p['open_world_reserve_epsilon'],p['residual_surprise']['window_W'],tau or p['residual_surprise']['tau'],None)


def traj(seed,fam,mask,w,depth,active,tau=None,resume=False,strict=False):
    truth=(new_world if fam in('ood5','drift4') else old_world)(seed,fam)
    h=truth.start;init=truth.observed(h,mask,-1);L=make(w,depth,tau,resume,strict);L.initialize(init);out=[]
    for i,pa in enumerate(actions(seed,44)):
        e=L.experiment(pa) if active else None
        a=e['action'] if e else pa
        fs=(L.predict(0),L.predict(1))
        nxt=[new_step(truth,h,b,i) if fam=='drift4' else truth.next(h,b) for b in (0,1)]
        act=[truth.emission(x) for x in nxt];h=nxt[a];obs=truth.observed(h,mask,i)
        out.append((i+1,a,fs[a].certificate,act[a],fs[1-a].certificate,act[1-a],fs[a].reason.value if fs[a].reason else None))
        L.observe(a,obs)
    return out


def job(x):
    seed,fam,mask,arms=x
    return seed,fam,mask,{tag:traj(seed,fam,mask,*spec) for tag,spec in arms.items()}


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--arms',required=True);ap.add_argument('--tag',required=True)
    ap.add_argument('--studies',default='004,005');ap.add_argument('--families',default=None)
    ap.add_argument('--seeds',type=int,default=24);ap.add_argument('--workers',type=int,default=8);a=ap.parse_args()
    arms=json.loads(a.arms);jobs=[]
    for st in a.studies.split(','):
        R=(P4 if st=='004' else P5)['heldout_ranges']
        for f in (a.families.split(',') if a.families else list(R)):
            for s in range(R[f][0],R[f][0]+a.seeds):
                for m in P5['mask_rates']:jobs.append((s,f,m,arms))
    with ProcessPoolExecutor(a.workers) as ex:res=list(ex.map(job,jobs,chunksize=1))
    json.dump(res,open(Path(__file__).parent/f'outputs/probe_{a.tag}.json','w'))
    print('done',len(res))
