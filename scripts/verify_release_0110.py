"""Brute v0.11.0 release verification (BRUTE_PLAN_013). New file; verify_release_0100 and earlier stay frozen.

Same hardening as verify_release_090 (frozen helpers of verify_release_060 reused): every JSON artifact of results/study-013
(recursive; raw RESULTS/SCIENTIFIC excepted, bound by the block SEALs and their committed .json.gz by MANIFEST) plus
RELEASE.json is parsed first and its required key checked; any other exception becomes VerificationError.

  python scripts/verify_release_0110.py         # short: seals, freezes, regenerated paired/repro/gates, ledger, manifest, git order
  python scripts/verify_release_0110.py --long  # + second implementation re-run on samples.long_verify (33 cases, J10 and SP8)
                                                 #   from the restored SCIENTIFIC.json inside its own 900 s cap (GLV)
"""
from __future__ import annotations
import argparse,json,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common import VerificationError,check,sha,dumps
from scripts.verify_release_060 import read_bytes_,jload,req,_guard,_freeze,manifest_ok
from scripts.verify_release_090 import PREVIOUS_FREEZES as PF090

STUDY='results/study-013'
RAW=('RESULTS.json','SCIENTIFIC.json')
REQUIRED_KEYS={'SEAL.json':'files_sha256','2x2/SEAL.json':'block','big78/SEAL.json':'block','transfer/SEAL.json':'block',
               'repro/2x2/SEAL.json':'block','repro/transfer/SEAL.json':'block','KILL_DRILL_013.json':'kill_latency_s',
               'RUN_DONE_013.json':'elapsed_s','RUN_STATE_013.json':'events','PROGRESS_013.json':'streams',
               'STOP_013.json':'fired_at','STOP_013_ORCHESTRATOR.json':'stopped_at','CLEAN_CLONE_013.json':'passed'}
RELEASE_KEYS=('version','preregistration','preregistration_commit','source_freeze','source_freeze_commit','release_freeze',
              'scoring_scripts_commit','seal_commit','results_dir','gates_passed','gates_failed','GST','G_RT','GTI_release_statement','transfer','api')
PREVIOUS_FREEZES=PF090+('experiments/BRUTE_SOURCE_FREEZE_011.json','experiments/BRUTE_RELEASE_FREEZE_090_R1.json',
                       'experiments/BRUTE_SOURCE_FREEZE_012.json','experiments/BRUTE_RELEASE_FREEZE_0100.json')
SCORING=('scripts/make_gates_013.py','scripts/make_paired_013.py','scripts/make_reproducibility_013.py','scripts/clean_clone_013.py')
LEDGER_ORDER=('diag_applicability_013','preregistration_013','seedcheck_013','source_freeze_013','scoring_freeze_013','run_start_013','seal_013','gates_013')
LONG_CAP=900


def study_artifacts(root):
    s=Path(root)/STUDY
    return sorted(p for p in s.rglob('*.json') if p.name not in RAW and '.partial' not in p.name and 'CHECKPOINT' not in p.name)


def required_key(root,p):
    p=Path(p);root=Path(root)
    if p==root/'RELEASE.json':return 'version'
    return REQUIRED_KEYS.get(p.relative_to(root/STUDY).as_posix(),'schema')


def parse_all(root):
    out={}
    for p in study_artifacts(root)+[Path(root)/'RELEASE.json']:
        o=jload(p);req(o,required_key(root,p),str(p.relative_to(root)));out[str(p.relative_to(root))]=o
    for k in RELEASE_KEYS:req(out['RELEASE.json'],k,'RELEASE.json')
    return out


def ledger_order(receipts,root='.'):
    ev=[req(r,'event','ledger') for r in receipts]
    for e in LEDGER_ORDER:check(e in ev,'ledger lacks '+e)
    idx=[ev.index(e) for e in LEDGER_ORDER];check(idx==sorted(idx),'ledger study-013 chronology')
    rs=max(i for i,e in enumerate(ev) if e=='run_start_013')
    end=[i for i,e in enumerate(ev) if e in ('run_end_013','stop_013') and i>rs]
    check(end and end[0]<max(i for i,e in enumerate(ev) if e=='seal_013'),'ledger lacks run_end_013/stop_013 between the held-out run_start and seal')
    from datetime import datetime
    def t(r):
        try:return datetime.fromisoformat(r['note'].split()[0])
        except (ValueError,IndexError,KeyError):raise VerificationError('ledger note without ISO time: '+r['event']) from None
    sf=t([r for r in receipts if r['event']=='scoring_freeze_013'][-1]);st=t(receipts[rs])
    check((st-sf).total_seconds()>=600,'scoring scripts ledgered < 10 min before run_start')
    return {'scoring_freeze_013':sf.isoformat(),'run_start_013':st.isoformat(),'gap_s':(st-sf).total_seconds()}


