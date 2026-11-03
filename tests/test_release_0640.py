"""v0.64.0 release tests (new file): verify_release_0640 shape, and RELEASE.json / pyproject agreement once RELEASE.json says 0.64.0."""
import json,unittest
from pathlib import Path
from scripts import verify_release_0640 as V
ROOT=Path(__file__).resolve().parents[1]


class T(unittest.TestCase):
    def test_constants(self):
        self.assertEqual(V.VERSION,'0.64.0');self.assertIn('gates_failed',V.RELEASE_KEYS);self.assertTrue(V.GATES.endswith('GATES_068.json'))

    def test_release_if_present(self):
        R=json.loads((ROOT/'RELEASE.json').read_text())
        if R.get('version')!='0.64.0':self.skipTest('RELEASE.json not yet 0.64.0')
        self.assertIn('version = "0.64.0"',(ROOT/'pyproject.toml').read_text());V.release_ok(ROOT)


if __name__=='__main__':unittest.main()
