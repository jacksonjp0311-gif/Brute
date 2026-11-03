"""Gates for study 068 (experiments/BRUTE_PLAN_068.json criteria), LEAN process. Inputs: results/study-068/main/{RESULTS,SEAL,
RECOUNT_068}.json, results/study-068/TEST_SUITE_068.json, experiments/truth_068.py, experiments/targets_068.py, the ledger and git.
Writes results/study-068/GATES_068.json (refuses overwrite); --check recomputes and compares. Labels are the recount's (hand truth).
A missing job => GLIVE68 FAIL and every data gate FAIL INCOMPLETE_INPUT. Decided = ID or IDF; finished = not KILL.
  PYTHONPATH=. python scripts/make_gates_068.py [--check]"""
import ast,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common import load,sha,check,write_new
from experiments import truth_068 as TR
from experiments import targets_068 as TG
from scripts.recount_068 import compute as recount,reach
D=ROOT/'results/study-068';M=D/'main';OUT=D/'GATES_068.json';LEDGER=ROOT/'results/RESEARCH_LEDGER.jsonl'
PHRASE=('certified on real software (CPython 3.13.5 incremental utf-8 decoder, bytes 41/80/E1, held-out 41/80/F1 and utf-16-le '
        '41/D8/DC; read_bits 2, N <= 12, injected iid bit noise eps <= 0.30, delta 0.001, sequential re-reads)')
ORDER=('preregistration_068','truth_068','build_authorization_068','truthcheck_068','source_freeze_068','run_start_068','run_end_068')
BANNED=('getstate','setstate','reset','buffer','_buffer_decode')


def git(*a):return subprocess.run(['git',*a],cwd=ROOT,capture_output=True,text=True)


def ancestor(a,b):return git('merge-base','--is-ancestor',a,b).returncode==0


def ledger():return [json.loads(l) for l in LEDGER.read_text().splitlines() if l.strip()]


def adapter_ast_ok():
    t=ast.parse((ROOT/'experiments/targets_068.py').read_text());bad=[]
    for n in ast.walk(t):
        if isinstance(n,ast.Attribute):
            a=n.attr
            if a in BANNED or a.startswith('_'):bad.append(a)
            if isinstance(n.value,ast.Name) and n.value.id=='codecs' and a not in TG.ALLOWED_ATTRS:bad.append('codecs.'+a)
            if a=='dec':pass
        if isinstance(n,ast.Attribute) and isinstance(n.value,ast.Attribute) and n.value.attr=='dec' and n.attr!='decode':bad.append('dec.'+n.attr)
    return bad


def truth_readings(w,acts):
    q=w.start;out=[w.emissions[q]]
    for a in acts:q=w.transitions[q][a];out.append(w.emissions[q])
    return [[c>>1&1,c&1] for c in out]


def canon(rec):return {k:v for k,v in rec.items() if not (k.endswith('_informational'))}


