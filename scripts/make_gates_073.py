"""Gates for study 073 (experiments/BRUTE_PLAN_073.json gates), LEAN process. Inputs: results/study-073/main/{RESULTS,SEAL,RECOUNT_073}.json,
results/study-073/TEST_SUITE_073.json, experiments/truth_073.json, experiments/targets_073.py, the ledger and git.
Writes results/study-073/GATES_073.json (refuses overwrite); --check recomputes and compares. Labels are the recount's (oracle truth).
A missing job => GLIVE73 FAIL and every data gate FAIL INCOMPLETE_INPUT. Finished = not KILL.
  PYTHONPATH=. python scripts/make_gates_073.py [--check]"""
import json,statistics,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common import load,sha,check,write_new
from experiments import truth_073 as TR
from experiments import targets_073 as TG
from experiments.brute_study_073 import jobs_for,unpack,RLIMIT_AS,WORKERS,SEEDS
from scripts.recount_073 import compute as recount
from scripts.make_gates_070 import adapter_ast_ok,ancestor,git,ledger
D=ROOT/'results/study-073';M=D/'main';OUT=D/'GATES_073.json'
SCOPE=('CPython 3.13.5 incremental shift_jis, euc_kr, big5, utf-32-le, utf-8-sig, utf-16-be, euc_jis_2004, big5hkscs decoders, held out hz and johab; read_bits 2; '
       'declared N = oracle minimal size + 3 (loose) and + 1; clean readings; no resets; Brute SAT version space with homing-based tests and bitset preprocessing (certify/33h)')
PHRASE='certified reset-free at a loose declared N on real software ('+SCOPE+')'
ORDER=('truth_073','plan_073','build_authorization_073','source_freeze_073','run_start_073','run_end_073')
DECIDED=('ID','IDF')
HEAD_MIN=6;HEAD_TARGETS=3;C1_MIN=7;STEP_MAX=1.0   # constants of BRUTE_PLAN_073 (locked before the run)


