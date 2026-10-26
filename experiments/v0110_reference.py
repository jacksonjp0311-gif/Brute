"""Second implementation (same author, no `brute` import) for study BRUTE-0110-SOUND-TRANSFER-013 (G11, GLV, GS_ref).

Written from experiments/BRUTE_PLAN_013.json (transfer_definition, second_implementation) BEFORE brute/soundtransfer.py
and brute/api/certify.py existed. NOT an independent or third-party audit: same author.

* 2x2 (J10, SP8): the frozen experiments/v0100_reference audit (count / mutate) imported unchanged, run on plan 013.
* Transfer: libraries and hypotheses from the frozen v0100_reference re-implementation (ref_library, ref_hypotheses).
  ref_gated_arm independently recomputes the TR (M = 0), AT (M = 6), AT4 (M = 4) and DR decisions, rules,
  confirmation counts and summaries from the learner-visible SP8 trace. ref_lx_audit refilters the hypotheses on the
  LX trajectory (recorded actions and observations) and recomputes survivors, the largest predicted-code group per
  action, predictions, the refutation step and the chosen action for every LX rule (lx-split exactly; lx-plan = argmax
  of the RECORDED SP8 lookahead values, which are not re-derived: disclosed limitation), plus wrong flags and summaries.

Trace format (the learner side writes the same dicts, timing fields excluded):
  gated arm: {library, mode, M, hypotheses_initial, hypothesis_status, alive_after_initial, disabled_step,
              trace: [{step, alive, confirmations, certificate[2], rule[2], wrong[2]}], first_cert_step,
              false_certificates, certificates, transfer_certificates, disagreements}
  rules: 'sp8' (SP8 certificate, TR / AT), 'transfer' (library certificate), 'at-blocked' (transfer licensed by the
  library but confirmations < M; no certificate), 'dr-both' / 'dr-refuted' (DR keeps the SP8 certificate),
  'dr-disagree' (DR drops the SP8 certificate), None.
"""
from __future__ import annotations
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from experiments.brute_common import check,load,VerificationError
from experiments.v0100_reference import (plan_view,count,mutate,ref_library,ref_hypotheses,bit_compatible,ARMS_2X2)
from scripts.check_seeds_013 import source_seed as _source_seed

ROOT=Path(__file__).resolve().parents[1]
PLAN=ROOT/'experiments/BRUTE_PLAN_013.json'
CENSOR=45
GATED={'TR':0,'AT':6,'AT4':4,'DR':None}
_H={}


def hyps(lib):
    k=(lib['source_family'],lib['source_seed'])
    if k not in _H:_H[k]=ref_hypotheses(lib)
    return _H[k]


def _code(obs):return obs[0]*2+obs[1]


class RefTracker:
    def __init__(self,H,init):
        self.alive=[(T,E,0) for T,E in H if bit_compatible(E[0],init)];self.disabled=None if self.alive else 0

    def codes(self,b):
        out={}
        for T,E,s in self.alive:c=E[T[s][b]];out[c]=out.get(c,0)+1
        return out

    def pred(self,b):
        P=self.codes(b);return next(iter(P)) if len(P)==1 else None

    def step(self,t,a,obs):
        if not self.alive:return
        self.alive=[(T,E,T[s][a]) for T,E,s in self.alive if bit_compatible(E[T[s][a]],obs)]
        if not self.alive and self.disabled is None:self.disabled=t


