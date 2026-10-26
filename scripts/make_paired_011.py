"""Paired, seed-clustered bootstraps for study-011 (BRUTE_PLAN_011 scoring.bootstrap). Committed and ledgered
(scoring_freeze_011) before the held-out run_start; nothing is tuned after results are seen.

Method (the frozen make_paired_009 estimator, imported unchanged): 2000 resamples, numpy default_rng(20261026), one
fresh generator per contrast, seeds resampled with replacement WITHIN each family (each seed = its 3 mask cases);
per-family statistic = sum over resampled seeds of (X - Y certified forecasts over the seed's mask cases, post-burn-in
steps, taken + counterfactual) / sum of forecasts; pooled = unweighted mean over the listed families (plan order);
95% CI = percentiles 2.5/97.5.
Gated: G6b_dual_coverage_J9_minus_A2 on in_family_original_2x2. Reported: J9-SP8 (in_family_original and all
in_family_2x2), SP8-A2 and A4-A2 (in_family_original), point coverage of every arm on every family."""
from __future__ import annotations
import argparse,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common_011 import STUDY_DIR,PLAN,load,dumps,write_new,check,sha
from scripts.make_paired_009 import contrast,coverage,B,SEED


def build(study=STUDY_DIR,smoke=False):
    study=Path(study);plan=load(PLAN)
    check('2000 resamples, numpy default_rng(20261026)' in plan['scoring']['bootstrap'],'bootstrap registration changed')
    d2=load(study/'2x2'/'SCIENTIFIC.json');s2=load(study/'2x2'/'SEAL.json')
    check(s2['scientific_sha256']==sha(study/'2x2'/'SCIENTIFIC.json'),'2x2 SCIENTIFIC does not match its SEAL')
    two={f:[c for c in d2['cases'] if c['family']==f] for f in plan['heldout_ranges_2x2']};two={f:v for f,v in two.items() if v}
    IF=[f for f in plan['in_family_2x2'] if f in two];IFO=[f for f in plan['in_family_original_2x2'] if f in two]
    return {'schema':'brute.paired-analysis.v9_0','study':plan['study'],'resamples':B,'seed':SEED,'cluster':'seed within family',
            'scope':'post-burn-in steps; 2x2 dual coverage (taken + counterfactual)','smoke_dry_run':smoke,
            'scientific_sha256':{'2x2':s2['scientific_sha256']},'complete':{'2x2':d2.get('complete')},
            'G6b_dual_coverage_J9_minus_A2':contrast(two,IFO,'J9','A2'),
            'R_J9_minus_SP8_in_family_original':contrast(two,IFO,'J9','SP8'),
            'R_J9_minus_SP8_in_family':contrast(two,IF,'J9','SP8'),
            'R_SP8_minus_A2_in_family_original':contrast(two,IFO,'SP8','A2'),
            'R_A4_minus_A2_in_family_original':contrast(two,IFO,'A4','A2'),
            'R_coverage_all_point':{'2x2':{a:coverage(two,list(two),a) for a in plan['arms_by_block']['2x2']}}}


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--study-dir',default=str(STUDY_DIR));ap.add_argument('--check',action='store_true')
    ap.add_argument('--smoke',action='store_true',help='dry run on a smoke directory; prints, writes nothing')
    a=ap.parse_args()
    if a.smoke:obj=build(Path(a.study_dir),smoke=True);print(dumps(obj).decode()[:4000]);raise SystemExit
    obj=build(Path(a.study_dir));out=Path(a.study_dir)/'PAIRED_ANALYSIS_011.json'
    if a.check:check(out.read_bytes()==dumps(obj),'PAIRED_ANALYSIS_011.json does not reproduce');print('PAIRED_ANALYSIS_011 reproduces')
    else:write_new(out,obj);print(dumps(obj).decode()[:3000])
