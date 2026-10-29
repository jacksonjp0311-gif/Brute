"""v0.20.0 release checks for verify_release_0200_r1 (deviation #113). New file; tests/test_release_0200.py stays frozen.
Its test_short_verify_passes fails by design (the frozen git_order bug); its corruption matrix (git=False) still applies."""
import sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common import VerificationError
from scripts import verify_release_0200_r1 as R1
from scripts.verify_release_060 import jload


class Release0200R1(unittest.TestCase):
    def test_short_verify_passes(self):
        out=R1.verify();self.assertEqual(out['status'],'passed');self.assertEqual(out['process_order']['dual_role_commits'],['9e0ca70'])

    def test_frozen_verifier_reports_the_known_bug(self):
        import scripts.verify_release_0200 as V
        with self.assertRaisesRegex(VerificationError,'reference_1 and implementation_0 are the same commit'):V.git_order(ROOT,jload(ROOT/'RELEASE.json'))

    def test_no_leak_into_frozen_module(self):
        import scripts.verify_release_0200 as V;R1.verify();self.assertIsNot(V.git_order,R1.git_order)

    def test_other_duplicates_still_rejected(self):
        rel=dict(jload(ROOT/'RELEASE.json'));rel['seal_commit']=rel['source_freeze_commit']
        with self.assertRaises(VerificationError):R1.git_order(ROOT,rel)


if __name__=='__main__':unittest.main()