def ref_gated_arm(case,lib,label,mode):
    check(mode in GATED,'mode');M=GATED[mode];H,st=hyps(lib);burn=case['burn_in']
    tr=RefTracker(H,tuple(case['initial_visible']))
    out={'library':label,'mode':mode,'M':M,'hypotheses_initial':len(H),'hypothesis_status':st,'alive_after_initial':len(tr.alive),
         'disabled_step':tr.disabled,'trace':[]}
    conf=0;first=CENSOR;false=0
    for r in case['arms']['SP8']['trace']:
        t=r['step'];a=r['action'];R={a:r,1-a:r['counterfactual']};act={a:r['actual_emission_EVALUATOR_ONLY'],1-a:r['counterfactual_actual_EVALUATOR_ONLY']}
        cert=[None,None];rule=[None,None]
        for b in (0,1):
            sc=R[b]['certificate'];p=tr.pred(b)
            if mode=='DR':
                if sc is not None:
                    if not tr.alive:cert[b],rule[b]=sc,'dr-refuted'
                    elif p==sc:cert[b],rule[b]=sc,'dr-both'
                    else:rule[b]='dr-disagree'
                continue
            if sc is not None:cert[b],rule[b]=sc,'sp8';continue
            if tr.alive and t>burn and R[b]['support'] is not None and p is not None and p in R[b]['support']:
                if conf>=M:cert[b],rule[b]=p,'transfer'
                else:rule[b]='at-blocked'
        wrong=[cert[b] is not None and cert[b]!=act[b] for b in (0,1)];false+=sum(wrong)
        if cert[a] is not None and first==CENSOR:first=t
        out['trace'].append({'step':t,'alive':len(tr.alive),'confirmations':conf,'certificate':cert,'rule':rule,'wrong':wrong})
        obs=tuple(r['observed']);pa=tr.pred(a)
        if pa is not None and r['support'] is not None and len(r['support'])>=2 and None not in obs and _code(obs)==pa:conf+=1
        tr.step(t,a,obs)
    out['disabled_step']=tr.disabled;out['first_cert_step']=first;out['false_certificates']=false
    out['certificates']=sum(c is not None for s in out['trace'] for c in s['certificate'])
    out['transfer_certificates']=sum(x=='transfer' for s in out['trace'] for x in s['rule'])
    out['disagreements']=sum(x=='dr-disagree' for s in out['trace'] for x in s['rule'])
    return out


def ref_lx_audit(lx,case,lib,label):
    """Raises VerificationError at the first differing field of the LX arm dict `lx`."""
    H,st=hyps(lib);tr=RefTracker(H,tuple(case['initial_visible']))
    for k,v in (('library',label),('hypotheses_initial',len(H)),('hypothesis_status',st),('alive_after_initial',len(tr.alive))):
        check(lx[k]==v,f'LX {label} {k}')
    first=CENSOR;false=0;cnt={'lx-split':0,'lx-plan':0,'sp8':0};check(len(lx['trace'])==case['steps'],'LX steps')
    for i,r in enumerate(lx['trace']):
        t=i+1;n=len(tr.alive);where=f'LX {label} step {t}';check(r['step']==t,where+' step')
        G=[tr.codes(b) for b in (0,1)];big=[max(g.values()) if g else 0 for g in G];pred=[tr.pred(b) for b in (0,1)]
        check(r['alive']==n,where+' alive');check(r['largest_group']==big,where+' groups');check(r['prediction']==pred,where+' prediction')
        sa=r['sp8_action']
        if n>=2 and min(big)<n:
            mins=[b for b in (0,1) if big[b]==min(big)];rule='lx-split';a=sa if sa in mins else mins[0]
            check(r['v'] is None,where+' v')
        elif n>=1:
            v=r['v'];check(isinstance(v,list) and len(v)==2,where+' v missing')
            if v[0]!=v[1]:rule='lx-plan';a=0 if v[0]>v[1] else 1
            else:rule='sp8';a=sa
        else:rule='sp8';a=sa;check(r['v'] is None,where+' v')
        check(r['lx_rule']==rule,where+' rule');check(r['action']==a,where+' action');cnt[rule]+=1
        act=r['actual_EVALUATOR_ONLY'];wrong=[r['certificate'][b] is not None and r['certificate'][b]!=act[b] for b in (0,1)]
        check(r['wrong']==wrong,where+' wrong');false+=sum(wrong)
        if r['certificate'][a] is not None and first==CENSOR:first=t
        obs=tuple(r['observed']);check(all(o is None or o==((act[a]>>(1-j))&1) for j,o in enumerate(obs)),where+' observation vs actual')
        tr.step(t,a,obs)
    check(lx['disabled_step']==tr.disabled,f'LX {label} disabled_step');check(lx['first_cert_step']==first,f'LX {label} first_cert_step')
    check(lx['false_certificates']==false,f'LX {label} false');check(lx['rule_counts']==cnt,f'LX {label} rule_counts')
    check(lx['certificates']==sum(c is not None for s in lx['trace'] for c in s['certificate']),f'LX {label} certificates')


