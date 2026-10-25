import sys,probe,probe3,probe5
from probe2 import clone_update,certs_after
def lu(L,a):
    if L.support.status!='supported' or L.margin.status!='supported' or L.alarm_step is not None:return 0.
    s=L.support.predict_support(a);sc=0.
    for c in s:sc+=certs_after(clone_update(L.support,a,1<<c),clone_update(L.margin,a,1<<c))
    return round(sc/len(s),12)
old=probe.choose
def choose(L,policy,pa):
    if policy=='LU':
        sc=[lu(L,a) for a in (0,1)]
        return pa if sc[0]==sc[1] else (0 if sc[0]>sc[1] else 1)
    return old(L,policy,pa)
probe.choose=choose
probe5._main()
