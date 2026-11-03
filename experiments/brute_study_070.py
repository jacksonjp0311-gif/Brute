"""Study BRUTE-0660-RESETFREE-070 runner (experiments/BRUTE_PLAN_070.json). New file; drives brute.certify/32h (Brute: SAT version space
+ homing-based tests) and the textbook baseline brute.baseline/32t (Rivest-Schapire homing + L* + Vasilevskii-Chow) through their
public interfaces on the real decoders of experiments/targets_070.py, WITHOUT RESETS: one decoder object per job, one action stream.
Never imports the ground truth. Arms B / T at N = true + 1 (3 seeds), Bb (B on U3 seed 1), B2 / T2 (N = true + 2), B12 / T12 (N 12,
EJ 16), seed 12700101. One forked process per job (at most 7), SIGKILL at 900 s -> KILL record; 3600 s main cap.
  PYTHONPATH=. python experiments/brute_study_070.py --block main
  PYTHONPATH=. python experiments/brute_study_070.py --block smoke --output /tmp/x"""
from __future__ import annotations
import argparse,base64,hashlib,json,os,signal,sys,tempfile,time,zlib
import multiprocessing as mp
from pathlib import Path
from experiments.brute_common import check,sha,load,write_new
from experiments import targets_070 as TG
from brute.api import certify32h as C32H
from brute.api import baseline32t as B32T

ROOT=Path(__file__).resolve().parents[1]
PLAN=ROOT/'experiments/BRUTE_PLAN_070.json';FREEZE=ROOT/'experiments/BRUTE_SOURCE_FREEZE_070.json';STUDY_DIR=ROOT/'results/study-070'
READ_BITS=2;K_STEPS=40000;CONFLICT_CAP=50000;BUDGET=50000000;BATCH=400;STEP_CAP=3000000
NS={'main':{'U3':7,'U4':8,'W16':8,'EJ':14,'GB':9},'plus2':{'U3':8,'U4':9,'W16':9,'EJ':15,'GB':10},'n12':{'U3':12,'U4':12,'W16':12,'EJ':16,'GB':12}}
NKEY={'B':'main','T':'main','Bb':'main','B2':'plus2','T2':'plus2','B12':'n12','T12':'n12'}
BLOCK_OF={'U3':'main','U4':'main','W16':'main','EJ':'stretch','GB':'heldout'}
WORKERS=7;JOB_KILL_S=900.0;MAIN_CAP_S=3600.0;POLL_S=0.5
TARGETS=('U3','U4','W16','EJ','GB');SEEDS=(12700101,12700102,12700103);SMOKE_SEED=12700301
SCHEMA='brute.study.v70'
WALL_SUFFIXES=('_wall','_walls','_wall_max','_informational','_informational_seconds')


def jobs_for(block):
    if block=='main':
        return ([(t,s,a) for t in TARGETS for a in ('B','T') for s in SEEDS]+[('U3',SEEDS[0],'Bb')]
                +[(t,SEEDS[0],a) for a in ('B2','T2','B12','T12') for t in TARGETS])
    if block=='smoke':return [(t,SMOKE_SEED,a) for t in TARGETS for a in ('B','T')]
    raise ValueError(block)


def key(j):return f'{j[0]}:{j[1]}:{j[2]}'


def _strip(x):
    if isinstance(x,dict):return {k:_strip(v) for k,v in x.items() if not (k=='wall' or k.endswith(WALL_SUFFIXES))}
    if isinstance(x,list):return [_strip(v) for v in x]
    return x


def canon(rec):
    """Record without wall fields and the arm name (GDET70 compares these)."""
    return {k:v for k,v in _strip(rec).items() if k!='arm'}


def pack(digits):
    """Digit string -> {'z': base64 zlib, 'len', 'sha256'}; unpack() inverts."""
    s=''.join(map(str,digits)).encode();return {'z':base64.b64encode(zlib.compress(s,9)).decode(),'len':len(s),'sha256':hashlib.sha256(s).hexdigest()}


def unpack(p):
    s=zlib.decompress(base64.b64decode(p['z'])).decode();check(len(s)==p['len'] and hashlib.sha256(s.encode()).hexdigest()==p['sha256'],'pack');return [int(c) for c in s]


def _code(r):return 2*r[0]+r[1]


def run_fresh(name,seed,arm):
    tg=TG.Target(name);N=NS[NKEY[arm]][name];acts=[];reads=[_code(tg.read())];t0=time.perf_counter()
    if arm.startswith('B'):
        c=C32H.Certifier32H(tg.read(),tg.k,N,read_bits=READ_BITS,seed=seed,batch_steps=BATCH,K=K_STEPS,conflict_cap=CONFLICT_CAP,budget_conflicts=BUDGET)
        try:
            while True:
                w=c.propose()
                if w is None:break
                for a in w:r=tg.act(a);c.observe(a,r);acts.append(a);reads.append(_code(r))
            R=c.result();T,E=C32H._norm(R['model']) if R.get('model') else (None,None)
            out={'api':R['api'],'api_label':R['label'],'stop':R['stop'],'n_min':R['n_min'],'model_T':T,'model_E':E,'s1':R['s1'],
                 'rounds':R['rounds'],'conflicts':R['conflicts'],'capped':R['capped'],'batches':c.batches,'K':K_STEPS}
        finally:c.close()
    else:
        c=B32T.Baseline32T(tg.read(),tg.k,N,READ_BITS,seed=seed,step_cap=STEP_CAP);w=c.propose()
        while w is not None:
            for a in w:r=tg.act(a);c.observe(a,r);acts.append(a);reads.append(_code(r))
            w=c.next()
        R=c.record()
        out={'api':R['api'],'api_label':R['label'],'n':R.get('n'),'transitions':R.get('transitions'),'emissions':R.get('emissions'),
             'origin_step':R.get('origin_step'),'sigma':R.get('sigma'),'h':R['h'],'h_history':R['h_history'],'restarts':R['restarts'],
             'queries':R['queries'],'step_cap':STEP_CAP}
    check(tg.steps==len(acts),'step accounting')
    rec={'target':name,'block':BLOCK_OF[name],'codec':tg.codec,'bytes':list(tg.bs),'seed':seed,'arm':arm,'N':N,'python':sys.version,
         'decoder_calls':tg.steps,'decoder_objects':tg.decoder_objects,'resets':0,'actions':pack(acts),'readings':pack(reads),
         'killed':False,'job_wall_informational':time.perf_counter()-t0}
    rec.update(out);return rec


