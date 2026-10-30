"""S5 exact search for Brute v0.27.0 (BRUTE_PLAN_030). New file; brute/region.py (S1) and brute/scalesearch4.py (S4) are
untouched and imported only.

S5 = S4 with two changes:
  1. no symmetry-breaking clauses: the frozen S1 RegionK is built with symmetry=False (S4_nosym of study 029, promoted);
     the encoding is otherwise the S1 encoding, so exact answers are unchanged (symmetry clauses only remove relabelled
     copies of machines; every code they allow or forbid is the same);
  2. a hard per-query cap (scratch diagnosis results/diag-030/OVERRUN_DIAG_030.json): every solver chunk carries, besides
     the S4 conflict chunk, a propagation budget sized from the propagation rate measured on earlier chunks and the cap
     time left (at most CHUNK_TARGET_S and at most PROP_FRACTION of the time left); no chunk starts with less than
     MARGIN_S left; the per-step region build is skipped (query UNKNOWN) when its estimated time exceeds the time left;
     the S1 per-solve budget (CONF conflicts) is counted in conflicts actually used.
S5_softcap (ablation): 1 only, i.e. the S4 chunking unchanged (identical to study-029 S4_nosym).
Soundness: as S4: a code is reported impossible only by an UNSAT proof over the frozen S1 CNF (without symmetry clauses);
a code is reported possible only from a concrete consistent <= n machine (or as UNKNOWN). identify uses the S4 routine
(first-visit symmetry kept there, because uniqueness needs canonical state names).
Host-agnostic: no I/O, network, threads, child processes or global state."""
from __future__ import annotations
from time import perf_counter
from brute.scalesearch4 import (ScaleRegion4,_Region as _Region4,QUERY_S,CONF,SOLVER4,CHUNK_MIN,CHUNK_MAX,CHUNK_TARGET_S,
                                identify_trace)

PROP_RATE0=1.0e6       # propagations per second assumed before the first chunk is measured (conservative)
PROP_MIN=2000
PROP_FRACTION=0.5      # a chunk may use at most this share of the cap time left
MARGIN_S=0.05          # no chunk starts with less than this left
RATE_DECAY=0.5         # rate estimate: min(measured, blend) so one fast chunk cannot inflate the next budget
BUILD_SAFETY=2.0
__all__=['ScaleRegion5','QUERY_S','CONF','SOLVER4','identify_trace','PROP_FRACTION','MARGIN_S']


class _Region5(_Region4):
    """The frozen S1 RegionK (symmetry off), wall-capped by conflict and propagation budgets."""
    def _solve(self,assume):
        if self._skip:self._skip=False;return True
        o=self._owner
        if not o.hard_cap:return _Region4._solve(self,assume)
        self.calls+=1;o.solves+=1;used=0;s=self.s
        while True:
            left=self._dl-perf_counter()
            if left<MARGIN_S:o.unknowns+=1;o.cap_stops+=1;return None
            ch=max(1,min(o.chunk,CONF-used));pb=max(PROP_MIN,int(o.prate*min(CHUNK_TARGET_S,PROP_FRACTION*left)))
            st=s.accum_stats();c0=st.get('conflicts',0);p0=st.get('propagations',0)
            t=perf_counter();s.conf_budget(ch);s.prop_budget(pb);r=s.solve_limited(assumptions=assume);dt=perf_counter()-t
            st=s.accum_stats();dc=st.get('conflicts',0)-c0;dp=st.get('propagations',0)-p0;o.chunks+=1;used+=max(dc,1)
            o.max_chunk_s=max(o.max_chunk_s,dt)
            if dt>1e-3 and dp>0:o.prate=min(dp/dt,RATE_DECAY*o.prate+(1-RATE_DECAY)*dp/dt)
            o.chunk=int(max(CHUNK_MIN,min(CHUNK_MAX,ch*CHUNK_TARGET_S/max(dt,1e-3))))
            if r is not None:return r
            if used>=CONF:o.unknowns+=1;return None


class ScaleRegion5(ScaleRegion4):
    def __init__(self,n_max,k,s=2,query_s=QUERY_S,witness=True,solver=SOLVER4,hard_cap=True):
        ScaleRegion4.__init__(self,n_max,k,s,query_s,witness,solver,symmetry=False)
        self.hard_cap=hard_cap;self.prate=PROP_RATE0;self.cap_stops=0;self.build_skips=0;self.max_chunk_s=0.0
        self._build_rate=None     # seconds per (T+1) * n * n of the last build

    def _region(self,dl=None):
        if self.region is None:
            size=(len(self.acts)+1)*self.n*self.n
            if self.hard_cap and dl is not None and self._build_rate is not None:
                if BUILD_SAFETY*self._build_rate*size>dl-perf_counter()-MARGIN_S:self.build_skips+=1;return None
            t=perf_counter();self.region=_Region5(self,self.n,self.k,self.m,self.masks,self.acts,self.solver,False)
            dt=perf_counter()-t;self.builds+=1;self.timing['build']+=dt;self._build_rate=dt/size
        return self.region

    def support(self,b,deadline=None):
        """As ScaleRegion4.support; the build is guarded by the cap time left when hard_cap."""
        if b not in range(self.k):raise ValueError(f'action must be in 0..{self.k-1}')
        if self.status=='grammar_contradicted':return None,0
        if b in self.memo:return self.memo[b]
        dl=perf_counter()+self.query_s;dl=min(dl,deadline) if deadline is not None else dl
        rest=[c for c in range(self.m) if c not in self.wit[b]];unk=0
        if not rest:self.queries_by_witness+=1
        solved=False
        while rest:
            if perf_counter()>=dl:unk=len(rest);break
            R=self._region(dl)
            if R is None:unk=len(rest);break
            R._dl=dl;g=R._v();R.s.add_clause([-g]+[R.nc[b][c] for c in rest])
            solved=True;t=perf_counter();r=R._solve([g]);self.timing['solve']+=perf_counter()-t;R.s.add_clause([-g])
            if r is None:unk=len(rest);break
            if r is False:
                if len(rest)==self.m:
                    self.status='grammar_contradicted';self.memo={x:(None,0) for x in range(self.k)};return None,0
                break
            self._harvest(R,b,rest);rest=[c for c in rest if c not in self.wit[b]]
        if unk==0 and solved:self.queries_by_solve+=1
        res=(tuple(c for c in range(self.m) if c in self.wit[b] or (unk and c in rest)),unk)
        if unk==0:self.memo[b]=res
        return res