def compute():
    G={};seal=load(M/'SEAL.json');R=load(M/'RESULTS.json');RC=recount();recs=R['records']
    keys=[f'{t}:{s}:{a}' for t,s,a in jobs_for('main')]
    bound=sha(M/'RESULTS.json')==seal['results_sha256'];key=lambda r:f"{r['target']}:{r['seed']}:{r['arm']}"
    complete=bool(R['complete']) and bound and sorted(key(r) for r in recs)==sorted(keys)
    lab={r['key']:r['label'] for r in RC['rows']}
    fin=[r for r in recs if not r.get('killed')]
    G['GLIVE73']={'pass':complete and R.get('total_elapsed_informational',1e9)<=R['main_cap_s']+60,'records':len(recs),'jobs':len(keys),
                  'killed':[[key(r),r.get('kill_reason')] for r in recs if r.get('killed')],'elapsed_s':round(R.get('total_elapsed_informational',0),1)}
    inc=lambda:{'pass':False,'why':'INCOMPLETE_INPUT'}
    if not complete:
        for g in ('GHEAD73','GSTEP73','GHELD73','GC1_73','GS73_sound','GBASE73','GNORESET73','GFID73','GMEM73','G_recount73'):G[g]=inc()
    else:
        wr=lambda r:lab[key(r)] in ('WRONG','TRACE_MISMATCH')
        table={}
        for t in TR.TARGETS:
            row={}
            for a,sds in (('C3',SEEDS),('C1',SEEDS[:1]),('T3',SEEDS)):
                row[a]=[{'seed':s,'N':next(r['N'] for r in recs if r['target']==t and r['arm']==a and r['seed']==s),
                         'label':lab[f'{t}:{s}:{a}'],'steps':next(r.get('decoder_calls') for r in recs if r['target']==t and r['arm']==a and r['seed']==s),
                         'kill':next(r.get('kill_reason') for r in recs if r['target']==t and r['arm']==a and r['seed']==s)} for s in sds]
            table[t]=row
        wrong=[key(r) for r in recs if wr(r)]
        c3=[(t,s) for t in TR.TARGETS for s in SEEDS if lab[f'{t}:{s}:C3']=='IDF']
        c3t={t for (t,s) in c3};held=[(t,s) for (t,s) in c3 if t in ('HZ','JO')]
        G['GHEAD73']={'pass':len(c3)>=HEAD_MIN and len(c3t)>=HEAD_TARGETS and not wrong,'decided_cells':len(c3),'of':20,'needed':HEAD_MIN,'targets_decided':sorted(c3t),
                      'decided_per_target':{t:sum(1 for (x,s) in c3 if x==t) for t in TR.TARGETS}}
        G['GHELD73']={'pass':len(held)>=1 and not wrong,'heldout_decided_cells':[f'{t}:{s}' for t,s in held],'of':4}
        c1=[t for t in TR.TARGETS if lab[f'{t}:{SEEDS[0]}:C1']=='IDF']
        G['GC1_73']={'pass':len(c1)>=C1_MIN and not wrong,'decided_targets':c1,'of':10,'needed':C1_MIN}
        both=[(t,s) for (t,s) in c3 if lab[f'{t}:{s}:T3']=='ID']
        steps=lambda t,s,a:next(r['decoder_calls'] for r in recs if r['target']==t and r['seed']==s and r['arm']==a)
        ratios=[steps(t,s,'C3')/steps(t,s,'T3') for (t,s) in both]
        med=statistics.median(ratios) if ratios else None
        G['GSTEP73']={'pass':med is not None and med<=STEP_MAX,'median_ratio':med,'cells':len(both),'needed_at_most':STEP_MAX,'ratios':{f'{t}:{s}':round(x,3) for (t,s),x in zip(both,ratios)}}
        G['GS73_sound']={'pass':not wrong,'wrong':wrong,'decided_C':sum(lab[key(r)] in DECIDED for r in recs if r['arm'] in ('C1','C3')),'decided_T':sum(lab[key(r)] in DECIDED for r in recs if r['arm']=='T3')}
        tr=[r for r in recs if r['arm']=='T3']
        G['GBASE73']={'pass':len(tr)==20 and all(key(r) in lab for r in tr),'records':len(tr),'killed':[key(r) for r in tr if r.get('killed')],
                      'table':table,'t3_decided':sum(lab[key(r)]=='ID' for r in tr),
                      'c_kills':[[key(r),r.get('kill_reason')] for r in recs if r['arm'] in ('C1','C3') and r.get('killed')]}
        astbad=adapter_ast_ok(ROOT/'experiments/targets_073.py');objs=[key(r) for r in fin if r.get('decoder_objects')!=1 or r.get('resets')!=0]
        G['GNORESET73']={'pass':not astbad and not objs,'adapter_ast_violations':astbad,'records_not_single_object':objs,'records':len(fin)}
        badf=[]
        for r in fin:
            t=TG.Target(r['target']);acts=unpack(r['actions']);live=[2*x[0]+x[1] for x in [t.read()]+[t.act(a) for a in acts]]
            if live!=unpack(r['readings']):badf.append(key(r))
        G['GFID73']={'pass':not badf and bool(fin),'replay_mismatch':badf,'records':len(fin),'steps_replayed':sum(r['decoder_calls'] for r in fin)}
        memb=[key(r) for r in recs if r.get('rlimit_as_bytes')!=RLIMIT_AS or r.get('workers')!=WORKERS]
        G['GMEM73']={'pass':not memb,'bad':memb,'rlimit_as_bytes':RLIMIT_AS,'workers':WORKERS,'kills':[[key(r),r.get('kill_reason'),r.get('cap_hit')] for r in recs if r.get('killed')]}
        G['G_recount73']={'pass':(M/'RECOUNT_073.json').exists() and load(M/'RECOUNT_073.json')==RC}
    L=ledger();ev={}
    for e in L:
        if e['event'] in ORDER and e['event'] not in ev:ev[e['event']]=e
    rs=ev.get('run_start_073')
    if rs:
        diff=git('diff','--name-status','v0.68.0',rs['commit'],'--','brute').stdout.strip()
        want={'A\tbrute/apart33.py','A\tbrute/api/certify33h.py'}
        G['GHOST73']={'pass':set(diff.splitlines())==want,'diff_vs_v0680':diff,'allowed':sorted(want)}
    else:G['GHOST73']={'pass':False,'why':'no run_start_073'}
    tp=ROOT/'scripts/make_truth_073.py'
    try:
        r=subprocess.run([sys.executable,str(tp),'--check'],cwd=ROOT,capture_output=True,text=True,env={'PYTHONPATH':str(ROOT),'PATH':'/usr/bin:/bin'});reproduced=r.returncode==0
    except Exception:reproduced=False
    t_ok='truth_073' in ev and ev['truth_073'].get('source_sha256')==sha(ROOT/'experiments/truth_073.json')
    G['GTRUTH73']={'pass':reproduced and t_ok,'reproduced':reproduced,'ledger_sha_matches':t_ok}
    ts=D/'TEST_SUITE_073.json'
    if ts.exists():
        T=load(ts);shas=T.get('test_file_sha256',{});same=bool(shas) and all(sha(ROOT/f)==d for f,d in shas.items())
        G['GTEST73']={'pass':T['passed'] is True and same,'test_files_match':same,'modules':len(T.get('gated_modules',[]))}
    else:G['GTEST73']={'pass':False,'why':'no TEST_SUITE_073.json'}
    miss=[e for e in ORDER if e not in ev];chain=[ev[e]['commit'] for e in ORDER if e in ev]
    order_ok=not miss and all(ancestor(a,b) for a,b in zip(chain,chain[1:]))
    G['G_PROC73']={'pass':order_ok,'missing':miss,'chain':chain}
    failed=sorted(k for k,v in G.items() if not v['pass'])
    status=PHRASE if not failed else 'not certified (failing gates: '+', '.join(failed)+')'
    return {'study':'BRUTE-0690-LOOSEN-073','results_sha256':seal['results_sha256'],'gates':G,'failed':failed,
            'passed':sorted(k for k in G if k not in failed),'status':status,
            'contribution_split':{'textbook':'arm T: homing sequences, Vasilevskii-Chow suite shape, Rivest-Schapire learner (comparison only)',
                                  'brute':'arm C: certify/33h, the SAT version-space certificate over the whole reset-free trajectory (certify/32h with bitset trace preprocessing)'}}


if __name__=='__main__':
    r=compute()
    if '--check' in sys.argv:check(load(OUT)==r,'gates differ');print('gates --check ok')
    else:write_new(OUT,r);print('wrote',OUT)
    print(r['status'])
