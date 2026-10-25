"""Brute -> operator requests. Pure functions of cited trace fields; standard library only.

Triggers (frozen in BRIDGE_PLAN.md):
- CONTRADICTION_NOTICE: first response with reason FAMILY_CONTRADICTED.
- SCOPE_ALERT: OUT_OF_FAMILY/RESIDUAL_SURPRISE; legacy_family_alive true->false; attestation_id non-null->null. Once per kind.
- REQUEST_OBSERVATION: last observe request had a null channel AND the next predict is not CERTIFIED.
- REQUEST_ACTION: a response carries an `experiment` object with tied == false (brute.api/1.2; absent in 1.1).
  The next non-ERROR observe resolves it: 'satisfied' if it used the requested action, else 'overridden'.
  A newer REQUEST_ACTION before that observe marks the older one 'superseded'.
"""
from __future__ import annotations
from .claims import make


class Triggers:
    def __init__(self):
        self.n=0;self.fired=set();self.prev_legacy=None;self.prev_attest=None;self.masked=None
        self.want=None;self.resolutions=[]

    def _req(self,kind,claim):
        if claim is None:return None
        self.n+=1
        return {'request_id':f'q{self.n}','kind':kind,'trace_id':claim['trace_id'],'claims':[claim]}

    def feed(self,tid,traces):
        """Requests triggered by trace `tid` (already stored in `traces`)."""
        tr=traces[tid];q,r=tr['request'],tr['response'];out=[]
        ref=lambda p:f'{tid}#{p}'
        if r['reason']=='FAMILY_CONTRADICTED' and 'contradiction' not in self.fired:
            self.fired.add('contradiction')
            out.append(self._req('CONTRADICTION_NOTICE',make('req.contradiction',traces,[ref('/response/status'),ref('/response/reason'),ref('/response/retractions')],trace_id=tid)))
        if r['reason']=='RESIDUAL_SURPRISE' and r['status']=='OUT_OF_FAMILY' and 'residual' not in self.fired:
            self.fired.add('residual')
            out.append(self._req('SCOPE_ALERT',make('req.scope.residual',traces,[ref('/response/evidence/residual/surprise'),
                       ref('/response/evidence/residual/threshold'),ref('/response/status')],trace_id=tid)))
        ev=r.get('evidence')
        if ev is not None:
            if self.prev_legacy and ev['legacy_family_alive'] is False and 'legacy' not in self.fired:
                self.fired.add('legacy')
                out.append(self._req('SCOPE_ALERT',make('req.scope.legacy',traces,[ref('/response/evidence/legacy_family_alive'),
                           f'{self.prev_legacy}#/response/evidence/legacy_family_alive'],trace_id=tid)))
            if self.prev_attest and ev['attestation_id'] is None and 'attestation' not in self.fired:
                self.fired.add('attestation')
                out.append(self._req('SCOPE_ALERT',make('req.scope.attestation',traces,[f'{self.prev_attest}#/response/evidence/attestation_id',
                           ref('/response/evidence/attestation_id')],trace_id=tid)))
            if ev['legacy_family_alive']:self.prev_legacy=tid
            if ev['attestation_id'] is not None:self.prev_attest=tid
        if q.get('op')=='observe' and r['status']!='ERROR':
            if self.want is not None:
                rq,rt,act=self.want;self.want=None
                self.resolutions.append({'request_id':rq,'request_trace':rt,'observe_trace':tid,
                                         'status':'satisfied' if q.get('action')==act else 'overridden'})
            obs=q.get('observation') or {}
            self.masked=(tid,[k for k in obs if obs[k] is None]) if any(v is None for v in obs.values()) else None
        elif q.get('op')=='predict':
            if self.masked and r['status'] not in ('CERTIFIED','ERROR'):
                mt,chs=self.masked
                for ch in chs:
                    out.append(self._req('REQUEST_OBSERVATION',make('req.observation',traces,[f'{mt}#/request/observation/{ch}',ref('/response/status')],{'ch':ch},trace_id=tid)))
            self.masked=None
        e=r.get('experiment')
        if isinstance(e,dict) and e.get('tied') is False:
            x=self._req('REQUEST_ACTION',make('req.action',traces,[ref('/response/experiment/action'),ref('/response/experiment/score'),
                                                                  ref('/response/experiment/tied')],trace_id=tid))
            if x is not None:
                if self.want is not None:  # a newer experiment answer replaces an unanswered request
                    self.resolutions.append({'request_id':self.want[0],'request_trace':self.want[1],'observe_trace':None,'status':'superseded'})
                out.append(x);self.want=(x['request_id'],tid,e['action'])
        return [x for x in out if x is not None]

    def drain(self):
        out,self.resolutions=self.resolutions,[];return out
