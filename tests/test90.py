"""Exact finite-width support, budget rollback, adequacy and minimal quotient."""
import itertools, unittest
from random import Random
from bgr89.worlds import world,actions
from bgr90.symbolic import SymbolicLearner,mask_for_observation,Prefix
from bgr90.adequacy import AdequacyLearner
from bgr90.quotient import minimize_moore,reachable_states


def observable(trans,em,start,actions):
    s=start
    for action in actions:s=trans[s][action]
    return em[s]


def reference_pair_equivalent(trans,em,a,b):
    n=len(trans)
    for length in range(n+1):
        for word in itertools.product((0,1),repeat=length):
            if observable(trans,em,a,word)!=observable(trans,em,b,word):return False
    return True


class NewMathTests(unittest.TestCase):
    def test_observation_mask(self):
        self.assertEqual(mask_for_observation((None,None)),15)
        self.assertEqual(mask_for_observation((0,None)),0b0011)
        self.assertEqual(mask_for_observation((None,1)),0b1010)
        self.assertEqual(mask_for_observation((1,0)),0b0100)

    def test_exact_possible_next_outcomes_vs_complete_enumeration(self):
        # Independent complete-model reference, not the symbolic solver.
        for n in (1,2):
            machines=[]
            for trans_flat in itertools.product(range(n),repeat=n*2):
                tr=tuple(tuple(trans_flat[i*2:i*2+2]) for i in range(n))
                for emissions in itertools.product(range(4),repeat=n):
                    machines.append((tr,emissions))
            for seed in range(5):
                rng=Random(80111+seed)
                t_history=[];obs0=(rng.randrange(2),None)
                symbolic=SymbolicLearner(n,max_prefixes=5000)
                symbolic.initialize(obs0)
                for k in range(5):
                    a=rng.randrange(2)
                    predicted=symbolic.predict_support(a)
                    expected=set()
                    for tr,em in machines:
                        if not (obs0[0]==(em[0]>>1)):continue
                        cur=0;ok=True
                        for prev_a,ob in t_history:
                            cur=tr[cur][prev_a]
                            for j,b in enumerate(ob):
                                if b is not None and (em[cur]>>(1-j))&1 != b:ok=False
                            if not ok:break
                        if not ok:continue
                        dest=tr[cur][a]
                        expected.add(em[dest])
                    self.assertEqual(set(predicted or ()),expected)
                    # Choose a possible emission to keep at least one model alive.
                    result=sorted(expected)[rng.randrange(len(expected))]
                    observed=(result>>1,None) if k%2 else (None,result&1)
                    symbolic.observe(a,observed);t_history.append((a,observed))
                    self.assertEqual(symbolic.status,'supported')

    def test_four_state_world_never_excluded_within_grammar(self):
        for fam in ('cycle3','switch3','unstructured3','ood4'):
            w=world(11122,fam);s=w.start;solver=SymbolicLearner(4)
            solver.initialize(w.observed(s,.35,-1))
            for t,a in enumerate(actions(11122,35)):
                support=solver.predict_support(a)
                s=w.next(s,a)
                self.assertIn(w.emission(s),support)
                solver.observe(a,w.observed(s,.35,t))
                self.assertEqual(solver.status,'supported')

    def test_budget_failure_records_evidence_abstains_and_retry(self):
        l=SymbolicLearner(4,max_prefixes=4);l.initialize((None,None))
        l.observe(0,(None,None))
        l.observe(1,(None,None))
        l.observe(0,(None,None))
        self.assertEqual(l.status,'budget_exhausted')
        self.assertEqual(l.predict_support(0),None)
        self.assertEqual(len(l.evidence),4)
        recovered=l.reconstruct(max_prefixes=200000)
        self.assertEqual(recovered.status,'supported')
        self.assertEqual(len(recovered.evidence),4)

    def test_grammar_violation_preserves_evidence(self):
        l=SymbolicLearner(1);l.initialize((0,0));l.observe(0,(1,1))
        self.assertEqual(l.status,'grammar_contradicted')
        self.assertIsNone(l.predict_support(1))
        self.assertEqual(len(l.evidence),2)
        better=l.reconstruct(max_states=2)
        self.assertEqual(better.status,'supported')

    def test_unverified_grammar_never_issues_public_cert(self):
        l=AdequacyLearner(max_states=4,scope_verified=False)
        l.initialize((0,0))
        for _ in range(8):
            f=l.predict(0)
            self.assertIsNone(f.public_certificate)
            l.observe(0,(0,0))
        self.assertEqual(l.public_certs,0)
        self.assertFalse(l.diagnostics()['scope_verified_externally'])

    def test_lab_attestation_conditional_only_within_scope(self):
        l=AdequacyLearner(max_states=4,scope_verified=True)
        l.initialize((0,0))
        for _ in range(8):
            f=l.predict(0)
            self.assertEqual(f.public_certificate,f.conditional_certificate)
            l.observe(0,(0,0))
        l.retry(max_states=5)
        self.assertFalse(l.scope_verified)

    def test_sensor_alias_does_not_imply_equivalence(self):
        transitions=((1,0),(2,0),(2,0))
        emissions=(0,0,1)
        q=minimize_moore(transitions,emissions,0)
        self.assertEqual(q['minimal_count'],3)
        self.assertNotEqual(q['classes'][0],())
        self.assertFalse(reference_pair_equivalent(transitions,emissions,0,1))

    def test_twin_states_merge(self):
        transitions=((1,2),(1,2),(2,1))
        emissions=(0,1,1)
        q=minimize_moore(transitions,emissions,0)
        self.assertEqual(q['reachable_original_count'],3)
        self.assertEqual(q['minimal_count'],2)
        self.assertTrue(reference_pair_equivalent(transitions,emissions,1,2))

    def test_quotient_agrees_with_independent_future_word_reference(self):
        for n in (1,2,3,4):
            for seed in range(50):
                rng=Random(n*100000+seed)
                trans=tuple((rng.randrange(n),rng.randrange(n)) for _ in range(n))
                em=tuple(rng.randrange(4) for _ in range(n))
                q=minimize_moore(trans,em,0)
                reach=reachable_states(trans)
                mapping={s:i for i,grp in enumerate(q['classes']) for s in grp}
                for a in reach:
                    for b in reach:
                        self.assertEqual(mapping[a]==mapping[b],reference_pair_equivalent(trans,em,a,b))

    def test_permuting_hidden_state_labels_preserves_fingerprint(self):
        rng=Random(888)
        for n in (2,3,4):
            for _ in range(40):
                trans=tuple((rng.randrange(n),rng.randrange(n)) for _ in range(n))
                emissions=tuple(rng.randrange(4) for _ in range(n))
                permutation=list(range(n));rng.shuffle(permutation)
                new_index={old:i for i,old in enumerate(permutation)}
                perm_trans=tuple(tuple(new_index[t] for t in trans[old]) for old in permutation)
                perm_emit=tuple(emissions[old] for old in permutation)
                original=minimize_moore(trans,emissions,0)
                rewritten=minimize_moore(perm_trans,perm_emit,new_index[0])
                self.assertEqual(original['fingerprint'],rewritten['fingerprint'])

if __name__=='__main__':unittest.main()
