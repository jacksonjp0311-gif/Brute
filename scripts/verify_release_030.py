"""Brute v0.3.0 release verification. Raises VerificationError (never assert).

No literal study numbers are asserted: derived artifacts are regenerated and compared byte-for-byte, sealed artifacts
are checked against their seals, and (full mode) the study-005 independent reference is re-run.

  python scripts/verify_release_030.py               # full (re-runs the study-005 independent reference, long)
  python scripts/verify_release_030.py --fast        # hashes, seals, freezes, regenerated gates/paired, ledger, manifest, git order
  python scripts/verify_release_030.py --frozen      # also run the frozen v0.2.0 verifier (fast, no git) on the raw v0.2.0 tag blobs
"""
from __future__ import annotations
import argparse,json,subprocess,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common import VerificationError,check,sha,load,dumps
from scripts.verify_release import _freeze
from scripts.verify_release_020 import ledger_020,_git,_raw_tree

PREREG_COMMIT='25fa47b'
FREEZES=('experiments/SOURCE_FREEZE.json','experiments/BRUTE_SOURCE_FREEZE_002.json','experiments/BRUTE_RELEASE_FREEZE_010.json',
         'experiments/BRUTE_SOURCE_FREEZE_003.json','experiments/BRUTE_RELEASE_FREEZE_011.json',
         'experiments/BRUTE_SOURCE_FREEZE_004.json','experiments/BRUTE_RELEASE_FREEZE_020.json',
         'experiments/BRUTE_SOURCE_FREEZE_005.json','experiments/BRUTE_RELEASE_FREEZE_030.json')
FREEZE_RULE_FILES=('brute/changepoint.py','brute/release_version_030.py','brute/api/service_v030.py','experiments/brute_study_005.py',
                   'experiments/v030_independent_reference.py')
INHERITED=('results/study-001','results/study-002','results/study-003','results/study-004','experiments/BRUTE_PLAN_002.json',
           'experiments/BRUTE_PLAN_003.json','experiments/BRUTE_PLAN_004.json')
S5_LEDGER=('experiments/BRUTE_PLAN_005.json','experiments/BRUTE_SOURCE_FREEZE_005.json','results/study-005/CALIBRATION_CHECK.json',
           'results/study-005/SEAL.json','results/study-005/PAIRED_ANALYSIS.json','results/study-005/INDEPENDENT_AUDIT.json',
           'results/study-005/REPRODUCIBILITY.json','results/study-005/GATES.json')


def git_order(root):
    """The plan commit precedes code: the plan at PREREG_COMMIT equals the frozen plan, PREREG_COMMIT is an ancestor of HEAD,
    the freeze-rule files did not exist (committed) there, and PREREG_COMMIT is an ancestor of every commit touching them."""
    check(_git(root,'rev-parse','--git-dir').returncode==0,'not a git checkout')
    check(_git(root,'merge-base','--is-ancestor',PREREG_COMMIT,'HEAD').returncode==0,'pre-registration commit is not an ancestor of HEAD')
    plan=_git(root,'show',f'{PREREG_COMMIT}:experiments/BRUTE_PLAN_005.json')
    check(plan.returncode==0 and plan.stdout==(root/'experiments/BRUTE_PLAN_005.json').read_text(),'plan changed after pre-registration')
    for f in FREEZE_RULE_FILES:
        check(_git(root,'cat-file','-e',f'{PREREG_COMMIT}:{f}').returncode!=0,f'{f} existed at pre-registration')
        commits=_git(root,'log','--format=%H','--',f).stdout.split()
        check(commits,f'{f} has no commit')
        for c in commits:check(_git(root,'merge-base','--is-ancestor',PREREG_COMMIT,c).returncode==0,f'{f} touched by {c[:7]} before pre-registration')
    return PREREG_COMMIT


def inherited_unchanged(root):
    """Every inherited study artifact is byte-identical to its blob at tag v0.2.0."""
    n=0
    for p in INHERITED:
        ls=subprocess.run(['git','-C',str(root),'ls-tree','-r','-z','v0.2.0','--',p],capture_output=True);check(ls.returncode==0,'cannot list v0.2.0')
        for ent in ls.stdout.decode().split('\0'):
            if not ent:continue
            meta,path=ent.split('\t',1);obj=meta.split()[2]
            blob=subprocess.run(['git','-C',str(root),'cat-file','blob',obj],capture_output=True,check=True).stdout
            check((root/path).read_bytes()==blob,f'{path} differs from tag v0.2.0');n+=1
    check(n>0,'no inherited artifacts found');return n


def frozen_verifier_020(root):
    """Run the unmodified v0.2.0 verifier (fast, git=False: the raw tree has no history) on the raw blobs of tag v0.2.0."""
    env={'PYTHONPATH':'.','PATH':'/usr/bin:/bin','PYTHONDONTWRITEBYTECODE':'1'}
    with tempfile.TemporaryDirectory(prefix='brute-v020-') as tmp:
        _raw_tree(root,'v0.2.0',tmp)
        # Index (no commit) the raw tag blobs so the v0.2.0 manifest check lists exactly them; without a .git it would also
        # list the study-004 traces that its own ensure_raw() restores (deviation D2, BRUTE_DEVIATIONS_005).
        for args in (('init','-q'),('add','-A')):
            g=subprocess.run(['git','-C',tmp,*args],capture_output=True,text=True);check(g.returncode==0,'cannot index the raw v0.2.0 tree')
        code='import json;from scripts.verify_release_020 import verify;print(json.dumps(verify(fast=True,git=False)["status"]))'
        r=subprocess.run([sys.executable,'-c',code],cwd=tmp,capture_output=True,text=True,env=env)
        check(r.returncode==0 and '"passed"' in r.stdout,'frozen v0.2.0 verifier failed on the v0.2.0 tree: '+r.stdout[-400:]+r.stderr[-400:])
    return 'passed (unmodified scripts/verify_release_020.verify(fast=True, git=False) on the raw v0.2.0 tree)'


