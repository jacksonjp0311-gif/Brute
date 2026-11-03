"""GS_ref65 audit for study-065 (BRUTE_PLAN_065 GS_ref65 and design.reference; new file, built from scripts/run_reference_064.py
(frozen): identical machinery with bound 20 for every arm, the 065 arms and mutations from random.Random(650). Noisy-arm records are
audited against the TRUE (clean) trace of the world, so any settled-bit error that changed the answer is caught here too. The frozen scripts/run_reference_047.py machinery (pool, budget,
mutation test, report) and the frozen scripts/run_reference_041.py audit() are imported unchanged; in this process and its forked
workers only:
  R47.W43 -> a shim over experiments/worlds_065 (= worlds_064 'scale20') (world(seed, family), actions); R47.view -> this view (family per arm, the record's
  final_clique carried as a hint); R47.ORDER = ('C20','S10','S20','S30','S30b'), KEYS = ('scale20',), DELTA all None (bound N
  = the case's declared N = 20);
  run_reference_041.M = 4 (read_bits 2) before each audit;
  run_reference_041._nmin and exists_different -> the clique-pinned experiments/v0610_reference.py versions (own apartness, own
  pairwise clique verification of the hint, else its own greedy clique through position 0; own CNF; CaDiCaL; no brute/ code).
Per decided record: n_min, consistency, s1, every stored future / start verdict, completeness at the declared N and the stop label;
K_spent is audited as AMB. 1800 s total budget, 6 workers; 20 seeded mutations (random.Random(650)). PASS iff 0 mismatches, every
decided record audited and 20/20 mutations detected (vacuous pass stated if 0 decided).
  PYTHONPATH=. python scripts/run_reference_065.py results/study-065/main --workers 6 --budget 1800"""
import sys,types
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments import worlds_064 as W64
from experiments import v0610_reference as PIN
from scripts import run_reference_047 as R47
from scripts import run_reference_041 as R41
ORDER=('C20','S10','S20','S30','S30b');KEYS=('scale20',);SEED=650;BUDGET_S=1800.0;WORKERS=6
_audit47=R47._audit;_auditR41=R41.audit
_CUR={'C':None,'src':None,'hint':None}


def view(c,arm):
    a=c['arms'][arm];stop='AMB' if a['stop']=='K_spent' else a['stop']
    return {'id':f"{c['block']}/{c['key']}/{c['seed']}/{arm}",'arm':arm,'key':c['key'],'seed':c['seed'],'family':a['family'],
            'extra_acts':list(a['extra_acts']),'stop':stop,'stop_recorded':a['stop'],'n_min':a['n_min'],'model':a['model'],'s1':a['s1'],
            'future':a['future'],'start':a['start'],'N':c['N'],'final_clique':list(a.get('final_clique') or [])}


def _clique(acts,codes):
    if _CUR['C'] is None:_CUR['C'],_CUR['src']=PIN.verified_clique(acts,codes,_CUR['hint'])
    return _CUR['C']


def _nmin(acts,codes,k,N):return PIN.nmin(acts,codes,k,R41.M,N,_clique(acts,codes))


def _exd(acts,codes,n,k,m,M1,s1,mode,L):return PIN.exists_different(acts,codes,n,k,m,M1,s1,mode,L,_clique(acts,codes))


def _setm(r):R41.M=1<<W64.BITS[r['family']]


def _audit(r):
    _setm(r);_CUR.update(C=None,src=None,hint=r.get('final_clique') or None);x,cache,wall=_audit47(r)
    x['clique_used']=len(_CUR['C'] or []);x['clique_source']=_CUR['src'];return x,cache,wall


def audit(r,w,acts,codes,cache):
    _setm(r)
    if _CUR['C'] is None or _CUR.get('rid')!=r['id']:_CUR.update(C=None,src=None,hint=r.get('final_clique') or None,rid=r['id'])
    return _auditR41(r,w,acts,codes,cache)


R47.W43=types.SimpleNamespace(world=W64.world,actions=W64.actions,SIZES=W64.SIZES)
R47.view=view;R47.ORDER=ORDER;R47.KEYS=KEYS;R47.DELTA={a:None for a in ORDER};R47.SEED=SEED;R47.BUDGET_S=BUDGET_S;R47.WORKERS=WORKERS
R47._audit=_audit;R47.audit=audit;R41._nmin=_nmin;R41.exists_different=_exd


def main(argv=None):
    argv=list(sys.argv[1:] if argv is None else argv)
    if '--output-name' not in argv:argv+=['--output-name','REFERENCE_065.json']
    if '--workers' not in argv:argv+=['--workers',str(WORKERS)]
    if '--budget' not in argv:argv+=['--budget',str(BUDGET_S)]
    return R47.main(argv)


if __name__=='__main__':sys.exit(main())
