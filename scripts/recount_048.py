"""G_recount for study-048 (BRUTE_PLAN_048; pre-run deviation #169). New file. The per-case logic is the frozen
scripts/recount_047.py recount_case / replay_check, imported unchanged (worlds_047: scale16, control_cycle3, scale20; every arm at
bound N = the family size). Replays (block 'r') are API16D replays of sealed 046 A16_N traces, compared with the sealed record
(sha-checked against its SEAL) and re-classified with the 047 classes. Writes <study>/RECOUNT_048.json (refuses overwrite).
  PYTHONPATH=. python scripts/recount_048.py results/study-048/main"""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common import load,write_new,sha
from scripts.recount_047 import recount_case,replay_check,sealed,_counts
ORDER=('API16D','API16D_b');CLASSES=('none','cap-timing','word-divergence','infidelity')


def main(argv=None):
    argv=sys.argv[1:] if argv is None else argv;d=Path(argv[0]);res=load(d/'RESULTS.json');per={};bad={};rp={};rpc={}
    S=sealed('046') if res['replays'] else {}
    for c in res['replays']:
        k=f"r/{c['key']}/{c['seed']}";rp[k],b=recount_case(c)
        if c.get('source')!='046' or list(c['arms'])!=['API16D']:b=b+[('replay_source_or_arm',c.get('source'),list(c['arms']))]
        x,b2=replay_check(c,rp[k]['API16D'],S,'API16D');rpc[k]=x;b=b+b2
        if b:bad[k]=b
    for c in res['cases']:
        k=f"{c['block']}/{c['key']}/{c['seed']}";per[k],b=recount_case(c)
        if b:bad[k]=b
    main_=[v for k,v in per.items() if k.startswith('main/')];allv=list(per.values())+list(rp.values())
    sub=lambda p:{arm:_counts([v for k,v in per.items() if k.startswith(p)],arm) for arm in ORDER}
    out={'schema':'brute.recount.v45_0','results_sha256':sha(d/'RESULTS.json'),'replays':len(rp),'cases':len(per),
         'labels_main':{arm:_counts(main_,arm) for arm in ORDER},'labels_all':{arm:_counts(per.values(),arm) for arm in ORDER},
         'labels_scale16_main':sub('main/scale16/'),'labels_control_main':sub('main/control/'),'labels_scale20_main':sub('main/scale20/'),
         'replay_labels':_counts(rp.values(),'API16D'),
         'replay_summary':{'n':len(rpc),'same':sum(x['same'] for x in rpc.values()),'classes':{q:sum(x['class']==q for x in rpc.values()) for q in CLASSES}},
         'replay_compare':rpc,
         'misfires_main':{arm:sum(1 for v in main_ if arm in v and v[arm]['misfire']) for arm in ORDER},
         'replay_wrong':sum(v[a]['label']=='WRONG' for v in rp.values() for a in v),
         'amb_rule_applied':sum('amb_rule' in v[a] for v in allv for a in v),
         'words_unsound':sum(v[a]['words_unsound'] for v in allv for a in v),
         'words_checked':sum(v[a]['words_checked'] for v in allv for a in v),
         'truth_inconsistent':sum(sum(v[a]['truth_inconsistent_rounds'] for a in v)+sum(not x['truth_consistent_final'] for x in v.values()) for v in allv),
         'mismatching_cases':len(bad),'mismatches':{k:v for k,v in list(bad.items())[:50]},'per_case':per,'per_replay':rp,
         'PASS':not bad and len(per)>0}
    write_new(d/'RECOUNT_048.json',out);print(json.dumps({k:v for k,v in out.items() if k not in ('per_case','per_replay','replay_compare')},default=str));return 0 if out['PASS'] else 1


if __name__=='__main__':sys.exit(main())
