"""The only bridge module that touches files: append-only JSONL for transcripts and flags."""
from __future__ import annotations
import json


def dumps(obj):return json.dumps(obj,sort_keys=True,separators=(',',':'))


class JsonlSink:
    def __init__(self,path=None):
        self.path=path;self.lines=[]
        if path:open(path,'w').close()

    def write(self,obj):
        line=dumps(obj);self.lines.append(line)
        if self.path:
            with open(self.path,'a') as f:f.write(line+'\n')


def read_jsonl(path):
    with open(path) as f:return [json.loads(l) for l in f if l.strip()]


def read_text(path):
    with open(path) as f:return f.read()
