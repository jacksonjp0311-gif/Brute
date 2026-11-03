"""Study 069 recount (BRUTE_PLAN_069 G_recount69): label every sealed record against the hand truth (experiments/truth_069).
ID -> ID if the record's hypothesis is Moore-equivalent to the truth from the start, else WRONG; EXCEEDS_N -> EXCEEDS_N if the truth
has more than the declared N states, else WRONG; QCAP -> QCAP; KILL -> KILL. Writes results/study-069/main/RECOUNT_069.json (refuses
overwrite); --check recomputes and compares.
  PYTHONPATH=. python scripts/recount_069.py [--check]"""
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common import load,sha,check,write_new
from experiments import truth_069 as TR
from brute.api.certify32r import equivalent
D=ROOT/'results/study-069/main';OUT=D/'RECOUNT_069.json'


def label(rec):
    if rec.get('killed'):return 'KILL'
    w=TR.world(rec['target']);a=rec['api_label']
    if a=='ID':return 'ID' if equivalent(rec['transitions'],rec['emissions'],w.transitions,w.emissions)[0] else 'WRONG'
    if a=='EXCEEDS_N':return 'EXCEEDS_N' if TR.N_TRUE[rec['target']]>rec['N'] else 'WRONG'
    if a=='QCAP':return 'QCAP'
    return 'UNKNOWN'


def compute(d=D):
    seal=load(d/'SEAL.json');check(sha(d/'RESULTS.json')==seal['results_sha256'],'RESULTS does not match its seal')
    R=load(d/'RESULTS.json');rows=[]
    for rec in R['records']:
        l=label(rec);rows.append({'key':f"{rec['target']}:{rec['seed']}:{rec['arm']}",'api_label':rec['api_label'],'label':l,'agree':l==rec['api_label']})
    wrong=sum(r['label']=='WRONG' for r in rows)
    return {'study':R['study'],'results_sha256':seal['results_sha256'],'truth_sha256':sha(ROOT/'experiments/truth_069.py'),'rows':rows,
            'wrong':wrong,'labels_agree':all(r['agree'] for r in rows) and wrong==0,'complete':R['complete']}


if __name__=='__main__':
    r=compute()
    if '--check' in sys.argv:check(load(OUT)==r,'recount differs');print('recount --check ok')
    else:write_new(OUT,r);print('wrote',OUT)
    print({x['key']:x['label'] for x in r['rows']},'wrong',r['wrong'])
