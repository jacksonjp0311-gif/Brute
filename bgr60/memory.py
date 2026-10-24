"""Append-only lab skill receipts; no external authority or credential grants.

A valid SHA chain detects accidental changes, not a privileged attacker who can
rewrite the chain. Independent validation attestation is lab-supplied. Templates
from skills are never allowed to certify an unobserved target transition.
"""
from __future__ import annotations
from pathlib import Path
from hashlib import sha256
import json,os
from .generalist import GeneralLearner,Template

class PromotionRefused(Exception):pass

def canonical(v):return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=True).encode()
def digest(v):return sha256(canonical(v)).hexdigest()

class SkillLedger:
    def __init__(self,path):self.path=Path(path)
    def entries(self):
        if not self.path.exists():return []
        rows=[];previous='0'*64
        for raw in self.path.read_text(encoding='utf8').splitlines():
            x=json.loads(raw);value={k:v for k,v in x.items() if k!='receipt_sha256'}
            if x['previous_sha256']!=previous or x['receipt_sha256']!=digest(value):
                raise PromotionRefused('skill receipt corruption')
            previous=x['receipt_sha256'];rows.append(x)
        return rows
    def promote(self,model:GeneralLearner,attestation:dict):
        if not model.identified():raise PromotionRefused('incomplete causal function')
        if attestation.get('verified') is not True or attestation.get('matches_model') is not True:
            raise PromotionRefused('independent lab reference validation required')
        if attestation.get('schema_fingerprint')!=model.schema.fingerprint():
            raise PromotionRefused('mismatched schema')
        if attestation.get('case_count')!=len(model._states)*len(model.actions):
            raise PromotionRefused('incomplete reference coverage')
        packet={'schema':model.schema.data(),'schema_fingerprint':model.schema.fingerprint(),
                'actions':list(model.actions),
                'complete_transitions':[{'action':i,'state':list(s),'next':list(model.certified(i,s))}
                                        for i in range(len(model.actions)) for s in model._states],
                'templates':[x.data() for x in model.extracted_templates()],
                'history_digest':digest(model.history),'scope':'verified_finite_lab_world_only'}
        packet['packet_digest']=digest(packet)
        previous=self.entries()[-1]['receipt_sha256'] if self.entries() else '0'*64
        item={'event':'promote','previous_sha256':previous,'packet':packet,
              'attestation_digest':digest(attestation)}
        item['receipt_sha256']=digest(item)
        self.path.parent.mkdir(parents=True,exist_ok=True)
        with self.path.open('a',encoding='utf8',newline='\n') as f:
            f.write(canonical(item).decode()+'\n');f.flush();os.fsync(f.fileno())
        return item['receipt_sha256']
    def quarantine(self,packet_digest:str,reason:str):
        previous=self.entries()[-1]['receipt_sha256'] if self.entries() else '0'*64
        item={'event':'quarantine','previous_sha256':previous,
              'packet_digest':packet_digest,'reason':str(reason)}
        item['receipt_sha256']=digest(item)
        with self.path.open('a',encoding='utf8',newline='\n') as f:
            f.write(canonical(item).decode()+'\n');f.flush();os.fsync(f.fileno())
    def active(self):
        ledger={}
        for item in self.entries():
            if item['event']=='promote':
                p=item['packet'];ledger[p['packet_digest']]=p
            elif item['event']=='quarantine':ledger.pop(item['packet_digest'],None)
        return tuple(ledger.values())
    def exact_context(self,schema,actions):
        return tuple(x for x in self.active()
                     if x['schema_fingerprint']==schema.fingerprint() and x['actions']==list(actions))
    def transfer_templates(self):
        # Useful hints; never authoritative in a different environment.
        templates=set()
        for packet in self.active():
            for raw in packet['templates']:
                temp=Template.read(raw);templates.add(temp)
        return tuple(sorted(templates,key=lambda x:(x.domain_profile,x.values)))


def lab_attestation(model:GeneralLearner,world):
    """Privileged evaluator, not part of the learner or production interface."""
    all_checked=0;match=True
    for ai in range(len(world.actions)):
        for state in world.schema.all_states():
            all_checked+=1
            if model.certified(ai,state)!=world.transition(ai,state):match=False
    return {'verified':bool(match and model.identified()),'matches_model':match,
            'schema_fingerprint':model.schema.fingerprint(),'case_count':all_checked,
            'type':'privileged_synthetic_lab_reference'}
