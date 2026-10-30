"""v0.23.0: brute.certify/12 (search='region' = certify/11 unchanged; search='s2' on the S2 exact search)."""
import inspect,unittest
from brute.api import certify12 as C12
from brute.api.certify11 import certify11
from brute.region import RegionSpace

INIT,ACTS,OBS=(0,1),[0,1,0,1,1,0,0,1,1,1,0],[(0,1),(1,None),(0,1),(1,0),(None,1),(0,1),(1,0),(0,0),(1,1),(0,1),(1,None)]
K=('supports','unknown','certificates','status','m','steps')


class Certify12(unittest.TestCase):
    def test_region_default_equals_11(self):
        d=C12.certify12(INIT,ACTS,OBS);d11=certify11(INIT,ACTS,OBS)
        self.assertEqual(d['api'],'brute.certify/12');self.assertEqual(d['search'],'region');self.assertEqual(d['method'],'betting')
        for k in K:self.assertEqual(d[k],d11[k])
        s=C12.certify12(INIT,ACTS,OBS,method='lr');s11=certify11(INIT,ACTS,OBS,method='lr')
        for k in K:self.assertEqual(s[k],s11[k])

    def test_s2_exact_equals_regionk(self):
        d=C12.certify12(INIT,ACTS,OBS,family_bound=3,search='s2');self.assertEqual(d['method'],'exact')
        self.assertEqual(d['soundness']['kind'],'exact')
        R=RegionSpace(3,k=2,s=2);R.initialize(INIT);ref=[]
        for a,o in zip(ACTS+[None],OBS+[None]):
            R.unk=0;row=[R.predict_support(b) for b in range(2)];ref.append([None if x is None else tuple(x) for x in row])
            if a is not None:R.observe(a,o)
        R.close()
        for i,(r,u) in enumerate(zip(d['supports'],d['unknown'])):
            if u==[0,0]:self.assertEqual([None if x is None else tuple(x) for x in r],ref[i],i)

    def test_s2_certificate_on_cycle(self):
        acts=[0]*30;obs=[((i+1)%3>>1&1,(i+1)%3&1) for i in range(30)]
        d=C12.certify12((0,0),acts,obs,num_actions=1+1,family_bound=3,search='s2')
        self.assertTrue(any(c is not None for row in d['certificates'] for c in row))
        for t,row in enumerate(d['certificates']):
            if row[0] is not None:self.assertEqual(row[0],(t+1)%3)

    def test_s2_betting_runs(self):
        d=C12.certify12(INIT,ACTS,OBS,family_bound=3,search='s2',method='betting')
        self.assertEqual(d['soundness']['kind'],'probabilistic');self.assertEqual(len(d['supports']),len(ACTS)+1)

    def test_refusals(self):
        for kw in ({'search':'x'},{'search':'s2','method':'lr'},{'search':'s2','family_bound':17},{'search':'s2','num_actions':5}):
            with self.assertRaises(ValueError):C12.certify12(INIT,ACTS,OBS,**kw)

    def test_host_agnostic(self):
        src=inspect.getsource(C12)
        for x in ('import os','socket','threading','subprocess','open(','multiprocessing'):self.assertNotIn(x,src)


if __name__=='__main__':unittest.main()
