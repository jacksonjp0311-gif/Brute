"""Study BRUTE-0720-GUARD-076 runner (experiments/BRUTE_PLAN_076.json). New file. Arms on 10 real CPython decoders of experiments/targets_076.py
(the 8 of study 072 plus held-out hz and johab), WITHOUT RESETS (one decoder object per job): C = brute.certify/34h (unchanged: bitset preprocess + separating-word policy, no homing batch); T = brute.baseline/32t unchanged. C3: C at plus3 (N = oracle minimal size + 3),
10 targets x seeds 12760101 and 12760102; C1: C at plus1, 10 targets x seed 12760101; T3: T at plus3, 10 x 2. JOB_KILL 900 s; MAIN_CAP 4800 s; MEASUREMENT FIX: Certifier34H(..., wall_guard_case_s=JOB_KILL_S) so inherited GUARD_CASE_S=600 does not fire first (study 075 deviation #215). Per-job JSON under output/jobs/ (not /tmp). Never imports the truth. One forked
process per job, at most 3 alive; each child sets RLIMIT_AS = 2.0 GiB and oom_score_adj 1000; MemoryError / signal exit / job-kill SIGKILL ->
KILL record. Main cap; run once.
  PYTHONPATH=. python experiments/brute_study_076.py --block main
  PYTHONPATH=. python experiments/brute_study_076.py --block smoke --output /tmp/x"""
from __future__ import annotations
import argparse,base64,hashlib,json,os,resource,signal,sys,time,zlib
import multiprocessing as mp
from pathlib import Path
from experiments.brute_common import check,sha,load,write_new
from experiments import targets_076 as TG
from brute.api import certify34h as C34H
from brute.api import certify32h as H32
from brute.api import baseline32t as B32T

ROOT=Path(__file__).resolve().parents[1]
PLAN=ROOT/'experiments/BRUTE_PLAN_076.json';FREEZE=ROOT/'experiments/BRUTE_SOURCE_FREEZE_076.json';STUDY_DIR=ROOT/'results/study-076'
READ_BITS=2;K_STEPS=40000;RLIMIT_AS=int(2.0*(1<<30));CONFLICT_CAP=50000;BUDGET=50000000;BATCH=1;STEP_CAP=3000000
NS={'plus1':{'SJ':4,'KR':5,'B5':6,'U32':8,'U8S':10,'U16B':10,'EJ4':12,'HK':6,'HZ':11,'JO':5},'plus3':{'SJ':6,'KR':7,'B5':8,'U32':10,'U8S':12,'U16B':12,'EJ4':14,'HK':8,'HZ':13,'JO':7}}
NKEY={'C1':'plus1','C3':'plus3','T3':'plus3'}
BLOCK_OF={t:'main' for t in ('SJ','KR','B5','U32','U8S','U16B','EJ4','HK')};BLOCK_OF['HZ']='heldout';BLOCK_OF['JO']='heldout'
WORKERS=3;JOB_KILL_S=900.0;MAIN_CAP_S=4800.0;POLL_S=0.5;WALL_GUARD_CASE_S=JOB_KILL_S
TARGETS=tuple(TG.TARGETS);SEEDS=(12760101,12760102);SMOKE_SEED=12760301
SCHEMA='brute.study.v76'
WALL_SUFFIXES=('_wall','_walls','_wall_max','_informational','_informational_seconds')


def jobs_for(block):
    if block=='main':
        return [(t,sd,'C3') for sd in SEEDS for t in TARGETS]+[(t,SEEDS[0],'C1') for t in TARGETS]+[(t,sd,'T3') for sd in SEEDS for t in TARGETS]
    if block=='smoke':return [(t,SMOKE_SEED,a) for t in ('SJ','KR') for a in ('C1','T3')]
    raise ValueError(block)


def key(j):return f'{j[0]}:{j[1]}:{j[2]}'


def _strip(x):
    if isinstance(x,dict):return {k:_strip(v) for k,v in x.items() if not (k=='wall' or k.endswith(WALL_SUFFIXES))}
    if isinstance(x,list):return [_strip(v) for v in x]
    return x


def canon(rec):
    """Record without wall fields and the arm name (GDET compares these)."""
    return {k:v for k,v in _strip(rec).items() if k!='arm'}


