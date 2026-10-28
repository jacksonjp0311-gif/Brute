"""GLR_lemma recount (study-023): |H_n| from the one-hot groups of the frozen brute.region.RegionK(n, 2, 4) encoding
(start state x[0], transition groups d[q][a], emission groups e[q]) and D_n in exact integers; compared with the plan.

  PYTHONPATH=. python scripts/hn_recount_023.py [--write results/diag-023/HN_RECOUNT_023.json]
"""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from brute.region import RegionK
from experiments.brute_common import check

PLAN_H={1:4,2:512,3:139968,4:67108864};PLAN_D={1:3,2:4,3:5,4:7}


def groups(n):
    R=RegionK(n,2,4,[15],[],conf_budget=None)
    try:
        g=[len(R.x[0])]+[len(R.d[q][a]) for q in range(n) for a in range(2)]+[len(R.e[q]) for q in range(n)]
    finally:R.close()
    return g


def D_exact(h,dl_num=5,dl_den=1000):
    """least D with 49^D >= 4 h / delta_L, delta_L = dl_num/dl_den (integers only)."""
    D=0
    while 49**D*dl_num<4*h*dl_den:D+=1
    return D


def main(argv=()):
    rep={'schema':'brute.hn-recount-023.v1','groups':{},'H':{},'D':{}}
    for n in (1,2,3,4):
        g=groups(n);h=1
        for x in g:h*=x
        rep['groups'][n]=g;rep['H'][n]=h;rep['D'][n]=D_exact(h)
    rep['plan_H']=PLAN_H;rep['plan_D']=PLAN_D
    rep['PASS']=rep['H']==PLAN_H and rep['D']==PLAN_D and sum(__import__('fractions').Fraction(rep['H'][n],4*rep['H'][n]) for n in rep['H'])==1
    txt=json.dumps(rep,indent=1);print(txt);argv=list(argv)
    if '--write' in argv:
        p=ROOT/argv[argv.index('--write')+1];p.parent.mkdir(parents=True,exist_ok=True)
        with open(p,'x') as fh:fh.write(txt+'\n')
    check(rep['PASS'],'H_n / D_n recount differs from the plan');return 0


if __name__=='__main__':sys.exit(main(sys.argv[1:]))
