"""Durable checkpoint pusher for study-038 (plan 038; as 037; deviation #126 item 5, reused through #146 and by #148). New file.
Host-side process, separate from the runner and from the core API. Every PERIOD seconds, while the runner PID is alive,
it copies results/study-038/main/CHECKPOINT.jsonl (complete lines only) into a deterministic gzip at
results/study-038/snapshots/ckpt_snapshot.jsonl.gz, commits only that path and pushes the branch without force
(env -u GITHUB_TOKEN -u GH_TOKEN). It never edits the checkpoint, never relaunches the runner and stops when the runner
exits (after one final snapshot). Log: results/study-038/snapshots/PUSH_LOG.txt (informational).
  python scripts/push_checkpoint_038.py --pid PID [--period 300]"""
from __future__ import annotations
import argparse,gzip,io,os,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
CKPT=ROOT/'results/study-038/main/CHECKPOINT.jsonl'
SNAP=ROOT/'results/study-038/snapshots/ckpt_snapshot.jsonl.gz'
LOG=SNAP.parent/'PUSH_LOG.txt'
ENV={k:v for k,v in os.environ.items() if k not in ('GITHUB_TOKEN','GH_TOKEN')}


def complete_lines(data):
    i=data.rfind(b'\n');return data[:i+1] if i>=0 else b''


def gz(data):
    buf=io.BytesIO()
    with gzip.GzipFile(filename='',mode='wb',compresslevel=9,fileobj=buf,mtime=0) as f:f.write(data)
    return buf.getvalue()


def alive(pid):
    try:os.kill(pid,0);return True
    except OSError:return False


def git(*a):return subprocess.run(['git','-C',str(ROOT),*a],env=ENV,capture_output=True,text=True,timeout=120)


def snapshot(n,log):
    data=complete_lines(CKPT.read_bytes()) if CKPT.exists() else b'';z=gz(data);cases=data.count(b'\n')
    if SNAP.exists() and SNAP.read_bytes()==z:return False
    SNAP.parent.mkdir(parents=True,exist_ok=True);tmp=SNAP.with_suffix('.partial');tmp.write_bytes(z);tmp.replace(SNAP)
    git('add','-f',str(SNAP.relative_to(ROOT)))
    r=git('commit','-q','-m',f'study-038 checkpoint snapshot {n} ({cases} cases)','--',str(SNAP.relative_to(ROOT)))
    p=git('push','-q','-u','origin','HEAD')
    log(f'{time.strftime("%Y-%m-%dT%H:%M:%S%z")} snapshot {n} cases {cases} commit_rc {r.returncode} push_rc {p.returncode} {p.stderr.strip()[-120:]}')
    return True


def main(argv=None):
    ap=argparse.ArgumentParser();ap.add_argument('--pid',type=int,required=True);ap.add_argument('--period',type=float,default=300.0);a=ap.parse_args(argv)
    LOG.parent.mkdir(parents=True,exist_ok=True)
    def log(m):
        with open(LOG,'a') as f:f.write(m+'\n')
    n=0;log(f'{time.strftime("%Y-%m-%dT%H:%M:%S%z")} start pid {a.pid} period {a.period}')
    while alive(a.pid):
        t=time.time()
        while alive(a.pid) and time.time()-t<a.period:time.sleep(2)
        n+=1;snapshot(n,log)
    log(f'{time.strftime("%Y-%m-%dT%H:%M:%S%z")} runner exited; final snapshot taken');return 0


if __name__=='__main__':sys.exit(main())
