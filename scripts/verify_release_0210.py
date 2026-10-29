"""Brute v0.21.0 release verification (BRUTE_PLAN_024). New file; verify_release_0200(_r1) and earlier stay frozen.

Same hardening as verify_release_0200 (frozen helpers of verify_release_060 reused): every JSON artifact of results/study-024
(recursive; raw RESULTS/SCIENTIFIC excepted, bound by the block SEALs and their committed .json.gz by MANIFEST) plus
RELEASE.json is parsed first and its required key checked; any other exception becomes VerificationError.

Process order (plan release_gates.verifier_self_test, lesson of #113): the chain is read from experiments/COMMIT_ORDER_024.json
(bound by the source freeze), then the implementation commits not already listed there, then source freeze -> scoring
freeze -> seal -> HEAD. Each link must be an ancestor of the next. A commit may appear twice only when the commit-order
file and implementation_commits name the same hash (it is then listed once, never compared with itself).
process_chain() is pure (no git) so tests/test_release_0210 unit-tests it against the real source freeze.

  python scripts/verify_release_0210.py         # short
  python scripts/verify_release_0210.py --long  # + GLV: 12 main cases re-run from scratch (6 processes), compared to the sealed
                                                 #   SCIENTIFIC cases (timing stripped) and audited by v0210_reference; 900 s cap
"""
from __future__ import annotations
import argparse,json,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common import VerificationError,check,sha,dumps
from scripts.verify_release_060 import read_bytes_,jload,req,_guard,_freeze,manifest_ok
from scripts.verify_release_0200 import PREVIOUS_FREEZES as PF0200

STUDY='results/study-024'
RAW=('RESULTS.json','SCIENTIFIC.json')
REQUIRED_KEYS={'SEAL.json':'files_sha256','transfer/SEAL.json':'block','repro/reproset/SEAL.json':'block',
               'RUN_DONE_024.json':'elapsed_s','RUN_STATE_024.json':'events','PROGRESS_024.json':'streams','PROGRESS_G11_024.json':'cases_done','STOP_024.json':'fired_at','STOP_024_ORCHESTRATOR.json':'stopped_at',
               'CLEAN_CLONE_024.json':'passed','LAUNCH_024.json':'pids','LIVE_REFUSAL_024.json':'exit_code'}
RELEASE_KEYS=('version','preregistration','preregistration_commit','source_freeze','source_freeze_commit','release_freeze',
              'scoring_scripts_commit','seal_commit','results_dir','gates_passed','gates_failed','GLS','G_PROC','G_RT','G_HB','GTI_release_statement','api')
PREVIOUS_FREEZES=PF0200+('experiments/BRUTE_SOURCE_FREEZE_023.json','experiments/BRUTE_RELEASE_FREEZE_0200.json','experiments/BRUTE_RELEASE_FREEZE_0200_R1.json')
SCORING=('scripts/make_gates_024.py','scripts/make_paired_024.py','scripts/make_reproducibility_024.py','scripts/clean_clone_024.py',
         'scripts/clean_clone_024_gitclone.py','scripts/early_window_024.py','scripts/host_pause_probe_024.py','tests/test_scoring_024.py')
LEDGER_ORDER=('preregistration_024','build_authorization_024','seedcheck_024','source_freeze_024','scoring_freeze_024','run_start_024','seal_024','gates_024')
LONG_CAP=900
FAMILIES=('cycle3','switch3','unaliased2','ood4')


def long_cases(plan):
    R=plan['heldout_ranges']['targets'];E=(0.0,0.01,0.02);out=[]
    for f in FAMILIES:
        lo=R[f][0];out+=[('main',f,lo+i,E[i]) for i in range(3)]
    return out


def _one(x):
    from experiments import brute_study_024 as BS,v0210_reference as R
    from experiments.brute_common import load
    from scripts.make_reproducibility_024 import _canon
    j,sealed=x;plan=load(ROOT/'experiments/BRUTE_PLAN_024.json');_,c=BS.run_job(tuple(j),plan)
    if _canon(c)!=_canon(sealed):return {'case':BS.key(tuple(j)),'stage':'rerun'}
    ok,msg=R.audit_case(sealed,plan)
    return None if ok else {'case':BS.key(tuple(j)),'stage':'reference','first_difference':str(msg)[:200]}


def study_artifacts(root):
    s=Path(root)/STUDY
    return sorted(p for p in s.rglob('*.json') if p.name not in RAW and '.partial' not in p.name and 'CHECKPOINT' not in p.name)


