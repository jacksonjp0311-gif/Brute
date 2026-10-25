"""Brute v0.4.0 learner: v0.3.0 certification (Y1k) and LU-R lookahead with a recalibrated, resumable alarm.

Pre-registered in experiments/BRUTE_PLAN_006.json (alarm_rule, arms, candidate_rules). New file; brute/core/*,
fallback.py, active.py and changepoint.py are subclassed, never edited.

Resume rule (alarm_rule.resume). The residual alarm (residual > tau6, tau6 calibrated on in-family data only) withholds
certification as in v0.3.0. While it is set, consecutive observe() steps with residual <= tau6 are counted; after W of
them, with the <=4 family and the <=5 margin both still supported, the alarm clears and certification may resume from
the next predict. A new residual > tau6 sets it again. Contradiction is never resumed. Attestation is never re-enabled:
the frozen v0.1.1 learner already drops it at the first alarm, so after a resume certificates are conditional only.

Candidate rules (arms D2, F2; predicted unsound in the plan): `depth=2` scores LU2-R (one more lookahead level);
`fibre_w=2` certifies on the 2-step fibre F2 (states reachable from the observation t-2 through the recorded steps).
"""
from __future__ import annotations
from dataclasses import replace
from bgr90.symbolic import ALL,mask_for_observation
from brute.core.learner import Status
from brute.active import ActiveBruteLearner,_copy_update
from brute.changepoint import ChangePointBruteLearner,Reason030

RESUME_RULE='alarm clears after W consecutive residuals <= tau6 with family and margin supported; attestation never re-enabled'


def fibre_union(learner,action,masks,acts):
    """Union of successor codes for `action` over the fibre of `learner` over observation masks `masks` (oldest
    first) joined by `acts`. Unknown edges are open only at the current state (Y1k convention). One mask = Y1k."""
    if learner.status!='supported':return None
    u=0
    for p in learner.belief:
        F={j for j in range(p.used) if p.masks[j]&masks[0]}
        for a,m in zip(acts,masks[1:]):
            F={t for j in F for t in (p.trans[j*2+a],) if t>=0 and p.masks[t]&m}
        for j in F:
            d=p.trans[j*2+action]
            if d>=0:u|=p.masks[d]
            elif j==p.current:
                for k in range(p.used):u|=p.masks[k]
                if p.used<learner.max_states:u|=ALL
        if u==ALL:return (0,1,2,3)
    return tuple(c for c in range(4) if u>>c&1)


