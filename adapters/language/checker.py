"""check(response, claims) -> list of violations. Empty list means every sentence is grounded."""
from __future__ import annotations
from .templates import TEMPLATES
from .render import resolve,fill


def check(response:dict,claims:list)->list:
    out=[]
    for n,c in enumerate(claims):
        if not isinstance(c,dict) or not isinstance(c.get('text'),str):out.append(f'claim {n}: not a claim');continue
        refs=c.get('field_refs');tid=c.get('template')
        if not refs:out.append(f'claim {n}: no field_refs');continue
        if tid not in TEMPLATES:out.append(f'claim {n}: no template, sentence is unbacked');continue
        _,slots,when,role=TEMPLATES[tid]
        if len(refs)!=len(slots):out.append(f'claim {n}: wrong number of refs');continue
        ok=True
        for p,(pattern,_) in zip(refs,slots):
            if '{i}' in pattern:
                prefix,suffix=pattern.split('{i}')
                good=p.startswith(prefix) and p.endswith(suffix) and p[len(prefix):len(p)-len(suffix)].isdigit()
            else:good=p==pattern
            if not good:out.append(f'claim {n}: ref {p} not allowed by template {tid}');ok=False;continue
            try:v=resolve(response,p)
            except (KeyError,IndexError,TypeError,ValueError):out.append(f'claim {n}: ref {p} does not resolve');ok=False;continue
            if v is None:out.append(f'claim {n}: ref {p} is null');ok=False
        if not ok:continue
        if not when(response):out.append(f'claim {n}: template {tid} does not apply to status {response["status"]}/{response["reason"]}');continue
        if fill(tid,response,refs)!=c['text']:out.append(f'claim {n}: text is not the template filled from its refs')
    if response.get('refusal_text') is not None and not any(isinstance(c,dict) and c.get('text')==response['refusal_text'] for c in claims):
        out.append('refusal_text missing or altered')
    return out
