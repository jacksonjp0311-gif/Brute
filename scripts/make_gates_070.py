"""Gates for study 070 (experiments/BRUTE_PLAN_070.json criteria), LEAN process. Inputs: results/study-070/main/{RESULTS,SEAL,
RECOUNT_070}.json, results/study-070/TEST_SUITE_070.json, experiments/truth_069.py, experiments/targets_070.py, the ledger and git.
Writes results/study-070/GATES_070.json (refuses overwrite); --check recomputes and compares. Labels are the recount's (hand truth).
A missing job => GLIVE70 FAIL and every data gate FAIL INCOMPLETE_INPUT. Finished = not KILL.
  PYTHONPATH=. python scripts/make_gates_070.py [--check]"""
import ast,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common import load,sha,check,write_new
from experiments import truth_069 as TR
from experiments import targets_070 as TG
from experiments.brute_study_070 import canon,SEEDS,jobs_for,unpack
from scripts.recount_070 import compute as recount
D=ROOT/'results/study-070';M=D/'main';OUT=D/'GATES_070.json';LEDGER=ROOT/'results/RESEARCH_LEDGER.jsonl'
SCOPE=('CPython 3.13.5 incremental utf-8, utf-16-le, euc_jp and gb18030 decoders; read_bits 2; declared N = true size + 1; '
       'clean readings; no resets; Brute SAT version space with homing-based tests')
PHRASE='certified reset-free on real software ('+SCOPE+')'
ORDER=('plan_070','build_authorization_070','source_freeze_070','run_start_070','run_end_070')
NEW_FILES=('brute/api/baseline32t.py','brute/api/certify32h.py')
FORBIDDEN_IMPORTS=('os','sys','io','subprocess','socket','threading','multiprocessing','pathlib','shutil','tempfile','time')
OK_IMPORTS=('math','random','itertools','typing','__future__')
DECIDED=('ID','IDF');B_ARMS=('B','Bb','B2','B12')


def git(*a):return subprocess.run(['git',*a],cwd=ROOT,capture_output=True,text=True)


def ancestor(a,b):return git('merge-base','--is-ancestor',a,b).returncode==0


def ledger():return [json.loads(l) for l in LEDGER.read_text().splitlines() if l.strip()]


def adapter_ast_ok(path=ROOT/'experiments/targets_070.py'):
    """Violations of the reset-free public-interface rule: codecs.X only for X in ALLOWED_ATTRS, getincrementaldecoder called exactly
    once and only inside Target.__init__; self.dec only .decode; no reset / getstate / setstate / buffer / underscore attribute, and no
    method named reset."""
    t=ast.parse(Path(path).read_text());bad=[];calls=[]
    for n in ast.walk(t):
        if isinstance(n,ast.FunctionDef) and n.name=='reset':bad.append('def reset')
        if isinstance(n,ast.Attribute):
            a=n.attr
            if a in ('getstate','setstate','buffer','reset','_buffer_decode') or a.startswith('_'):bad.append(a)
            if isinstance(n.value,ast.Name) and n.value.id=='codecs' and a not in TG.ALLOWED_ATTRS:bad.append('codecs.'+a)
            if isinstance(n.value,ast.Attribute) and n.value.attr=='dec' and a!='decode':bad.append('dec.'+a)
    for c in ast.walk(t):
        if isinstance(c,ast.ClassDef) and c.name=='Target':
            for f in c.body:
                if isinstance(f,ast.FunctionDef):
                    for n in ast.walk(f):
                        if isinstance(n,ast.Attribute) and n.attr=='getincrementaldecoder':calls.append(f.name)
    tot=sum(1 for n in ast.walk(t) if isinstance(n,ast.Attribute) and n.attr=='getincrementaldecoder')
    if calls!=['__init__'] or tot!=1:bad.append(f'getincrementaldecoder uses {calls} total {tot}')
    return bad


def module_imports_ok(src):
    t=ast.parse(src);bad=[]
    for n in ast.walk(t):
        if isinstance(n,ast.Import):
            for a in n.names:
                r=a.name.split('.')[0]
                if r!='brute' and (r in FORBIDDEN_IMPORTS or r not in OK_IMPORTS):bad.append(a.name)
        elif isinstance(n,ast.ImportFrom):
            r=(n.module or '').split('.')[0]
            if r!='brute' and (r in FORBIDDEN_IMPORTS or r not in OK_IMPORTS):bad.append(n.module)
        elif isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id in ('open','exec','eval','__import__','compile'):bad.append(n.func.id)
    return not bad,bad


