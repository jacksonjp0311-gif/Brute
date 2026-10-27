import unittest
from experiments.v0150_reference import rgl_choice,ref_lookahead,KINDS,NS,MAIN_ARMS,OOD5_ARMS


class Ref0150(unittest.TestCase):
    def test_rgl_rule(self):
        L=lambda n0,d0,n1,d1:{'num':[n0,n1],'den':[d0,d1]}
        self.assertEqual(rgl_choice(8,8,None,1),(1,'sp8'))               # burn-in
        self.assertEqual(rgl_choice(9,8,L(1,2,1,3),1),(0,'rgl'))         # 1/2 > 1/3
        self.assertEqual(rgl_choice(9,8,L(1,2,2,4),1),(1,'sp8'))         # exact tie 1/2 = 2/4
        self.assertEqual(rgl_choice(9,8,L(0,0,0,3),0),(0,'sp8'))         # 0 = 0
        self.assertEqual(rgl_choice(9,8,L(0,2,1,4),0),(1,'rgl'))

    def test_lookahead_fully_observed_n1(self):
        # one state: after any full observation the next code is forced -> num = den
        r=ref_lookahead(1,(None,None),[0,0],[(None,None),(1,0)])
        for row in r:
            for n,d in row:self.assertEqual(n,d)

    def test_constants(self):
        self.assertEqual(NS,(1,2,3,4,5));self.assertEqual(len(KINDS),20);self.assertEqual(len(MAIN_ARMS),15)
        self.assertEqual(OOD5_ARMS,('RG4','RG5','RSXL5'));self.assertEqual(sum(k in ('rglx','rgl') for k in KINDS),5)


if __name__=='__main__':unittest.main()
