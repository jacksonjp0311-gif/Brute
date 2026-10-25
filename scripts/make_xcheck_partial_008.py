"""Write results/study-008/XCHECK_008.json from the PARTIAL stream-A checkpoint (DEVIATIONS_008 D21-D22).

Stream A (experiments.v060_xcheck) was stopped by owner decision at 17:44 EDT 2026-10-25 with 46 of 288 breadth cases
checked. This wrapper reuses the frozen v060_xcheck.summarize on the checkpoint, then recounts `per_family_arm` over ALL
sealed breadth cases: steps of a case that was never checked count as unchecked. The committed make_gates_008.py then
scores GX2' (iii) checked_fraction >= 0.99 per family x arm and `covers_every_breadth_case` on the frozen criterion
(both FAIL). Nothing in the gate script or the plan is changed. Refuses to overwrite.
"""
from __future__ import annotations
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.v060_xcheck import summarize,load_cases,ARMS_008,CONF_BUDGET
from experiments.brute_common_008 import STUDY_DIR,write_new,sha

STOP='stream A stopped by owner decision 2026-10-25 ~17:44 EDT (runtime: 46 of 288 breadth cases in ~8.8 h); not resumed'


def build(study=STUDY_DIR):
    study=Path(study);ck=study/'XCHECK_008_CHECKPOINT.jsonl';done={}
    for line in ck.read_text().splitlines():
        if line.strip():r=json.loads(line);done[r['case']]=r['out']
    cases=[(i,c) for i,c in enumerate(load_cases(study/'RESULTS.json')) if 'k' in c and any(a in c['arms'] for a in ARMS_008)]
    rep=summarize(done,ARMS_008,CONF_BUDGET)
    full={}
    for i,c in cases:
        for arm in ARMS_008:
            if arm not in c['arms']:continue
            g=full.setdefault(f"{c['family']}/{arm}",{'traces':0,'traces_checked':0,'steps':0,'steps_checked':0,'steps_unchecked':0,'mismatching_traces':0,'certs':0})
            n=len(c['arms'][arm]['trace']);g['traces']+=1;g['steps']+=n
            o=done.get(i,{}).get('arms',{}).get(arm)
            if o is None:g['steps_unchecked']+=n;continue
            g['traces_checked']+=1
            if not o['ok']:g['mismatching_traces']+=1;g['steps_unchecked']+=n;continue
            t=o['counts'];g['steps_checked']+=t['steps_checked'];g['steps_unchecked']+=n-t['steps_checked'];g['certs']+=t['certs']
    for g in full.values():g['checked_fraction']=round(g['steps_checked']/g['steps'],6) if g['steps'] else None
    rep['checked_cases_only']={'label':'Observed','per_family_arm':rep['per_family_arm'],'cases':rep['cases']}
    rep['per_family_arm']=dict(sorted(full.items()))
    rep.update({'partial':True,'cases_checked':len(done),'cases_expected':len(cases),'stop':STOP,
                'checkpoint_sha256':sha(ck),'results_file':str((study/'RESULTS.json').relative_to(ROOT)),
                'wrapper':'scripts/make_xcheck_partial_008.py (DEVIATIONS_008 D22)'})
    return rep


if __name__=='__main__':
    obj=build();write_new(STUDY_DIR/'XCHECK_008.json',obj)
    print(json.dumps({k:obj[k] for k in ('cases','cases_expected','mismatching_traces','witness_replay_failures','unknown_queries')}),
          {k:v['checked_fraction'] for k,v in obj['per_family_arm'].items()})
