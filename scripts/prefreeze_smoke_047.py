"""Pre-freeze smoke-gates and release-verifier test for study-047 (plan 047 process; pre-run deviation #167). New file; built from
scripts/prefreeze_smoke_046.py (frozen). Input: the sealed smoke block written by experiments/brute_study_047.py --block smoke
(outside results/study-047; seeds 11570001-11570006 only). It
  1. lists the stops present (ID, IDF, AMB, K_spent, unknown) and the missing ones (reported, not required: #167);
  2. runs recount_047 and run_reference_047 (blocks smoke and probe) on copies; runs scripts/api_checks_047.py into a temp file;
  3. builds a synthetic complete block (the smoke fresh cases relabelled 'main', the 4 smoke replays kept in their parts, expected
     counts patched in this process only), re-sealed with the runner's _write (stand-in freeze), recounted, referenced, its
     GFID16D(i) self-replay run, and gated twice (the dumps must be identical); exercises verify_release_0440.release_ok;
  4. runs the real verify_release_0440.chain on the repository (ledger since preregistration_047, HEAD standing in for the
     source freeze and seal): it must pass with 0 build-authorization exceptions;
  5. runtime projection (Inferred) over the main jobs, with and without part d:
       mean: LPT (8 workers) of the smoke mean wall per (arm, key) (replays: the smoke replay mean of their arm and key, else the
             smoke fresh mean of the arm, else of A16_N, for that key);
       worst (#167): wall arms (A16_N, API16) on scale16 at 250 s (240 s budget + 10 s); API16D / API16D_b on scale16 and scale20 at
             min(600 s case guard, B / r_min(key) + 10 s), r_min(key) = the slowest smoke conflict rate (conflicts_spent / arm wall)
             over that key's API16D records with arm wall >= 1 s; everything else at its mean;
     cut rule (plan runtime_estimate): cut_d_required = worst(with d) > 3600 s; the runner's CUT_D must equal it
     (cut_rule_consistent). Nothing else is cut; the post-cut worst case is reported beside the 3600 s G_RT cap.
Writes results/diag-047/PREFREEZE_SMOKE_GATES_047.json (refuses overwrite). Observed only: no gate decision, no tuning.
  PYTHONPATH=. python scripts/prefreeze_smoke_047.py /tmp/smoke"""
import copy,json,shutil,subprocess,sys,tempfile
from pathlib import Path
from unittest import mock
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments import brute_study_047 as ST
from experiments.brute_common_047 import load,write_new,PLAN,caps
from experiments.brute_common import dumps
from scripts import make_gates_047 as MG
from scripts import make_freeze_047 as MF
from scripts import verify_release_0440 as V
from scripts import api_checks_047 as AC
from scripts.recount_047 import main as recount
from scripts.run_reference_047 import main as reference,BUDGET_S
OUT=ROOT/'results/diag-047/PREFREEZE_SMOKE_GATES_047.json';CAP=3600;STOPS=('ID','IDF','AMB','K_spent','unknown')
WALL_WORST=250.0;GUARD=ST.GUARD_CASE_S


def status(g):return {k:{'pass':v['pass'],**({'reason':v['reason']} if 'reason' in v else {})} for k,v in g['gates'].items()}


def _lpt(walls,workers):
    bins=[0.0]*workers
    for x in sorted(walls,reverse=True):bins[bins.index(min(bins))]+=x
    return max(bins)


def _jobs(cut):
    with mock.patch.object(ST,'CUT_D',cut):return ST.jobs_for(load(PLAN),'main')


