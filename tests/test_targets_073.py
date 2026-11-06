"""Study 073 target and truth tests (new file): the adapter, the oracle truth against the hand-written truths, jobs and N."""
import unittest
from experiments import targets_073 as TG
from experiments import targets_070 as T70
from experiments import truth_072 as TR73
from experiments import truth_069 as H69
from experiments import truth_073 as TR
from experiments import brute_study_073 as BS
from scripts.make_truth_073 import oracle
from scripts.make_gates_070 import adapter_ast_ok
from brute.api.certify32r import equivalent


class T(unittest.TestCase):
    def test_adapter_has_no_reset(self):
        t=TG.Target('SJ');self.assertFalse(hasattr(t,'reset'));d=t.dec;t.act(1);t.act(2);self.assertIs(t.dec,d);self.assertEqual(t.decoder_objects,1)
        self.assertEqual(adapter_ast_ok(TG.__file__),[])

    def test_oracle_reproduces_hand_truths(self):
        for n,(c,bs) in T70.TARGETS.items():
            o=oracle(c,bs);w=H69.world(n)
            self.assertEqual(o['n'],w.n,n);self.assertTrue(equivalent(o['transitions'],o['emissions'],w.transitions,w.emissions,0,0)[0],n)

    def test_truth_matches_live_decoder(self):
        import random
        for name in TG.TARGETS:
            w=TR.world(name);t=TG.Target(name);s=0;rng=random.Random(5);self.assertEqual(2*t.read()[0]+t.read()[1],w.emissions[0])
            for _ in range(300):
                a=rng.randrange(3);r=t.act(a);s=w.transitions[s][a];self.assertEqual(2*r[0]+r[1],w.emissions[s],name)

    def test_truth_extends_072(self):
        for t,n in TR73.N_TRUE.items():self.assertEqual(TR.N_TRUE[t],n,t)

    def test_sizes_and_jobs(self):
        self.assertEqual(TR.N_TRUE,{'SJ':3,'KR':4,'B5':5,'U32':7,'U8S':9,'U16B':9,'EJ4':11,'HK':5,'HZ':10,'JO':4})
        self.assertEqual(BS.NS['plus1'],{t:TR.N_TRUE[t]+1 for t in TR.TARGETS});self.assertEqual(BS.NS['plus3'],{t:TR.N_TRUE[t]+3 for t in TR.TARGETS})
        j=BS.jobs_for('main');self.assertEqual(len(j),50);self.assertEqual(len(set(j)),50);self.assertEqual(BS.jobs_for('smoke')[0][2],'C1')
        self.assertEqual((BS.WORKERS,BS.JOB_KILL_S,BS.MAIN_CAP_S,BS.RLIMIT_AS),(3,420.0,3300.0,int(2.0*(1<<30))))


if __name__=='__main__':unittest.main()