def pack(digits):
    s=''.join(map(str,digits)).encode();return {'z':base64.b64encode(zlib.compress(s,9)).decode(),'len':len(s),'sha256':hashlib.sha256(s).hexdigest()}


def unpack(p):
    s=zlib.decompress(base64.b64decode(p['z'])).decode();check(len(s)==p['len'] and hashlib.sha256(s.encode()).hexdigest()==p['sha256'],'pack');return [int(c) for c in s]


def _code(r):return 2*r[0]+r[1]


def _t_run(tg,N,seed,acts,reads,feed=None):
    c=B32T.Baseline32T(tg.read(),tg.k,N,READ_BITS,seed=seed,step_cap=STEP_CAP);w=c.propose()
    while w is not None:
        for a in w:
            r=tg.act(a);c.observe(a,r);acts.append(a);reads.append(_code(r))
            if feed:feed(a,_code(r))
        w=c.next()
    R=c.record()
    return {'api':R['api'],'api_label':R['label'],'n':R.get('n'),'transitions':R.get('transitions'),'emissions':R.get('emissions'),
            'origin_step':R.get('origin_step'),'sigma':R.get('sigma'),'h':R['h'],'h_history':R['h_history'],'restarts':R['restarts'],
            'queries':R['queries'],'step_cap':STEP_CAP}


def run_fresh(name,seed,arm):
    tg=TG.Target(name);N=NS[NKEY[arm]][name];acts=[];reads=[_code(tg.read())];t0=time.perf_counter()
    if arm.startswith('C'):
        c=C34H.Certifier34H(tg.read(),tg.k,N,read_bits=READ_BITS,seed=seed,batch_steps=1,K=K_STEPS,conflict_cap=CONFLICT_CAP,budget_conflicts=BUDGET,
                             wall_guard_case_s=WALL_GUARD_CASE_S)
        try:
            while True:
                w=c.propose()
                if w is None:break
                for a in w:r=tg.act(a);c.observe(a,r);acts.append(a);reads.append(_code(r))
            R=c.result();T,E=H32._norm(R['model']) if R.get('model') else (None,None)
            out={'api':R['api'],'api_label':R['label'],'stop':R['stop'],'n_min':R['n_min'],'model_T':T,'model_E':E,'s1':R['s1'],
                 'rounds':R['rounds'],'conflicts':R['conflicts'],'capped':R['capped'],'batches':c.batches,'K':K_STEPS,
                 'wall_guard_case_s':WALL_GUARD_CASE_S,'wall_guard':R.get('wall_guard')}
        finally:c.close()
    else:out=_t_run(tg,N,seed,acts,reads)
    check(tg.steps==len(acts),'step accounting')
    rec={'target':name,'block':BLOCK_OF[name],'codec':tg.codec,'bytes':list(tg.bs),'seed':seed,'arm':arm,'N':N,'python':sys.version,
         'decoder_calls':tg.steps,'decoder_objects':tg.decoder_objects,'resets':0,'actions':pack(acts),'readings':pack(reads),
         'killed':False,'rlimit_as_bytes':RLIMIT_AS,'workers':WORKERS,'job_kill_s':JOB_KILL_S,'job_wall_informational':time.perf_counter()-t0}
    rec.update(out);return rec


def kill_record(j,wall,why='timeout',cap_hit=False):
    return {'target':j[0],'block':BLOCK_OF[j[0]],'seed':j[1],'arm':j[2],'N':NS[NKEY[j[2]]][j[0]],'api_label':'KILL','killed':True,
            'kill_reason':why,'cap_hit':cap_hit,'rlimit_as_bytes':RLIMIT_AS,'workers':WORKERS,'job_kill_s':JOB_KILL_S,
            'wall_guard_case_s':WALL_GUARD_CASE_S if j[2].startswith('C') else None,'job_wall_informational':wall}


def _child(j,path):
    try:
        try:
            with open('/proc/self/oom_score_adj','w') as fh:fh.write('1000')
        except OSError:pass
        resource.setrlimit(resource.RLIMIT_AS,(RLIMIT_AS,RLIMIT_AS))
        c=run_fresh(*j);tmp=path+'.part'
        with open(tmp,'w') as fh:json.dump(c,fh)
        os.replace(tmp,path);os._exit(0)
    except MemoryError as e:
        try:
            with open(path+'.mem','w') as fh:fh.write(repr(e))
        except Exception:pass
        os._exit(4)
    except BaseException as e:
        try:
            with open(path+'.err','w') as fh:fh.write(repr(e))
        except Exception:pass
        os._exit(3)


