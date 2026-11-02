"""GS_ref audit for study-057 (BRUTE_PLAN_057 GS_ref; pre-run deviation #188). New file built from the frozen
scripts/run_reference_056.py, on the frozen scripts/run_reference_047.py (independent CaDiCaL reference, audit at each record's bound
N, mutation seed 470): its view, run_pool, bucket, mutation_test and ordered are used unchanged, with its module names ORDER / DELTA /
KEYS / W43 bound in this process to the 057 arms and experiments/worlds_050. The audited trace is the prefix + extra_acts, which for
the extension arms holds the extension and then the certifier's words, so every verdict is checked on the exact trace it used.
Scope (plan GS_ref): every decided record of every arm (API16E20, COV_O, LEN_R, COV_X, COV_X_b). One total wall budget of 2400 s
on 8 workers; one mutation test (20 mutations, seed 470) over every audited decided record. A decided record not finished in its
budget is 'not_audited' and GS_ref fails; with no decided record the audit is vacuous. Runs after the main run and outside G_RT.
Writes <study>/REFERENCE_057.json (refuses overwrite).
  PYTHONPATH=. python scripts/run_reference_057.py results/study-057/main [--block main] [--workers 8]"""
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common import load,write_new,sha
from experiments import worlds_050 as W50
from experiments.brute_common_057 import ALL_ARMS
from scripts import run_reference_047 as R47
BUDGET_12=2400.0;OUTPUT_NAME='REFERENCE_057.json'
ORDER=ALL_ARMS;KEYS=('scale20v',)
R47.ORDER=ORDER;R47.DELTA={a:None for a in ORDER};R47.KEYS=KEYS;R47.W43=W50


def main(argv=None):
    ap=argparse.ArgumentParser();ap.add_argument('study');ap.add_argument('--workers',type=int,default=8);ap.add_argument('--block',default='main')
    ap.add_argument('--budget-12',type=float,default=BUDGET_12)
    a=ap.parse_args(argv);d=Path(a.study);res=load(d/'RESULTS.json')
    recs=R47.ordered([R47.view(c,g) for c in res['cases'] if c['block']==a.block and c['key'] in KEYS for g in ORDER if g in c['arms']])
    todo=[r for r in recs if r['stop']!='unknown']
    done,el12=R47.run_pool(todo,a.workers,a.budget_12)
    reports=[];mism=[];fires=[]
    for r in recs:
        if r['stop']=='unknown':reports.append({'id':r['id'],'decided':False,'audited':False,'mismatches':[],'stop_recorded':r['stop_recorded']});continue
        if r['id'] not in done:reports.append({'id':r['id'],'decided':True,'audited':False,'mismatches':[],'stop_recorded':r['stop_recorded']});continue
        x=dict(done[r['id']][0]);x['audited']=True;m,f=R47.bucket(r,x);x['counted']=m;x['misfire']=f
        mism+=[[r['id']]+y for y in m];fires+=[[r['id']]+y for y in f];reports.append(x)
    caches={k:v[1] for k,v in done.items()};mt=R47.mutation_test(todo,caches)
    na=[x['id'] for x in reports if x['decided'] and not x['audited']]
    per_arm={g:{'records':sum(1 for r in recs if r['arm']==g),'decided':sum(1 for r in todo if r['arm']==g),
                'audited':sum(1 for x in reports if x.get('audited') and x['id'].endswith('/'+g)),
                'mismatches':sum(1 for m in mism if m[0].endswith('/'+g)),'misfires':sum(1 for m in fires if m[0].endswith('/'+g))} for g in ORDER}
    out={'schema':'brute.reference.v54_0','study_results_sha256':sha(d/'RESULTS.json'),'block':a.block,
         'scope':{'budget_12_s':a.budget_12,'workers_12':a.workers,'order':list(ORDER),'key_order':list(KEYS)},
         'records':len(recs),'decided':len(todo),'audited':len(done),'not_audited':na,'not_reached':sum(not x['decided'] for x in reports),
         'complete':not na,'per_arm':per_arm,'k_spent_as_amb':sum(r['stop_recorded']=='K_spent' for r in todo),
         'verdicts_checked':sum(x.get('verdicts_checked',0) for x in reports),'mismatches':mism,'mismatch_count':len(mism),'misfires':fires,
         'mutation_test':mt,'per_record':reports,'walls_informational':{k:round(v[2],1) for k,v in done.items()},
         'elapsed_informational':{'r12':el12}}
    out['vacuous']=out['decided']==0
    out['PASS']=out['mismatch_count']==0 and out['complete'] and (out['vacuous'] or mt['pass'])
    write_new(d/OUTPUT_NAME,out)
    print(json.dumps({k:v for k,v in out.items() if k not in ('per_record','mutation_test','mismatches')},indent=1),'\nmutations',mt['detected'],'/',mt['mutations'])
    return 0 if out['PASS'] else 1


if __name__=='__main__':sys.exit(main())
