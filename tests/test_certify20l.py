"""Tests for brute/api/certify20l.py (certify/20l, no-reset table learner with certify/16e's rival proof; BRUTE_PLAN_056). New file.
Worlds: an old development seed (10050003, control_cycle3), outside every study-056 range, plus small random machines built
here from a fixed local PRNG (seeds 0..), never a study seed. Brute force: every machine with at most 3 states over 2 actions and 4 codes."""
import ast,itertools,random,unittest
from pathlib import Path
from brute.api import certify20l as L
from brute.api import certify16e as E
from brute.scalesearch15 import apart_matrix
from tests.test_certify20t import world,loop
ROOT=Path(__file__).resolve().parents[1];CAP=50000;BUD=10**7


def reading(c):return ((c>>1)&1,c&1)


def rand_machine(seed,n,k=2,codes=2):
    r=random.Random(seed);return [[r.randrange(n) for _ in range(k)] for _ in range(n)],[r.randrange(codes) for _ in range(n)]


def walk(d,e,acts,s=0):
    out=[e[s]]
    for a in acts:s=d[s][a];out.append(e[s])
    return out,s


def all_consistent(acts,codes,nmax,k=2):
    """Every machine (d, e, start 0) with at most nmax states consistent with the trace (brute force)."""
    out=[]
    for n in range(1,nmax+1):
        for flat in itertools.product(range(n),repeat=n*k):
            d=[list(flat[i*k:(i+1)*k]) for i in range(n)]
            for e in itertools.product(range(4),repeat=n):
                if walk(d,list(e),acts)[0]==codes:out.append((d,list(e)))
    return out


def equiv(d1,e1,s1,d2,e2,s2):
    seen={(s1,s2)};st=[(s1,s2)]
    while st:
        p,q=st.pop()
        if e1[p]!=e2[q]:return False
        for a in range(len(d1[0])):
            x=(d1[p][a],d2[q][a])
            if x not in seen:seen.add(x);st.append(x)
    return True


def run_trace(acts,codes,N,k=2,K=0,**kw):
    c=L.Certifier20L(reading(codes[0]),k,N,K=K,conflict_cap=CAP,budget_conflicts=BUD,**kw)
    try:
        for a,o in zip(acts,codes[1:]):c.observe(a,reading(o))
        c.propose();return c.result(),c.record()
    finally:c.close()


def cases(n_cases=40):
    for sd in range(n_cases):
        r=random.Random(1000+sd);n=r.choice((2,3));d,e=rand_machine(sd,n);acts=[r.randrange(2) for _ in range(r.randrange(3,14))]
        yield sd,d,e,acts,walk(d,e,acts)[0]


