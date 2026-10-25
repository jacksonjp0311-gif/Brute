"""Study-004-style bridge corpus (BRIDGE_PLAN v0.2 addendum, B10-B12).

Per family, the first case at mask 0.35 in results/study-004/SCIENTIFIC.json.gz, arm A. At every step the
operator asks Brute which action to test (`split`, default = the study's passive action), takes the action Brute
names, asks for counts, both predictions, why, vs, scope and retractions, then feeds the recorded observation.
Hidden truth (the *_EVALUATOR_ONLY fields) is never sent to Brute.
"""
import gzip,json
from functools import lru_cache
from bridge.session import Bridge
from tests.bridge_corpus import ROOT
ATTEST={'family':'deterministic-moore<=4/stationary','issuer':'evaluator','basis':'synthetic world built inside the family'}
F=lambda v:None if v is None else int(v)


@lru_cache(maxsize=1)
def cases():
    cs=json.loads(gzip.open(ROOT/'results/study-004/SCIENTIFIC.json.gz').read())['cases'];out={}
    for c in cs:
        if c['mask_rate']==0.35:out.setdefault(c['family'],c)
    return out


def _obs(v):return {'x':F(v[0]),'y':F(v[1])}


def drive(c,experiments=True,extra=True):
    """Returns (bridge, mismatches). With experiments=False the recorded action is used and no experiment op is sent."""
    b=Bridge(source=f"replay:results/study-004 {c['family']} seed {c['seed']} arm A{'' if experiments else ' (no experiment calls)'}")
    b.ask('init',obs=_obs(c['initial_visible']),**({'attestation':ATTEST} if c['attested'] else {}))
    bad=[]
    for r in c['arms']['A']['trace']:
        pa='ab'[r['passive_action']];rec='ab'[r['action']]
        a=rec
        if experiments:
            ans,_=b.ask('split',command=f'split default={pa}',default_action=pa)
            e=b.traces[b.last]['response']['experiment'];a=e['action']
            got=(a,[s['score'] for s in e['scores']],e['tied']);want=(rec,r['experiment']['scores'],r['experiment']['tied'])
            if got!=want:bad.append({'step':r['step'],'what':'experiment','got':got,'recorded':want})
            if extra:b.ask('models',command=f'models default={pa}',default_action=pa)
        b.ask('predict',command=f'predict {a}',action=a)
        p=b.traces[b.last_predict]['response']
        if (p['status'],p['reason'])!=(r['status'],r['reason']):
            bad.append({'step':r['step'],'what':'predict','got':[p['status'],p['reason']],'recorded':[r['status'],r['reason']]})
        if extra:
            o='ba'['ab'.index(a)]
            b.ask('predict',command=f'predict {o} x',action=o,channel='x')
            for i in ('why','version_space','scope','retractions'):b.ask(i,command=i)
        if a!=rec:break  # the recorded observation belongs to the recorded action; stop rather than invent one
        b.ask('observe',command=f'observe {a}',action=a,obs=_obs(r['observed']))
    b.ask('retractions',command='retractions');b.ask('scope',command='scope')
    return b,bad


@lru_cache(maxsize=1)
def sessions():
    return {f:drive(c) for f,c in cases().items()}
