"""Tests for the study-043 world dispatch (experiments/worlds_043.py) and the seed-check erratum adjudication
(scripts/check_seeds_043b.py). New file. Development seeds only (10050001-03), outside every study-043 range."""
import unittest
from experiments import worlds_043 as W
from experiments import worlds_039 as W39
from experiments import worlds_040 as W40
from experiments import worlds_026 as W26
from scripts.recount_033 import canon
DEV=(10050001,10050002,10050003)


def same(a,b):return (a.n,a.k,canon(a.transitions,a.emissions,a.start))==(b.n,b.k,canon(b.transitions,b.emissions,b.start))


class Worlds043(unittest.TestCase):
    def test_sizes(self):self.assertEqual(W.SIZES,{'lowobs12':12,'scale16':16,'control_cycle3':3})

    def test_dispatch_equals_frozen_generators(self):
        for s in DEV:
            self.assertTrue(same(W.world(s,'lowobs12'),W40.world(s,'lowobs12')))
            self.assertTrue(same(W.world(s,'scale16'),W39.world(s,'scale16')))
            self.assertTrue(same(W.world(s,'control_cycle3'),W26.world(s,'control_cycle3')))

    def test_lowobs_one_bit(self):
        for s in DEV:
            w=W.world(s,'lowobs12');self.assertEqual((w.n,w.k),(12,3))
            self.assertTrue(all(e in (0,1) for e in w.emissions))
            tr=W.trajectory(w,s,0.0)
            self.assertTrue(all(all(b in (0,1) for b in r) and int(''.join(map(str,r)),2)<=1 for r in tr['readings']))

    def test_unknown_family(self):
        with self.assertRaises(ValueError):W.world(DEV[0],'perm12')

    def test_erratum_adjudication(self):
        from scripts import check_seeds_043b as B
        line='{"cpu_jiffies": {"idle": 1, "user": 10980005}, "wall": 1.0}'
        self.assertEqual(B.paths_of(line,10980005),[('cpu_jiffies','user')])
        self.assertEqual(B.paths_of('{"seed": 10980005}',10980005),[('seed',)])
        self.assertFalse(B.allowed([('seed',)]));self.assertTrue(B.allowed([('cpu_jiffies','user')]))


if __name__=='__main__':unittest.main()
