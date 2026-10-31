"""Tests for the lean v0.36.0 release verifier (scripts/verify_release_0360.py). New file."""
import json,shutil,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
import sys;sys.path.insert(0,str(ROOT))
from experiments.brute_common import VerificationError
from scripts import verify_release_0360 as V


class TestRelease0360(unittest.TestCase):
    def _tmp(self,release,gates):
        d=Path(tempfile.mkdtemp());self.addCleanup(shutil.rmtree,d)
        (d/'results/study-039').mkdir(parents=True)
        (d/'RELEASE.json').write_text(json.dumps(release));(d/'results/study-039/GATES_039.json').write_text(json.dumps(gates))
        return d

    def _release(self,**kw):
        R={k:'x' for k in V.RELEASE_KEYS};R.update(version='0.36.0',gates_passed=['A'],gates_failed=['B'],gates_not_exercised=[],secondary={});R.update(kw);return R

    def test_release_ok(self):
        d=self._tmp(self._release(),{'gates':{'A':{'pass':True},'B':{'pass':False}}})
        self.assertEqual(V.release_ok(d)['version'],'0.36.0')

    def test_wrong_version(self):
        d=self._tmp(self._release(version='0.35.0'),{'gates':{'A':{'pass':True},'B':{'pass':False}}})
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
        # deviation #146 (kept by #150): the default test-suite output is outside the repository and never the tracked official file
        from scripts import run_tests_0360 as T
        a,b=T.scratch_path(),T.scratch_path()
        self.assertNotEqual(a,b);self.assertFalse(a.exists())
        self.assertNotIn(str(ROOT.resolve()),str(a.resolve()));self.assertNotEqual(a.resolve(),T.OFFICIAL.resolve())

    def test_run_tests_refuses_overwrite(self):
        from scripts import run_tests_0360 as T
        d=Path(tempfile.mkdtemp());self.addCleanup(shutil.rmtree,d);f=d/'x.json';f.write_text('{}')
        with self.assertRaises(SystemExit):T.main(['--output',str(f),'--modules'])


if __name__=='__main__':unittest.main()
