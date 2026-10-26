"""GTI test isolation runner for study-011 (BRUTE_PLAN_011 GTI_test_isolation): the run_tests_070 method.

Every tests/test*.py module (sorted) in its OWN fresh interpreter (the frozen scripts/run_tests_070.py child runner,
imported unchanged), with the pinned venv, plus the plain `unittest discover -s tests` run. Writes
results/study-011/TEST_SUITE_011.json (refuses to overwrite).
New v0.9.0 tests = tests/test*.py absent from tag v0.8.0. Known failures: the 14 study-009 K_frozen ids
(BRUTE_PLAN_009 criteria.GTI_test_isolation.known_failing_allowed, as plan 011 GTI says). Frozen files: every file of an experiments/*FREEZE*.json
(newest live freeze wins, superseded freezes only for files no live freeze lists) plus the study-009 adopted files.
K_060 / K_070 rules: a listed test_release_060 / test_release_070 failure is allowed only if the same test passes on a
clean worktree of tag v0.6.0 / v0.7.0 with the same runner (recorded).
"""
from __future__ import annotations
import argparse,glob,hashlib,json,subprocess,sys,tempfile,time
from pathlib import Path
from scripts import run_tests_070 as T

ROOT=Path(__file__).resolve().parents[1]
PLAN=ROOT/'experiments/BRUTE_PLAN_011.json'
PLAN009=ROOT/'experiments/BRUTE_PLAN_009.json'
OUT=ROOT/'results/study-011/TEST_SUITE_011.json'
K_ALLOWED={'060':{f'test_release_060.Release060.{t}' for t in ('test_version_consistent','test_fast_verify_passes','test_untampered_copy_passes')},
           '070':{f'test_release_070.Release070.{t}' for t in ('test_version_consistent','test_fast_verify_passes','test_untampered_copy_passes')}}


def new_tests(root=ROOT):
    old=set(subprocess.run(['git','ls-tree','--name-only','v0.8.0','tests/'],cwd=root,capture_output=True,text=True,check=True).stdout.split())
    return tuple(sorted(Path(x).name for x in glob.glob(str(root/'tests/test*.py')) if 'tests/'+Path(x).name not in old))
NEW_TESTS=new_tests()


def frozen_check(root=ROOT):
    freezes={Path(f).name:json.loads(Path(f).read_text()) for f in sorted(glob.glob(str(root/'experiments/*FREEZE*.json')))}
    sup={Path(d['supersedes']).name for d in freezes.values() if d.get('supersedes')}
    newest={}
    for live in (True,False):
        for name,d in freezes.items():
            if (name in sup)==live:continue
            for rel,h in d.get('sha256_files',{}).items():newest.setdefault(rel,(h,name))
    for rel,h in json.loads(PLAN009.read_text())['adopted_files']['files'].items():newest[rel]=(h,'BRUTE_PLAN_009.adopted_files')
    bad=[]
    for rel,(h,src) in sorted(newest.items()):
        p=root/rel;cur=hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None
        if cur!=h:bad.append({'file':rel,'freeze':src,'expected':h,'actual':cur})
    return {'files_checked':len(newest),'changed':bad,'superseded_freezes':sorted(sup)}


def clean_run(tag,module,python=sys.executable):
    """Run tests/<module> with the same per-module runner on a clean worktree of `tag`."""
    tmp=Path(tempfile.mkdtemp(prefix=f'{tag}wt-'))/'wt'
    subprocess.run(['git','worktree','add','--detach',str(tmp),tag],cwd=ROOT,check=True,capture_output=True)
    try:
        if not (tmp/'scripts/run_tests_070.py').exists():(tmp/'scripts/run_tests_070.py').write_text((ROOT/'scripts/run_tests_070.py').read_text())
        return T.run_child(module,tmp,python)
    finally:subprocess.run(['git','worktree','remove','--force',str(tmp)],cwd=ROOT,capture_output=True)


