"""Summarize design-probe outputs: pooled in-family dual coverage, drift4 false/stale certificates (taken+cf)."""
import sys,json
from pathlib import Path
INF=('cycle3','switch3','unstructured3','unaliased2','ood4')
res=[]
for f in sys.argv[1:]:res+=json.load(open(f))
arms=sorted(res[0][3])
for arm in arms:
    num=den=0;fam={}
    dr={'false':0,'nondrift':0,'stale':0,'certs':0};o5=0
    for seed,f,m,A in res:
        tr=A[arm]
        if f in INF:
            post=tr[8:];k=sum((r[2] is not None)+(r[4] is not None) for r in post)
            num+=k;den+=2*len(post);x=fam.setdefault(f,[0,0]);x[0]+=k;x[1]+=2*len(post)
        if f=='drift4':
            for r in tr:
                for c,act in ((r[2],r[3]),(r[4],r[5])):
                    if c is None:continue
                    dr['certs']+=1
                    if c!=act:
                        dr['false']+=1;dr['nondrift']+=r[0] not in (12,23,34);dr['stale']+=r[0]>12 and r[0] not in (12,23,34)
        if f=='ood5':o5+=sum((r[2] is not None and r[2]!=r[3])+(r[4] is not None and r[4]!=r[5]) for r in tr)
        if f in INF:
            assert all(r[2] is None or r[2]==r[3] for r in tr) and all(r[4] is None or r[4]==r[5] for r in tr),('in-family false',arm,seed,f,m)
    print(arm,'dual',round(num/den,4),{k:round(v[0]/v[1],3) for k,v in fam.items()},'drift4',dr,'ood5_false',o5)
print('--- taken-only drift4 non-drift false (G3prime), list')
for arm in arms:
    lst=[(seed,m,r[0]) for seed,f,m,A in res if f=='drift4' for r in A[arm] if r[2] is not None and r[2]!=r[3] and r[0] not in (12,23,34)]
    tot=sum(1 for seed,f,m,A in res if f=='drift4' for r in A[arm] if r[2] is not None and r[2]!=r[3])
    print(arm,'taken nondrift',len(lst),'taken total',tot,lst[:8])
