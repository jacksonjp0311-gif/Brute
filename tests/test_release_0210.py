"""v0.21.0 release checks (BRUTE_PLAN_024). New file; tests/test_release_0200*.py and earlier stay frozen.

Verifier self-test (plan release_gates.verifier_self_test, lesson of #113): VerifierSelfTest0210 runs the release verifier's
process-order logic against the REAL experiments/BRUTE_SOURCE_FREEZE_024.json and COMMIT_ORDER_024.json, and walks the
pre-seal part of the chain in live git. It needs no RELEASE.json or seal, so it runs before the release freeze.
Corruption matrix (4 modes, hard-linked copy): every JSON artifact of results/study-024 plus RELEASE.json and MANIFEST.sha256
must make scripts/verify_release_0210.verify raise VerificationError; any other exception or a silent pass fails.
"""
import json,os,subprocess,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common import VerificationError
from scripts import verify_release_0210 as V
from scripts.verify_release_060 import jload
MODES=('truncated_half','invalid_utf8_byte','empty','required_key_deleted')
FREEZE=ROOT/'experiments/BRUTE_SOURCE_FREEZE_024.json';CO=ROOT/'experiments/COMMIT_ORDER_024.json'


def _git(*a):return subprocess.run(['git',*a],cwd=ROOT,capture_output=True,text=True)


def _fake_rel(sf,sc,seal):
    co=jload(CO)['commits'];return {'preregistration_commit':co[0]['short'],'source_freeze_commit':sf,'scoring_scripts_commit':sc,'seal_commit':seal}


def _ledger_commit(event):
    for l in (ROOT/'results/RESEARCH_LEDGER.jsonl').read_text().splitlines()[::-1]:
        r=json.loads(l)
        if r.get('event')==event:return r['commit']


class VerifierSelfTest0210(unittest.TestCase):
    def test_chain_from_real_freeze(self):
        fr=jload(FREEZE);rel=_fake_rel('sfX','scX','sealX');ch=V.process_chain(fr,jload(CO),rel);names=[n for n,_ in ch]
        self.assertEqual(names[0],'preregistration_024');self.assertEqual(names[-4:],['source_freeze','scoring_scripts','seal','head'])
        commits=[c for _,c in ch[:-1]];self.assertEqual(len(commits),len(set(commits)))
        for c in fr['implementation_commits']:self.assertIn(c,commits)   # dual-role commits listed once, never compared with themselves

    def test_duplicate_rejected(self):
        fr=jload(FREEZE);rel=_fake_rel('x','x','y')
        with self.assertRaises(VerificationError):V.process_chain(fr,jload(CO),rel)

    def test_wrong_preregistration_rejected(self):
        rel=_fake_rel('a','b','c');rel['preregistration_commit']='deadbee'
        with self.assertRaises(VerificationError):V.process_chain(jload(FREEZE),jload(CO),rel)

    def test_commit_order_bound_by_freeze(self):
        from experiments.brute_common import sha
        self.assertEqual(sha(CO),jload(FREEZE)['commit_order_sha256'])

    def test_pre_seal_chain_in_live_git(self):
        sf=_ledger_commit('source_freeze_024');sc=_ledger_commit('scoring_freeze_024');self.assertTrue(sf and sc)
        ch=V.process_chain(jload(FREEZE),jload(CO),_fake_rel(sf,sc,'SEAL'))
        pre=[c for n,c in ch if n not in ('seal','head')]
        for a,b in zip(pre,pre[1:]):
            self.assertEqual(_git('merge-base','--is-ancestor',a,b).returncode,0,f'{a} !< {b}')
            self.assertNotEqual(_git('rev-parse',a).stdout,_git('rev-parse',b).stdout)


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
        obj=json.loads(data);del obj[V.required_key(root,p)];new=json.dumps(obj,indent=2,sort_keys=True).encode()+b'\n'
    p.write_bytes(new)


def targets(root=ROOT):
    return sorted({str(p.relative_to(root)) for p in V.study_artifacts(root)}|{'RELEASE.json','MANIFEST.sha256'})


def outcome(rel,mode):
    with tempfile.TemporaryDirectory() as tmp:
        dst=Path(tmp)/'brute';_linked_copy(dst);corrupt(dst,dst/rel,mode)
        try:V.verify(dst,fast=True,git=False)
        except VerificationError:return 'VerificationError'
        except Exception as e:return 'other:'+type(e).__name__
        return 'silent_pass'


@unittest.skipUnless((ROOT/'RELEASE.json').exists() and json.loads((ROOT/'RELEASE.json').read_text()).get('version')=='0.21.0','v0.21.0 RELEASE.json not written yet')
class Release0210(unittest.TestCase):
    def test_every_artifact_every_mode_raises_verification_error(self):
        m={f'{rel}|{mo}':outcome(rel,mo) for rel in targets() for mo in MODES};bad={k:v for k,v in m.items() if v!='VerificationError'}
        self.assertGreater(len(m),4*12);self.assertEqual(bad,{})

    def test_version_consistent(self):
        from brute.release_version_0210 import RELEASE_VERSION
        rel=json.loads((ROOT/'RELEASE.json').read_text());self.assertEqual(rel['version'],RELEASE_VERSION)
        import tomllib;self.assertEqual(tomllib.loads((ROOT/'pyproject.toml').read_text())['project']['version'],RELEASE_VERSION)

    def test_short_verify_passes(self):self.assertEqual(V.verify()['status'],'passed')

    def test_untampered_copy_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            dst=Path(tmp)/'brute';_linked_copy(dst);self.assertEqual(V.verify(dst,git=False)['status'],'passed')

    def test_scoring_inputs_tracked(self):
        from scripts.clean_clone_024 import tracked_check
        r=tracked_check('HEAD');self.assertTrue(r['passed'],r)

    def test_embeddable_api_answers(self):
        from brute.api.certify10 import certify10,API
        r=certify10((0,1),[0,1],[(0,1),(1,None)]);self.assertTrue(r['soundness']['anytime']);self.assertEqual(r['method'],'stitched');self.assertEqual(r['api'],API)
        self.assertEqual(json.loads((ROOT/'RELEASE.json').read_text())['api'],API)

    def test_storage_round_trip(self):
        from scripts.study024_storage import _gz
        import gzip;b=b'{"a": 1}\n';self.assertEqual(gzip.decompress(_gz(b)),b);self.assertEqual(_gz(b),_gz(b))


if __name__=='__main__':unittest.main()
