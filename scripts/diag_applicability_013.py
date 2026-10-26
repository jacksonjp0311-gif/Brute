"""EXPLORATORY seen-data diagnostic for v0.11.0 (committed BEFORE BRUTE_PLAN_013; deviation #52 discloses it).

Replays the SEALED study-012 transfer traces (results/study-012/transfer/RESULTS.json, already scored for v0.10.0) with
candidate applicability-test rules for library transfer, to calibrate the confirmation threshold M of the AT arm.
Seen data: nothing here is a held-out result; the held-out test is study-013 on fresh disjoint seeds.

Confirmation (candidate definition, the one plan 013 freezes if adopted): at step t, before observing, the library
survivors are unanimous on the next code c of the TAKEN action a, the SP8 support for a at step t has >= 2 codes (the
prediction is informative beyond the full region), the observation at t is fully unmasked, and its code equals c.
AT(M): the transfer rule of brute.transfer.TransferTracker.decide may fire only once confirmations >= M (counted on
earlier steps). SP8 certificates always pass through.
Writes results/diag-013/APPLICABILITY_DIAG_SEEN.json (refuses to overwrite).
"""
from __future__ import annotations
import json,sys,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from brute.transfer import expand,TransferTracker

SRC=ROOT/'results/study-012/transfer/RESULTS.json'
OUT=ROOT/'results/diag-013/APPLICABILITY_DIAG_SEEN.json'
MS=(0,1,2,3,4,5,6,8,10,12,16)


def replay(case,lib,M):
    H,st=expand(lib);tr=TransferTracker(H,tuple(case['initial_visible']),case['burn_in'])
    conf=0;first=45;false=0;tcerts=0
    for r in case['arms']['SP8']['trace']:
        t=r['step'];a=r['action'];R={a:r,1-a:r['counterfactual']};act={a:r['actual_emission_EVALUATOR_ONLY'],1-a:r['counterfactual_actual_EVALUATOR_ONLY']}
        cert=[None,None]
        for b in (0,1):
            c,rule=tr.decide(t,b,R[b]['certificate'],R[b]['support'])
            if rule=='transfer' and conf<M:c=None
            cert[b]=c
            if c is not None and c!=act[b]:false+=1
            if rule=='transfer' and c is not None:tcerts+=1
        if cert[a] is not None and first==45:first=t
        pred=tr.predict(a);obs=tuple(r['observed'])
        if pred is not None and r['support'] is not None and len(r['support'])>=2 and None not in obs and obs[0]*2+obs[1]==pred:conf+=1
        tr.observe(t,a,obs)
    sp=next((x['step'] for x in case['arms']['SP8']['trace'] if x['certificate'] is not None),45)
    return {'false':false,'transfer_certs':tcerts,'speedup':sp-first,'confirmations':conf}


def main():
    if OUT.exists():raise SystemExit('refusing to overwrite '+str(OUT))
    cases=json.loads(SRC.read_text())['cases'];rep={'schema':'brute.diag-applicability.v1','label':'EXPLORATORY seen data (study-012 sealed transfer traces)',
        'source':str(SRC.relative_to(ROOT)),'cases':len(cases),'by_M':{}}
    for M in MS:
        row={}
        for key in ('pos','neg'):
            rs=[replay(c,c['libraries'][key],M) for c in cases];sp=[x['speedup'] for x in rs]
            row[key]={'false_certificates':sum(x['false'] for x in rs),'cases_with_false':sum(x['false']>0 for x in rs),
                      'transfer_certificates':sum(x['transfer_certs'] for x in rs),'mean_speedup':round(statistics.mean(sp),4),
                      'sd_speedup':round(statistics.stdev(sp),4)}
        rep['by_M'][str(M)]=row;print(M,json.dumps(row),flush=True)
    OUT.write_text(json.dumps(rep,indent=1,sort_keys=True)+'\n')


if __name__=='__main__':main()
