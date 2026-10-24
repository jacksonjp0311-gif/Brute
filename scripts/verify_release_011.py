"""Brute v0.1.1 release verification. Raises VerificationError (never assert).

No literal study numbers are asserted: derived artifacts are regenerated and compared byte-for-byte,
sealed artifacts are checked against their seals, and (full mode) the independent reference is re-run.

  python scripts/verify_release_011.py           # full (re-runs the study-003 independent reference, minutes)
  python scripts/verify_release_011.py --fast    # hashes, seals, freezes, regenerated gates/paired/R4, ledger, manifest, git order
  python scripts/verify_release_011.py --frozen-v010  # also run the frozen v0.1.0 verifier on `git archive v0.1.0`
"""
from __future__ import annotations
import argparse,json,subprocess,sys,tarfile,tempfile,io
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common import VerificationError,check,sha,load,dumps
from scripts.verify_release import _freeze,_ledger

PREREG_COMMIT='1585a77'
FREEZES=('experiments/SOURCE_FREEZE.json','experiments/BRUTE_SOURCE_FREEZE_002.json','experiments/BRUTE_RELEASE_FREEZE_010.json',
         'experiments/BRUTE_SOURCE_FREEZE_003.json','experiments/BRUTE_RELEASE_FREEZE_011.json')


def _git(root,*args):
    return subprocess.run(['git','-C',str(root),*args],capture_output=True,text=True)


def git_order(root):
    """Pre-registration precedes code: the plan at PREREG_COMMIT equals the frozen plan, no v0.1.1 code
    existed there, and PREREG_COMMIT is an ancestor of HEAD."""
    check(_git(root,'rev-parse','--git-dir').returncode==0,'not a git checkout')
    check(_git(root,'merge-base','--is-ancestor',PREREG_COMMIT,'HEAD').returncode==0,'pre-registration commit is not an ancestor of HEAD')
    plan=_git(root,'show',f'{PREREG_COMMIT}:experiments/BRUTE_PLAN_003.json')
    check(plan.returncode==0 and plan.stdout==(root/'experiments/BRUTE_PLAN_003.json').read_text(),'plan changed after pre-registration')
    for f in ('brute/fallback.py','brute/api/service_v011.py','experiments/brute_study_003.py'):
        check(_git(root,'cat-file','-e',f'{PREREG_COMMIT}:{f}').returncode!=0,f'{f} existed at pre-registration')
        first=_git(root,'log','--format=%H','--diff-filter=A','--',f).stdout.split()
        check(first and _git(root,'merge-base','--is-ancestor',PREREG_COMMIT,first[-1]).returncode==0,f'{f} added before pre-registration')
    return PREREG_COMMIT


def frozen_v010(root):
    """Run the frozen v0.1.0 verifier, unmodified, on the raw blobs of tag v0.1.0.

    Blobs are written byte-for-byte (`git cat-file blob`), not via `git archive` or checkout: those apply the
    `*.ps1 eol=crlf` attribute and change BGR-All-One.ps1, which the v0.1.0 manifest records as committed (D5)."""
    ls=subprocess.run(['git','-C',str(root),'ls-tree','-r','-z','v0.1.0'],capture_output=True);check(ls.returncode==0,'cannot list tag v0.1.0')
    with tempfile.TemporaryDirectory(prefix='brute-v010-') as tmp:
        for ent in ls.stdout.decode().split('\0'):
            if not ent:continue
            meta,path=ent.split('\t',1);mode,kind,obj=meta.split()
            check(kind=='blob','unexpected tree entry at v0.1.0: '+path)
            blob=subprocess.run(['git','-C',str(root),'cat-file','blob',obj],capture_output=True,check=True).stdout
            f=Path(tmp)/path;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes(blob)
        r=subprocess.run([sys.executable,'scripts/verify_release.py','--fast'],cwd=tmp,capture_output=True,text=True,
                         env={'PYTHONPATH':'.','PATH':'/usr/bin:/bin','PYTHONDONTWRITEBYTECODE':'1'})
        check(r.returncode==0,'frozen v0.1.0 verifier failed on the v0.1.0 tree: '+r.stdout[-400:]+r.stderr[-400:])
    return 'passed (unmodified scripts/verify_release.py --fast on the raw v0.1.0 tree)'


