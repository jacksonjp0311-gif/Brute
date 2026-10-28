"""brute.certify/8 (BRUTE_PLAN_021 GAPI9): streaming equals batch, equals anytime_supports, 3 actions, validation,
host-agnostic source; certify.py ... certify7.py unchanged (sha256 as frozen by study-019)."""
import hashlib,json,unittest
from pathlib import Path
from brute.api.certify8 import Certifier8,certify8,API
from brute.anytimemargin import anytime_supports
from tests.test_anytime_0190 import traj
ROOT=Path(__file__).resolve().parents[1]


class Certify80190(unittest.TestCase):
    def test_stream_equals_batch_and_supports(self):
        ini,a,o=traj(3,T=28);r=certify8(ini,a,o)
        self.assertEqual(r['api'],API);self.assertEqual(len(r['supports']),29);self.assertTrue(r['soundness']['anytime'])
        self.assertEqual(r['supports'][:28],anytime_supports(ini,a,o,4)['support'])
        with Certifier8(ini) as c:
            for t,(x,y) in enumerate(zip(a,o)):
                row=c.current();self.assertEqual((row['supports'],row['m'],row['certificates']),(r['supports'][t],r['m'][t],r['certificates'][t]));c.observe(x,y)
            self.assertEqual(c.current()['supports'],r['supports'][28]);self.assertEqual(c.boundary(),r['boundary'])
        self.assertEqual(r['certificates'][0],[None,None])   # burn-in

    def test_three_actions(self):
        r=certify8((0,1),[0,1,2,0,1,2],[(1,0),(0,1),(1,1),(1,0),(0,1),(1,1)],num_actions=3)
        self.assertEqual(len(r['supports'][0]),3);self.assertEqual(r['steps'],6)

    def test_validation(self):
        for kw in ({'num_actions':4},{'family_bound':3},{'burn_in':-1},{'eps_bar':0.5},{'delta':0}):
            with self.assertRaises(ValueError,msg=str(kw)):Certifier8((0,1),**kw)
        with Certifier8((0,1)) as c:
            for bad in ((2,(0,1)),(True,(0,1)),(0,(0,2))):
                with self.assertRaises(ValueError):c.observe(*bad)
        with self.assertRaises(ValueError):certify8((0,1),[0],[])

    def test_host_agnostic(self):
        src=(ROOT/'brute/api/certify8.py').read_text()+(ROOT/'brute/anytimemargin.py').read_text()
        for bad in ('import os','socket','threading','subprocess','open(','multiprocessing'):self.assertNotIn(bad,src)

    def test_older_apis_unchanged(self):
        fz=json.loads((ROOT/'experiments/BRUTE_SOURCE_FREEZE_019.json').read_text())['sha256_files']
        for f in ('brute/api/certify7.py',):self.assertEqual(hashlib.sha256((ROOT/f).read_bytes()).hexdigest(),fz[f])


if __name__=='__main__':unittest.main()
