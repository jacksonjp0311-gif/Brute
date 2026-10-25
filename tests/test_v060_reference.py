"""Unit tests of the plan-008 rule in the second implementation (no brute import)."""
import subprocess,sys,unittest
from experiments.v050_reference import Row
from experiments.v060_reference import recent_union,last_traversals,_rule,RULE


def row():
    # 2 states, 2 actions; 0 -a0-> 1, 1 -a0-> 0 known; a1 untraversed. outputs {0} at 0, {3} at 1. path: 0,1,0 (acts 0,0)
    return Row((1,-1,0,-1),(frozenset((0,)),frozenset((3,))),0)


class Ref060(unittest.TestCase):
    def test_no_brute_import(self):
        out=subprocess.run([sys.executable,'-c','import sys,experiments.v060_reference;print(any(m=="brute" or m.startswith("brute.") for m in sys.modules))'],
                           capture_output=True,text=True,check=True).stdout.strip()
        self.assertEqual(out,'False')

    def test_last_traversals(self):
        self.assertEqual(last_traversals(row(),[0,0],2),{(0,0):0,(1,0):1})

    def test_recent_union(self):
        r=frozenset((row(),));codes=frozenset((0,))
        self.assertEqual(recent_union(r,0,codes,2,2,4,[0,0],0),frozenset((3,)))      # all traversals recent
        self.assertEqual(recent_union(r,0,codes,2,2,4,[0,0],2),frozenset(range(4)))  # edge (0,0) aged (last t=0 < 2)
        self.assertEqual(recent_union(r,0,codes,2,2,4,[0,0],1),frozenset(range(4)))
        self.assertEqual(recent_union(r,1,codes,2,2,4,[0,0],2),frozenset((0,3)))     # untraversed: open at current only (bound full)

    def test_rule(self):
        plain=lambda:frozenset((1,2));rec=lambda t0:frozenset((1,))
        self.assertEqual(_rule('C6',plain,rec,1,'CERTIFIED',None,[],8,8,8),('CERTIFIED',None,1,'tracked-calm'))
        self.assertEqual(_rule('C6',plain,rec,1,'CERTIFIED',None,[],7,8,8)[3],'downgraded')
        self.assertEqual(_rule('C6',plain,rec,1,'CERTIFIED',None,[3],9,8,8)[3],'downgraded')
        self.assertEqual(_rule('R6',plain,rec,1,'CERTIFIED',None,[3],10,8,8),('CERTIFIED',None,1,'Y1k-recent'))
        self.assertEqual(_rule('R6',plain,rec,1,'CERTIFIED',None,[3],11,8,8)[3],'downgraded')  # 11-3=8: inactive -> plain
        self.assertEqual(RULE,{'R6':'RO','BR6':'RO','C6':'CT','BC6':'CT'})


if __name__=='__main__':unittest.main()
