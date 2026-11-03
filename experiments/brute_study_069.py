"""Study BRUTE-0650-RESETDECODER-069 runner (experiments/BRUTE_PLAN_069.json). New file; drives the new brute.certify/32r through its
public interface on the real decoders of experiments/targets_069.py, with a reset (fresh decoder object) before every query word.
Never imports the ground truth. Arms: C clean; S injected iid bit noise eps 0.30 (eps_bar 0.35, delta 0.001; worlds_065.Noise
seeded by the job seed); Sb = S on U3 seed 12690101. Declared N 12 (EJ 16), read_bits 2, query cap 400000 words.
One forked process per job (at most 7), SIGKILL at 1200 s -> KILL record; 3600 s main cap.
  PYTHONPATH=. python experiments/brute_study_069.py --block main
  PYTHONPATH=. python experiments/brute_study_069.py --block smoke --output /tmp/x"""
from __future__ import annotations
import argparse,hashlib,json,os,random,signal,sys,tempfile,time
import multiprocessing as mp
from pathlib import Path
from experiments.brute_common import check,sha,load,dumps,write_new
from experiments import worlds_065 as W65
from experiments import targets_069 as TG
from brute.api import certify20s as C20S
from brute.api import certify20n as C20N
from brute.api import certify32r as C32R

ROOT=Path(__file__).resolve().parents[1]
PLAN=ROOT/'experiments/BRUTE_PLAN_069.json';FREEZE=ROOT/'experiments/BRUTE_SOURCE_FREEZE_069.json';STUDY_DIR=ROOT/'results/study-069'
QCAP=400000;READ_BITS=2;EPS=0.30;EPS_BAR=0.35;DELTA=0.001;FID_SAMPLE=200
NS={'U3':12,'U4':12,'W16':12,'EJ':16,'GB':12};BLOCK_OF={'U3':'main','U4':'main','W16':'main','EJ':'stretch','GB':'heldout'}
WORKERS=7;JOB_KILL_S=1200.0;MAIN_CAP_S=3600.0;POLL_S=0.5
TARGETS=('U3','U4','W16','EJ','GB');SEEDS=(12690101,12690102,12690103);SMOKE_SEED=12690301;ARMS=('C','S')
SCHEMA='brute.study.v65_0'
WALL_SUFFIXES=('_wall','_walls','_wall_max','_informational','_informational_seconds')
CANON_DROP=('arm','eps','eps_bar','delta','reads_total','reads_max','fixed_reads_total','settled_bit_errors','settled_obs_errors',
            'noise_draws','readings_sha256','reads_per_obs_sha256')


def jobs_for(block):
    if block=='main':return [(t,s,a) for t in TARGETS for a in ARMS for s in SEEDS]+[('U3',SEEDS[0],'Sb')]
    if block=='smoke':return [(t,SMOKE_SEED,a) for t in TARGETS for a in ARMS]
    raise ValueError(block)


def key(j):return f'{j[0]}:{j[1]}:{j[2]}'


def _strip(x):
    if isinstance(x,dict):return {k:_strip(v) for k,v in x.items() if not (k=='wall' or k.endswith(WALL_SUFFIXES))}
    if isinstance(x,list):return [_strip(v) for v in x]
    return x


def canon(rec):
    """Record without wall fields and without noise-only fields (GEQ69 / GDET69 compare these)."""
    return {k:v for k,v in _strip(rec).items() if k not in CANON_DROP}


def _bits(code):return [(code>>(READ_BITS-1-i))&1 for i in range(READ_BITS)]


