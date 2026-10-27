"""Brute v0.14.0 release verification (BRUTE_PLAN_016). New file; verify_release_0130 and earlier stay frozen.

Same hardening as verify_release_0110 (frozen helpers of verify_release_060 reused): every JSON artifact of results/study-016
(recursive; raw RESULTS/SCIENTIFIC excepted, bound by the block SEALs and their committed .json.gz by MANIFEST) plus
RELEASE.json is parsed first and its required key checked; any other exception becomes VerificationError.

  python scripts/verify_release_0140.py         # short: seals, freezes, regenerated paired/repro/gates, ledger, manifest, git order
  python scripts/verify_release_0140.py --long  # + GLV: 15 main + 3 ood5 cases re-run from scratch and compared to the sealed
                                                 #   SCIENTIFIC cases (timing keys stripped), then audited by v0140_reference,
                                                 #   inside its own 900 s cap
LONG_CASES (release_gates.GLV_long_verify): per main family offset 1 at mask 0.1, offset 2 at 0.6, offset 3 at 0.35, plus ood4
offsets 25 / 26 / 27 at 0.1 / 0.6 / 0.35; ood5
offsets 1-3 at 0.1 / 0.6 / 0.35 (offsets counted from 1 within the held-out target range).
"""
from __future__ import annotations
import argparse,json,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common import VerificationError,check,sha,dumps
from scripts.verify_release_060 import read_bytes_,jload,req,_guard,_freeze,manifest_ok
from scripts.verify_release_0130 import PREVIOUS_FREEZES as PF0130

STUDY='results/study-016'
RAW=('RESULTS.json','SCIENTIFIC.json')
REQUIRED_KEYS={'SEAL.json':'files_sha256','transfer/SEAL.json':'block','repro/transfer/SEAL.json':'block','KILL_DRILL_016.json':'kill_latency_s',
               'RUN_DONE_016.json':'elapsed_s','RUN_STATE_016.json':'events','PROGRESS_016.json':'streams',
               'STOP_016.json':'fired_at','STOP_016_ORCHESTRATOR.json':'stopped_at','CLEAN_CLONE_016.json':'passed'}
RELEASE_KEYS=('version','preregistration','preregistration_commit','source_freeze','source_freeze_commit','release_freeze',
              'scoring_scripts_commit','seal_commit','results_dir','gates_passed','gates_failed','GDS','G_RT','GTI_release_statement','api')
PREVIOUS_FREEZES=PF0130+('experiments/BRUTE_SOURCE_FREEZE_015.json','experiments/BRUTE_RELEASE_FREEZE_0130.json')
SCORING=('scripts/make_gates_016.py','scripts/make_paired_016.py','scripts/make_reproducibility_016.py','scripts/clean_clone_016.py')
LEDGER_ORDER=('preregistration_016','seedcheck_016','diag_license_016','source_freeze_016','scoring_freeze_016','run_start_016','seal_016','gates_016')
LONG_CAP=900
FAMILIES=('cycle3','switch3','unaliased2','ood4')


def long_cases(plan):
    R=plan['heldout_ranges_transfer']['targets'];out=[]
    for f in FAMILIES:
        lo=R[f][0];out+=[(f,lo,0.1),(f,lo+1,0.6),(f,lo+2,0.35)]
    lo=R['ood4'][0]+24;out+=[('ood4',lo,0.1),('ood4',lo+1,0.6),('ood4',lo+2,0.35)]
    lo=plan['heldout_ranges_transfer']['ood5_targets'][0]
    return out+[('ood5',lo,0.1),('ood5',lo+1,0.6),('ood5',lo+2,0.35)]


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
    idx=[ev.index(e) for e in LEDGER_ORDER];check(idx==sorted(idx),'ledger study-016 chronology')
    rs=max(i for i,e in enumerate(ev) if e=='run_start_016')
    end=[i for i,e in enumerate(ev) if e in ('run_end_016','stop_016') and i>rs]
    check(end and end[0]<max(i for i,e in enumerate(ev) if e=='seal_016'),'ledger lacks run_end_016/stop_016 between the held-out run_start and seal')
    from datetime import datetime
    def t(r):
        try:return datetime.fromisoformat(r['note'].split()[0])
        except (ValueError,IndexError,KeyError):raise VerificationError('ledger note without ISO time: '+r['event']) from None
    sf=t([r for r in receipts if r['event']=='scoring_freeze_016'][-1]);st=t(receipts[rs])
    check((st-sf).total_seconds()>=600,'scoring scripts ledgered < 10 min before run_start')
    return {'scoring_freeze_016':sf.isoformat(),'run_start_016':st.isoformat(),'gap_s':(st-sf).total_seconds()}


