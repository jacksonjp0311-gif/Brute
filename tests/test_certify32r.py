"""brute.certify/32r tests (new file): learns small Moore machines with resets, labels, noise settling, interface errors."""
import random,unittest
from brute.api import certify32r as C
from experiments import truth_069 as TR
from experiments import worlds_065 as W65


def drive(T,E,N,noise=None,seed=1,cap=400000,eps_bar=None,delta=None):
    c=C.Certifier32R(len(T[0]),N,2,eps_bar,delta,seed=seed,query_cap=cap)
    while (w:=c.propose()) is not None:
        q=0
        for i in range(len(w)+1):
            if i>0:q=T[q][w[i-1]]
            if c.wants(w[:i]):
                cl=(E[q]>>1&1,E[q]&1)
                if noise is None:rs=[cl]
                else:
                    rs=[noise.read(cl)]
                    while c.more(rs):rs.append(noise.read(cl))
                c.take(w[:i],rs)
    return c


class T(unittest.TestCase):
    def test_learns_truths(self):
        for name in TR.TARGETS:
            w=TR.world(name);N=16 if name=='EJ' else 12;c=drive(w.transitions,w.emissions,N);r=c.result()
            self.assertEqual(r['label'],'ID');self.assertEqual(r['n'],TR.N_TRUE[name])
            self.assertTrue(C.equivalent(r['transitions'],r['emissions'],w.transitions,w.emissions)[0])
            self.assertEqual((r['transitions'],r['emissions']),tuple(C.canonical(w.transitions,w.emissions)))

    def test_random_machines(self):
        rng=random.Random(5)
        for _ in range(30):
            n=rng.randrange(1,7);T=[[rng.randrange(n) for _ in range(2)] for _ in range(n)];E=[rng.randrange(4) for _ in range(n)]
            r=drive(T,E,8,seed=rng.randrange(99)).result();self.assertEqual(r['label'],'ID')
            self.assertTrue(C.equivalent(r['transitions'],r['emissions'],T,E)[0])

    def test_exceeds_n(self):
        w=TR.world('W16');self.assertEqual(drive(w.transitions,w.emissions,6).result()['label'],'EXCEEDS_N')

    def test_guarantee_is_conditional_on_N(self):
        # under-declared N (13-state EJ, N 8): 32r may return ID with a WRONG 8-state hypothesis. The ID guarantee holds only if the
        # target really has <= N states; this documents that limit.
        w=TR.world('EJ');r=drive(w.transitions,w.emissions,8).result();self.assertEqual(r['label'],'ID')
        self.assertFalse(C.equivalent(r['transitions'],r['emissions'],w.transitions,w.emissions)[0])

    def test_qcap(self):
        w=TR.world('U3');self.assertEqual(drive(w.transitions,w.emissions,12,cap=50).result()['label'],'QCAP')

    def test_noisy_equals_clean(self):
        w=TR.world('GB');a=drive(w.transitions,w.emissions,12,seed=3).record()
        b=drive(w.transitions,w.emissions,12,noise=W65.Noise(4,0.2),seed=3,eps_bar=0.25,delta=0.01).record()
        for k in ('label','n','transitions','emissions','tree','E','S','queries'):self.assertEqual(a[k],b[k])
        self.assertGreater(b['reads_total'],a['reads_total'])

    def test_determinism(self):
        w=TR.world('U4');self.assertEqual(drive(w.transitions,w.emissions,12,seed=9).record(),drive(w.transitions,w.emissions,12,seed=9).record())

    def test_errors(self):
        with self.assertRaises(ValueError):C.Certifier32R(3,0)
        with self.assertRaises(ValueError):C.Certifier32R(3,12,2,0.3,None)
        with self.assertRaises(ValueError):C.Certifier32R(3,12,2,0.6,0.1)
        c=C.Certifier32R(3,12);w=c.propose();self.assertEqual(w,())
        with self.assertRaises(ValueError):c.take((1,),[(0,0)])
        with self.assertRaises(ValueError):c.result()
        with self.assertRaises(ValueError):c.propose()
        c.take((),[(0,0)])
        with self.assertRaises(ValueError):c.take((),[(0,0)])

    def test_equivalent_witness(self):
        ok,wd=C.equivalent([[0]],[0],[[1],[1]],[0,2]);self.assertFalse(ok);self.assertEqual(wd,[0])

    def test_soundness_flags(self):
        s=C.soundness();self.assertFalse(s['sat']);self.assertTrue(s['resets']);self.assertEqual(C.API,'brute.certify/32r')


if __name__=='__main__':unittest.main()