def projection(res,workers=8):
    _,B=caps();fv={};rv={};rate={}
    for c in res['cases']:
        if c['block']!='smoke':continue
        for g,w in c['group_walls_informational'].items():fv.setdefault((g,c['key']),[]).append(w)
    for r in res['replays']:
        a=list(r['arms'])[0];rv.setdefault((a,r['key']),[]).append(r['job_wall_informational'])
    for c in res['replays']+[c for c in res['cases'] if c['block']=='smoke']:
        for a,x in c['arms'].items():
            w=x.get('arm_wall_informational')
            if a in ST.D_ARMS and w and w>=1.0:rate.setdefault(c['key'],[]).append(x['conflicts_spent']/w)
    fm={k:sum(x)/len(x) for k,x in fv.items()};rm={k:sum(x)/len(x) for k,x in rv.items()};rmin={k:min(v) for k,v in rate.items()}
    def mean(j):
        a,k=j[3],j[1]
        if j[0] in ST.REPLAY_PARTS and (a,k) in rm:return rm[(a,k)]
        return fm.get((a,k),fm.get(('A16_N',k),0.0))
    def worst(j):
        a,k=j[3],j[1]
        if a in ST.WALL_ARMS and k=='scale16':return WALL_WORST
        if a in ST.D_ARMS and k in rmin:return min(GUARD,B/rmin[k]+10.0)
        return mean(j)
    out={'label':'Inferred','mean_fresh_wall_by_arm_key':{f'{g}/{k}':round(v,2) for (g,k),v in sorted(fm.items())},
         'mean_replay_wall_by_arm_key':{f'{g}/{k}':round(v,2) for (g,k),v in sorted(rm.items())},
         'slowest_conflict_rate_by_key':{k:round(v,1) for k,v in sorted(rmin.items())},'budget_conflicts':B,'workers':workers,'cap_s':CAP}
    for nm,cut in (('with_d',False),('without_d',True)):
        J=_jobs(cut);w=[mean(j) for j in J];x=[worst(j) for j in J]
        out[nm]={'jobs':len(J),'serial_s':round(sum(w),1),'lpt_makespan_s':round(_lpt(w,workers),1),'worst_serial_s':round(sum(x),1),
                 'worst_case_lpt_s':round(_lpt(x,workers),1)}
    out['cut_d_required']=out['with_d']['worst_case_lpt_s']>CAP;out['runner_CUT_D']=ST.CUT_D;out['cut_rule_consistent']=out['cut_d_required']==ST.CUT_D
    out['post_cut_worst_over_cap']=out['without_d' if ST.CUT_D else 'with_d']['worst_case_lpt_s']>CAP
    out['caveat']='four scale16, two control and two scale20 smoke seeds only; the worst case assumes every long job exhausts its budget'
    return out


def ref_projection(walls,workers=8):
    fv={}
    for rid,x in walls.items():
        b,k,_,a=rid.split('/');fv.setdefault((a,k),[]).append(x)
    fm={k:sum(v)/len(v) for k,v in fv.items()};J=_jobs(ST.CUT_D)
    w=[fm[(j[3],j[1])] for j in J if j[0]=='main' and (j[3],j[1]) in fm]
    return {'label':'Inferred','mean_ref_wall_by_arm_key':{f'{a}/{k}':round(v,1) for (a,k),v in sorted(fm.items())},'records':len(w),
            'serial_s':round(sum(w),1),'lpt_makespan_s':round(_lpt(w,workers),1),'budget_s':BUDGET_S,
            'scale20_reference_wall':'Open: no scale20 smoke record was decided, so no bound-20 reference wall was observed',
            'caveat':'assumes every main record is decided like its smoke mean; unknown records are not audited (not_reached)'}


def stops(res):
    s={}
    for c in res['replays']+res['cases']:
        for a,x in c['arms'].items():s.setdefault(x['stop'],[]).append(f"{c['block']}/{c['key']}/{c['seed']}/{a}")
    return s


def head():return subprocess.run(['git','-C',str(ROOT),'rev-parse','--short','HEAD'],capture_output=True,text=True).stdout.strip()


