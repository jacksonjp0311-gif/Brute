"""Post-release verification: query-level differential of the incremental GX2' harness against the frozen one.

For each requested case, run the frozen experiments/v060_xcheck.audit over all breadth arms three times, with
(1) the frozen Oracle (brute/xcheck_sat.XRegion, full re-encoding), (2) IncOracle without and (3) with symmetry breaking,
and compare every memoised query answer (key = bound, evidence, query, args; value = answer, unknown count) and the
per-arm audit outcome. Writes a JSON report; does not touch any frozen file.
"""
import argparse,json,sys,time
from experiments import v060_xcheck as V
from experiments.v060_xcheck_incremental import IncOracle
from experiments.v050_reference import breadth_world
from experiments.brute_common import load,VerificationError


def arms_run(c,plan,tau7,o):
    out={}
    for arm in V.ARMS_008:
        try:out[arm]={'ok':True,'counts':V.audit(c,arm,plan,tau7,o)}
        except (VerificationError,KeyError,IndexError,TypeError,ValueError,AssertionError) as e:out[arm]={'ok':False,'err':str(e)}
        o.flush()
    return out


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--results',required=True);ap.add_argument('--cases',required=True)
    ap.add_argument('--output',required=True);a=ap.parse_args()
    cases=V.load_cases(a.results);plan=V.plan_view(load(V.PLAN));tau7=plan['tau7']['value'];rep=[]
    for i in [int(x) for x in a.cases.split(',')]:
        c=cases[i];w=breadth_world(c['seed'],c['family']);row={'case':i,'family':c['family'],'seed':c['seed'],'mask_rate':c['mask_rate']}
        runs={}
        for name,mk in (('frozen',lambda:V.Oracle(w.k,2**w.s)),('incremental',lambda:IncOracle(w.k,2**w.s)),
                        ('incremental_symmetry',lambda:IncOracle(w.k,2**w.s,symmetry=True))):
            o=mk();t=time.time();out=arms_run(c,plan,tau7,o)
            if hasattr(o,'close'):o.close()
            runs[name]=(o.res,out);row[f'wall_{name}']=round(time.time()-t,2);row[f'witness_failures_{name}']=o.witness_failures
            print(i,name,row[f'wall_{name}'],flush=True)
        ref,refout=runs['frozen']
        for name in ('incremental','incremental_symmetry'):
            res,out=runs[name]
            both=[k for k in ref if k in res];diff=[str(k) for k in both if ref[k]!=res[k] and not (ref[k][1] or res[k][1])]
            row[name]={'queries_frozen':len(ref),'queries_this':len(res),'common':len(both),
                       'answer_differences_both_known':len(diff),'differences':diff[:20],
                       'unknown_frozen_only':sum(1 for k in both if ref[k][1] and not res[k][1]),
                       'unknown_this_only':sum(1 for k in both if res[k][1] and not ref[k][1]),
                       'audit_outcome_equal':out==refout}
        rep.append(row);print(json.dumps(row)[:1500],flush=True)
    json.dump({'schema':'brute.xcheck-incremental-querylog.v1','cases':rep},open(a.output,'w'),indent=1,sort_keys=True)


if __name__=='__main__':main()
