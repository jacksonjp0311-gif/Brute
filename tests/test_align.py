"""brute/align.py: LU-C labels, calm logic, equality with LU-R when not calm, and >= LU-R when calm (2x2), plus
agreement with experiments/v080_reference.score_c on short trajectories."""
import random,unittest
from brute.align import AlignedSyncLearner
from brute.syncevent import SyncEventLearner
import experiments.v080_reference as R
from experiments.v90_independent_reference import ref_initial,ref_observe


def _walk(seed,T):
    """A random <=3-state 2x2 Moore machine, observed with each bit masked at rate 0.35."""
    rng=random.Random(seed);n=3;d=[[rng.randrange(n) for _ in (0,1)] for _ in range(n)];e=[rng.randrange(4) for _ in range(n)]
    def ob(q):return tuple(None if rng.random()<0.35 else (e[q]>>j)&1 for j in (0,1))
    q=0;obs=[ob(q)];acts=[]
    for _ in range(T):a=rng.randrange(2);q=d[q][a];acts.append(a);obs.append(ob(q))
    return obs,acts


def _learner(cls,**kw):
    return cls(4,5,160000,160000,0.08,0.05,8,1.645215321642,None,policy='LU-R',rule='CTR',**kw)


class Align(unittest.TestCase):
    def test_labels(self):
        L=_learner(AlignedSyncLearner);L.initialize((0,1))
        self.assertEqual(L.experiment(0)['policy'],'LU-C');self.assertEqual(L.diagnostics()['lookahead'],'LU-C')
        self.assertEqual(L.policy,'LU-R');L.close()
        with self.assertRaises(ValueError):AlignedSyncLearner(4,5,160000,160000,0.08,0.05,8,1.645215321642,None,policy='LU-R',rule='RO')

    def test_scores_vs_lur_and_reference(self):
        checked=0
        for seed in range(4):
            obs,acts=_walk(300+seed,10);A=_learner(AlignedSyncLearner);S=_learner(SyncEventLearner)
            A.initialize(obs[0]);S.initialize(obs[0]);r4=ref_initial(obs[0]);r5=ref_initial(obs[0]);s4=s5='supported'
            for i,(a,o) in enumerate(zip(acts,obs[1:])):
                ea=A.experiment(0);es=S.experiment(0);calm=A._calm_next()
                self.assertEqual(calm,R.calm_after(A.drift_events,i,8,8))
                if not calm:self.assertEqual(ea['scores'],es['scores'])
                else:self.assertTrue(all(x>=y for x,y in zip(ea['scores'],es['scores'])))
                if A.alarm_step is None and s4=='supported' and s5=='supported':
                    ref=[R.score_c(r4,s4,r5,s5,False,b,4,5,160000,160000,calm) for b in (0,1)]
                    self.assertEqual(ea['scores'],ref,(seed,i));checked+=1
                A.observe(a,o);S.observe(a,o)
                if s4=='supported':r4,s4=ref_observe(r4,a,o,4,160000)
                if s5=='supported':r5,s5=ref_observe(r5,a,o,5,160000)
            A.close();S.close()
        self.assertGreater(checked,10)


if __name__=='__main__':unittest.main()
