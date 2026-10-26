"""v0100_reference self-checks (seen/smoke data only)."""
import copy,unittest
from experiments import v0100_reference as R


class T(unittest.TestCase):
    def test_itertools_equals_dfs_n3(self):
        for f in ('cycle3','switch3','unaliased2'):
            codes,acts=R.ref_source_obs(5190021,f);cls=R._classes(codes)
            for n in (2,3):self.assertEqual(R._enum_small(codes,acts,n,cls),R._dfs4(codes,acts,cls,n=n))

    def test_library_minimal(self):
        exp={'cycle3':3,'switch3':3,'unaliased2':2,'ood4':4}
        for f,n in exp.items():
            L=R.ref_library(f,5190022);self.assertEqual((L['status'],L['min_n']),('ok',n))
            H,st=R.ref_hypotheses(L);self.assertEqual(st,'ok');self.assertGreater(len(H),0)

    def test_true_target_in_hypotheses(self):
        from bgr89.worlds import world
        for f in ('cycle3','switch3','unaliased2','ood4'):
            H,_=R.ref_hypotheses(R.ref_library(f,5190023));w=world(5190001,f)
            n={'cycle3':3,'switch3':3,'unaliased2':2,'ood4':4}[f]
            T=[[w.next(s,a) for a in (0,1)] for s in range(n)];E=[w.emission(s) for s in range(n)]
            self.assertIn(R._canon(T,E,w.start),set(H))

    def test_canon_relabel_invariant(self):
        T=[[1,0],[2,1],[0,2]];E=[1,1,3]
        p=[2,0,1];T2=[None]*3;E2=[None]*3
        for s in range(3):T2[p[s]]=[p[T[s][0]],p[T[s][1]]];E2[p[s]]=E[s]
        self.assertEqual(R._canon(T,E,0),R._canon(T2,E2,p[0]))


if __name__=='__main__':unittest.main()
