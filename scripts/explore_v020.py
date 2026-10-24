"""EXPLORATORY (post hoc, not pre-registered, not a gate): what the n<=5 margin learner knew on study-002 steps
where the n<=4 family was contradicted and Brute fell back to uniform. Input: sealed SCIENTIFIC.json only.
Writes results/study-002/EXPLORATORY_V020.json (build / --check)."""
import argparse,math,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common import STUDY_DIR,load,dumps,write_new,check,sha
OUT=STUDY_DIR/'EXPLORATORY_V020.json'


def build():
    sci=load(STUDY_DIR/'SCIENTIFIC.json');eps=sci['plan']['open_world_reserve_epsilon'];out={}
    for fam in ('ood5','drift4'):
        r={'steps':0,'margin_supported':0,'margin_contradicted':0,'margin_support_contains_actual':0,
           'margin_singletons':0,'margin_singletons_correct':0};ll={'brute':0.0,'margin_eps_reserve':0.0,'suffix1':0.0,'suffix2':0.0}
        for c in sci['cases']:
            if c['family']!=fam:continue
            for t in c['trace']:
                if t['step']<c['burn_in'] or t['reason']!='FAMILY_CONTRADICTED':continue
                r['steps']+=1;a=t['actual_emission_EVALUATOR_ONLY'];s=t['margin_support']
                r['margin_supported' if t['margin_status_after']=='supported' else 'margin_contradicted']+=1
                ll['brute']+=t['logloss_brute'];ll['suffix1']+=t['logloss_suffix']['1'];ll['suffix2']+=t['logloss_suffix']['2']
                if s:
                    r['margin_support_contains_actual']+=a in s
                    if len(s)==1:r['margin_singletons']+=1;r['margin_singletons_correct']+=s[0]==a
                    ll['margin_eps_reserve']+=-math.log((1-eps)/len(s)*(a in s)+eps/4)
                else:ll['margin_eps_reserve']+=math.log(4)
        r['mean_logloss']={k:round(v/r['steps'],6) for k,v in ll.items()};out[fam]=r
    return {'schema':'brute.exploratory.v1','label':'EXPLORATORY post-hoc analysis; not pre-registered; not a criterion',
            'scientific_sha256':sha(STUDY_DIR/'SCIENTIFIC.json'),
            'question':'On post-burn-in steps where the n<=4 family is contradicted, would the n<=5 margin support have predicted well?',
            'margin_eps_reserve':'uniform over margin support with mass 1-eps plus eps/4 on every code (eps from plan)',
            'families':out}


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--check',action='store_true');a=ap.parse_args();obj=build()
    if a.check:check(OUT.read_bytes()==dumps(obj),'EXPLORATORY_V020.json does not reproduce');print('reproduces')
    else:write_new(OUT,obj);print(dumps(obj).decode())
