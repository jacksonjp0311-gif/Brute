"""No-model-weight local demonstration; observations are real simulated actions."""
import json
from bgr89.worlds import world,actions
from bgr90.adequacy import AdequacyLearner
from bgr90.quotient import minimize_moore
from scripts.open_world_counterexample import audit_witnesses


def main():
    seed=970007;truth=world(seed,'ood4');hidden=truth.start
    model=AdequacyLearner(max_states=4,max_prefixes=160000,scope_verified=False)
    model.initialize(truth.observed(hidden,.35,-1))
    conditional=wrong=legacy_wrong=0
    for t,a in enumerate(actions(seed,44)):
        f=model.predict(a)
        hidden=truth.next(hidden,a)
        actual=truth.emission(hidden)
        conditional+=f.conditional_certificate is not None
        wrong+=f.conditional_certificate is not None and f.conditional_certificate!=actual
        legacy_wrong+=f.prior_three_state_certificate is not None and f.prior_three_state_certificate!=actual
        assert f.public_certificate is None
        model.observe(a,truth.observed(hidden,.35,t))
    assert wrong==0 and model.status=='supported'
    quotient=minimize_moore(truth.transitions,truth.emissions,truth.start)
    print(json.dumps({'version':'0.90.0','world':'four-state deterministic hidden sensor test','seed':seed,
          'actions':44,'conditional_certifications':conditional,'false_expanded_conditional_certifications':wrong,
          'legacy_three_state_false_certifications':legacy_wrong,
          'legacy_model_contradicted':not model.legacy_valid,'expanded_status':model.status,
          'public_certifications':'NONE: external scope has not been validated',
          'minimal_predictive_states_EVALUATOR_ONLY':quotient['minimal_count'],
          'open_world_counterexample':audit_witnesses(20)['status'],
          'AGI_claim':'not demonstrated','BitWatts_electrical':'unmeasured'},indent=2))

if __name__=='__main__':main()
