import sys,json
from probe import *
import probe
from bgr90.symbolic import SymbolicLearner,mask_for_observation

def clone_update(l,a,mask):
    n=SymbolicLearner(l.max_states,l.max_prefixes);n.status=l.status;n.belief=l.belief;n.evidence=[None]
    try:n._update(a,mask)
    except Exception:n.status='x';n.belief=frozenset()
    return n

def certs_after(f,m):
    k=0
    for b in (0,1):
        s=f.predict_support(b) if f.status=='supported' else None
        if s and len(s)==1:
            ms=m.predict_support(b) if m.status=='supported' else None
            if ms==s and not all(p.used==f.max_states for p in f.belief):k+=1
    return k

def code_weights(l,a):
    w=[0.]*4
    for p in l.belief:
        mk=row_mask(p,a,l.max_states);cs=[c for c in range(4) if mk>>c&1]
        for c in cs:w[c]+=1/len(cs)
    z=sum(w);return [x/z for x in w]

def look(L,a):
    if L.support.status!='supported' or L.margin.status!='supported':return 0.
    w=code_weights(L.margin,a);sc=0.
    for c in range(4):
        if w[c]==0:continue
        f=clone_update(L.support,a,1<<c);m=clone_update(L.margin,a,1<<c)
        sc+=w[c]*certs_after(f,m)
    return round(sc,12)

old=probe.choose
def choose(L,policy,pa):
    if policy=='F':sc=[round(entropy(L.support,a),12) for a in (0,1)]
    elif policy=='M':sc=[round(entropy(L.margin,a),12) for a in (0,1)]
    elif policy=='LA':sc=[look(L,a) for a in (0,1)]
    elif policy=='LH':  # lookahead, tie -> entropy
        sc=[(look(L,a),round(entropy(L.support,a)+entropy(L.margin,a),12)) for a in (0,1)]
    else:return old(L,policy,pa)
    if sc[0]==sc[1]:return pa
    return 0 if sc[0]>sc[1] else 1
probe.choose=choose
def main():
    fam=sys.argv[1];pols=sys.argv[2].split(',');lo,hi=PLAN['heldout_ranges'][fam];hi=lo+int(sys.argv[3])-1
    res={}
    for pol in pols:
        post=[];wrong=0
        for seed in range(lo,hi+1):
            for rate in PLAN['mask_rates']:
                o,_,_,_=run(seed,fam,rate,pol);post+=[r for r in o if r['step']>8];wrong+=sum(r['wrong'] for r in o)
        res[pol]=dict(on=round(sum(r['cert'] is not None for r in post)/len(post),4),dual=round(sum(r['dual'] for r in post)/2/len(post),4),wrong=wrong,ll=round(sum(r['ll'] for r in post)/len(post),4))
    print(fam,json.dumps(res),flush=True)
if __name__=='__main__':main()
