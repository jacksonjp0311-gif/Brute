import json,re,unittest
from functools import lru_cache
from pathlib import Path
from adapters.language import render,check,resolve
from adapters.language.render import fill
from brute.api import API_VERSION,BruteService
ROOT=Path(__file__).resolve().parents[1]
V=API_VERSION


def req(op,**kw):return {'api_version':V,'session_id':'s','op':op,**kw}


@lru_cache(maxsize=1)
def responses():
    """Responses from replayed study-002 traces (one case per family) plus synthetic edge paths."""
    out=[]
    cases=json.loads((ROOT/'results/study-002/SCIENTIFIC.json').read_text())['cases']
    picked={}
    for c in cases:
        if c['mask_rate']==0.35:picked.setdefault(c['family'],c)
    for c in picked.values():
        svc=BruteService();out.append(svc.handle(req('initialize',observation={'x':c['initial_visible'][0],'y':c['initial_visible'][1]})))
        for r in c['trace']:
            a='ab'[r['action']]
            out.append(svc.handle(req('predict',action=a)))
            out.append(svc.handle(req('observe',action=a,observation={'x':r['observed'][0],'y':r['observed'][1]})))
    for kw in ({'tau':-1.0},{'max_prefixes':4}):
        svc=BruteService(**kw);svc.handle(req('initialize',observation={'x':0,'y':0}))
        for i in range(10):
            out.append(svc.handle(req('predict',action='a')));out.append(svc.handle(req('observe',action='a',observation={'x':0,'y':0})))
    svc=BruteService();out.append(svc.handle(req('initialize',observation={'x':0,'y':0},family={'max_states':1})))
    for i in range(8):out.append(svc.handle(req('predict',action='a',public=True)));svc.handle(req('observe',action='a',observation={'x':0,'y':0}))
    svc=BruteService();svc.handle(req('initialize',observation={'x':0,'y':0}))
    for i in range(10):out.append(svc.handle(req('predict',action='a',public=True)));svc.handle(req('observe',action='a',observation={'x':0,'y':0}))
    out.append(svc.handle(req('fly')));out.append(BruteService().handle(req('snapshot')))
    return out


def statuses():return {r['status'] if r['reason'] is None else r['status']+'/'+r['reason'] for r in responses()}

VALUE=re.compile(r'\bx=\d, y=\d\b')


class AdapterGrounding(unittest.TestCase):
    def test_covers_all_statuses(self):
        need={'ACKNOWLEDGED','CERTIFIED','POSSIBLE_SET','ABSTAIN/MARGIN_DISAGREES','ABSTAIN/BOUND_SATURATED','ABSTAIN/BUDGET_EXHAUSTED',
              'ABSTAIN/UNATTESTED_SCOPE','OUT_OF_FAMILY/FAMILY_CONTRADICTED','OUT_OF_FAMILY/RESIDUAL_SURPRISE','ERROR/INVALID_REQUEST','ERROR/NOT_INITIALIZED'}
        self.assertLessEqual(need,statuses())

    def test_every_claim_has_field_refs(self):
        for r in responses():
            claims=render(r);self.assertTrue(claims,r['status'])
            for c in claims:
                self.assertTrue(c['field_refs'])
                for p in c['field_refs']:self.assertIsNotNone(resolve(r,p))
            self.assertEqual(check(r,claims),[])

    def test_claim_text_is_template_of_refs(self):
        for r in responses():
            for c in render(r):self.assertEqual(fill(c['template'],r,c['field_refs']),c['text'])

    def test_refusal_passthrough_verbatim(self):
        n=0
        for r in responses():
            if r['status'] in ('ABSTAIN','OUT_OF_FAMILY','ERROR'):
                n+=1;claims=render(r)
                self.assertIn(r['refusal_text'],[c['text'] for c in claims])
                self.assertFalse(any(VALUE.search(c['text']) for c in claims))
                self.assertFalse(any(c['template'].startswith('certified') for c in claims))
                altered=[dict(c,text=c['text'].rstrip('.')+'!') if c['template']=='refusal' else c for c in claims]
                self.assertTrue(check(r,altered))
        self.assertGreater(n,0)

    def test_checker_rejects_unbacked_sentence(self):
        rs=responses()
        r=next(x for x in rs if x['status']=='CERTIFIED' and x['certificate']['kind']=='conditional')
        claims=render(r);self.assertEqual(check(r,claims),[])
        self.assertTrue(check(r,claims+[{'text':'The next reading will almost certainly be 1.','field_refs':['/status']}]))
        self.assertTrue(check(r,claims+[{'text':'The next reading will almost certainly be 1.','field_refs':['/status'],'template':'free'}]))
        self.assertTrue(check(r,claims+[{'text':'x','field_refs':['/refusal_text'],'template':'refusal'}]))  # cited null
        pub=[{'text':fill('certified.conditional',r,['/certificate/conditional_on','/certificate/value']).replace('If the world is in the family','Within the attested scope'),
              'field_refs':['/certificate/conditional_on','/evidence/attestation_id','/certificate/value'],'template':'certified.public'}]
        self.assertTrue(check(r,claims+pub))  # public wording on a conditional certificate
        p=next(x for x in rs if x['status']=='POSSIBLE_SET')
        forged=[{'text':fill('certified.conditional',r,['/certificate/conditional_on','/certificate/value']),
                 'field_refs':['/certificate/conditional_on','/certificate/value'],'template':'certified.conditional'}]
        self.assertTrue(check(p,render(p)+forged))

    def test_no_upgrade_of_status(self):
        for r in responses():
            for c in render(r):
                if r['status']=='POSSIBLE_SET':
                    self.assertNotRegex(c['text'].lower(),r'\b(certain|will)\b')
                if r['status']!='CERTIFIED':
                    found=VALUE.findall(c['text'])
                    self.assertFalse(len(found)==1,f"single value named under {r['status']}: {c['text']}")


if __name__=='__main__':unittest.main()
