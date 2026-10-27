"""run_study_015_R1 (deviation #72): only g11's worker count changes; the base orchestrator is untouched."""
import hashlib,unittest
from pathlib import Path
from scripts import run_study_015_R1 as R
ROOT=Path(__file__).resolve().parents[1]


class OrchestratorR1(unittest.TestCase):
    def test_streams(self):
        T={t['name']:(t['workers'],t['budget'],t['deps']) for t in R.tasks()}
        self.assertEqual(T,{'transfer':(4,3000,[]),'gti':(2,3600,[]),'repro':(2,1500,['transfer']),'g11':(4,2400,['transfer'])})
        self.assertEqual((R.CAP,R.MAX_WORKERS),(7200,8))

    def test_g11_command_uses_4_workers(self):
        g=[t for t in R.tasks() if t['name']=='g11'][0]['cmd'];i=g.index('--workers');self.assertEqual(g[i+1],'4')

    def test_peak_workers(self):
        T={t['name']:t['workers'] for t in R.tasks()}
        self.assertLessEqual(T['transfer']+T['gti'],8);self.assertLessEqual(T['gti']+T['repro']+T['g11'],8)

    def test_base_bytes_pinned(self):
        self.assertEqual(hashlib.sha256((ROOT/'scripts/run_study_015.py').read_bytes()).hexdigest(),R.BASE_SHA256)


if __name__=='__main__':unittest.main()
