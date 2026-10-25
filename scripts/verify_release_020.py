"""Brute v0.2.0 release verification. Raises VerificationError (never assert).

No literal study numbers are asserted: derived artifacts are regenerated and compared byte-for-byte, sealed artifacts
are checked against their seals, and (full mode) the study-004 independent reference is re-run.

  python scripts/verify_release_020.py               # full (re-runs the study-004 independent reference, minutes)
  python scripts/verify_release_020.py --fast        # hashes, seals, freezes, regenerated gates/paired, ledger, manifest, git order
  python scripts/verify_release_020.py --frozen      # also run the frozen v0.1.1 and v0.1.0 verifiers on the raw tag blobs
"""
from __future__ import annotations
import argparse,json,subprocess,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common import VerificationError,check,sha,load,dumps
from scripts.verify_release import _freeze

PREREG_COMMIT='c0ac594'
FREEZES=('experiments/SOURCE_FREEZE.json','experiments/BRUTE_SOURCE_FREEZE_002.json','experiments/BRUTE_RELEASE_FREEZE_010.json',
         'experiments/BRUTE_SOURCE_FREEZE_003.json','experiments/BRUTE_RELEASE_FREEZE_011.json',
         'experiments/BRUTE_SOURCE_FREEZE_004.json','experiments/BRUTE_RELEASE_FREEZE_020.json')
FREEZE_RULE_FILES=('brute/active.py','brute/release_version.py','brute/api/service_v020.py','experiments/brute_study_004.py',
                   'experiments/v020_independent_reference.py')
INHERITED=('results/study-001','results/study-002','results/study-003','experiments/BRUTE_PLAN_003.json','experiments/BRUTE_PLAN_002.json')


def _git(root,*args):
    return subprocess.run(['git','-C',str(root),*args],capture_output=True,text=True)


def ledger_020(root,git=True):
    """The frozen v0.1.0 `_ledger` requires every receipt's source to keep its bytes forever, but RELEASE.json is ledgered
    once per release (v0.1.1 receipt) and must change at each release (deviation D3). Rule: the chain and receipt
    hashes are checked exactly as in `_ledger`; the LAST receipt for each source must match the current bytes; an
    earlier receipt whose bytes differ is accepted only as superseded, and (when git is available) its recorded commit
    must hold a blob of that source with exactly the recorded hash."""
    import hashlib
    previous='0'*64;receipts=[]
    for line in (root/'results/RESEARCH_LEDGER.jsonl').read_text().splitlines():
        r=json.loads(line);check(r['previous']==previous,'ledger chain broken')
        previous=hashlib.sha256(json.dumps({k:v for k,v in r.items() if k!='receipt_sha256'},sort_keys=True,separators=(',',':')).encode()).hexdigest()
        check(previous==r['receipt_sha256'],'ledger receipt hash');receipts.append(r)
    last={r['source']:i for i,r in enumerate(receipts)};superseded=[]
    for i,r in enumerate(receipts):
        if sha(root/r['source'])==r['source_sha256']:continue
        check(last[r['source']]!=i,'ledger source changed: '+r['source'])
        if git:
            check('commit' in r,'superseded receipt without commit: '+r['source'])
            b=subprocess.run(['git','-C',str(root),'show',f"{r['commit']}:{r['source']}"],capture_output=True)
            check(b.returncode==0 and __import__('hashlib').sha256(b.stdout).hexdigest()==r['source_sha256'],
                  'superseded ledger receipt does not match its commit: '+r['source'])
        superseded.append(r['source']+'@'+r.get('commit','?'))
    return receipts,superseded


def git_order(root):
    """The plan commit precedes code: the plan at PREREG_COMMIT equals the frozen plan, PREREG_COMMIT is an ancestor of HEAD,
    the freeze-rule files did not exist there, and PREREG_COMMIT is an ancestor of every commit touching them."""
    check(_git(root,'rev-parse','--git-dir').returncode==0,'not a git checkout')
    check(_git(root,'merge-base','--is-ancestor',PREREG_COMMIT,'HEAD').returncode==0,'pre-registration commit is not an ancestor of HEAD')
    plan=_git(root,'show',f'{PREREG_COMMIT}:experiments/BRUTE_PLAN_004.json')
    check(plan.returncode==0 and plan.stdout==(root/'experiments/BRUTE_PLAN_004.json').read_text(),'plan changed after pre-registration')
    for f in FREEZE_RULE_FILES:
        check(_git(root,'cat-file','-e',f'{PREREG_COMMIT}:{f}').returncode!=0,f'{f} existed at pre-registration')
        commits=_git(root,'log','--format=%H','--',f).stdout.split()
        check(commits,f'{f} has no commit')
        for c in commits:check(_git(root,'merge-base','--is-ancestor',PREREG_COMMIT,c).returncode==0,f'{f} touched by {c[:7]} before pre-registration')
    return PREREG_COMMIT


