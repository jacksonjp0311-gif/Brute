import sys,probe,probe2
from probe2 import clone_update,certs_after
def lookp(L,a):
    if L.support.status!='supported' or L.margin.status!='supported' or L.alarm_step is not None:return 0.
    f=L.predict(a);sc=0.
    for c in (f.support or ()):
        sc+=f.probabilities[c]*certs_after(clone_update(L.support,a,1<<c),clone_update(L.margin,a,1<<c))
    return round(sc,12)
old=probe.choose
def choose(L,policy,pa):
    if policy=='LP':
        sc=[lookp(L,a) for a in (0,1)]
        return pa if sc[0]==sc[1] else (0 if sc[0]>sc[1] else 1)
    return old(L,policy,pa)
probe.choose=choose
if __name__=="__main__":probe2.main()
