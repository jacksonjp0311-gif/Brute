"""Shared corpus for bridge tests: study-002 replays (mask 0.35, one case per family) with every
intent asked at every step, plus edge sessions. Returns transcript rows (in memory)."""
import json
from functools import lru_cache
from pathlib import Path
from bridge.session import Bridge
from bridge.parse import parse
ROOT=Path(__file__).resolve().parents[1]
ATTEST={'family':'deterministic-moore<=4/stationary','issuer':'operator-test','basis':'bridge corpus'}


def cases():
    cs=json.loads((ROOT/'results/study-002/SCIENTIFIC.json').read_text())['cases'];out={}
    for c in cs:
        if c['mask_rate']==0.35:out.setdefault(c['family'],c)
    return out


def commands(c):
    x,y=c['initial_visible'];f=lambda v:'-' if v is None else str(v)
    yield f'init x={f(x)} y={f(y)}'
    for r in c['trace']:
        a='ab'[r['action']]
        for q in (f'predict {a}',f'predict {"ba"[r["action"]]} x','why','vs','scope','retractions','split','which models disagree?','hello there'):yield q
        yield f'observe {a} x={f(r["observed"][0])} y={f(r["observed"][1])}'
    yield 'vs'


def drive(b,lines):
    for l in lines:
        intent,args=parse(l);b.ask(intent,command=l,**args)
    return b


@lru_cache(maxsize=1)
def sessions():
    out={}
    for fam,c in cases().items():
        b=Bridge(source=f'replay:results/study-002 {fam} seed {c["seed"]}')
        out[fam]=drive(b,commands(c))
    # attested session that certifies, then is contradicted: attestation withdrawal + contradiction + retractions
    b=Bridge(source='edge:attested alternating world, then a contradicting reading')
    b.ask('init',obs={'x':0,'y':0},attestation=ATTEST)
    for i in range(20):b.ask('predict',action='a');b.ask('observe',action='a',obs={'x':i%2,'y':0})
    b.ask('predict',action='a');b.ask('observe',action='a',obs={'x':1,'y':1})
    b.ask('retractions');b.ask('scope');b.ask('why');out['edge_attested_contradiction']=b
    # residual alarm path (tau=-1)
    from brute.api.service_v011 import BruteServiceV011
    b=Bridge(service=BruteServiceV011(tau=-1.0),source='edge:tau=-1')
    drive(b,['init x=0 y=0']+['predict a','observe a x=0 y=0']*10+['scope','why']);out['edge_residual']=b
    b=Bridge(source='edge:k=1');drive(b,['init x=0 y=0 k=1']+['predict a','why','observe a x=0 y=0']*8);out['edge_k1']=b
    b=Bridge(source='edge:retry');drive(b,['init x=0 y=1']+['predict b','observe b x=1 y=-']*6+['retry k=5','vs','scope']);out['edge_retry']=b
    b=Bridge(source='edge:uninitialized');drive(b,['vs','predict a','why','scope','retractions']);out['edge_uninit']=b
    return out


def rows(b):return [json.loads(l) for l in b.transcript.lines]
