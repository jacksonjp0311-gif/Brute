"""Pre-freeze smoke-gates test for study-041 (plan 041 process: "pre-freeze gates test on a sealed smoke block"). New file;
built from scripts/prefreeze_smoke_040.py (frozen). Input: a sealed smoke block written by experiments/brute_study_041.py
--block smoke (outside results/study-041). Runs recount_041 and run_reference_041 (--part smoke) on a copy, builds
make_gates_041 on it, then builds a synthetic complete block in a temp dir to exercise every gate path: the smoke replays are
relabelled part a (repeat 0), part c (repeat 0) and part b (repeats 0, 1, 2 as copies), the smoke cases block 'main', with the
expected counts and the GINC seeds patched to the smoke values in this process only (no plan seed is touched); it is re-sealed
with the runner's _write (stand-in freeze hash), recounted, referenced and gated twice (the two dumps must be identical).
Also records the runtime projection for the main block (Inferred): per-variant mean smoke replay wall x the 48 main replays
per variant, plus the mean smoke fresh wall per (arm, key) x the main fresh cases, LPT makespan on 8 workers; plan 041 rule:
over 1500 s, part 1 (a) drops E1 and E2 by a deviation before the freeze. Writes results/diag-041/PREFREEZE_SMOKE_GATES_041.json
(refuses overwrite). Observed only: no gate decision, no tuning.
  PYTHONPATH=. python scripts/prefreeze_smoke_041.py /tmp/smoke"""
import copy,json,shutil,sys,tempfile
from pathlib import Path
from time import perf_counter
from unittest import mock
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments import brute_study_041 as ST
from experiments.brute_common_041 import load,write_new,PLAN
from experiments.brute_common import dumps
from scripts import make_gates_041 as MG
from scripts.recount_041 import main as recount
from scripts.run_reference_041 import main as reference
OUT=ROOT/'results/diag-041/PREFREEZE_SMOKE_GATES_041.json';THRESH=1500


def status(g):return {k:{'pass':v['pass'],**({'reason':v['reason']} if 'reason' in v else {})} for k,v in g['gates'].items()}


def _lpt(walls,workers):
    bins=[0.0]*workers
    for x in sorted(walls,reverse=True):bins[bins.index(min(bins))]+=x
    return max(bins)


def projection(res,workers=8):
    """Inferred: smoke means per variant (replays) and per (arm, key) (fresh) over the main job list; no contention model."""
    rv={}
    for r in res['replays']:rv.setdefault(r['variant'],[]).append(r['job_wall_informational'])
    fv={}
    for c in res['cases']:
        for g,w in c['group_walls_informational'].items():fv.setdefault((g,c['key']),[]).append(w)
    rm={v:sum(x)/len(x) for v,x in rv.items()};fm={k:sum(x)/len(x) for k,x in fv.items()};jobs=ST.jobs_for(load(PLAN),'main')
    def est(drop):
        w=[]
        for j in jobs:
            if j[0]=='replay':
                if drop and j[1]=='a' and j[5] in ('E1','E2'):continue
                w.append(rm[j[5]])
            else:w.append(fm[(j[3],j[1])])
        return {'jobs':len(w),'serial_s':round(sum(w),1),'ideal_parallel_s':round(sum(w)/workers,1),'lpt_makespan_s':round(_lpt(w,workers),1)}
    f=est(False);r=est(True)
    return {'label':'Inferred','mean_replay_wall_by_variant':{k:round(v,1) for k,v in sorted(rm.items())},
            'mean_fresh_wall_by_arm_key':{f'{g}/{k}':round(v,2) for (g,k),v in sorted(fm.items())},'workers':workers,'full_plan':f,
            'reduced_part_a_without_E1_E2':r,'smoke_total_elapsed_s':res.get('total_elapsed_informational'),'cap_s':1800,'threshold_s':THRESH,
            'drop_E1_E2_from_part_a':f['lpt_makespan_s']>THRESH,
            'caveat':'smoke traces are scale14 (part 1 has scale12 / perm12 / control and scale16); scale16 replays may be slower'}


def synthetic(res):
    reps=[]
    for r in res['replays']:
        for part,k in (('a',0),('c',0),('b',0),('b',1),('b',2)):x=copy.deepcopy(r);x['part']=part;x['repeat']=k;reps.append(x)
    cases=[dict(copy.deepcopy(c),block='main') for c in res['cases']]
    return reps,cases


