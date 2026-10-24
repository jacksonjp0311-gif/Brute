"""render(response) -> list of Claim dicts {text, field_refs, template}. Templates only; no free text."""
from __future__ import annotations
from .templates import TEMPLATES,ORDER,FORMATTERS


def resolve(doc,pointer):
    """RFC 6901 JSON pointer. Raises KeyError/IndexError when it does not resolve."""
    cur=doc
    for part in pointer.split('/')[1:]:
        part=part.replace('~1','/').replace('~0','~')
        cur=cur[int(part)] if isinstance(cur,list) else cur[part]
    return cur


def fill(template_id,response,refs):
    text,slots,_,_=TEMPLATES[template_id]
    values=[FORMATTERS[f](resolve(response,p)) for p,(_,f) in zip(refs,slots)]
    return text.format(*values)


def _instances(template_id,response):
    _,slots,_,_=TEMPLATES[template_id]
    if any('{i}' in p for p,_ in slots):
        return [[p.replace('{i}',str(i)) for p,_ in slots] for i in range(len(response['retractions']))]
    return [[p for p,_ in slots]]


def render(response:dict)->list:
    claims=[]
    for tid in ORDER:
        when=TEMPLATES[tid][2]
        if not when(response):continue
        for refs in _instances(tid,response):
            if any(resolve(response,p) is None for p in refs):continue  # never cite a null field
            claims.append({'text':fill(tid,response,refs),'field_refs':refs,'template':tid})
    return claims


def render_text(response:dict)->str:
    return ' '.join(c['text'] for c in render(response))
