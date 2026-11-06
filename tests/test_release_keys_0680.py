"""GTEST-style release-keys test for v0.68.0 (new file, built from tests/test_release_keys_0650.py): every RELEASE.json key that
scripts/verify_release_0680.py reads is in its REQUIRED tuple (derived from the verifier's AST), including contribution_split."""
import unittest
from pathlib import Path
from scripts import verify_release_0680 as V
from tests.test_release_keys_0650 import release_keys_read
ROOT=Path(__file__).resolve().parents[1];SRC=ROOT/'scripts/verify_release_0680.py'


class T(unittest.TestCase):
    def test_every_read_key_is_required(self):
        names,keys=release_keys_read(SRC.read_text())
        self.assertTrue(names);self.assertTrue({'version','gates_passed','gates_failed','status_phrase','contribution_split'}<=keys)
        self.assertEqual(sorted(keys-set(V.REQUIRED)),[])

    def test_required_extends_release_keys(self):
        self.assertEqual(tuple(V.REQUIRED[:len(V.RELEASE_KEYS)]),tuple(V.RELEASE_KEYS));self.assertIn('contribution_split',V.REQUIRED)


if __name__=='__main__':unittest.main()
