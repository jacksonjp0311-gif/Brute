"""experiments/v080_reference.py (second implementation, study-010): helpers and the unchanged SC7 / BSC7 audits on
sealed study-009 traces (seen data, development use only)."""
import json,unittest
from pathlib import Path
import experiments.v080_reference as R
from experiments.v90_independent_reference import ref_initial,ref_observe
from experiments.v030_independent_reference import y1k_union,score,compatible_codes
from experiments.brute_common import load

ROOT=Path(__file__).resolve().parents[1]


def _cases(path,arm,n):
    out=[]
    p=ROOT/path
    if not p.exists():return out
    with open(p) as f:
        for line in f:
            c=json.loads(line)['case']
            if arm in c['arms']:out.append(c)
            if len(out)>=n:break
    return out


class V080Reference(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan=load(R.PLAN);cls.view=R.plan_view(cls.plan)

    def test_constants(self):
        self.assertEqual(R.ARMS_2X2,('J8','SP8','SC7'));self.assertEqual(R.ARMS_BREADTH,('BSC7','BSP8'))
        self.assertEqual(R.POLICY['SP8'],'LU-C');self.assertEqual(R.POLICY['BSP8'],'LU-C');self.assertEqual(R.POLICY['J8'],'LU-R')
        self.assertTrue(str(R.PLAN).endswith('BRUTE_PLAN_010.json'))

    def test_no_brute_import(self):
        src=(ROOT/'experiments/v080_reference.py').read_text()
        self.assertNotIn('from brute',src);self.assertNotIn('import brute',src)

    def test_calm(self):
        self.assertFalse(R.calm_after([],6,8,8));self.assertTrue(R.calm_after([],7,8,8))
        self.assertFalse(R.calm_after([5],11,8,8));self.assertTrue(R.calm_after([5],12,8,8))

    def test_hull_contains_y1k_and_opens_on_fresh_state(self):
        obs=[(0,1),(1,None),(0,0),(None,1),(1,1),(0,None)];acts=[0,1,1,0,1]
        r=ref_initial(obs[0]);prev=None
        for a,o in zip(acts,obs[1:]):
            prev=r;r,st=ref_observe(r,a,o,4,160000);self.assertEqual(st,'supported')
        H=R.hull_unions(prev,r,len(acts),compatible_codes(obs[-1]),4)
        for b in (0,1):
            self.assertTrue(y1k_union(r,b,compatible_codes(obs[-1]),4)<=H[b])
        # some row visits < 4 states, so a jump into a fresh state opens every code
        if any(len(m.outputs)<4 for m in prev):
            for b in (0,1):self.assertEqual(H[b],frozenset(range(4)))
        # T = 0: hull rows are the current rows
        r0=ref_initial((0,1));H0=R.hull_unions(None,r0,0,compatible_codes((0,1)),4)
        for b in (0,1):self.assertEqual(H0[b],y1k_union(r0,b,compatible_codes((0,1)),4))

    def test_score_c_not_calm_equals_lur(self):
        obs=[(0,1),(1,None),(0,0),(None,1)];acts=[0,1,1]
        r4=ref_initial(obs[0]);r5=ref_initial(obs[0])
        for a,o in zip(acts,obs[1:]):r4,_=ref_observe(r4,a,o,4,160000);r5,_=ref_observe(r5,a,o,5,160000)
        for b in (0,1):
            self.assertEqual(R.score_c(r4,'supported',r5,'supported',False,b,4,5,160000,160000,False),
                             score(r4,'supported',r5,'supported',False,b,4,5,160000,160000,True))
            self.assertGreaterEqual(R.score_c(r4,'supported',r5,'supported',False,b,4,5,160000,160000,True),
                                    score(r4,'supported',r5,'supported',False,b,4,5,160000,160000,True))

    def test_sc7_audit_on_sealed_009_traces(self):
        cs=_cases('results/study-009/2x2/CHECKPOINT.jsonl','SC7',3)
        if not cs:self.skipTest('sealed study-009 checkpoint absent')
        for c in cs:
            ok,msg,_=R.audit_trace(c,'SC7',self.view,self.plan['tau6']['value'],self.plan['tau7']['value'])
            self.assertTrue(ok,msg)
            # an SC7 trace audited as SP8 must fail on the policy label
            c2=dict(c,arms={'SP8':c['arms']['SC7']})
            ok2,msg2,_=R.audit_trace(c2,'SP8',self.view,self.plan['tau6']['value'],self.plan['tau7']['value'])
            self.assertFalse(ok2);self.assertIn('rule',msg2)

    def test_bsc7_audit_on_sealed_009_trace(self):
        cs=_cases('results/study-009/breadth/CHECKPOINT.jsonl','BSC7',2)
        if not cs:self.skipTest('sealed study-009 checkpoint absent')
        for c in cs:
            ok,msg,_=R.audit_trace(c,'BSC7',self.view,self.plan['tau6']['value'],self.plan['tau7']['value'])
            self.assertTrue(ok,msg)


if __name__=='__main__':unittest.main()
