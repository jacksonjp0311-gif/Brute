"""Study BRUTE-0640-REALDECODER-068 runner (experiments/BRUTE_PLAN_068.json). New file; drives the frozen brute.certify/32p and
brute.certify/32s through their public interface on the real decoders of experiments/targets_068.py. Never imports the ground truth.
Arms: C certify/32p clean; S certify/32s eps 0.30 (eps_bar 0.35, delta 0.001; worlds_065.Noise injected per reading); Sb = S on U3
seed 12680101. Declared N 12, read_bits 2, C 50000, B 8000000, K 400, node cap 200000. Prefix: 40 actions random.Random(seed*68+680).
One forked process per job (at most 7), SIGKILL at 600 s -> KILL record; 2400 s main cap.
  PYTHONPATH=. python experiments/brute_study_068.py --block main
  PYTHONPATH=. python experiments/brute_study_068.py --block smoke --output /tmp/x"""
from __future__ import annotations
import argparse,hashlib,json,os,random,signal,sys,tempfile,time
import multiprocessing as mp
from pathlib import Path
from experiments.brute_common import check,sha,load,dumps,write_new
from experiments import worlds_065 as W65
from experiments import targets_068 as TG
from brute.api import certify20b as C20B
from brute.api import certify20s as C20S
from brute.api import certify20n as C20N
from brute.api import certify32p as C32P
from brute.api import certify32s as C32S
from brute.scalesearch4 import SOLVER4

ROOT=Path(__file__).resolve().parents[1]
PLAN=ROOT/'experiments/BRUTE_PLAN_068.json';FREEZE=ROOT/'experiments/BRUTE_SOURCE_FREEZE_068.json';STUDY_DIR=ROOT/'results/study-068'
C68=50000;B68=8000000;K68=400;NODE_CAP=200000;N68=12;READ_BITS=2;EPS=0.30;EPS_BAR=0.35;DELTA=0.001;PREFIX=40
WORKERS=7;JOB_KILL_S=600.0;MAIN_CAP_S=2400.0;POLL_S=0.5;HARD_KILL_S=1800.0;GUARD_CALL_S=30.0
TARGETS=('U3','U4','W16');SEEDS=(12680101,12680102,12680103);SMOKE_SEED=12680301;ARMS=('C','S')
NOISE_KEYS=('reads_per_obs','thresholds','settle_at','eps_bar','delta')
SCHEMA='brute.study.v64_0'
WALL_SUFFIXES=('_wall','_walls','_wall_max','_informational','_informational_seconds')


def prefix(seed):
    rng=random.Random(seed*68+680);return [rng.randrange(3) for _ in range(PREFIX)]


def jobs_for(block):
    if block=='main':return [(t,s,a) for t in TARGETS for a in ARMS for s in SEEDS]+[('U3',SEEDS[0],'Sb')]
    if block=='smoke':return [(t,SMOKE_SEED,a) for t in TARGETS for a in ARMS]
    raise ValueError(block)


def key(j):return f'{j[0]}:{j[1]}:{j[2]}'


def _strip(x):
    """Drop wall-clock fields: key 'wall' or any key ending _wall, _walls, _wall_max, _informational, _informational_seconds."""
    if isinstance(x,dict):return {k:_strip(v) for k,v in x.items() if not (k=='wall' or k.endswith(WALL_SUFFIXES))}
    if isinstance(x,list):return [_strip(v) for v in x]
    return x


def inner_of(R):
    return {k:v for k,v in _strip(R).items() if k not in NOISE_KEYS}


