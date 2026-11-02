"""Tests for brute.cover20/1 (v0.54.0, BRUTE_PLAN_057 design.cover20_policy). New file."""
import unittest
from brute.api import cover20 as CV


class Toy:
    """A 3-state, 2-action ring with outputs = state parity."""
    def __init__(self):self.q=0
    def step(self,a):self.q=(self.q+1+a)%3;return (self.q%2,)


class TestCover20(unittest.TestCase):
    def test_constants(self):
        self.assertEqual((CV.API,CV.H,CV.STEPS),('brute.cover20/1',1,120))

    def test_least_used_lowest_index(self):
        # h=0: the context is the latest (action, observation) pair; a repeated context moves to the next least-used action
        x=CV.Cover20((0,),3,h=0,steps=4);self.assertEqual(x.propose(),0);x.observe(0,(0,))
        self.assertEqual(x.propose(),0);x.observe(0,(0,));self.assertEqual(x.propose(),1);x.observe(1,(0,))
        self.assertEqual(x.propose(),0);x.observe(0,(0,));self.assertIsNone(x.propose())

    def test_prefix_counts(self):
        x=CV.Cover20((0,),2,h=0,steps=1)
        x.observe(0,(0,));x.observe(0,(0,))
        self.assertEqual(x.propose(),1)

    def test_context_h1(self):
        x=CV.Cover20((0,),2,h=1,steps=10);x.observe(0,(1,))
        # context (prev pair, current obs) is new, so the lowest action is proposed
        self.assertEqual(x.propose(),0)

    def test_refuses_mismatch(self):
        x=CV.Cover20((0,),2,steps=2);a=x.propose()
        with self.assertRaises(ValueError):x.observe(1-a,(0,))
        with self.assertRaises(ValueError):x.propose()
        with self.assertRaises(ValueError):CV.Cover20((0,),0)
        with self.assertRaises(ValueError):x.observe(5,(0,))

    def test_helper_deterministic(self):
        r=[]
        for _ in range(2):
            t=Toy();r.append(CV.cover20((0,),[],[],2,t.step,1,30))
        self.assertEqual(r[0],r[1]);self.assertEqual(len(r[0][0]),30)
        t=Toy();x=CV.Cover20((0,),2,1,30);acts=[]
        while (a:=x.propose()) is not None:acts.append(a);x.observe(a,t.step(a))
        self.assertEqual(acts,r[0][0]);self.assertTrue(x.result()['done'])

    def test_helper_length_check(self):
        with self.assertRaises(ValueError):CV.cover20((0,),[0],[],2,Toy().step)

    def test_pure(self):
        import inspect;src=inspect.getsource(CV)
        for bad in ('import os','import socket','import subprocess','import threading','open('):self.assertNotIn(bad,src)


if __name__=='__main__':unittest.main()
