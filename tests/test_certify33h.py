"""brute.certify/33h tests (new file): the same words, labels and models as certify/32h on real-decoder truth worlds (bitset preprocessing changes nothing but memory and time)."""
import unittest
from brute.api import certify32h as H32,certify33h as H33
from brute.api.certify20b import reading_of
from brute.api.certify32r import equivalent
from experiments import truth_072 as TR


def drive(cls,w,N,seed):
    s=0;words=[]
    c=cls(reading_of(w.emissions[0],2),3,N,read_bits=2,seed=seed,K=40000,conflict_cap=50000,budget_conflicts=50000000)
    try:
        while (p:=c.propose()) is not None:
            words.append(list(p))
            for a in p:s=w.transitions[s][a];c.observe(a,reading_of(w.emissions[s],2))
        r=c.result()
    finally:c.close()
    return words,r,s,c


class T(unittest.TestCase):
    def test_same_as_32h(self):
        for name,seed in (('SJ',3),('KR',4),('B5',5)):
            w=TR.world(name);N=TR.N_TRUE[name]+1
            a=drive(H32.Certifier32H,w,N,seed);b=drive(H33.Certifier33H,w,N,seed)
            self.assertEqual(a[0],b[0],name)
            for k in ('label','stop','n_min','s1','model','rounds'):self.assertEqual(a[1][k],b[1][k],(name,k))
            self.assertEqual(a[3].repins,b[3].repins)

    def test_certifies_and_interface(self):
        w=TR.world('KR');words,r,s,c=drive(H33.Certifier33H,w,5,7)
        self.assertIn(r['label'],('ID','IDF'));self.assertEqual(r['api'],'brute.certify/33h');self.assertFalse(r['soundness']['resets'])
        M=H32._norm(r['model']);self.assertTrue(equivalent(M[0],M[1],w.transitions,w.emissions,r['s1'],s)[0])

    def test_bad_args(self):
        with self.assertRaises(ValueError):H33.Certifier33H((0,0),3,7,read_bits=2,batch_steps=0)


if __name__=='__main__':unittest.main()
