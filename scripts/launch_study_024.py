"""Held-out launcher for study BRUTE-0210-STITCHED-LR-024 (BRUTE_PLAN_024 G_PROC a). The only sanctioned way to start the
held-out run. It REFUSES (exit 3, nothing started) if SMOKE or any dry-run hook (BRUTE_SMOKE_DRILL, CAP_S, BUDGET_S, LIMIT,
SKIP_GTI) or ANY environment variable whose name starts with STUDY_DIR_ is set (lesson of K_0200 / #111: a stale hook
redirected a study directory). It also refuses if results/study-024/RUN_T0 is missing, or if the orchestrator, watchdog or
sentinel already has a live RUN_STATE (never relaunches a live run).

When clean, it starts three detached sessions (setsid + nohup semantics: new session, stdin /dev/null, output appended to
a log) from a scrubbed environment (os.environ minus the refused names; PYTHONPATH = repo root):
    scripts/run_study_024.py   > results/study-024/RUN_024.log
    scripts/watchdog_024.py    > results/study-024/WATCHDOG_024.log
    scripts/hbsentinel_024.py  > results/study-024/HB_SENTINEL_024.log
and writes results/study-024/LAUNCH_024.json (refuses to overwrite) with the pids, the refused-name check and the time.
    $PY scripts/launch_study_024.py [--check-only]
"""
from __future__ import annotations
import argparse,json,os,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
STUDY=ROOT/'results/study-024'
PY=os.environ.get('PY','/workspace/bgr/venv/bin/python')
HOOKS=('SMOKE','BRUTE_SMOKE_DRILL','CAP_S','BUDGET_S','LIMIT','SKIP_GTI')
CHILDREN=(('scripts/run_study_024.py','RUN_024.log'),('scripts/watchdog_024.py','WATCHDOG_024.log'),('scripts/hbsentinel_024.py','HB_SENTINEL_024.log'))


def refused(env):
    """Names that make the launcher refuse: every dry-run hook, and every STUDY_DIR_* name (any study number)."""
    return sorted(k for k in env if k in HOOKS or k.startswith('STUDY_DIR_'))


def clean_env(env):
    e={k:v for k,v in env.items() if k not in HOOKS and not k.startswith('STUDY_DIR_')};e['PYTHONPATH']=str(ROOT);e['PY']=PY;return e


def _alive(pid):
    try:os.kill(int(pid),0);return True
    except (ProcessLookupError,ValueError,TypeError):return False
    except PermissionError:return True


def live_run(d=STUDY):
    st=d/'RUN_STATE_024.json'
    if not st.exists():return None
    try:pid=json.loads(st.read_text()).get('orchestrator_pid')
    except ValueError:return 'unreadable RUN_STATE_024.json'
    return f'orchestrator pid {pid} alive' if pid and _alive(pid) else None


def preflight(env,d=STUDY):
    bad=refused(env)
    if bad:return f'refusing: dry-run hook(s) set: {bad}'
    if not (d/'RUN_T0').exists():return 'refusing: RUN_T0 missing (ledger run_start_024 first)'
    lr=live_run(d)
    if lr:return 'refusing: '+lr
    if (d/'LAUNCH_024.json').exists():return 'refusing: LAUNCH_024.json exists (resume by hand per the frozen resume rule, never a second launch)'
    return None


def launch(d=STUDY):
    env=clean_env(os.environ);pids={}
    for script,log in CHILDREN:
        with open(d/log,'a') as out,open(os.devnull) as nul:
            p=subprocess.Popen(['nohup',PY,script],cwd=ROOT,env=env,stdin=nul,stdout=out,stderr=subprocess.STDOUT,start_new_session=True)
        pids[script]=p.pid
        if script.endswith('run_study_024.py'):time.sleep(1)
    rec={'schema':'brute.launch-024.v1','launched_at':time.strftime('%Y-%m-%dT%H:%M:%S%z'),'epoch':time.time(),'pids':pids,
         'refused_names_present':[],'run_t0':(d/'RUN_T0').read_text().split()[0],'study_dir':str(d.resolve()),'python':PY}
    p=d/'LAUNCH_024.json'
    if p.exists():raise SystemExit('LAUNCH_024.json appeared during launch')
    p.write_text(json.dumps(rec,indent=1,sort_keys=True)+'\n');return rec


def main(argv=None):
    ap=argparse.ArgumentParser();ap.add_argument('--check-only',action='store_true');a=ap.parse_args(argv)
    why=preflight(os.environ)
    if why:print(why,flush=True);return 3
    if a.check_only:print('preflight ok (nothing started)');return 0
    print(json.dumps(launch()),flush=True);return 0


if __name__=='__main__':sys.exit(main())
