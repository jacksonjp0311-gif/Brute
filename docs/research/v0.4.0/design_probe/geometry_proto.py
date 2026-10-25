"""Design-probe prototype of the constraint (H-)representation of the <=n version space (see brute/geometry.py)."""
from itertools import combinations
from pysat.solvers import Solver

ALL=0b1111


class ConstraintRegion:
    """CNF over complete machines: one-hot state x[t][q] (x[0]=0), one-hot delta d[q][a][r], one-hot emission e[q][c].
    Derived (Tseitin, both directions): A[q][c] (code c compatible with every visit of q), V[q] (q visited),
    Tr[q][a] (edge (q,a) traversed). A row of the enumeration learner is the projection of a model onto
    (x, traversed d, A); every query below is an existential projection of that region."""
    def __init__(self,n,masks,actions,solver='cd19',symmetry=True):
        assert len(masks)==len(actions)+1
        self.n=n;self.masks=list(masks);self.actions=list(actions);self.T=T=len(actions)
        self.nv=0;self.cl=[]
        v=self._v
        self.x=[[v() for _ in range(n)] for _ in range(T+1)]
        self.d=[[[v() for _ in range(n)] for _ in range(2)] for _ in range(n)]
        self.e=[[v() for _ in range(4)] for _ in range(n)]
        for row in self.x:self._one(row)
        for q in range(n):
            for a in range(2):self._one(self.d[q][a])
            self._one(self.e[q])
        self.cl.append([self.x[0][0]])
        if symmetry:  # canonical first-visit naming (the enumeration's naming): q>=1 only after q-1 was visited
            for t in range(T+1):
                for q in range(1,n):self.cl.append([-self.x[t][q]]+[self.x[u][q-1] for u in range(t)])
        for t in range(1,T+1):
            a=actions[t-1]
            for q in range(n):
                for r in range(n):self.cl.append([-self.x[t-1][q],-self.d[q][a][r],self.x[t][r]])
        for t,m in enumerate(masks):
            for q in range(n):self.cl.append([-self.x[t][q]]+[self.e[q][c] for c in range(4) if m>>c&1])
        self.A=[[v() for _ in range(4)] for _ in range(n)]
        for q in range(n):
            for c in range(4):
                bad=[self.x[t][q] for t,m in enumerate(masks) if not m>>c&1]
                for b in bad:self.cl.append([-self.A[q][c],-b])
                self.cl.append([self.A[q][c]]+bad)
        self.V=[v() for _ in range(n)]
        for q in range(n):
            xs=[self.x[t][q] for t in range(T+1)]
            for b in xs:self.cl.append([-b,self.V[q]])
            self.cl.append([-self.V[q]]+xs)
        self.Tr=[[v() for _ in range(2)] for _ in range(n)]
        for q in range(n):
            for a in range(2):
                xs=[self.x[t][q] for t in range(T) if actions[t]==a]
                for b in xs:self.cl.append([-b,self.Tr[q][a]])
                self.cl.append([-self.Tr[q][a]]+xs)
        self.nx=[[v() for _ in range(n)] for _ in range(2)];self.nc=[[v() for _ in range(4)] for _ in range(2)]
        for b in range(2):
            for q in range(n):
                for r in range(n):self.cl.append([-self.x[T][q],-self.d[q][b][r],self.nx[b][r]])
            self._amo(self.nx[b])
            for r in range(n):
                for c in range(4):self.cl.append([-self.nx[b][r],-self.e[r][c],self.nc[b][c]])
            self._amo(self.nc[b])
        self.clauses_base=len(self.cl);self.vars_base=self.nv
        self.s=Solver(name=solver,bootstrap_with=self.cl);self.calls=0
        self._sat=self._solve([])

    def _v(self):
        self.nv+=1;return self.nv
    def _amo(self,lits):
        for a,b in combinations(lits,2):self.cl.append([-a,-b])
    def _one(self,lits):
        self.cl.append(list(lits));self._amo(lits)
    def _solve(self,assume):
        self.calls+=1;return self.s.solve(assumptions=assume)
    def _add(self,clauses):
        for c in clauses:self.s.add_clause(c)
    def close(self):self.s.delete()

    @property
    def feasible(self):return self._sat

    def support(self,b):
        if not self._sat:return None
        return tuple(c for c in range(4) if self._solve([self.nc[b][c]]))

    def saturated(self):
        if not self._sat:return None
        g=self._v();self._add([[-g]+[-x for x in self.V]])
        r=not self._solve([g]);self._add([[-g]]);return r

    def fibre_support(self,b,mask_hist,act_hist=()):
        if not self._sat:return None
        n=self.n;w=len(act_hist);assert len(mask_hist)==w+1
        out=[]
        for c in range(4):
            v=self._v;g=v();C=[]
            P=[[v() for _ in range(n)] for _ in range(w+1)]
            for i in range(w+1):
                C.append([-g]+P[i])
                for a_,b_ in combinations(P[i],2):C.append([-g,-a_,-b_])
                for q in range(n):
                    C.append([-P[i][q],self.V[q]])
                    C.append([-P[i][q]]+[self.A[q][cc] for cc in range(4) if mask_hist[i]>>cc&1])
            for i in range(1,w+1):
                a=act_hist[i-1]
                for q in range(n):
                    for r in range(n):
                        C.append([-P[i-1][q],-P[i][r],self.Tr[q][a]]);C.append([-P[i-1][q],-P[i][r],self.d[q][a][r]])
            K1=[v() for _ in range(n)];K2=[v() for _ in range(n)];W=[v() for _ in range(n)]
            for j in range(n):
                pj=P[w][j]
                C.append([-pj,K1[j],K2[j]])
                C.append([-K1[j],self.Tr[j][b]])
                for r in range(n):C.append([-K1[j],-self.d[j][b][r],self.A[r][c]])
                C.append([-K2[j],-self.Tr[j][b]]);C.append([-K2[j],self.x[self.T][j]])
                C.append([-K2[j]]+W+[-x for x in self.V])
                C.append([-W[j],self.V[j]]);C.append([-W[j],self.A[j][c]])
            self._add(C)
            if self._solve([g]):out.append(c)
            self._add([[-g]])
        return tuple(out)
