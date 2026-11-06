"""Gates for study 071 (experiments/BRUTE_PLAN_071.json gates), LEAN process. Inputs: results/study-071/main/{RESULTS,SEAL,RECOUNT_071}.json,
results/study-071/TEST_SUITE_071.json, experiments/truth_069.py, experiments/targets_070.py, the ledger and git.
Writes results/study-071/GATES_071.json (refuses overwrite); --check recomputes and compares. Labels are the recount's (hand truth).
GN12_71_attempt is the plan's REPORTED ATTEMPT: it is computed and reported with the gates but its failure alone does not change the
status phrase (the plan names GHEAD71_plus1 as the headline). A missing job => GLIVE71 FAIL and every data gate FAIL INCOMPLETE_INPUT.
  PYTHONPATH=. python scripts/make_gates_071.py [--check]"""
import json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common import load,sha,check,write_new
from experiments import truth_069 as TR
from experiments import targets_070 as TG
from experiments.brute_study_071 import jobs_for,unpack,RLIMIT_AS,WORKERS
from scripts.recount_071 import compute as recount
from scripts.make_gates_070 import adapter_ast_ok,module_imports_ok,ancestor,git,ledger
D=ROOT/'results/study-071';M=D/'main';OUT=D/'GATES_071.json'
SCOPE=('CPython 3.13.5 incremental utf-8, utf-16-le and euc_jp decoders (gb18030 held out); read_bits 2; declared N = true size + 1; '
       'clean readings; no resets; textbook hypothesis (brute.baseline/32t) plus SAT certificate brute.certify/32x')
PHRASE='certified reset-free hybrid at tight N on real software ('+SCOPE+')'
ORDER=('plan_071','build_authorization_071','source_freeze_071','run_start_071','run_end_071')
NEW_FILES=('brute/api/certify32x.py',)
ATTEMPT=('GN12_71_attempt',)


