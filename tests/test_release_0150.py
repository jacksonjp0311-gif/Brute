"""v0.15.0 release checks (BRUTE_PLAN_017). New file; tests/test_release_0140.py and earlier stay frozen.

Corruption matrix (same 4 modes as test_release_0140, on a hard-linked copy): every JSON artifact of results/study-017
plus RELEASE.json and MANIFEST.sha256 must make scripts/verify_release_0150.verify raise VerificationError; any other
exception or a silent pass fails. test_scoring_inputs_tracked is the plan's clean_clone.tracked_files_test (GCC part).
"""
import json,os,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common import VerificationError
from scripts.verify_release_0150 import verify,study_artifacts,required_key
MODES=('truncated_half','invalid_utf8_byte','empty','required_key_deleted')


def _linked_copy(dst):
    import shutil
    shutil.copytree(ROOT,dst,copy_function=os.link,ignore=lambda d,names:[n for n in names if n=='__pycache__'])


def corrupt(root,path,mode):
    p=Path(path);data=p.read_bytes();os.unlink(p)
    if mode=='truncated_half':new=data[:len(data)//2]
    elif mode=='invalid_utf8_byte':new=data[:len(data)//2]+b'\xff'+data[len(data)//2:]
    elif mode=='empty':new=b''
    elif p.name=='MANIFEST.sha256':new=b''.join(data.splitlines(keepends=True)[1:])
    else:
        obj=json.loads(data);del obj[required_key(root,p)];new=json.dumps(obj,indent=2,sort_keys=True).encode()+b'\n'
    p.write_bytes(new)


def targets(root=ROOT):
    return sorted({str(p.relative_to(root)) for p in study_artifacts(root)}|{'RELEASE.json','MANIFEST.sha256'})


def outcome(rel,mode):
    with tempfile.TemporaryDirectory() as tmp:
        dst=Path(tmp)/'brute';_linked_copy(dst);corrupt(dst,dst/rel,mode)
        try:verify(dst,fast=True,git=False)
        except VerificationError:return 'VerificationError'
        except Exception as e:return 'other:'+type(e).__name__
        return 'silent_pass'


class Corruption0150(unittest.TestCase):
    def test_every_artifact_every_mode_raises_verification_error(self):
        m={f'{rel}|{mo}':outcome(rel,mo) for rel in targets() for mo in MODES};bad={k:v for k,v in m.items() if v!='VerificationError'}
        self.assertGreater(len(m),4*12);self.assertEqual(bad,{})


class Release0150(unittest.TestCase):
    def test_version_consistent(self):
        from brute.release_version_0150 import RELEASE_VERSION
        rel=json.loads((ROOT/'RELEASE.json').read_text());self.assertEqual(rel['version'],RELEASE_VERSION)
        import tomllib;self.assertEqual(tomllib.loads((ROOT/'pyproject.toml').read_text())['project']['version'],RELEASE_VERSION)

    def test_short_verify_passes(self):self.assertEqual(verify()['status'],'passed')

    def test_untampered_copy_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            dst=Path(tmp)/'brute';_linked_copy(dst);self.assertEqual(verify(dst,git=False)['status'],'passed')

    def test_scoring_inputs_tracked(self):
        from scripts.clean_clone_017 import tracked_check
        r=tracked_check('HEAD');self.assertTrue(r['passed'],r)

    def test_embeddable_api_answers(self):
        from brute.api.certify5 import certify5 as certify,API
        r=certify([(0,1)],[],0);self.assertEqual(r['api'],API);self.assertEqual(r['status'],'UNKNOWN')
        rel=json.loads((ROOT/'RELEASE.json').read_text());self.assertEqual(rel['api'],API)

    def test_storage_round_trip(self):
        from scripts.study017_storage import _gz
        import gzip;b=b'{"a": 1}\n';self.assertEqual(gzip.decompress(_gz(b)),b);self.assertEqual(_gz(b),_gz(b))


if __name__=='__main__':unittest.main()