def main(argv=None):
    argv=sys.argv[1:] if argv is None else argv;S=Path(argv[0]);out={'label':'Observed','purpose':__doc__.split('\n')[0]}
    res=load(S/'RESULTS.json');st=stops(res)
    out['stops_present']={k:len(v) for k,v in sorted(st.items())};out['stops_missing']=[k for k in STOPS if k not in st];out['stop_examples']={k:v[:3] for k,v in st.items()}
    out['smoke_replays']=[(r['block'],r['key'],r['seed'],r['replay']) for r in res['replays']]
    out['smoke_cases']=[(c['block'],c.get('probe'),c['key'],c['seed'],{a:[c['arms'][a]['label'],c['arms'][a]['stop'],c['arms'][a]['used'],
                         c['arms'][a]['capped'],c['arms'][a].get('conflicts_spent'),c['arms'][a].get('wall_guard')] for a in c['arms']}) for c in res['cases']]
    out['smoke_wall_guard_records']=[f"{c['block']}/{c['key']}/{c['seed']}/{a}" for c in res['replays']+res['cases'] for a,x in c['arms'].items() if x.get('wall_guard')]
    out['smoke_determinism']=[(c['key'],c['seed'],ST.canon16d(c['arms']['API16D'])==ST.canon16d(c['arms']['API16D_b'])) for c in res['cases'] if 'API16D_b' in c['arms']]
    out['runtime_projection']=projection(res)
    with tempfile.TemporaryDirectory() as d:
        C=Path(d)/'copy';C.mkdir()
        for nm in ('RESULTS.json','SCIENTIFIC.json','SEAL.json'):shutil.copy(S/nm,C/nm)
        out['recount_rc']=recount([str(C)]);rc=load(C/'RECOUNT_047.json')
        out['recount']={k:rc.get(k) for k in ('replays','cases','labels_all','replay_by_part','amb_rule_applied','words_checked','mismatching_cases','PASS')}
        out['reference_rc']={}
        for b in ('smoke','probe'):
            R=Path(d)/f'ref_{b}';R.mkdir()
            for nm in ('RESULTS.json','SCIENTIFIC.json','SEAL.json'):shutil.copy(S/nm,R/nm)
            out['reference_rc'][b]=reference([str(R),'--block',b,'--workers','8']);rf=load(R/'REFERENCE_047.json')
            out[f'reference_{b}']={k:rf.get(k) for k in ('records','decided','audited','not_audited','complete','per_arm','per_key','not_reached','k_spent_as_amb','verdicts_checked','mismatch_count','misfires','vacuous','PASS','elapsed_informational','walls_informational')}|{'mutations':rf['mutation_test']['detected'],'of':rf['mutation_test']['mutations']}
        ac=Path(d)/'API_CHECKS_047.json';out['api_checks_rc']=subprocess.run([sys.executable,str(ROOT/'scripts/api_checks_047.py'),'--output',str(ac)],
            cwd=ROOT,capture_output=True,text=True,timeout=900,env={'PYTHONPATH':str(ROOT),'PATH':'/usr/bin:/bin'}).returncode;A=load(ac)
        out['api_checks']={'PASS':A['PASS'],'compat':{'tests':A['compat']['tests'],'sample_046_PASS':A['compat']['sample_046'].get('PASS'),'PASS':A['compat']['PASS']},
                           'ghost':{k:A['ghost'][k] for k in ('newly_imported','new_flagged','closure_flagged_reported','no_network_run','PASS')}}
        out['reference_projection']=ref_projection(out['reference_smoke']['walls_informational'])
        sd=Path(d)/'smoke_as_study';(sd/'main').mkdir(parents=True)
        for nm in ('RESULTS.json','SCIENTIFIC.json','SEAL.json','RECOUNT_047.json'):(sd/'main'/nm).write_bytes((C/nm).read_bytes())
        g=MG.build(sd);out['smoke_gate_status']=status(g);out['smoke_sealed_input_verified']=g['sealed_input_verified']
        D=Path(d)/'synthetic';(D/'main').mkdir(parents=True);fz=Path(d)/'FREEZE_STANDIN.json';fz.write_text('{}')
        cases=[dict(copy.deepcopy(c),block='main') for c in res['cases'] if c['block']=='smoke'];P=load(PLAN)
        reps=[copy.deepcopy(r) for r in res['replays']]
        with mock.patch.object(ST,'FREEZE',fz),mock.patch.object(ST,'CUT_D',False):
            ST._write(D/'main',P,'main',[f'synthetic:{i}' for i in range(len(cases)+len(reps))],(reps,cases),True,{'total_elapsed_informational':res.get('total_elapsed_informational')})
        rr=recount([str(D/'main')]);rf2=reference([str(D/'main'),'--workers','8'])
        fi=AC.fidelity(D/'main');A2=dict(A,fidelity=fi);(D/'API_CHECKS_047.json').write_text(json.dumps(A2))
        exp={k:sum(c['key']==k for c in cases) for k in MG.FRESH};exr={p:sum(r['block']==p for r in reps) for p in MG.PARTS}
        g1=MG.build(D,exp,exr);g2=MG.build(D,exp,exr)
        out['synthetic']={'cases':exp,'replays':exr,'recount_rc':rr,'reference_rc':rf2,'crashed':False,'gate_status':status(g1),'secondary':sorted(g1['secondary']),
                          'fidelity_self_replay':{k:v for k,v in fi.items() if k!='per_case'}|{'per_case':fi['per_case']},
                          **{nm:g1['gates'][nm]['observed'] for nm in ('GDET','GFID_wall','GAPI16D_fresh','GS20_sound','G10','GQB22','GS_ref')},
                          'sealed_input_verified':g1['sealed_input_verified'],'reproduces':dumps(g1)==dumps(g2),'reports_keys':sorted(g1['reports']),
                          'label_source':g1['label_source'],
                          'note':'synthetic: smoke fresh cases as main with expected counts patched; GDET / GFID16D fail here by their 18 / 36-case counts, GAPI16D_fresh by its 7/12 bar, GS20_sound / GDET also by the smoke scale20 wall_guard firings and undecided scale20 cases, GAPI16_compat / GHOST16D by design (no freeze), GTI and G_PROC by design'}
        Rd=Path(d)/'rel';(Rd/V.STUDY).mkdir(parents=True);(Rd/V.STUDY/'GATES_047.json').write_bytes(dumps(g1))
        Rel={k:'x' for k in V.RELEASE_KEYS};Rel.update(version=V.VERSION,gates_passed=sorted(k for k,v in g1['gates'].items() if v['pass'] is True),
             gates_failed=sorted(k for k,v in g1['gates'].items() if v['pass'] is False),gates_not_exercised=sorted(k for k,v in g1['gates'].items() if v['pass'] is None),
             secondary={k:v['pass'] for k,v in g1['secondary'].items()})
        (Rd/'RELEASE.json').write_text(json.dumps(Rel))
        try:V.release_ok(Rd);out['release_ok_synthetic']=True
        except Exception as e:out['release_ok_synthetic']=f'error: {e}'
    E=MF.entries();h=head();R={'preregistration_commit':E[0]['commit'],'source_freeze_commit':h,'seal_commit':h}
    try:out['verifier_chain']={'passed':True,'entries':[[e['event'],e['commit']] for e in E],'head':h,**V.chain(ROOT,R,E)}
    except Exception as e:out['verifier_chain']={'passed':False,'error':str(e),'entries':[[e['event'],e['commit']] for e in E]}
    vc=out['verifier_chain'];pj=out['runtime_projection']
    out['PASS']=(out['recount_rc']==0 and all(v==0 for v in out['reference_rc'].values()) and out['synthetic']['recount_rc']==0
                 and out['synthetic']['reference_rc']==0 and out['synthetic']['reproduces'] and out['synthetic']['sealed_input_verified']
                 and not any('INCOMPLETE_INPUT (main' in v.get('reason','') for v in out['synthetic']['gate_status'].values())
                 and out['synthetic']['gate_status']['G_recount']['pass'] is True and out['synthetic']['label_source']=='recount'
                 and out['synthetic']['fidelity_self_replay']['exact']==out['synthetic']['fidelity_self_replay']['cases']>0
                 and out['api_checks_rc']==0 and out['api_checks']['PASS'] is True and pj['cut_rule_consistent']
                 and out['release_ok_synthetic'] is True and vc['passed'] and vc.get('authorization_exceptions')==0)
    out['note']='PASS here means the tooling ran end to end on a sealed block, gates reproduce, the self-replay is exact, the cut rule was applied as declared and the real commit-order check passes; gate outcomes on smoke are recorded, not required'
    write_new(OUT,out);print(json.dumps({k:v for k,v in out.items() if k not in ('smoke_replays','smoke_cases','stop_examples','synthetic','reference_smoke','reference_probe')},default=str)[:5000])
    print(json.dumps(out['synthetic']['gate_status']));return 0 if out['PASS'] else 1


if __name__=='__main__':sys.exit(main())
