"""BruteService: sessions over brute.core.BruteLearner, Forecast -> brute.api/1.0 Response.

The service never raises across the boundary; every failure becomes ERROR with a
stable reason. Every response is validated against schema/response.v1.json.
"""
from __future__ import annotations
import hashlib,itertools,json
from pathlib import Path
from brute.core.learner import BruteLearner,ScopeAttestation,Status as CoreStatus,Reason,DEFAULT_MAX_PREFIXES
from .schema import API_VERSION,Status,SchemaError,validate_request,validate_response
from .alphabet import DEFAULT_ALPHABET
from .refusals import refusal_text

# Residual threshold calibrated on in-family study-001 seeds (results/study-002/CALIBRATION.json).
CALIBRATED_TAU=1.433141502274
_CORE=Path(__file__).resolve().parents[1]/'core'
SOURCE_SHA256=hashlib.sha256(b''.join(p.read_bytes() for p in sorted(_CORE.glob('*.py')))).hexdigest()


def attestation_id(att):
    if att is None:return None
    blob=json.dumps({'family':att.family,'issuer':att.issuer,'basis':att.basis},sort_keys=True).encode()
    return hashlib.sha256(blob).hexdigest()[:16]


class BruteService:
    def __init__(self,alphabet=DEFAULT_ALPHABET,tau=CALIBRATED_TAU,max_prefixes=DEFAULT_MAX_PREFIXES):
        self.alphabet=alphabet;self.tau=tau;self.max_prefixes=max_prefixes
        self.sessions={};self._ids=itertools.count(1)

    # -- response builders -----------------------------------------------------
    def _evidence(self,L):
        if L is None:return None
        f=L.support;sat=L.saturated()
        return {'step':L.steps,'family_scope':L.family,'surviving_rows':f.count,
                'margin':{'states':L.margin_states,'agrees':None,'support_size':None},
                'saturated':sat,'residual':{'window':L.window,'surprise':L.residual,'threshold':L.tau,'alarm':L.alarm_step is not None},
                'legacy_family_alive':L.legacy_valid,'attestation_id':attestation_id(L.attestation),
                'evidence_count':len(f.evidence),'source_sha256':SOURCE_SHA256}

    def _retractions(self,L):
        if L is None or L.contradiction_step is None:return []
        return [{'step':s,'previous_value':self.alphabet.decode(v),'reason':'falsified_by_observation'} for s,v in L.issued]

    def _base(self,rid,op,status,reason=None,L=None):
        return {'api_version':API_VERSION,'request_id':rid,'op':op,'status':status.value,
                'reason':reason.value if reason else None,'certificate':None,'support':None,'probabilities':None,
                'refusal_text':refusal_text(reason),'retractions':self._retractions(L),'evidence':self._evidence(L)}

    def _error(self,rid,op,reason,L=None):
        return validate_response(self._base(rid,op if isinstance(op,str) else None,Status.ERROR,reason,L))

    # -- entry point -----------------------------------------------------------
    def handle(self,request):
        rid=request.get('request_id') if isinstance(request,dict) and isinstance(request.get('request_id'),str) else f'r{next(self._ids)}'
        op=request.get('op') if isinstance(request,dict) else None
        try:
            if not isinstance(request,dict):raise SchemaError('request must be an object')
            if isinstance(request.get('api_version'),str) and request['api_version'].split('/')[0]=='brute.api' \
               and request['api_version'].split('/')[-1].split('.')[0]!=API_VERSION.split('/')[-1].split('.')[0]:
                raise SchemaError('major version mismatch')
            validate_request(request)
        except SchemaError:
            return self._error(rid,op,Reason.INVALID_REQUEST)
        sid=request['session_id'];L=self.sessions.get(sid)
        try:
            if op=='initialize':return self._initialize(rid,sid,request,L)
            if L is None:return self._error(rid,op,Reason.NOT_INITIALIZED)
            if op=='observe':return self._observe(rid,L,request)
            if op=='predict':return self._predict(rid,L,request)
            if op=='retry':return self._retry(rid,sid,L,request)
            return validate_response(self._base(rid,op,Status.ACKNOWLEDGED,None,L))
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
        L=BruteLearner(k,k+1,fam.get('max_prefixes',self.max_prefixes),fam.get('max_prefixes',self.max_prefixes),
                       tau=self.tau,attestation=self._attestation(request))
        L.initialize(obs);self.sessions[sid]=L
        return validate_response(self._base(rid,'initialize',Status.ACKNOWLEDGED,None,L))

    def _observe(self,rid,L,request):
        a=self.alphabet.action_code(request['action']);obs=self.alphabet.observation_tuple(request['observation'])
        L.observe(a,obs)
        if L.support.status=='grammar_contradicted':
            return validate_response(self._base(rid,'observe',Status.OUT_OF_FAMILY,Reason.FAMILY_CONTRADICTED,L))
        if L.alarm_step is not None:
            return validate_response(self._base(rid,'observe',Status.OUT_OF_FAMILY,Reason.RESIDUAL_SURPRISE,L))
        return validate_response(self._base(rid,'observe',Status.ACKNOWLEDGED,None,L))

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
        r['evidence']['margin']['agrees']=None if f.support is None or f.margin_support is None else f.margin_support==f.support
        r['evidence']['margin']['support_size']=None if f.margin_support is None else len(f.margin_support)
        return validate_response(r)

    def _retry(self,rid,sid,L,request):
        fam=request.get('family',{});k=fam.get('max_states',L.family_states)
        new=L.retry(k,fam.get('max_prefixes'))
        att=self._attestation(request)
        if att is not None:new.attest(att)  # a NEW attestation must be supplied; the old one never carries over
        self.sessions[sid]=new
        return validate_response(self._base(rid,'retry',Status.ACKNOWLEDGED,None,new))


_DEFAULT=BruteService()


def handle(request):
    """Module-level entry point on a process-wide default service."""
    return _DEFAULT.handle(request)
