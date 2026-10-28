"""brute.certify/9 (BRUTE_PLAN_023 GAPI10): 'lr' streaming equals batch and lr_supports at delta/2 + delta/2; 'anytime'
equals brute.certify/8; 3 actions; validation; host-agnostic source; certify.py ... certify8.py unchanged."""
import hashlib,json,unittest
from pathlib import Path
from brute.api.certify9 import Certifier9,certify9,API,METHODS
from brute.api.certify8 import certify8
from brute.lrregion import lr_supports
from tests.test_anytime_0190 import traj
ROOT=Path(__file__).resolve().parents[1]


class Certify90200(unittest.TestCase):
    def test_lr_stream_equals_batch(self):
        ini,a,o=traj(3,T=20);r=certify9(ini,a,o)
        self.assertEqual((r['api'],r['method']),(API,'lr'));self.assertEqual(len(r['supports']),21);self.assertTrue(r['soundness']['anytime'])
        L=lr_supports(ini,a,o,delta_L=0.005,delta_a=0.005);self.assertEqual(r['supports'][:20],L['support']);self.assertEqual(r['m'][:20],L['m'])
        with Certifier9(ini) as c:
            for t,(x,y) in enumerate(zip(a,o)):
                row=c.current();self.assertEqual((row['supports'],row['m'],row['certificates']),(r['supports'][t],r['m'][t],r['certificates'][t]));c.observe(x,y)
        self.assertEqual(r['certificates'][0],[None,None])

    def test_anytime_equals_certify8(self):
        ini,a,o=traj(4,T=16);r9=certify9(ini,a,o,method='anytime');r8=certify8(ini,a,o)
        self.assertEqual(r9['api'],API);self.assertEqual(r9['method'],'anytime')
        for k in ('supports','unknown','certificates','m','status','observed_bits','steps'):self.assertEqual(r9[k],r8[k],k)

    def test_three_actions(self):
        r=certify9((0,1),[0,1,2,0,1,2],[(1,0),(0,1),(1,1),(1,0),(0,1),(1,1)],num_actions=3)
        self.assertEqual(len(r['supports'][0]),3);self.assertEqual(r['steps'],6)

    def test_validation(self):
        self.assertEqual(METHODS,('lr','anytime'))
        for kw in ({'num_actions':4},{'family_bound':3},{'burn_in':-1},{'eps_bar':0.5},{'delta':0},{'method':'flat'},{'method':None}):
            with self.assertRaises(ValueError,msg=str(kw)):Certifier9((0,1),**kw)
        with Certifier9((0,1)) as c:
            for bad in ((2,(0,1)),(True,(0,1)),(0,(0,2))):
                with self.assertRaises(ValueError):c.observe(*bad)
        with self.assertRaises(ValueError):certify9((0,1),[0],[])

    def test_host_agnostic(self):
        src=(ROOT/'brute/api/certify9.py').read_text()+(ROOT/'brute/lrregion.py').read_text()
        for bad in ('import os','socket','threading','subprocess','open(','multiprocessing'):self.assertNotIn(bad,src)

    def test_older_apis_unchanged(self):
        fz=json.loads((ROOT/'experiments/BRUTE_SOURCE_FREEZE_021.json').read_text())['sha256_files']
        for f in ('brute/api/certify8.py','brute/anytimemargin.py'):
            self.assertEqual(hashlib.sha256((ROOT/f).read_bytes()).hexdigest(),fz[f],f)


if __name__=='__main__':unittest.main()
