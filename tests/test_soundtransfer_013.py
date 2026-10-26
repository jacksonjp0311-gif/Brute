"""brute/soundtransfer.py + experiments/brute_study_013 transfer arms vs the second implementation (v0110_reference)."""
import unittest
from experiments.brute_common_013 import load,PLAN
import experiments.brute_study_013 as S
from experiments.v0110_reference import audit_transfer_case
from brute.soundtransfer import MODES


class SoundTransfer013(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan=load(PLAN);J=S.smoke_jobs(cls.plan,'transfer')
        cls.cases=[S.run_job(j,cls.plan)[1] for j in (J[0],J[6])]

    def test_reference_agrees(self):
        for c in self.cases:self.assertEqual(audit_transfer_case(c,self.plan),(True,None))

    def test_dr_subset_of_sp8(self):
        for c in self.cases:
            sp=c['arms']['SP8']['trace']
            for suf in 'pn':
                for r,d in zip(sp,c['transfer']['DR'+suf]['trace']):
                    R={r['action']:r,1-r['action']:r['counterfactual']}
                    for b in (0,1):
                        if d['certificate'][b] is not None:self.assertEqual(d['certificate'][b],R[b]['certificate'])

    def test_arms_complete(self):
        for c in self.cases:
            self.assertEqual(set(c['transfer']),{m+s for m in list(MODES)+['LX'] for s in 'pn'})
            for v in c['transfer'].values():self.assertEqual(len(v['trace']),44)

    def test_mutation_detected(self):
        import copy
        c=copy.deepcopy(self.cases[0]);t=c['transfer']['ATp']['trace'][10];t['alive']+=1
        self.assertFalse(audit_transfer_case(c,self.plan)[0])


if __name__=='__main__':unittest.main()
