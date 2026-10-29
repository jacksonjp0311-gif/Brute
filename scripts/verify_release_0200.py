"""Brute v0.20.0 release verification (BRUTE_PLAN_023). New file; verify_release_0190 and earlier stay frozen.

Same hardening as verify_release_0190 (frozen helpers of verify_release_060 reused): every JSON artifact of results/study-023
(recursive; raw RESULTS/SCIENTIFIC excepted, bound by the block SEALs and their committed .json.gz by MANIFEST) plus
RELEASE.json is parsed first and its required key checked; any other exception becomes VerificationError.

  python scripts/verify_release_0200.py         # short: seals, freezes, regenerated paired/repro/gates, ledger, manifest, git order
  python scripts/verify_release_0200.py --long  # + GLV: 12 main cases re-run from scratch (6 processes) and compared to the sealed
                                                 #   SCIENTIFIC cases (timing keys stripped), then audited by v0200_reference,
                                                 #   inside its own 900 s wall cap
LONG_CASES (plan release_gates.GLV_long_verify, 3 per family across eps 0 / 0.01 / 0.02): per family the first held-out
target at eps 0, the second at eps 0.01, the third at eps 0.02.
"""
from __future__ import annotations
import argparse,json,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common import VerificationError,check,sha,dumps
from scripts.verify_release_060 import read_bytes_,jload,req,_guard,_freeze,manifest_ok
from scripts.verify_release_0190 import PREVIOUS_FREEZES as PF0190

STUDY='results/study-023'
RAW=('RESULTS.json','SCIENTIFIC.json')
REQUIRED_KEYS={'SEAL.json':'files_sha256','transfer/SEAL.json':'block','repro/reproset/SEAL.json':'block',
               'RUN_DONE_023.json':'elapsed_s','RUN_STATE_023.json':'events','PROGRESS_023.json':'streams',
               'STOP_023.json':'fired_at','STOP_023_ORCHESTRATOR.json':'stopped_at','CLEAN_CLONE_023.json':'passed','HEARTBEAT_ATTRIBUTION_023.json':'schema',
               'PROGRESS_G11_023.json':'cases_done'}
RELEASE_KEYS=('version','preregistration','preregistration_commit','source_freeze','source_freeze_commit','release_freeze',
              'scoring_scripts_commit','seal_commit','results_dir','gates_passed','gates_failed','GLR','G_RT','G_HB','GTI_release_statement','api')
PREVIOUS_FREEZES=PF0190+('experiments/BRUTE_SOURCE_FREEZE_021.json','experiments/BRUTE_RELEASE_FREEZE_0190.json')
SCORING=('scripts/make_gates_023.py','scripts/make_paired_023.py','scripts/make_reproducibility_023.py','scripts/clean_clone_023.py','tests/test_scoring_023.py')
LEDGER_ORDER=('preregistration_023','seedcheck_023','source_freeze_023','scoring_freeze_023','run_start_023','seal_023','gates_023')
LONG_CAP=900
FAMILIES=('cycle3','switch3','unaliased2','ood4')


def long_cases(plan):
    R=plan['heldout_ranges']['targets'];E=(0.0,0.01,0.02);out=[]
    for f in FAMILIES:
        lo=R[f][0];out+=[('main',f,lo+i,E[i]) for i in range(3)]
    return out


def _one(x):
    from experiments import brute_study_023 as BS,v0200_reference as R
    from experiments.brute_common import load
    from scripts.make_reproducibility_023 import _canon
    j,sealed=x;plan=load(ROOT/'experiments/BRUTE_PLAN_023.json');_,c=BS.run_job(tuple(j),plan)
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
    idx=[ev.index(e) for e in LEDGER_ORDER];check(idx==sorted(idx),'ledger study-023 chronology')
    rs=max(i for i,e in enumerate(ev) if e=='run_start_023')
    end=[i for i,e in enumerate(ev) if e in ('run_end_023','stop_023') and i>rs]
    check(end and end[0]<max(i for i,e in enumerate(ev) if e=='seal_023'),'ledger lacks run_end_023/stop_023 between the held-out run_start and seal')
    from datetime import datetime
    def t(r):
        try:return datetime.fromisoformat(r['note'].split()[0])
        except (ValueError,IndexError,KeyError):raise VerificationError('ledger note without ISO time: '+r['event']) from None
    sf=t([r for r in receipts if r['event']=='scoring_freeze_023'][-1]);st=t(receipts[rs])
    check((st-sf).total_seconds()>=600,'scoring scripts ledgered < 10 min before run_start')
    return {'scoring_freeze_023':sf.isoformat(),'run_start_023':st.isoformat(),'gap_s':(st-sf).total_seconds()}


