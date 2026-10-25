"""Offline transcript audit (standard library only; never imports brute).

Checks B1 (every claim grounded in its cited trace), B2 (UNSUPPORTED => 0 claims, 0 calls),
B4 (refusal_text verbatim), B5 (no single reading unless CERTIFIED / set / retraction),
B6 (recomputed triggers reproduce the logged requests exactly).
Usage: python -m bridge.audit TRANSCRIPT.jsonl
"""
from __future__ import annotations
import sys
from .claims import check_claim,READING,resolve,split_ref
from .triggers import Triggers
from .log import read_jsonl,dumps

SINGLE_OK=('cert','cert.channel','retraction','possible','prob','req.observation')


def audit(rows):
    v=[];traces={};trig=Triggers();n={'turns':0,'claims':0,'requests':0,'unsupported':0,'request_action':0}
    for row in rows:
        if row.get('type')!='turn':continue
        n['turns']+=1;a=row['answer'];new=row['trace_docs'];traces.update(new)
        if a['status']=='UNSUPPORTED':
            n['unsupported']+=1
            if a['claims'] or new:v.append(f"seq {a['seq']}: UNSUPPORTED with claims or API calls")
        for c in a['claims']+[c for q in row['requests'] for c in q['claims']]:
            n['claims']+=1
            for e in check_claim(c,traces):v.append(f"seq {a['seq']} {c.get('template')}: {e}")
            if READING.search(c['text']) and c['template'] not in SINGLE_OK:v.append(f"seq {a['seq']}: single reading in {c['template']}")
            if c['template'] in ('possible','prob') and len(READING.findall(c['text']))==1 and c['template']=='possible':
                st=resolve(traces[c['trace_id']],'/response/status')
                if st=='CERTIFIED':v.append(f"seq {a['seq']}: possible-set claim on CERTIFIED")
        for t in {split_ref(r)[0] for c in a['claims'] for r in c['field_refs']}:
            rt=traces[t]['response'].get('refusal_text')
            if rt is not None and rt not in [c['text'] for c in a['claims']]:v.append(f"seq {a['seq']}: refusal_text of {t} missing")
        recomputed=[q for t in new for q in trig.feed(t,traces)]
        if dumps(recomputed)!=dumps(row['requests']):v.append(f"seq {a['seq']}: requests do not match recomputed triggers")
        n['requests']+=len(row['requests']);n['request_action']+=sum(q['kind']=='REQUEST_ACTION' for q in row['requests'])
    return v,n


def main(argv=None):
    path=(argv or sys.argv[1:])[0];v,n=audit(read_jsonl(path))
    print(dumps({'violations':len(v),**n}));[print(' ',x) for x in v[:50]]
    sys.exit(1 if v else 0)


if __name__=='__main__':main()
