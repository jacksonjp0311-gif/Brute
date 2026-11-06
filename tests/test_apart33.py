"""Study 073 tests (new file): brute.apart33 returns exactly what the old set/matrix functions return (random traces and real machine traces)."""
import random,unittest
from brute.scalesearch15 import apart_matrix,greedy_clique,_ap
from brute.api.certify20p import max_clique0
from brute.apart33 import apart_bitsets,greedy_clique33,max_clique33,apart_pairs33
from experiments import truth_072 as TR


def check_trace(tc,masks,acts,caps=(200000,40)):
    A=apart_matrix(masks,acts);adj=apart_bitsets(masks,acts);T1=len(acts)+1
    for t in range(T1):
        tc.assertFalse((adj[t]>>t)&1)
        for u in range(T1):
            if t!=u:tc.assertEqual(bool(_ap(A,t,u)),bool((adj[t]>>u)&1),(t,u))
    g=greedy_clique(A);tc.assertEqual(g,greedy_clique33(adj))
    for cap in caps:tc.assertEqual(max_clique0(A,g,cap),max_clique33(adj,g,cap))
    tc.assertEqual({(t,u) for t in range(T1) for u in range(t+1,T1) if A[t][u] and masks[t]&masks[u]},apart_pairs33(adj,masks))


class T(unittest.TestCase):
    def test_random_traces(self):
        rng=random.Random(11)
        for _ in range(120):
            T=rng.randint(1,50);k=rng.choice([2,3]);masks=[rng.choice([1,2,4,8,3,12,15,5]) for _ in range(T+1)];acts=[rng.randrange(k) for _ in range(T)]
            check_trace(self,masks,acts)

    def test_real_machine_traces(self):
        rng=random.Random(3)
        for name in ('SJ','KR','B5','HK','U16B'):
            w=TR.world(name);s=0;masks=[1<<w.emissions[0]];acts=[]
            for _ in range(160):
                a=rng.randrange(3);s=w.transitions[s][a];acts.append(a);masks.append(1<<w.emissions[s])
            check_trace(self,masks,acts)

    def test_edge_traces(self):
        check_trace(self,[1],[]);check_trace(self,[1,1],[0]);check_trace(self,[1,2],[0])


if __name__=='__main__':unittest.main()