def kill_record(j,wall):
    return {'target':j[0],'block':BLOCK_OF[j[0]],'seed':j[1],'arm':j[2],'N':NS[NKEY[j[2]]][j[0]],'api_label':'KILL','killed':True,
            'job_kill_s':JOB_KILL_S,'job_wall_informational':wall}


def _child(j,path):
    try:
        c=run_fresh(*j);tmp=path+'.part'
        with open(tmp,'w') as fh:json.dump(c,fh)
        os.replace(tmp,path);os._exit(0)
    except BaseException as e:
        try:
            with open(path+'.err','w') as fh:fh.write(repr(e))
        except Exception:pass
        os._exit(3)


def run_jobs(jobs,log,t_start,cap):
    tmpd=tempfile.mkdtemp(prefix='brute070_');ctx=mp.get_context('fork');alive={};q=list(jobs);done={};errors=[];n=0
    while (q or alive) and time.perf_counter()-t_start<cap:
        while q and len(alive)<WORKERS:
            j=q.pop(0);path=os.path.join(tmpd,key(j).replace(':','_')+'.json')
            p=ctx.Process(target=_child,args=(j,path));p.start();alive[key(j)]=(j,p,path,time.perf_counter())
        time.sleep(POLL_S)
        for k_,(j,p,path,t0) in list(alive.items()):
            wall=time.perf_counter()-t0
            if p.exitcode is None and wall<JOB_KILL_S:continue
            if p.exitcode is None:os.kill(p.pid,signal.SIGKILL);p.join();c=kill_record(j,wall)
            else:
                p.join()
                if p.exitcode!=0 or not os.path.exists(path):
                    e=open(path+'.err').read() if os.path.exists(path+'.err') else f'exit {p.exitcode}';errors.append([k_,e]);del alive[k_]
                    log(f'ERROR {k_} {e}');continue
                with open(path) as fh:c=json.load(fh)
            done[k_]=c;del alive[k_];n+=1
            log(f'done {n}/{len(jobs)} {k_} {c["job_wall_informational"]:.1f}s {c["api_label"]} N={c["N"]} steps={c.get("decoder_calls")}')
    for k_,(j,p,path,t0) in alive.items():os.kill(p.pid,signal.SIGKILL);p.join()
    return done,errors


def run(output,block):
    output=Path(output);plan=load(PLAN)
    if block=='main':
        check(FREEZE.exists(),'source freeze missing');fz=load(FREEZE)
        for rel,d in fz['sha256_files'].items():check(sha(ROOT/rel)==d,'freeze mismatch '+rel)
    for nm in ('RESULTS.json','SEAL.json'):check(not (output/nm).exists(),'refusing overwrite')
    output.mkdir(parents=True,exist_ok=True);jobs=jobs_for(block);t0=time.perf_counter()
    logf=open(output/'run.log','a')
    def log(s):print(s,flush=True);logf.write(time.strftime('%H:%M:%S ')+s+'\n');logf.flush()
    done,errors=run_jobs(jobs,log,t0,MAIN_CAP_S)
    keys=[key(j) for j in jobs];missing=[k for k in keys if k not in done]
    res={'schema':SCHEMA,'study':plan['study'],'block':block,'complete':not missing and not errors,'job_keys':keys,'missing_job_keys':missing,
         'errors':errors,'records':[done[k] for k in keys if k in done],'N':NS,'read_bits':READ_BITS,'K_steps':K_STEPS,'conflict_cap':CONFLICT_CAP,
         'budget_conflicts':BUDGET,'batch_steps':BATCH,'step_cap':STEP_CAP,'job_kill_s':JOB_KILL_S,'main_cap_s':MAIN_CAP_S,'workers':WORKERS,
         'resets':0,'total_elapsed_informational':time.perf_counter()-t0}
    write_new(output/'RESULTS.json',res)
    write_new(output/'SEAL.json',{'study':plan['study'],'block':block,'results_sha256':sha(output/'RESULTS.json'),'plan_sha256':sha(PLAN),
              'freeze_sha256':sha(FREEZE) if block=='main' else None,'complete':res['complete'],'job_count':len(keys),'records':len(done)})
    return res


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--block',choices=('main','smoke'),default='main');ap.add_argument('--output')
    a=ap.parse_args();out=a.output or str(STUDY_DIR/a.block)
    if a.block!='main':check(not Path(out).resolve().is_relative_to(STUDY_DIR.resolve()),'smoke output outside results/study-070')
    r=run(out,a.block);print('done complete=',r['complete'])
