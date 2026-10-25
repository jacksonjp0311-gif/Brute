"""Brute v0.6.0 release verification (target (c) / GT1 of BRUTE_PLAN_008). New file; verify_release_050 stays frozen
with its recorded defect (a corrupt JSON artifact raises json.JSONDecodeError there, see tests/test_release_060.py).

GT1 design: every artifact read goes through `jload` / `read_bytes_` / `req`, which turn OSError, UnicodeDecodeError,
ValueError (incl. JSONDecodeError), gzip/zlib errors and missing keys into VerificationError. Before anything else the
verifier parses EVERY JSON artifact of results/study-008 (recursive, raw RESULTS/SCIENTIFIC excepted: those are bound by
the SEAL sha and their committed .json.gz by MANIFEST) plus RELEASE.json, and checks each file's required key
(REQUIRED_KEYS). In addition the whole verification body runs inside `_guard`, which converts any remaining
OSError/ValueError/KeyError/TypeError/IndexError/EOFError/zlib.error raised by reused (frozen) helpers into
VerificationError with the original exception named, so no other exception type escapes.

  python scripts/verify_release_060.py --fast     # seals, freezes, regenerated paired/repro/gates, ledger, manifest, git order
  python scripts/verify_release_060.py            # also re-runs the second implementation count (long)
"""
from __future__ import annotations
import argparse,json,sys,zlib,gzip
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common import VerificationError,check,sha,dumps

STUDY='results/study-008'
RAW=('RESULTS.json','SCIENTIFIC.json')
REQUIRED_KEYS={'SEAL.json':'scientific_sha256','GATES_008.json':'gates','GATES_008_FINAL.json':'gates','PAIRED_ANALYSIS.json':'scientific_sha256',
               'REPRODUCIBILITY.json':'G12_pass','SECOND_IMPLEMENTATION_COUNT.json':'mismatching_arm_traces','ENUM_B5_008.json':'mismatching_arm_traces',
               'XCHECK_008.json':'per_family_arm','GMC_COUNT_008.json':'summary','GMC_BREADTH_008.json':'summary','R_DEV_XCHECK_007.json':'mismatching_traces',
               'GT1_008.json':'pass','SEEDCHECK_008.json':'PASS','RELEASE.json':'version'}
RELEASE_KEYS=('version','preregistration','preregistration_commit','source_freeze','source_freeze_commit','release_freeze',
              'scoring_scripts_commit','seal_commit','results_dir','gates_passed','gates_failed')
PREVIOUS_FREEZES=('experiments/SOURCE_FREEZE.json','experiments/BRUTE_SOURCE_FREEZE_002.json','experiments/BRUTE_RELEASE_FREEZE_010.json',
                  'experiments/BRUTE_SOURCE_FREEZE_003.json','experiments/BRUTE_RELEASE_FREEZE_011.json',
                  'experiments/BRUTE_SOURCE_FREEZE_004.json','experiments/BRUTE_RELEASE_FREEZE_020.json',
                  'experiments/BRUTE_SOURCE_FREEZE_005.json','experiments/BRUTE_RELEASE_FREEZE_030.json',
                  'experiments/BRUTE_SOURCE_FREEZE_006.json','experiments/BRUTE_RELEASE_FREEZE_040.json',
                  'experiments/BRUTE_SOURCE_FREEZE_007.json','experiments/BRUTE_RELEASE_FREEZE_050.json')
SCORING=('scripts/make_gates_008.py','scripts/make_paired_008.py','scripts/make_reproducibility_008.py')
_CONVERT=(OSError,ValueError,KeyError,TypeError,IndexError,EOFError,zlib.error,gzip.BadGzipFile)


def read_bytes_(path):
    try:return Path(path).read_bytes()
    except OSError as e:raise VerificationError(f'cannot read {path}: {e}') from None


def jload(path):
    data=read_bytes_(path)
    try:text=data.decode('utf-8')
    except UnicodeDecodeError as e:raise VerificationError(f'{path}: invalid UTF-8: {e}') from None
    try:obj=json.loads(text)
    except ValueError as e:raise VerificationError(f'{path}: invalid JSON: {e}') from None
    check(isinstance(obj,dict),f'{path}: top level is not an object')
    return obj


def req(obj,key,where):
    try:return obj[key]
    except (KeyError,TypeError,IndexError):raise VerificationError(f'{where}: missing required key {key!r}') from None


