"""`python -m bridge` REPL / script runner over a live Bridge."""
from __future__ import annotations
import argparse,json,sys
from .parse import parse,HELP
from .session import Bridge


def show(ans,reqs,write):
    write(f"[{ans['status']}] {ans['intent']}  traces={','.join(ans['traces']) or '-'}")
    for c in ans['claims']:write(f"  - {c['text']}  [{c['label']}] <{c['trace_id']}>")
    if ans['note']:write(f"  (note: {ans['note']})")
    for q in reqs:
        for c in q['claims']:write(f"  >> {q['request_id']} {c['text']}  [{c['label']}] <{c['trace_id']}>")


def run(lines,bridge,write=print,echo=False):
    for line in lines:
        line=line.split('#',1)[0].strip() if not line.strip().startswith('raw') else line.strip()
        if not line:continue
        if echo:write(f'op> {line}')
        w=line.split()
        if w[0] in ('quit','exit'):break
        if w[0]=='help':write(HELP);continue
        if w[0]=='raw':write(json.dumps(bridge.traces.get(w[1] if len(w)>1 else ''),indent=1,sort_keys=True));continue
        if w[0]=='requests':
            for q in bridge.pending.values():write(f"  {q['request_id']} {q['claims'][0]['text']}")
            continue
        if w[0]=='decline' and len(w)==2:show(*bridge.decline(w[1],command=line),write);continue
        intent,args=parse(line);show(*bridge.ask(intent,command=line,**args),write)
        for x in bridge.last_resolved:write(f"  << {x['request_id']} {x['status']}"+(f" by <{x['observe_trace']}>" if x['observe_trace'] else ' (a newer request replaced it)'))


def main(argv=None):
    ap=argparse.ArgumentParser(prog='python -m bridge',description='Interrogate Brute (brute.api/1.2 by default); every claim cites a trace.')
    ap.add_argument('--script',help='file of operator commands');ap.add_argument('--transcript',default='bridge_transcript.jsonl')
    ap.add_argument('--flags',default='bridge/flags.jsonl');ap.add_argument('--api',choices=('1.1','1.2'),default='1.2');ap.add_argument('--source',default='operator')
    a=ap.parse_args(argv)
    b=Bridge(transcript=a.transcript,flags=a.flags,source=a.source,api=a.api)
    if a.script:
        from .log import read_text
        run(read_text(a.script).splitlines(),b,echo=True)
    else:
        print(f'Brute bridge ({b.api_version}). Type help.');
        def lines():
            while True:
                try:yield input('op> ')
                except EOFError:return
        run(lines(),b)
    print(f'transcript: {a.transcript}  flags: {a.flags}',file=sys.stderr)
