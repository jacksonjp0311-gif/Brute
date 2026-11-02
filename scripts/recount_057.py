"""G_recount for study-057 (BRUTE_PLAN_057; pre-run deviation #188). New file; built from scripts/recount_056.py (frozen).
The per-case logic is the frozen scripts/recount_047.py recount_case, imported unchanged, with its module names ORDER / DELTA / W43
bound in this process to the 057 arms (every arm at bound 20) and to experiments/worlds_050. One #188 reading for the extension arms
(COV_O, LEN_R, COV_X, COV_X_b): their extra_acts hold the extension followed by the certifier's words, while the record's 'used'
counts word steps only (as certify/16e reports it). The 047 ('used', ...) item is dropped for such an arm exactly when the record's
used == the recounted words_executed_length AND len(extra_acts) == ext_len + used; it is kept otherwise.
Also recomputed here, independent of the runner's bookkeeping (GMATCH57 input): per record the hand-off and final truth coverage
(unexercised (state, action) pairs overall and at states reachable from the true state), the COV_O extension against the declared
oracle walk, the LEN_R extension against the declared seeded RNG at the same seed's COV_O length, and the API16E20 extension empty.
Writes <study>/RECOUNT_057.json (refuses overwrite).
  PYTHONPATH=. python scripts/recount_057.py results/study-057/main"""
import json,random,sys
from collections import deque
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common import load,write_new,sha
from experiments import worlds_050 as W50
from experiments.brute_common_057 import ALL_ARMS,EXT_ARMS,KEY
from scripts import recount_047 as R47
R47.ORDER=ALL_ARMS;R47.DELTA={a:None for a in ALL_ARMS};R47.W43=W50
_counts=R47._counts


def recount_case(c):
    out,bad=R47.recount_case(c)
    for arm in EXT_ARMS:
        if arm not in out:continue
        a=c['arms'][arm];rec=out[arm];el=a.get('ext_len')
        rec['used_ok_057']=bool(isinstance(el,int) and a['used']==rec['words_executed_length'] and len(a.get('extra_acts') or [])==el+a['used'])
        if rec['used_ok_057']:bad=[b for b in bad if not (isinstance(b,tuple) and len(b)==4 and b[0]==arm and b[1]=='used' and b[3]==el+a['used'])]
    return out,bad


def _walk(w,acts):
    q=w.start;used=set()
    for a in acts:used.add((q,a));q=w.transitions[q][a]
    seen={q};dq=deque([q])
    while dq:
        s=dq.popleft()
        for t in w.transitions[s]:
            if t not in seen:seen.add(t);dq.append(t)
    return w.n*w.k-len(used),sum(1 for s in seen for a in range(w.k) if (s,a) not in used),used,q


def oracle(w,acts):
    """Independent re-implementation of plan design.oracle_walk."""
    _,_,used,q=_walk(w,acts);used=set(used);ext=[]
    while True:
        par={q:None};dq=deque([q]);hit=None
        while dq and hit is None:
            s=dq.popleft()
            for a in range(w.k):
                if (s,a) not in used:hit=(s,a);break
            if hit:break
            for a in range(w.k):
                t=w.transitions[s][a]
                if t not in par:par[t]=(s,a);dq.append(t)
        if hit is None:return ext
        s,a0=hit;p=[]
        while par[s] is not None:p.append(par[s][1]);s=par[s][0]
        for a in p[::-1]+[a0]:used.add((q,a));ext.append(a);q=w.transitions[q][a]


def coverage_case(c):
    w=W50.world(c['seed'],c['family']);pa=list(W50.actions(c['seed'],0.0,w.k));out={};bad=[];orc=oracle(w,pa)
    for arm,a in c['arms'].items():
        ext=list(a.get('ext_acts') or []);ok=list((a.get('extra_acts') or [])[:len(ext)])==ext and a.get('ext_len')==len(ext)
        uh,urh,_,_=_walk(w,pa+ext);uf,urf,_,_=_walk(w,pa+list(a.get('extra_acts') or []))
        if arm=='COV_O':ok=ok and ext==orc
        elif arm=='LEN_R':r=random.Random(c['seed']*7+57);ok=ok and ext==[r.randrange(w.k) for _ in range(len(orc))]
        elif arm=='API16E20':ok=ok and ext==[]
        rec={'ext_len':len(ext),'handoff':uh,'handoff_reachable':urh,'final':uf,'final_reachable':urf,'ext_ok':ok,'oracle_len':len(orc)}
        for f,v in (('truth_pairs_unexercised_handoff',uh),('truth_pairs_unexercised_handoff_reachable',urh),
                    ('truth_pairs_unexercised_final',uf),('truth_pairs_unexercised_final_reachable',urf)):
            if a.get(f)!=v:bad.append((arm,f,a.get(f),v))
        if not ok:bad.append((arm,'extension'))
        out[arm]=rec
    return out,bad


def main(argv=None):
    argv=sys.argv[1:] if argv is None else argv;d=Path(argv[0]);res=load(d/'RESULTS.json');per={};bad={};cov={}
    for c in res['cases']:
        k=f"{c['block']}/{c['key']}/{c['seed']}";per[k],b=recount_case(c);cov[k],b2=coverage_case(c)
        if b or b2:bad[k]=b+b2
    blk=res['block'];allv=list(per.values())
    out={'schema':'brute.recount.v54_0','results_sha256':sha(d/'RESULTS.json'),'cases':len(res['cases']),'recounted':len(per),
         'labels':{KEY:{arm:_counts([v for v in allv],arm) for arm in ALL_ARMS if any(arm in v for v in allv)}},
         'coverage':cov,
         'misfires':{arm:sum(1 for v in allv if arm in v and v[arm]['misfire']) for arm in ALL_ARMS},
         'amb_rule_applied':sum('amb_rule' in v[a] for v in allv for a in v),
         'words_unsound':sum(v[a]['words_unsound'] for v in allv for a in v),
         'words_checked':sum(v[a]['words_checked'] for v in allv for a in v),
         'truth_inconsistent':sum(sum(v[a]['truth_inconsistent_rounds'] for a in v)+sum(not x['truth_consistent_final'] for x in v.values()) for v in allv),
         'mismatching_cases':len(bad),'mismatches':{k:v for k,v in list(bad.items())[:50]},'per_case':per,
         'PASS':not bad and len(per)==len(res['cases'])>0}
    write_new(d/'RECOUNT_057.json',out);print(json.dumps({k:v for k,v in out.items() if k not in ('per_case','coverage')},default=str));return 0 if out['PASS'] else 1


if __name__=='__main__':sys.exit(main())