def inherited_unchanged(root):
    """Every inherited study artifact is byte-identical to its blob at tag v0.1.1."""
    n=0
    for p in INHERITED:
        ls=subprocess.run(['git','-C',str(root),'ls-tree','-r','-z','v0.1.1','--',p],capture_output=True);check(ls.returncode==0,'cannot list v0.1.1')
        for ent in ls.stdout.decode().split('\0'):
            if not ent:continue
            meta,path=ent.split('\t',1);obj=meta.split()[2]
            blob=subprocess.run(['git','-C',str(root),'cat-file','blob',obj],capture_output=True,check=True).stdout
            check((root/path).read_bytes()==blob,f'{path} differs from tag v0.1.1');n+=1
    check(n>0,'no inherited artifacts found');return n


def _raw_tree(root,tag,tmp):
    ls=subprocess.run(['git','-C',str(root),'ls-tree','-r','-z',tag],capture_output=True);check(ls.returncode==0,'cannot list tag '+tag)
    for ent in ls.stdout.decode().split('\0'):
        if not ent:continue
        meta,path=ent.split('\t',1);mode,kind,obj=meta.split();check(kind=='blob',f'unexpected tree entry at {tag}: {path}')
        blob=subprocess.run(['git','-C',str(root),'cat-file','blob',obj],capture_output=True,check=True).stdout
        f=Path(tmp)/path;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes(blob)


def frozen_verifiers(root):
    """Run the frozen v0.1.1 verifier (fast, git order skipped: the raw tree has no history; the v0.1.1 order is checked on
    this repository) on the raw blobs of tag v0.1.1, and the frozen v0.1.0 verifier on the raw blobs of tag v0.1.0."""
    env={'PYTHONPATH':'.','PATH':'/usr/bin:/bin','PYTHONDONTWRITEBYTECODE':'1'};out={}
    with tempfile.TemporaryDirectory(prefix='brute-v011-') as tmp:
        _raw_tree(root,'v0.1.1',tmp)
        code='import json;from scripts.verify_release_011 import verify;print(json.dumps(verify(fast=True,git=False)["status"]))'
        r=subprocess.run([sys.executable,'-c',code],cwd=tmp,capture_output=True,text=True,env=env)
        check(r.returncode==0 and '"passed"' in r.stdout,'frozen v0.1.1 verifier failed on the v0.1.1 tree: '+r.stdout[-400:]+r.stderr[-400:])
        out['v0.1.1']='passed (unmodified scripts/verify_release_011.verify(fast=True, git=False) on the raw v0.1.1 tree)'
    from scripts.verify_release_011 import git_order as order_011
    out['v0.1.1_git_order']=order_011(root)
    with tempfile.TemporaryDirectory(prefix='brute-v010-') as tmp:
        _raw_tree(root,'v0.1.0',tmp)
        r=subprocess.run([sys.executable,'scripts/verify_release.py','--fast'],cwd=tmp,capture_output=True,text=True,env=env)
        check(r.returncode==0,'frozen v0.1.0 verifier failed on the v0.1.0 tree: '+r.stdout[-400:]+r.stderr[-400:])
        out['v0.1.0']='passed (unmodified scripts/verify_release.py --fast on the raw v0.1.0 tree)'
    return out


