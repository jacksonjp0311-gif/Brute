"""Post-release verification: the incremental harness must still DETECT corrupted traces (it is not vacuous).
Corrupts one field per trial in a copy of a sealed breadth case (in memory only) and expects the frozen audit, run with
IncOracle(symmetry=True), to raise VerificationError."""
import copy,json,random,sys
from experiments import v060_xcheck as V
from experiments.v060_xcheck_incremental import IncOracle
from experiments.v050_reference import breadth_world
from experiments.brute_common import load,VerificationError
cases=V.load_cases(sys.argv[1]);plan=V.plan_view(load(V.PLAN));tau7=plan['tau7']['value'];rng=random.Random(2026);out=[]
breadth=[i for i,c in enumerate(cases) if 'k' in c]
for trial in range(24):
    i=rng.choice(breadth);c=copy.deepcopy(cases[i]);arm=rng.choice(V.ARMS_008);tr=c['arms'][arm]['trace'];st=rng.randrange(len(tr));b=rng.randrange(c['k'])
    f=tr[st]['forecasts'][b];kind=rng.choice(['support','certificate','saturated','margin_support'])
    m=2**c['s']
    if kind=='support':f['support']=sorted(set(f['support'] or [])^{rng.randrange(m)}) or None
    elif kind=='certificate':f['certificate']=(f['certificate']+1)%m if f['certificate'] is not None else 0
    elif kind=='saturated':f['saturated']=not f['saturated'] if f['saturated'] is not None else True
    else:f['margin_support']=sorted(set(f['margin_support'] or [])^{rng.randrange(m)}) or None
    w=breadth_world(c['seed'],c['family']);o=IncOracle(w.k,2**w.s,symmetry=True)
    try:V.audit(c,arm,plan,tau7,o);det=False;msg=None
    except (VerificationError,KeyError,IndexError,TypeError,ValueError,AssertionError) as e:det=True;msg=f'{type(e).__name__}: {e}'
    o.close();out.append({'case':i,'arm':arm,'step_index':st,'action':b,'field':kind,'detected':det,'error':msg});print(out[-1],flush=True)
json.dump({'schema':'brute.xcheck-incremental-tamper.v1','trials':len(out),'detected':sum(r['detected'] for r in out),'rows':out},open(sys.argv[2],'w'),indent=1)