def git_order(root,rel):
    from scripts.verify_release_020 import _git
    def anc(a,b):return _git(root,'merge-base','--is-ancestor',a,b).returncode==0
    check(_git(root,'rev-parse','--git-dir').returncode==0,'not a git checkout')
    fr=jload(root/rel['source_freeze'])
    check(rel['preregistration_commit']==req(fr,'preregistration_commit','freeze'),'RELEASE.json preregistration_commit differs from the source freeze')
    chain=[('preregistration',fr['preregistration_commit']),('seedcheck',req(fr,'seedcheck_commit','freeze'))]
    chain+=[(f'reference_{i}',c) for i,c in enumerate(req(fr,'reference_commits','freeze'))]
    chain+=[(f'implementation_{i}',c) for i,c in enumerate(req(fr,'implementation_commits','freeze'))]
    chain+=[('source_freeze',rel['source_freeze_commit']),('seal',rel['seal_commit']),('head','HEAD')]
    for (na,a),(nb,b) in zip(chain,chain[1:]):
        check(anc(a,b),f'{na} {a} is not an ancestor of {nb} {b}')
        if b!='HEAD':check(_git(root,'rev-parse',a).stdout!=_git(root,'rev-parse',b).stdout,f'{na} and {nb} are the same commit')
    sc=rel['scoring_scripts_commit'];sf=rel['source_freeze_commit']
    for a,b,na,nb in ((sf,sc,'source_freeze','scoring_scripts'),(sc,rel['seal_commit'],'scoring_scripts','seal')):
        check(anc(a,b) and _git(root,'rev-parse',a).stdout!=_git(root,'rev-parse',b).stdout,f'{na} {a} is not a strict ancestor of {nb} {b}')
    chain.insert([n for n,_ in chain].index('seal'),('scoring_scripts',sc))
    plan=_git(root,'show',f"{rel['preregistration_commit']}:{rel['preregistration']}")
    check(plan.returncode==0 and plan.stdout==(root/rel['preregistration']).read_text(),'plan changed after pre-registration')
    for f in SCORING:
        b=_git(root,'show',f"{rel['scoring_scripts_commit']}:{f}");check(b.returncode==0 and b.stdout==(root/f).read_text(),f'{f} changed after the scoring freeze')
    return {n:c for n,c in chain if c!='HEAD'}


def long_verify(root,cap=LONG_CAP):
    """GLV: re-run LONG_CASES from scratch (frozen runner) and compare to the sealed cases; then the second implementation."""
    from experiments import brute_study_023 as BS
    from experiments.brute_common import load
    from scripts.make_reproducibility_023 import _key
    from concurrent.futures import ProcessPoolExecutor,TimeoutError as FT
    plan=load(ROOT/'experiments/BRUTE_PLAN_023.json');L=long_cases(plan)
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
    """GAPI10 at release: brute.certify/9 (method 'lr' default, 'anytime' = /8) and the carried brute.certify/8 .. /1 import and answer host-agnostically."""
    from brute.api import certify as A1,certify2 as A2,certify3 as A3,certify4 as A4,certify5 as A5,certify6 as A6,certify7 as A7,certify8 as A8,certify9 as A9
    for m,v in ((A1,1),(A2,2),(A3,3),(A4,4),(A5,5),(A6,6),(A7,7),(A8,8),(A9,9)):check(getattr(m,'API',None)==f'brute.certify/{v}',f'{m.__name__} API is not brute.certify/{v}')
    check(tuple(A9.METHODS)==('lr','anytime'),'brute.certify/9 METHODS')
    r8=A8.certify8((0,1),[0,1],[(0,1),(1,None)]);s8=r8.get('soundness') or {}
    check(r8.get('api')=='brute.certify/8' and s8.get('anytime') is True and s8.get('conditional_on')==A8.CONDITIONAL_ON,'brute.certify/8 probe answer malformed')
    r=A9.certify9((0,1),[0,1],[(0,1),(1,None)]);s=r.get('soundness') or {}
    check(r.get('api')=='brute.certify/9' and r.get('method')=='lr' and s.get('kind')=='probabilistic' and s.get('delta')==0.01 and s.get('anytime') is True
          and s.get('method')=='lr' and s.get('conditional_on')==A9.CONDITIONAL_ON,'brute.certify/9 probe answer malformed')
    check(len(r.get('certificates',[]))==3 and not any(any(x) for x in r['certificates']),'brute.certify/9 certified inside the burn-in')
    ra=A9.certify9((0,1),[0,1],[(0,1),(1,None)],method='anytime')
    check(ra['certificates']==r8['certificates'] and ra['m']==r8['m'],"brute.certify/9 method='anytime' differs from certify8")
    with A9.Certifier9((0,1)) as c:
        c.observe(0,(0,1));c.observe(1,(1,None));check(c.current()['certificates']==r['certificates'][-1],'Certifier9 streaming differs from certify9')
    for bad in (dict(family_bound=5),dict(burn_in=-1),dict(eps_bar=0.5),dict(delta=0),dict(num_actions=4),dict(method='x')):
        try:A9.certify9((0,1),[0,1],[(0,1),(1,None)],**bad);raise VerificationError(f'certify9 accepted {bad}')
        except ValueError:pass
    return {'interface':'brute.certify/9','methods':list(A9.METHODS),'carried':[f'brute.certify/{v}' for v in range(8,0,-1)],
            'probe':{'m':r['m'],'status':r['status'],'soundness':s}}