def verify(root=ROOT,fast=False,git=True,frozen=False):
    root=Path(root);out={'schema':'brute.verify-release.v2_0'}
    rel=load(root/'RELEASE.json');from brute.release_version import RELEASE_VERSION
    check(rel['version']==RELEASE_VERSION=='0.2.0','RELEASE.json / brute.release_version.RELEASE_VERSION is not 0.2.0')
    out['locked_files']={f:_freeze(root,f) for f in FREEZES}
    for d,keys in (('results/study-001',('RESULTS.json','SCIENTIFIC.json')),('results/study-002',('RESULTS.json','SCIENTIFIC.json','CALIBRATION.json')),
                   ('results/study-003',('RESULTS.json','SCIENTIFIC.json','CALIBRATION_CHECK.json'))):
        seal=load(root/d/'SEAL.json')
        for name in keys:check(sha(root/d/name)==seal[name.split('.')[0].lower()+'_sha256'],f'{d}/{name} does not match SEAL')
    s4=root/'results/study-004';seal=load(s4/'SEAL.json')
    from scripts.study004_storage import ensure_raw;ensure_raw(s4)
    for name,key in (('RESULTS.json','results_sha256'),('SCIENTIFIC.json','scientific_sha256'),('CALIBRATION_CHECK.json','calibration_check_sha256')):
        check(sha(s4/name)==seal[key],'study-004 '+name+' does not match SEAL')
    check(sha(root/'experiments/BRUTE_PLAN_004.json')==seal['plan_sha256'] and sha(root/'experiments/BRUTE_SOURCE_FREEZE_004.json')==seal['freeze_sha256'],'study-004 plan/freeze')
    check(load(s4/'CALIBRATION_CHECK.json')['tau_reproduced'] is True,'tau not reproduced')
    from scripts import make_paired_004,make_gates_004
    for mod,name in ((make_paired_004,'PAIRED_ANALYSIS.json'),(make_gates_004,'GATES.json')):
        check((s4/name).read_bytes()==dumps(mod.build()),f'study-004 {name} does not regenerate byte-for-byte')
    rep=load(s4/'REPRODUCIBILITY.json');check(rep['all_byte_identical'] is True,'study-004 reproducibility record')
    check(rep['files']['SCIENTIFIC.json']['committed_sha256']==seal['scientific_sha256'],'reproducibility record is of other results')
    aud=load(s4/'INDEPENDENT_AUDIT.json');check(aud['status']=='passed' and aud['source_results_sha256']==seal['results_sha256'],'study-004 audit')
    if not fast:
        from experiments.v020_independent_reference import audit
        check(aud==audit(s4),'study-004 fresh independent reference differs from committed report')
        out['independent_audit']='re-run, identical to committed report'
    receipts,sup=ledger_020(root,git);out['ledger_receipts']=len(receipts);out['ledger_superseded']=sup;sources={r['source'] for r in receipts}
    for need in ('experiments/BRUTE_PLAN_004.json','experiments/BRUTE_SOURCE_FREEZE_004.json','results/study-004/CALIBRATION_CHECK.json',
                 'results/study-004/SEAL.json','results/study-004/SCIENTIFIC.json.gz','results/study-004/INDEPENDENT_AUDIT.json','results/study-004/GATES.json',
                 'results/study-004/REPRODUCIBILITY.json'):
        check(need in sources,'ledger lacks '+need)
    from scripts.make_manifest import build as manifest
    check((root/'MANIFEST.sha256').read_text()==manifest(root),'MANIFEST.sha256 does not match tracked files')
    out['manifest_files']=len((root/'MANIFEST.sha256').read_text().splitlines())
    if git:
        out['preregistration_precedes_code']=git_order(root);out['inherited_artifacts_identical_to_v0.1.1']=inherited_unchanged(root)
    if frozen:out['frozen_verifiers']=frozen_verifiers(root)
    g=load(s4/'GATES.json');out['study004_gates_passed']=g['passed'];out['study004_gates_failed']=g['failed']
    check(rel['gates_passed']==g['passed'] and rel['gates_failed']==g['failed'],'RELEASE.json gate lists differ from GATES.json')
    out['status']='passed'
    out['validity']='bounded deterministic Moore worlds, two actions, two bits, <=4-state family, <=5-state margin; not general intelligence'
    return out


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--fast',action='store_true');ap.add_argument('--frozen',action='store_true')
    a=ap.parse_args()
    try:print(json.dumps(verify(fast=a.fast,frozen=a.frozen),indent=2))
    except VerificationError as e:print('VERIFICATION FAILED:',e);sys.exit(1)
