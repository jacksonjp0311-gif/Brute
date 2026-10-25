"""brute.api/1.3 contract: RESYNC_AMBIGUOUS, experiment check/proposal/no_proposal_reason (bridge O3)."""
import unittest
from brute.api.service_v020 import BruteServiceV020,RESPONSE_SCHEMA_V12,REQUEST_SCHEMA_V12
from brute.api.service_v030 import (API_VERSION,BruteServiceV030,RESPONSE_SCHEMA_V13,REQUEST_SCHEMA_V13,
                                    SOURCE_SHA256_V13,validate_response_v13,refusal_text)
from tests.test_api_contract_v011 import stream


class ApiV030(unittest.TestCase):
    def test_schema(self):
        R13,R12=RESPONSE_SCHEMA_V13['properties'],RESPONSE_SCHEMA_V12['properties']
        self.assertEqual(R13['api_version']['const'],API_VERSION)
        self.assertEqual(R13['reason']['enum'],R12['reason']['enum']+['RESYNC_AMBIGUOUS'])
        for k in ('check','proposal','no_proposal_reason'):self.assertIn(k,R13['experiment']['required'])
        for k in R12:
            if k not in ('api_version','reason','experiment'):self.assertEqual(R13[k],R12[k],k)
        self.assertEqual({k:v for k,v in REQUEST_SCHEMA_V13['properties'].items() if k!='api_version'},
                         {k:v for k,v in REQUEST_SCHEMA_V12['properties'].items() if k!='api_version'})
        self.assertIn('brute.api/1.2',REQUEST_SCHEMA_V13['properties']['api_version']['enum'])
        self.assertTrue(refusal_text('RESYNC_AMBIGUOUS'))

    def test_same_as_v12_except_resync(self):
        down=0
        for seed,fam,mask in [(990002,'drift4',.1),(980001,'ood5',.1),(930002,'cycle3',.35),(940002,'switch3',.35)]:
            reqs,_=stream(seed,fam,mask,'brute.api/1.2')
            a,b=BruteServiceV020(),BruteServiceV030()
            for q in reqs:
                ra,rb=a.handle(q),b.handle(q);validate_response_v13(rb)
                self.assertEqual(rb['evidence']['source_sha256'],SOURCE_SHA256_V13)
                self.assertEqual(ra['probabilities'],rb['probabilities']);self.assertEqual(ra['forecast_source'],rb['forecast_source'])
                if rb['reason']=='RESYNC_AMBIGUOUS':
                    down+=1;self.assertEqual((ra['status'],rb['status']),('CERTIFIED','ABSTAIN'));self.assertIsNone(rb['certificate'])
                    self.assertEqual(rb['refusal_text'],refusal_text('RESYNC_AMBIGUOUS'))
                else:
                    for k in ('status','reason','certificate','support','refusal_text','op','request_id'):self.assertEqual(ra[k],rb[k],(seed,k))
                    # downgraded certificates are never issued, so v1.3 may list fewer retractions
                    self.assertTrue(all(x in ra['retractions'] for x in rb['retractions']))
        self.assertGreater(down,0)

    def _session(self,svc):
        base={'api_version':'brute.api/1.3','session_id':'s'}
        svc.handle(dict(base,op='initialize',observation={'x':0,'y':0}))
        for _ in range(12):svc.handle(dict(base,op='observe',action='a',observation={'x':0,'y':0}))
        return base

    def test_experiment_fields(self):
        svc=BruteServiceV030();base=self._session(svc)
        r=svc.handle(dict(base,op='experiment',default_action='b',counts=True));validate_response_v13(r)
        e=r['experiment'];self.assertEqual((e['proposal'],e['no_proposal_reason'],e['check']),('PROPOSED',None,False))
        self.assertEqual(r['api_version'],'brute.api/1.3')

    def test_no_proposal_out_of_scope(self):
        """Bridge O3: after OUT_OF_FAMILY, experiment says NO_PROPOSAL / OUT_OF_SCOPE instead of a bare tie."""
        svc=BruteServiceV030();base=self._session(svc)
        svc.handle(dict(base,op='observe',action='a',observation={'x':1,'y':1}))
        for obs in ({'x':1,'y':0},{'x':0,'y':1},{'x':1,'y':1},{'x':0,'y':0}):
            r=svc.handle(dict(base,op='observe',action='b',observation=obs))
            if r['reason']=='FAMILY_CONTRADICTED':break
        self.assertEqual(r['status'],'OUT_OF_FAMILY')
        e=svc.handle(dict(base,op='experiment'))['experiment']
        self.assertEqual((e['proposal'],e['no_proposal_reason']),('NO_PROPOSAL','OUT_OF_SCOPE'))


if __name__=='__main__':unittest.main()
