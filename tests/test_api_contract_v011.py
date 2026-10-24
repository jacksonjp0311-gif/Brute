"""F3 (v0.1.1): brute.api/1.1 contract: honest retraction reasons and forecast_source."""
import json,unittest
from bgr89.worlds import world as old_world,actions
from bgr90.worlds import world as new_world,step as new_step
from brute.api.service import BruteService
from brute.api.service_v011 import (API_VERSION,BruteServiceV011,RESPONSE_SCHEMA_V11,REQUEST_SCHEMA_V11,
                                    SOURCE_SHA256_V11,validate_response_v11)
from brute.api.schema import RESPONSE_SCHEMA,SchemaError
from brute.fallback import retraction_reason,RETRACTION_REASONS,FORECAST_SOURCES
from brute.core.learner import DECLARED_FAMILY

ATT={'family':DECLARED_FAMILY,'issuer':'test','basis':'synthetic'}


def stream(seed,family,mask,version):
    truth=(new_world if family in ('ood5','drift4') else old_world)(seed,family)
    h=truth.start;init=truth.observed(h,mask,-1)
    ob=lambda o:{'x':o[0],'y':o[1]}
    base={'api_version':version,'session_id':'s'}
    reqs=[dict(base,op='initialize',observation=ob(init))];truth_codes=[]
    for i,a in enumerate(actions(seed,44)):
        h=new_step(truth,h,a,i) if family=='drift4' else truth.next(h,a)
        reqs.append(dict(base,op='predict',action='ab'[a]))
        reqs.append(dict(base,op='observe',action='ab'[a],observation=ob(truth.observed(h,mask,i))))
        truth_codes.append(truth.emission(h))
    return reqs,truth_codes


class ApiV011(unittest.TestCase):
    def test_schema(self):
        self.assertEqual(RESPONSE_SCHEMA_V11['properties']['api_version']['const'],API_VERSION)
        self.assertEqual(RESPONSE_SCHEMA_V11['properties']['retractions']['items']['properties']['reason']['enum'],
                         list(RETRACTION_REASONS))
        self.assertEqual(RESPONSE_SCHEMA_V11['properties']['forecast_source']['enum'],[None]+list(FORECAST_SOURCES))
        for k in RESPONSE_SCHEMA['properties']:
            if k!='api_version' and k!='retractions':
                self.assertEqual(RESPONSE_SCHEMA_V11['properties'][k],RESPONSE_SCHEMA['properties'][k],k)
        self.assertIn('brute.api/1.0',REQUEST_SCHEMA_V11['properties']['api_version']['enum'])

    def test_same_as_v10_except_documented_fields(self):
        """Statuses, certificates, support, evidence equal 1.0; probabilities equal 1.0 before contradiction."""
        checked=0
        for seed,fam,mask in [(990001,'drift4',.1),(990004,'drift4',.35),(980001,'ood5',.1),(930002,'cycle3',.35)]:
            reqs,_=stream(seed,fam,mask,'brute.api/1.0')
            a,b=BruteService(),BruteServiceV011();contradicted=False
            for q in reqs:
                ra,rb=a.handle(q),b.handle(q)
                validate_response_v11(rb);self.assertEqual(rb['api_version'],API_VERSION)
                for k in ('status','reason','certificate','support','refusal_text','op','request_id'):
                    self.assertEqual(ra[k],rb[k],(seed,k))
                ea=dict(ra['evidence']);eb=dict(rb['evidence'])
                self.assertEqual(eb.pop('source_sha256'),SOURCE_SHA256_V11);ea.pop('source_sha256')
                if not contradicted:self.assertEqual(ea,eb)
                self.assertEqual([(r['step'],r['previous_value']) for r in ra['retractions']],
                                 [(r['step'],r['previous_value']) for r in rb['retractions']])
                if q['op']=='predict':
                    if not contradicted:
                        self.assertEqual(ra['probabilities'],rb['probabilities']);self.assertEqual(rb['forecast_source'],'v090')
                    else:
                        self.assertIn(rb['forecast_source'],('margin_n5','suffix1'));checked+=1
                else:self.assertIsNone(rb['forecast_source'])
                if rb['reason']=='FAMILY_CONTRADICTED':contradicted=True
        self.assertGreater(checked,0)

    def test_retraction_reasons_match_truth(self):
        seen={};total=0
        for seed in range(990001,990025):
            for mask in (.1,.35,.6):
                reqs,codes=stream(seed,'drift4',mask,API_VERSION)
                s=BruteServiceV011();obs_at={}
                step=0
                for q in reqs:
                    r=s.handle(q)
                    if q['op']=='observe':step+=1;obs_at[step]=(q['observation']['x'],q['observation']['y'])
                last=r['retractions']
                for x in last:
                    cert=2*x['previous_value']['x']+x['previous_value']['y']
                    self.assertEqual(x['reason'],retraction_reason(cert,obs_at[x['step']]))
                    if x['reason']=='falsified_by_observation':self.assertNotEqual(codes[x['step']-1],cert)
                    if x['reason']=='scope_withdrawn':self.assertEqual(codes[x['step']-1],cert)
                    seen[x['reason']]=seen.get(x['reason'],0)+1;total+=1
        self.assertGreater(total,0)
        self.assertIn('scope_withdrawn',seen)

    def test_round_trip_errors_and_attestation(self):
        s=BruteServiceV011()
        r=s.handle({'api_version':'brute.api/2.0','session_id':'s','op':'initialize'})
        self.assertEqual((r['status'],r['reason']),('ERROR','INVALID_REQUEST'))
        r=s.handle({'api_version':API_VERSION,'session_id':'s','op':'predict','action':'a'})
        self.assertEqual(r['reason'],'NOT_INITIALIZED')
        r=s.handle('nope');self.assertEqual(r['reason'],'INVALID_REQUEST')
        reqs,_=stream(930001,'cycle3',.1,API_VERSION)
        reqs[0]['attestation']=ATT
        for q in reqs:
            if q['op']=='predict':q['public']=True
            r=s.handle(q);self.assertEqual(json.loads(json.dumps(r)),r)
            if r['certificate']:self.assertEqual(r['certificate']['kind'],'public')
        r=s.handle({'api_version':API_VERSION,'session_id':'s','op':'retry','family':{'max_states':3}})
        self.assertEqual(r['status'],'ACKNOWLEDGED');self.assertIsNone(r['evidence']['attestation_id'])
        with self.assertRaises(SchemaError):validate_response_v11(dict(r,retractions=[{'step':1,'previous_value':{},'reason':'other'}]))


if __name__=='__main__':unittest.main()
