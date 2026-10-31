"""Tests for the lean v0.45.0 release verifier (scripts/verify_release_0450.py); built from tests/test_release_0440.py (frozen). New file."""
import json,shutil,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
import sys;sys.path.insert(0,str(ROOT))
from experiments.brute_common import VerificationError
from scripts import verify_release_0450 as V


class TestRelease0450(unittest.TestCase):
    def _tmp(self,release,gates):
        d=Path(tempfile.mkdtemp());self.addCleanup(shutil.rmtree,d)
        (d/'results/study-048').mkdir(parents=True)
        (d/'RELEASE.json').write_text(json.dumps(release));(d/'results/study-048/GATES_048.json').write_text(json.dumps(gates))
        return d

    def _release(self,**kw):
        R={k:'x' for k in V.RELEASE_KEYS};R.update(version='0.45.0',gates_passed=['A'],gates_failed=['B'],gates_not_exercised=[],secondary={});R.update(kw);return R

    def test_release_ok(self):
        d=self._tmp(self._release(),{'gates':{'A':{'pass':True},'B':{'pass':False}}})
        self.assertEqual(V.release_ok(d)['version'],'0.45.0')

    def test_wrong_version(self):
        d=self._tmp(self._release(version='0.44.0'),{'gates':{'A':{'pass':True},'B':{'pass':False}}})
        with self.assertRaises(VerificationError):V.release_ok(d)

    def test_gate_list_mismatch(self):
        d=self._tmp(self._release(),{'gates':{'A':{'pass':False},'B':{'pass':False}}})
        with self.assertRaises(VerificationError):V.release_ok(d)

    def test_secondary_mismatch(self):
        d=self._tmp(self._release(secondary={'GK14':True}),{'gates':{'A':{'pass':True},'B':{'pass':False}},'secondary':{'G16':{'pass':False}}})
        with self.assertRaises(VerificationError):V.release_ok(d)

    def test_missing_key(self):
        R=self._release();del R['headline'];d=self._tmp(R,{'gates':{}})
        with self.assertRaises(VerificationError):V.release_ok(d)


    def test_run_tests_default_is_scratch(self):
        # deviation #146 (kept by #150, #152, #154, #157, #159, #161, #163, #165, #167 and #169): the default test-suite output is outside the repository and never the tracked official file
        from scripts import run_tests_0450 as T
        a,b=T.scratch_path(),T.scratch_path()
        self.assertNotEqual(a,b);self.assertFalse(a.exists())
        self.assertNotIn(str(ROOT.resolve()),str(a.resolve()));self.assertNotEqual(a.resolve(),T.OFFICIAL.resolve())

    def test_run_tests_refuses_overwrite(self):
        from scripts import run_tests_0450 as T
        d=Path(tempfile.mkdtemp());self.addCleanup(shutil.rmtree,d);f=d/'x.json';f.write_text('{}')
        with self.assertRaises(SystemExit):T.main(['--output',str(f),'--modules'])

    def test_chain_authorization_exception(self):
        # 0380a rule kept by #157, #159, #161, #163, #165, #167 and #169: a build_authorization_048 entry may repeat the preregistration commit, nothing else may go back
        import subprocess
        d=Path(tempfile.mkdtemp());self.addCleanup(shutil.rmtree,d);g=lambda *a:subprocess.run(['git','-C',str(d),*a],check=True,capture_output=True,text=True).stdout.strip()
        g('init','-q');g('config','user.email','t@t');g('config','user.name','t');c=[]
        for i in range(3):(d/'f').write_text(str(i));g('add','f');g('commit','-qm',str(i));c.append(g('rev-parse','HEAD'))
        R={'preregistration_commit':c[0],'source_freeze_commit':c[2],'seal_commit':c[2]}
        E=[{'event':'preregistration_048','commit':c[0]},{'event':'plan_erratum_048','commit':c[1]},{'event':V.AUTH,'commit':c[0]},{'event':'seedcheck_048','commit':c[2]}]
        self.assertEqual(V.chain(d,R,E)['authorization_exceptions'],1)
        E2=[dict(e) for e in E];E2[2]['event']='other'
        with self.assertRaises(VerificationError):V.chain(d,R,E2)
        E3=[dict(e) for e in E];E3[2]['commit']=c[1];E3.insert(2,{'event':'x','commit':c[2]})
        with self.assertRaises(VerificationError):V.chain(d,R,E3)
        # the 048 case: build_authorization_048 names the preregistration commit itself and nothing lies between, so 0 exceptions
        E4=[{'event':'preregistration_048','commit':c[0]},{'event':V.AUTH,'commit':c[0]},{'event':'seedcheck_048','commit':c[1]}]
        self.assertEqual(V.chain(d,R,E4)['authorization_exceptions'],0)

    def test_release_version(self):
        from brute.release_version_0450 import RELEASE_VERSION
        self.assertEqual(RELEASE_VERSION,V.VERSION)


if __name__=='__main__':unittest.main()