def compute():
    G={};seal=load(M/'SEAL.json');R=load(M/'RESULTS.json');RC=recount();recs=R['records']
    keys=[f'{t}:{s}:{a}' for t,s,a in jobs_for('main')]
    bound=sha(M/'RESULTS.json')==seal['results_sha256'];key=lambda r:f"{r['target']}:{r['seed']}:{r['arm']}"
    complete=bool(R['complete']) and bound and sorted(key(r) for r in recs)==sorted(keys)
    lab={r['key']:r['label'] for r in RC['rows']}
    fin=[r for r in recs if not r.get('killed')]
    G['GLIVE70']={'pass':complete and R.get('total_elapsed_informational',1e9)<=R['main_cap_s']+60,'records':len(recs),'jobs':len(keys),
                  'elapsed_s':round(R.get('total_elapsed_informational',0),1)}
    inc=lambda:{'pass':False,'why':'INCOMPLETE_INPUT'}
    if not complete:
        for g in ('GS70_sound','GDEC70','GBASE70','GNORESET70','GFID70','GDET70','G_recount70'):G[g]=inc()
    else:
        bw=[key(r) for r in recs if r['arm'] in B_ARMS and lab[key(r)] in ('WRONG','TRACE_MISMATCH')]
        G['GS70_sound']={'pass':not bw,'wrong':bw,'decided':sum(lab[key(r)] in DECIDED for r in recs if r['arm'] in B_ARMS)}
        table={}
        for t in TR.TARGETS:
            row={}
            for a in sorted({r['arm'] for r in recs}):
                rr=[r for r in recs if r['target']==t and r['arm']==a]
                row[a]={'N':rr[0]['N'] if rr else None,'decided':sum(lab[key(r)] in DECIDED for r in rr),'of':len(rr),
                        'labels':[lab[key(r)] for r in rr],'steps':[r.get('decoder_calls') for r in rr]}
            table[t]=row
        dec=[t for t in TR.TARGETS if table[t]['B']['decided']>=2]
        G['GDEC70']={'pass':len(dec)>=3 and not bw,'targets_decided':dec,'count':len(dec),'of':5,'v0640_baseline':'0 of 18 at N 12 (not like-for-like)'}
        tr=[r for r in recs if r['arm']=='T'];terr=[key(r) for r in tr if r.get('killed')]
        G['GBASE70']={'pass':len(tr)==15 and all(key(r) in lab for r in tr),'records':len(tr),'killed':terr,
                      'textbook_wrong':[key(r) for r in recs if r['arm'].startswith('T') and lab[key(r)] in ('WRONG','TRACE_MISMATCH')],'table':table}
        astbad=adapter_ast_ok();objs=[key(r) for r in fin if r.get('decoder_objects')!=1 or r.get('resets')!=0]
        G['GNORESET70']={'pass':not astbad and not objs,'adapter_ast_violations':astbad,'records_not_single_object':objs,'records':len(fin)}
        bad=[]
        for r in fin:
            live=[2*x[0]+x[1] for x in TG.replay(r['target'],unpack(r['actions']))]
            if live!=unpack(r['readings']):bad.append(key(r))
        G['GFID70']={'pass':not bad and bool(fin),'replay_mismatch':bad,'records':len(fin),'steps_replayed':sum(r['decoder_calls'] for r in fin)}
        B=[r for r in recs if r['target']=='U3' and r['seed']==SEEDS[0] and r['arm']=='B'];Bb=[r for r in recs if r['arm']=='Bb']
        G['GDET70']={'pass':bool(B and Bb) and not B[0].get('killed') and canon(B[0])==canon(Bb[0])}
        G['G_recount70']={'pass':(M/'RECOUNT_070.json').exists() and load(M/'RECOUNT_070.json')==RC}
    L=ledger();ev={}
    for e in L:
        if e['event'] in ORDER+('truth_069',) and e['event'] not in ev:ev[e['event']]=e
    rs=ev.get('run_start_070')
    if rs:
        diff=git('diff','--name-status','v0.65.0',rs['commit'],'--','brute').stdout.split('\n');diff=sorted(x.split('\t') for x in diff if x.strip())
        ib=[]
        for f in NEW_FILES:
            src=git('show',f"{rs['commit']}:{f}").stdout;ok,b=module_imports_ok(src) if src else (False,['missing'])
            ib+=[f+':'+x for x in b]+([] if ok else [f])
        G['GHOST70']={'pass':diff==[['A',f] for f in NEW_FILES] and not ib,'diff_vs_v0650':diff,'import_violations':ib}
    else:G['GHOST70']={'pass':False,'why':'no run_start_070'}
    ts=D/'TEST_SUITE_070.json'
    if ts.exists():
        T=load(ts);shas=T.get('test_file_sha256',{});same=bool(shas) and all(sha(ROOT/f)==d for f,d in shas.items())
        G['GTEST70']={'pass':T['passed'] is True and same,'test_files_match':same,'modules':len(T.get('gated_modules',[]))}
    else:G['GTEST70']={'pass':False,'why':'no TEST_SUITE_070.json'}
    miss=[e for e in ORDER if e not in ev];chain=[ev[e]['commit'] for e in ORDER if e in ev]
    order_ok=not miss and all(ancestor(a,b) for a,b in zip(chain,chain[1:]))
    tr_ok='truth_069' in ev and ev['truth_069'].get('source_sha256')==sha(ROOT/'experiments/truth_069.py')
    G['G_PROC70']={'pass':order_ok and tr_ok,'missing':miss,'chain':chain,'truth_unchanged':tr_ok}
    failed=sorted(k for k,v in G.items() if not v['pass'])
    status=PHRASE if not failed else 'not certified (failing gates: '+', '.join(failed)+')'
    return {'study':'BRUTE-0660-RESETFREE-070','results_sha256':seal['results_sha256'],'gates':G,'failed':failed,
            'passed':sorted(k for k in G if k not in failed),'status':status,
            'contribution_split':{'textbook':'homing sequences, Vasilevskii-Chow suite shape, Rivest-Schapire learner (arm T)',
                                  'brute':'SAT version-space certificate over the whole reset-free trajectory; does not assume h is homing (arm B)'}}


if __name__=='__main__':
    r=compute()
    if '--check' in sys.argv:check(load(OUT)==r,'gates differ');print('gates --check ok')
    else:write_new(OUT,r);print('wrote',OUT)
    print(r['status'])
