"""Tests for the study-028 runner and scoring scripts (v0.25.0). New file."""
import copy,json,tempfile,unittest
from pathlib import Path
from experiments.brute_study_028 import run_case,jobs_for
from experiments.brute_common_028 import load,PLAN
from scripts.recount_028 import recount_case
from scripts import make_gates_028 as MG
from scripts import make_freeze_028 as MF
from scripts import run_reference_028 as RR
ROOT=Path(__file__).resolve().parents[1]


class Recount(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        c=run_case(9490001,'control_cycle3',0.0);c['block']='smoke';cls.c=json.loads(json.dumps(c))

    def test_arms_and_reproduces(self):
        self.assertEqual(set(self.c['arms']),{'S3','S3_tight','S2','S1'})
        per,bad=recount_case(self.c);self.assertEqual(bad,[]);self.assertEqual(set(per),{'S3','S3_tight','S2','S1'})
        self.assertIn('timing_informational',self.c['arms']['S3']);self.assertIn('solver_wins',self.c['arms']['S3'])

    def test_tamper_detected(self):
        c=copy.deepcopy(self.c);a=c['arms']['S3'];i=next(i for i in range(176) if a['unk'][i][0]==0)
        a['cert'][i][0]=(a['cert'][i][0] or 0)+1;_,bad=recount_case(c);self.assertTrue(bad)
        c=copy.deepcopy(self.c);c['arms']['S1']['F']+=1;_,bad=recount_case(c);self.assertTrue(bad)

    def test_clause_a(self):
        for o in ('S2','S1'):
            cmpd,mis,exc=MG.clause_a(self.c,o);self.assertEqual(mis,0);self.assertGreater(cmpd,0)
        self.assertEqual(MG.truth_missing(self.c)[1],0)
        c=copy.deepcopy(self.c);i=next(i for i in range(176) if c['arms']['S3']['unk'][i][1]==0 and c['arms']['S2']['unk'][i][1]==0)
        c['arms']['S3']['sup'][i][1]=[9];self.assertEqual(MG.clause_a(c,'S2')[1],1)

    def test_reference_slot(self):
        r=RR._s3_as_s2(self.c);self.assertEqual(set(r['arms']),{'S2'});self.assertIs(r['arms']['S2'],self.c['arms']['S3'])


class Gates(unittest.TestCase):
    def test_empty_study_fails_incomplete(self):
        with tempfile.TemporaryDirectory() as d:g=MG.build(Path(d))
        self.assertFalse(g['all_gated_pass'])
        for k in ('GQB','GSC3_headline','G10','GS_ref13','GTI','G_RT','G_recount','GAPI13'):
            self.assertFalse(g['gates'][k]['pass']);self.assertIn('INCOMPLETE',g['gates'][k].get('reason',''))

    def test_api_probe(self):
        p=MG.api_probe();self.assertIsNone(p['error']);self.assertEqual(p['searches'],['region','s2','s3'])
        self.assertTrue(p['region_equals_certify12']);self.assertTrue(p['s2_equals_certify12']);self.assertTrue(p['s3_equals_s2_small'])

    def test_bootstrap(self):
        self.assertEqual(MG.boot_mean([0.5]*12),[0.5,0.5]);lo,hi=MG.boot_mean([-0.2,-0.1,-0.3,0.0]*3);self.assertLess(lo,hi);self.assertLess(hi,0.0)


class Jobs(unittest.TestCase):
    def test_counts(self):
        P=load(PLAN);j=jobs_for(P,'main');self.assertEqual(len(j),51)
        self.assertEqual(sum(1 for x in j if x[0]=='stress'),9);self.assertEqual(len(jobs_for(P,'smoke')),7)


class Freeze(unittest.TestCase):
    def test_files_exist(self):
        for f in MF.FILES:
            if f not in ('experiments/COMMIT_ORDER_028.json',):self.assertTrue((ROOT/f).exists(),f)


if __name__=='__main__':unittest.main()