def git_order(root,rel):
    from scripts.verify_release_020 import _git
    def anc(a,b):return _git(root,'merge-base','--is-ancestor',a,b).returncode==0
    check(_git(root,'rev-parse','--git-dir').returncode==0,'not a git checkout')
    fr=jload(root/rel['source_freeze'])
    check(rel['preregistration_commit']==req(fr,'preregistration_commit','freeze'),'RELEASE.json preregistration_commit differs from the source freeze')
    chain=[('preregistration',fr['preregistration_commit']),('seedcheck',req(fr,'seedcheck_commit','freeze'))]
    chain+=[(f'reference_{i}',c) for i,c in enumerate(req(fr,'reference_commits','freeze'))]
    chain+=[(f'implementation_{i}',c) for i,c in enumerate(req(fr,'implementation_commits','freeze'))]
    chain+=[('source_freeze',rel['source_freeze_commit']),('seal',rel['seal_commit']),('head','HEAD')]
    for (na,a),(nb,b) in zip(chain,chain[1:]):
        check(anc(a,b),f'{na} {a} is not an ancestor of {nb} {b}')
        if b!='HEAD':check(_git(root,'rev-parse',a).stdout!=_git(root,'rev-parse',b).stdout,f'{na} and {nb} are the same commit')
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
    """GLV: re-run LONG_CASES from scratch (frozen runner) and compare to the sealed cases; then the second implementation."""
    from experiments import brute_study_016 as BS,v0140_reference as R
    from experiments.brute_common import load
    from scripts.make_reproducibility_016 import _canon
    plan=load(ROOT/'experiments/BRUTE_PLAN_016.json');L=long_cases(plan)
    sci=jload(Path(root)/STUDY/'transfer/SCIENTIFIC.json')
    M={(c['family'],c['seed'],c['mask_rate']):c for c in req(sci,'cases','SCIENTIFIC')}
    check(all(k in M for k in L) and len(L)==18,f'long_verify sample: {sum(k in M for k in L)}/{len(L)} sealed cases (18 required)')
    t0=time.time();bad=[]
    for f,s,m in L:
        check(time.time()-t0<=cap,f'long_verify exceeded its {cap} s cap')
        _,c=BS.run_job(('transfer',f,s,m),plan)
        if _canon(c)!=_canon(M[(f,s,m)]):bad.append({'case':f'{f}/{s}/{m}','stage':'rerun'});continue
        ok,msg=R.audit_case(M[(f,s,m)],plan)
        if not ok:bad.append({'case':f'{f}/{s}/{m}','stage':'reference','first_difference':str(msg)[:200]})
    wall=time.time()-t0;check(wall<=cap,f'long_verify exceeded its {cap} s cap')
    check(not bad,f'long_verify: {len(bad)} mismatching cases, first {bad[:1]}')
    return {'cases':len(L),'case_list':[f'{f}/{s}/{m}' for f,s,m in L],'mismatching_cases':0,'wall_s':round(wall,1),'cap_s':cap,'passed':True}


def api_check():
    """GAPI4 at release: brute.certify/4 (and the carried brute.certify/3, /2, /1) import and answer host-agnostically."""
    from brute.api import certify as A1,certify2 as A2,certify3 as A3,certify4 as A4
    for m,v in ((A1,1),(A2,2),(A3,3),(A4,4)):check(getattr(m,'API',None)==f'brute.certify/{v}',f'{m.__name__} API is not brute.certify/{v}')
    r=A4.certify4([(0,1)],[],0);check(r.get('api')=='brute.certify/4' and r.get('status')=='UNKNOWN','brute.certify/4 one-observation answer malformed')
    check(r.get('reason') in A4.REASONS,'brute.certify/4 reason not in REASONS')
    sg=A4.suggest4([(0,1)],[]);a=sg.get('action') if isinstance(sg,dict) else None
    check(sg.get('api')=='brute.certify/4' and a in (0,1) and sg.get('deferred') is True and sg.get('rule')=='sp8','brute.certify/4 suggest4 did not return a deferred SP8 action')
    try:A4.Certifier4(margin=0);raise VerificationError('Certifier4 accepted margin 0')
    except ValueError:pass
    return {'interface':'brute.certify/4','carried':['brute.certify/3','brute.certify/2','brute.certify/1'],'one_observation':{'status':r['status'],'reason':r['reason']},
            'suggest4':{'action':a,'rule':sg.get('rule'),'deferred':sg.get('deferred')}}


