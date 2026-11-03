"""Gates for study 069 (experiments/BRUTE_PLAN_069.json criteria), LEAN process. Inputs: results/study-069/main/{RESULTS,SEAL,
RECOUNT_069}.json, results/study-069/TEST_SUITE_069.json, experiments/truth_069.py, experiments/targets_069.py, the ledger and git.
Writes results/study-069/GATES_069.json (refuses overwrite); --check recomputes and compares. Labels are the recount's (hand truth).
A missing job => GLIVE69 FAIL and every data gate FAIL INCOMPLETE_INPUT. Finished = not KILL.
  PYTHONPATH=. python scripts/make_gates_069.py [--check]"""
import ast,hashlib,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common import load,sha,check,write_new
from experiments import truth_069 as TR
from experiments import targets_069 as TG
from experiments.brute_study_069 import canon,SEEDS,jobs_for
from scripts.recount_069 import compute as recount
from brute.api.certify32r import equivalent
D=ROOT/'results/study-069';M=D/'main';OUT=D/'GATES_069.json';LEDGER=ROOT/'results/RESEARCH_LEDGER.jsonl'
SCOPE=('CPython 3.13.5 incremental utf-8, utf-16-le, euc_jp and gb18030 decoders; read_bits 2, N <= 12 (euc_jp N <= 16), '
       'injected iid bit noise eps <= 0.30, delta 0.001; resets via fresh decoder objects')
PHRASE='certified with resets on real software ('+SCOPE+')'
MAIN_PHRASE='main block certified with resets ('+SCOPE+'); stretch/held-out not'
ORDER=('preregistration_069','truth_069','build_authorization_069','truthcheck_069','source_freeze_069','run_start_069','run_end_069')
DEC_BANNED=('getstate','setstate','reset','buffer','_buffer_decode')
NEW_FILE='brute/api/certify32r.py'
FORBIDDEN_IMPORTS=('os','sys','io','subprocess','socket','threading','multiprocessing','pathlib','shutil','tempfile','time')
OK_IMPORTS=('math','random','itertools','typing','__future__')
MAIN=('U3','U4','W16')


def git(*a):return subprocess.run(['git',*a],cwd=ROOT,capture_output=True,text=True)


def ancestor(a,b):return git('merge-base','--is-ancestor',a,b).returncode==0


def ledger():return [json.loads(l) for l in LEDGER.read_text().splitlines() if l.strip()]


def adapter_ast_ok(path=ROOT/'experiments/targets_069.py'):
    """Violations of the public-interface rule: codecs.X only for X in ALLOWED_ATTRS; the decoder object (self.dec) only .decode;
    no getstate/setstate/buffer/underscore attribute anywhere."""
    t=ast.parse(Path(path).read_text());bad=[]
    for n in ast.walk(t):
        if isinstance(n,ast.Attribute):
            a=n.attr
            if a in ('getstate','setstate','buffer','_buffer_decode') or a.startswith('_'):bad.append(a)
            if isinstance(n.value,ast.Name) and n.value.id=='codecs' and a not in TG.ALLOWED_ATTRS:bad.append('codecs.'+a)
            if isinstance(n.value,ast.Attribute) and n.value.attr=='dec' and a!='decode':bad.append('dec.'+a)
    return bad


def module_imports_ok(src):
    """(ok, bad list): the new certifier imports only OK_IMPORTS and brute.* modules, and never calls open/exec/eval/__import__."""
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


def truth_reading(w,word):
    q=w.start
    for a in word:q=w.transitions[q][a]
    c=w.emissions[q];return [c>>1&1,c&1]


