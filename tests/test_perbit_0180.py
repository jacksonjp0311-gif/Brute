"""brute.perbit (v0.18.0 per-bit partial certificates, #103 item 5): bit order, decisions, trace counts, and agreement with
the second implementation's bit rule (experiments/v0180_reference.bit)."""
import unittest
from brute.perbit import code_bit,perbit_decide,perbit_trace
import experiments.v0180_reference as REF


class PerBit0180(unittest.TestCase):
    def test_code_bit(self):
        for c in range(4):
            for j in range(2):self.assertEqual(code_bit(c,j),REF.bit(c,j))
        self.assertEqual([code_bit(2,0),code_bit(2,1)],[1,0])
        for bad in ((4,0),(-1,0),(True,0),(1,2)):
            with self.assertRaises(ValueError):code_bit(*bad)

    def test_decide(self):
        self.assertEqual(perbit_decide(8,8,{2,3}),[None,None])           # burn-in
        self.assertEqual(perbit_decide(9,8,set()),[None,None])           # empty support
        self.assertEqual(perbit_decide(9,8,{2,3}),[1,None]);self.assertEqual(perbit_decide(9,8,{1,3}),[None,1])
        self.assertEqual(perbit_decide(9,8,{0}),[0,0]);self.assertEqual(perbit_decide(9,8,{0,3}),[None,None])

    def test_trace(self):
        steps=[(9,0),(50,1),(60,0)];truth=[[2,0],[3,1],[0,0]];sup=[[{2,3},{0}],[{1,3},{2}],[{0,1},set()]]
        T=perbit_trace(steps,truth,sup,8)
        self.assertEqual(T['trace'][0]['bits'],[[1,None],[0,0]]);self.assertEqual(T['trace'][1]['wrong'],[[False,False],[True,True]])
        self.assertEqual((T['certified_bits'],T['false_bits'],T['late_certified_bits'],T['late_false_bits']),(7,2,4,2))


if __name__=='__main__':unittest.main()
