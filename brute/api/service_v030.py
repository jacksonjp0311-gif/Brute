"""BruteServiceV030: brute.api/1.3 over brute.changepoint.ChangePointBruteLearner (v0.3.0).

Changes from brute.api/1.2 (brute/api/service_v020.py, frozen; BRUTE_PLAN_005 api_1_3):
- predict may return ABSTAIN with reason RESYNC_AMBIGUOUS: the v0.2.0 rule would certify, but the certificate is
  not constant over every visited state consistent with the latest observation (Y1k change-robust certification);
- experiment gains `check` (true when the untaken-branch check overrode the choice; always false in the release
  learner, CHECK_RUN 0), `proposal` (PROPOSED / NO_PROPOSAL) and `no_proposal_reason` (OUT_OF_SCOPE when the family
  or margin is no longer supported, RESIDUAL_ALARM when the residual alarm is set). Scores are still returned;
  `rule` names the LU-R lookahead.
- responses are validated against schema/response.v1_3.json; requests may say 1.0 .. 1.3.

Text kept from the 1.2 docstring, changes from brute.api/1.1:
- new op 'experiment' (optional default_action, counts): the response field `experiment` gives
  {action, score, scores, rule, tie_break, tied[, per_action]} from the LU one-step certifiability lookahead.
  The op is read-only: it changes no evidence, certificate or issuance. `experiment` is null for other ops.
- forecast_source may be 'window_n4' (window rebuild after a family contradiction);
- a certified predict is recorded as issued at most once per (step, certificate), so predicting twice at one step
  no longer lists the retraction twice (bridge item B1; 1.1 keeps its behaviour because it is frozen).
- (1.2) responses were validated against schema/response.v1_2.json.
Everything else (status mapping, attestation, retry, error handling) is unchanged from 1.1.
"""
from __future__ import annotations
import hashlib,itertools,json
from pathlib import Path
from brute.core.learner import ScopeAttestation,Status as CoreStatus,Reason,DEFAULT_MAX_PREFIXES
from brute.changepoint import ChangePointBruteLearner,Reason030
from .schema import Status,SchemaError,_validate
from .service import CALIBRATED_TAU,attestation_id
from .alphabet import DEFAULT_ALPHABET
from .refusals import refusal_text as _refusal_text_v12

API_VERSION='brute.api/1.3'
_DIR=Path(__file__).with_name('schema')
REQUEST_SCHEMA_V13=json.loads((_DIR/'request.v1_3.json').read_text())
RESPONSE_SCHEMA_V13=json.loads((_DIR/'response.v1_3.json').read_text())
_BRUTE=Path(__file__).resolve().parents[1]
SOURCE_FILES_V13=sorted((_BRUTE/'core').glob('*.py'))+[_BRUTE/'fallback.py',_BRUTE/'active.py',_BRUTE/'changepoint.py']
SOURCE_SHA256_V13=hashlib.sha256(b''.join(p.read_bytes() for p in SOURCE_FILES_V13)).hexdigest()
RESYNC_REFUSAL=('The usual rule would certify, but the readings are consistent with more than one place in the learned '
                'cycle, and the places disagree; after a change in the world Brute may be lost, so it will not certify.')


def refusal_text(reason):
    if reason is not None and getattr(reason,'value',reason)==Reason030.RESYNC_AMBIGUOUS.value:return RESYNC_REFUSAL
    return _refusal_text_v12(reason)


def validate_request_v13(req):_validate(req,REQUEST_SCHEMA_V13);return req
def validate_response_v13(resp):_validate(resp,RESPONSE_SCHEMA_V13);return resp


