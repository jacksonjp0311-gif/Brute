"""Pre-freeze smoke-gates and release-verifier test for study-045 (plan 045 process). New file; built from
scripts/prefreeze_smoke_044.py (frozen). Input: a sealed smoke block written by experiments/brute_study_045.py --block smoke
(outside results/study-045). It
  1. checks the smoke contains at least one record of every stop the runner can emit (ID, IDF, AMB, K_spent, unknown) and lists
     the missing ones;
  2. runs recount_045 and run_reference_045 (blocks smoke and probe, all arms, default scope) on a copy and gates it (incomplete
     by design);
  3. builds a synthetic complete block in a temp dir (the 6 fresh smoke cases relabelled block 'main'; expected counts patched to
     them in this process only), re-sealed with the runner's _write (stand-in freeze hash), recounted, referenced and gated twice
     (the two dumps must be identical); exercises verify_release_0420.release_ok on a synthetic RELEASE.json;
  4. runs the real verify_release_0420.chain on this repository with the real ledger entries since preregistration_045, HEAD
     standing in for the source freeze and seal: it must pass with exactly 0 build-authorization exceptions (build_authorization_045
     names the preregistration commit 27d7946 itself);
  5. records the runtime projection (Inferred): mean smoke fresh wall per (arm, key) over the 54 main jobs, LPT on 8 workers, and a
     worst case with every scale16 job at its budget plus 10 s (250 s); and a reference projection (Inferred): mean smoke
     reference wall per (arm, key) over the main decided records, LPT on 8 workers, beside the 1800 s reference budget.
Writes results/diag-045/PREFREEZE_SMOKE_GATES_045.json (refuses overwrite). Observed only: no gate decision, no tuning.
  PYTHONPATH=. python scripts/prefreeze_smoke_045.py /tmp/smoke"""
import copy,json,shutil,subprocess,sys,tempfile
from pathlib import Path
from unittest import mock
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments import brute_study_045 as ST
from experiments.brute_common_045 import load,write_new,PLAN
from experiments.brute_common import dumps
from scripts import make_gates_045 as MG
from scripts import make_freeze_045 as MF
from scripts import verify_release_0420 as V
from scripts.recount_045 import main as recount
from scripts.run_reference_045 import main as reference,BUDGET_S
OUT=ROOT/'results/diag-045/PREFREEZE_SMOKE_GATES_045.json';CAP=3600;STOPS=('ID','IDF','AMB','K_spent','unknown')


def status(g):return {k:{'pass':v['pass'],**({'reason':v['reason']} if 'reason' in v else {})} for k,v in g['gates'].items()}


def _lpt(walls,workers):
    bins=[0.0]*workers
    for x in sorted(walls,reverse=True):bins[bins.index(min(bins))]+=x
    return max(bins)


WORST={a:250.0 for a in ST.ARMS}


def projection(res,workers=8):
    fv={}
    for c in res['cases']:
        if c['block']!='smoke':continue
        for g,w in c['group_walls_informational'].items():fv.setdefault((g,c['key']),[]).append(w)
    fm={k:sum(x)/len(x) for k,x in fv.items()};P=load(PLAN);jobs=ST.jobs_for(P,'main')
    w=[fm[(j[3],j[1])] for j in jobs];worst=[WORST[j[3]] if j[1]=='scale16' else fm[(j[3],j[1])] for j in jobs]
    lpt=_lpt(w,workers)
    return {'label':'Inferred','mean_fresh_wall_by_arm_key':{f'{g}/{k}':round(v,2) for (g,k),v in sorted(fm.items())},'workers':workers,
            'jobs':len(w),'serial_s':round(sum(w),1),'lpt_makespan_s':round(lpt,1),'worst_case_lpt_s':round(_lpt(worst,workers),1),'cap_s':CAP,
            'caveat':'four scale16 and two control smoke seeds only; scale16 walls vary widely (unknown cases may run to the budget)'}


