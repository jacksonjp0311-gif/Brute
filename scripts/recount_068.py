"""Study 068 recount (BRUTE_PLAN_068 G_recount68): label every sealed record against the hand truth (experiments/truth_068) with
truth_label of study 058 (ID: behaviour equality from the truth start; IDF: from the truth state reached after the record's full
action sequence). Writes results/study-068/main/RECOUNT_068.json (refuses overwrite); --check recomputes and compares.
  PYTHONPATH=. python scripts/recount_068.py [--check]"""
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common import load,sha,check,write_new
from experiments.brute_study_058 import truth_label
from experiments import truth_068 as TR
D=ROOT/'results/study-068/main';OUT=D/'RECOUNT_068.json'


def reach(w,q):
    seen={q};st=[q]
    while st:
        p=st.pop()
        for r in w.transitions[p]:
            if r not in seen:seen.add(r);st.append(r)
    return sorted(seen)


def label(rec):
    if rec.get('killed'):return {'label':'KILL','q_now':None,'covered':[]}
    w=TR.world(rec['target']);q=w.start
    for a in rec['acts']:q=w.transitions[q][a]
    m=rec['model'];lab=truth_label(rec['stop'],None if m is None else (m[0],m[1]),rec['s1'],w,q)
    cov=reach(w,w.start) if lab=='ID' else reach(w,q) if lab=='IDF' else []
    return {'label':lab,'q_now':q,'covered':cov}


def compute():
    seal=load(D/'SEAL.json');check(sha(D/'RESULTS.json')==seal['results_sha256'],'RESULTS does not match its seal')
    R=load(D/'RESULTS.json');rows=[]
    for rec in R['records']:
        l=label(rec);rows.append({'key':f"{rec['target']}:{rec['seed']}:{rec['arm']}",'api_label':rec['api_label'],**l,
                                  'agree':l['label']==rec['api_label'] or (l['label']=='WRONG' and rec['api_label'] in ('ID','IDF'))})
    wrong=sum(r['label']=='WRONG' for r in rows)
    return {'study':R['study'],'results_sha256':seal['results_sha256'],'truth_sha256':sha(ROOT/'experiments/truth_068.py'),'rows':rows,
            'wrong':wrong,'labels_agree':all(r['agree'] for r in rows) and wrong==0,'complete':R['complete']}


if __name__=='__main__':
    r=compute()
    if '--check' in sys.argv:check(load(OUT)==r,'recount differs');print('recount --check ok')
    else:write_new(OUT,r);print('wrote',OUT)
    print({x['key']:x['label'] for x in r['rows']},'wrong',r['wrong'])
