import sys,json
from pathlib import Path
res=json.load(open(sys.argv[1]));DRIFT=(12,23,34);B=8
INF=['cycle3','switch3','unstructured3','unaliased2','ood4']
arms=list(res[0][3])
fams=sorted({r[1] for r in res},key=lambda f:(INF+['ood5','drift4']).index(f))
for tag in arms:
    print('==',tag)
    pooled=[]
    for f in fams:
        g=[r[3][tag] for r in res if r[1]==f]
        post=[s for t in g for s in t[B:]];al=[s for t in g for s in t]
        dual=sum((s[2] is not None)+(s[4] is not None) for s in post)/(2*len(post))
        fa=sum(s[2] is not None and s[2]!=s[3] for s in al);fcf=sum(s[4] is not None and s[4]!=s[5] for s in al)
        nd=sum((s[2] is not None and s[2]!=s[3])+(s[4] is not None and s[4]!=s[5]) for s in al if s[0] not in DRIFT)
        ndt=sum((s[2] is not None and s[2]!=s[3]) for s in al if s[0] not in DRIFT)
        cert=sum(s[2] is not None for s in al);cf=sum(s[4] is not None for s in al)
        ll=sum(s[6] for s in post)/len(post);chk=sum(s[7] for s in post)/len(post)
        alt=sum(t[i][1]!=t[i-1][1] for t in g for i in range(B,44))/len(post)
        rs=sum(s[8]=='RESYNC_AMBIGUOUS' for s in al)
        if f in INF:pooled.append(dual)
        print(f'{f:14s} dual {dual:.4f} cert {cert:5d} cf {cf:5d} false {fa:3d}/{fcf:3d} nondrift(t+cf) {nd:3d} nondrift_taken {ndt:3d} ll {ll:.5f} chk {chk:.3f} alt {alt:.3f} resync_abst {rs}')
    print('pooled in-family dual',round(sum(pooled)/len(pooled),6))
