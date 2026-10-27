import unittest
from experiments.v0130_reference import rsx_choice,ref_eb,certs,KINDS,NS,MAIN_ARMS,OOD5_ARMS


class Ref0130(unittest.TestCase):
    def test_rsx_rule(self):
        self.assertEqual(rsx_choice(8,8,[1,4],0),(0,'sp8'))     # burn-in: SP8 choice
        self.assertEqual(rsx_choice(9,8,[1,4],0),(1,'rsx'))     # larger bounded support wins
        self.assertEqual(rsx_choice(9,8,[3,2],1),(0,'rsx'))
        self.assertEqual(rsx_choice(9,8,[2,2],1),(1,'sp8'))     # tie -> SP8 choice
        self.assertEqual(rsx_choice(9,8,[1,1],0),(0,'sp8'))     # all singleton -> SP8 choice
        self.assertEqual(rsx_choice(9,8,[0,1],0),(0,'sp8'))     # None counts 0; max <= 1 -> SP8

    def test_eb_rule(self):
        steps=[{'t':t,'a':0,'cert':[None,None],'supp':[[1,2],[3]],'obs':(0,1),'act':[1,3]} for t in (1,2)]
        none=[[None,None],[None,None]]
        BS={'1':{'support':none},'2':{'support':[[[1,2],[3]],[[2],[3]]]},'3':{'support':[[[2],[3]],[[1],[3]]]},
            '4':{'support':[[[1,2],[0,3]],[[1,2],[0,3]]]}}
        r=ref_eb(steps,BS,burn=1,margin=1)
        self.assertEqual([x['n_E'] for x in r['trace']],[2,2]);self.assertEqual([x['bound'] for x in r['trace']],[3,3])
        self.assertEqual([x['certificate'] for x in r['trace']],[[None,None],[1,3]])
        self.assertEqual(r['eb_certificates'],2);self.assertEqual(r['false_certificates'],0);self.assertEqual(r['first_cert_step'],2)
        r2=ref_eb(steps,BS,burn=1,margin=2)
        self.assertEqual([x['bound'] for x in r2['trace']],[4,4]);self.assertEqual(r2['certificates'],0)
        self.assertEqual(certs(r),[[2,0,1],[2,1,3]])

    def test_constants(self):
        self.assertEqual(NS,(1,2,3,4,5));self.assertEqual(len(KINDS),20);self.assertEqual(len(MAIN_ARMS),11);self.assertEqual(OOD5_ARMS,('RG4','RG5'))


if __name__=='__main__':unittest.main()
