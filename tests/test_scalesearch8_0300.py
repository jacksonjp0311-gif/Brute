"""v0.30.0: A8 active experiments (brute.scalesearch8). distinguishing_word is the shortest separating word (brute-force
check over all short words) and None exactly when no word separates; identify8 equals the frozen 031 probe identify6 on
n_min, uniqueness and second_found, also when started from an earlier prefix's n_min; the per-query cap gives UNKNOWN;
active8 executes only sound words (M1 and M2 agree before the last action and differ after it), keeps the hidden machine
consistent, never exceeds K, and reaches the world only through observe; host-agnostic source. New file."""
import itertools,random,unittest,pathlib
from time import perf_counter
from brute import scalesearch8 as S8
from brute.scalesearch6 import identify6
from brute.scalesearch import simulate
from tests.test_scalesearch_0230 import trace


def rand_machine(rng,n,k,m=4):return [[rng.randrange(n) for _ in range(k)] for _ in range(n)],[rng.randrange(m) for _ in range(n)]


def sep(d1,e1,s1,d2,e2,s2,w):
    p1=S8.run_word(d1,e1,s1,w);p2=S8.run_word(d2,e2,s2,w);return p1[:-1]==p2[:-1] and p1[-1]!=p2[-1]


class Word(unittest.TestCase):
    def test_shortest_and_none(self):
        rng=random.Random(30001);found=nones=0
        for _ in range(300):
            n1,n2,k=rng.randint(1,4),rng.randint(1,4),rng.randint(1,3);d1,e1=rand_machine(rng,n1,k,2);d2,e2=rand_machine(rng,n2,k,2)
            s1,s2=rng.randrange(n1),rng.randrange(n2);w=S8.distinguishing_word(d1,e1,s1,d2,e2,s2);L=n1*n2
            best=None
            for l in range(1,L+1):
                for x in itertools.product(range(k),repeat=l):
                    p1=S8.run_word(d1,e1,s1,x);p2=S8.run_word(d2,e2,s2,x)
                    if p1!=p2:best=l;break
                if best:break
            if best is None:self.assertIsNone(w);nones+=1
            else:self.assertEqual(len(w),best);self.assertTrue(sep(d1,e1,s1,d2,e2,s2,w));found+=1
        self.assertGreater(found,50);self.assertGreater(nones,5)


class Identify(unittest.TestCase):
    def test_equals_identify6(self):
        rng=random.Random(30002);seen=set()
        for _ in range(40):
            n,k=rng.randint(2,5),rng.randint(2,3);acts,codes=trace(rng,n,k,rng.randint(10,60));masks=[1<<c for c in codes]
            a=identify6(masks,acts,k,4,8,perf_counter()+60);b=S8.identify8(masks,acts,k,4,8,perf_counter()+60)
            for f in ('n_min','unique','unknown','second_found'):self.assertEqual(a[f],b[f],f)
            self.assertEqual(a['model'],b['model']);seen.add((b['unique'],b['second_found']))
            if b['second_found']:
                d,e=b['model2'];self.assertTrue(simulate(d,e,acts,masks)[0]);self.assertNotEqual(b['model'],b['model2'])
            h=len(acts)//2;c=S8.identify8(masks[:h+1],acts[:h],k,4,8,perf_counter()+60)
            r=S8.identify8(masks,acts,k,4,8,perf_counter()+60,n_lo=c['n_min'])
            self.assertEqual((r['n_min'],r['unique'],r['second_found']),(b['n_min'],b['unique'],b['second_found']))
        self.assertIn((True,False),seen);self.assertIn((False,True),seen)

    def test_query_cap(self):
        rng=random.Random(30003);acts,codes=trace(rng,5,3,80);masks=[1<<c for c in codes]
        r=S8.identify8(masks,acts,3,4,8,perf_counter()+60,query_s=0.0)
        self.assertTrue(r['unknown']);self.assertGreaterEqual(r['capped'],1);self.assertIsNone(r['n_min'])
        self.assertLessEqual(max(r['query_walls']),0.5)


class Active(unittest.TestCase):
    def test_sound_loop(self):
        rng=random.Random(30004);stops=set();used_any=0
        for _ in range(40):
            n,k=rng.randint(3,6),rng.randint(2,3);d,e=rand_machine(rng,n,k);q=0;acts=[];masks=[1<<e[0]]
            for _ in range(rng.randint(8,30)):a=rng.randrange(k);q=d[q][a];acts.append(a);masks.append(1<<e[q])
            st=[q];calls=[]
            def obs(a):
                calls.append(a);st[0]=d[st[0]][a];return 1<<e[st[0]]
            K=rng.choice((4,16,64));r=S8.active8(masks,acts,k,4,8,obs,perf_counter()+60,K=K);stops.add(r['stop'])
            self.assertLessEqual(r['used'],K);self.assertEqual(len(calls),r['used']);self.assertEqual(r['acts'][len(acts):],calls)
            self.assertTrue(simulate(d,e,r['acts'],r['masks'])[0]);used_any+=r['used']>0
            for x in r['rounds']:
                if x.get('word'):
                    (d1,e1),(d2,e2)=x['M1'],x['M2'];self.assertTrue(sep(d1,e1,x['s1'],d2,e2,x['s2'],x['word']))
                    T=x['T'];self.assertTrue(simulate(d1,e1,r['acts'][:T],r['masks'][:T+1])[0]);self.assertTrue(simulate(d2,e2,r['acts'][:T],r['masks'][:T+1])[0])
                    if 'obs' in x:
                        o=x['obs'];self.assertFalse(all(oo>>c&1 for oo,c in zip(o,x['pred1'])) and all(oo>>c&1 for oo,c in zip(o,x['pred2'])))
            if r['stop']=='unique':self.assertFalse(r['final']['second_found'])
        self.assertIn('unique',stops);self.assertGreater(used_any,5)


class HostAgnostic(unittest.TestCase):
    def test_source(self):
        src=pathlib.Path(S8.__file__).read_text()
        for bad in ('import os','subprocess','threading','multiprocessing','open(','socket','print('):self.assertNotIn(bad,src)


if __name__=='__main__':unittest.main()
