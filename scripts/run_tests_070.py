"""GTI test isolation runner (BRUTE_PLAN_009 GTI_test_isolation).

Runs every tests/test*.py module (sorted) in its OWN fresh interpreter (one subprocess per module, `python -m unittest
discover -s tests -p <file>` semantics: same loader, start dir tests/, top-level dir tests/), with the pinned venv, and the
plain `python -m unittest discover -s tests` run alongside (non-gated report; the order dependence of test_study_005 is
isolated, not removed). Writes results/study-009/TEST_SUITE_009.json (refuses to overwrite).

Verdict clauses (i)-(v) as in the plan. Subtest failures are reported under their parent test id.
(iv) frozen files: every file listed in an experiments/*FREEZE*.json must match the digest of the NEWEST freeze listing it,
where a freeze's 'supersedes' field replaces the superseded freeze (BRUTE_RELEASE_FREEZE_060_R1 supersedes
BRUTE_RELEASE_FREEZE_060 for scripts/verify_release_060.py, D26 of v0.6.0), plus the adopted_files digests.
K_060 rule: only evaluated if a test_release_060 test fails; then the same per-module runner is run on a clean git
worktree of tag v0.6.0 and recorded.
"""
from __future__ import annotations
import argparse,glob,hashlib,json,os,subprocess,sys,tempfile,time,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PLAN=ROOT/'experiments/BRUTE_PLAN_009.json'
OUT=ROOT/'results/study-009/TEST_SUITE_009.json'
NEW_TESTS=('test_seeds_009.py','test_syncevent.py','test_planner.py','test_v070_reference.py','test_run_tests_070.py','test_release_070.py')
K060_ALLOWED={'test_release_060.Release060.test_version_consistent','test_release_060.Release060.test_fast_verify_passes',
              'test_release_060.Release060.test_untampered_copy_passes'}
CHILD_TIMEOUT=3600


class _Rec(unittest.TextTestResult):
    def __init__(self,*a,**k):
        super().__init__(*a,**k);self.rec={}
    def _set(self,t,v,msg=None):
        tid=t.id()
        if self.rec.get(tid,('ok',))[0] in ('fail','error') and v=='ok':return
        self.rec[tid]=(v,msg)
    def addSuccess(self,t):super().addSuccess(t);self._set(t,'ok')
    def addFailure(self,t,e):super().addFailure(t,e);self._set(t,'fail',self._exc_info_to_string(e,t)[-600:])
    def addError(self,t,e):
        super().addError(t,e)
        tid=getattr(t,'id',lambda:str(t))();self.rec[tid]=('error',self._exc_info_to_string(e,t)[-600:])
    def addSkip(self,t,r):super().addSkip(t,r);self._set(t,'skip',str(r))
    def addExpectedFailure(self,t,e):super().addExpectedFailure(t,e);self._set(t,'ok','expected failure')
    def addUnexpectedSuccess(self,t):super().addUnexpectedSuccess(t);self._set(t,'fail','unexpected success')
    def addSubTest(self,t,st,e):
        super().addSubTest(t,st,e)
        if e is not None:
            kind='fail' if issubclass(e[0],t.failureException) else 'error'
            self.rec[t.id()]=(kind,('subtest %s: '%st._subDescription())+self._exc_info_to_string(e,t)[-500:])


def child(pattern,out):
    """Run one discover (pattern) in THIS interpreter and write {id: [outcome, msg]} + counts to `out`."""
    sys.path.insert(0,str(ROOT/'tests'));os.chdir(ROOT)
    suite=unittest.TestLoader().discover('tests',pattern=pattern)
    with open(os.devnull,'w') as dn:
        so=sys.stdout;sys.stdout=dn
        try:
            r=unittest.TextTestRunner(stream=dn,resultclass=_Rec,verbosity=0).run(suite)
        finally:sys.stdout=so
    Path(out).write_text(json.dumps({'tests_run':r.testsRun,'skipped':sorted(t.id() for t,_ in r.skipped),
                                     'results':{k:list(v) for k,v in sorted(r.rec.items())}},sort_keys=True))


def run_child(pattern,root=ROOT,python=sys.executable):
    with tempfile.NamedTemporaryFile(suffix='.json',delete=False) as f:tmp=f.name
    env=dict(os.environ,PYTHONPATH=str(root));t0=time.time()
    p=subprocess.run([python,str(root/'scripts/run_tests_070.py'),'--child',pattern,'--child-out',tmp],cwd=root,env=env,
                     capture_output=True,text=True,timeout=CHILD_TIMEOUT)
    try:d=json.loads(Path(tmp).read_text())
    except Exception:d={'tests_run':0,'skipped':[],'results':{f'{pattern}::<module>':['error',(p.stderr or '')[-800:]]}}
    os.unlink(tmp);d['returncode']=p.returncode;d['wall_informational']=round(time.time()-t0,1);return d


def per_module(root=ROOT,python=sys.executable,modules=None):
    mods=modules or sorted(Path(x).name for x in glob.glob(str(root/'tests/test*.py')))
    return {m:run_child(m,root,python) for m in mods}