def audit_transfer_case(c,plan):
    """(ok, message). Recomputes both libraries, every gated arm and the LX library side."""
    try:
        fam=c['family']
        for key,neg in (('pos',False),('neg',True)):
            if c.get('smoke'):sf,ss=c['libraries'][key]['source_family'],c['libraries'][key]['source_seed']
            else:
                off=c['seed']-plan['heldout_ranges_transfer']['targets'][fam][0]+1;sf,ss=_source_seed(fam,off,plan,neg)
            lib=ref_library(sf,ss);got=c['libraries'][key]
            for k in ('source_family','source_seed','min_n','status','motif_count','motifs'):check(got[k]==lib[k],f'library {key} {k}')
            suf='p' if key=='pos' else 'n'
            for mode in GATED:
                exp=ref_gated_arm(c,lib,key,mode);g=c['transfer'][mode+suf]
                for k in exp:check(g[k]==exp[k],f'{mode}{suf} {k}')
            ref_lx_audit(c['transfer']['LX'+suf],c,lib,key)
        return True,None
    except (VerificationError,KeyError,IndexError,TypeError,ValueError,AssertionError) as exc:
        return False,f'{type(exc).__name__}: {exc}'


def _tjob(x):
    i,c,plan=x;return i,audit_transfer_case(c,plan)


def run_transfer(cases,plan,workers=1,on_result=None):
    jobs=[(i,c,plan) for i,c in enumerate(cases)];outs=[]
    if workers<=1:
        for j in jobs:
            outs.append(_tjob(j))
            if on_result:on_result(outs[-1])
    else:
        with ProcessPoolExecutor(workers) as ex:
            for o in ex.map(_tjob,jobs,chunksize=2):
                outs.append(o)
                if on_result:on_result(o)
    bad=[{'case':i,'family':cases[i]['family'],'seed':cases[i]['seed'],'mask_rate':cases[i]['mask_rate'],'first_difference':m} for i,(ok,m) in sorted(outs) if not ok]
    return {'schema':'brute.transfer-reference.v2','study':plan['study'],'cases_checked':len(cases),'mismatching_cases':len(bad),'mismatches':bad,
            'scope':'libraries; TR / AT / AT4 / DR (all fields); LX library side (survivors, groups, predictions, rule, action; lx-plan from recorded v)',
            'wording':'second implementation by the same author, no brute import'}


def run(cases,plan,workers=4,mutate_k=0,arms=None,source_sha=None,on_result=None):
    """2x2 J10 / SP8 audit on plan 013 with the frozen v0100 audit path (G11)."""
    check(plan==load(PLAN),'plan mismatch');tau6=plan['tau6']['value'];arms=arms or ARMS_2X2
    view=plan_view(plan);checked,bad,hull=count(cases,view,tau6,arms,workers=workers,on_result=on_result)
    rep={'schema':'brute.second-implementation-count.v8','study':plan['study'],
         'wording':'second implementation by the same author, no brute import; not an independent or third-party audit',
         'arm_traces_checked':checked,'mismatching_arm_traces':len(bad),'mismatches':bad,'tau6':tau6,'jump_window_K':view['jump_window_K'],
         'j10_hull':hull,'row_budget':view['row_budget_enumeration'],
         'granularity':'one count per (case, arm) trace; the first differing field inside a trace is recorded',
         'scope':'J10 and SP8 via the frozen v0100_reference audit','source_sha256':source_sha}
    if mutate_k:
        mc,inj=mutate(cases,mutate_k,arms=arms);_,mbad,_=count(mc,view,tau6,arms,workers=workers)
        flagged={(b['case'],b['arm']) for b in mbad};base={(b['case'],b['arm']) for b in bad}
        rep['mutation_test']={'injected':len(inj),'injected_j10':sum(a=='J10' for _,a in inj),'injected_sp8':sum(a=='SP8' for _,a in inj),
                              'detected_injected':len(inj&flagged),'flagged_not_injected':len(flagged-inj-base),
                              'rng':'random.Random(20261026)','passed':inj<=flagged and not (flagged-inj-base)}
    return rep
