"""G_recount (study-025): (1) |H_n| and D_n exactly as study-023 (scripts/hn_recount_023.py, frozen, imported unchanged);
(2) the RGB6 level schedule of BETTING_LEMMA_025 in exact integers / rationals: p_j, delta_Lj, delta_cj, D^j_n
(least D with ((1-p)/p)^D >= 4|H_n|/delta_L), the delta split 1/400 + 1/400 + 2(1/800 + 1/800) = 1/100, the Exact
non-activation bound (1/(1-p_j))^178 < 800 and the least bit counts that could reach 800 (666 / 1334), and agreement
with brute.bettingregion.levels().

  PYTHONPATH=. python scripts/hn_recount_025.py [--write results/diag-025/HN_RECOUNT_025.json]
"""
import json,sys
from fractions import Fraction as F
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts import hn_recount_023 as H
from brute.bettingregion import levels as impl_levels
from experiments.brute_common import check

PLAN_LEVELS={0:{'p':'1/50','delta_L':'1/400','delta_c':None,'D':[3,4,5,7]},1:{'p':'1/100','delta_L':'1/800','delta_c':'1/800','D':[3,4,5,6]},
             2:{'p':'1/200','delta_L':'1/800','delta_c':'1/800','D':[2,3,4,5]}}
DA0=F(1,400);THRESH=800;MAXBITS=178


def D_exact(p,dL,h):
    r=(1-p)/p;D=0
    while r**D<4*h/dL:D+=1
    return D


def main(argv=()):
    rep={'schema':'brute.hn-recount-025.v1','groups':{},'H':{},'D':{}}
    for n in (1,2,3,4):
        g=H.groups(n);h=1
        for x in g:h*=x
        rep['groups'][n]=g;rep['H'][n]=h;rep['D'][n]=H.D_exact(h)
    rep['plan_H']=H.PLAN_H;rep['plan_D']=H.PLAN_D
    hn_ok=rep['H']==H.PLAN_H and rep['D']==H.PLAN_D
    lv={}
    for j,v in PLAN_LEVELS.items():
        p=F(v['p']);dL=F(v['delta_L']);lv[j]={'p':v['p'],'delta_L':v['delta_L'],'delta_c':v['delta_c'],'D':[D_exact(p,dL,rep['H'][n]) for n in (1,2,3,4)]}
        if v['delta_c'] is not None:
            b=0
            while (1/(1-p))**b<THRESH:b+=1
            lv[j]['K_upper_at_178']=float(round((1/(1-p))**MAXBITS,4));lv[j]['least_bits_to_reach_800']=b
            lv[j]['cannot_activate_within_178_bits']=(1/(1-p))**MAXBITS<THRESH
    rep['levels']=lv;rep['plan_levels']=PLAN_LEVELS
    split=DA0+sum(F(v['delta_L'])+(F(v['delta_c']) if v['delta_c'] else 0) for v in PLAN_LEVELS.values())
    rep['delta_split']=str(split)
    impl={l['j']:{'p':l['p'],'delta_L':l['delta_L'],'delta_c':l['delta_c'],'D':list(l['D'])} for l in impl_levels()}
    rep['implementation_mismatch']=[j for j in PLAN_LEVELS if impl.get(j)!={k:lv[j][k] for k in ('p','delta_L','delta_c','D')}]
    rep['PASS']=(hn_ok and split==F(1,100) and all({k:lv[j][k] for k in ('p','delta_L','delta_c','D')}==PLAN_LEVELS[j] for j in PLAN_LEVELS)
                 and not rep['implementation_mismatch'] and all(lv[j]['cannot_activate_within_178_bits'] for j in (1,2))
                 and lv[1]['least_bits_to_reach_800']==666 and lv[2]['least_bits_to_reach_800']==1334)
    txt=json.dumps(rep,indent=1);print(txt);argv=list(argv)
    if '--write' in argv:
        p=ROOT/argv[argv.index('--write')+1];p.parent.mkdir(parents=True,exist_ok=True)
        with open(p,'x') as fh:fh.write(txt+'\n')
    check(rep['PASS'],'G_recount differs from the plan / lemma');return 0


if __name__=='__main__':sys.exit(main(sys.argv[1:]))
