"""Brute v0.18.0 per-bit partial certificates (BRUTE_PLAN_020 perbit_block; docs/research/BRUTE_DEVIATIONS_020.md #103
item 5). New file, host-agnostic pure functions; no frozen module is changed and no API version is added.

perbit_decide(step, burn_in, support, width=2) -> [v_0, ..., v_{width-1}]: after burn-in, bit j (bit 0 = the high bit of
the code, as the reading order) is certified with value v iff the support is non-empty and every code in it has bit j
equal to v; otherwise None. SAT-UNKNOWN codes are part of the support (frozen semantics), so they can only block a bit.

Lemma (Exact, conditional, as brute.seqmargin): if the latent code is in the support, every certified bit equals the
latent bit. A full singleton certificate (rgn_decide) implies both bits.
"""
from __future__ import annotations

__all__=['code_bit','perbit_decide','perbit_trace']


def code_bit(code,j,width=2):
    if isinstance(code,bool) or not isinstance(code,int) or code<0 or code>=1<<width:raise ValueError('code out of range')
    if not 0<=j<width:raise ValueError('bit index out of range')
    return (code>>(width-1-j))&1


def perbit_decide(step,burn_in,support,width=2):
    if step<=burn_in or not support:return [None]*width
    out=[]
    for j in range(width):
        bs={code_bit(c,j,width) for c in support};out.append(bs.pop() if len(bs)==1 else None)
    return out


def perbit_trace(steps,truth,supports,burn_in,late=(45,88),width=2):
    """steps [(t, a)], truth[i][b] latent codes, supports[i][b]; per-step bits, wrong flags and counts (late window too)."""
    out={'trace':[]};n=f=nl=fl=0
    for i,(t,_a) in enumerate(steps):
        vals=[];wr=[]
        for b in range(len(supports[i])):
            row=perbit_decide(t,burn_in,supports[i][b],width)
            w=[row[j] is not None and row[j]!=code_bit(truth[i][b],j,width) for j in range(width)]
            vals.append(row);wr.append(w);k=sum(v is not None for v in row);x=sum(w);n+=k;f+=x
            if late[0]<=t<=late[1]:nl+=k;fl+=x
        out['trace'].append({'step':t,'bits':vals,'wrong':wr})
    out.update(certified_bits=n,false_bits=f,late_certified_bits=nl,late_false_bits=fl)
    return out