def _verify(root,git,long=False):
    out={'schema':'brute.verify-release.v20_0','mode':'long' if long else 'short'}
    arts=parse_all(root);rel=arts['RELEASE.json'];out['artifacts_parsed']=len(arts)
    out['manifest_files']=manifest_ok(root)
    from brute.release_version_0200 import RELEASE_VERSION
    check(rel['version']==RELEASE_VERSION,'RELEASE.json version differs from brute.release_version_0200')
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
    for n in ('008','009','010','011','012','013','014','015','016','017','018','019','020','021'):__import__(f'scripts.study{n}_storage',fromlist=['ensure_raw']).ensure_raw(root/f'results/study-{n}')
    check(rel['results_dir']==STUDY,'results_dir');s14=root/STUDY
    from scripts.study023_storage import ensure_raw;ensure_raw(s14)
    top=arts[f'{STUDY}/SEAL.json']
    for f,d in req(top,'files_sha256','study SEAL').items():
        p=s14/f
        if p.exists():check(sha(p)==d,f'study-023 {f} does not match the study SEAL')
        else:check('CHECKPOINT' in f or f.startswith('logs/') or f in ('RUN_023.log',),f'study-023 sealed file {f} is missing (only checkpoints and logs may be absent)')
    for sub in ('transfer','repro/reproset'):
        if not (s14/sub/'SEAL.json').exists():continue
        S=arts[f'{STUDY}/{sub}/SEAL.json']
        for n,k in (('RESULTS.json','results_sha256'),('SCIENTIFIC.json','scientific_sha256')):check(sha(s14/sub/n)==req(S,k,sub),f'study-023 {sub}/{n} does not match its SEAL')
    from scripts import make_paired_023,make_reproducibility_023,make_gates_023
    for mod,name in ((make_paired_023,'PAIRED_ANALYSIS_023.json'),(make_reproducibility_023,'REPRODUCIBILITY_023.json'),(make_gates_023,'GATES_023.json')):
        if (s14/name).exists() or name=='GATES_023.json':
            check(read_bytes_(s14/name)==dumps(mod.build(s14)),f'study-023 {name} does not regenerate byte-for-byte')
    gates=arts[f'{STUDY}/GATES_023.json']
    from scripts.verify_release_020 import ledger_020
    receipts,sup=ledger_020(root,git);out['ledger_receipts']=len(receipts);out['ledger_superseded']=sup
    out['run_chronology']=ledger_order(receipts,root)
    sources={r['source'] for r in receipts}
    for need in (rel['source_freeze'],f'{STUDY}/SEAL.json',f'{STUDY}/GATES_023.json'):check(need in sources,'ledger lacks '+need)
    if git:out['process_order']=git_order(root,rel)
    out['gates_passed']=gates['passed'];out['gates_failed']=gates['failed'];out['gates_pending']=gates['pending']
    check(rel['gates_passed']==gates['passed'] and rel['gates_failed']==gates['failed'],'RELEASE.json gate lists differ from GATES_023.json')
    for k in ('GLR','G_RT','G_HB'):
        check(rel[k]==gates[k],f'RELEASE.json {k} differs from GATES_023.json');out[k]=gates[k]
    out['stop_rule_fired']=gates.get('stop_rule_fired')
    out['api']=api_check();check(rel['api']==out['api']['interface'],'RELEASE.json api differs from brute.api.certify9')
    if long:out['GLV_long_verify']=long_verify(root)
    out['status']='passed'
    out['validity']='bounded deterministic Moore worlds (<= 4 states, 2 actions, 2 bits); noisy observations (eps <= 0.02 main, 0.05 stress) on 88-step traces with the likelihood-ratio anytime bound (RGL4) against the frozen anytime margin (RGNA4) and planned-B margin (RGNB4), pre-registered in BRUTE_PLAN_023; brute.certify/9 smoke-checked; not general intelligence'
    return out


def verify(root=ROOT,fast=True,git=True,long=False):
    return _guard(lambda r,g:_verify(r,g,long),Path(root),git)


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--long',action='store_true',help='GLV: re-run 12 main cases and audit them (900 s cap)')
    ap.add_argument('--fast',action='store_true',help='accepted for symmetry; the default short mode');a=ap.parse_args()
    try:print(json.dumps(verify(long=a.long),indent=2))
    except VerificationError as e:print('VERIFICATION FAILED:',e);sys.exit(1)
