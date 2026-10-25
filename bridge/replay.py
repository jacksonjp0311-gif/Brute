"""B7: replay a transcript's API requests on a fresh service; responses must be byte-identical."""
from __future__ import annotations
import sys
from .log import read_jsonl,dumps


def replay(rows):
    from .session import make_service,API_VERSIONS
    h=next((r for r in rows if r.get('type')=='header'),{});api=next((k for k,v in API_VERSIONS.items() if v==h.get('api_version')),'1.1')
    svc=make_service(api);bad=[];n=0
    for row in rows:
        for tid,doc in (row.get('trace_docs') or {}).items():
            n+=1
            if dumps(svc.handle(doc['request']))!=dumps(doc['response']):bad.append(tid)
    return n,bad


if __name__=='__main__':
    n,bad=replay(read_jsonl(sys.argv[1]));print(dumps({'replayed':n,'mismatches':len(bad)}));sys.exit(1 if bad else 0)
