import unittest
from experiments.v0120_reference import mask,ref_bounded,dx_bounds,ref_rg,KINDS,FB


class Ref0120(unittest.TestCase):
    def test_mask(self):
        self.assertEqual(mask((0,0)),1);self.assertEqual(mask((1,1)),8);self.assertEqual(mask((None,1)),2|8);self.assertEqual(mask((None,None)),15)

    def test_bounded_one_state(self):
        # a 1-state machine always repeats its code; after one full observation the projection is that code
        out=ref_bounded(1,(1,0),[0,1,0],[(1,0),(None,0),(1,None)])
        self.assertEqual(out,[[[2],[2]],[[2],[2]],[[2],[2]]])
        self.assertEqual(ref_bounded(1,(1,0),[0,0],[(0,0),(1,0)]),[[[2],[2]],[None,None]])

    def test_bounded_two_state_toggle(self):
        # codes 0,3,0,3,0 under action 0: with <= 2 states the code after ...3 must be 0
        out=ref_bounded(2,(0,0),[0,0,0,0],[(1,1),(0,0),(1,1),(0,0)])
        self.assertEqual(out[3][0],[0]);self.assertEqual(out[2][0],[3]);self.assertEqual(out[0][0],[0,1,2,3])

    def test_dx_bounds(self):
        self.assertEqual(dx_bounds(2),[3,4]);self.assertEqual(dx_bounds(3),[4]);self.assertEqual(dx_bounds(4),[4,5]);self.assertEqual(FB,4)

    def test_rg_rule(self):
        steps=[{'t':t,'a':0,'cert':[None,None],'supp':[[1,2],None],'obs':(0,1),'act':[1,3]} for t in (1,2)]
        BS={'4':{'support':[[[1],[3]],[[2],[3]]],'unknown':[[0,0],[0,0]]}}
        r=ref_rg(steps,BS,4,burn=1)
        self.assertEqual([x['certificate'] for x in r['trace']],[[None,None],[2,None]])
        self.assertEqual(r['false_certificates'],1);self.assertEqual(r['first_cert_step'],2)

    def test_mutation_kinds(self):
        self.assertEqual(len(KINDS),20);self.assertGreaterEqual(KINDS.count('bounded'),6);self.assertGreaterEqual(KINDS.count('dlf'),6)
        self.assertGreaterEqual(KINDS.count('stress'),4)


if __name__=='__main__':unittest.main()
