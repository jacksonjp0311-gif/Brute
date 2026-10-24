"""New causal representation, transfer, OOD and evidence-gating regression tests."""
import unittest,random,math
from bgr88.programs import (Program,ProgramLearner,OutsideModelFamily,catalogue,
                             essential_parent,OPERATOR_TABLES)
from bgr88.environments import make_world,walk,ood_two_target_trace
from bgr88.transfer import (source_train,motif_program_weights,motif_multiplicities,
                             uniform_motif_prior,uniform_program_prior)
from bgr88.evaluation import (prediction,evidence_logbf,adaptive_gate,world_record,summarize)
from bgr88.representation import roles

class V88Tests(unittest.TestCase):
    def test_essential_boolean_catalogue_is_unique(self):
        for n in (3,4,5):
            rules=catalogue(n,1)
            self.assertEqual(len(rules),n*(4+(n-1)*12))
            self.assertEqual(len(set(rules)),len(rules))
            for p in rules:
                if p.parents:self.assertTrue(essential_parent(p.table,len(p.parents),1))

    def test_source_motif_is_independent_of_channel_identity(self):
        for n in (4,5):
            for p in catalogue(n,1):
                perm=list(range(n))[::-1]
                q=Program(perm[p.target],tuple(perm[i] for i in p.parents),p.table)
                self.assertEqual(p.motif,q.motif)
                for bits in range(1<<n):
                    s=tuple((bits>>i)&1 for i in range(n))
                    transformed=[0]*n
                    for old,new in enumerate(perm):transformed[new]=s[old]
                    actual=[0]*n
                    for old,new in enumerate(perm):actual[new]=p.predict(s)[old]
                    self.assertEqual(q.predict(tuple(transformed)),tuple(actual))

    def test_models_infer_targets_not_oracle_labels(self):
        w=make_world(70031,'related')
        l=ProgramLearner(5,3)
        initial=roles(l)
        self.assertTrue(all(x['certified_target'] is None for x in initial['actions']))
        for s,a,t in walk(w,25,70031):l.observe(s,a,t)
        roles_after=roles(l)
        for label,p in zip(roles_after['actions'],w.actions):
            self.assertIn(p.target,label['possible_targets'])
            if label['certified_target'] is not None:self.assertEqual(label['certified_target'],p.target)
            self.assertTrue(set(label['necessary_parent_channels']).issubset(set(p.parents)))
        self.assertTrue(all(l.certify(s,a) in (None,w.transition(s,a)) for a in range(3)
                            for s in __import__('itertools').product((0,1),repeat=5)))

    def test_false_certification_not_authorized_by_prior(self):
        l=ProgramLearner(4,1,prior={p.motif:1e-8 for p in catalogue(4)})
        s=(0,0,1,1)
        self.assertIsNone(l.certify(s,0))
        prediction_dist=l.predict_distribution(s,0)
        self.assertAlmostEqual(sum(prediction_dist.values()),1)
        l.observe(s,0,(1,0,1,1))
        self.assertIsNone(l.certify((0,1,1,1),0))

    def test_atomic_contradiction_multi_target(self):
        l=ProgramLearner(4,1,allow_expand=True)
        s,t=ood_two_target_trace()
        before=l.snapshot()
        with self.assertRaises(OutsideModelFamily):l.observe(s,0,t)
        self.assertEqual(l.snapshot()['candidate_counts'],before['candidate_counts'])
        self.assertEqual(l.snapshot()['evidence_count'],before['evidence_count'])
        self.assertEqual(l.snapshot()['expansions'],before['expansions'])
        self.assertGreater(l.snapshot()['checks'],0)

    def test_parent_arity_expands_on_witness_without_reset(self):
        w=(Program(0,(1,2),0b01101001),Program(1,(),1),Program(2,(),1),Program(0,(),1))
        l=ProgramLearner(4,4,allow_expand=True)
        state=(0,0,0,0)
        rng=random.Random(0)
        for _ in range(80):
            a=rng.randrange(4);next_state=w[a].predict(state)
            l.observe(state,a,next_state);state=next_state
            if l.expansions:break
        self.assertTrue(l.expansions)
        self.assertGreaterEqual(l.expansions[0]['after_observation'],2)
        for a,before,after in l.evidence:
            self.assertTrue(any(p.predict(before)==after for p in l.banks[a]))
        self.assertEqual(len(l.evidence),l.expansions[0]['after_observation'])

    def test_trained_prior_uses_only_observed_source_evidence(self):
        p=source_train(801200,'related',worlds=24,steps=12,iterations=14)
        self.assertEqual(p.source_worlds,24)
        self.assertEqual(p.source_observations,24*12)
        self.assertAlmostEqual(sum(p.learned_mass.values()),1.,places=10)
        self.assertTrue(all(x>0 for x in p.weights.values()))
        self.assertNotEqual(p.learned_mass[(0,1)],p.learned_mass[(1,8)])

    def test_gate_decreases_transfer_trust_for_out_of_family_target(self):
        p=source_train(801300,'related',worlds=24,steps=16)
        t=source_train(801400,'shifted',worlds=24,steps=16)
        records=[world_record(801500+i,'shifted',p.weights,t.weights,checkpoint_steps=(0,2,8,14)) for i in range(12)]
        trust0=sum(r['checkpoint_rows'][0]['trust_source'] for r in records)/12
        trust14=sum(r['checkpoint_rows'][-1]['trust_source'] for r in records)/12
        self.assertAlmostEqual(trust0,.5)
        self.assertLess(trust14,trust0)
        self.assertTrue(all(row['incorrect_certified_unseen']==0 for r in records for row in r['checkpoint_rows']))

    def test_target_trace_has_no_reset_and_oracle_never_updates_models(self):
        source=source_train(801600,'related',worlds=20,steps=12).weights
        wrong=source_train(801700,'shifted',worlds=20,steps=12).weights
        r=world_record(801800,'related',source,wrong)
        self.assertEqual(r['trace'][0]['before'],r['initial'])
        for a,b in zip(r['trace'][:-1],r['trace'][1:]):
            self.assertEqual(a['after'],b['before'])
        self.assertEqual(len(r['checkpoint_rows']),5)
        self.assertTrue(all(x['incorrect_certified_unseen']==0 for x in r['checkpoint_rows']))

    def test_calibration_weights(self):
        learner=ProgramLearner(4,1)
        s=(0,0,0,0)
        for weights in (uniform_motif_prior(4),uniform_program_prior(4)):
            d=prediction(learner.banks[0],s,weights)
            self.assertAlmostEqual(sum(d.values()),1)
            self.assertTrue(all(0<p<1 for p in d.values()))
        self.assertAlmostEqual(adaptive_gate(0),0.5)
        self.assertLess(adaptive_gate(-10),.01)
        self.assertGreater(adaptive_gate(10),.99)

