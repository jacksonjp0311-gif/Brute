"""Study 069 script tests (new file): adapter resets and readings, hand truth vs live decoder, recount labels, gate helpers."""
import itertools,unittest
from experiments import targets_069 as TG
from experiments import truth_069 as TR
from experiments import brute_study_069 as BS
from scripts.make_gates_069 import adapter_ast_ok,module_imports_ok,truth_reading
from scripts.recount_069 import label
from scripts.truthcheck_069 import truth_readings,minimal
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]


class T(unittest.TestCase):
    def test_fresh_object_per_reset(self):
        t=TG.Target('U3');t.reset();t.act(2);d1=t.dec;self.assertEqual(t.reset(),(0,0));self.assertIsNot(t.dec,d1);self.assertEqual(t.resets,2)
        self.assertEqual(t.act(0),(1,0))                                             # pending E1 discarded by the fresh object

    def test_readings(self):
        self.assertEqual(TG.replay('EJ',[2,2]),[(0,0),(0,0),(1,0)])                 # A1 A1 -> U+3000
        self.assertEqual(TG.replay('GB',[1,2,1,2]),[(0,0)]*4+[(1,0)])               # 81 30 81 30 -> U+0080
        self.assertEqual(TG.replay('U3',[1]),[(0,0),(1,1)])

    def test_truth_vs_live(self):
        for name in TR.TARGETS:
            w=TR.world(name);self.assertTrue(minimal(w))
            for L in range(5):
                for acts in itertools.product(range(3),repeat=L):
                    self.assertEqual([list(x) for x in TG.replay(name,list(acts))],truth_readings(w,acts))
                    self.assertEqual(truth_reading(w,acts),truth_readings(w,acts)[-1])

    def test_recount_labels(self):
        w=TR.world('U3');good={'target':'U3','N':12,'api_label':'ID','transitions':w.transitions,'emissions':w.emissions}
        self.assertEqual(label(good),'ID');bad=dict(good,transitions=[list(r) for r in w.transitions]);bad['transitions'][4][1]=2
        self.assertEqual(label(bad),'WRONG');self.assertEqual(label({'target':'U3','N':12,'api_label':'EXCEEDS_N'}),'WRONG')
        self.assertEqual(label({'target':'EJ','N':8,'api_label':'EXCEEDS_N'}),'EXCEEDS_N');self.assertEqual(label({'killed':True}),'KILL')

    def test_ast_checks(self):
        self.assertEqual(adapter_ast_ok(),[])
        self.assertEqual(module_imports_ok((ROOT/'brute/api/certify32r.py').read_text()),(True,[]))
        self.assertFalse(module_imports_ok('import os')[0]);self.assertFalse(module_imports_ok('open("x")')[0])

    def test_jobs_and_canon(self):
        j=BS.jobs_for('main');self.assertEqual(len(j),31);self.assertEqual(len(set(j)),31);self.assertIn(('U3',12690101,'Sb'),j)
        self.assertEqual(BS.canon({'arm':'S','reads_total':5,'job_wall_informational':1,'n':6}),{'n':6})


if __name__=='__main__':unittest.main()
