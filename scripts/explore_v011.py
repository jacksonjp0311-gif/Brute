"""POST-HOC analysis for the v0.1.1 plan. Read-only on sealed study-002 / study-001 data.

Labels: every number here is Observed-post-hoc (re-tabulated from sealed traces) or Simulated
(a counterfactual predictor re-scored on the sealed traces). None of it is pre-registered evidence.
Writes docs/research/v0.1.1/POSTHOC_V011.json (build / --check). No core code is changed."""
import argparse,math,sys
from collections import Counter,defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common import STUDY_DIR,load,dumps,write_new,check,sha
OUT=ROOT/'docs/research/v0.1.1/POSTHOC_V011.json'
LN4=math.log(4);EPS_GRID=(0.02,0.05,0.1,0.2)
DRIFT_STEPS=(12,23,34)  # bgr90.worlds.step perturbs at loop index t%11==0, t>0 -> trace steps t+1


def r6(x):return None if x is None else round(x,6)


def key(t):return t['status'] if t['reason'] is None else t['status']+'/'+t['reason']


def post(c):return [t for t in c['trace'] if t['step']>c['burn_in']]  # plan: post-burn-in = steps 9..44


def contradiction_step(c):
    for t in c['trace']:
        if t['family_status_after']=='grammar_contradicted':return t['step']
    return None


def reweight(p,eps0,eps1):
    if all(abs(x-0.25)<1e-12 for x in p):return p
    return [(1-eps1)*((x-eps0/4)/(1-eps0))+eps1/4 for x in p]


def margin_probs(t,eps):
    s=t['margin_support']
    if not s:return [0.25]*4
    return [(1-eps)*(1/len(s) if i in s else 0)+eps/4 for i in range(4)]


