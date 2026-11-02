"""GS_ref audit for study-059 (BRUTE_PLAN_059 GS_ref; pre-run deviation #192; new file). The frozen scripts/run_reference_047.py
machinery (pool, budget, mutation test, report) and the frozen scripts/run_reference_041.py audit() (experiments/v0300_reference.py
and v0310_reference.py: plain CNF, CaDiCaL, no shared code with brute/) are imported unchanged; in this process and its forked
workers only:
  R47.W43 -> a shim over experiments/worlds_058 (world(seed, family), actions); R47.view -> this view;
  R47.trace -> the trace the certifier SAW: actions = worlds_026 prefix + recorded extra actions, codes = the recorded majority masks
            (mask.bit_length() - 1; for C4 these are the clean codes, which recount_059 checks independently); the reference label
            (ID / WRONG) is still taken against the CLEAN world;
  R47.ORDER = ('C4','N4_05','N4_10','N4_10b','NEG4'), KEYS = ('scale20n',), DELTA all None (bound N = 20 in every arm), M = 16;
  R47.bucket -> as frozen, except that in NEG4 (noise model violated, not gated) a ['stop', X, 'WRONG'] mismatch is reported as a
            misfire instead of a counted mismatch (a wrong majority trace can make the decision wrong; the gate GS59_sound covers
            only the gated arms).
Records with stop 'none' (NOFIT: no machine of <= 20 states fits the majority trace) are reported as not decided (no model to audit);
K_spent is audited as AMB. 1800 s total budget, 8 workers; 20 seeded mutations (random.Random(590)). PASS iff 0 counted mismatches,
every decided record audited and 20/20 mutations detected (vacuous pass stated if 0 decided).
  PYTHONPATH=. python scripts/run_reference_059.py results/study-059/main [--workers 8] [--budget 1800]"""
import sys,types
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments import worlds_058 as W58
from scripts import run_reference_047 as R47
from scripts import run_reference_041 as R41
ORDER=('C4','N4_05','N4_10','N4_10b','NEG4');KEYS=('scale20n',);SEED=590;BUDGET_S=1800.0
_bucket47=R47.bucket


def view(c,arm):
    a=c['arms'][arm];stop={'K_spent':'AMB','none':'unknown'}.get(a['stop'],a['stop'])
    return {'id':f"{c['block']}/{c['key']}/{c['seed']}/{arm}",'arm':arm,'key':c['key'],'seed':c['seed'],'family':a['family'],
            'extra_acts':list(a['extra_acts']),'stop':stop,'stop_recorded':a['stop'],'n_min':a['n_min'],'model':a['model'],'s1':a['s1'],
            'future':a['future'],'start':a['start'],'N':c['N'],'masks':list(a['prefix_masks'])+list(a['extra_masks'])}


def trace(r):
    w=W58.world(r['seed'],r['family']);acts=list(W58.actions(r['seed'],0.0,w.k))+r['extra_acts']
    codes=[m.bit_length()-1 for m in r['masks']]
    if len(codes)!=len(acts)+1:raise ValueError('mask count differs from the trace length: '+r['id'])
    return w,acts,codes


def bucket(r,x):
    if r['arm']!='NEG4':return _bucket47(r,x)
    mis=[];fire=[]
    for m in x['mismatches']:(fire if m[0]=='stop' and m[-1]=='WRONG' else mis).append(m)
    return mis,fire


R41.M=16
R47.W43=types.SimpleNamespace(world=W58.world,actions=W58.actions,SIZES=W58.SIZES)
R47.view=view;R47.trace=trace;R47.bucket=bucket;R47.ORDER=ORDER;R47.KEYS=KEYS;R47.DELTA={a:None for a in ORDER};R47.SEED=SEED;R47.BUDGET_S=BUDGET_S


def main(argv=None):
    argv=list(sys.argv[1:] if argv is None else argv)
    if '--output-name' not in argv:argv+=['--output-name','REFERENCE_059.json']
    return R47.main(argv)


if __name__=='__main__':sys.exit(main())
