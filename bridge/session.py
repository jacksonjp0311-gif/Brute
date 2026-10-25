"""Bridge: operator intents -> real brute.api/1.1 calls -> grounded claims (+ Brute's requests back)."""
from __future__ import annotations
import hashlib
from brute.api.service_v011 import BruteServiceV011,API_VERSION
from brute.api import DEFAULT_ALPHABET
from . import BRIDGE_VERSION
from .claims import make
from .triggers import Triggers
from .log import JsonlSink,dumps

SESSION='operator'
INTENTS=('init','observe','predict','retry','why','version_space','retractions','scope','split','models')
UNSUPPORTED_NOTES={
 'split':'brute.api/1.1 exposes no action-selection field; Brute cannot say which action best splits its hypotheses.',
 'models':'brute.api/1.1 exposes counts of surviving explanations, not their identities; Brute cannot list which models disagree.',
 'unknown':'No bridge intent matches this question; nothing was asked of Brute.',
}


class Bridge:
    def __init__(self,transcript=None,flags=None,service=None,source='operator'):
        self.svc=service or BruteServiceV011();self.traces={};self.seq=0;self.calls=0
        self.last_predict=None;self.last=None;self.triggers=Triggers();self.pending={};self._seen=set()
        self.transcript=JsonlSink(transcript);self.flags=JsonlSink(flags)
        self.transcript.write({'type':'header','bridge':BRIDGE_VERSION,'api_version':API_VERSION,'session_id':SESSION,
                               'source':source,'actions':list(DEFAULT_ALPHABET.actions),
                               'channels':[c.name for c in DEFAULT_ALPHABET.channels]})

    # -- API -----------------------------------------------------------------------------
    def _call(self,op,**kw):
        self.calls+=1
        req={'api_version':API_VERSION,'request_id':f'b{self.calls}','session_id':SESSION,'op':op,**kw}
        resp=self.svc.handle(req)
        tid=f't{self.calls:04d}-'+hashlib.sha256((dumps(req)+dumps(resp)).encode()).hexdigest()[:10]
        self.traces[tid]={'request':req,'response':resp};self.last=tid
        if op=='predict':self.last_predict=tid
        return tid

    def _flag(self,kind,**kw):self.flags.write({'type':'flag','seq':self.seq,'kind':kind,**kw})

    # -- claim helpers ---------------------------------------------------------------------
    def _c(self,out,tid,tpl,ptrs,params=None):
        c=make(tpl,self.traces,[f'{tid}#{p}' for p in ptrs],params)
        if c is not None:out.append(c)

    def _common(self,out,tid):
        r=self.traces[tid]['response']
        self._c(out,tid,'status',['/response/status','/response/op'])
        self._c(out,tid,'reason',['/response/reason'])
        self._c(out,tid,'refusal',['/response/refusal_text'])
        return r

    # -- intents ---------------------------------------------------------------------------
    def ask(self,intent,command=None,**args):
        self.seq+=1;start=self.calls
        fn=getattr(self,'_i_'+intent,None) if intent in INTENTS else None
        if fn is None and intent not in ('split','models'):intent='unknown'
        out=[];note=None;status='ANSWERED'
        if intent in ('split','models','unknown'):
            r=self.traces[self.last]['response'] if self.last else None
            if intent=='split' and r is not None and isinstance(r.get('experiment'),dict):  # v0.2.0 hook
                self._c(out,self.last,'experiment',['/response/experiment/action','/response/experiment/score'])
            else:
                status='UNSUPPORTED';note=UNSUPPORTED_NOTES[intent]
                self._flag('unsupported_intent',intent=intent,command=command)
        else:
            note=fn(out,**args)
            if note:status='NO_DATA'
        new=list(self.traces)[start:]
        reqs=[]
        for t in new:
            for q in self.triggers.feed(t,self.traces):
                reqs.append(q);self.pending[q['request_id']]=q
                if q['kind'] in ('CONTRADICTION_NOTICE','SCOPE_ALERT'):
                    self._flag(q['kind'].lower(),request_id=q['request_id'],trace_id=q['trace_id'],text=q['claims'][0]['text'])
        for t in new:
            rs=self.traces[t]['response']['retractions'];keys=[(x['step'],dumps(x['previous_value'])) for x in rs]
            if len(set(keys))<len(keys) and 'duplicate_retraction' not in self._seen:
                self._seen.add('duplicate_retraction')
                self._flag('duplicate_retraction_entries',trace_id=t,detail_refs=[f'{t}#/response/retractions'],
                           count=len(keys),distinct=len(set(keys)))
        ans={'seq':self.seq,'intent':intent,'args':args,'status':status,'claims':out,'note':note,
             'traces':sorted({c['trace_id'] for c in out}|set(new))}
        self.transcript.write({'type':'turn','seq':self.seq,'command':command,'answer':ans,'requests':reqs,
                               'trace_docs':{t:self.traces[t] for t in new}})
        return ans,reqs

    def decline(self,request_id,command=None):
        """Operator cannot satisfy a Brute request: flag it (no API call, no claims)."""
        self.seq+=1;q=self.pending.pop(request_id,None)
        ans={'seq':self.seq,'intent':'decline','args':{'request_id':request_id},'status':'ACKNOWLEDGED' if q else 'NO_DATA',
             'claims':[],'note':None if q else 'no pending request with that id','traces':[]}
        if q:self._flag('request_unsatisfied',request_id=request_id,request_kind=q['kind'],trace_id=q['trace_id'],text=q['claims'][0]['text'])
        self.transcript.write({'type':'turn','seq':self.seq,'command':command,'answer':ans,'requests':[],'trace_docs':{}})
        return ans,[]

    def _i_init(self,out,obs,max_states=None,attestation=None):
        kw={'observation':obs}
        if max_states:kw['family']={'max_states':max_states}
        if attestation:kw['attestation']=attestation
        tid=self._call('initialize',**kw);self._common(out,tid);self._c(out,tid,'ack',['/response/evidence/evidence_count'])

    def _i_observe(self,out,action,obs):
        tid=self._call('observe',action=action,observation=obs);self._common(out,tid)
        self._c(out,tid,'ack',['/response/evidence/evidence_count'])

    def _i_retry(self,out,max_states):
        tid=self._call('retry',family={'max_states':max_states});self._common(out,tid)
        self._c(out,tid,'survivors',['/response/evidence/surviving_rows','/response/evidence/family_scope','/response/evidence/evidence_count'])

    def _i_predict(self,out,action,channel=None):
        tid=self._call('predict',action=action);r=self._common(out,tid);p={'ch':channel} if channel else None
        if r['status']=='CERTIFIED':
            self._c(out,tid,'cert',['/response/certificate/kind','/response/certificate/conditional_on','/request/action','/response/certificate/value'])
            if channel and channel in r['certificate']['value']:self._c(out,tid,'cert.channel',[f'/response/certificate/value/{channel}'],p)
        elif r['support'] is not None:
            self._c(out,tid,'possible',['/request/action','/response/support','/response/support'])
            if channel and r['support'] and all(channel in s for s in r['support']):self._c(out,tid,'possible.channel',['/response/support'],p)
        for i in range(len(r['probabilities'] or [])):
            self._c(out,tid,'prob',[f'/response/probabilities/{i}/p',f'/response/probabilities/{i}/value','/response/forecast_source'])

    def _i_why(self,out):
        tid=self.last_predict
        if tid is None:return 'no prediction has been made in this session yet'
        r=self._common(out,tid)
        if r['status']=='CERTIFIED':self._c(out,tid,'not_withheld',['/response/status'])
        if r['support'] is not None and r['status']!='CERTIFIED':self._c(out,tid,'possible',['/request/action','/response/support','/response/support'])
        self._c(out,tid,'margin',['/response/evidence/margin/states','/response/evidence/margin/support_size'])
        self._c(out,tid,'survivors',['/response/evidence/surviving_rows','/response/evidence/family_scope','/response/evidence/evidence_count'])
        self._c(out,tid,'saturated',['/response/evidence/saturated'])

    def _snapshot(self,out):
        tid=self._call('snapshot');r=self.traces[tid]['response']
        if r['status']=='ERROR':self._common(out,tid)
        return tid,r

    def _i_version_space(self,out):
        tid,r=self._snapshot(out)
        self._c(out,tid,'survivors',['/response/evidence/surviving_rows','/response/evidence/family_scope','/response/evidence/evidence_count'])
        self._c(out,tid,'saturated',['/response/evidence/saturated'])

    def _i_retractions(self,out):
        tid,r=self._snapshot(out)
        self._c(out,tid,'retraction.count',['/response/retractions'])
        for i in range(len(r['retractions'])):
            self._c(out,tid,'retraction',[f'/response/retractions/{i}/step',f'/response/retractions/{i}/previous_value',f'/response/retractions/{i}/reason'])

    def _i_scope(self,out):
        tid,r=self._snapshot(out)
        self._c(out,tid,'scope.family',['/response/evidence/family_scope','/response/evidence/margin/states'])
        self._c(out,tid,'scope.attestation',['/response/evidence/attestation_id'])
        self._c(out,tid,'scope.legacy',['/response/evidence/legacy_family_alive'])
        self._c(out,tid,'scope.residual',['/response/evidence/residual/surprise','/response/evidence/residual/window',
                                          '/response/evidence/residual/threshold','/response/evidence/residual/alarm'])
