"""Tests of the study-006 second implementation (experiments/v040_reference.py). No brute import."""
import unittest
from pathlib import Path
from experiments import v040_reference as R


class Perm4(unittest.TestCase):
    def test_actions_are_bijections_and_one_aliased_pair(self):
        for seed in range(1600001,1600025):
            w=R.ref_perm4(seed)
            for b in (0,1):self.assertEqual(sorted(w.transitions[s][b] for s in range(4)),[0,1,2,3])
            self.assertEqual(len(set(w.emissions)),3);self.assertEqual(w.family,'perm4')


class Alarm(unittest.TestCase):
    def test_resume_needs_W_low_residuals_and_support(self):
        a=R._Alarm(1.0,2,True)
        a.push(1,0.5,'supported','supported');a.push(2,3.0,'supported','supported')   # R=1.75 > 1 -> set
        self.assertTrue(a.on);self.assertEqual(a.sets,[2])
        a.push(3,0.0,'supported','supported')            # R=1.5 > tau, run stays 0
        a.push(4,0.0,'supported','supported')            # R=0 -> run 1
        self.assertTrue(a.on)
        a.push(5,0.0,'supported','budget_exhausted')     # run 2 but margin not supported
        self.assertTrue(a.on)
        a.push(6,0.0,'supported','supported')            # run 3 >= 2 and supported -> clear
        self.assertFalse(a.on);self.assertEqual(a.resumes,[6]);self.assertTrue(a.ever)
        a.push(7,5.0,'supported','supported');self.assertTrue(a.on);self.assertEqual(a.sets,[2,7])

    def test_no_resume_mode_is_permanent(self):
        a=R._Alarm(1.0,1,False);a.push(1,2.0,'supported','supported');a.push(2,0.0,'supported','supported')
        self.assertTrue(a.on)


RES=R.STUDY_DIR/'RESULTS.json'


@unittest.skipUnless(RES.exists(),'study-006 not sealed in this checkout (restore it first)')
class OnSealed(unittest.TestCase):
    def test_count_and_mutation_on_a_slice(self):
        rep=R.run(R.STUDY_DIR,workers=4,limit=12,mutate_k=8)
        self.assertEqual(rep['mismatching_arm_traces'],0,rep['mismatches'][:3])
        self.assertTrue(rep['mutation_test']['passed'],rep['mutation_test'])


if __name__=='__main__':unittest.main()
