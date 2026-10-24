"""Independently reconstruct all partial-hypothesis supports and true outcomes.

The reference finite-machine constraint code is separate from the vectorized
v0.89 learner and bgr90.support; no hidden teacher state reaches the policy.
"""
from __future__ import annotations
from pathlib import Path
from hashlib import sha256
import json,argparse
from experiments.v90_independent_reference import audit_case,independently_count_minimal
from bgr90.evaluation import aggregate,FAMILIES
from bgr90.quotient import minimize_moore
from bgr89.worlds import world as old_world
from bgr90.worlds import world as new_world
ROOT=Path(__file__).resolve().parents[1]

def sha(path):return sha256(Path(path).read_bytes()).hexdigest()


def audit(directory):
    directory=Path(directory);result=json.loads((directory/'RESULTS.json').read_text());seal=json.loads((directory/'SEAL.json').read_text())
    for filename,key in (('RESULTS.json','results_sha256'),('SCIENTIFIC.json','scientific_sha256')):
        assert sha(directory/filename)==seal[key]
    assert result['plan']==json.loads((ROOT/'experiments/PLAN.json').read_text())
    assert sha(ROOT/'experiments/PLAN.json')==seal['plan_sha256']
    assert sha(ROOT/'experiments/SOURCE_FREEZE.json')==seal['freeze_sha256']
    freeze=json.loads((ROOT/'experiments/SOURCE_FREEZE.json').read_text())
    for rel,digest in freeze['sha256_files'].items():
        assert sha(ROOT/rel)==digest,rel
    from experiments.run_study import no_time
    assert no_time(result)==json.loads((directory/'SCIENTIFIC.json').read_text())
    assert aggregate(result['cases'])==result['summary']
    p=result['plan'];total_cases=len(result['cases']);unique=set();result_counts={}
    predictions=conditional=wrong=legacywrong=0
    budget=contradictions=0;logloss_sums={}
    for i,c in enumerate(result['cases']):
        assert c['family'] in p['heldout_ranges'];bounds=p['heldout_ranges'][c['family']]
        assert bounds[0]<=c['seed']<=bounds[1]
        assert c['mask_rate'] in p['mask_rates']
        key=(c['family'],c['seed'],c['mask_rate']);assert key not in unique;unique.add(key)
        tally=audit_case(c,p)
        predictions+=tally['predictions_checked'];conditional+=tally['conditional_certifications_checked']
        wrong+=tally['conditional_false_certifications'];legacywrong+=tally['legacy_false_certifications']
        budget+=c['expanded_status']=='budget_exhausted'
        contradictions+=c['expanded_status']=='grammar_contradicted'
        if c['within_proposed_4_state_grammar']:assert tally['conditional_false_certifications']==0
    assert len(unique)==total_cases==seal['case_count']
    # Separate brute-force word-equivalence reference for exact Moore quotient.
    quotient_records=[];mischecks=0
    for fam in ('cycle3','switch3','unstructured3','unaliased2','ood4'):
        lo,hi=p['heldout_ranges'][fam]
        for seed in range(lo,hi+1):
            world=old_world(seed,fam)
            q=minimize_moore(world.transitions,world.emissions,world.start)
            independent=independently_count_minimal(world.transitions,world.emissions,world.start)
            assert q['minimal_count']==independent
            quotient_records.append({'family':fam,'seed':seed,'nominal':world.n,
                                     'minimal':independent,'reachable':q['reachable_original_count'],
                                     'fingerprint':q['fingerprint']})
    return {'schema':'bgr90.independent-audit.v1','status':'passed',
            'source_study_sha256':sha(directory/'RESULTS.json'),
            'worlds_unique':total_cases,'observations_replayed':predictions,
            'conditional_certificates_independently_recomputed':conditional,
            'conditional_false_certificates_all_families':wrong,
            'legacy_three_state_false_certificates':legacywrong,
            'unattested_public_certificates':0,'out_of_scope_contradictions':contradictions,
            'budget_exhaustions':budget,'complete_world_quotients_bruteforce_audited':len(quotient_records),
            'original_state_count_gt_minimal':sum(r['nominal']>r['minimal'] for r in quotient_records),
            'reference_moore_quotient_examples':quotient_records[:15],
            'claim_scope':'Independent Python solver reconstructs possible hidden state paths and all next-emission supports; same synthetic reference worlds used for truth. No external scientific replication. Public certificates were suppressed without an external scope attestation.'}


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--results-dir',default=str(ROOT/'results/study-001'))
    parser.add_argument('--write',action='store_true');args=parser.parse_args()
    report=audit(args.results_dir)
    if args.write:
        dest=Path(args.results_dir)/'INDEPENDENT_AUDIT.json'
        if dest.exists():raise RuntimeError('refuse audit overwrite')
        dest.write_text(json.dumps(report,sort_keys=True,indent=2)+'\n')
    print(json.dumps(report,indent=2))
