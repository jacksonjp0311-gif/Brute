"""Scratch diagnosis for study-030 (never a gate input): replays arm S4 / S4_nosym of three study-029 GQB overrun cases
standalone (3 processes in parallel, not 8 workers) with per-chunk wall, conflict and propagation logging, to locate the
029 per-query cap overrun before S5 is built. New file; the replay seeds are 029 main seeds already published.
  PYTHONPATH=. python scripts/diag_030.py <family> <seed> <arm>"""
import sys,json,time
from time import perf_counter
sys.path.insert(0,'/workspace/brute')
import brute.scalesearch4 as S4
from experiments import brute_study_029 as B
from experiments import worlds_026 as W
LOG=[]
orig=S4._Region._solve
def solve(self,assume):
    if self._skip:self._skip=False;return True
    o=self._owner;self.calls+=1;o.solves+=1;used=0
    while True:
        if perf_counter()>=self._dl:o.unknowns+=1;return None
        ch=min(o.chunk,S4.CONF-used);st0=self.s.accum_stats();t=perf_counter();self.s.conf_budget(ch);r=self.s.solve_limited(assumptions=assume)
        dt=perf_counter()-t;st=self.s.accum_stats();o.chunks+=1;used+=ch
        LOG.append((round(dt,3),ch,st['conflicts']-st0['conflicts'],st['propagations']-st0['propagations'],round(self._dl-perf_counter(),3)))
        o.chunk=int(max(S4.CHUNK_MIN,min(S4.CHUNK_MAX,ch*S4.CHUNK_TARGET_S/max(dt,1e-3))))
        if r is not None:return r
        if used>=S4.CONF:o.unknowns+=1;return None
S4._Region._solve=solve
QT=[]
origsup=S4.ScaleRegion4.support
def sup(self,b,deadline=None):
    t=perf_counter();b0=self.timing['build'];s0=self.timing['solve'];n0=len(LOG);r=origsup(self,b,deadline);dt=perf_counter()-t
    if dt>3:QT.append({'q':round(dt,3),'build':round(self.timing['build']-b0,3),'solve':round(self.timing['solve']-s0,3),'chunks':LOG[n0:],'T':len(self.acts)})
    return r
S4.ScaleRegion4.support=sup
fam,seed,arm=sys.argv[1],int(sys.argv[2]),sys.argv[3]
w=W.world(seed,fam);tr=W.trajectory(w,seed,0.0);T=B.S26.truth(w,tr)
A,rec=B.run_arm(arm,w,tr,T,55.0);A.close()
big=sorted(QT,key=lambda x:-x['q'])[:3]
for x in big:x['top_chunks']=sorted(x.pop('chunks'),key=lambda c:-c[0])[:5]
print(json.dumps({'case':[fam,seed,arm],'qmax':rec['query_max_informational'],'U':rec['U_count'],'slow_queries':big,'max_chunk_s':max(c[0] for c in LOG),'chunks':len(LOG)}))
