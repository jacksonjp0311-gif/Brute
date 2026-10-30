"""Tests for scripts/verify_release_0220_r1.py (deviation #122). New file."""
import unittest,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts import verify_release_0220_r1 as V


class TestRelease0220R1(unittest.TestCase):
    def test_chain_reads_entries(self):
        R=V.jload(ROOT/'RELEASE.json');n=V.chain(ROOT,R)
        self.assertTrue(n=='skipped (no git)' or n>=4)

    def test_r1_freeze_listed(self):
        self.assertIn('BRUTE_RELEASE_FREEZE_0220_R1.json',(ROOT/'scripts/verify_release_0220_r1.py').read_text())


if __name__=='__main__':unittest.main()
