import copy,json,unittest
from brute.api import (API_VERSION,BruteService,Status,Reason,validate_response,validate_request,SchemaError,REFUSALS,refusal_text)
from brute.api.schema import REQUEST_SCHEMA,RESPONSE_SCHEMA
from brute.api.service import CALIBRATED_TAU,SOURCE_SHA256
from brute.core.learner import DECLARED_FAMILY
V=API_VERSION
ATT={'family':DECLARED_FAMILY,'issuer':'test','basis':'synthetic'}


def req(op,**kw):return {'api_version':V,'session_id':'s','op':op,**kw}


def drive(svc,k=4,steps=12,mask=lambda i:0,att=None,public=False):
    init=req('initialize',observation={'x':0,'y':0},family={'max_states':k})
    if att:init['attestation']=att
    rs=[svc.handle(init)]
    for i in range(steps):
        a='ab'[i%2]
        rs.append(svc.handle(req('predict',action=a,public=public)))
        rs.append(svc.handle(req('observe',action=a,observation={'x':0,'y':mask(i)})))
    return rs


def key(r):return r['status'] if r['reason'] is None else r['status']+'/'+r['reason']


class ApiContract(unittest.TestCase):
    def test_schema_enums_match_python_enums(self):
        self.assertEqual(RESPONSE_SCHEMA['properties']['status']['enum'],[s.value for s in Status])
        self.assertEqual(RESPONSE_SCHEMA['properties']['reason']['enum'],[None]+[r.value for r in Reason])
        self.assertEqual(set(REFUSALS),{r.value for r in Reason})
        self.assertEqual(RESPONSE_SCHEMA['properties']['api_version']['const'],V)
        self.assertEqual(REQUEST_SCHEMA['properties']['api_version']['const'],V)

    def test_schema_round_trip(self):
        for r in drive(BruteService(),att=ATT,public=True)+drive(BruteService(),k=1):
            back=json.loads(json.dumps(r))
            self.assertEqual(back,r);validate_response(back)
            self.assertEqual(r['refusal_text'],refusal_text(r['reason']))
            if r['evidence']:self.assertEqual(r['evidence']['source_sha256'],SOURCE_SHA256)

    def test_every_forecast_path_maps_to_one_status(self):
        seen={}
        cases={'k4':dict(k=4),'k1':dict(k=1)}
        for name,kw in cases.items():
            for r in drive(BruteService(),**kw):seen.setdefault(key(r),r)
        svc=BruteService(max_prefixes=4);[seen.setdefault(key(r),r) for r in drive(svc)]
        svc=BruteService(tau=-1.0);[seen.setdefault(key(r),r) for r in drive(svc,steps=10)]
        svc=BruteService();drive(svc,steps=12)
        r=svc.handle(req('observe',action='a',observation={'x':1,'y':1}));seen.setdefault(key(r),r)
        r=svc.handle(req('predict',action='a'));seen.setdefault('predict:'+key(r),r)
        for k in ('ACKNOWLEDGED','CERTIFIED','POSSIBLE_SET','ABSTAIN/MARGIN_DISAGREES','ABSTAIN/BOUND_SATURATED',
                  'ABSTAIN/BUDGET_EXHAUSTED','OUT_OF_FAMILY/RESIDUAL_SURPRISE','OUT_OF_FAMILY/FAMILY_CONTRADICTED',
                  'predict:OUT_OF_FAMILY/FAMILY_CONTRADICTED'):
            self.assertIn(k,seen)
        for k,r in seen.items():
            self.assertEqual(r['certificate'] is not None,r['status']=='CERTIFIED',k)
            if r['status']=='POSSIBLE_SET':self.assertGreater(len(r['support']),1)
            if r['status']=='OUT_OF_FAMILY' and r['op']=='predict':
                self.assertEqual([x['p'] for x in r['probabilities']].count(.25),4)  # uniform when contradicted
            if r['probabilities']:self.assertGreaterEqual(min(x['p'] for x in r['probabilities']),.005-1e-15)
        r=seen['OUT_OF_FAMILY/FAMILY_CONTRADICTED'];self.assertEqual(r['evidence']['surviving_rows'],0)
        self.assertGreater(len(r['retractions']),0)
        self.assertTrue(seen['ABSTAIN/BOUND_SATURATED']['evidence']['saturated'])
        self.assertFalse(seen['ABSTAIN/MARGIN_DISAGREES']['evidence']['margin']['agrees'])
        self.assertTrue(seen['OUT_OF_FAMILY/RESIDUAL_SURPRISE']['evidence']['residual']['alarm'])

    def test_public_needs_attestation(self):
        plain=[r for r in drive(BruteService(),public=True) if r['op']=='predict']
        self.assertIn('ABSTAIN/UNATTESTED_SCOPE',{key(r) for r in plain})
        self.assertNotIn('CERTIFIED',{key(r) for r in plain})
        att=[r for r in drive(BruteService(),att=ATT,public=True) if r['status']=='CERTIFIED']
        self.assertTrue(att and all(r['certificate']['kind']=='public' and r['evidence']['attestation_id'] for r in att))
        cond=[r for r in drive(BruteService()) if r['status']=='CERTIFIED']
        self.assertTrue(cond and all(r['certificate']['kind']=='conditional' for r in cond))
        wrong=dict(ATT,family='deterministic-moore<=9/stationary')
        self.assertNotIn('CERTIFIED',{key(r) for r in drive(BruteService(),att=wrong,public=True)})

    def test_retry_drops_attestation(self):
        svc=BruteService();drive(svc,att=ATT,public=True)
        r=svc.handle(req('retry',family={'max_states':5}))
        self.assertEqual(r['status'],'ACKNOWLEDGED');self.assertIsNone(r['evidence']['attestation_id'])
        self.assertEqual(r['evidence']['family_scope'],'deterministic-moore<=5/stationary')

    def test_error_on_bad_input(self):
        svc=BruteService()
        bad=[None,[],{},req('predict',action='a'),req('fly'),dict(req('snapshot'),api_version='brute.api/2.0'),
             dict(req('snapshot'),extra=1),req('initialize',observation={'x':2,'y':0}),req('initialize',observation={'x':0})]
        expect=['INVALID_REQUEST']*3+['NOT_INITIALIZED']+['INVALID_REQUEST']*5
        for b,e in zip(bad,expect):
            r=svc.handle(b);validate_response(r)
            self.assertEqual((r['status'],r['reason']),('ERROR',e),b)
        svc.handle(req('initialize',observation={'x':0,'y':0}))
        for b in (req('predict',action='z'),req('observe',action='a',observation={'x':0,'y':True}),
                  req('initialize',observation={'x':0,'y':0})):
            r=svc.handle(b);self.assertEqual((r['status'],r['reason']),('ERROR','INVALID_REQUEST'),b)
        self.assertEqual(svc.handle(req('snapshot'))['evidence']['evidence_count'],1)  # bad requests left no evidence

    def test_validator_rejects_malformed(self):
        r=BruteService().handle(req('snapshot'))
        for mut in (lambda d:d.update(status='MAYBE'),lambda d:d.pop('refusal_text'),lambda d:d.update(extra=1),
                    lambda d:d.update(reason='GUESS')):
            d=copy.deepcopy(r);mut(d)
            with self.assertRaises(SchemaError):validate_response(d)
        with self.assertRaises(SchemaError):validate_request({'api_version':V,'session_id':'s','op':'predict','action':3})

    def test_calibrated_tau_matches_study(self):
        from pathlib import Path
        cal=json.loads((Path(__file__).resolve().parents[1]/'results/study-002/CALIBRATION.json').read_text())
        self.assertEqual(CALIBRATED_TAU,cal['tau'])


if __name__=='__main__':unittest.main()