def compute():
    G={};seal=load(M/'SEAL.json');R=load(M/'RESULTS.json');RC=recount();recs=R['records']
    keys=[f'{t}:{s}:{a}' for t,s,a in jobs_for('main')]
    bound=sha(M/'RESULTS.json')==seal['results_sha256'];key=lambda r:f"{r['target']}:{r['seed']}:{r['arm']}"
    complete=bool(R['complete']) and bound and sorted(key(r) for r in recs)==sorted(keys)
    lab={r['key']:r['label'] for r in RC['rows']}
    fin=[r for r in recs if not r.get('killed')]
    G['GLIVE71']={'pass':complete and R.get('total_elapsed_informational',1e9)<=R['main_cap_s']+60,'records':len(recs),'jobs':len(keys),
                  'killed':[key(r) for r in recs if r.get('killed')],'elapsed_s':round(R.get('total_elapsed_informational',0),1)}
    inc=lambda:{'pass':False,'why':'INCOMPLETE_INPUT'}
    if not complete:
        for g in ('GHEAD71_plus1','GN12_71_attempt','GS71_sound','GNORESYNC71','GBASE71','GFID71','GMEM71','G_recount71'):G[g]=inc()
    else:
        wr=lambda r:lab[key(r)] in ('WRONG','TRACE_MISMATCH')
        table={}
        for t in TR.TARGETS:
            row={}
            for a in ('H','H12','B','T','T12'):
                rr=[r for r in recs if r['target']==t and r['arm']==a]
                row[a]={'N':rr[0]['N'] if rr else None,'label':[lab[key(r)] for r in rr],'steps':[r.get('decoder_calls') for r in rr],
                        't_steps':[r.get('t_steps') for r in rr],'iters':[(r.get('x') or {}).get('iters') for r in rr],
                        'kill':[r.get('kill_reason') for r in rr if r.get('killed')]}
            table[t]=row
        wrong=[key(r) for r in recs if r['arm'] in ('H','H12','B') and wr(r)]
        dec=lambda arm:[t for t in TR.TARGETS if table[t][arm]['label']==['IDF']]
        h1=dec('H');h12=dec('H12')
        G['GHEAD71_plus1']={'pass':len(h1)>=4 and not wrong,'decided':h1,'count':len(h1),'of':5,'heldout_GB_decided':'GB' in h1}
        G['GN12_71_attempt']={'pass':len(h12)>=4 and not wrong,'decided':h12,'count':len(h12),'of':5,'reported_attempt':True}
        G['GS71_sound']={'pass':not wrong,'wrong':wrong,'decided':sum(lab[key(r)] in ('IDF','ID') for r in recs if r['arm'] in ('H','H12','B'))}
        hr=[r for r in fin if r['arm'] in ('H','H12') and r['api_label']=='IDF']
        bad=[key(r) for r in hr if r['x'].get('assumes_resync') is not False or r.get('assumes_resync') is not False or r['api']!='brute.certify/32x'
             or r['x'].get('label')!='IDF' or r['x'].get('api')!='brute.certify/32x']
        objs=[key(r) for r in fin if r.get('decoder_objects')!=1 or r.get('resets')!=0];astbad=adapter_ast_ok()
        G['GNORESYNC71']={'pass':not bad and not objs and not astbad,'bad_idf':bad,'records_not_single_object':objs,'adapter_ast_violations':astbad,'h_idf_records':len(hr)}
        tr=[r for r in recs if r['arm'] in ('T','T12')]
        G['GBASE71']={'pass':len(tr)==10 and all(key(r) in lab for r in tr),'records':len(tr),'killed':[key(r) for r in tr if r.get('killed')],
                      'textbook_wrong':[key(r) for r in tr if wr(r)],'table':table}
        badf=[]
        for r in fin:
            live=[2*x[0]+x[1] for x in TG.replay(r['target'],unpack(r['actions']))]
            if live!=unpack(r['readings']):badf.append(key(r))
        G['GFID71']={'pass':not badf and bool(fin),'replay_mismatch':badf,'records':len(fin),'steps_replayed':sum(r['decoder_calls'] for r in fin)}
        memb=[key(r) for r in recs if r.get('rlimit_as_bytes')!=RLIMIT_AS or r.get('workers')!=WORKERS]
        G['GMEM71']={'pass':not memb,'bad':memb,'rlimit_as_bytes':RLIMIT_AS,'workers':WORKERS,'kills':[[key(r),r.get('kill_reason'),r.get('cap_hit')] for r in recs if r.get('killed')]}
        G['G_recount71']={'pass':(M/'RECOUNT_071.json').exists() and load(M/'RECOUNT_071.json')==RC}
    L=ledger();ev={}
    for e in L:
        if e['event'] in ORDER+('truth_069',) and e['event'] not in ev:ev[e['event']]=e
    rs=ev.get('run_start_071')
    if rs:
        diff=git('diff','--name-status','v0.66.0',rs['commit'],'--','brute').stdout.split('\n');diff=sorted(x.split('\t') for x in diff if x.strip())
        ib=[]
        for f in NEW_FILES:
            src=git('show',f"{rs['commit']}:{f}").stdout;ok,b=module_imports_ok(src) if src else (False,['missing'])
            ib+=[f+':'+x for x in b]+([] if ok else [f])
        G['GHOST71']={'pass':diff==[['A',f] for f in NEW_FILES] and not ib,'diff_vs_v0660':diff,'import_violations':ib}
    else:G['GHOST71']={'pass':False,'why':'no run_start_071'}
    ts=D/'TEST_SUITE_071.json'
    if ts.exists():
        T=load(ts);shas=T.get('test_file_sha256',{});same=bool(shas) and all(sha(ROOT/f)==d for f,d in shas.items())
        G['GTEST71']={'pass':T['passed'] is True and same,'test_files_match':same,'modules':len(T.get('gated_modules',[]))}
    else:G['GTEST71']={'pass':False,'why':'no TEST_SUITE_071.json'}
    miss=[e for e in ORDER if e not in ev];chain=[ev[e]['commit'] for e in ORDER if e in ev]
    order_ok=not miss and all(ancestor(a,b) for a,b in zip(chain,chain[1:]))
    tr_ok='truth_069' in ev and ev['truth_069'].get('source_sha256')==sha(ROOT/'experiments/truth_069.py')
    G['G_PROC71']={'pass':order_ok and tr_ok,'missing':miss,'chain':chain,'truth_unchanged':tr_ok}
    failed=sorted(k for k,v in G.items() if not v['pass']);core=[k for k in failed if k not in ATTEMPT]
    status=(PHRASE if not core else 'not certified (failing gates: '+', '.join(failed)+')')
    return {'study':'BRUTE-0670-HYBRID-071','results_sha256':seal['results_sha256'],'gates':G,'failed':failed,
            'passed':sorted(k for k in G if k not in failed),'reported_attempt_gates':list(ATTEMPT),
            'attempt_failed':[k for k in failed if k in ATTEMPT],'status':status,
            'contribution_split':{'textbook':'the hypothesis (Rivest-Schapire homing + L* + Vasilevskii-Chow, arm T) and most decoder steps',
                                  'brute':'the SAT certificate certify/32x under the declared N alone (no resync assumption), arm H'}}


if __name__=='__main__':
    r=compute()
    if '--check' in sys.argv:check(load(OUT)==r,'gates differ');print('gates --check ok')
    else:write_new(OUT,r);print('wrote',OUT)
    print(r['status'])