def run_jobs(jobs,log,t_start,cap,jobs_dir):
    jobs_dir=Path(jobs_dir);jobs_dir.mkdir(parents=True,exist_ok=True)
    ctx=mp.get_context('fork');alive={};q=list(jobs);done={};errors=[];n=0
    while (q or alive) and time.perf_counter()-t_start<cap:
        while q and len(alive)<WORKERS:
            j=q.pop(0);path=str(jobs_dir/(key(j).replace(':','_')+'.json'))
            p=ctx.Process(target=_child,args=(j,path));p.start();alive[key(j)]=(j,p,path,time.perf_counter())
        time.sleep(POLL_S)
        for k_,(j,p,path,t0) in list(alive.items()):
            wall=time.perf_counter()-t0
            if p.exitcode is None and wall<JOB_KILL_S:continue
            if p.exitcode is None:os.kill(p.pid,signal.SIGKILL);p.join();c=kill_record(j,wall)
            else:
                p.join()
                if p.exitcode==4 or (p.exitcode is not None and p.exitcode<0):
                    c=kill_record(j,wall,'memory_cap' if p.exitcode==4 else f'signal {-p.exitcode}',cap_hit=p.exitcode==4)
                elif p.exitcode!=0 or not os.path.exists(path):
                    e=open(path+'.err').read() if os.path.exists(path+'.err') else f'exit {p.exitcode}';errors.append([k_,e]);del alive[k_]
                    log(f'ERROR {k_} {e}');continue
                else:
                    with open(path) as fh:c=json.load(fh)
            done[k_]=c;del alive[k_];n+=1
            log(f'done {n}/{len(jobs)} {k_} {c["job_wall_informational"]:.1f}s {c["api_label"]} N={c["N"]} steps={c.get("decoder_calls")}')
    for k_,(j,p,path,t0) in alive.items():os.kill(p.pid,signal.SIGKILL);p.join()
    # recover any finished files left if parent died mid-join (reboot-survivable)
    for j in jobs:
        k_=key(j);path=jobs_dir/(k_.replace(':','_')+'.json')
        if k_ not in done and path.exists():
            with open(path) as fh:done[k_]=json.load(fh)
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
    done,errors=run_jobs(jobs,log,t0,MAIN_CAP_S,output/'jobs')
    keys=[key(j) for j in jobs];missing=[k for k in keys if k not in done]
    res={'schema':SCHEMA,'study':plan['study'],'block':block,'complete':not missing and not errors,'job_keys':keys,'missing_job_keys':missing,
         'errors':errors,'records':[done[k] for k in keys if k in done],'N':NS,'read_bits':READ_BITS,'K_steps':K_STEPS,'conflict_cap':CONFLICT_CAP,
         'budget_conflicts':BUDGET,'rlimit_as_bytes':RLIMIT_AS,'batch_steps':BATCH,'step_cap':STEP_CAP,'job_kill_s':JOB_KILL_S,'main_cap_s':MAIN_CAP_S,
         'wall_guard_case_s':WALL_GUARD_CASE_S,'workers':WORKERS,
         'resets':0,'total_elapsed_informational':time.perf_counter()-t0}
    write_new(output/'RESULTS.json',res)
    write_new(output/'SEAL.json',{'study':plan['study'],'block':block,'results_sha256':sha(output/'RESULTS.json'),'plan_sha256':sha(PLAN),
              'freeze_sha256':sha(FREEZE) if block=='main' else None,'complete':res['complete'],'job_count':len(keys),'records':len(done)})
    return res


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--block',choices=('main','smoke'),default='main');ap.add_argument('--output')
    a=ap.parse_args();out=a.output or str(STUDY_DIR/a.block)
    if a.block!='main':check(not Path(out).resolve().is_relative_to(STUDY_DIR.resolve()),'smoke output outside results/study-076')
    r=run(out,a.block);print('done complete=',r['complete'])
