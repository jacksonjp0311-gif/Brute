"""Study 070 recount (BRUTE_PLAN_070 G_recount70): label every sealed record against the hand truth (experiments/truth_069, unchanged).
The truth is simulated from its start over the record's full reset-free action sequence; its readings must equal the recorded ones
(else TRACE_MISMATCH, counted wrong). certify/32h IDF -> IDF if M1 from s1 is Moore-equivalent to the truth from its final state;
ID -> ID if additionally every M1 state that reproduces the trajectory and ends in s1 is equivalent to the truth start; else WRONG.
baseline/32t ID -> ID if H is equivalent to the truth from the truth state at origin_step, else WRONG; EXCEEDS_N -> EXCEEDS_N if the
truth has more than N states, else WRONG. Other labels are kept. Writes <dir>/RECOUNT_070.json (refuses overwrite); --check compares.
  PYTHONPATH=. python scripts/recount_070.py [--check] [--dir results/study-070/main]"""
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common import load,sha,check,write_new
from experiments import truth_069 as TR
from experiments.brute_study_070 import unpack
from brute.api.certify32r import equivalent
D=ROOT/'results/study-070/main'
DECIDED=('ID','IDF')


def truth_run(rec):
    w=TR.world(rec['target']);acts=unpack(rec['actions']);reads=unpack(rec['readings']);s=0;states=[0];ok=reads[0]==w.emissions[0]
    for i,a in enumerate(acts):
        s=w.transitions[s][a];states.append(s);ok=ok and reads[i+1]==w.emissions[s]
    return w,acts,reads,states,ok


def label(rec):
    if rec.get('killed'):return 'KILL',None
    w,acts,reads,states,ok=truth_run(rec);a=rec['api_label']
    if not ok:return 'TRACE_MISMATCH',None
    T,E=w.transitions,w.emissions
    if rec['api']=='brute.certify/32h':
        if a not in DECIDED:return a,None
        M,ME,s1=rec['model_T'],rec['model_E'],rec['s1']
        if not equivalent(M,ME,T,E,s1,states[-1])[0]:return 'WRONG','future'
        if a=='ID':
            starts=[]
            for q in range(len(M)):
                x=q;good=ME[x]==reads[0]
                for i,b in enumerate(acts):
                    if not good:break
                    x=M[x][b];good=ME[x]==reads[i+1]
                if good and x==s1:starts.append(q)
            if not starts or not all(equivalent(M,ME,T,E,q,0)[0] for q in starts):return 'WRONG','start'
        return a,None
    if a=='ID':return ('ID',None) if equivalent(rec['transitions'],rec['emissions'],T,E,0,states[rec['origin_step']])[0] else ('WRONG','origin')
    if a=='EXCEEDS_N':return ('EXCEEDS_N',None) if TR.N_TRUE[rec['target']]>rec['N'] else ('WRONG','exceeds')
    return a,None


def compute(d=D):
    d=Path(d);seal=load(d/'SEAL.json');check(sha(d/'RESULTS.json')==seal['results_sha256'],'RESULTS does not match its seal')
    R=load(d/'RESULTS.json');rows=[]
    for rec in R['records']:
        l,why=label(rec)
        rows.append({'key':f"{rec['target']}:{rec['seed']}:{rec['arm']}",'arm':rec['arm'],'target':rec['target'],'N':rec['N'],
                     'api_label':rec['api_label'],'label':l,'why':why,'agree':l==rec['api_label'],'steps':rec.get('decoder_calls')})
    wrong=sum(r['label'] in ('WRONG','TRACE_MISMATCH') for r in rows)
    return {'study':R['study'],'results_sha256':seal['results_sha256'],'truth_sha256':sha(ROOT/'experiments/truth_069.py'),'rows':rows,
            'wrong':wrong,'labels_agree':all(r['agree'] for r in rows) and wrong==0,'complete':R['complete']}


if __name__=='__main__':
    d=Path(sys.argv[sys.argv.index('--dir')+1]) if '--dir' in sys.argv else D;out=d/'RECOUNT_070.json';r=compute(d)
    if '--check' in sys.argv:check(load(out)==r,'recount differs');print('recount --check ok')
    else:write_new(out,r);print('wrote',out)
    print({x['key']:x['label'] for x in r['rows']},'wrong',r['wrong'])
