"""BruteServiceV050: brute.api/1.5 over brute.region_learner.RegionBruteLearner (v0.5.0, SAT region backend).

Changes from brute.api/1.4 (brute/api/service_v040.py, frozen; BRUTE_PLAN_007 api_1_5):
- the learner is RegionBruteLearner (A5: the A4 rule with every version-space query answered by the SAT region
  brute/region.py instead of row enumeration; policy 'M' adds the region-volume tie-break) -- 2x2 alphabet only;
- the reason enum gains SOLVER_BUDGET: a forecast that used >=1 UNKNOWN solver answer (Glucose conflict budget hit) is
  ABSTAIN / SOLVER_BUDGET with no certificate;
- evidence gains backend="sat-region" and solver_unknown (predict: UNKNOWN answers used by this forecast; else null);
  surviving_rows is null (rows are not enumerated);
- experiment responses gain policy and volumes; per-action row counts are null (the region has no rows);
- `tau` defaults to the study-006 calibrated tau6 (same alarm rule as v0.4.0);
- responses are validated against schema/response.v1_5.json; requests may say 1.0 .. 1.5.
Everything else is the 1.4 service unchanged (1.4 itself stays frozen). k-action / s-sensor sessions are Open.
"""
from __future__ import annotations
import hashlib,itertools,json
from pathlib import Path
from brute.core.learner import ScopeAttestation,Status as CoreStatus,Reason,DEFAULT_MAX_PREFIXES
from brute.changepoint import Reason030
from brute.region_learner import RegionBruteLearner,Reason050
from brute.region import PRODUCTION_CONF_BUDGET
from .schema import Status,SchemaError,_validate
from .service import attestation_id
from .alphabet import DEFAULT_ALPHABET
from .refusals import refusal_text as _refusal_text_v12

API_VERSION='brute.api/1.5'
_DIR=Path(__file__).with_name('schema')
REQUEST_SCHEMA_V15=json.loads((_DIR/'request.v1_5.json').read_text())
RESPONSE_SCHEMA_V15=json.loads((_DIR/'response.v1_5.json').read_text())
_BRUTE=Path(__file__).resolve().parents[1]
SOURCE_FILES_V15=sorted((_BRUTE/'core').glob('*.py'))+[_BRUTE/'fallback.py',_BRUTE/'active.py',_BRUTE/'changepoint.py',_BRUTE/'resume.py',_BRUTE/'region.py',_BRUTE/'region_learner.py']
SOURCE_SHA256_V15=hashlib.sha256(b''.join(p.read_bytes() for p in SOURCE_FILES_V15)).hexdigest()
CALIBRATION_006=_BRUTE.parent/'results/study-006/CALIBRATION_006.json'
RESYNC_REFUSAL=('The usual rule would certify, but the readings are consistent with more than one place in the learned '
                'cycle, and the places disagree; after a change in the world Brute may be lost, so it will not certify.')


def refusal_text(reason):
    if reason is not None and getattr(reason,'value',reason)==Reason050.SOLVER_BUDGET.value:return SOLVER_REFUSAL
    if reason is not None and getattr(reason,'value',reason)==Reason030.RESYNC_AMBIGUOUS.value:return RESYNC_REFUSAL
    return _refusal_text_v12(reason)


SOLVER_REFUSAL=('The solver ran out of its search budget before it could rule out every alternative, so Brute does not '
                'know whether the usual rule would certify; it will not certify.')


def calibrated_tau6(path=CALIBRATION_006):
    """tau6 from the study-006 calibration (raises if the calibration has not been run)."""
    return json.loads(Path(path).read_text())['tau6']


def validate_request_v15(req):_validate(req,REQUEST_SCHEMA_V15);return req
def validate_response_v15(resp):_validate(resp,RESPONSE_SCHEMA_V15);return resp


