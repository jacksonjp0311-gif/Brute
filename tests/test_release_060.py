"""v0.6.0 release checks (GT1 of BRUTE_PLAN_008). Version-specific paths come from RELEASE.json.

GT1: for EVERY JSON artifact of results/study-008 (recursive; raw RESULTS/SCIENTIFIC are bound by SEAL and their .json.gz
by MANIFEST) plus RELEASE.json, SEAL and MANIFEST.sha256, each of 4 corruption modes (truncated to half, an invalid UTF-8
byte inserted in the middle, empty file, valid JSON with the verifier's required key deleted; for MANIFEST, which is not
JSON, the 4th mode deletes its first line) must raise VerificationError from scripts/verify_release_060.verify on a
hard-linked copy; any other exception type or a silent pass fails.
Regression (documented, expected): the FROZEN scripts/verify_release_050.py still raises json.JSONDecodeError on the
recorded v0.5.0 case (corrupted results/study-007/SECOND_IMPLEMENTATION_COUNT.json), and its two files are unchanged.
"""
import hashlib,json,os,shutil,subprocess,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common import VerificationError
from scripts.verify_release_060 import verify,study_artifacts,REQUIRED_KEYS
MODES=('truncated_half','invalid_utf8_byte','empty','required_key_deleted')


def _linked_copy(dst):
    def ignore(d,names):return [n for n in names if n=='__pycache__']
    shutil.copytree(ROOT,dst,copy_function=os.link,ignore=ignore)


def corrupt(path,mode):
    p=Path(path);data=p.read_bytes();os.unlink(p)
    if mode=='truncated_half':new=data[:len(data)//2]
    elif mode=='invalid_utf8_byte':new=data[:len(data)//2]+b'\xff'+data[len(data)//2:]
    elif mode=='empty':new=b''
    elif p.name=='MANIFEST.sha256':new=b''.join(data.splitlines(keepends=True)[1:])
    else:
        obj=json.loads(data);k=REQUIRED_KEYS.get(p.name,'schema');del obj[k]
        new=json.dumps(obj,indent=2,sort_keys=True).encode()+b'\n'
    p.write_bytes(new)


def targets(root=ROOT):
    t=[str(p.relative_to(root)) for p in study_artifacts(root)]+['RELEASE.json','MANIFEST.sha256']
    return sorted(set(t))


def outcome(rel,mode):
    with tempfile.TemporaryDirectory() as tmp:
        dst=Path(tmp)/'brute';_linked_copy(dst);corrupt(dst/rel,mode)
        try:verify(dst,fast=True,git=False)
        except VerificationError:return 'VerificationError'
        except Exception as e:return 'other:'+type(e).__name__
        return 'silent_pass'


def gt1_matrix():
    return {f'{rel}|{m}':outcome(rel,m) for rel in targets() for m in MODES}


def regression_050():
    """The frozen v0.5.0 verifier on its recorded case, with the v0.5.0 RELEASE.json/pyproject restored in a copy."""
    fz=json.loads((ROOT/'experiments/BRUTE_RELEASE_FREEZE_050.json').read_text())['sha256_files']
    same={f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest()==fz[f] for f in ('scripts/verify_release_050.py','tests/test_release_050.py')}
    from scripts.verify_release_050 import verify as verify050
    with tempfile.TemporaryDirectory() as tmp:
        dst=Path(tmp)/'brute';_linked_copy(dst)
        for f in ('RELEASE.json','pyproject.toml'):
            b=subprocess.run(['git','-C',str(ROOT),'show',f'v0.5.0:{f}'],capture_output=True,check=True).stdout;os.unlink(dst/f);(dst/f).write_bytes(b)
        p=dst/'results/study-007/SECOND_IMPLEMENTATION_COUNT.json';data=p.read_bytes();os.unlink(p);p.write_bytes(data.replace(b'"',b"'",1))
        try:verify050(dst,fast=True,git=False);got='silent_pass'
        except json.JSONDecodeError:got='JSONDecodeError'
        except Exception as e:got=type(e).__name__
    return {'files_unchanged':same,'raised':got}


class GT1(unittest.TestCase):
    def test_every_artifact_every_mode_raises_verification_error(self):
        m=gt1_matrix();bad={k:v for k,v in m.items() if v!='VerificationError'}
        self.assertGreater(len(m),4*10);self.assertEqual(bad,{})

    def test_frozen_050_defect_still_recorded(self):
        r=regression_050();self.assertTrue(all(r['files_unchanged'].values()),r);self.assertEqual(r['raised'],'JSONDecodeError')


class Release060(unittest.TestCase):
    def test_version_consistent(self):
        from brute.release_version_060 import RELEASE_VERSION
        rel=json.loads((ROOT/'RELEASE.json').read_text());self.assertEqual(rel['version'],RELEASE_VERSION)
        import tomllib;self.assertEqual(tomllib.loads((ROOT/'pyproject.toml').read_text())['project']['version'],RELEASE_VERSION)

    def test_fast_verify_passes(self):self.assertEqual(verify(fast=True)['status'],'passed')

    def test_untampered_copy_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            dst=Path(tmp)/'brute';_linked_copy(dst);self.assertEqual(verify(dst,fast=True,git=False)['status'],'passed')


if __name__=='__main__':unittest.main()