def verdict(mods,plain,frozen,plan,clean=None,new_tests=None):
    """clean = {'060': run_child result or None, '070': ...}."""
    clean=clean or {};new_tests=NEW_TESTS if new_tests is None else new_tests
    K=set(json.loads(PLAN009.read_text())['criteria']['GTI_test_isolation']['known_failing_allowed'])
    failing={tid:v for d in mods.values() for tid,v in d['results'].items() if v[0] in ('fail','error')}
    allowed_k=set();rule={}
    for v,A in K_ALLOWED.items():
        rv={t for t in failing if t.startswith(f'test_release_{v}.')};c=clean.get(v)
        ok=bool(rv) and rv<=A and c is not None and all(c['results'].get(t,['missing'])[0]=='ok' for t in rv)
        rule[v]={'failures':sorted(rv),'applied':ok}
        if ok:allowed_k|=rv
    undeclared=sorted(t for t in failing if t not in K and t not in allowed_k)
    s5={t:v[0] for t,v in mods.get('test_study_005.py',{'results':{}})['results'].items()}
    run_total=sum(d['tests_run'] for d in mods.values());skipped=sorted(t for d in mods.values() for t in d['skipped'])
    new_bad=sorted(t for m in new_tests for t,v in mods.get(m,{'results':{}})['results'].items() if v[0] not in ('ok','skip'))
    missing_new=[m for m in new_tests if m not in mods]
    c={'i_only_declared_failures':not undeclared,
       'ii_test_study_005_six_pass':len(s5)==6 and all(v=='ok' for v in s5.values()),
       'iii_counts_match_plain':run_total==plain['tests_run'] and skipped==sorted(plain['skipped']),
       'iv_frozen_unchanged':not frozen['changed'],
       'v_new_tests_pass':not new_bad and not missing_new}
    return {'clauses':c,'passed':all(c.values()),'undeclared_failures':undeclared,'failing':sorted(failing),
            'test_study_005':s5,'tests_run_per_module_total':run_total,'tests_run_plain':plain['tests_run'],
            'skipped_per_module':skipped,'skipped_plain':sorted(plain['skipped']),'new_tests':list(new_tests),
            'new_test_failures':new_bad,'new_test_modules_missing':missing_new,'k_rules':rule}


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',default=str(OUT));ap.add_argument('--modules',help='comma list (dev only; not a GTI run)')
    a=ap.parse_args();out=Path(a.output)
    if out.exists():raise SystemExit(f'refusing to overwrite {out}')
    plan=json.loads(PLAN.read_text());t0=time.time()
    head=subprocess.run(['git','rev-parse','HEAD'],cwd=ROOT,capture_output=True,text=True).stdout.strip()
    dirty=subprocess.run(['git','status','--porcelain','--untracked-files=no'],cwd=ROOT,capture_output=True,text=True).stdout.strip()
    mods=T.per_module(modules=a.modules.split(',') if a.modules else None)
    plain=T.run_child('test*.py');frozen=frozen_check();clean={}
    for v,tag in (('060','v0.6.0'),('070','v0.7.0')):
        f=[t for d in mods.values() for t,r in d['results'].items() if t.startswith(f'test_release_{v}.') and r[0] in ('fail','error')]
        clean[v]=clean_run(tag,f'test_release_{v}.py') if f else None
    V=verdict(mods,plain,frozen,plan,clean)
    rep={'schema':'brute.test-suite.v2','study':plan['study'],'gate':'GTI_test_isolation','python':sys.version.split()[0],
         'executable':sys.executable,'head':head,'tracked_tree_dirty':bool(dirty),'modules_subset':a.modules,
         'per_module':mods,'plain_discover':plain,'frozen_files':frozen,'clean_tag_runs':clean,
         'verdict':V,'wall_informational':round(time.time()-t0,1)}
    out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(rep,indent=1,sort_keys=True)+'\n')
    print(json.dumps({'passed':V['passed'],'clauses':V['clauses'],'undeclared':V['undeclared_failures'],
                      'run':V['tests_run_per_module_total'],'plain':V['tests_run_plain']},indent=1))


if __name__=='__main__':main()
