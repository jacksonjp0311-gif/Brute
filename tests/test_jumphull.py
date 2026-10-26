"""brute/jumphull.py: JumpRegionK, Y1k subset of Y1kJ, J8 rule and hull_record, and agreement with the second
implementation (experiments/v080_reference.hull_unions) on short 2x2 trajectories (seen development worlds)."""
import random,unittest
from brute.region import RegionK
from brute.jumphull import JumpRegionK,JumpSyncLearner
from brute.syncevent import SyncEventLearner
from bgr90.symbolic import mask_for_observation
import experiments.v080_reference as R
from experiments.v90_independent_reference import ref_initial,ref_observe
from experiments.v030_independent_reference import compatible_codes


def _walk(seed,T):
    """A random <=3-state 2x2 Moore machine, observed with each bit masked at rate 0.35."""
    rng=random.Random(seed);n=3;d=[[rng.randrange(n) for _ in (0,1)] for _ in range(n)];e=[rng.randrange(4) for _ in range(n)]
    def ob(q):return tuple(None if rng.random()<0.35 else (e[q]>>j)&1 for j in (0,1))
    q=0;obs=[ob(q)];acts=[]
    for _ in range(T):a=rng.randrange(2);q=d[q][a];acts.append(a);obs.append(ob(q))
    return obs,acts


def _learner(cls,**kw):
    return cls(4,5,160000,160000,0.08,0.05,8,1.645215321642,None,policy='LU-R',**kw)


class JumpHull(unittest.TestCase):
    def test_t0_identical_to_regionk(self):
        for m in range(1,16):
            a=RegionK(4,2,4,[m],[],None);b=JumpRegionK(4,2,4,[m],[],None)
            self.assertEqual(a.base_clauses,b.base_clauses)
            for x in (0,1):self.assertEqual(a.y1k(x,m),b.y1k(x,m))
            a.close();b.close()

    def test_y1k_subset_of_hull(self):
        done=0
        for seed in range(12):
            obs,acts=_walk(seed,6);masks=[mask_for_observation(o) for o in obs]
            a=RegionK(4,2,4,masks,acts,None)
            if a.feasible is not True:a.close();continue
            b=JumpRegionK(4,2,4,masks,acts,None);self.assertIs(b.feasible,True)
            for x in (0,1):
                y,u=a.y1k(x,masks[-1]);h,v=b.y1k(x,masks[-1]);self.assertEqual(u+v,0)
                self.assertTrue(set(y)<=set(h),(seed,x,y,h));done+=set(y)<set(h)
            a.close();b.close()
        self.assertGreater(done,0)

    def test_hull_matches_reference(self):
        done=0
        for seed in range(8):
            obs,acts=_walk(100+seed,5);masks=[mask_for_observation(o) for o in obs]
            r=ref_initial(obs[0]);prev=None;ok=True
            for a,o in zip(acts,obs[1:]):
                prev=r;r,st=ref_observe(r,a,o,4,160000)
                if st!='supported':ok=False;break
            if not ok:continue
            H=R.hull_unions(prev,r,len(acts),compatible_codes(obs[-1]),4)
            b=JumpRegionK(4,2,4,masks,acts,None)
            for x in (0,1):self.assertEqual(set(b.y1k(x,masks[-1])[0]),set(H[x]),(seed,x))
            b.close();done+=1
        self.assertGreaterEqual(done,6)

    def test_j8_rule(self):
        with self.assertRaises(ValueError):_learner(JumpSyncLearner,rule='CTR')
        obs,acts=_walk(7,10);J=_learner(JumpSyncLearner);S=_learner(SyncEventLearner,rule='RO')
        J.initialize(obs[0]);S.initialize(obs[0])
        for a,o in zip(acts,obs[1:]):
            for b in (0,1):
                fj=J.predict(b);fs=S.predict(b)
                if fj.certificate is not None:
                    self.assertEqual(fj.certificate,fs.certificate);self.assertTrue(fj.cert_rule.endswith('+hull'))
                if fs.certificate is not None and fj.certificate is None and fj.cert_rule is not None:
                    self.assertEqual(fj.cert_rule,'hull-downgraded')
            rec,u=J.hull_record()
            if J.support.status=='supported':self.assertEqual(set(rec),{'0','1'})
            else:self.assertEqual((rec,u),(None,0))
            J.observe(a,o);S.observe(a,o)
        self.assertIn('hull_downgrades',J.diagnostics());self.assertGreater(J.hull_queries,0);J.close();S.close()


if __name__=='__main__':unittest.main()