def frozen_check(root=ROOT):
    freezes={Path(f).name:json.loads(Path(f).read_text()) for f in sorted(glob.glob(str(root/'experiments/*FREEZE*.json')))}
    sup={Path(d['supersedes']).name for d in freezes.values() if d.get('supersedes')}
    newest={}
    for name,d in freezes.items():          # live freezes first
        if name in sup:continue
        for rel,h in d.get('sha256_files',{}).items():newest.setdefault(rel,(h,name))
    for name,d in freezes.items():          # superseded freezes only for files no live freeze lists
        if name not in sup:continue
        for rel,h in d.get('sha256_files',{}).items():newest.setdefault(rel,(h,name))
    plan=json.loads(PLAN.read_text())
    for rel,h in plan['adopted_files']['files'].items():newest[rel]=(h,'BRUTE_PLAN_009.adopted_files')
    bad=[]
    for rel,(h,src) in sorted(newest.items()):
        p=root/rel;cur=hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None
        if cur!=h:bad.append({'file':rel,'freeze':src,'expected':h,'actual':cur})
    return {'files_checked':len(newest),'changed':bad,'superseded_freezes':sorted(sup)}


def k060_clean(python=sys.executable):
    """Run tests/test_release_060.py with the same per-module runner on a clean worktree of tag v0.6.0."""
    tmp=Path(tempfile.mkdtemp(prefix='v060wt-'))/'wt'
    subprocess.run(['git','worktree','add','--detach',str(tmp),'v0.6.0'],cwd=ROOT,check=True,capture_output=True)
    try:
        # the v0.6.0 tree has no run_tests_070.py: copy this runner in (a runner, not a tested file)
        (tmp/'scripts/run_tests_070.py').write_text(Path(__file__).read_text())
        return run_child('test_release_060.py',tmp,python)
    finally:subprocess.run(['git','worktree','remove','--force',str(tmp)],cwd=ROOT,capture_output=True)


def verdict(mods,plain,frozen,plan,k060=None):
    K=set(plan['criteria']['GTI_test_isolation']['known_failing_allowed'])
    failing={tid:v for d in mods.values() for tid,v in d['results'].items() if v[0] in ('fail','error')}
    r060={t for t in failing if t.startswith('test_release_060.')}
    k060_ok=bool(r060) and r060<=K060_ALLOWED and k060 is not None and \
        all(k060['results'].get(t,['missing'])[0]=='ok' for t in r060)
    undeclared=sorted(t for t in failing if t not in K and not (t in r060 and k060_ok))
    s5={t:v[0] for t,v in mods.get('test_study_005.py',{'results':{}})['results'].items()}
    run_total=sum(d['tests_run'] for d in mods.values());skipped=sorted(t for d in mods.values() for t in d['skipped'])
    new_bad=sorted(t for m in NEW_TESTS for t,v in mods.get(m,{'results':{m+'::<missing>':['error','module missing']}})['results'].items() if v[0]!='ok' and v[0]!='skip')
    missing_new=[m for m in NEW_TESTS if m not in mods]
    c={'i_only_declared_failures':not undeclared,
       'ii_test_study_005_six_pass':len(s5)==6 and all(v=='ok' for v in s5.values()),
       'iii_counts_match_plain':run_total==plain['tests_run'] and skipped==sorted(plain['skipped']),
       'iv_frozen_unchanged':not frozen['changed'],
       'v_new_tests_pass':not new_bad and not missing_new}
    return {'clauses':c,'passed':all(c.values()),'undeclared_failures':undeclared,'failing':sorted(failing),
            'test_study_005':s5,'tests_run_per_module_total':run_total,'tests_run_plain':plain['tests_run'],
            'skipped_per_module':skipped,'skipped_plain':sorted(plain['skipped']),'new_test_failures':new_bad,
            'new_test_modules_missing':missing_new,'k060_failures':sorted(r060),'k060_rule_applied':k060_ok}


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--child');ap.add_argument('--child-out')
    ap.add_argument('--output',default=str(OUT));ap.add_argument('--modules',help='comma list (dev only; not a GTI run)')
    a=ap.parse_args()
    if a.child:child(a.child,a.child_out);return
    out=Path(a.output)
    if out.exists():raise SystemExit(f'refusing to overwrite {out}')
    plan=json.loads(PLAN.read_text());t0=time.time()
    head=subprocess.run(['git','rev-parse','HEAD'],cwd=ROOT,capture_output=True,text=True).stdout.strip()
    dirty=subprocess.run(['git','status','--porcelain','--untracked-files=no'],cwd=ROOT,capture_output=True,text=True).stdout.strip()
    mods=per_module(modules=a.modules.split(',') if a.modules else None)
    plain=run_child('test*.py')
    frozen=frozen_check()
    failing060=[t for d in mods.values() for t,v in d['results'].items() if t.startswith('test_release_060.') and v[0] in ('fail','error')]
    k060=k060_clean() if failing060 else None
    V=verdict(mods,plain,frozen,plan,k060)
    rep={'schema':'brute.test-suite.v1','study':plan['study'],'gate':'GTI_test_isolation','python':sys.version.split()[0],
         'executable':sys.executable,'head':head,'tracked_tree_dirty':bool(dirty),'modules_subset':a.modules,
         'per_module':mods,'plain_discover':{k:v for k,v in plain.items()},'frozen_files':frozen,'k060_clean_v060_run':k060,
         'verdict':V,'wall_informational':round(time.time()-t0,1)}
    out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(rep,indent=1,sort_keys=True)+'\n')
    print(json.dumps({'passed':V['passed'],'clauses':V['clauses'],'undeclared':V['undeclared_failures'],
                      'run':V['tests_run_per_module_total'],'plain':V['tests_run_plain']},indent=1))


if __name__=='__main__':main()