def ref_projection(walls,workers=8):
    fv={}
    for rid,x in walls.items():
        b,k,_,a=rid.split('/');fv.setdefault((a,k),[]).append(x)
    fm={k:sum(v)/len(v) for k,v in fv.items()};P=load(PLAN);jobs=ST.jobs_for(P,'main')
    w=[fm[(j[3],j[1])] for j in jobs if (j[3],j[1]) in fm]
    return {'label':'Inferred','mean_ref_wall_by_arm_key':{f'{a}/{k}':round(v,1) for (a,k),v in sorted(fm.items())},'records':len(w),
            'serial_s':round(sum(w),1),'lpt_makespan_s':round(_lpt(w,workers),1),'budget_s':BUDGET_S,
            'caveat':'assumes every main record is decided like its smoke mean; unknown records are not audited (not_reached)'}


def stops(res):
    s={}
    for r in res['replays']:s.setdefault(r['stop'],[]).append(f"replay/{r['seed']}/{r['variant']}")
    for c in res['cases']:
        for a,x in c['arms'].items():s.setdefault(x['stop'],[]).append(f"{c['block']}/{c['key']}/{c['seed']}/{a}")
    return s


def head():return subprocess.run(['git','-C',str(ROOT),'rev-parse','--short','HEAD'],capture_output=True,text=True).stdout.strip()