def main(argv=None):
    argv=sys.argv[1:] if argv is None else argv;S=Path(argv[0]);out={'label':'Observed','purpose':__doc__.split('\n')[0]}
    res=load(S/'RESULTS.json')
    out['smoke_replays']=[(r['study'],r['key'],r['seed'],r['variant'],r['stop'],r['n_min'],r['sealed'],r['queries'],r['capped'],round(r['query_max_s'] or 0,2),
                           r['kills'],round(r['job_wall_informational'],1)) for r in res['replays']]
    out['smoke_cases']=[(c['key'],c['seed'],{a:c['arms'][a]['label'] for a in c['arms']},{a:c['arms'][a].get('used') for a in c['arms']},
                         {a:round(c['arms'][a].get('query_max_s') or 0,2) for a in c['arms']}) for c in res['cases']]
    out['runtime_projection']=projection(res)
    with tempfile.TemporaryDirectory() as d:
        C=Path(d)/'copy';C.mkdir()
        for nm in ('RESULTS.json','SCIENTIFIC.json','SEAL.json'):shutil.copy(S/nm,C/nm)
        out['recount_rc']=recount([str(C)]);rc=load(C/'RECOUNT_041.json');out['recount']={k:rc.get(k) for k in ('replays','cases','labels','replay_labels','words_checked','mismatching_cases','PASS')}
        t=perf_counter();out['reference_rc']=reference([str(C),'--part','smoke','--workers','2']);rf=load(C/'REFERENCE_041.json')
        out['reference_on_smoke']={k:rf.get(k) for k in ('records','decided','not_reached','verdicts_checked','mismatch_count','PASS')}|{'mutations':rf['mutation_test']['detected'],'of':rf['mutation_test']['mutations'],'wall_s_informational':round(perf_counter()-t,1)}
        sd=Path(d)/'smoke_as_study';(sd/'main').mkdir(parents=True)
        for nm in ('RESULTS.json','SCIENTIFIC.json','SEAL.json','RECOUNT_041.json','REFERENCE_041.json'):(sd/'main'/nm).write_bytes((C/nm).read_bytes())
        g=MG.build(sd);out['smoke_gate_status']=status(g);out['smoke_sealed_input_verified']=g['sealed_input_verified']
        D=Path(d)/'synthetic';(D/'main').mkdir(parents=True);fz=Path(d)/'FREEZE_STANDIN.json';fz.write_text('{}')
        reps,cases=synthetic(res);P=load(PLAN);s=sorted({r['seed'] for r in res['replays']})
        with mock.patch.object(ST,'FREEZE',fz):
            ST._write(D/'main',P,'main',[f'synthetic:{i}' for i in range(len(reps)+3*len(cases))],(reps,cases),True,{'total_elapsed_informational':res.get('total_elapsed_informational')})
        rr=recount([str(D/'main')]);rf2=reference([str(D/'main'),'--part','c','--workers','2'])
        patches=dict(EXP_REPLAYS={'a':len(res['replays']),'c':len(res['replays']),'b':3*len(res['replays'])},
                     EXP_CASES={'perm12':sum(c['key']=='perm12' for c in cases),'control':sum(c['key']=='control' for c in cases)},
                     GINC=tuple(s),GINC_CELLS=((s[0],'E3'),(s[1],'E3'),(s[1],'E4')))
        with mock.patch.multiple(MG,**patches):
            g1=MG.build(D);g2=MG.build(D)
        out['synthetic']={'recount_rc':rr,'reference_rc':rf2,'crashed':False,'gate_status':status(g1),'secondary':sorted(g1['secondary']),
                          'sealed_input_verified':g1['sealed_input_verified'],'reproduces':dumps(g1)==dumps(g2),'reports_keys':sorted(g1['reports']),
                          'note':'synthetic copies (parts a / c / b from the 10 smoke replays; G10 and GS_ref fail here by their fixed counts (6 controls; 24 records over 12 traces), GTI and G_PROC by design: no TEST_SUITE_041, no 041 run events)',
                          'GAUD_loc_reading':g1['gates']['GAUD_loc']['observed']['reading'],'GAUD_time_E3':g1['gates']['GAUD_time']['observed']['E3_over_E0']['ci95_seed_bootstrap']}
    out['PASS']=(out['recount_rc']==0 and out['synthetic']['recount_rc']==0 and out['synthetic']['reproduces'] and out['synthetic']['sealed_input_verified']
                 and all(out['synthetic']['gate_status'][k]['pass'] is not None for k in out['synthetic']['gate_status']))
    out['note']='PASS here means the tooling ran end to end on a sealed block (recount, reference and gates run; gates reproduce); gate outcomes on smoke are recorded, not required'
    write_new(OUT,out);print(json.dumps({k:v for k,v in out.items() if k not in ('smoke_replays','smoke_cases')},default=str)[:5000]);return 0 if out['PASS'] else 1


if __name__=='__main__':sys.exit(main())
