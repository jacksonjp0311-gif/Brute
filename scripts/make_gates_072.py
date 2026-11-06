"""Gates for study 072 (experiments/BRUTE_PLAN_072.json gates), LEAN process. Inputs: results/study-072/main/{RESULTS,SEAL,RECOUNT_072}.json,
results/study-072/TEST_SUITE_072.json, experiments/truth_072.json, experiments/targets_072.py, the ledger and git.
Writes results/study-072/GATES_072.json (refuses overwrite); --check recomputes and compares. Labels are the recount's (oracle truth).
A missing job => GLIVE72 FAIL and every data gate FAIL INCOMPLETE_INPUT. Finished = not KILL.
  PYTHONPATH=. python scripts/make_gates_072.py [--check]"""
import json,statistics,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common import load,sha,check,write_new
from experiments import truth_072 as TR
from experiments import targets_072 as TG
from experiments.brute_study_072 import jobs_for,unpack,RLIMIT_AS,WORKERS,SEEDS
from scripts.recount_072 import compute as recount
from scripts.make_gates_070 import adapter_ast_ok,ancestor,git,ledger
D=ROOT/'results/study-072';M=D/'main';OUT=D/'GATES_072.json'
SCOPE=('CPython 3.13.5 incremental shift_jis, euc_kr, big5, utf-32-le, utf-8-sig, utf-16-be, euc_jis_2004 decoders (big5hkscs held out); read_bits 2; '
       'declared N = oracle minimal size + 1; clean readings; no resets; Brute SAT version space with homing-based tests (certify/32h, unchanged)')
PHRASE='certified reset-free on more real software ('+SCOPE+')'
ORDER=('truth_072','plan_072','build_authorization_072','source_freeze_072','run_start_072','run_end_072')
DECIDED=('ID','IDF')


