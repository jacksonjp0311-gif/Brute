"""Post-run diagnostic for study-051 GCOMPAT16S (deviation #176; informational, never a gate). For every part c case whose
label is IDF, checks whether the API16S_c model and the part-k API16E model are the same machine up to renaming AND choice of
start state (BFS form rooted at some state of each). IDF means identified from the current state, not from the start, so a
model that differs only in its start state is allowed by the label. Observed. New file.
  PYTHONPATH=. python scripts/diag_compat_051.py results/study-051/main"""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common_051 import load,write_new
from scripts.recount_051 import bfs_form
OUT=ROOT/'results/diag-051/COMPAT_IDF_DIAG_051.json'


def rooted(m,s):
    d,e=m;idx={s:0};o=[s];i=0
    while i<len(o):
        q=o[i];i+=1
        for t in d[q]:
            if t not in idx:idx[t]=len(o);o.append(t)
    return [[[idx[t] for t in d[q]] for q in o],[e[q] for q in o]]


def main(argv=None):
    argv=sys.argv[1:] if argv is None else argv;res=load(Path(argv[0])/'RESULTS.json')
    K={c['seed']:c['arms']['API16E'] for c in res['cases'] if c['block']=='main' and c['key']=='control'};out={'label':'Observed','cases':{}}
    for c in res['cases']:
        if c['block']!='c':continue
        s=c['arms']['API16S_c'];e=K[c['seed']]
        if s['label']!='IDF':continue
        n=len(e['model'][1]);pairs=[[a,b] for a in range(n) for b in range(len(s['model'][1])) if rooted(e['model'],a)==rooted(s['model'],b)]
        out['cases'][str(c['seed'])]={'labels':[e['label'],s['label']],'equal_from_start_0':bfs_form(e['model'])==bfs_form(s['model']),
            'isomorphic_some_start':bool(pairs),'start_of_API16E_maps_to':[b for a,b in pairs if a==0],
            'future_match':[e.get('future_match'),s.get('future_match')],'T_final':[e.get('T_final'),s.get('T_final')]}
    write_new(OUT,out);print(json.dumps(out));return 0


if __name__=='__main__':sys.exit(main())