def verify(root=ROOT,fast=False,git=True,v010=False):
    root=Path(root);out={'schema':'brute.verify-release.v1_1'}
    rel=load(root/'RELEASE.json');from brute.version import RELEASE_VERSION
    check(rel['version']==RELEASE_VERSION=='0.1.1','RELEASE.json / brute.version.RELEASE_VERSION is not 0.1.1 (brute.__version__ stays 0.1.0: study-002 freeze, amendment A3)')
    out['locked_files']={f:_freeze(root,f) for f in FREEZES}
    # study-001 and study-002 seals (inherited, unchanged)
    st=root/'results/study-001';seal1=load(st/'SEAL.json')
    for name,key in (('RESULTS.json','results_sha256'),('SCIENTIFIC.json','scientific_sha256')):check(sha(st/name)==seal1[key],'study-001 '+name)
    s2=root/'results/study-002';seal2=load(s2/'SEAL.json')
    for name,key in (('RESULTS.json','results_sha256'),('SCIENTIFIC.json','scientific_sha256'),('CALIBRATION.json','calibration_sha256')):
        check(sha(s2/name)==seal2[key],'study-002 '+name)
    from scripts import make_gates,make_paired_analysis
    for mod,name in ((make_gates,'GATES.json'),(make_paired_analysis,'PAIRED_ANALYSIS.json')):
        check((s2/name).read_bytes()==dumps(mod.build()),f'study-002 {name} does not regenerate')
    # study-003
    s3=root/'results/study-003';seal3=load(s3/'SEAL.json')
    for name,key in (('RESULTS.json','results_sha256'),('SCIENTIFIC.json','scientific_sha256'),('CALIBRATION_CHECK.json','calibration_check_sha256')):
        check(sha(s3/name)==seal3[key],'study-003 '+name+' does not match SEAL')
    check(sha(root/'experiments/BRUTE_PLAN_003.json')==seal3['plan_sha256'] and sha(root/'experiments/BRUTE_SOURCE_FREEZE_003.json')==seal3['freeze_sha256'],'study-003 plan/freeze')
    cal=load(s3/'CALIBRATION_CHECK.json');check(cal['tau_reproduced'] is True,'tau not reproduced')
    from scripts import make_gates_003,make_paired_003,drift_stress_003
    for mod,name in ((make_paired_003,'PAIRED_ANALYSIS.json'),(make_gates_003,'GATES.json'),(drift_stress_003,'DRIFT_STRESS_R4.json')):
        check((s3/name).read_bytes()==dumps(mod.build()),f'study-003 {name} does not regenerate byte-for-byte')
    rep=load(s3/'REPRODUCIBILITY.json');check(rep['all_byte_identical'] is True,'study-003 reproducibility record')
    check(rep['files']['SCIENTIFIC.json']['committed_sha256']==seal3['scientific_sha256'],'reproducibility record is of other results')
    aud=load(s3/'INDEPENDENT_AUDIT.json');check(aud['status']=='passed' and aud['source_results_sha256']==seal3['results_sha256'],'study-003 audit')
    if not fast:
        from experiments.v011_independent_reference import audit
        check(aud==audit(s3),'study-003 fresh independent reference differs from committed report')
        out['independent_audit']='re-run, identical to committed report'
    receipts=_ledger(root);out['ledger_receipts']=len(receipts);sources={r['source'] for r in receipts}
    for need in ('experiments/BRUTE_PLAN_003.json','experiments/BRUTE_SOURCE_FREEZE_003.json','results/study-003/CALIBRATION_CHECK.json',
                 'results/study-003/SCIENTIFIC.json','results/study-003/INDEPENDENT_AUDIT.json','results/study-003/GATES.json',
                 'results/study-003/REPRODUCIBILITY.json'):
        check(need in sources,'ledger lacks '+need)
    from scripts.make_manifest import build as manifest
    check((root/'MANIFEST.sha256').read_text()==manifest(root),'MANIFEST.sha256 does not match tracked files')
    out['manifest_files']=len((root/'MANIFEST.sha256').read_text().splitlines())
    if git:out['preregistration_precedes_code']=git_order(root)
    if v010:out['frozen_v010_verifier']=frozen_v010(root)
    g=load(s3/'GATES.json');out['study003_gates_passed']=g['passed'];out['study003_gates_failed']=g['failed']
    check(rel['gates_passed']==g['passed'] and rel['gates_failed']==g['failed'],'RELEASE.json gate lists differ from GATES.json')
    out['status']='passed'
    out['validity']='bounded deterministic Moore worlds, two actions, two bits, <=4-state family, <=5-state margin; not general intelligence'
    return out


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--fast',action='store_true');ap.add_argument('--frozen-v010',action='store_true')
    a=ap.parse_args()
    try:print(json.dumps(verify(fast=a.fast,v010=a.frozen_v010),indent=2))
    except VerificationError as e:print('VERIFICATION FAILED:',e);sys.exit(1)
