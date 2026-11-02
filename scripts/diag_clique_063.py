"""Exploratory diagnostic for plan 063 (new file; not evidence for any gate). For each sealed study-062 main record (sealed seeds
only), rebuild the full 2-bit trace from experiments/worlds_058 and the recorded actions, then report on the trace's apartness graph
(brute.scalesearch15.apart_matrix, frozen): the greedy clique the frozen Pool15/Pool16E pins (greedy_clique on the final trace),
the EXACT maximum clique (deterministic Tomita-style branch and bound with a greedy-colouring bound, node cap NODE_CAP), and the
number of distinct true states the trace visited (an upper bound on any clique; read from the true world, so oracle, report only).
Question it answers: is the frozen greedy clique leaving lower-bound / symmetry-break strength on the table at 2 bits?
  PYTHONPATH=. python scripts/diag_clique_063.py [--output results/diag-063/CLIQUE_DIAG_063.json]"""
import json,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from brute.scalesearch15 import apart_matrix,greedy_clique
from experiments import worlds_058 as W58
NODE_CAP=2_000_000


def max_clique(A,seed_clique,cap=NODE_CAP):
    n=len(A);adj=[set() for _ in range(n)]
    for t in range(n):
        for u in range(t+1,n):
            if A[t][u]:adj[t].add(u);adj[u].add(t)
    best=list(seed_clique);nodes=[0]
    def colour_sort(P):
        P=sorted(P,key=lambda v:(-len(adj[v]),v));cls=[];order=[];bounds=[]
        for v in P:
            for c in cls:
                if not (adj[v]&c):c.add(v);break
            else:cls.append({v})
        for i,c in enumerate(cls):
            for v in sorted(c):order.append(v);bounds.append(i+1)
        return order,bounds
    def expand(R,P):
        nonlocal best
        nodes[0]+=1
        if nodes[0]>cap:return
        order,bounds=colour_sort(P)
        for i in range(len(order)-1,-1,-1):
            if len(R)+bounds[i]<=len(best):return
            v=order[i];R2=R+[v];P2=[u for u in order[:i] if u in adj[v]]
            if not P2:
                if len(R2)>len(best):best=R2
            else:expand(R2,P2)
    expand([],list(range(n)))
    return sorted(best),nodes[0]<=cap,nodes[0]


def main(argv):
    out=Path(argv[argv.index('--output')+1]) if '--output' in argv else None
    R=json.load(open(ROOT/'results/study-062/main/RESULTS.json'));rows=[]
    for c in R['cases']:
        for arm,a in c['arms'].items():
            fam=a['family'];w=W58.world(c['seed'],fam);pa=list(W58.actions(c['seed'],0.0,w.k));acts=pa+list(a['extra_acts'])
            q=w.start;codes=[w.emissions[q]];states=[q]
            for x in acts:q=w.transitions[q][x];codes.append(w.emissions[q]);states.append(q)
            masks=[1<<x for x in codes];t0=time.perf_counter();A=apart_matrix(masks,acts);g=greedy_clique(A)
            mc,exact,nodes=max_clique(A,g)
            rows.append({'seed':c['seed'],'arm':arm,'label':a['label'],'steps':len(acts),'greedy_clique':len(g),'max_clique':len(mc),
                         'max_clique_exact':exact,'bb_nodes':nodes,'distinct_true_states_visited':len(set(states)),'true_size':a['true_size'],
                         'recorded_clique_prefix':a['clique_prefix'],'recorded_clique_final':a['clique_final'],'n_min':a['n_min'],
                         'wall_s':round(time.perf_counter()-t0,2)})
            print(json.dumps(rows[-1]),flush=True)
    res={'label':'Observed (exploratory, sealed study-062 seeds; distinct_true_states is oracle, report only)','rows':rows}
    if out:
        if out.exists():raise SystemExit(f'refusing to overwrite {out}')
        out.write_text(json.dumps(res,indent=1,sort_keys=True)+'\n')


if __name__=='__main__':main(sys.argv[1:])
