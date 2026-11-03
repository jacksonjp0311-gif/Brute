"""G_recount65 / GMAJ65 recount for study-065 (BRUTE_PLAN_065 G_recount65; new file, built from scripts/recount_064.py (frozen); uses no
brute/ search code and NOT brute.api.certify20s: the stopping rule and the noise stream are re-implemented here from the plan text).
Per record: rebuild the trace from experiments/worlds_065 (prefix = worlds_026 actions, eps 0, plus the recorded extra actions),
recompute the true codes, check the recorded prefix and extra masks (1 << code; for a noisy arm the masks are the SETTLED readings,
so any settled-bit error shows as a mismatch here), K accounting (used = extra actions, <= 400), the final model's consistency with
the whole trace, the read width (2), the bound (20) and the truth label (ID from the start state, IDF from s1 against the true
current state; AMB / K_spent -> AMB; unknown -> IDU). For each noisy arm it ALSO regenerates the raw reading stream from
random.Random(seed*13+650+int(round(1000*eps))) (order t, read, bit; flip iff draw < eps), re-applies the random-walk rule
(m_t = smallest m >= 1 with 2 r^m/(1+r^m) <= delta 6/(pi^2 t^2), r = eps_bar/(1-eps_bar), done in exact fractions) and checks
reads_per_obs, thresholds, settle_at, reads_total, settled_bit_errors, settled_obs_errors, readings_sha256 and
fixed_reads_total (sum of certify20n's frozen reads_for; the one brute import, a pure arithmetic function).
PASS iff every record matches and the recounted per-arm decided counts equal the study's. Writes <study>/RECOUNT_065.json.
  PYTHONPATH=. python scripts/recount_065.py results/study-065/main"""
import hashlib,json,math,random,sys
from fractions import Fraction
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common import load,write_new,sha
from experiments import worlds_065 as W
from scripts.recount_058 import _eq,_consistent
from brute.api.certify20n import reads_for
ARMS=('C20','S10','S20','S30','S30b');K=400;NB=20;RB=2;DELTA=Fraction(1,1000)
NOISE={'C20':(0.0,None),'S10':(0.10,0.15),'S20':(0.20,0.25),'S30':(0.30,0.35),'S30b':(0.30,0.35)}
PI2_LO=Fraction(98696044010893586188,10**19);PI2_HI=Fraction(98696044010893586189,10**19)  # pi^2 bracket (21 digits)


def m_exact(t,eps_bar,read_bits=RB,delta=DELTA):
    """Smallest m >= 1 with read_bits r^m/(1+r^m) <= delta 6/(pi^2 t^2) (exact fractions; pi^2 bracketed, ambiguity -> error)."""
    e=Fraction(eps_bar).limit_denominator(10**6);r=e/(1-e);m=1
    while True:
        lhs=read_bits*r**m/(1+r**m);hi=delta*6/(PI2_LO*t*t);lo=delta*6/(PI2_HI*t*t)
        if lhs<=lo:return m
        if lhs<=hi:raise ValueError(f'pi bracket too wide at t={t} m={m}')
        m+=1


def stream(seed,eps,codes,eps_bar):
    """Regenerate every observation's raw readings and the settled values; returns per-obs dicts."""
    rng=random.Random(seed*13+650+int(round(1000*eps)));out=[];raw=[];mt={}
    for t,code in enumerate(codes,1):
        clean=tuple((code>>(RB-1-j))&1 for j in range(RB))
        if t not in mt:mt[t]=m_exact(t,eps_bar)
        m=mt[t];lead=[0]*RB;at=[None]*RB;rs=[]
        while any(a is None for a in at):
            r=tuple(b^1 if rng.random()<eps else b for b in clean);rs.append(list(r))
            for j in range(RB):
                if at[j] is None:
                    lead[j]+=1 if r[j] else -1
                    if abs(lead[j])>=m:at[j]=len(rs)
        val=tuple(1 if lead[j]>0 else 0 for j in range(RB));raw.append(rs)
        out.append({'k':len(rs),'m':m,'at':at,'val':val,'clean':clean,'err':sum(1 for x,y in zip(val,clean) if x!=y)})
    return out,hashlib.sha256(json.dumps(raw,separators=(',',':')).encode()).hexdigest()


