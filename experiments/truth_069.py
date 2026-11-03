"""Ground truth for study BRUTE-0650-RESETDECODER-069 (experiments/BRUTE_PLAN_069.json ground_truth).
U3, U4, W16: copied unchanged from experiments/truth_068.py (hand-derived for v0.64.0). EJ and GB: WRITTEN BY HAND from the CPython
v3.13.5 source (derivation and source sha256 in docs/research/TRUTH_069.md) before any run of brute.certify/32r on them; not derived
from Brute output. Read only by the truthcheck, recount and gates; the runner and the certifiers never import it.
Moore view: state = (undecoded buffer, class of the last decode() output); emission code 2*bit0+bit1: 0 (''), 2 (chars, no U+FFFD),
3 (contains U+FFFD). transitions[state][action]; start 0 (a fresh decoder)."""
from types import SimpleNamespace
from experiments import truth_068 as T68

# EJ: euc_jp, actions 0x41, 0x8F, 0xA1 (multibytecodec pending buffer + DECODER(euc_jp))
EJ_NAMES=["('',none)","('',char)","('',fffd)","(8F,none)","(A1,none)","(8F 41,none)","(8F 8F,none)","(8F A1,none)",
          "(8F,fffd)","(A1,fffd)","(8F 41,fffd)","(8F 8F,fffd)","(8F A1,fffd)"]
EJ_T=[[1,3,4],[1,3,4],[1,3,4],[5,6,7],[2,8,1],[2,8,9],[10,11,12],[2,8,2],[5,6,7],[2,8,1],[2,8,9],[10,11,12],[2,8,2]]
EJ_E=[0,2,3,0,0,0,0,0,3,3,3,3,3]

# GB: gb18030, actions 0x41, 0x81, 0x30 (multibytecodec pending buffer + DECODER(gb18030)); x = 41 or 30
GB_NAMES=["('',none)","('',char)","('',fffd)","(81,none)","(81,fffd)","(81 30,none)","(81 30 x,none)","(81 30 81,none)"]
GB_T=[[1,3,1],[1,3,1],[1,3,1],[1,1,5],[1,1,5],[6,7,6],[2,4,2],[2,2,1]]
GB_E=[0,2,3,0,3,0,0,0]

TARGETS=dict(T68.TARGETS)
TARGETS['EJ']=('euc_jp',(0x41,0x8F,0xA1),EJ_T,EJ_E,EJ_NAMES)
TARGETS['GB']=('gb18030',(0x41,0x81,0x30),GB_T,GB_E,GB_NAMES)
N_TRUE={'U3':6,'U4':7,'W16':7,'EJ':13,'GB':8}


def world(name):
    codec,bs,T,E,names=TARGETS[name]
    return SimpleNamespace(n=len(T),k=len(bs),s=2,start=0,transitions=[list(r) for r in T],emissions=list(E),names=list(names),codec=codec,bytes=bs)
