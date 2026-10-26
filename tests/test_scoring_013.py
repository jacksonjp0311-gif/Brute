"""Unit tests for the study-013 scoring scripts (scoring_freeze_013; written after the source freeze)."""
import json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'scripts'))
import make_gates_013 as G,make_paired_013 as P,make_reproducibility_013 as R,clean_clone_013 as CC


class ScoringConstants(unittest.TestCase):
    def test_constants_match_plan(self):
        p=json.loads((ROOT/'experiments/BRUTE_PLAN_013.json').read_text())
        self.assertEqual(G.EXPECTED,{'2x2':792,'big78':288,'transfer':288})
        self.assertEqual(G.CAP,7200);self.assertEqual(G.G11_BUDGET,1800);self.assertEqual(G.G78_MIN_CERTS,150)
        self.assertEqual(set(G.TR_ARMS)|{'SP8'},set(p['arms_by_block']['transfer']))
        self.assertEqual(G.BIG_ARMS,tuple(p['arms_by_block']['big78']))
        for k in ('GST_sound_transfer','GS_a_transfer_soundness','GS_b_dual_region_subset','GS_c_wrong_family_control',
                  'GS_d_AT_speedup','GS_e_LX_speedup','GS_ref_transfer_audit','GAPI_embeddable_certify'):self.assertIn(k,p['criteria'])
        self.assertIn('GA1_012_support_drift_and_coverage',p['retired_gates'])

    def test_orchestrator_budgets_equal_gate_budgets(self):
        src=(ROOT/'scripts/run_study_013.py').read_text()
        for n,b in G.BUDGETS.items():self.assertIn(f"('{n}',",src);self.assertIn(f",{b},",src)

    def test_strip_timing_is_recursive(self):
        x={'a':1,'w_informational':2,'b':[{'c_wall_informational':3,'d':4}]}
        self.assertEqual(R.strip_timing(x),{'a':1,'b':[{'d':4}]})

    def test_clean_clone_inputs(self):
        self.assertIn('results/study-013/KILL_DRILL_013.json',CC.TRACKED)
        self.assertIn('results/study-013/GATES_013.json',CC.TRACKED)


class TransferContrast(unittest.TestCase):
    def case(self,fam,seed,sp8_cert,x_cert):
        tr=[{'step':s,'certificate':(1 if s>=sp8_cert else None)} for s in range(1,45)]
        return {'family':fam,'seed':seed,'mask_rate':0.35,'arms':{'SP8':{'trace':tr}},
                'transfer':{'LXp':{'first_cert_step':x_cert},'LXn':{'first_cert_step':sp8_cert}}}

    def test_saving_sign_and_null(self):
        cs=[self.case('cycle3',i,20,15) for i in range(4)]
        d=P.transfer_contrast(cs,'LXp');n=P.transfer_contrast(cs,'LXn')
        self.assertEqual(d['mean_S'],5.0);self.assertEqual(n['mean_S'],0);self.assertEqual(n['ci95'],[0.0,0.0])


if __name__=='__main__':unittest.main()