class API(unittest.TestCase):
    def test_constants(self):
        self.assertEqual(L.API,'brute.certify/20l');self.assertTrue(issubclass(L.Certifier20L,E.Certifier16E))
        s=L.soundness();self.assertEqual(s['search'],'a20l');self.assertIn('no least-machine search',s['proof'])
        with self.assertRaises(ValueError):L.Certifier20L((0,0),2,3,'a16d',conflict_cap=1,budget_conflicts=1)

    def test_rows_pairwise_apart_and_lower_bound(self):
        # Exact: the basis rows are pairwise apart, so no consistent machine has fewer states (brute force at <= 3 states)
        for sd,d,e,acts,codes in cases():
            masks=[1<<c for c in codes];tab=L.table_of(masks,acts);B=tab['basis'];A=apart_matrix(masks,acts)
            for i in range(len(B)):
                for j in range(i+1,len(B)):
                    a,b=sorted((B[i],B[j]));self.assertTrue(A[a][b])
            ms=all_consistent(acts,codes,3)
            if ms:self.assertGreaterEqual(min(len(m[0]) for m in ms),len(B),sd)

    def test_labels_against_brute_force(self):
        # ID / IDF only when every consistent machine with <= N states agrees with the model (future; and start for ID)
        seen=set()
        for sd,d,e,acts,codes in cases():
            r,rec=run_trace(acts,codes,3);seen.add(r['label'])
            ms=all_consistent(acts,codes,3)
            if r['label'] in ('ID','IDF'):
                (d1,e1),s1=r['model'],r['s1']
                for d2,e2 in ms:
                    self.assertTrue(equiv(d1,e1,s1,d2,e2,walk(d2,e2,acts)[1]),sd)
                if r['label']=='ID':
                    for d2,e2 in ms:self.assertTrue(equiv(d1,e1,0,d2,e2,0),sd)
            if r['label']=='AMB':
                self.assertTrue(any(not equiv(*r['model'],r['s1'],d2,e2,walk(d2,e2,acts)[1]) for d2,e2 in ms) or len(rec['table']['basis'])>3,sd)
        self.assertTrue('AMB' in seen and seen&{'ID','IDF'},seen)

    def test_no_wrong_with_deliberately_wrong_hypothesis(self):
        # a wrong H (every cell a self-loop, emissions shifted) may cost budget but never yields a WRONG ID / IDF
        orig=L.hypothesis
        def bad(masks,acts,k,tab,L_=None,rounds=None):
            (dd,ee),miss,conf=orig(masks,acts,k,tab);n=len(dd);return ([[i]*k for i in range(n)],[(x+1)%4 for x in ee]),miss,conf
        L.hypothesis=bad
        try:
            for sd,d,e,acts,codes in cases(25):
                r,rec=run_trace(acts,codes,3)
                if r['label'] in ('ID','IDF'):
                    for d2,e2 in all_consistent(acts,codes,3):
                        self.assertTrue(equiv(*r['model'],r['s1'],d2,e2,walk(d2,e2,acts)[1]),sd)
                self.assertNotEqual(r['label'],'ID',sd)    # the shifted H is inconsistent from the start
        finally:L.hypothesis=orig

    def test_learner_loop_small_world_matches_certify16e(self):
        for N,n in ((3,None),(5,10)):
            a,ra=loop(L.Certifier20L,N=N,n=n);b,rb=loop(E.Certifier16E,N=N,n=n)
            self.assertEqual((a['label'],a['n_min']),(b['label'],b['n_min']),(N,n))
        a,ra=loop(L.Certifier20L);self.assertEqual((a['api'],a['label'],a['n_min']),('brute.certify/20l','ID',3))

    def test_counterexample_words_distinguish(self):
        a,rec=loop(L.Certifier20L,N=5,n=10)
        from brute.scalesearch8 import run_word
        n=0
        for r in rec['rounds']:
            if r.get('word'):
                n+=1;p1=run_word(*r['M1'],r['s1'],r['word']);p2=run_word(*r['M2'],r['s2'],r['word'])
                self.assertEqual(p1[:-1],p2[:-1]);self.assertNotEqual(p1[-1],p2[-1])
        self.assertGreater(n,0)

    def test_table_reproduces_from_trace(self):
        # GTABLE56 in miniature: every table-filling word is recomputed from the trace prefix alone
        a,rec=loop(L.Certifier20L,N=5,n=10);w,sw,acts,rd=world();m=rec['masks'];A=rec['acts'];basis=[0];k=w.k
        for x in rec['table']['log']:
            if x['kind'] in ('home','cell','route'):
                T=x['T'];tab=L.table_of(m[:T+1],A[:T],basis);basis=tab['basis'];H,miss,conf=L.hypothesis(m[:T+1],A[:T],k,tab)
                self.assertEqual(L.fill_word(m[:T+1],A[:T],k,tab,H,miss),(x['word'],x['kind']))
                self.assertEqual(A[T:T+len(x['word'])],x['word'])

    def test_deterministic_and_conflict_accounting(self):
        a,r1=loop(L.Certifier20L,N=5,n=10);b,r2=loop(L.Certifier20L,N=5,n=10)
        strip=lambda r:[{k:v for k,v in x.items() if 'wall' not in k} for x in r['rounds']]
        self.assertEqual(strip(r1),strip(r2));self.assertEqual(r1['table'],r2['table']);self.assertEqual(r1['acts'],r2['acts'])
        self.assertEqual(sum(sum(x) for rr in r1['rounds'] for x in rr['chunk_conflicts']),r1['conflicts_spent'])

    def test_rows_exceed_bound_stops_amb(self):
        acts=[0]*6;codes=[0,1,2,3,0,1,2];r,rec=run_trace(acts,codes,3)
        self.assertEqual((r['label'],r['stop']),('AMB','AMB'));self.assertEqual(rec['table']['log'][-1]['kind'],'rows_exceed_N')

    def test_core_has_no_io(self):
        t=ast.parse((ROOT/'brute/api/certify20l.py').read_text());names=set()
        for nd in ast.walk(t):
            if isinstance(nd,ast.Import):names|={a.name.split('.')[0] for a in nd.names}
            if isinstance(nd,ast.ImportFrom) and nd.module:names.add(nd.module.split('.')[0])
        self.assertFalse(names&{'os','subprocess','threading','socket','multiprocessing','shutil'})


if __name__=='__main__':unittest.main()
