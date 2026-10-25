"""GR1 sanity (v0.4.0): the geometric replay agrees on unmodified sealed traces and counts injected errors.

A replay that cannot detect a planted error proves nothing; each mutation below must be counted (full count, no
first-stop). Uses sealed study-005 traces (read-only).
"""
import copy,unittest
from experiments.exactness_006 import _cases,replay,ROOT


def _mutate(r):r['support']=list(r['support'])[1:]   # drop one member of the possible set


class ExactnessMutation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cs=_cases(ROOT/'results/study-005/RESULTS.json')
        cls.cases=[c for c in cs if c['family'] in ('cycle3','switch3','drift4')][:4]

    def test_clean_zero(self):
        for i,c in enumerate(self.cases):
            for arm in ('A3','P3'):
                n,bad,_,_=replay('005',i,c,arm);self.assertGreater(n,0);self.assertEqual(bad,[],(i,arm,bad[:2]))

    def test_each_mutation_counted(self):
        planted=caught=0
        for i,c in enumerate(self.cases):
            for arm in ('A3','P3'):
                recs=c['arms'][arm]['trace']
                for j in (3,len(recs)//2):
                    if j>=len(recs) or not recs[j].get('support'):continue
                    m=copy.deepcopy(c);_mutate(m['arms'][arm]['trace'][j]);planted+=1
                    _,bad,_,_=replay('005',i,m,arm);caught+=len(bad)==1
        self.assertGreaterEqual(planted,8);self.assertEqual(caught,planted)

    def test_k_mutations_k_counts(self):
        c=copy.deepcopy(self.cases[0]);recs=c['arms']['P3']['trace']
        idx=[j for j,r in enumerate(recs) if r.get('support')][:5]
        for j in idx:_mutate(recs[j])
        _,bad,_,_=replay('005',0,c,'P3');self.assertEqual(len(bad),len(idx))


if __name__=='__main__':unittest.main()
