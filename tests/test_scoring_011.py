"""Data-independent checks of the study-011 scoring scripts (the full dry run on a smoke directory is ledgered with
scoring_freeze_011). Nothing here reads results/study-011."""
import ast,unittest
from pathlib import Path
from experiments.brute_common import load
from scripts import make_gates_011 as G, make_paired_011 as P, make_reproducibility_011 as R, clean_clone_011 as CC
ROOT=Path(__file__).resolve().parents[1];PLAN=load(ROOT/'experiments/BRUTE_PLAN_011.json')


class Scoring011(unittest.TestCase):
    def test_lag_and_drift_definition(self):
        assert G.DRIFT==(12,23,34) and G.lag(12) is None and G.lag(13)==1 and G.lag(15)==3 and G.lag(24)==1 and G.lag(44)==10
        assert not G.nondrift(12) and not G.nondrift(23) and not G.nondrift(5) and G.nondrift(13) and G.nondrift(35)
        assert 'step > 12' in PLAN['drift_definition'] or '12' in str(PLAN['drift_definition'])


    def test_constants_match_plan(self):
        assert G.EXPECTED==792 and G.CAP==7200 and G.G11_BUDGET==1500 and G.GH_STEPS==(14,15,16) and G.TAU6==PLAN['tau6']['value']
        assert set(PLAN['arms_by_block']['2x2'])==set(G.ALL) and R.BLOCKS==('2x2',)
        assert 'cap' in PLAN['stop_rule'] and '7200' in PLAN['stop_rule']['cap']


    def test_every_gated_criterion_is_scored(self):
        src=(ROOT/'scripts/make_gates_011.py').read_text()
        for name,c in PLAN['criteria'].items():
            if isinstance(c,dict) and c.get('gated',True):assert f"'{name}'" in src,name


    def test_scoring_inputs_cover_what_gates_read(self):
        src=(ROOT/'scripts/make_gates_011.py').read_text()
        names={Path(p).name for p in CC.TRACKED+CC.OPTIONAL_TRACKED+CC.RAW_GZ}
        for lit in {n.value for n in ast.walk(ast.parse(src)) if isinstance(n,ast.Constant) and isinstance(n.value,str)}:
            if lit.endswith(('.json','.jsonl')) and lit.isidentifier() is False and '/' not in lit and lit[0].isupper():
                assert lit in names,lit
