"""Scratch identify diagnostic for study-031 (never a gate input): on the sealed study-030 main block (published seeds,
disjoint from every 031 seed), regenerates each eps-0 world and trajectory and records how many (state, action) pairs of
the true machine the 176-step trace never exercises, against the 030 identify outcome; then runs the new probe
(brute.scalesearch6.identify6, 60 s) on three 030 scale12 traces in parallel (3 processes) to see whether its labels
separate AMB (a second machine found) from IDU (deadline). New file.
  PYTHONPATH=. python scripts/diag_031.py --write results/diag-031/IDENTIFY_DIAG_031.json"""
import argparse,json,sys
from pathlib import Path
from time import perf_counter
from concurrent.futures import ProcessPoolExecutor
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common_031 import load,write_new,sha
from experiments import worlds_026 as W
from experiments import brute_study_031 as B
STEPS=W.HORIZON
SEEDS=((9620001,'scale12'),(9620002,'scale12'),(9620003,'scale12'))


def pairs(seed,fam):
    w=W.world(seed,fam);tr=W.trajectory(w,seed,0.0);used=set(zip(tr['states'][:STEPS],tr['actions'][:STEPS]))
    return w.n*w.k-len(used),len(set(tr['states']))


def probe(args):
    seed,fam=args;w=W.world(seed,fam);tr=W.trajectory(w,seed,0.0);p=B.identify_case(w,tr);p['seed']=seed;p['family']=fam;return p


def main(argv=None):
    ap=argparse.ArgumentParser();ap.add_argument('--write');a=ap.parse_args(argv)
    src=ROOT/'results/study-030/main/RESULTS.json';res=load(src);rows=[]
    for c in res['cases']:
        if c['block']!='main' or c['family']=='control_cycle3':continue
        un,vis=pairs(c['seed'],c['family']);idf=c['arms']['S5']['identify']
        rows.append({'family':c['family'],'seed':c['seed'],'n':c['n'],'unexercised_pairs':un,'states_visited':vis,
                     'S5_ran':idf['ran'],'S5_n_min':idf['n_min'],'S5_unique':idf['unique'],'S5_unknown':idf['unknown'],'S5_ID':idf['ID']})
    summ={}
    for f in ('scale8','scale12','scale16'):
        r=[x for x in rows if x['family']==f]
        summ[f]={'cases':len(r),'with_unexercised_pairs':sum(1 for x in r if x['unexercised_pairs']>0),
                 'unexercised_pairs_mean':round(sum(x['unexercised_pairs'] for x in r)/len(r),2),
                 'n_min_below_n':sum(1 for x in r if x['S5_n_min'] is not None and x['S5_n_min']<x['n']),'S5_ID':sum(x['S5_ID'] for x in r),
                 'ID_with_unexercised_pairs':sum(1 for x in r if x['S5_ID'] and x['unexercised_pairs']>0)}
    t=perf_counter()
    with ProcessPoolExecutor(3) as ex:pr=list(ex.map(probe,SEEDS))
    out={'label':'Observed','not_used_for':'no gate decision, no tuning; 030 main seeds are published and disjoint from 031 (SEEDCHECK_031)',
         'source_results_sha256':sha(src),'per_case':rows,'summary':summ,'identify6_probe_on_030_scale12':pr,
         'probe_elapsed_informational':round(perf_counter()-t,1)}
    if a.write:write_new(Path(a.write),out)
    print(json.dumps({'summary':summ,'probe':[(p['seed'],p['label'],p['n_min'],round(p['wall_informational'],1)) for p in pr]}))


if __name__=='__main__':main()