def required_key(root,p):
    p=Path(p);root=Path(root)
    if p==root/'RELEASE.json':return 'version'
    return REQUIRED_KEYS.get(p.relative_to(root/STUDY).as_posix(),'schema')


def parse_all(root):
    out={}
    for p in study_artifacts(root)+[Path(root)/'RELEASE.json']:
        o=jload(p);req(o,required_key(root,p),str(p.relative_to(root)));out[str(p.relative_to(root))]=o
    for k in RELEASE_KEYS:req(out['RELEASE.json'],k,'RELEASE.json')
    return out


def ledger_order(receipts,root='.'):
    ev=[req(r,'event','ledger') for r in receipts]
    for e in LEDGER_ORDER:check(e in ev,'ledger lacks '+e)
    idx=[ev.index(e) for e in LEDGER_ORDER];check(idx==sorted(idx),'ledger study-024 chronology')
    rs=max(i for i,e in enumerate(ev) if e=='run_start_024')
    end=[i for i,e in enumerate(ev) if e in ('run_end_024','stop_024') and i>rs]
    check(end and end[0]<max(i for i,e in enumerate(ev) if e=='seal_024'),'ledger lacks run_end_024/stop_024 between the held-out run_start and seal')
    from datetime import datetime
    def t(r):
        try:return datetime.fromisoformat(r['note'].split()[0])
        except (ValueError,IndexError,KeyError):raise VerificationError('ledger note without ISO time: '+r['event']) from None
    sf=t([r for r in receipts if r['event']=='scoring_freeze_024'][-1]);st=t(receipts[rs])
    check((st-sf).total_seconds()>=600,'scoring scripts ledgered < 10 min before run_start')
    return {'scoring_freeze_024':sf.isoformat(),'run_start_024':st.isoformat(),'gap_s':(st-sf).total_seconds()}


def process_chain(freeze,commit_order,rel):
    """Pure: the ordered (name, commit) chain the git check walks. Raises VerificationError on a malformed input."""
    check(freeze.get('commit_order_sha256') is not None,'source freeze lacks commit_order_sha256')
    co=sorted(req(commit_order,'commits','commit order'),key=lambda c:c['order'])
    check([c['order'] for c in co]==list(range(len(co))),'commit order is not 0..n-1')
    check(co and co[0]['event'].startswith('preregistration'),'commit order does not start at the preregistration')
    check(rel['preregistration_commit'] in (co[0]['short'],co[0]['commit']),'RELEASE.json preregistration_commit differs from the commit-order file')
    chain=[(c['event'],c['short']) for c in co];seen={c['short'] for c in co}|{c['commit'] for c in co}
    chain+=[(f'implementation_{i}',c) for i,c in enumerate(req(freeze,'implementation_commits','freeze')) if c not in seen]
    chain+=[('source_freeze',rel['source_freeze_commit']),('scoring_scripts',rel['scoring_scripts_commit']),('seal',rel['seal_commit'])]
    names=[c for _,c in chain];check(len(set(names))==len(names),'a commit appears twice in the process chain')
    return chain+[('head','HEAD')]


def git_order(root,rel):
    from scripts.verify_release_020 import _git
    def anc(a,b):return _git(root,'merge-base','--is-ancestor',a,b).returncode==0
    def same(a,b):return _git(root,'rev-parse',a).stdout==_git(root,'rev-parse',b).stdout
    check(_git(root,'rev-parse','--git-dir').returncode==0,'not a git checkout')
    fr=jload(root/rel['source_freeze']);co_p=root/'experiments/COMMIT_ORDER_024.json'
    check(sha(co_p)==fr.get('commit_order_sha256'),'COMMIT_ORDER_024.json differs from the source freeze')
    chain=process_chain(fr,jload(co_p),rel)
    for (na,a),(nb,b) in zip(chain,chain[1:]):
        check(anc(a,b),f'{na} {a} is not an ancestor of {nb} {b}')
        if b!='HEAD':check(not same(a,b),f'{na} and {nb} are the same commit')
    plan=_git(root,'show',f"{rel['preregistration_commit']}:{rel['preregistration']}")
    check(plan.returncode==0 and plan.stdout==(root/rel['preregistration']).read_text(),'plan changed after pre-registration')
    for f in SCORING:
        b=_git(root,'show',f"{rel['scoring_scripts_commit']}:{f}");check(b.returncode==0 and b.stdout==(root/f).read_text(),f'{f} changed after the scoring freeze')
    return {n:c for n,c in chain if c!='HEAD'}


