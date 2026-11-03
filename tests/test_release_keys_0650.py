"""Regression test for the GTEST68 bug (new file). v0.64.0's test asserted a RELEASE.json key was in verify_release_0640.RELEASE_KEYS
when the verifier actually read it outside that tuple. This test derives, from the AST of scripts/verify_release_0650.py, every
RELEASE.json key the verifier reads (R['...'] subscripts on the RELEASE.json object) and checks each is in REQUIRED, so a missing
key fails with a clean message instead of a KeyError; and it pins the exact fact: status_phrase is required but NOT in RELEASE_KEYS."""
import ast,unittest
from pathlib import Path
from scripts import verify_release_0650 as V
ROOT=Path(__file__).resolve().parents[1];SRC=ROOT/'scripts/verify_release_0650.py'


def release_keys_read(src):
    """String keys subscripted on any name bound to jload(.../'RELEASE.json') inside the verifier."""
    t=ast.parse(src);names=set();keys=set()
    for n in ast.walk(t):
        if isinstance(n,ast.Assign) and isinstance(n.value,ast.Call) and 'RELEASE.json' in ast.unparse(n.value):
            names|={x.id for x in n.targets if isinstance(x,ast.Name)}
    for n in ast.walk(t):
        if isinstance(n,ast.Subscript) and isinstance(n.value,ast.Name) and n.value.id in names and isinstance(n.slice,ast.Constant) and isinstance(n.slice.value,str):
            keys.add(n.slice.value)
    return names,keys


class T(unittest.TestCase):
    def test_every_read_key_is_required(self):
        names,keys=release_keys_read(SRC.read_text())
        self.assertTrue(names,'no RELEASE.json binding found');self.assertTrue({'version','gates_passed','gates_failed','status_phrase'}<=keys)
        self.assertEqual(sorted(keys-set(V.REQUIRED)),[])

    def test_status_phrase_fact(self):
        self.assertIn('status_phrase',V.REQUIRED);self.assertNotIn('status_phrase',V.RELEASE_KEYS)
        self.assertEqual(tuple(V.REQUIRED[:len(V.RELEASE_KEYS)]),tuple(V.RELEASE_KEYS))

    def test_would_have_caught_0640(self):
        # applied to the v0.64.0 verifier with RELEASE_KEYS as its required list, the check finds status_phrase missing
        from scripts import verify_release_0640 as V64
        _,keys=release_keys_read((ROOT/'scripts/verify_release_0640.py').read_text())
        self.assertEqual(sorted(keys-set(V64.RELEASE_KEYS)),['status_phrase'])


if __name__=='__main__':unittest.main()