if __name__=='__main__':unittest.main()

class ProjectionTests(unittest.TestCase):
    def test_projection_proof_requires_all_candidate_parents_inside(self):
        from bgr88.representation import certify_state_projection
        l=ProgramLearner(4,1)
        self.assertFalse(certify_state_projection(l,(0,1))['proved_sufficient'])
        with self.assertRaises(ValueError):certify_state_projection(l,())

    def test_projection_evaluator_equivalence_without_oracle_leak(self):
        from bgr88.representation import inferred_minimal_projection
        from itertools import product
        world=make_world(780004,'related')
        learner=ProgramLearner(world.width,len(world.actions))
        for s,a,t in walk(world,30,780004):learner.observe(s,a,t)
        proj=inferred_minimal_projection(learner)
        keep=proj['projection']
        for a in range(len(world.actions)):
            for s in product((0,1),repeat=world.width):
                for r in product((0,1),repeat=world.width):
                    if all(s[i]==r[i] for i in keep):
                        v=world.transition(s,a);u=world.transition(r,a)
                        self.assertEqual(tuple(v[i] for i in keep),tuple(u[i] for i in keep))
        self.assertTrue(proj['proof']['proved_sufficient'])

    def test_known_unused_distractor_can_be_dropped(self):
        from bgr88.representation import inferred_minimal_projection
        from itertools import product
        program=Program(0,(1,),6)  # XOR self and observed bit 1
        l=ProgramLearner(4,1)
        for s in product((0,1),repeat=4):
            l.observe(s,0,program.predict(s))
        r=inferred_minimal_projection(l)
        self.assertEqual(r['projection'],(0,1))
        self.assertEqual(r['dropped'],(2,3))
