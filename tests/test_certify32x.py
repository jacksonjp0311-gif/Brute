"""brute.certify/32x tests (new file): hybrid certificate of a given hypothesis state on a reset-free trace of a hand truth."""
import random,unittest
from brute.api import certify32x as X
from brute.api.certify32r import equivalent
from experiments import truth_069 as TR


def drive(name,hyp_T,hyp_E,N,steps=300,seed=3,K=40000):
    """Random warm-up trace on the truth, then 32x on hypothesis (state 0 at position 0)."""
    w=TR.world(name);rng=random.Random(seed);s=0
    c=X.Certifier32X(w.emissions[0],3,N,K=K)
    try:
        for _ in range(steps):
            a=rng.randrange(3);s=w.transitions[s][a];c.observe(a,w.emissions[s])
        c.set_hypothesis(hyp_T,list(hyp_E),origin=0)
        while (p:=c.propose()) is not None:
            for a in p:s=w.transitions[s][a];c.observe(a,w.emissions[s])
        return c.result(),w,s
    finally:c.close()


class T(unittest.TestCase):
    def test_idf_on_true_hypothesis(self):
        w=TR.world('U3');r,w,s=drive('U3',w.transitions,w.emissions,7)
        self.assertEqual(r['label'],'IDF');self.assertEqual(r['api'],X.API);self.assertIs(r['assumes_resync'],False)
        self.assertTrue(equivalent(r['hyp_T'],r['hyp_E'],w.transitions,w.emissions,r['q_star'],s)[0])

    def test_wrong_hypothesis_is_never_idf_true(self):
        w=TR.world('U3');bad=[list(x) for x in w.transitions];bad[0][0]=(bad[0][0]+1)%6
        r,w,s=drive('U3',bad,w.emissions,7)
        if r['label']=='IDF':self.assertTrue(equivalent(r['hyp_T'],r['hyp_E'],w.transitions,w.emissions,r['q_star'],s)[0])
        else:self.assertIn(r['label'],('HYP_REJECTED','K_spent','IDU','WINDOW_CAP'))

    def test_too_small_bound_does_not_certify_wrongly(self):
        w=TR.world('U3');r,w,s=drive('U3',w.transitions,w.emissions,5)
        self.assertIn(r['label'],('IDF','HYP_REJECTED','K_spent','IDU','WINDOW_CAP','HYP_INCONSISTENT'))

    def test_host_agnostic(self):
        import ast
        from pathlib import Path
        t=ast.parse((Path(X.__file__)).read_text());mods=set()
        for n in ast.walk(t):
            if isinstance(n,ast.ImportFrom):mods.add((n.module or '').split('.')[0])
            elif isinstance(n,ast.Import):mods|={a.name.split('.')[0] for a in n.names}
        self.assertEqual(mods,{'__future__','brute'})

    def test_sep(self):
        T1=[[1,0],[1,0]];E1=[0,1]
        self.assertEqual(X._sep(T1,E1,0,T1,E1,1),[])
        self.assertIsNone(X._sep(T1,E1,0,T1,E1,0))


if __name__=='__main__':unittest.main()