def verify(root=ROOT,fast=False,git=True,frozen=False):
    root=Path(root);out={'schema':'brute.verify-release.v3_0'}
    rel=load(root/'RELEASE.json');from brute.release_version_030 import RELEASE_VERSION
    check(rel['version']==RELEASE_VERSION=='0.3.0','RELEASE.json / brute.release_version_030.RELEASE_VERSION is not 0.3.0')
    out['locked_files']={f:_freeze(root,f) for f in FREEZES}
    for d,keys in (('results/study-001',('RESULTS.json','SCIENTIFIC.json')),('results/study-002',('RESULTS.json','SCIENTIFIC.json','CALIBRATION.json')),
                   ('results/study-003',('RESULTS.json','SCIENTIFIC.json','CALIBRATION_CHECK.json'))):
        seal=load(root/d/'SEAL.json')
        for name in keys:check(sha(root/d/name)==seal[name.split('.')[0].lower()+'_sha256'],f'{d}/{name} does not match SEAL')
    s4=root/'results/study-004';seal4=load(s4/'SEAL.json')
    from scripts.study004_storage import ensure_raw as raw4;raw4(s4)
    for name,key in (('RESULTS.json','results_sha256'),('SCIENTIFIC.json','scientific_sha256'),('CALIBRATION_CHECK.json','calibration_check_sha256')):
        check(sha(s4/name)==seal4[key],'study-004 '+name+' does not match SEAL')
    s5=root/'results/study-005';seal=load(s5/'SEAL.json')
    from scripts.study005_storage import ensure_raw as raw5;raw5(s5)
    for name,key in (('RESULTS.json','results_sha256'),('SCIENTIFIC.json','scientific_sha256'),('CALIBRATION_CHECK.json','calibration_check_sha256')):
        check(sha(s5/name)==seal[key],'study-005 '+name+' does not match SEAL')
    check(sha(root/'experiments/BRUTE_PLAN_005.json')==seal['plan_sha256'] and sha(root/'experiments/BRUTE_SOURCE_FREEZE_005.json')==seal['freeze_sha256'],'study-005 plan/freeze')
    check(load(s5/'CALIBRATION_CHECK.json')['tau_reproduced'] is True,'tau not reproduced')
    from scripts import make_paired_005,make_gates_005
    for mod,name in ((make_paired_005,'PAIRED_ANALYSIS.json'),(make_gates_005,'GATES.json')):
        check((s5/name).read_bytes()==dumps(mod.build()),f'study-005 {name} does not regenerate byte-for-byte')
    rep=load(s5/'REPRODUCIBILITY.json');check(rep['all_byte_identical'] is True,'study-005 reproducibility record')
    check(rep['files']['SCIENTIFIC.json']['committed_sha256']==seal['scientific_sha256'],'reproducibility record is of other results')
    aud=load(s5/'INDEPENDENT_AUDIT.json');check(aud['status']=='passed' and aud['source_results_sha256']==seal['results_sha256'],'study-005 audit')
    if not fast:
        from experiments.v030_independent_reference import audit
        check(aud==json.loads(dumps(audit(s5))),'study-005 fresh independent reference differs from committed report')
        out['independent_audit']='re-run, identical to committed report'
    receipts,sup=ledger_020(root,git);out['ledger_receipts']=len(receipts);out['ledger_superseded']=sup;sources={r['source'] for r in receipts}
    for need in S5_LEDGER:check(need in sources,'ledger lacks '+need)
    from scripts.make_manifest import build as manifest
    check((root/'MANIFEST.sha256').read_text()==manifest(root),'MANIFEST.sha256 does not match tracked files')
    out['manifest_files']=len((root/'MANIFEST.sha256').read_text().splitlines())
    if git:
        out['preregistration_precedes_code']=git_order(root);out['inherited_artifacts_identical_to_v0.2.0']=inherited_unchanged(root)
    if frozen:out['frozen_verifier_v0.2.0']=frozen_verifier_020(root)
    g=load(s5/'GATES.json');out['study005_gates_passed']=g['passed'];out['study005_gates_failed']=g['failed'];out['G14_verdict']=g['G14_verdict']
    check(rel['gates_passed']==g['passed'] and rel['gates_failed']==g['failed'],'RELEASE.json gate lists differ from GATES.json')
    check(rel.get('G14_verdict')==g['G14_verdict'],'RELEASE.json G14 verdict differs from GATES.json')
    out['status']='passed'
    out['validity']='bounded deterministic Moore worlds, two actions, two bits, <=4-state family, <=5-state margin; not general intelligence'
    return out


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--fast',action='store_true');ap.add_argument('--frozen',action='store_true')
    a=ap.parse_args()
    try:print(json.dumps(verify(fast=a.fast,frozen=a.frozen),indent=2))
    except VerificationError as e:print('VERIFICATION FAILED:',e);sys.exit(1)