def run_fresh(name,seed,arm,budget=B68):
    noisy=arm in ('S','Sb');tg=TG.Target(name);acts=prefix(seed);clean=[tg.read()];raw=[];nz=W65.Noise(seed,EPS);err=[0,0]
    kw=dict(max_chunks=None,K=K68,conflict_cap=C68,budget_conflicts=budget,wall_guard_case_s=HARD_KILL_S,wall_guard_call_s=GUARD_CALL_S,
            solver=SOLVER4,hook=None,factory=C20B.counted16d,node_cap=NODE_CAP)
    def noisy_reads(more):
        rs=[];cl=tg.read()
        while True:
            rs.append(nz.read(cl))
            if not more(rs):break
        raw.append([list(r) for r in rs]);return rs
    def tally(v):
        e=sum(1 for x,y in zip(v,tg.read()) if x!=y);err[0]+=e;err[1]+=e>0
    t0=time.perf_counter()
    if noisy:
        m1=C20S.threshold(1,EPS_BAR,DELTA,READ_BITS);first=noisy_reads(lambda rs:C20S.settle(rs,m1,READ_BITS)[0] is None)
        tally(C20S.settle(first,m1,READ_BITS)[0])
        c=C32S.Certifier32S(first,tg.k,N68,read_bits=READ_BITS,eps_bar=EPS_BAR,delta=DELTA,**kw)
        def obs(a):
            clean.append(tg.act(a));rs=noisy_reads(c.more);m=C20S.threshold(c.t+1,EPS_BAR,DELTA,READ_BITS);tally(C20S.settle(rs,m,READ_BITS)[0]);c.observe(a,rs)
    else:
        c=C32P.Certifier32P(tg.read(),tg.k,N68,'a16d',read_bits=READ_BITS,**kw)
        def obs(a):clean.append(tg.act(a));c.observe(a,tg.read())
    try:
        for a in acts:obs(a)
        while True:
            x=c.propose()
            if x is None:break
            for a in x:obs(a)
        R=c.record();res=c.result()
    finally:c.close()
    f=R['final'];check(R['acts'][:PREFIX]==acts and len(R['acts'])==tg.steps,'action accounting')
    check(res['family_bound']==N68 and R['budget_conflicts']==budget and R['conflict_cap']==C68,'caps not applied')
    rec={'target':name,'codec':tg.codec,'bytes':list(tg.bs),'seed':seed,'arm':arm,'N':N68,'python':sys.version,'api':res['api'],
         'stop':R['stop'],'api_label':res['label'],'n_min':f['n_min'],'model':f['model'],'s1':f['s1'],'acts':list(R['acts']),
         'clean_readings':[list(r) for r in clean],'used':R['used'],'conflicts_spent':R['conflicts_spent'],'decoder_calls':tg.steps,
         'inner_sha256':hashlib.sha256(dumps(inner_of(R))).hexdigest(),'killed':False,'job_wall_informational':time.perf_counter()-t0}
    if noisy:
        T=len(R['acts'])+1;check(len(R['reads_per_obs'])==T==len(raw),'observation count')
        rec.update(eps=EPS,eps_bar=EPS_BAR,delta=DELTA,reads_total=sum(R['reads_per_obs']),reads_max=max(R['reads_per_obs']),
                   fixed_reads_total=sum(C20N.reads_for(t,EPS_BAR,DELTA,READ_BITS) for t in range(1,T+1)),settled_bit_errors=err[0],
                   settled_obs_errors=err[1],noise_draws=nz.draws,readings_sha256=hashlib.sha256(json.dumps(raw,separators=(',',':')).encode()).hexdigest())
    return rec


def kill_record(j,wall):
    return {'target':j[0],'seed':j[1],'arm':j[2],'N':N68,'stop':'KILL','api_label':'KILL','n_min':None,'model':None,'s1':None,
            'killed':True,'job_kill_s':JOB_KILL_S,'job_wall_informational':wall}


def _child(j,path,budget):
    try:
        c=run_fresh(j[0],j[1],j[2],budget);tmp=path+'.part'
        with open(tmp,'w') as fh:json.dump(c,fh)
        os.replace(tmp,path);os._exit(0)
    except BaseException as e:
        try:
            with open(path+'.err','w') as fh:fh.write(repr(e))
        except Exception:pass
        os._exit(3)


def run_jobs(jobs,log,budget,t_start,cap):
    tmpd=tempfile.mkdtemp(prefix='brute068_');ctx=mp.get_context('fork');alive={};q=list(jobs);done={};errors=[];n=0
    while (q or alive) and time.perf_counter()-t_start<cap:
        while q and len(alive)<WORKERS:
            j=q.pop(0);path=os.path.join(tmpd,key(j).replace(':','_')+'.json')
            p=ctx.Process(target=_child,args=(j,path,budget));p.start();alive[key(j)]=(j,p,path,time.perf_counter())
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
            log(f'done {n}/{len(jobs)} {k_} {c["job_wall_informational"]:.1f}s {c["api_label"]}/{c["stop"]} n_min={c["n_min"]} reads={c.get("reads_total")} err={c.get("settled_bit_errors")}')
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
    done,errors=run_jobs(jobs,log,B68 if block=='main' else 2000000,t0,MAIN_CAP_S)
    keys=[key(j) for j in jobs];missing=[k for k in keys if k not in done]
    res={'schema':SCHEMA,'study':plan['study'],'block':block,'complete':not missing and not errors,'job_keys':keys,'missing_job_keys':missing,
         'errors':errors,'records':[done[k] for k in keys if k in done],'caps':[C68,B68,K68],'N':N68,'read_bits':READ_BITS,
         'eps':EPS,'eps_bar':EPS_BAR,'delta':DELTA,'prefix':PREFIX,'job_kill_s':JOB_KILL_S,'main_cap_s':MAIN_CAP_S,'workers':WORKERS,
         'total_elapsed_informational':time.perf_counter()-t0}
    write_new(output/'RESULTS.json',res)
    write_new(output/'SEAL.json',{'study':plan['study'],'block':block,'results_sha256':sha(output/'RESULTS.json'),'plan_sha256':sha(PLAN),
              'freeze_sha256':sha(FREEZE) if block=='main' else None,'complete':res['complete'],'job_count':len(keys),'records':len(done)})
    return res


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--block',choices=('main','smoke'),default='main');ap.add_argument('--output')
    a=ap.parse_args();out=a.output or str(STUDY_DIR/a.block)
    if a.block!='main':check(not Path(out).resolve().is_relative_to(STUDY_DIR.resolve()),'smoke output outside results/study-068')
    r=run(out,a.block);print('done complete=',r['complete'])
