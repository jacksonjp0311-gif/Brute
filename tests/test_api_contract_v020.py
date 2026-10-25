"""brute.api/1.2 contract: experiment op/field, window_n4 source, issuance de-duplication (bridge B1/B3)."""
import unittest
from brute.api.service_v011 import BruteServiceV011,RESPONSE_SCHEMA_V11
from brute.api.service_v020 import (API_VERSION,BruteServiceV020,RESPONSE_SCHEMA_V12,REQUEST_SCHEMA_V12,
                                    SOURCE_SHA256_V12,validate_response_v12)
from brute.active import FORECAST_SOURCES
from tests.test_api_contract_v011 import stream


class ApiV020(unittest.TestCase):
    def test_schema(self):
        self.assertEqual(RESPONSE_SCHEMA_V12['properties']['api_version']['const'],API_VERSION)
        self.assertEqual(RESPONSE_SCHEMA_V12['properties']['forecast_source']['enum'],[None]+list(FORECAST_SOURCES))
        self.assertIn('experiment',REQUEST_SCHEMA_V12['properties']['op']['enum'])
        for k in RESPONSE_SCHEMA_V11['properties']:
            if k not in ('api_version','forecast_source'):
                self.assertEqual(RESPONSE_SCHEMA_V12['properties'][k],RESPONSE_SCHEMA_V11['properties'][k],k)

    def test_same_as_v11_except_documented(self):
        windows=0
        for seed,fam,mask in [(990002,'drift4',.1),(980001,'ood5',.1),(930002,'cycle3',.35)]:
            reqs,_=stream(seed,fam,mask,'brute.api/1.1')
            a,b=BruteServiceV011(),BruteServiceV020()
            for q in reqs:
                ra,rb=a.handle(q),b.handle(q);validate_response_v12(rb)
                self.assertIsNone(rb['experiment'])
                for k in ('status','reason','certificate','support','refusal_text','op','request_id','retractions'):
                    self.assertEqual(ra[k],rb[k],(seed,k))
                self.assertEqual(rb['evidence']['source_sha256'],SOURCE_SHA256_V12)
                if q['op']=='predict':
                    if rb['forecast_source']=='window_n4':windows+=1;self.assertEqual(ra['forecast_source'],'suffix1')
                    else:self.assertEqual(ra['probabilities'],rb['probabilities'])
        self.assertGreater(windows,0)

    def _certified_session(self,svc,version='brute.api/1.2'):
        base={'api_version':version,'session_id':'s'}
        svc.handle(dict(base,op='initialize',observation={'x':0,'y':0}))
        for _ in range(12):svc.handle(dict(base,op='observe',action='a',observation={'x':0,'y':0}))
        return base

    def test_double_predict_records_once(self):
        """Bridge B1: two predicts at one step, then a contradiction, list the retraction once in 1.2 (twice in 1.1)."""
        for svc,want in ((BruteServiceV020(),1),(BruteServiceV011(),2)):
            base=self._certified_session(svc,'brute.api/1.1' if svc.__class__ is BruteServiceV011 else 'brute.api/1.2')
            r1=svc.handle(dict(base,op='predict',action='a'));r2=svc.handle(dict(base,op='predict',action='a'))
            self.assertEqual(r1['status'],'CERTIFIED');self.assertEqual(r2['status'],'CERTIFIED')
            svc.handle(dict(base,op='observe',action='a',observation={'x':1,'y':1}))
            for obs in ({'x':1,'y':0},{'x':0,'y':1},{'x':1,'y':1},{'x':0,'y':0}):
                r=svc.handle(dict(base,op='observe',action='b',observation=obs))
                if r['reason']=='FAMILY_CONTRADICTED':break
            self.assertEqual(r['reason'],'FAMILY_CONTRADICTED')
            if True:
                self.assertEqual(len([x for x in r['retractions'] if x['step']==13]),want)

    def test_experiment_op(self):
        svc=BruteServiceV020();base=self._certified_session(svc)
        r=svc.handle(dict(base,op='experiment',default_action='b',counts=True));validate_response_v12(r)
        self.assertEqual(r['status'],'ACKNOWLEDGED');e=r['experiment']
        self.assertIn(e['action'],('a','b'));self.assertEqual([s['action'] for s in e['scores']],['a','b'])
        if e['tied']:self.assertEqual(e['action'],'b')
        self.assertEqual(len(e['per_action']),2)
        r2=svc.handle(dict(base,op='experiment',default_action='z'));self.assertEqual(r2['reason'],'INVALID_REQUEST')
        r3=svc.handle({'api_version':'brute.api/1.1','session_id':'s','op':'experiment'})
        self.assertEqual(r3['status'],'ACKNOWLEDGED')

    def test_bad_requests(self):
        svc=BruteServiceV020()
        self.assertEqual(svc.handle({'api_version':'brute.api/1.2','session_id':'q','op':'experiment'})['reason'],'NOT_INITIALIZED')
        self.assertEqual(svc.handle({'api_version':'brute.api/2.0','session_id':'q','op':'experiment'})['reason'],'INVALID_REQUEST')
        self.assertEqual(svc.handle('nope')['reason'],'INVALID_REQUEST')


if __name__=='__main__':unittest.main()