def recount_case(c):
    out={};bad=[]
    for arm,a in c['arms'].items():
        w=W.world(c['seed']);pa=list(W.actions(c['seed'],0.0,w.k));acts=pa+list(a['extra_acts'])
        q=w.start;codes=[w.emissions[q]]
        for x in acts:q=w.transitions[q][x];codes.append(w.emissions[q])
        if a['family']!='scale20' or a['read_bits']!=RB or a['bound']!=NB:bad.append((arm,'family/bits/bound'))
        if [1<<x for x in codes[:len(pa)+1]]!=list(a['prefix_masks']):bad.append((arm,'prefix_readings'))
        if [1<<x for x in codes[len(pa)+1:]]!=list(a['extra_masks']):bad.append((arm,'extra_readings'))
        if a['used']!=len(a['extra_acts']) or a['used']>K:bad.append((arm,'K_accounting'))
        m=a['model'];stop=a['stop']
        if m is not None and not _consistent(m[0],m[1],acts,codes):bad.append((arm,'model_inconsistent'))
        if m is not None and (len(m[0])!=a['n_min'] or a['n_min']>NB):bad.append((arm,'n_min'))
        if stop=='unknown':lab='IDU'
        elif stop in ('AMB','K_spent'):lab='AMB'
        elif m is None:lab='WRONG'
        elif stop=='ID':lab='ID' if _eq(m[0],m[1],0,w.transitions,w.emissions,w.start) else 'WRONG'
        elif stop=='IDF':lab='IDF' if _eq(m[0],m[1],a['s1'],w.transitions,w.emissions,q) else 'WRONG'
        else:lab='WRONG'
        if lab!=a['label']:bad.append((arm,'label',a['label'],lab))
        o={'label':lab,'stop':stop,'steps':len(acts)}
        eps,eb=NOISE[arm]
        if eb is not None:
            if a.get('eps')!=eps or a.get('eps_bar')!=eb or a.get('delta')!=0.001:bad.append((arm,'noise_params'))
            obs,h=stream(c['seed'],eps,codes,eb);T=len(codes)
            chk={'reads_per_obs':[x['k'] for x in obs],'thresholds':[x['m'] for x in obs],'settle_at':[x['at'] for x in obs],
                 'reads_total':sum(x['k'] for x in obs),'settled_bit_errors':sum(x['err'] for x in obs),
                 'settled_obs_errors':sum(1 for x in obs if x['err']),'readings_sha256':h,'observations':T,
                 'fixed_reads_total':sum(reads_for(t,eb,0.001,RB) for t in range(1,T+1))}
            for f,v in chk.items():
                if a.get(f)!=v:bad.append((arm,'noise:'+f))
            o.update(reads_total=chk['reads_total'],fixed_reads_total=chk['fixed_reads_total'],settled_bit_errors=chk['settled_bit_errors'])
        out[arm]=o
    return out,bad


def main(argv):
    study=Path(argv[0]);R=load(study/'RESULTS.json');recs={};bad=[];cnt={g:0 for g in ARMS};study_cnt={g:0 for g in ARMS}
    for c in R['cases']:
        o,b=recount_case(c);recs[str(c['seed'])]=o;bad+=[[c['seed']]+list(x) for x in b]
        for g,v in o.items():cnt[g]+=v['label'] in ('ID','IDF')
        for g,v in c['arms'].items():study_cnt[g]+=v['label'] in ('ID','IDF')
    wrong=sum(1 for o in recs.values() for v in o.values() if v['label']=='WRONG')
    sbe=sum(v.get('settled_bit_errors',0) for o in recs.values() for v in o.values())
    rep={'schema':'brute.recount.v62','results_sha256':sha(study/'RESULTS.json'),'cases':len(R['cases']),'records':sum(len(o) for o in recs.values()),
         'mismatches':bad,'decided_by_arm':cnt,'study_decided_by_arm':study_cnt,'wrong':wrong,'settled_bit_errors':sbe,'per_case':recs,
         'PASS':not bad and cnt==study_cnt}
    write_new(study/'RECOUNT_065.json',rep);print(json.dumps({k:rep[k] for k in ('records','mismatches','decided_by_arm','wrong','settled_bit_errors','PASS')}))
    return 0 if rep['PASS'] else 1


if __name__=='__main__':sys.exit(main(sys.argv[1:]))
