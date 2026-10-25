"""Design probe for v0.3.0 on study-004 seeds (DESIGN DATA; not used for any v0.3.0 claim).
Arms are (certification resync on/off, check_run). Output: outputs/probe_<tag>.json."""
import sys,json,argparse
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from bgr89.worlds import world as old_world,actions
from bgr90.worlds import world as new_world,step as new_step
from brute.active import ActiveBruteLearner
from brute.changepoint import ChangePointBruteLearner
from brute.evaluation import loss
PLAN=json.load(open(ROOT/'experiments/BRUTE_PLAN_004.json'))
DRIFT=(12,23,34)

def make(resync,k,active):
    cls=type('L',(ChangePointBruteLearner,),{'resync':resync,'check_run':k})
    p=PLAN;return cls(p['family_state_cap'],p['margin_state_cap'],p['row_budget_family'],p['row_budget_margin'],
               p['prediction_smoothing'],p['open_world_reserve_epsilon'],p['residual_surprise']['window_W'],p['residual_surprise']['tau'],None)

def traj(seed,fam,mask,resync,k,active):
    truth=(new_world if fam in('ood5','drift4') else old_world)(seed,fam)
    h=truth.start;init=truth.observed(h,mask,-1);L=make(resync,k,active);L.initialize(init)
    out=[]
    for i,pa in enumerate(actions(seed,44)):
        e=L.experiment(pa) if active else None
        a=e['action'] if e else pa
        fs=(L.predict(0),L.predict(1))
        nxt=[new_step(truth,h,b,i) if fam=='drift4' else truth.next(h,b) for b in (0,1)]
        act=[truth.emission(x) for x in nxt];h=nxt[a];obs=truth.observed(h,mask,i)
        out.append((i+1,a,fs[a].certificate,act[a],fs[1-a].certificate,act[1-a],round(loss(fs[a].probabilities,act[a]),10),
                    bool(e and e.get('check')),fs[a].reason.value if fs[a].reason else None))
        L.observe(a,obs)
    return out

def job(x):
    seed,fam,mask,arms=x
    return seed,fam,mask,{tag:traj(seed,fam,mask,*spec) for tag,spec in arms.items()}

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--arms',required=True);ap.add_argument('--tag',required=True)
    ap.add_argument('--families',default=None);ap.add_argument('--workers',type=int,default=4);a=ap.parse_args()
    arms=json.loads(a.arms);fams=a.families.split(',') if a.families else list(PLAN['heldout_ranges'])
    jobs=[(s,f,m,arms) for f in fams for s in range(PLAN['heldout_ranges'][f][0],PLAN['heldout_ranges'][f][1]+1) for m in PLAN['mask_rates']]
    with ProcessPoolExecutor(a.workers) as ex:res=list(ex.map(job,jobs,chunksize=1))
    json.dump(res,open(Path(__file__).parent/f'outputs/probe_{a.tag}.json','w'))
    print('done',len(res))