def long_verify(root,cap=LONG_CAP):
    """GLV: re-run LONG_CASES from scratch (frozen runner) and compare to the sealed cases; then the second implementation."""
    from experiments import brute_study_024 as BS
    from experiments.brute_common import load
    from scripts.make_reproducibility_024 import _key
    from concurrent.futures import ProcessPoolExecutor,TimeoutError as FT
    plan=load(ROOT/'experiments/BRUTE_PLAN_024.json');L=long_cases(plan)
    sci=jload(Path(root)/STUDY/'transfer/SCIENTIFIC.json')
    M={_key(c):c for c in req(sci,'cases','SCIENTIFIC')}
    K=[BS.key(j) for j in L]
    check(all(k in M for k in K) and len(L)==12,f'long_verify sample: {sum(k in M for k in K)}/{len(L)} sealed cases (12 required)')
    t0=time.time()
    with ProcessPoolExecutor(6) as ex:
        futs=[ex.submit(_one,(j,M[k])) for j,k in zip(L,K)]
        try:bad=[r for f in futs for r in [f.result(timeout=max(1,cap-(time.time()-t0)))] if r]
        except FT:
            for p in ex._processes.values():p.kill()
            raise VerificationError(f'long_verify exceeded its {cap} s cap') from None
    wall=time.time()-t0;check(wall<=cap,f'long_verify exceeded its {cap} s cap')
    check(not bad,f'long_verify: {len(bad)} mismatching cases, first {bad[:1]}')
    return {'cases':len(L),'case_list':K,'mismatching_cases':0,'wall_s':round(wall,1),'cap_s':cap,'passed':True}


def api_check():
    """GAPI10 at release: brute.certify/10 (default 'stitched'; 'lr' == certify9, 'anytime' == certify9 anytime) plus the frozen
    v0.20.0 check of brute.certify/9 .. /1."""
    from scripts.verify_release_0200 import api_check as api9
    from scripts.make_gates_024 import api10_probe
    from brute.api import certify10 as A10
    carried=api9();p=api10_probe()
    check(p.get('error') is None,f"brute.certify/10 probe error: {p.get('error')}")
    check(p['api']=='brute.certify/10' and A10.API=='brute.certify/10','brute.certify/10 API name')
    check(p['methods']==['stitched','lr','anytime'] and p['default_method']=='stitched' and p['default_answer_method']=='stitched','brute.certify/10 METHODS/default')
    check(p['lr_equals_certify9'] and p['anytime_equals_certify9_anytime'],"brute.certify/10 method='lr'/'anytime' differ from certify9")
    for bad in (dict(method='x'),dict(delta=0)):
        try:A10.certify10((0,1),[0,1],[(0,1),(1,None)],**bad);raise VerificationError(f'certify10 accepted {bad}')
        except ValueError:pass
    return {'interface':'brute.certify/10','methods':p['methods'],'default':p['default_method'],
            'carried':[carried['interface']]+carried['carried'],'probe':{'soundness':p['soundness_stitched']}}