def run_fresh(name,seed,arm):
    noisy=arm in ('S','Sb');tg=TG.Target(name);N=NS[name];nz=W65.Noise(seed,EPS);err=[0,0];raw=[]
    c=C32R.Certifier32R(tg.k,N,READ_BITS,*((EPS_BAR,DELTA) if noisy else (None,None)),seed=seed,query_cap=QCAP)
    clean={};t0=time.perf_counter()
    while True:
        w=c.propose()
        if w is None:break
        tg.reset()
        for i in range(len(w)+1):
            if i>0:tg.act(w[i-1])
            p=w[:i]
            if not c.wants(p):continue
            cl=tg.read();clean[p]=list(cl)
            if noisy:
                rs=[nz.read(cl)]
                while c.more(rs):rs.append(nz.read(cl))
                raw.append(rs)
            else:rs=[cl]
            c.take(p,rs)
            if noisy:
                e=sum(1 for x,y in zip(_bits(c.tree[p]),cl) if x!=y);err[0]+=e;err[1]+=e>0
    R=c.record();tree=R.pop('tree');check(len(tree)==len(clean)==R['tree_nodes'],'tree accounting')
    words=sorted(clean);rng=random.Random(seed*69+690);sample=words if len(words)<=FID_SAMPLE else rng.sample(words,FID_SAMPLE)
    rec={'target':name,'block':BLOCK_OF[name],'codec':tg.codec,'bytes':list(tg.bs),'seed':seed,'arm':arm,'N':N,'python':sys.version,
         'api':R['api'],'api_label':R['label'],'n':R.get('n'),'transitions':R.get('transitions'),'emissions':R.get('emissions'),
         'queries':R['queries'],'tree_nodes':R['tree_nodes'],'rounds':R['rounds'],'counterexamples':R['counterexamples'],'S':R['S'],'E':R['E'],
         'suite_words_checked':R['suite_words_checked'],'decoder_calls':tg.steps,'decoder_objects':tg.resets,'query_cap':QCAP,
         'tree_sha256':hashlib.sha256(json.dumps(tree,separators=(',',':')).encode()).hexdigest(),
         'fid_sample':[[list(p),clean[p]] for p in sample],'killed':False,'job_wall_informational':time.perf_counter()-t0}
    if noisy:
        T=len(raw);rpo=[len(r) for r in raw]
        rec.update(eps=EPS,eps_bar=EPS_BAR,delta=DELTA,reads_total=sum(rpo),reads_max=max(rpo),
                   fixed_reads_total=sum(C20N.reads_for(t,EPS_BAR,DELTA,READ_BITS) for t in range(1,T+1)),settled_bit_errors=err[0],
                   settled_obs_errors=err[1],noise_draws=nz.draws,reads_per_obs_sha256=hashlib.sha256(json.dumps(rpo).encode()).hexdigest(),
                   readings_sha256=hashlib.sha256(json.dumps(raw,separators=(',',':')).encode()).hexdigest())
    return rec


def kill_record(j,wall):
    return {'target':j[0],'block':BLOCK_OF[j[0]],'seed':j[1],'arm':j[2],'N':NS[j[0]],'api_label':'KILL','n':None,'killed':True,
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
    tmpd=tempfile.mkdtemp(prefix='brute069_');ctx=mp.get_context('fork');alive={};q=list(jobs);done={};errors=[];n=0
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
            log(f'done {n}/{len(jobs)} {k_} {c["job_wall_informational"]:.1f}s {c["api_label"]} n={c["n"]} q={c.get("queries")} reads={c.get("reads_total")} err={c.get("settled_bit_errors")}')
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
         'errors':errors,'records':[done[k] for k in keys if k in done],'query_cap':QCAP,'N':NS,'read_bits':READ_BITS,
         'eps':EPS,'eps_bar':EPS_BAR,'delta':DELTA,'job_kill_s':JOB_KILL_S,'main_cap_s':MAIN_CAP_S,'workers':WORKERS,
         'total_elapsed_informational':time.perf_counter()-t0}
    write_new(output/'RESULTS.json',res)
    write_new(output/'SEAL.json',{'study':plan['study'],'block':block,'results_sha256':sha(output/'RESULTS.json'),'plan_sha256':sha(PLAN),
              'freeze_sha256':sha(FREEZE) if block=='main' else None,'complete':res['complete'],'job_count':len(keys),'records':len(done)})
    return res


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--block',choices=('main','smoke'),default='main');ap.add_argument('--output')
    a=ap.parse_args();out=a.output or str(STUDY_DIR/a.block)
    if a.block!='main':check(not Path(out).resolve().is_relative_to(STUDY_DIR.resolve()),'smoke output outside results/study-069')
    r=run(out,a.block);print('done complete=',r['complete'])
