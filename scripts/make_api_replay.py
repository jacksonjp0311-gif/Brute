"""Replay recorded traces through the public surface brute.api (plan §4.4 target).

1. Every study-002 case (all 7 families): count CERTIFIED API responses whose value differs
   from the evaluator-only emission, and confirm the API agrees with the core evaluator.
2. Every study-001 v0.90 false conditional certification (140): record what the API returns
   at that step, and whether the following observe returns a retraction of it.
Deterministic: output depends only on the traces, the plan and the core source.
"""
from __future__ import annotations
import argparse,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from brute.api import BruteService,API_VERSION,DEFAULT_ALPHABET
from brute.api.service import CALIBRATED_TAU,SOURCE_SHA256
from experiments.brute_common import load,dumps,write_new,check,STUDY_DIR,sha,PLAN

OUT=STUDY_DIR/'API_REPLAY.json'


def obs(o):return {'x':o[0],'y':o[1]}
def code(v):return 2*v['x']+v['y']


def replay(case,attest,watch=()):
    svc=BruteService(tau=CALIBRATED_TAU)
    plan=load(PLAN)
    req={'api_version':API_VERSION,'session_id':'s','op':'initialize','observation':obs(case['initial_visible'])}
    if attest:req['attestation']={'family':plan['declared_family'],'issuer':'evaluator','basis':'synthetic world built inside the family'}
    r=svc.handle(req);check(r['status']=='ACKNOWLEDGED','initialize failed')
    out=[]
    for rec in case['trace']:
        a=DEFAULT_ALPHABET.actions[rec['action']]
        p=svc.handle({'api_version':API_VERSION,'session_id':'s','op':'predict','action':a,'public':bool(attest)})
        o=svc.handle({'api_version':API_VERSION,'session_id':'s','op':'observe','action':a,'observation':obs(rec['observed'])})
        check(p['status']!='ERROR' and o['status']!='ERROR','API error during replay')
        out.append((rec,p,o))
    return out


def build():
    s2=load(STUDY_DIR/'SCIENTIFIC.json');fam={}
    for case in s2['cases']:
        f=fam.setdefault(case['family'],{'certified':0,'certified_wrong':0,'public':0,'public_wrong':0,
                                         'retraction_responses':0,'disagreements_with_core_evaluator':0})
        for rec,p,o in replay(case,case['attested']):
            actual=rec['actual_emission_EVALUATOR_ONLY']
            core_key=rec['status'] if rec['reason'] is None else rec['status']+'/'+rec['reason']
            if rec['certificate'] is not None and case['attested'] and rec['public_certificate'] is None:
                core_key='ABSTAIN/UNATTESTED_SCOPE'
            api_key=p['status'] if p['reason'] is None else p['status']+'/'+p['reason']
            f['disagreements_with_core_evaluator']+=api_key!=core_key
            if p['status']=='CERTIFIED':
                v=code(p['certificate']['value']);f['certified']+=1;f['certified_wrong']+=v!=actual
                if p['certificate']['kind']=='public':f['public']+=1;f['public_wrong']+=v!=actual
            if o['retractions'] and o['status']=='OUT_OF_FAMILY' and o['reason']=='FAMILY_CONTRADICTED' and not p['status']=='OUT_OF_FAMILY':
                f['retraction_responses']+=1
    s1=load(ROOT/'results/study-001/SCIENTIFIC.json');outcome={};total=0
    for case in s1['cases']:
        steps={r['step'] for r in case['trace'] if r['expanded_wrong_certificate']}
        if not steps:continue
        for rec,p,o in replay(case,False):
            if rec['step'] not in steps:continue
            total+=1
            key=p['status'] if p['reason'] is None else p['status']+'/'+p['reason']
            if p['status']=='CERTIFIED':
                retracted=any(x['step']==rec['step'] for x in o['retractions'])
                key+='+RETRACTED_NEXT_OBSERVE' if retracted else '+NOT_RETRACTED'
            k=f"{case['family']}:{key}";outcome[k]=outcome.get(k,0)+1
    return {'schema':'brute.api-replay.v1','api_version':API_VERSION,'core_source_sha256':SOURCE_SHA256,
            'tau':CALIBRATED_TAU,'study002_scientific_sha256':sha(STUDY_DIR/'SCIENTIFIC.json'),
            'study001_scientific_sha256':sha(ROOT/'results/study-001/SCIENTIFIC.json'),
            'study002_by_family':fam,'study001_false_certifications_replayed':total,
            'study001_false_certification_outcomes':dict(sorted(outcome.items()))}


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--check',action='store_true');a=ap.parse_args()
    obj=build()
    if a.check:check(OUT.read_bytes()==dumps(obj),'API_REPLAY.json does not reproduce');print('API_REPLAY reproduces')
    else:write_new(OUT,obj);print(dumps(obj).decode())