def build():
    sci=load(STUDY_DIR/'SCIENTIFIC.json');plan=sci['plan'];eps=plan['open_world_reserve_epsilon']
    groups=defaultdict(list)
    for c in sci['cases']:groups[(c['family'],c['mask_rate'])].append(c);groups[(c['family'],'all')].append(c)
    table={};decomp={};sims={};cover={}
    for (fam,rate),cs in sorted(groups.items(),key=lambda kv:(kv[0][0],str(kv[0][1]))):
        P=[t for c in cs for t in post(c)];n=len(P);tag=f'{fam}@{rate}'
        v89=[t for t in P if t['logloss_v089'] is not None]
        table[tag]={'steps':n,'brute':r6(sum(t['logloss_brute'] for t in P)/n),'v090':r6(sum(t['logloss_v090'] for t in P)/n),
            'uniform':r6(LN4),'suffix1':r6(sum(t['logloss_suffix']['1'] for t in P)/n),
            'v089_valid_steps':len(v89),'v089_on_valid':r6(sum(t['logloss_v089'] for t in v89)/len(v89)) if v89 else None,
            'brute_on_v089_valid':r6(sum(t['logloss_brute'] for t in v89)/len(v89)) if v89 else None,
            'coverage_brute':r6(sum(t['certificate'] is not None for t in P)/n),
            'coverage_v090':r6(sum(t['v090_certificate'] is not None for t in P)/n),
            'false_certs_brute_post':sum(t['brute_wrong'] for t in P),'false_certs_v090_post':sum(t['v090_wrong'] for t in P),
            'status':dict(sorted(Counter(key(t) for t in P).items()))}
        # loss decomposition: contribution of each phase to (mean loss - ln4)
        ph=defaultdict(lambda:[0,0.0])
        for c in cs:
            cs_=contradiction_step(c)
            for t in post(c):
                if cs_ is not None and t['step']==cs_:p='contradiction_step'
                elif cs_ is not None and t['step']>cs_:p='after_contradiction'
                else:p='before:'+key(t)
                ph[p][0]+=1;ph[p][1]+=t['logloss_brute']
        decomp[tag]={p:{'steps':k,'mean_loss':r6(s/k),'contribution_to_mean_excess_over_ln4':r6((s-k*LN4)/n)}
                     for p,(k,s) in sorted(ph.items())}
        decomp[tag]['_total_excess_over_ln4']=r6(sum(t['logloss_brute'] for t in P)/n-LN4)
        # Simulated counterfactual predictors on the same post-burn-in steps
        s={}
        for e1 in EPS_GRID:
            s[f'reserve_eps_{e1}']=r6(sum(-math.log(reweight(t['probabilities'],eps,e1)[t['actual_emission_EVALUATOR_ONLY']]) for t in P)/n)
        def fb(e1):
            tot=0.0
            for c in cs:
                cs_=contradiction_step(c)
                for t in post(c):
                    a=t['actual_emission_EVALUATOR_ONLY']
                    if cs_ is not None and t['step']>cs_ and t['margin_support']:p=margin_probs(t,e1)  # prediction-time info only
                    else:p=reweight(t['probabilities'],eps,e1)
                    tot+=-math.log(p[a])
            return r6(tot/n)
        for e1 in EPS_GRID:s[f'margin_fallback_after_contradiction_eps_{e1}']=fb(e1)
        for lam in (0.1,0.25,0.5):  # mix margin-support probabilities into every pre-contradiction step, plus fallback after
            tot=0.0
            for c in cs:
                cs_=contradiction_step(c)
                for t in post(c):
                    a=t['actual_emission_EVALUATOR_ONLY']
                    if cs_ is not None and t['step']>cs_:p=margin_probs(t,eps) if t['margin_support'] else [0.25]*4
                    elif t['margin_support']:p=[(1-lam)*x+lam*y for x,y in zip(t['probabilities'],margin_probs(t,eps))]
                    else:p=t['probabilities']
                    tot+=-math.log(p[a])
            s[f'margin_mixture_lambda_{lam}_plus_fallback']=r6(tot/n)
        tot=0.0  # chain: margin support if alive, else the suffix-1 baseline's own loss (approximate: its alpha smoothing, no eps remix)
        for c in cs:
            cs_=contradiction_step(c)
            for t in post(c):
                if cs_ is not None and t['step']>cs_:
                    tot+=-math.log(margin_probs(t,eps)[t['actual_emission_EVALUATOR_ONLY']]) if t['margin_support'] else t['logloss_suffix']['1']
                else:tot+=t['logloss_brute']
        s['fallback_chain_margin_then_suffix1_approx']=r6(tot/n)
        sims[tag]=s
        # coverage: what margin disagreements / saturation were protecting
        md=[t for t in P if t['reason']=='MARGIN_DISAGREES'];sat=[t for t in P if t['reason']=='BOUND_SATURATED']
        al=[t for t in P if t['reason']=='RESIDUAL_SURPRISE']
        def wrong_family_singleton(ts):return sum(t['support'] is not None and len(t['support'])==1 and t['support'][0]!=t['actual_emission_EVALUATOR_ONLY'] for t in ts)
        grown=[t for c in cs if contradiction_step(c) for t in post(c) if t['step']>contradiction_step(c)
               and t['margin_support'] and len(t['margin_support'])==1]  # prediction-time margin support (no look-ahead)
        cover[tag]={'margin_disagrees_steps':len(md),'margin_disagrees_family_singleton_wrong':wrong_family_singleton(md),
            'margin_support_size_at_disagree':dict(sorted(Counter(len(t['margin_support']) for t in md if t['margin_support']).items())),
            'bound_saturated_steps':len(sat),'bound_saturated_family_singleton_wrong':wrong_family_singleton(sat),
            'residual_alarm_steps':len(al),'residual_alarm_family_singleton_wrong':wrong_family_singleton(al),
            'residual_alarm_mean_loss':r6(sum(t['logloss_brute'] for t in al)/len(al)) if al else None,
            'growth_proxy_after_contradiction_n5_singletons':len(grown),
            'growth_proxy_wrong':sum(t['margin_support'][0]!=t['actual_emission_EVALUATOR_ONLY'] for t in grown),
            'growth_proxy_note':'n<=5 margin singletons after the n<=4 family is contradicted; an n<=6 check is NOT simulated (Open)'}
    # study-002 contradiction-step anatomy (what Brute predicted just before being contradicted)
    anat={}
    for fam in ('ood5','drift4'):
        rows=Counter();steps=Counter();after_drift=Counter()
        for c in sci['cases']:
            if c['family']!=fam:continue
            cs_=contradiction_step(c)
            if cs_ is None:continue
            t=c['trace'][cs_-1];rows[f"{key(t)}|support_size={len(t['support']) if t['support'] else None}|actual_in_support={t['actual_emission_EVALUATOR_ONLY'] in (t['support'] or [])}"]+=1
            steps['post_burn_in' if cs_>c['burn_in'] else 'burn_in']+=1
            if fam=='drift4':after_drift[str(cs_)]+=1
        anat[fam]={'cases_contradicted':sum(rows.values()),'prediction_on_contradiction_step':dict(sorted(rows.items())),
                   'contradiction_in':dict(steps)}
        if fam=='drift4':anat[fam]['contradiction_step_histogram']=dict(sorted(after_drift.items(),key=lambda kv:int(kv[0])))
    drift=drift_replay_study001(plan)
    return {'schema':'brute.posthoc-v011.v1','study001_drift4_replay':drift,
            'label':'Observed-post-hoc tables and Simulated counterfactuals on sealed study-002 traces; NOT pre-registered evidence',
            'scientific_sha256':sha(STUDY_DIR/'SCIENTIFIC.json'),'post_burn_in':'steps > burn_in (9..44), as in the plan',
            'drift_perturbation_trace_steps':list(DRIFT_STEPS),
            'per_family_mask':table,'loss_decomposition':decomp,'simulated':sims,'gate_value':cover,'contradiction_anatomy':anat}


