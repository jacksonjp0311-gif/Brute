"""v0.22.0: brute.certify/11 (method 'betting' default; other methods delegate unchanged)."""
import inspect,unittest
from brute.api import certify11 as C11
from brute.api.certify10 import certify10
from brute.api.certify9 import certify9

INIT,ACTS,OBS=(0,1),[0,1,0,1,1,0,0,1,1,1,0],[(0,1),(1,None),(0,1),(1,0),(None,1),(0,1),(1,0),(0,0),(1,1),(0,1),(1,None)]
K=('supports','unknown','certificates','status','m','steps')


class Certify11(unittest.TestCase):
    def test_api_and_methods(self):
        d=C11.certify11(INIT,ACTS,OBS);self.assertEqual(d['api'],'brute.certify/11');self.assertEqual(d['method'],'betting')
        self.assertEqual(C11.METHODS,('betting','stitched','lr','anytime'))
        self.assertEqual(inspect.signature(C11.certify11).parameters['method'].default,'betting')

    def test_delegation(self):
        s=C11.certify11(INIT,ACTS,OBS,method='stitched');s10=certify10(INIT,ACTS,OBS)
        l=C11.certify11(INIT,ACTS,OBS,method='lr');r9=certify9(INIT,ACTS,OBS)
        a=C11.certify11(INIT,ACTS,OBS,method='anytime');a9=certify9(INIT,ACTS,OBS,method='anytime')
        for k in K:self.assertEqual(s.get(k),s10.get(k));self.assertEqual(l.get(k),r9.get(k));self.assertEqual(a.get(k),a9.get(k))

    def test_unknown_method(self):
        with self.assertRaises(Exception):C11.certify11(INIT,ACTS,OBS,method='nope')

    def test_host_agnostic(self):
        src=inspect.getsource(C11)
        for x in ('import os','socket','threading','subprocess','open(','multiprocessing'):self.assertNotIn(x,src)


if __name__=='__main__':unittest.main()
