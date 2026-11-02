"""Tests for the lean v0.54.0 release verifier (scripts/verify_release_0540.py) and the plan 057 status_wording_rule; built from
tests/test_release_0530.py (frozen). New file."""
import json,shutil,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
import sys;sys.path.insert(0,str(ROOT))
from experiments.brute_common import VerificationError
from scripts import verify_release_0540 as V


class TestRelease0540(unittest.TestCase):
    def _tmp(self,release,gates):
        d=Path(tempfile.mkdtemp());self.addCleanup(shutil.rmtree,d)
        (d/'results/study-057').mkdir(parents=True)
        (d/'RELEASE.json').write_text(json.dumps(release));(d/'results/study-057/GATES_057.json').write_text(json.dumps(gates))
        return d

    def _release(self,**kw):
        R={k:'x' for k in V.RELEASE_KEYS};R.update(version='0.54.0',gates_passed=['A'],gates_failed=['B'],gates_not_exercised=[],secondary={},certified_20v_N20=None,sound_not_certified_20v=None);R.update(kw);return R

    def test_release_ok(self):
        d=self._tmp(self._release(),{'gates':{'A':{'pass':True},'B':{'pass':False}}})
        self.assertEqual(V.release_ok(d)['version'],'0.54.0')

    def test_wrong_version(self):
        d=self._tmp(self._release(version='0.53.0'),{'gates':{'A':{'pass':True},'B':{'pass':False}}})
        with self.assertRaises(VerificationError):V.release_ok(d)

    def test_gate_list_mismatch(self):
        d=self._tmp(self._release(),{'gates':{'A':{'pass':False},'B':{'pass':False}}})
        with self.assertRaises(VerificationError):V.release_ok(d)

    def test_secondary_mismatch(self):
        d=self._tmp(self._release(secondary={'GK14':True}),{'gates':{'A':{'pass':True},'B':{'pass':False}},'secondary':{'G16':{'pass':False}}})
        with self.assertRaises(VerificationError):V.release_ok(d)

    def test_flag_mismatch(self):
        G={'gates':{'A':{'pass':True},'B':{'pass':False}},'certified_20v_N20':False,'sound_not_certified_20v':True}
        d=self._tmp(self._release(certified_20v_N20=False,sound_not_certified_20v=True),G);self.assertEqual(V.release_ok(d)['version'],'0.54.0')
        d=self._tmp(self._release(certified_20v_N20=True,sound_not_certified_20v=True),G)
        with self.assertRaises(VerificationError):V.release_ok(d)
        d=self._tmp(self._release(certified_20v_N20=False,sound_not_certified_20v=False),G)
        with self.assertRaises(VerificationError):V.release_ok(d)

    def test_status_phrase_mismatch(self):
        G={'gates':{'A':{'pass':True},'B':{'pass':False}},'status_phrase':'sound but not certified'}
        d=self._tmp(self._release(status_phrase='sound but not certified'),G);self.assertEqual(V.release_ok(d)['version'],'0.54.0')
        d=self._tmp(self._release(status_phrase='certified'),G)
        with self.assertRaises(VerificationError):V.release_ok(d)

    def test_status_wording_rule(self):
        # plan 057 status_wording_rule: the three phrases, derived only from the two GATES_057 flags
        from scripts.make_gates_057 import status_phrase
        self.assertEqual(status_phrase(True,False,[]),'certified')
        self.assertEqual(status_phrase(False,True,['GPRE57','GX_gain57']),'sound but not certified')
        p=status_phrase(False,False,['GMATCH57','GDET57'])
        self.assertTrue(p.startswith('not certified, no certification status'));self.assertIn('GMATCH57, GDET57',p)

    def test_missing_key(self):
        R=self._release();del R['headline'];d=self._tmp(R,{'gates':{}})
        with self.assertRaises(VerificationError):V.release_ok(d)


    def test_run_tests_default_is_scratch(self):
        # deviation #146 (kept by #150, #152, #154, #157, #159, #161, #163, #165, #167, #169, #171, #173, #175 #177 #179, #183, #185 and #188): the default test-suite output is outside the repository and never the tracked official file
        from scripts import run_tests_0540 as T
        a,b=T.scratch_path(),T.scratch_path()
        self.assertNotEqual(a,b);self.assertFalse(a.exists())
        self.assertNotIn(str(ROOT.resolve()),str(a.resolve()));self.assertNotEqual(a.resolve(),T.OFFICIAL.resolve())

    def test_run_tests_refuses_overwrite(self):
        from scripts import run_tests_0540 as T
        d=Path(tempfile.mkdtemp());self.addCleanup(shutil.rmtree,d);f=d/'x.json';f.write_text('{}')
        with self.assertRaises(SystemExit):T.main(['--output',str(f),'--modules'])

    def test_chain_authorization_exception(self):
        # 0380a rule kept by #157, #159, #161, #163, #165, #167, #169, #171, #173, #175, #177, #179, #183, #185 and #188: a build_authorization_057 entry may repeat the preregistration commit, nothing else may go back
        import subprocess
        d=Path(tempfile.mkdtemp());self.addCleanup(shutil.rmtree,d);g=lambda *a:subprocess.run(['git','-C',str(d),*a],check=True,capture_output=True,text=True).stdout.strip()
        g('init','-q');g('config','user.email','t@t');g('config','user.name','t');c=[]
        for i in range(3):(d/'f').write_text(str(i));g('add','f');g('commit','-qm',str(i));c.append(g('rev-parse','HEAD'))
        R={'preregistration_commit':c[0],'source_freeze_commit':c[2],'seal_commit':c[2]}
        E=[{'event':'preregistration_057','commit':c[0]},{'event':'plan_erratum_057','commit':c[1]},{'event':V.AUTH,'commit':c[0]},{'event':'seedcheck_057','commit':c[2]}]
        self.assertEqual(V.chain(d,R,E)['authorization_exceptions'],1)
        E2=[dict(e) for e in E];E2[2]['event']='other'
        with self.assertRaises(VerificationError):V.chain(d,R,E2)
        E3=[dict(e) for e in E];E3[2]['commit']=c[1];E3.insert(2,{'event':'x','commit':c[2]})
        with self.assertRaises(VerificationError):V.chain(d,R,E3)
        # the 057 case: build_authorization_057 names the preregistration commit itself and nothing lies between, so 0 exceptions
        E4=[{'event':'preregistration_057','commit':c[0]},{'event':V.AUTH,'commit':c[0]},{'event':'seedcheck_057','commit':c[1]}]
        self.assertEqual(V.chain(d,R,E4)['authorization_exceptions'],0)

    def test_release_version(self):
        from brute.release_version_0540 import RELEASE_VERSION
        self.assertEqual(RELEASE_VERSION,V.VERSION)


if __name__=='__main__':unittest.main()
