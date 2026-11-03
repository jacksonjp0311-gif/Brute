"""Study 068 script tests (new file): adapter public-interface readings, hand truth vs live decoder, recount labelling, adapter AST."""
import unittest
from experiments import targets_068 as TG
from experiments import truth_068 as TR
from experiments.brute_study_058 import truth_label
from scripts.make_gates_068 import adapter_ast_ok,truth_readings
from scripts.recount_068 import reach
import itertools


class T(unittest.TestCase):
    def test_readings(self):
        self.assertEqual(TG.reading(''),(0,0));self.assertEqual(TG.reading('A'),(1,0));self.assertEqual(TG.reading('\ufffdA'),(1,1))
        self.assertEqual(TG.replay('U3',[2,1,1]),[(0,0),(0,0),(0,0),(1,0)])          # E1 80 80 -> U+1040
        self.assertEqual(TG.replay('W16',[2]),[(0,0),(0,0)])                          # odd byte buffered
        self.assertEqual(TG.replay('W16',[0,1,0,2]),[(0,0),(0,0),(0,0),(0,0),(1,0)])  # surrogate pair joined

    def test_reread_preserves_state(self):
        t=TG.Target('U4');t.act(2);r=[t.read() for _ in range(5)];self.assertEqual(t.steps,1);self.assertEqual(set(r),{(0,0)})

    def test_truth_vs_live(self):
        for name in TR.TARGETS:
            w=TR.world(name);self.assertEqual(w.n,TR.N_TRUE[name])
            for L in range(5):
                for acts in itertools.product(range(3),repeat=L):
                    self.assertEqual([list(x) for x in TG.replay(name,list(acts))],truth_readings(w,acts))

    def test_reach_and_labels(self):
        w=TR.world('U3');self.assertEqual(reach(w,0),list(range(6)));self.assertEqual(reach(w,1),[1,2,3,4,5])
        self.assertEqual(truth_label('ID',(w.transitions,w.emissions),0,w,0),'ID')
        bad=[list(r) for r in w.transitions];bad[4][1]=2
        self.assertEqual(truth_label('ID',(bad,w.emissions),0,w,0),'WRONG')
        self.assertEqual(truth_label('K_spent',None,None,w,0),'AMB')

    def test_adapter_ast(self):self.assertEqual(adapter_ast_ok(),[])


if __name__=='__main__':unittest.main()