def git_order(root,rel):
    from scripts.verify_release_020 import _git
    def anc(a,b):return _git(root,'merge-base','--is-ancestor',a,b).returncode==0
    check(_git(root,'rev-parse','--git-dir').returncode==0,'not a git checkout')
    fr=jload(root/rel['source_freeze'])
    check(rel['preregistration_commit']==req(fr,'preregistration_commit','freeze'),'RELEASE.json preregistration_commit differs from the source freeze')
    chain=[('diagnostic',fr['diagnostic_commit']),('preregistration',fr['preregistration_commit']),('seedcheck',fr['seedcheck_commit']),('reference',fr['reference_commit'])]
    chain+=[(f'implementation_{i}',c) for i,c in enumerate(req(fr,'implementation_commits','freeze'))]
    chain+=[('source_freeze',rel['source_freeze_commit']),('seal',rel['seal_commit']),('head','HEAD')]
    for (na,a),(nb,b) in zip(chain,chain[1:]):
        check(anc(a,b),f'{na} {a} is not an ancestor of {nb} {b}')
        if b!='HEAD':check(_git(root,'rev-parse',a).stdout!=_git(root,'rev-parse',b).stdout,f'{na} and {nb} are the same commit')
    # plan order (6): the scoring scripts are committed strictly after the source freeze and strictly before the seal; their
    # freeze is the scoring_freeze_013 ledger entries (>= 600 s before run_start, checked by ledger_order); bytes equal the tree (below).
    sc=rel['scoring_scripts_commit'];sf=rel['source_freeze_commit']
    for a,b,na,nb in ((sf,sc,'source_freeze','scoring_scripts'),(sc,rel['seal_commit'],'scoring_scripts','seal')):
        check(anc(a,b) and _git(root,'rev-parse',a).stdout!=_git(root,'rev-parse',b).stdout,f'{na} {a} is not a strict ancestor of {nb} {b}')
    chain.insert([n for n,_ in chain].index('seal'),('scoring_scripts',sc))
    plan=_git(root,'show',f"{rel['preregistration_commit']}:{rel['preregistration']}")
    check(plan.returncode==0 and plan.stdout==(root/rel['preregistration']).read_text(),'plan changed after pre-registration')
    for f in SCORING:
        b=_git(root,'show',f"{rel['scoring_scripts_commit']}:{f}");check(b.returncode==0 and b.stdout==(root/f).read_text(),f'{f} changed after the scoring freeze')
    return {n:c for n,c in chain if c!='HEAD'}


def long_verify(root,cap=LONG_CAP):
    """GLV: second implementation on samples.long_verify (33 cases, J10, SP8) from the restored SCIENTIFIC.json."""
    from experiments import v0100_reference as R
    from experiments.brute_common import load
    from scripts.check_seeds_013 import long_sample
    plan=load(ROOT/'experiments/BRUTE_PLAN_013.json');view=R.plan_view(plan);tau6=plan['tau6']['value'];L=long_sample(plan)
    sci=jload(Path(root)/STUDY/'2x2/SCIENTIFIC.json');want={(f,s,m) for f,ss in L.items() for s in ss for m in plan['mask_rates']}
    cases=[c for c in req(sci,'cases','SCIENTIFIC') if (c['family'],c['seed'],c['mask_rate']) in want]
    check(len(cases)==len(want)==33,f'long_verify sample has {len(cases)}/{len(want)} cases (33 required)')
    t0=time.time();bad=[];n=0
    for c in cases:
        for a in R.ARMS_2X2:
            check(time.time()-t0<=cap,f'long_verify exceeded its {cap} s cap');ok,msg,_=R.audit_trace(c,a,view,tau6);n+=1
            if not ok:bad.append({'case':f"{c['family']}/{c['seed']}/{c['mask_rate']}",'arm':a,'first_difference':str(msg)[:200]})
    wall=time.time()-t0;check(wall<=cap,f'long_verify exceeded its {cap} s cap')
    check(not bad,f'long_verify: {len(bad)} mismatching traces, first {bad[:1]}')
    return {'cases':len(cases),'arm_traces':n,'mismatching_traces':0,'wall_s':round(wall,1),'cap_s':cap,'passed':True}


def api_check():
    """GAPI at release: the host-agnostic brute.certify/1 interface imports and returns a certified answer or UNKNOWN."""
    from brute.api import certify as A
    iface=getattr(A,'API',None);check(iface=='brute.certify/1','brute.api.certify API is not brute.certify/1')
    r=A.certify([(0,1)],[],0);check(r.get('api')==iface and r.get('status') in ('CERTIFIED','UNKNOWN'),'brute.certify/1 answer malformed')
    check(r['status']=='UNKNOWN','brute.certify/1 certified after one observation (expected UNKNOWN)')
    return {'interface':iface,'one_observation_status':r['status']}


