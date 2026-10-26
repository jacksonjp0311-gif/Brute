"""Unit tests for the study-012 scoring scripts (scoring_freeze_012; written after the source freeze)."""
import json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'scripts'))
import make_gates_012 as G,make_paired_012 as P,make_reproducibility_012 as R


class ScoringConstants(unittest.TestCase):
    def test_budgets_match_plan_plus_deviation_49(self):
        p=json.loads((ROOT/'experiments/BRUTE_PLAN_012.json').read_text())
        self.assertEqual(G.BUDGETS['big78'],2700)  # deviation #49 (rate math), plan says 1800
        self.assertEqual(G.EXPECTED,{'2x2':792,'big78':144,'transfer':288})
        self.assertEqual(G.CAP,7200)
        self.assertIn('stop_rule',p)

    def test_orchestrator_budgets_equal_gate_budgets(self):
        src=(ROOT/'scripts/run_study_012.py').read_text()
        for n,b in G.BUDGETS.items():self.assertIn(f"('{n}',",src);self.assertIn(f",{b},",src)

    def test_strip_timing_is_recursive(self):
        x={'a':1,'w_informational':2,'b':[{'c_wall_informational':3,'d':4}]}
        self.assertEqual(R.strip_timing(x),{'a':1,'b':[{'d':4}]})


class TransferContrast(unittest.TestCase):
    def case(self,fam,seed,sp8_cert,tr_cert):
        tr=[{'step':s,'certificate':(1 if s>=sp8_cert else None)} for s in range(13,45)]
        return {'family':fam,'seed':seed,'mask_rate':0.35,'arms':{'SP8':{'trace':tr}},
                'transfer':{'TRp':{'first_cert_step':tr_cert},'TRn':{'first_cert_step':sp8_cert}}}

    def test_saving_sign_and_null(self):
        cs=[self.case('cycle3',i,20,15) for i in range(4)]
        d=P.transfer_contrast(cs,'TRp');n=P.transfer_contrast(cs,'TRn')
        self.assertGreater(d['mean_S'],0);self.assertEqual(n['mean_S'],0)


if __name__=='__main__':unittest.main()
