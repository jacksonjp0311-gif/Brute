"""Deviation #96 corrective test: the study-017 orchestrator stream table with g11 at 6 workers (deviation #92).
tests/test_scripts_017.py (frozen in BRUTE_SOURCE_FREEZE_017) keeps a stale 'g11': (4, ...) literal; this file is the
correct assertion. Reported only; it changes no GTI verdict."""
import unittest
from scripts import run_study_017 as RS


class Streams017R1(unittest.TestCase):
    def test_streams_with_g11_six(self):
        T={t['name']:(t['workers'],t['budget'],t['deps']) for t in RS.tasks()}
        self.assertEqual(T,{'transfer':(4,3000,[]),'gti':(2,3600,[]),'repro':(2,1500,['transfer']),'g11':(6,2400,['transfer'])})
        self.assertEqual((RS.CAP,RS.MAX_WORKERS,RS.G11_WORKERS),(7200,8,6))


if __name__=='__main__':unittest.main()
