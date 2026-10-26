"""experiments/v090_reference.py (second implementation, study-011): window helpers, and the unchanged SP8 audit on
sealed study-010 traces (seen data, development use only)."""
import json,unittest
from pathlib import Path
import experiments.v090_reference as R
from experiments.v080_reference import jump_rows
from experiments.v90_independent_reference import ref_initial,ref_observe
from experiments.v030_independent_reference import y1k_union,compatible_codes
from experiments.brute_common import load

ROOT=Path(__file__).resolve().parents[1]
OBS=[(0,1),(1,None),(0,0),(None,1),(1,1),(0,None),(1,0),(None,None)];ACTS=[0,1,1,0,1,0,1]


def _hist():
    r=ref_initial(OBS[0]);h=[r]
    for a,o in zip(ACTS,OBS[1:]):
        r,st=ref_observe(r,a,o,4,160000);h.append(r if st=='supported' else frozenset())
    return h


def _cases(path,arm,n):
    out=[];p=ROOT/path
    if not p.exists():return out
    with open(p) as f:
        for line in f:
            c=json.loads(line).get('case') or json.loads(line)
            if arm in c.get('arms',{}):out.append(c)
            if len(out)>=n:break
    return out


class V090Reference(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan=load(R.PLAN);cls.view=R.plan_view(cls.plan)

    def test_constants(self):
        self.assertEqual(R.ARMS_2X2,('J9','SP8'));self.assertEqual(self.view['jump_window_K'],4)
        self.assertTrue(str(R.PLAN).endswith('BRUTE_PLAN_011.json'))

    def test_no_brute_import(self):
        src=(ROOT/'experiments/v090_reference.py').read_text()
        self.assertNotIn('from brute',src);self.assertNotIn('import brute',src)

    def test_window_positions(self):
        self.assertEqual(R.window_positions(0,4),[]);self.assertEqual(R.window_positions(1,4),[])
        self.assertEqual(R.window_positions(2,4),[1]);self.assertEqual(R.window_positions(7,4),[4,5,6])
        self.assertNotIn(7,R.window_positions(7,4))                 # the last transition is never a jump

    def test_window_contains_no_jump_rows(self):
        h=_hist()
        for T in range(len(h)):
            if not h[T]:break
            W,ok=R.window_rows(h,OBS,ACTS,T,4,160000,4);self.assertTrue(ok);self.assertTrue(h[T]<=W)
            if T<=1:self.assertEqual(W,h[T])
            H,_=R.window_hull(h,OBS,ACTS,T,4,160000,4)
            for b in (0,1):self.assertTrue(y1k_union(h[T],b,compatible_codes(OBS[T]),4)<=H[b])

    def test_window_branch_is_jump_then_observe(self):
        h=_hist();T=4;t=3
        rows=jump_rows(h[t-1],compatible_codes(OBS[t]),4)
        rows,st=ref_observe(rows,ACTS[t],OBS[t+1],4,160000)
        W,_=R.window_rows(h,OBS,ACTS,T,4,160000,4)
        if st=='supported':self.assertTrue(rows<=W)

    def test_budget_marks_unauditable(self):
        h=_hist();_,ok=R.window_rows(h,OBS,ACTS,5,4,1,4);self.assertFalse(ok)

    def test_sp8_audit_on_sealed_010_traces(self):
        cs=_cases('results/study-010/2x2/CHECKPOINT.jsonl','SP8',2)
        if not cs:self.skipTest('sealed study-010 checkpoint absent')
        for c in cs:
            ok,msg,_=R.audit_trace(c,'SP8',self.view,self.plan['tau6']['value']);self.assertTrue(ok,msg)
            c2=dict(c,arms={'J9':c['arms']['SP8']})
            ok2,msg2,_=R.audit_trace(c2,'J9',self.view,self.plan['tau6']['value'])
            self.assertFalse(ok2)                                   # an SP8 trace has no hull fields


if __name__=='__main__':unittest.main()
