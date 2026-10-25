"""Claims: build, fill and check. Standard library only (the offline audit uses this module).

A claim is {text, template, label, params, field_refs, trace_id}; each field_ref is
'<trace_id>#<json pointer>' into a trace document {'request':..., 'response':...}.
"""
from __future__ import annotations
import json,re
from .templates import TEMPLATES

READING=re.compile(r'\bx=\d, y=\d\b')


def resolve(doc,pointer):
    cur=doc
    for part in pointer.split('/')[1:]:
        part=part.replace('~1','/').replace('~0','~')
        cur=cur[int(part)] if isinstance(cur,list) else cur[part]
    return cur


def _reading(v):return ', '.join(f'{k}={v[k]}' for k in v)
FORMATTERS={'plain':lambda v,p:json.dumps(v) if v is None or isinstance(v,bool) else str(v),
            'reading':lambda v,p:_reading(v),
            'set':lambda v,p:'; '.join('{'+_reading(x)+'}' for x in v),
            'len':lambda v,p:str(len(v)),
            'prob':lambda v,p:f'{v:.4f}',
            'proj':lambda v,p:', '.join(str(x) for x in sorted({e[p['ch']] for e in v}))}


def split_ref(ref):
    tid,_,ptr=ref.partition('#');return tid,ptr


def fill(tid,traces,refs,params=None):
    text,slots,_=TEMPLATES[tid];params=params or {}
    vals=[]
    for ref,(_,fmt,_n) in zip(refs,slots):
        t,ptr=split_ref(ref);vals.append(FORMATTERS[fmt](resolve(traces[t],ptr),params))
    return text.format(*vals,**params)


def pattern_ok(pattern,ptr,params):
    for k,v in (params or {}).items():pattern=pattern.replace('{'+k+'}',v)
    if '{i}' in pattern:
        pre,suf=pattern.split('{i}');mid=ptr[len(pre):len(ptr)-len(suf)] if len(ptr)>=len(pre)+len(suf) else ''
        return ptr.startswith(pre) and ptr.endswith(suf) and mid.isdigit()
    return ptr==pattern


def make(tid,traces,refs,params=None,trace_id=None):
    """Build a claim, or return None if any non-nullable ref is missing or null (never cite absence)."""
    _,slots,label=TEMPLATES[tid]
    for ref,(_,_f,nullable) in zip(refs,slots):
        t,ptr=split_ref(ref)
        try:v=resolve(traces[t],ptr)
        except (KeyError,IndexError,TypeError,ValueError):return None
        if v is None and not nullable:return None
    try:text=fill(tid,traces,refs,params)
    except (KeyError,TypeError,ValueError):return None
    return {'text':text,'template':tid,'label':label,'params':dict(params or {}),'field_refs':list(refs),
            'trace_id':trace_id or split_ref(refs[0])[0]}


def check_claim(c,traces):
    """List of violations for one claim against the stored traces."""
    out=[];tid=c.get('template')
    if tid not in TEMPLATES:return ['unknown template (unbacked sentence)']
    _,slots,label=TEMPLATES[tid];refs=c.get('field_refs') or []
    if c.get('label')!=label:out.append('label does not match template')
    if len(refs)!=len(slots):return out+['wrong number of refs']
    for ref,(pat,_f,nullable) in zip(refs,slots):
        t,ptr=split_ref(ref)
        if t not in traces:out.append(f'{ref}: unknown trace');continue
        if not pattern_ok(pat,ptr,c.get('params')):out.append(f'{ref}: not allowed by {tid}');continue
        try:v=resolve(traces[t],ptr)
        except (KeyError,IndexError,TypeError,ValueError):out.append(f'{ref}: does not resolve');continue
        if v is None and not nullable:out.append(f'{ref}: null')
    for k,v in (c.get('params') or {}).items():
        if k!='ch' or not isinstance(v,str):out.append(f'bad param {k}')
    if c.get('trace_id') not in {split_ref(r)[0] for r in refs}:out.append('trace_id is not one of the cited traces')
    if out:return out
    try:
        if fill(tid,traces,refs,c.get('params'))!=c.get('text'):out.append('text is not the template filled from its refs')
    except (KeyError,TypeError,ValueError) as e:out.append(f'fill failed: {e!r}')
    return out
