"""Study BRUTE-0730-RESUME-077 runner (experiments/BRUTE_PLAN_077.json). New file.
Same arms as study 076 on experiments/targets_077.py: C = brute.certify/34h with wall_guard_case_s=JOB_KILL_S=900;
T = brute.baseline/32t. Seeds 12770101/12770102. Per-job JSON under output/jobs/.
RESUME-SAFE: on start, load any existing jobs/*.json into done and skip those keys; never re-run a finished key.
If the parent dies mid-run, the orchestrator may be started ONCE more on the same output dir (no RESULTS/SEAL yet) to finish missing keys only.
Main cap applies per invocation; run_jobs only schedules missing keys.
  PYTHONPATH=. python experiments/brute_study_077.py --block main
  PYTHONPATH=. python experiments/brute_study_077.py --block smoke --output /tmp/x"""
from __future__ import annotations
import argparse,base64,hashlib,json,os,resource,signal,sys,time,zlib
import multiprocessing as mp
from pathlib import Path
from experiments.brute_common import check,sha,load,write_new
from experiments import targets_077 as TG
from brute.api import certify34h as C34H
from brute.api import certify32h as H32
from brute.api import baseline32t as B32T

ROOT=Path(__file__).resolve().parents[1]
PLAN=ROOT/'experiments/BRUTE_PLAN_077.json';FREEZE=ROOT/'experiments/BRUTE_SOURCE_FREEZE_077.json';STUDY_DIR=ROOT/'results/study-077'
READ_BITS=2;K_STEPS=40000;RLIMIT_AS=int(2.0*(1<<30));CONFLICT_CAP=50000;BUDGET=50000000;BATCH=1;STEP_CAP=3000000
NS={'plus1':{'SJ':4,'KR':5,'B5':6,'U32':8,'U8S':10,'U16B':10,'EJ4':12,'HK':6,'HZ':11,'JO':5},'plus3':{'SJ':6,'KR':7,'B5':8,'U32':10,'U8S':12,'U16B':12,'EJ4':14,'HK':8,'HZ':13,'JO':7}}
NKEY={'C1':'plus1','C3':'plus3','T3':'plus3'}
BLOCK_OF={t:'main' for t in ('SJ','KR','B5','U32','U8S','U16B','EJ4','HK')};BLOCK_OF['HZ']='heldout';BLOCK_OF['JO']='heldout'
WORKERS=3;JOB_KILL_S=900.0;MAIN_CAP_S=4800.0;POLL_S=0.5;WALL_GUARD_CASE_S=JOB_KILL_S
TARGETS=tuple(TG.TARGETS);SEEDS=(12770101,12770102);SMOKE_SEED=12770301
SCHEMA='brute.study.v77'
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


def load_existing(jobs_dir, keys):
    done={};jobs_dir=Path(jobs_dir)
    if not jobs_dir.exists():return done
    for k in keys:
        path=jobs_dir/(k.replace(':','_')+'.json')
        if path.exists():
            with open(path) as fh:done[k]=json.load(fh)
    return done


def run_jobs(jobs,log,t_start,cap,jobs_dir,done):
    jobs_dir=Path(jobs_dir);jobs_dir.mkdir(parents=True,exist_ok=True)
    ctx=mp.get_context('fork');alive={};q=[j for j in jobs if key(j) not in done];errors=[];n=len(done)
    if n:log(f'resume skip {n} finished keys; remaining {len(q)}')
    while (q or alive) and time.perf_counter()-t_start<cap:
        while q and len(alive)<WORKERS:
            j=q.pop(0);path=str(jobs_dir/(key(j).replace(':','_')+'.json'))
            if os.path.exists(path):  # another writer / prior finish
                with open(path) as fh:done[key(j)]=json.load(fh);n=len(done);continue
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
    for k_,(j,p,path,t0) in alive.items():
        os.kill(p.pid,signal.SIGKILL);p.join()
        # do not invent kill records for still-running on cap if file appeared
        if os.path.exists(path) and k_ not in done:
            with open(path) as fh:done[k_]=json.load(fh)
    return done,errors


def run(output,block):
    output=Path(output);plan=load(PLAN)
    if block=='main':
        check(FREEZE.exists(),'source freeze missing');fz=load(FREEZE)
        for rel,d in fz['sha256_files'].items():check(sha(ROOT/rel)==d,'freeze mismatch '+rel)
    for nm in ('RESULTS.json','SEAL.json'):check(not (output/nm).exists(),'refusing overwrite')
    output.mkdir(parents=True,exist_ok=True);jobs=jobs_for(block);keys=[key(j) for j in jobs]
    jobs_dir=output/'jobs'
    prior=load_existing(jobs_dir,keys)
    resume_count=1 if prior else 0
    missing_at_resume=sorted(k for k in keys if k not in prior) if prior else []
    # invoke counter file (at most one resume)
    inv=output/'ORCHESTRATOR_INVOCATIONS.json'
    if inv.exists():
        inv_d=json.loads(inv.read_text());inv_d['count']=inv_d.get('count',0)+1
    else:
        inv_d={'count':1,'study':plan['study'],'block':block}
    check(inv_d['count']<=2,'refusing more than one resume (2 invocations max)');inv.write_text(json.dumps(inv_d,sort_keys=True)+'\n')
    if inv_d['count']==2:check(bool(prior),'second invocation requires prior jobs/')
    t0=time.perf_counter()
    logf=open(output/'run.log','a')
    def log(s):print(s,flush=True);logf.write(time.strftime('%H:%M:%S ')+s+'\n');logf.flush()
    log(f'orchestrator invocation {inv_d["count"]} resume_count_flag={resume_count} prior={len(prior)}')
    done,errors=run_jobs(jobs,log,t0,MAIN_CAP_S,jobs_dir,dict(prior))
    # reload all jobs from disk (source of truth)
    done=load_existing(jobs_dir,keys)
    missing=[k for k in keys if k not in done]
    res={'schema':SCHEMA,'study':plan['study'],'block':block,'complete':not missing and not errors,'job_keys':keys,'missing_job_keys':missing,
         'errors':errors,'records':[done[k] for k in keys if k in done],'N':NS,'read_bits':READ_BITS,'K_steps':K_STEPS,'conflict_cap':CONFLICT_CAP,
         'budget_conflicts':BUDGET,'rlimit_as_bytes':RLIMIT_AS,'batch_steps':BATCH,'step_cap':STEP_CAP,'job_kill_s':JOB_KILL_S,'main_cap_s':MAIN_CAP_S,
         'wall_guard_case_s':WALL_GUARD_CASE_S,'workers':WORKERS,'resets':0,
         'resume_count':resume_count,'orchestrator_invocations':inv_d['count'],'missing_at_resume':missing_at_resume,
         'total_elapsed_informational':time.perf_counter()-t0}
    write_new(output/'RESULTS.json',res)
    write_new(output/'SEAL.json',{'study':plan['study'],'block':block,'results_sha256':sha(output/'RESULTS.json'),'plan_sha256':sha(PLAN),
              'freeze_sha256':sha(FREEZE) if block=='main' else None,'complete':res['complete'],'job_count':len(keys),'records':len(done)})
    return res


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--block',choices=('main','smoke'),default='main');ap.add_argument('--output')
    a=ap.parse_args();out=a.output or str(STUDY_DIR/a.block)
    if a.block!='main':check(not Path(out).resolve().is_relative_to(STUDY_DIR.resolve()),'smoke output outside results/study-077')
    r=run(out,a.block);print('done complete=',r['complete'],'resume_count=',r['resume_count'],'invocations=',r['orchestrator_invocations'])
