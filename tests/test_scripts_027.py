"""Tests for the study-027 scoring scripts (v0.24.0). New file."""
import copy,json,tempfile,unittest
from pathlib import Path
from experiments.brute_study_027 import run_case
from scripts.recount_027 import recount_case
from scripts import make_gates_027 as MG
from scripts import make_freeze_027 as MF
ROOT=Path(__file__).resolve().parents[1]


class Recount(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        c=run_case(9390001,'control_cycle3',0.0);c['block']='smoke';cls.c=json.loads(json.dumps(c))

    def test_reproduces(self):
        per,bad=recount_case(self.c);self.assertEqual(bad,[]);self.assertEqual(set(per),{'S1','S2','S2_tight'})

    def test_tamper_detected(self):
        c=copy.deepcopy(self.c);a=c['arms']['S2'];i=next(i for i in range(176) if a['unk'][i][0]==0)
        a['cert'][i][0]=(a['cert'][i][0] or 0)+1;_,bad=recount_case(c);self.assertTrue(bad)
        c=copy.deepcopy(self.c);c['arms']['S1']['F']+=1;_,bad=recount_case(c);self.assertTrue(bad)

    def test_clause_a(self):
        cmpd,mis,exc=MG.clause_a(self.c);self.assertEqual(mis,0);self.assertGreater(cmpd,0)
        c=copy.deepcopy(self.c);i=next(i for i in range(176) if c['arms']['S2']['unk'][i][1]==0 and c['arms']['S1']['unk'][i][1]==0)
        c['arms']['S2']['sup'][i][1]=[9];self.assertEqual(MG.clause_a(c)[1],1)


class Gates(unittest.TestCase):
    def test_empty_study_fails_incomplete(self):
        with tempfile.TemporaryDirectory() as d:
            g=MG.build(Path(d))
        self.assertFalse(g['all_gated_pass'])
        for k in ('GSC_headline','G10','GS_ref12','GTI','G_RT','G_recount','GAPI12'):
            self.assertFalse(g['gates'][k]['pass']);self.assertIn('INCOMPLETE',g['gates'][k].get('reason',''))

    def test_api_probe_and_older_api(self):
        p=MG.api_probe();self.assertIsNone(p['error']);self.assertEqual(p['searches'],['region','s2']);self.assertTrue(p['region_equals_certify11'])


class Freeze(unittest.TestCase):
    def test_files_exist(self):
        for f in MF.FILES:
            if f not in ('experiments/COMMIT_ORDER_027.json','docs/research/BRUTE_DEVIATIONS_027_126.md'):self.assertTrue((ROOT/f).exists(),f)


if __name__=='__main__':unittest.main()
