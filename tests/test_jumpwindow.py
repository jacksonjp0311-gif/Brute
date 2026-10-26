"""brute/jumpwindow.py: JumpWindowRegionK equals RegionK when J(T) is empty, contains it otherwise, matches the second
implementation (experiments/v090_reference.window_hull) on short 2x2 trajectories (seen development worlds), and
the J9 rule / hull_record contract."""
import random,unittest
from brute.region import RegionK
from brute.jumpwindow import JumpWindowRegionK,WindowSyncLearner,window_positions
from brute.align import AlignedSyncLearner
from bgr90.symbolic import mask_for_observation
import experiments.v090_reference as R
from experiments.v90_independent_reference import ref_initial,ref_observe


def _walk(seed,T,jump_at=None):
    """A random <=3-state 2x2 Moore machine, each bit masked at rate 0.35; optional teleport before step jump_at."""
    rng=random.Random(seed);n=3;d=[[rng.randrange(n) for _ in (0,1)] for _ in range(n)];e=[rng.randrange(4) for _ in range(n)]
    def ob(q):return tuple(None if rng.random()<0.35 else (e[q]>>j)&1 for j in (0,1))
    q=0;obs=[ob(q)];acts=[]
    for t in range(1,T+1):
        a=rng.randrange(2);q=d[q][a]
        if t==jump_at:q=rng.randrange(n)
        acts.append(a);obs.append(ob(q))
    return obs,acts


def _learner(cls,**kw):
    return cls(4,5,160000,160000,0.08,0.05,8,1.645215321642,None,policy='LU-R',rule='CTR',**kw)   # LU-C comes from the AlignedSyncLearner override


class JumpWindow(unittest.TestCase):
    def test_positions(self):
        self.assertEqual(window_positions(1,4),[]);self.assertEqual(window_positions(9,4),[6,7,8])
        self.assertEqual(window_positions(9,4),R.window_positions(9,4))

    def test_no_window_identical_to_regionk(self):
        for m in range(1,16):
            for acts in ([],[0],[1]):
                masks=[m]*(len(acts)+1);a=RegionK(4,2,4,masks,acts,None);b=JumpWindowRegionK(4,2,4,masks,acts,None)
                self.assertEqual(a.base_clauses,b.base_clauses);self.assertEqual(a.base_vars,b.base_vars)
                for x in (0,1):self.assertEqual(a.y1k(x,m),b.y1k(x,m))
                a.close();b.close()

    def test_y1k_subset_of_window(self):
        done=0
        for seed in range(12):
            obs,acts=_walk(seed,7);masks=[mask_for_observation(o) for o in obs]
            a=RegionK(4,2,4,masks,acts,None)
            if a.feasible is not True:a.close();continue
            b=JumpWindowRegionK(4,2,4,masks,acts,None);self.assertIs(b.feasible,True)
            for x in (0,1):
                y,u=a.y1k(x,masks[-1]);h,v=b.y1k(x,masks[-1]);self.assertEqual(u+v,0)
                self.assertTrue(set(y)<=set(h),(seed,x,y,h));done+=set(y)<set(h)
            a.close();b.close()
        self.assertGreater(done,0)

    def test_window_matches_reference(self):
        done=0
        for seed in range(16):
            obs,acts=_walk(200+seed,6,jump_at=(4 if seed%2 else None));masks=[mask_for_observation(o) for o in obs]
            r=ref_initial(obs[0]);hist=[r];ok=True
            for a,o in zip(acts,obs[1:]):
                r,st=ref_observe(r,a,o,4,160000)
                if st!='supported':ok=False;break
                hist.append(r)
            if not ok:continue
            H,okr=R.window_hull(hist,obs,acts,len(acts),4,160000,4);self.assertTrue(okr)
            b=JumpWindowRegionK(4,2,4,masks,acts,None)
            for x in (0,1):self.assertEqual(set(b.y1k(x,masks[-1])[0]),set(H[x]),(seed,x))
            b.close();done+=1
        self.assertGreaterEqual(done,8)

    def test_j9_rule(self):
        for seed in (7,11):
            obs,acts=_walk(seed,12,jump_at=6);J=_learner(WindowSyncLearner);S=_learner(AlignedSyncLearner)
            J.initialize(obs[0]);S.initialize(obs[0])
            for a,o in zip(acts,obs[1:]):
                for b in (0,1):
                    fj=J.predict(b);fs=S.predict(b)
                    if fj.certificate is not None:
                        self.assertEqual(fj.certificate,fs.certificate);self.assertTrue(fj.cert_rule.endswith('+whull'))
                    if fs.certificate is None:self.assertIsNone(fj.certificate)
                rec,u=J.hull_record()
                if J.support.status=='supported':self.assertEqual(set(rec),{'0','1'})
                else:self.assertEqual((rec,u),(None,0))
                J.observe(a,o);S.observe(a,o)
            d=J.diagnostics();self.assertEqual(d['window_K'],4);self.assertIn('hull_downgrades',d)
            self.assertGreater(J.hull_queries,0);J.close();S.close()


if __name__=='__main__':unittest.main()