def drift_replay_study001(plan):
    """Re-run the frozen BruteLearner (v0.1.0 defaults, CALIBRATED_TAU) on the sealed study-001 drift4/ood5 traces."""
    from brute.core import BruteLearner
    from brute.api.service import CALIBRATED_TAU
    s1=load(ROOT/'results/study-001/SCIENTIFIC.json');out={}
    for fam in ('drift4','ood5'):
        certs=[]
        for c in s1['cases']:
            if c['family']!=fam:continue
            L=BruteLearner(4,5,160000,160000,plan['prediction_smoothing'],plan['open_world_reserve_epsilon'],8,CALIBRATED_TAU,None)
            L.initialize(tuple(c['initial_visible']))
            for r in c['trace']:
                f=L.predict(r['action']);L.record_issued(f)
                if f.certificate is not None:
                    a=r['actual_emission_EVALUATOR_ONLY']
                    certs.append({'seed':c['seed'],'mask_rate':c['mask_rate'],'step':r['step'],'certificate':f.certificate,'wrong':f.certificate!=a,
                        'at_drift_step':r['step'] in DRIFT_STEPS,'margin_support':list(f.margin_support) if f.margin_support else None,
                        'saturated':f.saturated,'residual':r6(f.residual)})
                L.observe(r['action'],tuple(r['observed']))
        out[fam]={'certificates':len(certs),'wrong':sum(x['wrong'] for x in certs),
                  'wrong_at_drift_step':sum(x['wrong'] and x['at_drift_step'] for x in certs),'wrong_detail':[x for x in certs if x['wrong']]}
    return out


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--check',action='store_true');a=ap.parse_args();obj=build()
    if a.check:check(OUT.read_bytes()==dumps(obj),'POSTHOC_V011.json does not reproduce');print('reproduces')
    else:write_new(OUT,obj);print('written',OUT)
