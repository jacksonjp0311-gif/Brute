"""Brute v0.12.0 release verification (BRUTE_PLAN_014). New file; verify_release_0110 and earlier stay frozen.

Same hardening as verify_release_0110 (frozen helpers of verify_release_060 reused): every JSON artifact of results/study-014
(recursive; raw RESULTS/SCIENTIFIC excepted, bound by the block SEALs and their committed .json.gz by MANIFEST) plus
RELEASE.json is parsed first and its required key checked; any other exception becomes VerificationError.

  python scripts/verify_release_0120.py         # short: seals, freezes, regenerated paired/repro/gates, ledger, manifest, git order
  python scripts/verify_release_0120.py --long  # + GLV: the 12 LONG_CASES re-run from scratch and compared to the sealed
                                                 #   SCIENTIFIC cases (timing keys stripped), then audited by v0120_reference,
                                                 #   inside its own 900 s cap
LONG_CASES (samples.long_verify; the plan text lists "offsets 1 and 2 ... at masks 0.1 and 0.6, offset 3 at 0.35 ..." and
fixes 12 cases; the list written here before the release freeze is 3 per family: offset 1 at mask 0.1, offset 2 at 0.6,
offset 3 at 0.35, offsets counted from 1 within the family's held-out target range).
"""
from __future__ import annotations
import argparse,json,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common import VerificationError,check,sha,dumps
from scripts.verify_release_060 import read_bytes_,jload,req,_guard,_freeze,manifest_ok
from scripts.verify_release_0110 import PREVIOUS_FREEZES as PF0110

STUDY='results/study-014'
RAW=('RESULTS.json','SCIENTIFIC.json')
REQUIRED_KEYS={'SEAL.json':'files_sha256','transfer/SEAL.json':'block','repro/transfer/SEAL.json':'block','KILL_DRILL_014.json':'kill_latency_s',
               'RUN_DONE_014.json':'elapsed_s','RUN_STATE_014.json':'events','PROGRESS_014.json':'streams',
               'STOP_014.json':'fired_at','STOP_014_ORCHESTRATOR.json':'stopped_at','CLEAN_CLONE_014.json':'passed'}
RELEASE_KEYS=('version','preregistration','preregistration_commit','source_freeze','source_freeze_commit','release_freeze',
              'scoring_scripts_commit','seal_commit','results_dir','gates_passed','gates_failed','GST2','G_RT','GTI_release_statement','api')
PREVIOUS_FREEZES=PF0110+('experiments/BRUTE_SOURCE_FREEZE_013.json','experiments/BRUTE_RELEASE_FREEZE_0110.json')
SCORING=('scripts/make_gates_014.py','scripts/make_paired_014.py','scripts/make_reproducibility_014.py','scripts/clean_clone_014.py')
LEDGER_ORDER=('diag_license_014','preregistration_014','seedcheck_014','source_freeze_014','scoring_freeze_014','run_start_014','seal_014','gates_014')
LONG_CAP=900
FAMILIES=('cycle3','switch3','unaliased2','ood4')


def long_cases(plan):
    R=plan['heldout_ranges_transfer']['targets'];out=[]
    for f in FAMILIES:
        lo=R[f][0];out+=[(f,lo,0.1),(f,lo+1,0.6),(f,lo+2,0.35)]
    return out


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
    idx=[ev.index(e) for e in LEDGER_ORDER];check(idx==sorted(idx),'ledger study-014 chronology')
    rs=max(i for i,e in enumerate(ev) if e=='run_start_014')
    end=[i for i,e in enumerate(ev) if e in ('run_end_014','stop_014') and i>rs]
    check(end and end[0]<max(i for i,e in enumerate(ev) if e=='seal_014'),'ledger lacks run_end_014/stop_014 between the held-out run_start and seal')
    from datetime import datetime
    def t(r):
        try:return datetime.fromisoformat(r['note'].split()[0])
        except (ValueError,IndexError,KeyError):raise VerificationError('ledger note without ISO time: '+r['event']) from None
    sf=t([r for r in receipts if r['event']=='scoring_freeze_014'][-1]);st=t(receipts[rs])
    check((st-sf).total_seconds()>=600,'scoring scripts ledgered < 10 min before run_start')
    return {'scoring_freeze_014':sf.isoformat(),'run_start_014':st.isoformat(),'gap_s':(st-sf).total_seconds()}


