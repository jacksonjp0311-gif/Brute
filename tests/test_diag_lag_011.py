import unittest
from scripts.diag_lag_011 import classify,summarise


class LagDiag011(unittest.TestCase):
    def test_classify(self):
        self.assertEqual(classify(5),('pre_drift',None,None))
        self.assertEqual(classify(12),('drift_step',None,None))
        self.assertEqual(classify(13),('non_drift',12,1))
        self.assertEqual(classify(23)[0],'drift_step')
        self.assertEqual(classify(27),('non_drift',23,4))

    def test_summary(self):
        R=[{'study':'s','arm':'X','seed':1,'mask':0.1,'step':s,'side':'taken','class':classify(s)[0],'d':classify(s)[1],
            'lag':classify(s)[2],'rule':'Y1k','events_between':[],'contradiction_step':40} for s in (13,14,26)]
        S=summarise(R)
        self.assertEqual(S['non_drift_total'],3);self.assertEqual(S['lag_histogram'],{'1':1,'2':1,'3':1})
        self.assertEqual(S['lag_cumulative_fraction'][2],0.6667);self.assertEqual(S['contradicted_after_step'],3)


if __name__=='__main__':unittest.main()
