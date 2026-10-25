"""Second-implementation audit of the sealed study-008 traces (G11) and the frozen-enumeration B5 audit used by GX2' (iv).

  SECOND_IMPLEMENTATION_COUNT.json : experiments/v060_reference.run over R6/C6/BR6/BC6, mutation test k=20 with
                                     random.Random(20261026) (G11).
  ENUM_B5_008.json                 : the frozen experiments/v050_reference.count over B5 breadth traces (enumeration up to
                                     the row budget); GX2' (iv) compares its verdicts with experiments/v060_xcheck's.
Both are by the same author as the production code; neither is an independent audit. Outputs refuse to overwrite.
"""
import argparse,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common_008 import STUDY_DIR,PLAN,load,sha,write_new,plan_view
from experiments import v060_reference as R6REF
from experiments import v050_reference as V5REF


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--results-dir',default=str(STUDY_DIR));ap.add_argument('--workers',type=int,default=2)
    ap.add_argument('--only',choices=['g11','enum'],help='run one of the two outputs');ap.add_argument('--limit',type=int)
    a=ap.parse_args();d=Path(a.results_dir);res=load(d/'RESULTS.json');plan=load(PLAN)
    cases=res['cases'][:a.limit] if a.limit else res['cases'];src=sha(d/'RESULTS.json')
    out=d/'SECOND_IMPLEMENTATION_COUNT.json'
    if a.only in (None,'g11') and not out.exists():
        rep=R6REF.run(cases,plan,workers=a.workers,mutate_k=20,source_sha=src);write_new(out,rep)
        print('G11',rep['arm_traces_checked'],rep['mismatching_arm_traces'],rep.get('mutation_test'),flush=True)
    out=d/'ENUM_B5_008.json'
    if a.only in (None,'enum') and not out.exists():
        view=plan_view(plan);checked,bad,cov=V5REF.count(cases,view,plan['tau6']['value'],plan['tau7']['value'],arms=('B5',),workers=a.workers)
        rep={'schema':'brute.enum-b5-008.v1','wording':'frozen v050_reference enumeration (same author), B5 breadth traces, up to the row budget',
             'arm_traces_checked':checked,'mismatching_arm_traces':len(bad),'mismatches':bad,'breadth_steps_checked':cov,'source_sha256':src}
        write_new(out,rep);print('ENUM',checked,len(bad),flush=True)


if __name__=='__main__':main()
