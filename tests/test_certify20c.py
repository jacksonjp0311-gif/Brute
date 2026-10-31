"""Tests for brute/api/certify20c.py (certify/20c, cube-and-conquer on capped queries; BRUTE_PLAN_055). New file; built from
tests/test_certify20t.py (frozen). Worlds use an old development seed (10050003, control_cycle3), outside every study-055 range.
A tiny conflict cap (2) forces the cube split on small instances so the split itself is exercised."""
import ast,itertools,unittest
from pathlib import Path
from brute.api import certify20c as C
from brute.api import certify16e as E
from tests.test_certify20t import world,loop
ROOT=Path(__file__).resolve().parents[1]


def brute_colourings(d,n):
    """All colourings of d positions with x0 = 0 that first-visit symmetry allows (q >= 1 needs q - 1 earlier)."""
    out=[]
    for c in itertools.product(range(n),repeat=d):
        if c[0]!=0:continue
        if all(c[t]==0 or (c[t]-1) in c[:t] for t in range(d)):out.append(c)
    return out


def rec_of(N,n,cap=2):
    w,sw,acts,rd=world();c=C.Certifier20C(rd[0],w.k,N,K=0,conflict_cap=cap,budget_conflicts=10**7)
    for a,o in zip(acts[:n],rd[1:n+1]):c.observe(a,o)
    c.propose();return c.record()


class API(unittest.TestCase):
    def test_constants(self):
        self.assertEqual(C.API,'brute.certify/20c');self.assertEqual(C.CUBE_DEPTH,5);self.assertTrue(issubclass(C.Certifier20C,E.Certifier16E))
        self.assertIn('cube-and-conquer',C.soundness()['split'])

    def test_rgs_bell_numbers(self):
        self.assertEqual([len(C.rgs(d,20)) for d in range(1,6)],[1,2,5,15,52]);self.assertEqual(len(C.rgs(5,2)),16)

    def test_cube_partition_matches_brute_force(self):
        # Exact at small N: the cube list equals the set of first-visit colourings, in lexicographic order, without repeats
        for n in range(1,7):
            for d in range(1,6):
                R=C.rgs(d,n);self.assertEqual(R,sorted(set(R)));self.assertEqual(set(R),set(brute_colourings(d,n)),(n,d))

    def test_pruning_rule(self):
        pos,live,pruned=C.cube_plan(4,10,{(0,2),(1,3),(3,9)})
        self.assertEqual(pos,[0,1,2,3,4])
        for c in live:self.assertTrue(c[0]!=c[2] and c[1]!=c[3])
        for c,(t,u) in pruned:self.assertEqual(c[t],c[u])
        self.assertEqual(len(live)+len(pruned),len(C.rgs(5,4)))
        self.assertEqual(C.cube_plan(3,2,set())[0],[0,1,2])

    def test_verdict_equals_certify16e_under_forced_split(self):
        w,sw,acts,rd=world();used=0
        for N in (3,4,5,6):
            for n in range(2,len(acts)+1,7):
                a=C.certify20c(rd[0],acts[:n],rd[1:n+1],w.k,N,conflict_cap=2,budget_conflicts=10**7)
                b=E.certify16e(rd[0],acts[:n],rd[1:n+1],w.k,N,conflict_cap=50000,budget_conflicts=10**7)
                self.assertEqual((a['label'],a['n_min']),(b['label'],b['n_min']),(N,n))

    def test_split_exercised_sat_and_unsat(self):
        s=rec_of(6,20)['cube']['queries'];u=rec_of(6,50)['cube']['queries']
        self.assertTrue(s and s[0]['sat'] is not None);self.assertTrue(u and u[0]['sat'] is None and not u[0]['open'])
        self.assertEqual(len(u[0]['closed']),len(u[0]['cubes']))

    def test_conflict_accounting(self):
        for N,n in ((6,20),(6,50),(4,30)):
            r=rec_of(N,n);tot=sum(sum(x) for rr in r['rounds'] for x in rr['chunk_conflicts']);self.assertEqual(tot,r['conflicts_spent'])
            for q in r['cube']['queries']:
                pos,live,pruned=C.cube_plan(q['n'],q['T'],set());self.assertEqual(len(q['cubes'])+len(q['pruned']),len(live))

    def test_loop_ID_at_true_size(self):
        r,rec=loop(C.Certifier20C);self.assertEqual((r['api'],r['label'],r['n_min']),('brute.certify/20c','ID',3))

    def test_core_has_no_io(self):
        t=ast.parse((ROOT/'brute/api/certify20c.py').read_text());names=set()
        for nd in ast.walk(t):
            if isinstance(nd,ast.Import):names|={a.name.split('.')[0] for a in nd.names}
            if isinstance(nd,ast.ImportFrom) and nd.module:names.add(nd.module.split('.')[0])
        self.assertFalse(names&{'os','subprocess','threading','socket','multiprocessing','shutil'})


if __name__=='__main__':unittest.main()