def compute():
    G={};seal=load(M/'SEAL.json');R=load(M/'RESULTS.json');RC=recount();recs=R['records']
    keys=[f'{t}:{s}:{a}' for t,s,a in jobs_for('main')]
    bound=sha(M/'RESULTS.json')==seal['results_sha256'];key=lambda r:f"{r['target']}:{r['seed']}:{r['arm']}"
    complete=bool(R['complete']) and bound and sorted(key(r) for r in recs)==sorted(keys)
    lab={r['key']:r['label'] for r in RC['rows']}
    fin=[r for r in recs if not r.get('killed')]
    G['GLIVE72']={'pass':complete and R.get('total_elapsed_informational',1e9)<=R['main_cap_s']+60,'records':len(recs),'jobs':len(keys),
                  'killed':[[key(r),r.get('kill_reason')] for r in recs if r.get('killed')],'elapsed_s':round(R.get('total_elapsed_informational',0),1)}
    inc=lambda:{'pass':False,'why':'INCOMPLETE_INPUT'}
    if not complete:
        for g in ('GHEAD72','GSTEP72','GS72_sound','GBASE72','GNORESET72','GFID72','GMEM72','G_recount72'):G[g]=inc()
    else:
        wr=lambda r:lab[key(r)] in ('WRONG','TRACE_MISMATCH')
        table={}
        for t in TR.TARGETS:
            row={}
            for a,sds in (('B',SEEDS),('T',SEEDS),('B3',SEEDS[:1])):
                row[a]=[{'seed':s,'N':next(r['N'] for r in recs if r['target']==t and r['arm']==a and r['seed']==s),
                         'label':lab[f'{t}:{s}:{a}'],'steps':next(r.get('decoder_calls') for r in recs if r['target']==t and r['arm']==a and r['seed']==s),
                         'kill':next(r.get('kill_reason') for r in recs if r['target']==t and r['arm']==a and r['seed']==s)} for s in sds]
            table[t]=row
        wrong=[key(r) for r in recs if wr(r)]
        b1=[(t,s) for t in TR.TARGETS for s in SEEDS if lab[f'{t}:{s}:B']=='IDF']
        hk=[s for (t,s) in b1 if t=='HK']
        G['GHEAD72']={'pass':len(b1)>=12 and len(hk)>=1 and not wrong,'decided_cells':len(b1),'of':16,'heldout_HK_decided_seeds':hk,
                      'decided_per_target':{t:sum(1 for (x,s) in b1 if x==t) for t in TR.TARGETS}}
        both=[(t,s) for (t,s) in b1 if lab[f'{t}:{s}:T']=='ID']
        steps=lambda t,s,a:next(r['decoder_calls'] for r in recs if r['target']==t and r['seed']==s and r['arm']==a)
        ratios=[steps(t,s,'B')/steps(t,s,'T') for (t,s) in both]
        med=statistics.median(ratios) if ratios else None
        G['GSTEP72']={'pass':med is not None and med<=0.5,'median_ratio':med,'cells':len(both),'ratios':{f'{t}:{s}':round(x,3) for (t,s),x in zip(both,ratios)}}
        G['GS72_sound']={'pass':not wrong,'wrong':wrong,'decided_B':sum(lab[key(r)] in DECIDED for r in recs if r['arm'] in ('B','B3')),'decided_T':sum(lab[key(r)] in DECIDED for r in recs if r['arm']=='T')}
        tr=[r for r in recs if r['arm']=='T']
        G['GBASE72']={'pass':len(tr)==16 and all(key(r) in lab for r in tr),'records':len(tr),'killed':[key(r) for r in tr if r.get('killed')],
                      'table':table,'b3_decided':sum(lab[key(r)]=='IDF' for r in recs if r['arm']=='B3')}
        astbad=adapter_ast_ok(ROOT/'experiments/targets_072.py');objs=[key(r) for r in fin if r.get('decoder_objects')!=1 or r.get('resets')!=0]
        G['GNORESET72']={'pass':not astbad and not objs,'adapter_ast_violations':astbad,'records_not_single_object':objs,'records':len(fin)}
        badf=[]
        for r in fin:
            t=TG.Target(r['target']);acts=unpack(r['actions']);live=[2*x[0]+x[1] for x in [t.read()]+[t.act(a) for a in acts]]
            if live!=unpack(r['readings']):badf.append(key(r))
        G['GFID72']={'pass':not badf and bool(fin),'replay_mismatch':badf,'records':len(fin),'steps_replayed':sum(r['decoder_calls'] for r in fin)}
        memb=[key(r) for r in recs if r.get('rlimit_as_bytes')!=RLIMIT_AS or r.get('workers')!=WORKERS]
        G['GMEM72']={'pass':not memb,'bad':memb,'rlimit_as_bytes':RLIMIT_AS,'workers':WORKERS,'kills':[[key(r),r.get('kill_reason'),r.get('cap_hit')] for r in recs if r.get('killed')]}
        G['G_recount72']={'pass':(M/'RECOUNT_072.json').exists() and load(M/'RECOUNT_072.json')==RC}
    L=ledger();ev={}
    for e in L:
        if e['event'] in ORDER and e['event'] not in ev:ev[e['event']]=e
    rs=ev.get('run_start_072')
    if rs:
        diff=git('diff','--name-status','v0.67.0',rs['commit'],'--','brute').stdout.strip()
        G['GHOST72']={'pass':diff=='','diff_vs_v0670':diff}
    else:G['GHOST72']={'pass':False,'why':'no run_start_072'}
    tp=ROOT/'scripts/make_truth_072.py'
    try:
        r=subprocess.run([sys.executable,str(tp),'--check'],cwd=ROOT,capture_output=True,text=True,env={'PYTHONPATH':str(ROOT),'PATH':'/usr/bin:/bin'});reproduced=r.returncode==0
    except Exception:reproduced=False
    t_ok='truth_072' in ev and ev['truth_072'].get('source_sha256')==sha(ROOT/'experiments/truth_072.json')
    G['GTRUTH72']={'pass':reproduced and t_ok,'reproduced':reproduced,'ledger_sha_matches':t_ok}
    ts=D/'TEST_SUITE_072.json'
    if ts.exists():
        T=load(ts);shas=T.get('test_file_sha256',{});same=bool(shas) and all(sha(ROOT/f)==d for f,d in shas.items())
        G['GTEST72']={'pass':T['passed'] is True and same,'test_files_match':same,'modules':len(T.get('gated_modules',[]))}
    else:G['GTEST72']={'pass':False,'why':'no TEST_SUITE_072.json'}
    miss=[e for e in ORDER if e not in ev];chain=[ev[e]['commit'] for e in ORDER if e in ev]
    order_ok=not miss and all(ancestor(a,b) for a,b in zip(chain,chain[1:]))
    G['G_PROC72']={'pass':order_ok,'missing':miss,'chain':chain}
    failed=sorted(k for k,v in G.items() if not v['pass'])
    status=PHRASE if not failed else 'not certified (failing gates: '+', '.join(failed)+')'
    return {'study':'BRUTE-0680-BREADTH-072','results_sha256':seal['results_sha256'],'gates':G,'failed':failed,
            'passed':sorted(k for k in G if k not in failed),'status':status,
            'contribution_split':{'textbook':'arm T: homing sequences, Vasilevskii-Chow suite shape, Rivest-Schapire learner (comparison only)',
                                  'brute':'arm B: certify/32h, the SAT version-space certificate over the whole reset-free trajectory (unchanged since v0.66.0)'}}


if __name__=='__main__':
    r=compute()
    if '--check' in sys.argv:check(load(OUT)==r,'gates differ');print('gates --check ok')
    else:write_new(OUT,r);print('wrote',OUT)
    print(r['status'])
