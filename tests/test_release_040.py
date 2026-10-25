"""Release checks parameterised by version: the fast verifier passes on the checkout and fails on tampered copies.
Version-specific paths are read from RELEASE.json, so the test does not hard-code study numbers or commits."""
import json,os,shutil,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common import VerificationError
from scripts.verify_release_040 import verify,git_order
from brute.release_version_040 import RELEASE_VERSION
REL=json.loads((ROOT/'RELEASE.json').read_text())


def _linked_copy(dst):
    """Hard-linked copy including .git (read-only use), so the manifest is built from the same tracked-file list."""
    def ignore(d,names):return [n for n in names if n=='__pycache__']
    shutil.copytree(ROOT,dst,copy_function=os.link,ignore=ignore)


def _tamper(path):
    data=Path(path).read_bytes();os.unlink(path);Path(path).write_bytes(data.replace(b'"', b"'",1) if b'"' in data else data+b' ')


class ReleaseVersioned(unittest.TestCase):
    def test_version_consistent(self):
        self.assertEqual(REL['version'],RELEASE_VERSION)
        import tomllib;self.assertEqual(tomllib.loads((ROOT/'pyproject.toml').read_text())['project']['version'],RELEASE_VERSION)

    def test_fast_verify_passes(self):
        out=verify(fast=True);self.assertEqual(out['status'],'passed')
        self.assertEqual(out['process_order']['scoring_scripts'],REL['scoring_scripts_commit'])

    def test_git_order(self):self.assertEqual(git_order(ROOT,REL)['preregistration'],REL['preregistration_commit'])

    def test_untampered_copy_passes(self):
        """Control for the tamper test: the copy itself verifies, so a failure below is caused by the tampering."""
        with tempfile.TemporaryDirectory() as tmp:
            dst=Path(tmp)/'brute';_linked_copy(dst);self.assertEqual(verify(dst,fast=True,git=False)['status'],'passed')

    def test_tampered_copies_fail(self):
        d=REL['results_dir']
        for rel in (f'{d}/SCIENTIFIC.json',REL['preregistration'],'brute/resume.py','brute/geometry.py',f'{d}/GATES.json',
                    f'{d}/SECOND_IMPLEMENTATION_COUNT.json','scripts/make_gates_006.py','results/study-005/SCIENTIFIC.json'):
            with self.subTest(rel=rel),tempfile.TemporaryDirectory() as tmp:
                dst=Path(tmp)/'brute';_linked_copy(dst);_tamper(dst/rel)
                with self.assertRaises(VerificationError):verify(dst,fast=True,git=False)


if __name__=='__main__':unittest.main()
