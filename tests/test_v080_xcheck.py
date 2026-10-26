"""v080_xcheck.truncate_arm: prefix restriction of the end-of-trace fields (spot pass, steps 1..N)."""
import unittest
from experiments.v080_xcheck import truncate_arm


def arm(contra=None):
    tr=[{'step':s,'family_status_after':'grammar_contradicted' if contra and s>=contra else 'ok'} for s in range(1,41)]
    return {'trace':tr,'issued':[[3,'a'],[20,'b'],[30,'c']],'retractions':[[30,'c']] if contra else [],
            'diagnostics':{'first_alarm_step':26,'alarm_steps':[26,31],'resume_steps':[10,28],'drift_events':[5,25],
                           'certificates_issued':3,'certificates_retracted':1 if contra else 0}}


class Truncate(unittest.TestCase):
    def test_prefix(self):
        A=arm(contra=33);B=truncate_arm(A,24)
        self.assertEqual(len(B['trace']),24);self.assertEqual(B['trace'],A['trace'][:24])
        self.assertEqual(B['issued'],[[3,'a'],[20,'b']]);self.assertEqual(B['retractions'],[])
        d=B['diagnostics'];self.assertIsNone(d['first_alarm_step']);self.assertEqual(d['alarm_steps'],[])
        self.assertEqual(d['resume_steps'],[10]);self.assertEqual(d['drift_events'],[5])
        self.assertEqual((d['certificates_issued'],d['certificates_retracted']),(2,0))
        self.assertEqual(len(A['trace']),40)          # input untouched

    def test_retraction_kept_when_contradiction_inside(self):
        B=truncate_arm(arm(contra=12),24);self.assertEqual(B['retractions'],[[30,'c']]);self.assertEqual(B['diagnostics']['certificates_retracted'],1)

    def test_full_length_is_identity_on_counts(self):
        A=arm(contra=33);B=truncate_arm(A,40);self.assertEqual(B,A)


if __name__=='__main__':unittest.main()
