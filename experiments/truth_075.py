"""Reader for experiments/truth_075.json (oracle truth of the 10 study-075 targets). Read only by the recount, gates and tests; the runner
and the certifiers never import it."""
import json
from pathlib import Path
from types import SimpleNamespace
_D=json.loads((Path(__file__).resolve().parent/'truth_075.json').read_text())
TARGETS=tuple(_D['targets'])
N_TRUE={k:v['n'] for k,v in _D['targets'].items()}


def world(name):
    t=_D['targets'][name]
    return SimpleNamespace(n=t['n'],k=len(t['bytes']),s=2,start=0,transitions=[list(r) for r in t['transitions']],emissions=list(t['emissions']),codec=t['codec'],bytes=tuple(t['bytes']))
