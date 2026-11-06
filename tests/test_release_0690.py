"""v0.69.0 release tests (new file): verify_release_0690 shape, and RELEASE.json / pyproject agreement once RELEASE.json says 0.69.0."""
import json,unittest
from pathlib import Path
from scripts import verify_release_0690 as V
ROOT=Path(__file__).resolve().parents[1]


class T(unittest.TestCase):
    def test_constants(self):
        self.assertEqual(V.VERSION,'0.69.0');self.assertIn('gates_failed',V.REQUIRED);self.assertIn('status_phrase',V.REQUIRED)
        self.assertTrue(V.GATES.endswith('GATES_073.json'))

    def test_release_if_present(self):
        R=json.loads((ROOT/'RELEASE.json').read_text())
        if R.get('version')!='0.69.0':self.skipTest('RELEASE.json not yet 0.69.0')
        self.assertIn('version = "0.69.0"',(ROOT/'pyproject.toml').read_text());V.release_ok(ROOT)


if __name__=='__main__':unittest.main()
