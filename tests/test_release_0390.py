"""Tests for the lean v0.39.0 release verifier (scripts/verify_release_0390.py); built from tests/test_release_0380.py (frozen). New file."""
import json,shutil,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
import sys;sys.path.insert(0,str(ROOT))
from experiments.brute_common import VerificationError
from scripts import verify_release_0390 as V


class TestRelease0390(unittest.TestCase):
    def _tmp(self,release,gates):
        d=Path(tempfile.mkdtemp());self.addCleanup(shutil.rmtree,d)
        (d/'results/study-042').mkdir(parents=True)
        (d/'RELEASE.json').write_text(json.dumps(release));(d/'results/study-042/GATES_042.json').write_text(json.dumps(gates))
        return d

    def _release(self,**kw):
        R={k:'x' for k in V.RELEASE_KEYS};R.update(version='0.39.0',gates_passed=['A'],gates_failed=['B'],gates_not_exercised=[],secondary={});R.update(kw);return R

    def test_release_ok(self):
        d=self._tmp(self._release(),{'gates':{'A':{'pass':True},'B':{'pass':False}}})
        self.assertEqual(V.release_ok(d)['version'],'0.39.0')

    def test_wrong_version(self):
        d=self._tmp(self._release(version='0.38.0'),{'gates':{'A':{'pass':True},'B':{'pass':False}}})
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
        # deviation #146 (kept by #150, #152, #154 and #157): the default test-suite output is outside the repository and never the tracked official file
        from scripts import run_tests_0390 as T
        a,b=T.scratch_path(),T.scratch_path()
        self.assertNotEqual(a,b);self.assertFalse(a.exists())
        self.assertNotIn(str(ROOT.resolve()),str(a.resolve()));self.assertNotEqual(a.resolve(),T.OFFICIAL.resolve())

    def test_run_tests_refuses_overwrite(self):
        from scripts import run_tests_0390 as T
        d=Path(tempfile.mkdtemp());self.addCleanup(shutil.rmtree,d);f=d/'x.json';f.write_text('{}')
        with self.assertRaises(SystemExit):T.main(['--output',str(f),'--modules'])

    def test_chain_authorization_exception(self):
        # 0380a rule kept by #157: a build_authorization_042 entry may repeat the preregistration commit, nothing else may go back
        import subprocess
        d=Path(tempfile.mkdtemp());self.addCleanup(shutil.rmtree,d);g=lambda *a:subprocess.run(['git','-C',str(d),*a],check=True,capture_output=True,text=True).stdout.strip()
        g('init','-q');g('config','user.email','t@t');g('config','user.name','t');c=[]
        for i in range(3):(d/'f').write_text(str(i));g('add','f');g('commit','-qm',str(i));c.append(g('rev-parse','HEAD'))
        R={'preregistration_commit':c[0],'source_freeze_commit':c[2],'seal_commit':c[2]}
        E=[{'event':'preregistration_042','commit':c[0]},{'event':'plan_erratum_042','commit':c[1]},{'event':V.AUTH,'commit':c[0]},{'event':'seedcheck_042','commit':c[2]}]
        self.assertEqual(V.chain(d,R,E)['authorization_exceptions'],1)
        E2=[dict(e) for e in E];E2[2]['event']='other'
        with self.assertRaises(VerificationError):V.chain(d,R,E2)
        E3=[dict(e) for e in E];E3[2]['commit']=c[1];E3.insert(2,{'event':'x','commit':c[2]})
        with self.assertRaises(VerificationError):V.chain(d,R,E3)


if __name__=='__main__':unittest.main()