class BruteServiceV030:
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
                'evidence_count':len(f.evidence),'source_sha256':SOURCE_SHA256_V13}

    def _retractions(self,L):
        if L is None or L.contradiction_step is None:return []
        return [{'step':r['step'],'previous_value':self.alphabet.decode(r['certificate']),'reason':r['reason']}
                for r in L.retractions()]

    def _base(self,rid,op,status,reason=None,L=None):
        return {'api_version':API_VERSION,'request_id':rid,'op':op,'status':status.value,
                'reason':reason.value if reason else None,'certificate':None,'support':None,'probabilities':None,
                'forecast_source':None,'refusal_text':refusal_text(reason),'retractions':self._retractions(L),
                'evidence':self._evidence(L),'experiment':None}

    def _error(self,rid,op,reason,L=None):
        return validate_response_v13(self._base(rid,op if isinstance(op,str) else None,Status.ERROR,reason,L))

    def handle(self,request):
        rid=request.get('request_id') if isinstance(request,dict) and isinstance(request.get('request_id'),str) else f'r{next(self._ids)}'
        op=request.get('op') if isinstance(request,dict) else None
        try:
            if not isinstance(request,dict):raise SchemaError('request must be an object')
            if isinstance(request.get('api_version'),str) and request['api_version'].split('/')[0]=='brute.api' \
               and request['api_version'].split('/')[-1].split('.')[0]!=API_VERSION.split('/')[-1].split('.')[0]:
                raise SchemaError('major version mismatch')
            validate_request_v13(request)
        except SchemaError:
            return self._error(rid,op,Reason.INVALID_REQUEST)
        sid=request['session_id'];L=self.sessions.get(sid)
        try:
            if op=='initialize':return self._initialize(rid,sid,request,L)
            if L is None:return self._error(rid,op,Reason.NOT_INITIALIZED)
            if op=='observe':return self._observe(rid,L,request)
            if op=='predict':return self._predict(rid,L,request)
            if op=='retry':return self._retry(rid,sid,L,request)
            if op=='experiment':return self._experiment(rid,L,request)
            return validate_response_v13(self._base(rid,op,Status.ACKNOWLEDGED,None,L))
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
        L=ChangePointBruteLearner(k,k+1,fam.get('max_prefixes',self.max_prefixes),fam.get('max_prefixes',self.max_prefixes),
                             tau=self.tau,attestation=self._attestation(request))
        L.initialize(obs);self.sessions[sid]=L
        return validate_response_v13(self._base(rid,'initialize',Status.ACKNOWLEDGED,None,L))

    def _observe(self,rid,L,request):
        a=self.alphabet.action_code(request['action']);obs=self.alphabet.observation_tuple(request['observation'])
        L.observe(a,obs)
        if L.support.status=='grammar_contradicted':
            return validate_response_v13(self._base(rid,'observe',Status.OUT_OF_FAMILY,Reason.FAMILY_CONTRADICTED,L))
        if L.alarm_step is not None:
            return validate_response_v13(self._base(rid,'observe',Status.OUT_OF_FAMILY,Reason.RESIDUAL_SURPRISE,L))
        return validate_response_v13(self._base(rid,'observe',Status.ACKNOWLEDGED,None,L))

    def _predict(self,rid,L,request):
        a=self.alphabet.action_code(request['action']);f=L.predict(a)
        status=Status(f.status.value);reason=f.reason;cert=None
        if f.status==CoreStatus.CERTIFIED:
            if request.get('public') and f.public_certificate is None:
                status,reason=Status.ABSTAIN,Reason.UNATTESTED_SCOPE
            else:
                L.record_issued(f)   # de-duplicated per (step, certificate)
                cert={'value':self.alphabet.decode(f.certificate),
                      'kind':'public' if f.public_certificate is not None else 'conditional','conditional_on':f.family}
        r=self._base(rid,'predict',status,reason,L)
        r['certificate']=cert
        r['support']=None if f.support is None else [self.alphabet.decode(c) for c in f.support]
        r['probabilities']=[{'value':self.alphabet.decode(c),'p':p} for c,p in enumerate(f.probabilities)]
        r['forecast_source']=f.forecast_source
        r['evidence']['margin']['agrees']=None if f.support is None or f.margin_support is None else f.margin_support==f.support
        r['evidence']['margin']['support_size']=None if f.margin_support is None else len(f.margin_support)
        return validate_response_v13(r)

    def _experiment(self,rid,L,request):
        sym=self.alphabet.actions
        d=self.alphabet.action_code(request['default_action']) if 'default_action' in request else 0
        e=L.experiment(d,counts=bool(request.get('counts')))
        out={'action':sym[e['action']],'score':e['score'],'scores':[{'action':sym[b],'score':e['scores'][b]} for b in (0,1)],
             'rule':e['rule'],'tie_break':e['tie_break'],'tied':e['tied'],'check':e['check'],
             'proposal':e['proposal'],'no_proposal_reason':e['no_proposal_reason']}
        if 'per_action' in e:
            out['per_action']=[{'action':sym[b],'counts':None if c is None else
                                {'family_code_rows':[{'value':self.alphabet.decode(x),'rows':c['family_code_rows'][x]} for x in range(4)],
                                 'family_open_rows':c['family_open_rows'],'family_rows':c['family_rows'],'margin_rows':c['margin_rows']}}
                               for b,c in enumerate(e['per_action'])]
        r=self._base(rid,'experiment',Status.ACKNOWLEDGED,None,L);r['experiment']=out
        return validate_response_v13(r)

    def _retry(self,rid,sid,L,request):
        fam=request.get('family',{});k=fam.get('max_states',L.family_states)
        new=L.retry(k,fam.get('max_prefixes'))
        att=self._attestation(request)
        if att is not None:new.attest(att)  # a NEW attestation must be supplied; the old one never carries over
        self.sessions[sid]=new
        return validate_response_v13(self._base(rid,'retry',Status.ACKNOWLEDGED,None,new))