def _verify(root,git,long=False):
    out={'schema':'brute.verify-release.v11_0','mode':'long' if long else 'short'}
    arts=parse_all(root);rel=arts['RELEASE.json'];out['artifacts_parsed']=len(arts)
    out['manifest_files']=manifest_ok(root)
    from brute.release_version_0110 import RELEASE_VERSION
    check(rel['version']==RELEASE_VERSION,'RELEASE.json version differs from brute.release_version_0110')
    import tomllib
    try:pv=tomllib.loads(read_bytes_(root/'pyproject.toml').decode())['project']['version']
    except (ValueError,KeyError) as e:raise VerificationError(f'pyproject.toml: {e}') from None
    check(pv==RELEASE_VERSION,'pyproject version differs')
    out['locked_files']={f:_freeze(root,f) for f in PREVIOUS_FREEZES+(rel['source_freeze'],rel['release_freeze'])}
    for d in ('results/study-001','results/study-002','results/study-003'):
        seal=jload(root/d/'SEAL.json');check(sha(root/d/'SCIENTIFIC.json')==req(seal,'scientific_sha256',d),d+' SCIENTIFIC does not match SEAL')
    for d,mod in (('results/study-004','study004_storage'),('results/study-005','study005_storage'),('results/study-006','study006_storage'),
                  ('results/study-007','study007_storage')):
        seal=jload(root/d/'SEAL.json');__import__('scripts.'+mod,fromlist=['ensure_raw']).ensure_raw(root/d)
        for n,k in (('RESULTS.json','results_sha256'),('SCIENTIFIC.json','scientific_sha256')):check(sha(root/d/n)==req(seal,k,d),f'{d}/{n} does not match SEAL')
    for n in ('008','009','010','011','012'):__import__(f'scripts.study{n}_storage',fromlist=['ensure_raw']).ensure_raw(root/f'results/study-{n}')
    check(rel['results_dir']==STUDY,'results_dir');s13=root/STUDY
    from scripts.study013_storage import ensure_raw;ensure_raw(s13)
    top=arts[f'{STUDY}/SEAL.json']
    for f,d in req(top,'files_sha256','study SEAL').items():
        p=s13/f
        if p.exists():check(sha(p)==d,f'study-013 {f} does not match the study SEAL')
        else:check('CHECKPOINT' in f or f.startswith('logs/') or f in ('RUN_013.log',),f'study-013 sealed file {f} is missing (only checkpoints and logs may be absent)')
    for sub in ('2x2','big78','transfer','repro/2x2','repro/transfer'):
        if not (s13/sub/'SEAL.json').exists():continue
        S=arts[f'{STUDY}/{sub}/SEAL.json']
        for n,k in (('RESULTS.json','results_sha256'),('SCIENTIFIC.json','scientific_sha256')):check(sha(s13/sub/n)==req(S,k,sub),f'study-013 {sub}/{n} does not match its SEAL')
    from scripts import make_paired_013,make_reproducibility_013,make_gates_013
    for mod,name in ((make_paired_013,'PAIRED_ANALYSIS_013.json'),(make_reproducibility_013,'REPRODUCIBILITY_013.json'),(make_gates_013,'GATES_013.json')):
        if (s13/name).exists() or name=='GATES_013.json':
            check(read_bytes_(s13/name)==dumps(mod.build(s13)),f'study-013 {name} does not regenerate byte-for-byte')
    gates=arts[f'{STUDY}/GATES_013.json']
    from scripts.verify_release_020 import ledger_020
    receipts,sup=ledger_020(root,git);out['ledger_receipts']=len(receipts);out['ledger_superseded']=sup
    out['run_chronology']=ledger_order(receipts,root)
    sources={r['source'] for r in receipts}
    for need in (rel['source_freeze'],f'{STUDY}/SEAL.json',f'{STUDY}/GATES_013.json'):check(need in sources,'ledger lacks '+need)
    if git:out['process_order']=git_order(root,rel)
    out['gates_passed']=gates['passed'];out['gates_failed']=gates['failed'];out['gates_pending']=gates['pending']
    check(rel['gates_passed']==gates['passed'] and rel['gates_failed']==gates['failed'],'RELEASE.json gate lists differ from GATES_013.json')
    for k in ('GST','G_RT','transfer'):
        check(rel[k]==gates[k],f'RELEASE.json {k} differs from GATES_013.json');out[k]=gates[k]
    out['stop_rule_fired']=gates.get('stop_rule_fired')
    out['api']=api_check();check(rel['api']==out['api']['interface'],'RELEASE.json api differs from brute.api.certify')
    if long:out['GLV_long_verify']=long_verify(root)
    out['status']='passed'
    out['validity']='bounded deterministic Moore worlds; 2x2, big78 and transfer blocks pre-registered in BRUTE_PLAN_013; brute.certify/1 API smoke-checked; not general intelligence'
    return out


def verify(root=ROOT,fast=True,git=True,long=False):
    return _guard(lambda r,g:_verify(r,g,long),Path(root),git)


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--long',action='store_true',help='GLV: re-run the second implementation on 33 cases (900 s cap)')
    ap.add_argument('--fast',action='store_true',help='accepted for symmetry; the default short mode');a=ap.parse_args()
    try:print(json.dumps(verify(long=a.long),indent=2))
    except VerificationError as e:print('VERIFICATION FAILED:',e);sys.exit(1)
