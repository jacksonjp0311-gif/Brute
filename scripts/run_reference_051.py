"""GS_ref / GS20_sound51 / GN12_sound51 audit for study-051 (BRUTE_PLAN_051 GS_ref; pre-run deviation #175). New file built on
the frozen scripts/run_reference_047.py (independent CaDiCaL reference, audit at bound N = 20 / 12, mutation seed 470): its view,
_audit, bucket, run_pool and mutation_test are used unchanged, with its module names ORDER / DELTA / KEYS / W43 bound in this
process to the 051 arms and experiments/worlds_050. The reference rebuilds the clean trace from the world and the recorded
actions, so a noise record is audited against the truth. Part c is compared with part k by recount_051 (outside this scope).
Scope (plan GS_ref, declared before the freeze):
  r12: every decided 12-state record of block main (control API16E / API16E_b, noise12 API16N / API16N_b), one total wall budget
       of 2400 s on 8 workers (run_reference_047.run_pool);
  s20: then every decided scale20 record (API16S / API16S_b), one at a time, each with its own 1800 s wall budget on 1 worker;
  one mutation test (20 mutations, seed 470) over every audited decided record. A record not finished in its budget is
  'not_audited' and GS_ref fails. Runs after the main run and outside G_RT.
Writes <study>/REFERENCE_051.json (refuses overwrite).
  PYTHONPATH=. python scripts/run_reference_051.py results/study-051/main [--block main] [--workers 8]"""
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common import load,write_new,sha
from experiments import worlds_050 as W50
from scripts import run_reference_047 as R47
BUDGET_12=2400.0;BUDGET_20=1800.0;OUTPUT_NAME='REFERENCE_051.json'
ORDER=('API16S','API16S_b','API16E','API16E_b','API16N','API16N_b');KEYS=('scale20','control','noise12')
R47.ORDER=ORDER;R47.DELTA={a:None for a in ORDER};R47.KEYS=KEYS;R47.W43=W50


def main(argv=None):
    ap=argparse.ArgumentParser();ap.add_argument('study');ap.add_argument('--workers',type=int,default=8);ap.add_argument('--block',default='main')
    ap.add_argument('--budget-12',type=float,default=BUDGET_12);ap.add_argument('--budget-20',type=float,default=BUDGET_20)
    a=ap.parse_args(argv);d=Path(a.study);res=load(d/'RESULTS.json')
    recs=R47.ordered([R47.view(c,g) for c in res['cases'] if c['block']==a.block for g in ORDER if g in c['arms']])
    todo=[r for r in recs if r['stop']!='unknown'];t12=[r for r in todo if r['key']!='scale20'];t20=[r for r in todo if r['key']=='scale20']
    done,el12=R47.run_pool(t12,a.workers,a.budget_12);el20={}
    for r in t20:
        d1,e1=R47.run_pool([r],1,a.budget_20);done.update(d1);el20[r['id']]=round(e1,1)
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
                'mismatches':sum(1 for m in mism if m[0].endswith('/'+g)),'misfires':sum(1 for m in fires if m[0].endswith('/'+g)),
                'idf_future_mismatch':sum(1 for x in reports if x.get('audited') and x['id'].endswith('/'+g) and x.get('label')=='IDF' and not x['future_match_ref'])}
             for g in ORDER}
    per_key={k:{'decided':sum(1 for r in todo if r['key']==k),'audited':sum(1 for r in todo if r['key']==k and r['id'] in done),
                'mismatches':sum(1 for m in mism if m[0].split('/')[1]==k)} for k in KEYS}
    out={'schema':'brute.reference.v48_0','study_results_sha256':sha(d/'RESULTS.json'),'block':a.block,
         'scope':{'budget_12_s':a.budget_12,'workers_12':a.workers,'budget_20_s_per_record':a.budget_20,'workers_20':1,'order':list(ORDER),'key_order':list(KEYS)},
         'records':len(recs),'decided':len(todo),'audited':len(done),'not_audited':na,'not_reached':sum(not x['decided'] for x in reports),
         'complete':not na,'per_arm':per_arm,'per_key':per_key,'k_spent_as_amb':sum(r['stop_recorded']=='K_spent' for r in todo),
         'verdicts_checked':sum(x.get('verdicts_checked',0) for x in reports),'mismatches':mism,'mismatch_count':len(mism),'misfires':fires,
         'mutation_test':mt,'per_record':reports,'walls_informational':{k:round(v[2],1) for k,v in done.items()},
         'elapsed_informational':{'r12':el12,'s20':el20}}
    out['vacuous']=out['decided']==0
    out['PASS']=out['mismatch_count']==0 and out['complete'] and (out['vacuous'] or mt['pass'])
    write_new(d/OUTPUT_NAME,out)
    print(json.dumps({k:v for k,v in out.items() if k not in ('per_record','mutation_test','mismatches')},indent=1),'\nmutations',mt['detected'],'/',mt['mutations'])
    return 0 if out['PASS'] else 1


if __name__=='__main__':sys.exit(main())