def git_order(root,rel):
    from scripts.verify_release_020 import _git
    def anc(a,b):return _git(root,'merge-base','--is-ancestor',a,b).returncode==0
    check(_git(root,'rev-parse','--git-dir').returncode==0,'not a git checkout')
    fr=jload(root/rel['source_freeze'])
    check(rel['preregistration_commit']==req(fr,'preregistration_commit','freeze'),'RELEASE.json preregistration_commit differs from the source freeze')
    chain=[(f'diagnostic_{i}',c) for i,c in enumerate(req(fr,'diagnostic_commits','freeze'))]
    chain+=[('preregistration',fr['preregistration_commit']),('seedcheck',fr['seedcheck_commit']),('reference',fr['reference_commit'])]
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
    from experiments import brute_study_014 as BS,v0120_reference as R
    from experiments.brute_common import load
    from scripts.make_reproducibility_014 import _canon
    plan=load(ROOT/'experiments/BRUTE_PLAN_014.json');L=long_cases(plan)
    sci=jload(Path(root)/STUDY/'transfer/SCIENTIFIC.json')
    M={(c['family'],c['seed'],c['mask_rate']):c for c in req(sci,'cases','SCIENTIFIC')}
    check(all(k in M for k in L) and len(L)==12,f'long_verify sample: {sum(k in M for k in L)}/{len(L)} sealed cases (12 required)')
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
    """GAPI2 at release: brute.certify/2 (and the carried brute.certify/1) import and answer host-agnostically."""
    from brute.api import certify as A1,certify2 as A2
    check(getattr(A1,'API',None)=='brute.certify/1','brute.api.certify API is not brute.certify/1')
    check(getattr(A2,'API',None)=='brute.certify/2','brute.api.certify2 API is not brute.certify/2')
    r=A2.certify2([(0,1)],[],0);check(r.get('api')=='brute.certify/2' and r.get('status')=='UNKNOWN','brute.certify/2 one-observation answer malformed')
    check(r.get('reason') in A2.REASONS,'brute.certify/2 reason not in REASONS')
    try:A2.Certifier2(margin=0);raise VerificationError('Certifier2 accepted margin 0')
    except ValueError:pass
    return {'interface':'brute.certify/2','carried':'brute.certify/1','one_observation':{'status':r['status'],'reason':r['reason']}}


def _verify(root,git,long=False):
    out={'schema':'brute.verify-release.v12_0','mode':'long' if long else 'short'}
    arts=parse_all(root);rel=arts['RELEASE.json'];out['artifacts_parsed']=len(arts)
    out['manifest_files']=manifest_ok(root)
    from brute.release_version_0120 import RELEASE_VERSION
    check(rel['version']==RELEASE_VERSION,'RELEASE.json version differs from brute.release_version_0120')
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
    for n in ('008','009','010','011','012','013'):__import__(f'scripts.study{n}_storage',fromlist=['ensure_raw']).ensure_raw(root/f'results/study-{n}')
    check(rel['results_dir']==STUDY,'results_dir');s14=root/STUDY
    from scripts.study014_storage import ensure_raw;ensure_raw(s14)
    top=arts[f'{STUDY}/SEAL.json']
    for f,d in req(top,'files_sha256','study SEAL').items():
        p=s14/f
        if p.exists():check(sha(p)==d,f'study-014 {f} does not match the study SEAL')
        else:check('CHECKPOINT' in f or f.startswith('logs/') or f in ('RUN_014.log',),f'study-014 sealed file {f} is missing (only checkpoints and logs may be absent)')
    for sub in ('transfer','repro/transfer'):
        if not (s14/sub/'SEAL.json').exists():continue
        S=arts[f'{STUDY}/{sub}/SEAL.json']
        for n,k in (('RESULTS.json','results_sha256'),('SCIENTIFIC.json','scientific_sha256')):check(sha(s14/sub/n)==req(S,k,sub),f'study-014 {sub}/{n} does not match its SEAL')
    from scripts import make_paired_014,make_reproducibility_014,make_gates_014
    for mod,name in ((make_paired_014,'PAIRED_ANALYSIS_014.json'),(make_reproducibility_014,'REPRODUCIBILITY_014.json'),(make_gates_014,'GATES_014.json')):
        if (s14/name).exists() or name=='GATES_014.json':
            check(read_bytes_(s14/name)==dumps(mod.build(s14)),f'study-014 {name} does not regenerate byte-for-byte')
    gates=arts[f'{STUDY}/GATES_014.json']
    from scripts.verify_release_020 import ledger_020
    receipts,sup=ledger_020(root,git);out['ledger_receipts']=len(receipts);out['ledger_superseded']=sup
    out['run_chronology']=ledger_order(receipts,root)
    sources={r['source'] for r in receipts}
    for need in (rel['source_freeze'],f'{STUDY}/SEAL.json',f'{STUDY}/GATES_014.json'):check(need in sources,'ledger lacks '+need)
    if git:out['process_order']=git_order(root,rel)
    out['gates_passed']=gates['passed'];out['gates_failed']=gates['failed'];out['gates_pending']=gates['pending']
    check(rel['gates_passed']==gates['passed'] and rel['gates_failed']==gates['failed'],'RELEASE.json gate lists differ from GATES_014.json')
    for k in ('GST2','G_RT'):
        check(rel[k]==gates[k],f'RELEASE.json {k} differs from GATES_014.json');out[k]=gates[k]
    out['stop_rule_fired']=gates.get('stop_rule_fired')
    out['api']=api_check();check(rel['api']==out['api']['interface'],'RELEASE.json api differs from brute.api.certify2')
    if long:out['GLV_long_verify']=long_verify(root)
    out['status']='passed'
    out['validity']='bounded deterministic Moore worlds (<= 4 states, 2 actions, 2 bits); transfer block pre-registered in BRUTE_PLAN_014; brute.certify/2 smoke-checked; not general intelligence'
    return out


def verify(root=ROOT,fast=True,git=True,long=False):
    return _guard(lambda r,g:_verify(r,g,long),Path(root),git)


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--long',action='store_true',help='GLV: re-run 12 cases and audit them (900 s cap)')
    ap.add_argument('--fast',action='store_true',help='accepted for symmetry; the default short mode');a=ap.parse_args()
    try:print(json.dumps(verify(long=a.long),indent=2))
    except VerificationError as e:print('VERIFICATION FAILED:',e);sys.exit(1)