class ResumeBruteLearner(ChangePointBruteLearner):
    """v0.4.0 (A4/P4): Y1k + LU-R + tau6 + resume. depth/fibre_w select the D2/F2 candidate rules."""
    resume=True
    depth=1
    fibre_w=0

    def __init__(self,*args,resume=None,depth=None,fibre_w=None,**kwargs):
        super().__init__(*args,**kwargs)
        if resume is not None:self.resume=bool(resume)
        if depth is not None:self.depth=int(depth)
        if fibre_w is not None:self.fibre_w=int(fibre_w)
        if self.depth not in (1,2) or self.fibre_w not in (0,2):raise ValueError('depth in {1,2}, fibre_w in {0,2}')
        self._run=0;self.first_alarm_step=None;self.alarm_steps=[];self.resume_steps=[]

    # ---- alarm with resume -------------------------------------------------------------------------------------
    def observe(self,action,obs):
        was=self.alarm_step
        s=super().observe(action,obs)
        if was is None and self.alarm_step is not None:
            self.alarm_steps.append(self.alarm_step);self._run=0
            if self.first_alarm_step is None:self.first_alarm_step=self.alarm_step
        elif self.resume and was is not None and self.alarm_step is not None:
            self._run=self._run+1 if (self.residual is not None and self.residual<=self.tau) else 0
            if self._run>=self.window and self.support.status=='supported' and self.margin.status=='supported':
                self.alarm_step=None;self._run=0;self.resume_steps.append(self.steps)
        return s

    @property
    def resumes(self):return len(self.resume_steps)

    # ---- certification on the w-step fibre -------------------------------------------------------------------
    def _hist(self):
        ev=self.support.evidence;tail=ev[-(self.fibre_w+1):]
        return [mask_for_observation(o) for _,o in tail],[a for a,_ in tail[1:]]

    def _ext(self,hist,a,c):
        masks,acts=hist;masks=(masks+[1<<c])[-(self.fibre_w+1):];acts=acts+[a]
        return masks,(acts[len(acts)-(len(masks)-1):] if len(masks)>1 else [])

    def predict(self,action):
        if self.fibre_w==0:return super().predict(action)
        f=ActiveBruteLearner.predict(self,action)
        if f.certificate is not None and fibre_union(self.support,action,*self._hist())!=(f.certificate,):
            return replace(f,status=Status.ABSTAIN,reason=Reason030.RESYNC_AMBIGUOUS,certificate=None,
                           public_certificate=None,public_reason=None)
        return f

    # ---- lookahead ----------------------------------------------------------------------------------------------
    def _count(self,fam,mar_src,a,c,hist):
        """LU-R count on the family copy `fam` (already updated with (a,c)); returns (count, margin copy or None)."""
        if fam is None:return 0,None
        self.lookahead_peak_rows=max(self.lookahead_peak_rows,fam.count)
        if all(p.used==fam.max_states for p in fam.belief):return 0,None
        singles={b:fam.predict_support(b) for b in (0,1)}
        singles={b:s for b,s in singles.items() if s and len(s)==1 and fibre_union(fam,b,*hist)==s}
        mar,hit=_copy_update(mar_src,a,c);self.lookahead_budget_hits+=hit;self.lookahead_copies+=1
        if mar is not None:self.lookahead_peak_rows=max(self.lookahead_peak_rows,mar.count)
        if not singles or mar is None:return 0,mar
        return sum(mar.predict_support(b)==s for b,s in singles.items()),mar

    def experiment_score(self,action):
        if self.depth==1 and self.fibre_w==0:return super().experiment_score(action)
        if self.support.status!='supported' or self.margin.status!='supported' or self.alarm_step is not None:return 0.
        S=self.support.predict_support(action);h0=self._hist();tot=0.
        for c in S:
            fam,hit=_copy_update(self.support,action,c);self.lookahead_budget_hits+=hit;self.lookahead_copies+=1
            h1=self._ext(h0,action,c);n1,mar=self._count(fam,self.margin,action,c,h1);v=n1
            if self.depth==2 and fam is not None and mar is not None:
                best=0.
                for a2 in (0,1):
                    S2=fam.predict_support(a2);t=0.
                    for c2 in S2:
                        f2,hit=_copy_update(fam,a2,c2);self.lookahead_budget_hits+=hit;self.lookahead_copies+=1
                        n2,_=self._count(f2,mar,a2,c2,self._ext(h1,a2,c2));t+=n2
                    if S2:best=max(best,t/len(S2))
                v+=best
            tot+=v
        return round(tot/len(S),12)

    def retry(self,family_states=None,max_prefixes=None):
        """Replay all evidence under a new bound with the same class and settings. Attestation never carries over."""
        new=type(self)(family_states or self.family_states,max(self.margin_states,(family_states or self.family_states)+1),
                       max_prefixes or self.support.max_prefixes,self.margin.max_prefixes,
                       self.smoothing,self.epsilon,self.window,self.tau,None,resync=self.resync,check_run=self.check_run,
                       resume=self.resume,depth=self.depth,fibre_w=self.fibre_w)
        ev=self.support.evidence;new.initialize(ev[0][1])
        for a,obs in ev[1:]:new.observe(a,obs)
        return new

    def diagnostics(self):
        d=super().diagnostics()
        d.update({'resume':self.resume,'depth':self.depth,'fibre_w':self.fibre_w,'first_alarm_step':self.first_alarm_step,
                  'alarm_steps':list(self.alarm_steps),'resume_steps':list(self.resume_steps),'resumes':self.resumes})
        return d
