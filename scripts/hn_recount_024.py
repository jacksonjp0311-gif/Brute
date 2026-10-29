"""G_recount (study-024): (1) |H_n| and D_n exactly as study-023 (scripts/hn_recount_023.py, frozen, imported unchanged);
(2) the RGL5 epoch schedule of STITCHED_LEMMA_024 in exact integers / rationals: k(i), H_k = 28*2^k, B_k = 2*H_k,
delta_k = delta_a/((k+1)(k+2)) for the 88-step horizon (k = 0, 1, 2), the partial sums sum_{k<=K} delta_k = delta_a(1 - 1/(K+2)) < delta_a,
and agreement with brute.stitchedregion.epoch_of / epoch_delta.

  PYTHONPATH=. python scripts/hn_recount_024.py [--write results/diag-024/HN_RECOUNT_024.json]
"""
import json,sys
from fractions import Fraction as F
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts import hn_recount_023 as H
from brute.stitchedregion import epoch_of,epoch_delta
from experiments.brute_common import check

DA=F(5,1000)
PLAN_EPOCHS={0:{'steps':[1,28],'B':56,'delta':'1/400'},1:{'steps':[29,56],'B':112,'delta':'1/1200'},2:{'steps':[57,88],'B':224,'delta':'1/2400'}}


def k_exact(i):
    if i<=28:return 0
    k=0
    while i>28*2**k:k+=1
    return k


def main(argv=()):
    rep={'schema':'brute.hn-recount-024.v1','groups':{},'H':{},'D':{}}
    for n in (1,2,3,4):
        g=H.groups(n);h=1
        for x in g:h*=x
        rep['groups'][n]=g;rep['H'][n]=h;rep['D'][n]=H.D_exact(h)
    rep['plan_H']=H.PLAN_H;rep['plan_D']=H.PLAN_D
    hn_ok=rep['H']==H.PLAN_H and rep['D']==H.PLAN_D
    ep={}
    for i in range(1,89):
        k=k_exact(i);e=ep.setdefault(k,{'steps':[i,i],'B':2*28*2**k,'delta':str(DA/((k+1)*(k+2)))});e['steps'][1]=i
    rep['epochs']=ep;rep['plan_epochs']=PLAN_EPOCHS
    impl=[(i,epoch_of(i)) for i in range(1,89) if epoch_of(i)!=k_exact(i)]
    dimpl=[k for k in ep if F(epoch_delta(k)) != DA/((k+1)*(k+2))] if all(isinstance(epoch_delta(k),(F,int)) for k in ep) else \
          [k for k in ep if abs(float(epoch_delta(k))-float(DA/((k+1)*(k+2))))>0]
    psum={K:str(sum(DA/((k+1)*(k+2)) for k in range(K+1))) for K in range(0,12)}
    rep['partial_sums']=psum;rep['implementation_epoch_mismatch']=impl;rep['implementation_delta_mismatch']=dimpl
    sums_ok=all(F(v)==DA*(1-F(1,K+2)) and F(v)<DA for K,v in psum.items())
    rep['PASS']=hn_ok and {k:v for k,v in ep.items()}=={k:{'steps':v['steps'],'B':v['B'],'delta':v['delta']} for k,v in PLAN_EPOCHS.items()} \
        and not impl and not dimpl and sums_ok
    txt=json.dumps(rep,indent=1);print(txt);argv=list(argv)
    if '--write' in argv:
        p=ROOT/argv[argv.index('--write')+1];p.parent.mkdir(parents=True,exist_ok=True)
        with open(p,'x') as fh:fh.write(txt+'\n')
    check(rep['PASS'],'G_recount differs from the plan / lemma');return 0


if __name__=='__main__':sys.exit(main(sys.argv[1:]))
