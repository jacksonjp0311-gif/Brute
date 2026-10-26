"""Paired, seed-clustered bootstraps for study-010 (BRUTE_PLAN_010 scoring.bootstrap). Committed and ledgered
(scoring_freeze_010) before the held-out run_start; nothing is tuned after results are seen.

Method (the frozen make_paired_009 estimator, imported unchanged): 2000 resamples, numpy default_rng(20261026), one
fresh generator per contrast, seeds resampled with replacement WITHIN each family (each seed = its 3 mask cases);
per-family statistic = sum over resampled seeds of (X - Y certified forecasts over the seed's mask cases, post-burn-in
steps, taken + counterfactual) / sum of forecasts; pooled = unweighted mean over the listed families (plan order);
95% CI = percentiles 2.5/97.5. Breadth contrasts use all k forecasts of each step.
Gated: G6b_dual_coverage_{J8,SP8}_minus_A2 on in_family_original_2x2. Reported: SP8-SC7, SC7-A2, A4-A2 (in_family_original),
SP8-SC7 and J8-SC7 on all in-family 2x2, BSP8-BSC7 and BSC7-B5 (in-family breadth), point coverage of every arm."""
from __future__ import annotations
import argparse,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common_010 import STUDY_DIR,PLAN,load,dumps,write_new,check,sha
from scripts.make_paired_009 import contrast,coverage,B,SEED


def block(study,name):
    d=load(study/name/'SCIENTIFIC.json');s=load(study/name/'SEAL.json')
    check(s['scientific_sha256']==sha(study/name/'SCIENTIFIC.json'),f'{name} SCIENTIFIC does not match its SEAL')
    return d,s


def build(study=STUDY_DIR,smoke=False):
    study=Path(study);plan=load(PLAN)
    check('2000 resamples, numpy default_rng(20261026)' in plan['scoring']['bootstrap'],'bootstrap registration changed')
    d2,s2=block(study,'2x2');db,sb=block(study,'breadth')
    two={f:[c for c in d2['cases'] if c['family']==f] for f in plan['heldout_ranges_2x2']};two={f:v for f,v in two.items() if v}
    br={f:[c for c in db['cases'] if c['family']==f] for f in plan['heldout_ranges_breadth']};br={f:v for f,v in br.items() if v}
    IF=[f for f in plan['in_family_2x2'] if f in two];IFO=[f for f in plan['in_family_original_2x2'] if f in two]
    IB=[f for f in plan['in_family_breadth'] if f in br]
    return {'schema':'brute.paired-analysis.v8_0','study':plan['study'],'resamples':B,'seed':SEED,'cluster':'seed within family',
            'scope':'post-burn-in steps; 2x2 dual coverage (taken + counterfactual); breadth all-action coverage','smoke_dry_run':smoke,
            'scientific_sha256':{'2x2':s2['scientific_sha256'],'breadth':sb['scientific_sha256']},
            'complete':{'2x2':d2.get('complete'),'breadth':db.get('complete')},
            'G6b_dual_coverage_J8_minus_A2':contrast(two,IFO,'J8','A2'),
            'G6b_dual_coverage_SP8_minus_A2':contrast(two,IFO,'SP8','A2'),
            'R_SP8_minus_SC7_in_family_original':contrast(two,IFO,'SP8','SC7'),
            'R_dual_coverage_SC7_minus_A2':contrast(two,IFO,'SC7','A2'),
            'R_dual_coverage_A4_minus_A2':contrast(two,IFO,'A4','A2'),
            'R_SP8_minus_SC7_in_family':contrast(two,IF,'SP8','SC7'),
            'R_J8_minus_SC7_in_family':contrast(two,IF,'J8','SC7'),
            'R_BSP8_minus_BSC7':contrast(br,IB,'BSP8','BSC7',True),
            'R_BSC7_minus_B5':contrast(br,IB,'BSC7','B5',True),
            'R_coverage_all_point':{'2x2':{a:coverage(two,list(two),a) for a in plan['arms_by_block']['2x2']},
                                    'breadth':{a:coverage(br,list(br),a,True) for a in plan['arms_by_block']['breadth']}}}


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--study-dir',default=str(STUDY_DIR));ap.add_argument('--check',action='store_true')
    ap.add_argument('--smoke',action='store_true',help='dry run on a smoke directory; prints, writes nothing')
    a=ap.parse_args()
    if a.smoke:obj=build(Path(a.study_dir),smoke=True);print(dumps(obj).decode()[:4000]);raise SystemExit
    obj=build(Path(a.study_dir));out=Path(a.study_dir)/'PAIRED_ANALYSIS_010.json'
    if a.check:check(out.read_bytes()==dumps(obj),'PAIRED_ANALYSIS_010.json does not reproduce');print('PAIRED_ANALYSIS_010 reproduces')
    else:write_new(out,obj);print(dumps(obj).decode()[:3000])
