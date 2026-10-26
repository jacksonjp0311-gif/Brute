import unittest
from scripts.diag_stale_010 import classify_arm,hull_check,non_drift


def rec(step,wrong=False,cwrong=False,**kw):
    r={'step':step,'wrong':wrong,'counterfactual':{'wrong':cwrong},'action':0,'actual_emission_EVALUATOR_ONLY':1,
       'counterfactual_actual_EVALUATOR_ONLY':2,'family_status_after':'supported'};r.update(kw);return r


class DiagStale010(unittest.TestCase):
    def test_nondrift(self):
        self.assertFalse(non_drift(12));self.assertFalse(non_drift(23));self.assertTrue(non_drift(13));self.assertFalse(non_drift(5))

    def test_classify(self):
        tr=[rec(s) for s in range(1,45)];tr[12]=rec(13,wrong=True);tr[24]=rec(25,cwrong=True);tr[22]=rec(23,wrong=True)
        c={'seed':1,'mask_rate':0.1,'arms':{'X':{'trace':tr,'diagnostics':{'drift_events':[23]}}}}
        F=classify_arm(c,'X');self.assertEqual([(x['step'],x['stale_class']) for x in F],[(13,True),(25,False)])

    def test_hull(self):
        tr=[rec(s) for s in range(1,45)];tr[12]['hull_union']={'0':[1],'1':[0,1,2,3]}
        c={'seed':1,'mask_rate':0.1,'arms':{'J8':{'trace':tr,'diagnostics':{}}}}
        h=hull_check(c,'J8');self.assertTrue(h['contained']);self.assertTrue(h['nonvacuous'])
        tr[12]['hull_union']={'0':[0],'1':[2]};self.assertFalse(hull_check(c,'J8')['contained'])
        tr[11]['family_status_after']='grammar_contradicted';self.assertIsNone(hull_check(c,'J8'))


if __name__=='__main__':unittest.main()
