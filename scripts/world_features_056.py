"""Post-run exploratory analysis for v0.54.0 planning (new file; not gated; read-only over sealed RESULTS of studies 050, 051,
054, 055, 056). For every 20-state world it computes static structure of the true machine (emission classes, pairwise
separation depth, start eccentricity, self-loops) and joins the per-arm outcome, stop step, K used, conflicts, the number of
truth (state, action) pairs the trace never exercised, n_min and rounds. Usage: PYTHONPATH=. python scripts/world_features_056.py OUT.json"""
import json,sys
from collections import deque
sys.path.insert(0,'.')
from experiments import worlds_050 as W50
def feats(w):
    n=w.n;k=w.k;T=w.transitions;E=w.emissions
    # pair separation depth via BFS on pairs
    INF=99;D={}
    q=deque()
    for i in range(n):
        for j in range(i+1,n):
            if E[i]!=E[j]:D[(i,j)]=0;q.append((i,j))
    pre={}
    for i in range(n):
        for j in range(i+1,n):
            for a in range(k):
                x,y=T[i][a],T[j][a]
                if x==y:continue
                p=(min(x,y),max(x,y));pre.setdefault(p,[]).append((i,j))
    while q:
        p=q.popleft()
        for r in pre.get(p,[]):
            if r not in D:D[r]=D[p]+1;q.append(r)
    ds=[D.get((i,j),INF) for i in range(n) for j in range(i+1,n)]
    # reachable from start, and diameter from start
    dist={w.start:0};q=deque([w.start])
    while q:
        s=q.popleft()
        for a in range(k):
            t=T[s][a]
            if t not in dist:dist[t]=dist[s]+1;q.append(t)
    return {'n':n,'k':k,'emission_classes':len(set(E)),'sep_depth_max':max(ds),'sep_depth_mean':round(sum(ds)/len(ds),3),
            'pairs_depth_ge2':sum(d>=2 for d in ds),'unseparable_pairs':sum(d==INF for d in ds),'reach':len(dist),'ecc_start':max(dist.values()),
            'self_loops':sum(T[s][a]==s for s in range(n) for a in range(k))}
out={}
for st,key,fam in (('056','scale20t','scale20'),('050','scale20','scale20'),('055','scale20t','scale20'),('054','scale20t','scale20'),('051','scale20','scale20')):
    try:R=json.load(open(f'results/study-{st}/main/RESULTS.json'))
    except Exception as e:continue
    for c in R['cases']:
        if c.get('n')!=20:continue
        w=W50.world(c['seed'],fam);f=feats(w)
        f['labels']={g:a.get('label') for g,a in c['arms'].items()};f['conflicts']={g:a.get('conflicts_spent') for g,a in c['arms'].items()}
        f['T_final']={g:a.get('T_final') for g,a in c['arms'].items()}
        f['used']={g:a.get('used') for g,a in c['arms'].items()}
        f['unexercised']={g:(len(a['truth_pairs_unexercised']) if isinstance(a.get('truth_pairs_unexercised'),list) else a.get('truth_pairs_unexercised')) for g,a in c['arms'].items()}
        f['n_min']={g:a.get('n_min') for g,a in c['arms'].items()}
        f['rounds']={g:a.get('n_rounds') for g,a in c['arms'].items()}
        out[f'{st}/{c["key"]}/{c["seed"]}']=f
json.dump(out,open(sys.argv[1],'w'),indent=1,sort_keys=True)
if 0:print(k,{x:f[x] for x in ('emission_classes','sep_depth_max','sep_depth_mean','pairs_depth_ge2','ecc_start','self_loops')},sorted(set(f['labels'].values())))

rows=[(k,g,f['labels'][g],f['unexercised'][g],f['n_min'][g]) for k,f in out.items() for g in f['labels'] if g in ('API16E','API16E20')]
dec=lambda r:r[2] in ('ID','IDF')
s0=[r for r in rows if r[3]==0];s1=[r for r in rows if r[3] not in (0,None)]
summ={'certify16e_records_n20':len(rows),'decided':[r[:3] for r in rows if dec(r)],'unexercised_0':{'records':len(s0),'decided':sum(map(dec,s0)),'seeds':[r[0] for r in s0]},
      'unexercised_gt0':{'records':len(s1),'decided':sum(map(dec,s1))},'note':'API16E rows from 050 are B 4M; API16E20 rows from 054-056 are B 2M; _b passes excluded'}
json.dump({'worlds':out,'summary':summ},open(sys.argv[1],'w'),indent=1,sort_keys=True);print(json.dumps(summ))
