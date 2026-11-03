"""Ground truth for study BRUTE-0640-REALDECODER-068 (experiments/BRUTE_PLAN_068.json ground_truth).
WRITTEN BY HAND from the CPython v3.13.5 source (derivation and source sha256 in docs/research/TRUTH_068.md), before any Brute run
on these targets; not derived from Brute output. Read only by the recount and the gates; the runner and the certifiers never import it.
Moore view of the decoder (plan interface.machine): a state is (undecoded buffer, class of the last decode() output).
Emission code = 2*bit0 + bit1, bit0 = last output non-empty, bit1 = last output contains U+FFFD; codes 0 (''), 2 (chars, no U+FFFD),
3 (contains U+FFFD). transitions[state][action]; start 0. Every state below is reachable from the start and all are pairwise
distinguishable (TRUTH_068.md), so N_TRUE is the minimal size."""
from types import SimpleNamespace

# U3: utf-8, actions 0x41, 0x80, 0xE1
U3_NAMES=["('',none)","('',char)","('',fffd)","(E1,none)","(E1 80,none)","(E1,fffd)"]
U3_T=[[1,2,3],[1,2,3],[1,2,3],[2,4,5],[2,1,5],[2,4,5]]
U3_E=[0,2,3,0,0,3]

# U4: utf-8, actions 0x41, 0x80, 0xF1
U4_NAMES=["('',none)","('',char)","('',fffd)","(F1,none)","(F1 80,none)","(F1 80 80,none)","(F1,fffd)"]
U4_T=[[1,2,3],[1,2,3],[1,2,3],[2,4,6],[2,5,6],[2,1,6],[2,4,6]]
U4_E=[0,2,3,0,0,0,3]

# W16: utf-16-le, actions 0x41, 0xD8, 0xDC (one byte each); x, z = any earlier byte
W16_NAMES=["('',none)","(x,none)","('',char)","('',fffd)","(x D8,none)","(x D8 z,none)","(x D8,fffd)"]
W16_T=[[1,1,1],[2,4,3],[1,1,1],[1,1,1],[5,5,5],[3,6,2],[5,5,5]]
W16_E=[0,0,2,3,0,0,3]

TARGETS={'U3':('utf-8',(0x41,0x80,0xE1),U3_T,U3_E,U3_NAMES),
         'U4':('utf-8',(0x41,0x80,0xF1),U4_T,U4_E,U4_NAMES),
         'W16':('utf-16-le',(0x41,0xD8,0xDC),W16_T,W16_E,W16_NAMES)}
N_TRUE={'U3':6,'U4':7,'W16':7}


def world(name):
    """The hand truth as a world object (n, k, s, start, transitions, emissions) for truth_label / beq."""
    codec,bs,T,E,names=TARGETS[name]
    return SimpleNamespace(n=len(T),k=len(bs),s=2,start=0,transitions=[list(r) for r in T],emissions=list(E),names=list(names),codec=codec,bytes=bs)