class BruteServiceV050:
    def __init__(self,alphabet=DEFAULT_ALPHABET,tau=None,max_prefixes=DEFAULT_MAX_PREFIXES,policy='LU-R',conf_budget=PRODUCTION_CONF_BUDGET):
        self.policy=policy;self.conf_budget=conf_budget;self.alphabet=alphabet;self.tau=calibrated_tau6() if tau is None else tau;self.max_prefixes=max_prefixes
        self.sessions={};self._ids=itertools.count(1)

    def _evidence(self,L):
        if L is None:return None
        f=L.support;sat=L.saturated()
        return {'step':L.steps,'family_scope':L.family,'surviving_rows':None,
                'margin':{'states':L.margin_states,'agrees':None,'support_size':None},
                'saturated':sat,'residual':{'window':L.window,'surprise':L.residual,'threshold':L.tau,'alarm':L.alarm_step is not None},
                'legacy_family_alive':L.legacy_valid,'attestation_id':attestation_id(L.attestation),
                'evidence_count':len(f.evidence),'source_sha256':SOURCE_SHA256_V15,'backend':'sat-region','solver_unknown':None}

    def _retractions(self,L):
        if L is None or L.contradiction_step is None:return []
        return [{'step':r['step'],'previous_value':self.alphabet.decode(r['certificate']),'reason':r['reason']}
                for r in L.retractions()]

    def _base(self,rid,op,status,reason=None,L=None):
        return {'api_version':API_VERSION,'request_id':rid,'op':op,'status':status.value,
                'reason':reason.value if reason else None,'certificate':None,'support':None,'probabilities':None,
                'forecast_source':None,'refusal_text':refusal_text(reason),'retractions':self._retractions(L),
                'evidence':self._evidence(L),'experiment':None,'resumed':None,'alarm_resumes':None}

    def _error(self,rid,op,reason,L=None):
        return validate_response_v15(self._base(rid,op if isinstance(op,str) else None,Status.ERROR,reason,L))

    def handle(self,request):
        rid=request.get('request_id') if isinstance(request,dict) and isinstance(request.get('request_id'),str) else f'r{next(self._ids)}'
        op=request.get('op') if isinstance(request,dict) else None
        try:
            if not isinstance(request,dict):raise SchemaError('request must be an object')
            if isinstance(request.get('api_version'),str) and request['api_version'].split('/')[0]=='brute.api' \
               and request['api_version'].split('/')[-1].split('.')[0]!=API_VERSION.split('/')[-1].split('.')[0]:
                raise SchemaError('major version mismatch')
            validate_request_v15(request)
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
            return validate_response_v15(self._base(rid,op,Status.ACKNOWLEDGED,None,L))
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
        L=RegionBruteLearner(k,k+1,fam.get('max_prefixes',self.max_prefixes),fam.get('max_prefixes',self.max_prefixes),
                             tau=self.tau,attestation=self._attestation(request),conf_budget=self.conf_budget,policy=self.policy)
        L.initialize(obs);self.sessions[sid]=L
        return validate_response_v15(self._base(rid,'initialize',Status.ACKNOWLEDGED,None,L))

    def _observe(self,rid,L,request):
        a=self.alphabet.action_code(request['action']);obs=self.alphabet.observation_tuple(request['observation'])
        L.observe(a,obs)
        if L.support.status=='grammar_contradicted':
            return validate_response_v15(self._base(rid,'observe',Status.OUT_OF_FAMILY,Reason.FAMILY_CONTRADICTED,L))
        if L.alarm_step is not None:
            return validate_response_v15(self._base(rid,'observe',Status.OUT_OF_FAMILY,Reason.RESIDUAL_SURPRISE,L))
        return validate_response_v15(self._base(rid,'observe',Status.ACKNOWLEDGED,None,L))

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
        r['evidence']['solver_unknown']=f.solver_unknown
        r['evidence']['margin']['agrees']=None if f.support is None or f.margin_support is None else f.margin_support==f.support
        r['evidence']['margin']['support_size']=None if f.margin_support is None else len(f.margin_support)
        r['resumed']=bool(L.resumes) and L.alarm_step is None;r['alarm_resumes']=L.resumes
        return validate_response_v15(r)

    def _experiment(self,rid,L,request):
        sym=self.alphabet.actions
        d=self.alphabet.action_code(request['default_action']) if 'default_action' in request else 0
        e=L.experiment(d,counts=bool(request.get('counts')))
        out={'action':sym[e['action']],'score':e['score'],'scores':[{'action':sym[b],'score':e['scores'][b]} for b in (0,1)],
             'rule':e['rule'],'tie_break':e['tie_break'],'tied':e['tied'],'check':e['check'],
             'proposal':e['proposal'],'no_proposal_reason':e['no_proposal_reason'],
             'policy':e['policy'],'volumes':e['volumes']}
        if 'per_action' in e:
            out['per_action']=[{'action':sym[b],'counts':None if c is None else
                                {'family_code_rows':[{'value':self.alphabet.decode(x),'rows':c['family_code_rows'][x]} for x in range(4)],
                                 'family_open_rows':c['family_open_rows'],'family_rows':c['family_rows'],'margin_rows':c['margin_rows']}}
                               for b,c in enumerate(e['per_action'])]
        r=self._base(rid,'experiment',Status.ACKNOWLEDGED,None,L);r['experiment']=out
        return validate_response_v15(r)

    def _retry(self,rid,sid,L,request):
        fam=request.get('family',{});k=fam.get('max_states',L.family_states)
        new=L.retry(k,fam.get('max_prefixes'))
        att=self._attestation(request)
        if att is not None:new.attest(att)  # a NEW attestation must be supplied; the old one never carries over
        self.sessions[sid]=new
        return validate_response_v15(self._base(rid,'retry',Status.ACKNOWLEDGED,None,new))
