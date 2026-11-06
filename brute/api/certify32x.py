"""brute.certify/32x (v0.67.0, hybrid arm H of BRUTE_PLAN_071): certify a given hypothesis's current state from ONE reset-free trace
under the declared state bound N alone. A rival is any Moore machine with <= N states and 4 reading codes; the SAT asks for a rival
reproducing a pinned suffix window of the trace and ending apart (leveled apartness, depth N+n) from the hypothesis state q*. UNSAT ->
IDF (exact, conditional on N and clean readings: the window is a relaxation of the full trace). SAT -> the rival is checked on the full
trace; inconsistent -> double the window; consistent and apart -> its separating word is a targeted experiment (K budget).
Symmetry breaking pins window positions that the TRACE shows pairwise apart to distinct rival states (hypothesis only guides choice).
Host-agnostic: no I/O; the solver is brute.api.certify16d.counted16d."""
from __future__ import annotations
from brute.api.certify16d import counted16d

API='brute.certify/32x'


def _sep(T1,E1,p,T2,E2,q):
    """Shortest word w with different readings from R-state p and H-state q (product BFS), or None if equivalent."""
    seen={(p,q):()};Q=[(p,q)];i=0
    while i<len(Q):
        x=Q[i];i+=1
        if E1[x[0]]!=E2[x[1]]:return list(seen[x])
        for a in range(len(T2[0])):
            y=(T1[x[0]][a],T2[x[1]][a])
            if y not in seen:seen[y]=seen[x]+(a,);Q.append(y)
    return None


def _track(T,E,acts,reads,u,j,S=None):
    """States set after tracking machine (T, E) over positions u..j from every state reading reads[u] (or S)."""
    S={p for p in range(len(T)) if E[p]==reads[u]} if S is None else S
    for i in range(u,j):
        a=acts[i];r=reads[i+1];S={T[p][a] for p in S};S={p for p in S if E[p]==r}
        if not S:return S,i+1
    return S,j


