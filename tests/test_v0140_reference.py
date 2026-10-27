import unittest
from experiments.v0140_reference import rsxl_choice,KINDS,NS,MAIN_ARMS,OOD5_ARMS


class Ref0140(unittest.TestCase):
    def test_rsxl_rule(self):
        self.assertEqual(rsxl_choice(20,8,[1,4],0,True),(0,'sp8'))    # deferred: SP8 choice whatever the sizes
        self.assertEqual(rsxl_choice(20,8,[1,4],0,False),(1,'rsx'))   # after the switch: the RSX rule
        self.assertEqual(rsxl_choice(8,8,[1,4],0,False),(0,'sp8'))    # burn-in: SP8 choice
        self.assertEqual(rsxl_choice(9,8,[2,2],1,False),(1,'sp8'))    # tie -> SP8 choice

    def test_constants(self):
        self.assertEqual(NS,(1,2,3,4,5));self.assertEqual(len(KINDS),20);self.assertEqual(len(MAIN_ARMS),11);self.assertEqual(OOD5_ARMS,('RG4','RG5'))
        self.assertEqual(sum(k.startswith('rsxl') for k in KINDS),4)


if __name__=='__main__':unittest.main()
