"""GAPI14_compat fixture for study-046 (BRUTE_PLAN_046; new file). Records brute.api.certify14 outputs on small fixed traces
BEFORE brute/api/certify16.py exists in any commit, so the gate can check certify16(search=...) reproduces them byte for byte
(canonical JSON: sort_keys, default=str). Refuses overwrite.
  PYTHONPATH=. python scripts/make_certify14_sample_046.py results/diag-046/CERTIFY14_SAMPLE_046.json"""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common import write_new
D=((0,1),[0,1,0,1,1,0,0,1,1,1,0],[(0,1),(1,None),(0,1),(1,0),(None,1),(0,1),(1,0),(0,0),(1,1),(0,1),(1,None)])
D2=((1,0),[0,0,1,1,0,1,0,1,1,0,0,1],[(0,1),(1,1),(1,0),(0,0),(1,0),(0,1),(1,1),(1,0),(0,1),(1,0),(0,0),(1,1)])
CASES=[('D_s4_fb3',D,{'family_bound':3,'search':'s4'}),('D_s4_fb4',D,{'family_bound':4,'search':'s4'}),
       ('D2_s4_fb3',D2,{'family_bound':3,'search':'s4'}),('D_s3_fb3',D,{'family_bound':3,'search':'s3'}),('D_region',D,{})]


def canon(x):return json.dumps(x,sort_keys=True,default=str)


def sample():
    from brute.api.certify14 import certify14
    return [{'name':n,'args':[list(d[0]),d[1],[list(o) for o in d[2]]],'kwargs':kw,'output':canon(certify14(*d,**kw))} for n,d,kw in CASES]


if __name__=='__main__':
    out={'schema':'brute.certify14_sample.v43','cases':sample()};write_new(Path(sys.argv[1]),out)
    print(json.dumps([(c['name'],len(c['output'])) for c in out['cases']]))
