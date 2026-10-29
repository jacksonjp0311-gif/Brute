"""brute.certify/10 (BRUTE_PLAN_024 GAPI10): 'stitched' streaming equals batch and stitched_supports at delta/2 + delta/2;
'lr' and 'anytime' equal brute.certify/9; 3 actions; validation; host-agnostic source; certify.py ... certify9.py unchanged."""
import hashlib,json,unittest
from pathlib import Path
from brute.api.certify10 import Certifier10,certify10,API,METHODS
from brute.api.certify9 import certify9
from brute.stitchedregion import stitched_supports
from tests.test_anytime_0190 import traj
ROOT=Path(__file__).resolve().parents[1]


class Certify100210(unittest.TestCase):
    def test_stitched_stream_equals_batch(self):
        ini,a,o=traj(3,T=20);r=certify10(ini,a,o)
        self.assertEqual((r['api'],r['method']),(API,'stitched'));self.assertEqual(len(r['supports']),21);self.assertTrue(r['soundness']['anytime'])
        L=stitched_supports(ini,a,o,delta_L=0.005,delta_a=0.005);self.assertEqual(r['supports'][:20],L['support']);self.assertEqual(r['m'][:20],L['m'])
        with Certifier10(ini) as c:
            for t,(x,y) in enumerate(zip(a,o)):
                row=c.current();self.assertEqual((row['supports'],row['m'],row['certificates']),(r['supports'][t],r['m'][t],r['certificates'][t]));c.observe(x,y)
        self.assertEqual(r['certificates'][0],[None,None])

    def test_lr_anytime_equal_certify9(self):
        ini,a,o=traj(4,T=16)
        for m in ('lr','anytime'):
            r10=certify10(ini,a,o,method=m);r9=certify9(ini,a,o,method=m)
            self.assertEqual(r10['api'],API);self.assertEqual(r10['method'],m)
            for k in ('supports','unknown','certificates','m','status','observed_bits','steps'):self.assertEqual(r10[k],r9[k],(m,k))

    def test_three_actions(self):
        r=certify10((0,1),[0,1,2,0,1,2],[(1,0),(0,1),(1,1),(1,0),(0,1),(1,1)],num_actions=3)
        self.assertEqual(len(r['supports'][0]),3);self.assertEqual(r['steps'],6)

    def test_validation(self):
        self.assertEqual(METHODS,('stitched','lr','anytime'))
        for kw in ({'num_actions':4},{'family_bound':3},{'burn_in':-1},{'eps_bar':0.5},{'delta':0},{'method':'flat'},{'method':None}):
            with self.assertRaises(ValueError,msg=str(kw)):Certifier10((0,1),**kw)
        with Certifier10((0,1)) as c:
            for bad in ((2,(0,1)),(True,(0,1)),(0,(0,2))):
                with self.assertRaises(ValueError):c.observe(*bad)
        with self.assertRaises(ValueError):certify10((0,1),[0],[])

    def test_host_agnostic(self):
        src=(ROOT/'brute/api/certify10.py').read_text()+(ROOT/'brute/stitchedregion.py').read_text()
        for bad in ('import os','socket','threading','subprocess','open(','multiprocessing'):self.assertNotIn(bad,src)

    def test_older_apis_unchanged(self):
        fz=json.loads((ROOT/'experiments/BRUTE_SOURCE_FREEZE_023.json').read_text())['sha256_files']
        for f in ('brute/api/certify9.py','brute/lrregion.py'):
            self.assertEqual(hashlib.sha256((ROOT/f).read_bytes()).hexdigest(),fz[f],f)


if __name__=='__main__':unittest.main()
