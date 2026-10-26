"""scripts/feasibility_011.py on smoke seeds 4190028-4190030 only: job grid, one measurement, CLI checkpoint + summary."""
import json,tempfile,unittest
from pathlib import Path
from experiments.brute_common_011 import load,PLAN
import scripts.feasibility_011 as F


class Feasibility011(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.plan=load(PLAN)

    def test_feasibility_smoke(self):
        J=F.jobs(self.plan,smoke=True);self.assertEqual({j[0] for j in J},{4190028,4190029,4190030})
        self.assertEqual(len(F.jobs(self.plan)),36*4)
        r=F.measure(4190028,6,8);self.assertIs(r['feasible'],True);self.assertEqual(r['T'],8)
        d=Path(tempfile.mkdtemp());F.main(['--checkpoint',str(d/'ck.jsonl'),'--output',str(d/'F.json'),'--smoke','--limit','2'])
        rep=json.loads((d/'F.json').read_text());self.assertTrue(rep['smoke']);self.assertEqual(rep['measurements'],2)
        self.assertTrue(rep['all_feasible'])


if __name__=='__main__':unittest.main()
