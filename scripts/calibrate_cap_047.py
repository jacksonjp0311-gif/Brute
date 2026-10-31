"""Cap calibration for study 047 (plan 047 design.cap_rule; smoke range 11570001-11570006 ONLY, never gated). New file.
Rule (plan): C = the median number of conflicts the frozen A16_N solver completes in 9.0 s on the smoke range, rounded down to a
multiple of the chunk size (scalesearch4.CHUNK0 = 2000); B = 240/9 x C.
Measurement (declared here before the run, restated in the pre-run deviation): each smoke case (scale16 x 4: 11570001-04,
control x 2: 11570005-06; the 046 smoke layout) is run once by the frozen brute.scalesearch16.active16 at the 046 settings
(query_s 9.0, case budget 240 s, K 128, g3, N = family size) in its own process with an in-process pysat g3 behind a logging
factory (no SolverServer: the conflict count of a child solver is not visible to the host; same solver build). The factory logs
every solve_limited chunk's conflicts (accum_stats delta) and wall. The case rate is its total conflicts / total solve wall. The
median is taken over the cases with at least 1.0 s of solve wall (trivial controls excluded; declared). C = floor(median rate x
9.0 / 2000) x 2000; B = floor(240 / 9 x C). Also reported, not used: per-case rates, and how many 9 s query caps fired.
  PYTHONPATH=. python scripts/calibrate_cap_047.py --write results/diag-047/CAP_CALIBRATION_047.json"""
import argparse,json,statistics,sys
from pathlib import Path
from time import perf_counter
from concurrent.futures import ProcessPoolExecutor
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from brute.region import codes_mask
from brute import scalesearch16 as S16
from brute.scalesearch4 import CHUNK0
from brute.api.certify16d import CCounted
from experiments import worlds_047 as W
from experiments.brute_study_033 import StepWorld,passive
from experiments.brute_common import check,write_new,dumps
from scripts.check_seeds_047 import check_run_seeds,SMOKE,FAMILY_OF

PLAN=ROOT/'experiments/BRUTE_PLAN_047.json'
CASES=(('scale16',SMOKE[0]),('scale16',SMOKE[0]+1),('scale16',SMOKE[0]+2),('scale16',SMOKE[0]+3),('control',SMOKE[0]+4),('control',SMOKE[0]+5))
CAP_S=9.0;BUDGET_S=240.0;MIN_WALL=1.0


class Logging(CCounted):
    log=None

    def solve_limited(self,assumptions=(),expect_interrupt=False):
        b=self.conflicts();t=perf_counter();r=CCounted.solve_limited(self,assumptions,expect_interrupt)
        Logging.log.append((self.conflicts()-b,perf_counter()-t));return r


def one(arg):
    key,seed=arg;from experiments.brute_common import load
    check_run_seeds('smoke',[seed],load(PLAN));fam=FAMILY_OF[key];w=W.world(seed,fam);sw=StepWorld(w);masks,acts,rd=passive(sw,seed)
    Logging.log=[];t0=perf_counter()
    res=S16.active16(masks,acts,w.k,1<<W.S_BITS,W.SIZES[fam],lambda a:codes_mask(sw.step(a),W.S_BITS),t0+BUDGET_S,S16.K14,CAP_S,'g3',None,Logging)
    lg=Logging.log;conf=sum(c for c,_ in lg);wall=sum(t for _,t in lg)
    return {'key':key,'seed':seed,'stop':res['stop'],'chunks':len(lg),'conflicts':conf,'solve_wall':wall,
            'rate':conf/wall if wall>0 else None,'capped_queries':sum(r['capped'] for r in res['rounds']),'case_wall':perf_counter()-t0}


def main(out=None):
    with ProcessPoolExecutor(len(CASES)) as ex:rows=list(ex.map(one,CASES))
    used=[r['rate'] for r in rows if r['solve_wall']>=MIN_WALL];check(used,'no smoke case with >= 1 s solve wall')
    med=statistics.median(used);C=int(med*CAP_S//CHUNK0)*CHUNK0;B=int(BUDGET_S/CAP_S*C)
    rep={'schema':'brute.capcal.v44','rule':'C = floor(median smoke conflict rate x 9.0 / 2000) x 2000; B = floor(240/9 x C)',
         'smoke_cases':rows,'rates_used':used,'median_rate_conflicts_per_s':med,'conflict_cap':C,'budget_conflicts':B,
         'chunk':CHUNK0,'min_solve_wall_s':MIN_WALL,'label':'Observed (smoke range only; never gated)'}
    print(json.dumps(rep,indent=1))
    if out:write_new(Path(out),rep)
    return rep


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--write');a=ap.parse_args();main(a.write)
