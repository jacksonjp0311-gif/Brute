"""BruteServiceV011: brute.api/1.1 over brute.fallback.FallbackBruteLearner (v0.1.1, F1 + F3).

Changes from brute.api/1.0 (brute/api/service.py, frozen):
- probabilities after a family contradiction come from the F1 fallback (margin_n5 / suffix1);
  the response says which in `forecast_source` (null for non-predict ops);
- every retraction carries its G8 reason: falsified_by_observation, scope_withdrawn or
  unverifiable_masked (1.0 labelled every retraction falsified_by_observation);
- responses are validated against schema/response.v1_1.json; requests may say 1.0 or 1.1.
Everything else (status mapping, attestation, retry, error handling) is unchanged.
The 1.0 module-level validator is bound inside service.py, so the handlers are restated here.
"""
from __future__ import annotations
import hashlib,itertools,json
from pathlib import Path
from brute.core.learner import ScopeAttestation,Status as CoreStatus,Reason,DEFAULT_MAX_PREFIXES
from brute.fallback import FallbackBruteLearner
from .schema import Status,SchemaError,_validate
from .service import CALIBRATED_TAU,attestation_id
from .alphabet import DEFAULT_ALPHABET
from .refusals import refusal_text

API_VERSION='brute.api/1.1'
_DIR=Path(__file__).with_name('schema')
REQUEST_SCHEMA_V11=json.loads((_DIR/'request.v1_1.json').read_text())
RESPONSE_SCHEMA_V11=json.loads((_DIR/'response.v1_1.json').read_text())
_BRUTE=Path(__file__).resolve().parents[1]
SOURCE_FILES_V11=sorted((_BRUTE/'core').glob('*.py'))+[_BRUTE/'fallback.py']
SOURCE_SHA256_V11=hashlib.sha256(b''.join(p.read_bytes() for p in SOURCE_FILES_V11)).hexdigest()


def validate_request_v11(req):_validate(req,REQUEST_SCHEMA_V11);return req
def validate_response_v11(resp):_validate(resp,RESPONSE_SCHEMA_V11);return resp


