"""brute.baseline/32t tests (new file): the textbook Rivest-Schapire reset-free learner on hand truths, h extension, caps, interface."""
import unittest
from brute.api import baseline32t as B
from brute.api.certify20b import reading_of
from brute.api.certify32r import equivalent
from experiments import truth_069 as TR


def drive(T,E,N,seed=1,cap=B.STEP_CAP):
    s=0;c=B.Baseline32T(reading_of(E[0],2),len(T[0]),N,2,seed=seed,step_cap=cap);w=c.propose();states=[0]
    while w is not None:
        for a in w:s=T[s][a];states.append(s);c.observe(a,reading_of(E[s],2))
        w=c.next()
    return c,states


class T(unittest.TestCase):
    def test_learns_truths(self):
        for name in TR.TARGETS:
            w=TR.world(name);N=TR.N_TRUE[name]+1;c,st=drive(w.transitions,w.emissions,N);r=c.result()
            self.assertEqual(r['label'],'ID');self.assertFalse(r['soundness']['resets'])
            self.assertTrue(equivalent(r['transitions'],r['emissions'],w.transitions,w.emissions,0,st[r['origin_step']])[0])

    def test_h_extends(self):
        w=TR.world('W16');c,_=drive(w.transitions,w.emissions,8);r=c.result()
        self.assertGreaterEqual(r['restarts'],1);self.assertEqual(len(c.h_history),r['restarts']);self.assertEqual(c.h_history[-1]['h'],r['h'])

    def test_step_cap(self):
        w=TR.world('U3');c,_=drive(w.transitions,w.emissions,7,cap=50);self.assertEqual(c.result()['label'],'QCAP')

    def test_interface(self):
        c=B.Baseline32T((0,0),3,7,2)
        with self.assertRaises(ValueError):c.observe(0,(0,0))
        with self.assertRaises(ValueError):c.result()


if __name__=='__main__':unittest.main()
