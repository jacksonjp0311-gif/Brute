"""Operator text -> (intent, args). A fixed grammar plus a few phrase aliases; no generative parsing."""
from __future__ import annotations
import re
ACTIONS=('a','b');CHANNELS=('x','y')
HELP='''commands:
  init x=0 y=1 [k=4] [attest=FAMILY]  initialize (k = max hidden states, 1..5;
                            attest = operator-declared scope, needed for public certificates)
  observe a x=1 y=-         feed an observation ('-' = masked)
  predict a [x|y]           ask for the next reading after action a (real predict call;
                            a CERTIFIED answer is recorded as issued and can later be retracted)
  why                       why the last prediction was (not) certified
  vs                        version space size (surviving explanations)
  retractions               what Brute withdrew and why
  scope                     declared family, attestation, residual alarm
  split [default=a]         which action Brute would test next (read-only `experiment` op, brute.api/1.2;
                            default = your planned action, used on a tie). UNSUPPORTED under --api 1.1
  models [default=a]        how many surviving rows admit each reading per action (counts, not identities)
  retry k=5                 replay evidence under a new state bound
  requests | decline qN     Brute's pending requests to you | say you cannot satisfy one
  raw tNNNN-...             print a stored trace;  help;  quit'''


def _obs(tokens):
    obs={}
    for t in tokens:
        m=re.fullmatch(r'([xy])=([01-])',t)
        if not m:raise ValueError(t)
        obs[m[1]]=None if m[2]=='-' else int(m[2])
    if set(obs)!=set(CHANNELS):raise ValueError('need x= and y=')
    return obs


def parse(line):
    s=line.strip().lower().rstrip('?');w=s.split()
    if not w:return None,{}
    try:
        if w[0] in ('init','initialize'):
            k=[int(t[2:]) for t in w[1:] if t.startswith('k=')];att=[t[7:] for t in w[1:] if t.startswith('attest=')]
            args={'obs':_obs([t for t in w[1:] if not t.startswith(('k=','attest='))])}
            if k:args['max_states']=k[0]
            if att:args['attestation']={'family':att[0],'issuer':'operator','basis':'declared by the operator via bridge'}
            return 'init',args
        if w[0]=='observe' and len(w)>=2 and w[1] in ACTIONS:return 'observe',{'action':w[1],'obs':_obs(w[2:])}
        if w[0]=='retry' and len(w)==2 and w[1].startswith('k='):return 'retry',{'max_states':int(w[1][2:])}
    except ValueError:return 'unknown',{}
    if w[0]=='predict' and len(w) in (2,3) and w[1] in ACTIONS and (len(w)==2 or w[2] in CHANNELS):
        return 'predict',{'action':w[1],**({'channel':w[2]} if len(w)==3 else {})}
    m=re.search(r'predict\b.*?\b(?:sensor |channel )?([xy])\b.*\bafter (?:action )?([ab])\b',s)
    if m:return 'predict',{'action':m[2],'channel':m[1]}
    m=re.search(r'predict\b.*\bafter (?:action )?([ab])\b',s)
    if m:return 'predict',{'action':m[1]}
    d=[t[8:] for t in w[1:] if t.startswith('default=')]
    if d and d[0] not in ACTIONS:return 'unknown',{}
    dk={'default_action':d[0]} if d else {}
    if re.search(r'\b(which|what) (surviving )?models\b',s) or w[0]=='models':return 'models',dk
    if w[0]=='why' or s.startswith('why '):return 'why',{}
    if w[0] in ('vs','version-space','version_space') or 'version space' in s:return 'version_space',{}
    if w[0]=='retractions' or 'retract' in s:return 'retractions',{}
    if w[0]=='scope' or 'scope' in s:return 'scope',{}
    if w[0]=='split' or 'best action' in s or 'which action' in s or 'split' in s:return 'split',dk
    return 'unknown',{}