def _verify(root,git,long=False):
    out={'schema':'brute.verify-release.v21_0','mode':'long' if long else 'short'}
    arts=parse_all(root);rel=arts['RELEASE.json'];out['artifacts_parsed']=len(arts)
    out['manifest_files']=manifest_ok(root)
    from brute.release_version_0210 import RELEASE_VERSION
    check(rel['version']==RELEASE_VERSION,'RELEASE.json version differs from brute.release_version_0210')
    import tomllib
    try:pv=tomllib.loads(read_bytes_(root/'pyproject.toml').decode())['project']['version']
    except (ValueError,KeyError) as e:raise VerificationError(f'pyproject.toml: {e}') from None
    check(pv==RELEASE_VERSION,'pyproject version differs')
    out['locked_files']={f:_freeze(root,f) for f in PREVIOUS_FREEZES+(rel['source_freeze'],rel['release_freeze'])}
    for d in ('results/study-001','results/study-002','results/study-003'):
        seal=jload(root/d/'SEAL.json');check(sha(root/d/'SCIENTIFIC.json')==req(seal,'scientific_sha256',d),d+' SCIENTIFIC does not match SEAL')
    for d,mod in (('results/study-004','study004_storage'),('results/study-005','study005_storage'),('results/study-006','study006_storage'),
                  ('results/study-007','study007_storage')):
        seal=jload(root/d/'SEAL.json');__import__('scripts.'+mod,fromlist=['ensure_raw']).ensure_raw(root/d)
        for n,k in (('RESULTS.json','results_sha256'),('SCIENTIFIC.json','scientific_sha256')):check(sha(root/d/n)==req(seal,k,d),f'{d}/{n} does not match SEAL')
    for n in ('008','009','010','011','012','013','014','015','016','017','018','019','020','021','023'):__import__(f'scripts.study{n}_storage',fromlist=['ensure_raw']).ensure_raw(root/f'results/study-{n}')
    check(rel['results_dir']==STUDY,'results_dir');s=root/STUDY
    from scripts.study024_storage import ensure_raw;ensure_raw(s)
    top=arts[f'{STUDY}/SEAL.json']
    for f,d in req(top,'files_sha256','study SEAL').items():
        p=s/f
        if p.exists():check(sha(p)==d,f'study-024 {f} does not match the study SEAL')
        else:check('CHECKPOINT' in f or f.startswith('logs/') or f in ('RUN_024.log',),f'study-024 sealed file {f} is missing (only checkpoints and logs may be absent)')
    for sub in ('transfer','repro/reproset'):
        if not (s/sub/'SEAL.json').exists():continue
        S=arts[f'{STUDY}/{sub}/SEAL.json']
        for n,k in (('RESULTS.json','results_sha256'),('SCIENTIFIC.json','scientific_sha256')):check(sha(s/sub/n)==req(S,k,sub),f'study-024 {sub}/{n} does not match its SEAL')
    from scripts import make_paired_024,make_reproducibility_024,make_gates_024
    for mod,name in ((make_paired_024,'PAIRED_ANALYSIS_024.json'),(make_reproducibility_024,'REPRODUCIBILITY_024.json'),(make_gates_024,'GATES_024.json')):
        if (s/name).exists() or name=='GATES_024.json':
            check(read_bytes_(s/name)==dumps(mod.build(s)),f'study-024 {name} does not regenerate byte-for-byte')
    gates=arts[f'{STUDY}/GATES_024.json']
    from scripts.verify_release_020 import ledger_020
    receipts,sup=ledger_020(root,git);out['ledger_receipts']=len(receipts);out['ledger_superseded']=sup
    out['run_chronology']=ledger_order(receipts,root)
    sources={r['source'] for r in receipts}
    for need in (rel['source_freeze'],f'{STUDY}/SEAL.json',f'{STUDY}/GATES_024.json'):check(need in sources,'ledger lacks '+need)
    if git:out['process_order']=git_order(root,rel)
    out['gates_passed']=gates['passed'];out['gates_failed']=gates['failed'];out['gates_pending']=gates['pending']
    check(rel['gates_passed']==gates['passed'] and rel['gates_failed']==gates['failed'],'RELEASE.json gate lists differ from GATES_024.json')
    for k in ('GLS','G_PROC','G_RT','G_HB'):
        check(rel[k]==gates.get(k),f'RELEASE.json {k} differs from GATES_024.json');out[k]=gates.get(k)
    out['stop_rule_fired']=gates.get('stop_rule_fired')
    out['api']=api_check();check(rel['api']==out['api']['interface'],'RELEASE.json api differs from brute.api.certify10')
    if long:out['GLV_long_verify']=long_verify(root)
    out['status']='passed'
    out['validity']='bounded deterministic Moore worlds (<= 4 states, 2 actions, 2 bits); noisy observations (eps <= 0.02 main, 0.05 stress) on 88-step traces with the stitched likelihood-ratio bound (RGL5) against the frozen RGL4 and the planned-B margin (RGNB4), pre-registered in BRUTE_PLAN_024; brute.certify/10 smoke-checked; not general intelligence'
    return out


def verify(root=ROOT,fast=True,git=True,long=False):
    return _guard(lambda r,g:_verify(r,g,long),Path(root),git)


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--long',action='store_true',help='GLV: re-run 12 main cases and audit them (900 s cap)')
    ap.add_argument('--fast',action='store_true',help='accepted for symmetry; the default short mode');a=ap.parse_args()
    try:print(json.dumps(verify(long=a.long),indent=2))
    except VerificationError as e:print('VERIFICATION FAILED:',e);sys.exit(1)
