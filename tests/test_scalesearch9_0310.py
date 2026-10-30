"""v0.31.0: A9 sound active identification (brute.scalesearch9). differ9 equals exhaustive enumeration of every complete
machine with <= n states (n <= 3, 2 actions, 2 codes) in both modes: SAT exactly when some consistent machine differs from
M1 from the given states, and a SAT answer decodes to a consistent machine and a separating word; least9 equals
enumeration on n_min; active9 on minimal reachable truths with N = their size never stops 'ID' on a machine that is not the truth, keeps the hidden machine consistent,
executes only sound words, never exceeds K and reaches the world only through observe; the per-query cap gives
'unknown'; host-agnostic source. New file."""
import itertools,random,unittest,pathlib
from time import perf_counter
from brute import scalesearch9 as S9
from brute.scalesearch8 import _Owner8,run_word
from brute.scalesearch import simulate,canonical_bfs


def rand_machine(rng,n,k,m):return [[rng.randrange(n) for _ in range(k)] for _ in range(n)],[rng.randrange(m) for _ in range(n)]


def all_machines(n,k,m):
    for d in itertools.product(range(n),repeat=n*k):
        D=[list(d[q*k:(q+1)*k]) for q in range(n)]
        for e in itertools.product(range(m),repeat=n):yield D,list(e)


def behaves_differently(d1,e1,s1,d2,e2,s2):
    k=len(d1[0]);seen={(s1,s2)};st=[(s1,s2)]
    while st:
        p,q=st.pop()
        if e1[p]!=e2[q]:return True
        for a in range(k):
            x=(d1[p][a],d2[q][a])
            if x not in seen:seen.add(x);st.append(x)
    return False


def minimal(d,e):
    """Number of behaviour classes (Moore partition refinement)."""
    n=len(d);k=len(d[0]);cls=list(e)
    while True:
        sig=[(cls[q],)+tuple(cls[d[q][a]] for a in range(k)) for q in range(n)];idx={}
        new=[idx.setdefault(x,len(idx)) for x in sig]
        if len(set(new))==len(set(cls)):return len(set(new))
        cls=new


def trace_of(d,e,acts):
    q=0;masks=[1<<e[0]]
    for a in acts:q=d[q][a];masks.append(1<<e[q])
    return masks


class Differ(unittest.TestCase):
    def test_against_enumeration(self):
        rng=random.Random(31001);k=2;m=2;sat=unsat=0
        for it in range(40):
            nt=rng.randint(1,3);d,e=rand_machine(rng,nt,k,m);acts=[rng.randrange(k) for _ in range(rng.randint(0,7))];masks=trace_of(d,e,acts)
            o=_Owner8(10.0);st,n1,M1=S9.least9(o,masks,acts,k,m,3,perf_counter()+30)
            self.assertEqual(st,'ok')
            least=min(n for n in range(1,4) if any(simulate(D,E,acts,masks)[0] for D,E in all_machines(n,k,m)))
            self.assertEqual(n1,least)
            s1=simulate(M1[0],M1[1],acts,masks)[1]
            for n in range(1,4):
                for mode in ('future','start'):
                    exp=False
                    for D,E in all_machines(n,k,m):
                        ok,s2,_=simulate(D,E,acts,masks)
                        if ok and behaves_differently(M1[0],M1[1],s1 if mode=='future' else 0,D,E,s2 if mode=='future' else 0):exp=True;break
                    f,M2,s2,w=S9.differ9(o,masks,acts,k,m,n,M1,s1,mode,S9.word_len9(3,n1),perf_counter()+30)
                    self.assertEqual(f,exp,(it,n,mode));sat+=f;unsat+=not f
                    if f:
                        self.assertTrue(simulate(M2[0],M2[1],acts,masks)[0])
                        q1,q2=(s1,s2) if mode=='future' else (0,0)
                        self.assertNotEqual([M1[1][q1]]+run_word(M1[0],M1[1],q1,w),[M2[1][q2]]+run_word(M2[0],M2[1],q2,w))
        self.assertGreater(sat,20);self.assertGreater(unsat,20)

    def test_word_bound(self):self.assertEqual(S9.word_len9(12,11),22)


class Active(unittest.TestCase):
    def test_sound_loop(self):
        rng=random.Random(31002);ids=0
        for it in range(25):
            n=rng.randint(2,5);k=rng.randint(2,3);m=4;d,e=rand_machine(rng,n,k,m)
            while len(canonical_bfs(d,e,0)[1])!=n or minimal(d,e)!=n:d,e=rand_machine(rng,n,k,m)
            acts=[rng.randrange(k) for _ in range(rng.randint(3,20))]
            masks=trace_of(d,e,acts);q=[simulate(d,e,acts,masks)[1]];calls=[]
            def obs(a):calls.append(a);q[0]=d[q[0]][a];return 1<<e[q[0]]
            r=S9.active9(masks,acts,k,m,n,obs,perf_counter()+60,K=30)
            self.assertIn(r['stop'],('ID','IDF','K_spent'));self.assertLessEqual(r['used'],30);self.assertEqual(calls,r['acts'][len(acts):])
            self.assertTrue(simulate(d,e,r['acts'],r['masks'])[0])
            if r['stop']=='ID':
                ids+=1;M1=r['final']['model'];self.assertEqual(canonical_bfs(M1[0],M1[1],0),canonical_bfs(d,e,0))
            for x in r['rounds']:
                if x.get('obs') is not None:
                    p1,p2=x['pred1'],x['pred2'];self.assertEqual(p1[:-1],p2[:-1]);self.assertNotEqual(p1[-1],p2[-1])
        self.assertGreater(ids,10)

    def test_cap_unknown(self):
        rng=random.Random(31003);d,e=rand_machine(rng,10,3,4);acts=[rng.randrange(3) for _ in range(60)];masks=trace_of(d,e,acts)
        r=S9.stop_check9(masks,acts,3,4,12,perf_counter()+60,query_s=0.0)
        self.assertEqual(r['stop'],'unknown')

    def test_host_agnostic(self):
        src=pathlib.Path(S9.__file__).read_text()
        for bad in ('import os','subprocess','threading','socket','open(','print('):self.assertNotIn(bad,src)


if __name__=='__main__':unittest.main()