def compute():
    G={};seal=load(M/'SEAL.json');R=load(M/'RESULTS.json');RC=recount();recs=R['records']
    bound=sha(M/'RESULTS.json')==seal['results_sha256'];complete=bool(R['complete']) and bound and len(recs)==19
    lab={r['key']:r for r in RC['rows']};key=lambda r:f"{r['target']}:{r['seed']}:{r['arm']}"
    fin=[r for r in recs if not r.get('killed')];noisy=[r for r in fin if r['arm'] in ('S','Sb')]
    G['GLIVE68']={'pass':complete,'records':len(recs),'elapsed_s':round(R.get('total_elapsed_informational',0),1)}
    inc=lambda:{'pass':False,'why':'INCOMPLETE_INPUT'}
    if not complete:
        for g in ('GS68_sound','GDEC68','GMAJ68','GEQ68','GDET68','GFID68','GMATCH68','G_recount68'):G[g]=inc()
    else:
        G['GS68_sound']={'pass':RC['wrong']==0,'wrong':RC['wrong'],'finished':len(fin)}
        dec={}
        for t in TR.TARGETS:
            for a in ('C','S'):dec[f'{t}/{a}']=sum(lab[key(r)]['label'] in ('ID','IDF') for r in recs if r['target']==t and r['arm']==a)
        G['GDEC68']={'pass':all(v>=2 for v in dec.values()),'decided_of_3':dec,
                     'labels':{k:v['label'] for k,v in lab.items()}}
        G['GMAJ68']={'pass':all(r['settled_bit_errors']==0 for r in noisy),'bit_errors':sum(r['settled_bit_errors'] for r in noisy),
                     'reads_total':sum(r['reads_total'] for r in noisy),'fixed_reads_total':sum(r['fixed_reads_total'] for r in noisy)}
        cl={(r['target'],r['seed']):r for r in fin if r['arm']=='C'};pairs=[(r,cl[(r['target'],r['seed'])]) for r in noisy if (r['target'],r['seed']) in cl]
        G['GEQ68']={'pass':bool(pairs) and all(a['inner_sha256']==b['inner_sha256'] for a,b in pairs),'pairs':len(pairs),
                    'equal':sum(a['inner_sha256']==b['inner_sha256'] for a,b in pairs)}
        S=[r for r in recs if r['target']=='U3' and r['seed']==12680101 and r['arm']=='S'];Sb=[r for r in recs if r['arm']=='Sb']
        det=bool(S and Sb) and not S[0].get('killed') and not Sb[0].get('killed') and {k:v for k,v in canon(S[0]).items() if k!='arm'}=={k:v for k,v in canon(Sb[0]).items() if k!='arm'}
        G['GDET68']={'pass':det}
        bad=[];astbad=adapter_ast_ok()
        for r in fin:
            live=[list(x) for x in TG.replay(r['target'],r['acts'])]
            if live!=r['clean_readings'] or truth_readings(TR.world(r['target']),r['acts'])!=r['clean_readings']:bad.append(key(r))
        G['GFID68']={'pass':not bad and not astbad,'replay_mismatch':bad,'adapter_ast_violations':astbad,'checked':len(fin)}
        per={};ok=True
        for t in TR.TARGETS:
            w=TR.world(t);need=set(reach(w,w.start));cov=set();nm=[]
            for r in fin:
                if r['target']!=t:continue
                L=lab[key(r)]
                if L['label'] in ('ID','IDF'):
                    cov|=set(L['covered'])
                    if r['n_min']!=len(L['covered']):nm.append(key(r))
            p=not nm and cov==need;ok&=p
            per[t]={'pass':p,'covered':len(cov),'reachable':len(need),'n_min_mismatch':nm}
        G['GMATCH68']={'pass':ok,'per_target':per}
        G['G_recount68']={'pass':(M/'RECOUNT_068.json').exists() and load(M/'RECOUNT_068.json')==RC and RC['labels_agree']}
    G['GHOST68']={'pass':None}
    L=ledger();ev={}
    for e in L:
        if e['event'] in ORDER and e['event'] not in ev:ev[e['event']]=e
    rs=ev.get('run_start_068')
    if rs:
        t1=git('rev-parse',f"{rs['commit']}:brute").stdout.strip();t0=git('rev-parse','v0.63.0:brute').stdout.strip()
        G['GHOST68']={'pass':bool(t0) and t0==t1,'tree_v0630':t0,'tree_run':t1}
    else:G['GHOST68']={'pass':False,'why':'no run_start_068'}
    ts=D/'TEST_SUITE_068.json';G['GTEST68']={'pass':ts.exists() and load(ts)['passed'] is True}
    miss=[e for e in ORDER if e not in ev];chain=[ev[e]['commit'] for e in ORDER if e in ev]
    order_ok=not miss and all(ancestor(a,b) for a,b in zip(chain,chain[1:]))
    tr_ok='truth_068' in ev and ev['truth_068']['source_sha256']==sha(ROOT/'experiments/truth_068.py')
    G['G_PROC68']={'pass':order_ok and tr_ok,'missing':miss,'chain':chain,'truth_unchanged':tr_ok}
    failed=sorted(k for k,v in G.items() if not v['pass'])
    return {'study':'BRUTE-0640-REALDECODER-068','results_sha256':seal['results_sha256'],'gates':G,'failed':failed,
            'passed':sorted(k for k in G if k not in failed),'status':PHRASE if not failed else 'not certified (failing gates: '+', '.join(failed)+')'}


if __name__=='__main__':
    r=compute()
    if '--check' in sys.argv:check(load(OUT)==r,'gates differ');print('gates --check ok')
    else:write_new(OUT,r);print('wrote',OUT)
    print(r['status'])
