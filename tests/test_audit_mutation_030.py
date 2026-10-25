"""Mutation test for the study-005 mismatch counter (v0.3.0 errata, review H1): injected single-field errors in distinct
arm traces are each counted, nothing else is flagged, and the untouched traces give a count of 0."""
import sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))


class AuditMutation030(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from experiments.brute_common_005 import STUDY_DIR,load
        from scripts.study005_storage import ensure_raw
        ensure_raw(STUDY_DIR);cls.res=load(STUDY_DIR/'RESULTS.json')

    def test_clean_count_zero(self):
        from scripts.audit_count_030 import count
        out=count(self.res,workers=2,limit=6);self.assertEqual(out['arm_traces_checked'],30);self.assertEqual(out['mismatching_arm_traces'],0)

    def test_injected_errors_are_counted(self):
        from scripts.audit_count_030 import count
        out=count(self.res,workers=2,limit=12,mutate_k=8);m=out['mutation_test']
        self.assertEqual((m['injected'],m['detected_injected'],m['flagged_not_injected']),(8,8,0));self.assertTrue(m['passed'])
        self.assertEqual(out['mismatching_arm_traces'],8)


if __name__=='__main__':unittest.main()