def _guard(fn,*a,**k):
    try:return fn(*a,**k)
    except VerificationError:raise
    except _CONVERT as e:raise VerificationError(f'{type(e).__name__} in {getattr(fn,"__name__",fn)}: {e}') from None


def study_artifacts(root):
    s=Path(root)/STUDY
    return sorted(p for p in s.rglob('*.json') if not (p.name in RAW) and '.partial' not in p.name)


def parse_all(root):
    """Step 0 (GT1): parse every study-008 JSON artifact and RELEASE.json, check required keys."""
    out={}
    for p in study_artifacts(root)+[Path(root)/'RELEASE.json']:
        o=jload(p);k=REQUIRED_KEYS.get(p.name,'schema')
        req(o,k,str(p.relative_to(root)));out[str(p.relative_to(root))]=o
    rel=out['RELEASE.json']
    for k in RELEASE_KEYS:req(rel,k,'RELEASE.json')
    return out


def _freeze(root,rel):
    lock=jload(root/rel)
    for f,digest in req(lock,'sha256_files',rel).items():check(sha(root/f)==digest,f'{rel}: {f} changed')
    return len(lock['sha256_files'])


def manifest_ok(root):
    from scripts.make_manifest import build as manifest
    text=read_bytes_(root/'MANIFEST.sha256')
    try:text=text.decode('utf-8')
    except UnicodeDecodeError as e:raise VerificationError(f'MANIFEST.sha256: invalid UTF-8: {e}') from None
    check(text==manifest(root),'MANIFEST.sha256 does not match tracked files')
    return len(text.splitlines())


def ledger_order(receipts):
    ev=[req(r,'event','ledger') for r in receipts]
    for e in ('preregistration_008','source_freeze_008','scoring_scripts_008','run_start_008','run_end_008','seal_008','gates_008'):check(e in ev,'ledger lacks '+e)
    check(ev.index('source_freeze_008')<ev.index('scoring_scripts_008')<ev.index('run_start_008')<ev.index('run_end_008')<ev.index('seal_008')<ev.index('gates_008'),
          'ledger run chronology')
    return {e:next(r['note'] for r in receipts if r['event']==e)[:160] for e in ('scoring_scripts_008','run_start_008','run_end_008')}


def git_order(root,rel):
    from scripts.verify_release_020 import _git
    def anc(a,b):return _git(root,'merge-base','--is-ancestor',a,b).returncode==0
    check(_git(root,'rev-parse','--git-dir').returncode==0,'not a git checkout')
    fr=jload(root/rel['source_freeze'])
    chain=[('preregistration',req(fr,'preregistration_commit','freeze')),('reference',req(fr,'reference_commit','freeze'))]
    chain+=[(f'implementation_{i}',c) for i,c in enumerate(req(fr,'implementation_commits','freeze'))]
    chain+=[(f'pre_freeze_fix_{i}',c) for i,c in enumerate(fr.get('pre_freeze_fix_commits',[]))]
    chain+=[('source_freeze',rel['source_freeze_commit']),('scoring_scripts',rel['scoring_scripts_commit']),('seal',rel['seal_commit']),('head','HEAD')]
    for (na,a),(nb,b) in zip(chain,chain[1:]):
        check(anc(a,b),f'{na} {a} is not an ancestor of {nb} {b}')
        if b!='HEAD':check(_git(root,'rev-parse',a).stdout!=_git(root,'rev-parse',b).stdout,f'{na} and {nb} are the same commit')
    plan=_git(root,'show',f"{fr['preregistration_commit']}:{rel['preregistration']}")
    check(plan.returncode==0 and plan.stdout==(root/rel['preregistration']).read_text(),'plan changed after pre-registration')
    sc=rel['scoring_scripts_commit']
    for f in SCORING:
        check(_git(root,'cat-file','-e',f"{rel['source_freeze_commit']}:{f}").returncode!=0,f'{f} existed at the source freeze')
        b=_git(root,'show',f'{sc}:{f}');check(b.returncode==0 and b.stdout==(root/f).read_text(),f'{f} changed after the scoring-script commit')
        check(len(_git(root,'log','--format=%H','--',f).stdout.split())==1,f'{f} has more than one commit')
    return {n:c for n,c in chain if c!='HEAD'}


