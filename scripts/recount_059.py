"""G_recount for study-059 (BRUTE_PLAN_059 G_recount; pre-run deviation #192; new file; uses no brute/ code). Per record: rebuild the
trace from experiments/worlds_058 'scale20r4' (prefix = worlds_026 actions, eps 0, plus the recorded extra actions) and recompute the
true codes. For noisy arms the reading noise is regenerated INDEPENDENTLY of worlds_059 and brute/api: this file re-implements the
anytime k rule (smallest odd k with 4*exp(-2k(1/2-eps_bar)^2) <= delta*6/(pi^2 t^2)) and the seeded flip order
(random.Random(seed*13+590+round(1000*eps)), one random() per bit in order (t, read, bit)), takes the per-bit majority and checks the
recorded prefix and extra masks equal 1 << majority code, the recorded reads_per_obs, reads_total, maj_errors and maj_bit_errors; for
C4 the masks must equal 1 << true code. Then the final model's consistency with the recorded (majority) trace, n_min <= 20, and the
truth label against the CLEAN world (ID from the start state, IDF from s1 against the true current state; AMB / K_spent -> AMB;
unknown -> IDU; none -> NOFIT). Then recount ID+IDF per arm. PASS iff every record matches and the recounted counts equal the study's.
Writes <study>/RECOUNT_059.json (refuses overwrite).
  PYTHONPATH=. python scripts/recount_059.py results/study-059/main"""
import json,math,random,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common import load,write_new,sha
from experiments import worlds_058 as W58
from scripts.recount_058 import _eq,_consistent
ARMS=('C4','N4_05','N4_10','N4_10b','NEG4');NOISE={'C4':(0.0,None),'N4_05':(0.05,0.10),'N4_10':(0.10,0.15),'N4_10b':(0.10,0.15),'NEG4':(0.25,0.10)}
SB=4;DELTA=0.001


def k_for(t,eb,delta=DELTA,b=SB):
    k=max(1,math.ceil(math.log(b*math.pi**2*t*t/(6.0*delta))/(2.0*(0.5-eb)**2)-1e-12));return k+1 if k%2==0 else k


def _bits(c):return [(c>>(SB-1-j))&1 for j in range(SB)]


def _code(bs):
    v=0
    for b in bs:v=2*v+b
    return v


def recount_case(c):
    out={};bad=[]
    for arm,a in c['arms'].items():
        eps,eb=NOISE[arm];w=W58.world(c['seed'],'scale20r4');pa=list(W58.actions(c['seed'],0.0,w.k));acts=pa+list(a['extra_acts'])
        q=w.start;codes=[w.emissions[q]]
        for x in acts:q=w.transitions[q][x];codes.append(w.emissions[q])
        if a['family']!='scale20r4' or a['read_bits']!=SB or a['eps']!=eps or a['eps_bar']!=eb:bad.append((arm,'family/bits/noise'))
        if eb is None:maj=list(codes);ks=[1]*len(codes);me=mb=0
        else:
            rng=random.Random(c['seed']*13+590+int(round(1000*eps)));maj=[];ks=[];me=mb=0
            for t,cd in enumerate(codes,1):
                k=k_for(t,eb);ks.append(k);clean=_bits(cd);ones=[0]*SB
                for _ in range(k):
                    for j in range(SB):ones[j]+=clean[j]^(1 if rng.random()<eps else 0)
                m=[1 if 2*o>k else 0 for o in ones];e=sum(x!=y for x,y in zip(m,clean));mb+=e;me+=e>0;maj.append(_code(m))
        if [1<<x for x in maj[:len(pa)+1]]!=list(a['prefix_masks']):bad.append((arm,'prefix_readings'))
        if [1<<x for x in maj[len(pa)+1:]]!=list(a['extra_masks']):bad.append((arm,'extra_readings'))
        if list(a['reads_per_obs'])!=ks or a['reads_total']!=sum(ks):bad.append((arm,'reads'))
        if a['maj_errors']!=me or a['maj_bit_errors']!=mb:bad.append((arm,'maj_errors',a['maj_errors'],me))
        m=a['model'];stop=a['stop']
        if m is not None and not _consistent(m[0],m[1],acts,maj):bad.append((arm,'model_inconsistent'))
        if m is not None and (len(m[0])!=a['n_min'] or a['n_min']>20):bad.append((arm,'n_min'))
        if stop=='unknown':lab='IDU'
        elif stop in ('AMB','K_spent'):lab='AMB'
        elif stop=='none':lab='NOFIT'
        elif m is None:lab='WRONG'
        elif stop=='ID':lab='ID' if _eq(m[0],m[1],0,w.transitions,w.emissions,w.start) else 'WRONG'
        elif stop=='IDF':lab='IDF' if _eq(m[0],m[1],a['s1'],w.transitions,w.emissions,q) else 'WRONG'
        else:lab='WRONG'
        if lab!=a['label']:bad.append((arm,'label',a['label'],lab))
        out[arm]={'label':lab,'stop':stop,'steps':len(acts),'maj_errors':me,'reads_total':sum(ks)}
    return out,bad


def main(argv):
    study=Path(argv[0]);R=load(study/'RESULTS.json');recs={};bad=[];cnt={g:0 for g in ARMS};study_cnt={g:0 for g in ARMS}
    for c in R['cases']:
        o,b=recount_case(c);recs[str(c['seed'])]=o;bad+=[[c['seed']]+list(x) for x in b]
        for g,v in o.items():cnt[g]+=v['label'] in ('ID','IDF')
        for g,v in c['arms'].items():study_cnt[g]+=v['label'] in ('ID','IDF')
    wrong={g:sum(1 for o in recs.values() for h,v in o.items() if h==g and v['label']=='WRONG') for g in ARMS}
    rep={'schema':'brute.recount.v59','results_sha256':sha(study/'RESULTS.json'),'cases':len(R['cases']),'records':sum(len(o) for o in recs.values()),
         'mismatches':bad,'decided_by_arm':cnt,'study_decided_by_arm':study_cnt,'wrong_by_arm':wrong,'per_case':recs,
         'PASS':not bad and cnt==study_cnt}
    write_new(study/'RECOUNT_059.json',rep);print(json.dumps({k:rep[k] for k in ('records','mismatches','decided_by_arm','wrong_by_arm','PASS')}))
    return 0 if rep['PASS'] else 1


if __name__=='__main__':sys.exit(main(sys.argv[1:]))