def _verify(root,git,long=False):
    out={'schema':'brute.verify-release.v14_0','mode':'long' if long else 'short'}
    arts=parse_all(root);rel=arts['RELEASE.json'];out['artifacts_parsed']=len(arts)
    out['manifest_files']=manifest_ok(root)
    from brute.release_version_0140 import RELEASE_VERSION
    check(rel['version']==RELEASE_VERSION,'RELEASE.json version differs from brute.release_version_0140')
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
    for n in ('008','009','010','011','012','013','014','015'):__import__(f'scripts.study{n}_storage',fromlist=['ensure_raw']).ensure_raw(root/f'results/study-{n}')
    check(rel['results_dir']==STUDY,'results_dir');s14=root/STUDY
    from scripts.study016_storage import ensure_raw;ensure_raw(s14)
    top=arts[f'{STUDY}/SEAL.json']
    for f,d in req(top,'files_sha256','study SEAL').items():
        p=s14/f
        if p.exists():check(sha(p)==d,f'study-016 {f} does not match the study SEAL')
        else:check('CHECKPOINT' in f or f.startswith('logs/') or f in ('RUN_016.log',),f'study-016 sealed file {f} is missing (only checkpoints and logs may be absent)')
    for sub in ('transfer','repro/transfer'):
        if not (s14/sub/'SEAL.json').exists():continue
        S=arts[f'{STUDY}/{sub}/SEAL.json']
        for n,k in (('RESULTS.json','results_sha256'),('SCIENTIFIC.json','scientific_sha256')):check(sha(s14/sub/n)==req(S,k,sub),f'study-016 {sub}/{n} does not match its SEAL')
    from scripts import make_paired_016,make_reproducibility_016,make_gates_016
    for mod,name in ((make_paired_016,'PAIRED_ANALYSIS_016.json'),(make_reproducibility_016,'REPRODUCIBILITY_016.json'),(make_gates_016,'GATES_016.json')):
        if (s14/name).exists() or name=='GATES_016.json':
            check(read_bytes_(s14/name)==dumps(mod.build(s14)),f'study-016 {name} does not regenerate byte-for-byte')
    gates=arts[f'{STUDY}/GATES_016.json']
    from scripts.verify_release_020 import ledger_020
    receipts,sup=ledger_020(root,git);out['ledger_receipts']=len(receipts);out['ledger_superseded']=sup
    out['run_chronology']=ledger_order(receipts,root)
    sources={r['source'] for r in receipts}
    for need in (rel['source_freeze'],f'{STUDY}/SEAL.json',f'{STUDY}/GATES_016.json'):check(need in sources,'ledger lacks '+need)
    if git:out['process_order']=git_order(root,rel)
    out['gates_passed']=gates['passed'];out['gates_failed']=gates['failed'];out['gates_pending']=gates['pending']
    check(rel['gates_passed']==gates['passed'] and rel['gates_failed']==gates['failed'],'RELEASE.json gate lists differ from GATES_016.json')
    for k in ('GDS','G_RT'):
        check(rel[k]==gates[k],f'RELEASE.json {k} differs from GATES_016.json');out[k]=gates[k]
    out['stop_rule_fired']=gates.get('stop_rule_fired')
    out['api']=api_check();check(rel['api']==out['api']['interface'],'RELEASE.json api differs from brute.api.certify4')
    if long:out['GLV_long_verify']=long_verify(root)
    out['status']='passed'
    out['validity']='bounded deterministic Moore worlds (<= 4 states, 2 actions, 2 bits); deferred-split block pre-registered in BRUTE_PLAN_016; brute.certify/4 smoke-checked; not general intelligence'
    return out


def verify(root=ROOT,fast=True,git=True,long=False):
    return _guard(lambda r,g:_verify(r,g,long),Path(root),git)


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--long',action='store_true',help='GLV: re-run 18 cases and audit them (900 s cap)')
    ap.add_argument('--fast',action='store_true',help='accepted for symmetry; the default short mode');a=ap.parse_args()
    try:print(json.dumps(verify(long=a.long),indent=2))
    except VerificationError as e:print('VERIFICATION FAILED:',e);sys.exit(1)