class BruteServiceV011:
    def __init__(self,alphabet=DEFAULT_ALPHABET,tau=CALIBRATED_TAU,max_prefixes=DEFAULT_MAX_PREFIXES):
        self.alphabet=alphabet;self.tau=tau;self.max_prefixes=max_prefixes
        self.sessions={};self._ids=itertools.count(1)

    def _evidence(self,L):
        if L is None:return None
        f=L.support;sat=L.saturated()
        return {'step':L.steps,'family_scope':L.family,'surviving_rows':f.count,
                'margin':{'states':L.margin_states,'agrees':None,'support_size':None},
                'saturated':sat,'residual':{'window':L.window,'surprise':L.residual,'threshold':L.tau,'alarm':L.alarm_step is not None},
                'legacy_family_alive':L.legacy_valid,'attestation_id':attestation_id(L.attestation),
                'evidence_count':len(f.evidence),'source_sha256':SOURCE_SHA256_V11}

    def _retractions(self,L):
        if L is None or L.contradiction_step is None:return []
        return [{'step':r['step'],'previous_value':self.alphabet.decode(r['certificate']),'reason':r['reason']}
                for r in L.retractions()]

    def _base(self,rid,op,status,reason=None,L=None):
        return {'api_version':API_VERSION,'request_id':rid,'op':op,'status':status.value,
                'reason':reason.value if reason else None,'certificate':None,'support':None,'probabilities':None,
                'forecast_source':None,'refusal_text':refusal_text(reason),'retractions':self._retractions(L),
                'evidence':self._evidence(L)}

    def _error(self,rid,op,reason,L=None):
        return validate_response_v11(self._base(rid,op if isinstance(op,str) else None,Status.ERROR,reason,L))

    def handle(self,request):
        rid=request.get('request_id') if isinstance(request,dict) and isinstance(request.get('request_id'),str) else f'r{next(self._ids)}'
        op=request.get('op') if isinstance(request,dict) else None
        try:
            if not isinstance(request,dict):raise SchemaError('request must be an object')
            if isinstance(request.get('api_version'),str) and request['api_version'].split('/')[0]=='brute.api' \
               and request['api_version'].split('/')[-1].split('.')[0]!=API_VERSION.split('/')[-1].split('.')[0]:
                raise SchemaError('major version mismatch')
            validate_request_v11(request)
        except SchemaError:
            return self._error(rid,op,Reason.INVALID_REQUEST)
        sid=request['session_id'];L=self.sessions.get(sid)
        try:
            if op=='initialize':return self._initialize(rid,sid,request,L)
            if L is None:return self._error(rid,op,Reason.NOT_INITIALIZED)
            if op=='observe':return self._observe(rid,L,request)
            if op=='predict':return self._predict(rid,L,request)
            if op=='retry':return self._retry(rid,sid,L,request)
            return validate_response_v11(self._base(rid,op,Status.ACKNOWLEDGED,None,L))
        except (ValueError,TypeError,KeyError):
            return self._error(rid,op,Reason.INVALID_REQUEST,L)
        except Exception:  # never raise across the boundary
            return self._error(rid,op,Reason.INTERNAL,L)

    def _attestation(self,request):
        a=request.get('attestation')
        return None if a is None else ScopeAttestation(a['family'],a['issuer'],a['basis'])

    def _initialize(self,rid,sid,request,L):
        if L is not None:return self._error(rid,'initialize',Reason.INVALID_REQUEST,L)
        fam=request.get('family',{});k=fam.get('max_states',4)
        obs=self.alphabet.observation_tuple(request['observation'])
        L=FallbackBruteLearner(k,k+1,fam.get('max_prefixes',self.max_prefixes),fam.get('max_prefixes',self.max_prefixes),
                               tau=self.tau,attestation=self._attestation(request))
        L.initialize(obs);self.sessions[sid]=L
        return validate_response_v11(self._base(rid,'initialize',Status.ACKNOWLEDGED,None,L))

    def _observe(self,rid,L,request):
        a=self.alphabet.action_code(request['action']);obs=self.alphabet.observation_tuple(request['observation'])
        L.observe(a,obs)
        if L.support.status=='grammar_contradicted':
            return validate_response_v11(self._base(rid,'observe',Status.OUT_OF_FAMILY,Reason.FAMILY_CONTRADICTED,L))
        if L.alarm_step is not None:
            return validate_response_v11(self._base(rid,'observe',Status.OUT_OF_FAMILY,Reason.RESIDUAL_SURPRISE,L))
        return validate_response_v11(self._base(rid,'observe',Status.ACKNOWLEDGED,None,L))

    def _predict(self,rid,L,request):
        a=self.alphabet.action_code(request['action']);f=L.predict(a)
        status=Status(f.status.value);reason=f.reason;cert=None
        if f.status==CoreStatus.CERTIFIED:
            if request.get('public') and f.public_certificate is None:
                status,reason=Status.ABSTAIN,Reason.UNATTESTED_SCOPE
            else:
                L.record_issued(f)
                cert={'value':self.alphabet.decode(f.certificate),
                      'kind':'public' if f.public_certificate is not None else 'conditional','conditional_on':f.family}
        r=self._base(rid,'predict',status,reason,L)
        r['certificate']=cert
        r['support']=None if f.support is None else [self.alphabet.decode(c) for c in f.support]
        r['probabilities']=[{'value':self.alphabet.decode(c),'p':p} for c,p in enumerate(f.probabilities)]
        r['forecast_source']=f.forecast_source
        r['evidence']['margin']['agrees']=None if f.support is None or f.margin_support is None else f.margin_support==f.support
        r['evidence']['margin']['support_size']=None if f.margin_support is None else len(f.margin_support)
        return validate_response_v11(r)

    def _retry(self,rid,sid,L,request):
        fam=request.get('family',{});k=fam.get('max_states',L.family_states)
        new=L.retry(k,fam.get('max_prefixes'))
        att=self._attestation(request)
        if att is not None:new.attest(att)  # a NEW attestation must be supplied; the old one never carries over
        self.sessions[sid]=new
        return validate_response_v11(self._base(rid,'retry',Status.ACKNOWLEDGED,None,new))