def _verify(root,fast,git):
    out={'schema':'brute.verify-release.v6_0'}
    arts=parse_all(root);rel=arts['RELEASE.json'];out['artifacts_parsed']=len(arts)
    out['manifest_files']=manifest_ok(root)
    from brute.release_version_060 import RELEASE_VERSION
    check(rel['version']==RELEASE_VERSION,'RELEASE.json version differs from brute.release_version_060')
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
    s8=root/rel['results_dir'];check(rel['results_dir']==STUDY,'results_dir')
    seal=arts[f'{STUDY}/SEAL.json'];rseal=arts[f'{STUDY}/repro/SEAL.json']
    from scripts.study008_storage import ensure_raw;ensure_raw(s8)
    for n,k in (('RESULTS.json','results_sha256'),('SCIENTIFIC.json','scientific_sha256')):
        check(sha(s8/n)==req(seal,k,'SEAL'),f'study-008 {n} does not match SEAL');check(sha(s8/'repro'/n)==req(rseal,k,'repro SEAL'),f'study-008 repro {n} does not match its SEAL')
    check(sha(root/rel['preregistration'])==req(seal,'plan_sha256','SEAL') and sha(root/rel['source_freeze'])==req(seal,'freeze_sha256','SEAL'),'study-008 plan/freeze')
    from scripts import make_paired_008,make_reproducibility_008,make_gates_008
    for mod,name in ((make_paired_008,'PAIRED_ANALYSIS.json'),(make_reproducibility_008,'REPRODUCIBILITY.json')):
        check(read_bytes_(s8/name)==dumps(mod.build(s8)),f'study-008 {name} does not regenerate byte-for-byte')
    final=make_gates_008.build(s8);check(read_bytes_(s8/'GATES_008_FINAL.json')==dumps(final),'GATES_008_FINAL.json does not regenerate byte-for-byte')
    pre=arts[f'{STUDY}/GATES_008.json']
    check({k:v for k,v in pre['gates'].items() if k!='GT1_verifier_parse_errors'}=={k:v for k,v in final['gates'].items() if k!='GT1_verifier_parse_errors'},
          'GATES_008.json differs from GATES_008_FINAL.json outside GT1')
    cnt=arts[f'{STUDY}/SECOND_IMPLEMENTATION_COUNT.json'];check(req(cnt,'source_sha256','count')==seal['results_sha256'],'second implementation count is of other results')
    check('second implementation by the same author' in req(cnt,'wording','count'),'second implementation wording')
    for n in ('GMC_COUNT_008.json',):check(req(arts[f'{STUDY}/{n}'],'results_sha256',n)==seal['results_sha256'],n+' is of other results')
    check(req(arts[f'{STUDY}/repro/GMC_COUNT_008.json'],'results_sha256','repro GMC')==rseal['results_sha256'],'repro GMC is of other results')
    if not fast:
        from experiments import v060_reference
        from experiments.brute_common_008 import load as _l8,PLAN as _P8
        res=jload(s8/'RESULTS.json')
        again=v060_reference.run(req(res,'cases','RESULTS'),_l8(_P8),workers=6,mutate_k=20,source_sha=sha(s8/'RESULTS.json'))
        check(json.loads(dumps(again))==cnt,'second implementation count does not reproduce')
        out['second_implementation']='re-run, identical'
    from scripts.verify_release_020 import ledger_020
    receipts,sup=ledger_020(root,git);out['ledger_receipts']=len(receipts);out['ledger_superseded']=sup
    out['run_chronology']=ledger_order(receipts)
    sources={r['source'] for r in receipts}
    for need in (rel['preregistration'],rel['source_freeze'],f'{STUDY}/SEAL.json',f'{STUDY}/GATES_008.json'):check(need in sources,'ledger lacks '+need)
    if git:out['process_order']=git_order(root,rel)
    out['gates_passed']=final['passed'];out['gates_failed']=final['failed'];out['gates_pending']=final['pending']
    check(rel['gates_passed']==final['passed'] and rel['gates_failed']==final['failed'],'RELEASE.json gate lists differ from GATES_008_FINAL.json')
    for k in ('GA1','GX2_prime','GMC'):out[k]=final[k];check(rel.get(k)==final[k],f'RELEASE.json {k} differs from GATES_008_FINAL.json')
    out['status']='passed'
    out['validity']='bounded deterministic Moore worlds; 2x2 families plus pre-registered breadth families; not general intelligence'
    return out


def verify(root=ROOT,fast=False,git=True):
    return _guard(_verify,Path(root),fast,git)


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--fast',action='store_true');a=ap.parse_args()
    try:print(json.dumps(verify(fast=a.fast),indent=2))
    except VerificationError as e:print('VERIFICATION FAILED:',e);sys.exit(1)
