"""Tamper detection for every release verifier, parameterized by version (v0.3.0 errata, review M4).

The frozen tests test_brute_repro.test_verify_fails_under_tampered_results, test_release_011/020.test_fast_verify_passes
stop at a version-string assertion after each version bump, so their tamper checks are never reached. This test runs each
release's own verifier on the raw blobs of its own tag (where its version assertion holds), checks that it passes, then
tampers a sealed result, a gate file and a frozen source file one at a time and checks that it fails. Each case adds one
line to the end of an artifact or flips one value; nothing in the repository is changed (temporary copies only).
"""
import subprocess,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.verify_release_020 import _raw_tree

# tag -> (verifier call evaluated in the raw tag tree, files to tamper)
CASES={
    'v0.1.0':('from scripts.verify_release import verify;r=verify(fast=True)',
              ('results/study-002/GATES.json','results/study-002/SCIENTIFIC.json','brute/core/learner.py')),
    'v0.1.1':('from scripts.verify_release_011 import verify;r=verify(fast=True,git=False)',
              ('results/study-003/GATES.json','results/study-003/SCIENTIFIC.json','brute/fallback.py')),
    'v0.2.0':('from scripts.verify_release_020 import verify;r=verify(fast=True,git=False)',
              ('results/study-004/GATES.json','results/study-004/SEAL.json','brute/active.py')),
    'v0.3.0':('from scripts.verify_release_030 import verify;r=verify(fast=True,git=False)',
              ('results/study-005/GATES.json','results/study-005/SEAL.json','brute/changepoint.py')),
}
ENV={'PYTHONPATH':'.','PATH':'/usr/bin:/bin','PYTHONDONTWRITEBYTECODE':'1'}


def _tag_exists(tag):return subprocess.run(['git','-C',str(ROOT),'rev-parse','-q','--verify',f'refs/tags/{tag}'],capture_output=True).returncode==0


def run_verifier(tmp,call):
    code=call+';import json;print("STATUS",r["status"])'
    r=subprocess.run([sys.executable,'-c',code],cwd=tmp,capture_output=True,text=True,env=ENV)
    return r.returncode==0 and 'STATUS passed' in r.stdout,(r.stdout+r.stderr)[-600:]


def tamper(path):
    s=path.read_bytes()
    if path.suffix=='.json':
        t=s.replace(b'true',b'false',1) if b'true' in s else s.replace(b'0',b'1',1)
    else:t=s+b'\n# tamper\n'
    assert t!=s;path.write_bytes(t);return s


class TamperByVersion(unittest.TestCase):
    def _check(self,tag):
        if not _tag_exists(tag):self.skipTest(f'tag {tag} not present (shallow clone)')
        call,files=CASES[tag]
        with tempfile.TemporaryDirectory(prefix=f'brute-{tag}-') as tmp:
            _raw_tree(ROOT,tag,tmp)
            for args in (('init','-q'),('add','-A')):subprocess.run(['git','-C',tmp,*args],capture_output=True,check=True)
            ok,log=run_verifier(tmp,call);self.assertTrue(ok,f'{tag} verifier does not pass on its own tag tree: {log}')
            for rel in files:
                p=Path(tmp)/rel;orig=tamper(p)
                ok,log=run_verifier(tmp,call);self.assertFalse(ok,f'{tag} verifier missed tampering of {rel}')
                p.write_bytes(orig)

    def test_v010(self):self._check('v0.1.0')
    def test_v011(self):self._check('v0.1.1')
    def test_v020(self):self._check('v0.2.0')
    def test_v030(self):self._check('v0.3.0')


if __name__=='__main__':unittest.main()
