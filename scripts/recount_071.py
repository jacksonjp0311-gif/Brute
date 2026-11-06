"""Study 071 recount (BRUTE_PLAN_071 G_recount71): label every sealed record against the hand truth (experiments/truth_069, unchanged).
The truth is simulated from its start over the record's full reset-free action sequence; its readings must equal the recorded ones
(else TRACE_MISMATCH, counted wrong). certify/32x IDF (arm H) -> IDF iff the hypothesis from q_star is Moore-equivalent to the truth
from its final state, else WRONG. certify/32h and baseline/32t records are labelled with scripts/recount_070.label (unchanged rules).
Writes <dir>/RECOUNT_071.json (refuses overwrite); --check compares.
  PYTHONPATH=. python scripts/recount_071.py [--check] [--dir results/study-071/main]"""
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common import load,sha,check,write_new
from scripts.recount_070 import truth_run,label as label070
from brute.api.certify32r import equivalent
D=ROOT/'results/study-071/main'


def label(rec):
    if rec.get('killed'):return 'KILL',None
    if rec['api']!='brute.certify/32x':return label070(rec)
    w,acts,reads,states,ok=truth_run(rec)
    if not ok:return 'TRACE_MISMATCH',None
    a=rec['api_label'];x=rec['x']
    if a!='IDF':return a,None
    if x.get('assumes_resync') is not False:return 'WRONG','resync'
    return ('IDF',None) if equivalent(x['hyp_T'],x['hyp_E'],w.transitions,w.emissions,x['q_star'],states[-1])[0] else ('WRONG','future')


def compute(d=D):
    d=Path(d);seal=load(d/'SEAL.json');check(sha(d/'RESULTS.json')==seal['results_sha256'],'RESULTS does not match its seal')
    R=load(d/'RESULTS.json');rows=[]
    for rec in R['records']:
        l,why=label(rec)
        rows.append({'key':f"{rec['target']}:{rec['seed']}:{rec['arm']}",'arm':rec['arm'],'target':rec['target'],'N':rec['N'],
                     'api_label':rec['api_label'],'label':l,'why':why,'agree':l==rec['api_label'],'steps':rec.get('decoder_calls'),
                     't_steps':rec.get('t_steps'),'kill_reason':rec.get('kill_reason')})
    wrong=sum(r['label'] in ('WRONG','TRACE_MISMATCH') for r in rows)
    return {'study':R['study'],'results_sha256':seal['results_sha256'],'truth_sha256':sha(ROOT/'experiments/truth_069.py'),'rows':rows,
            'wrong':wrong,'labels_agree':all(r['agree'] for r in rows) and wrong==0,'complete':R['complete']}


if __name__=='__main__':
    d=Path(sys.argv[sys.argv.index('--dir')+1]) if '--dir' in sys.argv else D;out=d/'RECOUNT_071.json';r=compute(d)
    if '--check' in sys.argv:check(load(out)==r,'recount differs');print('recount --check ok')
    else:write_new(out,r);print('wrote',out)
    print({x['key']:x['label'] for x in r['rows']},'wrong',r['wrong'])