class Certifier32X:
    def __init__(self,initial,num_actions,family_bound,m=4,K=40000,conflict_cap=50000,budget_conflicts=50000000,max_window_steps=100000):
        self.k=num_actions;self.N=family_bound;self.m=m;self.K=K;self.cap=conflict_cap;self.budget=budget_conflicts
        self.maxw=max_window_steps;self.acts=bytearray();self.reads=bytearray([initial]);self.H=None;self.label=None
        self.used=0;self.spent=0;self.iters=0;self.windows=[];self.win_steps=0;self.final=None;self.exps=[];self.s=None;self.why=None;self.cands=24;self.clique=0

    def observe(self,a,r):
        self.acts.append(a);self.reads.append(r)
        if self.H is not None:self.used+=1;self._extend_final()

    # --- SAT encoding -------------------------------------------------------------------------------------------------------
    def _v(self):self.nv+=1;return self.nv

    def set_hypothesis(self,T,E,origin=None):
        """Hypothesis (T, E) whose state 0 is the target state at trace position origin (default: now)."""
        self.H=([list(r) for r in T],list(E));self.L0=len(self.acts) if origin is None else origin;self.h0=0;n=len(T);N=self.N;k=self.k;m=self.m;self.s=counted16d();self.nv=0;v=self._v;add=self.s.add_clause
        self.d=[[[v() for _ in range(N)] for _ in range(k)] for _ in range(N)];self.e=[[v() for _ in range(m)] for _ in range(N)]
        def one(L):
            add(L)
            for i in range(len(L)):
                for j in range(i+1,len(L)):add([-L[i],-L[j]])
        for p in range(N):
            for a in range(k):one(self.d[p][a])
            one(self.e[p])
        TH,EH=self.H;Kd=N+n;self.ap=[[[v() for _ in range(n)] for _ in range(N)] for _ in range(Kd+1)]
        for p in range(N):
            for q in range(n):add([-self.ap[0][p][q],-self.e[p][EH[q]]])
        for j in range(1,Kd+1):
            for p in range(N):
                for q in range(n):
                    zs=[]
                    for a in range(k):
                        for p2 in range(N):
                            z=v();zs.append(z);add([-z,self.d[p][a][p2]]);add([-z,self.ap[j-1][p2][TH[q][a]]])
                    add([-self.ap[j][p][q],self.ap[j-1][p][q],-self.e[p][EH[q]]]+zs)
        self.Kd=Kd;self.clauses0=self.s.n_clauses

    def _apart(self,i,j):
        """True iff the trace itself shows positions i and j in different target states (same actions, then different reading)."""
        A=self.acts;R=self.reads;L=len(A);t=0
        while True:
            if R[i+t]!=R[j+t]:return True
            if i+t>=L or j+t>=L or A[i+t]!=A[j+t]:return False
            t+=1

    def _clique(self,u,j):
        """Window positions pairwise trace-apart, one per H-state where possible (H only guides the choice; apartness is
        checked on the trace itself, so pinning them to distinct rival states is sound symmetry breaking)."""
        TH,EH=self.H;n=len(TH);allq=lambda r:{p for p in range(n) if EH[p]==r};S=allq(self.reads[u]);cand={}
        for i in range(u,j+1):
            if i>u:
                a=self.acts[i-1];S={TH[p][a] for p in S};S={p for p in S if EH[p]==self.reads[i]}
                if not S:S=allq(self.reads[i])
            if len(S)==1:
                q=next(iter(S));lst=cand.setdefault(q,[])
                if len(lst)<self.cands:lst.append(i)
        groups=sorted(cand.values(),key=len);best=[];nodes=[0]
        def dfs(g,C):
            nonlocal best
            nodes[0]+=1
            if len(C)+len(groups)-g<=len(best) or nodes[0]>20000:return
            if g==len(groups):best=list(C);return
            for i in groups[g]:
                if all(self._apart(i,c) for c in C):C.append(i);dfs(g+1,C);C.pop()
                if len(best)==len(groups):return
            dfs(g+1,C)
        dfs(0,[]);return best[:self.N]

    def _window(self,u,j,pin=False):
        """Positions u..j constrained: one rival run reproduces readings reads[u..j]. Returns the list of per-position state vars."""
        N=self.N;add=self.s.add_clause;X=[]
        for i in range(u,j+1):X.append(self._pos(X,i,False))
        if pin:
            self.g=self._v();C=self._clique(u,j);self.clique=len(C)
            for idx,i in enumerate(C):add([-self.g,X[i-u][idx]])
        self.windows.append((u,j));self.win_steps+=j-u;return X

    def _pos(self,X,i,pin):
        N=self.N;add=self.s.add_clause;x=[self._v() for _ in range(N)];r=self.reads[i]
        for p in range(N):add([-x[p],self.e[p][r]])
        if not X:
            add(list(x))
        else:
            a=self.acts[i-1];y=X[-1]
            for p in range(N):
                for p2 in range(N):add([-y[p],-self.d[p][a][p2],x[p2]])
        return x

    def _extend_final(self):
        if self.final is None:return
        X,u=self.final
        while u+len(X)-1<len(self.acts):X.append(self._pos(X,u+len(X),False))

    def _qstar(self):
        TH,EH=self.H
        if EH[self.h0]!=self.reads[self.L0]:return None,'HYP_INCONSISTENT'
        S,_=_track(TH,EH,self.acts,self.reads,self.L0,len(self.acts),{self.h0})
        if not S:return None,'HYP_INCONSISTENT'
        S=sorted(S);q=S[0]
        for p in S[1:]:
            w=_sep(TH,EH,p,TH,EH,q)
            if w is not None:return None,('HYP_AMBIG',w)
        return q,None

    def _model(self):
        M=set(l for l in self.s.get_model() if l>0);N=self.N
        T=[[next(p2 for p2 in range(N) if self.d[p][a][p2] in M) for a in range(self.k)] for p in range(N)]
        E=[next(c for c in range(self.m) if self.e[p][c] in M) for p in range(N)];return T,E

    def propose(self):
        if self.label is not None:return None
        L=len(self.acts)
        if self.final is None:
            u=max(0,L-64);self.final=(self._window(u,L,pin=True),u)
        while True:
            q,bad=self._qstar()
            if bad=='HYP_INCONSISTENT':self.label='HYP_REJECTED';self.why=bad;return None
            if bad:
                w=bad[1]
                if self.used+len(w)>self.K:self.label='K_spent';return None
                self.exps.append(('hyp',len(w)));return list(w)
            X,u=self.final;sel=self._v();add=self.s.add_clause;xl=X[-1]
            for p in range(self.N):add([-sel,-xl[p],self.ap[self.Kd][p][q]])
            left=self.budget-self.spent
            if left<=0:self.label='IDU';return None
            b0=self.s.conflicts();self.s.conf_budget(min(self.cap,left));r=self.s.solve_limited(assumptions=[sel,self.g]);self.spent+=self.s.conflicts()-b0
            add([-sel]);self.iters+=1
            if r is None:
                if self.spent>=self.budget:self.label='IDU';return None
                X,u=self.final;uu=max(0,L-2*(L-u))
                if uu==u:continue
                self.final=(self._window(uu,L,pin=True),uu)
                if self.win_steps>self.maxw:self.label='WINDOW_CAP';return None
                continue
            if r is False:self.label='IDF';self.q=q;return None
            T,E=self._model();TH,EH=self.H
            S,j=_track(T,E,self.acts,self.reads,0,L)
            if not S:
                X,u=self.final;ln=2*(L-u)
                while True:
                    uu=max(0,L-ln);S2,_=_track(T,E,self.acts,self.reads,uu,L)
                    if not S2 or uu==0:break
                    ln*=2
                self.final=(self._window(uu,L,pin=True),uu)
                if self.win_steps>self.maxw:self.label='WINDOW_CAP';return None
                continue
            rivals=[(p,_sep(T,E,p,TH,EH,q)) for p in S];rivals=[x for x in rivals if x[1] is not None]
            if rivals:
                w=min((x[1] for x in rivals),key=len)
                if self.used+len(w)>self.K:self.label='K_spent';return None
                self.exps.append(('rival',len(w)));return list(w)
            ln=2*len(X)
            while True:
                uu=max(0,L-ln);S2,_=_track(T,E,self.acts,self.reads,uu,L)
                if all(_sep(T,E,p,TH,EH,q) is None for p in S2) or uu==0:break
                ln*=2
            self.final=(self._window(uu,L,pin=True),uu);self.win_steps+=0
            if self.win_steps>self.maxw:self.label='WINDOW_CAP';return None

    def close(self):
        if self.s is not None:self.s.delete();self.s=None

    def result(self):
        return {'api':API,'label':self.label,'iters':self.iters,'conflicts':self.spent,'windows':len(self.windows),'window_steps':self.win_steps,
                'experiments':len(self.exps),'exp_steps':self.used,'vars':self.nv,'clauses':self.s.n_clauses if self.s else 0,'why':self.why,'clique':self.clique,'q_star':getattr(self,'q',None),'assumes_resync':False,
                'hyp_T':self.H[0] if self.H else None,'hyp_E':self.H[1] if self.H else None}
