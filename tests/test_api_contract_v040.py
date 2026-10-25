"""brute.api/1.4 contract: resumed / alarm_resumes; never a public certificate after the first alarm."""
import unittest
from brute.api.service_v030 import BruteServiceV030,RESPONSE_SCHEMA_V13,REQUEST_SCHEMA_V13
from brute.api.service_v040 import (API_VERSION,BruteServiceV040,RESPONSE_SCHEMA_V14,REQUEST_SCHEMA_V14,
                                    SOURCE_SHA256_V14,SOURCE_FILES_V14,validate_response_v14)
from tests.test_api_contract_v011 import stream


class ApiV040(unittest.TestCase):
    def test_schema(self):
        R14,R13=RESPONSE_SCHEMA_V14['properties'],RESPONSE_SCHEMA_V13['properties']
        self.assertEqual(R14['api_version']['const'],API_VERSION);self.assertEqual(API_VERSION,'brute.api/1.4')
        self.assertEqual(set(R14)-set(R13),{'resumed','alarm_resumes'})
        for k in R13:
            if k!='api_version':self.assertEqual(R14[k],R13[k],k)
        self.assertEqual({k:v for k,v in REQUEST_SCHEMA_V14['properties'].items() if k!='api_version'},
                         {k:v for k,v in REQUEST_SCHEMA_V13['properties'].items() if k!='api_version'})
        self.assertIn('brute.api/1.3',REQUEST_SCHEMA_V14['properties']['api_version']['enum'])
        self.assertTrue(any(p.name=='resume.py' for p in SOURCE_FILES_V14))

    def test_resume_session(self):
        """tau=0.3 on cycle3 seed 930002 (mask .35) alarms then clears: resumed predicts are never publicly certified."""
        reqs,_=stream(930002,'cycle3',.35,'brute.api/1.4');s=BruteServiceV040(tau=0.3);alarmed=False;resumed=0
        for q in reqs:
            r=validate_response_v14(s.handle(q));self.assertEqual(r['evidence']['source_sha256'],SOURCE_SHA256_V14)
            if r['op']!='predict':self.assertIsNone(r['resumed']);self.assertIsNone(r['alarm_resumes']);continue
            L=s.sessions['s'];alarmed|=bool(L.alarm_steps)
            if alarmed:self.assertIsNone(L.attestation)
            if r['resumed']:
                resumed+=1;self.assertGreaterEqual(r['alarm_resumes'],1)
                if r['status']=='CERTIFIED':self.assertEqual(r['certificate']['kind'],'conditional')
        self.assertGreater(resumed,0)
        pub=BruteServiceV040(tau=0.3)
        for q in reqs:
            q=dict(q,public=True) if q['op']=='predict' else q;r=pub.handle(q)
            if r['op']=='predict' and pub.sessions['s'].alarm_steps:self.assertNotEqual(r['status'],'CERTIFIED')

    def test_no_alarm_same_as_v13(self):
        """With no alarm ever set (tau=None in both: no residual alarm), 1.4 equals 1.3 apart from version fields."""
        for seed,fam,mask in [(930002,'cycle3',.35),(940002,'switch3',.1)]:
            reqs,_=stream(seed,fam,mask,'brute.api/1.3');a=BruteServiceV030(tau=None);b=BruteServiceV040(tau=float('inf'))
            for q in reqs:
                ra,rb=a.handle(q),b.handle(q)
                for k in ('status','reason','certificate','support','probabilities','refusal_text','retractions','experiment'):
                    self.assertEqual(ra[k],rb[k],(seed,k,q['op']))
                if rb['op']=='predict':self.assertEqual((rb['resumed'],rb['alarm_resumes']),(False,0))


if __name__=='__main__':unittest.main()