def compute():
    G={};seal=load(M/'SEAL.json');R=load(M/'RESULTS.json');RC=recount();recs=R['records']
    keys=[f'{t}:{s}:{a}' for t,s,a in jobs_for('main')]
    bound=sha(M/'RESULTS.json')==seal['results_sha256'];key=lambda r:f"{r['target']}:{r['seed']}:{r['arm']}"
    complete=bool(R['complete']) and bound and sorted(key(r) for r in recs)==sorted(keys)
    lab={r['key']:r['label'] for r in RC['rows']}
    fin=[r for r in recs if not r.get('killed')];noisy=[r for r in fin if r['arm'] in ('S','Sb')]
    G['GLIVE69']={'pass':complete,'records':len(recs),'jobs':len(keys),'elapsed_s':round(R.get('total_elapsed_informational',0),1)}
    inc=lambda:{'pass':False,'why':'INCOMPLETE_INPUT'}
    if not complete:
        for g in ('GS69_sound','GDEC69','GMATCH69','GSTRETCH69','GHELD69','GMAJ69','GEQ69','GDET69','GFID69','G_recount69'):G[g]=inc()
    else:
        G['GS69_sound']={'pass':RC['wrong']==0,'wrong':RC['wrong'],'finished':len(fin)}
        ids={}
        for t in TR.TARGETS:
            for a in ('C','S'):ids[f'{t}/{a}']=sum(lab[key(r)]=='ID' for r in recs if r['target']==t and r['arm']==a)
        G['GDEC69']={'pass':all(ids[f'{t}/{a}']>=2 for t in MAIN for a in ('C','S')),'id_of_3':{k:v for k,v in ids.items() if k.split('/')[0] in MAIN},
                     'labels':lab}
        G['GSTRETCH69']={'pass':ids['EJ/C']>=2 and ids['EJ/S']>=2,'id_of_3':{'EJ/C':ids['EJ/C'],'EJ/S':ids['EJ/S']}}
        G['GHELD69']={'pass':ids['GB/C']>=2 and ids['GB/S']>=2,'id_of_3':{'GB/C':ids['GB/C'],'GB/S':ids['GB/S']}}
        per={};ok=True
        for t in MAIN:
            w=TR.world(t);idr=[r for r in fin if r['target']==t and lab[key(r)]=='ID'];bad=[]
            for r in idr:
                if r['n']!=TR.N_TRUE[t] or not equivalent(r['transitions'],r['emissions'],w.transitions,w.emissions)[0]:bad.append(key(r))
            p=bool(idr) and not bad;ok&=p;per[t]={'pass':p,'id_records':len(idr),'n_true':TR.N_TRUE[t],'mismatch':bad}
        G['GMATCH69']={'pass':ok,'per_target':per}
        G['GMAJ69']={'pass':bool(noisy) and all(r['settled_bit_errors']==0 for r in noisy),'bit_errors':sum(r['settled_bit_errors'] for r in noisy),
                     'reads_total':sum(r['reads_total'] for r in noisy),'fixed_reads_total':sum(r['fixed_reads_total'] for r in noisy)}
        cl={(r['target'],r['seed']):r for r in fin if r['arm']=='C'};pairs=[(r,cl[(r['target'],r['seed'])]) for r in noisy if (r['target'],r['seed']) in cl]
        neq=[key(a) for a,b in pairs if canon(a)!=canon(b)]
        G['GEQ69']={'pass':len(pairs)==len(noisy)>0 and not neq,'pairs':len(pairs),'unequal':neq}
        S=[r for r in recs if r['target']=='U3' and r['seed']==SEEDS[0] and r['arm']=='S'];Sb=[r for r in recs if r['arm']=='Sb']
        det=bool(S and Sb) and not S[0].get('killed') and not Sb[0].get('killed') and canon(S[0])==canon(Sb[0]) and \
            S[0]['readings_sha256']==Sb[0]['readings_sha256'] and S[0]['reads_total']==Sb[0]['reads_total']
        G['GDET69']={'pass':det}
        bad=[];astbad=adapter_ast_ok();n=0
        for r in fin:
            w=TR.world(r['target'])
            for word,rd in r['fid_sample']:
                n+=1;live=list(TG.replay(r['target'],word)[-1])
                if live!=rd or truth_reading(w,word)!=rd:bad.append([key(r),word]);break
        G['GFID69']={'pass':not bad and not astbad and n>0,'replay_mismatch':bad,'adapter_ast_violations':astbad,'words_checked':n,'records':len(fin)}
        G['G_recount69']={'pass':(M/'RECOUNT_069.json').exists() and load(M/'RECOUNT_069.json')==RC and RC['labels_agree']}
    L=ledger();ev={}
    for e in L:
        if e['event'] in ORDER and e['event'] not in ev:ev[e['event']]=e
    rs=ev.get('run_start_069')
    if rs:
        diff=git('diff','--name-status','v0.64.0',rs['commit'],'--','brute').stdout.split('\n');diff=[x.split('\t') for x in diff if x.strip()]
        src=git('show',f"{rs['commit']}:{NEW_FILE}").stdout;iok,ibad=module_imports_ok(src) if src else (False,['missing'])
        G['GHOST69']={'pass':diff==[['A',NEW_FILE]] and iok,'diff_vs_v0640':diff,'import_violations':ibad}
    else:G['GHOST69']={'pass':False,'why':'no run_start_069'}
    ts=D/'TEST_SUITE_069.json'
    if ts.exists():
        T=load(ts);shas=T.get('test_file_sha256',{});same=bool(shas) and all(sha(ROOT/f)==d for f,d in shas.items())
        G['GTEST69']={'pass':T['passed'] is True and same,'test_files_match':same,'modules':len(T.get('gated_modules',[]))}
    else:G['GTEST69']={'pass':False,'why':'no TEST_SUITE_069.json'}
    miss=[e for e in ORDER if e not in ev];chain=[ev[e]['commit'] for e in ORDER if e in ev]
    order_ok=not miss and all(ancestor(a,b) for a,b in zip(chain,chain[1:]))
    tr_ok='truth_069' in ev and ev['truth_069'].get('source_sha256')==sha(ROOT/'experiments/truth_069.py')
    G['G_PROC69']={'pass':order_ok and tr_ok,'missing':miss,'chain':chain,'truth_unchanged':tr_ok}
    failed=sorted(k for k,v in G.items() if not v['pass'])
    status=PHRASE if not failed else MAIN_PHRASE if set(failed)<={'GSTRETCH69','GHELD69'} else 'not certified (failing gates: '+', '.join(failed)+')'
    return {'study':'BRUTE-0650-RESETDECODER-069','results_sha256':seal['results_sha256'],'gates':G,'failed':failed,
            'passed':sorted(k for k in G if k not in failed),'status':status,'reset_free_certification':'Open'}


if __name__=='__main__':
    r=compute()
    if '--check' in sys.argv:check(load(OUT)==r,'gates differ');print('gates --check ok')
    else:write_new(OUT,r);print('wrote',OUT)
    print(r['status'])
