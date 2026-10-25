"""v0.2.0 release checks: the fast verifier passes on the checkout and fails on tampered copies."""
import os,shutil,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common import VerificationError
from scripts.verify_release_020 import verify,git_order


def _linked_copy(dst):
    def ignore(d,names):return [n for n in names if n in ('.git','__pycache__')]
    shutil.copytree(ROOT,dst,copy_function=os.link,ignore=ignore)


def _tamper(path):
    data=Path(path).read_bytes();os.unlink(path);Path(path).write_bytes(data.replace(b'"', b"'",1) if b'"' in data else data+b' ')


class ReleaseV020(unittest.TestCase):
    def test_fast_verify_passes(self):
        out=verify(fast=True);self.assertEqual(out['status'],'passed');self.assertEqual(out['preregistration_precedes_code'],'c0ac594')

    def test_git_order(self):self.assertEqual(git_order(ROOT),'c0ac594')

    def test_tampered_copies_fail(self):
        for rel in ('results/study-004/SCIENTIFIC.json','experiments/BRUTE_PLAN_004.json','brute/active.py','results/study-004/GATES.json',
                    'results/study-003/SCIENTIFIC.json','brute/api/service_v020.py'):
            with self.subTest(rel=rel),tempfile.TemporaryDirectory() as tmp:
                dst=Path(tmp)/'brute';_linked_copy(dst);_tamper(dst/rel)
                with self.assertRaises(VerificationError):verify(dst,fast=True,git=False)


if __name__=='__main__':unittest.main()
