import unittest
from scripts.open_world_counterexample import completion_pair,replay,audit_witnesses

class FinitePrefixLimitTests(unittest.TestCase):
    def test_any_single_prefix_has_divergent_completion(self):
        for history in [[(None,(0,0))],[(None,(None,1)),(1,(0,None)),(0,(1,1))]]:
            for next_action in (0,1):
                a,b=completion_pair(history,next_action)
                self.assertEqual(replay(a,history,next_action),0)
                self.assertEqual(replay(b,history,next_action),3)
    def test_randomized_mixed_masks_and_actions(self):
        self.assertEqual(audit_witnesses(120)['status'],'passed')

if __name__=='__main__':unittest.main()