def main(argv=None):
    argv=sys.argv[1:] if argv is None else argv;S=Path(argv[0]);out={'label':'Observed','purpose':__doc__.split('\n')[0]}
    res=load(S/'RESULTS.json');st=stops(res)
    out['stops_present']={k:len(v) for k,v in sorted(st.items())};out['stops_missing']=[k for k in STOPS if k not in st];out['stop_examples']={k:v[:3] for k,v in st.items()}
    out['smoke_replays']=[(r['seed'],r['variant'],r['stop'],r['n_min'],r['sealed'],r['queries'],r['capped'],round(r['query_max_s'] or 0,2),r['kills'],
                           round(r['job_wall_informational'],1)) for r in res['replays']]
    out['smoke_cases']=[(c['block'],c.get('probe'),c['key'],c['seed'],{a:[c['arms'][a]['label'],c['arms'][a]['stop'],c['arms'][a]['used']] for a in c['arms']}) for c in res['cases']]
    out['runtime_projection']=projection(res)
    with tempfile.TemporaryDirectory() as d:
        C=Path(d)/'copy';C.mkdir()
        for nm in ('RESULTS.json','SCIENTIFIC.json','SEAL.json'):shutil.copy(S/nm,C/nm)
        out['recount_rc']=recount([str(C)]);rc=load(C/'RECOUNT_045.json')
        out['recount']={k:rc.get(k) for k in ('replays','cases','labels_all','replay_labels','amb_rule_applied','words_checked','mismatching_cases','PASS')}
        out['reference_rc']={}
        for b in ('smoke','probe'):
            R=Path(d)/f'ref_{b}';R.mkdir()
            for nm in ('RESULTS.json','SCIENTIFIC.json','SEAL.json'):shutil.copy(S/nm,R/nm)
            out['reference_rc'][b]=reference([str(R),'--block',b,'--workers','8']);rf=load(R/'REFERENCE_045.json')
            out[f'reference_{b}']={k:rf.get(k) for k in ('records','decided','audited','not_audited','complete','nf2_all_audited','per_arm','not_reached','k_spent_as_amb','verdicts_checked','mismatch_count','misfires','vacuous','PASS','elapsed_informational','walls_informational')}|{'mutations':rf['mutation_test']['detected'],'of':rf['mutation_test']['mutations']}
        out['reference_projection']=ref_projection(out['reference_smoke']['walls_informational'])
        sd=Path(d)/'smoke_as_study';(sd/'main').mkdir(parents=True)
        for nm in ('RESULTS.json','SCIENTIFIC.json','SEAL.json','RECOUNT_045.json'):(sd/'main'/nm).write_bytes((C/nm).read_bytes())
        g=MG.build(sd);out['smoke_gate_status']=status(g);out['smoke_sealed_input_verified']=g['sealed_input_verified']
        D=Path(d)/'synthetic';(D/'main').mkdir(parents=True);fz=Path(d)/'FREEZE_STANDIN.json';fz.write_text('{}')
        cases=[dict(copy.deepcopy(c),block='main') for c in res['cases'] if c['block']=='smoke'];P=load(PLAN)
        with mock.patch.object(ST,'FREEZE',fz):
            ST._write(D/'main',P,'main',[f'synthetic:{i}' for i in range(2*len(cases))],([],cases),True,{'total_elapsed_informational':res.get('total_elapsed_informational')})
        rr=recount([str(D/'main')]);rf2=reference([str(D/'main'),'--workers','8'])
        exp={k:sum(c['key']==k for c in cases) for k in MG.EXP_CASES}
        g1=MG.build(D,exp);g2=MG.build(D,exp)
        out['synthetic']={'cases':exp,'recount_rc':rr,'reference_rc':rf2,'crashed':False,'gate_status':status(g1),'secondary':sorted(g1['secondary']),
                          'GREP16b':g1['secondary']['GREP16b']['observed'],'GNF_agree':g1['gates']['GNF_agree']['observed'],
                          'GNF_misfire':g1['gates']['GNF_misfire']['observed'],'GNF_bound':g1['gates']['GNF_bound']['observed'],
                          'GS_ref':g1['gates']['GS_ref']['observed'],
                          'sealed_input_verified':g1['sealed_input_verified'],'reproduces':dumps(g1)==dumps(g2),'reports_keys':sorted(g1['reports']),
                          'label_source':g1['gates']['GNF_agree']['observed']['label_source'],
                          'note':'synthetic: the 6 fresh smoke cases as main with expected counts patched to them; G10 can fail here only on its labels, GNF_agree by its thresholds, GTI and G_PROC by design (no TEST_SUITE_045, no 045 run events)'}
        Rd=Path(d)/'rel';(Rd/V.STUDY).mkdir(parents=True);(Rd/V.STUDY/'GATES_045.json').write_bytes(dumps(g1))
        Rel={k:'x' for k in V.RELEASE_KEYS};Rel.update(version=V.VERSION,gates_passed=sorted(k for k,v in g1['gates'].items() if v['pass'] is True),
             gates_failed=sorted(k for k,v in g1['gates'].items() if v['pass'] is False),gates_not_exercised=[],secondary={k:v['pass'] for k,v in g1['secondary'].items()})
        (Rd/'RELEASE.json').write_text(json.dumps(Rel))
        try:V.release_ok(Rd);out['release_ok_synthetic']=True
        except Exception as e:out['release_ok_synthetic']=f'error: {e}'
    E=MF.entries();h=head();R={'preregistration_commit':E[0]['commit'],'source_freeze_commit':h,'seal_commit':h}
    try:out['verifier_chain']={'passed':True,'entries':[[e['event'],e['commit']] for e in E],'head':h,**V.chain(ROOT,R,E)}
    except Exception as e:out['verifier_chain']={'passed':False,'error':str(e),'entries':[[e['event'],e['commit']] for e in E]}
    vc=out['verifier_chain']
    out['PASS']=(not out['stops_missing'] and out['recount_rc']==0 and all(v==0 for v in out['reference_rc'].values()) and out['synthetic']['recount_rc']==0
                 and out['synthetic']['reference_rc']==0 and out['synthetic']['reproduces'] and out['synthetic']['sealed_input_verified']
                 and not any('INCOMPLETE_INPUT (main' in v.get('reason','') for v in out['synthetic']['gate_status'].values())
                 and out['synthetic']['gate_status']['G_recount']['pass'] is True and out['synthetic']['label_source']=='recount'
                 and out['release_ok_synthetic'] is True and vc['passed'] and vc.get('authorization_exceptions')==0)
    out['note']='PASS here means every stop kind is present, the tooling ran end to end on a sealed block, gates reproduce and the real commit-order check passes; gate outcomes on smoke are recorded, not required'
    write_new(OUT,out);print(json.dumps({k:v for k,v in out.items() if k not in ('smoke_replays','smoke_cases','stop_examples')},default=str)[:6000]);return 0 if out['PASS'] else 1


if __name__=='__main__':sys.exit(main())
