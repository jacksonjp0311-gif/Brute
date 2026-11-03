"""brute.certify/32h tests (new file): homing sequences, characterizing sets, reset-free certification of a hand truth, interface."""
import itertools,unittest
from brute.api import certify32h as H
from brute.api.certify20b import reading_of
from brute.api.certify32r import equivalent
from experiments import truth_069 as TR


def homes(T,E,h):
    """Exact homing check: any two states with equal readings along h end in one state."""
    seen={}
    for q in range(len(T)):
        x=q;out=[E[x]]
        for a in h:x=T[x][a];out.append(E[x])
        if seen.setdefault(tuple(out),x)!=x:return False
    return True


class T(unittest.TestCase):
    def test_homing_sequences(self):
        for name in TR.TARGETS:
            w=TR.world(name);h=H.homing_sequence(w.transitions,w.emissions)
            self.assertIsNotNone(h);self.assertTrue(homes(w.transitions,w.emissions,h))
            for L in range(len(h)):
                for g in itertools.product(range(3),repeat=L):self.assertFalse(homes(w.transitions,w.emissions,list(g)),(name,g))

    def test_char_set(self):
        w=TR.world('U4');C=H.char_set(w.transitions,w.emissions);self.assertEqual(C[0],())
        for p in range(len(w.transitions)):
            for q in range(p+1,len(w.transitions)):
                def run(s,e):
                    for a in e:s=w.transitions[s][a]
                    return w.emissions[s]
                self.assertTrue(any(run(p,e)!=run(q,e) for e in C))

    def test_reset_free_certifies_u3(self):
        w=TR.world('U3');s=0
        c=H.Certifier32H(reading_of(w.emissions[0],2),3,7,read_bits=2,seed=5,K=40000,conflict_cap=50000,budget_conflicts=50000000)
        try:
            while (p:=c.propose()) is not None:
                for a in p:s=w.transitions[s][a];c.observe(a,reading_of(w.emissions[s],2))
            r=c.result()
        finally:c.close()
        self.assertIn(r['label'],('ID','IDF'));self.assertEqual(r['api'],H.API);self.assertFalse(r['soundness']['resets'])
        M=H._norm(r['model']);self.assertTrue(equivalent(M[0],M[1],w.transitions,w.emissions,r['s1'],s)[0])
        self.assertTrue(c.batches and all(0<b['steps']<H.BATCH_STEPS+60 for b in c.batches))

    def test_bad_args(self):
        with self.assertRaises(ValueError):H.Certifier32H((0,0),3,7,read_bits=2,batch_steps=0)
        with self.assertRaises(ValueError):H.Certifier32H((0,0),3,7,read_bits=2,seed=True)


if __name__=='__main__':unittest.main()
